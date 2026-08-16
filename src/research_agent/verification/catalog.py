"""Architecture-derived verification catalog shared by executable evaluators."""

# ruff: noqa: C901, PLR0911, PLR2004

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, cast

from research_agent.runtime.models import EpisodeStatus, FailureCode

if TYPE_CHECKING:
    from collections.abc import Mapping

    from research_agent.data_foundation import (
        DataCatalogSnapshot,
        InformationSet,
        MissingnessPolicy,
        RegisteredObservation,
        SampleKey,
        TrainingSample,
        TrainingWindow,
        TrainingWindowPolicy,
    )
    from research_agent.development import DevelopmentEvidence, FittedPredictiveSystem
    from research_agent.exploration import ArtifactRef
    from research_agent.formalization import PredictiveSystemDefinition
    from research_agent.protected_evaluation import (
        AuthorizedProtectedDataView,
        BacktestPermit,
        BacktestRun,
        EvaluationReport,
        FrozenPredictiveSystemIdentity,
        LedgerEntry,
        NegativeResult,
        ValidatedFinding,
        ValidationDecision,
    )
    from research_agent.reporting import RenderedFindingReport
    from research_agent.runtime.commit import CommitRequest, CommitResult
    from research_agent.runtime.engine import TurnResult
    from research_agent.runtime.models import (
        ContextPacket,
        EpisodeCheckpoint,
        ResearchEpisode,
        ResearcherState,
        StructuredObservation,
        TrajectoryEvent,
    )
    from research_agent.scientific_workflow import (
        RegisteredScientificWorkflow,
        ScientificWorkflowIssuance,
        WorkflowReceipt,
    )

LARGE_WORLD_ROW_COUNT = 18
SMALL_WORLD_ROW_COUNT = 2
INDEPENDENT_DECISION_AUTHORITY_COUNT = 3


@dataclass(frozen=True, slots=True)
class Proposition:
    """One deterministic composition and the evidence required to prove it."""

    id: str
    name: str
    seams: tuple[str, ...]
    invariants: tuple[str, ...]
    required_evidence: tuple[str, ...]
    expected_components: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ObservationWorldTrace:
    """Raw externally observed facts from one production observation world."""

    intervention: str
    context_row_count: int | None
    second_action_kind: str
    second_action_id: str
    state_version_after_observation: int
    event_types: tuple[str, ...]
    provider_replaced_before_decision: bool
    provider_state_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ArtifactTrace:
    """One runtime reference resolved through the session-scoped artifact authority."""

    runtime_ref: str
    artifact_ref: ArtifactRef
    content: bytes


@dataclass(frozen=True, slots=True)
class ExplorationContinuationWorldTrace:
    """Raw facts from one authorized exploratory-analysis continuation world."""

    intervention: str
    source: str
    first_observation: StructuredObservation
    decision_packet: ContextPacket
    second_turn: TurnResult
    state: ResearcherState
    episode: ResearchEpisode
    artifacts: tuple[ArtifactTrace, ...]
    event_types: tuple[str, ...]
    provider_state_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ContextReconstructionWorldTrace:
    """Raw checkpoint, rebuilt packet, and deterministic decision facts."""

    intervention: str
    checkpoint: EpisodeCheckpoint
    uninterrupted_packet: ContextPacket
    rebuilt_packet: ContextPacket
    uninterrupted_action_kind: str
    uninterrupted_action_id: str
    rebuilt_action_kind: str
    rebuilt_action_id: str
    observation: StructuredObservation
    artifacts: tuple[ArtifactTrace, ...]
    event_types: tuple[str, ...]
    provider_state_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FailureRepairWorldTrace:
    """Raw bounded episode trace for failure and no-failure paired worlds."""

    intervention: str
    turns: tuple[TurnResult, ...]
    decision_packets: tuple[ContextPacket, ...]
    state: ResearcherState
    episode: ResearchEpisode
    artifacts: tuple[ArtifactTrace, ...]
    event_types: tuple[str, ...]
    provider_state_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LearningWorldTrace:
    """Raw facts from scoped validated-learning interventions."""

    baseline_action: str
    applicable_action: str
    out_of_scope_action: str
    denied_actor_action: str
    applicable_entry_count: int
    out_of_scope_entry_count: int
    denied_actor_entry_count: int
    lesson_content_visible: bool
    caveats_visible: bool
    provenance_visible: bool
    rejection_preserved: bool
    rejected_entry_count: int
    packet_only_policy_state_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AtomicCommitWorldTrace:
    """Raw authoritative state observed around one semantic-commit intervention."""

    intervention: str
    observation: StructuredObservation
    request: CommitRequest
    events_before: tuple[TrajectoryEvent, ...]
    initial_state: ResearcherState
    initial_episode: ResearchEpisode
    result: CommitResult | None
    failure_type: str | None
    state_after_attempt: ResearcherState
    episode_after_attempt: ResearchEpisode
    commit_count_after_attempt: int
    events_after_attempt: tuple[TrajectoryEvent, ...]
    retry_result: CommitResult | None
    changed_request: CommitRequest | None
    conflict_result: CommitResult | None
    final_state: ResearcherState
    final_episode: ResearchEpisode
    final_commit_count: int
    final_events: tuple[TrajectoryEvent, ...]


@dataclass(frozen=True, slots=True)
class LegalFitWorldTrace:
    """Raw registered-data, legal-view, sample, window, and fit objects for one intervention."""

    intervention: str
    catalog: DataCatalogSnapshot
    definition: PredictiveSystemDefinition
    candidate_keys: tuple[SampleKey, ...]
    missingness_policy: MissingnessPolicy
    policy: TrainingWindowPolicy
    information: InformationSet
    sample: TrainingSample
    window: TrainingWindow
    fitted: FittedPredictiveSystem | None
    fit_calls: int
    poison_observation_id: str | None
    original_revision_observation_id: str | None
    future_revision_observation_id: str | None


@dataclass(frozen=True, slots=True)
class CatalogValidation:
    """Catalog-owned interpretation of raw production trace facts."""

    production_components: tuple[str, ...]
    assertions: Mapping[str, bool]


@dataclass(frozen=True, slots=True)
class ScientificWorkflowTrace:
    """Raw exact objects and interventions observed from one workflow execution world."""

    intervention: str
    workflow: RegisteredScientificWorkflow
    issuance: ScientificWorkflowIssuance
    receipt: WorkflowReceipt
    development: DevelopmentEvidence
    frozen: FrozenPredictiveSystemIdentity
    permit: BacktestPermit
    view: AuthorizedProtectedDataView
    run: BacktestRun
    report: EvaluationReport
    validation: ValidationDecision
    finding: ValidatedFinding | None
    negative: NegativeResult | None
    rendered: RenderedFindingReport | None
    ledger_entries: tuple[LedgerEntry, ...]
    exposure_count: int
    poison_observation_id: str
    mutation_rejected: bool
    measurement_fit_calls: int
    authority_field_names: tuple[str, ...]
    rejected_authority_mutations: tuple[str, ...]
    authority_probe_ledger_entries: int
    authority_probe_exposures: int


