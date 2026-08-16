"""Controlled fitting and inference boundaries for development candidates."""

# ruff: noqa: C901, D102, PLC0415, PLR0911, PLR0912, PLR0913, PLR2004

from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite, sqrt
from typing import TYPE_CHECKING, Never

from research_agent.data_foundation._identity import stable_identity
from research_agent.data_foundation.information import BoundaryStatus, InformationSetBuilder
from research_agent.data_foundation.targets import MaturityPolicy, construct_label
from research_agent.development.records import (
    DevelopmentStatus,
    FitRecord,
    FittedModelState,
    FittedPredictiveSystem,
    LearnedTransformState,
    OutcomeRecord,
    PredictionRecord,
    TrainingBlocked,
    TrainingFailure,
    TrainingFailureCode,
)
from research_agent.formalization import (
    ExpressionOperator,
    FeatureCompiler,
    FeatureMaterializer,
    FeatureSeriesStatus,
    FeatureValueStatus,
    FittedTransformState,
)

if TYPE_CHECKING:
    from datetime import datetime

    from research_agent.data_foundation.information import InformationSet
    from research_agent.data_foundation.observations import DataCatalogSnapshot, DimensionValues
    from research_agent.data_foundation.samples import PredictorValue, TrainingRow
    from research_agent.data_foundation.targets import TargetDefinition
    from research_agent.data_foundation.windows import TrainingWindow
    from research_agent.development.training_information import (
        TrainingInformationBundle,
        TrainingInformationRegistry,
    )
    from research_agent.formalization import (
        FeatureExpression,
        FeatureSeries,
        ModelDefinition,
        PredictiveSystemDefinition,
    )


@dataclass(frozen=True, slots=True)
class _TrainingMatrix:
    row_ids: tuple[str, ...]
    decision_times: tuple[datetime, ...]
    dimensions: tuple[DimensionValues, ...]
    values: tuple[tuple[float, ...], ...]
    labels: tuple[float, ...]
    information_set_ids: tuple[str, ...] = ()
    feature_series_ids: tuple[str, ...] = ()
    compiled_feature_ids: tuple[str, ...] = ()


class FittedSystemRegistry:
    """Trainer-owned issuance registry for fitted systems accepted by inference."""

    def __init__(self) -> None:
        """Start with no state authorized for inference."""
        self._issued: dict[str, FittedPredictiveSystem] = {}

    def _issue(self, fitted: FittedPredictiveSystem) -> None:
        existing = self._issued.get(fitted.fitted_system_id)
        if existing is not None and existing != fitted:
            msg = "fitted-system issuance identity conflicts with existing trainer state"
            raise ValueError(msg)
        self._issued[fitted.fitted_system_id] = fitted

    def require_issued(self, fitted: FittedPredictiveSystem) -> None:
        """Reject structurally valid state that this training authority did not issue."""
        issued = self._issued.get(fitted.fitted_system_id)
        if issued is None or issued != fitted:
            msg = "fitted system was not issued by the required training authority"
            raise ValueError(msg)


