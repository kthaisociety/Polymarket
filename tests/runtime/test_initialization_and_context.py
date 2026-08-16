"""Contract tests for initialization and context reconstruction."""

from dataclasses import replace
from typing import TYPE_CHECKING, cast

import pytest

from research_agent.runtime.context import ContextBuilder
from research_agent.runtime.initialization import ResearchRuntimeInitializer
from research_agent.runtime.models import (
    ContextPacket,
    ObservationStatus,
    Recoverability,
    StructuredObservation,
)
from research_agent.runtime.provider import ModelResponse
from research_agent.runtime.store import (
    CoherenceError,
    InjectedPersistenceError,
    InMemoryRuntimeStore,
)
from tests.runtime.support import confirmed_toy_task, initialized_runtime, toy_environment

if TYPE_CHECKING:
    from collections.abc import Mapping

TOY_ROW_COUNT = 18


class _SemanticsDrivenProvider:
    """Choose an intent only from mandatory packet semantics."""

    def complete(self, packet: ContextPacket) -> ModelResponse:
        constrained = "avoid extrapolation" in packet.constraints
        provisional = "regime may be unstable" in packet.temporary_interpretations
        marker = (
            f"{'constrained' if constrained else 'open'}-{'cautious' if provisional else 'plain'}"
        )
        return ModelResponse("", {"action_id": marker}, {})


def test_initialization_is_epistemic_zero_idempotent_and_independent() -> None:
    """Exact retry converges while a new request creates isolated records."""
    store = InMemoryRuntimeStore()
    task = confirmed_toy_task()
    environment = toy_environment()
    initializer = ResearchRuntimeInitializer(store)

    first = initializer.initialize(task, environment, request_id="request-1")
    replay = initializer.initialize(task, environment, request_id="request-1")
    sibling = initializer.initialize(task, environment, request_id="request-2")
    different_subject = initializer.initialize(
        confirmed_toy_task(objective="Characterize a different time-series research subject."),
        environment,
        request_id="request-3",
    )

    assert first == replay
    assert sibling.session.session_id != first.session.session_id
    assert sibling.state.state_id != first.state.state_id
    assert sibling.episode.episode_id != first.episode.episode_id
    assert first.state.version == 0
    assert first.state.durable_understanding == ()
    assert first.state.protected_exposures == ()
    assert first.episode.observation_ids == ()
    assert different_subject.state.mission != first.state.mission
    assert different_subject.state.durable_understanding == ()


def test_initialization_failure_publishes_no_half_session() -> None:
    """Injected publication failure leaves no active resumable records."""
    store = InMemoryRuntimeStore()
    store.fail_next_initialization = True

    with pytest.raises(InjectedPersistenceError):
        ResearchRuntimeInitializer(store).initialize(
            confirmed_toy_task(),
            toy_environment(),
            request_id="request-fail",
        )

    assert store.sessions == {}
    assert store.states == {}
    assert store.episodes == {}


def test_context_rebuild_uses_episode_evidence_not_trajectory_transcript() -> None:
    """Substantive working evidence survives provider-context loss without becoming belief."""
    store, initialized = initialized_runtime()
    observation = StructuredObservation(
        observation_id="observation-18",
        delivery_id="delivery-18",
        session_id=initialized.session.session_id,
        episode_id=initialized.episode.episode_id,
        environment_ref=initialized.session.environment_ref,
        action_id="action-1",
        status=ObservationStatus.SUCCEEDED,
        observation_type="dataset_inspection",
        summary="Dataset has 18 rows.",
        payload={"row_count": 18},
        warnings=(),
        provenance=None,
        artifact_refs=("artifact-1",),
        recoverability=Recoverability.REPAIRABLE,
    )
    store.record_observation(initialized.session.session_id, observation)
    store.append_event(initialized.session.session_id, "private.transcript", {"secret": "omit"})
    builder = ContextBuilder(store)

    first = builder.build_current_context(initialized.session.session_id)
    rebuilt = builder.build_current_context(initialized.session.session_id)

    assert rebuilt == first
    assert rebuilt.working_observations[0].payload["row_count"] == TOY_ROW_COUNT
    assert "private.transcript" not in repr(rebuilt)
    assert rebuilt.committed_understanding == ()
    assert store.states[initialized.state.state_id].version == 0