COMPOSITES = (
    Proposition(
        "observation-to-next-action",
        "observation-to-action",
        (
            "observation.assemble-authoritative-result",
            "runtime.continue-from-observation",
            "context.build-packet",
            "action.decode-intent",
        ),
        ("I9", "I14", "I20"),
        (
            "paired_observation_meaning_reached_context",
            "same_provider_selected_distinct_typed_actions",
            "observation_did_not_mutate_durable_state",
            "decision_used_no_transcript_or_source_store",
            "missing_payload_selected_sentinel_action",
        ),
        (
            "ActionRouter.execute_inspection",
            "InMemoryRuntimeStore.record_observation",
            "ContextBuilder.build_current_context",
            "AutonomousResearchRuntime.advance_one_turn",
            "decode_action",
        ),
    ),
    Proposition(
        "evidence-to-atomic-commit",
        "atomic-semantic-commit",
        ("commit.compose-request", "trajectory.append-event"),
        ("I9", "I11", "I25"),
        (
            "valid_evidence_published_both_effects",
            "foreign_evidence_published_neither_effect",
            "injected_failure_published_neither_effect",
            "exact_replay_did_not_duplicate_effects",
        ),
        (
            "ActionRouter.execute_inspection",
            "InMemoryRuntimeStore.record_observation",
            "EpisodeTransitionValidator.validate",
            "StateUpdateValidator.validate",
            "CommitCoordinator.commit",
            "InMemoryRuntimeStore.publish_semantic_commit",
            "InMemoryRuntimeStore.events_for",
        ),
    ),
    Proposition(
        "registered-data-to-legal-fit",
        "legal-data-to-fit",
        ("data.register-observations", "data.prove-temporal-substrate", "training.fit-system"),
        ("I1", "I2", "I23", "I26"),
        ("independent_clocks_propagated", "fit_consumed_only_legal_samples"),
        (
            "ObservationRegistrar.register",
            "InformationSetBuilder.build",
            "TrainingSampleBuilder.build",
            "TrainingWindowSelector.select",
            "SystemTrainer.fit",
        ),
    ),
    Proposition(
        "feature-identity-to-prediction",
        "feature-identity-to-prediction",
        ("feature.define-identity", "prediction.generate-record"),
        ("I2", "I3", "I5"),
        ("exact_identity_propagated", "prediction_performed_no_learning"),
    ),
    Proposition(
        "exploration-to-development-evidence",
        "exploration-to-development-evidence",
        ("sandbox.authorize-execution", "ledger.record-trial-lineage"),
        ("I6", "I12", "I18"),
        ("exploration_explicitly_formalized", "losing_trial_retained"),
    ),
    Proposition(
        "development-to-protected-authority",
        "development-to-protected-authority",
        ("freeze.assess-eligibility", "backtest.bind-protected-view"),
        ("I4", "I8", "I14"),
        (
            "development_evidence_bound",
            "independent_authorities_resolved",
            "protected_scope_bound_before_read",
            "authority_mutations_rejected_before_disclosure",
        ),
        (
            "DevelopmentEvaluator.evaluate",
            "FreezeGate.assess",
            "FreezeGate.seal",
            "BacktestGovernance.authorize",
            "ProtectedViewBinder.bind",
            "ScientificWorkflowCoordinator.execute",
        ),
    ),
    Proposition(
        "frozen-system-to-immutable-run",
        "frozen-system-to-run",
        ("backtest.bind-protected-view", "backtest.seal-run"),
        ("I1", "I4", "I11", "I21"),
        ("frozen_identity_executed", "immutable_run_sealed"),
        (
            "WorkflowRegistry.get",
            "BacktestEngine.execute",
            "ScientificWorkflowCoordinator.execute",
        ),
    ),
    Proposition(
        "run-to-finding-or-rejection",
        "run-to-finding-or-rejection",
        ("evaluation.measure-run", "ledger.preserve-scientific-history"),
        ("I8", "I11", "I21"),
        ("run_measured_without_fit", "finding_or_rejection_retained"),
        (
            "Evaluator.measure",
            "Validator.validate",
            "FindingPublisher.publish",
            "ScientificWorkflowCoordinator.execute",
        ),
    ),
    Proposition(
        "exposure-to-descendant-governance",
        "exposure-to-descendant-governance",
        (
            "formalization.version-material-change",
            "exposure.record-disclosure",
            "ledger.preserve-scientific-history",
        ),
        ("I7", "I22"),
        ("exposure_reached_descendant", "descendant_freshness_denied"),
    ),
    Proposition(
        "authorized-exploration-to-next-action",
        "exploration-to-next-action",
        ("sandbox.authorize-execution", "research.continue-from-exploration"),
        ("I14", "I18"),
        ("authorized_analysis_executed", "analysis_meaning_changed_next_action"),
        (
            "AnalysisHarness.run",
            "ActionRouter.execute_analysis",
            "InMemoryRuntimeStore.record_observation",
            "ContextBuilder.build_current_context",
            "AutonomousResearchRuntime.advance_one_turn",
            "decode_action",
        ),
    ),
    Proposition(
        "context-loss-reconstruction",
        "context-loss-reconstruction",
        ("context.checkpoint-episode", "evaluation.grade-research-behavior"),
        ("I15", "I16", "I20"),
        ("checkpoint_preserved_meaning", "rebuilt_action_was_equivalent"),
        (
            "ContextBuilder.checkpoint_current_episode",
            "InMemoryRuntimeStore.publish_checkpoint",
            "ContextBuilder.rebuild_from_checkpoint",
            "decode_action",
        ),
    ),
    Proposition(
        "failure-to-repaired-continuation",
        "failure-to-repaired-continuation",
        (
            "runtime.return-repairable-failure",
            "research.repair-exploratory-action",
            "runtime.run-bounded-episode",
        ),
        ("I9", "I17", "I25"),
        (
            "failure_was_explicit_and_repairable",
            "same_episode_executed_corrected_action",
            "failure_history_remained_visible",
            "repair_created_no_durable_belief",
        ),
        (
            "AnalysisHarness.run",
            "ActionRouter.execute_analysis",
            "InMemoryRuntimeStore.record_observation",
            "ContextBuilder.build_current_context",
            "AutonomousResearchRuntime.run_until_terminal",
        ),
    ),
    Proposition(
        "privileged-retry-idempotency",
        "privileged-retry-idempotency",
        ("backtest.authorize-request", "governance.retry-privileged-operation"),
        ("I7", "I25"),
        (
            "independent_authority_enforced",
            "exact_retry_reused_original_decision",
            "changed_semantics_conflicted_before_effect",
            "permit_remained_exactly_scope_bound",
        ),
    ),
    Proposition(
        "finding-to-report-invariance",
        "finding-to-report-invariance",
        ("finding.publish-validated-claim", "report.render-finding"),
        ("I13", "I19"),
        ("scientific_substance_preserved",),
        (
            "CanonicalReportRegistry.register",
            "ReportBuilder.render",
            "ScientificWorkflowCoordinator.execute",
        ),
    ),
    Proposition(
        "validated-learning-to-future-behavior",
        "validated-learning-to-behavior",
        ("learning.reflect-history", "learning.influence-future-research"),
        ("I8", "I13", "I16"),
        ("validated_scoped_lesson_reached_context", "lesson_changed_only_applicable_behavior"),
    ),
)

