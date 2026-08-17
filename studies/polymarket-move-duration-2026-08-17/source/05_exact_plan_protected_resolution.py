"""Replay the duration candidate against an exact issued plan, then resolve one holdout."""

# ruff: noqa: ANN001, ANN202, C901, D103, E501, EM101, INP001, PLR0912, PLR0915, PLR2004, T201, TRY003

from __future__ import annotations

import hashlib
import json
import runpy
from datetime import timedelta
from pathlib import Path

from research_agent.data_adapters.polymarket import (
    PolymarketCorpusSnapshotRef,
    PolymarketCorpusStore,
    build_polymarket_development_analysis,
    register_polymarket_resolution_corpus,
)
from research_agent.data_foundation import (
    MissingnessPolicy,
    SampleKey,
    TemporalOffset,
    TrainingWindowPolicy,
    WindowKind,
)
from research_agent.investigation import (
    AuthoredBacktestEngine,
    AuthoredCandidateManifest,
    AuthoredFreezeService,
    AuthoredProgramProposal,
    AuthoredProtectedPlan,
    AuthoredProtectedResolutionService,
    DevelopmentBudget,
    InvestigationRequest,
    ProtectedEvaluationPredeclaration,
    ResearchQuestion,
    RuntimeInvestigationCoordinator,
    configure_authored_protected_plan_authority,
)
from research_agent.protected_evaluation import (
    BacktestGovernance,
    CriterionComparison,
    EvaluationScenario,
    EvaluationSpec,
    Evaluator,
    ExposureRecorder,
    ExposureRegistry,
    FindingPublisher,
    FreezeEligibilityRegistry,
    FreezeGate,
    FrozenSystemRegistry,
    MetricCriterion,
    MetricName,
    NegativeResultRegistry,
    PermissionGrant,
    PermitRegistry,
    PromotionStandard,
    ProtectedContentManifest,
    ProtectedExposureStatus,
    ProtectedResourceScope,
    ProtectedViewBinder,
    ResearchLedger,
    ScenarioKind,
    Validator,
)
from research_agent.scientific_workflow import (
    ValidationAuthorityGrant,
    WorkflowAuthorityRegistry,
    configure_protected_resource_authority,
)

HERE = Path(__file__).resolve().parent
SOURCE_04 = HERE / "04_coordinator_freeze_replay.py"
RECEIPT = HERE.parent / "protected-receipts/05_exact_plan_protected_resolution.json"
SNAPSHOT_SHA256 = "610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f"
SNAPSHOT_SIZE = 19_434_443
WORKSPACE = Path(__file__).resolve().parents[5] / "data/chronos/polymarket-corpora"
EXPECTED_CANDIDATE_ID = (
    "authored-candidate:bb76fb6846cd5bb935934e16d53c520865f5649d230c53b0cc1ca5c3e1be770d"
)
EXPECTED_EVIDENCE_ID = (
    "authored-development-evidence:7729af09c56fed64323cc805df708ab2643ec547aa90877dda30e53a6e9c5372"
)
DATA_PROTOCOL = "protocol:data:polymarket-corpus-610b8b9-final-seven-events-v2"
TRAINING_PROTOCOL = "protocol:training:authored-expanding-event-equal-duration-v2"
VALIDATION_POLICY = "policy:validation:polymarket-duration-holdout-v1"
RESOURCE_POLICY = "policy:protected-resource:polymarket-duration-holdout-v1"


def _manifest_for(catalog) -> ProtectedContentManifest:
    content = catalog.identity.encode()
    return ProtectedContentManifest.create(
        content_digest=hashlib.sha256(content).hexdigest(),
        byte_length=len(content),
        catalog_id=catalog.identity,
        provenance_ref=f"authority-retained:{SNAPSHOT_SHA256}",
    )


