"""Replaceable model-provider boundaries and adapters."""

# ruff: noqa: EM101, TRY003

from __future__ import annotations

import http.client
import json
import math
import os
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from threading import Lock
from types import MappingProxyType
from typing import TYPE_CHECKING, Protocol, cast
from uuid import uuid4

from research_agent.runtime._canonical import canonical_bytes, canonical_value, freeze_mapping

if TYPE_CHECKING:
    from research_agent.runtime.models import ContextPacket

_ACTION_TOOL_NAME = "submit_research_action"
_MAX_PROVIDER_ATTEMPTS = 10
_HTTP_OK_MIN = 200
_HTTP_OK_MAX = 299
_HTTP_RATE_LIMITED = 429
_HTTP_SERVER_ERROR_MIN = 500
_HTTP_SERVER_ERROR_MAX = 599
_MAX_RESPONSE_NESTING = 256
_ASCII_CONTROL_END = 32
_ASCII_DELETE = 127
_VISIBLE_ASCII_MIN = 33
_VISIBLE_ASCII_MAX = 126


class ProviderUnavailableError(RuntimeError):
    """Recoverable provider operation failure."""


class ProviderAuthenticationError(ProviderUnavailableError):
    """Provider authentication was absent or rejected and must not be retried."""


class ProviderRequestError(ValueError):
    """The configured request is invalid or permanently rejected."""


class ProviderResponseError(ValueError):
    """Provider output cannot be normalized without inventing intent."""


class TransportFailureKind(Enum):
    """Failure classes declared by a replaceable HTTP transport."""

    TRANSIENT = "transient"
    AUTHENTICATION = "authentication"
    PERMANENT = "permanent"
    INVALID_RESPONSE = "invalid_response"


class HttpTransportError(RuntimeError):
    """Transport failure detached from a native HTTP client."""

    def __init__(self, kind: TransportFailureKind, message: str) -> None:
        """Record a safe failure class and message without native objects."""
        super().__init__(message)
        self.kind = kind


@dataclass(frozen=True, slots=True)
class ModelResponse:
    """Provider-neutral normalized model response."""

    message: str
    action: Mapping[str, object]
    provider_metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        """Detach and freeze untrusted provider mappings after acceptance."""
        object.__setattr__(self, "action", freeze_mapping(self.action))
        object.__setattr__(self, "provider_metadata", freeze_mapping(self.provider_metadata))


class ModelProvider(Protocol):
    """Neutral intelligence interface consumed by the runtime."""

    def complete(self, packet: ContextPacket) -> ModelResponse:
        """Return one normalized decision for the supplied packet."""
        ...


