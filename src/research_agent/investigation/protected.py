"""Protected execution of the exact researcher-authored scientific program."""

# ruff: noqa: BLE001, D102, D105, D107, EM101, EM102, PLR0913, PLR0917, SLF001, TRY003, TRY301

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from threading import RLock
from typing import TYPE_CHECKING, cast

from research_agent.data_foundation._identity import stable_identity
from research_agent.data_foundation.information import InformationSetBuilder
from research_agent.investigation.program import (
    JsonValue,
    ProgramInvocation,
    ScientificProgramError,
    ScientificProgramHarness,
)
from research_agent.protected_evaluation import (
    BacktestDecisionRecord,
    BacktestPermit,
    BacktestRequest,
    BacktestRun,
    BacktestRunRegistry,
    BacktestRunStatus,
    ClaimDefinition,
    DisclosureEvent,
    EvaluationScenario,
    EvaluationSpec,
    ExposureRecorder,
    FrozenPredictiveSystemIdentity,
    LoadedProtectedCatalog,
    PrivilegedOperationCoordinator,
    PromotionStandard,
    ProtectedExecutionMismatchError,
    ProtectedFailureCode,
    ProtectedFailureRecord,
    ProtectedFitRecord,
    ProtectedOutcomeRecord,
    ProtectedPredictionRecord,
    ProtectedResourceScope,
    ResearchLedger,
    ScenarioKind,
)
from research_agent.protected_evaluation.ledger import LedgerEntry

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from research_agent.data_foundation import DataCatalogSnapshot, RegisteredObservation, SampleKey
    from research_agent.investigation.engine import RuntimeInvestigationCoordinator
    from research_agent.investigation.records import (
        AuthoredCandidate,
        AuthoredDevelopmentEvidence,
        ProgramAccess,
        ProtectedEvaluationPredeclaration,
        RegisteredInvestigation,
    )
    from research_agent.protected_evaluation import ProtectedViewBinder
    from research_agent.protected_evaluation.governance import FrozenSystemRegistry, PermitRegistry
    from research_agent.protected_evaluation.records import (
        AuthorizedProtectedDataView,
        ExposureRecord,
    )


class AuthoredProtectedPlanError(ValueError):
    """A protected authored plan is absent, altered, or does not compose exactly."""


@dataclass(frozen=True, slots=True)
class AuthoredProtectedPlan:
    """Authority-issued holdout plan fixed before authored development begins."""

    plan_id: str
    scenario: EvaluationScenario
    evaluation_spec: EvaluationSpec
    promotion_standard: PromotionStandard
    protected_scope: ProtectedResourceScope
    claim_name: str
    claim_version: int
    claim_statement: str
    claim_scope_limitations: tuple[str, ...]
    claim_required_caveats: tuple[str, ...]
    claim_provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.plan_id != stable_identity("authored-protected-plan", _plan_payload(self)):
            raise AuthoredProtectedPlanError(
                "authored protected plan identity does not match content"
            )
        if (
            self.scenario.environment_ref != self.protected_scope.environment_ref
            or self.evaluation_spec.identity != self.promotion_standard.evaluation_spec_id
            or not all(
                (
                    self.claim_name,
                    self.claim_statement,
                    self.claim_scope_limitations,
                    self.claim_required_caveats,
                    self.claim_provenance_refs,
                )
            )
            or self.claim_version < 1
        ):
            raise AuthoredProtectedPlanError("authored protected plan components do not compose")

    @classmethod
    def create(
        cls,
        *,
        scenario: EvaluationScenario,
        evaluation_spec: EvaluationSpec,
        promotion_standard: PromotionStandard,
        protected_scope: ProtectedResourceScope,
        claim_name: str,
        claim_version: int,
        claim_statement: str,
        claim_scope_limitations: tuple[str, ...],
        claim_required_caveats: tuple[str, ...],
        claim_provenance_refs: tuple[str, ...],
    ) -> AuthoredProtectedPlan:
        payload = {
            "scenario_id": scenario.identity,
            "evaluation_spec_id": evaluation_spec.identity,
            "promotion_standard_id": promotion_standard.identity,
            "protected_scope_id": protected_scope.scope_id,
            "claim_name": claim_name,
            "claim_version": claim_version,
            "claim_statement": claim_statement,
            "claim_scope_limitations": claim_scope_limitations,
            "claim_required_caveats": claim_required_caveats,
            "claim_provenance_refs": claim_provenance_refs,
        }
        return cls(
            stable_identity("authored-protected-plan", payload),
            scenario,
            evaluation_spec,
            promotion_standard,
            protected_scope,
            claim_name,
            claim_version,
            claim_statement,
            claim_scope_limitations,
            claim_required_caveats,
            claim_provenance_refs,
        )

    @property
    def claim_template_ref(self) -> str:
        """Return candidate-independent claim meaning fixed before protected disclosure."""
        return stable_identity(
            "authored-claim-template",
            {
                "name": self.claim_name,
                "version": self.claim_version,
                "statement": self.claim_statement,
                "scope_limitations": self.claim_scope_limitations,
                "required_caveats": self.claim_required_caveats,
                "provenance_refs": self.claim_provenance_refs,
            },
        )

    def claim_for(self, candidate: AuthoredCandidate) -> ClaimDefinition:
        """Bind the predeclared claim template to one exact frozen candidate and label."""
        return ClaimDefinition(
            name=self.claim_name,
            version=self.claim_version,
            statement=self.claim_statement,
            system_id=candidate.candidate_id,
            target_id=_target_id(candidate),
            scope_limitations=self.claim_scope_limitations,
            required_caveats=self.claim_required_caveats,
            provenance_refs=self.claim_provenance_refs,
        )

    def require_predeclared(self, declaration: ProtectedEvaluationPredeclaration) -> None:
        """Reject any plan component selected after development began."""
        expected = (
            self.scenario.data_protocol_ref,
            self.scenario.training_protocol_ref,
            self.scenario.identity,
            self.scenario.decision_times_ref,
            self.evaluation_spec.identity,
            self.promotion_standard.identity,
            self.protected_scope.scope_id,
            self.claim_template_ref,
        )
        actual = (
            declaration.data_protocol_ref,
            declaration.training_protocol_ref,
            declaration.scenario_ref,
            declaration.decision_times_ref,
            declaration.evaluation_spec_ref,
            declaration.validation_standard_ref,
            declaration.protected_scope_id,
            declaration.claim_template_ref,
        )
        if actual != expected:
            raise AuthoredProtectedPlanError(
                "protected plan differs from pre-development declaration"
            )


