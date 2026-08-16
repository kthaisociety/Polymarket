"""Irreversible protected-evidence exposure history."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import TYPE_CHECKING

from research_agent.protected_evaluation._identity import scientific_identity
from research_agent.protected_evaluation.idempotency import PrivilegedOperationCoordinator
from research_agent.protected_evaluation.ledger import LedgerEntry, ResearchLedger
from research_agent.protected_evaluation.records import ExposureRecord, ProtectedResourceScope

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class DisclosureEvent:
    """Harness-observed protected disclosure awaiting durable recording."""

    disclosure_key: str
    view_id: str
    permit_id: str
    request_id: str
    frozen_system_id: str
    system_id: str
    lineage_refs: tuple[str, ...]
    scope: ProtectedResourceScope
    recipient_id: str
    disclosure_status: str


class ExposureRegistry:
    """Append-only exposure index used by later governance decisions."""

    def __init__(self) -> None:
        """Initialize with no disclosed protected evidence."""
        self._lock = RLock()
        self._records: tuple[ExposureRecord, ...] = ()
        self._by_id: dict[str, ExposureRecord] = {}

    def _issue(self, record: ExposureRecord) -> ExposureRecord:
        """Append a recorder-issued exposure; callers have no publication API."""
        with self._lock:
            prior = self._by_id.get(record.exposure_id)
            if prior is not None:
                if prior != record:
                    msg = "Exposure identity was reused with changed semantics."
                    raise ValueError(msg)
                return prior
            self._by_id[record.exposure_id] = record
            self._records = (*self._records, record)
            return record

    def records(self) -> tuple[ExposureRecord, ...]:
        """Return immutable irreversible exposure history."""
        with self._lock:
            return self._records

    def affects(self, *, exposure_period_id: str, lineage_refs: frozenset[str]) -> bool:
        """Report exposure for the same holdout period on shared ancestry."""
        with self._lock:
            return any(
                record.exposure_period_id == exposure_period_id
                and bool(lineage_refs.intersection(record.lineage_refs))
                for record in self._records
            )

    def references_for(
        self, *, exposure_period_id: str, lineage_refs: frozenset[str]
    ) -> tuple[str, ...]:
        """Return exact authoritative exposure refs affecting a lineage and period."""
        with self._lock:
            return tuple(
                record.exposure_id
                for record in self._records
                if record.exposure_period_id == exposure_period_id
                and bool(lineage_refs.intersection(record.lineage_refs))
            )


class ExposureRecorder:
    """Record disclosure exactly once before acknowledging it to a caller."""

    def __init__(
        self,
        *,
        registry: ExposureRegistry,
        ledger: ResearchLedger,
        clock: Callable[[], datetime],
        operations: PrivilegedOperationCoordinator | None = None,
    ) -> None:
        """Bind append-only exposure, ledger, and idempotency stores."""
        self._registry = registry
        self._ledger = ledger
        self._clock = clock
        self._operations = operations or PrivilegedOperationCoordinator()

    def record(self, event: DisclosureEvent) -> ExposureRecord:
        """Append the earliest disclosure fact; outcome success is irrelevant."""
        full_lineage = tuple(dict.fromkeys((event.system_id, *event.lineage_refs)))
        payload = (
            ("view_id", event.view_id),
            ("permit_id", event.permit_id),
            ("request_id", event.request_id),
            ("frozen_system_id", event.frozen_system_id),
            ("system_id", event.system_id),
            ("lineage_refs", full_lineage),
            ("scope_id", event.scope.scope_id),
            ("content_manifest_id", event.scope.content_manifest_id),
            ("content_identity_id", event.scope.content_identity_id),
            ("recipient_id", event.recipient_id),
            ("disclosure_status", event.disclosure_status),
        )
        return self._operations.execute(
            operation_key=f"exposure:{event.disclosure_key}",
            semantic_payload=payload,
            effect=lambda: self._append(event, full_lineage),
        ).result

    def _append(self, event: DisclosureEvent, lineage_refs: tuple[str, ...]) -> ExposureRecord:
        disclosed_at = self._clock()
        exposure_id = scientific_identity(
            "exposure",
            (
                ("disclosure_key", event.disclosure_key),
                ("view_id", event.view_id),
                ("scope_id", event.scope.scope_id),
                ("content_manifest_id", event.scope.content_manifest_id),
                ("content_identity_id", event.scope.content_identity_id),
                ("recipient_id", event.recipient_id),
            ),
        )
        record = ExposureRecord(
            exposure_id=exposure_id,
            disclosure_key=event.disclosure_key,
            view_id=event.view_id,
            permit_id=event.permit_id,
            request_id=event.request_id,
            frozen_system_id=event.frozen_system_id,
            system_id=event.system_id,
            lineage_refs=lineage_refs,
            scope=event.scope,
            content_manifest_id=event.scope.content_manifest_id,
            content_identity_id=event.scope.content_identity_id,
            exposure_period_id=event.scope.exposure_period_id,
            recipient_id=event.recipient_id,
            disclosure_status=event.disclosure_status,
            disclosed_at=disclosed_at,
        )
        self._ledger.append(
            LedgerEntry.create(
                event_type="exposure.protected-disclosed",
                subject_id=exposure_id,
                status=event.disclosure_status,
                authority_id="harness",
                references=(
                    event.view_id,
                    event.permit_id,
                    event.request_id,
                    event.frozen_system_id,
                    event.scope.scope_id,
                    event.scope.content_manifest_id,
                    event.scope.content_identity_id,
                    *lineage_refs,
                ),
                reason_code="PROTECTED_DISCLOSURE",
                occurred_at=disclosed_at,
            )
        )
        self._registry._issue(record)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        return record


__all__ = ["DisclosureEvent", "ExposureRecorder", "ExposureRegistry"]
