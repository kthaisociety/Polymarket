# ruff: noqa: ASYNC240, D103, EM101, EM102, INP001, PLC0415, SIM117, T201, TRY003

"""Retain exact Hormuz fill opportunities across the historical publication-vintage window."""

from __future__ import annotations

import argparse
import asyncio
import gzip
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
_MARKET_IDS = (
    "0x5c79dfde05559b79a9cb9f7c4187e4d49632dd042572ae676952f812732591cc",
    "0x60c2c085ee8c16bc8f2419739a94971d4c9d00f637ead10fc0f540afa1be64e8",
    "0xa08a5ce99e14ce0b22767af6f16c08a2ab012249444c20887193a9a3e98e11fc",
)
_QUERY = """
SELECT fill_time, fill_uid, market_id, outcome_index, side, price, size
FROM market.fills
WHERE venue = 'polymarket'
  AND market_id = ANY($1::text[])
  AND outcome_index = 0
  AND fill_time >= $2::timestamptz
  AND fill_time <= $3::timestamptz
  AND (raw->'topics' IS NULL
       OR lower('0x' || right(raw->'topics'->>3, 40)) = lower(raw->>'address'))
ORDER BY fill_time, fill_uid
""".strip()


def _default(value: object) -> object:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def _line(value: object) -> bytes:
    return (
        json.dumps(value, default=_default, separators=(",", ":"), sort_keys=True) + "\n"
    ).encode()


async def _acquire(
    database_url: str, *, start: datetime, end: datetime, output: Path
) -> dict[str, object]:
    from core.db.pool import close_pool, create_pool

    pool = await create_pool(database_url, min_size=1, max_size=1)
    temporary = output.with_suffix(f"{output.suffix}.partial")
    count = 0
    uncompressed_hash = hashlib.sha256()
    by_market = dict.fromkeys(_MARKET_IDS, 0)
    try:
        async with (
            pool.acquire() as connection,
            connection.transaction(isolation="repeatable_read", readonly=True),
        ):
            proof = await connection.fetchrow(READ_ONLY_PROOF_QUERY)
            require_read_only_role(proof)
            rows = connection.cursor(_QUERY, _MARKET_IDS, start, end, prefetch=1000)
            output.parent.mkdir(parents=True, exist_ok=True)
            with temporary.open("xb") as raw_output:
                with gzip.GzipFile(fileobj=raw_output, mode="wb", mtime=0) as compressed:
                    header = _line(
                        {
                            "kind": "header",
                            "schema": "chronos-polymarket-hormuz-taker-fills-jsonl/v2",
                            "row_semantics": (
                                "One taker aggregate row per match bundle; side is the "
                                "aggressor's YES-outcome side."
                            ),
                            "environment_id": "bdl-polymarket-production-readonly",
                            "market_ids": _MARKET_IDS,
                            "outcome_index": 0,
                            "start": start,
                            "end": end,
                            "query_sha256": hashlib.sha256(_QUERY.encode()).hexdigest(),
                            "authority": {
                                "database_role": "human_ro",
                                "default_read_only": True,
                                "transaction_read_only": True,
                                "repeatable_read": True,
                                "insert_update_privileges": False,
                            },
                        }
                    )
                    compressed.write(header)
                    uncompressed_hash.update(header)
                    async for row in rows:
                        item = {"kind": "fill", **dict(row)}
                        encoded = _line(item)
                        compressed.write(encoded)
                        uncompressed_hash.update(encoded)
                        by_market[str(row["market_id"])] += 1
                        count += 1
            temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
        await close_pool(pool)
    return {
        "status": "retained",
        "fill_count": count,
        "fills_by_market": by_market,
        "compressed_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "uncompressed_sha256": uncompressed_hash.hexdigest(),
        "compressed_bytes": output.stat().st_size,
        "credentials_printed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    start = datetime.fromisoformat(args.start)
    end = datetime.fromisoformat(args.end)
    if start.tzinfo is None or end.tzinfo is None or start >= end:
        raise SystemExit("ordered timezone-aware bounds are required")
    database_url = os.environ.get(_DATABASE_URL_ENV)
    if not database_url:
        raise SystemExit(f"{_DATABASE_URL_ENV} is required")
    result = asyncio.run(_acquire(database_url, start=start, end=end, output=args.output))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
