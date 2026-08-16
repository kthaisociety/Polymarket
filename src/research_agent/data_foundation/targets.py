"""Immutable, domain-neutral target semantics and causal label construction."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from statistics import fmean
from typing import TYPE_CHECKING

from research_agent.data_foundation._identity import stable_identity

if TYPE_CHECKING:
    from datetime import datetime

    from research_agent.data_foundation.information import InformationSet
    from research_agent.data_foundation.observations import (
        DimensionValues,
        RegisteredObservation,
        Scalar,
    )
    from research_agent.data_foundation.schema import FieldRef
    from research_agent.data_foundation.temporal import TemporalOffset
    from research_agent.task_compilation import ResearchTask


class TargetKind(Enum):
    """Declared relationship between an outcome interval and a label."""

    ENDPOINT = "endpoint"
    PATH = "path"
    EVENT = "event"


class OutcomeAlignment(Enum):
    """Explicit timestamp alignment for outcome observations."""

    EXACT = "exact"
    LATEST_AT_OR_BEFORE = "latest_at_or_before"


class PathReduction(Enum):
    """Non-learned reduction for a path-dependent target."""

    MAXIMUM = "maximum"
    MINIMUM = "minimum"
    SUM = "sum"
    MEAN = "mean"


class Comparison(Enum):
    """Declared event comparison."""

    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"


class StateAggregation(Enum):
    """Causal trailing aggregation used by a state-conditioned event rule."""

    LAST = "last"
    MEAN = "mean"
    MAXIMUM = "maximum"
    MINIMUM = "minimum"


class MaturityPolicy(Enum):
    """When a label becomes complete, before publication delay is added."""

    FULL_INTERVAL = "full_interval"
    EVENT_OR_INTERVAL_END = "event_or_interval_end"


class IncompleteOutcomePolicy(Enum):
    """Declared response to an incomplete outcome interval."""

    EXCLUDE = "exclude"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class StateConditionedThreshold:
    """A threshold computed only from a trailing legal information set."""

    field_ref: FieldRef
    lookback: TemporalOffset
    as_of_offset: TemporalOffset
    aggregation: StateAggregation
    multiplier: float
    additive: float

    def __post_init__(self) -> None:
        """Reject non-causal or undefined state windows."""
        if not self.lookback.is_positive:
            msg = "state-conditioned lookback must be positive"
            raise ValueError(msg)
        if self.as_of_offset.is_positive:
            msg = "state-conditioned target rules cannot inspect after decision time"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class EventCondition:
    """Fixed or causal state-conditioned event definition."""

    comparison: Comparison
    fixed_threshold: float | None
    state_threshold: StateConditionedThreshold | None

    def __post_init__(self) -> None:
        """Require exactly one explicit threshold source."""
        if (self.fixed_threshold is None) == (self.state_threshold is None):
            msg = "event condition requires exactly one threshold source"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class TargetDefinition:
    """Complete immutable identity of how a future interval becomes a label."""

    task_id: str
    task_version: int
    task_semantic_digest: str
    confirmed_task_horizon_id: str
    version: int
    parent_target_id: str | None
    field_ref: FieldRef
    kind: TargetKind
    horizon: TemporalOffset
    outcome_start_offset: TemporalOffset
    outcome_end_offset: TemporalOffset
    alignment: OutcomeAlignment
    path_reduction: PathReduction | None
    event_condition: EventCondition | None
    maturity_delay: TemporalOffset
    maturity_policy: MaturityPolicy
    required_observation_count: int
    value_encoding: str
    units: str
    censoring_policy: str
    incomplete_outcome_policy: IncompleteOutcomePolicy
    environment_id: str
    schema_provenance_ref: str
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:  # noqa: C901, PLR0912
        """Validate complete and internally consistent target semantics."""
        if not all(
            (
                self.task_id,
                self.task_semantic_digest,
                self.confirmed_task_horizon_id,
                self.value_encoding,
                self.units,
                self.censoring_policy,
                self.environment_id,
                self.schema_provenance_ref,
            )
        ):
            msg = "target scientific meaning and provenance must be explicit"
            raise ValueError(msg)
        if self.task_version < 1 or self.version < 1 or not self.horizon.is_positive:
            msg = "target version and horizon must be positive"
            raise ValueError(msg)
        if self.outcome_start_offset.is_negative:
            msg = "target outcome interval is invalid"
            raise ValueError(msg)
        if self.outcome_end_offset != self.horizon:
            msg = "horizon and outcome interval end must agree explicitly"
            raise ValueError(msg)
        if self.confirmed_task_horizon_id != self.horizon.identity:
            msg = "target horizon does not match the exact confirmed task horizon"
            raise ValueError(msg)
        if self.maturity_delay.is_negative or self.required_observation_count < 1:
            msg = "target maturity delay/count is invalid"
            raise ValueError(msg)
        if self.environment_id != self.field_ref.environment_id:
            msg = "target and field environment identities differ"
            raise ValueError(msg)
        if self.kind is TargetKind.ENDPOINT:
            if self.path_reduction is not None or self.event_condition is not None:
                msg = "endpoint targets cannot contain path/event rules"
                raise ValueError(msg)
        elif self.kind is TargetKind.PATH:
            if self.path_reduction is None or self.event_condition is not None:
                msg = "path targets require only a path reduction"
                raise ValueError(msg)
        elif self.event_condition is None or self.path_reduction is not None:
            msg = "event targets require only an event condition"
            raise ValueError(msg)
        if (
            self.maturity_policy is MaturityPolicy.EVENT_OR_INTERVAL_END
            and self.kind is not TargetKind.EVENT
        ):
            msg = "early event maturity is valid only for event targets"
            raise ValueError(msg)

    @property
    def identity(self) -> str:
        """Return the stable identity including outcome and maturity semantics."""
        return stable_identity("target", self)

    @classmethod
    def from_confirmed_task(  # noqa: PLR0913
        cls,
        task: ResearchTask,
        *,
        field_ref: FieldRef,
        version: int,
        parent_target_id: str | None,
        kind: TargetKind,
        outcome_start_offset: TemporalOffset,
        alignment: OutcomeAlignment,
        path_reduction: PathReduction | None,
        event_condition: EventCondition | None,
        maturity_delay: TemporalOffset,
        maturity_policy: MaturityPolicy,
        required_observation_count: int,
        value_encoding: str,
        units: str,
        censoring_policy: str,
        incomplete_outcome_policy: IncompleteOutcomePolicy,
        schema_provenance_ref: str,
        provenance_refs: tuple[str, ...],
    ) -> TargetDefinition:
        """Publish target semantics bound to the exact human-confirmed task horizon."""
        horizon = task.forecast_horizon
        if horizon is None:
            msg = "confirmed task has an unresolved horizon"
            raise ValueError(msg)
        if task.target_field_id is not None and task.target_field_id != field_ref.field_id:
            msg = "confirmed task and target field identities differ"
            raise ValueError(msg)
        return cls(
            task_id=task.task_id,
            task_version=task.version,
            task_semantic_digest=task.semantic_digest,
            confirmed_task_horizon_id=horizon.identity,
            version=version,
            parent_target_id=parent_target_id,
            field_ref=field_ref,
            kind=kind,
            horizon=horizon,
            outcome_start_offset=outcome_start_offset,
            outcome_end_offset=horizon,
            alignment=alignment,
            path_reduction=path_reduction,
            event_condition=event_condition,
            maturity_delay=maturity_delay,
            maturity_policy=maturity_policy,
            required_observation_count=required_observation_count,
            value_encoding=value_encoding,
            units=units,
            censoring_policy=censoring_policy,
            incomplete_outcome_policy=incomplete_outcome_policy,
            environment_id=field_ref.environment_id,
            schema_provenance_ref=schema_provenance_ref,
            provenance_refs=provenance_refs,
        )

    @property
    def state_field_refs(self) -> tuple[FieldRef, ...]:
        """Return any decision-time fields required by the target rule."""
        condition = self.event_condition
        if condition is None or condition.state_threshold is None:
            return ()
        return (condition.state_threshold.field_ref,)

    def interval(self, decision_time: datetime) -> tuple[datetime, datetime]:
        """Return the declared outcome interval for one decision."""
        start = self.outcome_start_offset.apply(decision_time)
        end = self.outcome_end_offset.apply(decision_time)
        if start > end:
            msg = "target outcome interval is invalid at this decision-time anchor"
            raise ValueError(msg)
        return start, end


@dataclass(frozen=True, slots=True)
class ConstructedLabel:
    """One label plus exact maturity and source lineage."""

    value: Scalar
    matured_at: datetime
    observation_ids: tuple[str, ...]
    threshold: float | None


def construct_label(  # noqa: PLR0913
    definition: TargetDefinition,
    *,
    decision_time: datetime,
    current_time: datetime,
    target_observations: tuple[RegisteredObservation, ...],
    decision_information: InformationSet,
    target_dimensions: DimensionValues = (),
    state_dimensions: tuple[tuple[FieldRef, DimensionValues], ...] = (),
) -> ConstructedLabel | None:
    """Construct a label without exposing target-rule state to post-decision information."""
    interval_start, interval_end = definition.interval(decision_time)
    relevant = tuple(
        sorted(
            (
                item
                for item in target_observations
                if interval_start < item.reference_time <= interval_end
                and item.available_at <= current_time
                and item.dimensions == target_dimensions
            ),
            key=lambda item: item.reference_time,
        )
    )
    if definition.kind is TargetKind.ENDPOINT:
        relevant = _endpoint_observations(definition, relevant, interval_end)

    event_index: int | None = None
    threshold: float | None = None
    if definition.kind is TargetKind.EVENT:
        threshold = _event_threshold(
            definition,
            decision_time,
            decision_information,
            state_dimensions,
        )
        event_index = _first_event_index(definition, relevant, threshold)

    maturity_base = interval_end
    if (
        definition.maturity_policy is MaturityPolicy.EVENT_OR_INTERVAL_END
        and event_index is not None
    ):
        maturity_base = relevant[event_index].reference_time
        relevant = relevant[: event_index + 1]
    matured_at = definition.maturity_delay.apply(maturity_base)
    if current_time < matured_at:
        return None

    minimum_count = definition.required_observation_count
    if (
        event_index is not None
        and definition.maturity_policy is MaturityPolicy.EVENT_OR_INTERVAL_END
    ):
        minimum_count = 1
    if len(relevant) < minimum_count:
        return None

    values = tuple(_numeric(item.value) for item in relevant)
    if definition.kind is TargetKind.ENDPOINT:
        label: Scalar = relevant[-1].value
    elif definition.kind is TargetKind.PATH:
        label = _reduce_path(definition.path_reduction, values)
    else:
        label = event_index is not None
    return ConstructedLabel(
        value=label,
        matured_at=max(matured_at, *(item.available_at for item in relevant)),
        observation_ids=tuple(item.observation_id for item in relevant),
        threshold=threshold,
    )


def _endpoint_observations(
    definition: TargetDefinition,
    observations: tuple[RegisteredObservation, ...],
    interval_end: datetime,
) -> tuple[RegisteredObservation, ...]:
    if definition.alignment is OutcomeAlignment.EXACT:
        return tuple(item for item in observations if item.reference_time == interval_end)
    return observations[-1:] if observations else ()


def _event_threshold(
    definition: TargetDefinition,
    decision_time: datetime,
    information: InformationSet,
    state_dimensions: tuple[tuple[FieldRef, DimensionValues], ...],
) -> float:
    condition = definition.event_condition
    if condition is None:
        msg = "event target lost its condition"
        raise AssertionError(msg)
    if condition.fixed_threshold is not None:
        return condition.fixed_threshold
    rule = condition.state_threshold
    if rule is None:
        msg = "event target lost its threshold source"
        raise AssertionError(msg)
    end = rule.as_of_offset.apply(decision_time)
    start = rule.lookback.negated().apply(end)
    dimension_lookup = dict(state_dimensions)
    if rule.field_ref not in dimension_lookup:
        msg = "state-conditioned target rule is missing a population slice"
        raise ValueError(msg)
    observations = tuple(
        item
        for item in information.for_field(rule.field_ref)
        if start < item.reference_time <= end
        and item.dimensions == dimension_lookup[rule.field_ref]
    )
    if not observations:
        msg = "state-conditioned target rule has insufficient legal history"
        raise ValueError(msg)
    values = tuple(_numeric(item.value) for item in observations)
    if rule.aggregation is StateAggregation.LAST:
        base = values[-1]
    elif rule.aggregation is StateAggregation.MEAN:
        base = fmean(values)
    elif rule.aggregation is StateAggregation.MAXIMUM:
        base = max(values)
    else:
        base = min(values)
    return base * rule.multiplier + rule.additive


def _first_event_index(
    definition: TargetDefinition,
    observations: tuple[RegisteredObservation, ...],
    threshold: float,
) -> int | None:
    condition = definition.event_condition
    if condition is None:
        msg = "event target lost its condition"
        raise AssertionError(msg)
    for index, observation in enumerate(observations):
        value = _numeric(observation.value)
        matched = {
            Comparison.GREATER_THAN: value > threshold,
            Comparison.GREATER_THAN_OR_EQUAL: value >= threshold,
            Comparison.LESS_THAN: value < threshold,
            Comparison.LESS_THAN_OR_EQUAL: value <= threshold,
        }[condition.comparison]
        if matched:
            return index
    return None


def _reduce_path(reduction: PathReduction | None, values: tuple[float, ...]) -> float:
    if reduction is PathReduction.MAXIMUM:
        return max(values)
    if reduction is PathReduction.MINIMUM:
        return min(values)
    if reduction is PathReduction.SUM:
        return sum(values)
    if reduction is PathReduction.MEAN:
        return fmean(values)
    msg = "path target lost its reduction"
    raise AssertionError(msg)


def _numeric(value: Scalar) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        msg = "path and event targets require numeric observations"
        raise TypeError(msg)
    return float(value)
