"""Canonical Milestone 1 runtime records."""

# ruff: noqa: EM101, TRY003

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from research_agent.data_foundation.temporal import TemporalOffset

from research_agent.runtime._canonical import content_digest, freeze_mapping

EMPTY_OBSERVATION_CHAIN_DIGEST = content_digest(())


class EpisodeStatus(Enum):
    """Lifecycle of one research investigation."""

    ACTIVE = "active"
    RESOLVED = "resolved"
    ABANDONED = "abandoned"
    SUSPENDED = "suspended"


class ObservationStatus(Enum):
    """Outcome represented by a structured observation."""

    SUCCEEDED = "succeeded"
    REJECTED = "rejected"
    FAILED = "failed"


class Recoverability(Enum):
    """Whether the autonomous loop may repair and continue."""

    REPAIRABLE = "repairable"
    NON_RETRYABLE = "non_retryable"


class FailureCode(Enum):
    """Milestone 1 failure vocabulary."""

    INVALID_REQUEST = "INVALID_REQUEST"
    AUTHORITY_DENIED = "AUTHORITY_DENIED"
    NOT_FOUND = "NOT_FOUND"
    MALFORMED_MODEL_RESPONSE = "MALFORMED_MODEL_RESPONSE"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    INVALID_EPISODE_TRANSITION = "INVALID_EPISODE_TRANSITION"
    STALE_STATE_VERSION = "STALE_STATE_VERSION"
    INVALID_EVIDENCE_REFERENCE = "INVALID_EVIDENCE_REFERENCE"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    INTERNAL_FAILURE = "INTERNAL_FAILURE"


@dataclass(frozen=True, slots=True)
class StructuredFailure:
    """Safe model-facing failure with optional drill-down reference."""

    code: FailureCode
    message: str
    recoverability: Recoverability
    diagnostic_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ResearchEnvironmentSnapshot:
    """Exact session environment and capability authority snapshot."""

    environment_id: str
    version: int
    dataset_refs: tuple[str, ...]
    readable_dataset_refs: tuple[str, ...]
    capability_names: tuple[str, ...]
    protected_resource_refs: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def snapshot_ref(self) -> str:
        """Return stable exact-version identity."""
        return f"{self.environment_id}@{self.version}"


@dataclass(frozen=True, slots=True)
class ResearchSession:
    """One independent attempt at a confirmed research task."""

    session_id: str
    task_id: str
    task_version: int
    environment_ref: str
    state_id: str
    episode_id: str
    initialization_request_id: str


@dataclass(frozen=True, slots=True)
class ResearcherState:
    """Committed resumable understanding, separate from episode working evidence."""

    state_id: str
    session_id: str
    task_id: str
    task_version: int
    environment_ref: str
    version: int
    mission: str
    constraints: tuple[str, ...]
    unresolved_semantics: tuple[str, ...]
    durable_understanding: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    explored_paths: tuple[str, ...] = ()
    protected_exposures: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ResearchEpisode:
    """Temporary working state for one active investigation."""

    episode_id: str
    session_id: str
    task_id: str
    task_version: int
    environment_ref: str
    starting_state_version: int
    objective: str
    active_question: str
    current_plan: tuple[str, ...]
    unresolved_questions: tuple[str, ...]
    status: EpisodeStatus
    observation_ids: tuple[str, ...] = ()
    temporary_interpretations: tuple[str, ...] = ()
    transition_count: int = 0
    observation_chain_digest: str = EMPTY_OBSERVATION_CHAIN_DIGEST


@dataclass(frozen=True, slots=True)
class RuntimeInitialization:
    """Coherent published session, state zero, and active episode zero."""

    session: ResearchSession
    state: ResearcherState
    episode: ResearchEpisode


@dataclass(frozen=True, slots=True)
class ExecutionProvenance:
    """Harness-observed authority and resource access provenance."""

    session_id: str
    environment_ref: str
    capability_name: str
    authorized_dataset_ref: str | None
    selected_field_ids: tuple[str, ...]
    preview_limit: int | None
    code_sha256: str | None = None
    accesses: tuple[AnalysisDataAccess, ...] = ()
    dataset_refs: tuple[str, ...] = ()
    environment_refs: tuple[str, ...] = ()
    random_seed: int | None = None
    execution_status: str | None = None


@dataclass(frozen=True, slots=True)
class AnalysisDataAccess:
    """One exact harness-observed exploratory field access."""

    ordinal: int
    view_id: str
    dataset_ref: str
    environment_ref: str
    field_id: str


@dataclass(frozen=True, slots=True)
class AnalysisExecutionProvenance(ExecutionProvenance):
    """Execution provenance specialized for open-ended sandbox analysis."""


