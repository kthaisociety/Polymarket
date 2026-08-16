"""Exact legal information views consumed by one controlled training window."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import TYPE_CHECKING, Never

from research_agent.data_foundation._identity import stable_identity
from research_agent.data_foundation.information import BoundaryStatus, InformationSetBuilder

if TYPE_CHECKING:
    from research_agent.data_foundation.information import InformationSet
    from research_agent.data_foundation.observations import DataCatalogSnapshot, DimensionValues
    from research_agent.data_foundation.samples import TrainingSample
    from research_agent.data_foundation.schema import FieldRef
    from research_agent.data_foundation.windows import TrainingWindow


@dataclass(frozen=True, slots=True)
class TrainingInformationEntry:
    """One training row bound to its exact historical legal information view."""

    row_id: str
    dimensions: DimensionValues
    information: InformationSet


@dataclass(frozen=True, slots=True)
class TrainingInformationBundle:
    """Immutable row-to-InformationSet authority for one exact fitting window."""

    bundle_id: str
    catalog_id: str
    environment_id: str
    training_sample_id: str
    training_window_id: str
    requested_fields: tuple[FieldRef, ...]
    entries: tuple[TrainingInformationEntry, ...]

    def __post_init__(self) -> None:
        """Reject reordered, cross-catalog, or stale bundle identity."""
        if not self.requested_fields or len(set(self.requested_fields)) != len(
            self.requested_fields
        ):
            msg = "training information requires unique exact field scope"
            raise ValueError(msg)
        if not self.entries:
            msg = "training information requires at least one legal row view"
            raise ValueError(msg)
        row_ids = tuple(entry.row_id for entry in self.entries)
        information_ids = tuple(entry.information.information_set_id for entry in self.entries)
        decision_times = tuple(entry.information.decision_time for entry in self.entries)
        if len(set(row_ids)) != len(row_ids) or len(set(information_ids)) != len(information_ids):
            msg = "training information requires unique row and information identities"
            raise ValueError(msg)
        if decision_times != tuple(sorted(decision_times)) or len(set(decision_times)) != len(
            decision_times
        ):
            msg = "training information requires unique increasing decision times"
            raise ValueError(msg)
        if any(
            entry.information.catalog_id != self.catalog_id
            or entry.information.environment_id != self.environment_id
            or entry.information.requested_fields != self.requested_fields
            or entry.information.status is not BoundaryStatus.READY
            for entry in self.entries
        ):
            msg = "training information entries cross exact catalog, environment, or field scope"
            raise ValueError(msg)
        expected = stable_identity("training-information-bundle", _bundle_payload(self))
        if self.bundle_id != expected:
            msg = "training-information bundle identity does not match content"
            raise ValueError(msg)

    @property
    def information_sets(self) -> tuple[InformationSet, ...]:
        """Return legal views in exact training-row order."""
        return tuple(entry.information for entry in self.entries)

    @property
    def row_ids(self) -> tuple[str, ...]:
        """Return exact training-row order."""
        return tuple(entry.row_id for entry in self.entries)


class TrainingInformationRegistry:
    """In-process issuance authority for exact reconstructed training information."""

    def __init__(self) -> None:
        """Start with no bundle authorized for formal fitting."""
        self._issued: dict[str, TrainingInformationBundle] = {}
        self._lock = RLock()

    def __copy__(self) -> Never:
        """Prevent shallow copies from sharing scientific issuance authority."""
        msg = "training-information issuance authority cannot be copied"
        raise TypeError(msg)

    def __deepcopy__(self, memo: dict[int, object]) -> Never:
        """Prevent deep copies from manufacturing a substitute authority."""
        del memo
        msg = "training-information issuance authority cannot be copied"
        raise TypeError(msg)

    def _issue(self, bundle: TrainingInformationBundle) -> TrainingInformationBundle:
        with self._lock:
            existing = self._issued.get(bundle.bundle_id)
            if existing is not None:
                if existing != bundle:
                    msg = "training-information identity already has changed content"
                    raise ValueError(msg)
                return existing
            self._issued[bundle.bundle_id] = bundle
            return bundle

    def require_issued(self, bundle: TrainingInformationBundle) -> None:
        """Require the exact object issued by this configured authority."""
        with self._lock:
            if self._issued.get(bundle.bundle_id) is not bundle:
                msg = "training information was not issued by the configured authority"
                raise ValueError(msg)


class TrainingInformationBuilder:
    """Reconstruct and verify legal historical views for an issued sample/window."""

    def __init__(self, registry: TrainingInformationRegistry | None = None) -> None:
        """Bind reconstruction to one explicit issuance authority."""
        self.registry = registry if registry is not None else TrainingInformationRegistry()

    def build(  # noqa: C901, PLR0912
        self,
        catalog: DataCatalogSnapshot,
        sample: TrainingSample,
        window: TrainingWindow,
        *,
        requested_fields: tuple[FieldRef, ...],
    ) -> TrainingInformationBundle:
        """Bind every selected row to the exact ``I_t`` used for feature materialization."""
        if sample.catalog_id != catalog.identity:
            msg = "training sample does not belong to the supplied catalog"
            raise ValueError(msg)
        if window.sample_id != sample.sample_id:
            msg = "training window does not belong to the supplied sample"
            raise ValueError(msg)
        sample_rows = {row.row_id: row for row in sample.rows}
        if any(sample_rows.get(row.row_id) != row for row in window.rows):
            msg = "training window contains a row outside the exact sample"
            raise ValueError(msg)
        if not requested_fields or len(set(requested_fields)) != len(requested_fields):
            msg = "training information requires unique exact field scope"
            raise ValueError(msg)
        if requested_fields != sample.predictor_fields:
            msg = "training information field scope differs from the exact sample predictors"
            raise ValueError(msg)
        for field_ref in requested_fields:
            catalog.resolve_schema(field_ref)

        observations = {item.observation_id: item for item in catalog.observations}
        entries: list[TrainingInformationEntry] = []
        for row in window.rows:
            information = InformationSetBuilder().build(
                catalog,
                decision_time=row.decision_time,
                requested_fields=requested_fields,
            )
            if information.status is not BoundaryStatus.READY:
                msg = "training row lacks a READY legal historical InformationSet"
                raise ValueError(msg)
            visible = {
                item.observation_id: item
                for item in information.observations
                if item.dimensions == row.dimensions
            }
            predictor_fields = tuple(item.field_ref for item in row.predictors)
            if predictor_fields != requested_fields:
                msg = "training row does not inventory the exact ordered feature dependencies"
                raise ValueError(msg)
            for predictor in row.predictors:
                observation = visible.get(predictor.observation_id)
                if observation is None or observation.value != predictor.value:
                    msg = "training-row predictor is not present in its exact legal InformationSet"
                    raise ValueError(msg)
            label_lineage = tuple(
                observations.get(label_id) for label_id in row.label_observation_ids
            )
            if any(item is None for item in label_lineage):
                msg = "training-row label lineage does not resolve in the supplied catalog"
                raise ValueError(msg)
            if any(
                item is not None
                and (item.available_at > sample.current_time or item.dimensions != row.dimensions)
                for item in label_lineage
            ):
                msg = "training-row label lineage was not legally mature in its dimension slice"
                raise ValueError(msg)
            entries.append(TrainingInformationEntry(row.row_id, row.dimensions, information))

        entry_tuple = tuple(entries)
        payload = {
            "catalog_id": catalog.identity,
            "environment_id": catalog.environment_id,
            "training_sample_id": sample.sample_id,
            "training_window_id": window.window_id,
            "requested_fields": requested_fields,
            "entries": tuple(
                {
                    "row_id": entry.row_id,
                    "dimensions": entry.dimensions,
                    "information_set_id": entry.information.information_set_id,
                }
                for entry in entry_tuple
            ),
        }
        bundle = TrainingInformationBundle(
            bundle_id=stable_identity("training-information-bundle", payload),
            catalog_id=catalog.identity,
            environment_id=catalog.environment_id,
            training_sample_id=sample.sample_id,
            training_window_id=window.window_id,
            requested_fields=requested_fields,
            entries=entry_tuple,
        )
        return self.registry._issue(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
            bundle
        )


def _bundle_payload(bundle: TrainingInformationBundle) -> dict[str, object]:
    return {
        "catalog_id": bundle.catalog_id,
        "environment_id": bundle.environment_id,
        "training_sample_id": bundle.training_sample_id,
        "training_window_id": bundle.training_window_id,
        "requested_fields": bundle.requested_fields,
        "entries": tuple(
            {
                "row_id": entry.row_id,
                "dimensions": entry.dimensions,
                "information_set_id": entry.information.information_set_id,
            }
            for entry in bundle.entries
        ),
    }


__all__ = [
    "TrainingInformationBuilder",
    "TrainingInformationBundle",
    "TrainingInformationEntry",
    "TrainingInformationRegistry",
]