class SystemTrainer:
    """Fit every learned quantity using only one exact READY TrainingWindow."""

    _SUPPORTED = frozenset({"mean", "linear_regression", "linear_interactions"})

    def __init__(
        self,
        *,
        registry: FittedSystemRegistry | None = None,
        training_information_registry: TrainingInformationRegistry | None = None,
    ) -> None:
        """Bind fitting and legal training views to explicit issuance authorities."""
        from research_agent.development.training_information import (
            TrainingInformationRegistry,
        )

        self.registry = registry if registry is not None else FittedSystemRegistry()
        self.training_information_registry = (
            training_information_registry
            if training_information_registry is not None
            else TrainingInformationRegistry()
        )

    def fit(
        self,
        definition: PredictiveSystemDefinition,
        window: TrainingWindow,
        training_information: TrainingInformationBundle | None = None,
    ) -> FittedPredictiveSystem:
        """Execute the exact declared recipe or raise one typed blocking failure."""
        provenance = (
            *definition.provenance_refs,
            f"window:{window.window_id}",
            *(
                (f"training-information:{training_information.bundle_id}",)
                if training_information
                else ()
            ),
        )
        if window.status is not BoundaryStatus.READY or not window.rows:
            self._block(
                TrainingFailureCode.WINDOW_NOT_READY,
                definition,
                window,
                "SystemTrainer requires a non-empty READY TrainingWindow",
                provenance,
            )
        if any(row.target_id != definition.target.identity for row in window.rows):
            self._block(
                TrainingFailureCode.INCOMPATIBLE_IDENTITY,
                definition,
                window,
                "training rows do not belong to the system target identity",
                provenance,
            )
        for feature in definition.feature_set.members:
            try:
                FeatureCompiler().compile(feature)
            except ValueError as error:
                self._block(
                    TrainingFailureCode.INCOMPATIBLE_IDENTITY,
                    definition,
                    window,
                    f"feature definition cannot compile exactly: {error}",
                    provenance,
                )
            if any(row.dimensions != feature.dimensions for row in window.rows):
                self._block(
                    TrainingFailureCode.INCOMPATIBLE_IDENTITY,
                    definition,
                    window,
                    "training-row dimensions differ from the exact feature dimension slice",
                    provenance,
                )
        if training_information is not None:
            try:
                self.training_information_registry.require_issued(training_information)
                self._validate_training_information(definition, window, training_information)
            except ValueError as error:
                self._block(
                    TrainingFailureCode.INVALID_TRAINING_DATA,
                    definition,
                    window,
                    f"formal training information is incompatible: {error}",
                    provenance,
                )
        unsupported = tuple(
            model for model in definition.models if model.algorithm not in self._SUPPORTED
        )
        if unsupported:
            model = unsupported[0]
            self._block(
                TrainingFailureCode.UNSUPPORTED_RECIPE,
                definition,
                window,
                f"unsupported model recipe {model.algorithm!r}; no fallback was declared",
                provenance,
                model=model,
            )
        try:
            transforms = self._fit_transforms(
                definition,
                window,
                provenance,
                training_information,
            )
            matrix = self._matrix(
                definition,
                window.rows,
                transforms,
                training_information,
            )
            models = tuple(
                self._fit_model(
                    model,
                    window.window_id,
                    matrix,
                    tuple(feature.identity for feature in definition.feature_set.members),
                    provenance,
                )
                for model in definition.models
            )
            weights = self._ensemble_weights(definition, models)
        except TrainingBlocked:
            raise
        except (ArithmeticError, TypeError, ValueError) as error:
            self._block(
                TrainingFailureCode.FIT_FAILED,
                definition,
                window,
                f"exact training recipe failed: {error}",
                provenance,
            )
        fitted_through = max(row.label_matured_at for row in window.rows)
        fit_payload: dict[str, object] = {
            "system_definition_id": definition.identity,
            "training_window_id": window.window_id,
            "training_sample_id": window.sample_id,
            "environment_id": definition.environment_id,
            "fitted_through": fitted_through,
            "row_ids": matrix.row_ids,
            "model_state_ids": tuple(model.fitted_model_id for model in models),
            "transform_state_ids": tuple(state.state_id for state in transforms),
            "procedure_refs": (
                definition.training_protocol_id,
                *(model.selection_procedure_ref for model in definition.models),
            ),
            "provenance_refs": provenance,
            "status": DevelopmentStatus.DEVELOPMENT,
        }
        if training_information is not None:
            fit_payload.update(
                {
                    "training_information_bundle_id": training_information.bundle_id,
                    "information_set_ids": matrix.information_set_ids,
                    "feature_series_ids": matrix.feature_series_ids,
                    "compiled_feature_ids": matrix.compiled_feature_ids,
                }
            )
        fit_record = FitRecord(
            fit_id=stable_identity("fit-record", fit_payload),
            system_definition_id=definition.identity,
            training_window_id=window.window_id,
            training_sample_id=window.sample_id,
            environment_id=definition.environment_id,
            fitted_through=fitted_through,
            row_ids=matrix.row_ids,
            model_state_ids=tuple(model.fitted_model_id for model in models),
            transform_state_ids=tuple(state.state_id for state in transforms),
            procedure_refs=(
                definition.training_protocol_id,
                *(model.selection_procedure_ref for model in definition.models),
            ),
            provenance_refs=provenance,
            training_information_bundle_id=(
                None if training_information is None else training_information.bundle_id
            ),
            information_set_ids=matrix.information_set_ids,
            feature_series_ids=matrix.feature_series_ids,
            compiled_feature_ids=matrix.compiled_feature_ids,
            status=DevelopmentStatus.DEVELOPMENT,
        )
        system_payload = {
            "system_definition_id": definition.identity,
            "feature_set_id": definition.feature_set.identity,
            "target_id": definition.target.identity,
            "environment_id": definition.environment_id,
            "fit_record": fit_record,
            "models": models,
            "transforms": transforms,
            "ensemble_weights": weights,
        }
        fitted = FittedPredictiveSystem(
            fitted_system_id=stable_identity("fitted-predictive-system", system_payload),
            system_definition_id=definition.identity,
            feature_set_id=definition.feature_set.identity,
            target_id=definition.target.identity,
            environment_id=definition.environment_id,
            fit_record=fit_record,
            models=models,
            transforms=transforms,
            ensemble_weights=weights,
        )
        self.registry._issue(fitted)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        return fitted

    def _fit_transforms(
        self,
        definition: PredictiveSystemDefinition,
        window: TrainingWindow,
        provenance: tuple[str, ...],
        training_information: TrainingInformationBundle | None,
    ) -> tuple[LearnedTransformState, ...]:
        fitted_through = max(row.label_matured_at for row in window.rows)
        states: list[LearnedTransformState] = []
        for feature in definition.feature_set.members:
            slots = self._standardize_operands(feature.expression)
            declared = dict(feature.fitted_state_procedures)
            if set(slots) != set(declared):
                msg = "only exact declared standardize fitted procedures are supported"
                raise ValueError(msg)
            for slot, operand in slots.items():
                if declared[slot] != "fit:standardize-v1":
                    msg = f"unsupported fitted transform procedure {declared[slot]!r}"
                    raise ValueError(msg)
                transform_provenance = provenance
                if training_information is None:
                    values = tuple(
                        self.evaluate_row_expression(operand, row.predictors, {})
                        for row in window.rows
                    )
                else:
                    if operand.fitted_slots():
                        msg = "nested fitted transforms are not supported without an exact ordering"
                        raise ValueError(msg)
                    operand_definition = replace(
                        feature,
                        name=f"{feature.name}::{slot}::training-operand",
                        dependencies=operand.dependencies(),
                        expression=operand,
                        fitted_state_procedures=(),
                    )
                    compiled_operand = FeatureCompiler().compile(operand_definition)
                    operand_series = FeatureMaterializer().materialize(
                        operand_definition,
                        compiled_operand,
                        training_information.information_sets,
                    )
                    if (
                        operand_series.status is not FeatureSeriesStatus.READY
                        or len(operand_series.values) != len(window.rows)
                        or any(item.value is None for item in operand_series.values)
                    ):
                        msg = "fitted transform operand did not materialize for every legal row"
                        raise ValueError(msg)
                    values = tuple(
                        float(item.value)
                        for item in operand_series.values
                        if item.value is not None
                    )
                    transform_provenance = (
                        *provenance,
                        f"operand-series:{operand_series.series_id}",
                    )
                location = sum(values) / len(values)
                variance = sum((value - location) ** 2 for value in values) / len(values)
                scale = sqrt(variance)
                if scale == 0:
                    msg = f"standardize state {slot!r} has zero scale"
                    raise ValueError(msg)
                payload = {
                    "state_slot": slot,
                    "feature_definition_id": feature.identity,
                    "training_window_id": window.window_id,
                    "fitted_through": fitted_through,
                    "parameters": (("location", location), ("scale", scale)),
                    "provenance_refs": (*transform_provenance, declared[slot]),
                }
                states.append(
                    LearnedTransformState(
                        state_id=stable_identity("learned-transform", payload),
                        state_slot=slot,
                        feature_definition_id=feature.identity,
                        training_window_id=window.window_id,
                        fitted_through=fitted_through,
                        parameters=(("location", location), ("scale", scale)),
                        provenance_refs=(*transform_provenance, declared[slot]),
                    )
                )
        return tuple(states)

    def _matrix(
        self,
        definition: PredictiveSystemDefinition,
        rows: tuple[TrainingRow, ...],
        transforms: tuple[LearnedTransformState, ...],
        training_information: TrainingInformationBundle | None,
    ) -> _TrainingMatrix:
        state_by_feature = {
            feature.identity: {
                state.state_slot: dict(state.parameters)
                for state in transforms
                if state.feature_definition_id == feature.identity
            }
            for feature in definition.feature_set.members
        }
        if training_information is not None:
            return self._formal_matrix(
                definition,
                rows,
                transforms,
                training_information,
            )
        values: list[tuple[float, ...]] = []
        labels: list[float] = []
        for row in rows:
            vector = tuple(
                self.evaluate_row_expression(
                    feature.expression,
                    row.predictors,
                    state_by_feature[feature.identity],
                )
                for feature in definition.feature_set.members
            )
            if any(not isfinite(value) for value in vector):
                msg = "training feature matrix contains non-finite value"
                raise ValueError(msg)
            if isinstance(row.label, bool) or not isinstance(row.label, (int, float)):
                msg = "initial deterministic trainers require numeric labels"
                raise TypeError(msg)
            label = float(row.label)
            if not isfinite(label):
                msg = "training label is non-finite"
                raise ValueError(msg)
            values.append(vector)
            labels.append(label)
        return _TrainingMatrix(
            tuple(row.row_id for row in rows),
            tuple(row.decision_time for row in rows),
            tuple(row.dimensions for row in rows),
            tuple(values),
            tuple(labels),
        )

    @staticmethod
    def _validate_training_information(
        definition: PredictiveSystemDefinition,
        window: TrainingWindow,
        training_information: TrainingInformationBundle,
    ) -> None:
        dependencies = tuple(
            dict.fromkeys(
                dependency
                for feature in definition.feature_set.members
                for dependency in feature.dependencies
            )
        )
        if training_information.environment_id != definition.environment_id:
            msg = "training information belongs to another environment"
            raise ValueError(msg)
        if training_information.training_window_id != window.window_id:
            msg = "training information belongs to another window"
            raise ValueError(msg)
        if training_information.training_sample_id != window.sample_id:
            msg = "training information belongs to another sample"
            raise ValueError(msg)
        if training_information.row_ids != tuple(row.row_id for row in window.rows):
            msg = "training information row order differs from the exact window"
            raise ValueError(msg)
        if training_information.requested_fields != dependencies:
            msg = "training information does not bind the exact ordered feature dependencies"
            raise ValueError(msg)
        if any(
            entry.dimensions != row.dimensions
            or entry.information.decision_time != row.decision_time
            for entry, row in zip(training_information.entries, window.rows, strict=True)
        ):
            msg = "training information row dimensions or decision clocks differ"
            raise ValueError(msg)

    def _formal_matrix(
        self,
        definition: PredictiveSystemDefinition,
        rows: tuple[TrainingRow, ...],
        transforms: tuple[LearnedTransformState, ...],
        training_information: TrainingInformationBundle,
    ) -> _TrainingMatrix:
        series: list[FeatureSeries] = []
        compiled_ids: list[str] = []
        fitted_through = max(row.label_matured_at for row in rows)
        for feature in definition.feature_set.members:
            compiled = FeatureCompiler().compile(feature)
            compiled_ids.append(compiled.identity)
            states = tuple(
                FittedTransformState(
                    state_slot=state.state_slot,
                    feature_definition_id=state.feature_definition_id,
                    environment_id=definition.environment_id,
                    training_window_id=state.training_window_id,
                    information_set_id=information.information_set_id,
                    fitted_through=fitted_through,
                    parameters=state.parameters,
                    provenance_refs=state.provenance_refs,
                )
                for information in training_information.information_sets
                for state in transforms
                if state.feature_definition_id == feature.identity
            )
            materialized = FeatureMaterializer().materialize_training(
                feature,
                compiled,
                training_information.information_sets,
                fitted_states=states,
                training_window_id=training_information.training_window_id,
            )
            if (
                materialized.status is not FeatureSeriesStatus.READY
                or len(materialized.values) != len(rows)
                or any(item.value is None for item in materialized.values)
            ):
                msg = "formal feature did not materialize one value for every training row"
                raise ValueError(msg)
            series.append(materialized)

        vectors = tuple(
            tuple(self._present_feature_value(item.values[index].value) for item in series)
            for index in range(len(rows))
        )
        if any(
            len(vector) != len(series) or any(not isfinite(value) for value in vector)
            for vector in vectors
        ):
            msg = "formal training feature matrix contains missing or non-finite values"
            raise ValueError(msg)
        labels = tuple(self._numeric_training_label(row) for row in rows)
        return _TrainingMatrix(
            row_ids=tuple(row.row_id for row in rows),
            decision_times=tuple(row.decision_time for row in rows),
            dimensions=tuple(row.dimensions for row in rows),
            values=vectors,
            labels=labels,
            information_set_ids=tuple(
                item.information_set_id for item in training_information.information_sets
            ),
            feature_series_ids=tuple(item.series_id for item in series),
            compiled_feature_ids=tuple(compiled_ids),
        )

    @staticmethod
    def _numeric_training_label(row: TrainingRow) -> float:
        if isinstance(row.label, bool) or not isinstance(row.label, (int, float)):
            msg = "initial deterministic trainers require numeric labels"
            raise TypeError(msg)
        label = float(row.label)
        if not isfinite(label):
            msg = "training label is non-finite"
            raise ValueError(msg)
        return label

    @staticmethod
    def _present_feature_value(value: float | None) -> float:
        if value is None:
            msg = "formal training feature value is missing"
            raise ValueError(msg)
        return float(value)

    @classmethod
    def evaluate_row_expression(
        cls,
        expression: FeatureExpression,
        predictors: tuple[PredictorValue, ...],
        fitted_states: dict[str, dict[str, float]],
    ) -> float:
        operator = expression.operator
        if operator is ExpressionOperator.FIELD:
            matches = tuple(item for item in predictors if item.field_ref == expression.field_ref)
            if len(matches) != 1:
                msg = "row does not contain one exact feature dependency"
                raise ValueError(msg)
            value = matches[0].value
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                msg = "numeric model received non-numeric predictor"
                raise TypeError(msg)
            return float(value)
        if operator is ExpressionOperator.CONSTANT:
            if expression.constant is None:
                msg = "constant expression lost its exact value"
                raise ValueError(msg)
            return expression.constant
        if operator in {
            ExpressionOperator.LAG,
            ExpressionOperator.DIFFERENCE,
            ExpressionOperator.ROLLING_MEAN,
        }:
            msg = f"{operator.value} requires pre-materialized temporal history; no fallback exists"
            raise ValueError(msg)
        left = cls.evaluate_row_expression(expression.operands[0], predictors, fitted_states)
        if operator is ExpressionOperator.LOG:
            if left <= 0:
                msg = "log feature is outside its positive domain"
                raise ValueError(msg)
            import math

            return math.log(left)
        if operator is ExpressionOperator.STANDARDIZE:
            if expression.state_slot is None or expression.state_slot not in fitted_states:
                msg = "standardize expression lacks exact trainer-owned state"
                raise ValueError(msg)
            parameters = fitted_states[expression.state_slot]
            return (left - parameters["location"]) / parameters["scale"]
        right = cls.evaluate_row_expression(expression.operands[1], predictors, fitted_states)
        if operator is ExpressionOperator.ADD:
            return left + right
        if operator is ExpressionOperator.SUBTRACT:
            return left - right
        if operator is ExpressionOperator.MULTIPLY:
            return left * right
        if operator is ExpressionOperator.DIVIDE:
            if right == 0:
                msg = "feature division denominator is zero"
                raise ValueError(msg)
            return left / right
        msg = f"unsupported feature operator {operator.value!r}"
        raise ValueError(msg)

    @classmethod
    def _standardize_operands(
        cls,
        expression: FeatureExpression,
    ) -> dict[str, FeatureExpression]:
        found: dict[str, FeatureExpression] = {}
        if expression.operator is ExpressionOperator.STANDARDIZE:
            if expression.state_slot is None:
                msg = "standardize expression lost its state slot"
                raise ValueError(msg)
            found[expression.state_slot] = expression.operands[0]
        for operand in expression.operands:
            for slot, child in cls._standardize_operands(operand).items():
                if slot in found and found[slot] != child:
                    msg = "one fitted-state slot cannot represent different transforms"
                    raise ValueError(msg)
                found[slot] = child
        return found

    def _fit_model(
        self,
        definition: ModelDefinition,
        window_id: str,
        matrix: _TrainingMatrix,
        feature_ids: tuple[str, ...],
        provenance: tuple[str, ...],
    ) -> FittedModelState:
        parameters = dict(definition.hyperparameters)
        allowed_by_algorithm: dict[str, frozenset[str]] = {
            "mean": frozenset(),
            "linear_regression": frozenset({"fit_intercept", "ridge"}),
            "linear_interactions": frozenset({"fit_intercept", "ridge"}),
        }
        allowed = allowed_by_algorithm[definition.algorithm]
        unknown = set(parameters) - allowed
        if unknown:
            msg = f"unsupported hyperparameters for exact recipe: {sorted(unknown)!r}"
            raise ValueError(msg)
        if definition.algorithm == "mean":
            if parameters:
                msg = "mean recipe accepts no hyperparameters"
                raise ValueError(msg)
            terms: tuple[tuple[int, ...], ...] = ()
            coefficients: tuple[float, ...] = ()
            intercept = sum(matrix.labels) / len(matrix.labels)
        else:
            fit_intercept = parameters.get("fit_intercept", True)
            ridge = parameters.get("ridge", 0.0)
            if not isinstance(fit_intercept, bool):
                msg = "fit_intercept must be boolean"
                raise TypeError(msg)
            if isinstance(ridge, bool) or not isinstance(ridge, (int, float)) or ridge < 0:
                msg = "ridge must be a non-negative number"
                raise ValueError(msg)
            feature_count = len(matrix.values[0])
            terms = tuple((index,) for index in range(feature_count))
            if definition.algorithm == "linear_interactions":
                terms = (
                    *terms,
                    *tuple(
                        (left, right)
                        for left in range(feature_count)
                        for right in range(left + 1, feature_count)
                    ),
                )
            design = tuple(self.expand_terms(row, terms) for row in matrix.values)
            coefficients, intercept = self.least_squares(
                design,
                matrix.labels,
                fit_intercept=fit_intercept,
                ridge=float(ridge),
            )
        payload = {
            "model_definition_id": definition.identity,
            "training_window_id": window_id,
            "algorithm": definition.algorithm,
            "input_feature_ids": feature_ids,
            "coefficients": coefficients,
            "intercept": intercept,
            "expansion_terms": terms,
            "provenance_refs": (*provenance, *definition.provenance_refs),
        }
        return FittedModelState(
            fitted_model_id=stable_identity("fitted-model-state", payload),
            model_definition_id=definition.identity,
            training_window_id=window_id,
            algorithm=definition.algorithm,
            input_feature_ids=feature_ids,
            coefficients=coefficients,
            intercept=intercept,
            expansion_terms=terms,
            provenance_refs=(*provenance, *definition.provenance_refs),
        )

    @staticmethod
    def expand_terms(
        row: tuple[float, ...],
        terms: tuple[tuple[int, ...], ...],
    ) -> tuple[float, ...]:
        return tuple(
            row[term[0]] if len(term) == 1 else row[term[0]] * row[term[1]] for term in terms
        )

    @staticmethod
    def least_squares(
        values: tuple[tuple[float, ...], ...],
        labels: tuple[float, ...],
        *,
        fit_intercept: bool,
        ridge: float,
    ) -> tuple[tuple[float, ...], float]:
        design = tuple(((1.0, *row) if fit_intercept else row) for row in values)
        width = len(design[0])
        if len(design) < width and ridge == 0:
            msg = "linear recipe is underdetermined and declares no regularization"
            raise ValueError(msg)
        gram = [
            [sum(row[left] * row[right] for row in design) for right in range(width)]
            for left in range(width)
        ]
        offset = 1 if fit_intercept else 0
        for index in range(offset, width):
            gram[index][index] += ridge
        rhs = [
            sum(row[index] * label for row, label in zip(design, labels, strict=True))
            for index in range(width)
        ]
        solution = SystemTrainer._solve(gram, rhs)
        intercept = solution[0] if fit_intercept else 0.0
        coefficients = tuple(solution[offset:])
        return coefficients, intercept

    @staticmethod
    def _solve(matrix: list[list[float]], rhs: list[float]) -> list[float]:
        size = len(rhs)
        augmented = [(*row, value) for row, value in zip(matrix, rhs, strict=True)]
        work = [list(row) for row in augmented]
        for column in range(size):
            pivot = max(range(column, size), key=lambda row: abs(work[row][column]))
            if abs(work[pivot][column]) < 1e-12:
                msg = "linear system is singular and no fallback is permitted"
                raise ValueError(msg)
            work[column], work[pivot] = work[pivot], work[column]
            pivot_value = work[column][column]
            work[column] = [value / pivot_value for value in work[column]]
            for row in range(size):
                if row == column:
                    continue
                factor = work[row][column]
                work[row] = [
                    current - factor * pivot_current
                    for current, pivot_current in zip(work[row], work[column], strict=True)
                ]
        return [work[index][-1] for index in range(size)]

    @staticmethod
    def _ensemble_weights(
        definition: PredictiveSystemDefinition,
        models: tuple[FittedModelState, ...],
    ) -> tuple[float, ...]:
        if definition.ensemble is None:
            if len(models) != 1:
                msg = "multiple models require an exact EnsembleDefinition"
                raise ValueError(msg)
            return (1.0,)
        ensemble = definition.ensemble
        if ensemble.fixed_weights is None:
            msg = "learned ensemble weights are not implemented; no fallback exists"
            raise ValueError(msg)
        if ensemble.method != "weighted_mean":
            msg = f"unsupported ensemble method {ensemble.method!r}"
            raise ValueError(msg)
        total = sum(ensemble.fixed_weights)
        if abs(total - 1.0) > 1e-12:
            msg = "fixed ensemble weights must sum to one"
            raise ValueError(msg)
        return ensemble.fixed_weights

    @staticmethod
    def _block(
        code: TrainingFailureCode,
        definition: PredictiveSystemDefinition,
        window: TrainingWindow,
        detail: str,
        provenance: tuple[str, ...],
        *,
        model: ModelDefinition | None = None,
    ) -> Never:
        raise TrainingBlocked(
            TrainingFailure.create(
                code,
                system_definition_id=definition.identity,
                model_definition_id=None if model is None else model.identity,
                training_window_id=window.window_id,
                detail=detail,
                provenance_refs=provenance,
            )
        )


