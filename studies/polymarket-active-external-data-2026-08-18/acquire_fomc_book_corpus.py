# ruff: noqa: ASYNC240, D103, EM101, EM102, INP001, PLC0415, PTH105, SIM117, T201, TRY003

"""Retain an exact bounded FOMC order-book corpus through the proved read-only boundary."""

from __future__ import annotations

import argparse
import asyncio
import gzip
import hashlib
import json
import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

from research_agent.data_adapters.polymarket.database import (
    READ_ONLY_PROOF_QUERY,
    require_read_only_role,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

_DATABASE_URL_ENV = "BDL__DB__URL"
_MARKET_ID = "0x876506d8b2bd7a0d3fa4fe18c024eee6e1dd81ee24c26795dadd6cfe4a7b5d0d"
_QUERY = """
WITH targets AS (
    SELECT unnest($2::timestamptz[]) AS target_time
), ranked AS (
    SELECT
        targets.target_time,
        snapshot.venue,
        snapshot.market_id,
        snapshot.outcome_index,
        snapshot.ts,
        snapshot.seq,
        snapshot.bids,
        snapshot.asks,
        snapshot.raw,
        row_number() OVER (
            PARTITION BY targets.target_time
            ORDER BY snapshot.ts DESC, snapshot.seq DESC
        ) AS quote_rank
    FROM targets
    JOIN market.book_snapshots AS snapshot
      ON snapshot.ts <= targets.target_time
     AND snapshot.ts >= targets.target_time - interval '15 minutes'
    WHERE snapshot.venue = 'polymarket'
      AND snapshot.market_id = $1
      AND snapshot.outcome_index = 0
)
SELECT
    target_time, venue, market_id, outcome_index, ts, seq, bids, asks, raw
FROM ranked
WHERE quote_rank = 1
ORDER BY target_time
""".strip()


def _json_default(value: object) -> object:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def _line(value: object) -> bytes:
    return (
        json.dumps(
            value,
            default=_json_default,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode()


async def _acquire(
    database_url: str,
    *,
    targets: tuple[datetime, ...],
    output: Path,
) -> tuple[int, str, int]:
    from core.db.pool import close_pool, create_pool

    pool = await create_pool(database_url, min_size=1, max_size=1)
    temporary = output.with_suffix(f"{output.suffix}.partial")
    count = 0
    uncompressed_hash = hashlib.sha256()
    try:
        async with (
            pool.acquire() as connection,
            connection.transaction(isolation="repeatable_read", readonly=True),
        ):
            proof = await connection.fetchrow(READ_ONLY_PROOF_QUERY)
            require_read_only_role(proof)
            rows = await connection.fetch(_QUERY, _MARKET_ID, targets)
            output.parent.mkdir(parents=True, exist_ok=True)
            with temporary.open("xb") as raw_output:
                with gzip.GzipFile(fileobj=raw_output, mode="wb", mtime=0) as compressed:
                    header = {
                        "kind": "header",
                        "schema": "chronos-polymarket-book-snapshots-jsonl/v1",
                        "environment_id": "bdl-polymarket-production-readonly",
                        "market_id": _MARKET_ID,
                        "outcome_index": 0,
                        "target_times": targets,
                        "maximum_quote_age_minutes": 15,
                        "query_sha256": hashlib.sha256(_QUERY.encode()).hexdigest(),
                        "authority": {
                            "database_role": "human_ro",
                            "default_read_only": True,
                            "transaction_read_only": True,
                            "repeatable_read": True,
                            "insert_update_privileges": False,
                        },
                    }
                    encoded = _line(header)
                    compressed.write(encoded)
                    uncompressed_hash.update(encoded)
                    for row in rows:
                        snapshot: Mapping[str, object] = dict(row)
                        encoded = _line({"kind": "snapshot", **snapshot})
                        compressed.write(encoded)
                        uncompressed_hash.update(encoded)
                        count += 1
            os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
        await close_pool(pool)
    return count, uncompressed_hash.hexdigest(), output.stat().st_size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", action="append", default=[])
    parser.add_argument("--decision", action="append", default=[])
    parser.add_argument("--horizon-hours", action="append", type=int, default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    explicit = [datetime.fromisoformat(item) for item in args.target]
    decisions = [datetime.fromisoformat(item) for item in args.decision]
    if args.horizon_hours and not decisions:
        raise SystemExit("--horizon-hours requires at least one --decision")
    expanded = decisions + [
        decision + timedelta(hours=horizon)
        for decision in decisions
        for horizon in args.horizon_hours
    ]
    targets = tuple(sorted(set(explicit + expanded)))
    if not targets:
        raise SystemExit("at least one --target or --decision is required")
    if any(item.tzinfo is None or item.utcoffset() is None for item in targets):
        raise SystemExit("every --target must be timezone-aware")
    if any(horizon <= 0 for horizon in args.horizon_hours):
        raise SystemExit("--horizon-hours values must be positive")
    database_url = os.environ.get(_DATABASE_URL_ENV)
    if not database_url:
        raise SystemExit(f"{_DATABASE_URL_ENV} is required")
    count, uncompressed_sha256, size = asyncio.run(
        _acquire(database_url, targets=targets, output=args.output)
    )
    print(
        json.dumps(
            {
                "status": "retained",
                "output": str(args.output),
                "snapshot_count": count,
                "compressed_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
                "uncompressed_sha256": uncompressed_sha256,
                "compressed_bytes": size,
                "credentials_printed": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
