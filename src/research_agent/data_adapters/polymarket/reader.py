"""Read-only protocol and production implementation for Polymarket research facts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Protocol, cast

from research_agent.data_adapters.polymarket.models import (
    PolymarketBlockVintage,
    PolymarketContractRecord,
    PolymarketCorpus,
    PolymarketCorpusContract,
    PolymarketCorpusOutcome,
    PolymarketCorpusRequest,
    PolymarketFillRecord,
    PolymarketOutcomeRecord,
    PolymarketPricePoint,
    PolymarketResolutionRecord,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime
    from decimal import Decimal


class _FetchExecutor(Protocol):
    """Small direct SELECT surface implemented by an asyncpg connection or test fake."""

    async def fetch(self, query: str, *args: object) -> Sequence[Mapping[str, object]]:
        """Return rows for one parameterized SELECT."""
        ...

    async def fetchrow(self, query: str, *args: object) -> Mapping[str, object] | None:
        """Return one row for a parameterized SELECT."""
        ...


_VENUE = "polymarket"
_HISTORY_CURSOR = "pm-onchain-history"
_FORWARD_CURSOR = "pm-onchain-forward"


class PolymarketResearchReader(Protocol):
    """Minimum read-only fact surface required by the Chronos adapter."""

    async def read_vintage(self) -> PolymarketBlockVintage:
        """Read the closed production block window."""
        ...

    async def read_contracts(
        self, market_ids: tuple[str, ...]
    ) -> tuple[PolymarketContractRecord, ...]:
        """Read exact contract and outcome identities."""
        ...

    async def read_fills(self, market_id: str) -> tuple[PolymarketFillRecord, ...]:
        """Read one contract's taker-side tape in event-time order."""
        ...


class EnginePolymarketResearchReader:
    """Read the legacy BDL schema through a Chronos-owned read-only surface.

    The public name is retained for compatibility with existing Chronos studies. The
    implementation is standalone and does not import the parent BDL engine.
    """

    def __init__(self, executor: _FetchExecutor) -> None:
        """Retain a proved read-only database executor."""
        self._executor = executor

    async def read_vintage(self) -> PolymarketBlockVintage:
        """Read and validate the two persisted on-chain sweep cursors."""
        history = await self._executor.fetchrow(_CURSOR_SQL, _HISTORY_CURSOR)
        forward = await self._executor.fetchrow(_CURSOR_SQL, _FORWARD_CURSOR)
        history_payload = None if history is None else history.get("cursor")
        forward_payload = None if forward is None else forward.get("cursor")
        lower = _cursor_block(history_payload, _HISTORY_CURSOR)
        upper = _cursor_block(forward_payload, _FORWARD_CURSOR)
        return PolymarketBlockVintage(
            lower_block=lower,
            upper_block=upper,
            history_cursor=_HISTORY_CURSOR,
            forward_cursor=_FORWARD_CURSOR,
        )

    async def read_contracts(
        self, market_ids: tuple[str, ...]
    ) -> tuple[PolymarketContractRecord, ...]:
        """Read exact contract metadata from the legacy production schema."""
        count_rows = await self._executor.fetch(_OUTCOME_COUNTS_SQL, _VENUE)
        identity_rows = await self._executor.fetch(_IDENTITY_SQL, _VENUE)
        close_rows = await self._executor.fetch(_CLOSE_TIMES_SQL, _VENUE)
        resolved_rows = await self._executor.fetch(_RESOLVED_MARKETS_SQL, _VENUE)
        payout_rows = await self._executor.fetch(_RESOLVED_PAYOUTS_SQL, _VENUE)
        counts = {
            str(row["market_id"]): int(cast("int", row["outcome_count"])) for row in count_rows
        }
        close_times = {
            str(row["market_id"]): cast("datetime", row["close_time"]) for row in close_rows
        }
        resolved = {str(row["market_id"]) for row in resolved_rows}
        outcomes = _outcomes_by_market(identity_rows, payout_rows)
        return tuple(
            PolymarketContractRecord(
                market_id=market_id,
                outcome_count=counts[market_id],
                outcomes=outcomes.get(market_id, ()),
                close_time=close_times.get(market_id),
                resolved=market_id in resolved,
            )
            for market_id in market_ids
        )

    async def read_fills(self, market_id: str) -> tuple[PolymarketFillRecord, ...]:
        """Map one direct taker-tape read into adapter-local records."""
        rows = await self._executor.fetch(_MARKET_TAKER_FILLS_SQL, _VENUE, market_id)
        return tuple(_fill_record(row) for row in rows)


