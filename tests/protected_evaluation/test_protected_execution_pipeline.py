"""Adversarial protected walk-forward, measurement, and promotion tests."""

# ruff: noqa: EM101, FBT001, PLR0913, PLR2004, TRY003

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import cast

import pytest

from research_agent.data_foundation import (
    DataCatalogSnapshot,
    DatasetSchema,
    FieldDefinition,
    IncompleteOutcomePolicy,
    MaturityPolicy,
    MissingnessPolicy,
    ObservationInput,
    ObservationRegistrar,
    OutcomeAlignment,
    SampleKey,
    TargetDefinition,
    TargetKind,
    TemporalOffset,
    TrainingSampleBuilder,
    TrainingWindowPolicy,
    WindowKind,
)
from research_agent.data_foundation._identity import stable_identity
from research_agent.development import (
    DevelopmentEvaluator,
    DevelopmentProtocol,
    SystemTrainer,
    TrialStatus,
)
from research_agent.formalization import (
    FailureAction,
    FeatureAlignment,
    FeatureDefinition,
    FeatureExpression,
    FeatureSet,
    HistoryKind,
    HistorySemantics,
    ModelDefinition,
    PredictiveSystemDefinition,
    TemporalMapping,
)
from research_agent.protected_evaluation import (
    AuthorizedProtectedDataView,
    BacktestDenial,
    BacktestEngine,
    BacktestGovernance,
    BacktestPermit,
    BacktestRequest,
    BacktestRun,
    BacktestRunRegistry,
    BacktestRunStatus,
    ClaimDefinition,
    CriterionComparison,
    DecisionStatus,
    DenialCode,
    EvaluationReport,
    EvaluationReportRegistry,
    EvaluationScenario,
    EvaluationSpec,
    Evaluator,
    ExposureRecorder,
    ExposureRegistry,
    FindingPublisher,
    FreezeEligibilityIssuer,
    FreezeEligibilityRegistration,
    FreezeEligibilityRegistry,
    FreezeEligibilityRequest,
    FreezeGate,
    FrozenPredictiveSystemIdentity,
    FrozenSystemRegistry,
    IdempotencyConflictError,
    LoadedProtectedCatalog,
    MetricCriterion,
    MetricName,
    MetricResult,
    NegativeResultRegistry,
    PermissionGrant,
    PermitRegistry,
    PrivilegedOperationCoordinator,
    PromotionStandard,
    ProtectedContentManifest,
    ProtectedExecutionMismatchError,
    ProtectedExposureStatus,
    ProtectedFailureCode,
    ProtectedPredictionRecord,
    ProtectedResourceScope,
    ProtectedViewBinder,
    ResearchLedger,
    ScenarioKind,
    ValidationDecision,
    ValidationStatus,
    Validator,
)
from research_agent.protected_evaluation._identity import scientific_identity

DAY = timedelta(days=1)
ELAPSED_DAY = TemporalOffset.elapsed(DAY)
ZERO_OFFSET = TemporalOffset.zero()
ORIGIN = datetime(2025, 1, 1, tzinfo=UTC)
NOW = ORIGIN + DAY * 20


def _clock() -> datetime:
    return NOW


def _forge_run(run: BacktestRun) -> BacktestRun:
    provenance = (*run.provenance_refs, "caller:forged")
    payload = {
        name: provenance if name == "provenance_refs" else getattr(run, name)
        for name in run.__dataclass_fields__
        if name != "run_id"
    }
    return replace(
        run,
        run_id=stable_identity("backtest-run", payload),
        provenance_refs=provenance,
    )


def _forge_report(
    report: EvaluationReport,
    *,
    metrics: tuple[MetricResult, ...] | None = None,
) -> EvaluationReport:
    changed_metrics = report.metrics if metrics is None else metrics
    caveats = (*report.caveats, "caller-forged-report")
    payload = {
        name: (
            changed_metrics
            if name == "metrics"
            else caveats
            if name == "caveats"
            else getattr(report, name)
        )
        for name in report.__dataclass_fields__
        if name != "report_id"
    }
    return replace(
        report,
        report_id=stable_identity("evaluation-report", payload),
        metrics=changed_metrics,
        caveats=caveats,
    )


def _forge_decision(decision: ValidationDecision) -> ValidationDecision:
    reasons = (*decision.reasons, "CALLER_FORGED")
    payload = {
        name: reasons if name == "reasons" else getattr(decision, name)
        for name in decision.__dataclass_fields__
        if name != "decision_id"
    }
    return replace(
        decision,
        decision_id=stable_identity("validation-decision", payload),
        reasons=reasons,
    )


def _schema() -> DatasetSchema:
    return DatasetSchema(
        dataset_id="protected-fixture",
        version="schema-v1",
        environment_id="environment-v1",
        provenance_ref="artifact:schema-v1",
        fields=(
            FieldDefinition("x", "X", "float", "index", (), "Predictor."),
            FieldDefinition("y", "Y", "float", "units", (), "Outcome."),
        ),
    )


def _catalog(
    *,
    future_poison: bool = True,
    protected_outcomes: tuple[float, float, float] | None = None,
) -> DataCatalogSnapshot:
    schema = _schema()
    rows: list[ObservationInput] = []
    for day, value in enumerate((1.0, 2.0, 3.0, 4.0, 5.0, 6.0)):
        available = ORIGIN + DAY * day
        if day == 4:
            available = ORIGIN + DAY * 5
        rows.append(
            ObservationInput(
                schema.field_ref("x"),
                value,
                ORIGIN + DAY * day,
                available,
                f"x-v{day}",
                0,
                "source:x",
                f"provenance:x:{day}",
                "availability:x-v1",
                (),
            )
        )
    outcome_available = {4: 6}
    for reference_day in range(1, 8):
        available_day = outcome_available.get(reference_day, reference_day)
        value = float(reference_day * 2)
        if protected_outcomes is not None and reference_day in {4, 5, 6}:
            value = protected_outcomes[reference_day - 4]
        rows.append(
            ObservationInput(
                schema.field_ref("y"),
                value,
                ORIGIN + DAY * reference_day,
                ORIGIN + DAY * available_day,
                f"y-v{reference_day}",
                0,
                "source:y",
                f"provenance:y:{reference_day}",
                "availability:y-v1",
                (),
            )
        )
    if future_poison:
        rows.append(
            ObservationInput(
                schema.field_ref("x"),
                999_999.0,
                ORIGIN + DAY * 5,
                ORIGIN + DAY * 10,
                "x-v5-revision",
                1,
                "source:x",
                "provenance:future-poison",
                "availability:x-v1",
                (),
            )
        )
    registration = ObservationRegistrar().register(schema, tuple(rows))
    return DataCatalogSnapshot(schema.environment_id, (registration,))


