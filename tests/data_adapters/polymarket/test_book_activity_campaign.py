"""Chronological LL-04c campaign adversaries over exact LL-04b ablations."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import cast

import pytest

from research_agent.data_adapters.polymarket.book_activity import (
    BookActivityDefinition,
    BookActivitySeries,
    build_book_activity_series,
)
from research_agent.data_adapters.polymarket.book_activity_campaign import (
    ActivityGateCampaignBlock,
    ActivityGateCampaignDefinition,
    ActivityGateCampaignMetric,
    ActivityGateCampaignPrimaryContrast,
    activity_gate_parent_recipe,
    evaluate_activity_gate_campaign,
)
from research_agent.data_adapters.polymarket.book_activity_gate import (
    ActivityGateRivalAblation,
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
)

START = datetime(2026, 8, 23, 12, tzinfo=UTC)
BLOCK_DURATION = timedelta(seconds=10)
BLOCK_GAP = timedelta(seconds=20)
RECENT_WINDOW = timedelta(seconds=2)
MAXIMUM_QUIET = timedelta(seconds=1, microseconds=500_000)
ROUND_TRIP_COST = Decimal("0.01")
ENTRY_ASK = Decimal("0.50")
EXPECTED_BLOCK_COUNT = 3
EXPECTED_SCORED_BLOCK_COUNT = 2
EXPECTED_UNGATED_ATTEMPT_COUNT = 9
EXPECTED_COMPLETE_HISTORY_ATTEMPT_COUNT = 6
EXPECTED_JOINT_ATTEMPT_COUNT = 3


def _snapshot(leg: BookLeg, *, at: datetime, seq: int) -> BookSnapshotRecord:
    return BookSnapshotRecord(
        leg=leg,
        ts=at,
        reference_time=at,
        seq=seq,
        bids=(("0.49", "10"),),
        asks=(("0.50", "10"),),
        raw={"kind": "snapshot", "seq": seq},
    )


def _delta(leg: BookLeg, *, at: datetime, seq: int) -> BookDeltaRecord:
    return BookDeltaRecord(
        leg=leg,
        ts=at,
        reference_time=at,
        seq=seq,
        side="BID",
        price=Decimal("0.49"),
        size=Decimal(10 + seq),
        raw={"kind": "delta", "seq": seq},
    )


def _activity(start_at: datetime, market_id: str) -> tuple[BookActivitySeries, BookLeg, BookLeg]:
    reference_leg = BookLeg("polymarket", market_id, 0)
    complement_leg = BookLeg("polymarket", market_id, 1)
    end_at = start_at + BLOCK_DURATION
    events = (
        _snapshot(reference_leg, at=start_at, seq=1),
        _snapshot(complement_leg, at=start_at + timedelta(microseconds=1), seq=2),
        _delta(reference_leg, at=start_at + timedelta(seconds=1), seq=3),
        _delta(reference_leg, at=start_at + timedelta(seconds=2), seq=4),
        _delta(reference_leg, at=start_at + timedelta(seconds=3), seq=5),
        _delta(reference_leg, at=start_at + timedelta(seconds=6), seq=6),
    )
    request = BookCorpusRequest(
        environment_id="test-h4c",
        scope_authority_ref="scope:h4c",
        legs=(reference_leg, complement_leg),
        start_at=start_at,
        end_at=end_at,
    )
    snapshot = BookCorpusStore.from_corpus(
        BookCorpus(request, tuple(sorted(events, key=lambda event: event.sort_key)))
    )
    return (
        build_book_activity_series(snapshot, BookActivityDefinition(RECENT_WINDOW)),
        reference_leg,
        complement_leg,
    )


def _post_jump_definition(
    reference_leg: BookLeg,
    complement_leg: BookLeg,
    *,
    definition_id: str,
) -> PostJumpReversalDefinition:
    return PostJumpReversalDefinition(
        definition_id=definition_id,
        scope_authority_ref="scope:h4c",
        reference_leg=reference_leg,
        complement_leg=complement_leg,
        minimum_midpoint_shock=Decimal("0.02"),
        maximum_shock_gap=timedelta(seconds=5),
        action_delay=timedelta(seconds=1),
        maximum_quote_age=timedelta(seconds=2),
        reversal_distance=Decimal("0.02"),
        continuation_distance=Decimal("0.02"),
        maximum_holding_period=timedelta(seconds=2),
        minimum_entry_quantity=Decimal(1),
        round_trip_cost_per_share=ROUND_TRIP_COST,
    )


def _attempt(
    decision_at: datetime,
    net_pnl: Decimal | None,
    selected_leg: BookLeg,
) -> PostJumpReversalAttempt:
    arrival_at = decision_at + timedelta(seconds=1)
    terminal_at = arrival_at + timedelta(seconds=1)
    gross_pnl = None if net_pnl is None else net_pnl + ROUND_TRIP_COST
    exit_bid = None if gross_pnl is None else ENTRY_ASK + gross_pnl
    return PostJumpReversalAttempt(
        decision_at=decision_at,
        arrival_at=arrival_at,
        terminal_at=terminal_at,
        terminal_status="MISSING_EXIT_QUOTE" if net_pnl is None else "REVERSAL_EXIT",
        shock_sign=1,
        shock_change=Decimal("0.02"),
        selected_leg=selected_leg,
        previous_reference_midpoint=Decimal("0.48"),
        decision_reference_midpoint=Decimal("0.50"),
        entry_reference_midpoint=Decimal("0.50"),
        exit_reference_midpoint=None if exit_bid is None else Decimal("0.48"),
        entry_ask=ENTRY_ASK,
        entry_displayed_size=Decimal(5),
        exit_bid=exit_bid,
        exit_displayed_size=None if exit_bid is None else Decimal(4),
        diagnostic_quantity=None if exit_bid is None else Decimal(2),
        gross_touch_pnl_per_share=gross_pnl,
        round_trip_cost_per_share=ROUND_TRIP_COST,
        net_touch_pnl_per_share=net_pnl,
        decision_event_ordinal=1,
        entry_reference_event_ordinal=2,
        entry_selected_event_ordinal=2,
        exit_reference_event_ordinal=None if exit_bid is None else 3,
        exit_selected_event_ordinal=None if exit_bid is None else 3,
    )


def _post_jump_ablation(
    block_start: datetime,
    market_id: str,
    *,
    joint_pnl: Decimal | None,
    inactive_pnl: Decimal | None,
) -> ActivityGateRivalAblation:
    activity, reference_leg, complement_leg = _activity(block_start, market_id)
    parent_definition = _post_jump_definition(
        reference_leg,
        complement_leg,
        definition_id=f"ll03-{market_id}",
    )
    attempts = (
        _attempt(
            block_start + timedelta(seconds=1),
            Decimal("-0.01"),
            complement_leg,
        ),
        _attempt(block_start + timedelta(seconds=3), joint_pnl, complement_leg),
        _attempt(block_start + timedelta(seconds=6), inactive_pnl, complement_leg),
    )
    screen = PostJumpReversalScreen(
        definition=parent_definition,
        source_snapshot_uri=activity.snapshot_ref.uri,
        source_start_at=block_start,
        source_end_at=block_start + BLOCK_DURATION,
        evaluated_reference_updates=4,
        raw_shock_count=len(attempts),
        ignored_overlapping_shock_count=0,
        entered_attempt_count=len(attempts),
        terminal_status_counts=(
            (
                "REVERSAL_EXIT",
                sum(attempt.net_touch_pnl_per_share is not None for attempt in attempts),
            ),
            (
                "MISSING_EXIT_QUOTE",
                sum(attempt.net_touch_pnl_per_share is None for attempt in attempts),
            ),
        ),
        attempts=attempts,
    )
    gate_definition = ActivityParticipationGateDefinition(
        definition_id=f"ll04a-{market_id}",
        parent_strategy_kind="LL03_POST_JUMP_REVERSAL",
        parent_strategy_definition_id=parent_definition.definition_id,
        scope_authority_ref="scope:h4c",
        reference_leg=reference_leg,
        recent_window=RECENT_WINDOW,
        maximum_quiet_duration=MAXIMUM_QUIET,
        minimum_recent_source_event_count=1,
    )
    comparison = compare_activity_participation_gate(screen, activity, gate_definition)
    assert tuple(decision.status for decision in comparison.decisions) == (
        "ABSTAIN_MISSING_HISTORY",
        "PASS",
        "ABSTAIN_QUIET_AND_LOW_ACTIVITY",
    )
    return compare_activity_gate_rivals(comparison)


def _block(
    ordinal: int,
    *,
    joint_pnl: Decimal | None,
    inactive_pnl: Decimal | None,
) -> ActivityGateCampaignBlock:
    start_at = START + ordinal * BLOCK_GAP
    return ActivityGateCampaignBlock(
        block_id=f"block-{ordinal}",
        start_at=start_at,
        end_at=start_at + BLOCK_DURATION,
        ablations=(
            _post_jump_ablation(
                start_at,
                f"market-{ordinal}",
                joint_pnl=joint_pnl,
                inactive_pnl=inactive_pnl,
            ),
        ),
    )


def _campaign_definition(
    ablation: ActivityGateRivalAblation,
) -> ActivityGateCampaignDefinition:
    return ActivityGateCampaignDefinition(
        definition_id="ll04c-test",
        parent_strategy_kind="LL03_POST_JUMP_REVERSAL",
        parent_strategy_recipe=activity_gate_parent_recipe(
            ablation.comparison.parent_strategy_definition
        ),
        scope_authority_ref="scope:h4c",
        recent_window=RECENT_WINDOW,
        maximum_quiet_duration=MAXIMUM_QUIET,
        minimum_recent_source_event_count=1,
        primary_contrast_kind="JOINT_MINUS_COMPLETE_HISTORY",
        primary_metric="NET_TOUCH_PNL_PER_SHARE_MEAN_CHANGE",
    )


def _three_blocks() -> tuple[ActivityGateCampaignBlock, ...]:
    return (
        _block(0, joint_pnl=Decimal("0.04"), inactive_pnl=Decimal("-0.02")),
        _block(1, joint_pnl=None, inactive_pnl=None),
        _block(2, joint_pnl=Decimal("-0.02"), inactive_pnl=Decimal("0.02")),
    )


def test_campaign_recomputes_block_and_pooled_rival_populations() -> None:
    """All attempts remain traceable through exact block and pooled subset economics."""
    blocks = _three_blocks()

    result = evaluate_activity_gate_campaign(_campaign_definition(blocks[0].ablations[0]), blocks)

    assert tuple(block.block.block_id for block in result.blocks) == (
        "block-0",
        "block-1",
        "block-2",
    )
    pooled = {population.population: population for population in result.pooled.populations}
    assert pooled["UNGATED"].economics.attempt_count == EXPECTED_UNGATED_ATTEMPT_COUNT
    assert (
        pooled["COMPLETE_HISTORY"].economics.attempt_count
        == EXPECTED_COMPLETE_HISTORY_ATTEMPT_COUNT
    )
    assert pooled["JOINT"].economics.attempt_count == EXPECTED_JOINT_ATTEMPT_COUNT
    assert pooled["JOINT"].economics.entered_attempt_count == EXPECTED_JOINT_ATTEMPT_COUNT
    assert pooled["JOINT"].economics.scorable_attempt_count == EXPECTED_SCORED_BLOCK_COUNT
    assert pooled["JOINT"].economics.unresolved_entered_attempt_count == 1
    assert pooled["UNGATED"].market_count == EXPECTED_BLOCK_COUNT
    assert len(pooled["UNGATED"].source_snapshot_uris) == EXPECTED_BLOCK_COUNT


def test_campaign_stability_splits_chronology_before_missing_values() -> None:
    """An unscored middle block cannot move a later loss into the early half."""
    blocks = _three_blocks()

    result = evaluate_activity_gate_campaign(_campaign_definition(blocks[0].ablations[0]), blocks)
    stability = result.stability

    assert stability.block_count == EXPECTED_BLOCK_COUNT
    assert stability.scored_block_count == EXPECTED_SCORED_BLOCK_COUNT
    assert stability.missing_block_count == 1
    assert stability.positive_block_count == 1
    assert stability.zero_block_count == 0
    assert stability.negative_block_count == 1
    assert stability.pooled_primary_value == Decimal("0.005")
    assert stability.block_macro_mean == Decimal("0.005")
    assert stability.early_block_mean == Decimal("0.03")
    assert stability.late_block_mean == Decimal("-0.02")
    assert stability.largest_positive_block_share == Decimal(1)


@pytest.mark.parametrize(
    "metric",
    [
        "NET_TOUCH_PNL_PER_COLLATERAL_SECOND_CHANGE",
        "DIAGNOSTIC_DISPLAYED_NET_PER_COLLATERAL_SECOND_CHANGE",
    ],
)
def test_campaign_supports_both_predeclared_collateral_time_metrics(
    metric: ActivityGateCampaignMetric,
) -> None:
    """One-share and displayed-quantity rate contrasts keep left-minus-right direction."""
    blocks = _three_blocks()
    definition = replace(
        _campaign_definition(blocks[0].ablations[0]),
        primary_metric=metric,
    )

    stability = evaluate_activity_gate_campaign(definition, blocks).stability

    assert stability.pooled_primary_value == Decimal("0.01")
    assert stability.block_macro_mean == Decimal("0.01")
    assert stability.early_block_mean == Decimal("0.06")
    assert stability.late_block_mean == Decimal("-0.04")


def test_campaign_rejects_policy_recipe_scope_and_coverage_mismatch() -> None:
    """No neighboring activity or parent policy can enter a fixed campaign."""
    blocks = _three_blocks()
    definition = _campaign_definition(blocks[0].ablations[0])

    with pytest.raises(ValueError, match="policy identity"):
        evaluate_activity_gate_campaign(
            replace(definition, minimum_recent_source_event_count=2),
            blocks,
        )
    with pytest.raises(ValueError, match="policy identity"):
        evaluate_activity_gate_campaign(
            replace(definition, scope_authority_ref="scope:foreign"),
            blocks,
        )
    changed_parent = replace(
        blocks[0].ablations[0].comparison.parent_strategy_definition,
        minimum_midpoint_shock=Decimal("0.03"),
    )
    with pytest.raises(ValueError, match="policy identity"):
        evaluate_activity_gate_campaign(
            replace(definition, parent_strategy_recipe=activity_gate_parent_recipe(changed_parent)),
            blocks,
        )
    with pytest.raises(ValueError, match="coverage escapes"):
        evaluate_activity_gate_campaign(
            definition,
            (
                replace(
                    blocks[0],
                    start_at=blocks[0].start_at + timedelta(microseconds=1),
                ),
            ),
        )


def test_campaign_rejects_empty_duplicate_overlapping_or_reversed_blocks() -> None:
    """Chronology and evidence identity fail rather than deduplicating or reordering."""
    blocks = _three_blocks()
    definition = _campaign_definition(blocks[0].ablations[0])

    with pytest.raises(ValueError, match="at least one"):
        evaluate_activity_gate_campaign(definition, ())
    with pytest.raises(ValueError, match="identities"):
        evaluate_activity_gate_campaign(
            definition,
            (blocks[0], replace(blocks[1], block_id=blocks[0].block_id)),
        )
    with pytest.raises(ValueError, match="overlap or are out of order"):
        evaluate_activity_gate_campaign(
            definition,
            (blocks[1], blocks[0]),
        )
    with pytest.raises(ValueError, match="overlap or are out of order"):
        evaluate_activity_gate_campaign(
            definition,
            (
                blocks[0],
                replace(blocks[1], start_at=blocks[0].end_at - timedelta(seconds=1)),
            ),
        )


def test_campaign_rejects_duplicate_parent_attempt_across_distinct_ablations() -> None:
    """Different snapshot or definition labels cannot double-count one market-time attempt."""
    block = _three_blocks()[0]
    original = block.ablations[0]
    comparison = original.comparison
    parent_definition = replace(
        comparison.parent_strategy_definition,
        definition_id="ll03-duplicate-label",
    )
    gate_definition = replace(
        comparison.definition,
        definition_id="ll04a-duplicate-label",
        parent_strategy_definition_id=parent_definition.definition_id,
    )
    duplicated_comparison = replace(
        comparison,
        definition=gate_definition,
        parent_strategy_definition=parent_definition,
        source_snapshot_uri=f"{comparison.source_snapshot_uri}:duplicate-label",
    )
    duplicated = compare_activity_gate_rivals(duplicated_comparison)

    with pytest.raises(ValueError, match="duplicate parent attempt"):
        evaluate_activity_gate_campaign(
            _campaign_definition(original),
            (replace(block, ablations=(original, duplicated)),),
        )


def test_campaign_result_rejects_mutated_stability() -> None:
    """Stored macro evidence cannot drift away from its chronological blocks."""
    blocks = _three_blocks()
    result = evaluate_activity_gate_campaign(_campaign_definition(blocks[0].ablations[0]), blocks)

    with pytest.raises(ValueError, match="detached from its exact inputs"):
        replace(
            result,
            stability=replace(result.stability, block_macro_mean=Decimal(999)),
        )


def test_campaign_definition_requires_explicit_policy_and_primary_identity() -> None:
    """Campaign construction supplies no threshold, contrast, or metric defaults."""
    block = _three_blocks()[0]
    definition = _campaign_definition(block.ablations[0])

    with pytest.raises(ValueError, match="exact fixed policy"):
        replace(definition, definition_id="")
    with pytest.raises(ValueError, match="exact fixed policy"):
        replace(definition, recent_window=timedelta(0))
    with pytest.raises(ValueError, match="exact fixed policy"):
        replace(definition, maximum_quiet_duration=timedelta(0))
    with pytest.raises(ValueError, match="exact fixed policy"):
        replace(definition, minimum_recent_source_event_count=-1)
    with pytest.raises(ValueError, match="exact fixed policy"):
        replace(
            definition,
            primary_contrast_kind=cast(
                "ActivityGateCampaignPrimaryContrast",
                "COMPLETE_HISTORY_MINUS_UNGATED",
            ),
        )


def _depth_metrics() -> DepthImbalanceMetrics:
    return DepthImbalanceMetrics(
        midpoint=Decimal("0.50"),
        spread=Decimal("0.01"),
        bid_depth=Decimal(100),
        ask_depth=Decimal(20),
        total_depth=Decimal(120),
        imbalance=Decimal("0.6666666667"),
        top_imbalance=Decimal("0.20"),
        bid_level_count=2,
        ask_level_count=2,
        event_ordinal=1,
    )


def _depth_ablation() -> ActivityGateRivalAblation:
    activity, reference_leg, complement_leg = _activity(START, "depth-market")
    parent_definition = DepthImbalanceDefinition(
        definition_id="ll05-depth-market",
        scope_authority_ref="scope:h4c",
        reference_leg=reference_leg,
        complement_leg=complement_leg,
        entry_imbalance_threshold=Decimal("0.50"),
        exit_imbalance_threshold=Decimal("0.10"),
        maximum_spread=Decimal("0.03"),
        minimum_total_depth=Decimal(50),
        minimum_reference_midpoint=Decimal("0.10"),
        maximum_reference_midpoint=Decimal("0.90"),
        action_delay=timedelta(seconds=1),
        maximum_quote_age=timedelta(seconds=2),
        take_profit_distance=Decimal("0.02"),
        stop_loss_distance=Decimal("0.02"),
        maximum_holding_period=timedelta(seconds=2),
        minimum_entry_quantity=Decimal(1),
        round_trip_cost_per_share=ROUND_TRIP_COST,
    )
    decision_at = START + timedelta(seconds=3)
    attempt = DepthImbalanceAttempt(
        decision_at=decision_at,
        arrival_at=decision_at + timedelta(seconds=1),
        terminal_at=decision_at + timedelta(seconds=2),
        terminal_status="TAKE_PROFIT_EXIT",
        signal_sign=1,
        selected_leg=reference_leg,
        decision_metrics=_depth_metrics(),
        arrival_metrics=_depth_metrics(),
        exit_metrics=_depth_metrics(),
        entry_ask=ENTRY_ASK,
        entry_displayed_size=Decimal(5),
        exit_bid=Decimal("0.53"),
        exit_displayed_size=Decimal(4),
        diagnostic_quantity=Decimal(2),
        gross_touch_pnl_per_share=Decimal("0.03"),
        round_trip_cost_per_share=ROUND_TRIP_COST,
        net_touch_pnl_per_share=Decimal("0.02"),
        entry_selected_event_ordinal=2,
        exit_selected_event_ordinal=3,
    )
    screen = DepthImbalanceScreen(
        definition=parent_definition,
        source_snapshot_uri=activity.snapshot_ref.uri,
        source_start_at=START,
        source_end_at=START + BLOCK_DURATION,
        evaluated_reference_updates=4,
        raw_crossing_count=1,
        ignored_overlapping_crossing_count=0,
        entered_attempt_count=1,
        terminal_status_counts=(("TAKE_PROFIT_EXIT", 1),),
        attempts=(attempt,),
    )
    gate_definition = ActivityParticipationGateDefinition(
        definition_id="ll04a-depth-market",
        parent_strategy_kind="LL05_DEPTH_IMBALANCE",
        parent_strategy_definition_id=parent_definition.definition_id,
        scope_authority_ref="scope:h4c",
        reference_leg=reference_leg,
        recent_window=RECENT_WINDOW,
        maximum_quiet_duration=MAXIMUM_QUIET,
        minimum_recent_source_event_count=1,
    )
    return compare_activity_gate_rivals(
        compare_activity_participation_gate(screen, activity, gate_definition)
    )


def test_campaign_composes_with_depth_imbalance_parent_recipe() -> None:
    """H5 uses the same chronological campaign without losing its parent recipe identity."""
    ablation = _depth_ablation()
    block = ActivityGateCampaignBlock(
        block_id="depth-block",
        start_at=START,
        end_at=START + BLOCK_DURATION,
        ablations=(ablation,),
    )
    definition = ActivityGateCampaignDefinition(
        definition_id="ll04c-depth-test",
        parent_strategy_kind="LL05_DEPTH_IMBALANCE",
        parent_strategy_recipe=activity_gate_parent_recipe(
            ablation.comparison.parent_strategy_definition
        ),
        scope_authority_ref="scope:h4c",
        recent_window=RECENT_WINDOW,
        maximum_quiet_duration=MAXIMUM_QUIET,
        minimum_recent_source_event_count=1,
        primary_contrast_kind="JOINT_MINUS_COMPLETE_HISTORY",
        primary_metric="NET_TOUCH_PNL_PER_SHARE_MEAN_CHANGE",
    )

    result = evaluate_activity_gate_campaign(definition, (block,))

    assert result.definition.parent_strategy_kind == "LL05_DEPTH_IMBALANCE"
    assert result.pooled.populations[-1].economics.net_touch_pnl_per_share_sum == Decimal("0.02")
