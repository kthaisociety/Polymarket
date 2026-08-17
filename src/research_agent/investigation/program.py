"""Constrained execution substrate for researcher-authored scientific programs."""

# ruff: noqa: D102, D105, D107, EM101, TRY003, TRY300, TRY301

from __future__ import annotations

import ast
import json
import multiprocessing
import resource
import traceback
from contextlib import suppress
from dataclasses import dataclass
from math import exp, isfinite, log, sqrt
from typing import TYPE_CHECKING, Final, Self, cast

from research_agent.investigation.records import ProgramAccess

if TYPE_CHECKING:
    from multiprocessing.connection import Connection
    from multiprocessing.process import BaseProcess
    from types import CodeType

type JsonValue = bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"] | None


class ScientificProgramError(RuntimeError):
    """Authored scientific source failed or crossed the worker policy."""


@dataclass(frozen=True, slots=True)
class ProgramLimits:
    """Enforced per-entrypoint and persistent-session worker bounds."""

    wall_time_seconds: float = 2.0
    max_source_bytes: int = 64_000
    max_result_bytes: int = 2_000_000
    max_memory_bytes: int = 512_000_000
    max_session_invocations: int = 2_000_000

    def __post_init__(self) -> None:
        if (
            self.wall_time_seconds <= 0
            or min(
                self.max_source_bytes,
                self.max_result_bytes,
                self.max_memory_bytes,
                self.max_session_invocations,
            )
            <= 0
        ):
            raise ValueError("scientific program resource limits must be positive")


@dataclass(frozen=True, slots=True)
class ProgramInvocation:
    """One phase-specific payload; unavailable channels are absent, not hidden by convention."""

    entrypoint: str
    histories: dict[str, list[dict[str, JsonValue]]] | None = None
    context_histories: dict[str, list[dict[str, JsonValue]]] | None = None
    outcome: list[dict[str, JsonValue]] | None = None
    training: list[dict[str, JsonValue]] | None = None
    state: JsonValue = None
    features: dict[str, JsonValue] | None = None


@dataclass(frozen=True, slots=True)
class ProgramResult:
    """Finite JSON result plus harness-observed capability accesses."""

    value: JsonValue
    accesses: tuple[ProgramAccess, ...]


_INTERFACES: Final[frozenset[str]] = frozenset(
    {
        "history",
        "context_history",
        "outcome_path",
        "training_rows",
        "model_state",
        "feature_values",
    }
)
_SAFE_CALLS: Final[frozenset[str]] = frozenset(
    {
        "abs",
        "all",
        "any",
        "bool",
        "context_history",
        "dict",
        "enumerate",
        "exp",
        "float",
        "history",
        "int",
        "isfinite",
        "len",
        "list",
        "log",
        "max",
        "min",
        "model_state",
        "outcome_path",
        "predict",
        "range",
        "round",
        "set",
        "sorted",
        "sqrt",
        "str",
        "sum",
        "training_rows",
        "tuple",
        "feature_values",
        "zip",
    }
)
_SAFE_BUILTINS: Final[dict[str, object]] = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "range": range,
    "round": round,
    "set": set,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
}
_FORBIDDEN: Final[tuple[type[ast.AST], ...]] = (
    ast.AsyncFunctionDef,
    ast.Attribute,
    ast.Await,
    ast.ClassDef,
    ast.Delete,
    ast.Global,
    ast.Import,
    ast.ImportFrom,
    ast.Lambda,
    ast.Nonlocal,
    ast.Raise,
    ast.Try,
    ast.With,
    ast.AsyncWith,
    ast.Yield,
    ast.YieldFrom,
)
_ENTRYPOINTS: Final[frozenset[str]] = frozenset({"make_features", "make_label", "fit", "predict"})


