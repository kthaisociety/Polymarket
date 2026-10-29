"""Public command for retaining and registering an exact dual-clock L2 corpus."""

# ruff: noqa: T201

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from research_agent.data_adapters.polymarket.book_corpus import (
    BookCorpusRequest,
    BookCorpusStore,
    BookDeltaRecord,
    BookLeg,
    BookSnapshotRecord,
)
from research_agent.data_adapters.polymarket.database import (
    LiveBookCorpusResult,
    read_live_book_corpus,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

_DATABASE_URL_ENV = "BDL__DB__URL"


def build_parser() -> argparse.ArgumentParser:
    """Build the exact bounded book-corpus command surface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-authority-ref", required=True)
    parser.add_argument(
        "--leg",
        action="append",
        required=True,
        help="canonical venue:market_id:outcome_index identity; repeat for every leg",
    )
    parser.add_argument("--start-at", required=True)
    parser.add_argument("--end-at", required=True)
    parser.add_argument("--environment-id", default="bdl-polymarket-production-readonly")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Retain exact live L2 bytes and emit only sanitized identity metadata."""
    arguments = build_parser().parse_args(argv)
    database_url = os.environ.get(_DATABASE_URL_ENV)
    if database_url is None:
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "error_code": "READ_ONLY_DATABASE_URL_UNSET",
                    "required_action": "open the approved human_ro tunnel and set BDL__DB__URL",
                    "live_data_read": False,
                },
                sort_keys=True,
            )
        )
        return 2

    live_data_read = False
    try:
        request = BookCorpusRequest(
            environment_id=arguments.environment_id,
            scope_authority_ref=arguments.scope_authority_ref,
            legs=tuple(_parse_leg(value) for value in arguments.leg),
            start_at=_parse_aware_datetime(arguments.start_at, "start-at"),
            end_at=_parse_aware_datetime(arguments.end_at, "end-at"),
        )
        result = asyncio.run(
            read_live_book_corpus(
                database_url,
                request,
                BookCorpusStore(arguments.workspace),
            )
        )
        live_data_read = True
        payload = _sanitized_payload(result)
        if arguments.receipt is not None:
            _persist_receipt(payload, arguments.receipt)
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        print(
            json.dumps(
                {
                    "status": "FAILED",
                    "error_code": "BOOK_CORPUS_SNAPSHOT_FAILED",
                    "error_type": type(error).__name__,
                    "live_data_read": live_data_read,
                },
                sort_keys=True,
            )
        )
        return 3

    print(json.dumps(payload, sort_keys=True))
    return 0


def _sanitized_payload(result: LiveBookCorpusResult) -> dict[str, object]:
    corpus = result.corpus
    registration = result.registration
    source_events = corpus.events
    replay_states = registration.states
    snapshot_count = sum(isinstance(event, BookSnapshotRecord) for event in source_events)
    delta_count = sum(isinstance(event, BookDeltaRecord) for event in source_events)
    return {
        "status": "SUCCEEDED",
        "live_data_read": True,
        "database_role": "human_ro",
        "default_transaction_read_only": True,
        "transaction_isolation": "repeatable_read",
        "transaction_read_only": True,
        "environment_id": corpus.request.environment_id,
        "scope_authority_ref": corpus.request.scope_authority_ref,
        "collector_time_interval": {
            "start_inclusive": corpus.request.start_at.isoformat(),
            "end_exclusive": corpus.request.end_at.isoformat(),
        },
        "legs": [
            {
                "venue": leg.venue,
                "market_id": leg.market_id,
                "outcome_index": leg.outcome_index,
            }
            for leg in corpus.request.legs
        ],
        "leg_count": len(corpus.request.legs),
        "source_event_count": len(source_events),
        "source_snapshot_count": snapshot_count,
        "source_delta_count": delta_count,
        "replay_state_count": len(replay_states),
        "registered_observation_count": len(registration.dataset.observations),
        "source_available_at_bounds": {
            "first": min(event.ts for event in source_events).isoformat(),
            "last": max(event.ts for event in source_events).isoformat(),
        },
        "source_reference_time_bounds": {
            "first": min(event.reference_time for event in source_events).isoformat(),
            "last": max(event.reference_time for event in source_events).isoformat(),
        },
        "snapshot_ref": {
            "uri": result.retention.ref.uri,
            "content_sha256": result.retention.ref.content_sha256,
            "size_bytes": result.retention.ref.size_bytes,
        },
        "dataset_registration_id": registration.dataset.registration_id,
        "catalog_id": registration.catalog.identity,
        "availability_rule": "decoded-book-collector-absorb/v1",
        "snapshot_caveats": [
            "retained canonical bytes, not the mutable live database, anchor this corpus identity",
            "reference_time is venue supplied or the collector fallback recorded at capture",
            "available_at is collector absorb time and controls simulated admissibility",
            "displayed depth does not establish hidden depth, queue position, ownership, or fills",
            "scope authority and outcome semantics are supplied by a separate reviewed audit",
            "registration grants no strategy, protected-evidence, or live-trading authority",
        ],
        "epistemic_status": "REGISTERED_DATA_NOT_SCIENTIFIC_EVIDENCE",
        "formal_object_refs": [],
        "durable_state_effects": [],
    }


def _parse_leg(value: str) -> BookLeg:
    try:
        venue, remainder = value.split(":", maxsplit=1)
        market_id, raw_outcome_index = remainder.rsplit(":", maxsplit=1)
        outcome_index = int(raw_outcome_index)
    except (ValueError, TypeError) as error:
        msg = "leg must use venue:market_id:outcome_index"
        raise ValueError(msg) from error
    if venue not in ("kalshi", "polymarket"):
        msg = "leg venue must be kalshi or polymarket"
        raise ValueError(msg)
    return BookLeg(venue, market_id, outcome_index)


def _parse_aware_datetime(value: str, field: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = f"{field} time must be timezone-aware ISO-8601"
        raise ValueError(msg)
    return parsed


def _persist_receipt(payload: dict[str, object], path: Path) -> None:
    content = (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as receipt_file:
            receipt_file.write(content)
    except FileExistsError:
        if path.read_bytes() != content:
            msg = "receipt path already contains different bytes"
            raise ValueError(msg) from None


if __name__ == "__main__":
    raise SystemExit(main())
