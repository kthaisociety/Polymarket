"""Checkpoint and reconstruction tests for bounded provider context."""

from __future__ import annotations

from dataclasses import replace
from typing import cast

import pytest

from research_agent.runtime._canonical import canonical_bytes
from research_agent.runtime.context import ContextBuilder
from research_agent.runtime.models import (
    AnalysisDataAccess,
    AnalysisExecutionProvenance,
    ObservationStatus,
    Recoverability,
    RuntimeInitialization,
    StructuredObservation,
)
from research_agent.runtime.store import CoherenceError, StaleCheckpointError
from tests.runtime.support import initialized_runtime

DELTA_INDEX = 3
DELTA_TOTAL = 4
DECISION_THRESHOLD = 5
PACKET_LIMIT = 3
TOTAL_OBSERVATIONS = 10
OMITTED_OBSERVATIONS = TOTAL_OBSERVATIONS - PACKET_LIMIT
DEFAULT_CHECKPOINT_RETENTION = 8
DEFAULT_CHECKPOINT_OMISSION = TOTAL_OBSERVATIONS - DEFAULT_CHECKPOINT_RETENTION
LARGE_HISTORY_FIRST = 100
LARGE_HISTORY_TOTAL = 200
LARGE_CHECKPOINT_LIMIT = 3
LARGE_PACKET_LIMIT = 2
LARGE_SERIALIZED_LIMIT = 16_000


def _observation(index: int, initialized: RuntimeInitialization) -> StructuredObservation:
    return StructuredObservation(
        observation_id=f"observation-{index}",
        delivery_id=f"delivery-{index}",
        session_id=initialized.session.session_id,
        episode_id=initialized.episode.episode_id,
        environment_ref=initialized.session.environment_ref,
        action_id=f"action-{index}",
        status=ObservationStatus.SUCCEEDED,
        observation_type="analysis_result",
        summary=f"analysis {index}",
        payload={
            "index": index,
            "decision": "continue" if index < DECISION_THRESHOLD else "review",
        },
        warnings=(f"warning-{index}",),
        provenance=AnalysisExecutionProvenance(
            session_id=initialized.session.session_id,
            environment_ref=initialized.session.environment_ref,
            capability_name="run_analysis",
            authorized_dataset_ref=None,
            selected_field_ids=("predictor_value",),
            preview_limit=None,
            code_sha256=f"code-{index}",
            accesses=(
                AnalysisDataAccess(
                    ordinal=0,
                    view_id="development-view",
                    dataset_ref="toy-monthly",
                    environment_ref="environment-v1@1",
                    field_id="predictor_value",
                ),
            ),
            dataset_refs=("toy-monthly",),
            environment_refs=("environment-v1@1",),
            random_seed=index,
            execution_status="succeeded",
        ),
        artifact_refs=(f"analysis-artifact:{index}",),
        recoverability=Recoverability.NON_RETRYABLE,
        epistemic_status="EXPLORATORY",
    )


def test_checkpoint_rebuild_preserves_working_semantics_after_context_loss() -> None:
    """A current checkpoint plus later evidence reconstructs the same provider surface."""
    store, initialized = initialized_runtime()
    session_id = initialized.session.session_id
    store.episodes[initialized.episode.episode_id] = replace(
        initialized.episode,
        current_plan=("inspect", "test", "interpret"),
        unresolved_questions=("Does the signal survive perturbation?",),
        temporary_interpretations=("The first diagnostic is provisional.",),
    )
    for index in range(3):
        store.record_observation(session_id, _observation(index, initialized))
    builder = ContextBuilder(store, max_observations=3)

    checkpoint = builder.checkpoint_current_episode(session_id)
    original = builder.build_current_context(session_id)
    store.append_event(session_id, "provider.transcript-discarded", {"all": True})
    rebuilt = builder.rebuild_from_checkpoint(session_id, checkpoint.checkpoint_id)

    assert rebuilt == original
    assert checkpoint.current_plan == ("inspect", "test", "interpret")
    assert checkpoint.unresolved_questions == ("Does the signal survive perturbation?",)
    assert checkpoint.temporary_interpretations == ("The first diagnostic is provisional.",)
    assert checkpoint.permitted_dataset_refs == ("toy-monthly",)
    assert checkpoint.warnings == ("Milestone 1 does not establish temporal legality.",)
    assert checkpoint.observations[-1].warnings == ("warning-2",)
    assert checkpoint.observations[-1].artifact_refs == ("analysis-artifact:2",)
    assert checkpoint.observations[-1].current is True
    assert checkpoint.observations[-1].superseded_by is None
    assert rebuilt.committed_understanding == ()

    store.record_observation(session_id, _observation(DELTA_INDEX, initialized))
    with_delta = builder.rebuild_from_checkpoint(session_id, checkpoint.checkpoint_id)
    assert with_delta.total_observation_count == DELTA_TOTAL
    assert with_delta.working_observations[-1].payload["index"] == DELTA_INDEX


def test_new_checkpoint_supersedes_old_and_stale_rebuild_is_rejected() -> None:
    """Only the current lineage base can reconstruct an authoritative packet."""
    store, initialized = initialized_runtime()
    session_id = initialized.session.session_id
    builder = ContextBuilder(store)
    store.record_observation(session_id, _observation(0, initialized))
    first = builder.checkpoint_current_episode(session_id)
    assert builder.checkpoint_current_episode(session_id) is first
    store.record_observation(session_id, _observation(1, initialized))
    second = builder.checkpoint_current_episode(session_id)

    assert second.checkpoint_version == first.checkpoint_version + 1
    assert second.supersedes_checkpoint_id == first.checkpoint_id
    stale_rejected = False
    try:
        builder.rebuild_from_checkpoint(session_id, first.checkpoint_id)
    except StaleCheckpointError:
        stale_rejected = True
    assert stale_rejected
    assert builder.rebuild_from_checkpoint(session_id, second.checkpoint_id).checkpoint_ref == (
        second.checkpoint_id
    )