class _RedactedHeaders(Mapping[str, str]):
    """Transport-readable headers whose representation hides credentials."""

    def __init__(self, values: Mapping[str, str], sensitive_names: frozenset[str]) -> None:
        self._values = dict(values)
        self._sensitive_names = frozenset(name.lower() for name in sensitive_names)

    def __getitem__(self, key: str) -> str:
        return self._values[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __repr__(self) -> str:
        safe = {
            key: "<redacted>" if key.lower() in self._sensitive_names else value
            for key, value in self._values.items()
        }
        return repr(safe)


@dataclass(frozen=True, slots=True, repr=False)
class HttpRequest:
    """Provider-private HTTP request consumed only by a transport."""

    url: str
    headers: Mapping[str, str]
    body: bytes
    timeout_seconds: float
    logical_request_id: str
    max_response_bytes: int

    def __repr__(self) -> str:
        """Expose safe diagnostics without body or credential values."""
        return (
            "HttpRequest("
            f"url={self.url!r}, header_names={tuple(self.headers)!r}, "
            f"body_bytes={len(self.body)}, timeout_seconds={self.timeout_seconds!r}, "
            f"logical_request_id={self.logical_request_id!r}, "
            f"max_response_bytes={self.max_response_bytes!r})"
        )


@dataclass(frozen=True, slots=True, repr=False)
class HttpResponse:
    """Provider-private complete HTTP response."""

    status_code: int
    body: bytes

    def __repr__(self) -> str:
        """Expose only bounded diagnostics, never native response content."""
        return f"HttpResponse(status_code={self.status_code!r}, body_bytes={len(self.body)})"


class HttpTransport(Protocol):
    """Minimal replaceable HTTP transport with no scientific authority."""

    def send(self, request: HttpRequest) -> HttpResponse:
        """Send one complete request and return one complete response."""
        ...


class SecretResolver(Protocol):
    """Resolve a credential inside the provider adapter boundary."""

    def resolve(self, secret_ref: str) -> str:
        """Return the secret for one operational reference."""
        ...


class EnvironmentSecretResolver:
    """Resolve provider credentials from process environment variables."""

    def resolve(self, secret_ref: str) -> str:
        """Fail explicitly when the configured secret is absent."""
        value = os.environ.get(secret_ref)
        if value is None or not value.strip():
            raise ProviderAuthenticationError("Configured provider credential is unavailable.")
        return value


class UrllibHttpTransport:
    """Standard-library transport for complete JSON requests."""

    def send(self, request: HttpRequest) -> HttpResponse:
        """POST once while bounding reads and neutralizing native failures."""
        outcome = self._send_native(request)
        if isinstance(outcome, HttpResponse):
            return outcome
        if outcome is TransportFailureKind.INVALID_RESPONSE:
            raise HttpTransportError(outcome, "Provider response exceeded its byte bound.")
        if outcome is TransportFailureKind.PERMANENT:
            raise HttpTransportError(outcome, "Provider transport configuration was invalid.")
        raise HttpTransportError(outcome, "Provider transport did not complete.")

    @staticmethod
    def _send_native(request: HttpRequest) -> HttpResponse | TransportFailureKind:
        """Keep native exceptions inside this frame and return only safe facts."""
        invalid_configuration = False
        transient_failure = False
        invalid_response = False
        result: HttpResponse | None = None
        try:
            native_request = urllib.request.Request(  # noqa: S310
                request.url,
                data=request.body,
                headers=dict(request.headers),
                method="POST",
            )
            try:
                with urllib.request.urlopen(  # noqa: S310
                    native_request,
                    timeout=request.timeout_seconds,
                ) as response:
                    body = response.read(request.max_response_bytes + 1)
                    if len(body) > request.max_response_bytes:
                        invalid_response = True
                    else:
                        result = HttpResponse(response.status, body)
            except urllib.error.HTTPError as error:
                body = error.read(request.max_response_bytes + 1)
                if len(body) > request.max_response_bytes:
                    invalid_response = True
                else:
                    result = HttpResponse(error.code, body)
        except ValueError:
            invalid_configuration = True
        except (TimeoutError, urllib.error.URLError, http.client.HTTPException, OSError):
            transient_failure = True
        if result is not None:
            return result
        if invalid_response:
            return TransportFailureKind.INVALID_RESPONSE
        if invalid_configuration:
            return TransportFailureKind.PERMANENT
        if transient_failure:
            return TransportFailureKind.TRANSIENT
        return TransportFailureKind.PERMANENT


@dataclass(frozen=True, slots=True)
class OpenAICompatibleProviderConfig:
    """Explicit non-secret configuration for a compatible JSON endpoint."""

    base_url: str
    model: str
    api_key_secret_ref: str
    timeout_seconds: float = 60.0
    max_attempts: int = 3
    max_request_bytes: int = 1_000_000
    max_response_bytes: int = 1_000_000
    max_response_nesting: int = 64

    def __post_init__(self) -> None:
        """Reject ambiguous or unbounded operational configuration."""
        if any(
            ord(character) < _ASCII_CONTROL_END or ord(character) == _ASCII_DELETE
            for character in self.base_url
        ):
            raise ValueError("base_url must be a safe explicit HTTP(S) URL.")
        parsed = urllib.parse.urlsplit(self.base_url)
        if (
            parsed.scheme not in {"https", "http"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("base_url must contain only an HTTP(S) host, optional port, and path.")
        if not self.model.strip():
            raise ValueError("model must be explicit and non-empty.")
        if not self.api_key_secret_ref.strip():
            raise ValueError("api_key_secret_ref must be non-empty.")
        if (
            isinstance(self.timeout_seconds, bool)
            or not math.isfinite(self.timeout_seconds)
            or self.timeout_seconds <= 0
        ):
            raise ValueError("timeout_seconds must be positive and finite.")
        if (
            type(self.max_attempts) is not int
            or not 1 <= self.max_attempts <= _MAX_PROVIDER_ATTEMPTS
        ):
            raise ValueError("max_attempts must be between 1 and 10.")
        if type(self.max_request_bytes) is not int or self.max_request_bytes < 1:
            raise ValueError("max_request_bytes must be positive.")
        if type(self.max_response_bytes) is not int or self.max_response_bytes < 1:
            raise ValueError("max_response_bytes must be positive.")
        if (
            type(self.max_response_nesting) is not int
            or not 1 <= self.max_response_nesting <= _MAX_RESPONSE_NESTING
        ):
            raise ValueError("max_response_nesting must be between 1 and 256.")

    @property
    def endpoint(self) -> str:
        """Return the compatible chat-completions endpoint."""
        return f"{self.base_url.rstrip('/')}/chat/completions"


def action_json_schema() -> Mapping[str, object]:
    """Return the exact provider-facing schema for runtime actions."""
    identity: dict[str, object] = {
        "action_id": {"type": "string", "minLength": 1},
        "session_id": {"type": "string", "minLength": 1},
        "episode_id": {"type": "string", "minLength": 1},
    }
    variants = [
        _action_variant(
            "inspect_dataset",
            identity,
            {
                "dataset_ref": {"type": "string", "minLength": 1},
                "selected_field_ids": _string_array_schema(),
                "preview_limit": {"type": "integer"},
            },
            ("dataset_ref",),
        ),
        _action_variant(
            "run_analysis",
            identity,
            {
                "source": {"type": "string", "minLength": 1},
                "data_access": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["view_id", "field_ids"],
                        "properties": {
                            "view_id": {"type": "string", "minLength": 1},
                            "field_ids": _string_array_schema(),
                        },
                    },
                },
                "random_seed": {"type": ["integer", "null"]},
            },
            ("source", "data_access"),
        ),
        _action_variant(
            "run_authored_development_trial",
            identity,
            {
                "investigation_id": {"type": "string", "minLength": 1},
                "source": {"type": "string", "minLength": 1},
                "manifest": _authored_manifest_schema(),
                "rationale": {"type": "string", "minLength": 1},
                "parent_trial_ids": _string_array_schema(),
                "idempotency_key": {"type": "string", "minLength": 1},
            },
            (
                "investigation_id",
                "source",
                "manifest",
                "rationale",
                "parent_trial_ids",
                "idempotency_key",
            ),
        ),
        _action_variant(
            "run_scientific_workflow",
            identity,
            {
                "workflow_id": {"type": "string", "minLength": 1},
                "idempotency_key": {"type": "string", "minLength": 1},
            },
            ("workflow_id", "idempotency_key"),
        ),
        _action_variant(
            "propose_episode_transition",
            identity,
            {
                "target_status": {
                    "type": "string",
                    "enum": ["resolved", "abandoned", "suspended"],
                },
                "synthesis": {"type": "string", "minLength": 1},
                "evidence_refs": _string_array_schema(),
                "idempotency_key": {"type": "string", "minLength": 1},
                "state_update": {
                    "oneOf": [
                        {"type": "null"},
                        {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "starting_state_version",
                                "durable_understanding",
                                "evidence_refs",
                            ],
                            "properties": {
                                "starting_state_version": {"type": "integer"},
                                "durable_understanding": _string_array_schema(),
                                "evidence_refs": _string_array_schema(),
                            },
                        },
                    ]
                },
            },
            ("target_status", "synthesis", "evidence_refs", "idempotency_key"),
        ),
    ]
    return MappingProxyType({"oneOf": variants})


