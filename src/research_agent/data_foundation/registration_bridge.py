"""Authority boundary from verified derived JSON to registered temporal observations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from threading import RLock
from typing import TYPE_CHECKING, Never, cast

from research_agent.data_foundation._identity import require_aware, stable_identity
from research_agent.data_foundation.observations import (
    DataCatalogSnapshot,
    ObservationInput,
    ObservationRegistrar,
    RegisteredDataset,
)
from research_agent.data_foundation.schema import DatasetSchema, FieldDefinition

if TYPE_CHECKING:
    from research_agent.data_workspace import DataWorkspace, DerivedDatasetRef
    from research_agent.data_workspace.workspace import JsonValue

_ENVELOPE_VERSION = "temporal-observations/v1"
_SUPPORTED_TYPES = frozenset(
    {"bool", "boolean", "float", "int", "integer", "number", "str", "string"}
)


@dataclass(frozen=True, slots=True)
class TemporalDatasetProfile:
    """Trusted, source-neutral semantics required to interpret one temporal dataset."""

    dataset_id: str
    schema_version: str
    environment_id: str
    semantic_provenance_ref: str
    availability_rule_version: str
    fields: tuple[FieldDefinition, ...]
    mandatory_caveats: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Require complete semantics and a representation the bridge can validate exactly."""
        if not all(
            (
                self.dataset_id,
                self.schema_version,
                self.environment_id,
                self.semantic_provenance_ref,
                self.availability_rule_version,
            )
        ):
            msg = "temporal dataset profile requires exact identity and provenance"
            raise ValueError(msg)
        field_ids = tuple(field.field_id for field in self.fields)
        if not field_ids or len(set(field_ids)) != len(field_ids):
            msg = "temporal dataset profile requires unique fields"
            raise ValueError(msg)
        if any(field.data_type not in _SUPPORTED_TYPES for field in self.fields):
            msg = "temporal dataset profile contains an unsupported exact data type"
            raise ValueError(msg)
        if any(not caveat for caveat in self.mandatory_caveats):
            msg = "mandatory caveats cannot be empty"
            raise ValueError(msg)

    @property
    def identity(self) -> str:
        """Bind every semantic choice independently from physical data bytes."""
        return stable_identity("temporal-dataset-profile", self)

    @property
    def schema(self) -> DatasetSchema:
        """Construct the exact stable schema authorized by this profile."""
        return DatasetSchema(
            dataset_id=self.dataset_id,
            version=self.schema_version,
            environment_id=self.environment_id,
            provenance_ref=f"temporal-profile:{self.identity}",
            fields=self.fields,
        )


@dataclass(frozen=True, slots=True)
class ApprovedTemporalDataset:
    """Composition-owned approval of one exact retained object under one exact profile."""

    derived_ref: DerivedDatasetRef
    profile: TemporalDatasetProfile
    approval_ref: str

    def __post_init__(self) -> None:
        """Require an exact independent approval reference."""
        if not self.approval_ref:
            msg = "temporal dataset approval requires independent provenance"
            raise ValueError(msg)

    @property
    def identity(self) -> str:
        """Bind retained content, transformation lineage, semantics, and approval provenance."""
        return stable_identity("approved-temporal-dataset", self)


@dataclass(frozen=True, slots=True)
class RegisteredTemporalDataset:
    """Authority-issued attestation over one exact kernel registration."""

    attestation_id: str
    approval_id: str
    derived_ref_uri: str
    profile_id: str
    dataset: RegisteredDataset

    def __post_init__(self) -> None:
        """Reject an attestation detached from its exact registration content."""
        expected = stable_identity(
            "registered-temporal-dataset",
            {
                "approval_id": self.approval_id,
                "derived_ref_uri": self.derived_ref_uri,
                "profile_id": self.profile_id,
                "registration_id": self.dataset.registration_id,
            },
        )
        if self.attestation_id != expected:
            msg = "registered temporal dataset attestation does not match content"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class AuthoritativeDataCatalog:
    """Exact issued catalog plus the registrations that gave it scientific authority."""

    catalog_attestation_id: str
    registrations: tuple[RegisteredTemporalDataset, ...]
    snapshot: DataCatalogSnapshot

    def __post_init__(self) -> None:
        """Bind the snapshot exactly to its authority-issued registrations."""
        if not self.registrations:
            msg = "authoritative catalog requires at least one issued registration"
            raise ValueError(msg)
        if tuple(item.dataset for item in self.registrations) != self.snapshot.datasets:
            msg = "authoritative catalog registrations differ from its snapshot"
            raise ValueError(msg)
        expected = stable_identity(
            "authoritative-data-catalog",
            {
                "registration_attestation_ids": tuple(
                    item.attestation_id for item in self.registrations
                ),
                "snapshot_id": self.snapshot.identity,
            },
        )
        if self.catalog_attestation_id != expected:
            msg = "authoritative catalog attestation does not match content"
            raise ValueError(msg)


