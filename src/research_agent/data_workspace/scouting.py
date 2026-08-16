"""Provider-neutral source proposals ahead of the existing acquisition boundary."""

# ruff: noqa: EM101, EM102, TRY003, TRY004

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import secrets
import stat
import threading
import urllib.parse
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Final, cast

from research_agent.data_workspace.workspace import (
    DataWorkspace,
    FetchReceipt,
    FetchRequest,
    FetchStatus,
    JsonValue,
)

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

_REQUEST_SCHEMA: Final[str] = "source-search-request/v1"
_RESPONSE_SCHEMA: Final[str] = "source-scout-response/v1"
_REPORT_SCHEMA: Final[str] = "source-scouting-report/v1"
_LEDGER_SCHEMA: Final[str] = "source-scouting-ledger/v1"
_MAX_TEXT: Final[int] = 8_000
_MAX_QUERY_COUNT: Final[int] = 8
_MAX_REQUIREMENT_COUNT: Final[int] = 24
_MAX_CANDIDATES: Final[int] = 20
_MAX_LIST_ITEMS: Final[int] = 24
_SHA256_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")
_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/-]{0,127}$")
_SECRET_MARKERS: Final[tuple[str, ...]] = (
    "authorization",
    "credential",
    "password",
    "secret",
    "signature",
    "token",
    "api-key",
    "api_key",
    "apikey",
)
_CREDENTIAL_ASSIGNMENT: Final[re.Pattern[str]] = re.compile(
    r"(?i)\b(?:authorization|credential|password|secret|signature|token|api[-_ ]?key)\s*[:=]\s*\S+"
)
_CANDIDATE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "title",
        "resource_url",
        "landing_page_url",
        "publisher",
        "description",
        "why_relevant",
        "temporal_coverage",
        "frequency",
        "license",
        "access_notes",
        "risks",
        "evidence_urls",
    }
)
_EXTERNAL_FAILURE_CODES: Final[frozenset[str]] = frozenset(
    {"EXTERNAL_SCOUT_DENIED", "EXTERNAL_SCOUT_FAILED", "EXTERNAL_SCOUT_TIMEOUT"}
)
_MAX_LEDGER_BYTES: Final[int] = 8 * 1024 * 1024


class ScoutingStatus(Enum):
    """Truthful source-scouting outcome."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ScoutedFetchStatus(Enum):
    """Outcome of handing an issued candidate to acquisition."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DENIED = "denied"


class ScoutingConflictError(ValueError):
    """Raised when one idempotency identity is reused for changed intent."""


class ScoutingResolutionError(ValueError):
    """Raised when a scouting reference is absent or does not match retained content."""


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
        raise ValueError("scouting values must be finite JSON") from error


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _sha256_identifier(value: object, *, field: str) -> str:
    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase SHA-256 identity")
    return value


def _strict_text(value: object, *, field: str, allow_empty: bool = False) -> str:
    if (
        not isinstance(value, str)
        or len(value) > _MAX_TEXT
        or (not value.strip() and not allow_empty)
    ):
        raise ValueError(f"{field} must be bounded text")
    return value


def _metadata_text(value: object, *, field: str) -> str:
    text = _strict_text(value, field=field)
    if _CREDENTIAL_ASSIGNMENT.search(text) is not None:
        raise ValueError(f"{field} cannot contain credential assignments")
    return text


def _strict_text_tuple(value: object, *, field: str, maximum: int) -> tuple[str, ...]:
    if not isinstance(value, list | tuple):
        raise ValueError(f"{field} must be a bounded text list")
    items = cast("list[object] | tuple[object, ...]", value)
    if len(items) > maximum:
        raise ValueError(f"{field} must be a bounded text list")
    result = tuple(_strict_text(item, field=field) for item in items)
    if len(set(result)) != len(result):
        raise ValueError(f"{field} cannot contain duplicates")
    return result


