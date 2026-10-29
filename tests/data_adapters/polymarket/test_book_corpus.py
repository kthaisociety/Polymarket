"""Adversaries for exact dual-clock L2 retention and temporal registration."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

from research_agent.data_adapters.polymarket import (
    BookCorpus,
    BookCorpusRequest,
    BookCorpusStore,
    BookDeltaRecord,
    BookLeg,
    BookSnapshotRecord,
    DatabaseBookCorpusReader,
    register_book_corpus,
)
from research_agent.data_foundation import InformationSetBuilder

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

START = datetime(2026, 8, 23, 10, 0, tzinfo=UTC)
END = START + timedelta(minutes=1)
PM = BookLeg("polymarket", "pm-market", 1)
KALSHI = BookLeg("kalshi", "kx-market", 0)
LEGS = (KALSHI, PM)
EXPECTED_QUERY_COUNT = 2
EXPECTED_PM_OBSERVATION_COUNT = 18


def _request() -> BookCorpusRequest:
    return BookCorpusRequest(
        "ll-01-development",
        "semantic-audit:75ec8496452816964f4db6749c1ba90d",
        LEGS,
        START,
        END,
    )


def _snapshot(
    leg: BookLeg,
    *,
    ts: datetime = START + timedelta(seconds=1),
    reference_time: datetime = START + timedelta(milliseconds=900),
    seq: int = 1,
) -> BookSnapshotRecord:
    return BookSnapshotRecord(
        leg=leg,
        ts=ts,
        reference_time=reference_time,
        seq=seq,
        bids=(("0.44", "10"),),
        asks=(("0.46", "8"),),
        raw={"kind": "snapshot"},
    )


def _delta(
    leg: BookLeg,
    *,
    ts: datetime = START + timedelta(seconds=2),
    reference_time: datetime = START + timedelta(seconds=1, milliseconds=900),
    seq: int = 2,
) -> BookDeltaRecord:
    return BookDeltaRecord(
        leg=leg,
        ts=ts,
        reference_time=reference_time,
        seq=seq,
        side="BID",
        price=Decimal("0.45"),
        size=Decimal(7),
        raw={"kind": "delta"},
    )


def _corpus() -> BookCorpus:
    events = tuple(
        sorted(
            (_snapshot(KALSHI), _snapshot(PM), _delta(KALSHI), _delta(PM)),
            key=lambda item: item.sort_key,
        )
    )
    return BookCorpus(_request(), events)


class _Executor:
    """Protocol-compatible fake that exposes the exact two SELECT boundaries."""

    def __init__(self, *, legacy_snapshot: bool = False) -> None:
        self.legacy_snapshot = legacy_snapshot
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    async def fetch(self, query: str, *args: object) -> Sequence[Mapping[str, object]]:
        self.calls.append((query, args))
        if "FROM market.book_snapshots" in query:
            return [
                {
                    "venue": leg.venue,
                    "market_id": leg.market_id,
                    "outcome_index": leg.outcome_index,
                    "ts": START + timedelta(seconds=1),
                    "reference_time": (
                        None
                        if self.legacy_snapshot and leg == PM
                        else START + timedelta(milliseconds=900)
                    ),
                    "seq": 1,
                    "bids": [["0.44", "10"]],
                    "asks": [["0.46", "8"]],
                    "raw": {"kind": "snapshot"},
                }
                for leg in LEGS
            ]
        if "FROM market.book_deltas" in query:
            return [
                {
                    "venue": leg.venue,
                    "market_id": leg.market_id,
                    "outcome_index": leg.outcome_index,
                    "ts": START + timedelta(seconds=2),
                    "reference_time": START + timedelta(seconds=1, milliseconds=900),
                    "seq": 2,
                    "side": "BID",
                    "price": Decimal("0.45"),
                    "size": Decimal(7),
                    "raw": {"kind": "delta"},
                }
                for leg in LEGS
            ]
        message = "unexpected SQL"
        raise AssertionError(message)


def _read(executor: _Executor | None = None) -> BookCorpus:
    reader = DatabaseBookCorpusReader(executor or _Executor())
    return asyncio.run(reader.read_corpus(_request()))


def test_request_requires_canonical_exact_legs_and_half_open_time_window() -> None:
    """Order ambiguity and empty collector windows fail before any read."""
    with pytest.raises(ValueError, match="scope-authority"):
        BookCorpusRequest("env", "", LEGS, START, END)
    with pytest.raises(ValueError, match="canonical"):
        BookCorpusRequest("env", "scope-authority", tuple(reversed(LEGS)), START, END)
    with pytest.raises(ValueError, match="half-open"):
        BookCorpusRequest("env", "scope-authority", LEGS, END, START)


def test_reader_uses_parameterized_scope_and_dual_clock_predicate() -> None:
    """Both source tables use the same exact legs, bounds, and legacy exclusion."""
    executor = _Executor()

    corpus = _read(executor)

    assert corpus == _corpus()
    assert len(executor.calls) == EXPECTED_QUERY_COUNT
    for query, args in executor.calls:
        assert "reference_time IS NOT NULL" in query
        assert "ts >=" in query
        assert "ts <" in query
        assert args == (
            tuple(leg.venue for leg in LEGS),
            tuple(leg.market_id for leg in LEGS),
            tuple(leg.outcome_index for leg in LEGS),
            START,
            END,
        )


def test_legacy_null_fails_even_if_executor_violates_sql_predicate() -> None:
    """A bad executor cannot smuggle pre-change clock semantics into the corpus."""
    with pytest.raises(TypeError, match="reference_time"):
        _read(_Executor(legacy_snapshot=True))


def test_corpus_rejects_foreign_or_out_of_window_rows() -> None:
    """Python validation independently enforces SQL leg and time scope."""
    corpus = _corpus()
    foreign = _snapshot(BookLeg("kalshi", "foreign", 0))
    foreign_events = tuple(sorted((*corpus.events, foreign), key=lambda item: item.sort_key))
    with pytest.raises(ValueError, match="requested leg"):
        replace(corpus, events=foreign_events)
    late = _delta(PM, ts=END)
    late_events = tuple(sorted((*corpus.events, late), key=lambda item: item.sort_key))
    with pytest.raises(ValueError, match="collector-time window"):
        replace(corpus, events=late_events)


def test_corpus_requires_snapshot_anchor_for_every_leg() -> None:
    """Deltas alone cannot create an initial book state."""
    events = tuple(item for item in _corpus().events if not isinstance(item, BookSnapshotRecord))
    with pytest.raises(ValueError, match="snapshot anchor"):
        BookCorpus(_request(), events)


def test_replay_registers_distinct_reference_and_availability_clocks() -> None:
    """Venue time describes the event while collector time gates admissibility."""
    registration = register_book_corpus(BookCorpusStore.from_corpus(_corpus()))
    bid_ref = registration.dataset.schema.field_ref("best_bid_price")
    pm_bid = tuple(
        item
        for item in registration.dataset.observations
        if item.field_ref == bid_ref and dict(item.dimensions)["venue"] == "polymarket"
    )

    assert tuple(item.value for item in pm_bid) == (0.44, 0.45)
    assert pm_bid[0].reference_time == START + timedelta(milliseconds=900)
    assert pm_bid[0].available_at == START + timedelta(seconds=1)
    assert pm_bid[0].availability_rule_version == "decoded-book-collector-absorb/v1"
    before_absorb = InformationSetBuilder().build(
        registration.catalog,
        decision_time=START + timedelta(milliseconds=950),
        requested_fields=(bid_ref,),
    )
    assert before_absorb.for_field(bid_ref) == ()


def test_replay_preserves_and_registers_complete_best_first_depth() -> None:
    """Far levels remain causal registered data rather than disappearing behind the touch."""
    deep_pm = replace(
        _snapshot(PM),
        bids=(("0.44", "10"), ("0.40", "30"), ("0.10", "50")),
        asks=(("0.46", "8"), ("0.60", "20"), ("0.90", "40")),
    )
    corpus = BookCorpus(
        _request(),
        tuple(
            sorted(
                (
                    _snapshot(KALSHI),
                    deep_pm,
                    _delta(KALSHI),
                    _delta(PM),
                ),
                key=lambda item: item.sort_key,
            )
        ),
    )

    registration = register_book_corpus(BookCorpusStore.from_corpus(corpus))
    first_pm = next(state for state in registration.states if state.leg == PM)
    depth_size_ref = registration.dataset.schema.field_ref("depth_size")
    first_pm_sizes = tuple(
        item
        for item in registration.dataset.observations
        if item.field_ref == depth_size_ref
        and dict(item.dimensions)["venue"] == "polymarket"
        and dict(item.dimensions)["event_ordinal"] == "0"
    )

    assert first_pm.bid_levels == (
        (Decimal("0.44"), Decimal(10)),
        (Decimal("0.40"), Decimal(30)),
        (Decimal("0.10"), Decimal(50)),
    )
    assert first_pm.ask_levels == (
        (Decimal("0.46"), Decimal(8)),
        (Decimal("0.60"), Decimal(20)),
        (Decimal("0.90"), Decimal(40)),
    )
    assert tuple((dict(item.dimensions)["side"], item.value) for item in first_pm_sizes) == (
        ("BID", 10.0),
        ("BID", 30.0),
        ("BID", 50.0),
        ("ASK", 8.0),
        ("ASK", 20.0),
        ("ASK", 40.0),
    )
    assert all(item.available_at == START + timedelta(seconds=1) for item in first_pm_sizes)


def test_delta_before_first_snapshot_is_not_published() -> None:
    """An in-window pre-anchor delta remains retained but cannot become state."""
    early = _delta(PM, ts=START + timedelta(milliseconds=500), seq=0)
    corpus = BookCorpus(
        _request(),
        tuple(sorted((*_corpus().events, early), key=lambda item: item.sort_key)),
    )

    registration = register_book_corpus(BookCorpusStore.from_corpus(corpus))

    pm_rows = tuple(
        item
        for item in registration.dataset.observations
        if dict(item.dimensions)["venue"] == "polymarket"
    )
    assert len(pm_rows) == EXPECTED_PM_OBSERVATION_COUNT


def test_crossed_replay_state_fails_closed() -> None:
    """A non-executable replay state aborts the registration."""
    crossed = replace(_delta(PM), price=Decimal("0.47"))
    corpus = BookCorpus(
        _request(),
        tuple(
            sorted(
                (
                    *(item for item in _corpus().events if item != _delta(PM)),
                    crossed,
                ),
                key=lambda item: item.sort_key,
            )
        ),
    )
    with pytest.raises(ValueError, match="crossed"):
        register_book_corpus(BookCorpusStore.from_corpus(corpus))


def test_retained_bytes_are_content_addressed_and_tamper_evident(tmp_path: Path) -> None:
    """The immutable object, not the mutable database query, anchors identity."""
    store = BookCorpusStore(tmp_path)
    retained = store.retain(_corpus())

    assert store.load(retained.ref) == store.from_corpus(_corpus())
    path = store.object_path(retained.ref)
    path.write_bytes(path.read_bytes() + b"tampered")
    assert not store.verify(retained.ref)
