"""Domain-neutral deterministic vertical fixture for scientific workflow proofs."""

# ruff: noqa: EM101, PLR0913, TRY003

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256

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
from research_agent.development import DevelopmentEvaluator, DevelopmentProtocol, TrialStatus
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
    ClaimDefinition,
    CriterionComparison,
    DecisionStatus,
    EvaluationScenario,
    EvaluationSpec,
    FreezeEligibilityIssuer,
    FreezeEligibilityRegistry,
    FreezeEligibilityRequest,
    MetricCriterion,
    MetricName,
    PermissionGrant,
    PromotionStandard,
    ProtectedContentManifest,
    ProtectedExposureStatus,
    ProtectedResourceScope,
    ScenarioKind,
)
from research_agent.runtime._canonical import content_digest
from research_agent.runtime.initialization import ResearchRuntimeInitializer
from research_agent.runtime.models import ResearchEnvironmentSnapshot, RuntimeInitialization
from research_agent.runtime.store import InMemoryRuntimeStore
from research_agent.scientific_workflow import (
    ProtectedResourceIssuer,
    ProtectedResourceRegistration,
    ProtectedResourceRegistry,
    RegisteredScientificWorkflow,
    ScientificWorkflowCoordinator,
    ScientificWorkflowIssuer,
    ValidationAuthorityGrant,
    WorkflowAuthorityRegistry,
    WorkflowRegistry,
    configure_protected_resource_authority,
    configure_scientific_workflow_authority,
)
from research_agent.task_compilation import (
    ResearchEnvironmentSummary,
    ResearchTask,
    TaskCompiler,
    TaskConfirmation,
    TaskPublisher,
    UserMandate,
)

DAY = timedelta(days=1)
ELAPSED_DAY = TemporalOffset.elapsed(DAY)
ZERO_OFFSET = TemporalOffset.zero()
ORIGIN = datetime(2025, 1, 1, tzinfo=UTC)
NOW = ORIGIN + DAY * 30
ENVIRONMENT_ID = "workflow-environment"
ENVIRONMENT_REF = f"{ENVIRONMENT_ID}@1"
DATASET_ID = "workflow-series"
PROTECTED_RESOURCE_ID = "workflow-protected"
PROTECTED_RESOURCE_AUTHORITY_ID = "protected-data-authority"
WORKFLOW_AUTHORITY_ID = "workflow-authority"
GOVERNANCE_AUTHORITY_ID = "backtest-governor"
VALIDATION_AUTHORITY_ID = "finding-validator"


def fixed_clock() -> datetime:
    """Return one deterministic authority time for exact-replay proofs."""
    return NOW


@dataclass(frozen=True, slots=True)
class ToyScientificWorkflowWorld:
    """Runnable task/session/workflow composition plus its poison identity."""

    store: InMemoryRuntimeStore
    initialized: RuntimeInitialization
    registry: WorkflowRegistry
    coordinator: ScientificWorkflowCoordinator
    workflow: RegisteredScientificWorkflow
    future_poison_observation_id: str
    authorities: WorkflowAuthorityRegistry
    protected_resources: ProtectedResourceRegistry
    protected_resource_issuer: ProtectedResourceIssuer
    protected_resource_registration: ProtectedResourceRegistration
    workflow_issuer: ScientificWorkflowIssuer


@dataclass(frozen=True, slots=True)
class ToyScientificDefinition:
    """Unfitted domain-neutral scientific inputs for verification compositions."""

    schema: DatasetSchema
    system: PredictiveSystemDefinition


def make_toy_scientific_definition(
    *,
    world_id: str = "definition",
) -> ToyScientificDefinition:
    """Build exact task-derived target, feature, model, and protocol identities without fitting."""
    task = _confirmed_task(world_id)
    schema = _schema()
    protocol = DevelopmentProtocol(
        name="ordered development",
        version=1,
        minimum_training_rows=3,
        validation_rows=2,
        step_rows=2,
        purge_overlapping_labels=True,
        embargo=None,
        metric_names=("mse", "mae"),
        feature_analysis_methods=("permutation", "ablation", "single_feature"),
        environment_id=ENVIRONMENT_REF,
        provenance_refs=("protocol:development-v1",),
    )
    target = _target(schema, task)
    return ToyScientificDefinition(schema, _system(schema, target, protocol))


