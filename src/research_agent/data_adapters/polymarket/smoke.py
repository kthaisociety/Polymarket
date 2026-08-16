"""Fail-closed live read-only smoke for the Polymarket Chronos adapter."""

# ruff: noqa: T201

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import timedelta
from typing import TYPE_CHECKING

from research_agent.data_adapters.polymarket import (
    EnginePolymarketResearchReader,
    PolymarketImportRequest,
    ingest_polymarket_contract_tape,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

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
    from core.db.pool import (  # noqa: PLC0415 - optional BDL composition dependency
        close_pool,
        create_pool,
    )

    pool = await create_pool(
        database_url,
        min_size=1,
        max_size=1,
        connect_timeout=timedelta(seconds=10),
        command_timeout=timedelta(minutes=5),
    )
    try:
        async with pool.acquire() as connection:
            role_query = (
                "SELECT current_user AS role, "
                "current_setting('default_transaction_read_only') AS default_read_only, "
                "current_setting('transaction_read_only') AS transaction_read_only, "
                "has_table_privilege(current_user, 'market.markets', 'INSERT') "
                "AS can_insert_markets, "
                "has_table_privilege(current_user, 'market.markets', 'UPDATE') "
                "AS can_update_markets, "
                "has_table_privilege(current_user, 'market.fills', 'INSERT') AS can_insert_fills, "
                "has_table_privilege(current_user, 'market.fills', 'UPDATE') AS can_update_fills"
            )
            role = await connection.fetchrow(role_query)
        _require_read_only_role(role)
        result = await ingest_polymarket_contract_tape(
            EnginePolymarketResearchReader(pool),
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
    finally:
        await close_pool(pool)


def _require_read_only_role(role: Mapping[str, object] | None) -> None:
    """Fail unless the connection proves every required read-only condition explicitly."""
    write_privileges = (
        "can_insert_markets",
        "can_update_markets",
        "can_insert_fills",
        "can_update_fills",
    )
    if (
        role is None
        or role.get("role") != "human_ro"
        or role.get("default_read_only") != "on"
        or role.get("transaction_read_only") != "on"
        or any(role.get(privilege) is not False for privilege in write_privileges)
    ):
        msg = "database role did not prove the approved human_ro read-only contract"
        raise RuntimeError(msg)


if __name__ == "__main__":
    raise SystemExit(main())