def _plan(full_catalog, protected_keys: tuple[SampleKey, ...], all_keys: tuple[SampleKey, ...]):
    content_manifest = _manifest_for(full_catalog)
    scope = ProtectedResourceScope(
        resource_id="polymarket-retained-duration-holdout",
        resource_version="v1",
        slice_id="final-seven-events",
        environment_ref=full_catalog.environment_id,
        policy_ref=RESOURCE_POLICY,
        content_manifest_id=content_manifest.manifest_id,
        content_identity_id=content_manifest.content_identity_id,
        epistemic_period_ref="period:polymarket-corpus-610b8b9-final-seven-events",
        exposure_status=ProtectedExposureStatus.UNSEEN,
    )
    outcome_recorded_at = max(item.available_at for item in full_catalog.observations)
    scenario = EvaluationScenario(
        name="Polymarket sampled two-cent duration holdout",
        version=1,
        kind=ScenarioKind.HISTORICAL_WALK_FORWARD,
        decision_sample_keys=protected_keys,
        training_candidate_keys=all_keys,
        outcome_recorded_at=outcome_recorded_at,
        training_protocol_ref=TRAINING_PROTOCOL,
        window_policy=TrainingWindowPolicy(
            1,
            WindowKind.EXPANDING,
            40,
            None,
            TRAINING_PROTOCOL,
        ),
        missingness_policy=MissingnessPolicy.EXCLUDE_EXAMPLE,
        interpretation="one untouched whole-event chronological Polymarket holdout",
        environment_ref=full_catalog.environment_id,
        data_protocol_ref=DATA_PROTOCOL,
        provenance_refs=(
            f"polymarket-corpus:{SNAPSHOT_SHA256}",
            "partition:whole-event-chronological-latest-resolution-v1",
            "sampling:greedy-non-overlapping-48h-duration-v1",
        ),
    )
    specification = EvaluationSpec(
        name="Polymarket sampled duration protected forecast quality",
        version=1,
        protocol_ref="protocol:evaluation:duration-mae-mse-coverage-stability-v1",
        metric_names=(
            MetricName.MAE,
            MetricName.MSE,
            MetricName.COVERAGE,
            MetricName.FAILURE_RATE,
        ),
        rolling_window=10,
        include_per_time=True,
        include_dimension_views=True,
        include_stability=True,
        include_concentration=True,
        benchmark_refs=(
            "development-state-observation-mae:0.2594522719950635",
            "development-state-observation-mse:0.10689266569308234",
        ),
        provenance_refs=(
            "gate-memo:polymarket-move-duration-protected-gate",
            EXPECTED_EVIDENCE_ID,
        ),
    )
    standard = PromotionStandard(
        name="Polymarket sampled duration protected standard",
        version=1,
        evaluation_spec_id=specification.identity,
        criteria=(
            MetricCriterion(MetricName.MAE, CriterionComparison.LESS_THAN_OR_EQUAL, 0.25946),
            MetricCriterion(MetricName.MSE, CriterionComparison.LESS_THAN_OR_EQUAL, 0.10690),
            MetricCriterion(MetricName.COVERAGE, CriterionComparison.GREATER_THAN_OR_EQUAL, 0.95),
            MetricCriterion(MetricName.FAILURE_RATE, CriterionComparison.LESS_THAN_OR_EQUAL, 0.05),
        ),
        maximum_stability_stddev=0.20,
        maximum_error_concentration=0.50,
        required_scenario_kind=ScenarioKind.HISTORICAL_WALK_FORWARD,
        authority_policy_ref=VALIDATION_POLICY,
        provenance_refs=(
            "gate-memo:polymarket-move-duration-protected-gate",
            "standard:fixed-before-protected-disclosure",
        ),
    )
    plan = AuthoredProtectedPlan.create(
        scenario=scenario,
        evaluation_spec=specification,
        promotion_standard=standard,
        protected_scope=scope,
        claim_name="Polymarket sampled two-cent movement-duration finding",
        claim_version=1,
        claim_statement="The exact frozen state-staleness ridge met its predeclared sampled two-cent first-passage duration standard on the retained final-seven-event holdout.",
        claim_scope_limitations=(
            "Applies only to the exact retained corpus and whole-event final-seven-event holdout.",
            "Predicts sampled movement duration, not direction, resolution, executable return, or profitability.",
        ),
        claim_required_caveats=(
            "Sampled first passage is not continuous-time first passage.",
            "Retained observation staleness may reflect the observation process rather than information arrival.",
            "Protected success does not establish causality or a deployable trading strategy.",
        ),
        claim_provenance_refs=(
            "claim-template:sampled-two-cent-first-passage-duration-v2",
            "gate-memo:polymarket-move-duration-protected-gate",
        ),
    )
    return plan, content_manifest


def _metric_json(item) -> dict[str, object]:
    return {
        "name": item.name.value,
        "value": item.value,
        "sample_size": item.sample_size,
        "denominator": item.denominator,
        "warning": item.warning,
    }


