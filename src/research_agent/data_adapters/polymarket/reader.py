"""Read-only protocol and production implementation for Polymarket research facts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from research_agent.data_adapters.polymarket.models import (
    PolymarketBlockVintage,
    PolymarketContractRecord,
    PolymarketFillRecord,
    PolymarketOutcomeRecord,
)

if TYPE_CHECKING:
    from collections.abc import Mapping
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
