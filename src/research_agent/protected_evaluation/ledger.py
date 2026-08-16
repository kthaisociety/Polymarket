"""Append-only scientific governance and evidence history."""

# ruff: noqa: EM101, TRY003

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import TYPE_CHECKING

from research_agent.protected_evaluation._identity import scientific_identity

if TYPE_CHECKING:
    from datetime import datetime


class LedgerConflictError(RuntimeError):
    """An existing ledger identity was reused with different semantics."""


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    """One immutable consequential scientific or governance event."""

    entry_id: str
    event_type: str
    subject_id: str
    status: str
    authority_id: str
    references: tuple[str, ...]
    reason_code: str
    occurred_at: datetime

    @classmethod
    def create(  # noqa: PLR0913
        cls,
        *,
        event_type: str,
        subject_id: str,
        status: str,
        authority_id: str,
        references: tuple[str, ...],
        reason_code: str,
        occurred_at: datetime,
    ) -> LedgerEntry:
        """Construct a deterministic identity from event semantics."""
        entry_id = scientific_identity(
            "ledger-entry",
            (
                ("event_type", event_type),
                ("subject_id", subject_id),
                ("status", status),
                ("authority_id", authority_id),
                ("references", references),
                ("reason_code", reason_code),
                ("occurred_at", occurred_at.isoformat()),
            ),
        )
        return cls(
            entry_id=entry_id,
            event_type=event_type,
            subject_id=subject_id,
            status=status,
            authority_id=authority_id,
            references=references,
            reason_code=reason_code,
            occurred_at=occurred_at,
        )


class ResearchLedger:
    """Lock-protected append-only history with exact-replay convergence."""

    def __init__(self) -> None:
        """Initialize an empty history without mutation/delete APIs."""
        self._lock = RLock()
        self._entries: tuple[LedgerEntry, ...] = ()
        self._by_id: dict[str, LedgerEntry] = {}

    def append(self, entry: LedgerEntry) -> LedgerEntry:
        """Append once, return exact replay, and reject changed identity reuse."""
        with self._lock:
            prior = self._by_id.get(entry.entry_id)
            if prior is not None:
                if prior != entry:
                    raise LedgerConflictError(
                        "Ledger entry identity was reused with changed semantics."
                    )
                return prior
            self._by_id[entry.entry_id] = entry
            self._entries = (*self._entries, entry)
            return entry

    def entries(self) -> tuple[LedgerEntry, ...]:
        """Return an immutable snapshot in causal append order."""
        with self._lock:
            return self._entries

    def entries_for(self, subject_id: str) -> tuple[LedgerEntry, ...]:
        """Return all positive and negative history for an exact subject."""
        with self._lock:
            return tuple(entry for entry in self._entries if entry.subject_id == subject_id)

    def authoritative(self, entry: LedgerEntry) -> bool:
        """Return whether the exact event was published by this ledger instance."""
        with self._lock:
            return self._by_id.get(entry.entry_id) == entry


__all__ = ["LedgerConflictError", "LedgerEntry", "ResearchLedger"]
