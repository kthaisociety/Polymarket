"""Source records for importing a Polymarket contract tape into Chronos."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

_BINARY_OUTCOME_COUNT = 2
_MIN_CORPUS_POINTS = 2


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
    """One exact outcome identity exposed by the database read surface."""

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
    """One taker-side contract print returned by the database read surface."""

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


def _require_aware(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        msg = f"{field} must be timezone-aware"
        raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class PolymarketCorpusRequest:
    """Exact bounded selection policy for one resolved-contract research corpus."""

    environment_id: str
    as_of: datetime
    min_points: int
    max_markets: int
    outcome_index: int = 0
    fidelity: int = 60

    def __post_init__(self) -> None:
        """Reject an unbounded, temporally ambiguous, or invalid selection."""
        _require_aware(self.as_of, "as_of")
        if (
            not self.environment_id
            or self.min_points < _MIN_CORPUS_POINTS
            or self.max_markets <= 0
            or self.outcome_index < 0
            or self.fidelity <= 0
        ):
            msg = "Polymarket corpus selection must be explicit and positively bounded"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class PolymarketCorpusOutcome:
    """One exact outcome identity and settlement value in a corpus contract."""

    outcome_index: int
    label: str
    outcome_token: str
    payout: Decimal


@dataclass(frozen=True, slots=True)
class PolymarketCorpusContract:
    """One binary contract with server-issued event identity and lifecycle times."""

    market_id: str
    event_id: str
    market_type: str
    question: str
    open_time: datetime
    close_time: datetime
    outcomes: tuple[PolymarketCorpusOutcome, ...]

    def __post_init__(self) -> None:
        """Require complete binary identity without inferring missing groups or legs."""
        _require_aware(self.open_time, "open_time")
        _require_aware(self.close_time, "close_time")
        indexes = tuple(item.outcome_index for item in self.outcomes)
        tokens = tuple(item.outcome_token for item in self.outcomes)
        if (
            not self.market_id
            or not self.event_id
            or self.market_type != "binary"
            or not self.question
            or self.open_time >= self.close_time
            or indexes != (0, 1)
            or len(set(tokens)) != _BINARY_OUTCOME_COUNT
            or any(not token for token in tokens)
        ):
            msg = "Polymarket corpus contract requires complete binary event identity"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class PolymarketResolutionRecord:
    """One exact on-chain settlement fact and its recorded availability time."""

    market_id: str
    resolved_time: datetime
    payouts: tuple[Decimal, ...]
    oracle: str | None
    question_id: str | None
    transaction_hash: str | None

    def __post_init__(self) -> None:
        """Reject incomplete or non-probability settlement vectors."""
        _require_aware(self.resolved_time, "resolved_time")
        if (
            not self.market_id
            or len(self.payouts) != _BINARY_OUTCOME_COUNT
            or any(value < 0 or value > 1 for value in self.payouts)
            or sum(self.payouts) != Decimal(1)
        ):
            msg = "Polymarket resolution requires a complete binary payout vector"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class PolymarketPricePoint:
    """One historical sampled outcome-token price."""

    market_id: str
    outcome_index: int
    outcome_token: str
    observed_at: datetime
    price: Decimal
    fidelity: int

    def __post_init__(self) -> None:
        """Reject impossible prices and ambiguous observation identity."""
        _require_aware(self.observed_at, "observed_at")
        if (
            not self.market_id
            or not self.outcome_token
            or self.outcome_index < 0
            or self.price < 0
            or self.price > 1
            or self.fidelity <= 0
        ):
            msg = "Polymarket price point has invalid identity or value"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class PolymarketCorpus:
    """Exact in-memory result of one bounded production corpus read."""

    request: PolymarketCorpusRequest
    contracts: tuple[PolymarketCorpusContract, ...]
    resolutions: tuple[PolymarketResolutionRecord, ...]
    prices: tuple[PolymarketPricePoint, ...]

    def __post_init__(self) -> None:
        """Require exact one-to-one contract/resolution scope and sufficient prices."""
        contract_ids = tuple(item.market_id for item in self.contracts)
        resolution_ids = tuple(item.market_id for item in self.resolutions)
        if (
            not self.contracts
            or len(set(contract_ids)) != len(contract_ids)
            or resolution_ids != contract_ids
        ):
            msg = "Polymarket corpus contracts and resolutions must match exactly"
            raise ValueError(msg)
        contracts = {item.market_id: item for item in self.contracts}
        counts = dict.fromkeys(contract_ids, 0)
        last_key: tuple[str, datetime] | None = None
        for point in self.prices:
            contract = contracts.get(point.market_id)
            if contract is None:
                msg = "Polymarket corpus price belongs to an unknown contract"
                raise ValueError(msg)
            outcome = contract.outcomes[self.request.outcome_index]
            if (
                point.outcome_index != self.request.outcome_index
                or point.outcome_token != outcome.outcome_token
                or point.observed_at > self.request.as_of
                or point.observed_at > contract.close_time
            ):
                msg = "Polymarket corpus price violates requested outcome or time scope"
                raise ValueError(msg)
            key = (point.market_id, point.observed_at)
            if last_key is not None and key < last_key:
                msg = "Polymarket corpus prices must be ordered by contract and time"
                raise ValueError(msg)
            last_key = key
            counts[point.market_id] += 1
        if any(count < self.request.min_points for count in counts.values()):
            msg = "Polymarket corpus contract has insufficient price history"
            raise ValueError(msg)
        for contract, resolution in zip(self.contracts, self.resolutions, strict=True):
            if (
                resolution.resolved_time > self.request.as_of
                or resolution.resolved_time < contract.close_time
                or resolution.payouts != tuple(item.payout for item in contract.outcomes)
            ):
                msg = "Polymarket corpus resolution conflicts with contract lifecycle"
                raise ValueError(msg)
