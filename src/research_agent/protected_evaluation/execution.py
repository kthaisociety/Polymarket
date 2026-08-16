"""Protected historical execution with exact temporal reconstruction and sealing."""

# ruff: noqa: BLE001, D105, D107, PLC0415, PLR0911, PLR0913, PLR0917, TRY301

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from threading import RLock
from typing import TYPE_CHECKING

from research_agent.data_foundation._identity import stable_identity
from research_agent.data_foundation.information import BoundaryStatus, InformationSetBuilder
from research_agent.data_foundation.samples import TrainingSampleBuilder
from research_agent.data_foundation.windows import TrainingWindowSelector
from research_agent.development import (
    FittedSystemRegistry,
    OutcomeRecorder,
    SystemPredictor,
    SystemTrainer,
    TrainingBlocked,
    TrainingInformationBuilder,
)
from research_agent.protected_evaluation.exposure import DisclosureEvent, ExposureRecorder
from research_agent.protected_evaluation.idempotency import PrivilegedOperationCoordinator
from research_agent.protected_evaluation.ledger import LedgerEntry, ResearchLedger
from research_agent.protected_evaluation.protocols import EvaluationScenario, ScenarioKind

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from research_agent.data_foundation.observations import (
        DataCatalogSnapshot,
        DimensionValues,
        Scalar,
    )
    from research_agent.data_foundation.samples import SampleKey
    from research_agent.formalization import PredictiveSystemDefinition
    from research_agent.protected_evaluation.access import ProtectedViewBinder
    from research_agent.protected_evaluation.governance import FrozenSystemRegistry, PermitRegistry
    from research_agent.protected_evaluation.records import (
        AuthorizedProtectedDataView,
        BacktestPermit,
        BacktestRequest,
        ExposureRecord,
        FrozenPredictiveSystemIdentity,
        LoadedProtectedCatalog,
    )


class ProtectedFailureCode(Enum):
    """Typed reasons a declared protected decision did not produce complete evidence."""

    UNSUPPORTED_SCENARIO_KIND = "unsupported_scenario_kind"
    PROTECTED_CONTENT_RESOLUTION_FAILED = "protected_content_resolution_failed"
    INFORMATION_SET_NOT_READY = "information_set_not_ready"
    TRAINING_SAMPLE_NOT_READY = "training_sample_not_ready"
    TRAINING_WINDOW_NOT_READY = "training_window_not_ready"
    FIT_FAILED = "fit_failed"
    PREDICTION_FAILED = "prediction_failed"
    OUTCOME_UNAVAILABLE = "outcome_unavailable"
    DIMENSION_SCOPE_UNSUPPORTED = "dimension_scope_unsupported"
    FORMAL_EXECUTION_FAILED = "formal_execution_failed"


