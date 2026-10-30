"""Composition test through the engine's real public Polymarket read functions."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from research_agent.data_adapters.polymarket import DatabasePolymarketResearchReader

MARKET = "0xmarket"
INCLUDED_BLOCK = 150


class _ProductionProtocolExecutor:
    """SQL executor implementing the same calls consumed by public market reads."""

    async def fetchrow(self, query: str, *args: object) -> dict[str, object] | None:
        assert "ops.ingest_cursors" in query
        name = args[0]
        block = 100 if name == "pm-onchain-history" else 200
        return {"cursor": {"block": block}}

    async def fetch(self, query: str, *args: object) -> list[dict[str, object]]:
        del args
        if "outcome_count" in query:
            return [{"market_id": MARKET, "outcome_count": 2}]
        if "outcome_token IS NOT NULL" in query:
            return [
                {"outcome_token": "yes", "market_id": MARKET, "outcome_index": 0},
                {"outcome_token": "no", "market_id": MARKET, "outcome_index": 1},
            ]
        if "tracked AND close_time IS NOT NULL" in query:
            return [{"market_id": MARKET, "close_time": datetime(2026, 2, 1, tzinfo=UTC)}]
        if "status = 'resolved'" in query:
            return [{"market_id": MARKET}]
        if "payout IS NOT NULL" in query:
            return [
                {"market_id": MARKET, "outcome_index": 0, "payout": Decimal(1)},
                {"market_id": MARKET, "outcome_index": 1, "payout": Decimal(0)},
            ]
        if "One market's per-print tape" in query:
            return [
                {
                    "venue": "polymarket",
                    "fill_time": datetime(2026, 1, 1, tzinfo=UTC),
                    "fill_uid": "fill-1",
                    "market_id": MARKET,
                    "outcome_index": 0,
                    "outcome_token": "yes",
                    "account": "wallet",
                    "side": "BUY",
                    "price": Decimal("0.4"),
                    "size": Decimal(10),
                    "tx_hash": "0xtx",
                    "log_index": 1,
                    "block_number": INCLUDED_BLOCK,
                }
            ]
        message = "unexpected production read SQL"
        raise AssertionError(message)


def test_database_reader_uses_parameterized_reads_for_exact_contract_tape() -> None:
    """The standalone reader uses only its local read-only database protocol."""
    reader = DatabasePolymarketResearchReader(_ProductionProtocolExecutor())

    vintage = asyncio.run(reader.read_vintage())
    contracts = asyncio.run(reader.read_contracts((MARKET,)))
    fills = asyncio.run(reader.read_fills(MARKET))

    assert vintage.identity == "polygon-blocks:100-200"
    assert contracts[0].market_id == MARKET
    assert contracts[0].outcomes[0].resolved_payout == Decimal(1)
    assert fills[0].fill_uid == "fill-1"
    assert fills[0].block_number == INCLUDED_BLOCK
