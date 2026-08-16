"""Reconstruct bounded provider context from coherent authoritative runtime records."""

# ruff: noqa: EM101, TRY003

from __future__ import annotations

from research_agent.runtime._canonical import canonical_bytes, content_digest
from research_agent.runtime.models import (
    ContextObservation,
    ContextPacket,
    EpisodeCheckpoint,
    EpisodeStatus,
    StructuredObservation,
)
from research_agent.runtime.store import CoherenceError, InMemoryRuntimeStore

DEFAULT_CONTEXT_BYTES = 32_000
DEFAULT_CHECKPOINT_OBSERVATIONS = 8
DEFAULT_CHECKPOINT_BYTES = 32_000


class ContextBuilder:
    """Build bounded provider-neutral context without transcript dependency."""

    def __init__(
        self,
        store: InMemoryRuntimeStore,
        *,
        max_observations: int = 8,
        max_packet_payload_bytes: int = DEFAULT_CONTEXT_BYTES,
        max_checkpoint_observations: int = DEFAULT_CHECKPOINT_OBSERVATIONS,
        max_checkpoint_payload_bytes: int = DEFAULT_CHECKPOINT_BYTES,
    ) -> None:
        """Configure deterministic count and byte bounds for working evidence."""
        if (
            min(
                max_observations,
                max_packet_payload_bytes,
                max_checkpoint_observations,
                max_checkpoint_payload_bytes,
            )
            < 1
        ):
            raise ValueError("Context and checkpoint bounds must be positive.")
        self._store = store
        self._max_observations = max_observations
        self._max_packet_payload_bytes = max_packet_payload_bytes
        self._max_checkpoint_observations = max_checkpoint_observations
        self._max_checkpoint_payload_bytes = max_checkpoint_payload_bytes

    def build_current_context(self, session_id: str) -> ContextPacket:
        """Reconstruct the current decision surface from system-owned truth."""
        task, environment, session, state, episode = self._store.coherent_view(session_id)
        if episode.status is not EpisodeStatus.ACTIVE:
            raise CoherenceError("Context requires an active research episode.")
        checkpoint_id = self._store.current_checkpoint_by_episode.get(episode.episode_id)
        checkpoint = (
            self._store.checkpoint_for_rebuild(session_id, checkpoint_id)
            if checkpoint_id is not None
            else None
        )
        observations = self._bounded_current_observations(episode.observation_ids, checkpoint)
        total_count = len(episode.observation_ids)
        omitted_count = total_count - len(observations)
        available_actions = available_actions_for(environment.capability_names)
        warnings = environment.warnings
        if omitted_count:
            warnings += (
                f"{omitted_count} earlier working observations are retained outside this packet.",
            )
        omitted_ref = (
            checkpoint.omitted_observations_ref
            if checkpoint is not None and checkpoint.omitted_observation_count
            else None
        )
        packet_semantics = {
            "session_id": session.session_id,
            "task_id": task.task_id,
            "task_version": task.version,
            "state_id": state.state_id,
            "state_version": state.version,
            "episode_id": episode.episode_id,
            "environment_ref": environment.snapshot_ref,
            "mission": state.mission,
            "constraints": state.constraints,
            "target_field_id": task.target_field_id,
            "forecast_horizon": task.forecast_horizon,
            "unresolved_semantics": state.unresolved_semantics,
            "committed_understanding": state.durable_understanding,
            "episode_objective": episode.objective,
            "episode_status": episode.status,
            "active_question": episode.active_question,
            "current_plan": episode.current_plan,
            "unresolved_questions": episode.unresolved_questions,
            "temporary_interpretations": episode.temporary_interpretations,
            "observation_digests": tuple(item.source_content_digest for item in observations),
            "total_observation_count": total_count,
            "checkpoint_ref": checkpoint_id,
            "permitted_dataset_refs": environment.readable_dataset_refs,
            "available_actions": available_actions,
            "protected_exposure_refs": state.protected_exposures,
            "protected_resource_refs": environment.protected_resource_refs,
            "warnings": warnings,
        }
        return ContextPacket(
            packet_id=content_digest(packet_semantics),
            session_id=session.session_id,
            task_id=task.task_id,
            task_version=task.version,
            state_id=state.state_id,
            state_version=state.version,
            episode_id=episode.episode_id,
            environment_ref=environment.snapshot_ref,
            mission=state.mission,
            constraints=state.constraints,
            target_field_id=task.target_field_id,
            forecast_horizon=task.forecast_horizon,
            unresolved_semantics=state.unresolved_semantics,
            committed_understanding=state.durable_understanding,
            episode_objective=episode.objective,
            episode_status=episode.status,
            active_question=episode.active_question,
            current_plan=episode.current_plan,
            unresolved_questions=episode.unresolved_questions,
            temporary_interpretations=episode.temporary_interpretations,
            working_observations=observations,
            total_observation_count=total_count,
            omitted_observation_count=omitted_count,
            checkpoint_ref=checkpoint_id,
            omitted_observations_ref=omitted_ref,
            permitted_dataset_refs=environment.readable_dataset_refs,
            available_actions=available_actions,
            protected_exposure_refs=state.protected_exposures,
            protected_resource_refs=environment.protected_resource_refs,
            warnings=warnings,
        )

    def checkpoint_current_episode(self, session_id: str) -> EpisodeCheckpoint:
        """Persist a bounded structured checkpoint of unresolved episode semantics."""
        task, environment, session, state, episode = self._store.coherent_view(session_id)
        if episode.status is not EpisodeStatus.ACTIVE:
            raise CoherenceError("Only an active research episode can be checkpointed.")
        current_id = self._store.current_checkpoint_by_episode.get(episode.episode_id)
        current = (
            self._store.checkpoint_for_rebuild(session_id, current_id)
            if current_id is not None
            else None
        )
        if current is not None and current.observation_count == len(episode.observation_ids):
            return current

        candidate_observations = self._load_tail(
            episode.observation_ids,
            self._max_checkpoint_observations,
            self._max_checkpoint_payload_bytes,
        )
        total_count = len(episode.observation_ids)
        retained_count = len(candidate_observations)
        omitted_count = total_count - retained_count
        omitted_ref: str | None = None
        if omitted_count:
            omitted_chain = self._store.observation_chain_by_episode_count[
                (episode.episode_id, omitted_count)
            ]
            omitted_descriptor = (episode.episode_id, omitted_count, omitted_chain)
            omitted_ref = f"artifact:episode-history:{content_digest(omitted_descriptor)}"
            self._store.put_artifact(omitted_ref, omitted_descriptor)

        checkpoint = EpisodeCheckpoint(
            checkpoint_id="",
            checkpoint_version=1 if current is None else current.checkpoint_version + 1,
            supersedes_checkpoint_id=current_id,
            session_id=session.session_id,
            task_id=task.task_id,
            task_version=task.version,
            task_content_digest=content_digest(task),
            episode_id=episode.episode_id,
            environment_ref=environment.snapshot_ref,
            environment_content_digest=content_digest(environment),
            state_id=state.state_id,
            state_version=state.version,
            state_content_digest=content_digest(state),
            episode_transition_count=episode.transition_count,
            objective=episode.objective,
            active_question=episode.active_question,
            current_plan=episode.current_plan,
            unresolved_questions=episode.unresolved_questions,
            temporary_interpretations=episode.temporary_interpretations,
            observations=candidate_observations,
            observation_count=total_count,
            retained_observation_count=retained_count,
            omitted_observation_count=omitted_count,
            omitted_observations_ref=omitted_ref,
            covered_observation_digest=episode.observation_chain_digest,
            permitted_dataset_refs=environment.readable_dataset_refs,
            available_actions=available_actions_for(environment.capability_names),
            warnings=environment.warnings,
            constraints=state.constraints,
            unresolved_semantics=state.unresolved_semantics,
            protected_exposure_refs=state.protected_exposures,
            protected_resource_refs=environment.protected_resource_refs,
        )
        return self._store.publish_checkpoint(checkpoint)

    def rebuild_from_checkpoint(self, session_id: str, checkpoint_id: str) -> ContextPacket:
        """Reject a stale base, then rebuild using checkpoint plus later evidence."""
        checkpoint = self._store.checkpoint_for_rebuild(session_id, checkpoint_id)
        packet = self.build_current_context(session_id)
        if packet.checkpoint_ref != checkpoint.checkpoint_id:
            raise CoherenceError("Rebuilt packet did not use the requested current checkpoint.")
        return packet

    def _bounded_current_observations(
        self,
        observation_ids: tuple[str, ...],
        checkpoint: EpisodeCheckpoint | None,
    ) -> tuple[ContextObservation, ...]:
        if checkpoint is None:
            return self._load_tail(
                observation_ids,
                self._max_observations,
                self._max_packet_payload_bytes,
            )
        later_ids = observation_ids[checkpoint.observation_count :]
        if len(later_ids) >= self._max_observations:
            return self._load_tail(
                later_ids,
                self._max_observations,
                self._max_packet_payload_bytes,
            )
        later = tuple(self._load_observation(item) for item in later_ids)
        candidates = (*checkpoint.observations, *later)
        return _bounded_tail(
            candidates,
            self._max_observations,
            self._max_packet_payload_bytes,
        )

    def _load_tail(
        self,
        observation_ids: tuple[str, ...],
        count_bound: int,
        byte_bound: int,
    ) -> tuple[ContextObservation, ...]:
        candidates = tuple(
            self._load_observation(observation_id)
            for observation_id in observation_ids[-count_bound:]
        )
        return _bounded_tail(candidates, count_bound, byte_bound)

    def _load_observation(self, observation_id: str) -> ContextObservation:
        observation = self._store.observations.get(observation_id)
        if observation is None:
            raise CoherenceError("Episode references a missing working observation.")
        try:
            observation.verify_content_identity()
        except ValueError as error:
            raise CoherenceError(str(error)) from error
        return self._project_observation(observation)

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


def available_actions_for(capability_names: tuple[str, ...]) -> tuple[str, ...]:
    """Project exact runtime capability names into the supported action surface."""
    actions = tuple(
        action
        for action in (
            "inspect_dataset",
            "run_analysis",
            "run_authored_development_trial",
            "run_scientific_workflow",
        )
        if action in capability_names
    )
    return (*actions, "propose_episode_transition")


def _bounded_tail(
    observations: tuple[ContextObservation, ...],
    count_bound: int,
    byte_bound: int,
) -> tuple[ContextObservation, ...]:
    retained: list[ContextObservation] = []
    retained_bytes = 0
    for observation in reversed(observations[-count_bound:]):
        size = len(canonical_bytes(observation))
        if retained_bytes + size > byte_bound:
            break
        retained.append(observation)
        retained_bytes += size
    retained.reverse()
    return tuple(retained)


__all__ = ["ContextBuilder", "available_actions_for"]
