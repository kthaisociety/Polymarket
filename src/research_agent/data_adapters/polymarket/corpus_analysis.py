"""Compose a retained Polymarket corpus into development-only analysis capabilities."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from research_agent.exploration import (
    AnalysisHarness,
    AnalysisRequest,
    ArtifactStore,
    AuthorizedDataView,
    CapabilityPolicy,
    DataAccessRequest,
    ResourceLimits,
    StructuredObservation,
)

if TYPE_CHECKING:
    from datetime import datetime

    from research_agent.data_adapters.polymarket.corpus import PolymarketCorpusSnapshot
    from research_agent.data_adapters.polymarket.models import (
        PolymarketCorpus,
        PolymarketCorpusContract,
    )
    from research_agent.exploration.sandbox import JsonValue

_PRICE_VIEW = "polymarket-development-prices"
_OUTCOME_VIEW = "polymarket-development-outcomes"
_PRICE_FIELDS = (
    "market_id",
    "event_id",
    "event_chronological_ordinal",
    "observation_ordinal",
    "observed_at_epoch_seconds",
    "market_probability",
)
_OUTCOME_FIELDS = (
    "market_id",
    "event_id",
    "event_chronological_ordinal",
    "question",
    "outcome_label",
    "open_time_epoch_seconds",
    "close_time_epoch_seconds",
    "resolved_time_epoch_seconds",
    "resolution_payout",
    "price_point_count",
)
_MIN_DEVELOPMENT_EVENTS = 2


@dataclass(frozen=True, slots=True)
class PolymarketEventPartition:
    """Exact whole-event chronological development/protected partition."""

    partition_id: str
    snapshot_ref: str
    development_event_ids: tuple[str, ...]
    protected_event_count: int
    development_market_count: int
    protected_market_count: int


@dataclass(frozen=True, slots=True)
class PolymarketDevelopmentAnalysis:
    """A development-only sandbox composition over one exact corpus partition."""

    partition: PolymarketEventPartition
    price_view: AuthorizedDataView
    outcome_view: AuthorizedDataView
    harness: AnalysisHarness
    artifacts: ArtifactStore

    def run(self, *, source: str, session_id: str, action_id: str) -> StructuredObservation:
        """Execute authored source with access only to development-event columns."""
        return self.harness.run(
            AnalysisRequest(
                session_id=session_id,
                action_id=action_id,
                source=source,
                data_access=(
                    DataAccessRequest(self.price_view.view_id, _PRICE_FIELDS),
                    DataAccessRequest(self.outcome_view.view_id, _OUTCOME_FIELDS),
                ),
            )
        )


def build_polymarket_development_analysis(
    snapshot: PolymarketCorpusSnapshot,
    *,
    session_id: str,
    protected_numerator: int = 1,
    protected_denominator: int = 5,
    resource_limits: ResourceLimits | None = None,
) -> PolymarketDevelopmentAnalysis:
    """Hide the latest whole-event block and expose only earlier events to the sandbox."""
    if protected_numerator <= 0 or protected_denominator <= protected_numerator or not session_id:
        msg = "Polymarket event partition requires a non-empty session and proper fraction"
        raise ValueError(msg)
    corpus = snapshot.corpus
    ordered_events = _ordered_events(corpus)
    protected_count = (
        len(ordered_events) * protected_numerator + protected_denominator - 1
    ) // protected_denominator
    development_count = len(ordered_events) - protected_count
    if development_count < _MIN_DEVELOPMENT_EVENTS or protected_count < 1:
        msg = "Polymarket corpus has too few event groups for development and protection"
        raise ValueError(msg)
    development_events = ordered_events[:development_count]
    development_set = frozenset(development_events)
    development_contracts = tuple(
        contract for contract in corpus.contracts if contract.event_id in development_set
    )
    protected_market_count = len(corpus.contracts) - len(development_contracts)
    partition_id = _partition_identity(
        snapshot.ref.uri,
        ordered_events,
        protected_numerator,
        protected_denominator,
    )
    environment_ref = f"polymarket-development-environment:{partition_id}"
    price_ref = f"polymarket-development-prices:{partition_id}"
    outcome_ref = f"polymarket-development-outcomes:{partition_id}"
    contract_by_market = {item.market_id: item for item in development_contracts}
    event_ordinals = {event_id: ordinal for ordinal, event_id in enumerate(development_events)}
    price_columns, ordinals = _development_price_columns(
        corpus,
        contract_by_market,
        event_ordinals,
    )
    outcome_columns = _development_outcome_columns(
        corpus,
        development_contracts,
        ordinals,
        event_ordinals,
    )
    price_view = AuthorizedDataView(
        view_id=_PRICE_VIEW,
        dataset_ref=price_ref,
        environment_ref=environment_ref,
        fields={field: tuple(values) for field, values in price_columns.items()},
    )
    outcome_view = AuthorizedDataView(
        view_id=_OUTCOME_VIEW,
        dataset_ref=outcome_ref,
        environment_ref=environment_ref,
        fields={field: tuple(values) for field, values in outcome_columns.items()},
    )
    artifacts = ArtifactStore()
    harness = AnalysisHarness(
        views={price_view.view_id: price_view, outcome_view.view_id: outcome_view},
        policy=CapabilityPolicy(
            session_id=session_id,
            environment_ref=environment_ref,
            allowed_fields_by_view={
                price_view.view_id: frozenset(_PRICE_FIELDS),
                outcome_view.view_id: frozenset(_OUTCOME_FIELDS),
            },
        ),
        artifacts=artifacts,
        resource_limits=resource_limits
        or ResourceLimits(wall_time_seconds=10.0, max_inline_bytes=200_000),
    )
    partition = PolymarketEventPartition(
        partition_id=partition_id,
        snapshot_ref=snapshot.ref.uri,
        development_event_ids=development_events,
        protected_event_count=protected_count,
        development_market_count=len(development_contracts),
        protected_market_count=protected_market_count,
    )
    return PolymarketDevelopmentAnalysis(partition, price_view, outcome_view, harness, artifacts)


def _ordered_events(corpus: PolymarketCorpus) -> tuple[str, ...]:
    resolution_by_market = {item.market_id: item for item in corpus.resolutions}
    latest_by_event: dict[str, datetime] = {}
    for contract in corpus.contracts:
        resolved_time = resolution_by_market[contract.market_id].resolved_time
        current = latest_by_event.get(contract.event_id)
        if current is None or resolved_time > current:
            latest_by_event[contract.event_id] = resolved_time
    return tuple(
        event_id
        for event_id, _ in sorted(latest_by_event.items(), key=lambda item: (item[1], item[0]))
    )


def _development_price_columns(
    corpus: PolymarketCorpus,
    contract_by_market: dict[str, PolymarketCorpusContract],
    event_ordinals: dict[str, int],
) -> tuple[dict[str, list[JsonValue]], dict[str, int]]:
    columns: dict[str, list[JsonValue]] = {field: [] for field in _PRICE_FIELDS}
    ordinals: dict[str, int] = {}
    for point in corpus.prices:
        contract = contract_by_market.get(point.market_id)
        if contract is None:
            continue
        ordinal = ordinals.get(point.market_id, 0)
        ordinals[point.market_id] = ordinal + 1
        columns["market_id"].append(point.market_id)
        columns["event_id"].append(contract.event_id)
        columns["event_chronological_ordinal"].append(event_ordinals[contract.event_id])
        columns["observation_ordinal"].append(ordinal)
        columns["observed_at_epoch_seconds"].append(point.observed_at.timestamp())
        columns["market_probability"].append(float(point.price))
    return columns, ordinals


def _development_outcome_columns(
    corpus: PolymarketCorpus,
    contracts: tuple[PolymarketCorpusContract, ...],
    ordinals: dict[str, int],
    event_ordinals: dict[str, int],
) -> dict[str, list[JsonValue]]:
    columns: dict[str, list[JsonValue]] = {field: [] for field in _OUTCOME_FIELDS}
    resolution_by_market = {item.market_id: item for item in corpus.resolutions}
    for contract in contracts:
        resolution = resolution_by_market[contract.market_id]
        columns["market_id"].append(contract.market_id)
        columns["event_id"].append(contract.event_id)
        columns["event_chronological_ordinal"].append(event_ordinals[contract.event_id])
        columns["question"].append(contract.question)
        columns["outcome_label"].append(contract.outcomes[corpus.request.outcome_index].label)
        columns["open_time_epoch_seconds"].append(contract.open_time.timestamp())
        columns["close_time_epoch_seconds"].append(contract.close_time.timestamp())
        columns["resolved_time_epoch_seconds"].append(resolution.resolved_time.timestamp())
        columns["resolution_payout"].append(float(resolution.payouts[corpus.request.outcome_index]))
        columns["price_point_count"].append(ordinals[contract.market_id])
    return columns


def _partition_identity(
    snapshot_ref: str,
    ordered_events: tuple[str, ...],
    numerator: int,
    denominator: int,
) -> str:
    payload = json.dumps(
        {
            "denominator": denominator,
            "method": "whole-event-chronological-latest-resolution/v1",
            "numerator": numerator,
            "ordered_events": ordered_events,
            "snapshot_ref": snapshot_ref,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(payload).hexdigest()


__all__ = [
    "PolymarketDevelopmentAnalysis",
    "PolymarketEventPartition",
    "build_polymarket_development_analysis",
]