def _string_array_schema() -> dict[str, object]:
    return {"type": "array", "items": {"type": "string"}}


def _field_ref_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["dataset_id", "schema_version", "field_id", "environment_id"],
        "properties": {
            name: {"type": "string", "minLength": 1}
            for name in ("dataset_id", "schema_version", "field_id", "environment_id")
        },
    }


def _temporal_offset_schema() -> dict[str, object]:
    return {
        "oneOf": [
            {
                "type": "object",
                "additionalProperties": False,
                "required": ["kind", "elapsed_microseconds"],
                "properties": {
                    "kind": {"const": "elapsed"},
                    "elapsed_microseconds": {"type": "integer"},
                },
            },
            {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "kind",
                    "count",
                    "unit",
                    "anchor",
                    "month_end_policy",
                    "timezone_name",
                    "timezone_policy",
                ],
                "properties": {
                    "kind": {"const": "calendar"},
                    "count": {"type": "integer"},
                    "unit": {"type": "string", "enum": ["month", "quarter"]},
                    "anchor": {"const": "exact_input"},
                    "month_end_policy": {
                        "type": "string",
                        "enum": ["clamp", "preserve", "reject"],
                    },
                    "timezone_name": {"type": "string", "minLength": 1},
                    "timezone_policy": {
                        "type": "string",
                        "enum": ["wall_clock_reject_transition", "wall_clock_preserve_fold"],
                    },
                },
            },
        ]
    }