class BacktestRunStatus(Enum):
    """Sealed execution status without performance judgment."""

    COMPLETED = "completed"
    COMPLETED_WITH_FAILURES = "completed_with_failures"
    INCOMPLETE = "incomplete"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class ProtectedFitRecord:
    """Protected wrapper around one exact legal fit produced at a decision time."""

    record_id: str
    decision_time: datetime
    protected_system_id: str
    source_fit_id: str
    training_sample_id: str
    training_window_id: str
    training_row_ids: tuple[str, ...]
    fitted_system_id: str
    environment_ref: str

    def __post_init__(self) -> None:
        if self.record_id != stable_identity("protected-fit-record", _without_id(self)):
            msg = "protected fit identity does not match content"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class ProtectedPredictionRecord:
    """Protected immutable prediction, separate from its later outcome."""

    record_id: str
    decision_time: datetime
    dimensions: DimensionValues
    protected_system_id: str
    fit_record_id: str
    source_prediction_id: str
    information_set_id: str
    information_observation_ids: tuple[str, ...]
    value: float
    target_id: str
    environment_ref: str

    def __post_init__(self) -> None:
        if not isfinite(self.value):
            msg = "protected prediction value must be finite"
            raise ValueError(msg)
        if self.record_id != stable_identity("protected-prediction-record", _without_id(self)):
            msg = "protected prediction identity does not match content"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class ProtectedOutcomeRecord:
    """Protected immutable mature outcome linked to one prior prediction."""

    record_id: str
    decision_time: datetime
    dimensions: DimensionValues
    prediction_record_id: str
    source_outcome_id: str
    value: Scalar
    available_at: datetime
    observation_ids: tuple[str, ...]
    target_id: str
    environment_ref: str

    def __post_init__(self) -> None:
        if (
            isinstance(self.value, bool)
            or not isinstance(self.value, (int, float))
            or not isfinite(float(self.value))
        ):
            msg = "protected outcome value must be a finite numeric value"
            raise ValueError(msg)
        if self.record_id != stable_identity("protected-outcome-record", _without_id(self)):
            msg = "protected outcome identity does not match content"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class ProtectedFailureRecord:
    """One explicit failure retained at its declared decision time."""

    failure_id: str
    decision_time: datetime
    dimensions: DimensionValues
    code: ProtectedFailureCode
    stage: str
    detail: str
    system_id: str
    scenario_id: str
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.failure_id != stable_identity("protected-failure", _without_id(self)):
            msg = "protected failure identity does not match content"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class BacktestDecisionRecord:
    """Complete immutable facts for one and only one declared decision time."""

    decision_id: str
    ordinal: int
    decision_time: datetime
    dimensions: DimensionValues
    information_set_id: str | None
    information_observation_ids: tuple[str, ...]
    training_sample_id: str | None
    training_row_ids: tuple[str, ...]
    training_window_id: str | None
    fit: ProtectedFitRecord | None
    prediction: ProtectedPredictionRecord | None
    outcome: ProtectedOutcomeRecord | None
    failures: tuple[ProtectedFailureRecord, ...]

    def __post_init__(self) -> None:
        if self.decision_id != stable_identity("backtest-decision", _without_id(self)):
            msg = "backtest decision identity does not match content"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class BacktestRun:
    """Sealed immutable execution facts; measurement is deliberately absent."""

    run_id: str
    request_id: str
    permit_id: str
    view_id: str
    exposure_id: str | None
    frozen_system_id: str
    system_id: str
    target_id: str
    scenario_id: str
    scenario_kind: ScenarioKind
    scenario_interpretation: str
    evaluation_spec_ref: str
    validation_standard_ref: str
    claim_ref: str
    protected_scope_id: str
    data_id: str
    environment_ref: str
    ancestry_refs: tuple[str, ...]
    decisions: tuple[BacktestDecisionRecord, ...]
    status: BacktestRunStatus
    sealed_at: datetime
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.decisions:
            msg = "sealed run requires every declared decision record"
            raise ValueError(msg)
        ordinals = tuple(item.ordinal for item in self.decisions)
        if ordinals != tuple(range(len(self.decisions))):
            msg = "sealed run decisions must retain exact declared order"
            raise ValueError(msg)
        if len({item.decision_id for item in self.decisions}) != len(self.decisions):
            msg = "sealed run cannot duplicate decision records"
            raise ValueError(msg)
        if self.status is BacktestRunStatus.COMPLETED and self.failures:
            msg = "a completed run cannot contain formal execution failures"
            raise ValueError(msg)
        if self.status is BacktestRunStatus.UNSUPPORTED and not all(
            failure.code is ProtectedFailureCode.UNSUPPORTED_SCENARIO_KIND
            for failure in self.failures
        ):
            msg = "unsupported status requires only explicitly unsupported scenario failures"
            raise ValueError(msg)
        if self.run_id != stable_identity("backtest-run", _without_id(self)):
            msg = "backtest run identity does not match content"
            raise ValueError(msg)

    @property
    def failures(self) -> tuple[ProtectedFailureRecord, ...]:
        """Return all failures without offering a filtered-success projection."""
        return tuple(failure for decision in self.decisions for failure in decision.failures)


