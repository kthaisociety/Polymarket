"""Chronological multi-market campaign diagnostics for the LL-04 activity gate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from itertools import pairwise
from typing import TYPE_CHECKING, Literal

from research_agent.data_adapters.polymarket.book_activity_gate import (
    ACTIVITY_GATE_RIVAL_CONTRASTS,
    ACTIVITY_GATE_RIVAL_POPULATIONS,
    ActivityGateAttempt,
    ActivityGateEconomicSummary,
    ActivityGateParentDefinition,
    ActivityGateParentKind,
    ActivityGateRivalAblation,
    ActivityGateRivalContrast,
    ActivityGateRivalContrastKind,
    ActivityGateRivalPopulation,
    contrast_activity_gate_economics,
    summarize_activity_gate_attempts,
)
from research_agent.data_adapters.polymarket.low_latency import PostJumpReversalDefinition

if TYPE_CHECKING:
    from research_agent.data_adapters.polymarket.book_corpus import BookLeg

type ActivityGateCampaignMetric = Literal[
    "NET_TOUCH_PNL_PER_SHARE_MEAN_CHANGE",
    "NET_TOUCH_PNL_PER_COLLATERAL_SECOND_CHANGE",
    "DIAGNOSTIC_DISPLAYED_NET_PER_COLLATERAL_SECOND_CHANGE",
]
type ActivityGateCampaignPrimaryContrast = Literal[
    "JOINT_MINUS_COMPLETE_HISTORY",
    "JOINT_MINUS_QUIET_ONLY",
    "JOINT_MINUS_RECENT_ACTIVITY_ONLY",
]
type ActivityGateParentRecipeValue = Decimal | timedelta | int | None

_CAMPAIGN_METRICS: tuple[ActivityGateCampaignMetric, ...] = (
    "NET_TOUCH_PNL_PER_SHARE_MEAN_CHANGE",
    "NET_TOUCH_PNL_PER_COLLATERAL_SECOND_CHANGE",
    "DIAGNOSTIC_DISPLAYED_NET_PER_COLLATERAL_SECOND_CHANGE",
)
_CAMPAIGN_PRIMARY_CONTRASTS: tuple[ActivityGateCampaignPrimaryContrast, ...] = (
    "JOINT_MINUS_COMPLETE_HISTORY",
    "JOINT_MINUS_QUIET_ONLY",
    "JOINT_MINUS_RECENT_ACTIVITY_ONLY",
)


def _require_aware(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        message = f"{field} must be timezone-aware"
        raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ActivityGateParentRecipe:
    """Market-independent scientific parameters of one H3 or H5 parent policy."""

    parent_strategy_kind: ActivityGateParentKind
    parameters: tuple[tuple[str, ActivityGateParentRecipeValue], ...]

    def __post_init__(self) -> None:
        """Require a nonempty unique canonical parameter identity."""
        names = tuple(name for name, _ in self.parameters)
        if (
            self.parent_strategy_kind not in ("LL03_POST_JUMP_REVERSAL", "LL05_DEPTH_IMBALANCE")
            or not self.parameters
            or any(not name for name in names)
            or len(set(names)) != len(names)
        ):
            message = "activity gate parent recipe requires exact unique parameters"
            raise ValueError(message)


def activity_gate_parent_recipe(
    definition: ActivityGateParentDefinition,
) -> ActivityGateParentRecipe:
    """Remove only market/scope identity from one exact H3 or H5 definition."""
    if isinstance(definition, PostJumpReversalDefinition):
        return ActivityGateParentRecipe(
            parent_strategy_kind="LL03_POST_JUMP_REVERSAL",
            parameters=(
                ("minimum_midpoint_shock", definition.minimum_midpoint_shock),
                ("maximum_shock_gap", definition.maximum_shock_gap),
                ("action_delay", definition.action_delay),
                ("maximum_quote_age", definition.maximum_quote_age),
                ("reversal_distance", definition.reversal_distance),
                ("continuation_distance", definition.continuation_distance),
                ("maximum_holding_period", definition.maximum_holding_period),
                ("minimum_entry_quantity", definition.minimum_entry_quantity),
                ("round_trip_cost_per_share", definition.round_trip_cost_per_share),
            ),
        )
    return ActivityGateParentRecipe(
        parent_strategy_kind="LL05_DEPTH_IMBALANCE",
        parameters=(
            ("entry_imbalance_threshold", definition.entry_imbalance_threshold),
            ("exit_imbalance_threshold", definition.exit_imbalance_threshold),
            ("maximum_spread", definition.maximum_spread),
            ("minimum_total_depth", definition.minimum_total_depth),
            ("minimum_reference_midpoint", definition.minimum_reference_midpoint),
            ("maximum_reference_midpoint", definition.maximum_reference_midpoint),
            ("action_delay", definition.action_delay),
            ("maximum_quote_age", definition.maximum_quote_age),
            ("take_profit_distance", definition.take_profit_distance),
            ("stop_loss_distance", definition.stop_loss_distance),
            ("maximum_holding_period", definition.maximum_holding_period),
            ("minimum_entry_quantity", definition.minimum_entry_quantity),
            ("round_trip_cost_per_share", definition.round_trip_cost_per_share),
            ("depth_levels", definition.depth_levels),
        ),
    )


@dataclass(frozen=True, slots=True)
class ActivityGateCampaignDefinition:
    """Exact fixed policy and primary diagnostic for one LL-04c campaign."""

    definition_id: str
    parent_strategy_kind: ActivityGateParentKind
    parent_strategy_recipe: ActivityGateParentRecipe
    scope_authority_ref: str
    recent_window: timedelta
    maximum_quiet_duration: timedelta
    minimum_recent_source_event_count: int
    primary_contrast_kind: ActivityGateCampaignPrimaryContrast
    primary_metric: ActivityGateCampaignMetric

    def __post_init__(self) -> None:
        """Reject implicit policy, parent, scope, contrast, or metric semantics."""
        if (
            not self.definition_id
            or self.parent_strategy_kind not in ("LL03_POST_JUMP_REVERSAL", "LL05_DEPTH_IMBALANCE")
            or self.parent_strategy_recipe.parent_strategy_kind != self.parent_strategy_kind
            or not self.scope_authority_ref
            or self.recent_window <= timedelta(0)
            or self.maximum_quiet_duration <= timedelta(0)
            or self.minimum_recent_source_event_count < 0
            or self.primary_contrast_kind not in _CAMPAIGN_PRIMARY_CONTRASTS
            or self.primary_metric not in _CAMPAIGN_METRICS
        ):
            message = "activity gate campaign requires exact fixed policy and metric identity"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ActivityGateCampaignBlock:
    """One explicit half-open collector interval and its LL-04b ablations."""

    block_id: str
    start_at: datetime
    end_at: datetime
    ablations: tuple[ActivityGateRivalAblation, ...]

    def __post_init__(self) -> None:
        """Require an aware nonempty half-open campaign block."""
        _require_aware(self.start_at, "block start_at")
        _require_aware(self.end_at, "block end_at")
        if not self.block_id or self.start_at >= self.end_at or not self.ablations:
            message = "activity gate campaign block requires identity, coverage, and ablations"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ActivityGateCampaignPopulationSummary:
    """Pooled exact economics for one rival population over campaign inputs."""

    population: ActivityGateRivalPopulation
    ablation_count: int
    market_count: int
    source_snapshot_uris: tuple[str, ...]
    economics: ActivityGateEconomicSummary

    def __post_init__(self) -> None:
        """Keep input coverage and population economics explicit."""
        if (
            self.population not in ACTIVITY_GATE_RIVAL_POPULATIONS
            or self.ablation_count <= 0
            or self.market_count <= 0
            or not self.source_snapshot_uris
            or self.source_snapshot_uris != tuple(sorted(set(self.source_snapshot_uris)))
        ):
            message = "activity gate campaign population has incoherent input coverage"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ActivityGateCampaignAggregate:
    """Five population summaries and six contrasts for one campaign slice."""

    populations: tuple[ActivityGateCampaignPopulationSummary, ...]
    contrasts: tuple[ActivityGateRivalContrast, ...]

    def __post_init__(self) -> None:
        """Require every predeclared population and contrast in canonical order."""
        if (
            tuple(population.population for population in self.populations)
            != ACTIVITY_GATE_RIVAL_POPULATIONS
            or tuple(contrast.contrast_kind for contrast in self.contrasts)
            != tuple(kind for kind, _, _ in ACTIVITY_GATE_RIVAL_CONTRASTS)
            or len({population.ablation_count for population in self.populations}) != 1
            or len({population.market_count for population in self.populations}) != 1
            or len({population.source_snapshot_uris for population in self.populations}) != 1
        ):
            message = "activity gate campaign aggregate is incomplete or out of order"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ActivityGateCampaignBlockResult:
    """Immutable aggregate for one exact chronological block."""

    block: ActivityGateCampaignBlock
    aggregate: ActivityGateCampaignAggregate

    def __post_init__(self) -> None:
        """Reject stored block evidence that differs from its exact ablations."""
        if self.aggregate != _aggregate_ablations(self.block.ablations):
            message = "activity gate campaign block result is detached from its ablations"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ActivityGateCampaignStability:
    """Chronological stability and positive-improvement concentration for one metric."""

    primary_contrast_kind: ActivityGateCampaignPrimaryContrast
    primary_metric: ActivityGateCampaignMetric
    block_count: int
    scored_block_count: int
    missing_block_count: int
    positive_block_count: int
    zero_block_count: int
    negative_block_count: int
    pooled_primary_value: Decimal | None
    block_macro_mean: Decimal | None
    early_block_mean: Decimal | None
    late_block_mean: Decimal | None
    largest_positive_block_share: Decimal | None

    def __post_init__(self) -> None:
        """Preserve block coverage, sign counts, and concentration denominators."""
        counts = (
            self.block_count,
            self.scored_block_count,
            self.missing_block_count,
            self.positive_block_count,
            self.zero_block_count,
            self.negative_block_count,
        )
        if (
            min(counts) < 0
            or self.block_count <= 0
            or self.scored_block_count + self.missing_block_count != self.block_count
            or self.positive_block_count + self.zero_block_count + self.negative_block_count
            != self.scored_block_count
            or ((self.scored_block_count == 0) != (self.block_macro_mean is None))
            or (
                self.largest_positive_block_share is not None
                and not Decimal(0) < self.largest_positive_block_share <= Decimal(1)
            )
        ):
            message = "activity gate campaign stability has incoherent coverage or signs"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ActivityGateCampaignResult:
    """Immutable chronological and pooled LL-04c campaign evidence."""

    definition: ActivityGateCampaignDefinition
    blocks: tuple[ActivityGateCampaignBlockResult, ...]
    pooled: ActivityGateCampaignAggregate
    stability: ActivityGateCampaignStability

    def __post_init__(self) -> None:
        """Rebuild every output from the retained definition and input blocks."""
        input_blocks = tuple(block_result.block for block_result in self.blocks)
        _validate_campaign_inputs(self.definition, input_blocks)
        expected_blocks = tuple(_build_block_result(block) for block in input_blocks)
        expected_pooled = _aggregate_ablations(
            tuple(ablation for block in input_blocks for ablation in block.ablations)
        )
        expected_stability = _build_stability(
            self.definition,
            expected_blocks,
            expected_pooled,
        )
        if (
            self.blocks != expected_blocks
            or self.pooled != expected_pooled
            or self.stability != expected_stability
        ):
            message = "activity gate campaign result is detached from its exact inputs"
            raise ValueError(message)


def evaluate_activity_gate_campaign(
    definition: ActivityGateCampaignDefinition,
    blocks: tuple[ActivityGateCampaignBlock, ...],
) -> ActivityGateCampaignResult:
    """Aggregate one fixed H4 policy without fitting, selection, or imputation."""
    _validate_campaign_inputs(definition, blocks)
    block_results = tuple(_build_block_result(block) for block in blocks)
    pooled = _aggregate_ablations(
        tuple(ablation for block in blocks for ablation in block.ablations)
    )
    return ActivityGateCampaignResult(
        definition=definition,
        blocks=block_results,
        pooled=pooled,
        stability=_build_stability(definition, block_results, pooled),
    )


def _validate_campaign_inputs(
    definition: ActivityGateCampaignDefinition,
    blocks: tuple[ActivityGateCampaignBlock, ...],
) -> None:
    _validate_block_sequence(blocks)
    ablation_identities: set[tuple[str, str, BookLeg]] = set()
    attempt_identities: set[tuple[BookLeg, datetime]] = set()
    for block in blocks:
        for ablation in block.ablations:
            _validate_ablation_policy(definition, block, ablation)
            comparison = ablation.comparison
            gate = comparison.definition
            ablation_identity = (
                comparison.source_snapshot_uri,
                gate.parent_strategy_definition_id,
                gate.reference_leg,
            )
            if ablation_identity in ablation_identities:
                message = "activity gate campaign contains a duplicate ablation identity"
                raise ValueError(message)
            ablation_identities.add(ablation_identity)
            for decision in comparison.decisions:
                attempt_identity = (gate.reference_leg, decision.attempt.decision_at)
                if attempt_identity in attempt_identities:
                    message = "activity gate campaign contains a duplicate parent attempt"
                    raise ValueError(message)
                attempt_identities.add(attempt_identity)


def _validate_block_sequence(blocks: tuple[ActivityGateCampaignBlock, ...]) -> None:
    if not blocks:
        message = "activity gate campaign requires at least one chronological block"
        raise ValueError(message)
    if len({block.block_id for block in blocks}) != len(blocks):
        message = "activity gate campaign block identities must be unique"
        raise ValueError(message)
    for previous, current in pairwise(blocks):
        if previous.end_at > current.start_at:
            message = "activity gate campaign blocks overlap or are out of order"
            raise ValueError(message)


def _validate_ablation_policy(
    definition: ActivityGateCampaignDefinition,
    block: ActivityGateCampaignBlock,
    ablation: ActivityGateRivalAblation,
) -> None:
    comparison = ablation.comparison
    gate = comparison.definition
    if (
        comparison.parent_strategy_kind != definition.parent_strategy_kind
        or activity_gate_parent_recipe(comparison.parent_strategy_definition)
        != definition.parent_strategy_recipe
        or gate.scope_authority_ref != definition.scope_authority_ref
        or gate.recent_window != definition.recent_window
        or gate.maximum_quiet_duration != definition.maximum_quiet_duration
        or gate.minimum_recent_source_event_count != definition.minimum_recent_source_event_count
    ):
        message = "activity gate campaign ablation policy identity differs"
        raise ValueError(message)
    if comparison.source_start_at < block.start_at or comparison.source_end_at > block.end_at:
        message = "activity gate campaign ablation coverage escapes its block"
        raise ValueError(message)


def _build_block_result(block: ActivityGateCampaignBlock) -> ActivityGateCampaignBlockResult:
    return ActivityGateCampaignBlockResult(
        block=block,
        aggregate=_aggregate_ablations(block.ablations),
    )


def _aggregate_ablations(
    ablations: tuple[ActivityGateRivalAblation, ...],
) -> ActivityGateCampaignAggregate:
    market_ids = {ablation.comparison.definition.reference_leg.market_id for ablation in ablations}
    source_snapshot_uris = tuple(
        sorted({ablation.comparison.source_snapshot_uri for ablation in ablations})
    )
    attempts_by_population: dict[ActivityGateRivalPopulation, list[ActivityGateAttempt]] = {
        population: [] for population in ACTIVITY_GATE_RIVAL_POPULATIONS
    }
    for ablation in ablations:
        decision_by_index = {
            decision.parent_attempt_index: decision for decision in ablation.comparison.decisions
        }
        for population in ablation.populations:
            attempts_by_population[population.population].extend(
                decision_by_index[index].attempt for index in population.parent_attempt_indices
            )
    populations = tuple(
        ActivityGateCampaignPopulationSummary(
            population=population,
            ablation_count=len(ablations),
            market_count=len(market_ids),
            source_snapshot_uris=source_snapshot_uris,
            economics=summarize_activity_gate_attempts(tuple(attempts_by_population[population])),
        )
        for population in ACTIVITY_GATE_RIVAL_POPULATIONS
    )
    population_by_kind = {population.population: population for population in populations}
    contrasts = tuple(
        contrast_activity_gate_economics(
            contrast_kind=contrast_kind,
            left_population=left_population,
            right_population=right_population,
            left_economics=population_by_kind[left_population].economics,
            right_economics=population_by_kind[right_population].economics,
        )
        for contrast_kind, left_population, right_population in ACTIVITY_GATE_RIVAL_CONTRASTS
    )
    return ActivityGateCampaignAggregate(populations=populations, contrasts=contrasts)


def _build_stability(
    definition: ActivityGateCampaignDefinition,
    blocks: tuple[ActivityGateCampaignBlockResult, ...],
    pooled: ActivityGateCampaignAggregate,
) -> ActivityGateCampaignStability:
    block_values = tuple(
        _primary_value(
            _contrast_by_kind(block.aggregate, definition.primary_contrast_kind),
            definition.primary_metric,
        )
        for block in blocks
    )
    scored_values = tuple(value for value in block_values if value is not None)
    midpoint = (len(block_values) + 1) // 2
    early_values = tuple(value for value in block_values[:midpoint] if value is not None)
    late_values = tuple(value for value in block_values[midpoint:] if value is not None)
    positive_values = tuple(value for value in scored_values if value > 0)
    positive_total = sum(positive_values, start=Decimal(0))
    return ActivityGateCampaignStability(
        primary_contrast_kind=definition.primary_contrast_kind,
        primary_metric=definition.primary_metric,
        block_count=len(blocks),
        scored_block_count=len(scored_values),
        missing_block_count=len(block_values) - len(scored_values),
        positive_block_count=sum(value > 0 for value in scored_values),
        zero_block_count=sum(value == 0 for value in scored_values),
        negative_block_count=sum(value < 0 for value in scored_values),
        pooled_primary_value=_primary_value(
            _contrast_by_kind(pooled, definition.primary_contrast_kind),
            definition.primary_metric,
        ),
        block_macro_mean=_mean(scored_values),
        early_block_mean=_mean(early_values),
        late_block_mean=_mean(late_values),
        largest_positive_block_share=(
            None if positive_total <= 0 else max(positive_values) / positive_total
        ),
    )


def _contrast_by_kind(
    aggregate: ActivityGateCampaignAggregate,
    kind: ActivityGateRivalContrastKind,
) -> ActivityGateRivalContrast:
    matching = tuple(contrast for contrast in aggregate.contrasts if contrast.contrast_kind == kind)
    if len(matching) != 1:
        message = "activity gate campaign primary contrast is missing or duplicated"
        raise ValueError(message)
    return matching[0]


def _primary_value(
    contrast: ActivityGateRivalContrast,
    metric: ActivityGateCampaignMetric,
) -> Decimal | None:
    if metric == "NET_TOUCH_PNL_PER_SHARE_MEAN_CHANGE":
        return contrast.net_touch_pnl_per_share_mean_change
    if metric == "NET_TOUCH_PNL_PER_COLLATERAL_SECOND_CHANGE":
        return contrast.net_touch_pnl_per_collateral_second_change
    return contrast.diagnostic_displayed_net_per_collateral_second_change


def _mean(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return sum(values, start=Decimal(0)) / Decimal(len(values))