def _authored_manifest_schema() -> dict[str, object]:
    required = [
        "question_id",
        "environment_id",
        "predictor_fields",
        "outcome_field",
        "horizon",
        "minimum_outcome_points",
        "population_dimensions",
        "feature_names",
        "missing_value_policy",
        "evidence_refs",
        "provenance_refs",
    ]
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": {
            "question_id": {"type": "string", "minLength": 1},
            "environment_id": {"type": "string", "minLength": 1},
            "predictor_fields": {"type": "array", "items": _field_ref_schema()},
            "outcome_field": _field_ref_schema(),
            "horizon": _temporal_offset_schema(),
            "minimum_outcome_points": {"type": "integer"},
            "population_dimensions": {
                "type": "array",
                "items": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 2,
                    "items": {"type": "string"},
                },
            },
            "feature_names": _string_array_schema(),
            "missing_value_policy": {
                "type": "string",
                "enum": ["exclude_example", "fail_trial"],
            },
            "evidence_refs": _string_array_schema(),
            "provenance_refs": _string_array_schema(),
        },
    }


def _action_variant(
    kind: str,
    identity: Mapping[str, object],
    argument_properties: Mapping[str, object],
    required_arguments: tuple[str, ...],
) -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["kind", *identity, "arguments"],
        "properties": {
            "kind": {"const": kind},
            **identity,
            "arguments": {
                "type": "object",
                "additionalProperties": False,
                "required": list(required_arguments),
                "properties": dict(argument_properties),
            },
        },
    }


def _new_logical_call_id() -> str:
    return uuid4().hex


def _resolve_secret(resolver: SecretResolver, secret_ref: str) -> str:
    failed = False
    value: object = None
    try:
        value = resolver.resolve(secret_ref)
    except Exception:  # noqa: BLE001
        failed = True
    if failed or not isinstance(value, str) or not value:
        raise ProviderAuthenticationError("Configured provider credential is unavailable.")
    if any(
        ord(character) < _VISIBLE_ASCII_MIN or ord(character) > _VISIBLE_ASCII_MAX
        for character in value
    ):
        raise ProviderAuthenticationError("Configured provider credential is not header-safe.")
    return value


def _safe_transport_send(
    transport: HttpTransport,
    request: HttpRequest,
) -> tuple[HttpResponse | None, TransportFailureKind | None]:
    failure_kind: TransportFailureKind | None = None
    response: object = None
    try:
        response = transport.send(request)
    except HttpTransportError as error:
        failure_kind = error.kind
    except Exception:  # noqa: BLE001
        failure_kind = TransportFailureKind.PERMANENT
    if failure_kind is not None:
        return None, failure_kind
    if not isinstance(response, HttpResponse):
        return None, TransportFailureKind.INVALID_RESPONSE
    return response, None


