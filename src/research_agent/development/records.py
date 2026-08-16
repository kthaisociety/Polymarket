"""Immutable development records, protocols, and append-only trial lineage."""

# ruff: noqa: D102, D105, D107, N818, PLR0913

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING

from research_agent.data_foundation._identity import require_aware, stable_identity

if TYPE_CHECKING:
    from research_agent.data_foundation.observations import DimensionValues, Scalar


class DevelopmentStatus(Enum):
    """Epistemic status available to the development subsystem."""

    DEVELOPMENT = "development"
    FAILED = "failed"


class TrainingFailureCode(Enum):
    """Blocking reasons that can never be converted into another recipe silently."""

    WINDOW_NOT_READY = "window_not_ready"
    INCOMPATIBLE_IDENTITY = "incompatible_identity"
    UNSUPPORTED_RECIPE = "unsupported_recipe"
    INVALID_TRAINING_DATA = "invalid_training_data"
    SINGULAR_SYSTEM = "singular_system"
    FIT_FAILED = "fit_failed"
    INFERENCE_FAILED = "inference_failed"


@dataclass(frozen=True, slots=True)
class TrainingFailure:
    """Typed formal failure with exact recipe and training-boundary provenance."""

    failure_id: str
    code: TrainingFailureCode
    system_definition_id: str
    model_definition_id: str | None
    training_window_id: str
    detail: str
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        expected = stable_identity("training-failure", _failure_payload(self))
        if self.failure_id != expected:
            msg = "training-failure identity does not match content"
            raise ValueError(msg)

    @classmethod
    def create(
        cls,
        code: TrainingFailureCode,
        *,
        system_definition_id: str,
        training_window_id: str,
        detail: str,
        provenance_refs: tuple[str, ...],
        model_definition_id: str | None = None,
    ) -> TrainingFailure:
        payload = {
            "code": code,
            "system_definition_id": system_definition_id,
            "model_definition_id": model_definition_id,
            "training_window_id": training_window_id,
            "detail": detail,
            "provenance_refs": provenance_refs,
        }
        return cls(
            failure_id=stable_identity("training-failure", payload),
            code=code,
            system_definition_id=system_definition_id,
            model_definition_id=model_definition_id,
            training_window_id=training_window_id,
            detail=detail,
            provenance_refs=provenance_refs,
        )


class TrainingBlocked(RuntimeError):
    """Raised when the exact formal fitting or inference recipe cannot execute."""

    def __init__(self, failure: TrainingFailure) -> None:
        super().__init__(failure.detail)
        self.failure = failure


