"""Independent validation and atomic, idempotent semantic commit."""

# ruff: noqa: EM101, TRY003

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from hashlib import sha256
from typing import TYPE_CHECKING
from uuid import uuid4

from research_agent.runtime.models import (
    EpisodeStatus,
    FailureCode,
    Recoverability,
    ResearchEpisode,
    StructuredFailure,
)
from research_agent.runtime.store import (
    InjectedPersistenceError,
    InMemoryRuntimeStore,
    StoredCommit,
)

if TYPE_CHECKING:
    from research_agent.runtime.actions import EpisodeTransitionProposal, StateUpdateProposal


@dataclass(frozen=True, slots=True)
class CommitRequest:
    """One explicit semantic boundary with independently optional state change."""

    session_id: str
    episode_id: str
    transition: EpisodeTransitionProposal
    state_update: StateUpdateProposal | None
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class CommitResult:
    """Observable outcome of one semantic commit request."""

    commit_id: str | None
    committed: bool
    replayed: bool
    episode_status: EpisodeStatus
    state_version: int
    failure: StructuredFailure | None = None


class EpisodeTransitionValidator:
    """Validate lifecycle authority without constructing state deltas."""

    def validate(
        self, current: EpisodeStatus, proposal: EpisodeTransitionProposal
    ) -> StructuredFailure | None:
        """Return no failure only for ACTIVE to terminal transitions."""
        allowed = {
            EpisodeStatus.RESOLVED,
            EpisodeStatus.ABANDONED,
            EpisodeStatus.SUSPENDED,
        }
        if current is not EpisodeStatus.ACTIVE or proposal.target_status not in allowed:
            return StructuredFailure(
                FailureCode.INVALID_EPISODE_TRANSITION,
                "Requested episode lifecycle transition is not legal.",
                Recoverability.REPAIRABLE,
            )
        if not proposal.synthesis.strip():
            return StructuredFailure(
                FailureCode.INVALID_EPISODE_TRANSITION,
                "A semantic transition requires a non-empty synthesis.",
                Recoverability.REPAIRABLE,
            )
        return None


class StateUpdateValidator:
    """Validate evidence-backed durable-state changes without persistence."""

    def validate(
        self,
        *,
        current_version: int,
        proposal: StateUpdateProposal,
        allowed_evidence_refs: frozenset[str],
    ) -> StructuredFailure | None:
        """Reject stale versions and evidence outside the active episode."""
        if proposal.starting_state_version != current_version:
            return StructuredFailure(
                FailureCode.STALE_STATE_VERSION,
                "State proposal does not start from the current state version.",
                Recoverability.REPAIRABLE,
            )
        if not proposal.evidence_refs or not set(proposal.evidence_refs) <= allowed_evidence_refs:
            return StructuredFailure(
                FailureCode.INVALID_EVIDENCE_REFERENCE,
                "State proposal cites missing or unauthorized working evidence.",
                Recoverability.REPAIRABLE,
            )
        if not proposal.durable_understanding:
            return StructuredFailure(
                FailureCode.INVALID_REQUEST,
                "State proposal contains no durable understanding.",
                Recoverability.REPAIRABLE,
            )
        return None


