"""Causal clock and quiet-duration adversaries for retained L2 events."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from research_agent.data_adapters.polymarket.book_activity import (
    BookActivityDefinition,
    BookActivitySeries,
    build_book_activity_series,
    coalesce_book_source_events,
)
from research_agent.data_adapters.polymarket.book_corpus import (
    BookCorpus,
    BookCorpusRequest,
    BookCorpusSnapshot,
    BookCorpusSnapshotRef,
    BookCorpusStore,
    BookDeltaRecord,
    BookLeg,
    BookSnapshotRecord,
    register_book_corpus,
)

START = datetime(2026, 8, 23, 12, tzinfo=UTC)
END = START + timedelta(minutes=1)
YES = BookLeg("polymarket", "market-1", 0)
NO = BookLeg("polymarket", "market-1", 1)
KALSHI = BookLeg("kalshi", "KX-MARKET", 0)
RECENT_WINDOW = timedelta(seconds=5)
SHARED_SEQUENCE = 3
EXPECTED_SHARED_ROWS = 3
EXPECTED_VENUE_EVENTS = 2
EXPECTED_ACTIVITY_POINTS = 3
EXPECTED_CONCURRENT_EVENTS = 2
EXPECTED_POSITIVE_DELAYS = 2


def _snapshot(
    leg: BookLeg,
    *,
    available_at: datetime,
    reference_time: datetime | None = None,
    seq: int,
) -> BookSnapshotRecord:
    return BookSnapshotRecord(
        leg=leg,
        ts=available_at,
        reference_time=reference_time or available_at,
        seq=seq,
        bids=(("0.44", "10"), ("0.40", "20")),
        asks=(("0.46", "11"), ("0.50", "21")),
        raw={"kind": "snapshot", "seq": seq},
    )


def _delta(
    leg: BookLeg,
    *,
    available_at: datetime,
    reference_time: datetime | None = None,
    seq: int,
    price: str = "0.44",
) -> BookDeltaRecord:
    return BookDeltaRecord(
        leg=leg,
        ts=available_at,
        reference_time=reference_time or available_at,
        seq=seq,
        side="BID",
        price=Decimal(price),
        size=Decimal(12),
        raw={"kind": "delta", "seq": seq, "price": price},
    )


def _corpus(*events: BookSnapshotRecord | BookDeltaRecord) -> BookCorpus:
    legs = tuple(sorted({event.leg for event in events}))
    request = BookCorpusRequest(
        environment_id="test-book-activity",
        scope_authority_ref="scope:activity-test",
        legs=legs,
        start_at=START,
        end_at=END,
    )
    return BookCorpus(request, tuple(sorted(events, key=lambda event: event.sort_key)))


def _series(
    *events: BookSnapshotRecord | BookDeltaRecord,
    recent_window: timedelta = RECENT_WINDOW,
) -> BookActivitySeries:
    snapshot = BookCorpusStore.from_corpus(_corpus(*events))
    return build_book_activity_series(snapshot, BookActivityDefinition(recent_window))


def test_multirow_cross_leg_message_is_one_source_event() -> None:
    """One venue message cannot become one activity event per row or outcome leg."""
    shared_time = START + timedelta(seconds=3)
    events = (
        _snapshot(YES, available_at=START, seq=1),
        _snapshot(NO, available_at=START + timedelta(microseconds=1), seq=2),
        _delta(
            YES,
            available_at=shared_time,
            reference_time=shared_time - timedelta(milliseconds=5),
            seq=SHARED_SEQUENCE,
        ),
        _delta(
            YES,
            available_at=shared_time,
            reference_time=shared_time - timedelta(milliseconds=5),
            seq=SHARED_SEQUENCE,
            price="0.43",
        ),
        _delta(
            NO,
            available_at=shared_time,
            reference_time=shared_time - timedelta(milliseconds=5),
            seq=SHARED_SEQUENCE,
        ),
    )

    source_event = next(
        event
        for event in coalesce_book_source_events(_corpus(*events))
        if event.seq == SHARED_SEQUENCE
    )

    assert source_event.kind == "DELTA"
    assert source_event.legs == (YES, NO)
    assert source_event.row_count == EXPECTED_SHARED_ROWS


def test_identical_cross_venue_clocks_and_sequences_remain_separate() -> None:
    """Venue identity prevents unrelated connections from sharing one message."""
    events = (
        _snapshot(KALSHI, available_at=START, seq=7),
        _snapshot(YES, available_at=START, seq=7),
    )

    source_events = coalesce_book_source_events(_corpus(*events))

    assert len(source_events) == EXPECTED_VENUE_EVENTS
    assert tuple(event.venue for event in source_events) == ("kalshi", "polymarket")


def test_same_time_messages_publish_one_point_and_exclude_current_burst() -> None:
    """Same-time source messages are legal together but absent from their prior count."""
    events = (
        _snapshot(YES, available_at=START, seq=1),
        _delta(YES, available_at=START + timedelta(seconds=2), seq=2),
        _delta(YES, available_at=START + timedelta(seconds=6), seq=3),
        _delta(
            YES,
            available_at=START + timedelta(seconds=6),
            reference_time=START + timedelta(seconds=5, milliseconds=999),
            seq=4,
            price="0.43",
        ),
    )

    series = _series(*events)
    last = series.points[-1]

    assert len(series.points) == EXPECTED_ACTIVITY_POINTS
    assert last.decision_time == START + timedelta(seconds=6)
    assert last.concurrent_source_event_count == EXPECTED_CONCURRENT_EVENTS
    assert last.quiet_duration == timedelta(seconds=4)
    assert last.recent_source_event_count == 1


def test_left_truncation_and_lookback_warmup_remain_missing() -> None:
    """Corpus start cannot be substituted for unseen prior activity history."""
    events = (
        _snapshot(YES, available_at=START + timedelta(seconds=1), seq=1),
        _delta(YES, available_at=START + timedelta(seconds=3), seq=2),
        _delta(YES, available_at=START + timedelta(seconds=7), seq=3),
    )

    series = _series(*events)
    first, warmup, complete = series.points

    assert first.previous_event_time is None
    assert first.quiet_duration is None
    assert first.recent_source_event_count is None
    assert warmup.quiet_duration == timedelta(seconds=2)
    assert warmup.recent_source_event_count is None
    assert complete.quiet_duration == timedelta(seconds=4)
    assert complete.recent_source_event_count == 1


def test_clock_profile_separates_skew_zero_and_positive_delay() -> None:
    """Negative skew and fallback-like equality remain visible outside latency quantiles."""
    delays = (
        timedelta(milliseconds=-1),
        timedelta(0),
        timedelta(milliseconds=10),
        timedelta(milliseconds=30),
    )
    events = tuple(
        _snapshot(
            YES,
            available_at=START + timedelta(seconds=index),
            reference_time=START + timedelta(seconds=index) - delay,
            seq=index,
        )
        for index, delay in enumerate(delays, start=1)
    )

    profile = _series(*events).clock_profiles[0]

    assert profile.negative_delay_count == 1
    assert profile.zero_delay_count == 1
    assert profile.positive_delay_count == EXPECTED_POSITIVE_DELAYS
    assert profile.signed_delay_min == timedelta(milliseconds=-1)
    assert profile.signed_delay_max == timedelta(milliseconds=30)
    assert profile.nonnegative_p50 == timedelta(milliseconds=10)
    assert profile.nonnegative_p90 == timedelta(milliseconds=30)
    assert profile.nonnegative_p95 == timedelta(milliseconds=30)
    assert profile.nonnegative_p99 == timedelta(milliseconds=30)


def test_activity_point_carries_current_signed_delay_range() -> None:
    """A same-time burst exposes clock disagreement without changing its decision count."""
    current = START + timedelta(seconds=6)
    events = (
        _snapshot(YES, available_at=START, seq=1),
        _delta(
            YES,
            available_at=current,
            reference_time=current + timedelta(milliseconds=2),
            seq=2,
        ),
        _delta(
            YES,
            available_at=current,
            reference_time=current - timedelta(milliseconds=7),
            seq=3,
            price="0.43",
        ),
    )

    point = _series(*events).points[-1]

    assert point.reference_delay_min == timedelta(milliseconds=-2)
    assert point.reference_delay_max == timedelta(milliseconds=7)
    assert point.source_event_sequences == (2, 3)


def test_ambiguous_snapshot_and_delta_identity_fails_closed() -> None:
    """One venue/clock/sequence identity cannot silently split across row kinds."""
    anchor = _snapshot(YES, available_at=START, seq=1)
    ambiguous = _delta(YES, available_at=START, seq=1)

    with pytest.raises(ValueError, match="row kinds"):
        coalesce_book_source_events(_corpus(anchor, ambiguous))


@pytest.mark.parametrize("recent_window", [timedelta(0), timedelta(microseconds=-1)])
def test_activity_definition_requires_positive_elapsed_window(recent_window: timedelta) -> None:
    """An empty or reversed elapsed window cannot acquire implicit semantics."""
    with pytest.raises(ValueError, match="positive"):
        BookActivityDefinition(recent_window)


def test_detached_snapshot_identity_fails_before_feature_derivation() -> None:
    """Timing features cannot cite a snapshot hash that does not own their source rows."""
    corpus = _corpus(_snapshot(YES, available_at=START, seq=1))
    snapshot = BookCorpusStore.from_corpus(corpus)
    detached = BookCorpusSnapshot(
        BookCorpusSnapshotRef("0" * 64, snapshot.ref.size_bytes),
        corpus,
    )

    with pytest.raises(ValueError, match="identity"):
        build_book_activity_series(detached, BookActivityDefinition(RECENT_WINDOW))


def test_series_preserves_snapshot_scope_and_definition_identity() -> None:
    """Downstream gates can reconstruct the source, authority, and exact lookback."""
    corpus = _corpus(_snapshot(YES, available_at=START, seq=1))
    snapshot = BookCorpusStore.from_corpus(corpus)
    definition = BookActivityDefinition(RECENT_WINDOW)

    series = build_book_activity_series(snapshot, definition)

    assert series.snapshot_ref == snapshot.ref
    assert series.environment_id == corpus.request.environment_id
    assert series.scope_authority_ref == corpus.request.scope_authority_ref
    assert series.start_at == START
    assert series.end_at == END
    assert series.definition == definition


def test_activity_clock_composes_with_every_replayed_book_state() -> None:
    """Existing strategy states can join activity only on the same legal collector clock."""
    corpus = _corpus(
        _snapshot(YES, available_at=START, seq=1),
        _delta(YES, available_at=START + timedelta(seconds=2), seq=2),
    )
    snapshot = BookCorpusStore.from_corpus(corpus)
    registration = register_book_corpus(snapshot)
    series = build_book_activity_series(snapshot, BookActivityDefinition(RECENT_WINDOW))
    activity_keys = {(point.leg, point.decision_time) for point in series.points}

    assert {(state.leg, state.available_at) for state in registration.states} <= activity_keys