def test_context_fails_on_cross_session_episode_identity() -> None:
    """ContextBuilder cannot assemble a plausible packet from torn identities."""
    store, initialized = initialized_runtime()
    store.episodes[initialized.episode.episode_id] = replace(
        initialized.episode,
        session_id="another-session",
    )

    with pytest.raises(CoherenceError):
        ContextBuilder(store).build_current_context(initialized.session.session_id)


def test_context_fails_when_episode_observation_is_missing() -> None:
    """A dangling working-evidence reference cannot become plausible context."""
    store, initialized = initialized_runtime()
    store.episodes[initialized.episode.episode_id] = replace(
        initialized.episode,
        observation_ids=("missing-observation",),
    )

    with pytest.raises(CoherenceError):
        ContextBuilder(store).build_current_context(initialized.session.session_id)


def test_observation_delivery_is_authority_bound_immutable_and_idempotent() -> None:
    """Exact replay converges while mutation and foreign delivery fail closed."""
    store, initialized = initialized_runtime()
    observation = StructuredObservation(
        observation_id="observation-bound",
        delivery_id="delivery-bound",
        session_id=initialized.session.session_id,
        episode_id=initialized.episode.episode_id,
        environment_ref=initialized.session.environment_ref,
        action_id="action-bound",
        status=ObservationStatus.SUCCEEDED,
        observation_type="analysis_result",
        summary="Bounded evidence.",
        payload={"nested": {"values": [1, 2, 3]}},
        warnings=(),
        provenance=None,
        artifact_refs=(),
        recoverability=Recoverability.REPAIRABLE,
    )

    first = store.record_observation(initialized.session.session_id, observation)
    replay = store.record_observation(initialized.session.session_id, observation)

    assert replay == first
    assert first.observation_ids == (observation.observation_id,)
    nested = cast("Mapping[str, object]", observation.payload["nested"])
    with pytest.raises(TypeError):
        cast("dict[str, object]", nested)["forged"] = True
    with pytest.raises(CoherenceError, match="delivery identity"):
        store.record_observation(
            initialized.session.session_id,
            replace(observation, payload={"nested": {"values": [999]}}),
        )
    with pytest.raises(CoherenceError, match="authority"):
        store.record_observation(
            initialized.session.session_id,
            replace(
                observation,
                observation_id="foreign-observation",
                delivery_id="foreign-delivery",
                session_id="foreign-session",
            ),
        )
    assert store.episodes[initialized.episode.episode_id].observation_ids == (
        observation.observation_id,
    )


def test_constraints_and_temporary_interpretation_causally_change_packet_action() -> None:
    """Mandatory mission/episode semantics survive reconstruction and affect behavior."""
    environment = toy_environment()
    constrained_store = InMemoryRuntimeStore()
    constrained_task = confirmed_toy_task(constraints=("avoid extrapolation",))
    constrained = ResearchRuntimeInitializer(constrained_store).initialize(
        constrained_task,
        environment,
        request_id="constrained",
    )
    constrained_store.episodes[constrained.episode.episode_id] = replace(
        constrained.episode,
        temporary_interpretations=("regime may be unstable",),
    )
    open_store, open_session = initialized_runtime(request_id="open")
    constrained_packet = ContextBuilder(constrained_store).build_current_context(
        constrained.session.session_id
    )
    open_packet = ContextBuilder(open_store).build_current_context(open_session.session.session_id)

    provider = _SemanticsDrivenProvider()
    constrained_action = provider.complete(constrained_packet).action["action_id"]
    open_action = provider.complete(open_packet).action["action_id"]

    assert constrained_action == "constrained-cautious"
    assert open_action == "open-plain"
    assert constrained_action != open_action
    assert constrained_packet.target_field_id == "target_value"
    assert constrained_packet.forecast_horizon == constrained_task.forecast_horizon
    assert constrained_packet.episode_objective == constrained.state.mission
    assert constrained_packet.protected_exposure_refs == ()
    assert constrained_packet.protected_resource_refs == ()
