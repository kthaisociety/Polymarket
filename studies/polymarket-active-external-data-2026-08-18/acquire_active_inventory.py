# ruff: noqa: D103, E501, EM101, EM102, INP001, PLC0415, PLR2004, T201, TRY003

"""Retain a bounded active-contract inventory through the proved human_ro boundary."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any

from research_agent.data_adapters.polymarket.database import (
    READ_ONLY_PROOF_QUERY,
    require_read_only_role,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

_DATABASE_URL_ENV = "BDL__DB__URL"
_QUERY = """
WITH recent AS (
    SELECT
        market_id,
        count(*) AS fills_72h,
        sum(size * price) AS observed_notional_72h,
        min(fill_time) AS first_fill_72h,
        max(fill_time) AS last_fill_72h
    FROM market.fills
    WHERE venue = $1
      AND fill_time > $2::timestamptz - interval '72 hours'
      AND fill_time <= $2::timestamptz
    GROUP BY market_id
)
SELECT
    m.market_id,
    m.event_id,
    m.question,
    m.slug,
    m.market_type,
    m.open_time,
    m.close_time,
    m.updated_at,
    r.fills_72h,
    r.observed_notional_72h,
    r.first_fill_72h,
    r.last_fill_72h,
    m.raw->'outcomes' AS outcomes,
    m.raw->'prices' AS current_price_metadata
FROM market.markets AS m
JOIN recent AS r USING (market_id)
WHERE m.venue = $1
  AND m.status = 'open'
  AND (m.close_time IS NULL OR m.close_time > $2::timestamptz)
ORDER BY r.observed_notional_72h DESC NULLS LAST, m.market_id
LIMIT $3
""".strip()


def _json_default(value: object) -> object:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def _canonical_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            default=_json_default,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode()


async def _acquire(database_url: str, *, as_of: datetime, limit: int) -> dict[str, Any]:
    from core.db.pool import close_pool, create_pool

    pool = await create_pool(database_url, min_size=1, max_size=1)
    try:
        async with (
            pool.acquire() as connection,
            connection.transaction(isolation="repeatable_read", readonly=True),
        ):
            proof = await connection.fetchrow(READ_ONLY_PROOF_QUERY)
            require_read_only_role(proof)
            rows = await connection.fetch(_QUERY, "polymarket", as_of, limit)
        contracts: list[Mapping[str, object]] = [dict(row) for row in rows]
        body: dict[str, Any] = {
            "schema": "chronos-active-polymarket-inventory/v1",
            "environment_id": "bdl-polymarket-production-readonly",
            "as_of": as_of,
            "selection": {
                "venue": "polymarket",
                "status": "open",
                "close_after_as_of": True,
                "recent_fill_window_hours": 72,
                "rank": "observed_notional_72h_desc",
                "limit": limit,
            },
            "authority": {
                "database_role": "human_ro",
                "default_read_only": True,
                "transaction_read_only": True,
                "repeatable_read": True,
                "insert_update_privileges": False,
            },
            "query_sha256": hashlib.sha256(_QUERY.encode()).hexdigest(),
            "contract_count": len(contracts),
            "contracts": contracts,
            "caveats": [
                "recent observed notional is a scouting rank, not liquidity or executable depth",
                "current_price_metadata is a retained server metadata snapshot, not historical book state",
                "active status is observed at acquisition and is not a reconstructible historical status",
                "no protected corpus values or credentials are present",
            ],
        }
        content_hash = hashlib.sha256(_canonical_bytes(body)).hexdigest()
        body["content_sha256_without_this_field"] = content_hash
        return body
    finally:
        await close_pool(pool)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    as_of = datetime.fromisoformat(args.as_of)
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise SystemExit("--as-of must be timezone-aware")
    if not 1 <= args.limit <= 500:
        raise SystemExit("--limit must be between 1 and 500")
    database_url = os.environ.get(_DATABASE_URL_ENV)
    if not database_url:
        raise SystemExit(f"{_DATABASE_URL_ENV} is required")
    payload = asyncio.run(_acquire(database_url, as_of=as_of, limit=args.limit))
    args.output.write_bytes(_canonical_bytes(payload))
    print(
        json.dumps(
            {
                "status": "retained",
                "output": str(args.output),
                "contract_count": payload["contract_count"],
                "content_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
                "credentials_printed": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