def make_toy_scientific_workflow_world(
    *,
    world_id: str = "primary",
    promotion_mse_threshold: float = 0.001,
    readable_protected_resource: bool = True,
    include_future_poison: bool = True,
    protected_final_day: int = 13,
    outcome_slope: float = 2.0,
    freeze_status: DecisionStatus = DecisionStatus.ACCEPT,
    freeze_eligibility: FreezeEligibilityRegistry | None = None,
) -> ToyScientificWorkflowWorld:
    """Build a new domain-neutral subject using the same scientific coordinator."""
    task = _confirmed_task(world_id)
    environment = ResearchEnvironmentSnapshot(
        environment_id=ENVIRONMENT_ID,
        version=1,
        dataset_refs=(DATASET_ID,),
        readable_dataset_refs=(DATASET_ID,),
        capability_names=("inspect_dataset", "run_scientific_workflow"),
        protected_resource_refs=(PROTECTED_RESOURCE_ID,) if readable_protected_resource else (),
        warnings=("Protected evaluation requires the registered workflow gate.",),
    )
    store = InMemoryRuntimeStore()
    initialized = ResearchRuntimeInitializer(store).initialize(
        task,
        environment,
        request_id=f"initialize:{world_id}",
    )
    schema = _schema()
    development_catalog = _catalog(
        schema,
        final_day=8,
        include_future_poison=False,
        outcome_slope=outcome_slope,
    )
    protected_catalog = _catalog(
        schema,
        final_day=protected_final_day,
        include_future_poison=include_future_poison,
        outcome_slope=outcome_slope,
    )
    poison = next(
        (
            item.observation_id
            for item in protected_catalog.observations
            if item.provenance_ref == "provenance:future-poison"
        ),
        "",
    )
    target = _target(schema, task)
    protocol = DevelopmentProtocol(
        name="ordered development",
        version=1,
        minimum_training_rows=3,
        validation_rows=2,
        step_rows=2,
        purge_overlapping_labels=True,
        embargo=None,
        metric_names=("mse", "mae"),
        feature_analysis_methods=("permutation", "ablation", "single_feature"),
        environment_id=ENVIRONMENT_REF,
        provenance_refs=("protocol:development-v1",),
    )
    system = _system(schema, target, protocol)
    scenario = EvaluationScenario(
        name="protected historical path",
        version=1,
        kind=ScenarioKind.HISTORICAL_WALK_FORWARD,
        decision_sample_keys=tuple(SampleKey(ORIGIN + DAY * day) for day in (10, 11, 12)),
        training_candidate_keys=tuple(SampleKey(ORIGIN + DAY * day) for day in range(12)),
        outcome_recorded_at=ORIGIN + DAY * 14,
        training_protocol_ref=system.training_protocol_id,
        window_policy=TrainingWindowPolicy(
            1,
            WindowKind.EXPANDING,
            3,
            None,
            "protocol:protected-expanding-v1",
        ),
        missingness_policy=MissingnessPolicy.EXCLUDE_EXAMPLE,
        interpretation="one realized historical walk-forward path",
        environment_ref=ENVIRONMENT_REF,
        data_protocol_ref=system.data_protocol_id,
        provenance_refs=("scenario:historical-v1",),
    )
    evaluation_spec = EvaluationSpec(
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
        evaluation_spec_id=evaluation_spec.identity,
        criteria=(
            MetricCriterion(
                MetricName.MSE,
                CriterionComparison.LESS_THAN_OR_EQUAL,
                promotion_mse_threshold,
            ),
            MetricCriterion(
                MetricName.COVERAGE,
                CriterionComparison.GREATER_THAN_OR_EQUAL,
                1.0,
            ),
            MetricCriterion(
                MetricName.FAILURE_RATE,
                CriterionComparison.LESS_THAN_OR_EQUAL,
                0.0,
            ),
        ),
        maximum_stability_stddev=0.001,
        maximum_error_concentration=1.0,
        required_scenario_kind=ScenarioKind.HISTORICAL_WALK_FORWARD,
        authority_policy_ref="validation-policy:v1",
        provenance_refs=("validation:predeclared",),
    )
    claim = ClaimDefinition(
        name="bounded forecast claim",
        version=1,
        statement="The frozen system met the exact predeclared forecast standard.",
        system_id=system.identity,
        target_id=target.identity,
        scope_limitations=("applies only to the declared protected historical path",),
        required_caveats=("does not establish downstream usefulness",),
        provenance_refs=("claim:predeclared-v1",),
    )
    protected_catalog_bytes = protected_catalog.identity.encode()
    protected_manifest = ProtectedContentManifest.create(
        content_digest=sha256(protected_catalog_bytes).hexdigest(),
        byte_length=len(protected_catalog_bytes),
        catalog_id=protected_catalog.identity,
        provenance_ref="fixture:protected-catalog",
    )
    scope = ProtectedResourceScope(
        resource_id=PROTECTED_RESOURCE_ID,
        resource_version="v1",
        slice_id=f"holdout:{protected_manifest.content_identity_id}",
        environment_ref=ENVIRONMENT_REF,
        policy_ref="protected-policy:v1",
        content_manifest_id=protected_manifest.manifest_id,
        content_identity_id=protected_manifest.content_identity_id,
        epistemic_period_ref=f"protected-period:{protected_manifest.content_identity_id}",
        exposure_status=ProtectedExposureStatus.UNSEEN,
    )
    protected_resources, protected_resource_issuer = configure_protected_resource_authority(
        PROTECTED_RESOURCE_AUTHORITY_ID
    )
    protected_resource_registration = protected_resource_issuer.issue(
        scope=scope,
        resource_binding_ref=f"protected-binding:{protected_catalog.identity}",
        content_manifest=protected_manifest,
        catalog=protected_catalog,
    )
    authorities = WorkflowAuthorityRegistry(
        governance_permissions=(
            PermissionGrant(
                actor_id="research-runtime",
                authority_id=GOVERNANCE_AUTHORITY_ID,
                scope_ids=frozenset({scope.scope_id}),
                policy_ref=scope.policy_ref,
                environment_ref=scope.environment_ref,
            ),
        ),
        validation_grants=(
            ValidationAuthorityGrant(
                authority_id=VALIDATION_AUTHORITY_ID,
                authority_policy_ref=standard.authority_policy_ref,
                environment_ref=scope.environment_ref,
            ),
        ),
    )
    development_candidate_keys = tuple(SampleKey(ORIGIN + DAY * day) for day in range(7))
    development_current_time = ORIGIN + DAY * 9
    dependencies = tuple(
        dict.fromkeys(
            dependency
            for feature in system.feature_set.members
            for dependency in feature.dependencies
        )
    )
    development_sample = TrainingSampleBuilder().build(
        development_catalog,
        target=system.target,
        predictor_fields=dependencies,
        candidate_sample_keys=development_candidate_keys,
        current_time=development_current_time,
        missingness_policy=MissingnessPolicy.EXCLUDE_EXAMPLE,
    )
    authority_evaluator = DevelopmentEvaluator()
    authority_evidence = authority_evaluator.evaluate(
        system,
        development_sample,
        protocol,
        protected_evaluation_spec_ref=evaluation_spec.identity,
        validation_standard_ref=standard.identity,
        catalog=development_catalog,
    )
    authority_evaluator.ledger.append(
        trial_id=authority_evidence.trial_id,
        candidate_id=system.identity,
        protocol_id=protocol.identity,
        parent_trial_ids=(),
        status=TrialStatus.SELECTED,
        rationale="independent authority selected exact predeclared development evidence",
        evidence_refs=(authority_evidence.evidence_id,),
    )
    eligibility = freeze_eligibility or FreezeEligibilityRegistry()
    freeze_request = FreezeEligibilityRequest(
        system_id=system.identity,
        candidate_version=str(system.version),
        ancestry_refs=system.candidate_ancestry,
        development_evidence_refs=(authority_evidence.evidence_id,),
        protocol_refs=tuple(
            dict.fromkeys(
                (
                    system.data_protocol_id,
                    system.training_protocol_id,
                    system.evaluation_protocol_id,
                    evaluation_spec.identity,
                    standard.identity,
                )
            )
        ),
        environment_ref=ENVIRONMENT_REF,
        standard_ref=standard.identity,
        requester_id="research-runtime",
        beneficiary_id="candidate-owner",
    )
    freeze_registration = FreezeEligibilityIssuer(
        authority_id="freeze-governor",
        development_evidence=authority_evaluator.evidence_registry,
        trial_ledger=authority_evaluator.ledger,
        eligibility=eligibility,
    ).issue(
        freeze_request,
        evidence=authority_evidence,
        status=freeze_status,
        reason_code=(
            "DEVELOPMENT_EVIDENCE_ELIGIBLE"
            if freeze_status is DecisionStatus.ACCEPT
            else "INDEPENDENT_FREEZE_REJECTED"
        ),
    )
    workflow = RegisteredScientificWorkflow(
        task_id=task.task_id,
        task_version=task.version,
        task_semantic_digest=task.semantic_digest,
        session_id=initialized.session.session_id,
        episode_id=initialized.episode.episode_id,
        environment_ref=ENVIRONMENT_REF,
        environment_content_digest=content_digest(environment),
        development_catalog=development_catalog,
        system=system,
        development_protocol=protocol,
        development_candidate_keys=development_candidate_keys,
        development_current_time=development_current_time,
        development_missingness_policy=MissingnessPolicy.EXCLUDE_EXAMPLE,
        scenario=scenario,
        evaluation_spec=evaluation_spec,
        promotion_standard=standard,
        claim=claim,
        protected_scope=scope,
        requester_id="research-runtime",
        beneficiary_id="candidate-owner",
        protected_recipient_id=f"research-process:{world_id}",
        freeze_eligibility_registration=freeze_registration,
    )
    registry, workflow_issuer = configure_scientific_workflow_authority(
        authority_id=WORKFLOW_AUTHORITY_ID,
        freeze_eligibility=eligibility,
        authorities=authorities,
        protected_resources=protected_resources,
    )
    workflow_issuer.issue(workflow)
    coordinator = ScientificWorkflowCoordinator(
        registry=registry,
        runtime_store=store,
        clock=fixed_clock,
    )
    return ToyScientificWorkflowWorld(
        store,
        initialized,
        registry,
        coordinator,
        workflow,
        poison,
        authorities,
        protected_resources,
        protected_resource_issuer,
        protected_resource_registration,
        workflow_issuer,
    )


