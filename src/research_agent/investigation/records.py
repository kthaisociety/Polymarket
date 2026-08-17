"""Immutable records for creativity-first autonomous investigations."""

# ruff: noqa: D102, D105, EM101, PLR2004, TRY003

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import TYPE_CHECKING, Protocol

from research_agent.data_foundation._identity import require_aware, stable_identity

if TYPE_CHECKING:
    from datetime import datetime

    from research_agent.data_foundation import DataCatalogSnapshot, FieldRef, SampleKey
    from research_agent.data_foundation.temporal import TemporalOffset
    from research_agent.development.records import TrialRecord


class DevelopmentDisposition(Enum):
    """Harness-owned result of applying the predeclared development rule."""

    REVISE = "revise"
    REJECT = "reject"
    CREDIBLE = "credible"


class QuestionStatus(Enum):
    """Current research status without claiming protected validation."""

    ACTIVE = "active"
    NEGATIVE = "negative"
    CREDIBLE_CANDIDATE = "credible_candidate"


class QuestionReopenReason(Enum):
    """Explicit structural reason that a prior terminal question may be revisited."""

    NEW_CATALOG = "new_catalog"
    MATERIAL_HYPOTHESIS = "material_hypothesis"


@dataclass(frozen=True, slots=True)
class QuestionReopenDeclaration:
    """Link a new investigation to prior terminal memory without erasing it."""

    prior_memory_id: str
    reason: QuestionReopenReason
    rationale: str

    def __post_init__(self) -> None:
        if not self.prior_memory_id or not self.rationale.strip():
            raise ValueError("question reopen ancestry and rationale must be explicit")


@dataclass(frozen=True, slots=True)
class ResearchQuestion:
    """Exact research question from which investigation starts."""

    question_id: str
    text: str
    environment_id: str
    task_ref: str
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not all(
            (self.question_id, self.text, self.environment_id, self.task_ref, self.evidence_refs)
        ):
            raise ValueError("research question meaning and provenance must be explicit")


@dataclass(frozen=True, slots=True)
class DevelopmentBudget:
    """Predeclared search and credibility boundary."""

    max_trials: int
    minimum_training_rows: int
    minimum_oof_predictions: int
    primary_metric: str
    credible_at_or_below: float

    def __post_init__(self) -> None:
        if (
            self.max_trials < 1
            or self.minimum_training_rows < 2
            or self.minimum_oof_predictions < 1
        ):
            raise ValueError("development search and evidence bounds must be positive")
        if self.primary_metric not in {"mse", "mae"}:
            raise ValueError("unsupported primary development metric")
        if not isfinite(self.credible_at_or_below) or self.credible_at_or_below < 0:
            raise ValueError("development credibility threshold must be finite and non-negative")

    @property
    def identity(self) -> str:
        return stable_identity("authored-development-budget", self)


@dataclass(frozen=True, slots=True)
class ProtectedEvaluationPredeclaration:
    """Exact downstream protocol identities fixed before authored development begins."""

    data_protocol_ref: str
    training_protocol_ref: str
    scenario_ref: str
    decision_times_ref: str
    evaluation_spec_ref: str
    validation_standard_ref: str
    protected_scope_id: str
    claim_template_ref: str
    freeze_standard_ref: str

    def __post_init__(self) -> None:
        values = (
            self.data_protocol_ref,
            self.training_protocol_ref,
            self.scenario_ref,
            self.decision_times_ref,
            self.evaluation_spec_ref,
            self.validation_standard_ref,
            self.protected_scope_id,
            self.claim_template_ref,
            self.freeze_standard_ref,
        )
        if not all(values) or len(set(values)) != len(values):
            raise ValueError("protected protocol identities must be explicit and distinct")

    @property
    def protocol_refs(self) -> tuple[str, ...]:
        """Return the exact ordered protocol set bound into a frozen identity."""
        return (
            self.data_protocol_ref,
            self.training_protocol_ref,
            self.scenario_ref,
            self.decision_times_ref,
            self.evaluation_spec_ref,
            self.validation_standard_ref,
            self.protected_scope_id,
            self.claim_template_ref,
        )


