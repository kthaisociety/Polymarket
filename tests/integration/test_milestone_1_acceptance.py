"""Whole-organism Milestone 1 acceptance and repair scenarios."""

from typing import cast

from research_agent.runtime.capabilities import (
    ActionRouter,
    DatasetRepository,
    make_toy_monthly_dataset,
)
from research_agent.runtime.commit import CommitCoordinator
from research_agent.runtime.context import ContextBuilder
from research_agent.runtime.engine import AutonomousResearchRuntime
from research_agent.runtime.models import EpisodeStatus
from research_agent.runtime.provider import ScriptedModelProvider
from research_agent.runtime.store import InMemoryRuntimeStore
from tests.runtime.support import initialized_runtime

PREVIEW_LIMIT = 4
TOY_ROW_COUNT = 18
DURABLE_INSPECTION_FACT = (
    "The authorized toy dataset contains 18 monthly rows and one missing predictor."
)


def _inspection_response(session_id: str, episode_id: str) -> dict[str, object]:
    return {
        "message": "Inspect the bounded authorized dataset.",
        "action": {
            "kind": "inspect_dataset",
            "action_id": "inspect-1",
            "session_id": session_id,
            "episode_id": episode_id,
            "arguments": {
                "dataset_ref": "toy-monthly",
                "selected_field_ids": [
                    "reference_time",
                    "available_at",
                    "predictor_value",
                    "target_value",
                ],
                "preview_limit": 4,
            },
        },
    }


def _commit_response(
    session_id: str,
    episode_id: str,
    evidence_ref: str,
    artifact_ref: str,
    *,
    idempotency_key: str,
) -> dict[str, object]:
    return {
        "message": "Resolve the descriptive inspection boundary.",
        "action": {
            "kind": "propose_episode_transition",
            "action_id": f"transition:{idempotency_key}",
            "session_id": session_id,
            "episode_id": episode_id,
            "arguments": {
                "target_status": "resolved",
                "synthesis": "The authorized inspection established dataset shape and missingness.",
                "evidence_refs": [evidence_ref, artifact_ref],
                "state_update": {
                    "starting_state_version": 0,
                    "durable_understanding": [DURABLE_INSPECTION_FACT],
                    "evidence_refs": [evidence_ref, artifact_ref],
                },
                "idempotency_key": idempotency_key,
            },
        },
    }


def _runtime(
    provider: ScriptedModelProvider,
    store: InMemoryRuntimeStore,
) -> AutonomousResearchRuntime:
    return AutonomousResearchRuntime(
        store,
        provider,
        ContextBuilder(store),
        ActionRouter(store, DatasetRepository((make_toy_monthly_dataset(),))),
        CommitCoordinator(store),
    )


def test_complete_inspection_episode_survives_provider_context_loss() -> None:
    """Observation progresses the episode; only validated commit changes state."""
    store, initialized = initialized_runtime()
    session_id = initialized.session.session_id
    episode_id = initialized.episode.episode_id
    provider = ScriptedModelProvider((_inspection_response(session_id, episode_id),))
    runtime = _runtime(provider, store)

    inspection_turn = runtime.advance_one_turn(session_id)

    assert inspection_turn.observation is not None
    observation = inspection_turn.observation
    artifact_ref = observation.artifact_refs[0]
    _, _, _, state_before, episode_before = store.coherent_view(session_id)
    assert state_before.version == 0
    assert state_before.durable_understanding == ()
    assert episode_before.status is EpisodeStatus.ACTIVE
    assert episode_before.observation_ids == (observation.observation_id,)
    preview = observation.payload["preview"]
    assert isinstance(preview, tuple)
    assert len(cast("tuple[object, ...]", preview)) == PREVIEW_LIMIT

    provider.discard_native_context()
    provider.queue_response(
        _commit_response(
            session_id,
            episode_id,
            observation.observation_id,
            artifact_ref,
            idempotency_key="commit-acceptance",
        )
    )
    terminal_run = runtime.run_until_terminal(session_id, max_turns=1)
    commit_turn = terminal_run.turns[0]

    assert provider.calls[0].working_observations[0].payload["row_count"] == TOY_ROW_COUNT
    assert commit_turn.commit_result is not None
    assert commit_turn.commit_result.committed
    _, _, _, state_after, episode_after = store.coherent_view(session_id)
    assert state_after.version == 1
    assert state_after.evidence_refs == (observation.observation_id, artifact_ref)
    assert episode_after.status is EpisodeStatus.RESOLVED
    assert terminal_run.terminal_status is EpisodeStatus.RESOLVED
    event_types = tuple(event.event_type for event in store.events_for(session_id))
    assert event_types.index("action.authorized") < event_types.index("capability.executed")
    assert event_types.index("capability.executed") < event_types.index("observation.assembled")
    assert event_types.index("observation.assembled") < event_types.index("commit.published")


def test_invalid_commit_returns_repairable_observation_then_corrected_request_succeeds() -> None:
    """Commit rejection stays in the active episode and can be repaired."""
    store, initialized = initialized_runtime()
    session_id = initialized.session.session_id
    episode_id = initialized.episode.episode_id
    provider = ScriptedModelProvider((_inspection_response(session_id, episode_id),))
    runtime = _runtime(provider, store)
    inspection = runtime.advance_one_turn(session_id)
    assert inspection.observation is not None
    real_observation = inspection.observation
    artifact_ref = real_observation.artifact_refs[0]
    provider.queue_response(
        _commit_response(
            session_id,
            episode_id,
            "missing-evidence",
            artifact_ref,
            idempotency_key="invalid-commit",
        )
    )

    rejected = runtime.advance_one_turn(session_id)

    assert rejected.observation is not None
    _, _, _, state, episode = store.coherent_view(session_id)
    assert state.version == 0
    assert episode.status is EpisodeStatus.ACTIVE
    assert rejected.observation.observation_id in episode.observation_ids
    provider.queue_response(
        _commit_response(
            session_id,
            episode_id,
            real_observation.observation_id,
            artifact_ref,
            idempotency_key="corrected-commit",
        )
    )

    corrected = runtime.advance_one_turn(session_id)

    assert corrected.commit_result is not None
    assert corrected.commit_result.committed
