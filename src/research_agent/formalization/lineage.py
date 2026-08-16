"""Material-change lineage for immutable formal scientific objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from research_agent.data_foundation._identity import stable_identity


class VersionedDefinition(Protocol):
    """Minimum structural contract for formal material-change validation."""

    @property
    def version(self) -> int:
        """Return the immutable explicit version."""
        ...

    @property
    def identity(self) -> str:
        """Return the immutable scientific identity."""
        ...


@dataclass(frozen=True, slots=True)
class MaterialChange:
    """Append-only semantic diff link between immutable definition versions."""

    change_id: str
    object_kind: str
    parent_id: str
    child_id: str
    parent_version: int
    child_version: int
    reason: str
    provenance_refs: tuple[str, ...]


def record_material_change[DefinitionT: VersionedDefinition](
    parent: DefinitionT,
    child: DefinitionT,
    *,
    reason: str,
    provenance_refs: tuple[str, ...],
) -> MaterialChange:
    """Validate a material successor and return an immutable lineage record."""
    if type(parent) is not type(child):
        msg = "material-change lineage cannot cross formal object kinds"
        raise TypeError(msg)
    if child.version != parent.version + 1:
        msg = "material change must advance exactly one version"
        raise ValueError(msg)
    if child.identity == parent.identity:
        msg = "material change must produce a new scientific identity"
        raise ValueError(msg)
    expected_parent = getattr(child, "parent_definition_id", None)
    if expected_parent is None:
        expected_parent = getattr(child, "parent_feature_set_id", None)
    if expected_parent is None:
        expected_parent = getattr(child, "parent_system_id", None)
    if expected_parent != parent.identity:
        msg = "material successor does not name the exact parent identity"
        raise ValueError(msg)
    if not reason or not provenance_refs:
        msg = "material change requires reason and provenance"
        raise ValueError(msg)
    object_kind = type(parent).__name__
    payload = {
        "object_kind": object_kind,
        "parent_id": parent.identity,
        "child_id": child.identity,
        "parent_version": parent.version,
        "child_version": child.version,
        "reason": reason,
        "provenance_refs": provenance_refs,
    }
    return MaterialChange(
        change_id=stable_identity("material-change", payload),
        object_kind=object_kind,
        parent_id=parent.identity,
        child_id=child.identity,
        parent_version=parent.version,
        child_version=child.version,
        reason=reason,
        provenance_refs=provenance_refs,
    )
