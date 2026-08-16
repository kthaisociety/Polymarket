"""Deterministic mandate compilation and exact human task confirmation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from threading import RLock
from uuid import uuid4

from research_agent.data_foundation.temporal import TemporalOffset


class CompilationStatus(Enum):
    """Resolution state of a compiled research mandate."""

    RESOLVED = "resolved"
    PARTIALLY_RESOLVED = "partially_resolved"
    UNRESOLVABLE = "unresolvable"


class ConfirmationStatus(Enum):
    """Outcome of the human-owned task publication boundary."""

    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CONFLICT = "conflict"


@dataclass(frozen=True, slots=True)
class UserMandate:
    """Original research intent and explicitly supplied scientific semantics."""

    original_text: str
    research_objective: str
    target_field_id: str | None = None
    forecast_horizon: TemporalOffset | None = None
    dataset_refs: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Require an explicit temporal identity rather than a numeric month convention."""
        if self.forecast_horizon is not None and not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
            self.forecast_horizon, TemporalOffset
        ):
            msg = "forecast horizon must be an explicit TemporalOffset"
            raise TypeError(msg)
        if self.forecast_horizon is not None and not self.forecast_horizon.is_positive:
            msg = "forecast horizon must be positive"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class ResearchEnvironmentSummary:
    """Metadata sufficient for compilation without dataset-value access."""

    environment_id: str
    available_field_ids: tuple[str, ...]
    available_dataset_refs: tuple[str, ...]
    protected_resource_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ResearchTaskProposal:
    """Reviewable, non-authoritative structured interpretation of a mandate."""

    proposal_id: str
    semantic_digest: str
    original_mandate: str
    research_objective: str
    target_field_id: str | None
    forecast_horizon: TemporalOffset | None
    dataset_refs: tuple[str, ...]
    constraints: tuple[str, ...]
    environment_id: str
    version: int
    parent_proposal_id: str | None
    unresolved_fields: tuple[str, ...]

    @property
    def readback(self) -> str:
        """Return deterministic human-readable semantics for confirmation."""
        unresolved = ", ".join(self.unresolved_fields) or "none"
        horizon = self.forecast_horizon.describe() if self.forecast_horizon else "unresolved"
        return (
            f"Objective: {self.research_objective}\n"
            f"Target: {self.target_field_id or 'unresolved'}\n"
            f"Forecast horizon: {horizon}\n"
            f"Datasets: {', '.join(self.dataset_refs)}\n"
            f"Constraints: {', '.join(self.constraints) or 'none'}\n"
            f"Unresolved: {unresolved}\n"
            f"Original mandate: {self.original_mandate}"
        )


@dataclass(frozen=True, slots=True)
class ResearchTask:
    """Human-confirmed, versioned identity of one scientific problem."""

    task_id: str
    confirmed_proposal_id: str
    semantic_digest: str
    original_mandate: str
    research_objective: str
    target_field_id: str | None
    forecast_horizon: TemporalOffset | None
    dataset_refs: tuple[str, ...]
    constraints: tuple[str, ...]
    environment_id: str
    version: int
    parent_task_id: str | None
    confirmation_id: str


@dataclass(frozen=True, slots=True)
class TaskCompilationResult:
    """Explicit outcome of deterministic proposal compilation."""

    status: CompilationStatus
    proposal: ResearchTaskProposal | None
    unresolved_fields: tuple[str, ...] = ()
    invalid_references: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TaskConfirmation:
    """Human decision bound to the exact reviewed proposal semantics."""

    confirmation_id: str
    proposal_id: str
    proposal_version: int
    semantic_digest: str
    approved: bool


@dataclass(frozen=True, slots=True)
class TaskConfirmationResult:
    """Publication result for one exact confirmation request."""

    status: ConfirmationStatus
    task: ResearchTask | None
    message: str


