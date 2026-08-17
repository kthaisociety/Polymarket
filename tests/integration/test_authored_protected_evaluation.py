"""Application proof that frozen authored source reaches protected execution unchanged."""

# ruff: noqa: D103, EM101, PLR0915, PLR2004, TRY003

from __future__ import annotations

import copy
import json
import sqlite3
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from research_agent.data_foundation import (
    DataCatalogSnapshot,
    DatasetSchema,
    FieldDefinition,
    FieldRef,
    MissingnessPolicy,
    ObservationInput,
    ObservationRegistrar,
    SampleKey,
    TemporalOffset,
    TrainingWindowPolicy,
    WindowKind,
)
from research_agent.data_foundation._identity import stable_identity
from research_agent.investigation import (
    AuthoredBacktestEngine,
    AuthoredCandidateManifest,
    AuthoredFreezeService,
    AuthoredProgramProposal,
    AuthoredProtectedPlan,
    AuthoredProtectedResolutionService,
    AuthoredResolutionStatus,
    DevelopmentBudget,
    DevelopmentDisposition,
    DurableQuestionMemoryArchive,
    InvestigationRequest,
    ProtectedEvaluationPredeclaration,
    QuestionAlreadyResolvedError,
    QuestionMemoryPersistenceError,
    QuestionMemoryStatus,
    QuestionReopenDeclaration,
    QuestionReopenReason,
    ResearchQuestion,
    RuntimeInvestigationCoordinator,
    configure_authored_protected_plan_authority,
    configure_validated_question_memory,
)
from research_agent.protected_evaluation import (
    AuthorizedProtectedDataView,
    BacktestGovernance,
    BacktestPermit,
    BacktestRequest,
    BacktestRunStatus,
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
    LoadedProtectedCatalog,
    MetricCriterion,
    MetricName,
    NegativeResultRegistry,
    PermissionGrant,
    PermitRegistry,
    PromotionStandard,
    ProtectedContentManifest,
    ProtectedExecutionMismatchError,
    ProtectedExposureStatus,
    ProtectedResourceScope,
    ProtectedViewBinder,
    ResearchLedger,
    ScenarioKind,
    Validator,
)
from research_agent.runtime.capabilities import ActionRouter, DatasetRepository
from research_agent.runtime.commit import CommitCoordinator
from research_agent.runtime.context import ContextBuilder
from research_agent.runtime.engine import AutonomousResearchRuntime
from research_agent.runtime.initialization import ResearchRuntimeInitializer
from research_agent.runtime.models import (
    ContextPacket,
    ObservationStatus,
    ResearchEnvironmentSnapshot,
)
from research_agent.runtime.provider import ModelResponse
from research_agent.runtime.store import InMemoryRuntimeStore
from research_agent.scientific_workflow import (
    ValidationAuthorityGrant,
    WorkflowAuthorityRegistry,
    configure_protected_resource_authority,
)
from research_agent.task_compilation import (
    ResearchEnvironmentSummary,
    TaskCompiler,
    TaskConfirmation,
    TaskPublisher,
    UserMandate,
)

DAY = timedelta(days=1)
ORIGIN = datetime(2025, 1, 1, tzinfo=UTC)
ENVIRONMENT = "authored-protected-world"
SESSION = "session:authored-researcher"
EPISODE = "episode:authored-researcher"
TASK = "task:authored-researcher"


class _OneAuthoredTrialProvider:
    """Packet-only intelligence fixture; scientific authority remains outside the provider."""

    def __init__(self, investigation_id: str, proposal: AuthoredProgramProposal) -> None:
        self._investigation_id = investigation_id
        self._proposal = proposal

    def complete(self, packet: ContextPacket) -> ModelResponse:
        action: dict[str, object] = {
            "kind": "run_authored_development_trial",
            "action_id": "action:authored-full-application",
            "session_id": packet.session_id,
            "episode_id": packet.episode_id,
            "arguments": {
                "investigation_id": self._investigation_id,
                "source": self._proposal.source,
                "manifest": _manifest_json(self._proposal.manifest),
                "rationale": self._proposal.rationale,
                "parent_trial_ids": list(self._proposal.parent_trial_ids),
                "idempotency_key": "authored-full-application",
            },
        }
        return ModelResponse(
            message="Test the authored interaction under the declared budget.",
            action=action,
            provider_metadata={"fixture": "packet-only"},
        )


def _clock() -> datetime:
    return ORIGIN + DAY * 100


def _schema() -> DatasetSchema:
    return DatasetSchema(
        dataset_id="authored-interaction",
        version="v1",
        environment_id=ENVIRONMENT,
        provenance_ref="fixture:authored-interaction-schema",
        fields=(
            FieldDefinition("x1", "Signal one", "float", "index", ("market_id",), "First input."),
            FieldDefinition("x2", "Signal two", "float", "index", ("market_id",), "Second input."),
            FieldDefinition(
                "future_poison",
                "Future poison",
                "float",
                "index",
                ("market_id",),
                "Released only after every protected decision.",
            ),
            FieldDefinition(
                "y", "Next outcome", "float", "units", ("market_id",), "One-day outcome."
            ),
        ),
    )


