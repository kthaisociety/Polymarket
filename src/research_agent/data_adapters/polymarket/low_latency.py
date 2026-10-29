"""Predeclared gross feasibility screen for conservative two-leg payout dominance."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from itertools import groupby
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from datetime import datetime
    from decimal import Decimal

    from research_agent.data_adapters.polymarket.book_corpus import (
        BookCorpusRegistration,
        BookLeg,
        BookTopState,
    )


@dataclass(frozen=True, slots=True)
class PayoutDominanceDefinition:
    """Immutable identity and causal policy for one conservative gross pair."""

    definition_id: str
    scope_authority_ref: str
    first_leg: BookLeg
    second_leg: BookLeg
    payout_floor: Decimal
    minimum_gross_edge: Decimal
    maximum_quote_age: timedelta
    action_delay: timedelta

    def __post_init__(self) -> None:
        """Reject ambiguous direction, economics, or timing policy."""
        if not self.definition_id or not self.scope_authority_ref:
            msg = "payout dominance requires definition and scope authority identity"
            raise ValueError(msg)
        if self.first_leg == self.second_leg:
            msg = "payout dominance requires two distinct directed legs"
            raise ValueError(msg)
        if self.payout_floor <= 0 or self.minimum_gross_edge < 0:
            msg = "payout floor must be positive and minimum gross edge non-negative"
            raise ValueError(msg)
        if self.maximum_quote_age <= timedelta(0):
            msg = "maximum quote age must be positive"
            raise ValueError(msg)
        if self.action_delay < timedelta(0):
            msg = "action delay cannot be negative"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class PayoutDominanceOpportunity:
    """One legal displayed signal and its separately measured delayed display."""

    decision_at: datetime
    arrival_at: datetime
    trigger_legs: tuple[BookLeg, ...]
    first_event_ordinal: int
    second_event_ordinal: int
    decision_first_ask: Decimal
    decision_second_ask: Decimal
    decision_quantity: Decimal
    decision_gross_edge: Decimal
    delayed_first_ask: Decimal | None
    delayed_second_ask: Decimal | None
    delayed_quantity: Decimal | None
    delayed_gross_edge: Decimal | None
    displayed_edge_survives_delay: bool


@dataclass(frozen=True, slots=True)
class PayoutDominanceScreen:
    """Immutable gross feasibility output; it contains no fill or PnL claim."""

    definition: PayoutDominanceDefinition
    source_snapshot_uri: str
    evaluated_union_times: int
    opportunities: tuple[PayoutDominanceOpportunity, ...]


def screen_gross_payout_dominance(
    registration: BookCorpusRegistration,
    definition: PayoutDominanceDefinition,
) -> PayoutDominanceScreen:
    """Apply exact as-of joins and a fixed delayed-display diagnostic."""
    _require_scope(registration, definition)
    latest: dict[BookLeg, BookTopState] = {}
    opportunities: list[PayoutDominanceOpportunity] = []
    evaluated = 0
    for decision_at, source_group in groupby(
        registration.states,
        key=lambda state: state.available_at,
    ):
        group = tuple(source_group)
        for state in group:
            latest[state.leg] = state
        evaluated += 1
        pair = _fresh_pair(latest, definition, decision_at)
        if pair is None:
            continue
        first, second = pair
        edge = definition.payout_floor - first.ask_price - second.ask_price
        if edge <= 0 or edge < definition.minimum_gross_edge:
            continue
        arrival_at = decision_at + definition.action_delay
        delayed = _pair_as_of(registration.states, definition, arrival_at)
        delayed_edge = (
            None
            if delayed is None
            else definition.payout_floor - delayed[0].ask_price - delayed[1].ask_price
        )
        opportunities.append(
            PayoutDominanceOpportunity(
                decision_at=decision_at,
                arrival_at=arrival_at,
                trigger_legs=tuple(sorted({state.leg for state in group})),
                first_event_ordinal=first.event_ordinal,
                second_event_ordinal=second.event_ordinal,
                decision_first_ask=first.ask_price,
                decision_second_ask=second.ask_price,
                decision_quantity=min(first.ask_size, second.ask_size),
                decision_gross_edge=edge,
                delayed_first_ask=None if delayed is None else delayed[0].ask_price,
                delayed_second_ask=None if delayed is None else delayed[1].ask_price,
                delayed_quantity=(
                    None if delayed is None else min(delayed[0].ask_size, delayed[1].ask_size)
                ),
                delayed_gross_edge=delayed_edge,
                displayed_edge_survives_delay=(
                    delayed_edge is not None
                    and delayed_edge > 0
                    and delayed_edge >= definition.minimum_gross_edge
                ),
            )
        )
    return PayoutDominanceScreen(
        definition,
        registration.snapshot_ref.uri,
        evaluated,
        tuple(opportunities),
    )


def _require_scope(
    registration: BookCorpusRegistration,
    definition: PayoutDominanceDefinition,
) -> None:
    if registration.scope_authority_ref != definition.scope_authority_ref:
        msg = "payout screen scope authority does not match the retained corpus"
        raise ValueError(msg)
    observed = {state.leg for state in registration.states}
    expected = {definition.first_leg, definition.second_leg}
    if observed != expected:
        msg = "payout screen legs must exactly match the retained corpus"
        raise ValueError(msg)


def _fresh_pair(
    latest: dict[BookLeg, BookTopState],
    definition: PayoutDominanceDefinition,
    at: datetime,
) -> tuple[BookTopState, BookTopState] | None:
    first = latest.get(definition.first_leg)
    second = latest.get(definition.second_leg)
    if first is None or second is None:
        return None
    if (
        at - first.available_at > definition.maximum_quote_age
        or at - second.available_at > definition.maximum_quote_age
    ):
        return None
    return first, second


def _pair_as_of(
    states: tuple[BookTopState, ...],
    definition: PayoutDominanceDefinition,
    at: datetime,
) -> tuple[BookTopState, BookTopState] | None:
    latest: dict[BookLeg, BookTopState] = {}
    for state in states:
        if state.available_at > at:
            break
        latest[state.leg] = state
    return _fresh_pair(latest, definition, at)


type PostJumpTerminalStatus = Literal[
    "NO_ENTRY_QUOTE",
    "REVERSAL_EXIT",
    "CONTINUATION_EXIT",
    "TIMEOUT_EXIT",
    "MISSING_EXIT_QUOTE",
    "TRUNCATED",
]
_POST_JUMP_TERMINAL_STATUSES: tuple[PostJumpTerminalStatus, ...] = (
    "NO_ENTRY_QUOTE",
    "REVERSAL_EXIT",
    "CONTINUATION_EXIT",
    "TIMEOUT_EXIT",
    "MISSING_EXIT_QUOTE",
    "TRUNCATED",
)


@dataclass(frozen=True, slots=True)
class PostJumpReversalDefinition:
    """Fixed identity and marketable-touch policy for one binary market."""

    definition_id: str
    scope_authority_ref: str
    reference_leg: BookLeg
    complement_leg: BookLeg
    minimum_midpoint_shock: Decimal
    maximum_shock_gap: timedelta
    action_delay: timedelta
    maximum_quote_age: timedelta
    reversal_distance: Decimal
    continuation_distance: Decimal
    maximum_holding_period: timedelta
    minimum_entry_quantity: Decimal
    round_trip_cost_per_share: Decimal

    def __post_init__(self) -> None:
        """Reject ambiguous outcome semantics, time, geometry, or cost policy."""
        if not self.definition_id or not self.scope_authority_ref:
            msg = "post-jump reversal requires definition and scope authority identity"
            raise ValueError(msg)
        if (
            self.reference_leg.venue != "polymarket"
            or self.complement_leg.venue != "polymarket"
            or self.reference_leg.market_id != self.complement_leg.market_id
            or self.reference_leg.outcome_index == self.complement_leg.outcome_index
        ):
            msg = "post-jump reversal requires distinct outcomes of one Polymarket market"
            raise ValueError(msg)
        distances = (
            self.minimum_midpoint_shock,
            self.reversal_distance,
            self.continuation_distance,
        )
        if any(distance <= 0 or distance >= 1 for distance in distances):
            msg = "post-jump shock and path distances must lie strictly inside probability support"
            raise ValueError(msg)
        if (
            self.maximum_shock_gap <= timedelta(0)
            or self.maximum_quote_age <= timedelta(0)
            or self.maximum_holding_period <= timedelta(0)
        ):
            msg = "post-jump time windows must be positive"
            raise ValueError(msg)
        if self.action_delay < timedelta(0):
            msg = "post-jump action delay cannot be negative"
            raise ValueError(msg)
        if self.minimum_entry_quantity <= 0 or self.round_trip_cost_per_share < 0:
            msg = "post-jump size must be positive and cost non-negative"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class PostJumpReversalAttempt:
    """One non-overlapping shock and its causally delayed execution diagnostic."""

    decision_at: datetime
    arrival_at: datetime
    terminal_at: datetime
    terminal_status: PostJumpTerminalStatus
    shock_sign: int
    shock_change: Decimal
    selected_leg: BookLeg
    previous_reference_midpoint: Decimal
    decision_reference_midpoint: Decimal
    entry_reference_midpoint: Decimal | None
    exit_reference_midpoint: Decimal | None
    entry_ask: Decimal | None
    entry_displayed_size: Decimal | None
    exit_bid: Decimal | None
    exit_displayed_size: Decimal | None
    diagnostic_quantity: Decimal | None
    gross_touch_pnl_per_share: Decimal | None
    round_trip_cost_per_share: Decimal
    net_touch_pnl_per_share: Decimal | None
    decision_event_ordinal: int
    entry_reference_event_ordinal: int | None
    entry_selected_event_ordinal: int | None
    exit_reference_event_ordinal: int | None
    exit_selected_event_ordinal: int | None


@dataclass(frozen=True, slots=True)
class PostJumpReversalScreen:
    """Immutable LL-03 replay output; displayed touches do not imply fills."""

    definition: PostJumpReversalDefinition
    source_snapshot_uri: str
    source_start_at: datetime
    source_end_at: datetime
    evaluated_reference_updates: int
    raw_shock_count: int
    ignored_overlapping_shock_count: int
    entered_attempt_count: int
    terminal_status_counts: tuple[tuple[PostJumpTerminalStatus, int], ...]
    attempts: tuple[PostJumpReversalAttempt, ...]


@dataclass(frozen=True, slots=True)
class _ClockState:
    at: datetime
    latest: dict[BookLeg, BookTopState]
    updated_legs: tuple[BookLeg, ...]


def screen_book_post_jump_reversal(
    registration: BookCorpusRegistration,
    definition: PostJumpReversalDefinition,
) -> PostJumpReversalScreen:
    """Replay one fixed reversal policy on the collector-time union clock."""
    _require_reversal_scope(registration, definition)
    timeline = _collector_timeline(registration.states)
    previous_reference: BookTopState | None = None
    blocked_until: datetime | None = None
    attempts: list[PostJumpReversalAttempt] = []
    evaluated_updates = 0
    raw_shocks = 0
    ignored_overlaps = 0
    for frame_index, frame in enumerate(timeline):
        if definition.reference_leg not in frame.updated_legs:
            continue
        evaluated_updates += 1
        current_reference = frame.latest[definition.reference_leg]
        if previous_reference is None:
            previous_reference = current_reference
            continue
        previous_midpoint = _midpoint(previous_reference)
        current_midpoint = _midpoint(current_reference)
        shock_change = current_midpoint - previous_midpoint
        shock_gap = frame.at - previous_reference.available_at
        previous_reference = current_reference
        if (
            shock_gap > definition.maximum_shock_gap
            or abs(shock_change) < definition.minimum_midpoint_shock
        ):
            continue
        raw_shocks += 1
        if blocked_until is not None and frame.at <= blocked_until:
            ignored_overlaps += 1
            continue
        attempt, position_end = _evaluate_reversal_attempt(
            registration,
            definition,
            timeline,
            frame_index,
            previous_midpoint,
            current_reference,
            shock_change,
        )
        attempts.append(attempt)
        if attempt.entry_ask is not None:
            blocked_until = position_end
    return PostJumpReversalScreen(
        definition=definition,
        source_snapshot_uri=registration.snapshot_ref.uri,
        source_start_at=registration.start_at,
        source_end_at=registration.end_at,
        evaluated_reference_updates=evaluated_updates,
        raw_shock_count=raw_shocks,
        ignored_overlapping_shock_count=ignored_overlaps,
        entered_attempt_count=sum(attempt.entry_ask is not None for attempt in attempts),
        terminal_status_counts=tuple(
            (status, sum(attempt.terminal_status == status for attempt in attempts))
            for status in _POST_JUMP_TERMINAL_STATUSES
        ),
        attempts=tuple(attempts),
    )


def _require_reversal_scope(
    registration: BookCorpusRegistration,
    definition: PostJumpReversalDefinition,
) -> None:
    if registration.scope_authority_ref != definition.scope_authority_ref:
        msg = "post-jump screen scope authority does not match the retained corpus"
        raise ValueError(msg)
    observed = {state.leg for state in registration.states}
    expected = {definition.reference_leg, definition.complement_leg}
    if observed != expected:
        msg = "post-jump screen legs must exactly match the retained binary corpus"
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


def _evaluate_reversal_attempt(  # noqa: C901, PLR0911, PLR0913, PLR0917
    registration: BookCorpusRegistration,
    definition: PostJumpReversalDefinition,
    timeline: tuple[_ClockState, ...],
    decision_frame_index: int,
    previous_midpoint: Decimal,
    decision_reference: BookTopState,
    shock_change: Decimal,
) -> tuple[PostJumpReversalAttempt, datetime]:
    decision_at = timeline[decision_frame_index].at
    arrival_at = decision_at + definition.action_delay
    shock_sign = 1 if shock_change > 0 else -1
    selected_leg = definition.complement_leg if shock_sign > 0 else definition.reference_leg
    if arrival_at >= registration.end_at:
        return (
            _unentered_attempt(
                definition,
                decision_at,
                arrival_at,
                registration.end_at,
                "TRUNCATED",
                shock_sign,
                shock_change,
                selected_leg,
                previous_midpoint,
                decision_reference,
            ),
            registration.end_at,
        )
    entry_frame = _frame_as_of(timeline, arrival_at)
    entry_reference = entry_frame.latest.get(definition.reference_leg)
    entry_selected = entry_frame.latest.get(selected_leg)
    if (
        entry_reference is None
        or entry_selected is None
        or not _is_fresh(entry_reference, arrival_at, definition.maximum_quote_age)
        or not _is_fresh(entry_selected, arrival_at, definition.maximum_quote_age)
        or entry_selected.ask_size < definition.minimum_entry_quantity
    ):
        return (
            _unentered_attempt(
                definition,
                decision_at,
                arrival_at,
                arrival_at,
                "NO_ENTRY_QUOTE",
                shock_sign,
                shock_change,
                selected_leg,
                previous_midpoint,
                decision_reference,
            ),
            arrival_at,
        )
    entry_midpoint = _midpoint(entry_reference)
    deadline = arrival_at + definition.maximum_holding_period
    for frame in timeline[decision_frame_index + 1 :]:
        if frame.at <= arrival_at or frame.at > deadline:
            continue
        if definition.reference_leg not in frame.updated_legs:
            continue
        exit_reference = frame.latest[definition.reference_leg]
        aligned_change = shock_sign * (_midpoint(exit_reference) - entry_midpoint)
        if aligned_change <= -definition.reversal_distance:
            status: PostJumpTerminalStatus = "REVERSAL_EXIT"
        elif aligned_change >= definition.continuation_distance:
            status = "CONTINUATION_EXIT"
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
                    definition,
                    decision_at,
                    arrival_at,
                    frame.at,
                    "MISSING_EXIT_QUOTE",
                    shock_sign,
                    shock_change,
                    selected_leg,
                    previous_midpoint,
                    decision_reference,
                    entry_reference,
                    entry_selected,
                    exit_reference,
                    None,
                ),
                min(deadline, registration.end_at),
            )
        return (
            _entered_attempt(
                definition,
                decision_at,
                arrival_at,
                frame.at,
                status,
                shock_sign,
                shock_change,
                selected_leg,
                previous_midpoint,
                decision_reference,
                entry_reference,
                entry_selected,
                exit_reference,
                exit_selected,
            ),
            frame.at,
        )
    if deadline >= registration.end_at:
        return (
            _entered_attempt(
                definition,
                decision_at,
                arrival_at,
                registration.end_at,
                "TRUNCATED",
                shock_sign,
                shock_change,
                selected_leg,
                previous_midpoint,
                decision_reference,
                entry_reference,
                entry_selected,
                None,
                None,
            ),
            registration.end_at,
        )
    timeout_frame = _frame_as_of(timeline, deadline)
    timeout_reference = timeout_frame.latest.get(definition.reference_leg)
    timeout_selected = timeout_frame.latest.get(selected_leg)
    if (
        timeout_reference is None
        or timeout_selected is None
        or not _is_fresh(timeout_reference, deadline, definition.maximum_quote_age)
        or not _is_fresh(timeout_selected, deadline, definition.maximum_quote_age)
    ):
        return (
            _entered_attempt(
                definition,
                decision_at,
                arrival_at,
                deadline,
                "MISSING_EXIT_QUOTE",
                shock_sign,
                shock_change,
                selected_leg,
                previous_midpoint,
                decision_reference,
                entry_reference,
                entry_selected,
                timeout_reference,
                None,
            ),
            deadline,
        )
    return (
        _entered_attempt(
            definition,
            decision_at,
            arrival_at,
            deadline,
            "TIMEOUT_EXIT",
            shock_sign,
            shock_change,
            selected_leg,
            previous_midpoint,
            decision_reference,
            entry_reference,
            entry_selected,
            timeout_reference,
            timeout_selected,
        ),
        deadline,
    )


def _unentered_attempt(  # noqa: PLR0913, PLR0917
    definition: PostJumpReversalDefinition,
    decision_at: datetime,
    arrival_at: datetime,
    terminal_at: datetime,
    status: PostJumpTerminalStatus,
    shock_sign: int,
    shock_change: Decimal,
    selected_leg: BookLeg,
    previous_midpoint: Decimal,
    decision_reference: BookTopState,
) -> PostJumpReversalAttempt:
    return PostJumpReversalAttempt(
        decision_at=decision_at,
        arrival_at=arrival_at,
        terminal_at=terminal_at,
        terminal_status=status,
        shock_sign=shock_sign,
        shock_change=shock_change,
        selected_leg=selected_leg,
        previous_reference_midpoint=previous_midpoint,
        decision_reference_midpoint=_midpoint(decision_reference),
        entry_reference_midpoint=None,
        exit_reference_midpoint=None,
        entry_ask=None,
        entry_displayed_size=None,
        exit_bid=None,
        exit_displayed_size=None,
        diagnostic_quantity=None,
        gross_touch_pnl_per_share=None,
        round_trip_cost_per_share=definition.round_trip_cost_per_share,
        net_touch_pnl_per_share=None,
        decision_event_ordinal=decision_reference.event_ordinal,
        entry_reference_event_ordinal=None,
        entry_selected_event_ordinal=None,
        exit_reference_event_ordinal=None,
        exit_selected_event_ordinal=None,
    )


def _entered_attempt(  # noqa: PLR0913, PLR0917
    definition: PostJumpReversalDefinition,
    decision_at: datetime,
    arrival_at: datetime,
    terminal_at: datetime,
    status: PostJumpTerminalStatus,
    shock_sign: int,
    shock_change: Decimal,
    selected_leg: BookLeg,
    previous_midpoint: Decimal,
    decision_reference: BookTopState,
    entry_reference: BookTopState,
    entry_selected: BookTopState,
    exit_reference: BookTopState | None,
    exit_selected: BookTopState | None,
) -> PostJumpReversalAttempt:
    quantity = (
        None if exit_selected is None else min(entry_selected.ask_size, exit_selected.bid_size)
    )
    gross = None if exit_selected is None else exit_selected.bid_price - entry_selected.ask_price
    net = None if gross is None else gross - definition.round_trip_cost_per_share
    return PostJumpReversalAttempt(
        decision_at=decision_at,
        arrival_at=arrival_at,
        terminal_at=terminal_at,
        terminal_status=status,
        shock_sign=shock_sign,
        shock_change=shock_change,
        selected_leg=selected_leg,
        previous_reference_midpoint=previous_midpoint,
        decision_reference_midpoint=_midpoint(decision_reference),
        entry_reference_midpoint=_midpoint(entry_reference),
        exit_reference_midpoint=(None if exit_reference is None else _midpoint(exit_reference)),
        entry_ask=entry_selected.ask_price,
        entry_displayed_size=entry_selected.ask_size,
        exit_bid=None if exit_selected is None else exit_selected.bid_price,
        exit_displayed_size=None if exit_selected is None else exit_selected.bid_size,
        diagnostic_quantity=quantity,
        gross_touch_pnl_per_share=gross,
        round_trip_cost_per_share=definition.round_trip_cost_per_share,
        net_touch_pnl_per_share=net,
        decision_event_ordinal=decision_reference.event_ordinal,
        entry_reference_event_ordinal=entry_reference.event_ordinal,
        entry_selected_event_ordinal=entry_selected.event_ordinal,
        exit_reference_event_ordinal=(
            None if exit_reference is None else exit_reference.event_ordinal
        ),
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


def _midpoint(state: BookTopState) -> Decimal:
    return (state.bid_price + state.ask_price) / 2
