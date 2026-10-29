"""Paired activity-conditioned participation diagnostic for LL-03 and LL-05."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from research_agent.data_adapters.polymarket.book_imbalance import (
    DepthImbalanceAttempt,
    DepthImbalanceDefinition,
    DepthImbalanceScreen,
)
from research_agent.data_adapters.polymarket.low_latency import (
    PostJumpReversalAttempt,
    PostJumpReversalDefinition,
    PostJumpReversalScreen,
)

if TYPE_CHECKING:
    from research_agent.data_adapters.polymarket.book_activity import (
        BookActivityPoint,
        BookActivitySeries,
    )
    from research_agent.data_adapters.polymarket.book_corpus import BookLeg

type ActivityGateParentKind = Literal[
    "LL03_POST_JUMP_REVERSAL",
    "LL05_DEPTH_IMBALANCE",
]
type ActivityGateStatus = Literal[
    "PASS",
    "ABSTAIN_MISSING_HISTORY",
    "ABSTAIN_QUIET",
    "ABSTAIN_LOW_ACTIVITY",
    "ABSTAIN_QUIET_AND_LOW_ACTIVITY",
]
type ActivityGateRivalPopulation = Literal[
    "UNGATED",
    "COMPLETE_HISTORY",
    "QUIET_ONLY",
    "RECENT_ACTIVITY_ONLY",
    "JOINT",
]
type ActivityGateRivalContrastKind = Literal[
    "COMPLETE_HISTORY_MINUS_UNGATED",
    "QUIET_ONLY_MINUS_COMPLETE_HISTORY",
    "RECENT_ACTIVITY_ONLY_MINUS_COMPLETE_HISTORY",
    "JOINT_MINUS_COMPLETE_HISTORY",
    "JOINT_MINUS_QUIET_ONLY",
    "JOINT_MINUS_RECENT_ACTIVITY_ONLY",
]
type ActivityGateAttempt = PostJumpReversalAttempt | DepthImbalanceAttempt
type ActivityGateParentDefinition = PostJumpReversalDefinition | DepthImbalanceDefinition
type ActivityGateParentScreen = PostJumpReversalScreen | DepthImbalanceScreen

_GATE_STATUSES: tuple[ActivityGateStatus, ...] = (
    "PASS",
    "ABSTAIN_MISSING_HISTORY",
    "ABSTAIN_QUIET",
    "ABSTAIN_LOW_ACTIVITY",
    "ABSTAIN_QUIET_AND_LOW_ACTIVITY",
)
ACTIVITY_GATE_RIVAL_POPULATIONS: tuple[ActivityGateRivalPopulation, ...] = (
    "UNGATED",
    "COMPLETE_HISTORY",
    "QUIET_ONLY",
    "RECENT_ACTIVITY_ONLY",
    "JOINT",
)
ACTIVITY_GATE_RIVAL_CONTRASTS: tuple[
    tuple[
        ActivityGateRivalContrastKind,
        ActivityGateRivalPopulation,
        ActivityGateRivalPopulation,
    ],
    ...,
] = (
    ("COMPLETE_HISTORY_MINUS_UNGATED", "COMPLETE_HISTORY", "UNGATED"),
    ("QUIET_ONLY_MINUS_COMPLETE_HISTORY", "QUIET_ONLY", "COMPLETE_HISTORY"),
    (
        "RECENT_ACTIVITY_ONLY_MINUS_COMPLETE_HISTORY",
        "RECENT_ACTIVITY_ONLY",
        "COMPLETE_HISTORY",
    ),
    ("JOINT_MINUS_COMPLETE_HISTORY", "JOINT", "COMPLETE_HISTORY"),
    ("JOINT_MINUS_QUIET_ONLY", "JOINT", "QUIET_ONLY"),
    ("JOINT_MINUS_RECENT_ACTIVITY_ONLY", "JOINT", "RECENT_ACTIVITY_ONLY"),
)
_MICROSECONDS_PER_SECOND = Decimal(1_000_000)


def _require_aware(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        message = f"{field} must be timezone-aware"
        raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ActivityParticipationGateDefinition:
    """Exact parent identity and fixed causal H4a activity thresholds."""

    definition_id: str
    parent_strategy_kind: ActivityGateParentKind
    parent_strategy_definition_id: str
    scope_authority_ref: str
    reference_leg: BookLeg
    recent_window: timedelta
    maximum_quiet_duration: timedelta
    minimum_recent_source_event_count: int

    def __post_init__(self) -> None:
        """Reject implicit parent, scope, elapsed-window, or threshold semantics."""
        if (
            not self.definition_id
            or self.parent_strategy_kind not in ("LL03_POST_JUMP_REVERSAL", "LL05_DEPTH_IMBALANCE")
            or not self.parent_strategy_definition_id
            or not self.scope_authority_ref
            or self.reference_leg.venue != "polymarket"
            or self.recent_window <= timedelta(0)
            or self.maximum_quiet_duration <= timedelta(0)
            or self.minimum_recent_source_event_count < 0
        ):
            message = "activity participation gate requires exact identity and valid thresholds"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class _ParentIdentity:
    kind: ActivityGateParentKind
    definition_id: str
    scope_authority_ref: str
    reference_leg: BookLeg


@dataclass(frozen=True, slots=True)
class ActivityGateDecision:
    """One unchanged parent attempt and its exact signal-time gate disposition."""

    parent_attempt_index: int
    attempt: ActivityGateAttempt
    activity_point: BookActivityPoint
    quiet_passes: bool | None
    recent_activity_passes: bool | None
    status: ActivityGateStatus
    passes_gate: bool

    def __post_init__(self) -> None:
        """Keep parent order, exact join time, and disposition coherent."""
        expected_status = _status_from_passes(
            quiet_passes=self.quiet_passes,
            recent_passes=self.recent_activity_passes,
        )
        if (
            self.parent_attempt_index < 0
            or self.attempt.decision_at != self.activity_point.decision_time
            or self.status not in _GATE_STATUSES
            or self.status != expected_status
            or self.passes_gate != (self.status == "PASS")
        ):
            message = "activity gate decision is detached from its exact parent attempt"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ActivityGateEconomicSummary:
    """Coverage-first displayed-touch economics for one paired attempt subset."""

    attempt_count: int
    entered_attempt_count: int
    scorable_attempt_count: int
    unresolved_entered_attempt_count: int
    positive_scorable_count: int
    zero_scorable_count: int
    negative_scorable_count: int
    terminal_status_counts: tuple[tuple[str, int], ...]
    net_touch_pnl_per_share_sum: Decimal | None
    net_touch_pnl_per_share_mean: Decimal | None
    entered_holding_time: timedelta
    scorable_holding_time: timedelta
    scorable_collateral_seconds_per_share: Decimal | None
    net_touch_pnl_per_collateral_second: Decimal | None
    diagnostic_displayed_net_touch_pnl: Decimal | None
    diagnostic_displayed_collateral_seconds: Decimal | None
    diagnostic_displayed_net_per_collateral_second: Decimal | None

    def __post_init__(self) -> None:
        """Reject summaries that hide missing outcomes or incoherent denominators."""
        counts = (
            self.attempt_count,
            self.entered_attempt_count,
            self.scorable_attempt_count,
            self.unresolved_entered_attempt_count,
            self.positive_scorable_count,
            self.zero_scorable_count,
            self.negative_scorable_count,
        )
        score_fields = (
            self.net_touch_pnl_per_share_sum,
            self.net_touch_pnl_per_share_mean,
            self.scorable_collateral_seconds_per_share,
            self.diagnostic_displayed_net_touch_pnl,
            self.diagnostic_displayed_collateral_seconds,
        )
        if (
            min(counts) < 0
            or self.entered_attempt_count > self.attempt_count
            or self.scorable_attempt_count > self.entered_attempt_count
            or self.unresolved_entered_attempt_count
            != self.entered_attempt_count - self.scorable_attempt_count
            or self.positive_scorable_count
            + self.zero_scorable_count
            + self.negative_scorable_count
            != self.scorable_attempt_count
            or sum(count for _, count in self.terminal_status_counts) != self.attempt_count
            or tuple(status for status, _ in self.terminal_status_counts)
            != tuple(sorted(status for status, _ in self.terminal_status_counts))
            or self.entered_holding_time < timedelta(0)
            or self.scorable_holding_time < timedelta(0)
            or self.scorable_holding_time > self.entered_holding_time
            or (
                self.scorable_attempt_count == 0
                and any(field is not None for field in score_fields)
            )
            or (self.scorable_attempt_count > 0 and any(field is None for field in score_fields))
            or (
                self.net_touch_pnl_per_collateral_second is not None
                and (
                    self.scorable_collateral_seconds_per_share is None
                    or self.scorable_collateral_seconds_per_share <= 0
                )
            )
            or (
                self.diagnostic_displayed_net_per_collateral_second is not None
                and (
                    self.diagnostic_displayed_collateral_seconds is None
                    or self.diagnostic_displayed_collateral_seconds <= 0
                )
            )
        ):
            message = "activity gate economic summary is internally inconsistent"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ActivityGateComparison:
    """Immutable paired ungated and activity-gated H3/H5 diagnostic."""

    definition: ActivityParticipationGateDefinition
    parent_strategy_kind: ActivityGateParentKind
    parent_strategy_definition: ActivityGateParentDefinition
    source_snapshot_uri: str
    source_start_at: datetime
    source_end_at: datetime
    decisions: tuple[ActivityGateDecision, ...]
    gate_status_counts: tuple[tuple[ActivityGateStatus, int], ...]
    ungated: ActivityGateEconomicSummary
    gated: ActivityGateEconomicSummary
    incremental_net_touch_pnl_per_share_sum: Decimal | None
    incremental_net_touch_pnl_per_share_mean: Decimal | None
    incremental_net_per_collateral_second: Decimal | None
    incremental_diagnostic_displayed_net_touch_pnl: Decimal | None
    incremental_diagnostic_displayed_net_per_collateral_second: Decimal | None

    def __post_init__(self) -> None:
        """Keep the gated population an exact ordered subset of its paired baseline."""
        _require_aware(self.source_start_at, "source_start_at")
        _require_aware(self.source_end_at, "source_end_at")
        parent = _parent_definition_identity(self.parent_strategy_definition)
        gated_decisions = tuple(decision for decision in self.decisions if decision.passes_gate)
        expected_ungated = summarize_activity_gate_attempts(
            tuple(decision.attempt for decision in self.decisions)
        )
        expected_gated = summarize_activity_gate_attempts(
            tuple(decision.attempt for decision in gated_decisions)
        )
        expected_incrementals = (
            _difference(
                expected_gated.net_touch_pnl_per_share_sum,
                expected_ungated.net_touch_pnl_per_share_sum,
            ),
            _difference(
                expected_gated.net_touch_pnl_per_share_mean,
                expected_ungated.net_touch_pnl_per_share_mean,
            ),
            _difference(
                expected_gated.net_touch_pnl_per_collateral_second,
                expected_ungated.net_touch_pnl_per_collateral_second,
            ),
            _difference(
                expected_gated.diagnostic_displayed_net_touch_pnl,
                expected_ungated.diagnostic_displayed_net_touch_pnl,
            ),
            _difference(
                expected_gated.diagnostic_displayed_net_per_collateral_second,
                expected_ungated.diagnostic_displayed_net_per_collateral_second,
            ),
        )
        actual_incrementals = (
            self.incremental_net_touch_pnl_per_share_sum,
            self.incremental_net_touch_pnl_per_share_mean,
            self.incremental_net_per_collateral_second,
            self.incremental_diagnostic_displayed_net_touch_pnl,
            self.incremental_diagnostic_displayed_net_per_collateral_second,
        )
        if (
            self.parent_strategy_kind != self.definition.parent_strategy_kind
            or parent.kind != self.parent_strategy_kind
            or parent.definition_id != self.definition.parent_strategy_definition_id
            or parent.scope_authority_ref != self.definition.scope_authority_ref
            or parent.reference_leg != self.definition.reference_leg
            or not self.source_snapshot_uri
            or self.source_start_at >= self.source_end_at
            or any(
                not self.source_start_at <= decision.attempt.decision_at < self.source_end_at
                for decision in self.decisions
            )
            or tuple(decision.parent_attempt_index for decision in self.decisions)
            != tuple(range(len(self.decisions)))
            or self.gate_status_counts
            != tuple(
                (status, sum(decision.status == status for decision in self.decisions))
                for status in _GATE_STATUSES
            )
            or self.ungated.attempt_count != len(self.decisions)
            or self.gated.attempt_count != len(gated_decisions)
            or self.ungated != expected_ungated
            or self.gated != expected_gated
            or actual_incrementals != expected_incrementals
            or any(
                decision.activity_point.leg != self.definition.reference_leg
                or _gate_disposition(decision.activity_point, self.definition)
                != (
                    decision.quiet_passes,
                    decision.recent_activity_passes,
                    decision.status,
                )
                for decision in self.decisions
            )
        ):
            message = "activity gate comparison lost its paired parent population"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ActivityGateRivalPopulationSummary:
    """One exact ordered parent-attempt subset in the LL-04b rival ablation."""

    population: ActivityGateRivalPopulation
    parent_attempt_indices: tuple[int, ...]
    economics: ActivityGateEconomicSummary

    def __post_init__(self) -> None:
        """Keep population identity, order, and economic coverage aligned."""
        if (
            self.population not in ACTIVITY_GATE_RIVAL_POPULATIONS
            or self.parent_attempt_indices != tuple(sorted(set(self.parent_attempt_indices)))
            or any(index < 0 for index in self.parent_attempt_indices)
            or self.economics.attempt_count != len(self.parent_attempt_indices)
        ):
            message = "activity gate rival population lost its ordered parent subset"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ActivityGateRivalContrast:
    """Left-minus-right economics for one predeclared LL-04b rival contrast."""

    contrast_kind: ActivityGateRivalContrastKind
    left_population: ActivityGateRivalPopulation
    right_population: ActivityGateRivalPopulation
    attempt_count_change: int
    entered_attempt_count_change: int
    scorable_attempt_count_change: int
    unresolved_entered_attempt_count_change: int
    net_touch_pnl_per_share_sum_change: Decimal | None
    net_touch_pnl_per_share_mean_change: Decimal | None
    net_touch_pnl_per_collateral_second_change: Decimal | None
    diagnostic_displayed_net_touch_pnl_change: Decimal | None
    diagnostic_displayed_net_per_collateral_second_change: Decimal | None

    def __post_init__(self) -> None:
        """Reject a contrast whose name silently reverses its declared direction."""
        expected_sides = {
            kind: (left, right) for kind, left, right in ACTIVITY_GATE_RIVAL_CONTRASTS
        }.get(self.contrast_kind)
        if expected_sides != (self.left_population, self.right_population):
            message = "activity gate rival contrast direction does not match its identity"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ActivityGateRivalAblation:
    """Common-support component rivals for one immutable LL-04a comparison."""

    comparison: ActivityGateComparison
    populations: tuple[ActivityGateRivalPopulationSummary, ...]
    contrasts: tuple[ActivityGateRivalContrast, ...]

    def __post_init__(self) -> None:
        """Recompute every subset and contrast from the retained parent decisions."""
        expected_populations = _rival_population_summaries(self.comparison)
        expected_contrasts = _rival_contrasts(expected_populations)
        if self.populations != expected_populations or self.contrasts != expected_contrasts:
            message = "activity gate rival ablation is detached from its parent comparison"
            raise ValueError(message)


def compare_activity_gate_rivals(
    comparison: ActivityGateComparison,
) -> ActivityGateRivalAblation:
    """Compare the joint gate with warm-up, quiet-only, and count-only rivals."""
    populations = _rival_population_summaries(comparison)
    return ActivityGateRivalAblation(
        comparison=comparison,
        populations=populations,
        contrasts=_rival_contrasts(populations),
    )


def compare_activity_participation_gate(
    screen: ActivityGateParentScreen,
    activity: BookActivitySeries,
    definition: ActivityParticipationGateDefinition,
) -> ActivityGateComparison:
    """Apply one fixed activity gate without regenerating or mutating parent attempts."""
    parent = _parent_identity(screen)
    _require_matching_sources(
        screen,
        activity,
        definition,
        parent,
    )
    activity_by_key = {(point.leg, point.decision_time): point for point in activity.points}
    if len(activity_by_key) != len(activity.points):
        message = "activity gate requires unique exact leg and decision-time points"
        raise ValueError(message)
    decisions: list[ActivityGateDecision] = []
    for attempt_index, attempt in enumerate(screen.attempts):
        point = activity_by_key.get((definition.reference_leg, attempt.decision_at))
        if point is None:
            message = "parent attempt has no exact activity point at its signal time"
            raise ValueError(message)
        quiet_passes, recent_passes, status = _gate_disposition(point, definition)
        decisions.append(
            ActivityGateDecision(
                parent_attempt_index=attempt_index,
                attempt=attempt,
                activity_point=point,
                quiet_passes=quiet_passes,
                recent_activity_passes=recent_passes,
                status=status,
                passes_gate=status == "PASS",
            )
        )
    decision_tuple = tuple(decisions)
    ungated = summarize_activity_gate_attempts(
        tuple(decision.attempt for decision in decision_tuple)
    )
    gated = summarize_activity_gate_attempts(
        tuple(decision.attempt for decision in decision_tuple if decision.passes_gate)
    )
    return ActivityGateComparison(
        definition=definition,
        parent_strategy_kind=parent.kind,
        parent_strategy_definition=screen.definition,
        source_snapshot_uri=screen.source_snapshot_uri,
        source_start_at=screen.source_start_at,
        source_end_at=screen.source_end_at,
        decisions=decision_tuple,
        gate_status_counts=tuple(
            (status, sum(decision.status == status for decision in decision_tuple))
            for status in _GATE_STATUSES
        ),
        ungated=ungated,
        gated=gated,
        incremental_net_touch_pnl_per_share_sum=_difference(
            gated.net_touch_pnl_per_share_sum,
            ungated.net_touch_pnl_per_share_sum,
        ),
        incremental_net_touch_pnl_per_share_mean=_difference(
            gated.net_touch_pnl_per_share_mean,
            ungated.net_touch_pnl_per_share_mean,
        ),
        incremental_net_per_collateral_second=_difference(
            gated.net_touch_pnl_per_collateral_second,
            ungated.net_touch_pnl_per_collateral_second,
        ),
        incremental_diagnostic_displayed_net_touch_pnl=_difference(
            gated.diagnostic_displayed_net_touch_pnl,
            ungated.diagnostic_displayed_net_touch_pnl,
        ),
        incremental_diagnostic_displayed_net_per_collateral_second=_difference(
            gated.diagnostic_displayed_net_per_collateral_second,
            ungated.diagnostic_displayed_net_per_collateral_second,
        ),
    )


def _rival_population_summaries(
    comparison: ActivityGateComparison,
) -> tuple[ActivityGateRivalPopulationSummary, ...]:
    summaries: list[ActivityGateRivalPopulationSummary] = []
    for population in ACTIVITY_GATE_RIVAL_POPULATIONS:
        indices = tuple(
            decision.parent_attempt_index
            for decision in comparison.decisions
            if _decision_enters_rival_population(decision, population)
        )
        attempts = tuple(comparison.decisions[index].attempt for index in indices)
        summaries.append(
            ActivityGateRivalPopulationSummary(
                population=population,
                parent_attempt_indices=indices,
                economics=summarize_activity_gate_attempts(attempts),
            )
        )
    summary_tuple = tuple(summaries)
    summary_by_population = {summary.population: summary for summary in summary_tuple}
    if (
        summary_by_population["UNGATED"].economics != comparison.ungated
        or summary_by_population["JOINT"].economics != comparison.gated
    ):
        message = "activity gate rival endpoints differ from the parent comparison"
        raise ValueError(message)
    return summary_tuple


def _decision_enters_rival_population(
    decision: ActivityGateDecision,
    population: ActivityGateRivalPopulation,
) -> bool:
    if population == "UNGATED":
        return True
    has_complete_history = (
        decision.quiet_passes is not None and decision.recent_activity_passes is not None
    )
    if population == "COMPLETE_HISTORY":
        return has_complete_history
    if population == "QUIET_ONLY":
        return has_complete_history and decision.quiet_passes is True
    if population == "RECENT_ACTIVITY_ONLY":
        return has_complete_history and decision.recent_activity_passes is True
    return decision.passes_gate


def _rival_contrasts(
    populations: tuple[ActivityGateRivalPopulationSummary, ...],
) -> tuple[ActivityGateRivalContrast, ...]:
    population_by_kind = {population.population: population for population in populations}
    if tuple(population_by_kind) != ACTIVITY_GATE_RIVAL_POPULATIONS:
        message = "activity gate rival populations are incomplete or out of order"
        raise ValueError(message)
    return tuple(
        contrast_activity_gate_economics(
            contrast_kind=contrast_kind,
            left_population=left_population,
            right_population=right_population,
            left_economics=population_by_kind[left_population].economics,
            right_economics=population_by_kind[right_population].economics,
        )
        for contrast_kind, left_population, right_population in ACTIVITY_GATE_RIVAL_CONTRASTS
    )


def contrast_activity_gate_economics(
    *,
    contrast_kind: ActivityGateRivalContrastKind,
    left_population: ActivityGateRivalPopulation,
    right_population: ActivityGateRivalPopulation,
    left_economics: ActivityGateEconomicSummary,
    right_economics: ActivityGateEconomicSummary,
) -> ActivityGateRivalContrast:
    """Compute one declared left-minus-right contrast from exact population economics."""
    return ActivityGateRivalContrast(
        contrast_kind=contrast_kind,
        left_population=left_population,
        right_population=right_population,
        attempt_count_change=left_economics.attempt_count - right_economics.attempt_count,
        entered_attempt_count_change=(
            left_economics.entered_attempt_count - right_economics.entered_attempt_count
        ),
        scorable_attempt_count_change=(
            left_economics.scorable_attempt_count - right_economics.scorable_attempt_count
        ),
        unresolved_entered_attempt_count_change=(
            left_economics.unresolved_entered_attempt_count
            - right_economics.unresolved_entered_attempt_count
        ),
        net_touch_pnl_per_share_sum_change=_difference(
            left_economics.net_touch_pnl_per_share_sum,
            right_economics.net_touch_pnl_per_share_sum,
        ),
        net_touch_pnl_per_share_mean_change=_difference(
            left_economics.net_touch_pnl_per_share_mean,
            right_economics.net_touch_pnl_per_share_mean,
        ),
        net_touch_pnl_per_collateral_second_change=_difference(
            left_economics.net_touch_pnl_per_collateral_second,
            right_economics.net_touch_pnl_per_collateral_second,
        ),
        diagnostic_displayed_net_touch_pnl_change=_difference(
            left_economics.diagnostic_displayed_net_touch_pnl,
            right_economics.diagnostic_displayed_net_touch_pnl,
        ),
        diagnostic_displayed_net_per_collateral_second_change=_difference(
            left_economics.diagnostic_displayed_net_per_collateral_second,
            right_economics.diagnostic_displayed_net_per_collateral_second,
        ),
    )


def _parent_identity(
    screen: ActivityGateParentScreen,
) -> _ParentIdentity:
    return _parent_definition_identity(screen.definition)


def _parent_definition_identity(
    definition: ActivityGateParentDefinition,
) -> _ParentIdentity:
    if isinstance(definition, PostJumpReversalDefinition):
        return _ParentIdentity(
            kind="LL03_POST_JUMP_REVERSAL",
            definition_id=definition.definition_id,
            scope_authority_ref=definition.scope_authority_ref,
            reference_leg=definition.reference_leg,
        )
    return _ParentIdentity(
        kind="LL05_DEPTH_IMBALANCE",
        definition_id=definition.definition_id,
        scope_authority_ref=definition.scope_authority_ref,
        reference_leg=definition.reference_leg,
    )


def _require_matching_sources(
    screen: ActivityGateParentScreen,
    activity: BookActivitySeries,
    definition: ActivityParticipationGateDefinition,
    parent: _ParentIdentity,
) -> None:
    if screen.source_snapshot_uri != activity.snapshot_ref.uri:
        message = "activity gate screen and feature snapshot identities differ"
        raise ValueError(message)
    if screen.source_start_at != activity.start_at or screen.source_end_at != activity.end_at:
        message = "activity gate screen and feature coverage differ"
        raise ValueError(message)
    if (
        definition.scope_authority_ref != parent.scope_authority_ref
        or activity.scope_authority_ref != parent.scope_authority_ref
    ):
        message = "activity gate scope authority does not match parent and features"
        raise ValueError(message)
    if (
        definition.parent_strategy_kind != parent.kind
        or definition.parent_strategy_definition_id != parent.definition_id
    ):
        message = "activity gate parent strategy identity does not match the screen"
        raise ValueError(message)
    if definition.reference_leg != parent.reference_leg:
        message = "activity gate reference leg does not match the parent strategy"
        raise ValueError(message)
    if definition.recent_window != activity.definition.recent_window:
        message = "activity gate recent window does not match the feature series"
        raise ValueError(message)


def _gate_disposition(
    point: BookActivityPoint,
    definition: ActivityParticipationGateDefinition,
) -> tuple[bool | None, bool | None, ActivityGateStatus]:
    if point.quiet_duration is None or point.recent_source_event_count is None:
        return None, None, "ABSTAIN_MISSING_HISTORY"
    quiet_passes = point.quiet_duration <= definition.maximum_quiet_duration
    recent_passes = point.recent_source_event_count >= definition.minimum_recent_source_event_count
    status = _status_from_passes(
        quiet_passes=quiet_passes,
        recent_passes=recent_passes,
    )
    return quiet_passes, recent_passes, status


def _status_from_passes(
    *,
    quiet_passes: bool | None,
    recent_passes: bool | None,
) -> ActivityGateStatus:
    if quiet_passes is None or recent_passes is None:
        if quiet_passes is None and recent_passes is None:
            return "ABSTAIN_MISSING_HISTORY"
        message = "activity gate pass components must be jointly known or missing"
        raise ValueError(message)
    if quiet_passes and recent_passes:
        return "PASS"
    if not quiet_passes and not recent_passes:
        return "ABSTAIN_QUIET_AND_LOW_ACTIVITY"
    if not quiet_passes:
        return "ABSTAIN_QUIET"
    return "ABSTAIN_LOW_ACTIVITY"


def summarize_activity_gate_attempts(
    attempts: tuple[ActivityGateAttempt, ...],
) -> ActivityGateEconomicSummary:
    """Summarize one exact activity-gate attempt population without imputing outcomes."""
    _validate_attempts(attempts)
    entered = tuple(attempt for attempt in attempts if attempt.entry_ask is not None)
    scorable = tuple(attempt for attempt in entered if attempt.net_touch_pnl_per_share is not None)
    entered_holding = sum(
        (attempt.terminal_at - attempt.arrival_at for attempt in entered),
        start=timedelta(0),
    )
    scorable_holding = sum(
        (attempt.terminal_at - attempt.arrival_at for attempt in scorable),
        start=timedelta(0),
    )
    statuses = tuple(sorted({attempt.terminal_status for attempt in attempts}))
    if not scorable:
        net_sum = None
        net_mean = None
        collateral_seconds = None
        net_per_collateral_second = None
        displayed_net = None
        displayed_collateral_seconds = None
        displayed_net_per_collateral_second = None
    else:
        net_values = tuple(
            _require_decimal(attempt.net_touch_pnl_per_share, "scorable net touch PnL")
            for attempt in scorable
        )
        net_sum = sum(net_values, start=Decimal(0))
        net_mean = net_sum / Decimal(len(net_values))
        collateral_seconds = sum(
            (
                _require_decimal(attempt.entry_ask, "scorable entry ask")
                * _duration_seconds(attempt.terminal_at - attempt.arrival_at)
                for attempt in scorable
            ),
            start=Decimal(0),
        )
        net_per_collateral_second = (
            None if collateral_seconds <= 0 else net_sum / collateral_seconds
        )
        displayed_net = sum(
            (
                net_value
                * _require_decimal(attempt.diagnostic_quantity, "scorable diagnostic quantity")
                for attempt, net_value in zip(scorable, net_values, strict=True)
            ),
            start=Decimal(0),
        )
        displayed_collateral_seconds = sum(
            (
                _require_decimal(attempt.entry_ask, "scorable entry ask")
                * _require_decimal(attempt.diagnostic_quantity, "scorable diagnostic quantity")
                * _duration_seconds(attempt.terminal_at - attempt.arrival_at)
                for attempt in scorable
            ),
            start=Decimal(0),
        )
        displayed_net_per_collateral_second = (
            None
            if displayed_collateral_seconds <= 0
            else displayed_net / displayed_collateral_seconds
        )
    net_values_for_sign = tuple(
        _require_decimal(attempt.net_touch_pnl_per_share, "scorable net touch PnL")
        for attempt in scorable
    )
    return ActivityGateEconomicSummary(
        attempt_count=len(attempts),
        entered_attempt_count=len(entered),
        scorable_attempt_count=len(scorable),
        unresolved_entered_attempt_count=len(entered) - len(scorable),
        positive_scorable_count=sum(value > 0 for value in net_values_for_sign),
        zero_scorable_count=sum(value == 0 for value in net_values_for_sign),
        negative_scorable_count=sum(value < 0 for value in net_values_for_sign),
        terminal_status_counts=tuple(
            (status, sum(attempt.terminal_status == status for attempt in attempts))
            for status in statuses
        ),
        net_touch_pnl_per_share_sum=net_sum,
        net_touch_pnl_per_share_mean=net_mean,
        entered_holding_time=entered_holding,
        scorable_holding_time=scorable_holding,
        scorable_collateral_seconds_per_share=collateral_seconds,
        net_touch_pnl_per_collateral_second=net_per_collateral_second,
        diagnostic_displayed_net_touch_pnl=displayed_net,
        diagnostic_displayed_collateral_seconds=displayed_collateral_seconds,
        diagnostic_displayed_net_per_collateral_second=displayed_net_per_collateral_second,
    )


def _validate_attempts(attempts: tuple[ActivityGateAttempt, ...]) -> None:
    for attempt in attempts:
        _require_aware(attempt.decision_at, "attempt decision_at")
        _require_aware(attempt.arrival_at, "attempt arrival_at")
        _require_aware(attempt.terminal_at, "attempt terminal_at")
        if not attempt.decision_at <= attempt.arrival_at <= attempt.terminal_at:
            message = "activity gate parent attempt clocks are not ordered"
            raise ValueError(message)
        if attempt.entry_ask is None and attempt.net_touch_pnl_per_share is not None:
            message = "unentered parent attempt cannot carry net touch PnL"
            raise ValueError(message)
        if attempt.entry_ask is not None and attempt.entry_ask < 0:
            message = "entered parent attempt cannot carry a negative entry ask"
            raise ValueError(message)
        if attempt.net_touch_pnl_per_share is not None and (
            attempt.entry_ask is None
            or attempt.diagnostic_quantity is None
            or attempt.diagnostic_quantity <= 0
        ):
            message = "scorable parent attempt lacks entry or displayed quantity identity"
            raise ValueError(message)


def _require_decimal(value: Decimal | None, field: str) -> Decimal:
    if value is None:
        message = f"{field} is missing"
        raise ValueError(message)
    return value


def _duration_seconds(duration: timedelta) -> Decimal:
    whole_seconds = duration.days * 86_400 + duration.seconds
    return Decimal(whole_seconds) + Decimal(duration.microseconds) / _MICROSECONDS_PER_SECOND


def _difference(first: Decimal | None, second: Decimal | None) -> Decimal | None:
    if first is None or second is None:
        return None
    return first - second