def _row(
    schema: DatasetSchema,
    field_id: str,
    value: float,
    timing: tuple[int, int],
    market_id: str,
) -> ObservationInput:
    reference_day, available_day = timing
    return ObservationInput(
        schema.field_ref(field_id),
        value,
        ORIGIN + DAY * reference_day,
        ORIGIN + DAY * available_day,
        "initial",
        0,
        "fixture:authored-protected",
        f"fixture:{field_id}:{reference_day}:{value}",
        "fixture-release-v1",
        (("market_id", market_id),),
    )


def _catalog(start: int, stop: int, *, poison_value: float = 999_999.0) -> DataCatalogSnapshot:
    schema = _schema()
    market_id = "protected-market" if start >= 25 else "development-market"
    rows: list[ObservationInput] = []
    for day in range(start, stop):
        left = -1.0 if day % 2 else 1.0
        right = -1.0 if day % 4 < 2 else 1.0
        label = 3.0 * left * right
        rows.extend(
            (
                _row(schema, "x1", left, (day, day), market_id),
                _row(schema, "x2", right, (day, day), market_id),
                _row(
                    schema,
                    "future_poison",
                    poison_value,
                    (day, 90),
                    market_id,
                ),
                _row(schema, "y", label, (day + 1, day + 1), market_id),
            )
        )
    registration = ObservationRegistrar().register(schema, tuple(rows))
    return DataCatalogSnapshot(ENVIRONMENT, (registration,))


def _proposal(catalog: DataCatalogSnapshot) -> AuthoredProgramProposal:
    schema = catalog.datasets[0].schema
    source = """
def make_features():
    left = history("x1")
    right = history("x2")
    return {"interaction": left[-1]["value"] * right[-1]["value"]}

def make_label():
    current = history("x1")[-1]["value"]
    return outcome_path()[-1]["value"] + 0.0 * current

def fit():
    rows = training_rows()
    numerator = sum(row["features"]["interaction"] * row["label"] for row in rows)
    denominator = sum(row["features"]["interaction"] ** 2 for row in rows)
    return {"slope": numerator / denominator}

def predict():
    return model_state()["slope"] * feature_values()["interaction"]
"""
    return AuthoredProgramProposal(
        source=source,
        manifest=AuthoredCandidateManifest(
            question_id="question:authored-interaction",
            environment_id=ENVIRONMENT,
            predictor_fields=(schema.field_ref("x1"), schema.field_ref("x2")),
            outcome_field=schema.field_ref("y"),
            horizon=TemporalOffset.elapsed(DAY),
            minimum_outcome_points=1,
            population_dimensions=(),
            feature_names=("interaction",),
            missing_value_policy="exclude_example",
            evidence_refs=("exploration:interaction-hypothesis",),
            provenance_refs=("researcher:authored-program",),
            population_dimension_names=("market_id",),
        ),
        rationale="Test a researcher-invented nonlinear interaction.",
        parent_trial_ids=(),
    )


def _manifest(catalog: DataCatalogSnapshot) -> ProtectedContentManifest:
    content = catalog.identity.encode()
    return ProtectedContentManifest.create(
        content_digest=sha256(content).hexdigest(),
        byte_length=len(content),
        catalog_id=catalog.identity,
        provenance_ref="fixture:protected-authored-catalog",
    )


