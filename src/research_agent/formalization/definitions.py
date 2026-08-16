"""Immutable scientific definitions assembled before any model fitting."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from research_agent.data_foundation._identity import require_aware, stable_identity

if TYPE_CHECKING:
    from datetime import datetime

    from research_agent.data_foundation.schema import FieldRef
    from research_agent.data_foundation.targets import TargetDefinition
    from research_agent.data_foundation.temporal import TemporalOffset
    from research_agent.formalization.expressions import FeatureExpression

type ParameterValue = str | int | float | bool | None


class FeatureAlignment(Enum):
    """Declared reference-time alignment within an already legal InformationSet."""

    EXACT = "exact"
    LATEST_AT_OR_BEFORE = "latest_at_or_before"


class HistoryKind(Enum):
    """Whether available history grows or is truncated to a fixed width."""

    EXPANDING = "expanding"
    FIXED_WIDTH = "fixed_width"


class FailureAction(Enum):
    """Explicit response to an expected feature-value failure."""

    FAIL = "fail"
    RETURN_MISSING = "return_missing"


@dataclass(frozen=True, slots=True)
class TemporalMapping:
    """How a decision time anchors field reads."""

    alignment: FeatureAlignment
    decision_offset: TemporalOffset

    def __post_init__(self) -> None:
        """Forbid a feature anchor after the decision it claims to represent."""
        if self.decision_offset.is_positive:
            msg = "feature temporal mapping cannot anchor after decision time"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class HistorySemantics:
    """Warm-up, initialization, and finite-history behavior."""

    kind: HistoryKind
    warm_up: TemporalOffset
    fixed_width: TemporalOffset | None
    initialization: str
    truncation: str

    def __post_init__(self) -> None:
        """Require every behavior that affects early or truncated values."""
        if self.warm_up.is_negative or not self.initialization or not self.truncation:
            msg = "history warm-up, initialization, and truncation must be explicit"
            raise ValueError(msg)
        if self.kind is HistoryKind.EXPANDING and self.fixed_width is not None:
            msg = "expanding history cannot declare a fixed width"
            raise ValueError(msg)
        if self.kind is HistoryKind.FIXED_WIDTH and (
            self.fixed_width is None or not self.fixed_width.is_positive
        ):
            msg = "fixed-width history requires a positive width"
            raise ValueError(msg)
        if self.fixed_width is not None and self.warm_up.compare_magnitude(self.fixed_width) > 0:
            msg = "feature warm-up cannot exceed its fixed history width"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class FeatureDefinition:
    """Stable meaning of a causal mapping from legal data to one feature value."""

    name: str
    version: int
    parent_definition_id: str | None
    environment_id: str
    dependencies: tuple[FieldRef, ...]
    expression: FeatureExpression
    temporal_mapping: TemporalMapping
    history: HistorySemantics
    output_data_type: str
    output_units: str
    dimensions: tuple[tuple[str, str], ...]
    missing_input: FailureAction
    invalid_domain: FailureAction
    insufficiency: FailureAction
    failure: str
    hypothesis: str
    information_intent: str
    fitted_state_procedures: tuple[tuple[str, str], ...]
    evidence_refs: tuple[str, ...]
    candidate_ancestry: tuple[str, ...]
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        """Require complete identity, ancestry, and exact semantic dependencies."""
        required = (
            self.name,
            self.environment_id,
            self.output_data_type,
            self.output_units,
            self.failure,
            self.hypothesis,
            self.information_intent,
        )
        if self.version < 1 or not all(required):
            msg = "feature scientific meaning and version must be explicit"
            raise ValueError(msg)
        if (self.version == 1) != (self.parent_definition_id is None):
            msg = "feature versions after one require exact parent lineage"
            raise ValueError(msg)
        if not self.dependencies or len(set(self.dependencies)) != len(self.dependencies):
            msg = "feature dependencies must be non-empty and exact"
            raise ValueError(msg)
        if any(item.environment_id != self.environment_id for item in self.dependencies):
            msg = "feature dependencies cross environment identity"
            raise ValueError(msg)
        dimension_names = tuple(name for name, _ in self.dimensions)
        if len(set(dimension_names)) != len(dimension_names):
            msg = "feature dimension names must be unique"
            raise ValueError(msg)
        slots = tuple(slot for slot, _ in self.fitted_state_procedures)
        procedures = tuple(procedure for _, procedure in self.fitted_state_procedures)
        if len(set(slots)) != len(slots) or any(not item for item in (*slots, *procedures)):
            msg = "fitted-state procedures require unique exact slots and references"
            raise ValueError(msg)
        if not self.evidence_refs or not self.candidate_ancestry or not self.provenance_refs:
            msg = "feature evidence ancestry and provenance must be explicit"
            raise ValueError(msg)

    @property
    def identity(self) -> str:
        """Return the identity of every material scientific dimension."""
        return stable_identity("feature-definition", self)


@dataclass(frozen=True, slots=True)
class FeatureSet:
    """Exact ordered feature-definition membership with selection ancestry."""

    name: str
    version: int
    parent_feature_set_id: str | None
    environment_id: str
    members: tuple[FeatureDefinition, ...]
    selection_ancestry: tuple[str, ...]
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        """Reject latest resolution, ambiguous names, and non-definition artifacts."""
        if self.version < 1 or not self.name or not self.environment_id:
            msg = "feature-set identity and version must be explicit"
            raise ValueError(msg)
        if (self.version == 1) != (self.parent_feature_set_id is None):
            msg = "feature-set versions after one require exact parent lineage"
            raise ValueError(msg)
        if not self.members:
            msg = "FeatureSet requires at least one FeatureDefinition"
            raise ValueError(msg)
        if any(
            not isinstance(member, FeatureDefinition)  # pyright: ignore[reportUnnecessaryIsInstance]
            for member in self.members
        ):
            msg = "FeatureSet members must be exact FeatureDefinition objects"
            raise TypeError(msg)
        if any(member.environment_id != self.environment_id for member in self.members):
            msg = "FeatureSet members cross environment identity"
            raise ValueError(msg)
        names = tuple(member.name for member in self.members)
        identities = tuple(member.identity for member in self.members)
        if len(set(names)) != len(names):
            msg = "FeatureSet contains a duplicate output name"
            raise ValueError(msg)
        if len(set(identities)) != len(identities):
            msg = "FeatureSet contains a duplicate definition identity"
            raise ValueError(msg)
        if not self.selection_ancestry or not self.provenance_refs:
            msg = "FeatureSet selection ancestry and provenance must be explicit"
            raise ValueError(msg)

    @property
    def identity(self) -> str:
        """Bind exact ordered member versions and selection history."""
        return stable_identity("feature-set", self)


@dataclass(frozen=True, slots=True)
class ModelDefinition:
    """A reproducible unfitted model recipe."""

    name: str
    version: int
    parent_definition_id: str | None
    environment_id: str
    algorithm: str
    hyperparameters: tuple[tuple[str, ParameterValue], ...]
    preprocessing_refs: tuple[str, ...]
    selection_procedure_ref: str
    randomness_policy: str
    training_requirement_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    candidate_ancestry: tuple[str, ...]
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        """Forbid an incomplete recipe or ambiguous parameter names."""
        required = (
            self.name,
            self.environment_id,
            self.algorithm,
            self.selection_procedure_ref,
            self.randomness_policy,
        )
        if self.version < 1 or not all(required):
            msg = "model recipe and version must be explicit"
            raise ValueError(msg)
        if (self.version == 1) != (self.parent_definition_id is None):
            msg = "model versions after one require exact parent lineage"
            raise ValueError(msg)
        parameter_names = tuple(name for name, _ in self.hyperparameters)
        if len(set(parameter_names)) != len(parameter_names) or any(
            not name for name in parameter_names
        ):
            msg = "model hyperparameter names must be unique and explicit"
            raise ValueError(msg)
        if (
            not self.training_requirement_refs
            or not self.evidence_refs
            or not self.candidate_ancestry
            or not self.provenance_refs
        ):
            msg = "model training, evidence ancestry, and provenance must be explicit"
            raise ValueError(msg)

    @property
    def identity(self) -> str:
        """Return the exact unfitted recipe identity."""
        return stable_identity("model-definition", self)


@dataclass(frozen=True, slots=True)
class FittedModel:
    """Immutable learned state kept distinct from a ModelDefinition."""

    model_definition_id: str
    training_window_id: str
    environment_id: str
    fitted_through: datetime
    fitted_artifact_ref: str
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        """Require an exact training boundary and learned artifact."""
        require_aware(self.fitted_through, "fitted_through")
        if not all(
            (
                self.model_definition_id,
                self.training_window_id,
                self.environment_id,
                self.fitted_artifact_ref,
                self.provenance_refs,
            )
        ):
            msg = "fitted model requires definition, window, artifact, and provenance"
            raise ValueError(msg)

    @property
    def identity(self) -> str:
        """Return learned-state identity including its training window."""
        return stable_identity("fitted-model", self)


@dataclass(frozen=True, slots=True)
class EnsembleDefinition:
    """Exact model membership and fixed or learned combination procedure."""

    name: str
    version: int
    parent_definition_id: str | None
    environment_id: str
    members: tuple[ModelDefinition, ...]
    method: str
    fixed_weights: tuple[float, ...] | None
    weight_learning_procedure_ref: str | None
    evidence_refs: tuple[str, ...]
    candidate_ancestry: tuple[str, ...]
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        """Require explicit weight ownership and exact member versions."""
        if self.version < 1 or not all((self.name, self.environment_id, self.method)):
            msg = "ensemble identity and method must be explicit"
            raise ValueError(msg)
        if (self.version == 1) != (self.parent_definition_id is None):
            msg = "ensemble versions after one require exact parent lineage"
            raise ValueError(msg)
        if not self.members or any(
            not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
                member, ModelDefinition
            )
            for member in self.members
        ):
            msg = "ensemble members must be exact ModelDefinitions"
            raise TypeError(msg)
        member_ids = tuple(member.identity for member in self.members)
        if len(set(member_ids)) != len(member_ids):
            msg = "ensemble contains duplicate model identities"
            raise ValueError(msg)
        if any(member.environment_id != self.environment_id for member in self.members):
            msg = "ensemble members cross environment identity"
            raise ValueError(msg)
        fixed = self.fixed_weights is not None
        learned = self.weight_learning_procedure_ref is not None
        if fixed == learned:
            msg = "ensemble requires exactly one fixed or learned weight procedure"
            raise ValueError(msg)
        if self.fixed_weights is not None and len(self.fixed_weights) != len(self.members):
            msg = "fixed ensemble weights must match exact membership"
            raise ValueError(msg)
        if not self.evidence_refs or not self.candidate_ancestry or not self.provenance_refs:
            msg = "ensemble evidence ancestry and provenance must be explicit"
            raise ValueError(msg)

    @property
    def identity(self) -> str:
        """Return the exact unfitted ensemble recipe identity."""
        return stable_identity("ensemble-definition", self)


@dataclass(frozen=True, slots=True)
class PredictiveSystemDefinition:
    """Complete unfitted candidate recipe binding every material protocol identity."""

    name: str
    version: int
    parent_system_id: str | None
    environment_id: str
    target: TargetDefinition
    feature_set: FeatureSet
    models: tuple[ModelDefinition, ...]
    ensemble: EnsembleDefinition | None
    data_protocol_id: str
    training_protocol_id: str
    evaluation_protocol_id: str
    evidence_refs: tuple[str, ...]
    candidate_ancestry: tuple[str, ...]
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:  # noqa: C901
        """Bind exact components without fitting, freezing, or latest resolution."""
        required = (
            self.name,
            self.environment_id,
            self.data_protocol_id,
            self.training_protocol_id,
            self.evaluation_protocol_id,
        )
        if self.version < 1 or not all(required):
            msg = "predictive-system identity and protocols must be explicit"
            raise ValueError(msg)
        if (self.version == 1) != (self.parent_system_id is None):
            msg = "system versions after one require exact parent lineage"
            raise ValueError(msg)
        if self.target.environment_id != self.environment_id:
            msg = "target and system environment identities differ"
            raise ValueError(msg)
        if self.feature_set.environment_id != self.environment_id:
            msg = "feature set and system environment identities differ"
            raise ValueError(msg)
        if not self.models or any(
            not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
                model, ModelDefinition
            )
            for model in self.models
        ):
            msg = "predictive system requires exact ModelDefinitions"
            raise TypeError(msg)
        model_ids = tuple(model.identity for model in self.models)
        if len(set(model_ids)) != len(model_ids):
            msg = "predictive system contains duplicate model identities"
            raise ValueError(msg)
        if any(model.environment_id != self.environment_id for model in self.models):
            msg = "model and system environment identities differ"
            raise ValueError(msg)
        if self.ensemble is not None:
            if self.ensemble.environment_id != self.environment_id:
                msg = "ensemble and system environment identities differ"
                raise ValueError(msg)
            ensemble_ids = tuple(member.identity for member in self.ensemble.members)
            if ensemble_ids != model_ids:
                msg = "ensemble membership must exactly match system model order"
                raise ValueError(msg)
        if not self.evidence_refs or not self.candidate_ancestry or not self.provenance_refs:
            msg = "system evidence ancestry and provenance must be explicit"
            raise ValueError(msg)

    @property
    def identity(self) -> str:
        """Return the complete candidate-system identity."""
        return stable_identity("predictive-system-definition", self)
