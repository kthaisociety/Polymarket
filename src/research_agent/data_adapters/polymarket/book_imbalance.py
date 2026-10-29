"""Causal multi-level order-book imbalance impulse replay for LL-05."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from itertools import groupby
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from research_agent.data_adapters.polymarket.book_corpus import (
        BookCorpusRegistration,
        BookLeg,
        BookTopState,
    )

type DepthImbalanceTerminalStatus = Literal[
    "CANCELLED_AT_ARRIVAL",
    "TAKE_PROFIT_EXIT",
    "STOP_LOSS_EXIT",
    "IMBALANCE_EXIT",
    "TIMEOUT_EXIT",
    "MISSING_EXIT_QUOTE",
    "TRUNCATED",
]
_TERMINAL_STATUSES: tuple[DepthImbalanceTerminalStatus, ...] = (
    "CANCELLED_AT_ARRIVAL",
    "TAKE_PROFIT_EXIT",
    "STOP_LOSS_EXIT",
    "IMBALANCE_EXIT",
    "TIMEOUT_EXIT",
    "MISSING_EXIT_QUOTE",
    "TRUNCATED",
)


@dataclass(frozen=True, slots=True)
class DepthImbalanceDefinition:
    """Fixed market, depth, timing, and marketable-touch LL-05 policy."""

    definition_id: str
    scope_authority_ref: str
    reference_leg: BookLeg
    complement_leg: BookLeg
    entry_imbalance_threshold: Decimal
    exit_imbalance_threshold: Decimal
    maximum_spread: Decimal
    minimum_total_depth: Decimal
    minimum_reference_midpoint: Decimal
    maximum_reference_midpoint: Decimal
    action_delay: timedelta
    maximum_quote_age: timedelta
    take_profit_distance: Decimal
    stop_loss_distance: Decimal
    maximum_holding_period: timedelta
    minimum_entry_quantity: Decimal
    round_trip_cost_per_share: Decimal
    depth_levels: int | None = None

    def __post_init__(self) -> None:  # noqa: C901
        """Reject ambiguous binary semantics or invalid signal and execution gates."""
        if not self.definition_id or not self.scope_authority_ref:
            msg = "depth imbalance requires definition and scope authority identity"
            raise ValueError(msg)
        if (
            self.reference_leg.venue != "polymarket"
            or self.complement_leg.venue != "polymarket"
            or self.reference_leg.market_id != self.complement_leg.market_id
            or self.reference_leg.outcome_index == self.complement_leg.outcome_index
        ):
            msg = "depth imbalance requires distinct outcomes of one Polymarket market"
            raise ValueError(msg)
        if not 0 < self.entry_imbalance_threshold < 1:
            msg = "entry imbalance threshold must lie strictly between zero and one"
            raise ValueError(msg)
        if not 0 <= self.exit_imbalance_threshold < self.entry_imbalance_threshold:
            msg = "exit imbalance threshold must be non-negative and below entry"
            raise ValueError(msg)
        if self.maximum_spread <= 0 or self.maximum_spread >= 1:
            msg = "maximum spread must lie strictly inside probability support"
            raise ValueError(msg)
        if self.minimum_total_depth <= 0 or self.minimum_entry_quantity <= 0:
            msg = "depth and entry quantity floors must be positive"
            raise ValueError(msg)
        if not (0 <= self.minimum_reference_midpoint < self.maximum_reference_midpoint <= 1):
            msg = "reference midpoint band must be ordered inside probability support"
            raise ValueError(msg)
        if self.take_profit_distance <= 0 or self.stop_loss_distance <= 0:
            msg = "take-profit and stop distances must be positive"
            raise ValueError(msg)
        if self.maximum_quote_age <= timedelta(0) or self.maximum_holding_period <= timedelta(0):
            msg = "quote age and holding period must be positive"
            raise ValueError(msg)
        if self.action_delay < timedelta(0) or self.round_trip_cost_per_share < 0:
            msg = "action delay and round-trip cost cannot be negative"
            raise ValueError(msg)
        if self.depth_levels is not None and self.depth_levels <= 0:
            msg = "depth level limit must be positive when supplied"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class DepthImbalanceMetrics:
    """One exact multi-level state diagnostic at a collector time."""

    midpoint: Decimal
    spread: Decimal
    bid_depth: Decimal
    ask_depth: Decimal
    total_depth: Decimal
    imbalance: Decimal
    top_imbalance: Decimal
    bid_level_count: int
    ask_level_count: int
    event_ordinal: int


@dataclass(frozen=True, slots=True)
class DepthImbalanceAttempt:
    """One non-overlapping raw crossing and its delayed touch outcome."""

    decision_at: datetime
    arrival_at: datetime
    terminal_at: datetime
    terminal_status: DepthImbalanceTerminalStatus
    signal_sign: int
    selected_leg: BookLeg
    decision_metrics: DepthImbalanceMetrics
    arrival_metrics: DepthImbalanceMetrics | None
    exit_metrics: DepthImbalanceMetrics | None
    entry_ask: Decimal | None
    entry_displayed_size: Decimal | None
    exit_bid: Decimal | None
    exit_displayed_size: Decimal | None
    diagnostic_quantity: Decimal | None
    gross_touch_pnl_per_share: Decimal | None
    round_trip_cost_per_share: Decimal
    net_touch_pnl_per_share: Decimal | None
    entry_selected_event_ordinal: int | None
    exit_selected_event_ordinal: int | None


@dataclass(frozen=True, slots=True)
class DepthImbalanceScreen:
    """Immutable LL-05 output; no displayed touch is represented as a fill."""

    definition: DepthImbalanceDefinition
    source_snapshot_uri: str
    source_start_at: datetime
    source_end_at: datetime
    evaluated_reference_updates: int
    raw_crossing_count: int
    ignored_overlapping_crossing_count: int
    entered_attempt_count: int
    terminal_status_counts: tuple[tuple[DepthImbalanceTerminalStatus, int], ...]
    attempts: tuple[DepthImbalanceAttempt, ...]


@dataclass(frozen=True, slots=True)
class _ClockState:
    at: datetime
    latest: dict[BookLeg, BookTopState]
    updated_legs: tuple[BookLeg, ...]


def screen_depth_imbalance_impulse(
    registration: BookCorpusRegistration,
    definition: DepthImbalanceDefinition,
) -> DepthImbalanceScreen:
    """Replay raw imbalance crossings with delayed reconfirmation and touch exits."""
    _require_scope(registration, definition)
    timeline = _collector_timeline(registration.states)
    previous_signal_sign: int | None = None
    seen_reference = False
    blocked_until: datetime | None = None
    attempts: list[DepthImbalanceAttempt] = []
    evaluated_updates = 0
    raw_crossings = 0
    ignored_overlaps = 0
    for frame_index, frame in enumerate(timeline):
        if definition.reference_leg not in frame.updated_legs:
            continue
        evaluated_updates += 1
        reference = frame.latest[definition.reference_leg]
        metrics = depth_imbalance_metrics(reference, definition.depth_levels)
        signal_sign = _eligible_signal_sign(metrics, definition)
        if not seen_reference:
            seen_reference = True
            previous_signal_sign = signal_sign
            continue
        crossing = signal_sign is not None and signal_sign != previous_signal_sign
        previous_signal_sign = signal_sign
        if not crossing:
            continue
        raw_crossings += 1
        if blocked_until is not None and frame.at <= blocked_until:
            ignored_overlaps += 1
            continue
        if signal_sign is None:
            continue
        attempt, position_end = _evaluate_attempt(
            registration,
            definition,
            timeline,
            frame_index,
            signal_sign,
            metrics,
        )
        attempts.append(attempt)
        if attempt.entry_ask is not None:
            blocked_until = position_end
    return DepthImbalanceScreen(
        definition=definition,
        source_snapshot_uri=registration.snapshot_ref.uri,
        source_start_at=registration.start_at,
        source_end_at=registration.end_at,
        evaluated_reference_updates=evaluated_updates,
        raw_crossing_count=raw_crossings,
        ignored_overlapping_crossing_count=ignored_overlaps,
        entered_attempt_count=sum(attempt.entry_ask is not None for attempt in attempts),
        terminal_status_counts=tuple(
            (status, sum(attempt.terminal_status == status for attempt in attempts))
            for status in _TERMINAL_STATUSES
        ),
        attempts=tuple(attempts),
    )


def depth_imbalance_metrics(
    state: BookTopState,
    depth_levels: int | None = None,
) -> DepthImbalanceMetrics:
    """Derive all-level or fixed-top-N depth diagnostics without float conversion."""
    if depth_levels is not None and depth_levels <= 0:
        msg = "depth level limit must be positive when supplied"
        raise ValueError(msg)
    bid_levels = state.bid_levels if depth_levels is None else state.bid_levels[:depth_levels]
    ask_levels = state.ask_levels if depth_levels is None else state.ask_levels[:depth_levels]
    bid_depth = sum((size for _, size in bid_levels), start=Decimal(0))
    ask_depth = sum((size for _, size in ask_levels), start=Decimal(0))
    total_depth = bid_depth + ask_depth
    if total_depth <= 0:
        msg = "depth imbalance requires positive displayed depth"
        raise ValueError(msg)
    top_total = state.bid_size + state.ask_size
    return DepthImbalanceMetrics(
        midpoint=(state.bid_price + state.ask_price) / 2,
        spread=state.ask_price - state.bid_price,
        bid_depth=bid_depth,
        ask_depth=ask_depth,
        total_depth=total_depth,
        imbalance=(bid_depth - ask_depth) / total_depth,
        top_imbalance=(state.bid_size - state.ask_size) / top_total,
        bid_level_count=len(bid_levels),
        ask_level_count=len(ask_levels),
        event_ordinal=state.event_ordinal,
    )


def _require_scope(
    registration: BookCorpusRegistration,
    definition: DepthImbalanceDefinition,
) -> None:
    if registration.scope_authority_ref != definition.scope_authority_ref:
        msg = "depth imbalance scope authority does not match the retained corpus"
        raise ValueError(msg)
    observed = {state.leg for state in registration.states}
    expected = {definition.reference_leg, definition.complement_leg}
    if observed != expected:
        msg = "depth imbalance legs must exactly match the retained binary corpus"
        raise ValueError(msg)


def _collector_timeline(states: tuple[BookTopState, ...]) -> tuple[_ClockState, ...]:
    latest: dict[BookLeg, BookTopState] = {}
    timeline: list[_ClockState] = []
    for at, source_group in groupby(states, key=lambda state: state.available_at):
        group = tuple(source_group)
        for state in group:
            latest[state.leg] = state
        timeline.append(
            _ClockState(
                at=at,
                latest=dict(latest),
                updated_legs=tuple(sorted({state.leg for state in group})),
            )
        )
    return tuple(timeline)


def _eligible_signal_sign(
    metrics: DepthImbalanceMetrics,
    definition: DepthImbalanceDefinition,
) -> int | None:
    if (
        metrics.spread > definition.maximum_spread
        or metrics.total_depth < definition.minimum_total_depth
        or metrics.midpoint < definition.minimum_reference_midpoint
        or metrics.midpoint > definition.maximum_reference_midpoint
        or abs(metrics.imbalance) < definition.entry_imbalance_threshold
    ):
        return None
    return 1 if metrics.imbalance > 0 else -1


def _evaluate_attempt(  # noqa: C901, PLR0911, PLR0913, PLR0917
    registration: BookCorpusRegistration,
    definition: DepthImbalanceDefinition,
    timeline: tuple[_ClockState, ...],
    decision_frame_index: int,
    signal_sign: int,
    decision_metrics: DepthImbalanceMetrics,
) -> tuple[DepthImbalanceAttempt, datetime]:
    decision_at = timeline[decision_frame_index].at
    arrival_at = decision_at + definition.action_delay
    selected_leg = definition.reference_leg if signal_sign > 0 else definition.complement_leg
    if arrival_at >= registration.end_at:
        return (
            _unentered_attempt(
                definition=definition,
                decision_at=decision_at,
                arrival_at=arrival_at,
                terminal_at=registration.end_at,
                status="TRUNCATED",
                signal_sign=signal_sign,
                selected_leg=selected_leg,
                decision_metrics=decision_metrics,
                arrival_metrics=None,
            ),
            registration.end_at,
        )
    entry_frame = _frame_as_of(timeline, arrival_at)
    entry_reference = entry_frame.latest.get(definition.reference_leg)
    entry_selected = entry_frame.latest.get(selected_leg)
    arrival_metrics = (
        None
        if entry_reference is None
        else depth_imbalance_metrics(entry_reference, definition.depth_levels)
    )
    if (
        entry_reference is None
        or entry_selected is None
        or arrival_metrics is None
        or not _is_fresh(entry_reference, arrival_at, definition.maximum_quote_age)
        or not _is_fresh(entry_selected, arrival_at, definition.maximum_quote_age)
        or _eligible_signal_sign(arrival_metrics, definition) != signal_sign
        or entry_selected.ask_size < definition.minimum_entry_quantity
    ):
        return (
            _unentered_attempt(
                definition=definition,
                decision_at=decision_at,
                arrival_at=arrival_at,
                terminal_at=arrival_at,
                status="CANCELLED_AT_ARRIVAL",
                signal_sign=signal_sign,
                selected_leg=selected_leg,
                decision_metrics=decision_metrics,
                arrival_metrics=arrival_metrics,
            ),
            arrival_at,
        )
    deadline = arrival_at + definition.maximum_holding_period
    for frame in timeline[decision_frame_index + 1 :]:
        if frame.at <= arrival_at or frame.at > deadline:
            continue
        if definition.reference_leg not in frame.updated_legs:
            continue
        exit_reference = frame.latest[definition.reference_leg]
        exit_metrics = depth_imbalance_metrics(exit_reference, definition.depth_levels)
        aligned_move = signal_sign * (exit_metrics.midpoint - arrival_metrics.midpoint)
        if aligned_move >= definition.take_profit_distance:
            status: DepthImbalanceTerminalStatus = "TAKE_PROFIT_EXIT"
        elif aligned_move <= -definition.stop_loss_distance:
            status = "STOP_LOSS_EXIT"
        elif signal_sign * exit_metrics.imbalance <= definition.exit_imbalance_threshold:
            status = "IMBALANCE_EXIT"
        else:
            continue
        exit_selected = frame.latest.get(selected_leg)
        if exit_selected is None or not _is_fresh(
            exit_selected,
            frame.at,
            definition.maximum_quote_age,
        ):
            return (
                _entered_attempt(
                    definition=definition,
                    decision_at=decision_at,
                    arrival_at=arrival_at,
                    terminal_at=frame.at,
                    status="MISSING_EXIT_QUOTE",
                    signal_sign=signal_sign,
                    selected_leg=selected_leg,
                    decision_metrics=decision_metrics,
                    arrival_metrics=arrival_metrics,
                    exit_metrics=exit_metrics,
                    entry_selected=entry_selected,
                    exit_selected=None,
                ),
                min(deadline, registration.end_at),
            )
        return (
            _entered_attempt(
                definition=definition,
                decision_at=decision_at,
                arrival_at=arrival_at,
                terminal_at=frame.at,
                status=status,
                signal_sign=signal_sign,
                selected_leg=selected_leg,
                decision_metrics=decision_metrics,
                arrival_metrics=arrival_metrics,
                exit_metrics=exit_metrics,
                entry_selected=entry_selected,
                exit_selected=exit_selected,
            ),
            frame.at,
        )
    if deadline >= registration.end_at:
        return (
            _entered_attempt(
                definition=definition,
                decision_at=decision_at,
                arrival_at=arrival_at,
                terminal_at=registration.end_at,
                status="TRUNCATED",
                signal_sign=signal_sign,
                selected_leg=selected_leg,
                decision_metrics=decision_metrics,
                arrival_metrics=arrival_metrics,
                exit_metrics=None,
                entry_selected=entry_selected,
                exit_selected=None,
            ),
            registration.end_at,
        )
    timeout_frame = _frame_as_of(timeline, deadline)
    timeout_reference = timeout_frame.latest.get(definition.reference_leg)
    timeout_selected = timeout_frame.latest.get(selected_leg)
    timeout_metrics = (
        None
        if timeout_reference is None
        else depth_imbalance_metrics(timeout_reference, definition.depth_levels)
    )
    if (
        timeout_reference is None
        or timeout_selected is None
        or timeout_metrics is None
        or not _is_fresh(timeout_reference, deadline, definition.maximum_quote_age)
        or not _is_fresh(timeout_selected, deadline, definition.maximum_quote_age)
    ):
        return (
            _entered_attempt(
                definition=definition,
                decision_at=decision_at,
                arrival_at=arrival_at,
                terminal_at=deadline,
                status="MISSING_EXIT_QUOTE",
                signal_sign=signal_sign,
                selected_leg=selected_leg,
                decision_metrics=decision_metrics,
                arrival_metrics=arrival_metrics,
                exit_metrics=timeout_metrics,
                entry_selected=entry_selected,
                exit_selected=None,
            ),
            deadline,
        )
    return (
        _entered_attempt(
            definition=definition,
            decision_at=decision_at,
            arrival_at=arrival_at,
            terminal_at=deadline,
            status="TIMEOUT_EXIT",
            signal_sign=signal_sign,
            selected_leg=selected_leg,
            decision_metrics=decision_metrics,
            arrival_metrics=arrival_metrics,
            exit_metrics=timeout_metrics,
            entry_selected=entry_selected,
            exit_selected=timeout_selected,
        ),
        deadline,
    )


def _unentered_attempt(  # noqa: PLR0913
    *,
    definition: DepthImbalanceDefinition,
    decision_at: datetime,
    arrival_at: datetime,
    terminal_at: datetime,
    status: DepthImbalanceTerminalStatus,
    signal_sign: int,
    selected_leg: BookLeg,
    decision_metrics: DepthImbalanceMetrics,
    arrival_metrics: DepthImbalanceMetrics | None,
) -> DepthImbalanceAttempt:
    return DepthImbalanceAttempt(
        decision_at=decision_at,
        arrival_at=arrival_at,
        terminal_at=terminal_at,
        terminal_status=status,
        signal_sign=signal_sign,
        selected_leg=selected_leg,
        decision_metrics=decision_metrics,
        arrival_metrics=arrival_metrics,
        exit_metrics=None,
        entry_ask=None,
        entry_displayed_size=None,
        exit_bid=None,
        exit_displayed_size=None,
        diagnostic_quantity=None,
        gross_touch_pnl_per_share=None,
        round_trip_cost_per_share=definition.round_trip_cost_per_share,
        net_touch_pnl_per_share=None,
        entry_selected_event_ordinal=None,
        exit_selected_event_ordinal=None,
    )


def _entered_attempt(  # noqa: PLR0913
    *,
    definition: DepthImbalanceDefinition,
    decision_at: datetime,
    arrival_at: datetime,
    terminal_at: datetime,
    status: DepthImbalanceTerminalStatus,
    signal_sign: int,
    selected_leg: BookLeg,
    decision_metrics: DepthImbalanceMetrics,
    arrival_metrics: DepthImbalanceMetrics,
    exit_metrics: DepthImbalanceMetrics | None,
    entry_selected: BookTopState,
    exit_selected: BookTopState | None,
) -> DepthImbalanceAttempt:
    quantity = (
        None if exit_selected is None else min(entry_selected.ask_size, exit_selected.bid_size)
    )
    gross = None if exit_selected is None else exit_selected.bid_price - entry_selected.ask_price
    net = None if gross is None else gross - definition.round_trip_cost_per_share
    return DepthImbalanceAttempt(
        decision_at=decision_at,
        arrival_at=arrival_at,
        terminal_at=terminal_at,
        terminal_status=status,
        signal_sign=signal_sign,
        selected_leg=selected_leg,
        decision_metrics=decision_metrics,
        arrival_metrics=arrival_metrics,
        exit_metrics=exit_metrics,
        entry_ask=entry_selected.ask_price,
        entry_displayed_size=entry_selected.ask_size,
        exit_bid=None if exit_selected is None else exit_selected.bid_price,
        exit_displayed_size=None if exit_selected is None else exit_selected.bid_size,
        diagnostic_quantity=quantity,
        gross_touch_pnl_per_share=gross,
        round_trip_cost_per_share=definition.round_trip_cost_per_share,
        net_touch_pnl_per_share=net,
        entry_selected_event_ordinal=entry_selected.event_ordinal,
        exit_selected_event_ordinal=(
            None if exit_selected is None else exit_selected.event_ordinal
        ),
    )


def _frame_as_of(timeline: tuple[_ClockState, ...], at: datetime) -> _ClockState:
    latest = timeline[0]
    for frame in timeline:
        if frame.at > at:
            break
        latest = frame
    return latest


def _is_fresh(state: BookTopState, at: datetime, maximum_age: timedelta) -> bool:
    return state.available_at <= at and at - state.available_at <= maximum_age
