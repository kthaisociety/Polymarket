"""Exact predeclared scenario, measurement, and promotion definitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import TYPE_CHECKING

from research_agent.data_foundation._identity import require_aware, stable_identity

if TYPE_CHECKING:
    from datetime import datetime

    from research_agent.data_foundation.samples import MissingnessPolicy, SampleKey
    from research_agent.data_foundation.windows import TrainingWindowPolicy


class ScenarioKind(Enum):
    """Scientific interpretation of an evaluation world."""

    HISTORICAL_WALK_FORWARD = "historical_walk_forward"
    ALTERNATIVE_TEMPORAL_PATH = "alternative_temporal_path"
    SYNTHETIC_COUNTERFACTUAL = "synthetic_counterfactual"


@dataclass(frozen=True, slots=True)
class EvaluationScenario:
    """Immutable execution world fixed before protected contents are disclosed."""

    name: str
    version: int
    kind: ScenarioKind
    decision_sample_keys: tuple[SampleKey, ...]
    training_candidate_keys: tuple[SampleKey, ...]
    outcome_recorded_at: datetime
    training_protocol_ref: str
    window_policy: TrainingWindowPolicy
    missingness_policy: MissingnessPolicy
    interpretation: str
    environment_ref: str
    data_protocol_ref: str
    provenance_refs: tuple[str, ...]
    generator_ref: str | None = None
    random_seed: int | None = None

    def __post_init__(self) -> None:
        """Reject ambiguous time order, world identity, or protocol ownership."""
        require_aware(self.outcome_recorded_at, "outcome_recorded_at")
        if self.version < 1 or not all(
            (
                self.name,
                self.training_protocol_ref,
                self.interpretation,
                self.environment_ref,
                self.data_protocol_ref,
                self.provenance_refs,
            )
        ):
            msg = "scenario identity, protocols, interpretation, and provenance are required"
            raise ValueError(msg)
        if not self.decision_sample_keys:
            msg = "scenario requires explicit decision times"
            raise ValueError(msg)
        ordered_keys = tuple(
            sorted(
                self.decision_sample_keys, key=lambda item: (item.decision_time, item.dimensions)
            )
        )
        if self.decision_sample_keys != ordered_keys or len(set(self.decision_sample_keys)) != len(
            self.decision_sample_keys
        ):
            msg = "scenario sample keys must be unique and ordered by time and dimensions"
            raise ValueError(msg)
        ordered_training = tuple(
            sorted(
                self.training_candidate_keys,
                key=lambda item: (item.decision_time, item.dimensions),
            )
        )
        if self.training_candidate_keys != ordered_training or len(
            set(self.training_candidate_keys)
        ) != len(self.training_candidate_keys):
            msg = "scenario training candidates must be unique and deterministically ordered"
            raise ValueError(msg)
        if self.outcome_recorded_at < self.decision_sample_keys[-1].decision_time:
            msg = "scenario outcome recording boundary cannot precede its decisions"
            raise ValueError(msg)
        synthetic = self.kind is ScenarioKind.SYNTHETIC_COUNTERFACTUAL
        if synthetic != (self.generator_ref is not None):
            msg = "synthetic scenarios require a generator; historical worlds cannot claim one"
            raise ValueError(msg)
        if self.kind is ScenarioKind.HISTORICAL_WALK_FORWARD and self.random_seed is not None:
            msg = "literal historical walk-forward scenarios do not consume a generator seed"
            raise ValueError(msg)

    @property
    def identity(self) -> str:
        """Bind every scenario dimension that changes evidence meaning."""
        return stable_identity("evaluation-scenario", self)

    @property
    def decision_times_ref(self) -> str:
        """Return the exact identity of the declared decision sequence."""
        return stable_identity(
            "decision-times",
            self.decision_sample_keys,
        )


class MetricName(Enum):
    """Initial task-neutral stdlib measurements."""

    MSE = "mse"
    MAE = "mae"
    COVERAGE = "coverage"
    FAILURE_RATE = "failure_rate"


@dataclass(frozen=True, slots=True)
class EvaluationSpec:
    """Exact measurement plan; it contains no training or selection callback."""

    name: str
    version: int
    protocol_ref: str
    metric_names: tuple[MetricName, ...]
    rolling_window: int
    include_per_time: bool
    include_dimension_views: bool
    include_stability: bool
    include_concentration: bool
    benchmark_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        """Require an explicit non-duplicated measurement plan."""
        if self.version < 1 or not all((self.name, self.protocol_ref, self.provenance_refs)):
            msg = "evaluation identity, protocol, and provenance are required"
            raise ValueError(msg)
        if not self.metric_names or len(set(self.metric_names)) != len(self.metric_names):
            msg = "evaluation metrics must be explicit and unique"
            raise ValueError(msg)
        if self.rolling_window < 1:
            msg = "rolling_window must be positive"
            raise ValueError(msg)

    @property
    def identity(self) -> str:
        """Ensure metric and view changes create a new evaluation identity."""
        return stable_identity("evaluation-spec", self)


class CriterionComparison(Enum):
    """Direction of one exact promotion threshold."""

    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"


@dataclass(frozen=True, slots=True)
class MetricCriterion:
    """One predeclared metric threshold."""

    metric: MetricName
    comparison: CriterionComparison
    threshold: float

    def __post_init__(self) -> None:
        """Reject NaN and infinity before a standard can be predeclared."""
        if not isfinite(self.threshold):
            msg = "promotion metric thresholds must be finite"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class PromotionStandard:
    """Exact binary scientific standard owned by independent validation authority."""

    name: str
    version: int
    evaluation_spec_id: str
    criteria: tuple[MetricCriterion, ...]
    maximum_stability_stddev: float | None
    maximum_error_concentration: float | None
    required_scenario_kind: ScenarioKind
    authority_policy_ref: str
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        """Reject incomplete standards and duplicate or impossible criteria."""
        if self.version < 1 or not all(
            (
                self.name,
                self.evaluation_spec_id,
                self.authority_policy_ref,
                self.provenance_refs,
            )
        ):
            msg = "promotion standard identity and provenance are required"
            raise ValueError(msg)
        metrics = tuple(item.metric for item in self.criteria)
        if not metrics or len(set(metrics)) != len(metrics):
            msg = "promotion criteria must be explicit and unique by metric"
            raise ValueError(msg)
        for threshold in (
            self.maximum_stability_stddev,
            self.maximum_error_concentration,
        ):
            if threshold is not None and (not isfinite(threshold) or threshold < 0):
                msg = "promotion robustness thresholds must be finite and non-negative"
                raise ValueError(msg)

    @property
    def identity(self) -> str:
        """Ensure every threshold or authority-policy change gets a new identity."""
        return stable_identity("promotion-standard", self)


@dataclass(frozen=True, slots=True)
class ClaimDefinition:
    """Exact bounded scientific claim fixed before protected evidence is seen."""

    name: str
    version: int
    statement: str
    system_id: str
    target_id: str
    scope_limitations: tuple[str, ...]
    required_caveats: tuple[str, ...]
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        """Require bounded substance, identity, and provenance."""
        if self.version < 1 or not all(
            (
                self.name,
                self.statement,
                self.system_id,
                self.target_id,
                self.scope_limitations,
                self.required_caveats,
                self.provenance_refs,
            )
        ):
            msg = "claim substance, scope, caveats, identity, and provenance are required"
            raise ValueError(msg)

    @property
    def identity(self) -> str:
        """Ensure any wording or scope change creates a new predeclared claim."""
        return stable_identity("claim-definition", self)


__all__ = [
    "ClaimDefinition",
    "CriterionComparison",
    "EvaluationScenario",
    "EvaluationSpec",
    "MetricCriterion",
    "MetricName",
    "PromotionStandard",
    "ScenarioKind",
]
