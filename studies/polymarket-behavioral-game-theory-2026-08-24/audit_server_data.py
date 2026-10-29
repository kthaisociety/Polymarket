# Copyright (c) 2026 Eigen Kapital. All rights reserved.
# Proprietary and confidential. See the LICENSE file in the project root.
"""Print a sanitized, read-only scientific coverage audit for Polymarket data."""

from __future__ import annotations

import asyncio
import json

import asyncpg

from research_agent.data_adapters.polymarket.database import (
    READ_ONLY_PROOF_QUERY,
    require_read_only_role,
)
from tools.dev.prod_secrets import read_secret


async def main() -> None:
    """Query bounded aggregate metadata without printing secrets or contract text."""
    connection = await asyncpg.connect(
        host="127.0.0.1",
        port=15432,
        user="human_ro",
        password=read_secret("human_ro_password"),
        database="bdl",
        command_timeout=120,
    )
    try:
        async with connection.transaction(isolation="repeatable_read", readonly=True):
            role = await connection.fetchrow(READ_ONLY_PROOF_QUERY)
            require_read_only_role(role)
            server_time = await connection.fetchval("SELECT transaction_timestamp()")
            contracts = await connection.fetchrow(
                """
                SELECT count(*) FILTER (WHERE venue = 'polymarket') AS market_count,
                       count(DISTINCT event_id) FILTER (
                           WHERE venue = 'polymarket' AND event_id IS NOT NULL
                       ) AS event_count,
                       count(*) FILTER (
                           WHERE venue = 'polymarket' AND event_id IS NULL
                       ) AS missing_event_id_count,
                       count(*) FILTER (
                           WHERE venue = 'polymarket' AND status = 'open'
                       ) AS open_count,
                       count(*) FILTER (
                           WHERE venue = 'polymarket' AND status = 'resolved'
                       ) AS resolved_count,
                       min(open_time) FILTER (WHERE venue = 'polymarket') AS first_open_time,
                       max(updated_at) FILTER (WHERE venue = 'polymarket') AS last_metadata_update
                FROM market.markets
                """
            )
            labels = await connection.fetchrow(
                """
                SELECT count(*) AS outcome_count,
                       count(*) FILTER (WHERE outcome_token IS NULL) AS missing_token_count,
                       count(*) FILTER (WHERE is_winner IS NOT NULL) AS gamma_exact_winner_outcome_count,
                       count(DISTINCT market_id) FILTER (
                           WHERE is_winner IS NOT NULL
                       ) AS gamma_exact_winner_market_count
                FROM market.market_outcomes
                WHERE venue = 'polymarket'
                """
            )
            resolutions = await connection.fetchrow(
                """
                SELECT count(*) AS resolution_count,
                       min(resolved_time) AS first_resolution_time,
                       max(resolved_time) AS last_resolution_time,
                       count(*) FILTER (WHERE cardinality(payouts) <> 2) AS nonbinary_payout_count
                FROM market.resolutions
                WHERE venue = 'polymarket'
                """
            )
            resolution_mapping = await connection.fetchrow(
                """
                WITH comparable AS (
                    SELECT o.market_id, o.outcome_index, o.payout AS gamma_payout,
                           r.payouts[o.outcome_index + 1] AS onchain_indexed_payout
                    FROM market.market_outcomes o
                    JOIN market.resolutions r USING (venue, market_id)
                    WHERE o.venue = 'polymarket'
                      AND o.payout IS NOT NULL
                )
                SELECT count(*) AS comparable_outcome_count,
                       count(DISTINCT market_id) AS comparable_market_count,
                       count(*) FILTER (
                           WHERE (CASE WHEN gamma_payout > 0.5 THEN 1 ELSE 0 END)
                               = onchain_indexed_payout
                       ) AS direct_direction_match_count,
                       count(*) FILTER (
                           WHERE (CASE WHEN gamma_payout > 0.5 THEN 1 ELSE 0 END)
                               = 1 - onchain_indexed_payout
                       ) AS reversed_direction_match_count,
                       max(abs(gamma_payout - onchain_indexed_payout)) AS maximum_terminal_gap
                FROM comparable
                """
            )
            taker_tape = await connection.fetchrow(
                """
                WITH recent AS (
                    SELECT market_id, account, fill_time, tx_hash,
                           (raw->>'block_number')::bigint AS block_number
                    FROM market.fills
                    WHERE venue = 'polymarket'
                      AND fill_time >= now() - interval '7 days'
                      AND lower('0x' || right(raw->'topics'->>3, 40)) = lower(raw->>'address')
                )
                SELECT count(*) AS taker_prints_7d,
                       count(DISTINCT market_id) AS taker_markets_7d,
                       count(DISTINCT account) AS taker_wallets_7d,
                       count(DISTINCT tx_hash) AS transaction_count_7d,
                       count(*) FILTER (WHERE account IS NULL) AS missing_account_count,
                       count(*) FILTER (WHERE block_number IS NULL) AS missing_block_count,
                       min(fill_time) AS first_fill_time_7d,
                       max(fill_time) AS last_fill_time_7d
                FROM recent
                """
            )
            labeled_taker_tape = await connection.fetchrow(
                """
                WITH taker AS (
                    SELECT f.market_id, f.account, f.fill_time
                    FROM market.fills f
                    WHERE f.venue = 'polymarket'
                      AND f.fill_time >= now() - interval '30 days'
                      AND lower('0x' || right(f.raw->'topics'->>3, 40)) = lower(f.raw->>'address')
                )
                SELECT count(*) AS taker_prints_30d,
                       count(*) FILTER (WHERE r.market_id IS NOT NULL) AS resolved_prints_30d,
                       count(DISTINCT taker.market_id) FILTER (
                           WHERE r.market_id IS NOT NULL
                       ) AS resolved_markets_with_taker_fills_30d,
                       count(DISTINCT taker.account) FILTER (
                           WHERE r.market_id IS NOT NULL
                       ) AS wallets_in_resolved_markets_30d
                FROM taker
                LEFT JOIN market.resolutions r
                  ON r.venue = 'polymarket' AND r.market_id = taker.market_id
                """
            )
            recent_market_data = await connection.fetchrow(
                """
                SELECT
                    (SELECT count(*) FROM market.price_series
                     WHERE venue = 'polymarket' AND ts >= now() - interval '7 days')
                        AS price_points_7d,
                    (SELECT count(DISTINCT market_id) FROM market.price_series
                     WHERE venue = 'polymarket' AND ts >= now() - interval '7 days')
                        AS price_markets_7d,
                    (SELECT count(*) FROM market.fills
                     WHERE venue = 'polymarket' AND fill_time >= now() - interval '7 days')
                        AS fills_7d,
                    (SELECT count(DISTINCT market_id) FROM market.fills
                     WHERE venue = 'polymarket' AND fill_time >= now() - interval '7 days')
                        AS fill_markets_7d,
                    (SELECT count(*) FROM market.fills
                     WHERE venue = 'polymarket' AND fill_time >= now() - interval '7 days'
                       AND account IS NULL) AS unattributed_fills_7d,
                    (SELECT count(*) FROM market.book_snapshots
                     WHERE venue = 'polymarket' AND ts >= now() - interval '7 days')
                        AS book_snapshots_7d,
                    (SELECT count(DISTINCT market_id) FROM market.book_snapshots
                     WHERE venue = 'polymarket' AND ts >= now() - interval '7 days')
                        AS book_snapshot_markets_7d,
                    (SELECT count(*) FROM market.book_deltas
                     WHERE venue = 'polymarket' AND ts >= now() - interval '24 hours')
                        AS book_deltas_24h,
                    (SELECT count(DISTINCT market_id) FROM market.book_deltas
                     WHERE venue = 'polymarket' AND ts >= now() - interval '24 hours')
                        AS book_delta_markets_24h
                """
            )
            raw_clock_keys = await connection.fetch(
                """
                SELECT DISTINCT key
                FROM (
                    SELECT raw
                    FROM market.book_deltas
                    WHERE venue = 'polymarket'
                      AND ts >= now() - interval '24 hours'
                    ORDER BY ts DESC
                    LIMIT 1000
                ) AS recent
                CROSS JOIN LATERAL jsonb_object_keys(recent.raw) AS keys(key)
                ORDER BY key
                """
            )
            table_estimates = await connection.fetch(
                """
                SELECT schemaname, relname, n_live_tup, last_analyze, last_autoanalyze
                FROM pg_stat_user_tables
                WHERE schemaname = 'market'
                  AND relname IN (
                      'markets', 'market_outcomes', 'resolutions', 'price_series',
                      'fills', 'book_snapshots', 'book_deltas', 'candles'
                  )
                ORDER BY relname
                """
            )
        payload = {
            "server_transaction_time": server_time,
            "role_proof": dict(role),
            "contracts": dict(contracts),
            "labels": dict(labels),
            "resolutions": dict(resolutions),
            "resolution_outcome_index_crosscheck": dict(resolution_mapping),
            "taker_tape": dict(taker_tape),
            "labeled_taker_tape": dict(labeled_taker_tape),
            "recent_market_data": dict(recent_market_data),
            "dual_clock_quality_24h": {
                "reference_time_columns_deployed": False,
                "recent_delta_raw_keys": [row["key"] for row in raw_clock_keys],
            },
            "planner_estimates": [dict(row) for row in table_estimates],
        }
        print(json.dumps(payload, default=str, sort_keys=True))
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())