def workflow_for_session(
    world: ToyScientificWorkflowWorld,
    initialized: RuntimeInitialization,
) -> RegisteredScientificWorkflow:
    """Rebind the same scientific subject graph to another independent session."""
    return replace(
        world.workflow,
        session_id=initialized.session.session_id,
        episode_id=initialized.episode.episode_id,
    )


def _confirmed_task(world_id: str) -> ResearchTask:
    proposal = (
        TaskCompiler()
        .compile(
            UserMandate(
                original_text="Test one generic time-series predictive system.",
                research_objective="Evaluate a frozen predictive system without temporal leakage.",
                target_field_id="y",
                forecast_horizon=ELAPSED_DAY,
                dataset_refs=(DATASET_ID,),
                constraints=("use only as-known information",),
            ),
            ResearchEnvironmentSummary(
                environment_id=ENVIRONMENT_ID,
                available_field_ids=("x", "y"),
                available_dataset_refs=(DATASET_ID,),
                protected_resource_refs=(PROTECTED_RESOURCE_ID,),
            ),
        )
        .proposal
    )
    if proposal is None:
        raise RuntimeError("Toy workflow task did not compile.")
    result = TaskPublisher().confirm(
        proposal,
        TaskConfirmation(
            confirmation_id=f"confirmation:{world_id}",
            proposal_id=proposal.proposal_id,
            proposal_version=proposal.version,
            semantic_digest=proposal.semantic_digest,
            approved=True,
        ),
    )
    if result.task is None:
        raise RuntimeError("Toy workflow task was not confirmed.")
    return result.task


