"""Constrained execution substrate for researcher-authored scientific programs."""

# ruff: noqa: D102, D105, D107, EM101, TRY003, TRY301

from __future__ import annotations

import ast
import json
import multiprocessing
import resource
import traceback
from dataclasses import dataclass
from math import exp, isfinite, log, sqrt
from typing import TYPE_CHECKING, Final, cast

from research_agent.investigation.records import ProgramAccess

if TYPE_CHECKING:
    from multiprocessing.connection import Connection

type JsonValue = bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"] | None


class ScientificProgramError(RuntimeError):
    """Authored scientific source failed or crossed the worker policy."""


@dataclass(frozen=True, slots=True)
class ProgramLimits:
    """Enforced per-entrypoint worker bounds."""

    wall_time_seconds: float = 2.0
    max_source_bytes: int = 64_000
    max_result_bytes: int = 2_000_000
    max_memory_bytes: int = 512_000_000

    def __post_init__(self) -> None:
        if (
            self.wall_time_seconds <= 0
            or min(
                self.max_source_bytes,
                self.max_result_bytes,
                self.max_memory_bytes,
            )
            <= 0
        ):
            raise ValueError("scientific program resource limits must be positive")


@dataclass(frozen=True, slots=True)
class ProgramInvocation:
    """One phase-specific payload; unavailable channels are absent, not hidden by convention."""

    entrypoint: str
    histories: dict[str, list[dict[str, JsonValue]]] | None = None
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
    {"history", "outcome_path", "training_rows", "model_state", "feature_values"}
)
_SAFE_CALLS: Final[frozenset[str]] = frozenset(
    {
        "abs",
        "all",
        "any",
        "bool",
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
        if invocation.entrypoint not in _ENTRYPOINTS:
            raise ScientificProgramError("unknown scientific program entrypoint")
        if len(source.encode()) > self._limits.max_source_bytes:
            raise ScientificProgramError("scientific source exceeds its declared bound")
        _validate_source(source)
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

    namespace: dict[str, object] = {
        "__builtins__": _SAFE_BUILTINS,
        "history": history,
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
        exec(compile(source, "<scientific-program>", "exec"), namespace)  # noqa: S102
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
        send.send({"kind": "success", "value": value, "accesses": accesses})
    except BaseException as error:  # noqa: BLE001
        send.send(
            {
                "kind": "failure",
                "detail": f"{type(error).__name__}: {error}",
                "traceback": traceback.format_exc(limit=12),
                "accesses": accesses,
            }
        )
    finally:
        send.close()


__all__ = [
    "ProgramInvocation",
    "ProgramLimits",
    "ProgramResult",
    "ScientificProgramError",
    "ScientificProgramHarness",
]
