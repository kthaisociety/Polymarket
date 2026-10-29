"""Causal and execution adversaries for the LL-03 post-jump reversal screen."""

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
    PostJumpReversalDefinition,
    register_book_corpus,
    screen_book_post_jump_reversal,
)

START = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)
AUTHORITY = "binary-outcomes:authorized"
YES = BookLeg("polymarket", "condition-id", 0)
NO = BookLeg("polymarket", "condition-id", 1)
TWO_SHOCKS = 2
THREE_SHOCKS = 3


def _snapshot(  # noqa: PLR0913
    leg: BookLeg,
    *,
    seconds: int,
    bid: str,
    ask: str,
    bid_size: str = "10",
    ask_size: str = "10",
    reference_seconds: int | None = None,
) -> BookSnapshotRecord:
    ts = START + timedelta(seconds=seconds)
    reference_time = (
        ts - timedelta(milliseconds=100)
        if reference_seconds is None
        else START + timedelta(seconds=reference_seconds)
    )
    return BookSnapshotRecord(
        leg=leg,
        ts=ts,
        reference_time=reference_time,
        seq=1,
        bids=((bid, bid_size),),
        asks=((ask, ask_size),),
        raw={"kind": "snapshot"},
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
    reference_seconds: int | None = None,
) -> tuple[BookDeltaRecord, ...]:
    ts = START + timedelta(seconds=seconds)
    reference_time = (
        ts - timedelta(milliseconds=100)
        if reference_seconds is None
        else START + timedelta(seconds=reference_seconds)
    )
    rows = (
        BookDeltaRecord(
            leg, ts, reference_time, seq, "BID", Decimal(old_bid), Decimal(0), {"remove": 1}
        ),
        BookDeltaRecord(
            leg,
            ts,
            reference_time,
            seq,
            "BID",
            Decimal(new_bid),
            Decimal(bid_size),
            {"add": 1},
        ),
        BookDeltaRecord(
            leg, ts, reference_time, seq, "ASK", Decimal(old_ask), Decimal(0), {"remove": 1}
        ),
        BookDeltaRecord(
            leg,
            ts,
            reference_time,
            seq,
            "ASK",
            Decimal(new_ask),
            Decimal(ask_size),
            {"add": 1},
        ),
    )
    return tuple(sorted(rows, key=lambda row: row.sort_key))


def _registration(
    *events: BookSnapshotRecord | BookDeltaRecord,
    end_seconds: int = 120,
) -> BookCorpusRegistration:
    request = BookCorpusRequest(
        "ll-03-development",
        AUTHORITY,
        (YES, NO),
        START,
        START + timedelta(seconds=end_seconds),
    )
    corpus = BookCorpus(request, tuple(sorted(events, key=lambda event: event.sort_key)))
    return register_book_corpus(BookCorpusStore.from_corpus(corpus))


def _definition(**changes: object) -> PostJumpReversalDefinition:
    definition = PostJumpReversalDefinition(
        definition_id="ll03-touch-v1",
        scope_authority_ref=AUTHORITY,
        reference_leg=YES,
        complement_leg=NO,
        minimum_midpoint_shock=Decimal("0.02"),
        maximum_shock_gap=timedelta(hours=3),
        action_delay=timedelta(seconds=2),
        maximum_quote_age=timedelta(seconds=5),
        reversal_distance=Decimal("0.02"),
        continuation_distance=Decimal("0.02"),
        maximum_holding_period=timedelta(seconds=30),
        minimum_entry_quantity=Decimal(1),
        round_trip_cost_per_share=Decimal("0.005"),
    )
    return replace(definition, **changes)


def test_definition_requires_exact_binary_polymarket_scope_and_valid_policy() -> None:
    """Outcome identity, thresholds, clocks, size, and costs fail closed."""
    with pytest.raises(ValueError, match="distinct outcomes"):
        _definition(complement_leg=YES)
    with pytest.raises(ValueError, match="probability support"):
        _definition(reversal_distance=Decimal(0))
    with pytest.raises(ValueError, match="time windows"):
        _definition(maximum_holding_period=timedelta(0))
    with pytest.raises(ValueError, match="action delay"):
        _definition(action_delay=timedelta(seconds=-1))
    with pytest.raises(ValueError, match="cost"):
        _definition(round_trip_cost_per_share=Decimal("-0.01"))


