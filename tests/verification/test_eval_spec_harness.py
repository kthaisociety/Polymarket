"""Adversarial tests for production proof traces and behavioral fixture honesty."""

from __future__ import annotations

from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import TYPE_CHECKING, cast

import pytest

import research_agent.verification.behavioral as behavioral_module
from research_agent.verification import (
    COMPOSITES,
    FAMILIES,
    AgentScenario,
    BehavioralDecision,
    BehavioralExecutionStatus,
    HarnessValidity,
    ProductionProofFailureError,
    ProofAdapterRegistry,
    ProofTrace,
    ResearcherQuality,
    VerificationResult,
    VerificationStatus,
    generate_family,
    grade_dispositions,
    production_proof_registry,
    run_behavioral_family,
    run_proof_suite,
    summarize,
)
from research_agent.verification.catalog import (
    AtomicCommitWorldTrace,
    ContextReconstructionWorldTrace,
    ExplorationContinuationWorldTrace,
    FailureRepairWorldTrace,
    LegalFitWorldTrace,
    ObservationWorldTrace,
    ScientificWorkflowTrace,
)
from research_agent.verification.production_adapters import (
    AtomicSemanticCommitAdapter,
    AuthorizedExplorationToNextActionAdapter,
    ContextLossReconstructionAdapter,
    FailureToRepairedContinuationAdapter,
    LegalFitCompositionAdapter,
    ObservationToNextActionAdapter,
    ScientificWorkflowAdapter,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

PROVED = {
    "observation-to-next-action",
    "evidence-to-atomic-commit",
    "registered-data-to-legal-fit",
    "authorized-exploration-to-next-action",
    "context-loss-reconstruction",
    "failure-to-repaired-continuation",
}
PROVED.update(
    {
        "development-to-protected-authority",
        "frozen-system-to-immutable-run",
        "run-to-finding-or-rejection",
        "finding-to-report-invariance",
    }
)
EXPECTED_GREEN_COUNT = 10
EXPECTED_RED_COUNT = 5


def test_production_suite_greens_only_catalog_validated_current_composition() -> None:
    """Application-green requires a trusted raw trace and catalog-owned oracle."""
    results = run_proof_suite(production_proof_registry())
    counts = summarize(results)

    assert counts[VerificationStatus.HARNESS_GREEN] == EXPECTED_GREEN_COUNT
    assert counts[VerificationStatus.EXPECTED_RED] == EXPECTED_RED_COUNT
    assert counts[VerificationStatus.UNEXPECTED_GREEN] == 0
    assert counts[VerificationStatus.HARNESS_BUG] == 0
    assert {
        result.id for result in results if result.status is VerificationStatus.HARNESS_GREEN
    } == PROVED
    green = next(result for result in results if result.status is VerificationStatus.HARNESS_GREEN)
    assert green.evidence is not None
    assert green.evidence.production_components == COMPOSITES[0].expected_components
    assert all(green.evidence.assertions.values())


def test_application_composites_without_adapters_remain_expected_red() -> None:
    """Absence is named and never hidden by harness self-tests."""
    results = run_proof_suite()
    assert len(results) == len(COMPOSITES) == 15  # noqa: PLR2004
    assert {result.status for result in results} == {VerificationStatus.EXPECTED_RED}


@dataclass(frozen=True)
class _StaticTraceAdapter:
    proposition_id: str
    adapter_id: str
    trace: ProofTrace

    def execute(self) -> ProofTrace:
        return self.trace


def _all_true_fake_adapter() -> _StaticTraceAdapter:
    proposition = COMPOSITES[0]
    trace = ProofTrace(
        proposition.id,
        "fake.all-true",
        MappingProxyType(
            {
                "assertions": MappingProxyType(dict.fromkeys(proposition.required_evidence, True)),
                "production_components": proposition.expected_components,
            }
        ),
    )
    return _StaticTraceAdapter(proposition.id, trace.adapter_id, trace)


def _observation_worlds(facts: Mapping[str, object]) -> tuple[ObservationWorldTrace, ...]:
    """Narrow an adapter fact to the catalog's exact raw world trace type."""
    worlds = facts.get("worlds")
    if not isinstance(worlds, tuple) or not all(
        isinstance(world, ObservationWorldTrace) for world in cast("tuple[object, ...]", worlds)
    ):
        message = "proof facts did not contain observation world traces"
        raise TypeError(message)
    return cast("tuple[ObservationWorldTrace, ...]", worlds)


def _scientific_workflow_worlds(
    facts: Mapping[str, object],
) -> tuple[ScientificWorkflowTrace, ...]:
    """Narrow exact paired scientific-workflow proof worlds."""
    worlds = facts.get("worlds")
    if not isinstance(worlds, tuple) or not all(
        isinstance(world, ScientificWorkflowTrace) for world in cast("tuple[object, ...]", worlds)
    ):
        message = "proof facts did not contain scientific workflow traces"
        raise TypeError(message)
    return cast("tuple[ScientificWorkflowTrace, ...]", worlds)


def _legal_fit_worlds(facts: Mapping[str, object]) -> tuple[LegalFitWorldTrace, ...]:
    """Narrow exact registered-data-to-fit intervention traces."""
    worlds = facts.get("worlds")
    if not isinstance(worlds, tuple) or not all(
        isinstance(world, LegalFitWorldTrace) for world in cast("tuple[object, ...]", worlds)
    ):
        message = "proof facts did not contain legal-fit world traces"
        raise TypeError(message)
    return cast("tuple[LegalFitWorldTrace, ...]", worlds)


def _exploration_worlds(
    facts: Mapping[str, object],
) -> tuple[ExplorationContinuationWorldTrace, ...]:
    """Narrow exact authorized-exploration intervention traces."""
    worlds = facts.get("worlds")
    if not isinstance(worlds, tuple) or not all(
        isinstance(world, ExplorationContinuationWorldTrace)
        for world in cast("tuple[object, ...]", worlds)
    ):
        message = "proof facts did not contain exploratory continuation traces"
        raise TypeError(message)
    return cast("tuple[ExplorationContinuationWorldTrace, ...]", worlds)


def _reconstruction_worlds(
    facts: Mapping[str, object],
) -> tuple[ContextReconstructionWorldTrace, ...]:
    """Narrow exact checkpoint reconstruction intervention traces."""
    worlds = facts.get("worlds")
    if not isinstance(worlds, tuple) or not all(
        isinstance(world, ContextReconstructionWorldTrace)
        for world in cast("tuple[object, ...]", worlds)
    ):
        message = "proof facts did not contain context reconstruction traces"
        raise TypeError(message)
    return cast("tuple[ContextReconstructionWorldTrace, ...]", worlds)


def _failure_repair_worlds(
    facts: Mapping[str, object],
) -> tuple[FailureRepairWorldTrace, ...]:
    """Narrow exact bounded failure/repair intervention traces."""
    worlds = facts.get("worlds")
    if not isinstance(worlds, tuple) or not all(
        isinstance(world, FailureRepairWorldTrace) for world in cast("tuple[object, ...]", worlds)
    ):
        message = "proof facts did not contain failure repair traces"
        raise TypeError(message)
    return cast("tuple[FailureRepairWorldTrace, ...]", worlds)


def _atomic_commit_worlds(facts: Mapping[str, object]) -> tuple[AtomicCommitWorldTrace, ...]:
    """Narrow exact atomic semantic-commit intervention traces."""
    worlds = facts.get("worlds")
    if not isinstance(worlds, tuple) or not all(
        isinstance(world, AtomicCommitWorldTrace) for world in cast("tuple[object, ...]", worlds)
    ):
        message = "proof facts did not contain atomic commit world traces"
        raise TypeError(message)
    return cast("tuple[AtomicCommitWorldTrace, ...]", worlds)


def _atomic_mutation_result(
    worlds: tuple[AtomicCommitWorldTrace, ...],
) -> VerificationResult:
    trace = ProofTrace(
        "evidence-to-atomic-commit",
        AtomicSemanticCommitAdapter.adapter_id,
        MappingProxyType({"worlds": worlds}),
    )
    registry = ProofAdapterRegistry()
    registry.register_catalog_adapter(
        _StaticTraceAdapter(trace.proposition_id, trace.adapter_id, trace)
    )
    return next(
        item for item in run_proof_suite(registry) if item.id == "evidence-to-atomic-commit"
    )


@pytest.fixture(scope="module")
def atomic_commit_worlds() -> tuple[AtomicCommitWorldTrace, ...]:
    """Execute the composed atomic publication proof once for mutation tests."""
    return _atomic_commit_worlds(AtomicSemanticCommitAdapter().execute().facts)


def test_publicly_registered_fake_adapter_and_components_cannot_green() -> None:
    """Adapter-supplied booleans/component names have no proof authority."""
    registry = ProofAdapterRegistry()
    registry.register(_all_true_fake_adapter())

    result = run_proof_suite(registry)[0]

    assert result.status is VerificationStatus.UNEXPECTED_GREEN
    assert "untrusted adapter" in result.reason


@dataclass(frozen=True)
class _CrashingTrustedAdapter:
    proposition_id: str = "observation-to-next-action"
    adapter_id: str = "trusted.crash"

    def execute(self) -> ProofTrace:
        msg = "adapter implementation exploded"
        raise RuntimeError(msg)


@dataclass(frozen=True)
class _ProductionFailureAdapter:
    proposition_id: str = "observation-to-next-action"
    adapter_id: str = "trusted.production-failure"

    def execute(self) -> ProofTrace:
        msg = "production context builder regressed"
        raise ProductionProofFailureError(msg)


def test_harness_bug_and_production_regression_are_distinct() -> None:
    """Only adapter/validator defects are HARNESS_BUG; production failures are red."""
    crashing = ProofAdapterRegistry()
    crashing.register_catalog_adapter(_CrashingTrustedAdapter())
    production_failure = ProofAdapterRegistry()
    production_failure.register_catalog_adapter(_ProductionFailureAdapter())

    assert run_proof_suite(crashing)[0].status is VerificationStatus.HARNESS_BUG
    failed = run_proof_suite(production_failure)[0]
    assert failed.status is VerificationStatus.EXPECTED_RED
    assert failed.reason.startswith("production proof execution failed:")


def test_catalog_mutation_missing_production_event_turns_proof_red() -> None:
    """Dropping an observed seam event cannot be hidden by adapter assertions."""
    trace = ObservationToNextActionAdapter().execute()
    worlds = _observation_worlds(trace.facts)
    first = worlds[0]
    mutated = replace(
        first,
        event_types=tuple(item for item in first.event_types if item != "capability.executed"),
    )
    mutated_trace = replace(
        trace,
        facts=MappingProxyType({"worlds": (mutated, *worlds[1:])}),
    )
    adapter = _StaticTraceAdapter(trace.proposition_id, trace.adapter_id, mutated_trace)
    registry = ProofAdapterRegistry()
    registry.register_catalog_adapter(adapter)

    result = run_proof_suite(registry)[0]

    assert result.status is VerificationStatus.EXPECTED_RED
    assert "decision_used_no_transcript_or_source_store" in result.reason


def test_observation_trace_has_missing_payload_sentinel_and_fresh_providers() -> None:
    """The only green exposes all three interventions and actual runtime event traces."""
    result = run_proof_suite(production_proof_registry())[0]
    assert result.evidence is not None
    worlds = _observation_worlds(result.evidence.facts)
    assert tuple(world.context_row_count for world in worlds) == (18, 2, None)
    assert tuple(world.second_action_kind for world in worlds) == (
        "inspect_dataset",
        "propose_episode_transition",
        "run_analysis",
    )
    assert all(world.provider_replaced_before_decision for world in worlds)
    assert all(world.provider_state_fields == () for world in worlds)


def test_workflow_green_turns_red_when_resource_substitution_probe_is_removed() -> None:
    """Independent authority is causal evidence, not a happy-path authority label."""
    adapter = ScientificWorkflowAdapter("development-to-protected-authority")
    trace = adapter.execute()
    worlds = _scientific_workflow_worlds(trace.facts)
    mutated = replace(
        worlds[0],
        rejected_authority_mutations=tuple(
            item for item in worlds[0].rejected_authority_mutations if item != "protected-catalog"
        ),
    )
    mutated_trace = replace(
        trace,
        facts=MappingProxyType({"worlds": (mutated, *worlds[1:])}),
    )
    registry = ProofAdapterRegistry()
    registry.register_catalog_adapter(
        _StaticTraceAdapter(trace.proposition_id, trace.adapter_id, mutated_trace)
    )

    result = next(
        item
        for item in run_proof_suite(registry)
        if item.id == "development-to-protected-authority"
    )

    assert result.status is VerificationStatus.EXPECTED_RED
    assert "authority_mutations_rejected_before_disclosure" in result.reason


def test_legal_fit_proof_exposes_exact_causal_interventions() -> None:
    """The green contains paired temporal, revision, insufficiency, and learned-state worlds."""
    trace = LegalFitCompositionAdapter().execute()
    worlds = _legal_fit_worlds(trace.facts)
    by_intervention = {world.intervention: world for world in worlds}
    baseline = by_intervention["baseline"]
    future = by_intervention["future-unreleased-poison"]
    released = by_intervention["legally-released-poison"]
    before = by_intervention["clock-before"]
    predictor = by_intervention["predictor-released"]
    label = by_intervention["label-matured"]
    revision = by_intervention["earlier-revision-view"]
    insufficient = by_intervention["insufficient"]

    assert baseline.fitted is not None
    assert future.fitted is not None
    assert released.fitted is not None
    assert tuple(row.row_id for row in baseline.sample.rows) == tuple(
        row.row_id for row in future.sample.rows
    )
    assert tuple(model.coefficients for model in baseline.fitted.models) == tuple(
        model.coefficients for model in future.fitted.models
    )
    assert tuple(row.row_id for row in released.sample.rows) != tuple(
        row.row_id for row in baseline.sample.rows
    )
    assert tuple(model.coefficients for model in released.fitted.models) != tuple(
        model.coefficients for model in baseline.fitted.models
    )
    assert before.information.observations != predictor.information.observations
    assert before.sample.rows == predictor.sample.rows
    assert predictor.information.observations == label.information.observations
    assert predictor.sample.rows != label.sample.rows
    assert revision.future_revision_observation_id not in {
        item.observation_id for item in revision.information.observations
    }
    assert insufficient.fit_calls == 0
    assert insufficient.fitted is None


def test_legal_fit_green_turns_red_when_registered_observation_is_omitted() -> None:
    """A trace cannot claim legality when sample sources are absent from its registered catalog."""
    trace = LegalFitCompositionAdapter().execute()
    worlds = _legal_fit_worlds(trace.facts)
    baseline = worlds[0]
    mutated_catalog = replace(
        baseline.catalog,
        datasets=(),
    )
    mutated = replace(baseline, catalog=mutated_catalog)
    registry = ProofAdapterRegistry()
    registry.register_catalog_adapter(
        _StaticTraceAdapter(
            trace.proposition_id,
            trace.adapter_id,
            replace(trace, facts=MappingProxyType({"worlds": (mutated, *worlds[1:])})),
        )
    )

    result = next(
        item for item in run_proof_suite(registry) if item.id == "registered-data-to-legal-fit"
    )

    assert result.status is VerificationStatus.EXPECTED_RED
    assert "fit_consumed_only_legal_samples" in result.reason


def test_legal_fit_green_turns_red_when_causal_fit_fact_is_omitted() -> None:
    """Matching rows without the fitted learned payload cannot establish causal legal fitting."""
    trace = LegalFitCompositionAdapter().execute()
    worlds = _legal_fit_worlds(trace.facts)
    future_index = next(
        index
        for index, world in enumerate(worlds)
        if world.intervention == "future-unreleased-poison"
    )
    mutated_worlds = list(worlds)
    mutated_worlds[future_index] = replace(mutated_worlds[future_index], fitted=None)
    registry = ProofAdapterRegistry()
    registry.register_catalog_adapter(
        _StaticTraceAdapter(
            trace.proposition_id,
            trace.adapter_id,
            replace(trace, facts=MappingProxyType({"worlds": tuple(mutated_worlds)})),
        )
    )

    result = next(
        item for item in run_proof_suite(registry) if item.id == "registered-data-to-legal-fit"
    )

    assert result.status is VerificationStatus.EXPECTED_RED
    assert "fit_consumed_only_legal_samples" in result.reason


def test_legal_fit_green_turns_red_when_insufficient_world_reports_fit_call() -> None:
    """The insufficiency branch must causally prove that training was never invoked."""
    trace = LegalFitCompositionAdapter().execute()
    worlds = _legal_fit_worlds(trace.facts)
    mutated_worlds = tuple(
        replace(world, fit_calls=1) if world.intervention == "insufficient" else world
        for world in worlds
    )
    registry = ProofAdapterRegistry()
    registry.register_catalog_adapter(
        _StaticTraceAdapter(
            trace.proposition_id,
            trace.adapter_id,
            replace(trace, facts=MappingProxyType({"worlds": mutated_worlds})),
        )
    )

    result = next(
        item for item in run_proof_suite(registry) if item.id == "registered-data-to-legal-fit"
    )

    assert result.status is VerificationStatus.EXPECTED_RED
    assert "independent_clocks_propagated" in result.reason


@pytest.mark.parametrize(
    ("intervention", "failed_assertion"),
    [
        ("predictor-released", "independent_clocks_propagated"),
        ("earlier-revision-view", "independent_clocks_propagated"),
        ("insufficient", "independent_clocks_propagated"),
    ],
)
def test_legal_fit_green_turns_red_when_required_world_is_omitted(
    intervention: str,
    failed_assertion: str,
) -> None:
    """Every required temporal observation is causal proof, not optional narrative."""
    trace = LegalFitCompositionAdapter().execute()
    worlds = _legal_fit_worlds(trace.facts)
    mutated_worlds = tuple(world for world in worlds if world.intervention != intervention)
    registry = ProofAdapterRegistry()
    registry.register_catalog_adapter(
        _StaticTraceAdapter(
            trace.proposition_id,
            trace.adapter_id,
            replace(trace, facts=MappingProxyType({"worlds": mutated_worlds})),
        )
    )

    result = next(
        item for item in run_proof_suite(registry) if item.id == "registered-data-to-legal-fit"
    )

    assert result.status is VerificationStatus.EXPECTED_RED
    assert failed_assertion in result.reason or "catalog validator rejected" in result.reason


def test_atomic_commit_trace_exposes_every_required_publication_world(
    atomic_commit_worlds: tuple[AtomicCommitWorldTrace, ...],
) -> None:
    """The proof retains authority, stage-fault, retry, replay, and conflict facts."""
    by_intervention = {world.intervention: world for world in atomic_commit_worlds}
    assert set(by_intervention) == {
        "authoritative-evidence",
        "foreign-evidence",
        "forged-evidence",
        "failure-after-episode",
        "failure-after-state",
        "failure-after-commit",
        "failure-after-event",
        "exact-replay-and-conflict",
    }
    valid = by_intervention["authoritative-evidence"]
    assert valid.result is not None
    assert valid.result.committed
    assert valid.final_state.version == valid.initial_state.version + 1
    assert valid.final_episode.transition_count == valid.initial_episode.transition_count + 1
    assert valid.observation.provenance is not None
    for stage in ("episode", "state", "commit", "event"):
        world = by_intervention[f"failure-after-{stage}"]
        assert world.state_after_attempt == world.initial_state
        assert world.episode_after_attempt == world.initial_episode
        assert world.events_after_attempt == world.events_before
        assert world.retry_result is not None
        assert world.retry_result.committed


def test_atomic_green_turns_red_without_correlated_publication_event(
    atomic_commit_worlds: tuple[AtomicCommitWorldTrace, ...],
) -> None:
    """Episode and state writes alone are not a complete acknowledged boundary."""
    mutated = tuple(
        replace(
            world,
            final_events=tuple(
                event for event in world.final_events if event.event_type != "commit.published"
            ),
        )
        if world.intervention == "authoritative-evidence"
        else world
        for world in atomic_commit_worlds
    )
    result = _atomic_mutation_result(mutated)
    assert result.status is VerificationStatus.EXPECTED_RED
    assert "valid_evidence_published_both_effects" in result.reason


def test_atomic_green_turns_red_without_forged_authority_world(
    atomic_commit_worlds: tuple[AtomicCommitWorldTrace, ...],
) -> None:
    """A foreign reference alone cannot prove content-rehashed authority denial."""
    result = _atomic_mutation_result(
        tuple(world for world in atomic_commit_worlds if world.intervention != "forged-evidence")
    )
    assert result.status is VerificationStatus.EXPECTED_RED
    assert "foreign_evidence_published_neither_effect" in result.reason


@pytest.mark.parametrize("stage", ["episode", "state", "commit", "event"])
def test_atomic_green_turns_red_when_stage_failure_exposes_state(
    atomic_commit_worlds: tuple[AtomicCommitWorldTrace, ...],
    stage: str,
) -> None:
    """Each staged assignment is a causal all-or-nothing proof obligation."""
    mutated = tuple(
        replace(world, state_after_attempt=world.final_state)
        if world.intervention == f"failure-after-{stage}"
        else world
        for world in atomic_commit_worlds
    )
    result = _atomic_mutation_result(mutated)
    assert result.status is VerificationStatus.EXPECTED_RED
    assert "injected_failure_published_neither_effect" in result.reason


def test_atomic_green_turns_red_when_stage_failure_is_not_retryable(
    atomic_commit_worlds: tuple[AtomicCommitWorldTrace, ...],
) -> None:
    """Rollback must leave the exact request safely retryable."""
    mutated = tuple(
        replace(world, retry_result=None) if world.intervention == "failure-after-event" else world
        for world in atomic_commit_worlds
    )
    result = _atomic_mutation_result(mutated)
    assert result.status is VerificationStatus.EXPECTED_RED
    assert "injected_failure_published_neither_effect" in result.reason


def test_atomic_green_turns_red_when_replay_duplicates_publish_event(
    atomic_commit_worlds: tuple[AtomicCommitWorldTrace, ...],
) -> None:
    """Exact replay must return the original result without a second effect."""
    mutated_worlds: list[AtomicCommitWorldTrace] = []
    for world in atomic_commit_worlds:
        if world.intervention != "exact-replay-and-conflict":
            mutated_worlds.append(world)
            continue
        published = next(
            event for event in world.final_events if event.event_type == "commit.published"
        )
        mutated_worlds.append(replace(world, final_events=(*world.final_events, published)))
    result = _atomic_mutation_result(tuple(mutated_worlds))
    assert result.status is VerificationStatus.EXPECTED_RED
    assert "exact_replay_did_not_duplicate_effects" in result.reason


def test_atomic_green_turns_red_without_changed_payload_conflict(
    atomic_commit_worlds: tuple[AtomicCommitWorldTrace, ...],
) -> None:
    """Key-only replay cannot establish semantic idempotency."""
    mutated = tuple(
        replace(world, conflict_result=None)
        if world.intervention == "exact-replay-and-conflict"
        else world
        for world in atomic_commit_worlds
    )
    result = _atomic_mutation_result(mutated)
    assert result.status is VerificationStatus.EXPECTED_RED
    assert "exact_replay_did_not_duplicate_effects" in result.reason


def test_learning_causality_fixture_is_not_registered_as_independent_authority_proof() -> None:
    """Self-registered history and authority labels cannot establish the I8 composite."""
    result = next(
        item
        for item in run_proof_suite(production_proof_registry())
        if item.id == "validated-learning-to-future-behavior"
    )

    assert result.status is VerificationStatus.EXPECTED_RED
    assert result.adapter_id is None
    assert "production composition absent" in result.reason


def test_authorized_exploration_green_turns_red_without_actual_access_provenance() -> None:
    """A returned sentinel cannot substitute for harness-observed data access."""
    trace = AuthorizedExplorationToNextActionAdapter().execute()
    worlds = _exploration_worlds(trace.facts)
    first = worlds[0]
    provenance = first.first_observation.provenance
    assert provenance is not None
    mutated_observation = replace(
        first.first_observation,
        provenance=replace(provenance, accesses=()),
    )
    mutated_worlds = (replace(first, first_observation=mutated_observation), *worlds[1:])
    registry = ProofAdapterRegistry()
    registry.register_catalog_adapter(
        _StaticTraceAdapter(
            trace.proposition_id,
            trace.adapter_id,
            replace(trace, facts=MappingProxyType({"worlds": mutated_worlds})),
        )
    )

    result = next(
        item
        for item in run_proof_suite(registry)
        if item.id == "authorized-exploration-to-next-action"
    )

    assert result.status is VerificationStatus.EXPECTED_RED
    assert "authorized_analysis_executed" in result.reason


def test_context_reconstruction_green_turns_red_when_rebuilt_question_is_dropped() -> None:
    """Transcript loss is not survived if checkpoint meaning disappears on rebuild."""
    trace = ContextLossReconstructionAdapter().execute()
    worlds = _reconstruction_worlds(trace.facts)
    opened = worlds[0]
    mutated = replace(
        opened,
        rebuilt_packet=replace(opened.rebuilt_packet, unresolved_questions=()),
    )
    registry = ProofAdapterRegistry()
    registry.register_catalog_adapter(
        _StaticTraceAdapter(
            trace.proposition_id,
            trace.adapter_id,
            replace(trace, facts=MappingProxyType({"worlds": (mutated, *worlds[1:])})),
        )
    )

    result = next(
        item for item in run_proof_suite(registry) if item.id == "context-loss-reconstruction"
    )

    assert result.status is VerificationStatus.EXPECTED_RED
    assert "checkpoint_preserved_meaning" in result.reason


def test_failure_repair_green_turns_red_without_traceback_drilldown() -> None:
    """A repaired result cannot hide the exact operational failure evidence."""
    trace = FailureToRepairedContinuationAdapter().execute()
    worlds = _failure_repair_worlds(trace.facts)
    failed = worlds[0]
    registry = ProofAdapterRegistry()
    registry.register_catalog_adapter(
        _StaticTraceAdapter(
            trace.proposition_id,
            trace.adapter_id,
            replace(
                trace,
                facts=MappingProxyType({"worlds": (replace(failed, artifacts=()), *worlds[1:])}),
            ),
        )
    )

    result = next(
        item for item in run_proof_suite(registry) if item.id == "failure-to-repaired-continuation"
    )

    assert result.status is VerificationStatus.EXPECTED_RED
    assert "failure_was_explicit_and_repairable" in result.reason


def test_unsupported_retry_composition_is_honestly_red() -> None:
    """Normal replay is not registered as uncertain-acknowledgement recovery."""
    results = {result.id: result for result in run_proof_suite(production_proof_registry())}
    result = results["privileged-retry-idempotency"]
    assert result.status is VerificationStatus.EXPECTED_RED
    assert result.adapter_id is None


def test_composite_registry_is_unique_traceable_and_exact_for_green() -> None:
    """Every proposition names seams/invariants; green additionally owns exact components."""
    assert len({item.id for item in COMPOSITES}) == len(COMPOSITES)
    assert all(item.seams and item.invariants and item.required_evidence for item in COMPOSITES)
    assert {item.id for item in COMPOSITES if item.expected_components} == PROVED


@dataclass(frozen=True)
class _LookupPolicy:
    policy_id: str
    dispositions: dict[str, str]
    include_evidence: bool = True

    def decide(self, scenario: AgentScenario) -> BehavioralDecision:
        refs = (f"evidence:{scenario.scenario_id}",) if self.include_evidence else ()
        return BehavioralDecision(
            policy_id=self.policy_id,
            scenario_id=scenario.scenario_id,
            disposition=self.dispositions[scenario.scenario_id],
            evidence_refs=refs,
        )


@dataclass
class _AlternatingPolicy:
    policy_id: str = "alternating"
    calls: int = 0

    def decide(self, scenario: AgentScenario) -> BehavioralDecision:
        self.calls += 1
        return BehavioralDecision(
            self.policy_id,
            scenario.scenario_id,
            "left" if self.calls % 2 else "right",
        )


@dataclass(frozen=True)
class _CrashingPolicy:
    policy_id: str = "crashing"

    def decide(self, scenario: AgentScenario) -> BehavioralDecision:
        del scenario
        msg = "provider/runtime failed"
        raise RuntimeError(msg)


@dataclass(frozen=True)
class _VisibleIdExploitPolicy:
    policy_id: str = "old-visible-id-exploit"

    def decide(self, scenario: AgentScenario) -> BehavioralDecision:
        index = int(scenario.scenario_id.rsplit(":", maxsplit=1)[1])
        disposition = tuple(FAMILIES)[index]
        return BehavioralDecision(self.policy_id, scenario.scenario_id, disposition)


@pytest.mark.parametrize("family_id", sorted(FAMILIES))
def test_family_fixture_is_opaque_reproducible_and_never_researcher_pass(
    family_id: str,
) -> None:
    """Evaluator oracle validates mechanics but cannot establish researcher quality."""
    first = generate_family(family_id, seed=41)
    second = generate_family(family_id, seed=41)
    result = run_behavioral_family(
        first,
        behavioral_module.evaluator_fixture_policy(first),
    )

    assert first == second
    assert len(first.agent_views) == 3  # noqa: PLR2004
    assert result.harness_validity is HarnessValidity.VALID
    assert result.execution_status is BehavioralExecutionStatus.COMPLETED
    assert result.researcher_quality is ResearcherQuality.NOT_ASSESSED
    assert result.score == 1.0
    assert result.evidence_level == "HARNESS_CAUSALITY_ONLY"
    assert all(result.property_evidence.values())
    assert all(score < 1.0 for score in result.constant_policy_baselines.values())
    for visible in first.agent_views:
        assert visible.scenario_id.startswith("scenario-")
        assert ":" not in visible.scenario_id
        assert not hasattr(visible, "seed")
        assert not hasattr(visible, "order")
        assert not hasattr(visible, "required_disposition")


def test_complementary_cases_are_privately_shuffled() -> None:
    """Generator order changes reproducibly without entering the agent view."""
    first = generate_family("signal-discrimination", seed=41)
    second = generate_family("signal-discrimination", seed=42)
    first_order = tuple(case.required_disposition for case in first.evaluator_cases)
    second_order = tuple(case.required_disposition for case in second.evaluator_cases)

    assert first_order != second_order
    assert all(not hasattr(view, "seed") for view in (*first.agent_views, *second.agent_views))


def test_old_visible_id_truth_exploit_is_a_policy_failure_not_a_quality_pass() -> None:
    """Opaque IDs cannot be parsed into evaluator case order."""
    family = generate_family("signal-discrimination", seed=123)

    result = run_behavioral_family(family, _VisibleIdExploitPolicy())

    assert result.harness_validity is HarnessValidity.VALID
    assert result.execution_status is BehavioralExecutionStatus.POLICY_FAILED
    assert result.researcher_quality is ResearcherQuality.NOT_ASSESSED
    assert result.score is None


def test_even_evaluator_truth_lookup_without_evidence_never_passes_researcher_quality() -> None:
    """A perfect disposition lookup remains harness-only mechanical evidence."""
    family = generate_family("signal-discrimination", seed=52)
    oracle = behavioral_module.evaluator_fixture_policy(family)
    policy = _LookupPolicy(
        "evidence-blind-oracle",
        dict(oracle.dispositions),
        include_evidence=False,
    )

    result = run_behavioral_family(family, policy)

    assert result.score == 1.0
    assert result.researcher_quality is ResearcherQuality.NOT_ASSESSED
    assert all(not grade.evidence_refs for grade in result.scenario_grades)


@pytest.mark.parametrize("family_id", sorted(FAMILIES))
def test_constant_policy_baseline_is_scored_without_researcher_quality_claim(
    family_id: str,
) -> None:
    """Blanket behavior is mechanically weak; this fixture still does not assess a researcher."""
    family = generate_family(family_id, seed=91)
    disposition = family.evaluator_cases[0].required_disposition
    policy = _LookupPolicy(
        "constant-policy",
        {view.scenario_id: disposition for view in family.agent_views},
    )
    result = run_behavioral_family(family, policy)

    assert result.harness_validity is HarnessValidity.VALID
    assert result.execution_status is BehavioralExecutionStatus.COMPLETED
    assert result.researcher_quality is ResearcherQuality.NOT_ASSESSED
    assert result.score is not None
    assert result.score < 1.0
    assert result.constant_policy_baselines[disposition] == result.score


def test_policy_crash_and_nondeterminism_are_run_failures_not_invalid_harness() -> None:
    """A valid evaluator retains validity when the actor fails its execution protocol."""
    family = generate_family("signal-discrimination", seed=7)

    crashed = run_behavioral_family(family, _CrashingPolicy())
    nondeterministic = run_behavioral_family(family, _AlternatingPolicy())

    assert crashed.harness_validity is HarnessValidity.VALID
    assert crashed.execution_status is BehavioralExecutionStatus.POLICY_FAILED
    assert nondeterministic.harness_validity is HarnessValidity.VALID
    assert nondeterministic.execution_status is BehavioralExecutionStatus.NONDETERMINISTIC
    assert crashed.researcher_quality is ResearcherQuality.NOT_ASSESSED
    assert nondeterministic.researcher_quality is ResearcherQuality.NOT_ASSESSED


def test_incomplete_family_is_invalid_and_partial_grading_is_rejected() -> None:
    """Evaluator structure failure remains distinct from policy/runtime failure."""
    family = generate_family("signal-discrimination", seed=7)
    incomplete = replace(family, agent_views=family.agent_views[:1])
    result = run_behavioral_family(
        incomplete,
        behavioral_module.evaluator_fixture_policy(family),
    )

    assert result.harness_validity is HarnessValidity.INVALID
    assert result.execution_status is BehavioralExecutionStatus.NOT_RUN
    assert result.researcher_quality is ResearcherQuality.NOT_ASSESSED
    with pytest.raises(ValueError, match="complete valid non-empty"):
        grade_dispositions(family, ("strengthen",))
