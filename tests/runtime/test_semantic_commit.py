"""Contract and adversarial tests for the semantic commit boundary."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest

from research_agent.runtime.actions import EpisodeTransitionProposal, StateUpdateProposal
from research_agent.runtime.commit import CommitCoordinator, CommitRequest
from research_agent.runtime.models import (
    EpisodeStatus,
    FailureCode,
    ObservationStatus,
    Recoverability,
    RuntimeInitialization,
    StructuredObservation,
)
from research_agent.runtime.store import InjectedPersistenceError, InMemoryRuntimeStore
from tests.runtime.support import initialized_runtime


def _request(session_id: str, episode_id: str, evidence_ref: str) -> CommitRequest:
    return CommitRequest(
        session_id=session_id,
        episode_id=episode_id,
        transition=EpisodeTransitionProposal(
            EpisodeStatus.RESOLVED,
            "Inspection established the bounded descriptive facts.",
            (evidence_ref,),
        ),
        state_update=StateUpdateProposal(
            0,
            ("The authorized dataset contains 18 rows.",),
            (evidence_ref,),
        ),
        idempotency_key="commit-1",
    )


def _with_evidence() -> tuple[InMemoryRuntimeStore, RuntimeInitialization, str]:
    store, initialized = initialized_runtime()
    observation = StructuredObservation(
        "observation-1",
        "delivery-1",
        initialized.session.session_id,
        initialized.episode.episode_id,
        initialized.session.environment_ref,
        "action-1",
        ObservationStatus.SUCCEEDED,
        "dataset_inspection",
        "Dataset has 18 rows.",
        {"row_count": 18},
        (),
        None,
        (),
        Recoverability.REPAIRABLE,
    )
    store.record_observation(initialized.session.session_id, observation)
    return store, initialized, observation.observation_id


def test_combined_commit_is_atomic_and_exact_replay_is_idempotent() -> None:
    """Episode/state publish once and exact replay returns the original identity."""
    store, initialized, evidence_ref = _with_evidence()
    coordinator = CommitCoordinator(store)
    request = _request(
        initialized.session.session_id,
        initialized.episode.episode_id,
        evidence_ref,
    )

    first = coordinator.commit(request)
    replay = coordinator.commit(request)

    assert first.committed
    assert replay.committed
    assert replay.replayed
    assert replay.commit_id == first.commit_id
    _, _, _, state, episode = store.coherent_view(request.session_id)
    assert state.version == 1
    assert episode.status is EpisodeStatus.RESOLVED
    assert episode.transition_count == 1
    commit_events = [
        event
        for event in store.events_for(request.session_id)
        if event.event_type == "commit.published"
    ]
    assert len(commit_events) == 1


def test_changed_payload_with_same_key_conflicts_without_mutation() -> None:
    """Idempotency cannot conceal changed scientific semantics."""
    store, initialized, evidence_ref = _with_evidence()
    coordinator = CommitCoordinator(store)
    request = _request(
        initialized.session.session_id,
        initialized.episode.episode_id,
        evidence_ref,
    )
    coordinator.commit(request)

    conflict = coordinator.commit(
        replace(
            request,
            transition=replace(request.transition, synthesis="Changed synthesis."),
        )
    )

    assert not conflict.committed
    assert conflict.failure is not None
    assert conflict.failure.code is FailureCode.IDEMPOTENCY_CONFLICT


def test_concurrent_exact_commits_converge_on_one_boundary() -> None:
    """Concurrent retry cannot duplicate the state version or lifecycle transition."""
    store, initialized, evidence_ref = _with_evidence()
    coordinator = CommitCoordinator(store)
    request = _request(
        initialized.session.session_id,
        initialized.episode.episode_id,
        evidence_ref,
    )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(pool.map(coordinator.commit, (request, request)))

    assert all(result.committed for result in results)
    assert len({result.commit_id for result in results}) == 1
    _, _, _, state, episode = store.coherent_view(request.session_id)
    assert state.version == 1
    assert episode.transition_count == 1


def test_invalid_state_evidence_commits_neither_effect() -> None:
    """Independent validation failure cannot leave a resolved half-commit."""
    store, initialized, evidence_ref = _with_evidence()
    request = _request(
        initialized.session.session_id,
        initialized.episode.episode_id,
        evidence_ref,
    )
    assert request.state_update is not None
    invalid = replace(
        request, state_update=replace(request.state_update, evidence_refs=("missing",))
    )

    result = CommitCoordinator(store).commit(invalid)

    assert not result.committed
    _, _, _, state, episode = store.coherent_view(request.session_id)
    assert state.version == 0
    assert episode.status is EpisodeStatus.ACTIVE


def test_injected_persistence_failure_exposes_no_half_commit() -> None:
    """Failure before copy-on-write publication leaves both records unchanged."""
    store, initialized, evidence_ref = _with_evidence()
    store.fail_next_commit = True
    request = _request(
        initialized.session.session_id,
        initialized.episode.episode_id,
        evidence_ref,
    )

    with pytest.raises(InjectedPersistenceError):
        CommitCoordinator(store).commit(request)

    _, _, _, state, episode = store.coherent_view(request.session_id)
    assert state.version == 0
    assert episode.status is EpisodeStatus.ACTIVE


@pytest.mark.parametrize("stage", ["episode", "state", "commit", "event"])
def test_fault_after_each_staged_write_rolls_back_the_whole_boundary(stage: str) -> None:
    """No mid-publication fault can expose one semantic effect without the others."""
    store, initialized, evidence_ref = _with_evidence()
    request = _request(
        initialized.session.session_id,
        initialized.episode.episode_id,
        evidence_ref,
    )
    store.fail_commit_after_stage = stage
    events_before = store.events_for(request.session_id)

    with pytest.raises(InjectedPersistenceError, match=f"after {stage}"):
        CommitCoordinator(store).commit(request)

    _, _, _, state, episode = store.coherent_view(request.session_id)
    assert state.version == 0
    assert episode.status is EpisodeStatus.ACTIVE
    assert episode.transition_count == 0
    assert store.commits == {}
    assert store.events_for(request.session_id) == events_before

    repaired = CommitCoordinator(store).commit(request)
    assert repaired.committed
    _, _, _, repaired_state, repaired_episode = store.coherent_view(request.session_id)
    assert repaired_state.version == 1
    assert repaired_episode.status is EpisodeStatus.RESOLVED


def test_commit_rejects_evidence_whose_authority_binding_was_corrupted() -> None:
    """An episode-listed ID is insufficient without exact session/environment correlation."""
    store, initialized, evidence_ref = _with_evidence()
    original = store.observations[evidence_ref]
    store.observations[evidence_ref] = replace(original, session_id="foreign-session")
    request = _request(
        initialized.session.session_id,
        initialized.episode.episode_id,
        evidence_ref,
    )

    with pytest.raises(RuntimeError, match="authority"):
        CommitCoordinator(store).commit(request)

    _, _, _, state, episode = store.coherent_view(initialized.session.session_id)
    assert state.version == 0
    assert episode.status is EpisodeStatus.ACTIVE
