"""Validated terminal question memory for authored investigations."""

# ruff: noqa: D105, D107, EM101, TRY003

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import RLock
from typing import TYPE_CHECKING, Protocol

from research_agent.data_foundation._identity import require_aware, stable_identity
from research_agent.investigation.records import QuestionReopenReason
from research_agent.investigation.resolution import (
    AuthoredProtectedResolution,
    AuthoredProtectedResolutionService,
    AuthoredResolutionStatus,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from research_agent.investigation.engine import RuntimeInvestigationCoordinator
    from research_agent.investigation.records import InvestigationRequest


class QuestionMemoryStatus(Enum):
    """Terminal scientific meaning retained across later research tasks."""

    VALIDATED_FINDING = "validated_finding"
    PROTECTED_REJECTION = "protected_rejection"


class QuestionMemoryArchive(Protocol):
    """Crash-durable store bound to one in-process memory publication authority."""

    def bind_authority(self, capability: object) -> None:
        """Bind the archive to one hidden publication capability."""
        ...

    def load(self) -> tuple[QuestionMemoryRecord, ...]:
        """Load exact identity-checked structured records."""
        ...

    def append_issued(
        self,
        record: QuestionMemoryRecord,
        *,
        capability: object,
    ) -> QuestionMemoryRecord:
        """Append only through the configured memory authority."""
        ...

    def refresh_markdown(self) -> None:
        """Rebuild presentation views from structured records."""
        ...


@dataclass(frozen=True, slots=True)
class QuestionMemoryRecord:
    """Authority-issued terminal question outcome with exact evidence ancestry."""

    memory_id: str
    question_fingerprint: str
    question_id: str
    question_text: str
    environment_id: str
    catalog_id: str
    registration_id: str
    candidate_id: str
    development_evidence_id: str
    protected_resolution_id: str
    status: QuestionMemoryStatus
    terminal_evidence_ref: str
    evidence_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    resolved_at: datetime

    def __post_init__(self) -> None:
        require_aware(self.resolved_at, "question memory resolved_at")
        if not self.evidence_refs or not self.reason_codes or not self.terminal_evidence_ref:
            raise ValueError("question memory requires exact terminal evidence")
        if self.memory_id != stable_identity("validated-question-memory", _memory_payload(self)):
            raise ValueError("question memory identity does not match content")


class QuestionAlreadyResolvedError(ValueError):
    """The same question/catalog meaning already has a terminal protected outcome."""

    def __init__(self, message: str, record: QuestionMemoryRecord | None = None) -> None:
        super().__init__(message)
        self.record = record


class ValidatedQuestionMemory:
    """Append-only terminal memory; callers cannot publish their own conclusions."""

    def __init__(
        self,
        *,
        capability: object,
        archive: QuestionMemoryArchive | None = None,
    ) -> None:
        self._capability = capability
        self._archive = archive
        loaded = () if archive is None else archive.load()
        self._records: dict[str, QuestionMemoryRecord] = {}
        for record in loaded:
            prior = self._records.get(record.question_fingerprint)
            if prior is not None and prior != record:
                raise ValueError("durable question memory contains conflicting terminal outcomes")
            self._records[record.question_fingerprint] = record
        self._lock = RLock()

    def __copy__(self) -> ValidatedQuestionMemory:
        raise TypeError("validated question memory authority cannot be copied")

    def __deepcopy__(self, memo: dict[int, object]) -> ValidatedQuestionMemory:
        del memo
        raise TypeError("validated question memory authority cannot be copied")

    def require_open(self, request: InvestigationRequest) -> None:
        """Reject an exact question/catalog meaning that already reached a terminal result."""
        fingerprint = question_fingerprint(request)
        with self._lock:
            prior = self._records.get(fingerprint)
            if prior is not None:
                message = f"research question already resolved at memory {prior.memory_id}"
                raise QuestionAlreadyResolvedError(message, prior)
            reopen = request.reopen
            if reopen is not None:
                ancestor = next(
                    (
                        record
                        for record in self._records.values()
                        if record.memory_id == reopen.prior_memory_id
                    ),
                    None,
                )
                if ancestor is None:
                    raise QuestionAlreadyResolvedError(
                        "question reopen references unknown terminal memory"
                    )
                if ancestor.environment_id != request.question.environment_id:
                    raise QuestionAlreadyResolvedError(
                        "question reopen crosses its prior research environment",
                        ancestor,
                    )
                if (
                    reopen.reason is QuestionReopenReason.NEW_CATALOG
                    and ancestor.catalog_id == request.catalog.identity
                ):
                    raise QuestionAlreadyResolvedError(
                        "new-catalog reopen did not change exact catalog identity",
                        ancestor,
                    )
                if (
                    reopen.reason is QuestionReopenReason.MATERIAL_HYPOTHESIS
                    and _normalized_question(ancestor.question_text)
                    == _normalized_question(request.question.text)
                ):
                    raise QuestionAlreadyResolvedError(
                        "material-hypothesis reopen did not change normalized question meaning",
                        ancestor,
                    )
                return
            lineage = tuple(
                record
                for record in self._records.values()
                if record.environment_id == request.question.environment_id
                and record.question_id == request.question.question_id
            )
            if lineage:
                prior = lineage[-1]
                raise QuestionAlreadyResolvedError(
                    "resolved question lineage requires an explicit reopen declaration",
                    prior,
                )

    def get(self, request: InvestigationRequest) -> QuestionMemoryRecord | None:
        """Resolve exact prior terminal meaning without semantic-nearest fallback."""
        with self._lock:
            return self._records.get(question_fingerprint(request))

    def records(self) -> tuple[QuestionMemoryRecord, ...]:
        """Return every terminal question outcome without winner-only filtering."""
        with self._lock:
            return tuple(self._records.values())

    def context_for(
        self,
        request: InvestigationRequest,
        *,
        limit: int = 8,
    ) -> tuple[QuestionMemoryRecord, ...]:
        """Return bounded exact-lineage memory without semantic-nearest retrieval."""
        if limit < 1:
            raise ValueError("question memory context limit must be positive")
        reopen_memory_id = None if request.reopen is None else request.reopen.prior_memory_id
        with self._lock:
            relevant = tuple(
                record
                for record in self._records.values()
                if record.environment_id == request.question.environment_id
                and (
                    record.question_id == request.question.question_id
                    or record.memory_id == reopen_memory_id
                )
            )
        ordered = sorted(relevant, key=lambda item: (item.resolved_at, item.memory_id))
        return tuple(ordered[-limit:])

    def refresh_presentations(self) -> None:
        """Repair derived human views without changing any scientific record."""
        with self._lock:
            if self._archive is not None:
                self._archive.refresh_markdown()

    def record_issued(
        self,
        record: QuestionMemoryRecord,
        *,
        capability: object,
    ) -> QuestionMemoryRecord:
        """Publish only through the hidden capability held by the configured recorder."""
        if capability is not self._capability:
            raise ValueError("question memory record was not authority-issued")
        with self._lock:
            prior = self._records.get(record.question_fingerprint)
            if prior is not None:
                if prior != record:
                    raise QuestionAlreadyResolvedError(
                        "resolved question cannot acquire a second terminal outcome"
                    )
                return prior
            if self._archive is not None:
                try:
                    archived = self._archive.append_issued(record, capability=capability)
                except ValueError:
                    if record in self._archive.load():
                        self._records[record.question_fingerprint] = record
                    raise
                if archived != record:
                    raise ValueError("durable question memory changed the issued record")
            self._records[record.question_fingerprint] = record
            return record


class QuestionMemoryRecorder:
    """Translate only service-issued findings/rejections into terminal memory."""

    def __init__(
        self,
        *,
        investigations: RuntimeInvestigationCoordinator,
        resolutions: AuthoredProtectedResolutionService,
        memory: ValidatedQuestionMemory,
        capability: object,
        clock: Callable[[], datetime],
    ) -> None:
        self._investigations = investigations
        self._resolutions = resolutions
        self._memory = memory
        self._capability = capability
        self._clock = clock

    def __copy__(self) -> QuestionMemoryRecorder:
        raise TypeError("question memory recorder authority cannot be copied")

    def __deepcopy__(self, memo: dict[int, object]) -> QuestionMemoryRecorder:
        del memo
        raise TypeError("question memory recorder authority cannot be copied")

    def record(self, resolution: AuthoredProtectedResolution) -> QuestionMemoryRecord:
        """Record one exact independently resolved finding or protected rejection."""
        self._resolutions.require_issued(resolution)
        if resolution.status is AuthoredResolutionStatus.DENIED:
            raise ValueError("governance denial does not resolve the scientific question")
        registration, _, _ = self._investigations.require_credible(
            candidate_id=resolution.candidate_id,
            evidence_id=resolution.evidence_id,
        )
        request = registration.request
        prior = self._memory.get(request)
        if prior is not None:
            if prior.protected_resolution_id != resolution.resolution_id:
                raise QuestionAlreadyResolvedError(
                    "resolved question cannot acquire a different protected resolution"
                )
            self._memory.refresh_presentations()
            return prior
        terminal_ref = (
            resolution.finding_id
            if resolution.status is AuthoredResolutionStatus.FINDING
            else resolution.negative_result_id
        )
        if terminal_ref is None:
            raise ValueError("terminal protected resolution lost its evidence reference")
        status = (
            QuestionMemoryStatus.VALIDATED_FINDING
            if resolution.status is AuthoredResolutionStatus.FINDING
            else QuestionMemoryStatus.PROTECTED_REJECTION
        )
        resolved_at = self._clock()
        payload = {
            "question_fingerprint": question_fingerprint(request),
            "question_id": request.question.question_id,
            "question_text": request.question.text,
            "environment_id": request.question.environment_id,
            "catalog_id": request.catalog.identity,
            "registration_id": registration.registration_id,
            "candidate_id": resolution.candidate_id,
            "development_evidence_id": resolution.evidence_id,
            "protected_resolution_id": resolution.resolution_id,
            "status": status,
            "terminal_evidence_ref": terminal_ref,
            "evidence_refs": resolution.evidence_refs,
            "reason_codes": resolution.reason_codes,
            "resolved_at": resolved_at,
        }
        record = QuestionMemoryRecord(
            stable_identity("validated-question-memory", payload),
            question_fingerprint(request),
            request.question.question_id,
            request.question.text,
            request.question.environment_id,
            request.catalog.identity,
            registration.registration_id,
            resolution.candidate_id,
            resolution.evidence_id,
            resolution.resolution_id,
            status,
            terminal_ref,
            resolution.evidence_refs,
            resolution.reason_codes,
            resolved_at,
        )
        return self._memory.record_issued(record, capability=self._capability)


class QuestionMemoryRecorderIssuer:
    """Bind the hidden memory capability after runtime services are composed."""

    def __init__(self, *, memory: ValidatedQuestionMemory, capability: object) -> None:
        self._memory = memory
        self._capability = capability

    def __copy__(self) -> QuestionMemoryRecorderIssuer:
        raise TypeError("question memory recorder issuer cannot be copied")

    def __deepcopy__(self, memo: dict[int, object]) -> QuestionMemoryRecorderIssuer:
        del memo
        raise TypeError("question memory recorder issuer cannot be copied")

    def bind(
        self,
        *,
        investigations: RuntimeInvestigationCoordinator,
        resolutions: AuthoredProtectedResolutionService,
        clock: Callable[[], datetime],
    ) -> QuestionMemoryRecorder:
        """Create the recorder only after its exact upstream authorities exist."""
        return QuestionMemoryRecorder(
            investigations=investigations,
            resolutions=resolutions,
            memory=self._memory,
            capability=self._capability,
            clock=clock,
        )


def configure_validated_question_memory(
    archive: QuestionMemoryArchive | None = None,
) -> tuple[
    ValidatedQuestionMemory,
    QuestionMemoryRecorderIssuer,
]:
    """Create one memory registry and its non-reconstructible recorder issuer."""
    capability = object()
    if archive is not None:
        archive.bind_authority(capability)
    memory = ValidatedQuestionMemory(capability=capability, archive=archive)
    return memory, QuestionMemoryRecorderIssuer(memory=memory, capability=capability)


def question_fingerprint(request: InvestigationRequest) -> str:
    """Bind normalized question meaning to exact data content and environment."""
    normalized = _normalized_question(request.question.text)
    return stable_identity(
        "research-question-fingerprint",
        {
            "normalized_text": normalized,
            "environment_id": request.question.environment_id,
            "catalog_id": request.catalog.identity,
        },
    )


def _normalized_question(text: str) -> str:
    return " ".join(text.casefold().split())


def _memory_payload(record: QuestionMemoryRecord) -> dict[str, object]:
    return {
        name: getattr(record, name) for name in record.__dataclass_fields__ if name != "memory_id"
    }


__all__ = [
    "QuestionAlreadyResolvedError",
    "QuestionMemoryArchive",
    "QuestionMemoryRecord",
    "QuestionMemoryRecorder",
    "QuestionMemoryRecorderIssuer",
    "QuestionMemoryStatus",
    "ValidatedQuestionMemory",
    "configure_validated_question_memory",
    "question_fingerprint",
]