def _system(*, algorithm: str = "mean") -> PredictiveSystemDefinition:
    schema = _schema()
    target = TargetDefinition(
        task_id="task-v1",
        task_version=1,
        task_semantic_digest="task-semantic-v1",
        confirmed_task_horizon_id=ELAPSED_DAY.identity,
        version=1,
        parent_target_id=None,
        field_ref=schema.field_ref("y"),
        kind=TargetKind.ENDPOINT,
        horizon=ELAPSED_DAY,
        outcome_start_offset=ZERO_OFFSET,
        outcome_end_offset=ELAPSED_DAY,
        alignment=OutcomeAlignment.EXACT,
        path_reduction=None,
        event_condition=None,
        maturity_delay=ELAPSED_DAY,
        maturity_policy=MaturityPolicy.FULL_INTERVAL,
        required_observation_count=1,
        value_encoding="numeric",
        units="units",
        censoring_policy="complete interval",
        incomplete_outcome_policy=IncompleteOutcomePolicy.EXCLUDE,
        environment_id=schema.environment_id,
        schema_provenance_ref=schema.provenance_ref,
        provenance_refs=("research:target",),
    )
    feature = FeatureDefinition(
        name="x",
        version=1,
        parent_definition_id=None,
        environment_id=schema.environment_id,
        dependencies=(schema.field_ref("x"),),
        expression=FeatureExpression.field(schema.field_ref("x")),
        temporal_mapping=TemporalMapping(FeatureAlignment.LATEST_AT_OR_BEFORE, ZERO_OFFSET),
        history=HistorySemantics(
            HistoryKind.EXPANDING,
            ZERO_OFFSET,
            None,
            "use exact legal history",
            "no truncation",
        ),
        output_data_type="float",
        output_units="index",
        dimensions=(),
        missing_input=FailureAction.FAIL,
        invalid_domain=FailureAction.FAIL,
        insufficiency=FailureAction.FAIL,
        failure="fail without substitution",
        hypothesis="x may predict y",
        information_intent="retain exact legal x",
        fitted_state_procedures=(),
        evidence_refs=("analysis:x",),
        candidate_ancestry=("candidate:feature",),
        provenance_refs=(schema.provenance_ref,),
    )
    feature_set = FeatureSet(
        "features",
        1,
        None,
        schema.environment_id,
        (feature,),
        ("trial:features",),
        ("research:features",),
    )
    model = ModelDefinition(
        name=algorithm,
        version=1,
        parent_definition_id=None,
        environment_id=schema.environment_id,
        algorithm=algorithm,
        hyperparameters=(),
        preprocessing_refs=(feature_set.identity,),
        selection_procedure_ref="selection:none",
        randomness_policy="deterministic",
        training_requirement_refs=("trainer:controlled-v1",),
        evidence_refs=("development:model",),
        candidate_ancestry=("candidate:model",),
        provenance_refs=("implementation:mean",),
    )
    return PredictiveSystemDefinition(
        name="protected-candidate",
        version=1,
        parent_system_id=None,
        environment_id=schema.environment_id,
        target=target,
        feature_set=feature_set,
        models=(model,),
        ensemble=None,
        data_protocol_id="data:as-known-v1",
        training_protocol_id="training:refit-every-time-v1",
        evaluation_protocol_id="evaluation:protected-v1",
        evidence_refs=("development:evidence",),
        candidate_ancestry=("trial:parent",),
        provenance_refs=("research:system",),
    )


def _protocols(
    system: PredictiveSystemDefinition,
    *,
    maximum_stability_stddev: float = 100.0,
    minimum_training_rows: int = 2,
) -> tuple[EvaluationScenario, EvaluationSpec, PromotionStandard]:
    scenario = EvaluationScenario(
        name="protected historical path",
        version=1,
        kind=ScenarioKind.HISTORICAL_WALK_FORWARD,
        decision_sample_keys=tuple(SampleKey(ORIGIN + DAY * day) for day in (3, 4, 5)),
        training_candidate_keys=tuple(SampleKey(ORIGIN + DAY * day) for day in range(5)),
        outcome_recorded_at=ORIGIN + DAY * 8,
        training_protocol_ref=system.training_protocol_id,
        window_policy=TrainingWindowPolicy(
            1,
            WindowKind.EXPANDING,
            minimum_training_rows,
            None,
            "protocol:expanding-v1",
        ),
        missingness_policy=MissingnessPolicy.EXCLUDE_EXAMPLE,
        interpretation="one realized historical walk-forward path",
        environment_ref=system.environment_id,
        data_protocol_ref=system.data_protocol_id,
        provenance_refs=("scenario:historical-v1",),
    )
    spec = EvaluationSpec(
        name="forecast quality",
        version=1,
        protocol_ref=system.evaluation_protocol_id,
        metric_names=(
            MetricName.MSE,
            MetricName.MAE,
            MetricName.COVERAGE,
            MetricName.FAILURE_RATE,
        ),
        rolling_window=2,
        include_per_time=True,
        include_dimension_views=True,
        include_stability=True,
        include_concentration=True,
        benchmark_refs=(),
        provenance_refs=("evaluation:predeclared",),
    )
    standard = PromotionStandard(
        name="forecast promotion",
        version=1,
        evaluation_spec_id=spec.identity,
        criteria=(
            MetricCriterion(MetricName.MSE, CriterionComparison.LESS_THAN_OR_EQUAL, 100.0),
            MetricCriterion(MetricName.COVERAGE, CriterionComparison.GREATER_THAN_OR_EQUAL, 1.0),
            MetricCriterion(
                MetricName.FAILURE_RATE,
                CriterionComparison.LESS_THAN_OR_EQUAL,
                0.0,
            ),
        ),
        maximum_stability_stddev=maximum_stability_stddev,
        maximum_error_concentration=1.0,
        required_scenario_kind=ScenarioKind.HISTORICAL_WALK_FORWARD,
        authority_policy_ref="validation-policy:v1",
        provenance_refs=("validation:predeclared",),
    )
    return scenario, spec, standard


def _manifest(catalog: DataCatalogSnapshot) -> ProtectedContentManifest:
    content = catalog.identity.encode()
    return ProtectedContentManifest.create(
        content_digest=sha256(content).hexdigest(),
        byte_length=len(content),
        catalog_id=catalog.identity,
        provenance_ref="fixture:protected-catalog",
    )


def _loaded(catalog: DataCatalogSnapshot) -> LoadedProtectedCatalog:
    return LoadedProtectedCatalog(manifest=_manifest(catalog), catalog=catalog)


def _scope(catalog: DataCatalogSnapshot | None = None) -> ProtectedResourceScope:
    exact_catalog = catalog or _catalog()
    manifest = _manifest(exact_catalog)
    return ProtectedResourceScope(
        resource_id="protected-catalog",
        resource_version="v1",
        slice_id="holdout-2025",
        environment_ref="environment-v1",
        policy_ref="policy-v1",
        content_manifest_id=manifest.manifest_id,
        content_identity_id=manifest.content_identity_id,
        epistemic_period_ref="epistemic-period:holdout-2025",
        exposure_status=ProtectedExposureStatus.UNSEEN,
    )


def test_protected_manifest_and_freshness_are_identity_bearing() -> None:
    """Changed bytes or prior accessibility cannot retain an unseen protected identity."""
    catalog = _catalog()
    manifest = _manifest(catalog)
    with pytest.raises(ValueError, match="manifest identity"):
        replace(manifest, byte_length=manifest.byte_length + 1)
    unseen = _scope(catalog)
    preexposed = replace(unseen, exposure_status=ProtectedExposureStatus.PREEXPOSED)
    assert preexposed.scope_id != unseen.scope_id
    assert preexposed.exposure_period_id == unseen.exposure_period_id