class SystemPredictor:
    """Inference-only boundary over immutable fitted state and legal feature materializations."""

    def __init__(self, registry: FittedSystemRegistry) -> None:
        """Accept inference state only from the supplied training authority."""
        self._registry = registry

    def predict(
        self,
        definition: PredictiveSystemDefinition,
        fitted: FittedPredictiveSystem,
        information: InformationSet,
    ) -> PredictionRecord:
        """Materialize exact features and infer without any fit, update, or selection path."""
        self._registry.require_issued(fitted)
        self._validate(definition, fitted, information)
        series: list[FeatureSeries] = []
        for feature in definition.feature_set.members:
            states = tuple(
                FittedTransformState(
                    state_slot=state.state_slot,
                    feature_definition_id=state.feature_definition_id,
                    environment_id=definition.environment_id,
                    training_window_id=state.training_window_id,
                    information_set_id=information.information_set_id,
                    fitted_through=state.fitted_through,
                    parameters=state.parameters,
                    provenance_refs=(fitted.fit_record.fit_id, *state.provenance_refs),
                )
                for state in fitted.transforms
                if state.feature_definition_id == feature.identity
            )
            materialized = FeatureMaterializer().materialize(
                feature,
                FeatureCompiler().compile(feature),
                (information,),
                fitted_states=states,
            )
            series.append(materialized)
        exact_series = tuple(series)
        if any(
            item.status is not FeatureSeriesStatus.READY or len(item.values) != 1
            for item in exact_series
        ):
            msg = "formal materialization did not produce one READY value per feature"
            raise ValueError(msg)
        feature_values = tuple(item.values[0] for item in exact_series)
        first = feature_values[0]
        if any(
            item.decision_time != first.decision_time
            or item.dimensions != first.dimensions
            or item.information_set_id != first.information_set_id
            for item in feature_values
        ):
            msg = "feature dimensions, time, and information identity must align exactly"
            raise ValueError(msg)
        if any(
            item.status is not FeatureValueStatus.PRESENT or item.value is None
            for item in feature_values
        ):
            msg = "prediction cannot silently replace a missing feature value"
            raise ValueError(msg)
        vector = tuple(float(item.value) for item in feature_values if item.value is not None)
        predictions = tuple(self._infer_model(model, vector) for model in fitted.models)
        value = sum(
            weight * item for weight, item in zip(fitted.ensemble_weights, predictions, strict=True)
        )
        payload = {
            "fitted_system_id": fitted.fitted_system_id,
            "system_definition_id": definition.identity,
            "fit_record_id": fitted.fit_record.fit_id,
            "information_set_id": first.information_set_id,
            "feature_series_ids": tuple(item.series_id for item in exact_series),
            "feature_definition_ids": tuple(item.definition_id for item in exact_series),
            "decision_time": first.decision_time,
            "dimensions": first.dimensions,
            "target_id": definition.target.identity,
            "value": value,
            "environment_id": definition.environment_id,
            "provenance_refs": (fitted.fit_record.fit_id,),
            "status": DevelopmentStatus.DEVELOPMENT,
        }
        return PredictionRecord(
            prediction_id=stable_identity("prediction-record", payload),
            fitted_system_id=fitted.fitted_system_id,
            system_definition_id=definition.identity,
            fit_record_id=fitted.fit_record.fit_id,
            information_set_id=first.information_set_id,
            feature_series_ids=tuple(item.series_id for item in exact_series),
            feature_definition_ids=tuple(item.definition_id for item in exact_series),
            decision_time=first.decision_time,
            dimensions=first.dimensions,
            target_id=definition.target.identity,
            value=value,
            environment_id=definition.environment_id,
            provenance_refs=(fitted.fit_record.fit_id,),
            status=DevelopmentStatus.DEVELOPMENT,
        )

    @staticmethod
    def _validate(
        definition: PredictiveSystemDefinition,
        fitted: FittedPredictiveSystem,
        information: InformationSet,
    ) -> None:
        if fitted.system_definition_id != definition.identity:
            msg = "fitted state belongs to another system definition"
            raise ValueError(msg)
        if fitted.feature_set_id != definition.feature_set.identity:
            msg = "fitted state belongs to another exact FeatureSet"
            raise ValueError(msg)
        if fitted.target_id != definition.target.identity:
            msg = "fitted state belongs to another exact TargetDefinition"
            raise ValueError(msg)
        if fitted.environment_id != definition.environment_id:
            msg = "fitted state belongs to another environment"
            raise ValueError(msg)
        if information.environment_id != definition.environment_id:
            msg = "prediction information belongs to another environment"
            raise ValueError(msg)
        if information.decision_time < fitted.fit_record.fitted_through:
            msg = "prediction precedes the fitted training boundary"
            raise ValueError(msg)

    @staticmethod
    def _infer_model(model: FittedModelState, vector: tuple[float, ...]) -> float:
        expanded = SystemTrainer.expand_terms(vector, model.expansion_terms)
        if len(expanded) != len(model.coefficients):
            msg = "prediction dimensions differ from exact fitted model state"
            raise ValueError(msg)
        return model.intercept + sum(
            coefficient * value
            for coefficient, value in zip(model.coefficients, expanded, strict=True)
        )


