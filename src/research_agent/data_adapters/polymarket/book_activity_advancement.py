"""Fixed development-only advancement standard for the LL-04 activity candidate."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from research_agent.data_adapters.polymarket.book_activity_policy import (
    ActivityGateLatencyScaledPolicy,
    derive_latency_scaled_activity_gate,
    ll04d_latency_scaled_primary_policy,
)

if TYPE_CHECKING:
    from research_agent.data_adapters.polymarket.book_activity_campaign import (
        ActivityGateCampaignMetric,
        ActivityGateCampaignPrimaryContrast,
        ActivityGateCampaignResult,
    )
    from research_agent.data_adapters.polymarket.book_activity_gate import (
        ActivityGateEconomicSummary,
        ActivityGateRivalContrast,
        ActivityGateRivalContrastKind,
        ActivityGateRivalPopulation,
    )

type ActivityGateDevelopmentStatus = Literal[
    "INSUFFICIENT_COVERAGE",
    "REJECT_DEVELOPMENT",
    "ADVANCE_TO_PAPER_EXECUTION_STUDY",
]
type ActivityGateDevelopmentClauseSection = Literal["COVERAGE", "ECONOMICS"]
type ActivityGateDevelopmentClauseComparison = Literal[
    "AT_LEAST",
    "AT_MOST",
    "STRICTLY_POSITIVE",
]
type ActivityGateDevelopmentClauseKind = Literal[
    "MINIMUM_CHRONOLOGICAL_BLOCKS",
    "MINIMUM_SCORED_BLOCK_FRACTION",
    "MINIMUM_JOINT_SCORABLE_ATTEMPTS",
    "MINIMUM_JOINT_SCORABLE_RETENTION",
    "MAXIMUM_JOINT_UNRESOLVED_ENTERED_FRACTION",
    "MINIMUM_POSITIVE_SCORED_BLOCK_FRACTION",
    "MAXIMUM_LARGEST_POSITIVE_BLOCK_SHARE",
    "POSITIVE_POOLED_PRIMARY_VALUE",
    "POSITIVE_BLOCK_MACRO_MEAN",
    "POSITIVE_EARLY_BLOCK_MEAN",
    "POSITIVE_LATE_BLOCK_MEAN",
    "POSITIVE_POOLED_JOINT_MINUS_QUIET_ONLY",
    "POSITIVE_POOLED_JOINT_MINUS_RECENT_ACTIVITY_ONLY",
]
type ActivityGateDevelopmentClauseValue = Decimal | int | None

_REQUIRED_PRIMARY_CONTRAST: ActivityGateCampaignPrimaryContrast = "JOINT_MINUS_COMPLETE_HISTORY"
_REQUIRED_PRIMARY_METRIC: ActivityGateCampaignMetric = "NET_TOUCH_PNL_PER_COLLATERAL_SECOND_CHANGE"
_CLAUSE_SPECS: tuple[
    tuple[
        ActivityGateDevelopmentClauseKind,
        ActivityGateDevelopmentClauseSection,
        ActivityGateDevelopmentClauseComparison,
    ],
    ...,
] = (
    ("MINIMUM_CHRONOLOGICAL_BLOCKS", "COVERAGE", "AT_LEAST"),
    ("MINIMUM_SCORED_BLOCK_FRACTION", "COVERAGE", "AT_LEAST"),
    ("MINIMUM_JOINT_SCORABLE_ATTEMPTS", "COVERAGE", "AT_LEAST"),
    ("MINIMUM_JOINT_SCORABLE_RETENTION", "COVERAGE", "AT_LEAST"),
    (
        "MAXIMUM_JOINT_UNRESOLVED_ENTERED_FRACTION",
        "COVERAGE",
        "AT_MOST",
    ),
    (
        "MINIMUM_POSITIVE_SCORED_BLOCK_FRACTION",
        "ECONOMICS",
        "AT_LEAST",
    ),
    ("MAXIMUM_LARGEST_POSITIVE_BLOCK_SHARE", "ECONOMICS", "AT_MOST"),
    ("POSITIVE_POOLED_PRIMARY_VALUE", "ECONOMICS", "STRICTLY_POSITIVE"),
    ("POSITIVE_BLOCK_MACRO_MEAN", "ECONOMICS", "STRICTLY_POSITIVE"),
    ("POSITIVE_EARLY_BLOCK_MEAN", "ECONOMICS", "STRICTLY_POSITIVE"),
    ("POSITIVE_LATE_BLOCK_MEAN", "ECONOMICS", "STRICTLY_POSITIVE"),
    (
        "POSITIVE_POOLED_JOINT_MINUS_QUIET_ONLY",
        "ECONOMICS",
        "STRICTLY_POSITIVE",
    ),
    (
        "POSITIVE_POOLED_JOINT_MINUS_RECENT_ACTIVITY_ONLY",
        "ECONOMICS",
        "STRICTLY_POSITIVE",
    ),
)


@dataclass(frozen=True, slots=True)
class ActivityGateDevelopmentStandard:
    """One exact development-only decision standard for the LL-04d candidate."""

    definition_id: str
    activity_policy: ActivityGateLatencyScaledPolicy
    required_primary_contrast_kind: ActivityGateCampaignPrimaryContrast
    required_primary_metric: ActivityGateCampaignMetric
    minimum_block_count: int
    minimum_scored_block_fraction: Decimal
    minimum_positive_scored_block_fraction: Decimal
    maximum_largest_positive_block_share: Decimal
    minimum_joint_scorable_attempt_count: int
    minimum_joint_scorable_retention_fraction: Decimal
    maximum_joint_unresolved_entered_fraction: Decimal

    def __post_init__(self) -> None:
        """Reject policy drift or incoherent coverage and stability thresholds."""
        fractions = (
            self.minimum_scored_block_fraction,
            self.minimum_positive_scored_block_fraction,
            self.maximum_largest_positive_block_share,
            self.minimum_joint_scorable_retention_fraction,
            self.maximum_joint_unresolved_entered_fraction,
        )
        if (
            self.definition_id != "ll04e-primary-development-v1"
            or self.activity_policy != ll04d_latency_scaled_primary_policy()
            or self.required_primary_contrast_kind != _REQUIRED_PRIMARY_CONTRAST
            or self.required_primary_metric != _REQUIRED_PRIMARY_METRIC
            or self.minimum_block_count <= 0
            or self.minimum_joint_scorable_attempt_count <= 0
            or any(not Decimal(0) <= value <= Decimal(1) for value in fractions)
            or self.minimum_scored_block_fraction <= 0
            or self.minimum_positive_scored_block_fraction <= 0
            or self.maximum_largest_positive_block_share <= 0
            or self.minimum_joint_scorable_retention_fraction <= 0
        ):
            message = "activity development standard requires valid fixed thresholds and identity"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ActivityGateDevelopmentClause:
    """One inspectable observed value and fixed comparison in the LL-04e standard."""

    clause_kind: ActivityGateDevelopmentClauseKind
    section: ActivityGateDevelopmentClauseSection
    comparison: ActivityGateDevelopmentClauseComparison
    observed_value: ActivityGateDevelopmentClauseValue
    threshold_value: Decimal | int
    passes: bool

    def __post_init__(self) -> None:
        """Keep the clause name, comparison direction, and result coherent."""
        expected_spec = next(
            (spec for spec in _CLAUSE_SPECS if spec[0] == self.clause_kind),
            None,
        )
        expected_passes = _compare_clause_value(
            self.observed_value,
            self.threshold_value,
            self.comparison,
        )
        if (
            expected_spec != (self.clause_kind, self.section, self.comparison)
            or (self.comparison == "STRICTLY_POSITIVE" and self.threshold_value != 0)
            or self.passes != expected_passes
        ):
            message = "activity development clause evidence is internally inconsistent"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ActivityGateDevelopmentAssessment:
    """Immutable LL-04e disposition recomputed from one exact LL-04c campaign."""

    standard: ActivityGateDevelopmentStandard
    campaign: ActivityGateCampaignResult
    clauses: tuple[ActivityGateDevelopmentClause, ...]
    coverage_passes: bool
    economics_passes: bool
    status: ActivityGateDevelopmentStatus

    def __post_init__(self) -> None:
        """Reject stored clauses or disposition detached from campaign evidence."""
        _validate_campaign_identity(self.campaign, self.standard)
        expected_clauses = _build_clauses(self.campaign, self.standard)
        expected_coverage = _section_passes(expected_clauses, "COVERAGE")
        expected_economics = _section_passes(expected_clauses, "ECONOMICS")
        expected_status = _development_status(
            coverage_passes=expected_coverage,
            economics_passes=expected_economics,
        )
        if (
            self.clauses != expected_clauses
            or self.coverage_passes != expected_coverage
            or self.economics_passes != expected_economics
            or self.status != expected_status
        ):
            message = "activity development assessment is detached from its exact campaign"
            raise ValueError(message)


def ll04e_primary_development_standard() -> ActivityGateDevelopmentStandard:
    """Return the one predeclared development standard for the LL-04d primary policy."""
    return ActivityGateDevelopmentStandard(
        definition_id="ll04e-primary-development-v1",
        activity_policy=ll04d_latency_scaled_primary_policy(),
        required_primary_contrast_kind=_REQUIRED_PRIMARY_CONTRAST,
        required_primary_metric=_REQUIRED_PRIMARY_METRIC,
        minimum_block_count=10,
        minimum_scored_block_fraction=Decimal("0.80"),
        minimum_positive_scored_block_fraction=Decimal("0.60"),
        maximum_largest_positive_block_share=Decimal("0.50"),
        minimum_joint_scorable_attempt_count=30,
        minimum_joint_scorable_retention_fraction=Decimal("0.25"),
        maximum_joint_unresolved_entered_fraction=Decimal("0.10"),
    )


def assess_activity_gate_development_campaign(
    campaign: ActivityGateCampaignResult,
    standard: ActivityGateDevelopmentStandard,
) -> ActivityGateDevelopmentAssessment:
    """Apply the fixed no-fit standard without granting validation or execution authority."""
    _validate_campaign_identity(campaign, standard)
    clauses = _build_clauses(campaign, standard)
    coverage_passes = _section_passes(clauses, "COVERAGE")
    economics_passes = _section_passes(clauses, "ECONOMICS")
    return ActivityGateDevelopmentAssessment(
        standard=standard,
        campaign=campaign,
        clauses=clauses,
        coverage_passes=coverage_passes,
        economics_passes=economics_passes,
        status=_development_status(
            coverage_passes=coverage_passes,
            economics_passes=economics_passes,
        ),
    )


def _validate_campaign_identity(
    campaign: ActivityGateCampaignResult,
    standard: ActivityGateDevelopmentStandard,
) -> None:
    definition = campaign.definition
    policy = standard.activity_policy
    if (
        definition.primary_contrast_kind != standard.required_primary_contrast_kind
        or definition.primary_metric != standard.required_primary_metric
    ):
        message = "activity development campaign primary identity differs from its standard"
        raise ValueError(message)
    for block in campaign.blocks:
        for ablation in block.block.ablations:
            comparison = ablation.comparison
            expected_gate = derive_latency_scaled_activity_gate(
                comparison.parent_strategy_definition,
                policy,
            )
            if comparison.definition != expected_gate:
                message = "activity campaign does not retain the exact LL-04d-derived gate identity"
                raise ValueError(message)


def _build_clauses(
    campaign: ActivityGateCampaignResult,
    standard: ActivityGateDevelopmentStandard,
) -> tuple[ActivityGateDevelopmentClause, ...]:
    stability = campaign.stability
    complete_history = _population_economics(campaign, "COMPLETE_HISTORY")
    joint = _population_economics(campaign, "JOINT")
    joint_minus_quiet = _pooled_contrast(campaign, "JOINT_MINUS_QUIET_ONLY")
    joint_minus_recent = _pooled_contrast(
        campaign,
        "JOINT_MINUS_RECENT_ACTIVITY_ONLY",
    )
    values: dict[ActivityGateDevelopmentClauseKind, ActivityGateDevelopmentClauseValue] = {
        "MINIMUM_CHRONOLOGICAL_BLOCKS": stability.block_count,
        "MINIMUM_SCORED_BLOCK_FRACTION": _fraction(
            stability.scored_block_count,
            stability.block_count,
        ),
        "MINIMUM_JOINT_SCORABLE_ATTEMPTS": joint.scorable_attempt_count,
        "MINIMUM_JOINT_SCORABLE_RETENTION": _fraction(
            joint.scorable_attempt_count,
            complete_history.scorable_attempt_count,
        ),
        "MAXIMUM_JOINT_UNRESOLVED_ENTERED_FRACTION": _fraction(
            joint.unresolved_entered_attempt_count,
            joint.entered_attempt_count,
        ),
        "MINIMUM_POSITIVE_SCORED_BLOCK_FRACTION": _fraction(
            stability.positive_block_count,
            stability.scored_block_count,
        ),
        "MAXIMUM_LARGEST_POSITIVE_BLOCK_SHARE": stability.largest_positive_block_share,
        "POSITIVE_POOLED_PRIMARY_VALUE": stability.pooled_primary_value,
        "POSITIVE_BLOCK_MACRO_MEAN": stability.block_macro_mean,
        "POSITIVE_EARLY_BLOCK_MEAN": stability.early_block_mean,
        "POSITIVE_LATE_BLOCK_MEAN": stability.late_block_mean,
        "POSITIVE_POOLED_JOINT_MINUS_QUIET_ONLY": (
            joint_minus_quiet.net_touch_pnl_per_collateral_second_change
        ),
        "POSITIVE_POOLED_JOINT_MINUS_RECENT_ACTIVITY_ONLY": (
            joint_minus_recent.net_touch_pnl_per_collateral_second_change
        ),
    }
    thresholds: dict[ActivityGateDevelopmentClauseKind, Decimal | int] = {
        "MINIMUM_CHRONOLOGICAL_BLOCKS": standard.minimum_block_count,
        "MINIMUM_SCORED_BLOCK_FRACTION": standard.minimum_scored_block_fraction,
        "MINIMUM_JOINT_SCORABLE_ATTEMPTS": standard.minimum_joint_scorable_attempt_count,
        "MINIMUM_JOINT_SCORABLE_RETENTION": (standard.minimum_joint_scorable_retention_fraction),
        "MAXIMUM_JOINT_UNRESOLVED_ENTERED_FRACTION": (
            standard.maximum_joint_unresolved_entered_fraction
        ),
        "MINIMUM_POSITIVE_SCORED_BLOCK_FRACTION": (standard.minimum_positive_scored_block_fraction),
        "MAXIMUM_LARGEST_POSITIVE_BLOCK_SHARE": (standard.maximum_largest_positive_block_share),
        "POSITIVE_POOLED_PRIMARY_VALUE": Decimal(0),
        "POSITIVE_BLOCK_MACRO_MEAN": Decimal(0),
        "POSITIVE_EARLY_BLOCK_MEAN": Decimal(0),
        "POSITIVE_LATE_BLOCK_MEAN": Decimal(0),
        "POSITIVE_POOLED_JOINT_MINUS_QUIET_ONLY": Decimal(0),
        "POSITIVE_POOLED_JOINT_MINUS_RECENT_ACTIVITY_ONLY": Decimal(0),
    }
    return tuple(
        _build_clause(
            clause_kind=clause_kind,
            section=section,
            comparison=comparison,
            observed_value=values[clause_kind],
            threshold_value=thresholds[clause_kind],
        )
        for clause_kind, section, comparison in _CLAUSE_SPECS
    )


def _build_clause(
    *,
    clause_kind: ActivityGateDevelopmentClauseKind,
    section: ActivityGateDevelopmentClauseSection,
    comparison: ActivityGateDevelopmentClauseComparison,
    observed_value: ActivityGateDevelopmentClauseValue,
    threshold_value: Decimal | int,
) -> ActivityGateDevelopmentClause:
    return ActivityGateDevelopmentClause(
        clause_kind=clause_kind,
        section=section,
        comparison=comparison,
        observed_value=observed_value,
        threshold_value=threshold_value,
        passes=_compare_clause_value(observed_value, threshold_value, comparison),
    )


def _compare_clause_value(
    observed_value: ActivityGateDevelopmentClauseValue,
    threshold_value: Decimal | int,
    comparison: ActivityGateDevelopmentClauseComparison,
) -> bool:
    if observed_value is None:
        return False
    if comparison == "AT_LEAST":
        return observed_value >= threshold_value
    if comparison == "AT_MOST":
        return observed_value <= threshold_value
    return observed_value > 0


def _population_economics(
    campaign: ActivityGateCampaignResult,
    population: ActivityGateRivalPopulation,
) -> ActivityGateEconomicSummary:
    matches = tuple(
        summary.economics
        for summary in campaign.pooled.populations
        if summary.population == population
    )
    if len(matches) != 1:
        message = "activity development campaign population is missing or duplicated"
        raise ValueError(message)
    return matches[0]


def _pooled_contrast(
    campaign: ActivityGateCampaignResult,
    contrast_kind: ActivityGateRivalContrastKind,
) -> ActivityGateRivalContrast:
    matches = tuple(
        contrast
        for contrast in campaign.pooled.contrasts
        if contrast.contrast_kind == contrast_kind
    )
    if len(matches) != 1:
        message = "activity development campaign contrast is missing or duplicated"
        raise ValueError(message)
    return matches[0]


def _fraction(numerator: int, denominator: int) -> Decimal | None:
    if denominator <= 0:
        return None
    return Decimal(numerator) / Decimal(denominator)


def _section_passes(
    clauses: tuple[ActivityGateDevelopmentClause, ...],
    section: ActivityGateDevelopmentClauseSection,
) -> bool:
    selected = tuple(clause for clause in clauses if clause.section == section)
    if not selected:
        message = "activity development assessment has an empty clause section"
        raise ValueError(message)
    return all(clause.passes for clause in selected)


def _development_status(
    *,
    coverage_passes: bool,
    economics_passes: bool,
) -> ActivityGateDevelopmentStatus:
    if not coverage_passes:
        return "INSUFFICIENT_COVERAGE"
    if not economics_passes:
        return "REJECT_DEVELOPMENT"
    return "ADVANCE_TO_PAPER_EXECUTION_STUDY"