class TemporalRegistrationAuthority:
    """Non-copyable composition root for exact derived-to-scientific registrations."""

    def __init__(self, approvals: tuple[ApprovedTemporalDataset, ...]) -> None:
        """Configure the only exact dataset/profile approvals this authority may issue."""
        if not approvals:
            msg = "temporal registration authority requires configured approvals"
            raise ValueError(msg)
        identities = tuple(item.identity for item in approvals)
        if len(set(identities)) != len(identities):
            msg = "temporal registration approvals must be unique"
            raise ValueError(msg)
        self._approvals = dict(zip(identities, approvals, strict=True))
        self._registrations: dict[str, RegisteredTemporalDataset] = {}
        self._catalogs: dict[str, AuthoritativeDataCatalog] = {}
        self._lock = RLock()

    def __copy__(self) -> Never:
        """Prevent copied objects from sharing issuance authority."""
        msg = "temporal registration authority cannot be copied"
        raise TypeError(msg)

    def __deepcopy__(self, memo: dict[int, object]) -> Never:
        """Prevent copied objects from sharing issuance authority."""
        del memo
        msg = "temporal registration authority cannot be copied"
        raise TypeError(msg)

    def register(
        self,
        workspace: DataWorkspace,
        approval: ApprovedTemporalDataset,
    ) -> RegisteredTemporalDataset:
        """Resolve exact retained JSON and issue one all-or-nothing scientific registration."""
        with self._lock:
            if self._approvals.get(approval.identity) is not approval:
                msg = "temporal dataset was not approved by this configured authority"
                raise ValueError(msg)
        raw = workspace.read_derived_json(approval.derived_ref)
        dataset = _register_envelope(raw, approval)
        payload = {
            "approval_id": approval.identity,
            "derived_ref_uri": approval.derived_ref.uri,
            "profile_id": approval.profile.identity,
            "registration_id": dataset.registration_id,
        }
        registration = RegisteredTemporalDataset(
            attestation_id=stable_identity("registered-temporal-dataset", payload),
            approval_id=approval.identity,
            derived_ref_uri=approval.derived_ref.uri,
            profile_id=approval.profile.identity,
            dataset=dataset,
        )
        with self._lock:
            existing = self._registrations.get(registration.attestation_id)
            if existing is not None and existing is not registration:
                if existing != registration:
                    msg = "temporal registration attestation conflict"
                    raise ValueError(msg)
                return existing
            self._registrations[registration.attestation_id] = registration
        return registration

    def catalog(
        self,
        registrations: tuple[RegisteredTemporalDataset, ...],
    ) -> AuthoritativeDataCatalog:
        """Issue one catalog only from exact registrations issued by this authority."""
        if not registrations:
            msg = "catalog issuance requires registrations"
            raise ValueError(msg)
        with self._lock:
            if any(
                self._registrations.get(item.attestation_id) is not item for item in registrations
            ):
                msg = "catalog contains a registration not issued by this authority"
                raise ValueError(msg)
        environments = {item.dataset.schema.environment_id for item in registrations}
        if len(environments) != 1:
            msg = "authoritative catalog cannot mix environment identities"
            raise ValueError(msg)
        snapshot = DataCatalogSnapshot(
            environment_id=next(iter(environments)),
            datasets=tuple(item.dataset for item in registrations),
        )
        payload = {
            "registration_attestation_ids": tuple(item.attestation_id for item in registrations),
            "snapshot_id": snapshot.identity,
        }
        catalog = AuthoritativeDataCatalog(
            catalog_attestation_id=stable_identity("authoritative-data-catalog", payload),
            registrations=registrations,
            snapshot=snapshot,
        )
        with self._lock:
            existing = self._catalogs.get(catalog.catalog_attestation_id)
            if existing is not None:
                if existing != catalog:
                    msg = "authoritative catalog attestation conflict"
                    raise ValueError(msg)
                return existing
            self._catalogs[catalog.catalog_attestation_id] = catalog
        return catalog

    def require_catalog(self, catalog: AuthoritativeDataCatalog) -> None:
        """Reject equal-looking or rehashed catalogs that this authority did not issue."""
        with self._lock:
            if self._catalogs.get(catalog.catalog_attestation_id) is not catalog:
                msg = "catalog was not issued by the configured temporal authority"
                raise ValueError(msg)


