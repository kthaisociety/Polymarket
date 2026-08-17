"""Read-only protocol and production implementation for Polymarket research facts."""

from __future__ import annotations

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
    from collections.abc import Mapping, Sequence
    from datetime import datetime
    from decimal import Decimal

    from core.db.queries import Executor
    from market.models import Fill, Identity

    class _Status(Protocol):
        message: str


class _StatusOr[Value](Protocol):
    def ok(self) -> bool:
        """Return whether the engine read succeeded."""
        ...

    def value(self) -> Value:
        """Return the successful engine read value."""
        ...

    def status(self) -> _Status:
        """Return the failed engine read status."""
        ...


class _FetchExecutor(Protocol):
    """Small direct SELECT surface implemented by an asyncpg connection or test fake."""

    async def fetch(self, query: str, *args: object) -> Sequence[Mapping[str, object]]:
        """Return rows for one parameterized SELECT."""
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
    """Adapt the BDL engine's public market reads without owning the database."""

    def __init__(self, executor: Executor) -> None:
        """Retain the engine executor used only through public read functions."""
        self._executor = executor

    async def read_vintage(self) -> PolymarketBlockVintage:
        """Read and validate the two persisted on-chain sweep cursors."""
        from market import reads  # noqa: PLC0415 - optional BDL composition dependency

        history = await reads.read_cursor(self._executor, _HISTORY_CURSOR)
        forward = await reads.read_cursor(self._executor, _FORWARD_CURSOR)
        history_payload = _require_result(history, _HISTORY_CURSOR)
        forward_payload = _require_result(forward, _FORWARD_CURSOR)
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
        """Compose contract metadata only from public engine read functions."""
        from market import reads  # noqa: PLC0415 - optional BDL composition dependency

        counts = _require_result(
            await reads.read_outcome_counts(self._executor, _VENUE), "outcome counts"
        )
        identity = _require_result(
            await reads.read_identity(self._executor, _VENUE), "outcome identity"
        )
        close_times = _require_result(
            await reads.read_close_times(self._executor, _VENUE),
            "contract close times",
        )
        resolved = _require_result(
            await reads.read_resolved_market_ids(self._executor, _VENUE),
            "resolved contracts",
        )
        payouts = _require_result(
            await reads.read_resolved_payouts(self._executor, _VENUE),
            "resolved outcome payouts",
        )
        outcomes = _outcomes_by_market(identity, payouts)
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
        """Map the engine's public taker-tape result into adapter-local records."""
        from market import reads  # noqa: PLC0415 - optional BDL composition dependency

        fills = _require_result(
            await reads.read_market_taker_fills(self._executor, _VENUE, market_id),
            f"taker fills for {market_id}",
        )
        return tuple(_fill_record(fill) for fill in fills)


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


def _require_result[Value](result: _StatusOr[Value], description: str) -> Value:
    if not result.ok():
        msg = f"Polymarket database read failed for {description}: {result.status().message}"
        raise RuntimeError(msg)
    return result.value()


def _cursor_block(payload: object, name: str) -> int:
    if not isinstance(payload, dict) or not isinstance(payload.get("block"), int):
        msg = f"Polymarket cursor {name} does not carry an exact block"
        raise TypeError(msg)
    return payload["block"]


def _outcomes_by_market(
    identity: Identity, payouts: Mapping[tuple[str, int], Decimal]
) -> dict[str, tuple[PolymarketOutcomeRecord, ...]]:
    grouped: dict[str, list[PolymarketOutcomeRecord]] = {}
    for token, outcome in identity.items():
        grouped.setdefault(outcome.market_id, []).append(
            PolymarketOutcomeRecord(
                outcome.outcome_index,
                token,
                payouts.get((outcome.market_id, outcome.outcome_index)),
            )
        )
    return {
        market_id: tuple(sorted(outcomes, key=lambda item: item.outcome_index))
        for market_id, outcomes in grouped.items()
    }


def _fill_record(fill: Fill) -> PolymarketFillRecord:
    block = fill.raw.get("block_number")
    return PolymarketFillRecord(
        fill_uid=fill.fill_uid,
        fill_time=fill.fill_time,
        market_id=fill.market_id,
        outcome_index=fill.outcome_index,
        outcome_token=fill.outcome_token or "",
        side=fill.side,
        price=fill.price,
        size=fill.size,
        block_number=block if isinstance(block, int) else None,
        transaction_hash=fill.tx_hash,
    )


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
        payouts = tuple(cast("Decimal", value) for value in payouts_value)
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