COMPOSITES_BY_ID = {item.id: item for item in COMPOSITES}


def validate_production_trace(
    proposition: Proposition,
    facts: Mapping[str, object],
) -> CatalogValidation | None:
    """Interpret raw facts only where the catalog has an implemented exact oracle."""
    if proposition.id == "evidence-to-atomic-commit":
        return _validate_atomic_commit_trace(proposition, facts)
    if proposition.id == "registered-data-to-legal-fit":
        return _validate_legal_fit_trace(proposition, facts)
    if proposition.id == "authorized-exploration-to-next-action":
        return _validate_exploration_continuation_trace(proposition, facts)
    if proposition.id == "context-loss-reconstruction":
        return _validate_context_reconstruction_trace(proposition, facts)
    if proposition.id == "failure-to-repaired-continuation":
        return _validate_failure_repair_trace(proposition, facts)
    if proposition.id == "validated-learning-to-future-behavior":
        trace = facts.get("trace")
        if not isinstance(trace, LearningWorldTrace):
            return None
        assertions = MappingProxyType(
            {
                "validated_scoped_lesson_reached_context": (
                    trace.applicable_entry_count == 1
                    and trace.lesson_content_visible
                    and trace.caveats_visible
                    and trace.provenance_visible
                    and trace.applicable_action != trace.baseline_action
                ),
                "lesson_changed_only_applicable_behavior": (
                    trace.out_of_scope_entry_count == 0
                    and trace.denied_actor_entry_count == 0
                    and trace.out_of_scope_action == trace.baseline_action
                    and trace.denied_actor_action == trace.baseline_action
                    and trace.rejection_preserved
                    and trace.rejected_entry_count == 0
                    and not trace.packet_only_policy_state_fields
                ),
            }
        )
        return CatalogValidation(proposition.expected_components, assertions)
    if proposition.id in {
        "development-to-protected-authority",
        "frozen-system-to-immutable-run",
        "run-to-finding-or-rejection",
        "finding-to-report-invariance",
    }:
        return _validate_scientific_workflow_trace(proposition, facts)
    if proposition.id != "observation-to-next-action":
        return None
    worlds_value = facts.get("worlds")
    if not isinstance(worlds_value, tuple):
        return None
    world_objects = cast("tuple[object, ...]", worlds_value)
    if not all(isinstance(world, ObservationWorldTrace) for world in world_objects):
        return None
    worlds = cast("tuple[ObservationWorldTrace, ...]", worlds_value)
    by_intervention = {world.intervention: world for world in worlds}
    if set(by_intervention) != {"large", "small", "missing-payload"}:
        return None
    large = by_intervention["large"]
    small = by_intervention["small"]
    missing = by_intervention["missing-payload"]
    required_event_subsequence = (
        "model.call-started",
        "model.call-completed",
        "action.requested",
        "action.authorized",
        "capability.executed",
        "observation.assembled",
        "episode.observation-recorded",
    )
    traces_executed = all(
        _is_subsequence(required_event_subsequence, world.event_types) for world in worlds
    )
    assertions = MappingProxyType(
        {
            "paired_observation_meaning_reached_context": (
                large.context_row_count == LARGE_WORLD_ROW_COUNT
                and small.context_row_count == SMALL_WORLD_ROW_COUNT
            ),
            "same_provider_selected_distinct_typed_actions": (
                (large.second_action_kind, small.second_action_kind)
                == ("inspect_dataset", "propose_episode_transition")
            ),
            "observation_did_not_mutate_durable_state": all(
                world.state_version_after_observation == 0 for world in worlds
            ),
            "decision_used_no_transcript_or_source_store": (
                traces_executed
                and all(world.provider_replaced_before_decision for world in worlds)
                and all(not world.provider_state_fields for world in worlds)
            ),
            "missing_payload_selected_sentinel_action": (
                missing.context_row_count is None
                and missing.second_action_id == "missing-row-count"
                and missing.second_action_kind == "run_analysis"
            ),
        }
    )
    return CatalogValidation(proposition.expected_components, assertions)