def test_positive_shock_buys_no_after_delay_and_exits_at_coalesced_reversal_touch() -> None:
    """A delayed upward-YES reversal uses only as-of NO asks and contemporaneous NO bids."""
    registration = _registration(
        _snapshot(YES, seconds=0, bid="0.49", ask="0.51"),
        _snapshot(NO, seconds=0, bid="0.49", ask="0.51"),
        *_top_change(
            YES,
            seconds=10,
            seq=2,
            old_bid="0.49",
            old_ask="0.51",
            new_bid="0.53",
            new_ask="0.55",
            reference_seconds=-100,
        ),
        *_top_change(
            NO,
            seconds=11,
            seq=2,
            old_bid="0.49",
            old_ask="0.51",
            new_bid="0.44",
            new_ask="0.46",
            ask_size="7",
        ),
        *_top_change(
            NO,
            seconds=13,
            seq=3,
            old_bid="0.44",
            old_ask="0.46",
            new_bid="0.39",
            new_ask="0.41",
        ),
        *_top_change(
            YES,
            seconds=14,
            seq=3,
            old_bid="0.53",
            old_ask="0.55",
            new_bid="0.50",
            new_ask="0.52",
        ),
        *_top_change(
            NO,
            seconds=14,
            seq=4,
            old_bid="0.39",
            old_ask="0.41",
            new_bid="0.48",
            new_ask="0.50",
            bid_size="5",
        ),
    )

    result = screen_book_post_jump_reversal(registration, _definition())

    assert result.source_start_at == START
    assert result.source_end_at == START + timedelta(seconds=120)
    assert result.raw_shock_count == TWO_SHOCKS
    assert result.ignored_overlapping_shock_count == 1
    assert result.entered_attempt_count == 1
    assert dict(result.terminal_status_counts)["REVERSAL_EXIT"] == 1
    assert len(result.attempts) == 1
    attempt = result.attempts[0]
    assert attempt.decision_at == START + timedelta(seconds=10)
    assert attempt.arrival_at == START + timedelta(seconds=12)
    assert attempt.selected_leg == NO
    assert attempt.entry_ask == Decimal("0.46")
    assert attempt.terminal_status == "REVERSAL_EXIT"
    assert attempt.terminal_at == START + timedelta(seconds=14)
    assert attempt.exit_bid == Decimal("0.48")
    assert attempt.diagnostic_quantity == Decimal(5)
    assert attempt.gross_touch_pnl_per_share == Decimal("0.02")
    assert attempt.net_touch_pnl_per_share == Decimal("0.015")


def test_negative_shock_buys_yes_and_continuation_is_a_market_touch_stop() -> None:
    """The opposite shock sign selects YES without shorting and records continuation loss."""
    registration = _registration(
        _snapshot(YES, seconds=0, bid="0.49", ask="0.51"),
        _snapshot(NO, seconds=0, bid="0.49", ask="0.51"),
        *_top_change(
            YES,
            seconds=10,
            seq=2,
            old_bid="0.49",
            old_ask="0.51",
            new_bid="0.45",
            new_ask="0.47",
        ),
        *_top_change(
            YES,
            seconds=15,
            seq=3,
            old_bid="0.45",
            old_ask="0.47",
            new_bid="0.42",
            new_ask="0.44",
            bid_size="4",
        ),
    )

    result = screen_book_post_jump_reversal(
        registration,
        _definition(action_delay=timedelta(0)),
    )

    attempt = result.attempts[0]
    assert attempt.shock_sign == -1
    assert attempt.selected_leg == YES
    assert attempt.entry_ask == Decimal("0.47")
    assert attempt.terminal_status == "CONTINUATION_EXIT"
    assert attempt.exit_bid == Decimal("0.42")
    assert attempt.diagnostic_quantity == Decimal(4)
    assert attempt.gross_touch_pnl_per_share == Decimal("-0.05")


def test_stale_complement_is_no_entry_not_zero_return() -> None:
    """A favorable signal cannot forward-fill an over-age NO ask into an entered trade."""
    registration = _registration(
        _snapshot(YES, seconds=0, bid="0.49", ask="0.51"),
        _snapshot(NO, seconds=0, bid="0.49", ask="0.51"),
        *_top_change(
            YES,
            seconds=10,
            seq=2,
            old_bid="0.49",
            old_ask="0.51",
            new_bid="0.53",
            new_ask="0.55",
        ),
    )

    attempt = screen_book_post_jump_reversal(registration, _definition()).attempts[0]

    assert attempt.terminal_status == "NO_ENTRY_QUOTE"
    assert attempt.entry_ask is None
    assert attempt.net_touch_pnl_per_share is None