def _claim(system: PredictiveSystemDefinition) -> ClaimDefinition:
    return ClaimDefinition(
        name="forecast quality claim",
        version=1,
        statement="The frozen system met the exact predeclared forecast standard.",
        system_id=system.identity,
        target_id=system.target.identity,
        scope_limitations=("applies only to the declared protected historical scenario",),
        required_caveats=("does not establish downstream economic usefulness",),
        provenance_refs=("claim:predeclared-v1",),
    )


def test_public_freeze_path_carries_predeclared_protected_protocols_to_governance() -> None:
    """Evaluator-issued protected refs survive issuer, gate, and exact governance checks."""
    development_protocol = DevelopmentProtocol(
        name="pre-freeze-development",
        version=1,
        minimum_training_rows=2,
        validation_rows=2,
        step_rows=2,
        purge_overlapping_labels=False,
        embargo=None,
        metric_names=("mse", "mae"),
        feature_analysis_methods=("permutation", "ablation", "single_feature"),
        environment_id="environment-v1",
        provenance_refs=("protocol:development-v1",),
    )
    system = replace(
        _system(),
        evaluation_protocol_id=development_protocol.identity,
    )
    _, spec, standard = _protocols(system)
    schema = _schema()
    sample = TrainingSampleBuilder().build(
        _catalog(future_poison=False),
        target=system.target,
        predictor_fields=(schema.field_ref("x"),),
        candidate_decision_times=tuple(ORIGIN + DAY * day for day in range(5)),
        current_time=ORIGIN + DAY * 8,
        missingness_policy=MissingnessPolicy.EXCLUDE_EXAMPLE,
    )
    evaluator = DevelopmentEvaluator()
    evidence = evaluator.evaluate(
        system,
        sample,
        development_protocol,
        protected_evaluation_spec_ref=spec.identity,
        validation_standard_ref=standard.identity,
        catalog=_catalog(future_poison=False),
    )
    evaluator.ledger.append(
        trial_id=evidence.trial_id,
        candidate_id=system.identity,
        protocol_id=development_protocol.identity,
        parent_trial_ids=(),
        status=TrialStatus.SELECTED,
        rationale="selected before independent freeze assessment",
        evidence_refs=(evidence.evidence_id,),
    )
    freeze_request = FreezeEligibilityRequest(
        system_id=system.identity,
        candidate_version=str(system.version),
        ancestry_refs=system.candidate_ancestry,
        development_evidence_refs=(evidence.evidence_id,),
        protocol_refs=(
            system.data_protocol_id,
            system.training_protocol_id,
            system.evaluation_protocol_id,
            spec.identity,
            standard.identity,
        ),
        environment_ref=system.environment_id,
        standard_ref="freeze-standard:v1",
        requester_id="research-agent",
        beneficiary_id="candidate-team",
    )
    eligibility = FreezeEligibilityRegistry()
    issuer = FreezeEligibilityIssuer(
        authority_id="freeze-governor",
        development_evidence=evaluator.evidence_registry,
        trial_ledger=evaluator.ledger,
        eligibility=eligibility,
    )
    registration = issuer.issue(
        freeze_request,
        evidence=evidence,
        status=DecisionStatus.ACCEPT,
        reason_code="DEVELOPMENT_STANDARD_MET",
    )
    eligibility.require_issued(registration)
    ledger = ResearchLedger()
    systems = FrozenSystemRegistry()
    gate = FreezeGate(
        ledger=ledger,
        registry=systems,
        eligibility=eligibility,
        decision_authority_id="freeze-governor",
        clock=_clock,
    )
    frozen = gate.seal(freeze_request, gate.assess(freeze_request))
    backtest_request = BacktestRequest(
        frozen_system_id=frozen.frozen_system_id,
        system_id=system.identity,
        scenario_ref="scenario:predeclared",
        decision_times_ref="decision-times:predeclared",
        training_protocol_ref=system.training_protocol_id,
        evaluation_spec_ref=spec.identity,
        validation_standard_ref=standard.identity,
        claim_ref="claim:predeclared",
        protected_scope=_scope(),
        environment_ref=system.environment_id,
        ancestry_refs=frozen.ancestry_refs,
        prior_exposure_refs=(),
        requester_id="research-agent",
        beneficiary_id="candidate-team",
        idempotency_key="public-freeze-to-governance:v1",
    )
    governance = BacktestGovernance(
        ledger=ledger,
        frozen_systems=systems,
        exposures=ExposureRegistry(),
        permits=PermitRegistry(),
        permissions=(
            PermissionGrant(
                "research-agent",
                "backtest-governor",
                frozenset({_scope().scope_id}),
                "policy-v1",
                "environment-v1",
            ),
        ),
        current_environment_ref="environment-v1",
        current_policy_ref="policy-v1",
        clock=_clock,
    )

    permit = governance.authorize(backtest_request, authority_id="backtest-governor")
    assert isinstance(permit, BacktestPermit)

    changed_spec = replace(spec, rolling_window=spec.rolling_window + 1)
    changed_freeze = replace(
        freeze_request,
        protocol_refs=(
            system.data_protocol_id,
            system.training_protocol_id,
            system.evaluation_protocol_id,
            changed_spec.identity,
            standard.identity,
        ),
    )
    with pytest.raises(ValueError, match="authoritative system/development/protocol"):
        issuer.issue(
            changed_freeze,
            evidence=evidence,
            status=DecisionStatus.ACCEPT,
            reason_code="POST_HOC_PROTOCOL_CHANGE",
        )
    changed_backtest = replace(
        backtest_request,
        evaluation_spec_ref=changed_spec.identity,
        idempotency_key="public-freeze-to-governance:changed",
    )
    denial = governance.authorize(changed_backtest, authority_id="backtest-governor")
    assert isinstance(denial, BacktestDenial)
    assert denial.code is DenialCode.INCOMPLETE_PREDECLARATION