class DatabasePolymarketCorpusReader:
    """Read the new research corpus facts directly from a proved read-only connection."""

    def __init__(self, executor: _FetchExecutor) -> None:
        """Retain a connection whose role and transaction are proved by composition."""
        self._executor = executor

    async def read_corpus(self, request: PolymarketCorpusRequest) -> PolymarketCorpus:
        """Read one deterministic resolved binary cohort and its selected price leg."""
        contract_rows = await self._executor.fetch(
            _CORPUS_CONTRACTS_SQL,
            _VENUE,
            request.as_of,
            request.outcome_index,
            request.fidelity,
            request.min_points,
            request.max_markets,
        )
        contracts, resolutions = _corpus_contracts(contract_rows)
        if not contracts:
            msg = "Polymarket corpus selection returned no eligible resolved contracts"
            raise ValueError(msg)
        market_ids = [item.market_id for item in contracts]
        price_rows = await self._executor.fetch(
            _CORPUS_PRICES_SQL,
            _VENUE,
            market_ids,
            request.outcome_index,
            request.fidelity,
            request.as_of,
        )
        prices = tuple(
            PolymarketPricePoint(
                market_id=str(row["market_id"]),
                outcome_index=int(cast("int", row["outcome_index"])),
                outcome_token=str(row["outcome_token"]),
                observed_at=cast("datetime", row["ts"]),
                price=cast("Decimal", row["price"]),
                fidelity=int(cast("int", row["fidelity"])),
            )
            for row in price_rows
        )
        return PolymarketCorpus(request, contracts, resolutions, prices)


def _cursor_block(payload: object, name: str) -> int:
    if not isinstance(payload, Mapping):
        msg = f"Polymarket cursor {name} does not carry an exact block"
        raise TypeError(msg)
    block = cast("Mapping[str, object]", payload).get("block")
    if not isinstance(block, int):
        msg = f"Polymarket cursor {name} does not carry an exact block"
        raise TypeError(msg)
    return block


def _outcomes_by_market(
    identity_rows: Sequence[Mapping[str, object]],
    payout_rows: Sequence[Mapping[str, object]],
) -> dict[str, tuple[PolymarketOutcomeRecord, ...]]:
    payouts = {
        (str(row["market_id"]), int(cast("int", row["outcome_index"]))): cast(
            "Decimal", row["payout"]
        )
        for row in payout_rows
    }
    grouped: dict[str, list[PolymarketOutcomeRecord]] = {}
    for row in identity_rows:
        market_id = str(row["market_id"])
        outcome_index = int(cast("int", row["outcome_index"]))
        grouped.setdefault(market_id, []).append(
            PolymarketOutcomeRecord(
                outcome_index,
                str(row["outcome_token"]),
                payouts.get((market_id, outcome_index)),
            )
        )
    return {
        market_id: tuple(sorted(outcomes, key=lambda item: item.outcome_index))
        for market_id, outcomes in grouped.items()
    }


def _fill_record(row: Mapping[str, object]) -> PolymarketFillRecord:
    block = row["block_number"]
    return PolymarketFillRecord(
        fill_uid=str(row["fill_uid"]),
        fill_time=cast("datetime", row["fill_time"]),
        market_id=str(row["market_id"]),
        outcome_index=int(cast("int", row["outcome_index"])),
        outcome_token=str(row["outcome_token"]),
        side=str(row["side"]),
        price=cast("Decimal", row["price"]),
        size=cast("Decimal", row["size"]),
        block_number=block if isinstance(block, int) else None,
        transaction_hash=cast("str | None", row["tx_hash"]),
    )


_CURSOR_SQL = "SELECT cursor FROM ops.ingest_cursors WHERE name = $1"

_OUTCOME_COUNTS_SQL = """
SELECT market_id, outcome_count
FROM market.markets
WHERE venue = $1
"""

_IDENTITY_SQL = """
SELECT outcome_token, market_id, outcome_index
FROM market.market_outcomes
WHERE venue = $1 AND outcome_token IS NOT NULL
"""

_CLOSE_TIMES_SQL = """
SELECT market_id, close_time
FROM market.markets
WHERE venue = $1 AND tracked AND close_time IS NOT NULL
"""

_RESOLVED_MARKETS_SQL = """
SELECT market_id
FROM market.markets
WHERE venue = $1 AND status = 'resolved'
"""

_RESOLVED_PAYOUTS_SQL = """
SELECT market_id, outcome_index, payout
FROM market.market_outcomes
WHERE venue = $1 AND payout IS NOT NULL
"""

_MARKET_TAKER_FILLS_SQL = """
-- One market's per-print tape: each match once, from the taker's side.
SELECT venue, fill_time, fill_uid, market_id, outcome_index, outcome_token,
       account, side, price, size, tx_hash, log_index,
       (raw->>'block_number')::bigint AS block_number
FROM market.fills
WHERE venue = $1 AND market_id = $2
  AND (raw->'topics' IS NULL
       OR lower('0x' || right(raw->'topics'->>3, 40)) = lower(raw->>'address'))
ORDER BY fill_time, COALESCE(log_index, 0)
"""


