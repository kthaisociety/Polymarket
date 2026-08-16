"""Durable-shaped idempotency boundary for privileged operations."""

# ruff: noqa: EM101, TRY003

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from threading import RLock
from typing import TYPE_CHECKING, TypeVar, cast

from research_agent.protected_evaluation._identity import IdentityFields, scientific_identity

if TYPE_CHECKING:
    from collections.abc import Callable

ResultT = TypeVar("ResultT")


class IdempotencyConflictError(RuntimeError):
    """A stable operation key was reused with changed semantic payload."""


class PrivilegedOperationInDoubtError(RuntimeError):
    """An operation was claimed but has no sealed result safe to acknowledge."""


class PrivilegedOperationPhase(Enum):
    """Durable-shaped phases around one irreversible privileged effect."""

    CLAIMED = "claimed"
    EFFECT_SEALED = "effect_sealed"
    ACKNOWLEDGED = "acknowledged"


@dataclass(frozen=True, slots=True)
class PrivilegedOperationRecord[ResultT]:
    """Original durable outcome for one semantic privileged request."""

    operation_key: str
    semantic_digest: str
    phase: PrivilegedOperationPhase
    result: ResultT | None


@dataclass(frozen=True, slots=True)
class PrivilegedOperationResult[ResultT]:
    """Original result plus whether this call was an exact replay."""

    result: ResultT
    replayed: bool


class PrivilegedOperationCoordinator:
    """Atomically claim, execute, and retain one privileged operation outcome."""

    def __init__(self, *, after_effect_sealed: Callable[[str], None] | None = None) -> None:
        """Initialize an empty coordinator store and optional lost-ack fault seam."""
        self._lock = RLock()
        self._records: dict[str, PrivilegedOperationRecord[object]] = {}
        self._after_effect_sealed = after_effect_sealed

    def execute(
        self,
        *,
        operation_key: str,
        semantic_payload: IdentityFields,
        effect: Callable[[], ResultT],
    ) -> PrivilegedOperationResult[ResultT]:
        """Execute once, replay exactly, or conflict before a second effect."""
        digest = scientific_identity("privileged-operation", semantic_payload)
        with self._lock:
            prior = self._records.get(operation_key)
            if prior is not None:
                if prior.semantic_digest != digest:
                    raise IdempotencyConflictError(
                        "Privileged operation key was reused with changed semantics."
                    )
                if prior.phase is PrivilegedOperationPhase.CLAIMED or prior.result is None:
                    raise PrivilegedOperationInDoubtError(
                        "Privileged operation is claimed without a sealed result; recovery must "
                        "reconcile authoritative effect records before retry."
                    )
                if prior.phase is PrivilegedOperationPhase.EFFECT_SEALED:
                    prior = replace(prior, phase=PrivilegedOperationPhase.ACKNOWLEDGED)
                    self._records[operation_key] = prior
                return PrivilegedOperationResult(cast("ResultT", prior.result), replayed=True)
            self._records[operation_key] = PrivilegedOperationRecord(
                operation_key=operation_key,
                semantic_digest=digest,
                phase=PrivilegedOperationPhase.CLAIMED,
                result=None,
            )
            result = effect()
            self._records[operation_key] = PrivilegedOperationRecord(
                operation_key=operation_key,
                semantic_digest=digest,
                phase=PrivilegedOperationPhase.EFFECT_SEALED,
                result=result,
            )
            if self._after_effect_sealed is not None:
                self._after_effect_sealed(operation_key)
            self._records[operation_key] = replace(
                self._records[operation_key],
                phase=PrivilegedOperationPhase.ACKNOWLEDGED,
            )
            return PrivilegedOperationResult(result, replayed=False)

    def records(self) -> tuple[PrivilegedOperationRecord[object], ...]:
        """Return immutable operation records for durable persistence adapters."""
        with self._lock:
            return tuple(self._records.values())


__all__ = [
    "IdempotencyConflictError",
    "PrivilegedOperationCoordinator",
    "PrivilegedOperationInDoubtError",
    "PrivilegedOperationPhase",
    "PrivilegedOperationRecord",
    "PrivilegedOperationResult",
]
