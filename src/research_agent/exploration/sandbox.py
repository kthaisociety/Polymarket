"""A narrow subprocess boundary for researcher-authored exploratory Python.

This first substrate intentionally supplies data through one callable rather than exposing a
filesystem or dataframe catalog.  The syntax gate is a defence-in-depth boundary for this local
implementation, not a claim of OS-container isolation.
"""

from __future__ import annotations

import ast
import hashlib
import io
import json
import linecache
import math
import multiprocessing
import resource
import traceback
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, cast

if TYPE_CHECKING:
    from collections.abc import Mapping
    from multiprocessing.connection import Connection

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


class AnalysisStatus(Enum):
    """Truthful outcome of authorization and execution."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DENIED = "denied"


class ArtifactKind(Enum):
    """Exploratory detail retained outside the model-facing observation."""

    STDOUT = "stdout"
    STDERR = "stderr"
    TRACEBACK = "traceback"
    RESULT = "result"


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    """Immutable, session-authorized reference to drill-down content."""

    artifact_id: str
    kind: ArtifactKind
    size_bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class _ArtifactRecord:
    content: bytes
    session_id: str
    ref: ArtifactRef


class ArtifactStore:
    """Small in-memory ArtifactStore proving immutable, authorized drill-down semantics."""

    def __init__(self) -> None:
        """Create an empty artifact collection."""
        self._records: dict[str, _ArtifactRecord] = {}

    def __len__(self) -> int:
        """Return the number of retained immutable artifacts."""
        return len(self._records)

    def persist(
        self,
        content: bytes,
        *,
        session_id: str,
        kind: ArtifactKind,
    ) -> ArtifactRef:
        """Persist exact content under a content-derived, session-scoped identity."""
        digest = hashlib.sha256(content).hexdigest()
        identity_material = f"{session_id}:{kind.value}:{digest}".encode()
        artifact_id = hashlib.sha256(identity_material).hexdigest()
        ref = ArtifactRef(
            artifact_id=artifact_id,
            kind=kind,
            size_bytes=len(content),
            sha256=digest,
        )
        existing = self._records.get(artifact_id)
        if existing is not None and existing.content != content:
            msg = "artifact identity collision"
            raise RuntimeError(msg)
        self._records[artifact_id] = _ArtifactRecord(
            content=content, session_id=session_id, ref=ref
        )
        return ref

    def read(self, ref: ArtifactRef, *, session_id: str) -> bytes:
        """Retrieve exact content only for the session to which it was persisted."""
        record = self._records.get(ref.artifact_id)
        if record is None:
            raise KeyError(ref.artifact_id)
        if record.session_id != session_id:
            msg = "artifact access denied"
            raise PermissionError(msg)
        if record.ref != ref:
            msg = "artifact reference does not match stored identity"
            raise ValueError(msg)
        return record.content


@dataclass(frozen=True, slots=True)
class AuthorizedDataView:
    """A pre-scoped development-data capability, not a general data-domain object."""

    view_id: str
    dataset_ref: str
    environment_ref: str
    fields: Mapping[str, tuple[JsonValue, ...]]
    protected: bool = False

    def __post_init__(self) -> None:
        """Detach the capability from caller-owned mutable mappings."""
        copied = {field_id: tuple(values) for field_id, values in self.fields.items()}
        object.__setattr__(self, "fields", MappingProxyType(copied))


@dataclass(frozen=True, slots=True)
class AnalysisCapabilitySurface:
    """Value-free description of one exact exploratory capability grant."""

    view_id: str
    dataset_ref: str
    environment_ref: str
    field_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DataAccessRequest:
    """Exact view and fields requested for one analysis."""

    view_id: str
    field_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AnalysisRequest:
    """Researcher-authored local Python plus its requested capabilities."""

    session_id: str
    action_id: str
    source: str
    data_access: tuple[DataAccessRequest, ...] = ()
    random_seed: int | None = None


@dataclass(frozen=True, slots=True)
class ResourceLimits:
    """Limits actually enforced by this implementation."""

    wall_time_seconds: float = 2.0
    max_source_bytes: int = 64_000
    max_inline_bytes: int = 2_000
    max_output_bytes: int = 1_000_000
    max_result_bytes: int = 2_000_000
    max_memory_bytes: int = 512_000_000

    def __post_init__(self) -> None:
        """Reject limits that cannot bound an execution."""
        if self.wall_time_seconds <= 0:
            msg = "wall_time_seconds must be positive"
            raise ValueError(msg)
        for value in (
            self.max_source_bytes,
            self.max_inline_bytes,
            self.max_output_bytes,
            self.max_result_bytes,
            self.max_memory_bytes,
        ):
            if value <= 0:
                msg = "byte limits must be positive"
                raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class CapabilityPolicy:
    """Least-authority development-view policy for one research session."""

    session_id: str
    environment_ref: str
    allowed_fields_by_view: Mapping[str, frozenset[str]]

    def __post_init__(self) -> None:
        """Detach policy grants from caller-owned mutable mappings."""
        copied = {
            view_id: frozenset(field_ids)
            for view_id, field_ids in self.allowed_fields_by_view.items()
        }
        object.__setattr__(self, "allowed_fields_by_view", MappingProxyType(copied))


@dataclass(frozen=True, slots=True)
class DataAccessRecord:
    """One successful harness-observed field access in execution order."""

    ordinal: int
    view_id: str
    dataset_ref: str
    environment_ref: str
    field_id: str


@dataclass(frozen=True, slots=True)
class ExecutionProvenance:
    """Harness-owned execution facts; authored code cannot supply these values."""

    action_id: str
    code_sha256: str
    accesses: tuple[DataAccessRecord, ...]
    dataset_refs: tuple[str, ...]
    environment_refs: tuple[str, ...]
    random_seed: int | None
    execution_status: AnalysisStatus


@dataclass(frozen=True, slots=True)
class StructuredObservation:
    """Concise provisional evidence returned to the research loop."""

    status: AnalysisStatus
    summary: str
    details: JsonValue
    stdout_preview: str
    stderr_preview: str
    warnings: tuple[str, ...]
    recoverable: bool
    provenance: ExecutionProvenance
    artifact_refs: tuple[ArtifactRef, ...]
    epistemic_status: str = "EXPLORATORY"
    formal_object_refs: tuple[str, ...] = ()
    durable_state_effects: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _Grant:
    fields_by_view: dict[str, dict[str, tuple[JsonValue, ...]]]
    identities_by_view: dict[str, tuple[str, str]]


@dataclass(frozen=True, slots=True)
class _WorkerLimits:
    max_output_bytes: int
    max_result_bytes: int
    max_memory_bytes: int


class _AuthorizationDeniedError(Exception):
    pass


class _ExecutionAccessDeniedError(Exception):
    pass


class _PolicyViolationError(Exception):
    pass


class _OutputLimitExceededError(Exception):
    pass


class _BoundedTextIO(io.StringIO):
    def __init__(self, max_bytes: int) -> None:
        super().__init__()
        self._max_bytes = max_bytes
        self._written_bytes = 0

    def write(self, value: str) -> int:
        encoded_size = len(value.encode())
        if self._written_bytes + encoded_size > self._max_bytes:
            msg = "analysis output exceeded its declared byte limit"
            raise _OutputLimitExceededError(msg)
        self._written_bytes += encoded_size
        return super().write(value)


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
        "int",
        "len",
        "list",
        "log",
        "max",
        "min",
        "print",
        "range",
        "read",
        "round",
        "set",
        "sorted",
        "str",
        "structured_return",
        "sum",
        "tuple",
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
    "exp": math.exp,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "log": math.log,
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
_FORBIDDEN_NODES: Final[tuple[type[ast.AST], ...]] = (
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


def _validate_source(source: str) -> ast.Module:
    try:
        tree = ast.parse(source, filename="<analysis>", mode="exec")
    except SyntaxError as exc:
        msg = "analysis source is not valid Python"
        raise _PolicyViolationError(msg) from exc

    function_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    allowed_calls = _SAFE_CALLS | function_names
    for node in ast.walk(tree):
        if isinstance(node, _FORBIDDEN_NODES):
            msg = "analysis requests an unavailable host interface"
            raise _PolicyViolationError(msg)
        if isinstance(node, ast.Name) and "__" in node.id:
            msg = "analysis requests an unavailable runtime interface"
            raise _PolicyViolationError(msg)
        if isinstance(node, ast.Call) and (
            not isinstance(node.func, ast.Name) or node.func.id not in allowed_calls
        ):
            msg = "analysis calls an unavailable runtime interface"
            raise _PolicyViolationError(msg)
    return tree


def _json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    except (TypeError, ValueError) as exc:
        msg = "structured result must contain JSON-compatible finite values"
        raise ValueError(msg) from exc


def _validate_worker_result(raw_result: object, max_result_bytes: int) -> dict[str, object]:
    if not isinstance(raw_result, dict):
        msg = "analysis must assign result = structured_return(...)"
        raise TypeError(msg)
    result = cast("dict[str, object]", raw_result)
    if len(_json_bytes(result)) > max_result_bytes:
        msg = "structured result exceeded its declared byte limit"
        raise _OutputLimitExceededError(msg)
    return result


def _run_worker(
    send_connection: Connection,
    source: str,
    grant: _Grant,
    limits: _WorkerLimits,
) -> None:
    resource.setrlimit(resource.RLIMIT_AS, (limits.max_memory_bytes, limits.max_memory_bytes))
    stdout = _BoundedTextIO(limits.max_output_bytes)
    stderr = _BoundedTextIO(limits.max_output_bytes)
    accesses: list[tuple[str, str]] = []

    def read(view_id: str, field_id: str) -> tuple[JsonValue, ...]:
        fields = grant.fields_by_view.get(view_id)
        if fields is None or field_id not in fields:
            msg = "analysis attempted data access outside its exact grant"
            raise _ExecutionAccessDeniedError(msg)
        accesses.append((view_id, field_id))
        return fields[field_id]

    def structured_return(
        summary: str,
        details: JsonValue,
        *,
        warnings: tuple[str, ...] | list[str] = (),
        claimed_provenance: JsonValue = None,
    ) -> dict[str, object]:
        return {
            "summary": summary,
            "details": details,
            "warnings": tuple(warnings),
            "claimed_provenance": claimed_provenance,
        }

    def captured_print(
        *values: object,
        sep: str = " ",
        end: str = "\n",
        flush: bool = False,
    ) -> None:
        print(*values, sep=sep, end=end, file=stdout, flush=flush)

    namespace: dict[str, object] = {
        "__builtins__": _SAFE_BUILTINS,
        "read": read,
        "structured_return": structured_return,
        "print": captured_print,
    }
    try:
        tree = _validate_source(source)
        linecache.cache["<analysis>"] = (
            len(source),
            None,
            source.splitlines(keepends=True),
            "<analysis>",
        )
        exec(compile(tree, "<analysis>", "exec"), namespace)  # noqa: S102
        raw_result = _validate_worker_result(namespace.get("result"), limits.max_result_bytes)
        send_connection.send(
            {
                "kind": "success",
                "result": raw_result,
                "stdout": stdout.getvalue(),
                "stderr": stderr.getvalue(),
                "accesses": accesses,
            }
        )
    except _ExecutionAccessDeniedError:
        send_connection.send(
            {
                "kind": "denied",
                "stdout": stdout.getvalue(),
                "stderr": stderr.getvalue(),
                "accesses": accesses,
            }
        )
    except _PolicyViolationError:
        send_connection.send(
            {
                "kind": "policy_denied",
                "stdout": "",
                "stderr": "",
                "accesses": [],
            }
        )
    except BaseException as exc:  # noqa: BLE001
        send_connection.send(
            {
                "kind": "failure",
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc(),
                "stdout": stdout.getvalue(),
                "stderr": stderr.getvalue(),
                "accesses": accesses,
            }
        )
    finally:
        send_connection.close()


class AnalysisHarness:
    """Authorize, execute, record actual access, and assemble provisional observations."""

    def __init__(
        self,
        *,
        views: Mapping[str, AuthorizedDataView],
        policy: CapabilityPolicy,
        artifacts: ArtifactStore,
        resource_limits: ResourceLimits | None = None,
    ) -> None:
        """Bind the execution boundary to scoped views, policy, artifacts, and limits."""
        self._views = MappingProxyType(dict(views))
        self._policy = policy
        self.artifacts = artifacts
        self._limits = resource_limits or ResourceLimits()

    def authorized_runtime_surfaces(
        self,
        *,
        session_id: str,
        environment_ref: str,
        readable_dataset_refs: tuple[str, ...],
        protected_resource_refs: tuple[str, ...],
        investigation_dataset_refs: frozenset[str],
    ) -> tuple[AnalysisCapabilitySurface, ...]:
        """Describe already-authorized non-protected views without reading their values."""
        if session_id != self._policy.session_id or environment_ref != self._policy.environment_ref:
            msg = "analysis harness is not bound to this runtime authority"
            raise PermissionError(msg)
        readable = frozenset(readable_dataset_refs)
        protected = frozenset(protected_resource_refs)
        surfaces: list[AnalysisCapabilitySurface] = []
        for view_id in sorted(self._views):
            view = self._views[view_id]
            allowed = self._policy.allowed_fields_by_view.get(view_id, frozenset())
            if (
                view.environment_ref != environment_ref
                or view.dataset_ref not in readable
                or view.dataset_ref not in investigation_dataset_refs
                or view.dataset_ref in protected
                or view.protected
            ):
                continue
            field_ids = tuple(sorted(allowed & view.fields.keys()))
            if field_ids:
                surfaces.append(
                    AnalysisCapabilitySurface(
                        view_id=view.view_id,
                        dataset_ref=view.dataset_ref,
                        environment_ref=view.environment_ref,
                        field_ids=field_ids,
                    )
                )
        return tuple(surfaces)

    def accepts_runtime_scope(
        self,
        *,
        session_id: str,
        environment_ref: str,
        readable_dataset_refs: tuple[str, ...],
        protected_resource_refs: tuple[str, ...],
        requested_view_ids: tuple[str, ...],
    ) -> bool:
        """Check runtime/session binding without reading or returning view values."""
        if session_id != self._policy.session_id or environment_ref != self._policy.environment_ref:
            return False
        readable = frozenset(readable_dataset_refs)
        protected = frozenset(protected_resource_refs)
        for view_id in requested_view_ids:
            view = self._views.get(view_id)
            if (
                view is None
                or view.environment_ref != environment_ref
                or view.dataset_ref not in readable
                or view.dataset_ref in protected
                or view.protected
            ):
                return False
        return True

    def run(self, request: AnalysisRequest) -> StructuredObservation:
        """Run one analysis without a handle to episode, state, formal, or protected stores."""
        code_sha256 = hashlib.sha256(request.source.encode()).hexdigest()
        try:
            grant = self._authorize(request)
        except _AuthorizationDeniedError:
            return self._observation(
                request=request,
                code_sha256=code_sha256,
                status=AnalysisStatus.DENIED,
                summary="Analysis authorization denied by capability policy.",
                recoverable=False,
            )

        context = multiprocessing.get_context("fork")
        receive_connection, send_connection = context.Pipe(duplex=False)
        process = context.Process(
            target=_run_worker,
            args=(
                send_connection,
                request.source,
                grant,
                _WorkerLimits(
                    max_output_bytes=self._limits.max_output_bytes,
                    max_result_bytes=self._limits.max_result_bytes,
                    max_memory_bytes=self._limits.max_memory_bytes,
                ),
            ),
        )
        process.start()
        send_connection.close()
        process.join(self._limits.wall_time_seconds)
        if process.is_alive():
            process.terminate()
            process.join()
            receive_connection.close()
            return self._observation(
                request=request,
                code_sha256=code_sha256,
                status=AnalysisStatus.FAILED,
                summary="Analysis exceeded its wall-clock time limit.",
                recoverable=True,
            )
        if not receive_connection.poll():
            receive_connection.close()
            return self._observation(
                request=request,
                code_sha256=code_sha256,
                status=AnalysisStatus.FAILED,
                summary="Analysis worker ended without a result.",
                recoverable=True,
            )
        worker_result = cast("dict[str, object]", receive_connection.recv())
        receive_connection.close()
        return self._assemble(request, code_sha256, grant, worker_result)

    def _authorize(self, request: AnalysisRequest) -> _Grant:
        if request.session_id != self._policy.session_id:
            raise _AuthorizationDeniedError
        if len(request.source.encode()) > self._limits.max_source_bytes:
            raise _AuthorizationDeniedError
        fields_by_view: dict[str, dict[str, tuple[JsonValue, ...]]] = {}
        identities_by_view: dict[str, tuple[str, str]] = {}
        seen_views: set[str] = set()
        for access in request.data_access:
            if access.view_id in seen_views:
                raise _AuthorizationDeniedError
            seen_views.add(access.view_id)
            view = self._views.get(access.view_id)
            allowed = self._policy.allowed_fields_by_view.get(access.view_id)
            if view is None or allowed is None:
                raise _AuthorizationDeniedError
            if view.environment_ref != self._policy.environment_ref or view.protected:
                raise _AuthorizationDeniedError
            requested = frozenset(access.field_ids)
            if not requested <= allowed or not requested <= view.fields.keys():
                raise _AuthorizationDeniedError
            fields_by_view[view.view_id] = {
                field_id: tuple(view.fields[field_id]) for field_id in access.field_ids
            }
            identities_by_view[view.view_id] = (view.dataset_ref, view.environment_ref)
        return _Grant(fields_by_view=fields_by_view, identities_by_view=identities_by_view)

    def _assemble(
        self,
        request: AnalysisRequest,
        code_sha256: str,
        grant: _Grant,
        worker_result: dict[str, object],
    ) -> StructuredObservation:
        kind = cast("str", worker_result["kind"])
        access_pairs = cast("list[tuple[str, str]]", worker_result.get("accesses", []))
        accesses = self._actual_accesses(access_pairs, grant)
        stdout = cast("str", worker_result.get("stdout", ""))
        stderr = cast("str", worker_result.get("stderr", ""))
        artifact_refs: list[ArtifactRef] = []
        if stdout:
            artifact_refs.append(
                self.artifacts.persist(
                    stdout.encode(), session_id=request.session_id, kind=ArtifactKind.STDOUT
                )
            )
        if stderr:
            artifact_refs.append(
                self.artifacts.persist(
                    stderr.encode(), session_id=request.session_id, kind=ArtifactKind.STDERR
                )
            )

        if kind in {"denied", "policy_denied"}:
            return self._observation(
                request=request,
                code_sha256=code_sha256,
                status=AnalysisStatus.DENIED,
                summary="Analysis attempted an interface outside its exact capability grant.",
                recoverable=False,
                accesses=accesses,
                stdout=stdout,
                stderr=stderr,
                artifact_refs=artifact_refs,
            )
        if kind == "failure":
            raw_traceback = cast("str", worker_result["traceback"])
            artifact_refs.append(
                self.artifacts.persist(
                    raw_traceback.encode(),
                    session_id=request.session_id,
                    kind=ArtifactKind.TRACEBACK,
                )
            )
            exception_type = cast("str", worker_result["exception_type"])
            return self._observation(
                request=request,
                code_sha256=code_sha256,
                status=AnalysisStatus.FAILED,
                summary=f"Exploratory analysis failed with {exception_type}.",
                recoverable=True,
                accesses=accesses,
                stdout=stdout,
                stderr=stderr,
                artifact_refs=artifact_refs,
            )

        return self._assemble_success(
            request,
            code_sha256,
            accesses,
            stdout,
            stderr,
            artifact_refs,
            cast("dict[str, object]", worker_result["result"]),
        )

    def _assemble_success(  # noqa: PLR0913, PLR0917
        self,
        request: AnalysisRequest,
        code_sha256: str,
        accesses: tuple[DataAccessRecord, ...],
        stdout: str,
        stderr: str,
        artifact_refs: list[ArtifactRef],
        raw_result: dict[str, object],
    ) -> StructuredObservation:
        summary_value = raw_result.get("summary")
        if not isinstance(summary_value, str) or not summary_value.strip():
            return self._malformed_result(
                request, code_sha256, accesses, stdout, stderr, artifact_refs
            )
        summary = summary_value
        details = cast("JsonValue", raw_result["details"])
        details_bytes = _json_bytes(details)
        inline_details: JsonValue = details
        if len(details_bytes) > self._limits.max_inline_bytes:
            artifact_refs.append(
                self.artifacts.persist(
                    _json_bytes(raw_result),
                    session_id=request.session_id,
                    kind=ArtifactKind.RESULT,
                )
            )
            inline_details = None
        authored_warnings = raw_result.get("warnings", ())
        if not isinstance(authored_warnings, (tuple, list)):
            return self._malformed_result(
                request, code_sha256, accesses, stdout, stderr, artifact_refs
            )
        warning_values = cast("list[object] | tuple[object, ...]", authored_warnings)
        if not all(isinstance(item, str) for item in warning_values):
            return self._malformed_result(
                request, code_sha256, accesses, stdout, stderr, artifact_refs
            )
        warnings = tuple(cast("list[str] | tuple[str, ...]", warning_values))
        if len(_json_bytes(warnings)) > self._limits.max_inline_bytes:
            if not any(ref.kind is ArtifactKind.RESULT for ref in artifact_refs):
                artifact_refs.append(
                    self.artifacts.persist(
                        _json_bytes(raw_result),
                        session_id=request.session_id,
                        kind=ArtifactKind.RESULT,
                    )
                )
            warnings = ("authored warnings were externalized",)
        if raw_result.get("claimed_provenance") is not None:
            warnings += ("self-reported provenance was ignored",)
        if len(summary.encode()) > self._limits.max_inline_bytes:
            if not any(ref.kind is ArtifactKind.RESULT for ref in artifact_refs):
                artifact_refs.append(
                    self.artifacts.persist(
                        _json_bytes(raw_result),
                        session_id=request.session_id,
                        kind=ArtifactKind.RESULT,
                    )
                )
            summary = self._bounded_preview(summary)
        return self._observation(
            request=request,
            code_sha256=code_sha256,
            status=AnalysisStatus.SUCCEEDED,
            summary=summary,
            details=inline_details,
            warnings=warnings,
            recoverable=False,
            accesses=accesses,
            stdout=stdout,
            stderr=stderr,
            artifact_refs=artifact_refs,
        )

    def _malformed_result(  # noqa: PLR0913, PLR0917
        self,
        request: AnalysisRequest,
        code_sha256: str,
        accesses: tuple[DataAccessRecord, ...],
        stdout: str,
        stderr: str,
        artifact_refs: list[ArtifactRef],
    ) -> StructuredObservation:
        return self._observation(
            request=request,
            code_sha256=code_sha256,
            status=AnalysisStatus.FAILED,
            summary="Exploratory analysis returned a malformed structured result.",
            recoverable=True,
            accesses=accesses,
            stdout=stdout,
            stderr=stderr,
            artifact_refs=artifact_refs,
        )

    @staticmethod
    def _actual_accesses(
        access_pairs: list[tuple[str, str]], grant: _Grant
    ) -> tuple[DataAccessRecord, ...]:
        records: list[DataAccessRecord] = []
        for ordinal, (view_id, field_id) in enumerate(access_pairs):
            dataset_ref, environment_ref = grant.identities_by_view[view_id]
            records.append(
                DataAccessRecord(
                    ordinal=ordinal,
                    view_id=view_id,
                    dataset_ref=dataset_ref,
                    environment_ref=environment_ref,
                    field_id=field_id,
                )
            )
        return tuple(records)

    def _observation(  # noqa: PLR0913
        self,
        *,
        request: AnalysisRequest,
        code_sha256: str,
        status: AnalysisStatus,
        summary: str,
        recoverable: bool,
        details: JsonValue = None,
        warnings: tuple[str, ...] = (),
        accesses: tuple[DataAccessRecord, ...] = (),
        stdout: str = "",
        stderr: str = "",
        artifact_refs: list[ArtifactRef] | None = None,
    ) -> StructuredObservation:
        datasets = tuple(dict.fromkeys(access.dataset_ref for access in accesses))
        environments = tuple(dict.fromkeys(access.environment_ref for access in accesses))
        provenance = ExecutionProvenance(
            action_id=request.action_id,
            code_sha256=code_sha256,
            accesses=accesses,
            dataset_refs=datasets,
            environment_refs=environments,
            random_seed=request.random_seed,
            execution_status=status,
        )
        return StructuredObservation(
            status=status,
            summary=summary,
            details=details,
            stdout_preview=self._bounded_preview(stdout),
            stderr_preview=self._bounded_preview(stderr),
            warnings=warnings,
            recoverable=recoverable,
            provenance=provenance,
            artifact_refs=tuple(artifact_refs or ()),
        )

    def _bounded_preview(self, value: str) -> str:
        encoded = value.encode()
        if len(encoded) <= self._limits.max_inline_bytes:
            return value
        return encoded[: self._limits.max_inline_bytes].decode(errors="ignore")
