"""Source records for importing a Polymarket contract tape into Chronos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from decimal import Decimal


@dataclass(frozen=True, slots=True)
class PolymarketBlockVintage:
    """Closed Polygon block window read from the production sweep cursors."""

    lower_block: int
    upper_block: int
    history_cursor: str
    forward_cursor: str

    def __post_init__(self) -> None:
        """Reject an empty or inverted data vintage."""
        if self.lower_block < 0 or self.lower_block >= self.upper_block:
            msg = "Polymarket block vintage must satisfy 0 <= lower < upper"
            raise ValueError(msg)
        if not self.history_cursor or not self.forward_cursor:
            msg = "Polymarket block vintage requires exact cursor identities"
            raise ValueError(msg)

    @property
    def identity(self) -> str:
        """Return the human-readable immutable block-window identity."""
        return f"polygon-blocks:{self.lower_block}-{self.upper_block}"


@dataclass(frozen=True, slots=True)
class PolymarketOutcomeRecord:
    """One exact outcome identity exposed by the engine read surface."""

    outcome_index: int
    outcome_token: str
    resolved_payout: Decimal | None


@dataclass(frozen=True, slots=True)
class PolymarketContractRecord:
    """Contract metadata required to interpret a requested market tape."""

    market_id: str
    outcome_count: int
    outcomes: tuple[PolymarketOutcomeRecord, ...]
    close_time: datetime | None
    resolved: bool

    def __post_init__(self) -> None:
        """Require complete, unique outcome identity for the contract."""
        if not self.market_id or self.outcome_count <= 0:
            msg = "Polymarket contract identity and outcome count are required"
            raise ValueError(msg)
        indexes = tuple(outcome.outcome_index for outcome in self.outcomes)
        tokens = tuple(outcome.outcome_token for outcome in self.outcomes)
        if (
            len(self.outcomes) != self.outcome_count
            or indexes != tuple(range(self.outcome_count))
            or len(set(tokens)) != len(tokens)
            or any(not token for token in tokens)
        ):
            msg = "Polymarket contract outcomes must be complete, ordered, and unique"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class PolymarketFillRecord:
    """One taker-side contract print returned by the engine read surface."""

    fill_uid: str
    fill_time: datetime
    market_id: str
    outcome_index: int
    outcome_token: str
    side: str
    price: Decimal
    size: Decimal
    block_number: int | None
    transaction_hash: str | None


@dataclass(frozen=True, slots=True)
class PolymarketImportRequest:
    """Exact contract scope and environment for one Chronos registration."""

    market_ids: tuple[str, ...]
    environment_id: str

    def __post_init__(self) -> None:
        """Reject empty, repeated, or ambiguous requested contract identity."""
        if (
            not self.market_ids
            or len(set(self.market_ids)) != len(self.market_ids)
            or any(not market_id for market_id in self.market_ids)
            or not self.environment_id
        ):
            msg = "Polymarket import requires unique market IDs and an environment identity"
            raise ValueError(msg)