class OpenAICompatibleProvider:
    """Production-shaped compatible JSON adapter with bounded safe retry."""

    def __init__(
        self,
        config: OpenAICompatibleProviderConfig,
        transport: HttpTransport,
        secret_resolver: SecretResolver,
        *,
        logical_call_id_factory: Callable[[], str] | None = None,
    ) -> None:
        """Bind explicit configuration to injected operational dependencies."""
        self._config = config
        self._transport = transport
        self._secret_resolver = secret_resolver
        self._logical_call_id_factory = logical_call_id_factory or _new_logical_call_id
        self._logical_call_lock = Lock()
        self._issued_logical_call_ids: set[str] = set()

    def complete(self, packet: ContextPacket) -> ModelResponse:  # noqa: C901
        """Request and normalize exactly one action from a bounded packet."""
        secret = _resolve_secret(self._secret_resolver, self._config.api_key_secret_ref)
        logical_call_id = self._logical_call_id_factory()
        self._reserve_logical_call(logical_call_id)
        request = self._build_request(packet, secret=secret, logical_call_id=logical_call_id)
        for attempt in range(1, self._config.max_attempts + 1):
            response, failure_kind = _safe_transport_send(self._transport, request)
            if failure_kind is not None:
                if failure_kind is TransportFailureKind.AUTHENTICATION:
                    raise ProviderAuthenticationError("Provider authentication failed.")
                if failure_kind is TransportFailureKind.INVALID_RESPONSE:
                    raise ProviderResponseError(
                        "Provider response exceeds the configured byte bound."
                    )
                if (
                    failure_kind is not TransportFailureKind.TRANSIENT
                    or attempt == self._config.max_attempts
                ):
                    raise ProviderUnavailableError("Provider transport failed.")
                continue
            if response is None:
                raise AssertionError("Transport result omitted both response and failure.")
            if len(response.body) > self._config.max_response_bytes:
                raise ProviderResponseError("Provider response exceeds the configured byte bound.")
            if response.status_code in {401, 403}:
                raise ProviderAuthenticationError("Provider authentication was rejected.")
            if response.status_code == _HTTP_RATE_LIMITED or (
                _HTTP_SERVER_ERROR_MIN <= response.status_code <= _HTTP_SERVER_ERROR_MAX
            ):
                if attempt < self._config.max_attempts:
                    continue
                raise ProviderUnavailableError("Provider remained unavailable after bounded retry.")
            if not _HTTP_OK_MIN <= response.status_code <= _HTTP_OK_MAX:
                message = f"Provider rejected the request with status {response.status_code}."
                raise ProviderRequestError(message)
            return self._normalize_response(
                response.body,
                logical_request_id=request.logical_request_id,
                attempt_count=attempt,
                secret=secret,
            )
        raise AssertionError("Bounded provider attempt loop terminated unexpectedly.")

    def _reserve_logical_call(self, logical_call_id: str) -> None:
        if not logical_call_id:
            raise ProviderRequestError("Logical call identity must be non-empty text.")
        with self._logical_call_lock:
            if logical_call_id in self._issued_logical_call_ids:
                raise ProviderRequestError(
                    "Provider logical call identity was reused for another decision."
                )
            self._issued_logical_call_ids.add(logical_call_id)

    def _build_request(
        self,
        packet: ContextPacket,
        *,
        secret: str,
        logical_call_id: str,
    ) -> HttpRequest:
        packet_value = canonical_value(packet)
        if _contains_secret((self._config.model, packet_value), secret):
            raise ProviderAuthenticationError(
                "Provider credential appeared in the serialized request content."
            )
        semantic_request = {
            "adapter": "openai-compatible-json-v2",
            "endpoint": self._config.endpoint,
            "model": self._config.model,
            "packet": packet_value,
            "tool_schema": action_json_schema(),
            "timeout_seconds": self._config.timeout_seconds,
            "max_attempts": self._config.max_attempts,
            "max_request_bytes": self._config.max_request_bytes,
            "max_response_bytes": self._config.max_response_bytes,
            "max_response_nesting": self._config.max_response_nesting,
        }
        logical_request_id = sha256(
            canonical_bytes(
                {
                    "logical_call_id": logical_call_id,
                    "semantic_request": semantic_request,
                }
            )
        ).hexdigest()
        body_value = {
            "model": self._config.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Choose exactly one research action from the supplied provider-neutral "
                        "ContextPacket. A request grants no authority."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {"context_packet": packet_value},
                        allow_nan=False,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    ),
                },
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": _ACTION_TOOL_NAME,
                        "description": "Propose one untrusted runtime action.",
                        "strict": True,
                        "parameters": action_json_schema(),
                    },
                }
            ],
            "tool_choice": {"type": "function", "function": {"name": _ACTION_TOOL_NAME}},
            "parallel_tool_calls": False,
            "metadata": {"logical_request_id": logical_request_id},
        }
        if _contains_secret(body_value, secret):
            raise ProviderAuthenticationError(
                "Provider credential appeared in the serialized request content."
            )
        body = canonical_bytes(body_value)
        if len(body) > self._config.max_request_bytes:
            raise ProviderRequestError("Serialized provider request exceeds configured byte bound.")
        return HttpRequest(
            url=self._config.endpoint,
            headers=_RedactedHeaders(
                {
                    "Authorization": f"Bearer {secret}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": logical_request_id,
                    "X-Request-ID": logical_request_id,
                },
                frozenset({"Authorization"}),
            ),
            body=body,
            timeout_seconds=self._config.timeout_seconds,
            logical_request_id=logical_request_id,
            max_response_bytes=self._config.max_response_bytes,
        )

    def _normalize_response(
        self,
        response_body: bytes,
        *,
        logical_request_id: str,
        attempt_count: int,
        secret: str,
    ) -> ModelResponse:
        invalid_json = False
        try:
            native_value = _strict_json_loads(
                response_body,
                max_nesting=self._config.max_response_nesting,
            )
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
            invalid_json = True
            native_value = None
        if invalid_json:
            raise ProviderResponseError("Provider response is not complete valid JSON.")
        native = _mapping(native_value, "Provider response must be a JSON object.")
        choices = _sequence(native.get("choices"), "Provider response must contain choices.")
        if len(choices) != 1:
            raise ProviderResponseError("Provider response must contain exactly one choice.")
        choice = _mapping(choices[0], "Provider choice must be a JSON object.")
        message = _mapping(
            choice.get("message"),
            "Provider choice must contain one message object.",
        )
        action = _extract_action(
            message,
            max_nesting=self._config.max_response_nesting,
        )
        content = message.get("content")
        if content is None:
            content = ""
        if not isinstance(content, str):
            raise ProviderResponseError("Provider message content must be text or null.")
        metadata: dict[str, object] = {
            "adapter": "openai-compatible-json-v2",
            "logical_request_id": logical_request_id,
            "attempt_count": attempt_count,
        }
        if isinstance(native.get("id"), str):
            metadata["response_id"] = native["id"]
        if isinstance(native.get("model"), str):
            metadata["model"] = native["model"]
        usage = _normalize_usage(native.get("usage"))
        if usage:
            metadata["usage"] = usage
        if _contains_secret((content, action, metadata), secret):
            raise ProviderResponseError("Provider response contained credential material.")
        return ModelResponse(message=content, action=action, provider_metadata=metadata)


