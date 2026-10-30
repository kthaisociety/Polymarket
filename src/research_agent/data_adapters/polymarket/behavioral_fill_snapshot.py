"""Retain a parent-bound Polymarket taker-fill panel through proved human_ro."""

# ruff: noqa: T201

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

from research_agent.data_adapters.polymarket.behavioral_fills import (
    BehavioralFillRequest,
    BehavioralFillStore,
    behavioral_fill_query_sha256,
)
from research_agent.data_adapters.polymarket.corpus import (
    PolymarketCorpusSnapshotRef,
    PolymarketCorpusStore,
)
from research_agent.data_adapters.polymarket.database import (
    read_live_behavioral_fill_corpus,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

_DATABASE_URL_ENV = "POLYMARKET_DATABASE_URL"


def build_parser() -> argparse.ArgumentParser:
    """Build the explicit parent-bound acquisition command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-sha256", required=True)
    parser.add_argument("--parent-size", required=True, type=int)
    parser.add_argument("--corpus-workspace", required=True, type=Path)
    parser.add_argument("--fill-workspace", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Acquire, retain, reopen, and report only sanitized panel identities."""
    arguments = build_parser().parse_args(argv)
    database_url = os.environ.get(_DATABASE_URL_ENV)
    if database_url is None:
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "error_code": "READ_ONLY_DATABASE_URL_UNSET",
                    "live_data_read": False,
                },
                sort_keys=True,
            )
        )
        return 2
    try:
        parent = PolymarketCorpusStore(arguments.corpus_workspace).load(
            PolymarketCorpusSnapshotRef(arguments.parent_sha256, arguments.parent_size)
        )
        result = asyncio.run(
            read_live_behavioral_fill_corpus(
                database_url,
                BehavioralFillRequest(
                    environment_id=parent.corpus.request.environment_id,
                    as_of=parent.corpus.request.as_of,
                    parent_snapshot_ref=parent.ref.uri,
                ),
                market_ids=tuple(item.market_id for item in parent.corpus.contracts),
                store=BehavioralFillStore(arguments.fill_workspace),
            )
        )
        fills = result.snapshot.corpus.fills
        payload: dict[str, object] = {
            "status": "SUCCEEDED",
            "epistemic_status": "REGISTERED_INPUT_NOT_SCIENTIFIC_EVIDENCE",
            "live_data_read": True,
            "database_role": "human_ro",
            "default_transaction_read_only": True,
            "transaction_read_only": True,
            "transaction_isolation": "repeatable_read",
            "production_database_writes": False,
            "parent_snapshot_ref": parent.ref.as_dict(),
            "as_of": parent.corpus.request.as_of.isoformat(),
            "requested_market_count": len(parent.corpus.contracts),
            "retained_fill_count": len(fills),
            "retained_market_count": len({item.market_id for item in fills}),
            "retained_wallet_count": len({item.account for item in fills}),
            "first_fill_time": fills[0].fill_time.isoformat(),
            "last_fill_time": fills[-1].fill_time.isoformat(),
            "query_sha256": behavioral_fill_query_sha256(),
            "snapshot_ref": result.snapshot.ref.as_dict(),
            "formal_object_refs": [],
            "durable_state_effects": [result.snapshot.ref.uri],
            "caveats": [
                "rows are aggregate taker legs selected by the on-chain taker predicate",
                "fill_time is the public block-time clock, not collector arrival or order latency",
                "recorded fill prices are not delayed executable quotes",
                "the fixed historical ceiling cannot exclude later backfills into older timestamps",
            ],
        }
        _persist_receipt(payload, arguments.receipt)
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        print(
            json.dumps(
                {
                    "status": "FAILED",
                    "error_code": "BEHAVIORAL_FILL_SNAPSHOT_FAILED",
                    "error_type": type(error).__name__,
                    "live_data_read": False,
                },
                sort_keys=True,
            )
        )
        return 3
    print(json.dumps(payload, sort_keys=True))
    return 0


def _persist_receipt(payload: dict[str, object], path: Path) -> None:
    content = (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as output:
            output.write(content)
    except FileExistsError:
        if path.read_bytes() != content:
            msg = "behavioral fill receipt path contains different bytes"
            raise ValueError(msg) from None


if __name__ == "__main__":
    raise SystemExit(main())