class ScientificProgramHarness:
    """Execute exact authored source without filesystem, network, or scientific authority."""

    def __init__(self, limits: ProgramLimits | None = None) -> None:
        self._limits = limits or ProgramLimits()

    def invoke(self, source: str, invocation: ProgramInvocation) -> ProgramResult:
        self._validate(source, invocation)
        context = multiprocessing.get_context("fork")
        receive, send = context.Pipe(duplex=False)
        process = context.Process(
            target=_worker,
            args=(
                send,
                source,
                invocation,
                self._limits.max_result_bytes,
                self._limits.max_memory_bytes,
            ),
        )
        process.start()
        send.close()
        process.join(self._limits.wall_time_seconds)
        if process.is_alive():
            process.terminate()
            process.join()
            receive.close()
            raise ScientificProgramError("scientific program exceeded its wall-clock limit")
        if not receive.poll():
            receive.close()
            raise ScientificProgramError("scientific worker ended without a result")
        raw = cast("dict[str, object]", receive.recv())
        receive.close()
        return _decode_result(invocation, raw)

    def session(self, source: str) -> ScientificProgramSession:
        """Open one bounded worker that recompiles no source and retains no authored state."""
        if len(source.encode()) > self._limits.max_source_bytes:
            raise ScientificProgramError("scientific source exceeds its declared bound")
        _validate_source(source)
        context = multiprocessing.get_context("fork")
        parent, child = context.Pipe(duplex=True)
        process = context.Process(
            target=_session_worker,
            args=(
                child,
                source,
                self._limits.max_result_bytes,
                self._limits.max_memory_bytes,
            ),
        )
        process.start()
        child.close()
        if not parent.poll(self._limits.wall_time_seconds):
            _terminate(process, parent)
            raise ScientificProgramError(
                "scientific program session exceeded its wall-clock limit during initialization"
            )
        try:
            ready = cast("dict[str, object]", parent.recv())
        except EOFError as error:
            _terminate(process, parent)
            raise ScientificProgramError(
                "scientific session worker ended without a result"
            ) from error
        if ready.get("kind") != "ready":
            detail = cast("str", ready.get("detail", "scientific session failed to initialize"))
            _terminate(process, parent)
            raise ScientificProgramError(detail)
        return ScientificProgramSession(process, parent, self._limits)

    def _validate(self, source: str, invocation: ProgramInvocation) -> None:
        if invocation.entrypoint not in _ENTRYPOINTS:
            raise ScientificProgramError("unknown scientific program entrypoint")
        if len(source.encode()) > self._limits.max_source_bytes:
            raise ScientificProgramError("scientific source exceeds its declared bound")
        _validate_source(source)


class ScientificProgramSession:
    """One bounded worker with a fresh authored namespace and access log for every call."""

    def __init__(
        self,
        process: BaseProcess,
        connection: Connection,
        limits: ProgramLimits,
    ) -> None:
        self._process = process
        self._connection = connection
        self._limits = limits
        self._invocations = 0
        self._closed = False

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback_value: object) -> None:
        del exc_type, exc_value, traceback_value
        self.close()

    def invoke(self, invocation: ProgramInvocation) -> ProgramResult:
        """Execute one phase with the reference path's exact result and failure semantics."""
        if self._closed:
            raise ScientificProgramError("scientific program session is closed")
        if invocation.entrypoint not in _ENTRYPOINTS:
            raise ScientificProgramError("unknown scientific program entrypoint")
        if self._invocations >= self._limits.max_session_invocations:
            self.close()
            raise ScientificProgramError("scientific program session invocation limit exceeded")
        self._invocations += 1
        try:
            self._connection.send(("invoke", invocation))
        except (BrokenPipeError, EOFError, OSError) as error:
            self._close_broken()
            raise ScientificProgramError(
                "scientific session worker ended without a result"
            ) from error
        if not self._connection.poll(self._limits.wall_time_seconds):
            self._close_broken()
            raise ScientificProgramError("scientific program exceeded its wall-clock limit")
        try:
            raw = cast("dict[str, object]", self._connection.recv())
        except EOFError as error:
            self._close_broken()
            raise ScientificProgramError(
                "scientific session worker ended without a result"
            ) from error
        return _decode_result(invocation, raw)

    def close(self) -> None:
        """Close the session deterministically and terminate a non-responsive worker."""
        if self._closed:
            return
        self._closed = True
        with suppress(BrokenPipeError, EOFError, OSError):
            self._connection.send(("close", None))
        self._process.join(self._limits.wall_time_seconds)
        if self._process.is_alive():
            self._process.terminate()
            self._process.join()
        self._connection.close()

    def _close_broken(self) -> None:
        self._closed = True
        _terminate(self._process, self._connection)


def _validate_source(source: str) -> None:
    try:
        tree = ast.parse(source, filename="<scientific-program>", mode="exec")
    except SyntaxError as error:
        raise ScientificProgramError("scientific source is not valid Python") from error
    function_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    if not function_names >= _ENTRYPOINTS:
        raise ScientificProgramError("scientific source must define all four exact entrypoints")
    allowed_calls = _SAFE_CALLS | function_names
    for node in ast.walk(tree):
        if isinstance(node, _FORBIDDEN):
            raise ScientificProgramError("scientific source requests an unavailable host interface")
        if isinstance(node, ast.Name) and "__" in node.id:
            raise ScientificProgramError("scientific source requests runtime introspection")
        if isinstance(node, ast.Call) and (
            not isinstance(node.func, ast.Name) or node.func.id not in allowed_calls
        ):
            raise ScientificProgramError("scientific source calls an unavailable interface")