def _extract_action(
    message: Mapping[str, object],
    *,
    max_nesting: int,
) -> Mapping[str, object]:
    tool_calls = _sequence(
        message.get("tool_calls"),
        "Provider response must contain action calls.",
    )
    if len(tool_calls) != 1:
        raise ProviderResponseError("Provider response must request exactly one action.")
    tool_call = _mapping(tool_calls[0], "Provider action must be an object.")
    if tool_call.get("type") != "function":
        raise ProviderResponseError("Provider action must be a function tool call.")
    function = _mapping(tool_call.get("function"), "Provider function must be an object.")
    if function.get("name") != _ACTION_TOOL_NAME:
        raise ProviderResponseError("Provider used an unexpected action tool.")
    return _decode_action_arguments(function.get("arguments"), max_nesting=max_nesting)


def _mapping(value: object, message: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ProviderResponseError(message)
    unknown_mapping = cast("Mapping[object, object]", value)
    if not all(isinstance(key, str) for key in unknown_mapping):
        raise ProviderResponseError(message)
    return cast("Mapping[str, object]", unknown_mapping)


def _sequence(value: object, message: str) -> tuple[object, ...]:
    if not isinstance(value, (list, tuple)):
        raise ProviderResponseError(message)
    return tuple(cast("list[object] | tuple[object, ...]", value))


def _decode_action_arguments(value: object, *, max_nesting: int) -> Mapping[str, object]:
    if isinstance(value, str):
        malformed = False
        try:
            value = _strict_json_loads(value, max_nesting=max_nesting)
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
            malformed = True
        if malformed:
            raise ProviderResponseError("Provider action arguments are malformed JSON.")
    value = _mapping(value, "Provider action arguments must be one JSON object.")
    _validate_json_schema(value, action_json_schema())
    return value


def _strict_json_loads(value: str | bytes, *, max_nesting: int) -> object:
    def reject_constant(constant: str) -> object:
        message = f"Non-finite JSON value {constant!r} is not permitted."
        raise ProviderResponseError(message)

    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, item in pairs:
            if key in result:
                raise ProviderResponseError("Duplicate JSON object keys are not permitted.")
            result[key] = item
        return result

    text = value.decode("utf-8") if isinstance(value, bytes) else value
    _validate_json_nesting(text, max_nesting=max_nesting)
    return cast(
        "object",
        json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant),
    )


