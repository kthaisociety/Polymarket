"""Feature materialization from exact legal information sets without fitting."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from statistics import fmean
from typing import TYPE_CHECKING

from research_agent.data_foundation._identity import require_aware, stable_identity
from research_agent.formalization.definitions import (
    FailureAction,
    FeatureAlignment,
    FeatureDefinition,
    HistoryKind,
)
from research_agent.formalization.expressions import (
    CompiledFeatureExpression,
    ExpressionOperator,
    FeatureCompiler,
    FeatureExpression,
)

if TYPE_CHECKING:
    from datetime import datetime

    from research_agent.data_foundation.information import InformationSet
    from research_agent.data_foundation.observations import RegisteredObservation
    from research_agent.data_foundation.schema import FieldRef


class FeatureValueStatus(Enum):
    """Explicit materialization status for one decision-time value."""

    PRESENT = "present"
    MISSING_INPUT = "missing_input"
    INSUFFICIENT_HISTORY = "insufficient_history"
    INVALID_DOMAIN = "invalid_domain"


class FeatureSeriesStatus(Enum):
    """Whether a series is fully or only explicitly partially materialized."""

    READY = "ready"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"


class FeatureMaterializationError(ValueError):
    """Base class for a blocking formal materialization failure."""


class TemporalAccessError(FeatureMaterializationError):
    """The supplied information boundary contains temporally illegal content."""


class FittedStateRequiredError(FeatureMaterializationError):
    """A fitted expression has no exact trainer-supplied state."""


class InvalidFittedStateError(FeatureMaterializationError):
    """Supplied learned state does not belong to this legal fit boundary."""


class _MissingInputError(FeatureMaterializationError):
    pass


class _InsufficientHistoryError(FeatureMaterializationError):
    pass


class _InvalidDomainError(FeatureMaterializationError):
    pass


@dataclass(frozen=True, slots=True)
class FittedTransformState:
    """Trainer-produced learned state bound to one window and InformationSet."""

    state_slot: str
    feature_definition_id: str
    environment_id: str
    training_window_id: str
    information_set_id: str
    fitted_through: datetime
    parameters: tuple[tuple[str, float], ...]
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        """Require exact window, applicability, parameters, and provenance."""
        require_aware(self.fitted_through, "fitted_through")
        if not all(
            (
                self.state_slot,
                self.feature_definition_id,
                self.environment_id,
                self.training_window_id,
                self.information_set_id,
                self.provenance_refs,
            )
        ):
            msg = "fitted transform state requires exact window, view, and provenance"
            raise ValueError(msg)
        names = tuple(name for name, _ in self.parameters)
        if len(set(names)) != len(names) or any(not name for name in names):
            msg = "fitted transform parameters require unique exact names"
            raise ValueError(msg)

    @property
    def identity(self) -> str:
        """Return learned-state identity including the legal fit boundary."""
        return stable_identity("fitted-transform-state", self)

    def parameter(self, name: str) -> float:
        """Resolve an exact parameter without fallback."""
        matches = tuple(value for key, value in self.parameters if key == name)
        if len(matches) != 1:
            msg = f"fitted state does not define exact parameter {name!r}"
            raise InvalidFittedStateError(msg)
        return matches[0]


@dataclass(frozen=True, slots=True)
class FeatureValue:
    """One feature value tied to a legal decision-time view and exact dimension slice."""

    decision_time: datetime
    dimensions: tuple[tuple[str, str], ...]
    information_set_id: str
    value: float | None
    status: FeatureValueStatus
    source_observation_ids: tuple[str, ...]
    failure_detail: str | None


@dataclass(frozen=True, slots=True)
class FeatureSeries:
    """Immutable materialization of one definition across legal information boundaries."""

    series_id: str
    definition_id: str
    environment_id: str
    compiled_expression_id: str
    values: tuple[FeatureValue, ...]
    fitted_state_ids: tuple[str, ...]
    status: FeatureSeriesStatus


@dataclass(frozen=True, slots=True)
class _EvaluationContext:
    definition: FeatureDefinition
    information: InformationSet
    observations: tuple[RegisteredObservation, ...]
    fitted_states: dict[str, FittedTransformState]
    source_ids: set[str]


class FeatureMaterializer:
    """Evaluate exact expressions; this boundary deliberately has no fitting capability."""

    def materialize(
        self,
        definition: FeatureDefinition,
        compiled: CompiledFeatureExpression,
        information_sets: tuple[InformationSet, ...],
        *,
        fitted_states: tuple[FittedTransformState, ...] = (),
    ) -> FeatureSeries:
        """Materialize one declared dimension slice across increasing legal decision times."""
        return self._materialize(
            definition,
            compiled,
            information_sets,
            fitted_states=fitted_states,
            training_window_id=None,
        )

    def materialize_training(
        self,
        definition: FeatureDefinition,
        compiled: CompiledFeatureExpression,
        information_sets: tuple[InformationSet, ...],
        *,
        fitted_states: tuple[FittedTransformState, ...] = (),
        training_window_id: str,
    ) -> FeatureSeries:
        """Materialize rows inside the exact window that fitted supplied transforms.

        A transform learned across ``W_t`` is allowed to encode every row in that same
        window.  Ordinary inference remains stricter: :meth:`materialize` still rejects
        state learned after its decision time.
        """
        if not training_window_id:
            msg = "training materialization requires an exact window identity"
            raise ValueError(msg)
        if any(state.training_window_id != training_window_id for state in fitted_states):
            msg = "training materialization received state from another window"
            raise InvalidFittedStateError(msg)
        return self._materialize(
            definition,
            compiled,
            information_sets,
            fitted_states=fitted_states,
            training_window_id=training_window_id,
        )

    def _materialize(
        self,
        definition: FeatureDefinition,
        compiled: CompiledFeatureExpression,
        information_sets: tuple[InformationSet, ...],
        *,
        fitted_states: tuple[FittedTransformState, ...],
        training_window_id: str | None,
    ) -> FeatureSeries:
        if compiled.definition_id != definition.identity:
            msg = "compiled expression does not belong to the supplied FeatureDefinition"
            raise FeatureMaterializationError(msg)
        if (
            compiled.expression != definition.expression
            or compiled.compiler_version != FeatureCompiler.VERSION
        ):
            msg = "compiled expression is not the exact supported representation of the definition"
            raise FeatureMaterializationError(msg)
        if not information_sets:
            msg = "feature materialization requires at least one InformationSet"
            raise FeatureMaterializationError(msg)
        decision_times = tuple(item.decision_time for item in information_sets)
        if tuple(sorted(decision_times)) != decision_times or len(set(decision_times)) != len(
            decision_times
        ):
            msg = "InformationSets must have unique increasing decision times"
            raise FeatureMaterializationError(msg)
        state_index = self._index_states(definition, fitted_states)
        values = tuple(
            self._materialize_one(
                definition,
                compiled.expression,
                information,
                state_index,
                training_window_id=training_window_id,
            )
            for information in information_sets
        )
        used_states = tuple(
            state_index[(slot, information.information_set_id)].identity
            for information in information_sets
            for slot, _ in definition.fitted_state_procedures
        )
        present_count = sum(item.status is FeatureValueStatus.PRESENT for item in values)
        if present_count == len(values):
            status = FeatureSeriesStatus.READY
        elif present_count == 0:
            status = FeatureSeriesStatus.INSUFFICIENT
        else:
            status = FeatureSeriesStatus.PARTIAL
        payload = {
            "definition_id": definition.identity,
            "environment_id": definition.environment_id,
            "compiled_expression_id": compiled.identity,
            "values": values,
            "fitted_state_ids": used_states,
            "status": status,
        }
        return FeatureSeries(
            series_id=stable_identity("feature-series", payload),
            definition_id=definition.identity,
            environment_id=definition.environment_id,
            compiled_expression_id=compiled.identity,
            values=values,
            fitted_state_ids=used_states,
            status=status,
        )

    @staticmethod
    def _index_states(
        definition: FeatureDefinition,
        fitted_states: tuple[FittedTransformState, ...],
    ) -> dict[tuple[str, str], FittedTransformState]:
        index: dict[tuple[str, str], FittedTransformState] = {}
        declared = frozenset(slot for slot, _ in definition.fitted_state_procedures)
        for state in fitted_states:
            if not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
                state, FittedTransformState
            ):
                msg = "materializer accepts only already-fitted transform state"
                raise TypeError(msg)
            if state.state_slot not in declared:
                msg = "fitted state supplies an undeclared operation slot"
                raise InvalidFittedStateError(msg)
            key = (state.state_slot, state.information_set_id)
            if key in index:
                msg = "duplicate fitted state for one operation and InformationSet"
                raise InvalidFittedStateError(msg)
            index[key] = state
        return index

    def _materialize_one(
        self,
        definition: FeatureDefinition,
        expression: FeatureExpression,
        information: InformationSet,
        state_index: dict[tuple[str, str], FittedTransformState],
        *,
        training_window_id: str | None,
    ) -> FeatureValue:
        self._validate_information(definition, information)
        states: dict[str, FittedTransformState] = {}
        for slot, _ in definition.fitted_state_procedures:
            state = state_index.get((slot, information.information_set_id))
            if state is None:
                msg = f"fitted state {slot!r} is required for this InformationSet"
                raise FittedStateRequiredError(msg)
            self._validate_state(
                definition,
                information,
                state,
                training_window_id=training_window_id,
            )
            states[slot] = state
        observations = tuple(
            item
            for item in information.observations
            if item.field_ref in definition.dependencies
            and item.dimensions == definition.dimensions
        )
        context = _EvaluationContext(definition, information, observations, states, set())
        anchor = definition.temporal_mapping.decision_offset.apply(information.decision_time)
        try:
            self._validate_warm_up(context, anchor)
            value = self._evaluate(expression, anchor, context)
        except _MissingInputError as exc:
            return self._handle_expected_failure(
                definition.missing_input,
                FeatureValueStatus.MISSING_INPUT,
                information,
                definition,
                context,
                exc,
            )
        except _InsufficientHistoryError as exc:
            return self._handle_expected_failure(
                definition.insufficiency,
                FeatureValueStatus.INSUFFICIENT_HISTORY,
                information,
                definition,
                context,
                exc,
            )
        except _InvalidDomainError as exc:
            return self._handle_expected_failure(
                definition.invalid_domain,
                FeatureValueStatus.INVALID_DOMAIN,
                information,
                definition,
                context,
                exc,
            )
        return FeatureValue(
            decision_time=information.decision_time,
            dimensions=definition.dimensions,
            information_set_id=information.information_set_id,
            value=value,
            status=FeatureValueStatus.PRESENT,
            source_observation_ids=tuple(sorted(context.source_ids)),
            failure_detail=None,
        )

    @staticmethod
    def _validate_information(definition: FeatureDefinition, information: InformationSet) -> None:
        require_aware(information.decision_time, "information decision_time")
        if information.environment_id != definition.environment_id:
            msg = "InformationSet and feature environment identities differ"
            raise FeatureMaterializationError(msg)
        if not set(definition.dependencies) <= set(information.requested_fields):
            msg = "InformationSet does not contain every exact feature dependency"
            raise FeatureMaterializationError(msg)
        for observation in information.observations:
            if observation.available_at > information.decision_time:
                msg = "InformationSet contains a future observation"
                raise TemporalAccessError(msg)
            if observation.field_ref not in information.requested_fields:
                msg = "InformationSet contains an observation outside its declared field scope"
                raise TemporalAccessError(msg)

    @staticmethod
    def _validate_state(
        definition: FeatureDefinition,
        information: InformationSet,
        state: FittedTransformState,
        *,
        training_window_id: str | None,
    ) -> None:
        if state.feature_definition_id != definition.identity:
            msg = "fitted state belongs to another feature definition"
            raise InvalidFittedStateError(msg)
        if state.environment_id != definition.environment_id:
            msg = "fitted state belongs to another environment"
            raise InvalidFittedStateError(msg)
        if state.information_set_id != information.information_set_id:
            msg = "fitted state belongs to another InformationSet"
            raise InvalidFittedStateError(msg)
        if training_window_id is not None and state.training_window_id != training_window_id:
            msg = "fitted state belongs to another training window"
            raise InvalidFittedStateError(msg)
        if training_window_id is None and state.fitted_through > information.decision_time:
            msg = "fitted state was learned after decision time"
            raise InvalidFittedStateError(msg)

    @staticmethod
    def _validate_warm_up(context: _EvaluationContext, anchor: datetime) -> None:
        warm_up = context.definition.history.warm_up
        if warm_up.is_zero:
            return
        eligible = FeatureMaterializer._eligible_observations(context, anchor)
        lower = warm_up.negated().apply(anchor)
        if not eligible or min(item.reference_time for item in eligible) > lower:
            msg = "declared feature warm-up is not satisfied"
            raise _InsufficientHistoryError(msg)

    def _evaluate(  # noqa: C901, PLR0911, PLR0912
        self,
        expression: FeatureExpression,
        anchor: datetime,
        context: _EvaluationContext,
    ) -> float:
        operator = expression.operator
        if operator is ExpressionOperator.FIELD:
            if expression.field_ref is None:
                msg = "compiled field expression lost its FieldRef"
                raise AssertionError(msg)
            return self._field_value(expression.field_ref, anchor, context)
        if operator is ExpressionOperator.CONSTANT:
            if expression.constant is None:
                msg = "compiled constant expression lost its value"
                raise AssertionError(msg)
            return expression.constant
        operand = expression.operands[0]
        if operator is ExpressionOperator.LAG:
            if expression.duration is None:
                raise AssertionError
            return self._evaluate(operand, expression.duration.negated().apply(anchor), context)
        if operator is ExpressionOperator.DIFFERENCE:
            if expression.duration is None:
                raise AssertionError
            return self._evaluate(operand, anchor, context) - self._evaluate(
                operand, expression.duration.negated().apply(anchor), context
            )
        if operator is ExpressionOperator.ROLLING_MEAN:
            return self._rolling_mean(expression, anchor, context)
        if operator is ExpressionOperator.LOG:
            value = self._evaluate(operand, anchor, context)
            if value <= 0:
                msg = "log operand is outside its positive domain"
                raise _InvalidDomainError(msg)
            return math.log(value)
        if operator in {
            ExpressionOperator.ADD,
            ExpressionOperator.SUBTRACT,
            ExpressionOperator.MULTIPLY,
            ExpressionOperator.DIVIDE,
        }:
            return self._binary(expression, anchor, context)
        if operator is ExpressionOperator.STANDARDIZE:
            if expression.state_slot is None:
                raise AssertionError
            state = context.fitted_states[expression.state_slot]
            location = state.parameter("location")
            scale = state.parameter("scale")
            if scale == 0:
                msg = "standardization scale cannot be zero"
                raise _InvalidDomainError(msg)
            return (self._evaluate(operand, anchor, context) - location) / scale
        msg = f"unsupported exact feature operator: {operator.value}"
        raise FeatureMaterializationError(msg)

    def _field_value(
        self,
        field_ref: FieldRef,
        anchor: datetime,
        context: _EvaluationContext,
    ) -> float:
        observations = tuple(
            item
            for item in self._eligible_observations(context, anchor)
            if item.field_ref == field_ref and item.reference_time <= anchor
        )
        if context.definition.temporal_mapping.alignment is FeatureAlignment.EXACT:
            observations = tuple(item for item in observations if item.reference_time == anchor)
        else:
            latest_time = max((item.reference_time for item in observations), default=None)
            observations = tuple(
                item for item in observations if item.reference_time == latest_time
            )
        if not observations:
            msg = f"no exact legal value for field {field_ref.identity} at feature anchor"
            raise _MissingInputError(msg)
        if len(observations) != 1:
            msg = "field and dimension slice resolves to multiple observations"
            raise FeatureMaterializationError(msg)
        observation = observations[0]
        if isinstance(observation.value, bool) or not isinstance(observation.value, (int, float)):
            msg = "numeric expression received a non-numeric field value"
            raise _InvalidDomainError(msg)
        context.source_ids.add(observation.observation_id)
        return float(observation.value)

    @staticmethod
    def _eligible_observations(
        context: _EvaluationContext,
        anchor: datetime,
    ) -> tuple[RegisteredObservation, ...]:
        width = context.definition.history.fixed_width
        if context.definition.history.kind is HistoryKind.EXPANDING or width is None:
            return context.observations
        lower = width.negated().apply(anchor)
        return tuple(item for item in context.observations if item.reference_time > lower)

    def _rolling_mean(
        self,
        expression: FeatureExpression,
        anchor: datetime,
        context: _EvaluationContext,
    ) -> float:
        duration = expression.duration
        minimum = expression.min_observations
        if duration is None or minimum is None:
            raise AssertionError
        lower = duration.negated().apply(anchor)
        candidate_times = tuple(
            sorted(
                {
                    item.reference_time
                    for item in self._eligible_observations(context, anchor)
                    if lower < item.reference_time <= anchor
                }
            )
        )
        values: list[float] = []
        for candidate_time in candidate_times:
            try:
                values.append(self._evaluate(expression.operands[0], candidate_time, context))
            except _MissingInputError:
                continue
        if len(values) < minimum:
            msg = "rolling operation has insufficient legal observations"
            raise _InsufficientHistoryError(msg)
        return fmean(values)

    def _binary(
        self,
        expression: FeatureExpression,
        anchor: datetime,
        context: _EvaluationContext,
    ) -> float:
        left = self._evaluate(expression.operands[0], anchor, context)
        right = self._evaluate(expression.operands[1], anchor, context)
        if expression.operator is ExpressionOperator.ADD:
            return left + right
        if expression.operator is ExpressionOperator.SUBTRACT:
            return left - right
        if expression.operator is ExpressionOperator.MULTIPLY:
            return left * right
        if right == 0:
            msg = "division denominator cannot be zero"
            raise _InvalidDomainError(msg)
        return left / right

    @staticmethod
    def _handle_expected_failure(  # noqa: PLR0913, PLR0917
        action: FailureAction,
        status: FeatureValueStatus,
        information: InformationSet,
        definition: FeatureDefinition,
        context: _EvaluationContext,
        error: FeatureMaterializationError,
    ) -> FeatureValue:
        if action is FailureAction.FAIL:
            raise error
        return FeatureValue(
            decision_time=information.decision_time,
            dimensions=definition.dimensions,
            information_set_id=information.information_set_id,
            value=None,
            status=status,
            source_observation_ids=tuple(sorted(context.source_ids)),
            failure_detail=str(error),
        )