def _worker(
    send: Connection,
    source: str,
    invocation: ProgramInvocation,
    max_result_bytes: int,
    max_memory_bytes: int,
) -> None:
    resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))
    raw = _execute_invocation(
        compile(source, "<scientific-program>", "exec"),
        invocation,
        max_result_bytes,
    )
    send.send(raw)
    send.close()


def _session_worker(
    connection: Connection,
    source: str,
    max_result_bytes: int,
    max_memory_bytes: int,
) -> None:
    resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))
    try:
        compiled = compile(source, "<scientific-program>", "exec")
        connection.send({"kind": "ready"})
        while True:
            kind, invocation = cast("tuple[str, ProgramInvocation | None]", connection.recv())
            if kind == "close":
                return
            if kind != "invoke" or invocation is None:
                connection.send(
                    {"kind": "failure", "detail": "scientific session received an invalid command"}
                )
                continue
            connection.send(_execute_invocation(compiled, invocation, max_result_bytes))
    except EOFError:
        return
    except BaseException as error:  # noqa: BLE001
        with suppress(BrokenPipeError, EOFError, OSError):
            connection.send(
                {
                    "kind": "startup_failure",
                    "detail": f"{type(error).__name__}: {error}",
                    "traceback": traceback.format_exc(limit=12),
                }
            )
    finally:
        connection.close()


def _execute_invocation(
    compiled: CodeType,
    invocation: ProgramInvocation,
    max_result_bytes: int,
) -> dict[str, object]:
    accesses: list[tuple[str, str | None]] = []

    def require(interface: str, value: object) -> object:
        if value is None:
            message = f"{interface} is unavailable in {invocation.entrypoint}"
            raise PermissionError(message)
        accesses.append((interface, None))
        return value

    def history(field_id: str) -> list[dict[str, JsonValue]]:
        if invocation.histories is None or field_id not in invocation.histories:
            raise PermissionError("history field is outside the exact invocation grant")
        accesses.append(("history", field_id))
        return invocation.histories[field_id]

    def context_history(field_id: str) -> list[dict[str, JsonValue]]:
        if invocation.context_histories is None or field_id not in invocation.context_histories:
            raise PermissionError("context history field is outside the exact invocation grant")
        accesses.append(("context_history", field_id))
        return invocation.context_histories[field_id]

    namespace: dict[str, object] = {
        "__builtins__": _SAFE_BUILTINS.copy(),
        "history": history,
        "context_history": context_history,
        "outcome_path": lambda: require("outcome_path", invocation.outcome),
        "training_rows": lambda: require("training_rows", invocation.training),
        "model_state": lambda: require("model_state", invocation.state),
        "feature_values": lambda: require("feature_values", invocation.features),
        "sqrt": sqrt,
        "log": log,
        "exp": exp,
        "isfinite": isfinite,
    }
    try:
        exec(compiled, namespace)  # noqa: S102
        entrypoint = namespace.get(invocation.entrypoint)
        if not callable(entrypoint):
            raise TypeError("scientific entrypoint is not callable")
        value = entrypoint()
        encoded = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        if len(encoded) > max_result_bytes:
            raise ValueError("scientific result exceeds its declared bound")
        return {"kind": "success", "value": value, "accesses": accesses}
    except BaseException as error:  # noqa: BLE001
        return {
            "kind": "failure",
            "detail": f"{type(error).__name__}: {error}",
            "traceback": traceback.format_exc(limit=12),
            "accesses": accesses,
        }


def _decode_result(invocation: ProgramInvocation, raw: dict[str, object]) -> ProgramResult:
    if raw.get("kind") != "success":
        detail = cast("str", raw.get("detail", "scientific program failed"))
        raise ScientificProgramError(detail)
    value = cast("JsonValue", raw["value"])
    accesses = tuple(
        ProgramAccess(invocation.entrypoint, ordinal, interface, field_id)
        for ordinal, (interface, field_id) in enumerate(
            cast("list[tuple[str, str | None]]", raw["accesses"])
        )
    )
    return ProgramResult(value, accesses)


def _terminate(process: BaseProcess, connection: Connection) -> None:
    if process.is_alive():
        process.terminate()
        process.join()
    connection.close()


__all__ = [
    "ProgramInvocation",
    "ProgramLimits",
    "ProgramResult",
    "ScientificProgramError",
    "ScientificProgramHarness",
    "ScientificProgramSession",
]