def _register_envelope(raw: JsonValue, approval: ApprovedTemporalDataset) -> RegisteredDataset:
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "profile_id", "observations"}:
        msg = "temporal envelope must contain exact schema, profile, and observation keys"
        raise ValueError(msg)
    if raw["schema_version"] != _ENVELOPE_VERSION:
        msg = "temporal envelope schema version is unsupported"
        raise ValueError(msg)
    if raw["profile_id"] != approval.profile.identity:
        msg = "temporal envelope profile identity differs from the approved semantics"
        raise ValueError(msg)
    raw_observations = raw["observations"]
    if not isinstance(raw_observations, list) or not raw_observations:
        msg = "temporal envelope requires at least one observation"
        raise ValueError(msg)
    schema = approval.profile.schema
    rows = tuple(
        _observation_input(value, approval, schema, ordinal)
        for ordinal, value in enumerate(raw_observations)
    )
    return ObservationRegistrar().register(schema, rows)


def _observation_input(
    raw: JsonValue,
    approval: ApprovedTemporalDataset,
    schema: DatasetSchema,
    ordinal: int,
) -> ObservationInput:
    required = {
        "field_id",
        "value",
        "reference_time",
        "available_at",
        "vintage_id",
        "revision_number",
        "dimensions",
        "caveats",
    }
    if not isinstance(raw, dict) or set(raw) != required:
        msg = "temporal observation contains missing or unknown keys"
        raise ValueError(msg)
    field_id = raw["field_id"]
    if not isinstance(field_id, str):
        msg = "temporal observation field_id must be a string"
        raise ValueError(msg)  # noqa: TRY004 - malformed JSON is a value-boundary failure
    field = schema.resolve(field_id)
    value = raw["value"]
    _validate_value(value, field)
    reference_time = _parse_time(raw["reference_time"], "reference_time")
    available_at = _parse_time(raw["available_at"], "available_at")
    vintage_id = raw["vintage_id"]
    revision_number = raw["revision_number"]
    if not isinstance(vintage_id, str) or not vintage_id:
        msg = "temporal observation vintage_id must be explicit"
        raise ValueError(msg)
    if isinstance(revision_number, bool) or not isinstance(revision_number, int):
        msg = "temporal observation revision_number must be an integer"
        raise ValueError(msg)  # noqa: TRY004 - malformed JSON is a value-boundary failure
    dimensions = raw["dimensions"]
    if not isinstance(dimensions, dict) or set(dimensions) != set(field.dimensions):
        msg = "temporal observation dimensions differ from field semantics"
        raise ValueError(msg)
    dimension_values: list[tuple[str, str]] = []
    for name in field.dimensions:
        item = dimensions[name]
        if not isinstance(item, str) or not item:
            msg = "temporal observation dimension values must be non-empty strings"
            raise ValueError(msg)
        dimension_values.append((name, item))
    caveats = raw["caveats"]
    if not isinstance(caveats, list) or any(
        not isinstance(item, str) or not item for item in caveats
    ):
        msg = "temporal observation caveats must be explicit strings"
        raise ValueError(msg)
    provenance_ref = stable_identity(
        "derived-temporal-observation",
        {
            "approval_id": approval.identity,
            "derived_ref_uri": approval.derived_ref.uri,
            "ordinal": ordinal,
        },
    )
    return ObservationInput(
        field_ref=schema.field_ref(field_id),
        value=cast("str | int | float | bool | None", value),
        reference_time=reference_time,
        available_at=available_at,
        vintage_id=vintage_id,
        revision_number=revision_number,
        source_ref=approval.derived_ref.uri,
        provenance_ref=f"derived-row:{provenance_ref}",
        availability_rule_version=approval.profile.availability_rule_version,
        dimensions=tuple(dimension_values),
        caveats=(*approval.profile.mandatory_caveats, *cast("list[str]", caveats)),
    )


def _parse_time(raw: JsonValue, name: str) -> datetime:
    if not isinstance(raw, str):
        msg = f"temporal observation {name} must be an ISO-8601 string"
        raise ValueError(msg)  # noqa: TRY004 - malformed JSON is a value-boundary failure
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as error:
        msg = f"temporal observation {name} is invalid"
        raise ValueError(msg) from error
    require_aware(parsed, name)
    return parsed


def _validate_value(value: JsonValue, field: FieldDefinition) -> None:
    if value is None:
        return
    data_type = field.data_type
    if data_type in {"float", "number"}:
        valid = not isinstance(value, bool) and isinstance(value, (int, float))
        if valid and isinstance(value, float):
            valid = isfinite(value)
    elif data_type in {"int", "integer"}:
        valid = not isinstance(value, bool) and isinstance(value, int)
    elif data_type in {"str", "string"}:
        valid = isinstance(value, str)
    else:
        valid = isinstance(value, bool)
    if not valid:
        msg = f"temporal observation value does not match field type {data_type!r}"
        raise ValueError(msg)


__all__ = [
    "ApprovedTemporalDataset",
    "AuthoritativeDataCatalog",
    "RegisteredTemporalDataset",
    "TemporalDatasetProfile",
    "TemporalRegistrationAuthority",
]
