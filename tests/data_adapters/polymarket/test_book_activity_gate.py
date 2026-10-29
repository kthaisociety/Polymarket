"""Paired H4a activity-gate adversaries over unchanged H3/H5 attempts."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from research_agent.data_adapters.polymarket.book_activity import (
    BookActivityDefinition,
    BookActivitySeries,
    build_book_activity_series,
)
from research_agent.data_adapters.polymarket.book_activity_gate import (
    ActivityParticipationGateDefinition,
    compare_activity_gate_rivals,
    compare_activity_participation_gate,
)
from research_agent.data_adapters.polymarket.book_corpus import (
    BookCorpus,
    BookCorpusRequest,
    BookCorpusStore,
    BookDeltaRecord,
    BookLeg,
    BookSnapshotRecord,
)
from research_agent.data_adapters.polymarket.book_imbalance import (
    DepthImbalanceAttempt,
    DepthImbalanceDefinition,
    DepthImbalanceMetrics,
    DepthImbalanceScreen,
)
from research_agent.data_adapters.polymarket.low_latency import (
    PostJumpReversalAttempt,
    PostJumpReversalDefinition,
    PostJumpReversalScreen,
    PostJumpTerminalStatus,
)

START = datetime(2026, 8, 23, 12, tzinfo=UTC)
END = START + timedelta(minutes=1)
YES = BookLeg("polymarket", "market-1", 0)
NO = BookLeg("polymarket", "market-1", 1)
RECENT_WINDOW = timedelta(seconds=5)
MAXIMUM_QUIET = timedelta(seconds=3)
ROUND_TRIP_COST = Decimal("0.01")
ENTRY_ASK = Decimal("0.50")
DIAGNOSTIC_QUANTITY = Decimal(2)
EXPECTED_PARENT_ATTEMPTS = 5
EXPECTED_ENTERED_ATTEMPTS = 4
EXPECTED_SCORABLE_ATTEMPTS = 4


def _snapshot(leg: BookLeg, *, at: datetime, seq: int) -> BookSnapshotRecord:
    return BookSnapshotRecord(
        leg=leg,
        ts=at,
        reference_time=at,
        seq=seq,
        bids=(("0.44", "10"),),
        asks=(("0.46", "11"),),
        raw={"kind": "snapshot", "seq": seq},
    )


def _delta(*, at: datetime, seq: int) -> BookDeltaRecord:
    return BookDeltaRecord(
        leg=YES,
        ts=at,
        reference_time=at,
        seq=seq,
        side="BID",
        price=Decimal("0.44"),
        size=Decimal(10 + seq),
        raw={"kind": "delta", "seq": seq},
    )


def _activity() -> BookActivitySeries:
    events = (
        _snapshot(YES, at=START, seq=1),
        _snapshot(NO, at=START + timedelta(microseconds=1), seq=2),
        _delta(at=START + timedelta(seconds=2), seq=3),
        _delta(at=START + timedelta(seconds=5), seq=4),
        _delta(at=START + timedelta(seconds=6), seq=5),
        _delta(at=START + timedelta(seconds=7, microseconds=500_000), seq=6),
        _delta(at=START + timedelta(seconds=8), seq=7),
        _delta(at=START + timedelta(seconds=12), seq=8),
        _delta(at=START + timedelta(seconds=14), seq=9),
        _delta(at=START + timedelta(seconds=20), seq=10),
    )
    request = BookCorpusRequest(
        environment_id="test-h4a",
        scope_authority_ref="scope:h4a",
        legs=(YES, NO),
        start_at=START,
        end_at=END,
    )
    corpus = BookCorpus(request, tuple(sorted(events, key=lambda event: event.sort_key)))
    snapshot = BookCorpusStore.from_corpus(corpus)
    return build_book_activity_series(snapshot, BookActivityDefinition(RECENT_WINDOW))


def _post_jump_definition() -> PostJumpReversalDefinition:
    return PostJumpReversalDefinition(
        definition_id="ll03-parent",
        scope_authority_ref="scope:h4a",
        reference_leg=YES,
        complement_leg=NO,
        minimum_midpoint_shock=Decimal("0.02"),
        maximum_shock_gap=timedelta(seconds=10),
        action_delay=timedelta(seconds=1),
        maximum_quote_age=timedelta(seconds=5),
        reversal_distance=Decimal("0.02"),
        continuation_distance=Decimal("0.02"),
        maximum_holding_period=timedelta(seconds=10),
        minimum_entry_quantity=Decimal(1),
        round_trip_cost_per_share=ROUND_TRIP_COST,
    )


def _post_jump_attempt(
    decision_at: datetime,
    *,
    net_pnl: Decimal | None,
    entered: bool = True,
    status: PostJumpTerminalStatus = "REVERSAL_EXIT",
) -> PostJumpReversalAttempt:
    arrival_at = decision_at + timedelta(seconds=1)
    terminal_at = arrival_at + timedelta(seconds=10) if entered else arrival_at
    gross_pnl = None if net_pnl is None else net_pnl + ROUND_TRIP_COST
    exit_bid = None if gross_pnl is None else ENTRY_ASK + gross_pnl
    return PostJumpReversalAttempt(
        decision_at=decision_at,
        arrival_at=arrival_at,
        terminal_at=terminal_at,
        terminal_status=status,
        shock_sign=1,
        shock_change=Decimal("0.02"),
        selected_leg=NO,
        previous_reference_midpoint=Decimal("0.48"),
        decision_reference_midpoint=Decimal("0.50"),
        entry_reference_midpoint=Decimal("0.50") if entered else None,
        exit_reference_midpoint=Decimal("0.48") if exit_bid is not None else None,
        entry_ask=ENTRY_ASK if entered else None,
        entry_displayed_size=Decimal(5) if entered else None,
        exit_bid=exit_bid,
        exit_displayed_size=Decimal(4) if exit_bid is not None else None,
        diagnostic_quantity=DIAGNOSTIC_QUANTITY if exit_bid is not None else None,
        gross_touch_pnl_per_share=gross_pnl,
        round_trip_cost_per_share=ROUND_TRIP_COST,
        net_touch_pnl_per_share=net_pnl,
        decision_event_ordinal=1,
        entry_reference_event_ordinal=2 if entered else None,
        entry_selected_event_ordinal=2 if entered else None,
        exit_reference_event_ordinal=3 if exit_bid is not None else None,
        exit_selected_event_ordinal=3 if exit_bid is not None else None,
    )


def _post_jump_screen(
    activity: BookActivitySeries,
    attempts: tuple[PostJumpReversalAttempt, ...] | None = None,
) -> PostJumpReversalScreen:
    selected_attempts = attempts or (
        _post_jump_attempt(
            START + timedelta(seconds=2),
            net_pnl=Decimal("-0.01"),
        ),
        _post_jump_attempt(
            START + timedelta(seconds=6),
            net_pnl=Decimal("0.02"),
        ),
        _post_jump_attempt(
            START + timedelta(seconds=12),
            net_pnl=Decimal("-0.03"),
        ),
        _post_jump_attempt(
            START + timedelta(seconds=14),
            net_pnl=None,
            entered=False,
            status="NO_ENTRY_QUOTE",
        ),
        _post_jump_attempt(
            START + timedelta(seconds=20),
            net_pnl=Decimal("-0.04"),
        ),
    )
    return PostJumpReversalScreen(
        definition=_post_jump_definition(),
        source_snapshot_uri=activity.snapshot_ref.uri,
        source_start_at=START,
        source_end_at=END,
        evaluated_reference_updates=10,
        raw_shock_count=len(selected_attempts),
        ignored_overlapping_shock_count=0,
        entered_attempt_count=sum(attempt.entry_ask is not None for attempt in selected_attempts),
        terminal_status_counts=tuple(
            (status, sum(attempt.terminal_status == status for attempt in selected_attempts))
            for status in (
                "NO_ENTRY_QUOTE",
                "REVERSAL_EXIT",
                "CONTINUATION_EXIT",
                "TIMEOUT_EXIT",
                "MISSING_EXIT_QUOTE",
                "TRUNCATED",
            )
        ),
        attempts=selected_attempts,
    )


def _gate_definition() -> ActivityParticipationGateDefinition:
    return ActivityParticipationGateDefinition(
        definition_id="ll04a-test",
        parent_strategy_kind="LL03_POST_JUMP_REVERSAL",
        parent_strategy_definition_id="ll03-parent",
        scope_authority_ref="scope:h4a",
        reference_leg=YES,
        recent_window=RECENT_WINDOW,
        maximum_quiet_duration=MAXIMUM_QUIET,
        minimum_recent_source_event_count=2,
    )


def _depth_metrics() -> DepthImbalanceMetrics:
    return DepthImbalanceMetrics(
        midpoint=Decimal("0.50"),
        spread=Decimal("0.02"),
        bid_depth=Decimal(100),
        ask_depth=Decimal(20),
        total_depth=Decimal(120),
        imbalance=Decimal("0.6666666667"),
        top_imbalance=Decimal("0.20"),
        bid_level_count=2,
        ask_level_count=2,
        event_ordinal=1,
    )


def _depth_screen(activity: BookActivitySeries) -> DepthImbalanceScreen:
    definition = DepthImbalanceDefinition(
        definition_id="ll05-parent",
        scope_authority_ref="scope:h4a",
        reference_leg=YES,
        complement_leg=NO,
        entry_imbalance_threshold=Decimal("0.50"),
        exit_imbalance_threshold=Decimal("0.10"),
        maximum_spread=Decimal("0.03"),
        minimum_total_depth=Decimal(50),
        minimum_reference_midpoint=Decimal("0.10"),
        maximum_reference_midpoint=Decimal("0.90"),
        action_delay=timedelta(seconds=1),
        maximum_quote_age=timedelta(seconds=5),
        take_profit_distance=Decimal("0.02"),
        stop_loss_distance=Decimal("0.02"),
        maximum_holding_period=timedelta(seconds=10),
        minimum_entry_quantity=Decimal(1),
        round_trip_cost_per_share=ROUND_TRIP_COST,
    )
    decision_at = START + timedelta(seconds=6)
    attempt = DepthImbalanceAttempt(
        decision_at=decision_at,
        arrival_at=decision_at + timedelta(seconds=1),
        terminal_at=decision_at + timedelta(seconds=11),
        terminal_status="TAKE_PROFIT_EXIT",
        signal_sign=1,
        selected_leg=YES,
        decision_metrics=_depth_metrics(),
        arrival_metrics=_depth_metrics(),
        exit_metrics=_depth_metrics(),
        entry_ask=ENTRY_ASK,
        entry_displayed_size=Decimal(5),
        exit_bid=Decimal("0.53"),
        exit_displayed_size=Decimal(4),
        diagnostic_quantity=DIAGNOSTIC_QUANTITY,
        gross_touch_pnl_per_share=Decimal("0.03"),
        round_trip_cost_per_share=ROUND_TRIP_COST,
        net_touch_pnl_per_share=Decimal("0.02"),
        entry_selected_event_ordinal=2,
        exit_selected_event_ordinal=3,
    )
    return DepthImbalanceScreen(
        definition=definition,
        source_snapshot_uri=activity.snapshot_ref.uri,
        source_start_at=START,
        source_end_at=END,
        evaluated_reference_updates=5,
        raw_crossing_count=1,
        ignored_overlapping_crossing_count=0,
        entered_attempt_count=1,
        terminal_status_counts=(("TAKE_PROFIT_EXIT", 1),),
        attempts=(attempt,),
    )


def test_gate_dispositions_use_exact_signal_time_and_preserve_attempts() -> None:
    """Every gate disposition stays distinguishable on the unchanged parent attempts."""
    activity = _activity()
    screen = _post_jump_screen(activity)

    comparison = compare_activity_participation_gate(screen, activity, _gate_definition())

    assert tuple(decision.status for decision in comparison.decisions) == (
        "ABSTAIN_MISSING_HISTORY",
        "PASS",
        "ABSTAIN_QUIET",
        "ABSTAIN_LOW_ACTIVITY",
        "ABSTAIN_QUIET_AND_LOW_ACTIVITY",
    )
    assert tuple(decision.attempt for decision in comparison.decisions) == screen.attempts
    assert all(
        decision.attempt is screen.attempts[decision.parent_attempt_index]
        for decision in comparison.decisions
    )
    assert comparison.gate_status_counts == (
        ("PASS", 1),
        ("ABSTAIN_MISSING_HISTORY", 1),
        ("ABSTAIN_QUIET", 1),
        ("ABSTAIN_LOW_ACTIVITY", 1),
        ("ABSTAIN_QUIET_AND_LOW_ACTIVITY", 1),
    )


def test_paired_summary_preserves_counts_pnl_and_collateral_time() -> None:
    """Gated economics are a subset diagnostic with the full ungated baseline beside it."""
    activity = _activity()
    comparison = compare_activity_participation_gate(
        _post_jump_screen(activity),
        activity,
        _gate_definition(),
    )
    ungated = comparison.ungated
    gated = comparison.gated

    assert ungated.attempt_count == EXPECTED_PARENT_ATTEMPTS
    assert ungated.entered_attempt_count == EXPECTED_ENTERED_ATTEMPTS
    assert ungated.scorable_attempt_count == EXPECTED_SCORABLE_ATTEMPTS
    assert ungated.net_touch_pnl_per_share_sum == Decimal("-0.06")
    assert gated.attempt_count == 1
    assert gated.entered_attempt_count == 1
    assert gated.scorable_attempt_count == 1
    assert gated.positive_scorable_count == 1
    assert gated.net_touch_pnl_per_share_sum == Decimal("0.02")
    assert gated.net_touch_pnl_per_share_mean == Decimal("0.02")
    assert gated.entered_holding_time == timedelta(seconds=10)
    assert gated.scorable_collateral_seconds_per_share == Decimal(5)
    assert gated.net_touch_pnl_per_collateral_second == Decimal("0.004")
    assert gated.diagnostic_displayed_net_touch_pnl == Decimal("0.04")
    assert gated.diagnostic_displayed_collateral_seconds == Decimal(10)
    assert gated.diagnostic_displayed_net_per_collateral_second == Decimal("0.004")
    assert comparison.incremental_net_touch_pnl_per_share_sum == Decimal("0.08")


def test_rival_ablation_uses_exact_common_support_and_parent_order() -> None:
    """Warm-up, component, and joint populations are exact subsets of one comparison."""
    activity = _activity()
    comparison = compare_activity_participation_gate(
        _post_jump_screen(activity),
        activity,
        _gate_definition(),
    )

    ablation = compare_activity_gate_rivals(comparison)

    assert tuple(population.population for population in ablation.populations) == (
        "UNGATED",
        "COMPLETE_HISTORY",
        "QUIET_ONLY",
        "RECENT_ACTIVITY_ONLY",
        "JOINT",
    )
    assert tuple(population.parent_attempt_indices for population in ablation.populations) == (
        (0, 1, 2, 3, 4),
        (1, 2, 3, 4),
        (1, 3),
        (1, 2),
        (1,),
    )
    assert ablation.populations[0].economics == comparison.ungated
    assert ablation.populations[-1].economics == comparison.gated


def test_rival_contrasts_are_declared_left_minus_right_economics() -> None:
    """Every rival contrast has fixed direction and exact paired touch-PnL arithmetic."""
    activity = _activity()
    comparison = compare_activity_participation_gate(
        _post_jump_screen(activity),
        activity,
        _gate_definition(),
    )

    ablation = compare_activity_gate_rivals(comparison)
    contrasts = {contrast.contrast_kind: contrast for contrast in ablation.contrasts}

    assert tuple(contrasts) == (
        "COMPLETE_HISTORY_MINUS_UNGATED",
        "QUIET_ONLY_MINUS_COMPLETE_HISTORY",
        "RECENT_ACTIVITY_ONLY_MINUS_COMPLETE_HISTORY",
        "JOINT_MINUS_COMPLETE_HISTORY",
        "JOINT_MINUS_QUIET_ONLY",
        "JOINT_MINUS_RECENT_ACTIVITY_ONLY",
    )
    assert contrasts[
        "COMPLETE_HISTORY_MINUS_UNGATED"
    ].net_touch_pnl_per_share_sum_change == Decimal("0.01")
    assert contrasts[
        "QUIET_ONLY_MINUS_COMPLETE_HISTORY"
    ].net_touch_pnl_per_share_sum_change == Decimal("0.07")
    assert contrasts[
        "RECENT_ACTIVITY_ONLY_MINUS_COMPLETE_HISTORY"
    ].net_touch_pnl_per_share_sum_change == Decimal("0.04")
    assert contrasts["JOINT_MINUS_COMPLETE_HISTORY"].net_touch_pnl_per_share_sum_change == Decimal(
        "0.07"
    )
    assert contrasts["JOINT_MINUS_QUIET_ONLY"].net_touch_pnl_per_share_sum_change == Decimal(0)
    assert contrasts[
        "JOINT_MINUS_RECENT_ACTIVITY_ONLY"
    ].net_touch_pnl_per_share_sum_change == Decimal("0.03")


def test_unresolved_entered_attempt_is_not_scored_as_zero() -> None:
    """Missing exit economics remain unresolved in both paired populations."""
    activity = _activity()
    unresolved = _post_jump_attempt(
        START + timedelta(seconds=6),
        net_pnl=None,
        status="MISSING_EXIT_QUOTE",
    )
    screen = _post_jump_screen(activity, attempts=(unresolved,))

    comparison = compare_activity_participation_gate(screen, activity, _gate_definition())
    ablation = compare_activity_gate_rivals(comparison)

    for summary in (
        comparison.ungated,
        comparison.gated,
        *(population.economics for population in ablation.populations),
    ):
        assert summary.entered_attempt_count == 1
        assert summary.scorable_attempt_count == 0
        assert summary.unresolved_entered_attempt_count == 1
        assert summary.net_touch_pnl_per_share_sum is None
        assert summary.net_touch_pnl_per_share_mean is None
        assert summary.scorable_collateral_seconds_per_share is None
        assert summary.net_touch_pnl_per_collateral_second is None


def test_depth_imbalance_parent_uses_the_same_gate_contract() -> None:
    """H5 composes without a second activity definition or changed attempt path."""
    activity = _activity()
    screen = _depth_screen(activity)
    definition = replace(
        _gate_definition(),
        parent_strategy_kind="LL05_DEPTH_IMBALANCE",
        parent_strategy_definition_id="ll05-parent",
    )

    comparison = compare_activity_participation_gate(screen, activity, definition)

    assert comparison.parent_strategy_kind == "LL05_DEPTH_IMBALANCE"
    assert comparison.decisions[0].status == "PASS"
    assert comparison.decisions[0].attempt is screen.attempts[0]
    assert comparison.gated.net_touch_pnl_per_share_sum == Decimal("0.02")
    assert all(
        population.parent_attempt_indices == (0,)
        for population in compare_activity_gate_rivals(comparison).populations
    )


def test_nearest_prior_activity_point_cannot_replace_exact_join() -> None:
    """An attempt between activity points fails rather than receiving stale legal state."""
    activity = _activity()
    unmatched = _post_jump_attempt(
        START + timedelta(seconds=7),
        net_pnl=Decimal("0.01"),
    )

    with pytest.raises(ValueError, match="exact activity point"):
        compare_activity_participation_gate(
            _post_jump_screen(activity, attempts=(unmatched,)),
            activity,
            _gate_definition(),
        )


def test_source_scope_parent_window_and_leg_must_match_exactly() -> None:
    """No neighboring corpus, authority, strategy, window, or outcome can enter H4a."""
    activity = _activity()
    screen = _post_jump_screen(activity)
    definition = _gate_definition()

    with pytest.raises(ValueError, match="snapshot"):
        compare_activity_participation_gate(
            replace(screen, source_snapshot_uri="polymarket-book-corpus:foreign"),
            activity,
            definition,
        )
    with pytest.raises(ValueError, match="scope"):
        compare_activity_participation_gate(
            screen,
            activity,
            replace(definition, scope_authority_ref="scope:foreign"),
        )
    with pytest.raises(ValueError, match="parent"):
        compare_activity_participation_gate(
            screen,
            activity,
            replace(definition, parent_strategy_definition_id="ll03-foreign"),
        )
    with pytest.raises(ValueError, match="window"):
        compare_activity_participation_gate(
            screen,
            activity,
            replace(definition, recent_window=timedelta(seconds=6)),
        )
    with pytest.raises(ValueError, match="reference leg"):
        compare_activity_participation_gate(
            screen,
            activity,
            replace(definition, reference_leg=NO),
        )


def test_gate_definition_rejects_incomplete_identity_or_thresholds() -> None:
    """Threshold and parent identity cannot arrive through implicit defaults."""
    definition = _gate_definition()

    with pytest.raises(ValueError, match="exact identity"):
        replace(definition, definition_id="")
    with pytest.raises(ValueError, match="exact identity"):
        replace(definition, recent_window=timedelta(0))
    with pytest.raises(ValueError, match="exact identity"):
        replace(definition, maximum_quiet_duration=timedelta(0))
    with pytest.raises(ValueError, match="exact identity"):
        replace(definition, minimum_recent_source_event_count=-1)


def test_comparison_rejects_mutated_paired_economics() -> None:
    """A stored comparison cannot drift away from its immutable attempt subsets."""
    activity = _activity()
    comparison = compare_activity_participation_gate(
        _post_jump_screen(activity),
        activity,
        _gate_definition(),
    )

    with pytest.raises(ValueError, match="paired parent population"):
        replace(
            comparison,
            incremental_net_touch_pnl_per_share_sum=Decimal(999),
        )
    with pytest.raises(ValueError, match="paired parent population"):
        replace(comparison, source_end_at=START + timedelta(seconds=1))


def test_rival_ablation_rejects_mutated_contrast_economics() -> None:
    """Stored rival evidence cannot drift from the comparison that generated it."""
    activity = _activity()
    comparison = compare_activity_participation_gate(
        _post_jump_screen(activity),
        activity,
        _gate_definition(),
    )
    ablation = compare_activity_gate_rivals(comparison)
    mutated_contrast = replace(
        ablation.contrasts[0],
        net_touch_pnl_per_share_sum_change=Decimal(999),
    )

    with pytest.raises(ValueError, match="detached from its parent comparison"):
        replace(
            ablation,
            contrasts=(mutated_contrast, *ablation.contrasts[1:]),
        )
    with pytest.raises(ValueError, match="direction"):
        replace(
            ablation.contrasts[0],
            left_population="UNGATED",
            right_population="COMPLETE_HISTORY",
        )


def test_scorable_attempt_rejects_negative_entry_ask() -> None:
    """Collateral normalization cannot silently accept an invalid negative price."""
    activity = _activity()
    attempt = replace(
        _post_jump_attempt(
            START + timedelta(seconds=6),
            net_pnl=Decimal("0.02"),
        ),
        entry_ask=Decimal("-0.01"),
    )

    with pytest.raises(ValueError, match="negative entry ask"):
        compare_activity_participation_gate(
            _post_jump_screen(activity, attempts=(attempt,)),
            activity,
            _gate_definition(),
        )