def _strict_object(value: object, *, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return cast("dict[str, object]", value)


def _safe_public_url(value: object, *, field: str) -> str:
    url = _strict_text(value, field=field)
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise ValueError(f"{field} must be a public HTTP URL without userinfo or fragment")
    for key, item in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        lowered_item = item.lower()
        if any(marker in lowered or marker in lowered_item for marker in _SECRET_MARKERS):
            raise ValueError(f"{field} cannot contain credential-like query material")
    return url


def _strict_timestamp(value: object, *, field: str) -> str:
    timestamp = _strict_text(value, field=field)
    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a UTC offset")
    return timestamp


@dataclass(frozen=True, slots=True)
class SourceSearchRequest:
    """One exact, bounded statement of data needed to test a research question."""

    research_question: str
    data_need: str
    search_queries: tuple[str, ...]
    requirements: tuple[str, ...]
    max_candidates: int = 8

    def __post_init__(self) -> None:
        """Validate and detach every bounded request field."""
        object.__setattr__(
            self,
            "research_question",
            _strict_text(self.research_question, field="research_question"),
        )
        object.__setattr__(self, "data_need", _strict_text(self.data_need, field="data_need"))
        queries = _strict_text_tuple(
            self.search_queries,
            field="search_queries",
            maximum=_MAX_QUERY_COUNT,
        )
        if not queries:
            raise ValueError("at least one search query is required")
        object.__setattr__(self, "search_queries", queries)
        object.__setattr__(
            self,
            "requirements",
            _strict_text_tuple(
                self.requirements,
                field="requirements",
                maximum=_MAX_REQUIREMENT_COUNT,
            ),
        )
        if not 1 <= self.max_candidates <= _MAX_CANDIDATES:
            raise ValueError("max_candidates is outside the scouting bound")

    @property
    def request_id(self) -> str:
        """Return the stable content identity of this data need."""
        return _sha256(self._identity_payload())

    def _identity_payload(self) -> dict[str, JsonValue]:
        return {
            "schema_version": _REQUEST_SCHEMA,
            "research_question": self.research_question,
            "data_need": self.data_need,
            "search_queries": list(self.search_queries),
            "requirements": list(self.requirements),
            "max_candidates": self.max_candidates,
        }

    def as_dict(self) -> dict[str, JsonValue]:
        """Serialize a strict provider/operator request."""
        return {**self._identity_payload(), "request_id": self.request_id}

    @classmethod
    def from_dict(cls, value: object) -> SourceSearchRequest:
        """Decode exact request JSON and reject unknown or stale identity fields."""
        data = _strict_object(value, field="source-search request")
        expected = {
            "schema_version",
            "request_id",
            "research_question",
            "data_need",
            "search_queries",
            "requirements",
            "max_candidates",
        }
        if set(data) != expected or data.get("schema_version") != _REQUEST_SCHEMA:
            raise ValueError("source-search request schema is not exact")
        max_candidates = data.get("max_candidates")
        if not isinstance(max_candidates, int) or isinstance(max_candidates, bool):
            raise ValueError("max_candidates must be an integer")
        request = cls(
            research_question=cast("str", data.get("research_question")),
            data_need=cast("str", data.get("data_need")),
            search_queries=_strict_text_tuple(
                data.get("search_queries"), field="search_queries", maximum=_MAX_QUERY_COUNT
            ),
            requirements=_strict_text_tuple(
                data.get("requirements"), field="requirements", maximum=_MAX_REQUIREMENT_COUNT
            ),
            max_candidates=max_candidates,
        )
        if data.get("request_id") != request.request_id:
            raise ValueError("source-search request identity does not match content")
        return request


@dataclass(frozen=True, slots=True)
class SourceCandidate:
    """Unverified source proposal; never a dataset, observation, or evidence object."""

    title: str
    resource_url: str
    landing_page_url: str
    publisher: str
    description: str
    why_relevant: str
    temporal_coverage: str
    frequency: str
    license: str
    access_notes: str
    risks: tuple[str, ...]
    evidence_urls: tuple[str, ...]

    @property
    def candidate_id(self) -> str:
        """Return the exact identity of the provider proposal."""
        return _sha256(self._identity_payload())

    def _identity_payload(self) -> dict[str, JsonValue]:
        return {
            "title": self.title,
            "resource_url": self.resource_url,
            "landing_page_url": self.landing_page_url,
            "publisher": self.publisher,
            "description": self.description,
            "why_relevant": self.why_relevant,
            "temporal_coverage": self.temporal_coverage,
            "frequency": self.frequency,
            "license": self.license,
            "access_notes": self.access_notes,
            "risks": list(self.risks),
            "evidence_urls": list(self.evidence_urls),
        }

    def as_dict(self) -> dict[str, JsonValue]:
        """Serialize the proposal with explicit non-authoritative status."""
        return {
            **self._identity_payload(),
            "candidate_id": self.candidate_id,
            "epistemic_status": "UNVERIFIED_SOURCE_PROPOSAL",
            "scientific_authority": "NONE_PROPOSAL_ONLY",
        }

    @classmethod
    def from_provider_dict(cls, value: object) -> SourceCandidate:
        """Decode a provider response without accepting authority or data-value fields."""
        data = _strict_object(value, field="source candidate")
        if set(data) != set(_CANDIDATE_KEYS):
            raise ValueError("source candidate schema is not exact")
        evidence_urls = _strict_text_tuple(
            data.get("evidence_urls"), field="evidence_urls", maximum=_MAX_LIST_ITEMS
        )
        return cls(
            title=_metadata_text(data.get("title"), field="title"),
            resource_url=_safe_public_url(data.get("resource_url"), field="resource_url"),
            landing_page_url=_safe_public_url(
                data.get("landing_page_url"), field="landing_page_url"
            ),
            publisher=_metadata_text(data.get("publisher"), field="publisher"),
            description=_metadata_text(data.get("description"), field="description"),
            why_relevant=_metadata_text(data.get("why_relevant"), field="why_relevant"),
            temporal_coverage=_metadata_text(
                data.get("temporal_coverage"), field="temporal_coverage"
            ),
            frequency=_metadata_text(data.get("frequency"), field="frequency"),
            license=_metadata_text(data.get("license"), field="license"),
            access_notes=_metadata_text(data.get("access_notes"), field="access_notes"),
            risks=tuple(
                _metadata_text(item, field="risks")
                for item in _strict_text_tuple(
                    data.get("risks"), field="risks", maximum=_MAX_LIST_ITEMS
                )
            ),
            evidence_urls=tuple(
                _safe_public_url(url, field="evidence_urls") for url in evidence_urls
            ),
        )

    @classmethod
    def from_stored_dict(cls, value: object) -> SourceCandidate:
        """Decode a retained candidate and recheck its exact identity/status."""
        data = _strict_object(value, field="stored source candidate")
        if (
            data.get("epistemic_status") != "UNVERIFIED_SOURCE_PROPOSAL"
            or data.get("scientific_authority") != "NONE_PROPOSAL_ONLY"
        ):
            raise ValueError("stored source candidate status is invalid")
        provider_value: dict[str, object] = {key: data.get(key) for key in _CANDIDATE_KEYS}
        candidate = cls.from_provider_dict(provider_value)
        expected = _CANDIDATE_KEYS | {
            "candidate_id",
            "epistemic_status",
            "scientific_authority",
        }
        if set(data) != set(expected) or data.get("candidate_id") != candidate.candidate_id:
            raise ValueError("stored source candidate identity does not match content")
        return candidate


@dataclass(frozen=True, slots=True)
class SourceScoutingReportRef:
    """Value-free reference to one retained exact provider report."""

    report_id: str
    request_id: str
    provider_id: str
    candidate_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        """Reject path-like, stale, duplicated, or malformed reference identities."""
        object.__setattr__(
            self,
            "report_id",
            _sha256_identifier(self.report_id, field="report_id"),
        )
        object.__setattr__(
            self,
            "request_id",
            _sha256_identifier(self.request_id, field="request_id"),
        )
        object.__setattr__(self, "provider_id", _provider_id(self.provider_id))
        candidate_ids = _strict_text_tuple(
            self.candidate_ids,
            field="candidate_ids",
            maximum=_MAX_CANDIDATES,
        )
        object.__setattr__(
            self,
            "candidate_ids",
            tuple(_sha256_identifier(item, field="candidate_ids") for item in candidate_ids),
        )

    @property
    def uri(self) -> str:
        """Return the stable report reference spelling."""
        return f"scouting:{self.report_id}"

    def as_dict(self) -> dict[str, JsonValue]:
        """Return a bounded value-free report reference."""
        return {
            "kind": "SourceScoutingReportRef",
            "report_id": self.report_id,
            "request_id": self.request_id,
            "provider_id": self.provider_id,
            "candidate_ids": list(self.candidate_ids),
            "uri": self.uri,
        }


@dataclass(frozen=True, slots=True)
class SourceScoutingReport:
    """Append-only unverified source proposals for one exact data need."""

    report_id: str
    request: SourceSearchRequest
    provider_id: str
    candidates: tuple[SourceCandidate, ...]
    recorded_at: str

    @property
    def ref(self) -> SourceScoutingReportRef:
        """Return the value-free public reference."""
        return SourceScoutingReportRef(
            report_id=self.report_id,
            request_id=self.request.request_id,
            provider_id=self.provider_id,
            candidate_ids=tuple(candidate.candidate_id for candidate in self.candidates),
        )

    def _identity_payload(self) -> dict[str, JsonValue]:
        return {
            "schema_version": _REPORT_SCHEMA,
            "request": self.request.as_dict(),
            "provider_id": self.provider_id,
            "provider_identity_authority": "UNVERIFIED_CALLER_LABEL",
            "candidates": [candidate.as_dict() for candidate in self.candidates],
            "recorded_at": self.recorded_at,
        }

    def as_dict(self) -> dict[str, JsonValue]:
        """Serialize the complete retained proposal report."""
        return {
            **self._identity_payload(),
            "report_id": self.report_id,
            "epistemic_status": "EXPLORATORY_SOURCE_SCOUTING",
            "scientific_authority": "NONE_PROPOSAL_ONLY",
            "source_snapshot_refs": [],
            "registered_dataset_refs": [],
            "durable_scientific_state_effects": [],
        }


@dataclass(frozen=True, slots=True)
class SourceScoutingReceipt:
    """Truthful result of one idempotent provider scouting operation."""

    operation_id: str
    request_id: str
    status: ScoutingStatus
    report_ref: SourceScoutingReportRef | None
    error_code: str | None = None

    def as_dict(self) -> dict[str, JsonValue]:
        """Return predictable proposal-only JSON."""
        return {
            "operation_id": self.operation_id,
            "request_id": self.request_id,
            "status": self.status.value,
            "report_ref": None if self.report_ref is None else self.report_ref.as_dict(),
            "error_code": self.error_code,
            "epistemic_status": "EXPLORATORY_SOURCE_SCOUTING",
            "scientific_authority": "NONE_PROPOSAL_ONLY",
            "provider_identity_authority": "UNVERIFIED_CALLER_LABEL",
            "source_snapshot_refs": [],
            "registered_dataset_refs": [],
            "durable_scientific_state_effects": [],
        }


@dataclass(frozen=True, slots=True)
class ScoutedFetchReceipt:
    """Exact candidate-to-existing-acquisition linkage without registration authority."""

    status: ScoutedFetchStatus
    report_ref: SourceScoutingReportRef
    candidate_id: str
    fetch_receipt: FetchReceipt | None
    error_code: str | None = None

    def as_dict(self) -> dict[str, JsonValue]:
        """Return predictable acquisition-only JSON."""
        return {
            "status": self.status.value,
            "report_ref": self.report_ref.as_dict(),
            "candidate_id": self.candidate_id,
            "fetch_receipt": (None if self.fetch_receipt is None else self.fetch_receipt.as_dict()),
            "error_code": self.error_code,
            "epistemic_status": "ACQUIRED_NOT_SCIENTIFICALLY_REGISTERED",
            "scientific_authority": "NONE_ACQUISITION_ONLY",
            "registered_dataset_refs": [],
            "durable_scientific_state_effects": [],
        }


@dataclass(frozen=True, slots=True, init=False)
class RecordedSourceScoutProvider:
    """Passive untrusted response value produced outside the data process."""

    provider_id: str
    _response: dict[str, JsonValue] | None
    error_code: str | None

    def __init__(
        self,
        *,
        provider_id: str,
        response: Mapping[str, JsonValue] | None = None,
        error_code: str | None = None,
    ) -> None:
        """Detach either one response document or one sanitized external failure code."""
        object.__setattr__(self, "provider_id", _provider_id(provider_id))
        if (response is None) == (error_code is None):
            raise ValueError("record exactly one scout response or external failure")
        if error_code is not None:
            if error_code not in _EXTERNAL_FAILURE_CODES:
                raise ValueError("external scout failure code is not allowed")
            object.__setattr__(self, "_response", None)
            object.__setattr__(self, "error_code", error_code)
            return
        if response is None:
            raise ValueError("recorded scout response is missing")
        detached: object = json.loads(_canonical_bytes(dict(response)))
        data = _strict_object(detached, field="recorded provider response")
        object.__setattr__(self, "_response", cast("dict[str, JsonValue]", data))
        object.__setattr__(self, "error_code", None)

    def response_value(self) -> dict[str, JsonValue]:
        """Return detached untrusted JSON without executing external provider code."""
        if self._response is None:
            raise ValueError("external scout attempt has no response")
        value: object = json.loads(_canonical_bytes(self._response))
        return cast("dict[str, JsonValue]", _strict_object(value, field="scout response"))


def _provider_id(value: object) -> str:
    if not isinstance(value, str) or _ID_PATTERN.fullmatch(value) is None:
        raise ValueError("provider_id must be a bounded stable identifier")
    return value


def _decode_provider_response(
    value: object,
    *,
    maximum: int,
) -> tuple[SourceCandidate, ...]:
    data = _strict_object(value, field="source-scout response")
    if set(data) != {"schema_version", "candidates"}:
        raise ValueError("source-scout response schema is not exact")
    if data.get("schema_version") != _RESPONSE_SCHEMA:
        raise ValueError("source-scout response version is unsupported")
    raw_candidates = data.get("candidates")
    if not isinstance(raw_candidates, list):
        raise ValueError("source-scout candidate count exceeds the request")
    candidate_values = cast("list[object]", raw_candidates)
    if len(candidate_values) > maximum:
        raise ValueError("source-scout candidate count exceeds the request")
    candidates = tuple(SourceCandidate.from_provider_dict(item) for item in candidate_values)
    candidate_ids = tuple(candidate.candidate_id for candidate in candidates)
    resource_urls = tuple(candidate.resource_url for candidate in candidates)
    if len(set(candidate_ids)) != len(candidate_ids) or len(set(resource_urls)) != len(
        resource_urls
    ):
        raise ValueError("source-scout candidates cannot be duplicated")
    return candidates


class SourceScoutingService:
    """Proposal ledger and exact handoff to an unchanged `DataWorkspace.fetch`."""

    _workspace_locks_guard: Final[threading.Lock] = threading.Lock()
    _workspace_locks: Final[dict[str, threading.RLock]] = {}

    def __init__(
        self,
        workspace: DataWorkspace,
        provider: RecordedSourceScoutProvider | None = None,
    ) -> None:
        """Bind one optional passive response value to a workspace-local proposal ledger."""
        if provider is not None and type(provider) is not RecordedSourceScoutProvider:
            raise TypeError("source scouting accepts only passive recorded responses")
        self.workspace = workspace
        self.provider = provider
        self.ledger_root = workspace.root / "scouting"
        lock_key = str(self.ledger_root.resolve())
        with self._workspace_locks_guard:
            self._lock = self._workspace_locks.setdefault(lock_key, threading.RLock())
        self._prepare_ledger()
        self._ledger_descriptor = os.open(
            self.ledger_root,
            os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
        )

    def close(self) -> None:
        """Release the descriptor anchoring this service to its verified ledger root."""
        descriptor = getattr(self, "_ledger_descriptor", -1)
        if descriptor >= 0:
            os.close(descriptor)
            self._ledger_descriptor = -1

    def __del__(self) -> None:
        """Best-effort release when an operator does not use `close`."""
        with contextlib.suppress(OSError):
            self.close()

    def scout(
        self,
        request: SourceSearchRequest,
        *,
        idempotency_key: str,
    ) -> SourceScoutingReceipt:
        """Validate and retain one passive response produced outside this process."""
        if self.provider is None:
            raise ValueError("source scouting requires a recorded external response")
        provider_id = _provider_id(self.provider.provider_id)
        key = _strict_text(idempotency_key, field="idempotency_key")
        key_digest = _sha256({"idempotency_key": key})
        operation_id = _sha256(
            {"schema_version": _LEDGER_SCHEMA, "provider_id": provider_id, "key": key_digest}
        )
        operation_path = self.ledger_root / "operations" / f"{operation_id}.json"
        with self._lock:
            if self._record_exists(operation_path):
                return self._replay_operation(
                    operation_path,
                    request=request,
                    provider_id=provider_id,
                    key_digest=key_digest,
                )
            self._publish_exact(
                self.ledger_root / "requests" / f"{request.request_id}.json",
                request.as_dict(),
            )
            if self.provider.error_code is not None:
                receipt = SourceScoutingReceipt(
                    operation_id=operation_id,
                    request_id=request.request_id,
                    status=ScoutingStatus.FAILED,
                    report_ref=None,
                    error_code=self.provider.error_code,
                )
            else:
                try:
                    candidates = _decode_provider_response(
                        self.provider.response_value(),
                        maximum=request.max_candidates,
                    )
                except (TypeError, ValueError):
                    receipt = SourceScoutingReceipt(
                        operation_id=operation_id,
                        request_id=request.request_id,
                        status=ScoutingStatus.FAILED,
                        report_ref=None,
                        error_code="INVALID_PROVIDER_RESPONSE",
                    )
                else:
                    report = self._new_report(request, provider_id, candidates)
                    self._publish_exact(
                        self.ledger_root / "reports" / f"{report.report_id}.json",
                        report.as_dict(),
                    )
                    receipt = SourceScoutingReceipt(
                        operation_id=operation_id,
                        request_id=request.request_id,
                        status=ScoutingStatus.SUCCEEDED,
                        report_ref=report.ref,
                    )
            operation = {
                "schema_version": _LEDGER_SCHEMA,
                "record_type": "scouting_operation",
                "operation_id": operation_id,
                "request_id": request.request_id,
                "provider_id": provider_id,
                "idempotency_sha256": key_digest,
                "receipt": receipt.as_dict(),
            }
            self._publish_exact(operation_path, operation)
            return receipt

    def resolve_report(self, ref: SourceScoutingReportRef) -> SourceScoutingReport:
        """Resolve only the exact report retained by this workspace ledger."""
        try:
            value = self._read_json(self.ledger_root / "reports" / f"{ref.report_id}.json")
            report = self._report_from_dict(value)
        except (OSError, ValueError) as error:
            raise ScoutingResolutionError(
                "scouting report is not issued by this workspace"
            ) from error
        if report.ref != ref:
            raise ScoutingResolutionError("scouting report reference does not match content")
        return report

    def resolve_report_uri(self, uri: str) -> SourceScoutingReportRef:
        """Resolve a stable URI to an issued value-free report reference."""
        prefix, separator, report_id = uri.partition(":")
        if prefix != "scouting" or separator != ":":
            raise ScoutingResolutionError("invalid scouting report URI")
        try:
            report_id = _sha256_identifier(report_id, field="report_id")
        except ValueError as error:
            raise ScoutingResolutionError("invalid scouting report URI") from error
        value = self._read_json(self.ledger_root / "reports" / f"{report_id}.json")
        report = self._report_from_dict(value)
        if report.report_id != report_id:
            raise ScoutingResolutionError("scouting report URI does not match retained content")
        return report.ref

    def acquire_candidate(
        self,
        report_ref: SourceScoutingReportRef,
        *,
        candidate_id: str,
        max_response_bytes: int = 64 * 1024 * 1024,
        timeout_seconds: float = 30.0,
    ) -> ScoutedFetchReceipt:
        """Resolve one issued proposal, then delegate bytes entirely to existing acquisition."""
        try:
            report = self.resolve_report(report_ref)
        except ScoutingResolutionError:
            return ScoutedFetchReceipt(
                status=ScoutedFetchStatus.DENIED,
                report_ref=report_ref,
                candidate_id=candidate_id,
                fetch_receipt=None,
                error_code="UNISSUED_SCOUTING_REPORT",
            )
        candidate = next(
            (item for item in report.candidates if item.candidate_id == candidate_id),
            None,
        )
        if candidate is None:
            return ScoutedFetchReceipt(
                status=ScoutedFetchStatus.DENIED,
                report_ref=report_ref,
                candidate_id=candidate_id,
                fetch_receipt=None,
                error_code="UNKNOWN_SOURCE_CANDIDATE",
            )
        fetch_receipt = self.workspace.fetch(
            FetchRequest(
                url=candidate.resource_url,
                max_response_bytes=max_response_bytes,
                timeout_seconds=timeout_seconds,
            )
        )
        status = (
            ScoutedFetchStatus.SUCCEEDED
            if fetch_receipt.status is FetchStatus.SUCCEEDED
            else ScoutedFetchStatus.FAILED
        )
        result = ScoutedFetchReceipt(
            status=status,
            report_ref=report_ref,
            candidate_id=candidate_id,
            fetch_receipt=fetch_receipt,
            error_code=fetch_receipt.error_code,
        )
        linkage_id = _sha256(
            {
                "schema_version": _LEDGER_SCHEMA,
                "report_id": report_ref.report_id,
                "candidate_id": candidate_id,
                "request_sha256": fetch_receipt.request_sha256,
            }
        )
        self._publish_exact(
            self.ledger_root / "acquisitions" / f"{linkage_id}.json",
            {
                "schema_version": _LEDGER_SCHEMA,
                "record_type": "scouted_acquisition",
                "linkage_id": linkage_id,
                "receipt": result.as_dict(),
            },
        )
        return result

    def _new_report(
        self,
        request: SourceSearchRequest,
        provider_id: str,
        candidates: tuple[SourceCandidate, ...],
        *,
        recorded_at: str | None = None,
    ) -> SourceScoutingReport:
        exact_recorded_at = _strict_timestamp(
            datetime.now(UTC).isoformat() if recorded_at is None else recorded_at,
            field="recorded_at",
        )
        identity_payload = {
            "schema_version": _REPORT_SCHEMA,
            "request": request.as_dict(),
            "provider_id": provider_id,
            "provider_identity_authority": "UNVERIFIED_CALLER_LABEL",
            "candidates": [candidate.as_dict() for candidate in candidates],
            "recorded_at": exact_recorded_at,
        }
        return SourceScoutingReport(
            report_id=_sha256(identity_payload),
            request=request,
            provider_id=provider_id,
            candidates=candidates,
            recorded_at=exact_recorded_at,
        )

    def _report_from_dict(self, value: object) -> SourceScoutingReport:
        data = _strict_object(value, field="stored scouting report")
        expected = {
            "schema_version",
            "request",
            "provider_id",
            "provider_identity_authority",
            "candidates",
            "report_id",
            "recorded_at",
            "epistemic_status",
            "scientific_authority",
            "source_snapshot_refs",
            "registered_dataset_refs",
            "durable_scientific_state_effects",
        }
        if set(data) != expected or data.get("schema_version") != _REPORT_SCHEMA:
            raise ValueError("stored scouting report schema is not exact")
        if (
            data.get("epistemic_status") != "EXPLORATORY_SOURCE_SCOUTING"
            or data.get("scientific_authority") != "NONE_PROPOSAL_ONLY"
            or data.get("provider_identity_authority") != "UNVERIFIED_CALLER_LABEL"
            or data.get("source_snapshot_refs") != []
            or data.get("registered_dataset_refs") != []
            or data.get("durable_scientific_state_effects") != []
        ):
            raise ValueError("stored scouting report authority fields are invalid")
        request = SourceSearchRequest.from_dict(data.get("request"))
        provider_id = _provider_id(data.get("provider_id"))
        raw_candidates = data.get("candidates")
        if not isinstance(raw_candidates, list):
            raise ValueError("stored scouting report candidates are invalid")
        candidate_values = cast("list[object]", raw_candidates)
        if len(candidate_values) > request.max_candidates:
            raise ValueError("stored scouting report candidates are invalid")
        candidates = tuple(SourceCandidate.from_stored_dict(item) for item in candidate_values)
        recorded_at = _strict_timestamp(data.get("recorded_at"), field="recorded_at")
        report = self._new_report(
            request,
            provider_id,
            candidates,
            recorded_at=recorded_at,
        )
        if data.get("report_id") != report.report_id:
            raise ValueError("stored scouting report identity does not match content")
        return report

    def _replay_operation(
        self,
        path: Path,
        *,
        request: SourceSearchRequest,
        provider_id: str,
        key_digest: str,
    ) -> SourceScoutingReceipt:
        value = self._read_json(path)
        expected_operation_keys = {
            "schema_version",
            "record_type",
            "operation_id",
            "request_id",
            "provider_id",
            "idempotency_sha256",
            "receipt",
        }
        if (
            set(value) != expected_operation_keys
            or value.get("schema_version") != _LEDGER_SCHEMA
            or value.get("record_type") != "scouting_operation"
            or value.get("operation_id") != path.stem
            or value.get("request_id") != request.request_id
            or value.get("provider_id") != provider_id
            or value.get("idempotency_sha256") != key_digest
        ):
            raise ScoutingConflictError(
                "idempotency key was already used for a different scouting request"
            )
        raw_receipt = value.get("receipt")
        if not isinstance(raw_receipt, dict):
            raise ScoutingConflictError("stored scouting operation is invalid")
        receipt_data = cast("dict[str, object]", raw_receipt)
        status_value = receipt_data.get("status")
        try:
            status = ScoutingStatus(cast("str", status_value))
        except ValueError as error:
            raise ScoutingConflictError("stored scouting operation status is invalid") from error
        report_ref: SourceScoutingReportRef | None = None
        raw_ref = receipt_data.get("report_ref")
        if raw_ref is not None:
            if not isinstance(raw_ref, dict):
                raise ScoutingConflictError("stored scouting report reference is invalid")
            ref_data = cast("dict[str, object]", raw_ref)
            candidate_ids = ref_data.get("candidate_ids")
            if not isinstance(candidate_ids, list) or not all(
                isinstance(item, str) for item in cast("list[object]", candidate_ids)
            ):
                raise ScoutingConflictError("stored scouting candidate identities are invalid")
            report_ref = SourceScoutingReportRef(
                report_id=cast("str", ref_data.get("report_id")),
                request_id=cast("str", ref_data.get("request_id")),
                provider_id=cast("str", ref_data.get("provider_id")),
                candidate_ids=tuple(cast("list[str]", candidate_ids)),
            )
            self.resolve_report(report_ref)
        receipt = SourceScoutingReceipt(
            operation_id=cast("str", receipt_data.get("operation_id")),
            request_id=cast("str", receipt_data.get("request_id")),
            status=status,
            report_ref=report_ref,
            error_code=cast("str | None", receipt_data.get("error_code")),
        )
        if receipt.operation_id != path.stem or receipt.request_id != request.request_id:
            raise ScoutingConflictError("stored scouting receipt authority does not match")
        if receipt.as_dict() != receipt_data:
            raise ScoutingConflictError("stored scouting receipt does not match content")
        return receipt

    def _prepare_ledger(self) -> None:
        for path in (
            self.ledger_root,
            self.ledger_root / "requests",
            self.ledger_root / "reports",
            self.ledger_root / "operations",
            self.ledger_root / "acquisitions",
        ):
            path.mkdir(mode=0o700, parents=False, exist_ok=True)
            metadata = path.lstat()
            if not stat.S_ISDIR(metadata.st_mode) or path.is_symlink():
                raise ValueError("scouting ledger paths must be real directories")

    def _open_parent(self, path: Path) -> int:
        if path.parent.parent != self.ledger_root or path.parent.name not in {
            "acquisitions",
            "operations",
            "reports",
            "requests",
        }:
            raise ValueError("scouting record path is outside the anchored ledger")
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
        return os.open(path.parent.name, flags, dir_fd=self._ledger_descriptor)

    def _publish_exact(self, path: Path, value: object) -> None:
        content = _canonical_bytes(value) + b"\n"
        if len(content) > _MAX_LEDGER_BYTES:
            raise ValueError("scouting record exceeds the ledger bound")
        parent_descriptor = self._open_parent(path)
        temporary_name = f".{path.name}.{secrets.token_hex(16)}.tmp"
        descriptor = -1
        try:
            descriptor = os.open(
                temporary_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
                0o600,
                dir_fd=parent_descriptor,
            )
            with os.fdopen(descriptor, "wb") as stream:
                descriptor = -1
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(
                    temporary_name,
                    path.name,
                    src_dir_fd=parent_descriptor,
                    dst_dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
                os.fsync(parent_descriptor)
            except FileExistsError:
                if SourceScoutingService._read_regular_at(parent_descriptor, path.name) != content:
                    raise ScoutingConflictError("append-only scouting record conflicts") from None
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            with contextlib.suppress(FileNotFoundError):
                os.unlink(temporary_name, dir_fd=parent_descriptor)
            os.close(parent_descriptor)

    def _read_regular(self, path: Path) -> bytes:
        parent_descriptor = self._open_parent(path)
        try:
            return SourceScoutingService._read_regular_at(parent_descriptor, path.name)
        finally:
            os.close(parent_descriptor)

    def _record_exists(self, path: Path) -> bool:
        try:
            self._read_regular(path)
        except FileNotFoundError:
            return False
        return True

    @staticmethod
    def _read_regular_at(parent_descriptor: int, name: str) -> bytes:
        descriptor = os.open(
            name,
            os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
            dir_fd=parent_descriptor,
        )
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_size > _MAX_LEDGER_BYTES
        ):
            os.close(descriptor)
            raise ValueError("scouting records must be single-link regular files")
        with os.fdopen(descriptor, "rb") as stream:
            content = stream.read(_MAX_LEDGER_BYTES + 1)
        if len(content) > _MAX_LEDGER_BYTES:
            raise ValueError("scouting record exceeds the ledger bound")
        return content

    def _read_json(self, path: Path) -> dict[str, object]:
        value: object = json.loads(self._read_regular(path))
        if not isinstance(value, dict):
            raise ValueError("scouting record must be a JSON object")
        return cast("dict[str, object]", value)


__all__ = [
    "RecordedSourceScoutProvider",
    "ScoutedFetchReceipt",
    "ScoutedFetchStatus",
    "ScoutingConflictError",
    "ScoutingResolutionError",
    "ScoutingStatus",
    "SourceCandidate",
    "SourceScoutingReceipt",
    "SourceScoutingReport",
    "SourceScoutingReportRef",
    "SourceScoutingService",
    "SourceSearchRequest",
]