@dataclass(frozen=True, slots=True)
class StructuredObservation:
    """Bounded model-facing result with drillable provenance."""

    observation_id: str
    delivery_id: str
    session_id: str
    episode_id: str
    environment_ref: str
    action_id: str
    status: ObservationStatus
    observation_type: str
    summary: str
    payload: Mapping[str, object]
    warnings: tuple[str, ...]
    provenance: ExecutionProvenance | None
    artifact_refs: tuple[str, ...]
    recoverability: Recoverability
    failure: StructuredFailure | None = None
    epistemic_status: str = "WORKING"
    content_digest: str = field(init=False)

    def __post_init__(self) -> None:
        """Detach payload content and bind its identity to exact runtime authority."""
        required = (
            self.observation_id,
            self.delivery_id,
            self.session_id,
            self.episode_id,
            self.environment_ref,
            self.action_id,
        )
        if not all(required):
            raise ValueError("Observation authority and delivery identities must be non-empty.")
        object.__setattr__(self, "payload", freeze_mapping(self.payload))
        if self.provenance is not None and (
            self.provenance.session_id != self.session_id
            or self.provenance.environment_ref != self.environment_ref
        ):
            raise ValueError("Observation provenance differs from its runtime authority binding.")
        object.__setattr__(self, "content_digest", content_digest(self))

    def verify_content_identity(self) -> None:
        """Reject any identity-stable content mutation."""
        if self.content_digest != content_digest(self):
            raise ValueError("Observation content no longer matches its immutable identity.")


@dataclass(frozen=True, slots=True)
class ContextObservation:
    """Bounded substantive working-evidence projection."""

    observation_id: str
    status: ObservationStatus
    observation_type: str
    summary: str
    payload: Mapping[str, object]
    warnings: tuple[str, ...]
    provenance: ExecutionProvenance | None
    artifact_refs: tuple[str, ...]
    recoverability: Recoverability
    failure: StructuredFailure | None
    epistemic_status: str
    source_content_digest: str
    current: bool = True
    superseded_by: str | None = None

    def __post_init__(self) -> None:
        """Keep provider-facing evidence recursively immutable."""
        object.__setattr__(self, "payload", freeze_mapping(self.payload))


@dataclass(frozen=True, slots=True)
class EpisodeCheckpoint:
    """Immutable reconstructible snapshot of unresolved episode work."""

    checkpoint_id: str
    checkpoint_version: int
    supersedes_checkpoint_id: str | None
    session_id: str
    task_id: str
    task_version: int
    task_content_digest: str
    episode_id: str
    environment_ref: str
    environment_content_digest: str
    state_id: str
    state_version: int
    state_content_digest: str
    episode_transition_count: int
    objective: str
    active_question: str
    current_plan: tuple[str, ...]
    unresolved_questions: tuple[str, ...]
    temporary_interpretations: tuple[str, ...]
    observations: tuple[ContextObservation, ...]
    observation_count: int
    retained_observation_count: int
    omitted_observation_count: int
    omitted_observations_ref: str | None
    covered_observation_digest: str
    permitted_dataset_refs: tuple[str, ...]
    available_actions: tuple[str, ...]
    warnings: tuple[str, ...]
    constraints: tuple[str, ...]
    unresolved_semantics: tuple[str, ...]
    protected_exposure_refs: tuple[str, ...]
    protected_resource_refs: tuple[str, ...]
    content_digest: str = field(init=False)

    def __post_init__(self) -> None:
        """Derive and verify immutable checkpoint identity from exact content."""
        digest = content_digest(self)
        if self.checkpoint_id and self.checkpoint_id != digest:
            raise ValueError("Checkpoint ID does not match its exact semantic content.")
        object.__setattr__(self, "checkpoint_id", digest)
        object.__setattr__(self, "content_digest", digest)

    def verify_content_identity(self) -> None:
        """Reject any mutation after checkpoint publication."""
        if self.checkpoint_id != content_digest(self) or self.content_digest != self.checkpoint_id:
            raise ValueError("Checkpoint content no longer matches its immutable identity.")


@dataclass(frozen=True, slots=True)
class ContextPacket:
    """Provider-neutral context reconstructed from authoritative stores."""

    packet_id: str
    session_id: str
    task_id: str
    task_version: int
    state_id: str
    state_version: int
    episode_id: str
    environment_ref: str
    mission: str
    constraints: tuple[str, ...]
    target_field_id: str | None
    forecast_horizon: TemporalOffset | None
    unresolved_semantics: tuple[str, ...]
    committed_understanding: tuple[str, ...]
    episode_objective: str
    episode_status: EpisodeStatus
    active_question: str
    current_plan: tuple[str, ...]
    unresolved_questions: tuple[str, ...]
    temporary_interpretations: tuple[str, ...]
    working_observations: tuple[ContextObservation, ...]
    total_observation_count: int
    omitted_observation_count: int
    checkpoint_ref: str | None
    omitted_observations_ref: str | None
    permitted_dataset_refs: tuple[str, ...]
    available_actions: tuple[str, ...]
    protected_exposure_refs: tuple[str, ...]
    protected_resource_refs: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TrajectoryEvent:
    """Append-only audit event outside model state."""

    sequence: int
    session_id: str
    event_type: str
    detail: Mapping[str, object]


__all__ = [
    "EMPTY_OBSERVATION_CHAIN_DIGEST",
    "AnalysisDataAccess",
    "AnalysisExecutionProvenance",
    "ContextObservation",
    "ContextPacket",
    "EpisodeCheckpoint",
    "EpisodeStatus",
    "ExecutionProvenance",
    "FailureCode",
    "ObservationStatus",
    "Recoverability",
    "ResearchEnvironmentSnapshot",
    "ResearchEpisode",
    "ResearchSession",
    "ResearcherState",
    "RuntimeInitialization",
    "StructuredFailure",
    "StructuredObservation",
    "TrajectoryEvent",
]