def _corpus_contracts(
    rows: Sequence[Mapping[str, object]],
) -> tuple[tuple[PolymarketCorpusContract, ...], tuple[PolymarketResolutionRecord, ...]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    order: list[str] = []
    for row in rows:
        market_id = str(row["market_id"])
        if market_id not in grouped:
            grouped[market_id] = []
            order.append(market_id)
        grouped[market_id].append(row)
    contracts: list[PolymarketCorpusContract] = []
    resolutions: list[PolymarketResolutionRecord] = []
    for market_id in order:
        market_rows = grouped[market_id]
        first = market_rows[0]
        event_id = first["event_id"]
        if not isinstance(event_id, str) or not event_id:
            msg = f"Polymarket contract {market_id} has no authoritative event identity"
            raise ValueError(msg)
        outcomes = tuple(
            PolymarketCorpusOutcome(
                outcome_index=int(cast("int", row["outcome_index"])),
                label=str(row["label"]),
                outcome_token=str(row["outcome_token"]),
                payout=cast("Decimal", row["payout"]),
            )
            for row in market_rows
        )
        payouts_value = first["payouts"]
        if not isinstance(payouts_value, list | tuple):
            msg = f"Polymarket resolution {market_id} has no payout vector"
            raise TypeError(msg)
        payout_values = cast("Sequence[object]", payouts_value)
        payouts = tuple(cast("Decimal", value) for value in payout_values)
        contracts.append(
            PolymarketCorpusContract(
                market_id=market_id,
                event_id=event_id,
                market_type=str(first["market_type"]),
                question=str(first["question"]),
                open_time=cast("datetime", first["open_time"]),
                close_time=cast("datetime", first["close_time"]),
                outcomes=outcomes,
            )
        )
        resolutions.append(
            PolymarketResolutionRecord(
                market_id=market_id,
                resolved_time=cast("datetime", first["resolved_time"]),
                payouts=payouts,
                oracle=cast("str | None", first["oracle"]),
                question_id=cast("str | None", first["question_id"]),
                transaction_hash=cast("str | None", first["resolution_tx_hash"]),
            )
        )
    return tuple(contracts), tuple(resolutions)


_CORPUS_CONTRACTS_SQL = """
WITH eligible AS (
    SELECT m.market_id, m.event_id, m.market_type, m.question,
           m.open_time, m.close_time, m.outcome_count,
           r.resolved_time, r.oracle, r.question_id, r.payouts,
           r.tx_hash AS resolution_tx_hash
    FROM market.resolutions r
    JOIN market.markets m USING (venue, market_id)
    WHERE r.venue = $1
      AND r.resolved_time <= $2
      AND m.market_type = 'binary'
      AND m.event_id IS NOT NULL
      AND m.open_time IS NOT NULL
      AND m.close_time IS NOT NULL
      AND m.open_time < m.close_time
      AND r.resolved_time >= m.close_time
      AND m.outcome_count = 2
      AND cardinality(r.payouts) = 2
      AND (
          SELECT count(*)
          FROM (
              SELECT 1
              FROM market.price_series p
              WHERE p.venue = r.venue
                AND p.market_id = r.market_id
                AND p.outcome_index = $3
                AND p.fidelity = $4
                AND p.ts <= LEAST(m.close_time, $2)
              ORDER BY p.ts
              LIMIT $5
          ) AS bounded_coverage
      ) = $5
    ORDER BY r.resolved_time, m.event_id, m.market_id
    LIMIT $6
)
SELECT e.market_id, e.event_id, e.market_type, e.question,
       e.open_time, e.close_time, e.outcome_count,
       e.resolved_time, e.oracle, e.question_id, e.payouts,
       e.resolution_tx_hash,
       o.outcome_index, o.label, o.outcome_token,
       e.payouts[o.outcome_index + 1] AS payout
FROM eligible e
JOIN market.market_outcomes o
  ON o.venue = $1 AND o.market_id = e.market_id
ORDER BY e.resolved_time, e.event_id, e.market_id, o.outcome_index
"""


_CORPUS_PRICES_SQL = """
SELECT p.market_id, p.outcome_index, p.outcome_token,
       p.ts, p.price, p.fidelity
FROM market.price_series p
JOIN market.markets m
  ON m.venue = p.venue AND m.market_id = p.market_id
WHERE p.venue = $1
  AND p.market_id = ANY($2::text[])
  AND p.outcome_index = $3
  AND p.fidelity = $4
  AND p.ts <= LEAST(m.close_time, $5)
ORDER BY p.market_id, p.ts
"""