def test_stale_selected_exit_is_missing_and_suppresses_later_overlapping_shock() -> None:
    """A threshold without a fresh exit bid leaves PnL missing and the position unresolved."""
    registration = _registration(
        _snapshot(YES, seconds=0, bid="0.49", ask="0.51"),
        _snapshot(NO, seconds=0, bid="0.49", ask="0.51"),
        *_top_change(
            YES,
            seconds=10,
            seq=2,
            old_bid="0.49",
            old_ask="0.51",
            new_bid="0.53",
            new_ask="0.55",
        ),
        *_top_change(
            NO,
            seconds=10,
            seq=2,
            old_bid="0.49",
            old_ask="0.51",
            new_bid="0.44",
            new_ask="0.46",
        ),
        *_top_change(
            YES,
            seconds=20,
            seq=3,
            old_bid="0.53",
            old_ask="0.55",
            new_bid="0.50",
            new_ask="0.52",
        ),
        *_top_change(
            YES,
            seconds=25,
            seq=4,
            old_bid="0.50",
            old_ask="0.52",
            new_bid="0.54",
            new_ask="0.56",
        ),
    )

    result = screen_book_post_jump_reversal(
        registration,
        _definition(action_delay=timedelta(0)),
    )

    assert result.raw_shock_count == THREE_SHOCKS
    assert result.ignored_overlapping_shock_count == TWO_SHOCKS
    attempt = result.attempts[0]
    assert attempt.terminal_status == "MISSING_EXIT_QUOTE"
    assert attempt.exit_reference_midpoint == Decimal("0.51")
    assert attempt.exit_bid is None
    assert attempt.net_touch_pnl_per_share is None


def test_incomplete_holding_coverage_is_truncated_not_timeout() -> None:
    """A corpus ending before the fixed deadline cannot manufacture a terminal quote."""
    registration = _registration(
        _snapshot(YES, seconds=0, bid="0.49", ask="0.51"),
        _snapshot(NO, seconds=0, bid="0.49", ask="0.51"),
        *_top_change(
            YES,
            seconds=10,
            seq=2,
            old_bid="0.49",
            old_ask="0.51",
            new_bid="0.53",
            new_ask="0.55",
        ),
        *_top_change(
            NO,
            seconds=10,
            seq=2,
            old_bid="0.49",
            old_ask="0.51",
            new_bid="0.44",
            new_ask="0.46",
        ),
        end_seconds=25,
    )

    attempt = screen_book_post_jump_reversal(
        registration,
        _definition(action_delay=timedelta(0)),
    ).attempts[0]

    assert attempt.terminal_status == "TRUNCATED"
    assert attempt.terminal_at == START + timedelta(seconds=25)
    assert attempt.entry_ask == Decimal("0.46")
    assert attempt.exit_bid is None


def test_complete_holding_coverage_uses_fresh_timeout_touch() -> None:
    """No threshold crossing exits at the fixed deadline with current displayed size and cost."""
    registration = _registration(
        _snapshot(YES, seconds=0, bid="0.49", ask="0.51"),
        _snapshot(NO, seconds=0, bid="0.49", ask="0.51"),
        *_top_change(
            YES,
            seconds=10,
            seq=2,
            old_bid="0.49",
            old_ask="0.51",
            new_bid="0.53",
            new_ask="0.55",
        ),
        *_top_change(
            NO,
            seconds=10,
            seq=2,
            old_bid="0.49",
            old_ask="0.51",
            new_bid="0.44",
            new_ask="0.46",
            ask_size="8",
        ),
        *_top_change(
            YES,
            seconds=20,
            seq=3,
            old_bid="0.53",
            old_ask="0.55",
            new_bid="0.54",
            new_ask="0.56",
        ),
        *_top_change(
            NO,
            seconds=20,
            seq=3,
            old_bid="0.44",
            old_ask="0.46",
            new_bid="0.45",
            new_ask="0.47",
            bid_size="6",
        ),
    )

    attempt = screen_book_post_jump_reversal(
        registration,
        _definition(
            action_delay=timedelta(0),
            maximum_holding_period=timedelta(seconds=10),
        ),
    ).attempts[0]

    assert attempt.terminal_status == "TIMEOUT_EXIT"
    assert attempt.terminal_at == START + timedelta(seconds=20)
    assert attempt.exit_bid == Decimal("0.45")
    assert attempt.diagnostic_quantity == Decimal(6)
    assert attempt.gross_touch_pnl_per_share == Decimal("-0.01")
    assert attempt.net_touch_pnl_per_share == Decimal("-0.015")


def test_scope_authority_and_exact_leg_population_fail_before_replay() -> None:
    """The screen cannot reinterpret a corpus under different binary authority or legs."""
    registration = _registration(
        _snapshot(YES, seconds=0, bid="0.49", ask="0.51"),
        _snapshot(NO, seconds=0, bid="0.49", ask="0.51"),
    )

    with pytest.raises(ValueError, match="scope authority"):
        screen_book_post_jump_reversal(
            registration,
            _definition(scope_authority_ref="binary-outcomes:other"),
        )
    with pytest.raises(ValueError, match="exactly match"):
        screen_book_post_jump_reversal(
            registration,
            _definition(complement_leg=BookLeg("polymarket", "condition-id", 2)),
        )