def _authorized_execution(
    *,
    scenario_kind: ScenarioKind = ScenarioKind.HISTORICAL_WALK_FORWARD,
    decision_keys: tuple[SampleKey, ...] | None = None,
    maximum_stability_stddev: float = 100.0,
    minimum_training_rows: int = 2,
    algorithm: str = "mean",
    engine_operations: PrivilegedOperationCoordinator | None = None,
    disable_optional_views: bool = False,
    protected_catalog: DataCatalogSnapshot | None = None,
) -> tuple[
    BacktestEngine,
    BacktestRequest,
    BacktestPermit,
    AuthorizedProtectedDataView,
    FrozenPredictiveSystemIdentity,
    PredictiveSystemDefinition,
    EvaluationScenario,
    EvaluationSpec,
    PromotionStandard,
    ExposureRegistry,
    ResearchLedger,
    ProtectedViewBinder,
]:
    exact_protected_catalog = protected_catalog or _catalog()
    protected_scope = _scope(exact_protected_catalog)
    system = _system(algorithm=algorithm)
    scenario, spec, standard = _protocols(
        system,
        maximum_stability_stddev=maximum_stability_stddev,
        minimum_training_rows=minimum_training_rows,
    )
    if disable_optional_views:
        spec = replace(
            spec,
            include_per_time=False,
            include_dimension_views=False,
            include_stability=False,
            include_concentration=False,
        )
        standard = replace(
            standard,
            evaluation_spec_id=spec.identity,
            maximum_stability_stddev=None,
            maximum_error_concentration=None,
        )
    if scenario_kind is not ScenarioKind.HISTORICAL_WALK_FORWARD:
        scenario = replace(
            scenario,
            kind=scenario_kind,
            interpretation=f"{scenario_kind.value} evidence, not realized history",
            generator_ref=(
                "generator:declared-v1"
                if scenario_kind is ScenarioKind.SYNTHETIC_COUNTERFACTUAL
                else None
            ),
            random_seed=(7 if scenario_kind is ScenarioKind.SYNTHETIC_COUNTERFACTUAL else None),
        )
        standard = replace(
            standard,
            criteria=(
                MetricCriterion(
                    MetricName.COVERAGE,
                    CriterionComparison.GREATER_THAN_OR_EQUAL,
                    0.0,
                ),
                MetricCriterion(
                    MetricName.FAILURE_RATE,
                    CriterionComparison.LESS_THAN_OR_EQUAL,
                    1.0,
                ),
            ),
            maximum_stability_stddev=None,
            maximum_error_concentration=None,
            required_scenario_kind=scenario_kind,
        )
    if decision_keys is not None:
        scenario = replace(
            scenario,
            decision_sample_keys=decision_keys,
            training_candidate_keys=decision_keys,
        )
    freeze_request = FreezeEligibilityRequest(
        system_id=system.identity,
        candidate_version="1",
        ancestry_refs=system.candidate_ancestry,
        development_evidence_refs=system.evidence_refs,
        protocol_refs=(
            system.data_protocol_id,
            system.training_protocol_id,
            system.evaluation_protocol_id,
            spec.identity,
            standard.identity,
        ),
        environment_ref=system.environment_id,
        standard_ref="freeze-standard:v1",
        requester_id="research-agent",
        beneficiary_id="candidate-team",
    )
    ledger = ResearchLedger()
    systems = FrozenSystemRegistry()
    eligibility = FreezeEligibilityRegistry()
    registration = FreezeEligibilityRegistration._issue(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        freeze_request,
        authority_id="freeze-governor",
        status=DecisionStatus.ACCEPT,
        reason_code="DEVELOPMENT_STANDARD_MET",
    )
    eligibility._issue(registration)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    freeze_gate = FreezeGate(
        ledger=ledger,
        registry=systems,
        eligibility=eligibility,
        decision_authority_id="freeze-governor",
        clock=_clock,
    )
    freeze_decision = freeze_gate.assess(freeze_request)
    frozen = freeze_gate.seal(freeze_request, freeze_decision)
    request = BacktestRequest(
        frozen_system_id=frozen.frozen_system_id,
        system_id=system.identity,
        scenario_ref=scenario.identity,
        decision_times_ref=scenario.decision_times_ref,
        training_protocol_ref=system.training_protocol_id,
        evaluation_spec_ref=spec.identity,
        validation_standard_ref=standard.identity,
        claim_ref=_claim(system).identity,
        protected_scope=protected_scope,
        environment_ref=system.environment_id,
        ancestry_refs=frozen.ancestry_refs,
        prior_exposure_refs=(),
        requester_id="research-agent",
        beneficiary_id="candidate-team",
        idempotency_key="protected-run:v1",
    )
    exposures = ExposureRegistry()
    permits = PermitRegistry()
    governance = BacktestGovernance(
        ledger=ledger,
        frozen_systems=systems,
        exposures=exposures,
        permits=permits,
        permissions=(
            PermissionGrant(
                "research-agent",
                "backtest-governor",
                frozenset({protected_scope.scope_id}),
                "policy-v1",
                "environment-v1",
            ),
        ),
        current_environment_ref="environment-v1",
        current_policy_ref="policy-v1",
        clock=_clock,
    )
    permit = governance.authorize(request, authority_id="backtest-governor")
    assert isinstance(permit, BacktestPermit)
    binder = ProtectedViewBinder(
        permits=permits,
        clock=_clock,
        current_environment_ref="environment-v1",
        current_policy_ref="policy-v1",
    )
    view = binder.bind(
        permit=permit,
        request=request,
        requested_scope=protected_scope,
        caller_id="research-agent",
        resolve_exact_resource=lambda _: "protected-binding:catalog-v1",
    )
    assert isinstance(view, AuthorizedProtectedDataView)
    engine = BacktestEngine(
        permits=permits,
        frozen_systems=systems,
        views=binder,
        exposures=ExposureRecorder(registry=exposures, ledger=ledger, clock=_clock),
        ledger=ledger,
        clock=_clock,
        operations=engine_operations,
    )
    return (
        engine,
        request,
        permit,
        view,
        frozen,
        system,
        scenario,
        spec,
        standard,
        exposures,
        ledger,
        binder,
    )


def test_walk_forward_rebuilds_separate_clocks_and_retries_exactly_once() -> None:
    """Every t rebuilds I_t/S_t/W_t and exact retries disclose and execute once."""
    (
        engine,
        request,
        permit,
        view,
        frozen,
        system,
        scenario,
        _,
        _,
        exposures,
        ledger,
        _,
    ) = _authorized_execution()
    loads = 0

    def load(_binding: str) -> LoadedProtectedCatalog:
        nonlocal loads
        loads += 1
        return _loaded(_catalog())

    run = engine.execute(
        request=request,
        permit=permit,
        view=view,
        frozen=frozen,
        definition=system,
        scenario=scenario,
        recipient_id="research-process:1",
        load_protected_catalog=load,
    )
    replay = engine.execute(
        request=request,
        permit=permit,
        view=view,
        frozen=frozen,
        definition=system,
        scenario=scenario,
        recipient_id="research-process:1",
        load_protected_catalog=load,
    )

    assert replay is run
    assert run.status is BacktestRunStatus.COMPLETED
    assert len(run.decisions) == 3
    assert [len(item.information_observation_ids) for item in run.decisions] == [4, 4, 6]
    assert [len(item.training_row_ids) for item in run.decisions] == [2, 3, 3]
    assert all(item.fit and item.prediction and item.outcome for item in run.decisions)
    assert all(not item.failures for item in run.decisions)
    assert loads == 1
    assert len(exposures.records()) == 1
    assert len([item for item in ledger.entries() if item.event_type == "backtest.run-sealed"]) == 1
    poison = next(
        item.observation_id
        for item in _catalog().observations
        if item.provenance_ref == "provenance:future-poison"
    )
    assert all(poison not in item.information_observation_ids for item in run.decisions)
    frozen_attribute = "status"
    with pytest.raises(FrozenInstanceError):
        setattr(run, frozen_attribute, BacktestRunStatus.COMPLETED_WITH_FAILURES)
    with pytest.raises(ValueError, match="identity does not match"):
        replace(run, status=BacktestRunStatus.COMPLETED_WITH_FAILURES)
    with pytest.raises(IdempotencyConflictError, match="changed semantics"):
        engine.execute(
            request=request,
            permit=permit,
            view=view,
            frozen=frozen,
            definition=system,
            scenario=scenario,
            recipient_id="research-process:changed",
            load_protected_catalog=load,
        )
    assert loads == 1
    assert len(exposures.records()) == 1


def test_mismatch_fails_before_exposure_or_content_resolution() -> None:
    """System/protocol/scope mismatches cannot cross the protected disclosure boundary."""
    (
        engine,
        request,
        permit,
        view,
        frozen,
        system,
        scenario,
        _,
        _,
        exposures,
        _,
        _,
    ) = _authorized_execution()
    reads = 0

    def load(_binding: str) -> LoadedProtectedCatalog:
        nonlocal reads
        reads += 1
        return _loaded(_catalog())

    with pytest.raises(ProtectedExecutionMismatchError, match="exact issued"):
        engine.execute(
            request=request,
            permit=permit,
            view=view,
            frozen=frozen,
            definition=replace(system, training_protocol_id="training:changed"),
            scenario=scenario,
            recipient_id="research-process:1",
            load_protected_catalog=load,
        )
    assert reads == 0
    assert exposures.records() == ()