def _schema() -> DatasetSchema:
    return DatasetSchema(
        dataset_id=DATASET_ID,
        version="schema-v1",
        environment_id=ENVIRONMENT_REF,
        provenance_ref="artifact:schema-v1",
        fields=(
            FieldDefinition("x", "X", "float", "index", (), "Predictor."),
            FieldDefinition("y", "Y", "float", "units", (), "Outcome."),
        ),
    )


def _catalog(
    schema: DatasetSchema,
    *,
    final_day: int,
    include_future_poison: bool,
    outcome_slope: float,
) -> DataCatalogSnapshot:
    rows: list[ObservationInput] = []
    for day in range(final_day + 1):
        moment = ORIGIN + DAY * day
        rows.extend(
            (
                ObservationInput(
                    schema.field_ref("x"),
                    float(day),
                    moment,
                    moment,
                    f"x:{day}:v0",
                    0,
                    "source:x",
                    f"provenance:x:{day}",
                    "availability:x-v1",
                    (),
                ),
                ObservationInput(
                    schema.field_ref("y"),
                    float(outcome_slope * day + 1),
                    moment,
                    moment,
                    f"y:{day}:v0",
                    0,
                    "source:y",
                    f"provenance:y:{day}",
                    "availability:y-v1",
                    (),
                ),
            )
        )
    if include_future_poison:
        rows.append(
            ObservationInput(
                schema.field_ref("x"),
                999_999.0,
                ORIGIN + DAY * 10,
                ORIGIN + DAY * 20,
                "x:10:v1",
                1,
                "source:x",
                "provenance:future-poison",
                "availability:x-v1",
                (),
            )
        )
    registered = ObservationRegistrar().register(schema, tuple(rows))
    return DataCatalogSnapshot(ENVIRONMENT_REF, (registered,))