class AuthoredProtectedPlanRegistry:
    """Capability-issued immutable protected plans; content hashes alone have no authority."""

    def __init__(self, *, authority_id: str, capability: object) -> None:
        if not authority_id:
            raise AuthoredProtectedPlanError("protected plan authority must be explicit")
        self._authority_id = authority_id
        self._capability = capability
        self._plans: dict[str, AuthoredProtectedPlan] = {}
        self._lock = RLock()

    def __copy__(self) -> AuthoredProtectedPlanRegistry:
        raise TypeError("authored protected plan authority cannot be copied")

    def __deepcopy__(self, memo: dict[int, object]) -> AuthoredProtectedPlanRegistry:
        del memo
        raise TypeError("authored protected plan authority cannot be copied")

    def _issue(
        self,
        plan: AuthoredProtectedPlan,
        *,
        authority_id: str,
        capability: object,
    ) -> AuthoredProtectedPlan:
        if authority_id != self._authority_id or capability is not self._capability:
            raise AuthoredProtectedPlanError("protected plan was not authority-issued")
        with self._lock:
            prior = self._plans.get(plan.plan_id)
            if prior is not None and prior != plan:
                raise AuthoredProtectedPlanError("protected plan identity conflict")
            self._plans[plan.plan_id] = plan
            return plan

    def require_issued(self, plan: AuthoredProtectedPlan) -> None:
        with self._lock:
            if self._plans.get(plan.plan_id) != plan:
                raise AuthoredProtectedPlanError("protected plan was not issued by this authority")

    def resolve_predeclared(
        self,
        declaration: ProtectedEvaluationPredeclaration,
    ) -> AuthoredProtectedPlan:
        """Resolve exactly one issued plan matching every pre-development reference."""
        with self._lock:
            matches: list[AuthoredProtectedPlan] = []
            for plan in self._plans.values():
                try:
                    plan.require_predeclared(declaration)
                except AuthoredProtectedPlanError:
                    continue
                matches.append(plan)
            if len(matches) != 1:
                raise AuthoredProtectedPlanError(
                    "no unique authority-issued plan matches the pre-development declaration"
                )
            return matches[0]


class AuthoredProtectedPlanIssuer:
    """Non-reconstructible configured capability for publishing protected plans."""

    def __init__(
        self,
        *,
        authority_id: str,
        registry: AuthoredProtectedPlanRegistry,
        capability: object,
    ) -> None:
        self._authority_id = authority_id
        self._registry = registry
        self._capability = capability

    def __copy__(self) -> AuthoredProtectedPlanIssuer:
        raise TypeError("authored protected plan issuer cannot be copied")

    def __deepcopy__(self, memo: dict[int, object]) -> AuthoredProtectedPlanIssuer:
        del memo
        raise TypeError("authored protected plan issuer cannot be copied")

    def issue(self, plan: AuthoredProtectedPlan) -> AuthoredProtectedPlan:
        return self._registry._issue(  # pyright: ignore[reportPrivateUsage]
            plan,
            authority_id=self._authority_id,
            capability=self._capability,
        )