@dataclass(frozen=True, slots=True)
class AuthoredCandidateManifest:
    """Scientific meaning surrounding arbitrary researcher-authored source."""

    question_id: str
    environment_id: str
    predictor_fields: tuple[FieldRef, ...]
    outcome_field: FieldRef
    horizon: TemporalOffset
    minimum_outcome_points: int
    population_dimensions: tuple[tuple[str, str], ...]
    feature_names: tuple[str, ...]
    missing_value_policy: str
    evidence_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    population_dimension_names: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not all(
            (
                self.question_id,
                self.environment_id,
                self.predictor_fields,
                self.feature_names,
                self.missing_value_policy,
                self.evidence_refs,
                self.provenance_refs,
            )
        ):
            raise ValueError("authored candidate manifest is incomplete")
        if not self.horizon.is_positive or self.minimum_outcome_points < 1:
            raise ValueError("authored target horizon and path requirement must be positive")
        field_ids = tuple(item.field_id for item in self.predictor_fields)
        if len(set(self.predictor_fields)) != len(self.predictor_fields) or len(
            set(field_ids)
        ) != len(field_ids):
            raise ValueError("predictor dependencies must be exact and unambiguous")
        if any(item.environment_id != self.environment_id for item in self.predictor_fields):
            raise ValueError("predictor dependencies cross the candidate environment")
        if self.outcome_field.environment_id != self.environment_id:
            raise ValueError("outcome dependency crosses the candidate environment")
        if len(set(self.feature_names)) != len(self.feature_names) or any(
            not item for item in self.feature_names
        ):
            raise ValueError("authored feature output names must be unique and explicit")
        exact_dimensions, panel_names = _canonical_population_scope(
            self.population_dimensions,
            self.population_dimension_names,
        )
        object.__setattr__(self, "population_dimensions", exact_dimensions)
        object.__setattr__(self, "population_dimension_names", panel_names)
        if self.missing_value_policy not in {"exclude_example", "fail_trial"}:
            raise ValueError("unknown authored candidate missing-value policy")

    def admits_population(self, dimensions: tuple[tuple[str, str], ...]) -> bool:
        """Return whether one exact sample slice has the declared population meaning."""
        canonical = tuple(sorted(dimensions))
        if self.population_dimension_names:
            return tuple(name for name, _ in canonical) == self.population_dimension_names
        return canonical == self.population_dimensions

    @property
    def identity(self) -> str:
        return stable_identity("authored-candidate-manifest", self)


def _canonical_population_scope(
    exact_dimensions: tuple[tuple[str, str], ...],
    panel_names: tuple[str, ...],
) -> tuple[tuple[tuple[str, str], ...], tuple[str, ...]]:
    if any(not name or not value for name, value in exact_dimensions):
        raise ValueError("candidate population dimensions must be explicit")
    exact_names = tuple(name for name, _ in exact_dimensions)
    if len(set(exact_names)) != len(exact_names):
        raise ValueError("candidate population dimensions must be unique")
    if any(not name for name in panel_names) or len(set(panel_names)) != len(panel_names):
        raise ValueError("candidate panel dimension names must be unique and explicit")
    if exact_dimensions and panel_names:
        raise ValueError("candidate population cannot mix exact and panel dimensions")
    return tuple(sorted(exact_dimensions)), tuple(sorted(panel_names))


@dataclass(frozen=True, slots=True)
class AuthoredProgramProposal:
    """Untrusted proposal carrying source but no publication authority."""

    source: str
    manifest: AuthoredCandidateManifest
    rationale: str
    parent_trial_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.source or not self.rationale:
            raise ValueError("authored source and rationale are required")