def _plan(
    catalog: DataCatalogSnapshot,
    *,
    promotion_mse_threshold: float = 1e-12,
) -> AuthoredProtectedPlan:
    manifest = _manifest(catalog)
    dimensions = catalog.observations[0].dimensions
    scope = ProtectedResourceScope(
        resource_id="protected-authored-catalog",
        resource_version="v1",
        slice_id="holdout-2025",
        environment_ref=ENVIRONMENT,
        policy_ref="policy:authored-protected-v1",
        content_manifest_id=manifest.manifest_id,
        content_identity_id=manifest.content_identity_id,
        epistemic_period_ref="period:authored-holdout-2025",
        exposure_status=ProtectedExposureStatus.UNSEEN,
    )
    scenario = EvaluationScenario(
        name="authored protected walk-forward",
        version=1,
        kind=ScenarioKind.HISTORICAL_WALK_FORWARD,
        decision_sample_keys=tuple(
            SampleKey(ORIGIN + DAY * day, dimensions) for day in range(36, 45)
        ),
        training_candidate_keys=tuple(
            SampleKey(ORIGIN + DAY * day, dimensions) for day in range(25, 44)
        ),
        outcome_recorded_at=ORIGIN + DAY * 55,
        training_protocol_ref="protocol:authored-expanding-v1",
        window_policy=TrainingWindowPolicy(
            1,
            WindowKind.EXPANDING,
            6,
            None,
            "protocol:authored-expanding-v1",
        ),
        missingness_policy=MissingnessPolicy.EXCLUDE_EXAMPLE,
        interpretation="one untouched authored-program historical holdout",
        environment_ref=ENVIRONMENT,
        data_protocol_ref="protocol:authored-data-v1",
        provenance_refs=("scenario:authored-protected-v1",),
    )
    specification = EvaluationSpec(
        name="authored forecast quality",
        version=1,
        protocol_ref="protocol:authored-evaluation-v1",
        metric_names=(MetricName.MSE, MetricName.COVERAGE, MetricName.FAILURE_RATE),
        rolling_window=3,
        include_per_time=True,
        include_dimension_views=True,
        include_stability=True,
        include_concentration=True,
        benchmark_refs=(),
        provenance_refs=("evaluation:authored-predeclared",),
    )
    standard = PromotionStandard(
        name="authored forecast standard",
        version=1,
        evaluation_spec_id=specification.identity,
        criteria=(
            MetricCriterion(
                MetricName.MSE,
                CriterionComparison.LESS_THAN_OR_EQUAL,
                promotion_mse_threshold,
            ),
            MetricCriterion(MetricName.COVERAGE, CriterionComparison.GREATER_THAN_OR_EQUAL, 1.0),
            MetricCriterion(
                MetricName.FAILURE_RATE,
                CriterionComparison.LESS_THAN_OR_EQUAL,
                0.0,
            ),
        ),
        maximum_stability_stddev=1e-12,
        maximum_error_concentration=1.0,
        required_scenario_kind=ScenarioKind.HISTORICAL_WALK_FORWARD,
        authority_policy_ref="validation-policy:authored-v1",
        provenance_refs=("validation:authored-predeclared",),
    )
    return AuthoredProtectedPlan.create(
        scenario=scenario,
        evaluation_spec=specification,
        promotion_standard=standard,
        protected_scope=scope,
        claim_name="authored interaction claim",
        claim_version=1,
        claim_statement="The exact frozen authored program met its predeclared holdout standard.",
        claim_scope_limitations=("This claim applies only to the declared synthetic holdout.",),
        claim_required_caveats=("No causal interpretation is claimed.",),
        claim_provenance_refs=("claim-template:authored-v1",),
    )


def _request(
    catalog: DataCatalogSnapshot,
    plan: AuthoredProtectedPlan,
    *,
    task_ref: str = TASK,
    reopen: QuestionReopenDeclaration | None = None,
) -> InvestigationRequest:
    dimensions = catalog.observations[0].dimensions
    return InvestigationRequest(
        question=ResearchQuestion(
            "question:authored-interaction",
            "Can a researcher-authored interaction predict the next value?",
            ENVIRONMENT,
            task_ref,
            ("observation:research-question",),
        ),
        catalog=catalog,
        sample_keys=tuple(SampleKey(ORIGIN + DAY * day, dimensions) for day in range(2, 24)),
        current_time=ORIGIN + DAY * 30,
        budget=DevelopmentBudget(1, 6, 8, "mse", 1e-12),
        random_seed=17,
        protected_predeclaration=ProtectedEvaluationPredeclaration(
            data_protocol_ref=plan.scenario.data_protocol_ref,
            training_protocol_ref=plan.scenario.training_protocol_ref,
            scenario_ref=plan.scenario.identity,
            decision_times_ref=plan.scenario.decision_times_ref,
            evaluation_spec_ref=plan.evaluation_spec.identity,
            validation_standard_ref=plan.promotion_standard.identity,
            protected_scope_id=plan.protected_scope.scope_id,
            claim_template_ref=plan.claim_template_ref,
            freeze_standard_ref="freeze-standard:authored-v1",
        ),
        reopen=reopen,
    )


def _manifest_json(manifest: AuthoredCandidateManifest) -> dict[str, object]:
    return {
        "question_id": manifest.question_id,
        "environment_id": manifest.environment_id,
        "predictor_fields": [_field_json(item) for item in manifest.predictor_fields],
        "outcome_field": _field_json(manifest.outcome_field),
        "horizon": {
            "kind": "elapsed",
            "elapsed_microseconds": manifest.horizon.elapsed_microseconds,
        },
        "minimum_outcome_points": manifest.minimum_outcome_points,
        "population_dimensions": [list(item) for item in manifest.population_dimensions],
        "population_dimension_names": list(manifest.population_dimension_names),
        "feature_names": list(manifest.feature_names),
        "missing_value_policy": manifest.missing_value_policy,
        "evidence_refs": list(manifest.evidence_refs),
        "provenance_refs": list(manifest.provenance_refs),
    }


def _field_json(field: FieldRef) -> dict[str, object]:
    return {
        "dataset_id": field.dataset_id,
        "schema_version": field.schema_version,
        "field_id": field.field_id,
        "environment_id": field.environment_id,
    }