def test_future_poison_cannot_change_walk_forward_predictions_or_fit_rows() -> None:
    """Protected fitting and current features remain local to each legal historical boundary."""
    poison_catalog = _catalog(future_poison=True)
    clean_catalog = _catalog(future_poison=False)
    with_poison = _authorized_execution(protected_catalog=poison_catalog)
    without_poison = _authorized_execution(protected_catalog=clean_catalog)
    first = with_poison[0].execute(
        request=with_poison[1],
        permit=with_poison[2],
        view=with_poison[3],
        frozen=with_poison[4],
        definition=with_poison[5],
        scenario=with_poison[6],
        recipient_id="research-process:poison",
        load_protected_catalog=lambda _: _loaded(poison_catalog),
    )
    second = without_poison[0].execute(
        request=without_poison[1],
        permit=without_poison[2],
        view=without_poison[3],
        frozen=without_poison[4],
        definition=without_poison[5],
        scenario=without_poison[6],
        recipient_id="research-process:poison",
        load_protected_catalog=lambda _: _loaded(clean_catalog),
    )
    assert tuple(item.prediction.value for item in first.decisions if item.prediction) == tuple(
        item.prediction.value for item in second.decisions if item.prediction
    )
    assert tuple(len(item.training_row_ids) for item in first.decisions) == tuple(
        len(item.training_row_ids) for item in second.decisions
    )


def test_failure_after_disclosure_is_sealed_and_retry_does_not_reread() -> None:
    """A content failure still exposes the scope and retains every declared date."""
    (
        engine,
        request,
        permit,
        view,
        frozen,
        system,
        scenario,
        _,
        _,
        exposures,
        _,
        _,
    ) = _authorized_execution()
    reads = 0

    def fail(_binding: str) -> LoadedProtectedCatalog:
        nonlocal reads
        reads += 1
        raise OSError("protected sentinel must not enter the failure record")

    run = engine.execute(
        request=request,
        permit=permit,
        view=view,
        frozen=frozen,
        definition=system,
        scenario=scenario,
        recipient_id="research-process:1",
        load_protected_catalog=fail,
    )
    replay = engine.execute(
        request=request,
        permit=permit,
        view=view,
        frozen=frozen,
        definition=system,
        scenario=scenario,
        recipient_id="research-process:1",
        load_protected_catalog=fail,
    )
    assert replay is run
    assert reads == 1
    assert len(exposures.records()) == 1
    assert len(run.decisions) == len(scenario.decision_sample_keys)
    assert all(
        item.failures[0].code is ProtectedFailureCode.PROTECTED_CONTENT_RESOLUTION_FAILED
        for item in run.decisions
    )
    assert all("sentinel" not in item.failures[0].detail for item in run.decisions)


def test_changed_content_manifest_after_authorization_seals_failure() -> None:
    """A binding cannot serve different bytes after the exact permit and view were issued."""
    setup = _authorized_execution()
    engine, request, permit, view, frozen, system, scenario, *_, exposures, _, _binder = setup
    substituted = _catalog(future_poison=False)
    run = engine.execute(
        request=request,
        permit=permit,
        view=view,
        frozen=frozen,
        definition=system,
        scenario=scenario,
        recipient_id="research-process:manifest-substitution",
        load_protected_catalog=lambda _: _loaded(substituted),
    )

    assert run.status is BacktestRunStatus.COMPLETED_WITH_FAILURES
    assert len(exposures.records()) == 1
    assert all(item.prediction is None for item in run.decisions)
    assert all(
        item.failures[0].code is ProtectedFailureCode.PROTECTED_CONTENT_RESOLUTION_FAILED
        for item in run.decisions
    )


def test_same_time_population_slices_have_distinct_identity_and_records() -> None:
    """Panel sample identity includes dimensions and never collapses equal timestamps."""
    sample_a = SampleKey(ORIGIN + DAY * 3, (("entity", "A"),))
    sample_b = SampleKey(ORIGIN + DAY * 3, (("entity", "B"),))
    setup = _authorized_execution(decision_keys=(sample_a, sample_b))
    (
        engine,
        request,
        permit,
        view,
        frozen,
        system,
        panel,
        _,
        _,
        _,
        _,
        _,
    ) = setup
    changed_b = replace(
        panel,
        decision_sample_keys=(sample_a, SampleKey(sample_b.decision_time, (("entity", "C"),))),
    )

    assert panel.decision_times_ref != changed_b.decision_times_ref
    with pytest.raises(ValueError, match="ordered"):
        replace(panel, decision_sample_keys=(sample_b, sample_a))
    run = engine.execute(
        request=request,
        permit=permit,
        view=view,
        frozen=frozen,
        definition=system,
        scenario=panel,
        recipient_id="research-process:panel",
        load_protected_catalog=lambda _: _loaded(_catalog()),
    )
    assert tuple(item.dimensions for item in run.decisions) == (
        (("entity", "A"),),
        (("entity", "B"),),
    )
    assert len({item.decision_id for item in run.decisions}) == 2
    assert all(
        item.failures[0].code is ProtectedFailureCode.DIMENSION_SCOPE_UNSUPPORTED
        for item in run.decisions
    )


@pytest.mark.parametrize(
    "scenario_kind",
    [ScenarioKind.ALTERNATIVE_TEMPORAL_PATH, ScenarioKind.SYNTHETIC_COUNTERFACTUAL],
)
def test_nonhistorical_world_remains_typed_and_does_not_read_historical_content(
    scenario_kind: ScenarioKind,
) -> None:
    """Unsupported alternative worlds are never relabeled as historical evidence."""
    (
        engine,
        request,
        permit,
        view,
        frozen,
        system,
        scenario,
        _,
        _,
        exposures,
        _,
        _,
    ) = _authorized_execution(scenario_kind=scenario_kind)
    reads = 0

    def fail_if_read(_binding: str) -> LoadedProtectedCatalog:
        nonlocal reads
        reads += 1
        raise AssertionError("non-historical execution must not resolve protected content")

    run = engine.execute(
        request=request,
        permit=permit,
        view=view,
        frozen=frozen,
        definition=system,
        scenario=scenario,
        recipient_id="research-process:1",
        load_protected_catalog=fail_if_read,
    )
    assert run.status is BacktestRunStatus.UNSUPPORTED
    assert run.scenario_kind is scenario_kind
    assert all(
        item.failures[0].code is ProtectedFailureCode.UNSUPPORTED_SCENARIO_KIND
        for item in run.decisions
    )
    assert reads == 0
    assert exposures.records() == ()