class TaskCompiler:
    """Compile metadata and explicit intent without publishing a task."""

    def compile(
        self,
        mandate: UserMandate,
        environment: ResearchEnvironmentSummary,
    ) -> TaskCompilationResult:
        """Compile a first proposal while preserving unresolved semantics."""
        return self._compile_version(mandate, environment, version=1, parent_proposal_id=None)

    def revise(
        self,
        parent: ResearchTaskProposal,
        mandate: UserMandate,
        environment: ResearchEnvironmentSummary,
    ) -> TaskCompilationResult:
        """Compile edited semantics as a new proposal requiring confirmation."""
        return self._compile_version(
            mandate,
            environment,
            version=parent.version + 1,
            parent_proposal_id=parent.proposal_id,
        )

    @classmethod
    def _compile_version(
        cls,
        mandate: UserMandate,
        environment: ResearchEnvironmentSummary,
        *,
        version: int,
        parent_proposal_id: str | None,
    ) -> TaskCompilationResult:
        unresolved_fields = cls._unresolved_fields(mandate)
        invalid_references = cls._invalid_references(mandate, environment)
        if invalid_references:
            return TaskCompilationResult(
                status=CompilationStatus.UNRESOLVABLE,
                proposal=None,
                unresolved_fields=unresolved_fields,
                invalid_references=invalid_references,
            )

        status = (
            CompilationStatus.PARTIALLY_RESOLVED
            if unresolved_fields
            else CompilationStatus.RESOLVED
        )
        digest = _digest(_proposal_semantics(mandate, environment.environment_id, version))
        proposal = ResearchTaskProposal(
            proposal_id=str(uuid4()),
            semantic_digest=digest,
            original_mandate=mandate.original_text,
            research_objective=mandate.research_objective,
            target_field_id=mandate.target_field_id,
            forecast_horizon=mandate.forecast_horizon,
            dataset_refs=mandate.dataset_refs,
            constraints=mandate.constraints,
            environment_id=environment.environment_id,
            version=version,
            parent_proposal_id=parent_proposal_id,
            unresolved_fields=unresolved_fields,
        )
        return TaskCompilationResult(
            status=status, proposal=proposal, unresolved_fields=unresolved_fields
        )

    @staticmethod
    def _unresolved_fields(mandate: UserMandate) -> tuple[str, ...]:
        unresolved: list[str] = []
        if mandate.target_field_id is None:
            unresolved.append("target")
        if mandate.forecast_horizon is None:
            unresolved.append("forecast_horizon")
        return tuple(unresolved)

    @staticmethod
    def _invalid_references(
        mandate: UserMandate,
        environment: ResearchEnvironmentSummary,
    ) -> tuple[str, ...]:
        invalid = [
            f"dataset:{reference}"
            for reference in mandate.dataset_refs
            if reference not in environment.available_dataset_refs
        ]
        if (
            mandate.target_field_id is not None
            and mandate.target_field_id not in environment.available_field_ids
        ):
            invalid.append(f"field:{mandate.target_field_id}")
        return tuple(invalid)


class TaskPublisher:
    """Publish tasks only from exact, explicit human confirmation."""

    def __init__(self) -> None:
        """Initialize the confirmation-idempotency publication boundary."""
        self._lock = RLock()
        self._tasks_by_confirmation: dict[str, tuple[str, ResearchTask]] = {}

    def confirm(
        self,
        proposal: ResearchTaskProposal,
        confirmation: TaskConfirmation,
        *,
        parent_task_id: str | None = None,
    ) -> TaskConfirmationResult:
        """Confirm exact proposal semantics idempotently or fail closed."""
        requested_digest = _digest(
            {
                "proposal_id": confirmation.proposal_id,
                "proposal_version": confirmation.proposal_version,
                "semantic_digest": confirmation.semantic_digest,
                "approved": confirmation.approved,
            }
        )
        with self._lock:
            prior = self._tasks_by_confirmation.get(confirmation.confirmation_id)
            if prior is not None:
                prior_digest, task = prior
                if prior_digest != requested_digest:
                    return TaskConfirmationResult(
                        ConfirmationStatus.CONFLICT,
                        None,
                        "Confirmation identity was reused with changed semantics.",
                    )
                return TaskConfirmationResult(
                    ConfirmationStatus.CONFIRMED,
                    task,
                    "Exact confirmation replay returned the existing task.",
                )

            exact = (
                confirmation.proposal_id == proposal.proposal_id
                and confirmation.proposal_version == proposal.version
                and confirmation.semantic_digest == proposal.semantic_digest
            )
            if not confirmation.approved:
                return TaskConfirmationResult(
                    ConfirmationStatus.REJECTED,
                    None,
                    "The human rejected the proposal.",
                )
            if not exact:
                return TaskConfirmationResult(
                    ConfirmationStatus.CONFLICT,
                    None,
                    "Confirmation does not match the exact reviewed proposal.",
                )
            task = ResearchTask(
                task_id=str(uuid4()),
                confirmed_proposal_id=proposal.proposal_id,
                semantic_digest=proposal.semantic_digest,
                original_mandate=proposal.original_mandate,
                research_objective=proposal.research_objective,
                target_field_id=proposal.target_field_id,
                forecast_horizon=proposal.forecast_horizon,
                dataset_refs=proposal.dataset_refs,
                constraints=proposal.constraints,
                environment_id=proposal.environment_id,
                version=proposal.version,
                parent_task_id=parent_task_id,
                confirmation_id=confirmation.confirmation_id,
            )
            self._tasks_by_confirmation[confirmation.confirmation_id] = (requested_digest, task)
            return TaskConfirmationResult(
                ConfirmationStatus.CONFIRMED,
                task,
                "The exact reviewed proposal was confirmed.",
            )


def _proposal_semantics(
    mandate: UserMandate,
    environment_id: str,
    version: int,
) -> dict[str, object]:
    return {
        "original_mandate": mandate.original_text,
        "research_objective": mandate.research_objective,
        "target_field_id": mandate.target_field_id,
        "forecast_horizon_id": (
            mandate.forecast_horizon.identity if mandate.forecast_horizon is not None else None
        ),
        "dataset_refs": mandate.dataset_refs,
        "constraints": mandate.constraints,
        "environment_id": environment_id,
        "version": version,
    }


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=list).encode()
    return sha256(encoded).hexdigest()


__all__ = [
    "CompilationStatus",
    "ConfirmationStatus",
    "ResearchEnvironmentSummary",
    "ResearchTask",
    "ResearchTaskProposal",
    "TaskCompilationResult",
    "TaskCompiler",
    "TaskConfirmation",
    "TaskConfirmationResult",
    "TaskPublisher",
    "UserMandate",
]
