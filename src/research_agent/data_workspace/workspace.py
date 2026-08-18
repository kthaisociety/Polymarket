"""Source-agnostic acquisition and offline derivation over immutable local bytes."""

# ruff: noqa: C901, EM101, FBT003, PLR0911, PLR0912, PLR0913, PLR0915, PLR0917, TRY003, TRY301, TRY004

from __future__ import annotations

import ast
import contextlib
import csv
import hashlib
import io
import json
import multiprocessing
import os
import platform
import resource
import stat
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, Protocol, Self, cast

if TYPE_CHECKING:
    from collections.abc import Mapping
    from http.client import HTTPMessage
    from multiprocessing.connection import Connection
    from typing import IO

    from research_agent.exploration import AuthorizedDataView

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
_SCHEMA_VERSION: Final[str] = "generic-data-workspace/v1"
_WORKER_VERSION: Final[str] = "offline-json-transform/v1"
_DEFAULT_MAX_RESPONSE_BYTES: Final[int] = 64 * 1024 * 1024
_DEFAULT_MAX_CODE_BYTES: Final[int] = 128_000
_DEFAULT_MAX_OUTPUT_BYTES: Final[int] = 64 * 1024 * 1024
_DEFAULT_MEMORY_BYTES: Final[int] = 512_000_000
_DEFAULT_WALL_SECONDS: Final[float] = 10.0
_SECRET_MARKERS: Final[tuple[str, ...]] = (
    "authorization",
    "credential",
    "password",
    "secret",
    "signature",
    "token",
    "api-key",
    "apikey",
)


class FetchStatus(Enum):
    """Truthful acquisition outcome."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"


class DeriveStatus(Enum):
    """Truthful offline transformation outcome."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DENIED = "denied"


@dataclass(frozen=True, slots=True)
class SourceSnapshotRef:
    """Value-free public reference to one verified retained HTTP response."""

    snapshot_id: str
    content_sha256: str
    size_bytes: int

    @property
    def uri(self) -> str:
        """Return the stable path-independent reference spelling."""
        return f"source:{self.snapshot_id}"

    def as_dict(self) -> dict[str, JsonValue]:
        """Return a predictable JSON representation without response values."""
        return {
            "kind": "SourceSnapshotRef",
            "snapshot_id": self.snapshot_id,
            "content_sha256": self.content_sha256,
            "size_bytes": self.size_bytes,
            "uri": self.uri,
        }


@dataclass(frozen=True, slots=True)
class DerivedDatasetRef:
    """Public reference binding exact inputs, authored code, runtime, and output."""

    dataset_id: str
    output_sha256: str
    size_bytes: int
    code_sha256: str
    input_ref_ids: tuple[str, ...]
    parameters_sha256: str
    runtime_id: str

    @property
    def uri(self) -> str:
        """Return the stable path-independent reference spelling."""
        return f"derived:{self.dataset_id}"

    def as_dict(self) -> dict[str, JsonValue]:
        """Return the exact public lineage reference."""
        return {
            "kind": "DerivedDatasetRef",
            "dataset_id": self.dataset_id,
            "output_sha256": self.output_sha256,
            "size_bytes": self.size_bytes,
            "code_sha256": self.code_sha256,
            "input_ref_ids": list(self.input_ref_ids),
            "parameters_sha256": self.parameters_sha256,
            "runtime_id": self.runtime_id,
            "uri": self.uri,
        }


