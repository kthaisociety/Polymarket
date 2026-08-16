"""Exact causal feature expressions and compilation without learned state."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from research_agent.data_foundation._identity import stable_identity

if TYPE_CHECKING:
    from research_agent.data_foundation.schema import FieldRef
    from research_agent.data_foundation.temporal import TemporalOffset
    from research_agent.formalization.definitions import FeatureDefinition


class ExpressionOperator(Enum):
    """Small exact operator vocabulary for the first deterministic evaluator."""

    FIELD = "field"
    CONSTANT = "constant"
    LAG = "lag"
    DIFFERENCE = "difference"
    ROLLING_MEAN = "rolling_mean"
    LOG = "log"
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
    STANDARDIZE = "standardize"


class OperationMode(Enum):
    """Whether evaluating an operation consumes learned state."""

    DETERMINISTIC = "deterministic"
    FITTED = "fitted"


@dataclass(frozen=True, slots=True)
class FeatureExpression:
    """An immutable, exact feature AST with no implicit operator defaults."""

    operator: ExpressionOperator
    operands: tuple[FeatureExpression, ...] = ()
    field_ref: FieldRef | None = None
    constant: float | None = None
    duration: TemporalOffset | None = None
    min_observations: int | None = None
    state_slot: str | None = None

    def __post_init__(self) -> None:  # noqa: C901, PLR0912
        """Reject incomplete or ambiguous operator shapes."""
        unary = {
            ExpressionOperator.LAG,
            ExpressionOperator.DIFFERENCE,
            ExpressionOperator.ROLLING_MEAN,
            ExpressionOperator.LOG,
            ExpressionOperator.STANDARDIZE,
        }
        binary = {
            ExpressionOperator.ADD,
            ExpressionOperator.SUBTRACT,
            ExpressionOperator.MULTIPLY,
            ExpressionOperator.DIVIDE,
        }
        if self.operator is ExpressionOperator.FIELD:
            valid = self.field_ref is not None and not self.operands
        elif self.operator is ExpressionOperator.CONSTANT:
            valid = self.constant is not None and not self.operands
        elif self.operator in unary:
            valid = len(self.operands) == 1
        elif self.operator in binary:
            binary_operand_count = 2
            valid = len(self.operands) == binary_operand_count
        else:
            valid = False
        if not valid:
            msg = f"invalid operand shape for {self.operator.value}"
            raise ValueError(msg)
        if self.operator in {ExpressionOperator.LAG, ExpressionOperator.DIFFERENCE}:
            if self.duration is None or not self.duration.is_positive:
                msg = f"{self.operator.value} requires a positive causal duration"
                raise ValueError(msg)
        elif self.operator is ExpressionOperator.ROLLING_MEAN:
            if (
                self.duration is None
                or not self.duration.is_positive
                or self.min_observations is None
                or self.min_observations < 1
            ):
                msg = "rolling_mean requires a positive window and observation count"
                raise ValueError(msg)
        elif self.duration is not None:
            msg = f"{self.operator.value} cannot carry a duration"
            raise ValueError(msg)
        if self.operator is ExpressionOperator.STANDARDIZE:
            if not self.state_slot:
                msg = "standardize requires an exact fitted-state slot"
                raise ValueError(msg)
        elif self.state_slot is not None:
            msg = f"{self.operator.value} cannot carry a fitted-state slot"
            raise ValueError(msg)

    @property
    def identity(self) -> str:
        """Return the content identity of the exact expression tree."""
        return stable_identity("feature-expression", self)

    @classmethod
    def field(cls, field_ref: FieldRef) -> FeatureExpression:
        """Read one exact semantic field."""
        return cls(ExpressionOperator.FIELD, field_ref=field_ref)

    @classmethod
    def constant_value(cls, value: float) -> FeatureExpression:
        """Create an explicit numeric constant."""
        return cls(ExpressionOperator.CONSTANT, constant=value)

    @classmethod
    def lag(cls, operand: FeatureExpression, duration: TemporalOffset) -> FeatureExpression:
        """Evaluate an operand at an earlier reference time."""
        return cls(ExpressionOperator.LAG, (operand,), duration=duration)

    @classmethod
    def difference(cls, operand: FeatureExpression, duration: TemporalOffset) -> FeatureExpression:
        """Subtract the causal lagged value from the current value."""
        return cls(ExpressionOperator.DIFFERENCE, (operand,), duration=duration)

    @classmethod
    def rolling_mean(
        cls,
        operand: FeatureExpression,
        window: TemporalOffset,
        *,
        min_observations: int,
    ) -> FeatureExpression:
        """Average causal evaluations over an exact trailing window."""
        return cls(
            ExpressionOperator.ROLLING_MEAN,
            (operand,),
            duration=window,
            min_observations=min_observations,
        )

    @classmethod
    def log(cls, operand: FeatureExpression) -> FeatureExpression:
        """Apply the natural logarithm with explicit invalid-domain failure."""
        return cls(ExpressionOperator.LOG, (operand,))

    @classmethod
    def add(cls, left: FeatureExpression, right: FeatureExpression) -> FeatureExpression:
        """Add two operands without reordering them."""
        return cls(ExpressionOperator.ADD, (left, right))

    @classmethod
    def subtract(cls, left: FeatureExpression, right: FeatureExpression) -> FeatureExpression:
        """Subtract the right operand from the left operand."""
        return cls(ExpressionOperator.SUBTRACT, (left, right))

    @classmethod
    def multiply(cls, left: FeatureExpression, right: FeatureExpression) -> FeatureExpression:
        """Multiply two operands."""
        return cls(ExpressionOperator.MULTIPLY, (left, right))

    @classmethod
    def divide(
        cls,
        numerator: FeatureExpression,
        denominator: FeatureExpression,
    ) -> FeatureExpression:
        """Divide with explicit zero-domain failure."""
        return cls(ExpressionOperator.DIVIDE, (numerator, denominator))

    @classmethod
    def standardize(
        cls,
        operand: FeatureExpression,
        *,
        state_slot: str,
    ) -> FeatureExpression:
        """Consume pre-fitted location/scale state without fitting it."""
        return cls(ExpressionOperator.STANDARDIZE, (operand,), state_slot=state_slot)

    def dependencies(self) -> tuple[FieldRef, ...]:
        """Return exact field dependencies in first-use order."""
        ordered: list[FieldRef] = []
        if self.field_ref is not None:
            ordered.append(self.field_ref)
        for operand in self.operands:
            ordered.extend(operand.dependencies())
        return tuple(dict.fromkeys(ordered))

    def fitted_slots(self) -> tuple[str, ...]:
        """Return exact fitted-state slots in first-use order."""
        ordered: list[str] = []
        if self.state_slot is not None:
            ordered.append(self.state_slot)
        for operand in self.operands:
            ordered.extend(operand.fitted_slots())
        return tuple(dict.fromkeys(ordered))


@dataclass(frozen=True, slots=True)
class CompiledOperation:
    """Traceable node metadata emitted by exact compilation."""

    path: tuple[int, ...]
    operator: ExpressionOperator
    mode: OperationMode


@dataclass(frozen=True, slots=True)
class CompiledFeatureExpression:
    """Exact executable representation tied to one definition and compiler version."""

    definition_id: str
    compiler_version: str
    expression: FeatureExpression
    operations: tuple[CompiledOperation, ...]

    @property
    def identity(self) -> str:
        """Return the stable identity of compilation inputs and output graph."""
        return stable_identity("compiled-feature", self)


class FeatureCompiler:
    """Validate and translate a definition without fitting or semantic fallback."""

    VERSION = "exact-expression-compiler-v1"

    def compile(self, definition: FeatureDefinition) -> CompiledFeatureExpression:
        """Compile only when expression dependencies and fitted slots match exactly."""
        if definition.expression.dependencies() != definition.dependencies:
            msg = "expression dependencies must exactly match FeatureDefinition dependencies"
            raise ValueError(msg)
        declared_slots = tuple(slot for slot, _ in definition.fitted_state_procedures)
        if definition.expression.fitted_slots() != declared_slots:
            msg = "fitted expression slots must exactly match declared fitting procedures"
            raise ValueError(msg)
        operations: list[CompiledOperation] = []
        self._walk(definition.expression, (), operations)
        return CompiledFeatureExpression(
            definition_id=definition.identity,
            compiler_version=self.VERSION,
            expression=definition.expression,
            operations=tuple(operations),
        )

    def _walk(
        self,
        expression: FeatureExpression,
        path: tuple[int, ...],
        operations: list[CompiledOperation],
    ) -> None:
        mode = (
            OperationMode.FITTED
            if expression.operator is ExpressionOperator.STANDARDIZE
            else OperationMode.DETERMINISTIC
        )
        operations.append(CompiledOperation(path, expression.operator, mode))
        for index, operand in enumerate(expression.operands):
            self._walk(operand, (*path, index), operations)