@dataclass(frozen=True, slots=True)
class LearnedTransformState:
    """Trainer-owned parameters for one declared fitted feature-expression slot."""

    state_id: str
    state_slot: str
    feature_definition_id: str
    training_window_id: str
    fitted_through: datetime
    parameters: tuple[tuple[str, float], ...]
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        require_aware(self.fitted_through, "fitted_through")
        names = tuple(name for name, _ in self.parameters)
        if len(set(names)) != len(names) or not self.provenance_refs:
            msg = "learned-transform parameters and provenance must be exact"
            raise ValueError(msg)
        expected = stable_identity("learned-transform", _transform_payload(self))
        if self.state_id != expected:
            msg = "learned-transform identity does not match content"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class FittedModelState:
    """Dependency-light learned state for one exact model recipe."""

    fitted_model_id: str
    model_definition_id: str
    training_window_id: str
    algorithm: str
    input_feature_ids: tuple[str, ...]
    coefficients: tuple[float, ...]
    intercept: float
    expansion_terms: tuple[tuple[int, ...], ...]
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.input_feature_ids or not self.provenance_refs:
            msg = "fitted model requires exact inputs and provenance"
            raise ValueError(msg)
        if len(self.coefficients) != len(self.expansion_terms):
            msg = "fitted coefficients must match exact expansion terms"
            raise ValueError(msg)
        feature_count = len(self.input_feature_ids)
        if any(
            not term or any(index < 0 or index >= feature_count for index in term)
            for term in self.expansion_terms
        ):
            msg = "fitted expansion term references an unknown feature dimension"
            raise ValueError(msg)
        expected = stable_identity("fitted-model-state", _model_payload(self))
        if self.fitted_model_id != expected:
            msg = "fitted-model-state identity does not match content"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class FitRecord:
    """Reconstructible record of every learned component in one successful fit."""

    fit_id: str
    system_definition_id: str
    training_window_id: str
    training_sample_id: str
    environment_id: str
    fitted_through: datetime
    row_ids: tuple[str, ...]
    model_state_ids: tuple[str, ...]
    transform_state_ids: tuple[str, ...]
    procedure_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    training_information_bundle_id: str | None = None
    information_set_ids: tuple[str, ...] = ()
    feature_series_ids: tuple[str, ...] = ()
    compiled_feature_ids: tuple[str, ...] = ()
    status: DevelopmentStatus = DevelopmentStatus.DEVELOPMENT

    def __post_init__(self) -> None:
        require_aware(self.fitted_through, "fitted_through")
        if not self.row_ids or not self.model_state_ids or not self.provenance_refs:
            msg = "successful fit requires rows, model state, and provenance"
            raise ValueError(msg)
        legal_feature_refs = (
            self.information_set_ids,
            self.feature_series_ids,
            self.compiled_feature_ids,
        )
        if self.training_information_bundle_id is None:
            if any(legal_feature_refs):
                msg = "fit cannot claim formal training views without their exact bundle"
                raise ValueError(msg)
        elif (
            len(self.information_set_ids) != len(self.row_ids)
            or not self.feature_series_ids
            or not self.compiled_feature_ids
        ):
            msg = "formal fit requires every row view and compiled feature series identity"
            raise ValueError(msg)
        expected = stable_identity("fit-record", _fit_payload(self))
        if self.fit_id != expected:
            msg = "fit-record identity does not match content"
            raise ValueError(msg)
        if self.status is not DevelopmentStatus.DEVELOPMENT:
            msg = "a successful development fit cannot claim another evidence status"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class FittedPredictiveSystem:
    """Immutable fitted state for the exact candidate and legal training window."""

    fitted_system_id: str
    system_definition_id: str
    feature_set_id: str
    target_id: str
    environment_id: str
    fit_record: FitRecord
    models: tuple[FittedModelState, ...]
    transforms: tuple[LearnedTransformState, ...]
    ensemble_weights: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.models or len(self.models) != len(self.ensemble_weights):
            msg = "fitted system requires one weight per exact fitted model"
            raise ValueError(msg)
        if self.fit_record.system_definition_id != self.system_definition_id:
            msg = "fit record and fitted system definition identities differ"
            raise ValueError(msg)
        if self.fit_record.environment_id != self.environment_id:
            msg = "fit record and fitted system environment identities differ"
            raise ValueError(msg)
        if self.fit_record.model_state_ids != tuple(item.fitted_model_id for item in self.models):
            msg = "fit record does not inventory every exact fitted model"
            raise ValueError(msg)
        if self.fit_record.transform_state_ids != tuple(item.state_id for item in self.transforms):
            msg = "fit record does not inventory every exact learned transform"
            raise ValueError(msg)
        if any(
            item.training_window_id != self.fit_record.training_window_id for item in self.models
        ) or any(
            item.training_window_id != self.fit_record.training_window_id
            for item in self.transforms
        ):
            msg = "fitted components cross the recorded training-window boundary"
            raise ValueError(msg)
        expected = stable_identity("fitted-predictive-system", _system_payload(self))
        if self.fitted_system_id != expected:
            msg = "fitted-system identity does not match content"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class PredictionRecord:
    """Immutable inference result with no learning or outcome channel."""

    prediction_id: str
    fitted_system_id: str
    system_definition_id: str
    fit_record_id: str
    information_set_id: str
    feature_series_ids: tuple[str, ...]
    feature_definition_ids: tuple[str, ...]
    decision_time: datetime
    dimensions: DimensionValues
    target_id: str
    value: float
    environment_id: str
    provenance_refs: tuple[str, ...]
    status: DevelopmentStatus = DevelopmentStatus.DEVELOPMENT

    def __post_init__(self) -> None:
        require_aware(self.decision_time, "decision_time")
        if (
            not self.feature_series_ids
            or len(self.feature_series_ids) != len(self.feature_definition_ids)
            or not self.provenance_refs
        ):
            msg = "prediction requires exact feature and provenance identity"
            raise ValueError(msg)
        expected = stable_identity("prediction-record", _prediction_payload(self))
        if self.prediction_id != expected:
            msg = "prediction-record identity does not match content"
            raise ValueError(msg)
        if self.status is not DevelopmentStatus.DEVELOPMENT:
            msg = "development prediction cannot claim protected validation"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class OutcomeRecord:
    """Immutable mature outcome kept separate from its prior prediction."""

    outcome_id: str
    prediction_id: str
    target_id: str
    value: Scalar
    completion_time: datetime
    available_at: datetime
    recorded_at: datetime
    observation_ids: tuple[str, ...]
    environment_id: str
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for name, moment in (
            ("completion_time", self.completion_time),
            ("available_at", self.available_at),
            ("recorded_at", self.recorded_at),
        ):
            require_aware(moment, name)
        if self.recorded_at < self.available_at:
            msg = "outcome cannot be recorded before it is legally available"
            raise ValueError(msg)
        if not self.observation_ids or not self.provenance_refs:
            msg = "outcome requires exact source observations and provenance"
            raise ValueError(msg)
        expected = stable_identity("outcome-record", _outcome_payload(self))
        if self.outcome_id != expected:
            msg = "outcome-record identity does not match content"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class DevelopmentProtocol:
    """Exact ordered temporal-fold and diagnostic recipe."""

    name: str
    version: int
    minimum_training_rows: int
    validation_rows: int
    step_rows: int
    purge_overlapping_labels: bool
    embargo: timedelta | None
    metric_names: tuple[str, ...]
    feature_analysis_methods: tuple[str, ...]
    environment_id: str
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.version < 1 or not self.name or not self.environment_id:
            msg = "development protocol identity and version are required"
            raise ValueError(msg)
        if min(self.minimum_training_rows, self.validation_rows, self.step_rows) < 1:
            msg = "development fold sizes must be positive"
            raise ValueError(msg)
        if self.embargo is not None and self.embargo <= timedelta(0):
            msg = "configured embargo must be positive"
            raise ValueError(msg)
        if not self.metric_names or not self.provenance_refs:
            msg = "development metrics and provenance are required"
            raise ValueError(msg)

    @property
    def identity(self) -> str:
        return stable_identity("development-protocol", self)