def _validate_exploration_continuation_trace(
    proposition: Proposition,
    facts: Mapping[str, object],
) -> CatalogValidation | None:
    worlds = _typed_worlds(facts, ExplorationContinuationWorldTrace)
    if worlds is None:
        return None
    by_intervention = {world.intervention: world for world in worlds}
    if set(by_intervention) != {"low", "high", "missing-meaning"} or len(worlds) != 3:
        return _failed_validation(proposition)
    low = by_intervention["low"]
    high = by_intervention["high"]
    missing = by_intervention["missing-meaning"]
    all_observations = tuple(world.first_observation for world in worlds)
    all_provenance = tuple(item.provenance for item in all_observations)
    projections_match = all(
        world.decision_packet.working_observations
        and world.decision_packet.working_observations[-1].source_content_digest
        == world.first_observation.content_digest
        and world.decision_packet.working_observations[-1].provenance
        == world.first_observation.provenance
        and world.decision_packet.working_observations[-1].artifact_refs
        == world.first_observation.artifact_refs
        for world in worlds
    )
    artifacts_resolve = all(
        trace.runtime_ref in world.first_observation.artifact_refs
        and trace.runtime_ref == f"analysis-artifact:{trace.artifact_ref.artifact_id}"
        and _artifact_trace_is_valid(trace)
        for world in worlds
        for trace in world.artifacts
    ) and all(world.artifacts for world in worlds)
    actual_accesses = all(
        provenance is not None
        and provenance.capability_name == "run_analysis"
        and provenance.execution_status == "succeeded"
        and tuple(
            (
                access.ordinal,
                access.view_id,
                access.dataset_ref,
                access.environment_ref,
                access.field_id,
            )
            for access in provenance.accesses
        )
        == (
            (
                0,
                "development-view",
                "proof-dataset",
                world.first_observation.environment_ref,
                "signal",
            ),
        )
        for world, provenance in zip(worlds, all_provenance, strict=True)
    )
    required_events = (
        "action.requested",
        "action.authorized",
        "capability.executed",
        "observation.assembled",
        "episode.observation-recorded",
    )
    executed = all(_is_subsequence(required_events, world.event_types) for world in worlds)
    assertions = MappingProxyType(
        {
            "authorized_analysis_executed": (
                executed
                and actual_accesses
                and artifacts_resolve
                and projections_match
                and all(item.status.value == "succeeded" for item in all_observations)
                and all(item.epistemic_status == "EXPLORATORY" for item in all_observations)
                and all(
                    item.provenance is not None
                    and item.provenance.code_sha256
                    == hashlib.sha256(world.source.encode()).hexdigest()
                    for item, world in zip(all_observations, worlds, strict=True)
                )
            ),
            "analysis_meaning_changed_next_action": (
                low.first_observation.payload.get("details") == {"mean": 2.0, "sentinel": "low"}
                and high.first_observation.payload.get("details")
                == {"mean": 10.0, "sentinel": "high"}
                and missing.first_observation.payload.get("details") == {}
                and tuple(world.second_turn.action_kind for world in (low, high, missing))
                == ("run_analysis", "run_analysis", "run_analysis")
                and tuple(
                    world.second_turn.observation.action_id
                    if world.second_turn.observation is not None
                    else ""
                    for world in (low, high, missing)
                )
                == ("follow-low", "follow-high", "missing-analysis-meaning")
                and all(world.state.version == 0 for world in worlds)
                and all(not world.state.durable_understanding for world in worlds)
                and all(not world.provider_state_fields for world in worlds)
            ),
        }
    )
    return CatalogValidation(proposition.expected_components, assertions)


def _validate_context_reconstruction_trace(
    proposition: Proposition,
    facts: Mapping[str, object],
) -> CatalogValidation | None:
    worlds = _typed_worlds(facts, ContextReconstructionWorldTrace)
    if worlds is None:
        return None
    by_intervention = {world.intervention: world for world in worlds}
    if set(by_intervention) != {"question-open", "question-closed"} or len(worlds) != 2:
        return _failed_validation(proposition)
    opened = by_intervention["question-open"]
    closed = by_intervention["question-closed"]
    checkpoint_bound = all(
        world.checkpoint.session_id == world.uninterrupted_packet.session_id
        and world.checkpoint.task_id == world.uninterrupted_packet.task_id
        and world.checkpoint.task_version == world.uninterrupted_packet.task_version
        and world.checkpoint.state_id == world.uninterrupted_packet.state_id
        and world.checkpoint.state_version == world.uninterrupted_packet.state_version
        and world.checkpoint.episode_id == world.uninterrupted_packet.episode_id
        and world.checkpoint.environment_ref == world.uninterrupted_packet.environment_ref
        and world.checkpoint.observation_count == 1
        and world.checkpoint.observations[-1].source_content_digest
        == world.observation.content_digest
        and world.checkpoint.observations[-1].provenance == world.observation.provenance
        and world.checkpoint.observations[-1].artifact_refs == world.observation.artifact_refs
        and world.checkpoint.objective == world.uninterrupted_packet.episode_objective
        and world.checkpoint.active_question == world.uninterrupted_packet.active_question
        and world.checkpoint.current_plan == world.uninterrupted_packet.current_plan
        and world.checkpoint.unresolved_questions == world.uninterrupted_packet.unresolved_questions
        and world.checkpoint.temporary_interpretations
        == world.uninterrupted_packet.temporary_interpretations
        and world.checkpoint.permitted_dataset_refs
        == world.uninterrupted_packet.permitted_dataset_refs
        and world.checkpoint.available_actions == world.uninterrupted_packet.available_actions
        and world.checkpoint.constraints == world.uninterrupted_packet.constraints
        and world.checkpoint.unresolved_semantics == world.uninterrupted_packet.unresolved_semantics
        and world.checkpoint.protected_exposure_refs
        == world.uninterrupted_packet.protected_exposure_refs
        and world.checkpoint.protected_resource_refs
        == world.uninterrupted_packet.protected_resource_refs
        and world.uninterrupted_packet.checkpoint_ref == world.checkpoint.checkpoint_id
        and world.rebuilt_packet.checkpoint_ref == world.checkpoint.checkpoint_id
        and world.artifacts
        and all(
            item.runtime_ref in world.observation.artifact_refs and _artifact_trace_is_valid(item)
            for item in world.artifacts
        )
        for world in worlds
    )
    transcript_destroyed = all(
        "provider.transcript-discarded" in world.event_types for world in worlds
    )
    assertions = MappingProxyType(
        {
            "checkpoint_preserved_meaning": (
                checkpoint_bound
                and transcript_destroyed
                and opened.checkpoint.unresolved_questions == ("target",)
                and closed.checkpoint.unresolved_questions == ()
                and all(world.uninterrupted_packet == world.rebuilt_packet for world in worlds)
            ),
            "rebuilt_action_was_equivalent": (
                all(
                    (world.uninterrupted_action_kind, world.uninterrupted_action_id)
                    == (world.rebuilt_action_kind, world.rebuilt_action_id)
                    for world in worlds
                )
                and (opened.rebuilt_action_kind, opened.rebuilt_action_id)
                == ("run_analysis", "investigate-open-question")
                and (closed.rebuilt_action_kind, closed.rebuilt_action_id)
                == ("run_analysis", "continue-without-open-question")
                and all(not world.provider_state_fields for world in worlds)
            ),
        }
    )
    return CatalogValidation(proposition.expected_components, assertions)


