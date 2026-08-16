"""Narrow in-memory persistence proving Milestone 1 coherence and atomicity."""

# ruff: noqa: EM101, EM102, TRY003

from __future__ import annotations

from dataclasses import dataclass, replace
from threading import RLock
from typing import TYPE_CHECKING

from research_agent.runtime._canonical import content_digest
from research_agent.runtime.models import (
    ContextObservation,
    EpisodeCheckpoint,
    ResearchEnvironmentSnapshot,
    ResearchEpisode,
    ResearcherState,
    ResearchSession,
    RuntimeInitialization,
    StructuredObservation,
    TrajectoryEvent,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from research_agent.task_compilation import ResearchTask


class StoreError(RuntimeError):
    """Base explicit persistence error."""


class NotFoundError(StoreError):
    """Required authoritative record does not exist."""


class CoherenceError(StoreError):
    """Loaded records do not describe one coherent session view."""


class InjectedPersistenceError(StoreError):
    """Test-only failure before or during in-process atomic publication."""


class StaleCheckpointError(CoherenceError):
    """Checkpoint is no longer the current reconstruction base."""


@dataclass(frozen=True, slots=True)
class StoredCommit:
    """Successful idempotent commit payload and public result."""

    semantic_digest: str
    result: object


class InMemoryRuntimeStore:
    """One lock-protected store with coherent copy-on-write publication."""

    def __init__(self) -> None:
        """Initialize empty logical stores behind one coherence lock."""
        self.lock = RLock()
        self.tasks: dict[str, ResearchTask] = {}
        self.environments: dict[str, ResearchEnvironmentSnapshot] = {}
        self.sessions: dict[str, ResearchSession] = {}
        self.states: dict[str, ResearcherState] = {}
        self.episodes: dict[str, ResearchEpisode] = {}
        self.observations: dict[str, StructuredObservation] = {}
        self.observation_deliveries: dict[str, tuple[str, str]] = {}
        self.observation_chain_by_episode_count: dict[tuple[str, int], str] = {}
        self.checkpoints: dict[str, EpisodeCheckpoint] = {}
        self.current_checkpoint_by_episode: dict[str, str] = {}
        self.artifacts: dict[str, object] = {}
        self.trajectory: list[TrajectoryEvent] = []
        self.initializations: dict[str, tuple[str, RuntimeInitialization]] = {}
        self.commits: dict[str, StoredCommit] = {}
        self.fail_next_initialization = False
        self.fail_next_commit = False
        self.fail_commit_after_stage: str | None = None

    def register_task_and_environment(
        self,
        task: ResearchTask,
        environment: ResearchEnvironmentSnapshot,
    ) -> None:
        """Register immutable inputs used by runtime initialization."""
        with self.lock:
            self.tasks[task.task_id] = task
            self.environments[environment.snapshot_ref] = environment

    def publish_initialization(
        self,
        request_id: str,
        semantic_digest: str,
        initialization: RuntimeInitialization,
    ) -> RuntimeInitialization:
        """Publish all initialization records together and replay exactly."""
        with self.lock:
            prior = self.initializations.get(request_id)
            if prior is not None:
                prior_digest, prior_result = prior
                if prior_digest != semantic_digest:
                    msg = "Initialization request identity was reused with changed semantics."
                    raise CoherenceError(msg)
                return prior_result
            if self.fail_next_initialization:
                self.fail_next_initialization = False
                raise InjectedPersistenceError("Injected initialization publication failure.")
            session = initialization.session
            if (
                session.state_id != initialization.state.state_id
                or session.episode_id != initialization.episode.episode_id
            ):
                raise CoherenceError("Initialization records are not mutually linked.")
            self.sessions[session.session_id] = session
            self.states[initialization.state.state_id] = initialization.state
            self.episodes[initialization.episode.episode_id] = initialization.episode
            self.observation_chain_by_episode_count[(session.episode_id, 0)] = (
                initialization.episode.observation_chain_digest
            )
            self.initializations[request_id] = (semantic_digest, initialization)
            self.append_event_unlocked(
                session.session_id,
                "runtime.initialized",
                {"request_id": request_id, "state_version": 0},
            )
            return initialization

    def coherent_view(
        self,
        session_id: str,
    ) -> tuple[
        ResearchTask,
        ResearchEnvironmentSnapshot,
        ResearchSession,
        ResearcherState,
        ResearchEpisode,
    ]:
        """Load one mutually coherent authoritative session snapshot."""
        with self.lock:
            session = self.sessions.get(session_id)
            if session is None:
                raise NotFoundError(f"Session {session_id!r} was not found.")
            task = self.tasks.get(session.task_id)
            environment = self.environments.get(session.environment_ref)
            state = self.states.get(session.state_id)
            episode = self.episodes.get(session.episode_id)
            if task is None or environment is None or state is None or episode is None:
                raise CoherenceError("Session is missing a required authoritative record.")
            expected = (session.session_id, session.task_id, session.environment_ref)
            if (
                (state.session_id, state.task_id, state.environment_ref) != expected
                or (episode.session_id, episode.task_id, episode.environment_ref) != expected
                or session.task_version != task.version
                or state.task_version != task.version
                or episode.task_version != task.version
                or state.version < episode.starting_state_version
            ):
                raise CoherenceError("Session, state, episode, or environment identity mismatched.")
            return task, environment, session, state, episode

    def record_observation(
        self, session_id: str, observation: StructuredObservation
    ) -> ResearchEpisode:
        """Append working evidence to the episode without changing durable state."""
        with self.lock:
            _, environment, session, state, episode = self.coherent_view(session_id)
            if episode.status.value != "active":
                raise CoherenceError("A terminal episode cannot receive working evidence.")
            try:
                observation.verify_content_identity()
            except ValueError as error:
                raise CoherenceError(str(error)) from error
            if (
                observation.session_id != session.session_id
                or observation.episode_id != episode.episode_id
                or observation.environment_ref != environment.snapshot_ref
            ):
                raise CoherenceError("Observation authority does not match the active episode.")
            prior_delivery = self.observation_deliveries.get(observation.delivery_id)
            if prior_delivery is not None:
                if prior_delivery != (observation.content_digest, observation.observation_id):
                    raise CoherenceError(
                        "Observation delivery identity was reused with changed semantics."
                    )
                return episode
            prior_observation = self.observations.get(observation.observation_id)
            if prior_observation is not None:
                if prior_observation.content_digest != observation.content_digest:
                    raise CoherenceError("Observation identity was reused with changed semantics.")
                return episode
            self.observations[observation.observation_id] = observation
            self.observation_deliveries[observation.delivery_id] = (
                observation.content_digest,
                observation.observation_id,
            )
            next_count = len(episode.observation_ids) + 1
            next_chain = _next_observation_chain_digest(
                episode.observation_chain_digest,
                observation,
            )
            updated = replace(
                episode,
                observation_ids=(*episode.observation_ids, observation.observation_id),
                observation_chain_digest=next_chain,
            )
            self.episodes[session.episode_id] = updated
            self.observation_chain_by_episode_count[(episode.episode_id, next_count)] = next_chain
            self.append_event_unlocked(
                session_id,
                "episode.observation-recorded",
                {
                    "observation_id": observation.observation_id,
                    "state_version_unchanged": state.version,
                },
            )
            return updated

    def put_artifact(self, artifact_ref: str, artifact: object) -> None:
        """Persist drill-down material outside model context."""
        with self.lock:
            existing = self.artifacts.get(artifact_ref)
            if existing is not None and existing != artifact:
                raise CoherenceError("Artifact identity was reused with changed content.")
            self.artifacts[artifact_ref] = artifact

    def publish_semantic_commit(  # noqa: PLR0913
        self,
        *,
        session_id: str,
        state_id: str,
        episode_id: str,
        next_state: ResearcherState,
        next_episode: ResearchEpisode,
        scoped_key: str,
        stored_commit: StoredCommit,
        event_detail: Mapping[str, object],
    ) -> None:
        """Publish one semantic boundary or restore every prior table reference.

        This is an in-process atomicity boundary.  All replacement tables and the
        trajectory event are staged before the first visible assignment.  Any
        exception—including the explicit stage faults used by causal tests—restores
        the exact prior table references before control leaves the store lock.
        """
        with self.lock:
            if next_state.state_id != state_id or next_episode.episode_id != episode_id:
                raise CoherenceError("Semantic commit records do not match their exact keys.")
            if (
                next_state.session_id != session_id
                or next_episode.session_id != session_id
                or next_state.environment_ref != next_episode.environment_ref
                or next_state.task_id != next_episode.task_id
                or next_state.task_version != next_episode.task_version
            ):
                raise CoherenceError("Semantic commit records are not mutually coherent.")
            next_episodes = dict(self.episodes)
            next_states = dict(self.states)
            next_commits = dict(self.commits)
            next_episodes[episode_id] = next_episode
            next_states[state_id] = next_state
            next_commits[scoped_key] = stored_commit
            event = TrajectoryEvent(
                len(self.trajectory) + 1,
                session_id,
                "commit.published",
                dict(event_detail),
            )
            next_trajectory = [*self.trajectory, event]
            prior = (self.episodes, self.states, self.commits, self.trajectory)
            try:
                self.episodes = next_episodes
                self._raise_commit_stage_fault("episode")
                self.states = next_states
                self._raise_commit_stage_fault("state")
                self.commits = next_commits
                self._raise_commit_stage_fault("commit")
                self.trajectory = next_trajectory
                self._raise_commit_stage_fault("event")
            except Exception:
                self.episodes, self.states, self.commits, self.trajectory = prior
                raise

    def _raise_commit_stage_fault(self, stage: str) -> None:
        if self.fail_commit_after_stage != stage:
            return
        self.fail_commit_after_stage = None
        msg = f"Injected semantic commit failure after {stage} staging."
        raise InjectedPersistenceError(msg)

    def publish_checkpoint(self, checkpoint: EpisodeCheckpoint) -> EpisodeCheckpoint:
        """Publish one coherent current checkpoint without deleting underlying evidence."""
        with self.lock:
            try:
                checkpoint.verify_content_identity()
            except ValueError as error:
                raise CoherenceError(str(error)) from error
            existing = self.checkpoints.get(checkpoint.checkpoint_id)
            if existing is not None:
                if existing != checkpoint:
                    raise CoherenceError("Checkpoint identity was reused with changed semantics.")
                return existing
            task, environment, session, state, episode = self.coherent_view(checkpoint.session_id)
            current_id = self.current_checkpoint_by_episode.get(episode.episode_id)
            current = self.checkpoints.get(current_id) if current_id is not None else None
            expected_version = 1 if current is None else current.checkpoint_version + 1
            retained_ids = episode.observation_ids[
                checkpoint.observation_count
                - checkpoint.retained_observation_count : checkpoint.observation_count
            ]
            expected_observations = tuple(
                self._project_observation(self._verified_observation(item, episode))
                for item in retained_ids
            )
            expected_actions = _available_actions(environment.capability_names)
            expected_chain = self.observation_chain_by_episode_count.get(
                (episode.episode_id, checkpoint.observation_count)
            )
            if (
                checkpoint.task_id != task.task_id
                or checkpoint.task_version != task.version
                or checkpoint.task_content_digest != content_digest(task)
                or checkpoint.episode_id != episode.episode_id
                or checkpoint.environment_ref != environment.snapshot_ref
                or checkpoint.environment_content_digest != content_digest(environment)
                or checkpoint.state_id != state.state_id
                or checkpoint.state_version != state.version
                or checkpoint.state_content_digest != content_digest(state)
                or checkpoint.episode_transition_count != episode.transition_count
                or checkpoint.objective != episode.objective
                or checkpoint.active_question != episode.active_question
                or checkpoint.current_plan != episode.current_plan
                or checkpoint.unresolved_questions != episode.unresolved_questions
                or checkpoint.temporary_interpretations != episode.temporary_interpretations
                or checkpoint.observation_count != len(episode.observation_ids)
                or checkpoint.retained_observation_count != len(checkpoint.observations)
                or checkpoint.omitted_observation_count
                != checkpoint.observation_count - checkpoint.retained_observation_count
                or checkpoint.observations != expected_observations
                or checkpoint.covered_observation_digest != expected_chain
                or checkpoint.checkpoint_version != expected_version
                or checkpoint.supersedes_checkpoint_id != current_id
            ):
                raise StaleCheckpointError(
                    "Checkpoint does not describe the current authoritative episode."
                )
            if (
                checkpoint.permitted_dataset_refs != environment.readable_dataset_refs
                or checkpoint.available_actions != expected_actions
                or checkpoint.warnings != environment.warnings
                or checkpoint.protected_resource_refs != environment.protected_resource_refs
                or checkpoint.constraints != state.constraints
                or checkpoint.unresolved_semantics != state.unresolved_semantics
                or checkpoint.protected_exposure_refs != state.protected_exposures
            ):
                raise CoherenceError(
                    "Checkpoint authority differs from current authoritative state."
                )
            expected_omitted_descriptor = self._omitted_evidence_descriptor(
                episode,
                checkpoint.omitted_observation_count,
            )
            if expected_omitted_descriptor is not None:
                if (
                    checkpoint.omitted_observations_ref is None
                    or self.artifacts.get(checkpoint.omitted_observations_ref)
                    != expected_omitted_descriptor
                ):
                    raise CoherenceError(
                        "Checkpoint omitted-evidence reference is not authoritative."
                    )
            elif checkpoint.omitted_observations_ref is not None:
                raise CoherenceError("Checkpoint has an unnecessary omitted-evidence reference.")
            self.checkpoints[checkpoint.checkpoint_id] = checkpoint
            self.current_checkpoint_by_episode[episode.episode_id] = checkpoint.checkpoint_id
            self.append_event_unlocked(
                session.session_id,
                "context.episode-checkpointed",
                {
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "checkpoint_version": checkpoint.checkpoint_version,
                    "observation_count": checkpoint.observation_count,
                },
            )
            return checkpoint

    def checkpoint_for_rebuild(
        self,
        session_id: str,
        checkpoint_id: str,
    ) -> EpisodeCheckpoint:
        """Load only the current coherent checkpoint for a session."""
        with self.lock:
            task, environment, _, state, episode = self.coherent_view(session_id)
            checkpoint = self.checkpoints.get(checkpoint_id)
            current_id = self.current_checkpoint_by_episode.get(episode.episode_id)
            if checkpoint is None:
                raise NotFoundError(f"Checkpoint {checkpoint_id!r} was not found.")
            try:
                checkpoint.verify_content_identity()
            except ValueError as error:
                raise CoherenceError(str(error)) from error
            expected_chain = self.observation_chain_by_episode_count.get(
                (episode.episode_id, checkpoint.observation_count)
            )
            retained_ids = episode.observation_ids[
                checkpoint.observation_count
                - checkpoint.retained_observation_count : checkpoint.observation_count
            ]
            expected_observations = tuple(
                self._project_observation(self._verified_observation(item, episode))
                for item in retained_ids
            )
            expected_omitted_descriptor = self._omitted_evidence_descriptor(
                episode,
                checkpoint.omitted_observation_count,
            )
            if (
                current_id != checkpoint_id
                or checkpoint.session_id != session_id
                or checkpoint.task_id != task.task_id
                or checkpoint.task_version != task.version
                or checkpoint.task_content_digest != content_digest(task)
                or checkpoint.episode_id != episode.episode_id
                or checkpoint.environment_ref != environment.snapshot_ref
                or checkpoint.environment_content_digest != content_digest(environment)
                or checkpoint.state_id != state.state_id
                or checkpoint.state_version != state.version
                or checkpoint.state_content_digest != content_digest(state)
                or checkpoint.episode_transition_count != episode.transition_count
                or checkpoint.objective != episode.objective
                or checkpoint.active_question != episode.active_question
                or checkpoint.current_plan != episode.current_plan
                or checkpoint.unresolved_questions != episode.unresolved_questions
                or checkpoint.temporary_interpretations != episode.temporary_interpretations
                or checkpoint.observation_count > len(episode.observation_ids)
                or checkpoint.retained_observation_count != len(checkpoint.observations)
                or checkpoint.omitted_observation_count
                != checkpoint.observation_count - checkpoint.retained_observation_count
                or checkpoint.covered_observation_digest != expected_chain
                or checkpoint.observations != expected_observations
                or checkpoint.permitted_dataset_refs != environment.readable_dataset_refs
                or checkpoint.available_actions != _available_actions(environment.capability_names)
                or checkpoint.warnings != environment.warnings
                or checkpoint.protected_resource_refs != environment.protected_resource_refs
                or checkpoint.constraints != state.constraints
                or checkpoint.unresolved_semantics != state.unresolved_semantics
                or checkpoint.protected_exposure_refs != state.protected_exposures
                or (
                    checkpoint.omitted_observations_ref is not None
                    and self.artifacts.get(checkpoint.omitted_observations_ref)
                    != expected_omitted_descriptor
                )
                or (
                    (expected_omitted_descriptor is not None)
                    != (checkpoint.omitted_observations_ref is not None)
                )
            ):
                raise StaleCheckpointError("Checkpoint is stale for current reconstruction.")
            return checkpoint

    def _omitted_evidence_descriptor(
        self,
        episode: ResearchEpisode,
        omitted_count: int,
    ) -> tuple[str, int, str] | None:
        if omitted_count == 0:
            return None
        chain_digest = self.observation_chain_by_episode_count.get(
            (episode.episode_id, omitted_count)
        )
        if chain_digest is None:
            raise CoherenceError("Omitted evidence chain identity is unavailable.")
        return (episode.episode_id, omitted_count, chain_digest)

    def _verified_observation(
        self,
        observation_id: str,
        episode: ResearchEpisode,
    ) -> StructuredObservation:
        observation = self.observations.get(observation_id)
        if observation is None:
            raise CoherenceError("Checkpoint references missing authoritative evidence.")
        try:
            observation.verify_content_identity()
        except ValueError as error:
            raise CoherenceError(str(error)) from error
        if (
            observation.session_id != episode.session_id
            or observation.episode_id != episode.episode_id
            or observation.environment_ref != episode.environment_ref
        ):
            raise CoherenceError("Checkpoint evidence authority is incoherent.")
        return observation

    @staticmethod
    def _project_observation(observation: StructuredObservation) -> ContextObservation:
        return ContextObservation(
            observation_id=observation.observation_id,
            status=observation.status,
            observation_type=observation.observation_type,
            summary=observation.summary,
            payload=observation.payload,
            warnings=observation.warnings,
            provenance=observation.provenance,
            artifact_refs=observation.artifact_refs,
            recoverability=observation.recoverability,
            failure=observation.failure,
            epistemic_status=observation.epistemic_status,
            source_content_digest=observation.content_digest,
        )

    def append_event(
        self,
        session_id: str,
        event_type: str,
        detail: Mapping[str, object],
    ) -> TrajectoryEvent:
        """Append one trajectory event in causal order."""
        with self.lock:
            return self.append_event_unlocked(session_id, event_type, detail)

    def events_for(self, session_id: str) -> tuple[TrajectoryEvent, ...]:
        """Return session events without placing them in ContextPacket."""
        with self.lock:
            return tuple(event for event in self.trajectory if event.session_id == session_id)

    def append_event_unlocked(
        self,
        session_id: str,
        event_type: str,
        detail: Mapping[str, object],
    ) -> TrajectoryEvent:
        """Append while the caller already owns the store coherence lock."""
        event = TrajectoryEvent(len(self.trajectory) + 1, session_id, event_type, dict(detail))
        self.trajectory.append(event)
        return event


def _next_observation_chain_digest(
    previous_digest: str,
    observation: StructuredObservation,
) -> str:
    """Extend one episode's ordered evidence identity in constant time."""
    return content_digest((previous_digest, observation.observation_id, observation.content_digest))


def _available_actions(capability_names: tuple[str, ...]) -> tuple[str, ...]:
    actions = tuple(
        action
        for action in ("inspect_dataset", "run_analysis", "run_scientific_workflow")
        if action in capability_names
    )
    return (*actions, "propose_episode_transition")


__all__ = [
    "CoherenceError",
    "InMemoryRuntimeStore",
    "InjectedPersistenceError",
    "NotFoundError",
    "StaleCheckpointError",
    "StoreError",
    "StoredCommit",
]