def main() -> None:
    prior = runpy.run_path(str(SOURCE_04))
    development_catalog_builder = prior["_development_catalog"]
    sample_key_builder = prior["_sample_keys"]
    duration_metrics = prior["_duration_metrics"]
    state_feature_names = prior["STATE_FEATURE_NAMES"]
    staleness_feature_names = prior["STALENESS_FEATURE_NAMES"]
    event_mean_source = prior["EVENT_MEAN_SOURCE"]
    state_source = prior["STATE_RIDGE_SOURCE"]
    staleness_source = prior["STALENESS_RIDGE_SOURCE"]

    ref = PolymarketCorpusSnapshotRef(SNAPSHOT_SHA256, SNAPSHOT_SIZE)
    snapshot = PolymarketCorpusStore(WORKSPACE).load(ref)
    analysis = build_polymarket_development_analysis(
        snapshot,
        session_id="formal-move-duration-panel-2026-08-17",
    )
    development_events = frozenset(analysis.partition.development_event_ids)
    protected_events = frozenset(
        contract.event_id
        for contract in snapshot.corpus.contracts
        if contract.event_id not in development_events
    )
    development_markets = frozenset(
        contract.market_id
        for contract in snapshot.corpus.contracts
        if contract.event_id in development_events
    )
    protected_markets = frozenset(
        contract.market_id
        for contract in snapshot.corpus.contracts
        if contract.event_id in protected_events
    )
    development_catalog = development_catalog_builder(snapshot, development_markets)
    full_catalog = register_polymarket_resolution_corpus(snapshot).catalog
    development_prices = next(
        item
        for item in development_catalog.datasets
        if item.schema.dataset_id == "polymarket-outcome-price-series"
    )
    full_prices = next(
        item
        for item in full_catalog.datasets
        if item.schema.dataset_id == "polymarket-outcome-price-series"
    )
    development_keys = sample_key_builder(development_prices)
    all_keys = sample_key_builder(full_prices)
    protected_keys = tuple(
        key for key in all_keys if dict(key.dimensions)["market_id"] in protected_markets
    )
    if not protected_keys or any(
        dict(key.dimensions)["market_id"] not in protected_markets for key in protected_keys
    ):
        raise ValueError("protected decision scope is empty or crossed the event partition")
    if any(
        dict(key.dimensions)["market_id"] not in development_markets for key in development_keys
    ):
        raise ValueError("protected market entered the development key set")

    plan, content_manifest = _plan(full_catalog, protected_keys, all_keys)
    plan_registry, plan_issuer = configure_authored_protected_plan_authority(
        "authority:polymarket-duration-protected-plan"
    )
    plan_issuer.issue(plan)
    resource_registry, resource_issuer = configure_protected_resource_authority(
        "authority:polymarket-retained-corpus"
    )
    resource_registration = resource_issuer.issue(
        scope=plan.protected_scope,
        resource_binding_ref=f"binding:polymarket-corpus:{SNAPSHOT_SHA256}:duration-holdout-v1",
        content_manifest=content_manifest,
        catalog=full_catalog,
    )

    probability = development_prices.schema.field_ref("market_probability")
    question = ResearchQuestion(
        "question:polymarket-sampled-first-passage-duration-panel",
        "Does decision-time sampled-price staleness improve capped 48-hour two-cent first-passage duration prediction beyond probability state?",
        development_catalog.environment_id,
        "task:polymarket-move-duration-search",
        (
            "exploration:duration-benchmark-01",
            "exploration:duration-mechanism-compression-02",
            "implementation:authored-numeric-temporal-payload",
        ),
    )
    declaration = ProtectedEvaluationPredeclaration(
        data_protocol_ref=plan.scenario.data_protocol_ref,
        training_protocol_ref=plan.scenario.training_protocol_ref,
        scenario_ref=plan.scenario.identity,
        decision_times_ref=plan.scenario.decision_times_ref,
        evaluation_spec_ref=plan.evaluation_spec.identity,
        validation_standard_ref=plan.promotion_standard.identity,
        protected_scope_id=plan.protected_scope.scope_id,
        claim_template_ref=plan.claim_template_ref,
        freeze_standard_ref="standard:freeze:formal-duration-gate-v2",
    )
    request = InvestigationRequest(
        question=question,
        catalog=development_catalog,
        sample_keys=development_keys,
        current_time=max(item.available_at for item in development_catalog.observations),
        budget=DevelopmentBudget(3, 40, 500, "mse", 0.15),
        random_seed=43,
        protected_predeclaration=declaration,
    )
    plan.require_predeclared(declaration)
    population_names = tuple(
        sorted(development_prices.schema.resolve("market_probability").dimensions)
    )

    def candidate_manifest(feature_names: tuple[str, ...]) -> AuthoredCandidateManifest:
        return AuthoredCandidateManifest(
            question_id=question.question_id,
            environment_id=development_catalog.environment_id,
            predictor_fields=(probability,),
            outcome_field=probability,
            horizon=TemporalOffset.elapsed(timedelta(hours=48)),
            minimum_outcome_points=1,
            population_dimensions=(),
            feature_names=feature_names,
            missing_value_policy="exclude_example",
            evidence_refs=question.evidence_refs,
            provenance_refs=(ref.uri, "researcher:chronos-authored-program"),
            population_dimension_names=population_names,
        )

    session_id = "session:chronos-polymarket-duration-exact-protected"
    episode_id = "episode:chronos-polymarket-duration-exact-protected"
    coordinator = RuntimeInvestigationCoordinator()
    registration = coordinator.register(request, session_id=session_id, episode_id=episode_id)
    baseline_runtime = coordinator.execute(
        registration.registration_id,
        AuthoredProgramProposal(
            event_mean_source,
            candidate_manifest(state_feature_names),
            "Event-equal expanding historical normalized-duration mean.",
            (),
        ),
        session_id=session_id,
        episode_id=episode_id,
        idempotency_key="duration-exact-plan:baseline",
    )
    if baseline_runtime.trial_id is None or baseline_runtime.evidence_id is None:
        raise ValueError("exact-plan baseline did not issue evidence")
    state_runtime = coordinator.execute(
        registration.registration_id,
        AuthoredProgramProposal(
            state_source,
            candidate_manifest(state_feature_names),
            "Fixed-penalty event-equal ridge over exact probability state.",
            (baseline_runtime.trial_id,),
        ),
        session_id=session_id,
        episode_id=episode_id,
        idempotency_key="duration-exact-plan:state",
    )
    if state_runtime.trial_id is None or state_runtime.evidence_id is None:
        raise ValueError("exact-plan state comparator did not issue evidence")
    staleness_runtime = coordinator.execute(
        registration.registration_id,
        AuthoredProgramProposal(
            staleness_source,
            candidate_manifest(staleness_feature_names),
            "Selected five-feature state-staleness ridge with fixed event weights and penalty.",
            (state_runtime.trial_id,),
        ),
        session_id=session_id,
        episode_id=episode_id,
        idempotency_key="duration-exact-plan:state-staleness",
    )
    if staleness_runtime.candidate_id is None or staleness_runtime.evidence_id is None:
        raise ValueError("exact-plan candidate did not issue evidence")
    if (
        staleness_runtime.candidate_id != EXPECTED_CANDIDATE_ID
        or staleness_runtime.evidence_id != EXPECTED_EVIDENCE_ID
    ):
        raise ValueError("exact-plan replay changed the selected candidate or development evidence")
    baseline_evidence = coordinator.resolve_evidence(baseline_runtime.evidence_id)
    state_evidence = coordinator.resolve_evidence(state_runtime.evidence_id)
    staleness_evidence = coordinator.resolve_evidence(staleness_runtime.evidence_id)
    baseline_summary = duration_metrics(baseline_evidence)
    state_summary = duration_metrics(state_evidence, baseline_evidence)
    staleness_summary = duration_metrics(staleness_evidence, state_evidence)
    if float(staleness_summary["observation_mse"]) > 0.15:
        raise ValueError("exact-plan replay failed the fixed formal development ceiling")

    clock_time = max(item.available_at for item in full_catalog.observations) + timedelta(seconds=1)
    ledger = ResearchLedger()
    eligibility = FreezeEligibilityRegistry()
    frozen_systems = FrozenSystemRegistry()
    freeze = AuthoredFreezeService(
        authority_id="authority:independent-polymarket-duration-freeze-v2",
        investigations=coordinator,
        eligibility=eligibility,
        gate=FreezeGate(
            ledger=ledger,
            registry=frozen_systems,
            eligibility=eligibility,
            decision_authority_id="authority:independent-polymarket-duration-freeze-v2",
            clock=lambda: clock_time,
        ),
    ).assess_credible(
        candidate_id=staleness_runtime.candidate_id,
        evidence_id=staleness_runtime.evidence_id,
        requester_id=session_id,
        beneficiary_id=question.task_ref,
    )
    if freeze.frozen is None:
        raise ValueError("exact-plan candidate was not frozen")

    exposures = ExposureRegistry()
    permits = PermitRegistry()
    governance_grant = PermissionGrant(
        session_id,
        "authority:independent-polymarket-duration-governance",
        frozenset((plan.protected_scope.scope_id,)),
        plan.protected_scope.policy_ref,
        development_catalog.environment_id,
    )
    validation_grant = ValidationAuthorityGrant(
        "authority:independent-polymarket-duration-validation",
        plan.promotion_standard.authority_policy_ref,
        development_catalog.environment_id,
    )
    authorities = WorkflowAuthorityRegistry(
        governance_permissions=(governance_grant,),
        validation_grants=(validation_grant,),
    )
    governance = BacktestGovernance(
        ledger=ledger,
        frozen_systems=frozen_systems,
        exposures=exposures,
        permits=permits,
        permissions=(governance_grant,),
        current_environment_ref=development_catalog.environment_id,
        current_policy_ref=plan.protected_scope.policy_ref,
        clock=lambda: clock_time,
    )
    binder = ProtectedViewBinder(
        permits=permits,
        clock=lambda: clock_time,
        current_environment_ref=development_catalog.environment_id,
        current_policy_ref=plan.protected_scope.policy_ref,
    )
    recorder = ExposureRecorder(registry=exposures, ledger=ledger, clock=lambda: clock_time)
    engine = AuthoredBacktestEngine(
        investigations=coordinator,
        plans=plan_registry,
        permits=permits,
        frozen_systems=frozen_systems,
        views=binder,
        exposures=recorder,
        ledger=ledger,
        clock=lambda: clock_time,
    )
    evaluator = Evaluator(ledger=ledger, runs=engine.issued_runs, clock=lambda: clock_time)
    negatives = NegativeResultRegistry()
    validator = Validator(
        authorized_authority_ids=frozenset((validation_grant.authority_id,)),
        authority_policy_ref=validation_grant.authority_policy_ref,
        ledger=ledger,
        reports=evaluator.issued_reports,
        negatives=negatives,
        clock=lambda: clock_time,
    )
    publisher = FindingPublisher(
        ledger=ledger,
        reports=evaluator.issued_reports,
        decisions=validator.issued_decisions,
        clock=lambda: clock_time,
    )
    resolution_service = AuthoredProtectedResolutionService(
        investigations=coordinator,
        frozen_systems=frozen_systems,
        plans=plan_registry,
        authorities=authorities,
        protected_resources=resource_registry,
        governance=governance,
        views=binder,
        engine=engine,
        evaluator=evaluator,
        validator=validator,
        publisher=publisher,
        negatives=negatives,
    )
    resolution = resolution_service.resolve(
        candidate_id=staleness_runtime.candidate_id,
        evidence_id=staleness_runtime.evidence_id,
        frozen_system_id=freeze.frozen.frozen_system_id,
        requester_id=session_id,
        beneficiary_id=question.task_ref,
        recipient_id="researcher:chronos-polymarket-duration",
        idempotency_key="polymarket-duration-protected-resolution-v1",
    )
    if resolution.run_id is None or resolution.report_id is None:
        raise ValueError("authorized protected resolution did not produce a sealed report")
    run = engine.issued_runs.get(resolution.run_id)
    if run is None:
        raise ValueError("protected resolution referenced an unissued run")
    report = evaluator.measure(run, plan.evaluation_spec)
    if report.report_id != resolution.report_id:
        raise ValueError("protected report replay changed identity")
    exposure_records = exposures.records()
    if len(exposure_records) != 1 or report.exposure_ref != exposure_records[0].exposure_id:
        raise ValueError("protected resolution did not retain exactly one exposure")

    payload = {
        "status": "succeeded",
        "epistemic_status": resolution.status.value.upper(),
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "snapshot_ref": ref.uri,
        "partition_id": analysis.partition.partition_id,
        "development_event_count": len(development_events),
        "protected_event_count": len(protected_events),
        "development_market_count": len(development_markets),
        "protected_market_count": len(protected_markets),
        "development_key_count": len(development_keys),
        "protected_decision_count": len(protected_keys),
        "training_candidate_key_count": len(all_keys),
        "resource_registration_id": resource_registration.registration_id,
        "protected_plan": {
            "plan_id": plan.plan_id,
            "scenario_id": plan.scenario.identity,
            "decision_times_ref": plan.scenario.decision_times_ref,
            "evaluation_spec_id": plan.evaluation_spec.identity,
            "promotion_standard_id": plan.promotion_standard.identity,
            "protected_scope_id": plan.protected_scope.scope_id,
            "claim_template_ref": plan.claim_template_ref,
            "criteria": [
                {
                    "metric": item.metric.value,
                    "comparison": item.comparison.value,
                    "threshold": item.threshold,
                }
                for item in plan.promotion_standard.criteria
            ],
            "maximum_stability_stddev": plan.promotion_standard.maximum_stability_stddev,
            "maximum_error_concentration": plan.promotion_standard.maximum_error_concentration,
        },
        "exact_development_identity_match": True,
        "development": {
            "candidate_id": staleness_runtime.candidate_id,
            "evidence_id": staleness_runtime.evidence_id,
            "trial_id": staleness_runtime.trial_id,
            "baseline": baseline_summary,
            "state": state_summary,
            "state_staleness": staleness_summary,
        },
        "freeze": {
            "request_id": freeze.request.request_id,
            "decision_id": freeze.decision.decision_id,
            "frozen_system_id": freeze.frozen.frozen_system_id,
            "protocol_refs": list(freeze.frozen.protocol_refs),
            "authority_id": freeze.frozen.freeze_authority_id,
        },
        "resolution": {
            "resolution_id": resolution.resolution_id,
            "status": resolution.status.value,
            "request_id": resolution.request_id,
            "permit_or_denial_id": resolution.permit_or_denial_id,
            "view_id": resolution.view_id,
            "run_id": resolution.run_id,
            "report_id": resolution.report_id,
            "validation_decision_id": resolution.validation_decision_id,
            "finding_id": resolution.finding_id,
            "negative_result_id": resolution.negative_result_id,
            "reason_codes": list(resolution.reason_codes),
        },
        "exposure": {
            "exposure_id": exposure_records[0].exposure_id,
            "exposure_period_id": exposure_records[0].exposure_period_id,
            "disclosure_status": exposure_records[0].disclosure_status,
            "recipient_id": exposure_records[0].recipient_id,
            "disclosed_at": exposure_records[0].disclosed_at.isoformat(),
        },
        "run": {
            "run_id": run.run_id,
            "status": run.status.value,
            "decision_count": len(run.decisions),
            "failure_count": len(run.failures),
        },
        "report": {
            "report_id": report.report_id,
            "execution_valid": report.execution_valid,
            "metrics": [_metric_json(item) for item in report.metrics],
            "failures": [{"code": item.code, "count": item.count} for item in report.failures],
            "stability": {
                "absolute_error_stddev": report.stability.absolute_error_stddev,
                "rolling_mse": list(report.stability.rolling_mse),
            },
            "concentration": {
                "maximum_squared_error_share": report.concentration.maximum_squared_error_share,
                "worst_decision_time": (
                    report.concentration.worst_decision_time.isoformat()
                    if report.concentration.worst_decision_time is not None
                    else None
                ),
            },
            "per_time": [
                {
                    "decision_time": item.decision_time.isoformat(),
                    "dimensions": [list(value) for value in item.dimensions],
                    "prediction": item.prediction,
                    "outcome": item.outcome,
                    "absolute_error": item.absolute_error,
                    "squared_error": item.squared_error,
                }
                for item in report.per_time
            ],
            "per_dimension": [
                {
                    "dimensions": [list(value) for value in item.dimensions],
                    "sample_size": item.sample_size,
                    "mae": item.mae,
                    "mse": item.mse,
                }
                for item in report.per_dimension
            ],
            "caveats": list(report.caveats),
        },
        "ledger_entries": [
            {
                "entry_id": item.entry_id,
                "event_type": item.event_type,
                "subject_id": item.subject_id,
                "status": item.status,
                "authority_id": item.authority_id,
                "references": list(item.references),
                "reason_code": item.reason_code,
                "occurred_at": item.occurred_at.isoformat(),
            }
            for item in ledger.entries()
        ],
        "warnings": [
            "This is one irreversibly exposed historical holdout, not reusable development data.",
            "Sampled first passage is not continuous-time first passage or executable-price evidence.",
            "The claim does not establish direction, execution, profitability, or causality.",
        ],
    }
    content = json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n"
    if RECEIPT.exists() and RECEIPT.read_text() != content:
        raise ValueError("protected receipt path already contains different bytes")
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(content)
    print(
        json.dumps(
            {
                "status": "SUCCEEDED",
                "resolution_status": resolution.status.value,
                "frozen_system_id": freeze.frozen.frozen_system_id,
                "protected_decision_count": len(protected_keys),
                "metrics": {item.name.value: item.value for item in report.metrics},
                "receipt": str(RECEIPT),
                "receipt_sha256": hashlib.sha256(content.encode()).hexdigest(),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
