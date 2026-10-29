"""Depth, clock, signal-decay, and touch adversaries for LL-05."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from research_agent.data_adapters.polymarket import (
    BookCorpus,
    BookCorpusRegistration,
    BookCorpusRequest,
    BookCorpusStore,
    BookDeltaRecord,
    BookLeg,
    BookSnapshotRecord,
    DepthImbalanceDefinition,
    depth_imbalance_metrics,
    register_book_corpus,
    screen_depth_imbalance_impulse,
)

START = datetime(2026, 8, 23, 14, 0, tzinfo=UTC)
AUTHORITY = "binary-outcomes:authorized"
YES = BookLeg("polymarket", "condition-id", 0)
NO = BookLeg("polymarket", "condition-id", 1)


def _snapshot(
    leg: BookLeg,
    *,
    bids: tuple[tuple[str, str], ...],
    asks: tuple[tuple[str, str], ...],
    seconds: int = 0,
    seq: int = 1,
) -> BookSnapshotRecord:
    ts = START + timedelta(seconds=seconds)
    return BookSnapshotRecord(
        leg=leg,
        ts=ts,
        reference_time=ts - timedelta(milliseconds=100),
        seq=seq,
        bids=bids,
        asks=asks,
        raw={"kind": "snapshot"},
    )


def _level(  # noqa: PLR0913
    leg: BookLeg,
    *,
    seconds: int,
    seq: int,
    side: str,
    price: str,
    size: str,
) -> BookDeltaRecord:
    ts = START + timedelta(seconds=seconds)
    return BookDeltaRecord(
        leg=leg,
        ts=ts,
        reference_time=ts - timedelta(milliseconds=100),
        seq=seq,
        side=side,  # type: ignore[arg-type]
        price=Decimal(price),
        size=Decimal(size),
        raw={"kind": "delta"},
    )


def _top_change(  # noqa: PLR0913
    leg: BookLeg,
    *,
    seconds: int,
    seq: int,
    old_bid: str,
    old_ask: str,
    new_bid: str,
    new_ask: str,
    bid_size: str = "10",
    ask_size: str = "10",
) -> tuple[BookDeltaRecord, ...]:
    rows = (
        _level(leg, seconds=seconds, seq=seq, side="BID", price=old_bid, size="0"),
        _level(
            leg,
            seconds=seconds,
            seq=seq,
            side="BID",
            price=new_bid,
            size=bid_size,
        ),
        _level(leg, seconds=seconds, seq=seq, side="ASK", price=old_ask, size="0"),
        _level(
            leg,
            seconds=seconds,
            seq=seq,
            side="ASK",
            price=new_ask,
            size=ask_size,
        ),
    )
    return tuple(sorted(rows, key=lambda row: row.sort_key))


def _balanced_yes() -> BookSnapshotRecord:
    return _snapshot(
        YES,
        bids=(("0.49", "10"), ("0.40", "10")),
        asks=(("0.51", "10"), ("0.60", "10")),
    )


def _no_book() -> BookSnapshotRecord:
    return _snapshot(
        NO,
        bids=(("0.48", "10"), ("0.40", "10")),
        asks=(("0.50", "10"), ("0.60", "10")),
    )


def _registration(
    *events: BookSnapshotRecord | BookDeltaRecord,
    end_seconds: int = 60,
) -> BookCorpusRegistration:
    request = BookCorpusRequest(
        "ll-05-development",
        AUTHORITY,
        (YES, NO),
        START,
        START + timedelta(seconds=end_seconds),
    )
    corpus = BookCorpus(request, tuple(sorted(events, key=lambda event: event.sort_key)))
    return register_book_corpus(BookCorpusStore.from_corpus(corpus))


def _definition(**changes: object) -> DepthImbalanceDefinition:
    definition = DepthImbalanceDefinition(
        definition_id="ll05-full-depth-v1",
        scope_authority_ref=AUTHORITY,
        reference_leg=YES,
        complement_leg=NO,
        entry_imbalance_threshold=Decimal("0.5"),
        exit_imbalance_threshold=Decimal("0.25"),
        maximum_spread=Decimal("0.03"),
        minimum_total_depth=Decimal(100),
        minimum_reference_midpoint=Decimal("0.05"),
        maximum_reference_midpoint=Decimal("0.95"),
        action_delay=timedelta(seconds=1),
        maximum_quote_age=timedelta(seconds=5),
        take_profit_distance=Decimal("0.01"),
        stop_loss_distance=Decimal("0.01"),
        maximum_holding_period=timedelta(seconds=10),
        minimum_entry_quantity=Decimal(1),
        round_trip_cost_per_share=Decimal("0.005"),
    )
    return replace(definition, **changes)


def test_definition_rejects_invalid_binary_signal_and_execution_policy() -> None:
    """Scope, thresholds, bands, clocks, sizes, and costs fail closed."""
    with pytest.raises(ValueError, match="distinct outcomes"):
        _definition(complement_leg=YES)
    with pytest.raises(ValueError, match="entry imbalance"):
        _definition(entry_imbalance_threshold=Decimal(1))
    with pytest.raises(ValueError, match="below entry"):
        _definition(exit_imbalance_threshold=Decimal("0.5"))
    with pytest.raises(ValueError, match="midpoint band"):
        _definition(minimum_reference_midpoint=Decimal("0.96"))
    with pytest.raises(ValueError, match="positive"):
        _definition(maximum_holding_period=timedelta(0))
    with pytest.raises(ValueError, match="cannot be negative"):
        _definition(round_trip_cost_per_share=Decimal("-0.01"))


def test_far_level_bid_depth_triggers_when_top_touch_is_balanced() -> None:
    """The implemented question uses the full ladder and never substitutes touch size."""
    registration = _registration(
        _balanced_yes(),
        _no_book(),
        _level(YES, seconds=1, seq=2, side="BID", price="0.40", size="100"),
        *_top_change(
            YES,
            seconds=5,
            seq=3,
            old_bid="0.49",
            old_ask="0.51",
            new_bid="0.51",
            new_ask="0.53",
            bid_size="6",
            ask_size="8",
        ),
        _level(YES, seconds=6, seq=4, side="BID", price="0.40", size="90"),
    )

    result = screen_depth_imbalance_impulse(registration, _definition())

    assert result.raw_crossing_count == 1
    assert result.entered_attempt_count == 1
    attempt = result.attempts[0]
    assert attempt.decision_metrics.imbalance == Decimal(90) / Decimal(130)
    assert attempt.decision_metrics.top_imbalance == 0
    assert (
        depth_imbalance_metrics(
            next(state for state in registration.states if state.available_at == START),
            depth_levels=1,
        ).imbalance
        == 0
    )
    assert attempt.selected_leg == YES
    assert attempt.entry_ask == Decimal("0.51")
    assert attempt.terminal_status == "TAKE_PROFIT_EXIT"
    assert attempt.exit_bid == Decimal("0.51")
    assert attempt.diagnostic_quantity == Decimal(6)
    assert attempt.gross_touch_pnl_per_share == 0
    assert attempt.net_touch_pnl_per_share == Decimal("-0.005")
    assert len(result.attempts) == 1


def test_same_collector_time_depth_changes_coalesce_before_signal() -> None:
    """A row-order transient cannot become an imbalance crossing."""
    registration = _registration(
        _balanced_yes(),
        _no_book(),
        _level(YES, seconds=1, seq=2, side="BID", price="0.40", size="100"),
        _level(YES, seconds=1, seq=2, side="ASK", price="0.60", size="100"),
    )

    result = screen_depth_imbalance_impulse(registration, _definition())

    assert result.raw_crossing_count == 0
    assert result.attempts == ()


def test_capture_starting_inside_imbalance_waits_for_a_fresh_crossing() -> None:
    """Left-truncated active state is not silently called a newly observed signal."""
    initially_bid_heavy = _snapshot(
        YES,
        bids=(("0.49", "10"), ("0.40", "100")),
        asks=(("0.51", "10"), ("0.60", "10")),
    )
    registration = _registration(
        initially_bid_heavy,
        _no_book(),
        _level(YES, seconds=1, seq=2, side="BID", price="0.40", size="10"),
        _level(YES, seconds=2, seq=3, side="BID", price="0.40", size="100"),
    )

    result = screen_depth_imbalance_impulse(registration, _definition())

    assert result.raw_crossing_count == 1
    assert result.attempts[0].decision_at == START + timedelta(seconds=2)


def test_signal_decay_during_action_delay_cancels_entry() -> None:
    """The raw imbalance must survive to the legal delayed arrival state."""
    registration = _registration(
        _balanced_yes(),
        _no_book(),
        _level(YES, seconds=1, seq=2, side="BID", price="0.40", size="100"),
        _level(YES, seconds=2, seq=3, side="BID", price="0.40", size="10"),
    )

    attempt = screen_depth_imbalance_impulse(
        registration,
        _definition(action_delay=timedelta(seconds=2)),
    ).attempts[0]

    assert attempt.terminal_status == "CANCELLED_AT_ARRIVAL"
    assert attempt.arrival_metrics is not None
    assert attempt.arrival_metrics.imbalance == 0
    assert attempt.entry_ask is None
    assert attempt.net_touch_pnl_per_share is None


def test_ask_heavy_yes_selects_no_and_takes_profit_at_no_bid() -> None:
    """Negative imbalance is expressed through the complement rather than a naked short."""
    registration = _registration(
        _balanced_yes(),
        _no_book(),
        _level(YES, seconds=1, seq=2, side="ASK", price="0.60", size="100"),
        *_top_change(
            YES,
            seconds=5,
            seq=3,
            old_bid="0.49",
            old_ask="0.51",
            new_bid="0.47",
            new_ask="0.49",
        ),
        *_top_change(
            NO,
            seconds=5,
            seq=2,
            old_bid="0.48",
            old_ask="0.50",
            new_bid="0.51",
            new_ask="0.53",
            bid_size="7",
        ),
    )

    attempt = screen_depth_imbalance_impulse(registration, _definition()).attempts[0]

    assert attempt.signal_sign == -1
    assert attempt.selected_leg == NO
    assert attempt.entry_ask == Decimal("0.50")
    assert attempt.terminal_status == "TAKE_PROFIT_EXIT"
    assert attempt.exit_bid == Decimal("0.51")
    assert attempt.diagnostic_quantity == Decimal(7)
    assert attempt.net_touch_pnl_per_share == Decimal("0.005")


@pytest.mark.parametrize(
    ("terminal_update", "expected_status"),
    [
        (
            _top_change(
                YES,
                seconds=5,
                seq=3,
                old_bid="0.49",
                old_ask="0.51",
                new_bid="0.47",
                new_ask="0.49",
            ),
            "STOP_LOSS_EXIT",
        ),
        (
            (_level(YES, seconds=5, seq=3, side="BID", price="0.40", size="10"),),
            "IMBALANCE_EXIT",
        ),
    ],
)
def test_stop_and_imbalance_decay_use_marketable_yes_bid(
    terminal_update: tuple[BookDeltaRecord, ...],
    expected_status: str,
) -> None:
    """Both risk exits retain the actual selected-outcome touch economics."""
    registration = _registration(
        _balanced_yes(),
        _no_book(),
        _level(YES, seconds=1, seq=2, side="BID", price="0.40", size="100"),
        *terminal_update,
    )

    attempt = screen_depth_imbalance_impulse(
        registration,
        _definition(action_delay=timedelta(0)),
    ).attempts[0]

    assert attempt.terminal_status == expected_status
    assert attempt.exit_bid is not None
    assert attempt.gross_touch_pnl_per_share == attempt.exit_bid - Decimal("0.51")


def test_timeout_and_truncation_are_distinct_coverage_outcomes() -> None:
    """A completed deadline may exit; an earlier half-open corpus end may not."""
    events = (
        _balanced_yes(),
        _no_book(),
        _level(YES, seconds=1, seq=2, side="BID", price="0.40", size="100"),
        _level(YES, seconds=5, seq=3, side="BID", price="0.49", size="0"),
        _level(YES, seconds=5, seq=3, side="BID", price="0.50", size="10"),
    )
    completed = screen_depth_imbalance_impulse(
        _registration(*events, end_seconds=20),
        _definition(
            action_delay=timedelta(0),
            maximum_holding_period=timedelta(seconds=4),
        ),
    ).attempts[0]
    truncated = screen_depth_imbalance_impulse(
        _registration(*events[:3], end_seconds=5),
        _definition(action_delay=timedelta(0)),
    ).attempts[0]

    assert completed.terminal_status == "TIMEOUT_EXIT"
    assert completed.terminal_at == START + timedelta(seconds=5)
    assert completed.exit_bid == Decimal("0.50")
    assert truncated.terminal_status == "TRUNCATED"
    assert truncated.exit_bid is None


def test_stale_complement_exit_is_missing_not_zero_pnl() -> None:
    """A negative signal with no fresh NO exit keeps the execution result missing."""
    registration = _registration(
        _balanced_yes(),
        _no_book(),
        _level(YES, seconds=1, seq=2, side="ASK", price="0.60", size="100"),
        *_top_change(
            YES,
            seconds=10,
            seq=3,
            old_bid="0.49",
            old_ask="0.51",
            new_bid="0.47",
            new_ask="0.49",
        ),
    )

    attempt = screen_depth_imbalance_impulse(
        registration,
        _definition(action_delay=timedelta(0)),
    ).attempts[0]

    assert attempt.terminal_status == "MISSING_EXIT_QUOTE"
    assert attempt.exit_metrics is not None
    assert attempt.exit_bid is None
    assert attempt.net_touch_pnl_per_share is None


def test_scope_authority_and_exact_leg_population_fail_before_screen() -> None:
    """The screen cannot reinterpret a different binary market or authority."""
    registration = _registration(_balanced_yes(), _no_book())

    with pytest.raises(ValueError, match="scope authority"):
        screen_depth_imbalance_impulse(
            registration,
            _definition(scope_authority_ref="binary-outcomes:other"),
        )
    with pytest.raises(ValueError, match="exactly match"):
        screen_depth_imbalance_impulse(
            registration,
            _definition(complement_leg=BookLeg("polymarket", "condition-id", 2)),
        )