@dataclass(frozen=True, slots=True)
class AuthoredCandidate:
    """Authority-published exact source, manifest, and trial ancestry."""

    candidate_id: str
    source: str
    source_sha256: str
    manifest: AuthoredCandidateManifest
    rationale: str
    parent_trial_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        digest = hashlib.sha256(self.source.encode()).hexdigest()
        if digest != self.source_sha256:
            raise ValueError("authored candidate source digest does not match content")
        expected = stable_identity("authored-candidate", _candidate_payload(self))
        if self.candidate_id != expected:
            raise ValueError("authored candidate identity does not match content")


@dataclass(frozen=True, slots=True)
class ProgramAccess:
    """Harness-observed access made by one authored entrypoint."""

    entrypoint: str
    ordinal: int
    interface: str
    field_id: str | None


@dataclass(frozen=True, slots=True)
class AuthoredDevelopmentEvidence:
    """Selection-exposed out-of-fold evidence for one exact candidate trial."""

    evidence_id: str
    trial_id: str
    candidate_id: str
    catalog_id: str
    budget_id: str
    row_keys: tuple[SampleKey, ...]
    predictions: tuple[float, ...]
    outcomes: tuple[float, ...]
    metrics: tuple[tuple[str, float], ...]
    feature_accesses: tuple[ProgramAccess, ...]
    label_accesses: tuple[ProgramAccess, ...]
    fit_accesses: tuple[ProgramAccess, ...]
    prediction_accesses: tuple[ProgramAccess, ...]
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if len(self.predictions) != len(self.outcomes) or not self.metrics:
            raise ValueError("development evidence is incomplete")
        if any(not isfinite(item) for item in (*self.predictions, *self.outcomes)):
            raise ValueError("development evidence must be finite")
        if any(not isfinite(value) for _, value in self.metrics):
            raise ValueError("development metrics must be finite")
        expected = stable_identity("authored-development-evidence", _evidence_payload(self))
        if self.evidence_id != expected:
            raise ValueError("development evidence identity does not match content")


@dataclass(frozen=True, slots=True)
class ResearcherContext:
    """Bounded context returned to the researcher before one proposal."""

    question: ResearchQuestion
    schema_refs: tuple[str, ...]
    field_descriptions: tuple[tuple[str, str], ...]
    budget: DevelopmentBudget
    trial_ordinal: int
    prior_evidence: tuple[AuthoredDevelopmentEvidence, ...]


class Researcher(Protocol):
    """Provider-neutral intelligence boundary for authored proposals."""

    def propose(self, context: ResearcherContext) -> AuthoredProgramProposal:
        """Return one authored candidate revision from bounded context."""
        ...


@dataclass(frozen=True, slots=True)
class InvestigationRequest:
    """Exact application input: question, authorized data, sample scope, and budget."""

    question: ResearchQuestion
    catalog: DataCatalogSnapshot
    sample_keys: tuple[SampleKey, ...]
    current_time: datetime
    budget: DevelopmentBudget
    random_seed: int
    protected_predeclaration: ProtectedEvaluationPredeclaration | None = None
    reopen: QuestionReopenDeclaration | None = None

    def __post_init__(self) -> None:
        require_aware(self.current_time, "investigation current_time")
        if not self.sample_keys or len(set(self.sample_keys)) != len(self.sample_keys):
            raise ValueError("investigation sample keys must be non-empty and unique")
        if self.question.environment_id != self.catalog.environment_id:
            raise ValueError("question and catalog environments differ")


@dataclass(frozen=True, slots=True)
class InvestigationResult:
    """Application result without protected-validation authority."""

    question: ResearchQuestion
    disposition: DevelopmentDisposition
    question_status: QuestionStatus
    trials_attempted: int
    candidate: AuthoredCandidate | None
    evidence: tuple[AuthoredDevelopmentEvidence, ...]
    trial_ledger: tuple[TrialRecord, ...]


@dataclass(frozen=True, slots=True)
class RegisteredInvestigation:
    """Composition-authorized question/data/budget scope for runtime-authored trials."""

    registration_id: str
    session_id: str
    episode_id: str
    request: InvestigationRequest

    def __post_init__(self) -> None:
        expected = stable_identity("registered-investigation", _registration_payload(self))
        if self.registration_id != expected:
            raise ValueError("investigation registration identity does not match content")


