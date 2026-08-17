"""Public command for retaining and registering a resolved Polymarket corpus."""

# ruff: noqa: T201

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from research_agent.data_adapters.polymarket.corpus import PolymarketCorpusStore
from research_agent.data_adapters.polymarket.database import (
    LivePolymarketCorpusResult,
    read_live_polymarket_resolution_corpus,
)
from research_agent.data_adapters.polymarket.models import PolymarketCorpusRequest

if TYPE_CHECKING:
    from collections.abc import Sequence

_DATABASE_URL_ENV = "BDL__DB__URL"


def build_parser() -> argparse.ArgumentParser:
    """Build the explicit, bounded corpus-snapshot command surface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--min-points", type=int, required=True)
    parser.add_argument("--max-markets", type=int, required=True)
    parser.add_argument("--outcome-index", type=int, default=0)
    parser.add_argument("--fidelity", type=int, default=60)
    parser.add_argument("--environment-id", default="bdl-polymarket-production-readonly")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Retain exact live bytes and print only sanitized identity/count metadata."""
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
    try:
        request = PolymarketCorpusRequest(
            environment_id=arguments.environment_id,
            as_of=_parse_aware_datetime(arguments.as_of),
            min_points=arguments.min_points,
            max_markets=arguments.max_markets,
            outcome_index=arguments.outcome_index,
            fidelity=arguments.fidelity,
        )
        result = asyncio.run(
            read_live_polymarket_resolution_corpus(
                database_url,
                request,
                PolymarketCorpusStore(arguments.workspace),
            )
        )
        payload = _sanitized_payload(result)
        if arguments.receipt is not None:
            _persist_receipt(payload, arguments.receipt)
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        print(
            json.dumps(
                {
                    "status": "FAILED",
                    "error_code": "POLYMARKET_CORPUS_SNAPSHOT_FAILED",
                    "error_type": type(error).__name__,
                    "live_data_read": False,
                },
                sort_keys=True,
            )
        )
        return 3
    print(json.dumps(payload, sort_keys=True))
    return 0


def _sanitized_payload(result: LivePolymarketCorpusResult) -> dict[str, object]:
    corpus = result.corpus
    registration = result.registration
    return {
        "status": "SUCCEEDED",
        "live_data_read": True,
        "database_role": "human_ro",
        "default_transaction_read_only": True,
        "transaction_isolation": "repeatable_read",
        "transaction_read_only": True,
        "environment_id": corpus.request.environment_id,
        "as_of": corpus.request.as_of.isoformat(),
        "selection": {
            "min_points": corpus.request.min_points,
            "max_markets": corpus.request.max_markets,
            "outcome_index": corpus.request.outcome_index,
            "fidelity": corpus.request.fidelity,
        },
        "contract_count": len(corpus.contracts),
        "event_count": len({item.event_id for item in corpus.contracts}),
        "resolution_count": len(corpus.resolutions),
        "price_point_count": len(corpus.prices),
        "first_price_time": min(item.observed_at for item in corpus.prices).isoformat(),
        "last_price_time": max(item.observed_at for item in corpus.prices).isoformat(),
        "first_resolution_time": min(item.resolved_time for item in corpus.resolutions).isoformat(),
        "last_resolution_time": max(item.resolved_time for item in corpus.resolutions).isoformat(),
        "snapshot_ref": result.retention.ref.as_dict(),
        "price_registration_id": registration.price_dataset.registration_id,
        "resolution_registration_id": registration.resolution_dataset.registration_id,
        "catalog_id": registration.catalog.identity,
        "price_observation_count": len(registration.price_dataset.observations),
        "resolution_observation_count": len(registration.resolution_dataset.observations),
        "availability_rules": [
            "polymarket-clob-price-sample/v1",
            "polymarket-onchain-resolution/v1",
        ],
        "snapshot_caveats": [
            "retained canonical bytes, not the mutable live database, anchor this corpus identity",
            "event grouping is the server-recorded Polymarket event_id",
            "resolution labels become available only at the recorded on-chain resolved_time",
            "sampled prices are probability observations, not guaranteed executable quotes",
            "selection uses only declared lifecycle and price-coverage criteria",
            "contracts recorded as settling before their declared close time are excluded",
        ],
        "epistemic_status": "REGISTERED_DATA_NOT_SCIENTIFIC_EVIDENCE",
        "formal_object_refs": [],
        "durable_state_effects": [],
    }


def _parse_aware_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = "as-of time must be timezone-aware ISO-8601"
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