def _validate_failure_repair_trace(
    proposition: Proposition,
    facts: Mapping[str, object],
) -> CatalogValidation | None:
    worlds = _typed_worlds(facts, FailureRepairWorldTrace)
    if worlds is None:
        return None
    by_intervention = {world.intervention: world for world in worlds}
    if set(by_intervention) != {"controlled-failure", "no-failure"} or len(worlds) != 2:
        return _failed_validation(proposition)
    failed = by_intervention["controlled-failure"]
    control = by_intervention["no-failure"]
    if len(failed.turns) != 2 or len(control.turns) != 2:
        return _failed_validation(proposition)
    failure = failed.turns[0].observation
    repair = failed.turns[1].observation
    control_first = control.turns[0].observation
    control_second = control.turns[1].observation
    if any(item is None for item in (failure, repair, control_first, control_second)):
        return _failed_validation(proposition)
    failure = cast("StructuredObservation", failure)
    repair = cast("StructuredObservation", repair)
    control_first = cast("StructuredObservation", control_first)
    control_second = cast("StructuredObservation", control_second)
    diagnostic = failure.failure.diagnostic_ref if failure.failure is not None else None
    traceback = next(
        (item for item in failed.artifacts if item.runtime_ref == diagnostic),
        None,
    )
    failure_visible = (
        len(failed.decision_packets) == 2
        and bool(failed.decision_packets[1].working_observations)
        and failed.decision_packets[1].working_observations[-1].source_content_digest
        == failure.content_digest
        and failed.episode.observation_ids == (failure.observation_id, repair.observation_id)
    )
    assertions = MappingProxyType(
        {
            "failure_was_explicit_and_repairable": (
                failure.status.value == "failed"
                and failure.failure is not None
                and failure.failure.recoverability.value == "repairable"
                and failure.recoverability.value == "repairable"
                and failure.provenance is not None
                and failure.provenance.execution_status == "failed"
                and failure.provenance.code_sha256 is not None
                and failure.provenance.random_seed == 17
                and failure.provenance.accesses == ()
                and diagnostic is not None
                and traceback is not None
                and traceback.artifact_ref.kind.value == "traceback"
                and _artifact_trace_is_valid(traceback)
                and b"ZeroDivisionError" in traceback.content
            ),
            "same_episode_executed_corrected_action": (
                repair.status.value == "succeeded"
                and repair.summary == "repaired"
                and repair.action_id == "analysis-repair"
                and control_first.status.value == "succeeded"
                and control_second.action_id == "analysis-no-repair"
                and failure.episode_id == repair.episode_id == failed.episode.episode_id
                and failed.turns[0].session_id == failed.turns[1].session_id
                and all(
                    packet.episode_id == failed.episode.episode_id
                    and packet.episode_objective == failed.episode.objective
                    for packet in failed.decision_packets
                )
            ),
            "failure_history_remained_visible": (
                failure_visible
                and "runtime.failure" not in failed.event_types
                and _is_subsequence(
                    (
                        "capability.executed",
                        "episode.observation-recorded",
                        "capability.executed",
                        "episode.observation-recorded",
                    ),
                    failed.event_types,
                )
            ),
            "repair_created_no_durable_belief": (
                failed.state.version == 0
                and failed.state.durable_understanding == ()
                and control.state.version == 0
                and control.state.durable_understanding == ()
                and failed.episode.status.value == "active"
                and control.episode.status.value == "active"
                and all(not world.provider_state_fields for world in worlds)
            ),
        }
    )
    return CatalogValidation(proposition.expected_components, assertions)


def _typed_worlds[WorldT](
    facts: Mapping[str, object],
    expected: type[WorldT],
) -> tuple[WorldT, ...] | None:
    value = facts.get("worlds")
    if not isinstance(value, tuple) or not all(
        isinstance(item, expected) for item in cast("tuple[object, ...]", value)
    ):
        return None
    return cast("tuple[WorldT, ...]", value)


def _failed_validation(proposition: Proposition) -> CatalogValidation:
    return CatalogValidation(
        proposition.expected_components,
        MappingProxyType(dict.fromkeys(proposition.required_evidence, False)),
    )


def _artifact_trace_is_valid(trace: ArtifactTrace) -> bool:
    return (
        trace.artifact_ref.size_bytes == len(trace.content)
        and trace.artifact_ref.sha256 == hashlib.sha256(trace.content).hexdigest()
    )