def _validate_json_nesting(value: str, *, max_nesting: int) -> None:
    depth = 0
    in_string = False
    escaped = False
    for character in value:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > max_nesting:
                raise ProviderResponseError("Provider response exceeds its nesting bound.")
        elif character in "]}":
            depth -= 1


def _validate_json_schema(  # noqa: C901, PLR0912
    value: object,
    schema: Mapping[str, object],
) -> None:
    alternatives = schema.get("oneOf")
    if alternatives is not None:
        if not isinstance(alternatives, (list, tuple)):
            raise ProviderResponseError("Provider action schema is internally invalid.")
        matches = 0
        for alternative in cast("list[object] | tuple[object, ...]", alternatives):
            if not isinstance(alternative, Mapping):
                raise ProviderResponseError("Provider action schema is internally invalid.")
            try:
                _validate_json_schema(value, cast("Mapping[str, object]", alternative))
            except ProviderResponseError:
                continue
            matches += 1
        if matches != 1:
            raise ProviderResponseError("Provider action does not match the exact schema.")
        return

    if "const" in schema and value != schema["const"]:
        raise ProviderResponseError("Provider action does not match the exact schema.")
    enum_values = schema.get("enum")
    if enum_values is not None and value not in cast(
        "list[object] | tuple[object, ...]", enum_values
    ):
        raise ProviderResponseError("Provider action does not match the exact schema.")
    expected_type = schema.get("type")
    if expected_type is not None and not _matches_json_type(value, expected_type):
        raise ProviderResponseError("Provider action does not match the exact schema.")

    if isinstance(value, str):
        minimum = schema.get("minLength")
        if isinstance(minimum, int) and len(value) < minimum:
            raise ProviderResponseError("Provider action does not match the exact schema.")
    if isinstance(value, Mapping):
        mapping = _mapping(
            cast("object", value),
            "Provider action does not match the exact schema.",
        )
        required_value = schema.get("required", ())
        if not isinstance(required_value, (list, tuple)):
            raise ProviderResponseError("Provider action schema is internally invalid.")
        required = set(cast("list[str] | tuple[str, ...]", required_value))
        if not required.issubset(mapping):
            raise ProviderResponseError("Provider action does not match the exact schema.")
        properties_value = schema.get("properties", {})
        properties = _mapping(
            properties_value,
            "Provider action schema is internally invalid.",
        )
        if schema.get("additionalProperties") is False and not set(mapping).issubset(properties):
            raise ProviderResponseError("Provider action does not match the exact schema.")
        for key, item in mapping.items():
            child_schema = properties.get(key)
            if child_schema is not None:
                _validate_json_schema(
                    item,
                    _mapping(child_schema, "Provider action schema is internally invalid."),
                )
    if isinstance(value, (list, tuple)):
        sequence = cast("list[object] | tuple[object, ...]", value)
        item_schema = schema.get("items")
        if item_schema is not None:
            item_schema = _mapping(item_schema, "Provider action schema is internally invalid.")
            for item in sequence:
                _validate_json_schema(item, item_schema)