def configure_authored_protected_plan_authority(
    authority_id: str,
) -> tuple[AuthoredProtectedPlanRegistry, AuthoredProtectedPlanIssuer]:
    """Create one protected-plan registry and its opaque issuance capability."""
    capability = object()
    registry = AuthoredProtectedPlanRegistry(authority_id=authority_id, capability=capability)
    return registry, AuthoredProtectedPlanIssuer(
        authority_id=authority_id,
        registry=registry,
        capability=capability,
    )


@dataclass(frozen=True, slots=True)
class _LegalExample:
    key: SampleKey
    features: dict[str, float]
    label: float
    label_matured_at: datetime
    feature_observation_ids: tuple[str, ...]
    label_observation_ids: tuple[str, ...]
    feature_accesses: tuple[ProgramAccess, ...]
    label_accesses: tuple[ProgramAccess, ...]

    @property
    def row_id(self) -> str:
        return stable_identity("authored-protected-training-row", self)


class _Stage(Enum):
    INFORMATION = "information"
    TRAINING = "training"
    FIT = "fit"
    PREDICTION = "prediction"
    OUTCOME = "outcome"


class _DecisionFailureError(RuntimeError):
    def __init__(
        self,
        stage: _Stage,
        code: ProtectedFailureCode,
        detail: str,
        evidence_refs: tuple[str, ...],
    ) -> None:
        super().__init__(detail)
        self.stage = stage
        self.code = code
        self.detail = detail
        self.evidence_refs = evidence_refs


