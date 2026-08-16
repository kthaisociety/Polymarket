"""Registration of immutable, temporally explicit observations."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from typing import TYPE_CHECKING

from research_agent.data_foundation._identity import require_aware, stable_identity

if TYPE_CHECKING:
    from datetime import datetime

    from research_agent.data_foundation.schema import DatasetSchema, FieldRef

type Scalar = str | int | float | bool | None
type DimensionValues = tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class ObservationInput:
    """Declared row semantics supplied to registration."""

    field_ref: FieldRef
    value: Scalar
    reference_time: datetime
    available_at: datetime
    vintage_id: str
    revision_number: int
    source_ref: str
    provenance_ref: str
    availability_rule_version: str
    dimensions: DimensionValues
    caveats: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RegisteredObservation:
    """An immutable scientific observation with both time axes and lineage."""

    observation_id: str
    schema_id: str
    field_ref: FieldRef
    value: Scalar
    reference_time: datetime
    available_at: datetime
    vintage_id: str
    revision_number: int
    source_ref: str
    provenance_ref: str
    availability_rule_version: str
    dimensions: DimensionValues
    caveats: tuple[str, ...]

    def __post_init__(self) -> None:
        """Reject stale caller-supplied identity for changed scientific content."""
        require_aware(self.reference_time, "reference_time")
        require_aware(self.available_at, "available_at")
        expected = stable_identity("observation", _observation_payload(self.schema_id, self))
        if self.observation_id != expected:
            msg = "observation identity does not match content"
            raise ValueError(msg)

    @property
    def cell_identity(self) -> tuple[str, datetime, DimensionValues]:
        """Identify one semantic cell across immutable vintages."""
        return (self.field_ref.identity, self.reference_time, self.dimensions)


@dataclass(frozen=True, slots=True)
class RegisteredDataset:
    """Coherently registered observations for one exact schema."""

    registration_id: str
    schema: DatasetSchema
    observations: tuple[RegisteredObservation, ...]

    def __post_init__(self) -> None:
        """Verify content identity and an unambiguous revision history per cell."""
        schema_id = self.schema.identity
        for observation in self.observations:
            if observation.schema_id != schema_id:
                msg = "registered observation belongs to a different schema identity"
                raise ValueError(msg)
            self.schema.resolve_ref(observation.field_ref)
        identities = tuple(item.observation_id for item in self.observations)
        if len(set(identities)) != len(identities):
            msg = "registration contains duplicate observation identities"
            raise ValueError(msg)
        _validate_revision_histories(self.observations)
        expected = stable_identity(
            "registration",
            {"schema_id": schema_id, "observation_ids": identities},
        )
        if self.registration_id != expected:
            msg = "registration identity does not match content"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class DataCatalogSnapshot:
    """Immutable set of registrations visible in one environment snapshot."""

    environment_id: str
    datasets: tuple[RegisteredDataset, ...]

    def __post_init__(self) -> None:
        """Prevent registrations from crossing environment or schema identity."""
        if any(item.schema.environment_id != self.environment_id for item in self.datasets):
            msg = "catalog cannot mix environment identities"
            raise ValueError(msg)
        schema_keys = tuple((item.schema.dataset_id, item.schema.version) for item in self.datasets)
        if len(set(schema_keys)) != len(schema_keys):
            msg = "catalog contains duplicate dataset/schema registrations"
            raise ValueError(msg)

    @property
    def identity(self) -> str:
        """Return the stable catalog-snapshot identity."""
        return stable_identity(
            "catalog",
            {
                "environment_id": self.environment_id,
                "registration_ids": tuple(item.registration_id for item in self.datasets),
            },
        )

    @property
    def observations(self) -> tuple[RegisteredObservation, ...]:
        """Return all immutable observations in the snapshot."""
        return tuple(obs for dataset in self.datasets for obs in dataset.observations)

    def resolve_schema(self, field_ref: FieldRef) -> DatasetSchema:
        """Resolve an exact field reference to one registered schema."""
        if field_ref.environment_id != self.environment_id:
            msg = "field reference belongs to a different environment"
            raise KeyError(msg)
        matches = tuple(
            item.schema
            for item in self.datasets
            if item.schema.dataset_id == field_ref.dataset_id
            and item.schema.version == field_ref.schema_version
        )
        if len(matches) != 1:
            msg = "field reference does not resolve to one registered schema"
            raise KeyError(msg)
        matches[0].resolve_ref(field_ref)
        return matches[0]


class ObservationRegistrar:
    """Validate declared row semantics and publish an all-or-nothing registration."""

    def register(
        self,
        schema: DatasetSchema,
        rows: tuple[ObservationInput, ...],
    ) -> RegisteredDataset:
        """Register all rows coherently or raise without returning a partial result."""
        schema_id = schema.identity
        observations = tuple(self._register_one(schema, schema_id, row) for row in rows)
        identities = tuple(item.observation_id for item in observations)
        registration_id = stable_identity(
            "registration",
            {"schema_id": schema_id, "observation_ids": identities},
        )
        return RegisteredDataset(registration_id, schema, observations)

    @staticmethod
    def _register_one(
        schema: DatasetSchema,
        schema_id: str,
        row: ObservationInput,
    ) -> RegisteredObservation:
        field = schema.resolve_ref(row.field_ref)
        require_aware(row.reference_time, "reference_time")
        require_aware(row.available_at, "available_at")
        if row.revision_number < 0:
            msg = "revision_number cannot be negative"
            raise ValueError(msg)
        if not all(
            (row.vintage_id, row.source_ref, row.provenance_ref, row.availability_rule_version)
        ):
            msg = "vintage, source, provenance, and availability rule are required"
            raise ValueError(msg)
        dimension_names = tuple(name for name, _ in row.dimensions)
        if dimension_names != field.dimensions:
            msg = "observation dimensions must exactly match the field definition"
            raise ValueError(msg)
        payload = _observation_payload(schema_id, row)
        return RegisteredObservation(
            observation_id=stable_identity("observation", payload),
            schema_id=schema_id,
            field_ref=row.field_ref,
            value=row.value,
            reference_time=row.reference_time,
            available_at=row.available_at,
            vintage_id=row.vintage_id,
            revision_number=row.revision_number,
            source_ref=row.source_ref,
            provenance_ref=row.provenance_ref,
            availability_rule_version=row.availability_rule_version,
            dimensions=row.dimensions,
            caveats=row.caveats,
        )


def _observation_payload(
    schema_id: str,
    observation: ObservationInput | RegisteredObservation,
) -> dict[str, object]:
    return {
        "schema_id": schema_id,
        "field_ref": observation.field_ref,
        "value": observation.value,
        "reference_time": observation.reference_time,
        "available_at": observation.available_at,
        "vintage_id": observation.vintage_id,
        "revision_number": observation.revision_number,
        "source_ref": observation.source_ref,
        "provenance_ref": observation.provenance_ref,
        "availability_rule_version": observation.availability_rule_version,
        "dimensions": observation.dimensions,
        "caveats": observation.caveats,
    }


def _validate_revision_histories(observations: tuple[RegisteredObservation, ...]) -> None:
    by_cell: dict[
        tuple[str, datetime, DimensionValues],
        list[RegisteredObservation],
    ] = {}
    for observation in observations:
        by_cell.setdefault(observation.cell_identity, []).append(observation)
    for revisions in by_cell.values():
        revision_numbers = tuple(item.revision_number for item in revisions)
        vintage_ids = tuple(item.vintage_id for item in revisions)
        if len(set(revision_numbers)) != len(revision_numbers) or len(set(vintage_ids)) != len(
            vintage_ids
        ):
            msg = "ambiguous revision history for semantic cell"
            raise ValueError(msg)
        ordered = sorted(revisions, key=lambda item: item.revision_number)
        if any(newer.available_at <= older.available_at for older, newer in pairwise(ordered)):
            msg = "non-coherent revision history for semantic cell"
            raise ValueError(msg)
