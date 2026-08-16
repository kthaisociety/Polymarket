"""Construction of legal information sets at simulated decision times."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from research_agent.data_foundation._identity import require_aware, stable_identity

if TYPE_CHECKING:
    from datetime import datetime

    from research_agent.data_foundation.observations import (
        DataCatalogSnapshot,
        RegisteredObservation,
    )
    from research_agent.data_foundation.schema import FieldRef


class BoundaryStatus(Enum):
    """Whether a derived scientific boundary is usable downstream."""

    READY = "ready"
    INSUFFICIENT = "insufficient"


@dataclass(frozen=True, slots=True)
class InformationSet:
    """Exact observations knowable in a scoped environment at time ``t``."""

    information_set_id: str
    decision_time: datetime
    environment_id: str
    catalog_id: str
    requested_fields: tuple[FieldRef, ...]
    observations: tuple[RegisteredObservation, ...]
    status: BoundaryStatus
    exclusions: tuple[str, ...]

    def __post_init__(self) -> None:
        """Verify that immutable view identity matches its exact legal content."""
        require_aware(self.decision_time, "decision_time")
        expected = stable_identity("information-set", _information_set_payload(self))
        if self.information_set_id != expected:
            msg = "information-set identity does not match content"
            raise ValueError(msg)

    def for_field(self, field_ref: FieldRef) -> tuple[RegisteredObservation, ...]:
        """Return the legally visible observations for one exact field."""
        return tuple(item for item in self.observations if item.field_ref == field_ref)


class InformationSetBuilder:
    """Apply availability and as-known-at-time vintage semantics without learning."""

    def build(
        self,
        catalog: DataCatalogSnapshot,
        *,
        decision_time: datetime,
        requested_fields: tuple[FieldRef, ...],
    ) -> InformationSet:
        """Build the exact scoped view legally knowable at ``decision_time``."""
        require_aware(decision_time, "decision_time")
        if not requested_fields:
            msg = "an information set requires explicit field scope"
            raise ValueError(msg)
        for field_ref in requested_fields:
            catalog.resolve_schema(field_ref)

        requested = frozenset(requested_fields)
        legally_released = tuple(
            item
            for item in catalog.observations
            if item.field_ref in requested and item.available_at <= decision_time
        )
        latest_by_cell: dict[
            tuple[str, datetime, tuple[tuple[str, str], ...]],
            RegisteredObservation,
        ] = {}
        for item in legally_released:
            current = latest_by_cell.get(item.cell_identity)
            if current is None or item.revision_number > current.revision_number:
                latest_by_cell[item.cell_identity] = item
        observations = tuple(
            sorted(
                latest_by_cell.values(),
                key=lambda item: (
                    item.reference_time,
                    item.field_ref.identity,
                    item.dimensions,
                ),
            )
        )
        missing = tuple(
            field_ref.identity
            for field_ref in requested_fields
            if not any(item.field_ref == field_ref for item in observations)
        )
        exclusions = tuple(
            f"no legally available observation for {identity}" for identity in missing
        )
        status = BoundaryStatus.INSUFFICIENT if exclusions else BoundaryStatus.READY
        identity_payload = {
            "decision_time": decision_time,
            "environment_id": catalog.environment_id,
            "catalog_id": catalog.identity,
            "requested_fields": requested_fields,
            "observation_ids": tuple(item.observation_id for item in observations),
            "status": status,
            "exclusions": exclusions,
        }
        return InformationSet(
            information_set_id=stable_identity("information-set", identity_payload),
            decision_time=decision_time,
            environment_id=catalog.environment_id,
            catalog_id=catalog.identity,
            requested_fields=requested_fields,
            observations=observations,
            status=status,
            exclusions=exclusions,
        )


def _information_set_payload(information: InformationSet) -> dict[str, object]:
    return {
        "decision_time": information.decision_time,
        "environment_id": information.environment_id,
        "catalog_id": information.catalog_id,
        "requested_fields": information.requested_fields,
        "observation_ids": tuple(item.observation_id for item in information.observations),
        "status": information.status,
        "exclusions": information.exclusions,
    }
