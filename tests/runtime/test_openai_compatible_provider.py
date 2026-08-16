"""Contract tests for the production-shaped compatible JSON provider adapter."""

from __future__ import annotations

import http.client
import json
import math
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import replace
from typing import Self, cast

import pytest

from research_agent.runtime._canonical import canonical_value
from research_agent.runtime.actions import ActionDecodeError, InspectDatasetAction, decode_action
from research_agent.runtime.context import ContextBuilder
from research_agent.runtime.provider import (
    HttpRequest,
    HttpResponse,
    HttpTransportError,
    OpenAICompatibleProvider,
    OpenAICompatibleProviderConfig,
    ProviderAuthenticationError,
    ProviderRequestError,
    ProviderResponseError,
    ProviderUnavailableError,
    SecretResolver,
    TransportFailureKind,
    UrllibHttpTransport,
    action_json_schema,
)
from tests.runtime.support import initialized_runtime

SECRET = "secret-sentinel-that-must-not-leak"  # noqa: S105
TIMEOUT_SECONDS = 12.5
RETRY_ATTEMPTS = 3
EXHAUSTED_ATTEMPTS = 2


class _SecretResolver:
    def __init__(self, value: str = SECRET) -> None:
        self.value = value
        self.refs: list[str] = []

    def resolve(self, secret_ref: str) -> str:
        self.refs.append(secret_ref)
        return self.value


class _FailingSecretResolver:
    def resolve(self, secret_ref: str) -> str:
        del secret_ref
        raise RuntimeError(SECRET)


