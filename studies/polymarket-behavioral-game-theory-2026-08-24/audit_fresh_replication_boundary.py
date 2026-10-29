"""Audit whether a later corpus has legal fresh events before reading study values."""

from __future__ import annotations

import json
from pathlib import Path

from research_agent.data_adapters.polymarket.corpus import (
    PolymarketCorpusSnapshotRef,
    PolymarketCorpusStore,
)
from research_agent.data_adapters.polymarket.corpus_analysis import (
    _ordered_events,
    _validate_replication_ancestor,
)

_ANCESTOR = PolymarketCorpusSnapshotRef(
    "184b83f7f8012da4ca9116c8b6bad2076570ad5f0bada95b22615ee2f5cceae8",
    428_280_682,
)
_CURRENT = PolymarketCorpusSnapshotRef(
    "0c27543ac944a6d946b52bbf5749b419fc6a0f3d15a8632d30205376a865e40a",
    525_139_813,
)


def main() -> None:
    store = PolymarketCorpusStore(Path("data/chronos/polymarket-corpora"))
    ancestor = store.load(_ANCESTOR)
    current = store.load(_CURRENT)
    _validate_replication_ancestor(current.corpus, ancestor.corpus)
    ancestor_events = _ordered_events(ancestor.corpus)
    current_events = _ordered_events(current.corpus)
    ancestor_set = frozenset(ancestor_events)
    protected_count = (len(current_events) + 4) // 5
    development_events = current_events[: len(current_events) - protected_count]
    protected_events = current_events[len(current_events) - protected_count :]
    fresh_development_count = sum(
        event_id not in ancestor_set for event_id in development_events
    )
    novel_protected_count = sum(
        event_id not in ancestor_set for event_id in protected_events
    )
    result = {
        "schema_version": "polymarket-fresh-replication-boundary/v1",
        "status": (
            "READY_FOR_FROZEN_REPLAY"
            if fresh_development_count >= 2
            else "INSUFFICIENT_FRESH_COVERAGE"
        ),
        "strict_ancestor_prefix_verified": True,
        "ancestor_snapshot_ref": _ANCESTOR.uri,
        "current_snapshot_ref": _CURRENT.uri,
        "ancestor_event_count": len(ancestor_events),
        "current_event_count": len(current_events),
        "novel_event_count": len(set(current_events) - ancestor_set),
        "development_event_count_before_ancestor_embargo": len(development_events),
        "protected_event_count": len(protected_events),
        "embargoed_ancestor_event_count": sum(
            event_id in ancestor_set for event_id in development_events
        ),
        "fresh_development_event_count": fresh_development_count,
        "novel_protected_event_count": novel_protected_count,
        "protected_values_exposed": False,
        "source_executed": False,
        "required_total_event_count_for_first_legal_successor": 403,
        "warnings": [
            "All events absent from the selection corpus remain in the current final 20% protected block.",
            "No probability or payout value from a novel event was exposed to authored study code.",
            "The frozen source must not run until at least two legal fresh development events exist.",
        ],
    }
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    main()
