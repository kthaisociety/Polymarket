"""Deterministic selection of declared fitting windows."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from research_agent.data_foundation._identity import stable_identity
from research_agent.data_foundation.information import BoundaryStatus

if TYPE_CHECKING:
    from research_agent.data_foundation.samples import TrainingRow, TrainingSample


class WindowKind(Enum):
    """Supported non-learned window semantics."""

    EXPANDING = "expanding"
    ROLLING = "rolling"


@dataclass(frozen=True, slots=True)
class TrainingWindowPolicy:
    """Frozen deterministic sample-selection rule."""

    version: int
    kind: WindowKind
    minimum_samples: int
    maximum_samples: int | None
    provenance_ref: str

    def __post_init__(self) -> None:
        """Validate that the policy cannot imply an undeclared fallback."""
        if self.version < 1 or self.minimum_samples < 1 or not self.provenance_ref:
            msg = "window version, minimum, and provenance must be explicit"
            raise ValueError(msg)
        if self.kind is WindowKind.ROLLING:
            if self.maximum_samples is None or self.maximum_samples < self.minimum_samples:
                msg = "rolling windows require maximum_samples >= minimum_samples"
                raise ValueError(msg)
        elif self.maximum_samples is not None:
            msg = "expanding windows cannot silently impose a maximum"
            raise ValueError(msg)

    @property
    def identity(self) -> str:
        """Return the stable policy identity."""
        return stable_identity("training-window-policy", self)


@dataclass(frozen=True, slots=True)
class TrainingWindow:
    """Exact selected row identities for fitting, or explicit insufficiency."""

    window_id: str
    sample_id: str
    policy_id: str
    rows: tuple[TrainingRow, ...]
    status: BoundaryStatus
    insufficiency: str | None

    def __post_init__(self) -> None:
        """Verify that window identity matches its exact selected rows and status."""
        expected = stable_identity("training-window", _training_window_payload(self))
        if self.window_id != expected:
            msg = "training-window identity does not match content"
            raise ValueError(msg)


class TrainingWindowSelector:
    """Apply a frozen policy without tuning or fallback."""

    def select(
        self,
        sample: TrainingSample,
        policy: TrainingWindowPolicy,
    ) -> TrainingWindow:
        """Select the exact declared subset or return explicit insufficiency."""
        ordered = tuple(sorted(sample.rows, key=lambda row: row.decision_time))
        if len(ordered) < policy.minimum_samples:
            selected: tuple[TrainingRow, ...] = ()
            status = BoundaryStatus.INSUFFICIENT
            insufficiency = (
                f"requires {policy.minimum_samples} samples but only {len(ordered)} are legal"
            )
        else:
            selected = ordered
            if policy.kind is WindowKind.ROLLING:
                if policy.maximum_samples is None:
                    msg = "validated rolling policy lost maximum_samples"
                    raise RuntimeError(msg)
                selected = ordered[-policy.maximum_samples :]
            status = BoundaryStatus.READY
            insufficiency = None
        payload = {
            "sample_id": sample.sample_id,
            "policy_id": policy.identity,
            "row_ids": tuple(row.row_id for row in selected),
            "status": status,
            "insufficiency": insufficiency,
        }
        return TrainingWindow(
            window_id=stable_identity("training-window", payload),
            sample_id=sample.sample_id,
            policy_id=policy.identity,
            rows=selected,
            status=status,
            insufficiency=insufficiency,
        )


def _training_window_payload(window: TrainingWindow) -> dict[str, object]:
    return {
        "sample_id": window.sample_id,
        "policy_id": window.policy_id,
        "row_ids": tuple(row.row_id for row in window.rows),
        "status": window.status,
        "insufficiency": window.insufficiency,
    }