@pytest.mark.parametrize(
    ("promotion_mse_threshold", "expected_status"),
    [
        (1e-12, AuthoredResolutionStatus.FINDING),
        (-1.0, AuthoredResolutionStatus.REJECTED),
    ],
)
def test_exact_frozen_authored_source_executes_through_protected_walk_forward(
    promotion_mse_threshold: float,
    expected_status: AuthoredResolutionStatus,
    tmp_path: Path,
) -> None:
    development_catalog = _catalog(1, 25)
    protected_catalog = _catalog(25, 51)
    plan = _plan(
        protected_catalog,
        promotion_mse_threshold=promotion_mse_threshold,
    )
    plan_registry, plan_issuer = configure_authored_protected_plan_authority(
        "authority:protected-plan"
    )
    with pytest.raises(TypeError, match="plan issuer cannot be copied"):
        copy.copy(plan_issuer)
    plan_issuer.issue(plan)
    fail_markdown = [True]

    def controlled_markdown_write(path: Path, content: str) -> None:
        if fail_markdown[0]:
            raise OSError("injected Markdown projection failure")
        path.write_text(content, encoding="utf-8", newline="\n")

    archive = DurableQuestionMemoryArchive(
        tmp_path / "validated-question-memory",
        markdown_writer=controlled_markdown_write,
    )
    with pytest.raises(TypeError, match="archive cannot be copied"):
        copy.copy(archive)
    question_memory, memory_issuer = configure_validated_question_memory(archive)
    with pytest.raises(TypeError, match="memory authority cannot be copied"):
        copy.copy(question_memory)
    coordinator = RuntimeInvestigationCoordinator(question_memory=question_memory)
    registration = coordinator.register(
        _request(development_catalog, plan),
        session_id=SESSION,
        episode_id=EPISODE,
    )
    receipt = coordinator.execute(
        registration.registration_id,
        _proposal(development_catalog),
        session_id=SESSION,
        episode_id=EPISODE,
        idempotency_key="develop-authored-candidate",
    )
    assert receipt.disposition is DevelopmentDisposition.CREDIBLE
    assert receipt.candidate_id is not None
    assert receipt.evidence_id is not None

    ledger = ResearchLedger()
    eligibility = FreezeEligibilityRegistry()
    frozen_systems = FrozenSystemRegistry()
    freeze = AuthoredFreezeService(
        authority_id="authority:freeze",
        investigations=coordinator,
        eligibility=eligibility,
        gate=FreezeGate(
            ledger=ledger,
            registry=frozen_systems,
            eligibility=eligibility,
            decision_authority_id="authority:freeze",
            clock=_clock,
        ),
    ).assess_credible(
        candidate_id=receipt.candidate_id,
        evidence_id=receipt.evidence_id,
        requester_id=SESSION,
        beneficiary_id=TASK,
    )
    assert freeze.frozen is not None
    candidate = coordinator.resolve_candidate(receipt.candidate_id)
    claim = plan.claim_for(candidate)
    request = BacktestRequest(
        frozen_system_id=freeze.frozen.frozen_system_id,
        system_id=candidate.candidate_id,
        scenario_ref=plan.scenario.identity,
        decision_times_ref=plan.scenario.decision_times_ref,
        training_protocol_ref=plan.scenario.training_protocol_ref,
        evaluation_spec_ref=plan.evaluation_spec.identity,
        validation_standard_ref=plan.promotion_standard.identity,
        claim_ref=claim.identity,
        protected_scope=plan.protected_scope,
        environment_ref=ENVIRONMENT,
        ancestry_refs=freeze.frozen.ancestry_refs,
        prior_exposure_refs=(),
        requester_id=SESSION,
        beneficiary_id=TASK,
        idempotency_key="protected-authored-run",
    )
    exposures = ExposureRegistry()
    permits = PermitRegistry()
    governance_grant = PermissionGrant(
        SESSION,
        "authority:governance",
        frozenset((plan.protected_scope.scope_id,)),
        plan.protected_scope.policy_ref,
        ENVIRONMENT,
    )
    validation_grant = ValidationAuthorityGrant(
        "authority:validation",
        plan.promotion_standard.authority_policy_ref,
        ENVIRONMENT,
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
        current_environment_ref=ENVIRONMENT,
        current_policy_ref=plan.protected_scope.policy_ref,
        clock=_clock,
    )
    permit = governance.authorize(request, authority_id="authority:governance")
    assert isinstance(permit, BacktestPermit)
    binder = ProtectedViewBinder(
        permits=permits,
        clock=_clock,
        current_environment_ref=ENVIRONMENT,
        current_policy_ref=plan.protected_scope.policy_ref,
    )
    view = binder.bind(
        permit=permit,
        request=request,
        requested_scope=plan.protected_scope,
        caller_id=SESSION,
        resolve_exact_resource=lambda _: "binding:authored-protected-v1",
    )
    assert isinstance(view, AuthorizedProtectedDataView)
    recorder = ExposureRecorder(registry=exposures, ledger=ledger, clock=_clock)
    engine = AuthoredBacktestEngine(
        investigations=coordinator,
        plans=plan_registry,
        permits=permits,
        frozen_systems=frozen_systems,
        views=binder,
        exposures=recorder,
        ledger=ledger,
        clock=_clock,
    )
    with pytest.raises(TypeError, match="execution authority cannot be copied"):
        copy.copy(engine)
    load_calls: list[str] = []

    def load(binding: str) -> LoadedProtectedCatalog:
        load_calls.append(binding)
        return LoadedProtectedCatalog(_manifest(protected_catalog), protected_catalog)

    forged_frozen = replace(freeze.frozen, candidate_version="0" * 64)
    with pytest.raises(ProtectedExecutionMismatchError, match="required authorities"):
        engine.execute(
            request=request,
            permit=permit,
            view=view,
            frozen=forged_frozen,
            plan=plan,
            recipient_id="researcher:protected",
            load_protected_catalog=load,
        )
    forged_plan = replace(
        plan,
        plan_id=AuthoredProtectedPlan.create(
            scenario=plan.scenario,
            evaluation_spec=plan.evaluation_spec,
            promotion_standard=plan.promotion_standard,
            protected_scope=plan.protected_scope,
            claim_name=plan.claim_name,
            claim_version=plan.claim_version,
            claim_statement="A caller-selected post-development claim.",
            claim_scope_limitations=plan.claim_scope_limitations,
            claim_required_caveats=plan.claim_required_caveats,
            claim_provenance_refs=plan.claim_provenance_refs,
        ).plan_id,
        claim_statement="A caller-selected post-development claim.",
    )
    with pytest.raises(ProtectedExecutionMismatchError, match="required authorities"):
        engine.execute(
            request=request,
            permit=permit,
            view=view,
            frozen=freeze.frozen,
            plan=forged_plan,
            recipient_id="researcher:protected",
            load_protected_catalog=load,
        )
    assert load_calls == []
    assert exposures.records() == ()

    protected_resources, protected_issuer = configure_protected_resource_authority(
        "authority:protected-resource"
    )
    protected_issuer.issue(
        scope=plan.protected_scope,
        resource_binding_ref="binding:authored-protected-v1",
        content_manifest=_manifest(protected_catalog),
        catalog=protected_catalog,
    )
    evaluator = Evaluator(ledger=ledger, runs=engine.issued_runs, clock=_clock)
    negatives = NegativeResultRegistry()
    validator = Validator(
        authorized_authority_ids=frozenset((validation_grant.authority_id,)),
        authority_policy_ref=validation_grant.authority_policy_ref,
        ledger=ledger,
        reports=evaluator.issued_reports,
        negatives=negatives,
        clock=_clock,
    )
    publisher = FindingPublisher(
        ledger=ledger,
        reports=evaluator.issued_reports,
        decisions=validator.issued_decisions,
        clock=_clock,
    )
    resolution_service = AuthoredProtectedResolutionService(
        investigations=coordinator,
        frozen_systems=frozen_systems,
        plans=plan_registry,
        authorities=authorities,
        protected_resources=protected_resources,
        governance=governance,
        views=binder,
        engine=engine,
        evaluator=evaluator,
        validator=validator,
        publisher=publisher,
        negatives=negatives,
    )
    with pytest.raises(TypeError, match="resolution authority cannot be copied"):
        copy.copy(resolution_service)
    resolution = resolution_service.resolve(
        candidate_id=candidate.candidate_id,
        evidence_id=receipt.evidence_id,
        frozen_system_id=freeze.frozen.frozen_system_id,
        requester_id=SESSION,
        beneficiary_id=TASK,
        recipient_id="researcher:protected",
        idempotency_key="protected-authored-run",
    )
    assert resolution.status is expected_status
    if expected_status is AuthoredResolutionStatus.FINDING:
        assert resolution.finding_id is not None
        assert resolution.negative_result_id is None
    else:
        assert resolution.finding_id is None
        assert resolution.negative_result_id is not None
        assert len(negatives.records()) == 1
    assert resolution.run_id is not None
    run = engine.issued_runs.get(resolution.run_id)
    assert run is not None

    assert run.status is BacktestRunStatus.COMPLETED
    assert run.system_id == candidate.candidate_id
    assert run.frozen_system_id == freeze.frozen.frozen_system_id
    assert run.exposure_id == exposures.records()[0].exposure_id
    assert load_calls == []
    assert all(decision.fit is not None for decision in run.decisions)
    assert all(decision.prediction is not None for decision in run.decisions)
    assert all(decision.outcome is not None for decision in run.decisions)
    development_evidence = coordinator.resolve_evidence(receipt.evidence_id)
    assert {dict(key.dimensions)["market_id"] for key in development_evidence.row_keys} == {
        "development-market"
    }
    assert {dict(decision.dimensions)["market_id"] for decision in run.decisions} == {
        "protected-market"
    }
    assert tuple(
        decision.prediction.value for decision in run.decisions if decision.prediction
    ) == tuple(decision.outcome.value for decision in run.decisions if decision.outcome)
    poison_ids = {
        item.observation_id
        for item in protected_catalog.observations
        if item.field_ref.field_id == "future_poison"
    }
    assert all(
        poison_ids.isdisjoint(decision.information_observation_ids) for decision in run.decisions
    )
    report = evaluator.measure(run, plan.evaluation_spec)
    assert report.metric(MetricName.MSE).value == 0.0
    assert report.metric(MetricName.COVERAGE).value == 1.0
    assert report.metric(MetricName.FAILURE_RATE).value == 0.0

    replay = resolution_service.resolve(
        candidate_id=candidate.candidate_id,
        evidence_id=receipt.evidence_id,
        frozen_system_id=freeze.frozen.frozen_system_id,
        requester_id=SESSION,
        beneficiary_id=TASK,
        recipient_id="researcher:protected",
        idempotency_key="protected-authored-run",
    )
    assert replay is resolution
    assert len(exposures.records()) == 1
    assert load_calls == []

    memory_now = [_clock()]
    memory_recorder = memory_issuer.bind(
        investigations=coordinator,
        resolutions=resolution_service,
        clock=lambda: memory_now[0],
    )
    with pytest.raises(TypeError, match="memory recorder authority cannot be copied"):
        copy.copy(memory_recorder)
    with pytest.raises(QuestionMemoryPersistenceError, match="publication failed"):
        memory_recorder.record(resolution)
    assert len(question_memory.records()) == 1
    assert archive.load() == question_memory.records()
    fail_markdown[0] = False
    memory_record = memory_recorder.record(resolution)
    expected_memory_status = (
        QuestionMemoryStatus.VALIDATED_FINDING
        if expected_status is AuthoredResolutionStatus.FINDING
        else QuestionMemoryStatus.PROTECTED_REJECTION
    )
    assert memory_record.status is expected_memory_status
    assert memory_record.protected_resolution_id == resolution.resolution_id
    assert memory_record.terminal_evidence_ref in resolution.evidence_refs
    forged_reason_codes = (*resolution.reason_codes, "caller:favorable-interpretation")
    forged_payload = {
        name: getattr(resolution, name)
        for name in resolution.__dataclass_fields__
        if name != "resolution_id"
    }
    forged_payload["reason_codes"] = forged_reason_codes
    forged_resolution = replace(
        resolution,
        resolution_id=stable_identity("authored-protected-resolution", forged_payload),
        reason_codes=forged_reason_codes,
    )
    with pytest.raises(ValueError, match="not issued"):
        memory_recorder.record(forged_resolution)
    memory_now[0] += DAY
    assert memory_recorder.record(resolution) is memory_record
    assert memory_record.resolved_at == _clock()
    assert question_memory.records() == (memory_record,)
    with pytest.raises(QuestionMemoryPersistenceError, match="not authority-issued"):
        archive.append_issued(memory_record, capability=object())
    with pytest.raises(QuestionMemoryPersistenceError, match="already bound"):
        archive.bind_authority(object())
    report_path = archive.markdown_directory / f"{memory_record.memory_id}.md"
    assert archive.database_path.is_file()
    assert archive.index_path.is_file()
    assert report_path.is_file()
    assert "```mermaid" in archive.index_path.read_text(encoding="utf-8")
    assert memory_record.question_text in report_path.read_text(encoding="utf-8")
    report_path.write_text("caller-authored promotion", encoding="utf-8")
    archive.refresh_markdown()
    assert "caller-authored promotion" not in report_path.read_text(encoding="utf-8")

    reloaded_archive = DurableQuestionMemoryArchive(tmp_path / "validated-question-memory")
    reloaded_memory, _ = configure_validated_question_memory(reloaded_archive)
    assert reloaded_memory.records() == (memory_record,)

    with pytest.raises(QuestionAlreadyResolvedError, match="already resolved"):
        coordinator.register(
            _request(development_catalog, plan),
            session_id="session:repeated-question",
            episode_id="episode:repeated-question",
        )

    changed_catalog = _catalog(2, 26)
    with pytest.raises(QuestionAlreadyResolvedError, match="explicit reopen"):
        coordinator.register(
            _request(changed_catalog, plan),
            session_id="session:undeclared-new-catalog",
            episode_id="episode:undeclared-new-catalog",
        )
    changed_catalog_registration = coordinator.register(
        _request(
            changed_catalog,
            plan,
            reopen=QuestionReopenDeclaration(
                memory_record.memory_id,
                QuestionReopenReason.NEW_CATALOG,
                "A newly registered catalog may change the earlier protected conclusion.",
            ),
        ),
        session_id="session:new-catalog",
        episode_id="episode:new-catalog",
    )
    assert changed_catalog_registration.request.catalog.identity != memory_record.catalog_id
    assert coordinator.memory_context(changed_catalog_registration.registration_id) == (
        memory_record,
    )
    with pytest.raises(QuestionAlreadyResolvedError, match="unknown terminal memory"):
        coordinator.register(
            _request(
                changed_catalog,
                plan,
                reopen=QuestionReopenDeclaration(
                    "memory:unissued",
                    QuestionReopenReason.NEW_CATALOG,
                    "Attempt to cite a fabricated prior resolution.",
                ),
            ),
            session_id="session:forged-reopen",
            episode_id="episode:forged-reopen",
        )

    material_question = replace(
        _request(development_catalog, plan),
        question=ResearchQuestion(
            "question:authored-interaction",
            "Does a thresholded interaction predict the next value?",
            ENVIRONMENT,
            TASK,
            ("observation:material-hypothesis-change",),
        ),
    )
    with pytest.raises(QuestionAlreadyResolvedError, match="explicit reopen"):
        coordinator.register(
            material_question,
            session_id="session:undeclared-material-change",
            episode_id="episode:undeclared-material-change",
        )
    material_registration = coordinator.register(
        replace(
            material_question,
            reopen=QuestionReopenDeclaration(
                memory_record.memory_id,
                QuestionReopenReason.MATERIAL_HYPOTHESIS,
                "The nonlinear threshold changes the scientific hypothesis, not only wording.",
            ),
        ),
        session_id="session:material-change",
        episode_id="episode:material-change",
    )
    assert coordinator.memory_context(material_registration.registration_id) == (memory_record,)

    with sqlite3.connect(archive.database_path) as connection:
        encoded = connection.execute("SELECT record_json FROM question_memory").fetchone()
        assert encoded is not None
        forged = json.loads(str(encoded[0]))
        forged["question_text"] = "A filesystem-forged conclusion"
        connection.execute(
            "UPDATE question_memory SET record_json = ?",
            (json.dumps(forged, sort_keys=True, separators=(",", ":")),),
        )
        connection.commit()
    with pytest.raises(QuestionMemoryPersistenceError, match="reconstructed"):
        configure_validated_question_memory(
            DurableQuestionMemoryArchive(tmp_path / "validated-question-memory")
        )