def _target(schema: DatasetSchema, task: ResearchTask) -> TargetDefinition:
    return TargetDefinition.from_confirmed_task(
        task,
        version=1,
        parent_target_id=None,
        field_ref=schema.field_ref("y"),
        kind=TargetKind.ENDPOINT,
        outcome_start_offset=ZERO_OFFSET,
        alignment=OutcomeAlignment.EXACT,
        path_reduction=None,
        event_condition=None,
        maturity_delay=ZERO_OFFSET,
        maturity_policy=MaturityPolicy.FULL_INTERVAL,
        required_observation_count=1,
        value_encoding="numeric",
        units="units",
        censoring_policy="complete interval",
        incomplete_outcome_policy=IncompleteOutcomePolicy.EXCLUDE,
        schema_provenance_ref=schema.provenance_ref,
        provenance_refs=("research:target",),
    )


def _system(
    schema: DatasetSchema,
    target: TargetDefinition,
    protocol: DevelopmentProtocol,
) -> PredictiveSystemDefinition:
    feature = FeatureDefinition(
        name="x",
        version=1,
        parent_definition_id=None,
        environment_id=ENVIRONMENT_REF,
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
        ENVIRONMENT_REF,
        (feature,),
        ("trial:features",),
        ("research:features",),
    )
    model = ModelDefinition(
        name="linear",
        version=1,
        parent_definition_id=None,
        environment_id=ENVIRONMENT_REF,
        algorithm="linear_regression",
        hyperparameters=(("fit_intercept", True), ("ridge", 0.0)),
        preprocessing_refs=(feature_set.identity,),
        selection_procedure_ref="selection:none",
        randomness_policy="deterministic",
        training_requirement_refs=("trainer:controlled-v1",),
        evidence_refs=("development:model",),
        candidate_ancestry=("candidate:model",),
        provenance_refs=("implementation:linear",),
    )
    return PredictiveSystemDefinition(
        name="generic-time-series-candidate",
        version=1,
        parent_system_id=None,
        environment_id=ENVIRONMENT_REF,
        target=target,
        feature_set=feature_set,
        models=(model,),
        ensemble=None,
        data_protocol_id="data:as-known-v1",
        training_protocol_id="training:refit-every-time-v1",
        evaluation_protocol_id=protocol.identity,
        evidence_refs=("development:candidate",),
        candidate_ancestry=("trial:parent",),
        provenance_refs=("research:system",),
    )


__all__ = [
    "DATASET_ID",
    "DAY",
    "ENVIRONMENT_ID",
    "ENVIRONMENT_REF",
    "NOW",
    "ORIGIN",
    "PROTECTED_RESOURCE_AUTHORITY_ID",
    "PROTECTED_RESOURCE_ID",
    "WORKFLOW_AUTHORITY_ID",
    "ToyScientificDefinition",
    "ToyScientificWorkflowWorld",
    "fixed_clock",
    "make_toy_scientific_definition",
    "make_toy_scientific_workflow_world",
    "workflow_for_session",
]