class BacktestRunRegistry:
    """Engine-owned authoritative publication history for sealed runs."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._runs: dict[str, BacktestRun] = {}
        self._publication_ids: dict[str, str] = {}

    def _issue(
        self,
        run: BacktestRun,
        *,
        publication: LedgerEntry,
        ledger: ResearchLedger,
    ) -> BacktestRun:
        if (
            not ledger.authoritative(publication)
            or publication.event_type != "backtest.run-sealed"
            or publication.subject_id != run.run_id
        ):
            msg = "backtest-run issuance requires its exact engine seal event"
            raise ValueError(msg)
        with self._lock:
            prior = self._runs.get(run.run_id)
            if prior is not None and prior != run:
                msg = "backtest-run identity was reused with changed semantics"
                raise ValueError(msg)
            self._runs[run.run_id] = run
            self._publication_ids[run.run_id] = publication.entry_id
            return run

    def require_issued(self, run: BacktestRun) -> None:
        """Reject caller-created runs even when their content hash is valid."""
        with self._lock:
            if self._runs.get(run.run_id) != run or run.run_id not in self._publication_ids:
                msg = "backtest run was not issued by the required execution authority"
                raise ValueError(msg)

    def get(self, run_id: str) -> BacktestRun | None:
        """Resolve an exact engine-issued run without a latest fallback."""
        with self._lock:
            return self._runs.get(run_id)


class ProtectedExecutionMismatchError(ValueError):
    """Execution inputs do not match the exact governance and scientific identity."""


class BacktestEngine:
    """Execute an issued protected view exactly once as a historical walk-forward."""

    def __init__(
        self,
        *,
        permits: PermitRegistry,
        frozen_systems: FrozenSystemRegistry,
        views: ProtectedViewBinder,
        exposures: ExposureRecorder,
        ledger: ResearchLedger,
        clock: Callable[[], datetime],
        runs: BacktestRunRegistry | None = None,
        operations: PrivilegedOperationCoordinator | None = None,
    ) -> None:
        self._permits = permits
        self._frozen_systems = frozen_systems
        self._views = views
        self._exposures = exposures
        self._ledger = ledger
        self._clock = clock
        self._operations = operations or PrivilegedOperationCoordinator()
        self._runs = runs or BacktestRunRegistry()
        self._fitted_systems = FittedSystemRegistry()
        self._trainer = SystemTrainer(registry=self._fitted_systems)
        self._predictor = SystemPredictor(self._fitted_systems)

    @property
    def issued_runs(self) -> BacktestRunRegistry:
        """Expose exact sealed runs to the measurement authority."""
        return self._runs

    def execute(
        self,
        *,
        request: BacktestRequest,
        permit: BacktestPermit,
        view: AuthorizedProtectedDataView,
        frozen: FrozenPredictiveSystemIdentity,
        definition: PredictiveSystemDefinition,
        scenario: EvaluationScenario,
        recipient_id: str,
        load_protected_catalog: Callable[[str], LoadedProtectedCatalog],
    ) -> BacktestRun:
        """Validate metadata, record exposure, resolve content, and seal every decision."""
        self._validate(request, permit, view, frozen, definition, scenario, recipient_id)
        payload = (
            ("request_id", request.request_id),
            ("permit_id", permit.permit_id),
            ("view_id", view.view_id),
            ("frozen_system_id", frozen.frozen_system_id),
            ("system_id", definition.identity),
            ("scenario_id", scenario.identity),
            ("recipient_id", recipient_id),
        )
        return self._operations.execute(
            operation_key=f"backtest-run:{request.idempotency_key}",
            semantic_payload=payload,
            effect=lambda: self._execute_once(
                request,
                permit,
                view,
                frozen,
                definition,
                scenario,
                recipient_id,
                load_protected_catalog,
            ),
        ).result

    @staticmethod
    def _failure(
        *,
        key: SampleKey,
        code: ProtectedFailureCode,
        stage: str,
        detail: str,
        system_id: str,
        scenario_id: str,
        evidence_refs: tuple[str, ...],
    ) -> ProtectedFailureRecord:
        payload = {
            "decision_time": key.decision_time,
            "dimensions": key.dimensions,
            "code": code,
            "stage": stage,
            "detail": detail,
            "system_id": system_id,
            "scenario_id": scenario_id,
            "evidence_refs": evidence_refs,
        }
        return ProtectedFailureRecord(
            failure_id=stable_identity("protected-failure", payload),
            decision_time=key.decision_time,
            dimensions=key.dimensions,
            code=code,
            stage=stage,
            detail=detail,
            system_id=system_id,
            scenario_id=scenario_id,
            evidence_refs=evidence_refs,
        )

    def _execute_once(
        self,
        request: BacktestRequest,
        permit: BacktestPermit,
        view: AuthorizedProtectedDataView,
        frozen: FrozenPredictiveSystemIdentity,
        definition: PredictiveSystemDefinition,
        scenario: EvaluationScenario,
        recipient_id: str,
        load_protected_catalog: Callable[[str], LoadedProtectedCatalog],
    ) -> BacktestRun:
        if scenario.kind is not ScenarioKind.HISTORICAL_WALK_FORWARD:
            decisions = tuple(
                self._failed_decision(
                    index,
                    key,
                    self._failure(
                        key=key,
                        code=ProtectedFailureCode.UNSUPPORTED_SCENARIO_KIND,
                        stage="scenario",
                        detail=(
                            f"{scenario.kind.value} execution is not implemented; "
                            "its evidence remains distinctly typed"
                        ),
                        system_id=definition.identity,
                        scenario_id=scenario.identity,
                        evidence_refs=(request.request_id, view.view_id),
                    ),
                )
                for index, key in enumerate(scenario.decision_sample_keys)
            )
            return self._seal(
                request,
                permit,
                view,
                None,
                frozen,
                scenario,
                data_id=view.resource_binding_ref,
                target_id=definition.target.identity,
                decisions=decisions,
                status=BacktestRunStatus.UNSUPPORTED,
            )
        exposure = self._exposures.record(
            DisclosureEvent(
                disclosure_key=f"execute:{request.request_id}:{view.view_id}",
                view_id=view.view_id,
                permit_id=permit.permit_id,
                request_id=request.request_id,
                frozen_system_id=frozen.frozen_system_id,
                system_id=definition.identity,
                lineage_refs=frozen.ancestry_refs,
                scope=view.scope,
                recipient_id=recipient_id,
                disclosure_status="loader-invocation-is-disclosure",
            )
        )
        try:
            loaded = load_protected_catalog(view.resource_binding_ref)
            catalog = loaded.catalog
            if loaded.manifest.manifest_id != view.scope.content_manifest_id:
                msg = "resolved protected content does not match the authorized manifest"
                raise ProtectedExecutionMismatchError(msg)
            if loaded.manifest.content_identity_id != view.scope.content_identity_id:
                msg = "resolved protected bytes do not match the authorized content identity"
                raise ProtectedExecutionMismatchError(msg)
            if loaded.manifest.catalog_id != catalog.identity:
                msg = "resolved protected catalog identity does not match its content manifest"
                raise ProtectedExecutionMismatchError(msg)
            if catalog.environment_id != scenario.environment_ref:
                msg = "protected catalog belongs to another environment"
                raise ProtectedExecutionMismatchError(msg)
        except Exception as error:
            decisions = tuple(
                self._failed_decision(
                    index,
                    key,
                    self._failure(
                        key=key,
                        code=ProtectedFailureCode.PROTECTED_CONTENT_RESOLUTION_FAILED,
                        stage="protected-content",
                        detail=f"protected content resolution failed: {type(error).__name__}",
                        system_id=definition.identity,
                        scenario_id=scenario.identity,
                        evidence_refs=(request.request_id, exposure.exposure_id),
                    ),
                )
                for index, key in enumerate(scenario.decision_sample_keys)
            )
            return self._seal(
                request,
                permit,
                view,
                exposure,
                frozen,
                scenario,
                data_id=view.resource_binding_ref,
                target_id=definition.target.identity,
                decisions=decisions,
                status=BacktestRunStatus.COMPLETED_WITH_FAILURES,
            )
        decisions = tuple(
            self._execute_decision_safely(index, key, catalog, definition, scenario, exposure)
            for index, key in enumerate(scenario.decision_sample_keys)
        )
        status = (
            BacktestRunStatus.COMPLETED_WITH_FAILURES
            if any(item.failures for item in decisions)
            else BacktestRunStatus.COMPLETED
        )
        return self._seal(
            request,
            permit,
            view,
            exposure,
            frozen,
            scenario,
            data_id=catalog.identity,
            target_id=definition.target.identity,
            decisions=decisions,
            status=status,
        )

    def _execute_decision_safely(
        self,
        ordinal: int,
        key: SampleKey,
        catalog: DataCatalogSnapshot,
        definition: PredictiveSystemDefinition,
        scenario: EvaluationScenario,
        exposure: ExposureRecord,
    ) -> BacktestDecisionRecord:
        try:
            return self._execute_decision(
                ordinal,
                key,
                catalog,
                definition,
                scenario,
                exposure,
            )
        except Exception as error:
            failure = self._failure(
                key=key,
                code=ProtectedFailureCode.FORMAL_EXECUTION_FAILED,
                stage="formal-execution",
                detail=f"exact declared decision failed: {type(error).__name__}",
                system_id=definition.identity,
                scenario_id=scenario.identity,
                evidence_refs=(exposure.exposure_id,),
            )
            return self._failed_decision(ordinal, key, failure)

    def _execute_decision(
        self,
        ordinal: int,
        key: SampleKey,
        catalog: DataCatalogSnapshot,
        definition: PredictiveSystemDefinition,
        scenario: EvaluationScenario,
        exposure: ExposureRecord,
    ) -> BacktestDecisionRecord:
        feature_dimensions = tuple(feature.dimensions for feature in definition.feature_set.members)
        if any(item != key.dimensions for item in feature_dimensions):
            failure = self._failure(
                key=key,
                code=ProtectedFailureCode.DIMENSION_SCOPE_UNSUPPORTED,
                stage="population-slice",
                detail="formal feature dimensions do not match this exact scenario sample key",
                system_id=definition.identity,
                scenario_id=scenario.identity,
                evidence_refs=(definition.feature_set.identity,),
            )
            return self._failed_decision(ordinal, key, failure)
        fields = tuple(
            dict.fromkeys(
                dependency
                for feature in definition.feature_set.members
                for dependency in feature.dependencies
            )
        )
        information_fields = tuple(dict.fromkeys((*fields, *definition.target.state_field_refs)))
        information = InformationSetBuilder().build(
            catalog,
            decision_time=key.decision_time,
            requested_fields=information_fields,
        )
        info_ids = tuple(item.observation_id for item in information.observations)
        if information.status is not BoundaryStatus.READY:
            failure = self._failure(
                key=key,
                code=ProtectedFailureCode.INFORMATION_SET_NOT_READY,
                stage="information-set",
                detail="legal current InformationSet is not READY",
                system_id=definition.identity,
                scenario_id=scenario.identity,
                evidence_refs=(information.information_set_id, exposure.exposure_id),
            )
            return self._decision(
                ordinal,
                key,
                information.information_set_id,
                info_ids,
                None,
                (),
                None,
                None,
                None,
                None,
                (failure,),
            )
        candidates = tuple(
            item
            for item in scenario.training_candidate_keys
            if item.decision_time < key.decision_time
        )
        sample = TrainingSampleBuilder().build(
            catalog,
            target=definition.target,
            predictor_fields=fields,
            candidate_sample_keys=candidates,
            current_time=key.decision_time,
            missingness_policy=scenario.missingness_policy,
        )
        row_ids = tuple(item.row_id for item in sample.rows)
        if sample.status is not BoundaryStatus.READY:
            failure = self._failure(
                key=key,
                code=ProtectedFailureCode.TRAINING_SAMPLE_NOT_READY,
                stage="training-sample",
                detail="mature-label TrainingSample is not READY",
                system_id=definition.identity,
                scenario_id=scenario.identity,
                evidence_refs=(sample.sample_id, information.information_set_id),
            )
            return self._decision(
                ordinal,
                key,
                information.information_set_id,
                info_ids,
                sample.sample_id,
                row_ids,
                None,
                None,
                None,
                None,
                (failure,),
            )
        window = TrainingWindowSelector().select(sample, scenario.window_policy)
        if window.status is not BoundaryStatus.READY:
            failure = self._failure(
                key=key,
                code=ProtectedFailureCode.TRAINING_WINDOW_NOT_READY,
                stage="training-window",
                detail=window.insufficiency or "declared training window is not READY",
                system_id=definition.identity,
                scenario_id=scenario.identity,
                evidence_refs=(window.window_id, sample.sample_id),
            )
            return self._decision(
                ordinal,
                key,
                information.information_set_id,
                info_ids,
                sample.sample_id,
                row_ids,
                window.window_id,
                None,
                None,
                None,
                (failure,),
            )
        try:
            training_information = TrainingInformationBuilder(
                self._trainer.training_information_registry
            ).build(
                catalog,
                sample,
                window,
                requested_fields=fields,
            )
            fitted = self._trainer.fit(definition, window, training_information)
        except TrainingBlocked as error:
            failure = self._failure(
                key=key,
                code=ProtectedFailureCode.FIT_FAILED,
                stage="fit",
                detail=error.failure.code.value,
                system_id=definition.identity,
                scenario_id=scenario.identity,
                evidence_refs=(error.failure.failure_id, window.window_id),
            )
            return self._decision(
                ordinal,
                key,
                information.information_set_id,
                info_ids,
                sample.sample_id,
                row_ids,
                window.window_id,
                None,
                None,
                None,
                (failure,),
            )
        protected_fit = self._fit_record(key, fitted, definition.environment_id)
        try:
            prediction = self._predictor.predict(definition, fitted, information)
            protected_prediction = self._prediction_record(
                prediction,
                protected_fit,
                info_ids,
            )
        except (TypeError, ValueError) as error:
            failure = self._failure(
                key=key,
                code=ProtectedFailureCode.PREDICTION_FAILED,
                stage="prediction",
                detail=f"exact prediction failed: {type(error).__name__}",
                system_id=definition.identity,
                scenario_id=scenario.identity,
                evidence_refs=(protected_fit.record_id, information.information_set_id),
            )
            return self._decision(
                ordinal,
                key,
                information.information_set_id,
                info_ids,
                sample.sample_id,
                row_ids,
                window.window_id,
                protected_fit,
                None,
                None,
                (failure,),
            )
        failures: tuple[ProtectedFailureRecord, ...] = ()
        protected_outcome: ProtectedOutcomeRecord | None = None
        try:
            outcome = OutcomeRecorder().record(
                prediction,
                definition.target,
                catalog=catalog,
                decision_information=information,
                current_time=scenario.outcome_recorded_at,
            )
            protected_outcome = self._outcome_record(key, outcome, protected_prediction)
        except (TypeError, ValueError) as error:
            failures = (
                self._failure(
                    key=key,
                    code=ProtectedFailureCode.OUTCOME_UNAVAILABLE,
                    stage="outcome",
                    detail=f"declared outcome is unavailable: {type(error).__name__}",
                    system_id=definition.identity,
                    scenario_id=scenario.identity,
                    evidence_refs=(protected_prediction.record_id, definition.target.identity),
                ),
            )
        return self._decision(
            ordinal,
            key,
            information.information_set_id,
            info_ids,
            sample.sample_id,
            row_ids,
            window.window_id,
            protected_fit,
            protected_prediction,
            protected_outcome,
            failures,
        )

    @staticmethod
    def _fit_record(key: SampleKey, fitted: object, environment_ref: str) -> ProtectedFitRecord:
        from research_agent.development import FittedPredictiveSystem

        if not isinstance(fitted, FittedPredictiveSystem):
            msg = "trainer returned an unexpected fitted-system type"
            raise TypeError(msg)
        payload = {
            "decision_time": key.decision_time,
            "protected_system_id": fitted.system_definition_id,
            "source_fit_id": fitted.fit_record.fit_id,
            "training_sample_id": fitted.fit_record.training_sample_id,
            "training_window_id": fitted.fit_record.training_window_id,
            "training_row_ids": fitted.fit_record.row_ids,
            "fitted_system_id": fitted.fitted_system_id,
            "environment_ref": environment_ref,
        }
        return ProtectedFitRecord(
            record_id=stable_identity("protected-fit-record", payload),
            decision_time=key.decision_time,
            protected_system_id=fitted.system_definition_id,
            source_fit_id=fitted.fit_record.fit_id,
            training_sample_id=fitted.fit_record.training_sample_id,
            training_window_id=fitted.fit_record.training_window_id,
            training_row_ids=fitted.fit_record.row_ids,
            fitted_system_id=fitted.fitted_system_id,
            environment_ref=environment_ref,
        )

    @staticmethod
    def _prediction_record(
        prediction: object,
        fit: ProtectedFitRecord,
        observation_ids: tuple[str, ...],
    ) -> ProtectedPredictionRecord:
        from research_agent.development import PredictionRecord

        if not isinstance(prediction, PredictionRecord):
            msg = "predictor returned an unexpected prediction type"
            raise TypeError(msg)
        payload = {
            "decision_time": prediction.decision_time,
            "dimensions": prediction.dimensions,
            "protected_system_id": prediction.system_definition_id,
            "fit_record_id": fit.record_id,
            "source_prediction_id": prediction.prediction_id,
            "information_set_id": prediction.information_set_id,
            "information_observation_ids": observation_ids,
            "value": prediction.value,
            "target_id": prediction.target_id,
            "environment_ref": prediction.environment_id,
        }
        return ProtectedPredictionRecord(
            record_id=stable_identity("protected-prediction-record", payload),
            decision_time=prediction.decision_time,
            dimensions=prediction.dimensions,
            protected_system_id=prediction.system_definition_id,
            fit_record_id=fit.record_id,
            source_prediction_id=prediction.prediction_id,
            information_set_id=prediction.information_set_id,
            information_observation_ids=observation_ids,
            value=prediction.value,
            target_id=prediction.target_id,
            environment_ref=prediction.environment_id,
        )

    @staticmethod
    def _outcome_record(
        key: SampleKey,
        outcome: object,
        prediction: ProtectedPredictionRecord,
    ) -> ProtectedOutcomeRecord:
        from research_agent.development import OutcomeRecord

        if not isinstance(outcome, OutcomeRecord):
            msg = "outcome recorder returned an unexpected outcome type"
            raise TypeError(msg)
        payload = {
            "decision_time": key.decision_time,
            "dimensions": key.dimensions,
            "prediction_record_id": prediction.record_id,
            "source_outcome_id": outcome.outcome_id,
            "value": outcome.value,
            "available_at": outcome.available_at,
            "observation_ids": outcome.observation_ids,
            "target_id": outcome.target_id,
            "environment_ref": outcome.environment_id,
        }
        return ProtectedOutcomeRecord(
            record_id=stable_identity("protected-outcome-record", payload),
            decision_time=key.decision_time,
            dimensions=key.dimensions,
            prediction_record_id=prediction.record_id,
            source_outcome_id=outcome.outcome_id,
            value=outcome.value,
            available_at=outcome.available_at,
            observation_ids=outcome.observation_ids,
            target_id=outcome.target_id,
            environment_ref=outcome.environment_id,
        )

    @staticmethod
    def _decision(
        ordinal: int,
        key: SampleKey,
        information_set_id: str | None,
        information_observation_ids: tuple[str, ...],
        training_sample_id: str | None,
        training_row_ids: tuple[str, ...],
        training_window_id: str | None,
        fit: ProtectedFitRecord | None,
        prediction: ProtectedPredictionRecord | None,
        outcome: ProtectedOutcomeRecord | None,
        failures: tuple[ProtectedFailureRecord, ...],
    ) -> BacktestDecisionRecord:
        payload = {
            "ordinal": ordinal,
            "decision_time": key.decision_time,
            "dimensions": key.dimensions,
            "information_set_id": information_set_id,
            "information_observation_ids": information_observation_ids,
            "training_sample_id": training_sample_id,
            "training_row_ids": training_row_ids,
            "training_window_id": training_window_id,
            "fit": fit,
            "prediction": prediction,
            "outcome": outcome,
            "failures": failures,
        }
        return BacktestDecisionRecord(
            decision_id=stable_identity("backtest-decision", payload),
            ordinal=ordinal,
            decision_time=key.decision_time,
            dimensions=key.dimensions,
            information_set_id=information_set_id,
            information_observation_ids=information_observation_ids,
            training_sample_id=training_sample_id,
            training_row_ids=training_row_ids,
            training_window_id=training_window_id,
            fit=fit,
            prediction=prediction,
            outcome=outcome,
            failures=failures,
        )

    @classmethod
    def _failed_decision(
        cls,
        ordinal: int,
        key: SampleKey,
        failure: ProtectedFailureRecord,
    ) -> BacktestDecisionRecord:
        return cls._decision(ordinal, key, None, (), None, (), None, None, None, None, (failure,))

    def _seal(
        self,
        request: BacktestRequest,
        permit: BacktestPermit,
        view: AuthorizedProtectedDataView,
        exposure: ExposureRecord | None,
        frozen: FrozenPredictiveSystemIdentity,
        scenario: EvaluationScenario,
        *,
        data_id: str,
        target_id: str,
        decisions: tuple[BacktestDecisionRecord, ...],
        status: BacktestRunStatus,
    ) -> BacktestRun:
        sealed_at = self._clock()
        payload = {
            "request_id": request.request_id,
            "permit_id": permit.permit_id,
            "view_id": view.view_id,
            "exposure_id": None if exposure is None else exposure.exposure_id,
            "frozen_system_id": frozen.frozen_system_id,
            "system_id": frozen.system_id,
            "target_id": target_id,
            "scenario_id": scenario.identity,
            "scenario_kind": scenario.kind,
            "scenario_interpretation": scenario.interpretation,
            "evaluation_spec_ref": request.evaluation_spec_ref,
            "validation_standard_ref": request.validation_standard_ref,
            "claim_ref": request.claim_ref,
            "protected_scope_id": view.scope.scope_id,
            "data_id": data_id,
            "environment_ref": frozen.environment_ref,
            "ancestry_refs": frozen.ancestry_refs,
            "decisions": decisions,
            "status": status,
            "sealed_at": sealed_at,
            "provenance_refs": (
                *scenario.provenance_refs,
                *(() if exposure is None else (exposure.exposure_id,)),
            ),
        }
        run = BacktestRun(
            run_id=stable_identity("backtest-run", payload),
            request_id=request.request_id,
            permit_id=permit.permit_id,
            view_id=view.view_id,
            exposure_id=None if exposure is None else exposure.exposure_id,
            frozen_system_id=frozen.frozen_system_id,
            system_id=frozen.system_id,
            target_id=target_id,
            scenario_id=scenario.identity,
            scenario_kind=scenario.kind,
            scenario_interpretation=scenario.interpretation,
            evaluation_spec_ref=request.evaluation_spec_ref,
            validation_standard_ref=request.validation_standard_ref,
            claim_ref=request.claim_ref,
            protected_scope_id=view.scope.scope_id,
            data_id=data_id,
            environment_ref=frozen.environment_ref,
            ancestry_refs=frozen.ancestry_refs,
            decisions=decisions,
            status=status,
            sealed_at=sealed_at,
            provenance_refs=(
                *scenario.provenance_refs,
                *(() if exposure is None else (exposure.exposure_id,)),
            ),
        )
        publication = self._ledger.append(
            LedgerEntry.create(
                event_type="backtest.run-sealed",
                subject_id=run.run_id,
                status=status.value,
                authority_id="backtest-engine",
                references=(
                    request.request_id,
                    permit.permit_id,
                    *(() if exposure is None else (exposure.exposure_id,)),
                    frozen.frozen_system_id,
                    scenario.identity,
                    *tuple(item.decision_id for item in decisions),
                ),
                reason_code="EXECUTED_EXACT_PROTOCOL",
                occurred_at=sealed_at,
            )
        )
        self._runs._issue(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            run,
            publication=publication,
            ledger=self._ledger,
        )
        return run

    def _validate(
        self,
        request: BacktestRequest,
        permit: BacktestPermit,
        view: AuthorizedProtectedDataView,
        frozen: FrozenPredictiveSystemIdentity,
        definition: PredictiveSystemDefinition,
        scenario: EvaluationScenario,
        recipient_id: str,
    ) -> None:
        try:
            self._permits.require_issued(permit)
            self._frozen_systems.require_issued(frozen)
        except ValueError as error:
            msg = "protected execution inputs were not issued by required authorities"
            raise ProtectedExecutionMismatchError(msg) from error
        mismatch = (
            not self._views.authoritative(view)
            or permit.request_id != request.request_id
            or view.request_id != request.request_id
            or permit.permit_id != view.permit_id
            or request.frozen_system_id != frozen.frozen_system_id
            or request.system_id != frozen.system_id
            or definition.identity != frozen.system_id
            or request.scenario_ref != scenario.identity
            or permit.scenario_ref != scenario.identity
            or view.scenario_ref != scenario.identity
            or request.decision_times_ref != scenario.decision_times_ref
            or request.training_protocol_ref != scenario.training_protocol_ref
            or definition.training_protocol_id != scenario.training_protocol_ref
            or definition.data_protocol_id != scenario.data_protocol_ref
            or request.environment_ref != scenario.environment_ref
            or frozen.environment_ref != scenario.environment_ref
            or definition.environment_id != scenario.environment_ref
            or request.ancestry_refs != frozen.ancestry_refs
            or request.training_protocol_ref not in frozen.protocol_refs
            or request.evaluation_spec_ref not in frozen.protocol_refs
            or request.validation_standard_ref not in frozen.protocol_refs
            or definition.data_protocol_id not in frozen.protocol_refs
            or definition.training_protocol_id not in frozen.protocol_refs
            or definition.evaluation_protocol_id not in frozen.protocol_refs
            or request.protected_scope != view.scope
            or permit.scope != view.scope
            or view.caller_id != request.requester_id
            or not recipient_id
        )
        if mismatch:
            msg = "protected execution inputs do not match exact issued scientific identity"
            raise ProtectedExecutionMismatchError(msg)


def _without_id(item: object) -> dict[str, object]:
    """Return dataclass content excluding its first identity field."""
    fields = getattr(item, "__dataclass_fields__", {})
    identity_name = next(iter(fields), None)
    return {name: getattr(item, name) for name in fields if name != identity_name}


__all__ = [
    "BacktestDecisionRecord",
    "BacktestEngine",
    "BacktestRun",
    "BacktestRunRegistry",
    "BacktestRunStatus",
    "ProtectedExecutionMismatchError",
    "ProtectedFailureCode",
    "ProtectedFailureRecord",
    "ProtectedFitRecord",
    "ProtectedOutcomeRecord",
    "ProtectedPredictionRecord",
]
