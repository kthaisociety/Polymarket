"""Primary autonomous turn and bounded-episode orchestration seams."""

# ruff: noqa: EM101, TRY003

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from research_agent.runtime.actions import (
    ActionDecodeError,
    InspectDatasetAction,
    RunAnalysisAction,
    RunAuthoredDevelopmentTrialAction,
    RunScientificWorkflowAction,
    decode_action,
)
from research_agent.runtime.commit import CommitCoordinator, CommitRequest, CommitResult
from research_agent.runtime.models import (
    EpisodeStatus,
    FailureCode,
    ObservationStatus,
    Recoverability,
    StructuredFailure,
    StructuredObservation,
)
from research_agent.runtime.provider import ModelProvider, ProviderUnavailableError

if TYPE_CHECKING:
    from research_agent.runtime.capabilities import ActionRouter
    from research_agent.runtime.context import ContextBuilder
    from research_agent.runtime.store import InMemoryRuntimeStore


@dataclass(frozen=True, slots=True)
class TurnResult:
    """Observable result of exactly one autonomous model decision."""

    session_id: str
    action_kind: str | None
    observation: StructuredObservation | None
    commit_result: CommitResult | None


@dataclass(frozen=True, slots=True)
class EpisodeRunResult:
    """Bounded run result with all turn results."""

    session_id: str
    terminal_status: EpisodeStatus
    turns: tuple[TurnResult, ...]


class AutonomousResearchRuntime:
    """Central progression authority for the Milestone 1 autonomous loop."""

    def __init__(
        self,
        store: InMemoryRuntimeStore,
        provider: ModelProvider,
        context_builder: ContextBuilder,
        router: ActionRouter,
        commit_coordinator: CommitCoordinator,
    ) -> None:
        """Bind provider intelligence to runtime-owned authority and progression."""
        self._store = store
        self._provider = provider
        self._context_builder = context_builder
        self._router = router
        self._commit_coordinator = commit_coordinator

    def advance_one_turn(self, session_id: str) -> TurnResult:  # noqa: C901, PLR0911
        """Reconstruct context, request one action, and progress through governed paths."""
        packet = self._context_builder.build_current_context(session_id)
        self._store.append_event(
            session_id,
            "model.call-started",
            {"packet_id": packet.packet_id},
        )
        try:
            response = self._provider.complete(packet)
        except ProviderUnavailableError:
            return self._record_runtime_failure(
                session_id,
                "provider-call",
                FailureCode.PROVIDER_UNAVAILABLE,
                "The model provider is unavailable.",
            )
        except (TypeError, ValueError):
            return self._record_runtime_failure(
                session_id,
                "provider-response",
                FailureCode.MALFORMED_MODEL_RESPONSE,
                "The model provider returned a malformed response.",
            )
        self._store.append_event(
            session_id,
            "model.call-completed",
            {"packet_id": packet.packet_id},
        )
        try:
            action = decode_action(response)
        except ActionDecodeError:
            return self._record_runtime_failure(
                session_id,
                "action-decode",
                FailureCode.MALFORMED_MODEL_RESPONSE,
                "The requested action could not be decoded safely.",
            )
        if action.session_id != session_id or action.episode_id != packet.episode_id:
            return self._record_runtime_failure(
                session_id,
                action.action_id,
                FailureCode.INVALID_REQUEST,
                "Action identity does not match the current context.",
            )
        if isinstance(action, InspectDatasetAction):
            observation = self._router.execute_inspection(action)
            self._store.record_observation(session_id, observation)
            return TurnResult(session_id, "inspect_dataset", observation, None)
        if isinstance(action, RunAnalysisAction):
            observation = self._router.execute_analysis(action)
            self._store.record_observation(session_id, observation)
            return TurnResult(session_id, "run_analysis", observation, None)
        if isinstance(action, RunAuthoredDevelopmentTrialAction):
            observation = self._router.execute_authored_development_trial(action)
            self._store.record_observation(session_id, observation)
            return TurnResult(
                session_id,
                "run_authored_development_trial",
                observation,
                None,
            )
        if isinstance(action, RunScientificWorkflowAction):
            observation = self._router.execute_scientific_workflow(action)
            self._store.record_observation(session_id, observation)
            return TurnResult(session_id, "run_scientific_workflow", observation, None)
        request = CommitRequest(
            session_id=action.session_id,
            episode_id=action.episode_id,
            transition=action.transition,
            state_update=action.state_update,
            idempotency_key=action.idempotency_key,
        )
        result = self._commit_coordinator.commit(request)
        if result.committed:
            return TurnResult(session_id, "propose_episode_transition", None, result)
        failure = result.failure
        if failure is None:
            raise RuntimeError("Rejected commit did not provide a structured failure.")
        _, environment, session, _, episode = self._store.coherent_view(session_id)
        observation = StructuredObservation(
            observation_id=f"observation:{session.session_id}:{action.action_id}",
            delivery_id=f"delivery:{session.session_id}:{action.action_id}",
            session_id=session.session_id,
            episode_id=episode.episode_id,
            environment_ref=environment.snapshot_ref,
            action_id=action.action_id,
            status=ObservationStatus.REJECTED,
            observation_type="commit_rejection",
            summary=failure.message,
            payload={"failure_code": failure.code.value},
            warnings=(),
            provenance=None,
            artifact_refs=(),
            recoverability=failure.recoverability,
            failure=failure,
        )
        self._store.record_observation(session_id, observation)
        return TurnResult(session_id, "propose_episode_transition", observation, result)

    def run_until_terminal(self, session_id: str, *, max_turns: int) -> EpisodeRunResult:
        """Run bounded turns until terminal, refusing an unbounded loop."""
        if max_turns < 1:
            raise ValueError("max_turns must be positive.")
        turns: list[TurnResult] = []
        for _ in range(max_turns):
            turn = self.advance_one_turn(session_id)
            turns.append(turn)
            _, _, _, _, episode = self._store.coherent_view(session_id)
            if episode.status is not EpisodeStatus.ACTIVE:
                return EpisodeRunResult(session_id, episode.status, tuple(turns))
        _, _, _, _, episode = self._store.coherent_view(session_id)
        return EpisodeRunResult(session_id, episode.status, tuple(turns))

    def _record_runtime_failure(
        self,
        session_id: str,
        action_id: str,
        code: FailureCode,
        message: str,
    ) -> TurnResult:
        _, environment, session, _, episode = self._store.coherent_view(session_id)
        failure = StructuredFailure(code, message, Recoverability.REPAIRABLE)
        observation = StructuredObservation(
            observation_id=f"observation:{session.session_id}:{action_id}",
            delivery_id=f"delivery:{session.session_id}:{action_id}",
            session_id=session.session_id,
            episode_id=episode.episode_id,
            environment_ref=environment.snapshot_ref,
            action_id=action_id,
            status=ObservationStatus.FAILED,
            observation_type="runtime_failure",
            summary=message,
            payload={"failure_code": code.value},
            warnings=(),
            provenance=None,
            artifact_refs=(),
            recoverability=Recoverability.REPAIRABLE,
            failure=failure,
        )
        self._store.append_event(
            session_id,
            "runtime.failure",
            {"failure_code": code.value},
        )
        self._store.record_observation(session_id, observation)
        return TurnResult(session_id, None, observation, None)


__all__ = ["AutonomousResearchRuntime", "EpisodeRunResult", "TurnResult"]