class AuthoredBacktestEngine:
    """Walk the exact frozen authored source through a protected historical path."""

    def __init__(
        self,
        *,
        investigations: RuntimeInvestigationCoordinator,
        plans: AuthoredProtectedPlanRegistry,
        permits: PermitRegistry,
        frozen_systems: FrozenSystemRegistry,
        views: ProtectedViewBinder,
        exposures: ExposureRecorder,
        ledger: ResearchLedger,
        clock: Callable[[], datetime],
        programs: ScientificProgramHarness | None = None,
        runs: BacktestRunRegistry | None = None,
        operations: PrivilegedOperationCoordinator | None = None,
    ) -> None:
        self._investigations = investigations
        self._plans = plans
        self._permits = permits
        self._frozen_systems = frozen_systems
        self._views = views
        self._exposures = exposures
        self._ledger = ledger
        self._clock = clock
        self._programs = programs or ScientificProgramHarness()
        self._runs = runs or BacktestRunRegistry()
        self._operations = operations or PrivilegedOperationCoordinator()

    def __copy__(self) -> AuthoredBacktestEngine:
        raise TypeError("authored backtest execution authority cannot be copied")

    def __deepcopy__(self, memo: dict[int, object]) -> AuthoredBacktestEngine:
        del memo
        raise TypeError("authored backtest execution authority cannot be copied")

    @property
    def issued_runs(self) -> BacktestRunRegistry:
        return self._runs

    def execute(
        self,
        *,
        request: BacktestRequest,
        permit: BacktestPermit,
        view: AuthorizedProtectedDataView,
        frozen: FrozenPredictiveSystemIdentity,
        plan: AuthoredProtectedPlan,
        recipient_id: str,
        load_protected_catalog: Callable[[str], LoadedProtectedCatalog],
    ) -> BacktestRun:
        _, candidate, evidence = self._validate(request, permit, view, frozen, plan, recipient_id)
        payload = (
            ("request_id", request.request_id),
            ("permit_id", permit.permit_id),
            ("view_id", view.view_id),
            ("frozen_system_id", frozen.frozen_system_id),
            ("candidate_id", candidate.candidate_id),
            ("evidence_id", evidence.evidence_id),
            ("plan_id", plan.plan_id),
            ("recipient_id", recipient_id),
        )
        return self._operations.execute(
            operation_key=f"authored-backtest:{request.idempotency_key}",
            semantic_payload=payload,
            effect=lambda: self._execute_once(
                request,
                permit,
                view,
                frozen,
                candidate,
                plan,
                recipient_id,
                load_protected_catalog,
            ),
        ).result

    def _validate(
        self,
        request: BacktestRequest,
        permit: BacktestPermit,
        view: AuthorizedProtectedDataView,
        frozen: FrozenPredictiveSystemIdentity,
        plan: AuthoredProtectedPlan,
        recipient_id: str,
    ) -> tuple[RegisteredInvestigation, AuthoredCandidate, AuthoredDevelopmentEvidence]:
        try:
            self._plans.require_issued(plan)
            self._permits.require_issued(permit)
            self._frozen_systems.require_issued(frozen)
            if len(frozen.development_evidence_refs) != 1:
                raise ValueError(
                    "frozen authored candidate requires one exact development evidence"
                )
            registration, candidate, evidence = self._investigations.require_credible(
                candidate_id=frozen.system_id,
                evidence_id=frozen.development_evidence_refs[0],
            )
        except (AuthoredProtectedPlanError, ValueError) as error:
            raise ProtectedExecutionMismatchError(
                "authored protected inputs were not issued by required authorities"
            ) from error
        declaration = registration.request.protected_predeclaration
        if declaration is None:
            raise ProtectedExecutionMismatchError("protected evaluation was not predeclared")
        plan.require_predeclared(declaration)
        claim = plan.claim_for(candidate)
        expected_missingness = (
            "exclude_example"
            if plan.scenario.missingness_policy.value == "exclude_example"
            else "fail_trial"
        )
        mismatch = (
            not self._views.authoritative(view)
            or request.request_id != permit.request_id
            or request.request_id != view.request_id
            or permit.permit_id != view.permit_id
            or request.frozen_system_id != frozen.frozen_system_id
            or request.system_id != candidate.candidate_id
            or frozen.system_id != candidate.candidate_id
            or frozen.candidate_version != candidate.source_sha256
            or evidence.evidence_id not in frozen.development_evidence_refs
            or request.ancestry_refs != frozen.ancestry_refs
            or request.scenario_ref != plan.scenario.identity
            or request.decision_times_ref != plan.scenario.decision_times_ref
            or request.training_protocol_ref != plan.scenario.training_protocol_ref
            or request.evaluation_spec_ref != plan.evaluation_spec.identity
            or request.validation_standard_ref != plan.promotion_standard.identity
            or request.claim_ref != claim.identity
            or request.protected_scope != plan.protected_scope
            or permit.scope != plan.protected_scope
            or view.scope != plan.protected_scope
            or permit.scenario_ref != plan.scenario.identity
            or view.scenario_ref != plan.scenario.identity
            or view.caller_id != request.requester_id
            or request.environment_ref != candidate.manifest.environment_id
            or plan.scenario.environment_ref != candidate.manifest.environment_id
            or frozen.environment_ref != candidate.manifest.environment_id
            or candidate.manifest.missing_value_policy != expected_missingness
            or not recipient_id
        )
        if mismatch:
            raise ProtectedExecutionMismatchError(
                "protected request differs from the exact frozen authored experiment"
            )
        return registration, candidate, evidence

    def _execute_once(
        self,
        request: BacktestRequest,
        permit: BacktestPermit,
        view: AuthorizedProtectedDataView,
        frozen: FrozenPredictiveSystemIdentity,
        candidate: AuthoredCandidate,
        plan: AuthoredProtectedPlan,
        recipient_id: str,
        loader: Callable[[str], LoadedProtectedCatalog],
    ) -> BacktestRun:
        scenario = plan.scenario
        if scenario.kind is not ScenarioKind.HISTORICAL_WALK_FORWARD:
            decisions = tuple(
                self._failed_decision(
                    ordinal,
                    key,
                    candidate,
                    scenario,
                    ProtectedFailureCode.UNSUPPORTED_SCENARIO_KIND,
                    "scenario",
                    "authored protected execution currently supports historical walk-forward only",
                    (request.request_id, view.view_id),
                )
                for ordinal, key in enumerate(scenario.decision_sample_keys)
            )
            return self._seal(
                request,
                permit,
                view,
                frozen,
                candidate,
                plan,
                data_id=view.resource_binding_ref,
                exposure=None,
                decisions=decisions,
                status=BacktestRunStatus.UNSUPPORTED,
            )
        exposure = self._exposures.record(
            DisclosureEvent(
                disclosure_key=f"authored-execute:{request.request_id}:{view.view_id}",
                view_id=view.view_id,
                permit_id=permit.permit_id,
                request_id=request.request_id,
                frozen_system_id=frozen.frozen_system_id,
                system_id=candidate.candidate_id,
                lineage_refs=frozen.ancestry_refs,
                scope=view.scope,
                recipient_id=recipient_id,
                disclosure_status="loader-invocation-is-disclosure",
            )
        )
        try:
            loaded = loader(view.resource_binding_ref)
            catalog = loaded.catalog
            if (
                loaded.manifest.manifest_id != view.scope.content_manifest_id
                or loaded.manifest.content_identity_id != view.scope.content_identity_id
                or loaded.manifest.catalog_id != catalog.identity
                or catalog.environment_id != scenario.environment_ref
            ):
                raise ProtectedExecutionMismatchError("protected content differs from issued scope")
        except Exception as error:
            decisions = tuple(
                self._failed_decision(
                    ordinal,
                    key,
                    candidate,
                    scenario,
                    ProtectedFailureCode.PROTECTED_CONTENT_RESOLUTION_FAILED,
                    "protected-content",
                    f"protected content resolution failed: {type(error).__name__}",
                    (request.request_id, exposure.exposure_id),
                )
                for ordinal, key in enumerate(scenario.decision_sample_keys)
            )
            return self._seal(
                request,
                permit,
                view,
                frozen,
                candidate,
                plan,
                data_id=view.resource_binding_ref,
                exposure=exposure,
                decisions=decisions,
                status=BacktestRunStatus.COMPLETED_WITH_FAILURES,
            )
        decisions = tuple(
            self._execute_decision_safely(ordinal, key, catalog, candidate, scenario, exposure)
            for ordinal, key in enumerate(scenario.decision_sample_keys)
        )
        status = (
            BacktestRunStatus.COMPLETED_WITH_FAILURES
            if any(decision.failures for decision in decisions)
            else BacktestRunStatus.COMPLETED
        )
        return self._seal(
            request,
            permit,
            view,
            frozen,
            candidate,
            plan,
            data_id=catalog.identity,
            exposure=exposure,
            decisions=decisions,
            status=status,
        )

    def _execute_decision_safely(
        self,
        ordinal: int,
        key: SampleKey,
        catalog: DataCatalogSnapshot,
        candidate: AuthoredCandidate,
        scenario: EvaluationScenario,
        exposure: ExposureRecord,
    ) -> BacktestDecisionRecord:
        try:
            return self._execute_decision(ordinal, key, catalog, candidate, scenario)
        except _DecisionFailureError as error:
            return self._failed_decision(
                ordinal,
                key,
                candidate,
                scenario,
                error.code,
                error.stage.value,
                error.detail,
                (*error.evidence_refs, exposure.exposure_id),
            )
        except (ScientificProgramError, TypeError, ValueError) as error:
            return self._failed_decision(
                ordinal,
                key,
                candidate,
                scenario,
                ProtectedFailureCode.FORMAL_EXECUTION_FAILED,
                "authored-program",
                f"exact authored decision failed: {type(error).__name__}",
                (exposure.exposure_id,),
            )

    def _execute_decision(
        self,
        ordinal: int,
        key: SampleKey,
        catalog: DataCatalogSnapshot,
        candidate: AuthoredCandidate,
        scenario: EvaluationScenario,
    ) -> BacktestDecisionRecord:
        validation_features, information_id, information_ids, feature_accesses = self._features(
            catalog, candidate, key
        )
        examples = tuple(
            example
            for training_key in scenario.training_candidate_keys
            if training_key.decision_time < key.decision_time
            for example in (
                self._training_example(
                    catalog,
                    candidate,
                    training_key,
                    label_clock=key.decision_time,
                ),
            )
            if example is not None
        )
        policy = scenario.window_policy
        if len(examples) < policy.minimum_samples:
            raise _DecisionFailureError(
                _Stage.TRAINING,
                ProtectedFailureCode.TRAINING_WINDOW_NOT_READY,
                "declared authored training window is insufficient",
                tuple(example.row_id for example in examples),
            )
        selected = examples
        if policy.maximum_samples is not None:
            selected = examples[-policy.maximum_samples :]
        row_ids = tuple(example.row_id for example in selected)
        sample_id = stable_identity(
            "authored-protected-training-sample",
            {
                "candidate_id": candidate.candidate_id,
                "catalog_id": catalog.identity,
                "decision_time": key.decision_time,
                "row_ids": row_ids,
            },
        )
        window_id = stable_identity(
            "authored-protected-training-window",
            {"sample_id": sample_id, "policy_id": policy.identity, "row_ids": row_ids},
        )
        fit_result = self._programs.invoke(
            candidate.source,
            ProgramInvocation(
                "fit",
                training=[
                    {
                        "decision_time": example.key.decision_time.isoformat(),
                        "dimensions": [list(value) for value in example.key.dimensions],
                        "features": cast("dict[str, JsonValue]", example.features),
                        "label": example.label,
                    }
                    for example in selected
                ],
            ),
        )
        source_fit_id = stable_identity(
            "authored-protected-source-fit",
            {
                "candidate_id": candidate.candidate_id,
                "sample_id": sample_id,
                "window_id": window_id,
                "row_ids": row_ids,
                "state": fit_result.value,
                "accesses": fit_result.accesses,
            },
        )
        fitted_system_id = stable_identity(
            "authored-fitted-state",
            {"candidate_id": candidate.candidate_id, "source_fit_id": source_fit_id},
        )
        fit_payload = {
            "decision_time": key.decision_time,
            "protected_system_id": candidate.candidate_id,
            "source_fit_id": source_fit_id,
            "training_sample_id": sample_id,
            "training_window_id": window_id,
            "training_row_ids": row_ids,
            "fitted_system_id": fitted_system_id,
            "environment_ref": candidate.manifest.environment_id,
        }
        fit = ProtectedFitRecord(
            stable_identity("protected-fit-record", fit_payload),
            key.decision_time,
            candidate.candidate_id,
            source_fit_id,
            sample_id,
            window_id,
            row_ids,
            fitted_system_id,
            candidate.manifest.environment_id,
        )
        prediction_result = self._programs.invoke(
            candidate.source,
            ProgramInvocation(
                "predict",
                state=fit_result.value,
                features=cast("dict[str, JsonValue]", validation_features),
            ),
        )
        prediction_value = _finite_number(prediction_result.value, "protected prediction")
        target_id = _target_id(candidate)
        source_prediction_id = stable_identity(
            "authored-protected-source-prediction",
            {
                "candidate_id": candidate.candidate_id,
                "source_fit_id": source_fit_id,
                "information_id": information_id,
                "feature_observation_ids": information_ids,
                "feature_accesses": feature_accesses,
                "prediction_accesses": prediction_result.accesses,
                "value": prediction_value,
            },
        )
        prediction_payload = {
            "decision_time": key.decision_time,
            "dimensions": key.dimensions,
            "protected_system_id": candidate.candidate_id,
            "fit_record_id": fit.record_id,
            "source_prediction_id": source_prediction_id,
            "information_set_id": information_id,
            "information_observation_ids": information_ids,
            "value": prediction_value,
            "target_id": target_id,
            "environment_ref": candidate.manifest.environment_id,
        }
        prediction = ProtectedPredictionRecord(
            stable_identity("protected-prediction-record", prediction_payload),
            key.decision_time,
            key.dimensions,
            candidate.candidate_id,
            fit.record_id,
            source_prediction_id,
            information_id,
            information_ids,
            prediction_value,
            target_id,
            candidate.manifest.environment_id,
        )
        outcome = self._outcome(
            catalog,
            candidate,
            key,
            label_clock=scenario.outcome_recorded_at,
            prediction=prediction,
        )
        return _decision_record(
            ordinal,
            key,
            information_id,
            information_ids,
            sample_id,
            row_ids,
            window_id,
            fit,
            prediction,
            outcome,
            (),
        )

    def _features(
        self,
        catalog: DataCatalogSnapshot,
        candidate: AuthoredCandidate,
        key: SampleKey,
    ) -> tuple[dict[str, float], str, tuple[str, ...], tuple[ProgramAccess, ...]]:
        manifest = candidate.manifest
        if not manifest.admits_population(key.dimensions):
            raise _DecisionFailureError(
                _Stage.INFORMATION,
                ProtectedFailureCode.DIMENSION_SCOPE_UNSUPPORTED,
                "scenario population differs from the authored manifest",
                (),
            )
        information = InformationSetBuilder().build(
            catalog,
            decision_time=key.decision_time,
            requested_fields=manifest.predictor_fields,
        )
        histories = {
            field.field_id: [
                _observation_json(item)
                for item in information.for_field(field)
                if item.reference_time <= key.decision_time
                and tuple(sorted(item.dimensions)) == key.dimensions
            ]
            for field in manifest.predictor_fields
        }
        if any(not values for values in histories.values()):
            raise _DecisionFailureError(
                _Stage.INFORMATION,
                ProtectedFailureCode.INFORMATION_SET_NOT_READY,
                "legal authored predictor history is insufficient",
                (information.information_set_id,),
            )
        used_ids = tuple(
            cast("str", observation["observation_id"])
            for field in manifest.predictor_fields
            for observation in histories[field.field_id]
        )
        information_id = stable_identity(
            "authored-protected-information-view",
            {
                "source_information_set_id": information.information_set_id,
                "candidate_id": candidate.candidate_id,
                "sample_key": key,
                "observation_ids": used_ids,
            },
        )
        result = self._programs.invoke(
            candidate.source,
            ProgramInvocation("make_features", histories=histories),
        )
        return (
            _feature_values(result.value, manifest.feature_names),
            information_id,
            used_ids,
            result.accesses,
        )

    def _training_example(
        self,
        catalog: DataCatalogSnapshot,
        candidate: AuthoredCandidate,
        key: SampleKey,
        *,
        label_clock: datetime,
    ) -> _LegalExample | None:
        try:
            features, _, feature_ids, feature_accesses = self._features(catalog, candidate, key)
            label, matured_at, label_ids, label_accesses = self._label(
                catalog, candidate, key, label_clock=label_clock
            )
        except _DecisionFailureError:
            if candidate.manifest.missing_value_policy == "exclude_example":
                return None
            raise
        return _LegalExample(
            key,
            features,
            label,
            matured_at,
            feature_ids,
            label_ids,
            feature_accesses,
            label_accesses,
        )

    def _label(
        self,
        catalog: DataCatalogSnapshot,
        candidate: AuthoredCandidate,
        key: SampleKey,
        *,
        label_clock: datetime,
    ) -> tuple[float, datetime, tuple[str, ...], tuple[ProgramAccess, ...]]:
        manifest = candidate.manifest
        outcome_end = manifest.horizon.apply(key.decision_time)
        if outcome_end > label_clock:
            raise _DecisionFailureError(
                _Stage.OUTCOME,
                ProtectedFailureCode.OUTCOME_UNAVAILABLE,
                "authored outcome horizon has not matured",
                (),
            )
        information = InformationSetBuilder().build(
            catalog,
            decision_time=label_clock,
            requested_fields=(manifest.outcome_field,),
        )
        observations = tuple(
            item
            for item in information.for_field(manifest.outcome_field)
            if tuple(sorted(item.dimensions)) == key.dimensions
            and key.decision_time < item.reference_time <= outcome_end
        )
        if len(observations) < manifest.minimum_outcome_points:
            raise _DecisionFailureError(
                _Stage.OUTCOME,
                ProtectedFailureCode.OUTCOME_UNAVAILABLE,
                "authored outcome path is incomplete",
                (information.information_set_id,),
            )
        historical_information = InformationSetBuilder().build(
            catalog,
            decision_time=key.decision_time,
            requested_fields=manifest.predictor_fields,
        )
        histories = {
            field.field_id: [
                _observation_json(item)
                for item in historical_information.for_field(field)
                if item.reference_time <= key.decision_time
                and tuple(sorted(item.dimensions)) == key.dimensions
            ]
            for field in manifest.predictor_fields
        }
        if any(not values for values in histories.values()):
            raise _DecisionFailureError(
                _Stage.INFORMATION,
                ProtectedFailureCode.INFORMATION_SET_NOT_READY,
                "legal authored label history is insufficient",
                (historical_information.information_set_id,),
            )
        result = self._programs.invoke(
            candidate.source,
            ProgramInvocation(
                "make_label",
                histories=histories,
                outcome=[_observation_json(item) for item in observations],
            ),
        )
        return (
            _finite_number(result.value, "protected outcome"),
            max(outcome_end, *(item.available_at for item in observations)),
            tuple(item.observation_id for item in observations),
            result.accesses,
        )

    def _outcome(
        self,
        catalog: DataCatalogSnapshot,
        candidate: AuthoredCandidate,
        key: SampleKey,
        *,
        label_clock: datetime,
        prediction: ProtectedPredictionRecord,
    ) -> ProtectedOutcomeRecord:
        label, matured_at, observation_ids, accesses = self._label(
            catalog, candidate, key, label_clock=label_clock
        )
        source_outcome_id = stable_identity(
            "authored-protected-source-outcome",
            {
                "candidate_id": candidate.candidate_id,
                "sample_key": key,
                "observation_ids": observation_ids,
                "label_accesses": accesses,
                "value": label,
                "available_at": matured_at,
            },
        )
        payload = {
            "decision_time": key.decision_time,
            "dimensions": key.dimensions,
            "prediction_record_id": prediction.record_id,
            "source_outcome_id": source_outcome_id,
            "value": label,
            "available_at": matured_at,
            "observation_ids": observation_ids,
            "target_id": prediction.target_id,
            "environment_ref": candidate.manifest.environment_id,
        }
        return ProtectedOutcomeRecord(
            stable_identity("protected-outcome-record", payload),
            key.decision_time,
            key.dimensions,
            prediction.record_id,
            source_outcome_id,
            label,
            matured_at,
            observation_ids,
            prediction.target_id,
            candidate.manifest.environment_id,
        )

    def _failed_decision(
        self,
        ordinal: int,
        key: SampleKey,
        candidate: AuthoredCandidate,
        scenario: EvaluationScenario,
        code: ProtectedFailureCode,
        stage: str,
        detail: str,
        evidence_refs: tuple[str, ...],
    ) -> BacktestDecisionRecord:
        failure_payload = {
            "decision_time": key.decision_time,
            "dimensions": key.dimensions,
            "code": code,
            "stage": stage,
            "detail": detail,
            "system_id": candidate.candidate_id,
            "scenario_id": scenario.identity,
            "evidence_refs": evidence_refs,
        }
        failure = ProtectedFailureRecord(
            stable_identity("protected-failure", failure_payload),
            key.decision_time,
            key.dimensions,
            code,
            stage,
            detail,
            candidate.candidate_id,
            scenario.identity,
            evidence_refs,
        )
        return _decision_record(
            ordinal, key, None, (), None, (), None, None, None, None, (failure,)
        )

    def _seal(
        self,
        request: BacktestRequest,
        permit: BacktestPermit,
        view: AuthorizedProtectedDataView,
        frozen: FrozenPredictiveSystemIdentity,
        candidate: AuthoredCandidate,
        plan: AuthoredProtectedPlan,
        *,
        data_id: str,
        exposure: ExposureRecord | None,
        decisions: tuple[BacktestDecisionRecord, ...],
        status: BacktestRunStatus,
    ) -> BacktestRun:
        sealed_at = self._clock()
        scenario = plan.scenario
        payload = {
            "request_id": request.request_id,
            "permit_id": permit.permit_id,
            "view_id": view.view_id,
            "exposure_id": None if exposure is None else exposure.exposure_id,
            "frozen_system_id": frozen.frozen_system_id,
            "system_id": candidate.candidate_id,
            "target_id": _target_id(candidate),
            "scenario_id": scenario.identity,
            "scenario_kind": scenario.kind,
            "scenario_interpretation": scenario.interpretation,
            "evaluation_spec_ref": plan.evaluation_spec.identity,
            "validation_standard_ref": plan.promotion_standard.identity,
            "claim_ref": plan.claim_for(candidate).identity,
            "protected_scope_id": plan.protected_scope.scope_id,
            "data_id": data_id,
            "environment_ref": candidate.manifest.environment_id,
            "ancestry_refs": frozen.ancestry_refs,
            "decisions": decisions,
            "status": status,
            "sealed_at": sealed_at,
            "provenance_refs": (
                *scenario.provenance_refs,
                candidate.candidate_id,
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
            system_id=candidate.candidate_id,
            target_id=_target_id(candidate),
            scenario_id=scenario.identity,
            scenario_kind=scenario.kind,
            scenario_interpretation=scenario.interpretation,
            evaluation_spec_ref=plan.evaluation_spec.identity,
            validation_standard_ref=plan.promotion_standard.identity,
            claim_ref=plan.claim_for(candidate).identity,
            protected_scope_id=plan.protected_scope.scope_id,
            data_id=data_id,
            environment_ref=candidate.manifest.environment_id,
            ancestry_refs=frozen.ancestry_refs,
            decisions=decisions,
            status=status,
            sealed_at=sealed_at,
            provenance_refs=(
                *scenario.provenance_refs,
                candidate.candidate_id,
                *(() if exposure is None else (exposure.exposure_id,)),
            ),
        )
        publication = self._ledger.append(
            LedgerEntry.create(
                event_type="backtest.run-sealed",
                subject_id=run.run_id,
                status=status.value,
                authority_id="authored-backtest-engine",
                references=(
                    request.request_id,
                    permit.permit_id,
                    *(() if exposure is None else (exposure.exposure_id,)),
                    frozen.frozen_system_id,
                    scenario.identity,
                    *tuple(item.decision_id for item in decisions),
                ),
                reason_code="EXECUTED_EXACT_AUTHORED_PROTOCOL",
                occurred_at=sealed_at,
            )
        )
        return self._runs._issue(  # pyright: ignore[reportPrivateUsage]
            run,
            publication=publication,
            ledger=self._ledger,
        )


def _plan_payload(plan: AuthoredProtectedPlan) -> dict[str, object]:
    return {
        "scenario_id": plan.scenario.identity,
        "evaluation_spec_id": plan.evaluation_spec.identity,
        "promotion_standard_id": plan.promotion_standard.identity,
        "protected_scope_id": plan.protected_scope.scope_id,
        "claim_name": plan.claim_name,
        "claim_version": plan.claim_version,
        "claim_statement": plan.claim_statement,
        "claim_scope_limitations": plan.claim_scope_limitations,
        "claim_required_caveats": plan.claim_required_caveats,
        "claim_provenance_refs": plan.claim_provenance_refs,
    }


def _target_id(candidate: AuthoredCandidate) -> str:
    return stable_identity(
        "authored-target",
        {
            "candidate_id": candidate.candidate_id,
            "outcome_field": candidate.manifest.outcome_field,
            "horizon": candidate.manifest.horizon,
            "minimum_outcome_points": candidate.manifest.minimum_outcome_points,
        },
    )


def _observation_json(observation: RegisteredObservation) -> dict[str, JsonValue]:
    return {
        "observation_id": observation.observation_id,
        "field_id": observation.field_ref.field_id,
        "value": cast("JsonValue", observation.value),
        "reference_time": observation.reference_time.isoformat(),
        "available_at": observation.available_at.isoformat(),
        "dimensions": [list(item) for item in observation.dimensions],
    }


def _feature_values(value: JsonValue, expected: tuple[str, ...]) -> dict[str, float]:
    if not isinstance(value, dict) or tuple(value) != expected:
        raise ValueError("make_features must return the exact declared ordered outputs")
    return {name: _finite_number(value[name], f"feature {name}") for name in expected}


def _finite_number(value: JsonValue, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _decision_record(
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
        stable_identity("backtest-decision", payload),
        ordinal,
        key.decision_time,
        key.dimensions,
        information_set_id,
        information_observation_ids,
        training_sample_id,
        training_row_ids,
        training_window_id,
        fit,
        prediction,
        outcome,
        failures,
    )


__all__ = [
    "AuthoredBacktestEngine",
    "AuthoredProtectedPlan",
    "AuthoredProtectedPlanError",
    "AuthoredProtectedPlanIssuer",
    "AuthoredProtectedPlanRegistry",
    "configure_authored_protected_plan_authority",
]