def _matches_json_type(value: object, expected: object) -> bool:
    if isinstance(expected, str):
        candidates = (expected,)
    elif isinstance(expected, (list, tuple)):
        sequence = cast("list[object] | tuple[object, ...]", expected)
        if not all(isinstance(item, str) for item in sequence):
            raise ProviderResponseError("Provider action schema is internally invalid.")
        candidates = tuple(cast("list[str] | tuple[str, ...]", sequence))
    else:
        raise ProviderResponseError("Provider action schema is internally invalid.")
    return any(
        {
            "object": isinstance(value, Mapping),
            "array": isinstance(value, (list, tuple)),
            "string": isinstance(value, str),
            "integer": isinstance(value, int) and not isinstance(value, bool),
            "null": value is None,
        }.get(candidate, False)
        for candidate in candidates
    )


def _contains_secret(value: object, secret: str) -> bool:
    if isinstance(value, str):
        return secret in value
    if isinstance(value, Mapping):
        mapping = cast("Mapping[object, object]", value)
        return any(
            _contains_secret(key, secret) or _contains_secret(item, secret)
            for key, item in mapping.items()
        )
    if isinstance(value, (list, tuple)):
        sequence = cast("list[object] | tuple[object, ...]", value)
        return any(_contains_secret(item, secret) for item in sequence)
    return False


def _normalize_usage(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        return {}
    value = cast("Mapping[object, object]", value)
    normalized: dict[str, object] = {}
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        item = value.get(key)
        if isinstance(item, int) and not isinstance(item, bool) and item >= 0:
            normalized[key] = item
    return normalized


class ScriptedModelProvider:
    """Deterministic provider with no native object leakage."""

    def __init__(self, responses: tuple[Mapping[str, object], ...]) -> None:
        """Load a deterministic queue of provider-native response mappings."""
        self._responses = deque(responses)
        self.calls: list[ContextPacket] = []

    def complete(self, packet: ContextPacket) -> ModelResponse:
        """Normalize the next scripted native mapping into ModelResponse."""
        self.calls.append(packet)
        if not self._responses:
            raise ProviderUnavailableError("Scripted provider has no remaining response.")
        native = self._responses.popleft()
        action = native.get("action")
        if not isinstance(action, Mapping):
            raise TypeError("Provider response action must be a mapping.")
        action = cast("Mapping[str, object]", action)
        message = native.get("message", "")
        if not isinstance(message, str):
            raise TypeError("Provider response message must be text.")
        metadata = native.get("provider_metadata", {})
        if not isinstance(metadata, Mapping):
            raise TypeError("Provider metadata must be a mapping.")
        metadata = cast("Mapping[str, object]", metadata)
        return ModelResponse(message=message, action=dict(action), provider_metadata=dict(metadata))

    def discard_native_context(self) -> None:
        """Discard provider-side transcript/call memory for reconstruction tests."""
        self.calls.clear()

    def queue_response(self, response: Mapping[str, object]) -> None:
        """Append a deterministic future response after observing prior runtime output."""
        self._responses.append(response)


__all__ = [
    "EnvironmentSecretResolver",
    "HttpRequest",
    "HttpResponse",
    "HttpTransport",
    "HttpTransportError",
    "ModelProvider",
    "ModelResponse",
    "OpenAICompatibleProvider",
    "OpenAICompatibleProviderConfig",
    "ProviderAuthenticationError",
    "ProviderRequestError",
    "ProviderResponseError",
    "ProviderUnavailableError",
    "ScriptedModelProvider",
    "SecretResolver",
    "TransportFailureKind",
    "UrllibHttpTransport",
    "action_json_schema",
]
