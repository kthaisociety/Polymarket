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
    from research_agent.data_foundation import RegisteredTemporalDataset
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
_TEMPORAL_RESERVED_FIELD_COUNT = 4


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
class PolymarketRegisteredEventField:
    """One authority-issued temporal field permitted into development exploration."""

    view_id: str
    registration: RegisteredTemporalDataset
    field_id: str

    def __post_init__(self) -> None:
        """Require an explicit non-colliding capability identity."""
        if not self.view_id or self.view_id in {_PRICE_VIEW, _OUTCOME_VIEW} or not self.field_id:
            msg = "registered event field requires an explicit unique view and field"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class PolymarketDevelopmentAnalysis:
    """A development-only sandbox composition over one exact corpus partition."""

    partition: PolymarketEventPartition
    price_view: AuthorizedDataView
    outcome_view: AuthorizedDataView
    registered_event_views: tuple[AuthorizedDataView, ...]
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
                    *(
                        DataAccessRequest(view.view_id, tuple(view.fields))
                        for view in self.registered_event_views
                    ),
                ),
            )
        )


def build_polymarket_development_analysis(  # noqa: PLR0913
    snapshot: PolymarketCorpusSnapshot,
    *,
    session_id: str,
    protected_numerator: int = 1,
    protected_denominator: int = 5,
    resource_limits: ResourceLimits | None = None,
    registered_event_fields: tuple[PolymarketRegisteredEventField, ...] = (),
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
    environment_ref = price_view.environment_ref
    registered_event_views = tuple(
        _registered_event_view(
            item,
            corpus_environment_id=corpus.request.environment_id,
            development_event_ordinals=event_ordinals,
            environment_ref=environment_ref,
        )
        for item in registered_event_fields
    )
    view_ids = (_PRICE_VIEW, _OUTCOME_VIEW, *(view.view_id for view in registered_event_views))
    if len(set(view_ids)) != len(view_ids):
        msg = "development analysis view identities must be unique"
        raise ValueError(msg)
    artifacts = ArtifactStore()
    views = {view.view_id: view for view in (price_view, outcome_view, *registered_event_views)}
    harness = AnalysisHarness(
        views=views,
        policy=CapabilityPolicy(
            session_id=session_id,
            environment_ref=environment_ref,
            allowed_fields_by_view={
                view.view_id: frozenset(view.fields) for view in views.values()
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
    return PolymarketDevelopmentAnalysis(
        partition,
        price_view,
        outcome_view,
        registered_event_views,
        harness,
        artifacts,
    )


def _registered_event_view(
    requested: PolymarketRegisteredEventField,
    *,
    corpus_environment_id: str,
    development_event_ordinals: dict[str, int],
    environment_ref: str,
) -> AuthorizedDataView:
    registration = requested.registration
    dataset = registration.dataset
    if dataset.schema.environment_id != corpus_environment_id:
        msg = "registered event field belongs to a different corpus environment"
        raise ValueError(msg)
    field = dataset.schema.resolve(requested.field_id)
    if "event_id" not in field.dimensions:
        msg = "registered development field requires an exact event_id dimension"
        raise ValueError(msg)
    reserved = {
        requested.field_id,
        "event_chronological_ordinal",
        "reference_time_epoch_seconds",
        "available_at_epoch_seconds",
    }
    if len(reserved) != _TEMPORAL_RESERVED_FIELD_COUNT or any(
        dimension in reserved - {requested.field_id} for dimension in field.dimensions
    ):
        msg = "registered development dimensions collide with temporal view fields"
        raise ValueError(msg)
    observations = tuple(
        item for item in dataset.observations if item.field_ref.field_id == requested.field_id
    )
    if not observations:
        msg = "registered development field has no observations"
        raise ValueError(msg)
    columns: dict[str, list[JsonValue]] = {dimension: [] for dimension in field.dimensions}
    columns["event_chronological_ordinal"] = []
    columns["reference_time_epoch_seconds"] = []
    columns["available_at_epoch_seconds"] = []
    columns[requested.field_id] = []
    for observation in observations:
        dimensions = dict(observation.dimensions)
        event_id = dimensions["event_id"]
        if event_id not in development_event_ordinals:
            msg = "registered event field contains unknown or protected event observations"
            raise ValueError(msg)
        for dimension in field.dimensions:
            columns[dimension].append(dimensions[dimension])
        columns["event_chronological_ordinal"].append(development_event_ordinals[event_id])
        columns["reference_time_epoch_seconds"].append(observation.reference_time.timestamp())
        columns["available_at_epoch_seconds"].append(observation.available_at.timestamp())
        columns[requested.field_id].append(observation.value)
    return AuthorizedDataView(
        view_id=requested.view_id,
        dataset_ref=registration.attestation_id,
        environment_ref=environment_ref,
        fields={name: tuple(values) for name, values in columns.items()},
    )


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
    "PolymarketRegisteredEventField",
    "build_polymarket_development_analysis",
]