def test_bounded_packet_discloses_omission_while_checkpoint_retains_all_evidence() -> None:
    """Context stays bounded without pretending omitted observations disappeared."""
    store, initialized = initialized_runtime()
    session_id = initialized.session.session_id
    for index in range(TOTAL_OBSERVATIONS):
        store.record_observation(session_id, _observation(index, initialized))
    builder = ContextBuilder(store, max_observations=PACKET_LIMIT)

    checkpoint = builder.checkpoint_current_episode(session_id)
    packet = builder.build_current_context(session_id)

    assert len(packet.working_observations) == PACKET_LIMIT
    assert packet.total_observation_count == TOTAL_OBSERVATIONS
    assert packet.omitted_observation_count == OMITTED_OBSERVATIONS
    assert "7 earlier working observations" in packet.warnings[-1]
    assert packet.checkpoint_ref == checkpoint.checkpoint_id
    assert len(checkpoint.observations) < TOTAL_OBSERVATIONS
    assert checkpoint.omitted_observation_count == DEFAULT_CHECKPOINT_OMISSION
    assert checkpoint.omitted_observations_ref in store.artifacts
    assert len(store.observations) == TOTAL_OBSERVATIONS
    assert tuple(item.payload["index"] for item in packet.working_observations) == (7, 8, 9)


def test_checkpoint_content_is_immutable_and_reverified_against_authoritative_records() -> None:
    """Matching IDs cannot conceal provider mutation or forged checkpoint semantics."""
    store, initialized = initialized_runtime()
    session_id = initialized.session.session_id
    store.record_observation(session_id, _observation(0, initialized))
    builder = ContextBuilder(store)
    checkpoint = builder.checkpoint_current_episode(session_id)
    packet = builder.build_current_context(session_id)

    with pytest.raises(TypeError):
        cast("dict[str, object]", packet.working_observations[0].payload)["forged"] = True
    forged_observation = replace(
        checkpoint.observations[0],
        summary="forged protected claim",
        payload={"protected_value": 999},
    )
    forged_checkpoint = replace(
        checkpoint,
        checkpoint_id="",
        checkpoint_version=checkpoint.checkpoint_version + 1,
        supersedes_checkpoint_id=checkpoint.checkpoint_id,
        observations=(forged_observation,),
    )
    with pytest.raises((CoherenceError, StaleCheckpointError)):
        store.publish_checkpoint(forged_checkpoint)
    forged_authority = replace(
        checkpoint,
        checkpoint_id="",
        checkpoint_version=checkpoint.checkpoint_version + 1,
        supersedes_checkpoint_id=checkpoint.checkpoint_id,
        state_content_digest="forged-state",
    )
    with pytest.raises((CoherenceError, StaleCheckpointError)):
        store.publish_checkpoint(forged_authority)

    object.__setattr__(checkpoint, "warnings", ("identity-stable mutation",))
    with pytest.raises(CoherenceError, match="content"):
        store.checkpoint_for_rebuild(session_id, checkpoint.checkpoint_id)


def test_large_episode_produces_bounded_checkpoint_and_context_with_drilldown() -> None:
    """History size changes counts and refs, not checkpoint/context payload growth."""
    store, initialized = initialized_runtime()
    session_id = initialized.session.session_id
    store.episodes[initialized.episode.episode_id] = replace(
        initialized.episode,
        temporary_interpretations=("decision-critical regime caveat",),
    )
    builder = ContextBuilder(
        store,
        max_observations=LARGE_PACKET_LIMIT,
        max_packet_payload_bytes=8_000,
        max_checkpoint_observations=LARGE_CHECKPOINT_LIMIT,
        max_checkpoint_payload_bytes=12_000,
    )
    for index in range(LARGE_HISTORY_FIRST):
        store.record_observation(
            session_id,
            replace(
                _observation(index, initialized),
                payload={"index": index, "blob": "x" * 1_000},
            ),
        )
    first = builder.checkpoint_current_episode(session_id)
    first_size = len(canonical_bytes(first))
    for index in range(LARGE_HISTORY_FIRST, LARGE_HISTORY_TOTAL):
        store.record_observation(
            session_id,
            replace(
                _observation(index, initialized),
                payload={"index": index, "blob": "x" * 1_000},
            ),
        )
    second = builder.checkpoint_current_episode(session_id)
    packet = builder.rebuild_from_checkpoint(session_id, second.checkpoint_id)

    assert first.retained_observation_count <= LARGE_CHECKPOINT_LIMIT
    assert second.retained_observation_count <= LARGE_CHECKPOINT_LIMIT
    assert first.omitted_observation_count >= LARGE_HISTORY_FIRST - LARGE_CHECKPOINT_LIMIT
    assert second.omitted_observation_count >= LARGE_HISTORY_TOTAL - LARGE_CHECKPOINT_LIMIT
    assert first.omitted_observations_ref in store.artifacts
    assert second.omitted_observations_ref in store.artifacts
    assert first_size < LARGE_SERIALIZED_LIMIT
    assert len(canonical_bytes(second)) < LARGE_SERIALIZED_LIMIT
    assert len(packet.working_observations) <= LARGE_PACKET_LIMIT
    assert packet.total_observation_count == LARGE_HISTORY_TOTAL
    assert packet.omitted_observation_count >= LARGE_HISTORY_TOTAL - LARGE_PACKET_LIMIT
    assert packet.temporary_interpretations == ("decision-critical regime caveat",)