def _validate_atomic_commit_trace(
    proposition: Proposition,
    facts: Mapping[str, object],
) -> CatalogValidation | None:
    worlds_value = facts.get("worlds")
    if not isinstance(worlds_value, tuple) or not all(
        isinstance(item, AtomicCommitWorldTrace)
        for item in cast("tuple[object, ...]", worlds_value)
    ):
        return None
    worlds = cast("tuple[AtomicCommitWorldTrace, ...]", worlds_value)
    by_intervention = {world.intervention: world for world in worlds}
    stage_names = ("episode", "state", "commit", "event")
    required = {
        "authoritative-evidence",
        "foreign-evidence",
        "forged-evidence",
        "exact-replay-and-conflict",
        *(f"failure-after-{stage}" for stage in stage_names),
    }
    if set(by_intervention) != required or len(worlds) != len(required):
        return CatalogValidation(
            proposition.expected_components,
            MappingProxyType(dict.fromkeys(proposition.required_evidence, False)),
        )

    valid = by_intervention["authoritative-evidence"]
    foreign = by_intervention["foreign-evidence"]
    forged = by_intervention["forged-evidence"]
    replay = by_intervention["exact-replay-and-conflict"]
    stage_worlds = tuple(by_intervention[f"failure-after-{stage}"] for stage in stage_names)

    valid_result = valid.result
    valid_observation = _observation_content_is_exact(valid.observation)
    valid_events = _published_events(valid.final_events)
    valid_state_delta = valid.request.state_update
    valid_published = (
        valid_result is not None
        and valid_result.committed
        and not valid_result.replayed
        and valid_result.failure is None
        and valid_result.commit_id is not None
        and valid_observation
        and valid.observation.session_id == valid.request.session_id
        and valid.observation.episode_id == valid.request.episode_id
        and valid.observation.environment_ref == valid.initial_episode.environment_ref
        and valid.observation.observation_id in valid.initial_episode.observation_ids
        and valid.request.transition.evidence_refs == (valid.observation.observation_id,)
        and valid_state_delta is not None
        and valid_state_delta.evidence_refs == (valid.observation.observation_id,)
        and valid.state_after_attempt == valid.final_state
        and valid.episode_after_attempt == valid.final_episode
        and valid.final_state.version == valid.initial_state.version + 1
        and valid.final_state.durable_understanding
        == (
            *valid.initial_state.durable_understanding,
            *valid_state_delta.durable_understanding,
        )
        and valid.final_state.evidence_refs
        == (*valid.initial_state.evidence_refs, valid.observation.observation_id)
        and valid.final_episode.status is valid.request.transition.target_status
        and valid.final_episode.transition_count == valid.initial_episode.transition_count + 1
        and valid.final_episode.temporary_interpretations
        == (
            *valid.initial_episode.temporary_interpretations,
            valid.request.transition.synthesis,
        )
        and valid.commit_count_after_attempt == 1
        and valid.final_commit_count == 1
        and len(valid_events) == 1
        and valid_events[0].detail.get("commit_id") == valid_result.commit_id
        and valid_events[0].detail.get("state_version") == valid.final_state.version
        and valid_events[0].detail.get("episode_status") == valid.final_episode.status.value
    )

    foreign_result = foreign.result
    foreign_denied = (
        _world_attempt_unchanged(foreign)
        and foreign_result is not None
        and not foreign_result.committed
        and foreign_result.failure is not None
        and foreign_result.failure.code is FailureCode.INVALID_EVIDENCE_REFERENCE
        and foreign.observation.session_id != foreign.request.session_id
        and foreign.observation.observation_id not in foreign.initial_episode.observation_ids
        and foreign.commit_count_after_attempt == 0
        and not _published_events(foreign.events_after_attempt)
    )
    forged_denied = (
        _world_attempt_unchanged(forged)
        and forged.result is None
        and forged.failure_type == "RuntimeError"
        and forged.observation.observation_id in forged.initial_episode.observation_ids
        and (
            forged.observation.session_id != forged.initial_episode.session_id
            or forged.observation.environment_ref != forged.initial_episode.environment_ref
        )
        and forged.commit_count_after_attempt == 0
        and not _published_events(forged.events_after_attempt)
    )

    stage_failures_atomic = all(
        _world_attempt_unchanged(world)
        and world.failure_type == "InjectedPersistenceError"
        and world.result is None
        and world.commit_count_after_attempt == 0
        and world.events_after_attempt == world.events_before
        and not _published_events(world.events_after_attempt)
        and world.retry_result is not None
        and world.retry_result.committed
        and world.retry_result.failure is None
        and world.final_state.version == world.initial_state.version + 1
        and world.final_episode.status is world.request.transition.target_status
        and world.final_episode.transition_count == world.initial_episode.transition_count + 1
        and world.final_commit_count == 1
        and len(_published_events(world.final_events)) == 1
        for world in stage_worlds
    )

    replay_result = replay.result
    replayed_result = replay.retry_result
    conflict = replay.conflict_result
    replay_exact = (
        replay_result is not None
        and replay_result.committed
        and not replay_result.replayed
        and replayed_result is not None
        and replayed_result.committed
        and replayed_result.replayed
        and replayed_result.commit_id == replay_result.commit_id
        and replay.changed_request is not None
        and replay.changed_request.idempotency_key == replay.request.idempotency_key
        and replay.changed_request.transition.synthesis != replay.request.transition.synthesis
        and conflict is not None
        and not conflict.committed
        and conflict.failure is not None
        and conflict.failure.code is FailureCode.IDEMPOTENCY_CONFLICT
        and replay.final_state.version == replay.initial_state.version + 1
        and replay.final_episode.status is EpisodeStatus.RESOLVED
        and replay.final_episode.transition_count == replay.initial_episode.transition_count + 1
        and replay.final_commit_count == 1
        and len(_published_events(replay.final_events)) == 1
    )
    assertions = MappingProxyType(
        {
            "valid_evidence_published_both_effects": valid_published,
            "foreign_evidence_published_neither_effect": foreign_denied and forged_denied,
            "injected_failure_published_neither_effect": stage_failures_atomic,
            "exact_replay_did_not_duplicate_effects": replay_exact,
        }
    )
    return CatalogValidation(proposition.expected_components, assertions)


def _world_attempt_unchanged(world: AtomicCommitWorldTrace) -> bool:
    return (
        world.state_after_attempt == world.initial_state
        and world.episode_after_attempt == world.initial_episode
        and world.commit_count_after_attempt == 0
    )


def _published_events(events: tuple[TrajectoryEvent, ...]) -> tuple[TrajectoryEvent, ...]:
    return tuple(event for event in events if event.event_type == "commit.published")


def _observation_content_is_exact(observation: StructuredObservation) -> bool:
    try:
        observation.verify_content_identity()
    except ValueError:
        return False
    return True


def _validate_legal_fit_trace(
    proposition: Proposition,
    facts: Mapping[str, object],
) -> CatalogValidation | None:
    worlds_value = facts.get("worlds")
    if not isinstance(worlds_value, tuple) or not all(
        isinstance(item, LegalFitWorldTrace) for item in cast("tuple[object, ...]", worlds_value)
    ):
        return None
    worlds = cast("tuple[LegalFitWorldTrace, ...]", worlds_value)
    by_intervention = {world.intervention: world for world in worlds}
    required = {
        "baseline",
        "future-unreleased-poison",
        "legally-released-poison",
        "clock-before",
        "predictor-released",
        "label-matured",
        "earlier-revision-view",
        "insufficient",
    }
    if set(by_intervention) != required or len(worlds) != len(required):
        return CatalogValidation(
            proposition.expected_components,
            MappingProxyType(dict.fromkeys(proposition.required_evidence, False)),
        )

    baseline = by_intervention["baseline"]
    future = by_intervention["future-unreleased-poison"]
    released = by_intervention["legally-released-poison"]
    before = by_intervention["clock-before"]
    predictor = by_intervention["predictor-released"]
    label = by_intervention["label-matured"]
    revision = by_intervention["earlier-revision-view"]
    insufficient = by_intervention["insufficient"]

    before_information = _information_observation_ids(before)
    predictor_information = _information_observation_ids(predictor)
    label_information = _information_observation_ids(label)
    revision_registered = _registered_observation_ids(revision)
    revision_information = _information_observation_ids(revision)
    fit_worlds = (baseline, future, released)
    all_chains_bound = all(_legal_fit_chain_is_bound(world) for world in worlds)
    future_poison = _observation_by_id(future, future.poison_observation_id)
    released_poison = _observation_by_id(released, released.poison_observation_id)
    original_revision = _observation_by_id(
        revision,
        revision.original_revision_observation_id,
    )
    future_revision = _observation_by_id(
        revision,
        revision.future_revision_observation_id,
    )

    assertions = MappingProxyType(
        {
            "independent_clocks_propagated": (
                before_information != predictor_information
                and _sample_row_ids(before) == _sample_row_ids(predictor)
                and predictor_information == label_information
                and _sample_row_ids(predictor) != _sample_row_ids(label)
                and revision.original_revision_observation_id is not None
                and revision.future_revision_observation_id is not None
                and revision.original_revision_observation_id in revision_information
                and revision.future_revision_observation_id in revision_registered
                and revision.future_revision_observation_id not in revision_information
                and original_revision is not None
                and future_revision is not None
                and original_revision.cell_identity == future_revision.cell_identity
                and original_revision.revision_number < future_revision.revision_number
                and future_revision.available_at > revision.information.decision_time
                and insufficient.window.status.value == "insufficient"
                and insufficient.fit_calls == 0
                and insufficient.fitted is None
            ),
            "fit_consumed_only_legal_samples": (
                all_chains_bound
                and all(
                    world.window.status.value == "ready"
                    and world.fit_calls == 1
                    and world.fitted is not None
                    and world.fitted.fit_record.row_ids == _window_row_ids(world)
                    for world in fit_worlds
                )
                and _sample_row_facts(baseline) == _sample_row_facts(future)
                and _learned_payload(baseline) == _learned_payload(future)
                and future_poison is not None
                and released_poison is not None
                and _observation_semantics_excluding_availability(future_poison)
                == _observation_semantics_excluding_availability(released_poison)
                and future_poison.available_at > future.information.decision_time
                and released_poison.available_at <= released.information.decision_time
                and future.poison_observation_id in _registered_observation_ids(future)
                and future.poison_observation_id not in _information_observation_ids(future)
                and future.poison_observation_id not in _sample_source_observation_ids(future)
                and released.poison_observation_id is not None
                and released.poison_observation_id in _registered_observation_ids(released)
                and released.poison_observation_id in _sample_source_observation_ids(released)
                and _sample_row_facts(released) != _sample_row_facts(baseline)
                and _learned_payload(released) != _learned_payload(baseline)
            ),
        }
    )
    return CatalogValidation(proposition.expected_components, assertions)


