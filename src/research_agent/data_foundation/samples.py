"""Legal supervised-sample construction with independent temporal clocks."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from research_agent.data_foundation._identity import require_aware, stable_identity
from research_agent.data_foundation.information import (
    BoundaryStatus,
    InformationSetBuilder,
)
from research_agent.data_foundation.targets import (
    IncompleteOutcomePolicy,
    construct_label,
)

if TYPE_CHECKING:
    from datetime import datetime

    from research_agent.data_foundation.information import InformationSet
    from research_agent.data_foundation.observations import (
        DataCatalogSnapshot,
        DimensionValues,
        Scalar,
    )
    from research_agent.data_foundation.schema import FieldRef
    from research_agent.data_foundation.targets import TargetDefinition


class MissingnessPolicy(Enum):
    """Explicit non-learned handling of absent raw predictors."""

    EXCLUDE_EXAMPLE = "exclude_example"
    FAIL_SAMPLE = "fail_sample"


@dataclass(frozen=True, slots=True)
class SampleKey:
    """One exact decision-time population slice for a supervised example."""

    decision_time: datetime
    dimensions: DimensionValues = ()

    def __post_init__(self) -> None:
        """Canonicalize named dimensions and reject ambiguous population identity."""
        require_aware(self.decision_time, "candidate decision time")
        if any(not name or not value for name, value in self.dimensions):
            msg = "sample-key dimension names and values must be explicit"
            raise ValueError(msg)
        names = tuple(name for name, _ in self.dimensions)
        if len(set(names)) != len(names):
            msg = "sample-key dimensions must be unique"
            raise ValueError(msg)
        object.__setattr__(self, "dimensions", tuple(sorted(self.dimensions)))

    def slice_for(self, dimension_names: tuple[str, ...]) -> DimensionValues:
        """Return the exact named slice required by one field."""
        values = dict(self.dimensions)
        missing = tuple(name for name in dimension_names if name not in values)
        if missing:
            msg = f"sample key is missing dimensions {missing!r}"
            raise ValueError(msg)
        return tuple((name, values[name]) for name in dimension_names)


@dataclass(frozen=True, slots=True)
class PredictorValue:
    """One predictor value and its exact source observation."""

    field_ref: FieldRef
    value: Scalar
    observation_id: str


@dataclass(frozen=True, slots=True)
class TrainingRow:
    """One completed supervised example."""

    row_id: str
    decision_time: datetime
    dimensions: DimensionValues
    target_id: str
    predictors: tuple[PredictorValue, ...]
    label: Scalar
    label_matured_at: datetime
    label_observation_ids: tuple[str, ...]
    label_threshold: float | None

    def __post_init__(self) -> None:
        """Verify exact example identity rather than trusting a stale supplied ID."""
        expected = stable_identity("training-row", _training_row_payload(self))
        if self.row_id != expected:
            msg = "training-row identity does not match content"
            raise ValueError(msg)

    @property
    def sample_key(self) -> SampleKey:
        """Return the exact temporal and population identity of this row."""
        return SampleKey(self.decision_time, self.dimensions)


@dataclass(frozen=True, slots=True)
class TrainingSample:
    """Immutable completed legal examples available at one current time."""

    sample_id: str
    current_time: datetime
    target_id: str
    environment_id: str
    catalog_id: str
    predictor_fields: tuple[FieldRef, ...]
    rows: tuple[TrainingRow, ...]
    status: BoundaryStatus
    exclusions: tuple[str, ...]

    def __post_init__(self) -> None:
        """Verify sample identity and prevent repeated rows from inflating evidence."""
        require_aware(self.current_time, "current_time")
        row_ids = tuple(row.row_id for row in self.rows)
        if len(set(row_ids)) != len(row_ids):
            msg = "training sample contains duplicate row identities"
            raise ValueError(msg)
        if any(row.target_id != self.target_id for row in self.rows):
            msg = "training sample contains a row for a different target"
            raise ValueError(msg)
        if any(
            row.decision_time > self.current_time or row.label_matured_at > self.current_time
            for row in self.rows
        ):
            msg = "training sample contains a future decision or immature label"
            raise ValueError(msg)
        expected = stable_identity("training-sample", _training_sample_payload(self))
        if self.sample_id != expected:
            msg = "training-sample identity does not match content"
            raise ValueError(msg)


class TrainingSampleBuilder:
    """Reconstruct predictor legality per example and admit only mature labels."""

    def __init__(self, information_builder: InformationSetBuilder | None = None) -> None:
        """Use the supplied legality builder, or the kernel default."""
        self._information_builder = information_builder or InformationSetBuilder()

    def build(  # noqa: C901, PLR0912, PLR0913, PLR0915
        self,
        catalog: DataCatalogSnapshot,
        *,
        target: TargetDefinition,
        predictor_fields: tuple[FieldRef, ...],
        candidate_decision_times: tuple[datetime, ...] | None = None,
        candidate_sample_keys: tuple[SampleKey, ...] | None = None,
        current_time: datetime,
        missingness_policy: MissingnessPolicy,
    ) -> TrainingSample:
        """Build completed legal rows for the exact current time and target."""
        require_aware(current_time, "current_time")
        if target.environment_id != catalog.environment_id:
            msg = "target and catalog environment identities differ"
            raise ValueError(msg)
        if not predictor_fields:
            msg = "training sample requires explicit predictor fields"
            raise ValueError(msg)
        if (candidate_decision_times is None) == (candidate_sample_keys is None):
            msg = "provide exactly one candidate decision-time or sample-key sequence"
            raise ValueError(msg)
        sample_keys = (
            tuple(SampleKey(decision_time) for decision_time in candidate_decision_times)
            if candidate_decision_times is not None
            else candidate_sample_keys
        )
        if sample_keys is None:
            msg = "candidate sample keys were not supplied"
            raise AssertionError(msg)
        if len(set(sample_keys)) != len(sample_keys):
            msg = "candidate sample keys must be unique"
            raise ValueError(msg)
        catalog.resolve_schema(target.field_ref)
        target_information = self._information_builder.build(
            catalog,
            decision_time=current_time,
            requested_fields=(target.field_ref,),
        )
        target_observations = target_information.for_field(target.field_ref)
        rows: list[TrainingRow] = []
        exclusions: list[str] = []
        scope = tuple(dict.fromkeys((*predictor_fields, *target.state_field_refs)))
        all_fields = tuple(dict.fromkeys((*scope, target.field_ref)))
        dimensions_by_field = {
            field_ref: catalog.resolve_schema(field_ref).resolve_ref(field_ref).dimensions
            for field_ref in all_fields
        }
        required_dimension_names = frozenset(
            name for names in dimensions_by_field.values() for name in names
        )
        for sample_key in sample_keys:
            if frozenset(name for name, _ in sample_key.dimensions) != required_dimension_names:
                msg = "sample-key dimensions must exactly cover the scoped field dimensions"
                raise ValueError(msg)

        for sample_key in sample_keys:
            decision_time = sample_key.decision_time
            if decision_time > current_time:
                exclusions.append(f"{decision_time.isoformat()}: decision time is in the future")
                continue
            information = self._information_builder.build(
                catalog,
                decision_time=decision_time,
                requested_fields=scope,
            )
            predictors = self._predictors_at_decision(
                information,
                predictor_fields,
                sample_key,
                dimensions_by_field,
            )
            if predictors is None:
                message = f"{decision_time.isoformat()}: missing legal predictor"
                if missingness_policy is MissingnessPolicy.FAIL_SAMPLE:
                    return self._result(
                        catalog,
                        target,
                        predictor_fields=predictor_fields,
                        current_time=current_time,
                        rows=(),
                        exclusions=(*exclusions, message),
                    )
                exclusions.append(message)
                continue
            try:
                label = construct_label(
                    target,
                    decision_time=decision_time,
                    current_time=current_time,
                    target_observations=target_observations,
                    decision_information=information,
                    target_dimensions=sample_key.slice_for(dimensions_by_field[target.field_ref]),
                    state_dimensions=tuple(
                        (
                            field_ref,
                            sample_key.slice_for(dimensions_by_field[field_ref]),
                        )
                        for field_ref in target.state_field_refs
                    ),
                )
            except ValueError as error:
                message = f"{decision_time.isoformat()}: {error}"
                if target.incomplete_outcome_policy is IncompleteOutcomePolicy.FAIL:
                    return self._result(
                        catalog,
                        target,
                        predictor_fields=predictor_fields,
                        current_time=current_time,
                        rows=(),
                        exclusions=(*exclusions, message),
                    )
                exclusions.append(message)
                continue
            if label is None:
                message = f"{decision_time.isoformat()}: target is incomplete or immature"
                if target.incomplete_outcome_policy is IncompleteOutcomePolicy.FAIL:
                    return self._result(
                        catalog,
                        target,
                        predictor_fields=predictor_fields,
                        current_time=current_time,
                        rows=(),
                        exclusions=(*exclusions, message),
                    )
                exclusions.append(message)
                continue
            row_payload = {
                "decision_time": decision_time,
                "dimensions": sample_key.dimensions,
                "target_id": target.identity,
                "predictors": predictors,
                "label": label.value,
                "label_matured_at": label.matured_at,
                "label_observation_ids": label.observation_ids,
                "label_threshold": label.threshold,
            }
            rows.append(
                TrainingRow(
                    row_id=stable_identity("training-row", row_payload),
                    decision_time=decision_time,
                    dimensions=sample_key.dimensions,
                    target_id=target.identity,
                    predictors=predictors,
                    label=label.value,
                    label_matured_at=label.matured_at,
                    label_observation_ids=label.observation_ids,
                    label_threshold=label.threshold,
                )
            )
        return self._result(
            catalog,
            target,
            predictor_fields=predictor_fields,
            current_time=current_time,
            rows=tuple(rows),
            exclusions=tuple(exclusions),
        )

    @staticmethod
    def _predictors_at_decision(
        information: InformationSet,
        predictor_fields: tuple[FieldRef, ...],
        sample_key: SampleKey,
        dimensions_by_field: dict[FieldRef, tuple[str, ...]],
    ) -> tuple[PredictorValue, ...] | None:
        selected: list[PredictorValue] = []
        for field_ref in predictor_fields:
            observations = tuple(
                item
                for item in information.for_field(field_ref)
                if item.reference_time <= sample_key.decision_time
                and item.dimensions == sample_key.slice_for(dimensions_by_field[field_ref])
            )
            if not observations:
                return None
            latest = max(observations, key=lambda item: (item.reference_time, item.available_at))
            selected.append(PredictorValue(field_ref, latest.value, latest.observation_id))
        return tuple(selected)

    @staticmethod
    def _result(  # noqa: PLR0913
        catalog: DataCatalogSnapshot,
        target: TargetDefinition,
        *,
        predictor_fields: tuple[FieldRef, ...],
        current_time: datetime,
        rows: tuple[TrainingRow, ...],
        exclusions: tuple[str, ...],
    ) -> TrainingSample:
        status = BoundaryStatus.READY if rows else BoundaryStatus.INSUFFICIENT
        payload = {
            "current_time": current_time,
            "target_id": target.identity,
            "catalog_id": catalog.identity,
            "predictor_fields": predictor_fields,
            "row_ids": tuple(row.row_id for row in rows),
            "status": status,
            "exclusions": exclusions,
        }
        return TrainingSample(
            sample_id=stable_identity("training-sample", payload),
            current_time=current_time,
            target_id=target.identity,
            environment_id=catalog.environment_id,
            catalog_id=catalog.identity,
            predictor_fields=predictor_fields,
            rows=rows,
            status=status,
            exclusions=exclusions,
        )


def _training_row_payload(row: TrainingRow) -> dict[str, object]:
    return {
        "decision_time": row.decision_time,
        "dimensions": row.dimensions,
        "target_id": row.target_id,
        "predictors": row.predictors,
        "label": row.label,
        "label_matured_at": row.label_matured_at,
        "label_observation_ids": row.label_observation_ids,
        "label_threshold": row.label_threshold,
    }


def _training_sample_payload(sample: TrainingSample) -> dict[str, object]:
    return {
        "current_time": sample.current_time,
        "target_id": sample.target_id,
        "catalog_id": sample.catalog_id,
        "predictor_fields": sample.predictor_fields,
        "row_ids": tuple(row.row_id for row in sample.rows),
        "status": sample.status,
        "exclusions": sample.exclusions,
    }