class OutcomeRecorder:
    """Publish a target outcome only after declared completion and availability."""

    def record(
        self,
        prediction: PredictionRecord,
        target: TargetDefinition,
        *,
        catalog: DataCatalogSnapshot,
        decision_information: InformationSet,
        current_time: datetime,
    ) -> OutcomeRecord:
        if prediction.target_id != target.identity:
            msg = "prediction and outcome target identities differ"
            raise ValueError(msg)
        if target.maturity_policy is not MaturityPolicy.FULL_INTERVAL:
            msg = "initial outcome recorder supports only full-interval maturity"
            raise ValueError(msg)
        if catalog.environment_id != prediction.environment_id:
            msg = "outcome catalog and prediction environment identities differ"
            raise ValueError(msg)
        if decision_information.information_set_id != prediction.information_set_id:
            msg = "outcome construction requires the exact prediction InformationSet"
            raise ValueError(msg)
        outcome_information = InformationSetBuilder().build(
            catalog,
            decision_time=current_time,
            requested_fields=(target.field_ref,),
        )
        target_dimensions = prediction.dimensions
        label = construct_label(
            target,
            decision_time=prediction.decision_time,
            current_time=current_time,
            target_observations=outcome_information.for_field(target.field_ref),
            decision_information=decision_information,
            target_dimensions=target_dimensions,
            state_dimensions=tuple(
                (field_ref, target_dimensions) for field_ref in target.state_field_refs
            ),
        )
        if label is None:
            msg = "target outcome is not yet complete and legally available"
            raise ValueError(msg)
        completion_time = target.maturity_delay.apply(target.interval(prediction.decision_time)[1])
        provenance_refs = (
            catalog.identity,
            target.schema_provenance_ref,
            *target.provenance_refs,
        )
        payload = {
            "prediction_id": prediction.prediction_id,
            "target_id": target.identity,
            "value": label.value,
            "completion_time": completion_time,
            "available_at": label.matured_at,
            "recorded_at": current_time,
            "observation_ids": label.observation_ids,
            "environment_id": prediction.environment_id,
            "provenance_refs": provenance_refs,
        }
        return OutcomeRecord(
            outcome_id=stable_identity("outcome-record", payload),
            prediction_id=prediction.prediction_id,
            target_id=target.identity,
            value=label.value,
            completion_time=completion_time,
            available_at=label.matured_at,
            recorded_at=current_time,
            observation_ids=label.observation_ids,
            environment_id=prediction.environment_id,
            provenance_refs=provenance_refs,
        )