@dataclass(frozen=True, slots=True)
class TemporalFold:
    """One ordered development split including exact purge/embargo exclusions."""

    fold_id: str
    protocol_id: str
    target_id: str
    ordinal: int
    training_row_ids: tuple[str, ...]
    validation_row_ids: tuple[str, ...]
    unavailable_row_ids: tuple[str, ...]
    purged_row_ids: tuple[str, ...]
    embargoed_row_ids: tuple[str, ...]
    validation_start: datetime
    validation_end: datetime

    def __post_init__(self) -> None:
        require_aware(self.validation_start, "validation_start")
        require_aware(self.validation_end, "validation_end")
        expected = stable_identity("temporal-fold", _fold_payload(self))
        if self.fold_id != expected:
            msg = "temporal-fold identity does not match content"
            raise ValueError(msg)


class TrialStatus(Enum):
    """Append-only development trial outcomes and selection decisions."""

    ATTEMPTED = "attempted"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REJECTED = "rejected"
    SELECTED = "selected"


@dataclass(frozen=True, slots=True)
class TrialRecord:
    """One immutable trial event; later status creates another event."""

    event_id: str
    trial_id: str
    sequence: int
    candidate_id: str
    protocol_id: str
    parent_trial_ids: tuple[str, ...]
    status: TrialStatus
    evidence_refs: tuple[str, ...]
    failure_id: str | None
    rationale: str

    def __post_init__(self) -> None:
        expected = stable_identity("trial-event", _trial_payload(self))
        if self.event_id != expected:
            msg = "trial-event identity does not match content"
            raise ValueError(msg)


