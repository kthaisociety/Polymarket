# ruff: noqa: D103, EM101, EM102, INP001, PLC0415, T201, TRY003

"""Retain active Kalshi markets with recent fills for cross-venue semantic audit."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from research_agent.data_adapters.polymarket.database import (
    READ_ONLY_PROOF_QUERY,
    require_read_only_role,
)

_DATABASE_URL_ENV = "BDL__DB__URL"
_MAX_LIMIT = 1000
_QUERY = """
WITH recent AS (
    SELECT market_id,
           count(*) AS fills_14d,
           sum(size * price) AS observed_notional_14d,
           min(fill_time) AS first_fill_14d,
           max(fill_time) AS last_fill_14d
    FROM market.fills
    WHERE venue = 'kalshi'
      AND fill_time > $1::timestamptz - interval '14 days'
      AND fill_time <= $1::timestamptz
    GROUP BY market_id
)
SELECT m.market_id, m.event_id, m.series_id, m.question, m.slug, m.status,
       m.open_time, m.close_time, m.updated_at, m.raw,
       r.fills_14d, r.observed_notional_14d, r.first_fill_14d, r.last_fill_14d
FROM market.markets AS m
JOIN recent AS r USING (market_id)
WHERE m.venue = 'kalshi'
  AND m.status = 'open'
  AND (m.close_time IS NULL OR m.close_time > $1::timestamptz)
ORDER BY r.observed_notional_14d DESC NULLS LAST, m.market_id
LIMIT $2
""".strip()


def _default(value: object) -> object:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


async def _read(database_url: str, *, as_of: datetime, limit: int) -> dict[str, object]:
    from core.db.pool import close_pool, create_pool

    pool = await create_pool(database_url, min_size=1, max_size=1)
    try:
        async with (
            pool.acquire() as connection,
            connection.transaction(isolation="repeatable_read", readonly=True),
        ):
            proof = await connection.fetchrow(READ_ONLY_PROOF_QUERY)
            require_read_only_role(proof)
            rows = await connection.fetch(_QUERY, as_of, limit)
        return {
            "schema": "chronos-active-kalshi-inventory/v1",
            "environment_id": "bdl-polymarket-production-readonly",
            "as_of": as_of,
            "selection": {
                "venue": "kalshi",
                "status": "open",
                "recent_fill_window_days": 14,
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
            "contract_count": len(rows),
            "contracts": [dict(row) for row in rows],
            "credentials_printed": False,
        }
    finally:
        await close_pool(pool)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    as_of = datetime.fromisoformat(args.as_of)
    if as_of.tzinfo is None or not 1 <= args.limit <= _MAX_LIMIT:
        raise SystemExit("timezone-aware --as-of and limit 1..1000 are required")
    database_url = os.environ.get(_DATABASE_URL_ENV)
    if not database_url:
        raise SystemExit(f"{_DATABASE_URL_ENV} is required")
    payload = asyncio.run(_read(database_url, as_of=as_of, limit=args.limit))
    content = (json.dumps(payload, default=_default, indent=2, sort_keys=True) + "\n").encode()
    try:
        with args.output.open("xb") as output:
            output.write(content)
    except FileExistsError:
        if args.output.read_bytes() != content:
            raise ValueError("Kalshi inventory already contains different bytes") from None
    print(
        json.dumps(
            {
                "status": "retained",
                "contract_count": payload["contract_count"],
                "sha256": hashlib.sha256(content).hexdigest(),
                "output": str(args.output),
                "credentials_printed": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
