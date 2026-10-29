"""Causal adversaries for the LL-01 gross payout-dominance screen."""

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
    PayoutDominanceDefinition,
    register_book_corpus,
    screen_gross_payout_dominance,
)

START = datetime(2026, 8, 23, 10, 0, tzinfo=UTC)
END = START + timedelta(minutes=1)
AUTHORITY = "semantic-audit:75ec8496452816964f4db6749c1ba90d"
KALSHI = BookLeg("kalshi", "kx-market", 0)
PM = BookLeg("polymarket", "pm-market", 1)


def _snapshot(
    leg: BookLeg,
    *,
    seconds: int,
    seq: int,
    ask: str,
    ask_size: str = "8",
) -> BookSnapshotRecord:
    ts = START + timedelta(seconds=seconds)
    return BookSnapshotRecord(
        leg=leg,
        ts=ts,
        reference_time=ts - timedelta(milliseconds=100),
        seq=seq,
        bids=((str(Decimal(ask) - Decimal("0.02")), "10"),),
        asks=((ask, ask_size),),
        raw={"kind": "snapshot"},
    )


def _ask_change(
    leg: BookLeg,
    *,
    seconds: int,
    seq: int,
    old: str,
    new: str,
) -> tuple[BookDeltaRecord, BookDeltaRecord]:
    ts = START + timedelta(seconds=seconds)
    reference_time = ts - timedelta(milliseconds=100)
    return (
        BookDeltaRecord(
            leg,
            ts,
            reference_time,
            seq,
            "ASK",
            Decimal(old),
            Decimal(0),
            {"kind": "delta"},
        ),
        BookDeltaRecord(
            leg,
            ts,
            reference_time,
            seq,
            "ASK",
            Decimal(new),
            Decimal(6),
            {"kind": "delta"},
        ),
    )


def _registration(
    *, same_time: bool = False, pm_initial_ask: str = "0.55"
) -> BookCorpusRegistration:
    pm_seconds = 1 if same_time else 2
    events = (
        _snapshot(KALSHI, seconds=1, seq=1, ask="0.40", ask_size="7"),
        _snapshot(PM, seconds=pm_seconds, seq=1, ask=pm_initial_ask, ask_size="5"),
        *_ask_change(PM, seconds=3, seq=2, old=pm_initial_ask, new="0.65"),
    )
    request = BookCorpusRequest(
        "ll-01-development",
        AUTHORITY,
        (KALSHI, PM),
        START,
        END,
    )
    corpus = BookCorpus(request, tuple(sorted(events, key=lambda item: item.sort_key)))
    return register_book_corpus(BookCorpusStore.from_corpus(corpus))


def _definition(**changes: object) -> PayoutDominanceDefinition:
    definition = PayoutDominanceDefinition(
        definition_id="ll01-gross-v1",
        scope_authority_ref=AUTHORITY,
        first_leg=KALSHI,
        second_leg=PM,
        payout_floor=Decimal(1),
        minimum_gross_edge=Decimal("0.01"),
        maximum_quote_age=timedelta(seconds=5),
        action_delay=timedelta(0),
    )
    return replace(definition, **changes)


def test_definition_requires_exact_direction_and_positive_time_limits() -> None:
    """A pair cannot alias one leg or silently accept invalid latency policy."""
    with pytest.raises(ValueError, match="distinct"):
        _definition(second_leg=KALSHI)
    with pytest.raises(ValueError, match="quote age"):
        _definition(maximum_quote_age=timedelta(0))
    with pytest.raises(ValueError, match="action delay"):
        _definition(action_delay=timedelta(seconds=-1))


def test_signal_uses_latest_legal_other_leg_not_future_nearest_quote() -> None:
    """The adverse PM update at second three cannot erase the legal second-two signal."""
    result = screen_gross_payout_dominance(_registration(), _definition())

    assert tuple(item.decision_at for item in result.opportunities) == (
        START + timedelta(seconds=2),
    )
    opportunity = result.opportunities[0]
    assert opportunity.decision_gross_edge == Decimal("0.05")
    assert opportunity.decision_quantity == Decimal(5)
    assert opportunity.delayed_gross_edge == Decimal("0.05")
    assert opportunity.displayed_edge_survives_delay is True


def test_fixed_delay_reports_adverse_arrival_without_rewriting_signal() -> None:
    """A later quote changes the arrival diagnostic but not the original decision record."""
    result = screen_gross_payout_dominance(
        _registration(),
        _definition(action_delay=timedelta(seconds=2)),
    )

    opportunity = result.opportunities[0]
    assert opportunity.decision_gross_edge == Decimal("0.05")
    assert opportunity.delayed_gross_edge == Decimal("-0.05")
    assert opportunity.displayed_edge_survives_delay is False


def test_same_collector_time_is_coalesced_into_one_decision() -> None:
    """Both legs becoming available together creates one union-clock decision."""
    result = screen_gross_payout_dominance(_registration(same_time=True), _definition())

    assert len(result.opportunities) == 1
    assert result.opportunities[0].trigger_legs == (KALSHI, PM)


def test_stale_other_leg_blocks_signal() -> None:
    """A favorable but over-age quote cannot be forward-filled into a candidate."""
    result = screen_gross_payout_dominance(
        _registration(),
        _definition(maximum_quote_age=timedelta(milliseconds=500)),
    )

    assert result.opportunities == ()


def test_equality_to_payout_floor_is_not_positive_dominance() -> None:
    """A zero gross edge fails even when the configured minimum is zero."""
    registration = _registration(pm_initial_ask="0.60")

    result = screen_gross_payout_dominance(
        registration,
        _definition(minimum_gross_edge=Decimal(0)),
    )

    assert result.opportunities == ()


def test_scope_authority_or_leg_mismatch_fails_before_screening() -> None:
    """The screen cannot reinterpret states under a different semantic permission."""
    with pytest.raises(ValueError, match="scope authority"):
        screen_gross_payout_dominance(
            _registration(),
            _definition(scope_authority_ref="semantic-audit:other"),
        )
    with pytest.raises(ValueError, match="exactly match"):
        screen_gross_payout_dominance(
            _registration(),
            _definition(second_leg=BookLeg("polymarket", "other", 1)),
        )