class _FakeTransport:
    def __init__(self, outcomes: tuple[HttpResponse | Exception, ...]) -> None:
        self.outcomes = deque(outcomes)
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        outcome = self.outcomes.popleft()
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _native_response(action: Mapping[str, object]) -> HttpResponse:
    value = {
        "id": "response-native-1",
        "model": "provider-returned-model",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Inspect first.",
                    "tool_calls": [
                        {
                            "id": "tool-native-1",
                            "type": "function",
                            "function": {
                                "name": "submit_research_action",
                                "arguments": json.dumps(action),
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 7, "native_secret": SECRET},
        "native_client": SECRET,
    }
    return HttpResponse(200, json.dumps(value).encode())


def _action(
    session_id: str,
    episode_id: str,
    *,
    action_id: str = "action-provider-1",
) -> dict[str, object]:
    return {
        "kind": "inspect_dataset",
        "action_id": action_id,
        "session_id": session_id,
        "episode_id": episode_id,
        "arguments": {
            "dataset_ref": "toy-monthly",
            "selected_field_ids": ["predictor_value"],
            "preview_limit": 3,
        },
    }


def _provider(  # noqa: PLR0913
    transport: _FakeTransport,
    resolver: SecretResolver | None = None,
    *,
    max_attempts: int = 3,
    max_request_bytes: int = 1_000_000,
    max_response_bytes: int = 1_000_000,
    max_response_nesting: int = 64,
    base_url: str = "https://provider.example/v1",
    logical_call_id_factory: Callable[[], str] | None = None,
) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        OpenAICompatibleProviderConfig(
            base_url=base_url,
            model="configured-model",
            api_key_secret_ref="PROVIDER_API_KEY",  # noqa: S106
            timeout_seconds=TIMEOUT_SECONDS,
            max_attempts=max_attempts,
            max_request_bytes=max_request_bytes,
            max_response_bytes=max_response_bytes,
            max_response_nesting=max_response_nesting,
        ),
        transport,
        resolver or _SecretResolver(),
        logical_call_id_factory=logical_call_id_factory,
    )


def test_exact_packet_and_action_schema_are_serialized_without_secret_leak() -> None:
    """The request contains the complete bounded packet and exact typed action schema."""
    store, initialized = initialized_runtime()
    packet = ContextBuilder(store).build_current_context(initialized.session.session_id)
    resolver = _SecretResolver()
    transport = _FakeTransport((_native_response(_action(packet.session_id, packet.episode_id)),))

    response = _provider(transport, resolver).complete(packet)

    request = transport.requests[0]
    body = json.loads(request.body)
    packet_message = json.loads(body["messages"][1]["content"])
    assert request.url == "https://provider.example/v1/chat/completions"
    assert request.timeout_seconds == TIMEOUT_SECONDS
    assert body["model"] == "configured-model"
    assert packet_message == {"context_packet": canonical_value(packet)}
    assert body["tools"][0]["function"]["parameters"] == canonical_value(action_json_schema())
    assert body["tool_choice"]["function"]["name"] == "submit_research_action"
    assert body["parallel_tool_calls"] is False
    assert resolver.refs == ["PROVIDER_API_KEY"]
    assert request.headers["Authorization"] == f"Bearer {SECRET}"
    assert SECRET not in repr(request)
    assert SECRET not in repr(request.headers)
    assert SECRET.encode() not in request.body
    assert SECRET not in repr(response)
    assert SECRET not in repr(response.provider_metadata)
    assert response.provider_metadata["model"] == "provider-returned-model"
    assert "native_client" not in response.provider_metadata
    assert "native_secret" not in repr(response.provider_metadata)


def test_transient_retry_is_bounded_and_keeps_one_logical_identity() -> None:
    """Transport/rate failures retry with the same request and idempotency identity."""
    store, initialized = initialized_runtime()
    packet = ContextBuilder(store).build_current_context(initialized.session.session_id)
    transport = _FakeTransport(
        (
            HttpTransportError(TransportFailureKind.TRANSIENT, "timeout"),
            HttpResponse(429, b'{"error":"rate"}'),
            _native_response(_action(packet.session_id, packet.episode_id)),
        )
    )

    response = _provider(transport).complete(packet)

    assert len(transport.requests) == RETRY_ATTEMPTS
    request_ids = {request.logical_request_id for request in transport.requests}
    assert len(request_ids) == 1
    assert {request.headers["Idempotency-Key"] for request in transport.requests} == request_ids
    assert {request.headers["X-Request-ID"] for request in transport.requests} == request_ids
    assert len({request.body for request in transport.requests}) == 1
    assert response.provider_metadata["attempt_count"] == RETRY_ATTEMPTS
    assert response.provider_metadata["logical_request_id"] in request_ids


def test_retry_exhaustion_and_permanent_transport_failure_are_bounded() -> None:
    """Declared transient failures stop at the bound; permanent failures never retry."""
    store, initialized = initialized_runtime()
    packet = ContextBuilder(store).build_current_context(initialized.session.session_id)
    transient = HttpTransportError(TransportFailureKind.TRANSIENT, "timeout")
    transient_transport = _FakeTransport((transient, transient, transient))

    with pytest.raises(ProviderUnavailableError):
        _provider(transient_transport, max_attempts=EXHAUSTED_ATTEMPTS).complete(packet)
    assert len(transient_transport.requests) == EXHAUSTED_ATTEMPTS

    permanent_transport = _FakeTransport(
        (HttpTransportError(TransportFailureKind.PERMANENT, "invalid TLS policy"),)
    )
    with pytest.raises(ProviderUnavailableError):
        _provider(permanent_transport).complete(packet)
    assert len(permanent_transport.requests) == 1


@pytest.mark.parametrize(
    ("response", "error_type"),
    [
        (HttpResponse(401, b'{"error":"auth"}'), ProviderAuthenticationError),
        (HttpResponse(400, b'{"error":"bad-request"}'), ProviderRequestError),
        (HttpResponse(200, b"not-json"), ProviderResponseError),
        (
            HttpResponse(
                200,
                json.dumps({"choices": [{"message": {"content": "no action"}}]}).encode(),
            ),
            ProviderResponseError,
        ),
    ],
)
def test_auth_request_malformed_and_tool_free_fail_without_retry(
    response: HttpResponse,
    error_type: type[Exception],
) -> None:
    """Non-transient provider failures fail closed after one attempt."""
    store, initialized = initialized_runtime()
    packet = ContextBuilder(store).build_current_context(initialized.session.session_id)
    transport = _FakeTransport((response,))

    with pytest.raises(error_type):
        _provider(transport).complete(packet)

    assert len(transport.requests) == 1


def test_multiple_choices_and_multiple_actions_fail_closed() -> None:
    """The adapter never chooses the first of several native intents."""
    store, initialized = initialized_runtime()
    packet = ContextBuilder(store).build_current_context(initialized.session.session_id)
    action = _action(packet.session_id, packet.episode_id)
    native = json.loads(_native_response(action).body)
    native["choices"].append(native["choices"][0])
    multiple_choices = HttpResponse(200, json.dumps(native).encode())
    native = json.loads(_native_response(action).body)
    native["choices"][0]["message"]["tool_calls"].append(
        native["choices"][0]["message"]["tool_calls"][0]
    )
    multiple_tools = HttpResponse(200, json.dumps(native).encode())

    for invalid in (multiple_choices, multiple_tools):
        transport = _FakeTransport((invalid,))
        with pytest.raises(ProviderResponseError):
            _provider(transport).complete(packet)
        assert len(transport.requests) == 1


def test_normalized_action_is_compatible_with_typed_runtime_decoder() -> None:
    """Provider normalization preserves the exact action consumed by action.decode-intent."""
    store, initialized = initialized_runtime()
    packet = ContextBuilder(store).build_current_context(initialized.session.session_id)
    transport = _FakeTransport((_native_response(_action(packet.session_id, packet.episode_id)),))

    typed = decode_action(_provider(transport).complete(packet))

    assert isinstance(typed, InspectDatasetAction)
    assert typed.session_id == packet.session_id
    assert typed.episode_id == packet.episode_id
    assert typed.selected_field_ids == ("predictor_value",)


def test_packet_change_changes_identity_while_checkpoint_rebuild_is_equivalent() -> None:
    """Equivalent packets preserve meaning without conflating independent logical calls."""
    store, initialized = initialized_runtime()
    builder = ContextBuilder(store)
    checkpoint = builder.checkpoint_current_episode(initialized.session.session_id)
    current = builder.build_current_context(initialized.session.session_id)
    rebuilt = builder.rebuild_from_checkpoint(
        initialized.session.session_id,
        checkpoint.checkpoint_id,
    )
    changed = replace(current, active_question="A materially different next question")
    responses = tuple(
        _native_response(_action(current.session_id, current.episode_id, action_id=f"action-{i}"))
        for i in range(3)
    )
    transport = _FakeTransport(responses)
    provider = _provider(transport)

    provider.complete(current)
    provider.complete(rebuilt)
    provider.complete(changed)

    assert current == rebuilt
    first_body = json.loads(transport.requests[0].body)
    rebuilt_body = json.loads(transport.requests[1].body)
    assert first_body["messages"] == rebuilt_body["messages"]
    assert first_body["tools"] == rebuilt_body["tools"]
    assert transport.requests[0].logical_request_id != transport.requests[1].logical_request_id
    assert transport.requests[2].logical_request_id != transport.requests[0].logical_request_id


def test_request_size_bound_fails_before_transport() -> None:
    """Even an authoritative packet cannot create an unbounded provider request."""
    store, initialized = initialized_runtime()
    packet = ContextBuilder(store).build_current_context(initialized.session.session_id)
    transport = _FakeTransport(())

    with pytest.raises(ProviderRequestError, match="byte bound"):
        _provider(transport, max_request_bytes=1).complete(packet)

    assert transport.requests == []


def test_secret_cannot_escape_through_selected_response_fields_or_error_chains() -> None:
    """A credential echoed by native mechanics never reaches public output or exceptions."""
    store, initialized = initialized_runtime()
    packet = ContextBuilder(store).build_current_context(initialized.session.session_id)
    action = _action(packet.session_id, packet.episode_id)
    native = json.loads(_native_response(action).body)
    native["id"] = SECRET
    native["model"] = SECRET
    native["choices"][0]["message"]["content"] = SECRET

    with pytest.raises(ProviderResponseError) as response_failure:
        _provider(_FakeTransport((HttpResponse(200, json.dumps(native).encode()),))).complete(
            packet
        )
    assert SECRET not in repr(response_failure.value)
    assert response_failure.value.__cause__ is None
    assert response_failure.value.__context__ is None

    transport_error = HttpTransportError(TransportFailureKind.TRANSIENT, SECRET)
    with pytest.raises(ProviderUnavailableError) as transport_failure:
        _provider(_FakeTransport((transport_error,)), max_attempts=1).complete(packet)
    assert SECRET not in repr(transport_failure.value)
    assert transport_failure.value.__cause__ is None
    assert transport_failure.value.__context__ is None

    with pytest.raises(ProviderAuthenticationError) as auth_failure:
        _provider(_FakeTransport(()), _FailingSecretResolver()).complete(packet)
    assert SECRET not in repr(auth_failure.value)
    assert auth_failure.value.__cause__ is None
    assert auth_failure.value.__context__ is None

    body_transport = _FakeTransport(())
    with pytest.raises(ProviderAuthenticationError, match="request content"):
        _provider(body_transport).complete(replace(packet, mission=SECRET))
    assert body_transport.requests == []

    header_transport = _FakeTransport(())
    with pytest.raises(ProviderAuthenticationError, match="header-safe"):
        _provider(header_transport, _SecretResolver(f"safe{SECRET}\r\nInjected: yes")).complete(
            packet
        )
    assert header_transport.requests == []


def test_response_size_and_nesting_are_bounded_before_normalization() -> None:
    """Native output cannot allocate an unbounded response or escape as RecursionError."""
    store, initialized = initialized_runtime()
    packet = ContextBuilder(store).build_current_context(initialized.session.session_id)
    action = _action(packet.session_id, packet.episode_id)
    oversized = _native_response(action)
    native = json.loads(oversized.body)
    native["choices"][0]["message"]["content"] = "x" * 4_096
    oversized = HttpResponse(200, json.dumps(native).encode())

    with pytest.raises(ProviderResponseError, match="byte bound"):
        _provider(_FakeTransport((oversized,)), max_response_bytes=1_024).complete(packet)

    deeply_nested = b'{"choices":' + (b"[" * 100) + b"0" + (b"]" * 100) + b"}"
    with pytest.raises(ProviderResponseError, match="nesting"):
        _provider(
            _FakeTransport((HttpResponse(200, deeply_nested),)),
            max_response_nesting=32,
        ).complete(packet)


def test_standard_transport_bounds_reads_and_neutralizes_incomplete_native_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The concrete transport never performs an unbounded read or leaks HTTP exceptions."""
    store, initialized = initialized_runtime()
    packet = ContextBuilder(store).build_current_context(initialized.session.session_id)

    class BoundedResponse:
        status = 200

        def __init__(self) -> None:
            self.read_limits: list[int] = []

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *args: object) -> None:
            del args

        def read(self, limit: int) -> bytes:
            self.read_limits.append(limit)
            return b"x" * limit

    bounded = BoundedResponse()

    def return_bounded(*_args: object, **_kwargs: object) -> BoundedResponse:
        return bounded

    monkeypatch.setattr("urllib.request.urlopen", return_bounded)
    provider = OpenAICompatibleProvider(
        OpenAICompatibleProviderConfig(
            "https://provider.example/v1",
            "model",
            "PROVIDER_API_KEY",
            max_attempts=1,
            max_response_bytes=128,
        ),
        UrllibHttpTransport(),
        _SecretResolver(),
    )
    with pytest.raises(ProviderResponseError, match="byte bound"):
        provider.complete(packet)
    assert bounded.read_limits == [129]

    class IncompleteResponse(BoundedResponse):
        def read(self, limit: int) -> bytes:
            del limit
            partial = b"partial"
            raise http.client.IncompleteRead(partial, 100)

    def return_incomplete(*_args: object, **_kwargs: object) -> IncompleteResponse:
        return IncompleteResponse()

    monkeypatch.setattr("urllib.request.urlopen", return_incomplete)
    provider = OpenAICompatibleProvider(
        OpenAICompatibleProviderConfig(
            "https://provider.example/v1",
            "model",
            "PROVIDER_API_KEY",
            max_attempts=1,
            max_response_bytes=256,
        ),
        UrllibHttpTransport(),
        _SecretResolver(),
    )
    with pytest.raises(ProviderUnavailableError) as failure:
        provider.complete(packet)
    assert failure.value.__cause__ is None
    assert failure.value.__context__ is None


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_data_access",
        "unexpected_argument",
        "missing_nested_field_ids",
        "boolean_random_seed",
    ],
)
def test_recursive_action_schema_violations_fail_before_typed_decoding(
    mutation: str,
) -> None:
    """Compatible endpoints cannot bypass the exact recursive action contract."""
    store, initialized = initialized_runtime()
    packet = ContextBuilder(store).build_current_context(initialized.session.session_id)
    action: dict[str, object] = {
        "kind": "run_analysis",
        "action_id": "action-provider-analysis",
        "session_id": packet.session_id,
        "episode_id": packet.episode_id,
        "arguments": {
            "source": 'structured_return({"ok": True})',
            "data_access": [{"view_id": "view-1", "field_ids": ["predictor_value"]}],
            "random_seed": 7,
        },
    }
    arguments_value = action["arguments"]
    assert isinstance(arguments_value, dict)
    arguments = cast("dict[str, object]", arguments_value)
    if mutation == "missing_data_access":
        arguments.pop("data_access")
    elif mutation == "unexpected_argument":
        arguments["unexpected"] = "silently ignored"
    elif mutation == "missing_nested_field_ids":
        access = arguments["data_access"]
        assert isinstance(access, list)
        access_items = cast("list[object]", access)
        first_access_value = access_items[0]
        assert isinstance(first_access_value, dict)
        first_access = cast("dict[str, object]", first_access_value)
        first_access.pop("field_ids")
    else:
        arguments["random_seed"] = True

    with pytest.raises(ProviderResponseError, match="schema"):
        _provider(_FakeTransport((_native_response(action),))).complete(packet)


def test_typed_decoder_independently_rejects_schema_forbidden_arguments() -> None:
    """A provider implementation cannot bypass recursive validation owned by action decoding."""
    store, initialized = initialized_runtime()
    packet = ContextBuilder(store).build_current_context(initialized.session.session_id)
    response = _provider(
        _FakeTransport((_native_response(_action(packet.session_id, packet.episode_id)),))
    ).complete(packet)
    forged = dict(response.action)
    arguments_value = forged["arguments"]
    assert isinstance(arguments_value, Mapping)
    arguments = dict(cast("Mapping[str, object]", arguments_value))
    arguments["unexpected"] = "ignored before hardening"
    forged["arguments"] = arguments

    with pytest.raises(ActionDecodeError, match="exact schema"):
        decode_action(replace(response, action=forged))


def test_logical_call_collision_cannot_accept_a_second_decision() -> None:
    """One logical call identity can accept at most one native response."""
    store, initialized = initialized_runtime()
    packet = ContextBuilder(store).build_current_context(initialized.session.session_id)
    transport = _FakeTransport(
        (
            _native_response(_action(packet.session_id, packet.episode_id, action_id="first")),
            _native_response(_action(packet.session_id, packet.episode_id, action_id="second")),
        )
    )
    provider = _provider(
        transport,
        logical_call_id_factory=lambda: "deliberate-logical-call-collision",
    )

    first = provider.complete(packet)
    with pytest.raises(ProviderRequestError, match="logical call identity"):
        provider.complete(packet)

    assert first.action["action_id"] == "first"
    assert len(transport.requests) == 1


@pytest.mark.parametrize(
    "base_url",
    [
        "http://",
        "https://user:password@provider.example/v1",
        "https://provider.example/v1?route=other",
        "https://provider.example/v1#fragment",
        "https://provider.example/\r\nInjected: yes",
    ],
)
def test_unsafe_or_ambiguous_provider_urls_are_rejected(base_url: str) -> None:
    """Endpoint construction accepts an explicit host/path but no URL/header ambiguity."""
    with pytest.raises(ValueError, match="base_url"):
        OpenAICompatibleProviderConfig(base_url, "model", "PROVIDER_API_KEY")


@pytest.mark.parametrize("timeout", [math.nan, math.inf, -math.inf])
def test_non_finite_timeouts_are_rejected(timeout: float) -> None:
    """A configured timeout must be an actual finite operational bound."""
    with pytest.raises(ValueError, match="timeout_seconds"):
        OpenAICompatibleProviderConfig(
            "https://provider.example/v1",
            "model",
            "PROVIDER_API_KEY",
            timeout_seconds=timeout,
        )
