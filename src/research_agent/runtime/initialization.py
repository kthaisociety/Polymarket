"""Coherent and idempotent autonomous runtime initialization."""

# ruff: noqa: EM101, TRY003

from __future__ import annotations

import json
from hashlib import sha256
from typing import TYPE_CHECKING
from uuid import uuid4

from research_agent.runtime.models import (
    EpisodeStatus,
    ResearchEnvironmentSnapshot,
    ResearchEpisode,
    ResearcherState,
    ResearchSession,
    RuntimeInitialization,
)

if TYPE_CHECKING:
    from research_agent.runtime.store import InMemoryRuntimeStore
    from research_agent.task_compilation import ResearchTask


class ResearchRuntimeInitializer:
    """Create a complete epistemic-zero attempt without a provider call."""

    def __init__(self, store: InMemoryRuntimeStore) -> None:
        """Bind initialization to one runtime-owned persistence boundary."""
        self._store = store

    def initialize(
        self,
        task: ResearchTask,
        environment: ResearchEnvironmentSnapshot,
        *,
        request_id: str,
    ) -> RuntimeInitialization:
        """Publish one complete session/state/episode tuple or no tuple."""
        if task.environment_id != environment.environment_id:
            raise ValueError("Task and environment identities do not match.")
        session_id = str(uuid4())
        state_id = str(uuid4())
        episode_id = str(uuid4())
        unresolved = tuple(
            name
            for name, value in (
                ("target", task.target_field_id),
                ("forecast_horizon", task.forecast_horizon),
            )
            if value is None
        )
        session = ResearchSession(
            session_id=session_id,
            task_id=task.task_id,
            task_version=task.version,
            environment_ref=environment.snapshot_ref,
            state_id=state_id,
            episode_id=episode_id,
            initialization_request_id=request_id,
        )
        state = ResearcherState(
            state_id=state_id,
            session_id=session_id,
            task_id=task.task_id,
            task_version=task.version,
            environment_ref=environment.snapshot_ref,
            version=0,
            mission=task.research_objective,
            constraints=task.constraints,
            unresolved_semantics=unresolved,
        )
        episode = ResearchEpisode(
            episode_id=episode_id,
            session_id=session_id,
            task_id=task.task_id,
            task_version=task.version,
            environment_ref=environment.snapshot_ref,
            starting_state_version=0,
            objective=task.research_objective,
            active_question="Orient to the confirmed mission and inspect authorized resources.",
            current_plan=(),
            unresolved_questions=unresolved,
            status=EpisodeStatus.ACTIVE,
        )
        result = RuntimeInitialization(session, state, episode)
        semantic_digest = sha256(
            json.dumps(
                {
                    "request_id": request_id,
                    "task_id": task.task_id,
                    "task_version": task.version,
                    "environment_ref": environment.snapshot_ref,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()
        self._store.register_task_and_environment(task, environment)
        return self._store.publish_initialization(request_id, semantic_digest, result)


__all__ = ["ResearchRuntimeInitializer"]