def _registered_observation_ids(world: LegalFitWorldTrace) -> tuple[str, ...]:
    return tuple(item.observation_id for item in world.catalog.observations)


def _information_observation_ids(world: LegalFitWorldTrace) -> tuple[str, ...]:
    return tuple(item.observation_id for item in world.information.observations)


def _sample_row_ids(world: LegalFitWorldTrace) -> tuple[str, ...]:
    return tuple(item.row_id for item in world.sample.rows)


def _window_row_ids(world: LegalFitWorldTrace) -> tuple[str, ...]:
    return tuple(item.row_id for item in world.window.rows)


def _sample_source_observation_ids(world: LegalFitWorldTrace) -> frozenset[str]:
    return frozenset(
        observation_id
        for row in world.sample.rows
        for observation_id in (
            *(predictor.observation_id for predictor in row.predictors),
            *row.label_observation_ids,
        )
    )


def _sample_row_facts(world: LegalFitWorldTrace) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (
            row.decision_time,
            row.dimensions,
            tuple(
                (item.field_ref.identity, item.value, item.observation_id)
                for item in row.predictors
            ),
            row.label,
            row.label_matured_at,
            row.label_observation_ids,
            row.label_threshold,
        )
        for row in world.sample.rows
    )


def _learned_payload(world: LegalFitWorldTrace) -> tuple[object, ...] | None:
    if world.fitted is None:
        return None
    return (
        tuple(
            (
                model.model_definition_id,
                model.algorithm,
                model.input_feature_ids,
                model.coefficients,
                model.intercept,
                model.expansion_terms,
            )
            for model in world.fitted.models
        ),
        tuple(
            (
                state.state_slot,
                state.feature_definition_id,
                state.parameters,
            )
            for state in world.fitted.transforms
        ),
        world.fitted.ensemble_weights,
    )


def _observation_by_id(
    world: LegalFitWorldTrace,
    observation_id: str | None,
) -> RegisteredObservation | None:
    if observation_id is None:
        return None
    return next(
        (item for item in world.catalog.observations if item.observation_id == observation_id),
        None,
    )


def _observation_semantics_excluding_availability(
    observation: RegisteredObservation,
) -> tuple[object, ...]:
    return (
        observation.schema_id,
        observation.field_ref,
        observation.value,
        observation.reference_time,
        observation.vintage_id,
        observation.revision_number,
        observation.source_ref,
        observation.provenance_ref,
        observation.availability_rule_version,
        observation.dimensions,
        observation.caveats,
    )


def _legal_fit_chain_is_bound(world: LegalFitWorldTrace) -> bool:
    registered = frozenset(_registered_observation_ids(world))
    sources = _sample_source_observation_ids(world)
    return (
        bool(world.catalog.datasets)
        and world.definition.environment_id == world.catalog.environment_id
        and world.information.catalog_id == world.catalog.identity
        and world.sample.catalog_id == world.catalog.identity
        and world.sample.current_time == world.information.decision_time
        and world.sample.target_id == world.definition.target.identity
        and all(row.sample_key in world.candidate_keys for row in world.sample.rows)
        and world.window.sample_id == world.sample.sample_id
        and world.window.policy_id == world.policy.identity
        and _window_matches_policy(world)
        and set(_window_row_ids(world)).issubset(_sample_row_ids(world))
        and all(
            item.available_at <= world.information.decision_time
            for item in world.information.observations
        )
        and _sample_sources_are_legal(world)
        and sources.issubset(registered)
        and (
            world.fitted is None
            or (
                world.fitted.system_definition_id == world.definition.identity
                and world.fitted.fit_record.training_window_id == world.window.window_id
                and world.fitted.fit_record.training_sample_id == world.sample.sample_id
            )
        )
    )


def _sample_sources_are_legal(world: LegalFitWorldTrace) -> bool:
    registered = {item.observation_id: item for item in world.catalog.observations}
    for row in world.sample.rows:
        for predictor in row.predictors:
            observation = registered.get(predictor.observation_id)
            if (
                observation is None
                or observation.field_ref != predictor.field_ref
                or observation.value != predictor.value
                or observation.available_at > row.decision_time
                or observation.reference_time > row.decision_time
            ):
                return False
        for observation_id in row.label_observation_ids:
            observation = registered.get(observation_id)
            if (
                observation is None
                or observation.field_ref != world.definition.target.field_ref
                or observation.available_at > world.sample.current_time
            ):
                return False
        if row.label_matured_at > world.sample.current_time:
            return False
    return True


def _window_matches_policy(world: LegalFitWorldTrace) -> bool:
    ordered = tuple(sorted(world.sample.rows, key=lambda row: row.decision_time))
    if len(ordered) < world.policy.minimum_samples:
        return (
            world.window.status.value == "insufficient"
            and not world.window.rows
            and world.window.insufficiency is not None
        )
    if world.window.status.value != "ready" or world.window.insufficiency is not None:
        return False
    expected = ordered
    if world.policy.kind.value == "rolling":
        if world.policy.maximum_samples is None:
            return False
        expected = ordered[-world.policy.maximum_samples :]
    return world.window.rows == expected


