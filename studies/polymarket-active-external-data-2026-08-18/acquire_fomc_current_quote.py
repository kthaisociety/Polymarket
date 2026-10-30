# ruff: noqa: D103, EM101, EM102, INP001, PLC0415, T201, TRY003

"""Retain one current executable FOMC quote through the proved read-only boundary."""

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

_DATABASE_URL_ENV = "POLYMARKET_DATABASE_URL"
_MARKET_ID = "0x876506d8b2bd7a0d3fa4fe18c024eee6e1dd81ee24c26795dadd6cfe4a7b5d0d"
_QUERY = """
SELECT ts, seq, bid, ask
FROM market.book_tops
WHERE venue = 'polymarket' AND market_id = $1 AND outcome_index = 0
""".strip()


def _default(value: object) -> object:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(type(value).__name__)


async def _read(database_url: str) -> dict[str, object]:
    from research_agent.data_adapters.polymarket.pool import close_pool, create_pool

    pool = await create_pool(database_url, min_size=1, max_size=1)
    try:
        async with (
            pool.acquire() as connection,
            connection.transaction(isolation="repeatable_read", readonly=True),
        ):
            proof = await connection.fetchrow(READ_ONLY_PROOF_QUERY)
            require_read_only_role(proof)
            row = await connection.fetchrow(_QUERY, _MARKET_ID)
            if row is None or row["bid"] is None or row["ask"] is None:
                raise RuntimeError("selected FOMC outcome has no two-sided current quote")
        return {
            "schema": "chronos-current-executable-quote/v1",
            "environment_id": "polymarket-production-readonly",
            "market_id": _MARKET_ID,
            "outcome_index": 0,
            "quote": dict(row),
            "query_sha256": hashlib.sha256(_QUERY.encode()).hexdigest(),
            "authority": {
                "database_role": "human_ro",
                "default_read_only": True,
                "transaction_read_only": True,
                "repeatable_read": True,
                "insert_update_privileges": False,
            },
            "caveat": "Top of book is not a depth-qualified fill price.",
        }
    finally:
        await close_pool(pool)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    database_url = os.environ.get(_DATABASE_URL_ENV)
    if not database_url:
        raise SystemExit(f"{_DATABASE_URL_ENV} is required")
    payload = asyncio.run(_read(database_url))
    content = (json.dumps(payload, default=_default, indent=2, sort_keys=True) + "\n").encode()
    try:
        with args.output.open("xb") as output:
            output.write(content)
    except FileExistsError:
        if args.output.read_bytes() != content:
            raise ValueError("quote receipt already contains different bytes") from None
    print(
        json.dumps(
            {
                "status": "retained",
                "output": str(args.output),
                "sha256": hashlib.sha256(content).hexdigest(),
                "credentials_printed": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
