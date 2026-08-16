"""Trusted production traces for compositions proven at this checkpoint."""

# ruff: noqa: EM101, PLR2004, TRY003

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from datetime import timedelta
from types import MappingProxyType
from typing import TYPE_CHECKING, cast
from unittest.mock import patch

from research_agent.data_foundation import (
    BoundaryStatus,
    DataCatalogSnapshot,
    InformationSetBuilder,
    MissingnessPolicy,
    ObservationInput,
    ObservationRegistrar,
    SampleKey,
    TemporalOffset,
    TrainingSampleBuilder,
    TrainingWindowPolicy,
    TrainingWindowSelector,
    WindowKind,
)
from research_agent.development import DevelopmentEvidence, FittedPredictiveSystem, SystemTrainer
from research_agent.exploration import (
    AnalysisHarness,
    ArtifactRef,
    ArtifactStore,
    CapabilityPolicy,
)
from research_agent.exploration import (
    AuthorizedDataView as ExploratoryDataView,
)
from research_agent.protected_evaluation import (
    AuthorizedProtectedDataView,
    BacktestPermit,
    BacktestRun,
    BacktestRunStatus,
    EvaluationReport,
    Evaluator,
    FrozenPredictiveSystemIdentity,
    NegativeResult,
    ResearchLedger,
    ValidatedFinding,
    ValidationDecision,
)
from research_agent.reporting import RenderedFindingReport
from research_agent.runtime.actions import (
    EpisodeTransitionProposal,
    InspectDatasetAction,
    RunAnalysisAction,
    StateUpdateProposal,
    decode_action,
)
from research_agent.runtime.capabilities import ActionRouter, DatasetDefinition, DatasetRepository
from research_agent.runtime.commit import CommitCoordinator, CommitRequest, CommitResult
from research_agent.runtime.context import ContextBuilder
from research_agent.runtime.engine import AutonomousResearchRuntime
from research_agent.runtime.initialization import ResearchRuntimeInitializer
from research_agent.runtime.models import (
    ContextPacket,
    EpisodeStatus,
    ObservationStatus,
    ResearchEnvironmentSnapshot,
    StructuredObservation,
)
from research_agent.runtime.provider import ModelResponse
from research_agent.runtime.store import InjectedPersistenceError, InMemoryRuntimeStore
from research_agent.scientific_workflow import (
    ProtectedResourceIssuer,
    ScientificWorkflowIssuer,
    WorkflowRegistryError,
    WorkflowStatus,
)
from research_agent.task_compilation import (
    ResearchEnvironmentSummary,
    TaskCompiler,
    TaskConfirmation,
    TaskPublisher,
    UserMandate,
)
from research_agent.verification.catalog import (
    ArtifactTrace,
    AtomicCommitWorldTrace,
    ContextReconstructionWorldTrace,
    ExplorationContinuationWorldTrace,
    FailureRepairWorldTrace,
    LegalFitWorldTrace,
    ObservationWorldTrace,
    ScientificWorkflowTrace,
)
from research_agent.verification.composites import (
    ProductionProofFailureError,
    ProofAdapterRegistry,
    ProofTrace,
)
from research_agent.verification.scientific_workflow_fixture import (
    DAY,
    ORIGIN,
    ToyScientificWorkflowWorld,
    fixed_clock,
    make_toy_scientific_definition,
    make_toy_scientific_workflow_world,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from research_agent.data_foundation import DatasetSchema
    from research_agent.formalization import PredictiveSystemDefinition
    from research_agent.runtime.models import RuntimeInitialization
    from research_agent.runtime.provider import ModelProvider


def production_proof_registry() -> ProofAdapterRegistry:
    """Register only complete compositions with catalog-owned production-trace oracles."""
    registry = ProofAdapterRegistry()
    registry.register_catalog_adapter(ObservationToNextActionAdapter())
    registry.register_catalog_adapter(AtomicSemanticCommitAdapter())
    registry.register_catalog_adapter(AuthorizedExplorationToNextActionAdapter())
    registry.register_catalog_adapter(ContextLossReconstructionAdapter())
    registry.register_catalog_adapter(FailureToRepairedContinuationAdapter())
    registry.register_catalog_adapter(LegalFitCompositionAdapter())
    registry.register_catalog_adapter(
        ScientificWorkflowAdapter("development-to-protected-authority")
    )
    registry.register_catalog_adapter(ScientificWorkflowAdapter("frozen-system-to-immutable-run"))
    registry.register_catalog_adapter(ScientificWorkflowAdapter("run-to-finding-or-rejection"))
    registry.register_catalog_adapter(ScientificWorkflowAdapter("finding-to-report-invariance"))
    return registry


class AtomicSemanticCommitAdapter:
    """Exercise authoritative evidence through atomic semantic commit and retry."""

    proposition_id = "evidence-to-atomic-commit"
    adapter_id = "production.runtime.atomic-semantic-commit.v1"

    def execute(self) -> ProofTrace:
        """Return raw state, event, denial, stage-fault, replay, and conflict worlds."""
        try:
            worlds = _run_atomic_commit_worlds()
        except Exception as error:
            message = f"{type(error).__name__}: {error}"
            raise ProductionProofFailureError(message) from error
        return ProofTrace(
            proposition_id=self.proposition_id,
            adapter_id=self.adapter_id,
            facts=MappingProxyType({"worlds": worlds}),
        )


def _run_atomic_commit_worlds() -> tuple[AtomicCommitWorldTrace, ...]:
    return (
        _run_authoritative_commit_world(),
        _run_foreign_evidence_world(),
        _run_forged_evidence_world(),
        *(
            _run_commit_stage_failure_world(stage)
            for stage in ("episode", "state", "commit", "event")
        ),
        _run_commit_replay_conflict_world(),
    )


def _authoritative_commit_context(
    world: str,
) -> tuple[
    InMemoryRuntimeStore,
    RuntimeInitialization,
    StructuredObservation,
    CommitRequest,
]:
    store, initialized = _initialized_runtime(world)
    observation = ActionRouter(store, DatasetRepository((_dataset(18),))).execute_inspection(
        InspectDatasetAction(
            action_id=f"inspect:{world}",
            session_id=initialized.session.session_id,
            episode_id=initialized.episode.episode_id,
            dataset_ref="proof-dataset",
            selected_field_ids=("reference_time", "value"),
            preview_limit=2,
        )
    )
    store.record_observation(initialized.session.session_id, observation)
    request = CommitRequest(
        session_id=initialized.session.session_id,
        episode_id=initialized.episode.episode_id,
        transition=EpisodeTransitionProposal(
            EpisodeStatus.RESOLVED,
            "Authorized inspection established the bounded descriptive facts.",
            (observation.observation_id,),
        ),
        state_update=StateUpdateProposal(
            starting_state_version=0,
            durable_understanding=("The authorized proof dataset contains 18 rows.",),
            evidence_refs=(observation.observation_id,),
        ),
        idempotency_key=f"semantic-commit:{world}",
    )
    return store, initialized, observation, request


def _run_authoritative_commit_world() -> AtomicCommitWorldTrace:
    store, _, observation, request = _authoritative_commit_context("authoritative")
    _, _, _, initial_state, initial_episode = store.coherent_view(request.session_id)
    events_before = store.events_for(request.session_id)
    result = CommitCoordinator(store).commit(request)
    _, _, _, state_after, episode_after = store.coherent_view(request.session_id)
    events_after = store.events_for(request.session_id)
    return AtomicCommitWorldTrace(
        "authoritative-evidence",
        observation,
        request,
        events_before,
        initial_state,
        initial_episode,
        result,
        None,
        state_after,
        episode_after,
        len(store.commits),
        events_after,
        None,
        None,
        None,
        state_after,
        episode_after,
        len(store.commits),
        events_after,
    )


def _run_foreign_evidence_world() -> AtomicCommitWorldTrace:
    store, initialized, _, local_request = _authoritative_commit_context("foreign-local")
    task, environment, _, _, _ = store.coherent_view(initialized.session.session_id)
    foreign_initialized = ResearchRuntimeInitializer(store).initialize(
        task,
        environment,
        request_id="initialize:foreign-evidence-source",
    )
    foreign_observation = ActionRouter(
        store,
        DatasetRepository((_dataset(18),)),
    ).execute_inspection(
        InspectDatasetAction(
            action_id="inspect:foreign-evidence",
            session_id=foreign_initialized.session.session_id,
            episode_id=foreign_initialized.episode.episode_id,
            dataset_ref="proof-dataset",
            selected_field_ids=("value",),
            preview_limit=1,
        )
    )
    store.record_observation(foreign_initialized.session.session_id, foreign_observation)
    if local_request.state_update is None:
        raise RuntimeError("atomic proof request must include a state update")
    request = replace(
        local_request,
        transition=replace(
            local_request.transition,
            evidence_refs=(foreign_observation.observation_id,),
        ),
        state_update=replace(
            local_request.state_update,
            evidence_refs=(foreign_observation.observation_id,),
        ),
    )
    _, _, _, initial_state, initial_episode = store.coherent_view(request.session_id)
    events_before = store.events_for(request.session_id)
    result = CommitCoordinator(store).commit(request)
    _, _, _, state_after, episode_after = store.coherent_view(request.session_id)
    events_after = store.events_for(request.session_id)
    return AtomicCommitWorldTrace(
        "foreign-evidence",
        foreign_observation,
        request,
        events_before,
        initial_state,
        initial_episode,
        result,
        None,
        state_after,
        episode_after,
        len(store.commits),
        events_after,
        None,
        None,
        None,
        state_after,
        episode_after,
        len(store.commits),
        events_after,
    )


def _run_forged_evidence_world() -> AtomicCommitWorldTrace:
    store, _, observation, request = _authoritative_commit_context("forged")
    if observation.provenance is None:
        raise RuntimeError("Authoritative proof observation lacks harness provenance.")
    forged = replace(
        observation,
        session_id="forged-session",
        provenance=replace(observation.provenance, session_id="forged-session"),
    )
    store.observations[observation.observation_id] = forged
    _, _, _, initial_state, initial_episode = store.coherent_view(request.session_id)
    events_before = store.events_for(request.session_id)
    result: CommitResult | None = None
    failure_type: str | None = None
    try:
        result = CommitCoordinator(store).commit(request)
    except RuntimeError as error:
        failure_type = type(error).__name__
    _, _, _, state_after, episode_after = store.coherent_view(request.session_id)
    events_after = store.events_for(request.session_id)
    return AtomicCommitWorldTrace(
        "forged-evidence",
        forged,
        request,
        events_before,
        initial_state,
        initial_episode,
        result,
        failure_type,
        state_after,
        episode_after,
        len(store.commits),
        events_after,
        None,
        None,
        None,
        state_after,
        episode_after,
        len(store.commits),
        events_after,
    )


def _run_commit_stage_failure_world(stage: str) -> AtomicCommitWorldTrace:
    store, _, observation, request = _authoritative_commit_context(f"failure-{stage}")
    _, _, _, initial_state, initial_episode = store.coherent_view(request.session_id)
    events_before = store.events_for(request.session_id)
    store.fail_commit_after_stage = stage
    result: CommitResult | None = None
    failure_type: str | None = None
    try:
        result = CommitCoordinator(store).commit(request)
    except InjectedPersistenceError as error:
        failure_type = type(error).__name__
    _, _, _, state_after, episode_after = store.coherent_view(request.session_id)
    events_after = store.events_for(request.session_id)
    commit_count_after = len(store.commits)
    retry = CommitCoordinator(store).commit(request)
    _, _, _, final_state, final_episode = store.coherent_view(request.session_id)
    return AtomicCommitWorldTrace(
        f"failure-after-{stage}",
        observation,
        request,
        events_before,
        initial_state,
        initial_episode,
        result,
        failure_type,
        state_after,
        episode_after,
        commit_count_after,
        events_after,
        retry,
        None,
        None,
        final_state,
        final_episode,
        len(store.commits),
        store.events_for(request.session_id),
    )


def _run_commit_replay_conflict_world() -> AtomicCommitWorldTrace:
    store, _, observation, request = _authoritative_commit_context("replay-conflict")
    _, _, _, initial_state, initial_episode = store.coherent_view(request.session_id)
    events_before = store.events_for(request.session_id)
    coordinator = CommitCoordinator(store)
    result = coordinator.commit(request)
    _, _, _, state_after, episode_after = store.coherent_view(request.session_id)
    events_after = store.events_for(request.session_id)
    replay = CommitCoordinator(store).commit(request)
    changed = replace(
        request,
        transition=replace(request.transition, synthesis="Changed scientific synthesis."),
    )
    conflict = CommitCoordinator(store).commit(changed)
    _, _, _, final_state, final_episode = store.coherent_view(request.session_id)
    return AtomicCommitWorldTrace(
        "exact-replay-and-conflict",
        observation,
        request,
        events_before,
        initial_state,
        initial_episode,
        result,
        None,
        state_after,
        episode_after,
        len(store.commits),
        events_after,
        replay,
        changed,
        conflict,
        final_state,
        final_episode,
        len(store.commits),
        store.events_for(request.session_id),
    )


class LegalFitCompositionAdapter:
    """Exercise registered observations through the controlled fit boundary."""

    proposition_id = "registered-data-to-legal-fit"
    adapter_id = "production.data.legal-fit-composition.v1"

    def execute(self) -> ProofTrace:
        """Return raw production objects from causal temporal and fitting interventions."""
        try:
            worlds = _run_legal_fit_worlds()
        except Exception as error:
            message = f"{type(error).__name__}: {error}"
            raise ProductionProofFailureError(message) from error
        return ProofTrace(
            proposition_id=self.proposition_id,
            adapter_id=self.adapter_id,
            facts=MappingProxyType({"worlds": worlds}),
        )


def _run_legal_fit_worlds() -> tuple[LegalFitWorldTrace, ...]:
    definition = make_toy_scientific_definition(world_id="legal-fit-proof")
    schema = definition.schema
    system = definition.system
    normal_rows = _legal_fit_rows(schema)
    half_day_label = _observation(
        schema,
        "y",
        24.0,
        ORIGIN + DAY * 11 + DAY / 2,
        ORIGIN + DAY * 11 + DAY / 2,
        "y:11.5:v0",
        0,
        "provenance:y:11.5",
    )
    baseline_catalog = _register_legal_fit_catalog(schema, (*normal_rows, half_day_label))
    future_catalog = _register_legal_fit_catalog(
        schema,
        (
            *normal_rows,
            half_day_label,
            _observation(
                schema,
                "x",
                999_999.0,
                ORIGIN + DAY * 10 + DAY / 2,
                ORIGIN + DAY * 20,
                "x:10.5:poison",
                0,
                "provenance:x:10.5:poison",
            ),
        ),
    )
    released_catalog = _register_legal_fit_catalog(
        schema,
        (
            *normal_rows,
            half_day_label,
            _observation(
                schema,
                "x",
                999_999.0,
                ORIGIN + DAY * 10 + DAY / 2,
                ORIGIN + DAY * 10 + DAY / 2,
                "x:10.5:poison",
                0,
                "provenance:x:10.5:poison",
            ),
        ),
    )
    poison_candidates = (
        *(SampleKey(ORIGIN + DAY * day) for day in range(11)),
        SampleKey(ORIGIN + DAY * 10 + DAY / 2),
    )
    fit_current_time = ORIGIN + DAY * 14
    fit_policy = TrainingWindowPolicy(
        1,
        WindowKind.EXPANDING,
        3,
        None,
        "proof:legal-fit-expanding",
    )
    baseline = _run_legal_fit_world(
        "baseline",
        baseline_catalog,
        system,
        candidate_keys=poison_candidates,
        current_time=fit_current_time,
        policy=fit_policy,
        fit_when_ready=True,
    )
    future_poison_id = _observation_id(future_catalog, "provenance:x:10.5:poison")
    future = _run_legal_fit_world(
        "future-unreleased-poison",
        future_catalog,
        system,
        candidate_keys=poison_candidates,
        current_time=fit_current_time,
        policy=fit_policy,
        fit_when_ready=True,
        poison_observation_id=future_poison_id,
    )
    released_poison_id = _observation_id(
        released_catalog,
        "provenance:x:10.5:poison",
    )
    released = _run_legal_fit_world(
        "legally-released-poison",
        released_catalog,
        system,
        candidate_keys=poison_candidates,
        current_time=fit_current_time,
        policy=fit_policy,
        fit_when_ready=True,
        poison_observation_id=released_poison_id,
    )

    clock_rows = tuple(
        row
        for row in normal_rows
        if not (row.field_ref.field_id == "y" and row.reference_time == ORIGIN + DAY * 13)
    )
    clock_catalog = _register_legal_fit_catalog(
        schema,
        (
            *clock_rows,
            _observation(
                schema,
                "y",
                27.0,
                ORIGIN + DAY * 13,
                ORIGIN + DAY * 13 + DAY * 3 / 4,
                "y:13:delayed",
                0,
                "provenance:y:13:delayed",
            ),
            _observation(
                schema,
                "x",
                13.25,
                ORIGIN + DAY * 13 + DAY / 4,
                ORIGIN + DAY * 13 + DAY / 4,
                "x:13.25:v0",
                0,
                "provenance:x:13.25",
            ),
            _observation(
                schema,
                "x",
                5_000.0,
                ORIGIN + DAY * 5,
                ORIGIN + DAY * 15,
                "x:5:v1",
                1,
                "provenance:x:5:future-revision",
            ),
        ),
    )
    original_revision_id = _observation_id(clock_catalog, "provenance:x:5")
    future_revision_id = _observation_id(clock_catalog, "provenance:x:5:future-revision")
    clock_policy = TrainingWindowPolicy(
        1,
        WindowKind.EXPANDING,
        1,
        None,
        "proof:clock-expanding",
    )
    clock_candidates = (SampleKey(ORIGIN + DAY * 12),)
    before = _run_legal_fit_world(
        "clock-before",
        clock_catalog,
        system,
        candidate_keys=clock_candidates,
        current_time=ORIGIN + DAY * 13,
        policy=clock_policy,
        fit_when_ready=False,
    )
    predictor = _run_legal_fit_world(
        "predictor-released",
        clock_catalog,
        system,
        candidate_keys=clock_candidates,
        current_time=ORIGIN + DAY * 13 + DAY / 2,
        policy=clock_policy,
        fit_when_ready=False,
    )
    label = _run_legal_fit_world(
        "label-matured",
        clock_catalog,
        system,
        candidate_keys=clock_candidates,
        current_time=ORIGIN + DAY * 14,
        policy=clock_policy,
        fit_when_ready=False,
    )
    revision = _run_legal_fit_world(
        "earlier-revision-view",
        clock_catalog,
        system,
        candidate_keys=tuple(SampleKey(ORIGIN + DAY * day) for day in range(5)),
        current_time=ORIGIN + DAY * 6,
        policy=clock_policy,
        fit_when_ready=False,
        original_revision_observation_id=original_revision_id,
        future_revision_observation_id=future_revision_id,
    )
    insufficient = _run_legal_fit_world(
        "insufficient",
        baseline_catalog,
        system,
        candidate_keys=(SampleKey(ORIGIN),),
        current_time=fit_current_time,
        policy=fit_policy,
        fit_when_ready=True,
    )
    return (baseline, future, released, before, predictor, label, revision, insufficient)


def _run_legal_fit_world(  # noqa: PLR0913
    intervention: str,
    catalog: DataCatalogSnapshot,
    definition: PredictiveSystemDefinition,
    *,
    candidate_keys: tuple[SampleKey, ...],
    current_time: datetime,
    policy: TrainingWindowPolicy,
    fit_when_ready: bool,
    poison_observation_id: str | None = None,
    original_revision_observation_id: str | None = None,
    future_revision_observation_id: str | None = None,
) -> LegalFitWorldTrace:
    predictor_fields = tuple(
        dict.fromkeys(
            field for feature in definition.feature_set.members for field in feature.dependencies
        )
    )
    information = InformationSetBuilder().build(
        catalog,
        decision_time=current_time,
        requested_fields=predictor_fields,
    )
    sample = TrainingSampleBuilder().build(
        catalog,
        target=definition.target,
        predictor_fields=predictor_fields,
        candidate_sample_keys=candidate_keys,
        current_time=current_time,
        missingness_policy=MissingnessPolicy.EXCLUDE_EXAMPLE,
    )
    window = TrainingWindowSelector().select(sample, policy)
    fit_calls = 0
    fitted: FittedPredictiveSystem | None = None
    if fit_when_ready and window.status is BoundaryStatus.READY:
        fit_calls += 1
        fitted = SystemTrainer().fit(definition, window)
    return LegalFitWorldTrace(
        intervention,
        catalog,
        definition,
        candidate_keys,
        MissingnessPolicy.EXCLUDE_EXAMPLE,
        policy,
        information,
        sample,
        window,
        fitted,
        fit_calls,
        poison_observation_id,
        original_revision_observation_id,
        future_revision_observation_id,
    )


def _legal_fit_rows(schema: DatasetSchema) -> tuple[ObservationInput, ...]:
    rows: list[ObservationInput] = []
    for day in range(14):
        moment = ORIGIN + DAY * day
        rows.extend(
            (
                _observation(
                    schema,
                    "x",
                    float(day),
                    moment,
                    moment,
                    f"x:{day}:v0",
                    0,
                    f"provenance:x:{day}",
                ),
                _observation(
                    schema,
                    "y",
                    float(day * 2 + 1),
                    moment,
                    moment,
                    f"y:{day}:v0",
                    0,
                    f"provenance:y:{day}",
                ),
            )
        )
    return tuple(rows)


def _observation(  # noqa: PLR0913, PLR0917
    schema: DatasetSchema,
    field_id: str,
    value: float,
    reference_time: datetime,
    available_at: datetime,
    vintage_id: str,
    revision_number: int,
    provenance_ref: str,
) -> ObservationInput:
    return ObservationInput(
        schema.field_ref(field_id),
        value,
        reference_time,
        available_at,
        vintage_id,
        revision_number,
        f"source:{field_id}",
        provenance_ref,
        f"availability:{field_id}-v1",
        (),
    )


def _register_legal_fit_catalog(
    schema: DatasetSchema,
    rows: tuple[ObservationInput, ...],
) -> DataCatalogSnapshot:
    registration = ObservationRegistrar().register(schema, rows)
    return DataCatalogSnapshot(schema.environment_id, (registration,))


def _observation_id(catalog: DataCatalogSnapshot, provenance_ref: str) -> str:
    matches = tuple(
        item.observation_id
        for item in catalog.observations
        if item.provenance_ref == provenance_ref
    )
    if len(matches) != 1:
        message = f"Expected one registered observation for {provenance_ref!r}."
        raise RuntimeError(message)
    return matches[0]


class ScientificWorkflowAdapter:
    """Execute paired promotion/rejection worlds through the registered coordinator."""

    adapter_id = "production.scientific-workflow.v1"

    def __init__(self, proposition_id: str) -> None:
        """Bind this production composition to one catalog proposition."""
        self.proposition_id = proposition_id

    def execute(self) -> ProofTrace:
        """Return exact emitted objects plus causal mutation and fail-on-fit interventions."""
        try:
            worlds = (
                _run_scientific_workflow_world("promote", threshold=0.001),
                _run_scientific_workflow_world("reject", threshold=-1.0),
            )
        except Exception as error:
            message = f"{type(error).__name__}: {error}"
            raise ProductionProofFailureError(message) from error
        return ProofTrace(
            proposition_id=self.proposition_id,
            adapter_id=self.adapter_id,
            facts=MappingProxyType({"worlds": worlds}),
        )


def _run_scientific_workflow_world(
    intervention: str,
    *,
    threshold: float,
) -> ScientificWorkflowTrace:
    world = make_toy_scientific_workflow_world(
        world_id=f"proof-{intervention}",
        promotion_mse_threshold=threshold,
    )
    rejected_mutations = _probe_workflow_authority_boundaries(world)
    authority_probe_ledger_entries = len(world.coordinator.ledger.entries())
    authority_probe_exposures = len(world.coordinator.exposures.records())
    receipt = world.coordinator.execute(
        workflow_id=world.workflow.workflow_id,
        idempotency_key=f"proof:{intervention}",
        session_id=world.initialized.session.session_id,
        episode_id=world.initialized.episode.episode_id,
    )
    issuance = world.registry.resolve(world.workflow.workflow_id)
    development = _evidence(world, receipt.development_evidence_ref, DevelopmentEvidence)
    frozen = _evidence(world, receipt.frozen_system_ref, FrozenPredictiveSystemIdentity)
    permit = _evidence(world, receipt.permit_ref, BacktestPermit)
    view = _evidence(world, receipt.view_ref, AuthorizedProtectedDataView)
    run = _evidence(world, receipt.run_ref, BacktestRun)
    report = _evidence(world, receipt.evaluation_report_ref, EvaluationReport)
    validation = _evidence(world, receipt.validation_decision_ref, ValidationDecision)
    finding = (
        _evidence(world, receipt.finding_ref, ValidatedFinding)
        if receipt.finding_ref is not None
        else None
    )
    negative = (
        _evidence(world, receipt.negative_result_ref, NegativeResult)
        if receipt.negative_result_ref is not None
        else None
    )
    rendered = (
        _evidence(world, receipt.rendered_report_ref, RenderedFindingReport)
        if receipt.rendered_report_ref is not None
        else None
    )
    mutation_rejected = False
    try:
        replace(run, status=BacktestRunStatus.COMPLETED_WITH_FAILURES)
    except ValueError:
        mutation_rejected = True
    measurement_ledger = ResearchLedger()
    with patch.object(
        SystemTrainer, "fit", side_effect=AssertionError("measurement fitted")
    ) as fit:
        measured = Evaluator(
            ledger=measurement_ledger,
            runs=world.coordinator.runs,
            clock=fixed_clock,
        ).measure(run, world.workflow.evaluation_spec)
    if measured.report_id != report.report_id:
        raise RuntimeError("Repeated pure measurement changed exact report identity.")
    if intervention == "promote" and receipt.status is not WorkflowStatus.FINDING:
        raise RuntimeError("Promotion proof world did not produce a finding.")
    if intervention == "reject" and receipt.status is not WorkflowStatus.REJECTED:
        raise RuntimeError("Rejection proof world did not retain a negative result.")
    return ScientificWorkflowTrace(
        intervention=intervention,
        workflow=world.workflow,
        issuance=issuance,
        receipt=receipt,
        development=development,
        frozen=frozen,
        permit=permit,
        view=view,
        run=run,
        report=report,
        validation=validation,
        finding=finding,
        negative=negative,
        rendered=rendered,
        ledger_entries=world.coordinator.ledger.entries(),
        exposure_count=len(world.coordinator.exposures.records()),
        poison_observation_id=world.future_poison_observation_id,
        mutation_rejected=mutation_rejected,
        measurement_fit_calls=fit.call_count,
        authority_field_names=tuple(
            name
            for name in ("governance_authority_id", "validation_authority_id")
            if hasattr(world.workflow, name)
        ),
        rejected_authority_mutations=rejected_mutations,
        authority_probe_ledger_entries=authority_probe_ledger_entries,
        authority_probe_exposures=authority_probe_exposures,
    )


def _probe_workflow_authority_boundaries(
    world: ToyScientificWorkflowWorld,
) -> tuple[str, ...]:
    """Apply the exact former authority/resource substitutions before disclosure."""
    registration = world.protected_resource_registration
    rejected: list[str] = []

    def require_rejection(name: str, operation: Callable[[], object]) -> None:
        try:
            operation()
        except (TypeError, WorkflowRegistryError):
            rejected.append(name)
        else:
            message = f"Authority mutation {name!r} unexpectedly succeeded."
            raise RuntimeError(message)

    require_rejection(
        "workflow-privileged-labels",
        lambda: replace(
            world.workflow,
            governance_authority_id="attacker-appointed-governance",
            validation_authority_id="attacker-appointed-validation",
        ),
    )
    require_rejection(
        "workflow-protected-catalog",
        lambda: replace(
            world.workflow,
            protected_catalog=DataCatalogSnapshot(
                environment_id=registration.catalog.environment_id,
                datasets=(),
            ),
            protected_resource_binding_ref="attacker-binding:changed",
        ),
    )
    require_rejection(
        "workflow-authority-capability",
        lambda: ScientificWorkflowIssuer(
            authority_id=world.registry.resolve(world.workflow.workflow_id).workflow_authority_id,
            registry=world.registry,
            issuance_capability=object(),
        ).issue(world.workflow),
    )
    require_rejection(
        "protected-resource-authority-capability",
        lambda: ProtectedResourceIssuer(
            authority_id=registration.authority_id,
            registry=world.protected_resources,
            issuance_capability=object(),
        ).issue(
            scope=registration.scope,
            resource_binding_ref=registration.resource_binding_ref,
            content_manifest=registration.content_manifest,
            catalog=registration.catalog,
        ),
    )
    require_rejection(
        "protected-binding",
        lambda: world.protected_resource_issuer.issue(
            scope=registration.scope,
            resource_binding_ref="attacker-binding:changed",
            content_manifest=registration.content_manifest,
            catalog=registration.catalog,
        ),
    )
    substituted_catalog = DataCatalogSnapshot(
        environment_id=registration.catalog.environment_id,
        datasets=(),
    )
    require_rejection(
        "protected-catalog",
        lambda: world.protected_resource_issuer.issue(
            scope=registration.scope,
            resource_binding_ref=registration.resource_binding_ref,
            content_manifest=registration.content_manifest,
            catalog=substituted_catalog,
        ),
    )
    return tuple(rejected)


def _evidence[EvidenceT](
    world: ToyScientificWorkflowWorld,
    reference: str | None,
    expected: type[EvidenceT],
) -> EvidenceT:
    if reference is None:
        message = f"Missing exact {expected.__name__} reference."
        raise RuntimeError(message)
    evidence = world.coordinator.evidence(reference)
    if not isinstance(evidence, expected):
        message = f"Evidence {reference!r} is not {expected.__name__}."
        raise TypeError(message)
    return evidence


class AuthorizedExplorationToNextActionAdapter:
    """Prove authorized exploratory meaning causally selects the next typed action."""

    proposition_id = "authorized-exploration-to-next-action"
    adapter_id = "production.runtime.authorized-exploration-causality.v1"

    def execute(self) -> ProofTrace:
        """Run low, high, and missing-meaning worlds through the real analysis path."""
        try:
            worlds = (
                _run_exploration_continuation_world("low", (1.0, 2.0, 3.0)),
                _run_exploration_continuation_world("high", (9.0, 10.0, 11.0)),
                _run_exploration_continuation_world("missing-meaning", (-1.0, 0.0, 1.0)),
            )
        except Exception as error:
            message = f"{type(error).__name__}: {error}"
            raise ProductionProofFailureError(message) from error
        return ProofTrace(
            proposition_id=self.proposition_id,
            adapter_id=self.adapter_id,
            facts=MappingProxyType({"worlds": worlds}),
        )


class ContextLossReconstructionAdapter:
    """Prove a transcript-free decision survives authoritative checkpoint rebuild."""

    proposition_id = "context-loss-reconstruction"
    adapter_id = "production.runtime.context-reconstruction-causality.v1"

    def execute(self) -> ProofTrace:
        """Compare uninterrupted and rebuilt decisions in paired question worlds."""
        try:
            worlds = (
                _run_context_reconstruction_world("question-open", question_open=True),
                _run_context_reconstruction_world("question-closed", question_open=False),
            )
        except Exception as error:
            message = f"{type(error).__name__}: {error}"
            raise ProductionProofFailureError(message) from error
        return ProofTrace(
            proposition_id=self.proposition_id,
            adapter_id=self.adapter_id,
            facts=MappingProxyType({"worlds": worlds}),
        )


class FailureToRepairedContinuationAdapter:
    """Prove bounded same-episode repair is caused by explicit failure evidence."""

    proposition_id = "failure-to-repaired-continuation"
    adapter_id = "production.runtime.failure-repair-causality.v1"

    def execute(self) -> ProofTrace:
        """Run controlled-failure and no-failure worlds through the bounded runtime."""
        try:
            worlds = (
                _run_failure_repair_world("controlled-failure"),
                _run_failure_repair_world("no-failure"),
            )
        except Exception as error:
            message = f"{type(error).__name__}: {error}"
            raise ProductionProofFailureError(message) from error
        return ProofTrace(
            proposition_id=self.proposition_id,
            adapter_id=self.adapter_id,
            facts=MappingProxyType({"worlds": worlds}),
        )


_EXPLORATION_SOURCE = (
    'values = read("development-view", "signal")\n'
    "mean = sum(values) / len(values)\n"
    'sentinel = "low" if mean < 5 else "high"\n'
    'details = {} if mean == 0 else {"mean": mean, "sentinel": sentinel}\n'
    'print("exploration-diagnostic")\n'
    'result = structured_return("computed sentinel", details)'
)


class _ExplorationDecisionProvider:
    """Stateless test instrument whose only decision input is the current packet."""

    __slots__ = ()

    def complete(self, packet: ContextPacket) -> ModelResponse:
        """Request the shared analysis, then branch only on its visible meaning."""
        if not packet.working_observations:
            return _analysis_response(
                packet,
                action_id="compute-sentinel",
                source=_EXPLORATION_SOURCE,
                field_ids=("signal",),
            )
        details = packet.working_observations[-1].payload.get("details")
        typed_details: Mapping[str, object]
        if isinstance(details, Mapping):
            typed_details = cast("Mapping[str, object]", details)
        else:
            typed_details = MappingProxyType({})
        sentinel_value = typed_details.get("sentinel")
        sentinel = sentinel_value if isinstance(sentinel_value, str) else ""
        action_id = {
            "low": "follow-low",
            "high": "follow-high",
        }.get(sentinel, "missing-analysis-meaning")
        return _analysis_response(
            packet,
            action_id=action_id,
            source=f'result = structured_return("{action_id}", {{"branch": "{action_id}"}})',
            field_ids=(),
        )


class _ReconstructionDecisionProvider:
    """Stateless checkpoint test instrument with no transcript or source-store access."""

    __slots__ = ()

    def complete(self, packet: ContextPacket) -> ModelResponse:
        """Select an exact action solely from the rebuilt unresolved-question surface."""
        action_id = (
            "investigate-open-question"
            if packet.unresolved_questions
            else "continue-without-open-question"
        )
        return _analysis_response(
            packet,
            action_id=action_id,
            source=f'result = structured_return("{action_id}", {{}})',
            field_ids=(),
        )


class _FailureRepairProvider:
    """Stateless packet-only test instrument for a bounded repair intervention."""

    __slots__ = ()

    def complete(self, packet: ContextPacket) -> ModelResponse:
        """Introduce the configured world failure, then repair only visible failure evidence."""
        if not packet.working_observations:
            should_fail = "controlled failure" in packet.mission.lower()
            action_id = "analysis-failure" if should_fail else "analysis-control"
            source = (
                'broken = 1 / 0\nresult = structured_return("unreachable", {})'
                if should_fail
                else 'result = structured_return("control succeeded", {"value": 1})'
            )
        elif packet.working_observations[-1].status is ObservationStatus.FAILED:
            action_id = "analysis-repair"
            source = 'result = structured_return("repaired", {"value": 2})'
        else:
            action_id = "analysis-no-repair"
            source = 'result = structured_return("no repair required", {"value": 1})'
        return _analysis_response(packet, action_id=action_id, source=source, field_ids=())


class _RecordingContextBuilder:
    """Verification observer around the real context builder; it changes no packet."""

    def __init__(self, builder: ContextBuilder) -> None:
        self._builder = builder
        self.packets: list[ContextPacket] = []

    def build_current_context(self, session_id: str) -> ContextPacket:
        """Record the exact production packet presented to the provider."""
        packet = self._builder.build_current_context(session_id)
        self.packets.append(packet)
        return packet


def _run_exploration_continuation_world(
    intervention: str,
    values: tuple[float, ...],
) -> ExplorationContinuationWorldTrace:
    first_provider = _ExplorationDecisionProvider()
    runtime, store, initialized, artifacts = _exploration_runtime_fixture(
        f"exploration-{intervention}",
        first_provider,
        values=values,
        objective="Compute the authorized exploratory sentinel.",
    )
    first = runtime.advance_one_turn(initialized.session.session_id)
    if first.observation is None:
        raise RuntimeError("Exploratory analysis did not produce an observation.")
    decision_packet = ContextBuilder(store).build_current_context(initialized.session.session_id)
    second_provider = _ExplorationDecisionProvider()
    second_runtime = _runtime_from_fixture(store, second_provider, artifacts, values)
    second = second_runtime.advance_one_turn(initialized.session.session_id)
    _, _, _, state, episode = store.coherent_view(initialized.session.session_id)
    return ExplorationContinuationWorldTrace(
        intervention=intervention,
        source=_EXPLORATION_SOURCE,
        first_observation=first.observation,
        decision_packet=decision_packet,
        second_turn=second,
        state=state,
        episode=episode,
        artifacts=_artifact_traces(first.observation, store, artifacts),
        event_types=tuple(
            event.event_type for event in store.events_for(initialized.session.session_id)
        ),
        provider_state_fields=tuple(getattr(second_provider, "__slots__", ())),
    )


def _run_context_reconstruction_world(
    intervention: str,
    *,
    question_open: bool,
) -> ContextReconstructionWorldTrace:
    provider = _ExplorationDecisionProvider()
    runtime, store, initialized, artifacts = _exploration_runtime_fixture(
        f"context-{intervention}",
        provider,
        values=(1.0, 2.0, 3.0),
        objective="Preserve exact working meaning across context reconstruction.",
        target_field_id=None if question_open else "value",
    )
    first = runtime.advance_one_turn(initialized.session.session_id)
    if first.observation is None:
        raise RuntimeError("Context proof analysis did not produce an observation.")
    builder = ContextBuilder(store)
    checkpoint = builder.checkpoint_current_episode(initialized.session.session_id)
    uninterrupted = builder.build_current_context(initialized.session.session_id)
    store.append_event(
        initialized.session.session_id,
        "provider.transcript-discarded",
        {"all": True},
    )
    uninterrupted_provider = _ReconstructionDecisionProvider()
    uninterrupted_action = decode_action(uninterrupted_provider.complete(uninterrupted))
    rebuilt = builder.rebuild_from_checkpoint(
        initialized.session.session_id,
        checkpoint.checkpoint_id,
    )
    rebuilt_provider = _ReconstructionDecisionProvider()
    rebuilt_action = decode_action(rebuilt_provider.complete(rebuilt))
    return ContextReconstructionWorldTrace(
        intervention=intervention,
        checkpoint=checkpoint,
        uninterrupted_packet=uninterrupted,
        rebuilt_packet=rebuilt,
        uninterrupted_action_kind=_action_kind(uninterrupted_action),
        uninterrupted_action_id=uninterrupted_action.action_id,
        rebuilt_action_kind=_action_kind(rebuilt_action),
        rebuilt_action_id=rebuilt_action.action_id,
        observation=first.observation,
        artifacts=_artifact_traces(first.observation, store, artifacts),
        event_types=tuple(
            event.event_type for event in store.events_for(initialized.session.session_id)
        ),
        provider_state_fields=tuple(getattr(rebuilt_provider, "__slots__", ())),
    )


def _run_failure_repair_world(intervention: str) -> FailureRepairWorldTrace:
    provider = _FailureRepairProvider()
    objective = (
        "Execute one controlled failure and repair it from structured evidence."
        if intervention == "controlled-failure"
        else "Execute the no-failure causal control."
    )
    store, initialized, artifacts, harness = _exploration_fixture_state(
        f"repair-{intervention}",
        values=(1.0, 2.0, 3.0),
        objective=objective,
    )
    recording_builder = _RecordingContextBuilder(ContextBuilder(store))
    runtime = AutonomousResearchRuntime(
        store,
        provider,
        recording_builder,  # type: ignore[arg-type] -- exact observer wrapper
        ActionRouter(
            store,
            DatasetRepository((_dataset(3),)),
            analysis_harnesses={initialized.session.session_id: harness},
        ),
        CommitCoordinator(store),
    )
    result = runtime.run_until_terminal(initialized.session.session_id, max_turns=2)
    _, _, _, state, episode = store.coherent_view(initialized.session.session_id)
    observations = tuple(turn.observation for turn in result.turns if turn.observation is not None)
    artifact_traces = tuple(
        trace
        for observation in observations
        for trace in _artifact_traces(observation, store, artifacts)
    )
    return FailureRepairWorldTrace(
        intervention=intervention,
        turns=result.turns,
        decision_packets=tuple(recording_builder.packets),
        state=state,
        episode=episode,
        artifacts=artifact_traces,
        event_types=tuple(
            event.event_type for event in store.events_for(initialized.session.session_id)
        ),
        provider_state_fields=tuple(getattr(provider, "__slots__", ())),
    )


def _analysis_response(
    packet: ContextPacket,
    *,
    action_id: str,
    source: str,
    field_ids: tuple[str, ...],
) -> ModelResponse:
    data_access = (
        [{"view_id": "development-view", "field_ids": list(field_ids)}] if field_ids else []
    )
    return ModelResponse(
        message="verification packet-only action",
        action={
            "kind": "run_analysis",
            "action_id": action_id,
            "session_id": packet.session_id,
            "episode_id": packet.episode_id,
            "arguments": {
                "source": source,
                "data_access": data_access,
                "random_seed": 17,
            },
        },
        provider_metadata={},
    )


def _action_kind(action: object) -> str:
    return "run_analysis" if isinstance(action, RunAnalysisAction) else type(action).__name__


def _exploration_runtime_fixture(
    world: str,
    provider: ModelProvider,
    *,
    values: tuple[float, ...],
    objective: str,
    target_field_id: str | None = "value",
) -> tuple[AutonomousResearchRuntime, InMemoryRuntimeStore, RuntimeInitialization, ArtifactStore]:
    store, initialized, artifacts, harness = _exploration_fixture_state(
        world,
        values=values,
        objective=objective,
        target_field_id=target_field_id,
    )
    runtime = AutonomousResearchRuntime(
        store,
        provider,
        ContextBuilder(store),
        ActionRouter(
            store,
            DatasetRepository((_dataset(3),)),
            analysis_harnesses={initialized.session.session_id: harness},
        ),
        CommitCoordinator(store),
    )
    return runtime, store, initialized, artifacts


def _runtime_from_fixture(
    store: InMemoryRuntimeStore,
    provider: ModelProvider,
    artifacts: ArtifactStore,
    values: tuple[float, ...],
) -> AutonomousResearchRuntime:
    _, environment, session, _, _ = store.coherent_view(next(iter(store.sessions)))
    harness = AnalysisHarness(
        views={
            "development-view": ExploratoryDataView(
                "development-view",
                "proof-dataset",
                environment.snapshot_ref,
                {"signal": values},
            )
        },
        policy=CapabilityPolicy(
            session.session_id,
            environment.snapshot_ref,
            {"development-view": frozenset({"signal"})},
        ),
        artifacts=artifacts,
    )
    return AutonomousResearchRuntime(
        store,
        provider,
        ContextBuilder(store),
        ActionRouter(
            store,
            DatasetRepository((_dataset(3),)),
            analysis_harnesses={session.session_id: harness},
        ),
        CommitCoordinator(store),
    )


def _exploration_fixture_state(
    world: str,
    *,
    values: tuple[float, ...],
    objective: str,
    target_field_id: str | None = "value",
) -> tuple[InMemoryRuntimeStore, RuntimeInitialization, ArtifactStore, AnalysisHarness]:
    environment = ResearchEnvironmentSnapshot(
        environment_id="proof-environment",
        version=1,
        dataset_refs=("proof-dataset",),
        readable_dataset_refs=("proof-dataset",),
        capability_names=("inspect_dataset", "run_analysis"),
    )
    proposal = (
        TaskCompiler()
        .compile(
            UserMandate(
                original_text=objective,
                research_objective=objective,
                target_field_id=target_field_id,
                forecast_horizon=TemporalOffset.elapsed(timedelta(days=1)),
                dataset_refs=("proof-dataset",),
            ),
            ResearchEnvironmentSummary(
                environment_id="proof-environment",
                available_field_ids=("value",),
                available_dataset_refs=("proof-dataset",),
            ),
        )
        .proposal
    )
    if proposal is None:
        raise RuntimeError("Exploration proof task proposal did not compile.")
    published = TaskPublisher().confirm(
        proposal,
        TaskConfirmation(
            confirmation_id=f"confirmation:{world}",
            proposal_id=proposal.proposal_id,
            proposal_version=proposal.version,
            semantic_digest=proposal.semantic_digest,
            approved=True,
        ),
    )
    if published.task is None:
        raise RuntimeError("Exploration proof task was not confirmed.")
    store = InMemoryRuntimeStore()
    initialized = ResearchRuntimeInitializer(store).initialize(
        published.task,
        environment,
        request_id=f"initialize:{world}",
    )
    artifacts = ArtifactStore()
    view = ExploratoryDataView(
        "development-view",
        "proof-dataset",
        environment.snapshot_ref,
        {"signal": values},
    )
    harness = AnalysisHarness(
        views={view.view_id: view},
        policy=CapabilityPolicy(
            initialized.session.session_id,
            environment.snapshot_ref,
            {view.view_id: frozenset({"signal"})},
        ),
        artifacts=artifacts,
    )
    return store, initialized, artifacts, harness


def _artifact_traces(
    observation: StructuredObservation,
    store: InMemoryRuntimeStore,
    artifacts: ArtifactStore,
) -> tuple[ArtifactTrace, ...]:
    runtime_refs = observation.artifact_refs
    traces: list[ArtifactTrace] = []
    for runtime_ref in runtime_refs:
        stored = store.artifacts.get(runtime_ref)
        if not isinstance(stored, ArtifactRef):
            raise TypeError("Runtime analysis artifact did not resolve to an ArtifactRef.")
        content = artifacts.read(stored, session_id=observation.session_id)
        traces.append(ArtifactTrace(runtime_ref, stored, content))
    return tuple(traces)


class ObservationToNextActionAdapter:
    """Record raw production traces for observation-driven continuation."""

    proposition_id = "observation-to-next-action"
    adapter_id = "production.runtime.observation-causality.v2"

    def execute(self) -> ProofTrace:
        """Run large, small, and missing-payload worlds through fresh stateless providers."""
        try:
            worlds = (
                _run_observation_world("large", 18),
                _run_observation_world("small", 2),
                _run_observation_world("missing-payload", 7, remove_row_count=True),
            )
        except Exception as error:
            message = f"{type(error).__name__}: {error}"
            raise ProductionProofFailureError(message) from error
        return ProofTrace(
            proposition_id=self.proposition_id,
            adapter_id=self.adapter_id,
            facts=MappingProxyType({"worlds": worlds}),
        )


class _ObservationProvider:
    """Stateless packet-only fixture policy; a fresh instance handles every decision."""

    __slots__ = ()

    def complete(self, packet: ContextPacket) -> ModelResponse:
        """Choose solely from the complete visible packet passed to this call."""
        if not packet.working_observations:
            return _inspection_response(packet, preview_limit=1, action_id="inspect-initial")
        row_count = packet.working_observations[-1].payload.get("row_count")
        if row_count == 18:
            return _inspection_response(packet, preview_limit=1, action_id="inspect-follow-up")
        if row_count == 2:
            evidence_ref = packet.working_observations[-1].observation_id
            return ModelResponse(
                message="Resolve the small-data branch.",
                action={
                    "kind": "propose_episode_transition",
                    "action_id": "resolve-small",
                    "session_id": packet.session_id,
                    "episode_id": packet.episode_id,
                    "arguments": {
                        "target_status": "resolved",
                        "synthesis": "The bounded dataset is too small for further inspection.",
                        "evidence_refs": [evidence_ref],
                        "state_update": None,
                        "idempotency_key": "resolve-small",
                    },
                },
                provider_metadata={},
            )
        return ModelResponse(
            message="The required observation meaning is absent.",
            action={
                "kind": "run_analysis",
                "action_id": "missing-row-count",
                "session_id": packet.session_id,
                "episode_id": packet.episode_id,
                "arguments": {
                    "source": 'result = structured_return("missing", {})',
                    "data_access": [],
                    "random_seed": None,
                },
            },
            provider_metadata={},
        )


def _inspection_response(
    packet: ContextPacket,
    *,
    preview_limit: int,
    action_id: str,
) -> ModelResponse:
    return ModelResponse(
        message="Inspect the authorized dataset.",
        action={
            "kind": "inspect_dataset",
            "action_id": action_id,
            "session_id": packet.session_id,
            "episode_id": packet.episode_id,
            "arguments": {
                "dataset_ref": "proof-dataset",
                "selected_field_ids": ["reference_time", "value"],
                "preview_limit": preview_limit,
            },
        },
        provider_metadata={},
    )


def _run_observation_world(
    intervention: str,
    row_count: int,
    *,
    remove_row_count: bool = False,
) -> ObservationWorldTrace:
    store, initialized = _initialized_runtime(f"observation-{intervention}")
    datasets = DatasetRepository((_dataset(row_count),))
    first_provider = _ObservationProvider()
    first_runtime = AutonomousResearchRuntime(
        store,
        first_provider,
        ContextBuilder(store),
        ActionRouter(store, datasets),
        CommitCoordinator(store),
    )
    first = first_runtime.advance_one_turn(initialized.session.session_id)
    if first.observation is None:
        raise RuntimeError("Inspection did not produce a structured observation.")
    if remove_row_count:
        stored = store.observations[first.observation.observation_id]
        payload = dict(stored.payload)
        payload.pop("row_count", None)
        store.observations[stored.observation_id] = replace(stored, payload=payload)

    packet = ContextBuilder(store).build_current_context(initialized.session.session_id)
    context_row_count = packet.working_observations[-1].payload.get("row_count")
    if context_row_count is not None and not isinstance(context_row_count, int):
        raise TypeError("row_count trace fact must be an integer or absent")
    _, _, _, state, _ = store.coherent_view(initialized.session.session_id)

    second_provider = _ObservationProvider()
    second_runtime = AutonomousResearchRuntime(
        store,
        second_provider,
        ContextBuilder(store),
        ActionRouter(store, datasets),
        CommitCoordinator(store),
    )
    second = second_runtime.advance_one_turn(initialized.session.session_id)
    event_types = tuple(
        event.event_type for event in store.events_for(initialized.session.session_id)
    )
    return ObservationWorldTrace(
        intervention=intervention,
        context_row_count=context_row_count,
        second_action_kind=second.action_kind or "",
        second_action_id=_last_requested_action_id(store, initialized.session.session_id),
        state_version_after_observation=state.version,
        event_types=event_types,
        provider_replaced_before_decision=first_provider is not second_provider,
        provider_state_fields=tuple(getattr(second_provider, "__slots__", ())),
    )


def _last_requested_action_id(store: InMemoryRuntimeStore, session_id: str) -> str:
    requested = tuple(
        event for event in store.events_for(session_id) if event.event_type == "action.requested"
    )
    if not requested:
        return ""
    action_id = requested[-1].detail.get("action_id")
    return action_id if isinstance(action_id, str) else ""


def _dataset(row_count: int) -> DatasetDefinition:
    rows: tuple[Mapping[str, object], ...] = tuple(
        {"reference_time": f"2025-{index + 1:02d}-01", "value": float(index)}
        for index in range(row_count)
    )
    return DatasetDefinition(
        dataset_ref="proof-dataset",
        version=f"rows-{row_count}",
        field_semantics={"reference_time": "Reference time.", "value": "Synthetic value."},
        rows=rows,
    )


def _initialized_runtime(world: str) -> tuple[InMemoryRuntimeStore, RuntimeInitialization]:
    environment = ResearchEnvironmentSnapshot(
        environment_id="proof-environment",
        version=1,
        dataset_refs=("proof-dataset",),
        readable_dataset_refs=("proof-dataset",),
        capability_names=("inspect_dataset",),
    )
    proposal = (
        TaskCompiler()
        .compile(
            UserMandate(
                original_text="Inspect the proof dataset.",
                research_objective="Inspect the authorized proof dataset.",
                target_field_id="value",
                forecast_horizon=TemporalOffset.elapsed(timedelta(days=1)),
                dataset_refs=("proof-dataset",),
            ),
            ResearchEnvironmentSummary(
                environment_id="proof-environment",
                available_field_ids=("value",),
                available_dataset_refs=("proof-dataset",),
            ),
        )
        .proposal
    )
    if proposal is None:
        raise RuntimeError("Proof task proposal did not compile.")
    published = TaskPublisher().confirm(
        proposal,
        TaskConfirmation(
            confirmation_id=f"confirmation:{world}",
            proposal_id=proposal.proposal_id,
            proposal_version=proposal.version,
            semantic_digest=proposal.semantic_digest,
            approved=True,
        ),
    )
    if published.task is None:
        raise RuntimeError("Proof task was not confirmed.")
    store = InMemoryRuntimeStore()
    initialized = ResearchRuntimeInitializer(store).initialize(
        published.task,
        environment,
        request_id=f"initialize:{world}",
    )
    return store, initialized


__all__ = [
    "AtomicSemanticCommitAdapter",
    "AuthorizedExplorationToNextActionAdapter",
    "ContextLossReconstructionAdapter",
    "FailureToRepairedContinuationAdapter",
    "LegalFitCompositionAdapter",
    "ObservationToNextActionAdapter",
    "ScientificWorkflowAdapter",
    "production_proof_registry",
]