@dataclass(frozen=True, slots=True)
class FetchRequest:
    """One bounded generic HTTP acquisition request."""

    url: str
    method: str = "GET"
    headers: Mapping[str, str] = MappingProxyType({})
    body: bytes | None = None
    max_response_bytes: int = _DEFAULT_MAX_RESPONSE_BYTES
    timeout_seconds: float = 30.0
    allowed_redirect_hosts: tuple[str, ...] = ()
    permit_redirects: bool = True

    def __post_init__(self) -> None:
        """Detach mutable credentials and validate the acquisition boundary."""
        parsed = urllib.parse.urlsplit(self.url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            msg = "fetch URL must use http or https with a host"
            raise ValueError(msg)
        method = self.method.upper()
        if not method.isalpha():
            msg = "HTTP method must contain only letters"
            raise ValueError(msg)
        if self.max_response_bytes <= 0 or self.timeout_seconds <= 0:
            msg = "fetch limits must be positive"
            raise ValueError(msg)
        object.__setattr__(self, "method", method)
        object.__setattr__(self, "headers", MappingProxyType(dict(self.headers)))
        redirect_hosts = tuple(host.casefold() for host in self.allowed_redirect_hosts)
        if (
            len(set(redirect_hosts)) != len(redirect_hosts)
            or any(not host or "/" in host for host in redirect_hosts)
            or (redirect_hosts and parsed.hostname.casefold() not in redirect_hosts)
        ):
            msg = "redirect hosts must be unique hostnames containing the request host"
            raise ValueError(msg)
        object.__setattr__(self, "allowed_redirect_hosts", redirect_hosts)
        if not isinstance(self.permit_redirects, bool):
            msg = "permit_redirects must be a boolean"
            raise TypeError(msg)
        if self.body is not None:
            object.__setattr__(self, "body", bytes(self.body))


@dataclass(frozen=True, slots=True)
class FetchReceipt:
    """Acquisition receipt that never contains usable response values."""

    status: FetchStatus
    request_sha256: str
    snapshot_ref: SourceSnapshotRef | None
    error_code: str | None = None

    def as_dict(self) -> dict[str, JsonValue]:
        """Serialize receipt without credentials or response bytes."""
        return {
            "status": self.status.value,
            "request_sha256": self.request_sha256,
            "snapshot_ref": None if self.snapshot_ref is None else self.snapshot_ref.as_dict(),
            "error_code": self.error_code,
        }


@dataclass(frozen=True, slots=True)
class DeriveReceipt:
    """Offline transformation receipt; failure never carries a healthy reference."""

    status: DeriveStatus
    code_sha256: str
    dataset_ref: DerivedDatasetRef | None
    error_code: str | None = None

    def as_dict(self) -> dict[str, JsonValue]:
        """Serialize a bounded, non-authoritative derivation receipt."""
        return {
            "status": self.status.value,
            "epistemic_status": "EXPLORATORY",
            "scientific_authority": "NONE_EXPLORATORY_ONLY",
            "code_sha256": self.code_sha256,
            "dataset_ref": None if self.dataset_ref is None else self.dataset_ref.as_dict(),
            "error_code": self.error_code,
        }


@dataclass(frozen=True, slots=True)
class VerificationReceipt:
    """Integrity result for an exact retained ref."""

    ref_uri: str
    healthy: bool
    error_code: str | None

    def as_dict(self) -> dict[str, JsonValue]:
        """Return predictable JSON."""
        return {
            "ref_uri": self.ref_uri,
            "healthy": self.healthy,
            "error_code": self.error_code,
        }


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    """Value-free projection rebuilt from one authoritative manifest."""

    manifest_type: str
    ref_uri: str
    content_sha256: str
    size_bytes: int
    public_locator: str | None = None
    media_type: str | None = None
    input_ref_ids: tuple[str, ...] = ()
    output_sha256: str | None = None
    code_sha256: str | None = None
    runtime_id: str | None = None

    def as_dict(self) -> dict[str, JsonValue]:
        """Return value-free catalog metadata."""
        return {
            "manifest_type": self.manifest_type,
            "ref_uri": self.ref_uri,
            "content_sha256": self.content_sha256,
            "size_bytes": self.size_bytes,
            "public_locator": self.public_locator,
            "media_type": self.media_type,
            "input_ref_ids": list(self.input_ref_ids),
            "output_sha256": self.output_sha256,
            "code_sha256": self.code_sha256,
            "runtime_id": self.runtime_id,
        }


class _PolicyDeniedError(Exception):
    pass


class _OutputLimitError(Exception):
    pass


class _Readable(Protocol):
    def read(self, size: int = -1) -> bytes:
        """Read at most size bytes."""
        ...


class _ResponseHeaders(Protocol):
    def get(self, name: str) -> str | None:
        """Return one response header when present."""
        ...

    def get_content_type(self) -> str:
        """Return the parsed response media type."""
        ...


class _ResponseContext(_Readable, Protocol):
    status: int
    headers: _ResponseHeaders

    def __enter__(self) -> Self:
        """Enter the response context."""
        ...

    def __exit__(self, *args: object) -> None:
        """Close the response context."""
        ...

    def geturl(self) -> str:
        """Return the final response URL."""
        ...


class _RestrictedRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Refuse a redirect before urllib contacts an unapproved host."""

    def __init__(self, allowed_hosts: tuple[str, ...], *, permit_redirects: bool) -> None:
        super().__init__()
        self._allowed_hosts: frozenset[str] = frozenset(allowed_hosts)
        self._permit_redirects: bool = permit_redirects

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
        newurl: str,
    ) -> urllib.request.Request | None:
        """Delegate only same-policy HTTP(S) redirect targets."""
        if not self._permit_redirects:
            return None
        parsed = urllib.parse.urlsplit(newurl)
        if (
            parsed.scheme not in {"http", "https"}
            or parsed.hostname is None
            or parsed.hostname.casefold() not in self._allowed_hosts
        ):
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _open_request(
    raw_request: urllib.request.Request,
    request: FetchRequest,
) -> _ResponseContext:
    if not request.allowed_redirect_hosts and request.permit_redirects:
        return cast(
            "_ResponseContext",
            urllib.request.urlopen(raw_request, timeout=request.timeout_seconds),  # noqa: S310
        )
    opener = urllib.request.build_opener(
        _RestrictedRedirectHandler(
            request.allowed_redirect_hosts,
            permit_redirects=request.permit_redirects,
        )
    )
    return cast(
        "_ResponseContext",
        opener.open(raw_request, timeout=request.timeout_seconds),
    )


def _canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    except (TypeError, ValueError) as error:
        msg = "value must be finite JSON"
        raise ValueError(msg) from error


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _runtime_id() -> str:
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return (
        f"{_WORKER_VERSION}:{platform.python_implementation()}:{python_version}:"
        f"{platform.system()}:{platform.machine()}"
    )


def _sanitize_locator(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or ""
    if ":" in host:
        host = f"[{host}]"
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    safe_query = "query-redacted=true" if parsed.query else ""
    return urllib.parse.urlunsplit((parsed.scheme, host, parsed.path, safe_query, ""))


def _sanitize_parameters(value: JsonValue, *, key: str = "") -> JsonValue:
    if any(marker in key.lower() for marker in _SECRET_MARKERS):
        return {"redacted_sha256": _sha256(_canonical_bytes(value))}
    if isinstance(value, dict):
        return {name: _sanitize_parameters(item, key=name) for name, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_parameters(item) for item in value]
    return value


_SAFE_CALLS: Final[frozenset[str]] = frozenset(
    {
        "abs",
        "all",
        "any",
        "bool",
        "csv_input",
        "dict",
        "emit",
        "enumerate",
        "float",
        "input_bytes",
        "input_text",
        "int",
        "json_input",
        "len",
        "list",
        "max",
        "min",
        "param",
        "range",
        "round",
        "set",
        "sorted",
        "str",
        "sum",
        "tuple",
        "unix_utc_iso",
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


def _validate_transform_source(source: str) -> ast.Module:
    try:
        tree = ast.parse(source, filename="<data-derive>", mode="exec")
    except SyntaxError as error:
        msg = "transformation source is not valid Python"
        raise _PolicyDeniedError(msg) from error
    function_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    allowed_calls = _SAFE_CALLS | function_names
    for node in ast.walk(tree):
        if isinstance(node, _FORBIDDEN_NODES):
            msg = "transformation requests an unavailable host interface"
            raise _PolicyDeniedError(msg)
        if isinstance(node, ast.Name) and "__" in node.id:
            msg = "transformation requests an unavailable runtime interface"
            raise _PolicyDeniedError(msg)
        if isinstance(node, ast.Call) and (
            not isinstance(node.func, ast.Name) or node.func.id not in allowed_calls
        ):
            msg = "transformation calls an unavailable runtime interface"
            raise _PolicyDeniedError(msg)
    return tree


def _derive_worker(
    connection: Connection,
    source: str,
    inputs: dict[str, bytes],
    parameters: dict[str, JsonValue],
    max_output_bytes: int,
    max_memory_bytes: int,
) -> None:
    resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))
    accessed_aliases: list[str] = []

    def _input(alias: str) -> bytes:
        try:
            content = inputs[alias]
        except KeyError as error:
            msg = "transformation requested an undeclared input alias"
            raise PermissionError(msg) from error
        accessed_aliases.append(alias)
        return content

    def input_bytes(alias: str) -> tuple[int, ...]:
        return tuple(_input(alias))

    def input_text(alias: str) -> str:
        return _input(alias).decode("utf-8")

    def json_input(alias: str) -> JsonValue:
        return cast("JsonValue", json.loads(input_text(alias)))

    def csv_input(alias: str) -> list[list[str]]:
        return list(csv.reader(io.StringIO(input_text(alias))))

    def param(name: str) -> JsonValue:
        try:
            return parameters[name]
        except KeyError as error:
            msg = "transformation requested an undeclared parameter"
            raise PermissionError(msg) from error

    def emit(value: JsonValue) -> JsonValue:
        return value

    def unix_utc_iso(value: object) -> str:
        if isinstance(value, bool) or not isinstance(value, int | float):
            msg = "Unix timestamp must be numeric"
            raise TypeError(msg)
        return datetime.fromtimestamp(value, tz=UTC).isoformat()

    namespace: dict[str, object] = {
        "__builtins__": _SAFE_BUILTINS,
        "input_bytes": input_bytes,
        "input_text": input_text,
        "json_input": json_input,
        "csv_input": csv_input,
        "param": param,
        "emit": emit,
        "unix_utc_iso": unix_utc_iso,
    }
    try:
        tree = _validate_transform_source(source)
        exec(compile(tree, "<data-derive>", "exec"), namespace)  # noqa: S102
        if "result" not in namespace:
            msg = "transformation must assign result = emit(...)"
            raise ValueError(msg)
        output = _canonical_bytes(namespace["result"])
        if len(output) > max_output_bytes:
            raise _OutputLimitError
        connection.send({"kind": "success", "output": output, "accessed_aliases": accessed_aliases})
    except _PolicyDeniedError:
        connection.send({"kind": "denied"})
    except BaseException as error:  # noqa: BLE001
        connection.send({"kind": "failed", "error_type": type(error).__name__})
    finally:
        connection.close()


class DataWorkspace:
    """Append-only manifests plus immutable objects with a rebuildable memory index."""

    def __init__(self, root: Path = Path("/data")) -> None:
        """Open or create one local workspace and rebuild its non-authoritative catalog."""
        self.root = root.absolute()
        self._lock = threading.RLock()
        self._catalog: dict[str, CatalogEntry] = {}
        self._prepare_layout()
        self.rebuild_catalog()

    def fetch(self, request: FetchRequest) -> FetchReceipt:
        """Acquire bounded HTTP bytes, retain and verify them, then return a value-free ref."""
        request_sha256 = self._request_sha256(request)
        raw_request = urllib.request.Request(  # noqa: S310
            request.url,
            data=request.body,
            headers=dict(request.headers),
            method=request.method,
        )
        try:
            response_context = _open_request(raw_request, request)
            with response_context as response:
                final_url = cast("str", response.geturl())
                if urllib.parse.urlsplit(final_url).scheme not in {"http", "https"}:
                    return self._failed_fetch(request_sha256, "UNSUPPORTED_REDIRECT_SCHEME")
                declared_size = response.headers.get("Content-Length")
                if declared_size is not None and int(declared_size) > request.max_response_bytes:
                    return self._failed_fetch(request_sha256, "RESPONSE_TOO_LARGE")
                content = self._bounded_read(response, request.max_response_bytes)
                status = int(getattr(response, "status", 200))
                media_type = response.headers.get_content_type()
        except _OutputLimitError:
            return self._failed_fetch(request_sha256, "RESPONSE_TOO_LARGE")
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError):
            return self._failed_fetch(request_sha256, "HTTP_ACQUISITION_FAILED")

        digest = _sha256(content)
        identity_payload = {
            "schema_version": _SCHEMA_VERSION,
            "manifest_type": "source_snapshot",
            "request_sha256": request_sha256,
            "content_sha256": digest,
            "size_bytes": len(content),
        }
        snapshot_id = _sha256(_canonical_bytes(identity_payload))
        ref = SourceSnapshotRef(snapshot_id, digest, len(content))
        manifest: dict[str, object] = {
            **identity_payload,
            "snapshot_id": snapshot_id,
            "ref_uri": ref.uri,
            "public_locator": _sanitize_locator(final_url),
            "method": request.method,
            "request_header_names": sorted(name.lower() for name in request.headers),
            "request_body_sha256": None if request.body is None else _sha256(request.body),
            "request_body_size": 0 if request.body is None else len(request.body),
            "allowed_redirect_hosts": list(request.allowed_redirect_hosts),
            "permit_redirects": request.permit_redirects,
            "response_status": status,
            "media_type": media_type,
            "retained_at": datetime.now(UTC).isoformat(),
        }
        try:
            self._publish_object(digest, content)
            self._publish_manifest("source", snapshot_id, manifest)
            verification = self.verify(ref)
        except (OSError, ValueError):
            return self._failed_fetch(request_sha256, "PUBLICATION_FAILED")
        if not verification.healthy:
            return self._failed_fetch(request_sha256, verification.error_code or "VERIFY_FAILED")
        with self._lock:
            self._catalog[ref.uri] = self._entry_from_manifest(manifest)
        return FetchReceipt(FetchStatus.SUCCEEDED, request_sha256, ref)

    def derive(
        self,
        *,
        inputs: Mapping[str, SourceSnapshotRef | DerivedDatasetRef],
        source: str,
        parameters: Mapping[str, JsonValue],
        wall_time_seconds: float = _DEFAULT_WALL_SECONDS,
        max_output_bytes: int = _DEFAULT_MAX_OUTPUT_BYTES,
        max_memory_bytes: int = _DEFAULT_MEMORY_BYTES,
    ) -> DeriveReceipt:
        """Run authored transformation code offline over exact verified retained inputs."""
        code_bytes = source.encode()
        code_sha256 = _sha256(code_bytes)
        provided_ref_ids = tuple(inputs[alias].uri for alias in sorted(inputs))
        if not inputs:
            return self._failed_derive(code_sha256, "INPUT_REFERENCE_REQUIRED", denied=True)
        if (
            len(code_bytes) > _DEFAULT_MAX_CODE_BYTES
            or wall_time_seconds <= 0
            or max_output_bytes <= 0
            or max_memory_bytes <= 0
        ):
            return self._failed_derive(
                code_sha256,
                "TRANSFORMATION_POLICY_DENIED",
                denied=True,
                input_ref_ids=provided_ref_ids,
            )

        canonical_parameters = dict(parameters)
        try:
            parameters_bytes = _canonical_bytes(canonical_parameters)
        except ValueError:
            return self._failed_derive(
                code_sha256, "INVALID_PARAMETERS", input_ref_ids=provided_ref_ids
            )
        parameters_sha256 = _sha256(parameters_bytes)
        try:
            _validate_transform_source(source)
        except _PolicyDeniedError:
            return self._failed_derive(
                code_sha256,
                "TRANSFORMATION_POLICY_DENIED",
                denied=True,
                input_ref_ids=provided_ref_ids,
                parameters_sha256=parameters_sha256,
            )
        input_bytes: dict[str, bytes] = {}
        bindings: list[dict[str, str]] = []
        for alias in sorted(inputs):
            ref = inputs[alias]
            try:
                retained_ref = self.resolve(ref.uri)
            except (KeyError, OSError, ValueError):
                retained_ref = None
            if not alias or retained_ref != ref or not self.verify(ref).healthy:
                return self._failed_derive(
                    code_sha256,
                    "UNVERIFIED_INPUT_REFERENCE",
                    input_ref_ids=provided_ref_ids,
                    parameters_sha256=parameters_sha256,
                )
            input_bytes[alias] = self._read_object(self._content_digest(ref))
            bindings.append({"alias": alias, "ref_uri": ref.uri})
        input_ref_ids = tuple(binding["ref_uri"] for binding in bindings)

        context = multiprocessing.get_context("spawn")
        receive, send = context.Pipe(duplex=False)
        process = context.Process(
            target=_derive_worker,
            args=(
                send,
                source,
                input_bytes,
                canonical_parameters,
                max_output_bytes,
                max_memory_bytes,
            ),
        )
        process.start()
        send.close()
        # Drain a bounded worker message before joining. A successful derived dataset can
        # exceed the OS pipe buffer; joining first would leave the child blocked in send()
        # while the parent waits for that child to exit.
        if not receive.poll(wall_time_seconds):
            timed_out = process.is_alive()
            if timed_out:
                process.terminate()
            process.join()
            receive.close()
            error_code = "TRANSFORMATION_TIMEOUT" if timed_out else "TRANSFORMATION_WORKER_FAILED"
            return self._failed_derive(
                code_sha256,
                error_code,
                input_ref_ids=input_ref_ids,
                parameters_sha256=parameters_sha256,
            )
        try:
            worker_result: dict[str, object] | None = cast("dict[str, object]", receive.recv())
        except EOFError:
            worker_result = None
        receive.close()
        process.join()
        if worker_result is None:
            return self._failed_derive(
                code_sha256,
                "TRANSFORMATION_WORKER_FAILED",
                input_ref_ids=input_ref_ids,
                parameters_sha256=parameters_sha256,
            )
        if worker_result.get("kind") == "denied":
            return self._failed_derive(
                code_sha256,
                "TRANSFORMATION_POLICY_DENIED",
                denied=True,
                input_ref_ids=input_ref_ids,
                parameters_sha256=parameters_sha256,
            )
        if worker_result.get("kind") != "success":
            error_type = cast("str", worker_result.get("error_type", "Unknown"))
            return self._failed_derive(
                code_sha256,
                f"TRANSFORMATION_FAILED_{error_type.upper()}",
                input_ref_ids=input_ref_ids,
                parameters_sha256=parameters_sha256,
            )
        accessed_aliases = worker_result.get("accessed_aliases")
        if not isinstance(accessed_aliases, list) or set(
            cast("list[object]", accessed_aliases)
        ) != set(inputs):
            return self._failed_derive(
                code_sha256,
                "TRANSFORMATION_DID_NOT_USE_DECLARED_INPUTS",
                input_ref_ids=input_ref_ids,
                parameters_sha256=parameters_sha256,
            )

        output = cast("bytes", worker_result["output"])
        output_sha256 = _sha256(output)
        runtime_id = _runtime_id()
        identity_payload = {
            "schema_version": _SCHEMA_VERSION,
            "manifest_type": "derived_dataset",
            "input_bindings": bindings,
            "code_sha256": code_sha256,
            "parameters_sha256": parameters_sha256,
            "runtime_id": runtime_id,
            "output_sha256": output_sha256,
            "size_bytes": len(output),
        }
        dataset_id = _sha256(_canonical_bytes(identity_payload))
        ref = DerivedDatasetRef(
            dataset_id=dataset_id,
            output_sha256=output_sha256,
            size_bytes=len(output),
            code_sha256=code_sha256,
            input_ref_ids=input_ref_ids,
            parameters_sha256=parameters_sha256,
            runtime_id=runtime_id,
        )
        manifest: dict[str, object] = {
            **identity_payload,
            "dataset_id": dataset_id,
            "ref_uri": ref.uri,
            "input_ref_ids": list(input_ref_ids),
            "parameters": _sanitize_parameters(canonical_parameters),
            "epistemic_status": "EXPLORATORY",
            "scientific_authority": "NONE_EXPLORATORY_ONLY",
        }
        try:
            self._publish_object(code_sha256, code_bytes)
            self._publish_object(output_sha256, output)
            self._publish_manifest("derived", dataset_id, manifest)
            verification = self.verify(ref)
        except (OSError, ValueError):
            return self._failed_derive(
                code_sha256,
                "PUBLICATION_FAILED",
                input_ref_ids=input_ref_ids,
                parameters_sha256=parameters_sha256,
            )
        if not verification.healthy:
            return self._failed_derive(
                code_sha256,
                verification.error_code or "VERIFY_FAILED",
                input_ref_ids=input_ref_ids,
                parameters_sha256=parameters_sha256,
            )
        with self._lock:
            self._catalog[ref.uri] = self._entry_from_manifest(manifest)
        return DeriveReceipt(DeriveStatus.SUCCEEDED, code_sha256, ref)

    def verify(self, ref: SourceSnapshotRef | DerivedDatasetRef) -> VerificationReceipt:
        """Verify manifest identity and every consequential content object."""
        try:
            manifest = self._manifest_for_ref(ref)
            stored_ref = self._ref_from_manifest(manifest)
            if stored_ref != ref or not self._manifest_identity_is_valid(manifest, stored_ref):
                return VerificationReceipt(ref.uri, False, "REFERENCE_MANIFEST_MISMATCH")
            content = self._read_object(self._content_digest(ref))
            if _sha256(content) != self._content_digest(ref) or len(content) != ref.size_bytes:
                return VerificationReceipt(ref.uri, False, "CONTENT_DIGEST_MISMATCH")
            if isinstance(ref, DerivedDatasetRef):
                code = self._read_object(ref.code_sha256)
                if _sha256(code) != ref.code_sha256:
                    return VerificationReceipt(ref.uri, False, "CODE_DIGEST_MISMATCH")
                for input_uri in ref.input_ref_ids:
                    input_ref = self.resolve(input_uri)
                    if not self.verify(input_ref).healthy:
                        return VerificationReceipt(ref.uri, False, "INPUT_REFERENCE_UNHEALTHY")
        except (KeyError, OSError, ValueError, TypeError, json.JSONDecodeError):
            return VerificationReceipt(ref.uri, False, "MISSING_OR_INVALID_MANIFEST")
        return VerificationReceipt(ref.uri, True, None)

    def inspect(self, ref: SourceSnapshotRef | DerivedDatasetRef) -> CatalogEntry:
        """Return value-free metadata for an exact retained ref."""
        if not self.verify(ref).healthy:
            msg = "cannot inspect an unverified data reference"
            raise ValueError(msg)
        return self._entry_from_manifest(self._manifest_for_ref(ref))

    def search(self, query: str) -> tuple[CatalogEntry, ...]:
        """Search the rebuildable value-free catalog deterministically."""
        needle = query.casefold()
        with self._lock:
            entries = tuple(self._catalog.values())
        return tuple(
            sorted(
                (
                    entry
                    for entry in entries
                    if needle in _canonical_bytes(entry.as_dict()).decode().casefold()
                ),
                key=lambda entry: entry.ref_uri,
            )
        )

    def resolve(self, ref_uri: str) -> SourceSnapshotRef | DerivedDatasetRef:
        """Resolve an exact URI through authoritative manifests, never path coincidence."""
        kind, separator, identity = ref_uri.partition(":")
        if separator != ":" or kind not in {"source", "derived"} or len(identity) != 2**6:
            raise KeyError(ref_uri)
        directory = "source" if kind == "source" else "derived"
        manifest = self._read_manifest(directory, identity)
        ref = self._ref_from_manifest(manifest)
        if ref.uri != ref_uri:
            raise ValueError("manifest reference identity mismatch")
        return ref

    def rebuild_catalog(self) -> int:
        """Discard and reconstruct the non-authoritative index from append-only manifests."""
        rebuilt: dict[str, CatalogEntry] = {}
        for directory in ("source", "derived"):
            manifest_dir = self.root / "manifests" / directory
            self._require_workspace_directory_chain(manifest_dir)
            for path in sorted(manifest_dir.glob("*.json")):
                manifest = self._read_regular_json(path)
                ref = self._ref_from_manifest(manifest)
                if not self._manifest_identity_is_valid(manifest, ref):
                    raise ValueError("manifest identity does not match canonical content")
                rebuilt[ref.uri] = self._entry_from_manifest(manifest)
        with self._lock:
            self._catalog = rebuilt
        return len(rebuilt)

    def authorized_json_view(
        self,
        ref: DerivedDatasetRef,
        *,
        view_id: str,
        environment_ref: str,
    ) -> AuthorizedDataView:
        """Adapt only verified retained column JSON into the existing scoped view type."""
        try:
            retained = self.resolve(ref.uri)
        except (KeyError, OSError, ValueError):
            retained = None
        if retained != ref or not self.verify(ref).healthy:
            msg = "authorized view requires a verified retained derived dataset"
            raise ValueError(msg)
        raw = cast("object", json.loads(self._read_object(ref.output_sha256)))
        if not isinstance(raw, dict):
            msg = "authorized view requires a JSON object of column arrays"
            raise ValueError(msg)
        fields: dict[str, tuple[JsonValue, ...]] = {}
        for field_id, values in cast("dict[object, object]", raw).items():
            if not isinstance(field_id, str) or not isinstance(values, list):
                msg = "authorized view requires string fields and array values"
                raise ValueError(msg)
            fields[field_id] = tuple(cast("list[JsonValue]", values))
        from research_agent.exploration import AuthorizedDataView  # noqa: PLC0415

        return AuthorizedDataView(
            view_id=view_id,
            dataset_ref=ref.uri,
            environment_ref=environment_ref,
            fields=fields,
            protected=False,
        )

    def read_derived_json(self, ref: DerivedDatasetRef) -> JsonValue:
        """Return a detached JSON value only after exact retained-reference verification.

        This is a storage-integrity seam, not scientific registration.  Callers still need an
        independently configured semantic authority before these values may enter the time-series
        kernel.
        """
        try:
            retained = self.resolve(ref.uri)
        except (KeyError, OSError, ValueError):
            retained = None
        if retained != ref or not self.verify(ref).healthy:
            msg = "derived JSON read requires an exact verified retained reference"
            raise ValueError(msg)
        value = json.loads(self._read_object(ref.output_sha256))
        return cast("JsonValue", value)

    def _prepare_layout(self) -> None:
        current = self.root
        current.mkdir(parents=True, exist_ok=True)
        self._require_directory(current)
        for relative in (
            Path("objects"),
            Path("manifests"),
            Path("manifests/source"),
            Path("manifests/derived"),
            Path("attempts"),
            Path("attempts/fetch"),
            Path("attempts/derive"),
        ):
            path = self.root / relative
            path.mkdir(parents=True, exist_ok=True)
            self._require_directory(path)

    @staticmethod
    def _require_directory(path: Path) -> None:
        mode = path.lstat().st_mode
        if not stat.S_ISDIR(mode) or path.is_symlink():
            msg = f"workspace component is not a real directory: {path.name}"
            raise ValueError(msg)

    @staticmethod
    def _bounded_read(response: object, limit: int) -> bytes:
        reader = cast("_Readable", response)
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = reader.read(min(64 * 1024, limit - total + 1))
            if not chunk:
                break
            total += len(chunk)
            if total > limit:
                raise _OutputLimitError
            chunks.append(chunk)
        return b"".join(chunks)

    @staticmethod
    def _request_sha256(request: FetchRequest) -> str:
        exact = {
            "method": request.method,
            "url": request.url,
            "headers": sorted(request.headers.items()),
            "body_sha256": None if request.body is None else _sha256(request.body),
            "body_size": 0 if request.body is None else len(request.body),
            "allowed_redirect_hosts": list(request.allowed_redirect_hosts),
            "permit_redirects": request.permit_redirects,
        }
        return _sha256(_canonical_bytes(exact))

    def _failed_fetch(self, request_sha256: str, error_code: str) -> FetchReceipt:
        attempt = {
            "schema_version": _SCHEMA_VERSION,
            "attempt_type": "fetch",
            "status": "failed",
            "request_sha256": request_sha256,
            "error_code": error_code,
        }
        attempt_id = _sha256(_canonical_bytes(attempt))
        with contextlib.suppress(OSError, ValueError):
            self._publish_json(self.root / "attempts" / "fetch" / f"{attempt_id}.json", attempt)
        return FetchReceipt(FetchStatus.FAILED, request_sha256, None, error_code)

    def _failed_derive(
        self,
        code_sha256: str,
        error_code: str,
        *,
        denied: bool = False,
        input_ref_ids: tuple[str, ...] = (),
        parameters_sha256: str | None = None,
    ) -> DeriveReceipt:
        attempt = {
            "schema_version": _SCHEMA_VERSION,
            "attempt_type": "derive",
            "status": "denied" if denied else "failed",
            "code_sha256": code_sha256,
            "input_ref_ids": list(input_ref_ids),
            "parameters_sha256": parameters_sha256,
            "runtime_id": _runtime_id(),
            "error_code": error_code,
        }
        attempt_id = _sha256(_canonical_bytes(attempt))
        with contextlib.suppress(OSError, ValueError):
            self._publish_json(self.root / "attempts" / "derive" / f"{attempt_id}.json", attempt)
        return DeriveReceipt(
            DeriveStatus.DENIED if denied else DeriveStatus.FAILED,
            code_sha256,
            None,
            error_code,
        )

    def _publish_object(self, digest: str, content: bytes) -> None:
        if _sha256(content) != digest:
            raise ValueError("object digest does not match content")
        self._publish_bytes(self.root / "objects" / digest, content)

    def _publish_manifest(self, directory: str, identity: str, manifest: dict[str, object]) -> None:
        path = self.root / "manifests" / directory / f"{identity}.json"
        self._require_workspace_directory_chain(path.parent)
        if path.exists():
            existing = self._read_regular_json(path)
            existing_ref = self._ref_from_manifest(existing)
            candidate_ref = self._ref_from_manifest(manifest)
            if (
                existing_ref != candidate_ref
                or not self._manifest_identity_is_valid(existing, existing_ref)
                or not self._manifest_identity_is_valid(manifest, candidate_ref)
            ):
                raise ValueError("immutable manifest conflict")
            return
        self._publish_json(path, manifest)
        published = self._read_regular_json(path)
        published_ref = self._ref_from_manifest(published)
        candidate_ref = self._ref_from_manifest(manifest)
        if published_ref != candidate_ref or not self._manifest_identity_is_valid(
            published, published_ref
        ):
            raise ValueError("atomic manifest publication conflict")

    def _publish_json(self, path: Path, value: object) -> None:
        self._publish_bytes(path, _canonical_bytes(value) + b"\n")

    def _publish_bytes(self, path: Path, content: bytes) -> None:
        self._require_workspace_directory_chain(path.parent)
        suffix = f".{os.getpid()}.{threading.get_ident()}.tmp"
        temporary = path.with_name(path.name + suffix)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(temporary, flags, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, path)
            except FileExistsError:
                existing = self._read_regular(path)
                if existing != content and path.parent.name not in {"source", "derived"}:
                    raise ValueError("immutable content conflict") from None
        finally:
            with contextlib.suppress(FileNotFoundError):
                temporary.unlink()

    def _read_object(self, digest: str) -> bytes:
        self._require_workspace_directory_chain(self.root / "objects")
        return self._read_regular(self.root / "objects" / digest)

    @staticmethod
    def _read_regular(path: Path) -> bytes:
        mode = path.lstat().st_mode
        if not stat.S_ISREG(mode) or path.is_symlink():
            raise ValueError("workspace entry is not a regular file")
        return path.read_bytes()

    def _read_regular_json(self, path: Path) -> dict[str, object]:
        raw = json.loads(self._read_regular(path))
        if not isinstance(raw, dict):
            raise ValueError("manifest is not a JSON object")
        return cast("dict[str, object]", raw)

    def _read_manifest(self, directory: str, identity: str) -> dict[str, object]:
        self._require_workspace_directory_chain(self.root / "manifests" / directory)
        return self._read_regular_json(self.root / "manifests" / directory / f"{identity}.json")

    def _require_workspace_directory_chain(self, path: Path) -> None:
        self._require_directory(self.root)
        try:
            relative = path.relative_to(self.root)
        except ValueError as error:
            msg = "workspace publication path escaped its root"
            raise ValueError(msg) from error
        current = self.root
        for part in relative.parts:
            current = current / part
            self._require_directory(current)

    def _manifest_for_ref(self, ref: SourceSnapshotRef | DerivedDatasetRef) -> dict[str, object]:
        if isinstance(ref, SourceSnapshotRef):
            return self._read_manifest("source", ref.snapshot_id)
        return self._read_manifest("derived", ref.dataset_id)

    @staticmethod
    def _content_digest(ref: SourceSnapshotRef | DerivedDatasetRef) -> str:
        if isinstance(ref, SourceSnapshotRef):
            return ref.content_sha256
        return ref.output_sha256

    @staticmethod
    def _ref_from_manifest(manifest: Mapping[str, object]) -> SourceSnapshotRef | DerivedDatasetRef:
        manifest_type = manifest.get("manifest_type")
        if manifest_type == "source_snapshot":
            return SourceSnapshotRef(
                snapshot_id=cast("str", manifest["snapshot_id"]),
                content_sha256=cast("str", manifest["content_sha256"]),
                size_bytes=cast("int", manifest["size_bytes"]),
            )
        if manifest_type == "derived_dataset":
            return DerivedDatasetRef(
                dataset_id=cast("str", manifest["dataset_id"]),
                output_sha256=cast("str", manifest["output_sha256"]),
                size_bytes=cast("int", manifest["size_bytes"]),
                code_sha256=cast("str", manifest["code_sha256"]),
                input_ref_ids=tuple(cast("list[str]", manifest["input_ref_ids"])),
                parameters_sha256=cast("str", manifest["parameters_sha256"]),
                runtime_id=cast("str", manifest["runtime_id"]),
            )
        raise ValueError("unknown manifest type")

    @staticmethod
    def _entry_from_manifest(manifest: Mapping[str, object]) -> CatalogEntry:
        manifest_type = cast("str", manifest["manifest_type"])
        output_sha256 = cast("str | None", manifest.get("output_sha256"))
        return CatalogEntry(
            manifest_type=manifest_type,
            ref_uri=cast("str", manifest["ref_uri"]),
            content_sha256=cast("str", manifest.get("content_sha256", output_sha256 or "")),
            size_bytes=cast("int", manifest["size_bytes"]),
            public_locator=cast("str | None", manifest.get("public_locator")),
            media_type=cast("str | None", manifest.get("media_type")),
            input_ref_ids=tuple(cast("list[str]", manifest.get("input_ref_ids", []))),
            output_sha256=output_sha256,
            code_sha256=cast("str | None", manifest.get("code_sha256")),
            runtime_id=cast("str | None", manifest.get("runtime_id")),
        )

    @staticmethod
    def _manifest_identity_is_valid(
        manifest: Mapping[str, object], ref: SourceSnapshotRef | DerivedDatasetRef
    ) -> bool:
        if isinstance(ref, SourceSnapshotRef):
            identity_payload = {
                "schema_version": manifest.get("schema_version"),
                "manifest_type": manifest.get("manifest_type"),
                "request_sha256": manifest.get("request_sha256"),
                "content_sha256": manifest.get("content_sha256"),
                "size_bytes": manifest.get("size_bytes"),
            }
            return _sha256(_canonical_bytes(identity_payload)) == ref.snapshot_id
        raw_bindings = manifest.get("input_bindings")
        if not isinstance(raw_bindings, list):
            return False
        raw_input_ref_ids = manifest.get("input_ref_ids")
        if not isinstance(raw_input_ref_ids, list):
            return False
        input_objects = cast("list[object]", raw_input_ref_ids)
        if not all(isinstance(item, str) for item in input_objects):
            return False
        input_ref_ids = cast("list[str]", input_objects)
        bindings: list[dict[str, str]] = []
        for raw_binding in cast("list[object]", raw_bindings):
            if not isinstance(raw_binding, dict):
                return False
            binding = cast("dict[object, object]", raw_binding)
            if set(binding) != {"alias", "ref_uri"}:
                return False
            alias = binding["alias"]
            ref_uri = binding["ref_uri"]
            if not isinstance(alias, str) or not isinstance(ref_uri, str):
                return False
            bindings.append({"alias": alias, "ref_uri": ref_uri})
        if [binding["ref_uri"] for binding in bindings] != input_ref_ids:
            return False
        identity_payload = {
            "schema_version": manifest.get("schema_version"),
            "manifest_type": manifest.get("manifest_type"),
            "input_bindings": bindings,
            "code_sha256": manifest.get("code_sha256"),
            "parameters_sha256": manifest.get("parameters_sha256"),
            "runtime_id": manifest.get("runtime_id"),
            "output_sha256": manifest.get("output_sha256"),
            "size_bytes": manifest.get("size_bytes"),
        }
        return _sha256(_canonical_bytes(identity_payload)) == ref.dataset_id


__all__ = [
    "CatalogEntry",
    "DataWorkspace",
    "DeriveReceipt",
    "DeriveStatus",
    "DerivedDatasetRef",
    "FetchReceipt",
    "FetchRequest",
    "FetchStatus",
    "SourceSnapshotRef",
    "VerificationReceipt",
]
