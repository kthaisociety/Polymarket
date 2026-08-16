"""Stable semantic dataset schemas and exact field references."""

from __future__ import annotations

from dataclasses import dataclass

from research_agent.data_foundation._identity import stable_identity


@dataclass(frozen=True, slots=True)
class FieldDefinition:
    """Versioned semantic meaning of one dataset field."""

    field_id: str
    semantic_name: str
    data_type: str
    unit: str
    dimensions: tuple[str, ...]
    description: str

    def __post_init__(self) -> None:
        """Validate that semantic identity is complete and unambiguous."""
        required = (self.field_id, self.semantic_name, self.data_type, self.unit, self.description)
        if not all(required):
            msg = "field semantics must be explicit"
            raise ValueError(msg)
        if len(set(self.dimensions)) != len(self.dimensions):
            msg = "field dimensions must be unique"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class FieldRef:
    """Exact semantic reference; friendly names and paths are deliberately absent."""

    dataset_id: str
    schema_version: str
    field_id: str
    environment_id: str

    @property
    def identity(self) -> str:
        """Return the stable semantic field-reference identity."""
        return stable_identity("field", self)


@dataclass(frozen=True, slots=True)
class DatasetSchema:
    """Immutable semantic schema tied to the environment that registered it."""

    dataset_id: str
    version: str
    environment_id: str
    provenance_ref: str
    fields: tuple[FieldDefinition, ...]

    def __post_init__(self) -> None:
        """Validate schema identity and exact field uniqueness."""
        if not all((self.dataset_id, self.version, self.environment_id, self.provenance_ref)):
            msg = "schema identity and provenance must be explicit"
            raise ValueError(msg)
        field_ids = tuple(field.field_id for field in self.fields)
        if not field_ids or len(set(field_ids)) != len(field_ids):
            msg = "schema must contain uniquely identified fields"
            raise ValueError(msg)

    @property
    def identity(self) -> str:
        """Return the stable content identity for this exact schema."""
        return stable_identity("schema", self)

    def field_ref(self, field_id: str) -> FieldRef:
        """Create an exact reference after verifying the field exists."""
        self.resolve(field_id)
        return FieldRef(self.dataset_id, self.version, field_id, self.environment_id)

    def resolve(self, field_id: str) -> FieldDefinition:
        """Resolve one exact semantic field ID without similarity fallback."""
        matches = tuple(field for field in self.fields if field.field_id == field_id)
        if len(matches) != 1:
            msg = f"field {field_id!r} does not resolve exactly in schema {self.identity}"
            raise KeyError(msg)
        return matches[0]

    def resolve_ref(self, field_ref: FieldRef) -> FieldDefinition:
        """Resolve a reference only against its exact schema and environment."""
        expected = (self.dataset_id, self.version, self.environment_id)
        actual = (
            field_ref.dataset_id,
            field_ref.schema_version,
            field_ref.environment_id,
        )
        if actual != expected:
            msg = "field reference does not belong to this exact schema/environment"
            raise KeyError(msg)
        return self.resolve(field_ref.field_id)