class CommitCoordinator:
    """Own validation and coherent publication of one semantic boundary."""

    def __init__(self, store: InMemoryRuntimeStore) -> None:
        """Configure independent validators over one atomic persistence boundary."""
        self._store = store
        self._episode_validator = EpisodeTransitionValidator()
        self._state_validator = StateUpdateValidator()

    def commit(self, request: CommitRequest) -> CommitResult:
        """Validate and publish both effects exactly once, or neither effect."""
        semantic_digest = _commit_digest(request)
        scoped_key = f"{request.session_id}:{request.idempotency_key}"
        with self._store.lock:
            _, _, session, state, episode = self._store.coherent_view(request.session_id)
            prior = self._store.commits.get(scoped_key)
            if prior is not None:
                if prior.semantic_digest != semantic_digest:
                    return self._reject(
                        request,
                        episode.status,
                        state.version,
                        StructuredFailure(
                            FailureCode.IDEMPOTENCY_CONFLICT,
                            "Idempotency key was reused with changed semantic payload.",
                            Recoverability.NON_RETRYABLE,
                        ),
                    )
                prior_result = prior.result
                if not isinstance(prior_result, CommitResult):
                    raise TypeError("Stored commit result has an invalid type.")
                return replace(prior_result, replayed=True)
            if request.episode_id != session.episode_id:
                return self._reject(
                    request,
                    episode.status,
                    state.version,
                    StructuredFailure(
                        FailureCode.INVALID_REQUEST,
                        "Commit episode identity does not match the session.",
                        Recoverability.REPAIRABLE,
                    ),
                )
            transition_failure = self._episode_validator.validate(
                episode.status, request.transition
            )
            allowed_evidence = self._allowed_evidence_refs(episode)
            if not set(request.transition.evidence_refs) <= allowed_evidence:
                transition_failure = StructuredFailure(
                    FailureCode.INVALID_EVIDENCE_REFERENCE,
                    "Episode transition cites missing or unauthorized working evidence.",
                    Recoverability.REPAIRABLE,
                )
            state_failure = (
                None
                if request.state_update is None
                else self._state_validator.validate(
                    current_version=state.version,
                    proposal=request.state_update,
                    allowed_evidence_refs=allowed_evidence,
                )
            )
            failure = transition_failure or state_failure
            if failure is not None:
                return self._reject(request, episode.status, state.version, failure)
            if self._store.fail_next_commit:
                self._store.fail_next_commit = False
                raise InjectedPersistenceError("Injected semantic commit publication failure.")

            next_episode = replace(
                episode,
                status=request.transition.target_status,
                temporary_interpretations=(
                    *episode.temporary_interpretations,
                    request.transition.synthesis,
                ),
                transition_count=episode.transition_count + 1,
            )
            next_state = state
            if request.state_update is not None:
                next_state = replace(
                    state,
                    version=state.version + 1,
                    durable_understanding=(
                        *state.durable_understanding,
                        *request.state_update.durable_understanding,
                    ),
                    evidence_refs=tuple(
                        dict.fromkeys((*state.evidence_refs, *request.state_update.evidence_refs))
                    ),
                )
            result = CommitResult(
                commit_id=str(uuid4()),
                committed=True,
                replayed=False,
                episode_status=next_episode.status,
                state_version=next_state.version,
            )
            self._store.publish_semantic_commit(
                session_id=request.session_id,
                state_id=state.state_id,
                episode_id=episode.episode_id,
                next_state=next_state,
                next_episode=next_episode,
                scoped_key=scoped_key,
                stored_commit=StoredCommit(semantic_digest, result),
                event_detail={
                    "commit_id": result.commit_id or "",
                    "state_version": next_state.version,
                    "episode_status": next_episode.status.value,
                },
            )
            return result

    def _allowed_evidence_refs(self, episode: ResearchEpisode) -> frozenset[str]:
        refs = set(episode.observation_ids)
        for observation_id in episode.observation_ids:
            observation = self._store.observations.get(observation_id)
            if observation is None:
                raise RuntimeError("Episode evidence is missing from the authoritative store.")
            observation.verify_content_identity()
            if (
                observation.session_id != episode.session_id
                or observation.episode_id != episode.episode_id
                or observation.environment_ref != episode.environment_ref
            ):
                raise RuntimeError("Episode evidence authority is incoherent.")
            refs.update(observation.artifact_refs)
        return frozenset(refs)

    def _reject(
        self,
        request: CommitRequest,
        status: EpisodeStatus,
        state_version: int,
        failure: StructuredFailure,
    ) -> CommitResult:
        self._store.append_event_unlocked(
            request.session_id,
            "commit.rejected",
            {"failure_code": failure.code.value, "idempotency_key": request.idempotency_key},
        )
        return CommitResult(
            commit_id=None,
            committed=False,
            replayed=False,
            episode_status=status,
            state_version=state_version,
            failure=failure,
        )


def _commit_digest(request: CommitRequest) -> str:
    state_update = request.state_update
    value = {
        "session_id": request.session_id,
        "episode_id": request.episode_id,
        "target_status": request.transition.target_status.value,
        "synthesis": request.transition.synthesis,
        "transition_evidence": request.transition.evidence_refs,
        "state_update": None
        if state_update is None
        else {
            "starting_state_version": state_update.starting_state_version,
            "durable_understanding": state_update.durable_understanding,
            "evidence_refs": state_update.evidence_refs,
        },
    }
    return sha256(json.dumps(value, sort_keys=True, default=list).encode()).hexdigest()


__all__ = [
    "CommitCoordinator",
    "CommitRequest",
    "CommitResult",
    "EpisodeTransitionValidator",
    "StateUpdateValidator",
]
