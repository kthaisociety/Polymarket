"""Immutable records for independently validated cross-task learning."""

# ruff: noqa: D105, EM101, TRY003

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum

from research_agent.runtime._canonical import content_digest


class LessonKind(Enum):
    """Separate declarative knowledge from reusable procedure."""

    MEMORY = "memory"
    SKILL = "skill"


class LessonDecisionOutcome(Enum):
    """Independent validation result."""

    PROMOTE = "promote"
    REJECT = "reject"


class EvidenceStatus(Enum):
    """Closed evidence vocabulary; only SUCCEEDED is affirmative support."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REJECTED = "rejected"
    CONTRARY = "contrary"
    UNSUPPORTED = "unsupported"
    INVALID = "invalid"


class EvidenceProtection(Enum):
    """Protection classification derived from source authority, never caller input."""

    PERMITTED_HISTORY = "permitted_history"
    PROTECTED = "protected"


@dataclass(frozen=True, slots=True)
class EvidenceSourcePolicy:
    """Trusted bootstrap policy for one historical evidence source."""

    source_authority_id: str
    allowed_environment_refs: tuple[str, ...]
    allowed_task_kinds: tuple[str, ...]
    allowed_subject_tags: tuple[str, ...]
    protection: EvidenceProtection = EvidenceProtection.PERMITTED_HISTORY

    def __post_init__(self) -> None:
        if not self.source_authority_id:
            raise ValueError("Evidence source authority must be explicit.")
        _require_bounded_scope(
            self.allowed_environment_refs,
            self.allowed_task_kinds,
            self.allowed_subject_tags,
        )


@dataclass(frozen=True, slots=True)
class LearningReaderPolicy:
    """Trusted bootstrap policy for reflection and future-context readers."""

    actor_id: str
    readable_source_ids: tuple[str, ...]
    allowed_task_ids: tuple[str, ...]
    allowed_task_kinds: tuple[str, ...]
    allowed_environment_refs: tuple[str, ...]
    allowed_subject_tags: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.actor_id or not self.readable_source_ids or not self.allowed_task_ids:
            raise ValueError("Learning reader authority and bounds must be explicit.")
        _require_bounded_scope(
            self.allowed_environment_refs,
            self.allowed_task_kinds,
            self.allowed_subject_tags,
        )


@dataclass(frozen=True, slots=True)
class KnowledgePublisherPolicy:
    """Trusted bootstrap policy constraining publication and reader grants."""

    authority_id: str
    permitted_actor_ids: tuple[str, ...]
    allowed_task_kinds: tuple[str, ...]
    allowed_environment_refs: tuple[str, ...]
    allowed_subject_tags: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.authority_id or not self.permitted_actor_ids:
            raise ValueError("Knowledge publisher authority and readers must be explicit.")
        _require_bounded_scope(
            self.allowed_environment_refs,
            self.allowed_task_kinds,
            self.allowed_subject_tags,
        )


@dataclass(frozen=True, slots=True)
class EvidenceSourceCapability:
    """Registry-issued capability to register one bounded evidence class."""

    capability_id: str
    policy: EvidenceSourcePolicy

    def __post_init__(self) -> None:
        if self.capability_id != content_digest(_without_first_field(self)):
            raise ValueError("Evidence source capability identity mismatch.")


@dataclass(frozen=True, slots=True)
class LearningReaderCapability:
    """Registry-issued capability for bounded history or knowledge retrieval."""

    capability_id: str
    policy: LearningReaderPolicy

    def __post_init__(self) -> None:
        if self.capability_id != content_digest(_without_first_field(self)):
            raise ValueError("Learning reader capability identity mismatch.")


@dataclass(frozen=True, slots=True)
class LessonValidatorCapability:
    """Registry-issued independent lesson-validation capability."""

    capability_id: str
    authority_id: str

    def __post_init__(self) -> None:
        if self.capability_id != content_digest(_without_first_field(self)):
            raise ValueError("Lesson validator capability identity mismatch.")
        if not self.authority_id:
            raise ValueError("Lesson validator authority must be explicit.")


@dataclass(frozen=True, slots=True)
class KnowledgePublisherCapability:
    """Registry-issued bounded knowledge-publication capability."""

    capability_id: str
    policy: KnowledgePublisherPolicy

    def __post_init__(self) -> None:
        if self.capability_id != content_digest(_without_first_field(self)):
            raise ValueError("Knowledge publisher capability identity mismatch.")


class KnowledgeEntryStatus(Enum):
    """Currentness of an append-only knowledge entry."""

    CURRENT = "current"
    SUPERSEDED = "superseded"


@dataclass(frozen=True, slots=True)
class HistoryEvidence:
    """One permitted historical fact supplied to reflection or validation."""

    evidence_id: str
    source_authority_id: str
    task_id: str
    task_kind: str
    environment_ref: str
    subject_tags: tuple[str, ...]
    status: EvidenceStatus
    summary: str
    source_refs: tuple[str, ...]
    protection: EvidenceProtection
    current: bool = True

    def __post_init__(self) -> None:
        expected = content_digest(_without_first_field(self))
        if self.evidence_id != expected:
            raise ValueError("Historical evidence identity does not match its exact content.")
        if not all(
            (
                self.evidence_id,
                self.source_authority_id,
                self.task_id,
                self.task_kind,
                self.environment_ref,
                self.summary,
            )
        ):
            raise ValueError("Historical evidence identity and meaning must be explicit.")
        if not self.subject_tags or not self.source_refs:
            raise ValueError("Historical evidence must drill down to at least one source.")
        if not _is_evidence_status(self.status) or not _is_evidence_protection(self.protection):
            raise TypeError("Historical evidence status and protection must use closed enums.")

    @property
    def protected(self) -> bool:
        """Expose the authority-derived protection classification compatibly."""
        return self.protection is EvidenceProtection.PROTECTED


@dataclass(frozen=True, slots=True)
class EvidenceOmission:
    """Safe metadata for evidence omitted only because of a declared bound."""

    evidence_id: str
    task_id: str
    task_kind: str
    environment_ref: str
    subject_tags: tuple[str, ...]
    status: EvidenceStatus
    reason: str


@dataclass(frozen=True, slots=True)
class ReflectionEvidenceSelection:
    """Authority-issued complete bounded input to one reflection."""

    selection_id: str
    reader_capability_id: str
    reader_actor_id: str
    scope: ApplicabilityScope
    task_ids: tuple[str, ...]
    max_evidence: int
    evidence: tuple[HistoryEvidence, ...]
    omissions: tuple[EvidenceOmission, ...]

    def __post_init__(self) -> None:
        expected = content_digest(_without_first_field(self))
        if self.selection_id != expected:
            raise ValueError("Reflection selection identity does not match its exact content.")
        if (
            not self.reader_capability_id
            or not self.reader_actor_id
            or not self.task_ids
            or self.max_evidence < 1
        ):
            raise ValueError("Reflection selection authority and task boundary must be explicit.")
        selected_ids = {item.evidence_id for item in self.evidence}
        omitted_ids = {item.evidence_id for item in self.omissions}
        if selected_ids.intersection(omitted_ids):
            raise ValueError("Reflection evidence cannot be both selected and omitted.")
        if not selected_ids and not omitted_ids:
            raise ValueError("Reflection selection cannot be empty.")


@dataclass(frozen=True, slots=True)
class Reflection:
    """Provisional interpretation of a bounded, permitted history."""

    reflection_id: str
    reflector_id: str
    protocol_id: str
    selection_id: str
    scope: ApplicabilityScope
    evidence: tuple[HistoryEvidence, ...]
    omissions: tuple[EvidenceOmission, ...]
    claims: tuple[str, ...]
    uncertainties: tuple[str, ...]
    epistemic_status: str = "PROVISIONAL"

    def __post_init__(self) -> None:
        expected = content_digest(
            (
                "reflection",
                self.reflector_id,
                self.protocol_id,
                self.selection_id,
                self.scope,
                self.evidence,
                self.omissions,
                self.claims,
                self.uncertainties,
                self.epistemic_status,
            )
        )
        if self.reflection_id != expected:
            raise ValueError("Reflection identity does not match its exact content.")
        if self.epistemic_status != "PROVISIONAL":
            raise ValueError("Reflection cannot grant itself validated status.")
        if not self.selection_id or not self.evidence or not self.claims:
            raise ValueError("Reflection requires evidence and at least one explicit claim.")


@dataclass(frozen=True, slots=True)
class ApplicabilityScope:
    """No lesson is globally applicable by default."""

    task_kinds: tuple[str, ...]
    environment_refs: tuple[str, ...]
    subject_tags: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.task_kinds or not self.environment_refs or not self.subject_tags:
            raise ValueError("Learning scope must name task, environment, and subject boundaries.")
        if any(
            item.strip() in {"", "*", "all"}
            for item in (*self.task_kinds, *self.environment_refs, *self.subject_tags)
        ):
            raise ValueError("Universal or empty learning scope is not permitted.")

    def permits(self, query: KnowledgeQuery) -> bool:
        """Return exact structured applicability, not semantic guesswork."""
        return (
            query.task_kind in self.task_kinds
            and query.environment_ref in self.environment_refs
            and set(query.subject_tags).issubset(self.subject_tags)
        )

    def is_subset_of(self, other: ApplicabilityScope) -> bool:
        """Return whether this scope cannot broaden another scope."""
        return (
            set(self.task_kinds).issubset(other.task_kinds)
            and set(self.environment_refs).issubset(other.environment_refs)
            and set(self.subject_tags).issubset(other.subject_tags)
        )


@dataclass(frozen=True, slots=True)
class CandidateLesson:
    """Unvalidated knowledge or procedure proposed from one reflection."""

    candidate_id: str
    reflection_id: str
    proposer_id: str
    kind: LessonKind
    content: str
    scope: ApplicabilityScope
    supporting_evidence_ids: tuple[str, ...]
    contrary_evidence_ids: tuple[str, ...]
    caveats: tuple[str, ...]
    originating_task_ids: tuple[str, ...]
    parent_candidate_ids: tuple[str, ...] = ()
    status: str = "CANDIDATE"

    def __post_init__(self) -> None:
        expected = content_digest(_without_first_field(self))
        if self.candidate_id != expected:
            raise ValueError("Candidate lesson identity does not match its exact content.")
        if self.status != "CANDIDATE":
            raise ValueError("A proposal cannot claim validated learning status.")
        if not self.content.strip() or not self.supporting_evidence_ids:
            raise ValueError("Candidate lesson requires content and supporting evidence.")
        if not self.originating_task_ids or not self.caveats:
            raise ValueError("Candidate lesson requires origin tasks and explicit caveats.")
        if len(set(self.supporting_evidence_ids)) != len(self.supporting_evidence_ids):
            raise ValueError("Supporting evidence cannot be duplicated.")
        if set(self.supporting_evidence_ids).intersection(self.contrary_evidence_ids):
            raise ValueError("Evidence cannot be both supporting and contrary.")


@dataclass(frozen=True, slots=True)
class LessonValidationStandard:
    """Predeclared evidence and independence requirements."""

    standard_id: str
    version: int
    minimum_independent_evidence: int
    minimum_independent_tasks: int
    require_no_unresolved_contrary_evidence: bool = True

    def __post_init__(self) -> None:
        expected = content_digest(_without_first_field(self))
        if self.standard_id != expected:
            raise ValueError("Validation standard identity does not match its exact content.")
        if (
            self.version < 1
            or min(
                self.minimum_independent_evidence,
                self.minimum_independent_tasks,
            )
            < 1
        ):
            raise ValueError("Validation standard bounds must be positive.")


@dataclass(frozen=True, slots=True)
class LessonValidationDecision:
    """Immutable decision issued by an independent configured authority."""

    decision_id: str
    candidate_id: str
    standard_id: str
    validator_authority_id: str
    outcome: LessonDecisionOutcome
    independent_evidence_ids: tuple[str, ...]
    independent_task_ids: tuple[str, ...]
    reasons: tuple[str, ...]
    scope: ApplicabilityScope

    def __post_init__(self) -> None:
        expected = content_digest(_without_first_field(self))
        if self.decision_id != expected:
            raise ValueError("Lesson decision identity does not match its exact content.")
        if not self.reasons:
            raise ValueError("Lesson decision requires explicit reasons.")


@dataclass(frozen=True, slots=True)
class ValidatedLearning:
    """A promoted Memory or Skill; still scoped and caveated."""

    learning_id: str
    candidate_id: str
    decision_id: str
    kind: LessonKind
    content: str
    scope: ApplicabilityScope
    caveats: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    version: int
    supersedes_learning_id: str | None = None

    def __post_init__(self) -> None:
        expected = content_digest(_without_first_field(self))
        if self.learning_id != expected:
            raise ValueError("Validated learning identity does not match its exact content.")
        if self.version < 1 or not self.provenance_refs:
            raise ValueError("Validated learning requires versioned provenance.")


@dataclass(frozen=True, slots=True)
class RejectedLesson:
    """Append-only negative learning evidence."""

    rejection_id: str
    candidate_id: str
    decision_id: str
    reasons: tuple[str, ...]
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        expected = content_digest(_without_first_field(self))
        if self.rejection_id != expected:
            raise ValueError("Rejected lesson identity does not match its exact content.")


@dataclass(frozen=True, slots=True)
class KnowledgeEntry:
    """Published, permission-scoped representation of validated learning."""

    entry_id: str
    learning_id: str
    kind: LessonKind
    content: str
    scope: ApplicabilityScope
    caveats: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    permitted_actor_ids: tuple[str, ...]
    status: KnowledgeEntryStatus
    superseded_by: str | None = None

    def __post_init__(self) -> None:
        expected = content_digest(_without_first_field(self))
        if self.entry_id != expected:
            raise ValueError("Knowledge entry identity does not match its exact content.")
        if not self.permitted_actor_ids:
            raise ValueError("Knowledge publication requires explicit reader authority.")
        if self.status is KnowledgeEntryStatus.CURRENT and self.superseded_by is not None:
            raise ValueError("A current knowledge entry cannot name a superseding entry.")
        if self.status is KnowledgeEntryStatus.SUPERSEDED and not self.superseded_by:
            raise ValueError("A superseded entry must name its replacement.")


@dataclass(frozen=True, slots=True)
class KnowledgeQuery:
    """Exact future-task retrieval surface."""

    actor_id: str
    task_id: str
    task_kind: str
    environment_ref: str
    subject_tags: tuple[str, ...]
    allowed_kinds: tuple[LessonKind, ...] = (LessonKind.MEMORY, LessonKind.SKILL)

    def __post_init__(self) -> None:
        if not all((self.actor_id, self.task_id, self.task_kind, self.environment_ref)):
            raise ValueError("Knowledge query authority and scope must be explicit.")
        if not self.subject_tags or not self.allowed_kinds:
            raise ValueError("Knowledge query requires subject and type bounds.")


@dataclass(frozen=True, slots=True)
class KnowledgeRetrieval:
    """Bounded retrieval result with explicit exclusion count."""

    retrieval_id: str
    query: KnowledgeQuery
    entries: tuple[KnowledgeEntry, ...]
    omitted_count: int

    def __post_init__(self) -> None:
        expected = content_digest(_without_first_field(self))
        if self.retrieval_id != expected:
            raise ValueError("Knowledge retrieval identity does not match its exact content.")
        if self.omitted_count < 0:
            raise ValueError("Omitted count cannot be negative.")


@dataclass(frozen=True, slots=True)
class LearningLedgerEntry:
    """One immutable audit transition in the slow-learning pipeline."""

    entry_id: str
    event_type: str
    subject_id: str
    detail_refs: tuple[str, ...]
    ordinal: int

    def __post_init__(self) -> None:
        expected = content_digest(_without_first_field(self))
        if self.entry_id != expected:
            raise ValueError("Learning ledger entry identity does not match its content.")


def identified(record_type: type[object], **values: object) -> object:
    """Construct an identity-first dataclass from its exact remaining fields."""
    identity_field = fields(record_type)[0].name  # pyright: ignore[reportArgumentType]
    payload = {key: value for key, value in values.items() if key != identity_field}
    values[identity_field] = content_digest(payload)
    return record_type(**values)


def _without_first_field(item: object) -> dict[str, object]:
    record_fields = fields(item)  # pyright: ignore[reportArgumentType]
    return {
        record_field.name: getattr(item, record_field.name) for record_field in record_fields[1:]
    }


def _require_bounded_scope(*groups: tuple[str, ...]) -> None:
    if any(not group for group in groups):
        raise ValueError("Authority scope bounds cannot be empty.")
    if any(item.strip().casefold() in {"", "*", "all"} for group in groups for item in group):
        raise ValueError("Universal authority scope is not permitted.")


def _is_evidence_status(value: object) -> bool:
    return isinstance(value, EvidenceStatus)


def _is_evidence_protection(value: object) -> bool:
    return isinstance(value, EvidenceProtection)


__all__ = [
    "ApplicabilityScope",
    "CandidateLesson",
    "EvidenceOmission",
    "EvidenceProtection",
    "EvidenceSourceCapability",
    "EvidenceSourcePolicy",
    "EvidenceStatus",
    "HistoryEvidence",
    "KnowledgeEntry",
    "KnowledgeEntryStatus",
    "KnowledgePublisherCapability",
    "KnowledgePublisherPolicy",
    "KnowledgeQuery",
    "KnowledgeRetrieval",
    "LearningLedgerEntry",
    "LearningReaderCapability",
    "LearningReaderPolicy",
    "LessonDecisionOutcome",
    "LessonKind",
    "LessonValidationDecision",
    "LessonValidationStandard",
    "LessonValidatorCapability",
    "Reflection",
    "ReflectionEvidenceSelection",
    "RejectedLesson",
    "ValidatedLearning",
    "identified",
]