def _validate_scientific_workflow_trace(
    proposition: Proposition,
    facts: Mapping[str, object],
) -> CatalogValidation | None:
    worlds_value = facts.get("worlds")
    if not isinstance(worlds_value, tuple) or not all(
        isinstance(item, ScientificWorkflowTrace)
        for item in cast("tuple[object, ...]", worlds_value)
    ):
        return None
    worlds = cast("tuple[ScientificWorkflowTrace, ...]", worlds_value)
    by_intervention = {world.intervention: world for world in worlds}
    if set(by_intervention) != {"promote", "reject"}:
        return None
    promoted = by_intervention["promote"]
    rejected = by_intervention["reject"]
    if proposition.id == "development-to-protected-authority":
        assertions = {
            "development_evidence_bound": all(
                world.development.evidence_id in world.frozen.development_evidence_refs
                and world.development.candidate_id == world.workflow.system.identity
                and world.workflow.development_protocol.identity in world.frozen.protocol_refs
                for world in worlds
            ),
            "independent_authorities_resolved": all(
                world.issuance.workflow == world.workflow
                and world.issuance.governance_permission.actor_id == world.workflow.requester_id
                and world.issuance.validation_grant.authority_policy_ref
                == world.workflow.promotion_standard.authority_policy_ref
                and len(
                    {
                        world.workflow.freeze_authority_id,
                        world.issuance.governance_permission.authority_id,
                        world.issuance.validation_grant.authority_id,
                    }
                )
                == INDEPENDENT_DECISION_AUTHORITY_COUNT
                and not {
                    world.workflow.freeze_authority_id,
                    world.issuance.governance_permission.authority_id,
                    world.issuance.validation_grant.authority_id,
                }.intersection({world.workflow.requester_id, world.workflow.beneficiary_id})
                and any(
                    entry.event_type == "backtest.authorization-decided"
                    and entry.status == "permit"
                    and entry.authority_id == world.issuance.governance_permission.authority_id
                    for entry in world.ledger_entries
                )
                and any(
                    entry.event_type == "finding.validation-decided"
                    and entry.authority_id == world.issuance.validation_grant.authority_id
                    for entry in world.ledger_entries
                )
                for world in worlds
            ),
            "protected_scope_bound_before_read": all(
                world.permit.scope == world.workflow.protected_scope
                and world.view.scope == world.workflow.protected_scope
                and world.issuance.protected_resource.scope == world.workflow.protected_scope
                and world.view.resource_binding_ref
                == world.issuance.protected_resource.resource_binding_ref
                and world.run.data_id == world.issuance.protected_resource.catalog.identity
                and _event_before(
                    world.ledger_entries,
                    "backtest.authorization-decided",
                    "exposure.protected-disclosed",
                )
                for world in worlds
            ),
            "authority_mutations_rejected_before_disclosure": all(
                world.authority_field_names == ()
                and world.rejected_authority_mutations
                == (
                    "workflow-privileged-labels",
                    "workflow-protected-catalog",
                    "workflow-authority-capability",
                    "protected-resource-authority-capability",
                    "protected-binding",
                    "protected-catalog",
                )
                and world.authority_probe_ledger_entries == 0
                and world.authority_probe_exposures == 0
                for world in worlds
            ),
        }
    elif proposition.id == "frozen-system-to-immutable-run":
        assertions = {
            "frozen_identity_executed": all(
                world.run.frozen_system_id == world.frozen.frozen_system_id
                and world.run.system_id == world.workflow.system.identity
                and world.run.scenario_id == world.workflow.scenario.identity
                and world.run.protected_scope_id == world.workflow.protected_scope.scope_id
                and world.run.environment_ref == world.workflow.environment_ref
                and all(
                    world.poison_observation_id not in decision.information_observation_ids
                    for decision in world.run.decisions
                )
                for world in worlds
            ),
            "immutable_run_sealed": all(
                world.mutation_rejected
                and len(world.run.decisions) == len(world.workflow.scenario.decision_sample_keys)
                and _event_before(
                    world.ledger_entries,
                    "exposure.protected-disclosed",
                    "backtest.run-sealed",
                )
                for world in worlds
            ),
        }
    elif proposition.id == "run-to-finding-or-rejection":
        assertions = {
            "run_measured_without_fit": all(
                world.measurement_fit_calls == 0
                and world.report.run_id == world.run.run_id
                and _event_before(
                    world.ledger_entries,
                    "backtest.run-sealed",
                    "evaluation.run-measured",
                )
                for world in worlds
            ),
            "finding_or_rejection_retained": (
                promoted.finding is not None
                and promoted.negative is None
                and promoted.receipt.finding_ref == promoted.finding.finding_id
                and rejected.finding is None
                and rejected.negative is not None
                and rejected.receipt.negative_result_ref == rejected.negative.negative_id
                and all(
                    world.receipt.validation_decision_ref == world.validation.decision_id
                    for world in worlds
                )
            ),
        }
    else:
        assertions = {
            "scientific_substance_preserved": (
                promoted.finding is not None
                and promoted.rendered is not None
                and promoted.receipt.rendered_report_ref == promoted.rendered.rendered_report_id
                and promoted.rendered.finding_id == promoted.finding.finding_id
                and promoted.rendered.canonical_report_id == promoted.report.report_id
                and promoted.rendered.validation_decision_id == promoted.validation.decision_id
                and promoted.rendered.machine_payload.reconstruct_finding() == promoted.finding
                and rejected.finding is None
                and rejected.rendered is None
                and rejected.receipt.rendered_report_ref is None
            ),
        }
    return CatalogValidation(
        proposition.expected_components,
        MappingProxyType(assertions),
    )


def _event_before(entries: tuple[LedgerEntry, ...], left: str, right: str) -> bool:
    event_types = tuple(item.event_type for item in entries)
    return (
        left in event_types
        and right in event_types
        and event_types.index(left) < event_types.index(right)
    )


def _is_subsequence(required: tuple[str, ...], observed: tuple[str, ...]) -> bool:
    cursor = iter(observed)
    return all(any(item == expected for item in cursor) for expected in required)


__all__ = [
    "COMPOSITES",
    "COMPOSITES_BY_ID",
    "ArtifactTrace",
    "AtomicCommitWorldTrace",
    "CatalogValidation",
    "ContextReconstructionWorldTrace",
    "ExplorationContinuationWorldTrace",
    "FailureRepairWorldTrace",
    "LearningWorldTrace",
    "LegalFitWorldTrace",
    "ObservationWorldTrace",
    "Proposition",
    "ScientificWorkflowTrace",
    "validate_production_trace",
]