def test_runtime_authored_question_reaches_finding_and_blocks_exact_repeat(
    tmp_path: Path,
) -> None:
    """Exercise the actual model-facing turn through protected resolution and memory."""
    development_catalog = _catalog(1, 25)
    protected_catalog = _catalog(25, 51)
    plan = _plan(protected_catalog)
    plan_registry, plan_issuer = configure_authored_protected_plan_authority(
        "authority:runtime-protected-plan"
    )
    plan_issuer.issue(plan)

    task_proposal = (
        TaskCompiler()
        .compile(
            UserMandate(
                original_text="Research the authored interaction world.",
                research_objective="Find a lawful next-observation predictive relationship.",
                target_field_id="y",
                forecast_horizon=TemporalOffset.elapsed(DAY),
                dataset_refs=("authored-interaction",),
            ),
            ResearchEnvironmentSummary(
                environment_id=ENVIRONMENT,
                available_field_ids=("x1", "x2", "future_poison", "y"),
                available_dataset_refs=("authored-interaction",),
            ),
        )
        .proposal
    )
    assert task_proposal is not None
    published = TaskPublisher().confirm(
        task_proposal,
        TaskConfirmation(
            confirmation_id=f"confirmation:{task_proposal.proposal_id}",
            proposal_id=task_proposal.proposal_id,
            proposal_version=task_proposal.version,
            semantic_digest=task_proposal.semantic_digest,
            approved=True,
        ),
    )
    assert published.task is not None
    task = published.task
    store = InMemoryRuntimeStore()
    initialized = ResearchRuntimeInitializer(store).initialize(
        task,
        ResearchEnvironmentSnapshot(
            environment_id=ENVIRONMENT,
            version=1,
            dataset_refs=("authored-interaction",),
            readable_dataset_refs=("authored-interaction",),
            capability_names=("run_authored_development_trial",),
            protected_resource_refs=(plan.protected_scope.resource_id,),
        ),
        request_id="initialize:authored-full-application",
    )
    session_id = initialized.session.session_id

    archive = DurableQuestionMemoryArchive(tmp_path / "runtime-question-memory")
    question_memory, memory_issuer = configure_validated_question_memory(archive)
    coordinator = RuntimeInvestigationCoordinator(question_memory=question_memory)
    ledger = ResearchLedger()
    eligibility = FreezeEligibilityRegistry()
    frozen_systems = FrozenSystemRegistry()
    freeze_service = AuthoredFreezeService(
        authority_id="authority:runtime-freeze",
        investigations=coordinator,
        eligibility=eligibility,
        gate=FreezeGate(
            ledger=ledger,
            registry=frozen_systems,
            eligibility=eligibility,
            decision_authority_id="authority:runtime-freeze",
            clock=_clock,
        ),
    )
    governance_grant = PermissionGrant(
        session_id,
        "authority:runtime-governance",
        frozenset((plan.protected_scope.scope_id,)),
        plan.protected_scope.policy_ref,
        ENVIRONMENT,
    )
    validation_grant = ValidationAuthorityGrant(
        "authority:runtime-validation",
        plan.promotion_standard.authority_policy_ref,
        ENVIRONMENT,
    )
    authorities = WorkflowAuthorityRegistry(
        governance_permissions=(governance_grant,),
        validation_grants=(validation_grant,),
    )
    exposures = ExposureRegistry()
    permits = PermitRegistry()
    governance = BacktestGovernance(
        ledger=ledger,
        frozen_systems=frozen_systems,
        exposures=exposures,
        permits=permits,
        permissions=(governance_grant,),
        current_environment_ref=ENVIRONMENT,
        current_policy_ref=plan.protected_scope.policy_ref,
        clock=_clock,
    )
    binder = ProtectedViewBinder(
        permits=permits,
        clock=_clock,
        current_environment_ref=ENVIRONMENT,
        current_policy_ref=plan.protected_scope.policy_ref,
    )
    engine = AuthoredBacktestEngine(
        investigations=coordinator,
        plans=plan_registry,
        permits=permits,
        frozen_systems=frozen_systems,
        views=binder,
        exposures=ExposureRecorder(registry=exposures, ledger=ledger, clock=_clock),
        ledger=ledger,
        clock=_clock,
    )
    protected_resources, protected_issuer = configure_protected_resource_authority(
        "authority:runtime-protected-resource"
    )
    protected_issuer.issue(
        scope=plan.protected_scope,
        resource_binding_ref="binding:runtime-authored-protected-v1",
        content_manifest=_manifest(protected_catalog),
        catalog=protected_catalog,
    )
    evaluator = Evaluator(ledger=ledger, runs=engine.issued_runs, clock=_clock)
    negatives = NegativeResultRegistry()
    validator = Validator(
        authorized_authority_ids=frozenset((validation_grant.authority_id,)),
        authority_policy_ref=validation_grant.authority_policy_ref,
        ledger=ledger,
        reports=evaluator.issued_reports,
        negatives=negatives,
        clock=_clock,
    )
    publisher = FindingPublisher(
        ledger=ledger,
        reports=evaluator.issued_reports,
        decisions=validator.issued_decisions,
        clock=_clock,
    )
    resolution_service = AuthoredProtectedResolutionService(
        investigations=coordinator,
        frozen_systems=frozen_systems,
        plans=plan_registry,
        authorities=authorities,
        protected_resources=protected_resources,
        governance=governance,
        views=binder,
        engine=engine,
        evaluator=evaluator,
        validator=validator,
        publisher=publisher,
        negatives=negatives,
    )
    memory_recorder = memory_issuer.bind(
        investigations=coordinator,
        resolutions=resolution_service,
        clock=_clock,
    )
    router = ActionRouter(
        store,
        DatasetRepository(()),
        investigations=coordinator,
        authored_freeze=freeze_service,
        authored_resolution=resolution_service,
        authored_memory=memory_recorder,
    )
    request = _request(development_catalog, plan, task_ref=task.task_id)
    registration = router.register_investigation(request, session_id=session_id)
    context = ContextBuilder(store)
    runtime = AutonomousResearchRuntime(
        store,
        _OneAuthoredTrialProvider(registration.registration_id, _proposal(development_catalog)),
        context,
        router,
        CommitCoordinator(store),
    )

    turn = runtime.advance_one_turn(session_id)

    assert turn.observation is not None
    assert turn.observation.status is ObservationStatus.SUCCEEDED
    assert turn.observation.epistemic_status == "PROTECTED_VALIDATED"
    assert turn.observation.payload["protected_resolution_status"] == "finding"
    assert turn.observation.payload["question_memory_status"] == "recorded"
    memory_id = turn.observation.payload["question_memory_id"]
    assert isinstance(memory_id, str)
    assert len(question_memory.records()) == 1
    assert question_memory.records()[0].memory_id == memory_id
    assert f"question-memory:{memory_id}" in turn.observation.artifact_refs
    assert archive.index_path.is_file()
    assert (archive.markdown_directory / f"{memory_id}.md").is_file()
    rebuilt = context.build_current_context(session_id)
    assert rebuilt.working_observations[-1].payload["question_memory_id"] == memory_id
    with pytest.raises(QuestionAlreadyResolvedError, match="already resolved"):
        router.register_investigation(request, session_id=session_id)
    changed_catalog_request = _request(
        _catalog(2, 26),
        plan,
        task_ref=task.task_id,
        reopen=QuestionReopenDeclaration(
            memory_id,
            QuestionReopenReason.NEW_CATALOG,
            "Re-evaluate only because the exact registered catalog changed.",
        ),
    )
    changed_registration = router.register_investigation(
        changed_catalog_request,
        session_id=session_id,
    )
    rebuilt_with_memory = context.build_current_context(session_id)
    memory_context = rebuilt_with_memory.working_observations[-1].payload["prior_question_memory"]
    assert isinstance(memory_context, tuple)
    assert memory_context[0]["memory_id"] == memory_id
    assert coordinator.memory_context(changed_registration.registration_id) == (
        question_memory.records()[0],
    )
