# ruff: noqa: D103, EM101, EM102, INP001, PLC0415, T201, TRY003

"""Retain exact market semantics and book coverage for selected active candidates."""

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
_MARKET_QUERY = """
SELECT market_id, event_id, question, slug, status, open_time, close_time, raw
FROM market.markets
WHERE venue = 'polymarket' AND market_id = ANY($1::text[])
ORDER BY market_id
""".strip()
_OUTCOME_QUERY = """
SELECT market_id, outcome_index, label, outcome_token, raw
FROM market.market_outcomes
WHERE venue = 'polymarket' AND market_id = ANY($1::text[])
ORDER BY market_id, outcome_index
""".strip()
_TOP_QUERY = """
SELECT market_id, outcome_index, ts, seq, bid, ask
FROM market.book_tops
WHERE venue = 'polymarket' AND market_id = ANY($1::text[])
ORDER BY market_id, outcome_index
""".strip()
_COVERAGE_QUERY = """
SELECT market_id, outcome_index, count(*) AS snapshot_count, min(ts) AS first_ts, max(ts) AS last_ts
FROM market.book_snapshots
WHERE venue = 'polymarket' AND market_id = ANY($1::text[])
GROUP BY market_id, outcome_index
ORDER BY market_id, outcome_index
""".strip()


def _default(value: object) -> object:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


async def _read(database_url: str, market_ids: tuple[str, ...]) -> dict[str, object]:
    from core.db.pool import close_pool, create_pool

    pool = await create_pool(database_url, min_size=1, max_size=1)
    try:
        async with (
            pool.acquire() as connection,
            connection.transaction(isolation="repeatable_read", readonly=True),
        ):
            proof = await connection.fetchrow(READ_ONLY_PROOF_QUERY)
            require_read_only_role(proof)
            markets = await connection.fetch(_MARKET_QUERY, market_ids)
            outcomes = await connection.fetch(_OUTCOME_QUERY, market_ids)
            tops = await connection.fetch(_TOP_QUERY, market_ids)
            coverage = await connection.fetch(_COVERAGE_QUERY, market_ids)
        return {
            "schema": "chronos-active-candidate-audit/v1",
            "environment_id": "bdl-polymarket-production-readonly",
            "market_ids": market_ids,
            "authority": {
                "database_role": "human_ro",
                "default_read_only": True,
                "transaction_read_only": True,
                "repeatable_read": True,
                "insert_update_privileges": False,
            },
            "query_sha256": {
                "markets": hashlib.sha256(_MARKET_QUERY.encode()).hexdigest(),
                "outcomes": hashlib.sha256(_OUTCOME_QUERY.encode()).hexdigest(),
                "tops": hashlib.sha256(_TOP_QUERY.encode()).hexdigest(),
                "coverage": hashlib.sha256(_COVERAGE_QUERY.encode()).hexdigest(),
            },
            "markets": [dict(row) for row in markets],
            "outcomes": [dict(row) for row in outcomes],
            "current_tops": [dict(row) for row in tops],
            "snapshot_coverage": [dict(row) for row in coverage],
        }
    finally:
        await close_pool(pool)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--market-id", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    market_ids = tuple(dict.fromkeys(args.market_id))
    database_url = os.environ.get(_DATABASE_URL_ENV)
    if not database_url:
        raise SystemExit(f"{_DATABASE_URL_ENV} is required")
    payload = asyncio.run(_read(database_url, market_ids))
    content = (json.dumps(payload, default=_default, indent=2, sort_keys=True) + "\n").encode()
    try:
        with args.output.open("xb") as output:
            output.write(content)
    except FileExistsError:
        if args.output.read_bytes() != content:
            raise ValueError("candidate audit already contains different bytes") from None
    print(
        json.dumps(
            {
                "status": "retained",
                "market_count": len(payload["markets"]),
                "output": str(args.output),
                "sha256": hashlib.sha256(content).hexdigest(),
                "credentials_printed": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
