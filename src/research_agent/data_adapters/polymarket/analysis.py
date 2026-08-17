"""Compose registered Polymarket observations with the generic exploration sandbox."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from research_agent.data_foundation import BoundaryStatus, InformationSetBuilder
from research_agent.exploration import (
    AnalysisHarness,
    AnalysisRequest,
    ArtifactStore,
    AuthorizedDataView,
    CapabilityPolicy,
    DataAccessRequest,
)

if TYPE_CHECKING:
    from datetime import datetime

    from research_agent.data_adapters.polymarket.ingestion import PolymarketIngestionResult
    from research_agent.data_foundation import InformationSet
    from research_agent.exploration import ResourceLimits, StructuredObservation
    from research_agent.exploration.sandbox import JsonValue

_VIEW_ID = "polymarket-development-view"
_IDENTITY_FIELDS = (
    "market_id",
    "outcome_index",
    "outcome_token",
    "fill_uid",
    "reference_time",
    "available_at",
    "reference_time_epoch_seconds",
    "available_at_epoch_seconds",
    "vintage_id",
    "availability_rule_version",
    "observation_ids",
    "source_refs",
    "provenance_refs",
    "caveats",
)


@dataclass(frozen=True, slots=True)
class PolymarketExploratoryAnalysis:
    """One provisional authored analysis over an exact legal live-tape view."""

    information_set: InformationSet
    view: AuthorizedDataView
    observation: StructuredObservation
    artifacts: ArtifactStore


@dataclass(frozen=True, slots=True)
class PolymarketAnalysisRequest:
    """Exact authored action and capability request for one legal tape view."""

    decision_time: datetime
    source: str
    requested_view_fields: tuple[str, ...]
    session_id: str
    action_id: str
    random_seed: int | None = None
    resource_limits: ResourceLimits | None = None


def analyze_registered_polymarket_tape(
    ingestion: PolymarketIngestionResult,
    request: PolymarketAnalysisRequest,
) -> PolymarketExploratoryAnalysis:
    """Run unchanged authored code over a time-legal view of one exact registration."""
    schema = ingestion.registered.schema
    information_set = InformationSetBuilder().build(
        ingestion.catalog,
        decision_time=request.decision_time,
        requested_fields=tuple(schema.field_ref(field.field_id) for field in schema.fields),
    )
    if information_set.status is not BoundaryStatus.READY:
        msg = "Polymarket exploratory view has no complete legal field scope at decision time"
        raise ValueError(msg)
    available_fields = frozenset(_IDENTITY_FIELDS) | frozenset(
        field.field_id for field in schema.fields
    )
    if (
        not request.requested_view_fields
        or len(set(request.requested_view_fields)) != len(request.requested_view_fields)
        or any(field_id not in available_fields for field_id in request.requested_view_fields)
    ):
        msg = "unknown Polymarket exploratory view field or duplicate/empty field request"
        raise ValueError(msg)
    all_columns = _wide_columns(information_set, tuple(field.field_id for field in schema.fields))
    view = AuthorizedDataView(
        view_id=_VIEW_ID,
        dataset_ref=ingestion.registered.registration_id,
        environment_ref=ingestion.catalog.identity,
        fields={field_id: all_columns[field_id] for field_id in request.requested_view_fields},
        protected=False,
    )
    artifacts = ArtifactStore()
    harness = AnalysisHarness(
        views={view.view_id: view},
        policy=CapabilityPolicy(
            session_id=request.session_id,
            environment_ref=ingestion.catalog.identity,
            allowed_fields_by_view={view.view_id: frozenset(request.requested_view_fields)},
        ),
        artifacts=artifacts,
        resource_limits=request.resource_limits,
    )
    observation = harness.run(
        AnalysisRequest(
            session_id=request.session_id,
            action_id=request.action_id,
            source=request.source,
            data_access=(DataAccessRequest(view.view_id, request.requested_view_fields),),
            random_seed=request.random_seed,
        )
    )
    return PolymarketExploratoryAnalysis(information_set, view, observation, artifacts)


def _wide_columns(
    information_set: InformationSet,
    scientific_field_ids: tuple[str, ...],
) -> dict[str, tuple[JsonValue, ...]]:
    grouped: dict[tuple[object, ...], dict[str, object]] = {}
    for observation in information_set.observations:
        dimensions = dict(observation.dimensions)
        key = (
            observation.reference_time,
            observation.available_at,
            observation.dimensions,
            observation.vintage_id,
            observation.availability_rule_version,
        )
        row = grouped.setdefault(
            key,
            {
                "market_id": dimensions["market_id"],
                "outcome_index": int(dimensions["outcome_index"]),
                "outcome_token": dimensions["outcome_token"],
                "fill_uid": dimensions["fill_uid"],
                "reference_time": observation.reference_time.isoformat(),
                "available_at": observation.available_at.isoformat(),
                "reference_time_epoch_seconds": observation.reference_time.timestamp(),
                "available_at_epoch_seconds": observation.available_at.timestamp(),
                "vintage_id": observation.vintage_id,
                "availability_rule_version": observation.availability_rule_version,
                "observation_ids": [],
                "source_refs": [],
                "provenance_refs": [],
                "caveats": [],
            },
        )
        if observation.field_ref.field_id in row:
            msg = "Polymarket exploratory view encountered a duplicate registered field row"
            raise ValueError(msg)
        row[observation.field_ref.field_id] = observation.value
        cast("list[str]", row["observation_ids"]).append(observation.observation_id)
        cast("list[str]", row["source_refs"]).append(observation.source_ref)
        cast("list[str]", row["provenance_refs"]).append(observation.provenance_ref)
        caveats = cast("list[str]", row["caveats"])
        caveats.extend(item for item in observation.caveats if item not in caveats)
    expected = frozenset(scientific_field_ids)
    ordered_rows = []
    for key in sorted(grouped):
        row = grouped[key]
        present = frozenset(field_id for field_id in scientific_field_ids if field_id in row)
        if present != expected:
            msg = "Polymarket exploratory view cannot silently pivot an incomplete registered fill"
            raise ValueError(msg)
        ordered_rows.append(row)
    columns: dict[str, tuple[JsonValue, ...]] = {}
    for field_id in (*_IDENTITY_FIELDS, *scientific_field_ids):
        columns[field_id] = tuple(cast("JsonValue", row[field_id]) for row in ordered_rows)
    return columns
