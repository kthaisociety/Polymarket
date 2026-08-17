"""Fail-closed live read-only smoke for the Polymarket Chronos adapter."""

# ruff: noqa: T201

from __future__ import annotations

import argparse
import asyncio
import json
import os
from typing import TYPE_CHECKING

from research_agent.data_adapters.polymarket import PolymarketImportRequest
from research_agent.data_adapters.polymarket.database import (
    read_live_polymarket_tape,
    require_read_only_role,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

_DATABASE_URL_ENV = "BDL__DB__URL"


def build_parser() -> argparse.ArgumentParser:
    """Build the live-smoke command surface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--market-id", action="append", required=True)
    parser.add_argument("--environment-id", default="bdl-polymarket-production-readonly")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the smoke without ever printing or persisting database credentials."""
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
        payload = asyncio.run(
            _run_smoke(database_url, tuple(arguments.market_id), arguments.environment_id)
        )
    except (OSError, RuntimeError, ValueError) as error:
        print(
            json.dumps(
                {
                    "status": "FAILED",
                    "error_code": "POLYMARKET_READ_ONLY_SMOKE_FAILED",
                    "error_type": type(error).__name__,
                    "live_data_read": False,
                },
                sort_keys=True,
            )
        )
        return 3
    print(json.dumps(payload, sort_keys=True))
    return 0


async def _run_smoke(
    database_url: str, market_ids: tuple[str, ...], environment_id: str
) -> dict[str, object]:
    result = await read_live_polymarket_tape(
        database_url,
        PolymarketImportRequest(market_ids, environment_id),
    )
    return {
        "status": "SUCCEEDED",
        "live_data_read": True,
        "database_role": "human_ro",
        "default_transaction_read_only": True,
        "market_ids": list(market_ids),
        "vintage": result.vintage.identity,
        "contract_count": len(result.contracts),
        "included_fill_count": result.included_fill_count,
        "excluded_fill_count": result.excluded_fill_count,
        "registered_observation_count": len(result.registered.observations),
        "source_digest": result.source_digest,
        "registration_id": result.registered.registration_id,
        "snapshot_caveats": list(result.snapshot_caveats),
    }


_require_read_only_role = require_read_only_role


if __name__ == "__main__":
    raise SystemExit(main())