class TrialLedger:
    """Minimal append-only scientific trial history; no winner-only projection."""

    def __init__(self) -> None:
        self._records: list[TrialRecord] = []

    @property
    def records(self) -> tuple[TrialRecord, ...]:
        return tuple(self._records)

    def append(
        self,
        *,
        trial_id: str,
        candidate_id: str,
        protocol_id: str,
        parent_trial_ids: tuple[str, ...],
        status: TrialStatus,
        rationale: str,
        evidence_refs: tuple[str, ...] = (),
        failure_id: str | None = None,
    ) -> TrialRecord:
        self._validate_append(
            trial_id=trial_id,
            candidate_id=candidate_id,
            protocol_id=protocol_id,
            parent_trial_ids=parent_trial_ids,
            status=status,
            rationale=rationale,
            failure_id=failure_id,
        )
        payload = {
            "trial_id": trial_id,
            "sequence": len(self._records),
            "candidate_id": candidate_id,
            "protocol_id": protocol_id,
            "parent_trial_ids": parent_trial_ids,
            "status": status,
            "evidence_refs": evidence_refs,
            "failure_id": failure_id,
            "rationale": rationale,
        }
        record = TrialRecord(
            event_id=stable_identity("trial-event", payload),
            trial_id=trial_id,
            sequence=len(self._records),
            candidate_id=candidate_id,
            protocol_id=protocol_id,
            parent_trial_ids=parent_trial_ids,
            status=status,
            evidence_refs=evidence_refs,
            failure_id=failure_id,
            rationale=rationale,
        )
        self._records.append(record)
        return record

    def _validate_append(  # noqa: C901
        self,
        *,
        trial_id: str,
        candidate_id: str,
        protocol_id: str,
        parent_trial_ids: tuple[str, ...],
        status: TrialStatus,
        rationale: str,
        failure_id: str | None,
    ) -> None:
        if not all((trial_id, candidate_id, protocol_id, rationale)):
            msg = "trial identity and rationale are required"
            raise ValueError(msg)
        if any(parent == trial_id for parent in parent_trial_ids):
            msg = "a trial cannot be its own parent"
            raise ValueError(msg)
        if len(set(parent_trial_ids)) != len(parent_trial_ids):
            msg = "trial parent identities must be unique"
            raise ValueError(msg)
        if status is TrialStatus.FAILED and failure_id is None:
            msg = "failed trial events require the exact failure"
            raise ValueError(msg)
        if status is not TrialStatus.FAILED and failure_id is not None:
            msg = "only a failed trial event may reference a fitting failure"
            raise ValueError(msg)
        prior = tuple(item for item in self._records if item.trial_id == trial_id)
        if not prior and status is not TrialStatus.ATTEMPTED:
            msg = "a trial must be attempted before its outcome is recorded"
            raise ValueError(msg)
        if not prior:
            known_trials = {item.trial_id for item in self._records}
            if any(parent not in known_trials for parent in parent_trial_ids):
                msg = "every parent must reference an existing trial"
                raise ValueError(msg)
            if any(self._is_ancestor(parent, trial_id) for parent in parent_trial_ids):
                msg = "trial ancestry must remain acyclic"
                raise ValueError(msg)
        elif any(
            (
                item.candidate_id != candidate_id
                or item.protocol_id != protocol_id
                or item.parent_trial_ids != parent_trial_ids
            )
            for item in prior
        ):
            msg = "trial identity and ancestry cannot change across events"
            raise ValueError(msg)
        if prior and prior[-1].status in {
            TrialStatus.FAILED,
            TrialStatus.REJECTED,
            TrialStatus.SELECTED,
        }:
            msg = "terminal trial decision cannot be rewritten"
            raise ValueError(msg)
        allowed_next = {
            TrialStatus.ATTEMPTED: {TrialStatus.SUCCEEDED, TrialStatus.FAILED},
            TrialStatus.SUCCEEDED: {TrialStatus.REJECTED, TrialStatus.SELECTED},
        }
        if prior and status not in allowed_next.get(prior[-1].status, set()):
            msg = "event is not a legal trial transition"
            raise ValueError(msg)

    def _is_ancestor(self, trial_id: str, possible_ancestor: str) -> bool:
        parents_by_trial = {
            item.trial_id: item.parent_trial_ids
            for item in self._records
            if item.status is TrialStatus.ATTEMPTED
        }
        pending = [trial_id]
        seen: set[str] = set()
        while pending:
            current = pending.pop()
            if current == possible_ancestor:
                return True
            if current in seen:
                continue
            seen.add(current)
            pending.extend(parents_by_trial.get(current, ()))
        return False

    def ancestry(self, trial_id: str) -> tuple[TrialRecord, ...]:
        """Return every reachable event without deleting failed or rejected branches."""
        by_trial: dict[str, list[TrialRecord]] = {}
        for record in self._records:
            by_trial.setdefault(record.trial_id, []).append(record)
        seen: set[str] = set()
        ordered: list[TrialRecord] = []

        def visit(current: str) -> None:
            if current in seen:
                return
            seen.add(current)
            records = by_trial.get(current, [])
            for record in records:
                for parent in record.parent_trial_ids:
                    visit(parent)
                ordered.append(record)

        visit(trial_id)
        return tuple(ordered)