@dataclass(frozen=True, slots=True)
class RuntimeTrialReceipt:
    """One idempotent runtime execution of an authored development proposal."""

    receipt_id: str
    registration_id: str
    idempotency_key: str
    trial_ordinal: int
    trial_id: str | None
    execution_status: str
    disposition: DevelopmentDisposition
    question_status: QuestionStatus
    candidate_id: str | None
    evidence_id: str | None
    primary_metric: tuple[str, float] | None
    failure_detail: str | None
    ledger_event_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.execution_status not in {"succeeded", "failed"}:
            raise ValueError("runtime trial execution status is invalid")
        if self.execution_status == "succeeded" and (
            self.candidate_id is None
            or self.evidence_id is None
            or self.primary_metric is None
            or self.failure_detail is not None
        ):
            raise ValueError("successful runtime trial receipt is incomplete")
        if self.execution_status == "failed" and not self.failure_detail:
            raise ValueError("failed runtime trial receipt requires a safe failure detail")
        expected = stable_identity("runtime-trial-receipt", _runtime_receipt_payload(self))
        if self.receipt_id != expected:
            raise ValueError("runtime trial receipt identity does not match content")


def _candidate_payload(candidate: AuthoredCandidate) -> dict[str, object]:
    return {
        "source_sha256": candidate.source_sha256,
        "manifest_id": candidate.manifest.identity,
        "rationale": candidate.rationale,
        "parent_trial_ids": candidate.parent_trial_ids,
    }


def _evidence_payload(evidence: AuthoredDevelopmentEvidence) -> dict[str, object]:
    return {
        "trial_id": evidence.trial_id,
        "candidate_id": evidence.candidate_id,
        "catalog_id": evidence.catalog_id,
        "budget_id": evidence.budget_id,
        "row_keys": evidence.row_keys,
        "predictions": evidence.predictions,
        "outcomes": evidence.outcomes,
        "metrics": evidence.metrics,
        "feature_accesses": evidence.feature_accesses,
        "label_accesses": evidence.label_accesses,
        "fit_accesses": evidence.fit_accesses,
        "prediction_accesses": evidence.prediction_accesses,
        "warnings": evidence.warnings,
    }


def _registration_payload(registration: RegisteredInvestigation) -> dict[str, object]:
    request = registration.request
    return {
        "session_id": registration.session_id,
        "episode_id": registration.episode_id,
        "question": request.question,
        "catalog_id": request.catalog.identity,
        "sample_keys": request.sample_keys,
        "current_time": request.current_time,
        "budget_id": request.budget.identity,
        "random_seed": request.random_seed,
        "protected_predeclaration": request.protected_predeclaration,
        "reopen": request.reopen,
    }


def _runtime_receipt_payload(receipt: RuntimeTrialReceipt) -> dict[str, object]:
    return {
        "registration_id": receipt.registration_id,
        "idempotency_key": receipt.idempotency_key,
        "trial_ordinal": receipt.trial_ordinal,
        "trial_id": receipt.trial_id,
        "execution_status": receipt.execution_status,
        "disposition": receipt.disposition,
        "question_status": receipt.question_status,
        "candidate_id": receipt.candidate_id,
        "evidence_id": receipt.evidence_id,
        "primary_metric": receipt.primary_metric,
        "failure_detail": receipt.failure_detail,
        "ledger_event_ids": receipt.ledger_event_ids,
    }


__all__ = [
    "AuthoredCandidate",
    "AuthoredCandidateManifest",
    "AuthoredDevelopmentEvidence",
    "AuthoredProgramProposal",
    "DevelopmentBudget",
    "DevelopmentDisposition",
    "InvestigationRequest",
    "InvestigationResult",
    "ProgramAccess",
    "ProtectedEvaluationPredeclaration",
    "QuestionReopenDeclaration",
    "QuestionReopenReason",
    "QuestionStatus",
    "RegisteredInvestigation",
    "ResearchQuestion",
    "Researcher",
    "ResearcherContext",
    "RuntimeTrialReceipt",
]