def _run_and_evidence(
    *,
    protected_outcomes: tuple[float, float, float] | None = None,
    maximum_stability_stddev: float = 100.0,
    disable_optional_views: bool = False,
) -> tuple[
    BacktestRun,
    EvaluationSpec,
    PromotionStandard,
    ResearchLedger,
    BacktestRunRegistry,
]:
    protected_catalog = _catalog(protected_outcomes=protected_outcomes)
    setup = _authorized_execution(
        maximum_stability_stddev=maximum_stability_stddev,
        disable_optional_views=disable_optional_views,
        protected_catalog=protected_catalog,
    )
    (
        engine,
        request,
        permit,
        view,
        frozen,
        system,
        scenario,
        spec,
        standard,
        _,
        ledger,
        _,
    ) = setup
    run = engine.execute(
        request=request,
        permit=permit,
        view=view,
        frozen=frozen,
        definition=system,
        scenario=scenario,
        recipient_id="research-process:evaluation",
        load_protected_catalog=lambda _: _loaded(protected_catalog),
    )
    return run, spec, standard, ledger, engine.issued_runs


def test_evaluator_is_measurement_only_multidimensional_and_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Evaluation cannot fit and retains coverage, failures, stability, and concentration."""
    run, spec, _, ledger, runs = _run_and_evidence()

    def forbidden_fit(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("Evaluator attempted to fit")

    monkeypatch.setattr(SystemTrainer, "fit", forbidden_fit)
    evaluator = Evaluator(ledger=ledger, runs=runs, clock=_clock)
    report = evaluator.measure(run, spec)
    replay = evaluator.measure(run, spec)

    assert replay is report
    assert report.metric(MetricName.COVERAGE).value == 1.0
    assert report.metric(MetricName.FAILURE_RATE).value == 0.0
    assert report.per_time
    assert report.per_dimension
    assert report.stability.absolute_error_stddev is not None
    assert report.concentration.maximum_squared_error_share is not None
    assert {item.name.value for item in report.metrics} == {
        "mse",
        "mae",
        "coverage",
        "failure_rate",
    }
    assert "pnl" not in {item.name.value for item in report.metrics}
    assert (
        len([item for item in ledger.entries() if item.event_type == "evaluation.run-measured"])
        == 1
    )

    changed = replace(spec, metric_names=(MetricName.MSE, MetricName.COVERAGE))
    assert changed.identity != spec.identity
    with pytest.raises(ValueError, match="identities differ"):
        evaluator.measure(run, changed)


def test_failed_decision_date_is_retained_in_coverage_and_failure_structure() -> None:
    """A declared early date cannot disappear merely because its fit window is insufficient."""
    setup = _authorized_execution(minimum_training_rows=3)
    (
        engine,
        request,
        permit,
        view,
        frozen,
        system,
        scenario,
        spec,
        _,
        _,
        ledger,
        _,
    ) = setup
    run = engine.execute(
        request=request,
        permit=permit,
        view=view,
        frozen=frozen,
        definition=system,
        scenario=scenario,
        recipient_id="research-process:failures",
        load_protected_catalog=lambda _: _loaded(_catalog()),
    )
    assert len(run.decisions) == 3
    assert run.decisions[0].failures[0].code is ProtectedFailureCode.TRAINING_WINDOW_NOT_READY
    assert run.decisions[1].prediction is not None
    assert run.decisions[2].prediction is not None
    report = Evaluator(ledger=ledger, runs=engine.issued_runs, clock=_clock).measure(run, spec)
    assert report.metric(MetricName.COVERAGE).value == pytest.approx(2 / 3)
    assert report.metric(MetricName.FAILURE_RATE).value == pytest.approx(1 / 3)
    assert report.failures[0].code == ProtectedFailureCode.TRAINING_WINDOW_NOT_READY.value


def test_frozen_unsupported_fit_fails_each_date_without_recipe_fallback() -> None:
    """A protected fit failure cannot substitute another model or remove failed dates."""
    setup = _authorized_execution(algorithm="unsupported-best-effort-model")
    (
        engine,
        request,
        permit,
        view,
        frozen,
        system,
        scenario,
        _,
        _,
        _,
        _,
        _,
    ) = setup
    run = engine.execute(
        request=request,
        permit=permit,
        view=view,
        frozen=frozen,
        definition=system,
        scenario=scenario,
        recipient_id="research-process:no-fallback",
        load_protected_catalog=lambda _: _loaded(_catalog()),
    )
    assert len(run.decisions) == len(scenario.decision_sample_keys)
    assert all(item.prediction is None for item in run.decisions)
    assert all(item.failures[0].code is ProtectedFailureCode.FIT_FAILED for item in run.decisions)


def test_independent_validator_retains_rejection_and_only_promote_publishes() -> None:
    """A beneficiary cannot validate itself and rejected evidence remains append-only history."""
    run, spec, standard, ledger, runs = _run_and_evidence(
        protected_outcomes=(4.0, 5.0, 5.0),
    )
    evaluator = Evaluator(ledger=ledger, runs=runs, clock=_clock)
    report = evaluator.measure(run, spec)
    negatives = NegativeResultRegistry()
    validator = Validator(
        authorized_authority_ids=frozenset({"independent-validator"}),
        authority_policy_ref="validation-policy:v1",
        ledger=ledger,
        reports=evaluator.issued_reports,
        negatives=negatives,
        clock=_clock,
    )
    promoted = validator.validate(
        report,
        standard,
        authority_id="independent-validator",
        requester_id="research-agent",
        beneficiary_id="candidate-team",
    )
    replay = validator.validate(
        report,
        standard,
        authority_id="independent-validator",
        requester_id="research-agent",
        beneficiary_id="candidate-team",
    )
    assert replay is promoted
    assert promoted.status is ValidationStatus.PROMOTE

    publisher = FindingPublisher(
        ledger=ledger,
        reports=evaluator.issued_reports,
        decisions=validator.issued_decisions,
        clock=_clock,
    )
    claim = _claim(_system())
    finding = publisher.publish(
        promoted,
        report,
        claim=claim,
    )
    assert (
        publisher.publish(
            promoted,
            report,
            claim=claim,
        )
        is finding
    )
    assert set(report.caveats).issubset(finding.caveats)
    assert set(claim.required_caveats).issubset(finding.caveats)
    with pytest.raises(ValueError, match="exact promoted"):
        publisher.publish(
            promoted,
            report,
            claim=replace(claim, statement="A broader changed claim."),
        )

    self_negatives = NegativeResultRegistry()
    self_validator = Validator(
        authorized_authority_ids=frozenset({"candidate-team"}),
        authority_policy_ref="validation-policy:v1",
        ledger=ledger,
        reports=evaluator.issued_reports,
        negatives=self_negatives,
        clock=_clock,
    )
    rejected = self_validator.validate(
        report,
        standard,
        authority_id="candidate-team",
        requester_id="research-agent",
        beneficiary_id="candidate-team",
    )
    assert rejected.status is ValidationStatus.REJECT
    assert "SELF_VALIDATION_DENIED" in rejected.reasons
    assert len(self_negatives.records()) == 1
    with pytest.raises(ValueError, match="rejected"):
        publisher.publish(
            rejected,
            report,
            claim=claim,
        )

    changed_standard = replace(
        standard,
        criteria=(
            MetricCriterion(MetricName.MSE, CriterionComparison.LESS_THAN_OR_EQUAL, 0.5),
            *standard.criteria[1:],
        ),
    )
    assert changed_standard.identity != standard.identity
    with pytest.raises(ValueError, match="not predeclared"):
        validator.validate(
            report,
            changed_standard,
            authority_id="independent-validator",
            requester_id="research-agent",
            beneficiary_id="candidate-team",
        )
    wrong_policy = Validator(
        authorized_authority_ids=frozenset({"independent-validator"}),
        authority_policy_ref="validation-policy:changed",
        ledger=ledger,
        reports=evaluator.issued_reports,
        negatives=NegativeResultRegistry(),
        clock=_clock,
    )
    with pytest.raises(ValueError, match="authority policy"):
        wrong_policy.validate(
            report,
            standard,
            authority_id="independent-validator",
            requester_id="research-agent",
            beneficiary_id="candidate-team",
        )


def test_equal_headline_mse_different_stability_changes_predeclared_decision() -> None:
    """Equal scalar quality cannot hide temporal instability or concentration."""
    stable_run, stable_spec, stable_standard, stable_ledger, stable_runs = _run_and_evidence(
        protected_outcomes=(4.0, 5.0, 5.0),
        maximum_stability_stddev=0.1,
    )
    unstable_run, unstable_spec, unstable_standard, unstable_ledger, unstable_runs = (
        _run_and_evidence(
            protected_outcomes=(3.0, 4.0, 4.0 + 3**0.5),
            maximum_stability_stddev=0.1,
        )
    )
    stable_evaluator = Evaluator(ledger=stable_ledger, runs=stable_runs, clock=_clock)
    unstable_evaluator = Evaluator(ledger=unstable_ledger, runs=unstable_runs, clock=_clock)
    stable_report = stable_evaluator.measure(stable_run, stable_spec)
    unstable_report = unstable_evaluator.measure(
        unstable_run,
        unstable_spec,
    )
    assert stable_report.metric(MetricName.MSE).value == pytest.approx(1.0)
    assert unstable_report.metric(MetricName.MSE).value == pytest.approx(1.0)
    assert stable_report.stability.absolute_error_stddev == pytest.approx(0.0)
    unstable_stddev = unstable_report.stability.absolute_error_stddev
    assert unstable_stddev is not None
    assert unstable_stddev > 0.1

    stable_decision = Validator(
        authorized_authority_ids=frozenset({"validator"}),
        authority_policy_ref="validation-policy:v1",
        ledger=stable_ledger,
        reports=stable_evaluator.issued_reports,
        negatives=NegativeResultRegistry(),
        clock=_clock,
    ).validate(
        stable_report,
        stable_standard,
        authority_id="validator",
        requester_id="research-agent",
        beneficiary_id="candidate-team",
    )
    unstable_decision = Validator(
        authorized_authority_ids=frozenset({"validator"}),
        authority_policy_ref="validation-policy:v1",
        ledger=unstable_ledger,
        reports=unstable_evaluator.issued_reports,
        negatives=NegativeResultRegistry(),
        clock=_clock,
    ).validate(
        unstable_report,
        unstable_standard,
        authority_id="validator",
        requester_id="research-agent",
        beneficiary_id="candidate-team",
    )
    assert stable_decision.status is ValidationStatus.PROMOTE
    assert unstable_decision.status is ValidationStatus.REJECT


def test_rehashed_run_report_and_decision_cannot_cross_authority_boundaries() -> None:
    """Valid content hashes are evidence identity, not execution or promotion authority."""
    run, spec, standard, ledger, runs = _run_and_evidence()
    evaluator = Evaluator(ledger=ledger, runs=runs, clock=_clock)
    with pytest.raises(ValueError, match="not issued"):
        evaluator.measure(_forge_run(run), spec)

    report = evaluator.measure(run, spec)
    validator = Validator(
        authorized_authority_ids=frozenset({"validator"}),
        authority_policy_ref="validation-policy:v1",
        ledger=ledger,
        reports=evaluator.issued_reports,
        negatives=NegativeResultRegistry(),
        clock=_clock,
    )
    with pytest.raises(ValueError, match="not issued"):
        validator.validate(
            _forge_report(report),
            standard,
            authority_id="validator",
            requester_id="research-agent",
            beneficiary_id="candidate-team",
        )

    decision = validator.validate(
        report,
        standard,
        authority_id="validator",
        requester_id="research-agent",
        beneficiary_id="candidate-team",
    )
    publisher = FindingPublisher(
        ledger=ledger,
        reports=evaluator.issued_reports,
        decisions=validator.issued_decisions,
        clock=_clock,
    )
    with pytest.raises(ValueError, match="not issued"):
        publisher.publish(_forge_decision(decision), report, claim=_claim(_system()))
    assert not hasattr(runs, "add")
    assert not hasattr(evaluator.issued_reports, "add")
    assert not hasattr(validator.issued_decisions, "add")


def test_rehashed_frozen_substitution_is_rejected_before_disclosure() -> None:
    """Engine authority comes from the freeze registry, never a caller-supplied snapshot."""
    setup = _authorized_execution()
    engine, request, permit, view, frozen, system, scenario, *_, exposures, _, _binder = setup
    candidate_version = "caller-forged-version"
    forged_id = scientific_identity(
        "frozen-system",
        (
            ("system_id", frozen.system_id),
            ("candidate_version", candidate_version),
            ("ancestry_refs", frozen.ancestry_refs),
            ("development_evidence_refs", frozen.development_evidence_refs),
            ("protocol_refs", frozen.protocol_refs),
            ("environment_ref", frozen.environment_ref),
            ("standard_ref", frozen.standard_ref),
            ("freeze_decision_id", frozen.freeze_decision_id),
        ),
    )
    forged = replace(
        frozen,
        frozen_system_id=forged_id,
        candidate_version=candidate_version,
    )
    loads = 0

    def load(_binding: str) -> LoadedProtectedCatalog:
        nonlocal loads
        loads += 1
        return _loaded(_catalog())

    with pytest.raises(ProtectedExecutionMismatchError, match="authorities"):
        engine.execute(
            request=request,
            permit=permit,
            view=view,
            frozen=forged,
            definition=system,
            scenario=scenario,
            recipient_id="research-process:forgery",
            load_protected_catalog=load,
        )
    assert loads == 0
    assert exposures.records() == ()


def test_post_seal_ack_loss_does_not_repeat_any_protected_pipeline_effect() -> None:
    """Run, report, decision, and finding retries return sealed originals exactly once."""

    def lose_once() -> PrivilegedOperationCoordinator:
        lost = False

        def after_seal(_operation_key: str) -> None:
            nonlocal lost
            if not lost:
                lost = True
                raise ConnectionError("post-seal acknowledgement lost")

        return PrivilegedOperationCoordinator(after_effect_sealed=after_seal)

    setup = _authorized_execution(engine_operations=lose_once())
    (
        engine,
        request,
        permit,
        view,
        frozen,
        system,
        scenario,
        spec,
        standard,
        exposures,
        ledger,
        _,
    ) = setup
    loads = 0

    def load(_binding: str) -> LoadedProtectedCatalog:
        nonlocal loads
        loads += 1
        return _loaded(_catalog())

    with pytest.raises(ConnectionError, match="lost"):
        engine.execute(
            request=request,
            permit=permit,
            view=view,
            frozen=frozen,
            definition=system,
            scenario=scenario,
            recipient_id="research-process:lost-ack",
            load_protected_catalog=load,
        )
    run = engine.execute(
        request=request,
        permit=permit,
        view=view,
        frozen=frozen,
        definition=system,
        scenario=scenario,
        recipient_id="research-process:lost-ack",
        load_protected_catalog=load,
    )
    assert loads == 1
    assert len(exposures.records()) == 1
    assert len([e for e in ledger.entries() if e.event_type == "backtest.run-sealed"]) == 1

    evaluator = Evaluator(
        ledger=ledger,
        runs=engine.issued_runs,
        clock=_clock,
        operations=lose_once(),
    )
    with pytest.raises(ConnectionError, match="lost"):
        evaluator.measure(run, spec)
    report = evaluator.measure(run, spec)
    assert len([e for e in ledger.entries() if e.event_type == "evaluation.run-measured"]) == 1

    validator = Validator(
        authorized_authority_ids=frozenset({"validator"}),
        authority_policy_ref="validation-policy:v1",
        ledger=ledger,
        reports=evaluator.issued_reports,
        negatives=NegativeResultRegistry(),
        clock=_clock,
        operations=lose_once(),
    )
    with pytest.raises(ConnectionError, match="lost"):
        validator.validate(
            report,
            standard,
            authority_id="validator",
            requester_id="research-agent",
            beneficiary_id="candidate-team",
        )
    decision = validator.validate(
        report,
        standard,
        authority_id="validator",
        requester_id="research-agent",
        beneficiary_id="candidate-team",
    )
    assert decision.status is ValidationStatus.PROMOTE
    assert len([e for e in ledger.entries() if e.event_type == "finding.validation-decided"]) == 1

    publisher = FindingPublisher(
        ledger=ledger,
        reports=evaluator.issued_reports,
        decisions=validator.issued_decisions,
        clock=_clock,
        operations=lose_once(),
    )
    claim = _claim(system)
    with pytest.raises(ConnectionError, match="lost"):
        publisher.publish(decision, report, claim=claim)
    finding = publisher.publish(decision, report, claim=claim)
    publisher.issued_findings.require_issued(finding)
    assert (
        len([e for e in ledger.entries() if e.event_type == "finding.validated-claim-published"])
        == 1
    )


def test_unsupported_run_cannot_promote_under_permissive_thresholds() -> None:
    """Formal execution validity is a hard gate independent of favorable metrics."""
    setup = _authorized_execution(scenario_kind=ScenarioKind.ALTERNATIVE_TEMPORAL_PATH)
    engine, request, permit, view, frozen, system, scenario, spec, standard, _, ledger, _ = setup
    run = engine.execute(
        request=request,
        permit=permit,
        view=view,
        frozen=frozen,
        definition=system,
        scenario=scenario,
        recipient_id="research-process:unsupported",
        load_protected_catalog=lambda _: _loaded(_catalog()),
    )
    evaluator = Evaluator(ledger=ledger, runs=engine.issued_runs, clock=_clock)
    report = evaluator.measure(run, spec)
    assert report.run_status is BacktestRunStatus.UNSUPPORTED
    assert report.execution_valid is False
    validator = Validator(
        authorized_authority_ids=frozenset({"validator"}),
        authority_policy_ref="validation-policy:v1",
        ledger=ledger,
        reports=evaluator.issued_reports,
        negatives=NegativeResultRegistry(),
        clock=_clock,
    )
    decision = validator.validate(
        report,
        standard,
        authority_id="validator",
        requester_id="research-agent",
        beneficiary_id="candidate-team",
    )
    assert decision.status is ValidationStatus.REJECT
    assert "RUN_EXECUTION_INVALID" in decision.reasons


@pytest.mark.parametrize("disable_optional_views", [False, True])
def test_non_finite_values_fail_closed_with_optional_views_on_or_off(
    disable_optional_views: bool,
) -> None:
    """NaN cannot pass through thresholds, records, reports, or independent validation."""
    with pytest.raises(ValueError, match="finite"):
        MetricCriterion(MetricName.MSE, CriterionComparison.LESS_THAN_OR_EQUAL, float("nan"))
    run, spec, standard, ledger, runs = _run_and_evidence(
        disable_optional_views=disable_optional_views
    )
    prediction = next(item.prediction for item in run.decisions if item.prediction is not None)
    outcome = next(item.outcome for item in run.decisions if item.outcome is not None)
    with pytest.raises(ValueError, match="finite"):
        replace(prediction, value=float("nan"))
    with pytest.raises(ValueError, match="finite"):
        replace(outcome, value=float("nan"))
    with pytest.raises(ValueError, match="finite"):
        MetricResult(MetricName.MSE, float("nan"), 1, 1, None)
    with pytest.raises(ValueError, match="finite"):
        replace(standard, maximum_stability_stddev=float("nan"))

    unsafe_prediction = object.__new__(ProtectedPredictionRecord)
    for field_name in prediction.__dataclass_fields__:
        object.__setattr__(
            unsafe_prediction,
            field_name,
            float("nan") if field_name == "value" else getattr(prediction, field_name),
        )
    source_decision = next(item for item in run.decisions if item.prediction is prediction)
    decision_payload = {
        name: unsafe_prediction if name == "prediction" else getattr(source_decision, name)
        for name in source_decision.__dataclass_fields__
        if name != "decision_id"
    }
    unsafe_decision = replace(
        source_decision,
        decision_id=stable_identity("backtest-decision", decision_payload),
        prediction=unsafe_prediction,
    )
    decisions = tuple(
        unsafe_decision if item is source_decision else item for item in run.decisions
    )
    run_payload = {
        name: decisions if name == "decisions" else getattr(run, name)
        for name in run.__dataclass_fields__
        if name != "run_id"
    }
    unsafe_run = replace(
        run,
        run_id=stable_identity("backtest-run", run_payload),
        decisions=decisions,
    )

    class _ConfiguredRunAuthority:
        @staticmethod
        def require_issued(_run: BacktestRun) -> None:
            return None

    unsafe_evaluator = Evaluator(
        ledger=ledger,
        runs=cast("BacktestRunRegistry", _ConfiguredRunAuthority()),
        clock=_clock,
    )
    insufficiency = unsafe_evaluator.measure(unsafe_run, spec)
    assert any(item.code == "non_finite_evidence" for item in insufficiency.failures)
    assert "non-finite prediction or outcome evidence is formally insufficient" in (
        insufficiency.caveats
    )

    evaluator = Evaluator(ledger=ledger, runs=runs, clock=_clock)
    report = evaluator.measure(run, spec)
    unsafe = object.__new__(MetricResult)
    object.__setattr__(unsafe, "name", MetricName.MSE)
    object.__setattr__(unsafe, "value", float("nan"))
    object.__setattr__(unsafe, "sample_size", 1)
    object.__setattr__(unsafe, "denominator", 1)
    object.__setattr__(unsafe, "warning", None)
    metrics = tuple(unsafe if item.name is MetricName.MSE else item for item in report.metrics)
    forged = _forge_report(report, metrics=metrics)

    class _ConfiguredReportAuthority:
        @staticmethod
        def require_issued(_report: EvaluationReport) -> None:
            return None

    validator = Validator(
        authorized_authority_ids=frozenset({"validator"}),
        authority_policy_ref="validation-policy:v1",
        ledger=ledger,
        reports=cast("EvaluationReportRegistry", _ConfiguredReportAuthority()),
        negatives=NegativeResultRegistry(),
        clock=_clock,
    )
    decision = validator.validate(
        forged,
        standard,
        authority_id="validator",
        requester_id="research-agent",
        beneficiary_id="candidate-team",
    )
    assert decision.status is ValidationStatus.REJECT
    assert "NON_FINITE_REPORT_EVIDENCE" in decision.reasons