def _failure_payload(item: TrainingFailure) -> dict[str, object]:
    return {name: getattr(item, name) for name in item.__dataclass_fields__ if name != "failure_id"}


def _transform_payload(item: LearnedTransformState) -> dict[str, object]:
    return {name: getattr(item, name) for name in item.__dataclass_fields__ if name != "state_id"}


def _model_payload(item: FittedModelState) -> dict[str, object]:
    return {
        name: getattr(item, name) for name in item.__dataclass_fields__ if name != "fitted_model_id"
    }


def _fit_payload(item: FitRecord) -> dict[str, object]:
    omitted = {"fit_id"}
    if item.training_information_bundle_id is None:
        omitted.update(
            {
                "training_information_bundle_id",
                "information_set_ids",
                "feature_series_ids",
                "compiled_feature_ids",
            }
        )
    return {name: getattr(item, name) for name in item.__dataclass_fields__ if name not in omitted}


def _system_payload(item: FittedPredictiveSystem) -> dict[str, object]:
    return {
        name: getattr(item, name)
        for name in item.__dataclass_fields__
        if name != "fitted_system_id"
    }


def _prediction_payload(item: PredictionRecord) -> dict[str, object]:
    return {
        name: getattr(item, name) for name in item.__dataclass_fields__ if name != "prediction_id"
    }


def _outcome_payload(item: OutcomeRecord) -> dict[str, object]:
    return {name: getattr(item, name) for name in item.__dataclass_fields__ if name != "outcome_id"}


def _fold_payload(item: TemporalFold) -> dict[str, object]:
    return {name: getattr(item, name) for name in item.__dataclass_fields__ if name != "fold_id"}


def _trial_payload(item: TrialRecord) -> dict[str, object]:
    return {name: getattr(item, name) for name in item.__dataclass_fields__ if name != "event_id"}
