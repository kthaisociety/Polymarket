"""LL-04e development-only advancement-standard adversaries."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from research_agent.data_adapters import polymarket
from research_agent.data_adapters.polymarket.book_activity import (
    BookActivityDefinition,
    BookActivitySeries,
    build_book_activity_series,
)
from research_agent.data_adapters.polymarket.book_activity_advancement import (
    ActivityGateDevelopmentAssessment,
    assess_activity_gate_development_campaign,
    ll04e_primary_development_standard,
)
from research_agent.data_adapters.polymarket.book_activity_campaign import (
    ActivityGateCampaignBlock,
    ActivityGateCampaignDefinition,
    ActivityGateCampaignResult,
    activity_gate_parent_recipe,
    evaluate_activity_gate_campaign,
)
from research_agent.data_adapters.polymarket.book_activity_gate import (
    ActivityGateRivalAblation,
    compare_activity_gate_rivals,
    compare_activity_participation_gate,
)
from research_agent.data_adapters.polymarket.book_activity_policy import (
    derive_latency_scaled_activity_gate,
    ll04d_latency_scaled_primary_policy,
)
from research_agent.data_adapters.polymarket.book_corpus import (
    BookCorpus,
    BookCorpusRequest,
    BookCorpusStore,
    BookDeltaRecord,
    BookLeg,
    BookSnapshotRecord,
)
from research_agent.data_adapters.polymarket.low_latency import (
    PostJumpReversalAttempt,
    PostJumpReversalDefinition,
    PostJumpReversalScreen,
)

START = datetime(2026, 8, 23, 12, tzinfo=UTC)
BLOCK_DURATION = timedelta(seconds=35)
BLOCK_GAP = timedelta(seconds=45)
ACTION_DELAY = timedelta(seconds=1)
ROUND_TRIP_COST = Decimal("0.01")
ENTRY_ASK = Decimal("0.50")
MARKETS_PER_BLOCK = 3
PASSING_BLOCK_COUNT = 10
INSUFFICIENT_BLOCK_COUNT = 9
EXPECTED_JOINT_SCORABLE_ATTEMPTS = 30


@dataclass(frozen=True, slots=True)
class _PnlScenario:
    missing_history_pnl: Decimal | None
    joint_pnl: Decimal | None
    quiet_only_pnl: Decimal | None
    recent_only_pnl: Decimal | None
    joint_failure_pnl: Decimal | None
    exact_policy_identity: bool


PASSING_SCENARIO = _PnlScenario(
    missing_history_pnl=Decimal("-0.03"),
    joint_pnl=Decimal("0.05"),
    quiet_only_pnl=Decimal("-0.01"),
    recent_only_pnl=Decimal(0),
    joint_failure_pnl=Decimal("-0.02"),
    exact_policy_identity=True,
)


def _snapshot(leg: BookLeg, *, at: datetime, sequence: int) -> BookSnapshotRecord:
    return BookSnapshotRecord(
        leg=leg,
        ts=at,
        reference_time=at,
        seq=sequence,
        bids=(("0.49", "10"),),
        asks=(("0.50", "10"),),
        raw={"kind": "snapshot", "sequence": sequence},
    )


def _delta(leg: BookLeg, *, at: datetime, sequence: int) -> BookDeltaRecord:
    return BookDeltaRecord(
        leg=leg,
        ts=at,
        reference_time=at,
        seq=sequence,
        side="BID",
        price=Decimal("0.49"),
        size=Decimal(10 + sequence),
        raw={"kind": "delta", "sequence": sequence},
    )


def _activity(
    block_start: datetime,
    market_id: str,
) -> tuple[BookActivitySeries, BookLeg, BookLeg]:
    reference_leg = BookLeg("polymarket", market_id, 0)
    complement_leg = BookLeg("polymarket", market_id, 1)
    reference_offsets = (0, 1, 5, 6, 13, 14, 16, 17, 19, 26)
    reference_events = tuple(
        _snapshot(reference_leg, at=block_start, sequence=1)
        if offset == 0
        else _delta(
            reference_leg,
            at=block_start + timedelta(seconds=offset),
            sequence=index + 1,
        )
        for index, offset in enumerate(reference_offsets)
    )
    events = (
        *reference_events,
        _snapshot(
            complement_leg,
            at=block_start + timedelta(microseconds=1),
            sequence=100,
        ),
    )
    request = BookCorpusRequest(
        environment_id="test-h4e",
        scope_authority_ref="scope:h4e",
        legs=(reference_leg, complement_leg),
        start_at=block_start,
        end_at=block_start + BLOCK_DURATION,
    )
    snapshot = BookCorpusStore.from_corpus(
        BookCorpus(request, tuple(sorted(events, key=lambda event: event.sort_key)))
    )
    policy = ll04d_latency_scaled_primary_policy()
    return (
        build_book_activity_series(
            snapshot,
            BookActivityDefinition(ACTION_DELAY * policy.recent_window_action_delay_multiplier),
        ),
        reference_leg,
        complement_leg,
    )


def _parent_definition(
    reference_leg: BookLeg,
    complement_leg: BookLeg,
    *,
    definition_id: str,
) -> PostJumpReversalDefinition:
    return PostJumpReversalDefinition(
        definition_id=definition_id,
        scope_authority_ref="scope:h4e",
        reference_leg=reference_leg,
        complement_leg=complement_leg,
        minimum_midpoint_shock=Decimal("0.02"),
        maximum_shock_gap=timedelta(seconds=5),
        action_delay=ACTION_DELAY,
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
    arrival_at = decision_at + ACTION_DELAY
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


def _ablation(
    block_start: datetime,
    market_id: str,
    *,
    scenario: _PnlScenario,
) -> ActivityGateRivalAblation:
    activity, reference_leg, complement_leg = _activity(block_start, market_id)
    parent = _parent_definition(
        reference_leg,
        complement_leg,
        definition_id=f"ll03-{market_id}",
    )
    pnl_by_offset = (
        (1, scenario.missing_history_pnl),
        (6, scenario.joint_pnl),
        (14, scenario.quiet_only_pnl),
        (19, scenario.recent_only_pnl),
        (26, scenario.joint_failure_pnl),
    )
    attempts = tuple(
        _attempt(block_start + timedelta(seconds=offset), pnl, complement_leg)
        for offset, pnl in pnl_by_offset
    )
    screen = PostJumpReversalScreen(
        definition=parent,
        source_snapshot_uri=activity.snapshot_ref.uri,
        source_start_at=block_start,
        source_end_at=block_start + BLOCK_DURATION,
        evaluated_reference_updates=10,
        raw_shock_count=len(attempts),
        ignored_overlapping_shock_count=0,
        entered_attempt_count=len(attempts),
        terminal_status_counts=tuple(
            (status, sum(attempt.terminal_status == status for attempt in attempts))
            for status in ("MISSING_EXIT_QUOTE", "REVERSAL_EXIT")
        ),
        attempts=attempts,
    )
    gate = derive_latency_scaled_activity_gate(parent, ll04d_latency_scaled_primary_policy())
    if not scenario.exact_policy_identity:
        gate = replace(gate, definition_id=f"manual-threshold-copy:{market_id}")
    comparison = compare_activity_participation_gate(screen, activity, gate)
    assert tuple(decision.status for decision in comparison.decisions) == (
        "ABSTAIN_MISSING_HISTORY",
        "PASS",
        "ABSTAIN_LOW_ACTIVITY",
        "ABSTAIN_QUIET",
        "ABSTAIN_QUIET_AND_LOW_ACTIVITY",
    )
    return compare_activity_gate_rivals(comparison)


def _campaign(
    *,
    block_count: int = PASSING_BLOCK_COUNT,
    scenario: _PnlScenario = PASSING_SCENARIO,
    scenarios_by_block: tuple[_PnlScenario, ...] | None = None,
) -> ActivityGateCampaignResult:
    if scenarios_by_block is not None and len(scenarios_by_block) != block_count:
        message = "test campaign scenarios must match its chronological blocks"
        raise ValueError(message)
    blocks = tuple(
        ActivityGateCampaignBlock(
            block_id=f"block-{block_ordinal}",
            start_at=START + block_ordinal * BLOCK_GAP,
            end_at=START + block_ordinal * BLOCK_GAP + BLOCK_DURATION,
            ablations=tuple(
                _ablation(
                    START + block_ordinal * BLOCK_GAP,
                    f"market-{block_ordinal}-{market_ordinal}",
                    scenario=(
                        scenario
                        if scenarios_by_block is None
                        else scenarios_by_block[block_ordinal]
                    ),
                )
                for market_ordinal in range(MARKETS_PER_BLOCK)
            ),
        )
        for block_ordinal in range(block_count)
    )
    first_ablation = blocks[0].ablations[0]
    policy = ll04d_latency_scaled_primary_policy()
    definition = ActivityGateCampaignDefinition(
        definition_id="ll04c-for-ll04e-test",
        parent_strategy_kind="LL03_POST_JUMP_REVERSAL",
        parent_strategy_recipe=activity_gate_parent_recipe(
            first_ablation.comparison.parent_strategy_definition
        ),
        scope_authority_ref="scope:h4e",
        recent_window=ACTION_DELAY * policy.recent_window_action_delay_multiplier,
        maximum_quiet_duration=(ACTION_DELAY * policy.maximum_quiet_action_delay_multiplier),
        minimum_recent_source_event_count=policy.minimum_recent_source_event_count,
        primary_contrast_kind="JOINT_MINUS_COMPLETE_HISTORY",
        primary_metric="NET_TOUCH_PNL_PER_COLLATERAL_SECOND_CHANGE",
    )
    return evaluate_activity_gate_campaign(definition, blocks)


def _clauses(
    assessment: ActivityGateDevelopmentAssessment,
) -> dict[str, Decimal | int | None]:
    return {clause.clause_kind: clause.observed_value for clause in assessment.clauses}


def test_named_standard_fixes_one_policy_metric_and_decision_boundary() -> None:
    """LL-04e contains one inspectable no-fit development standard."""
    standard = ll04e_primary_development_standard()

    assert standard.definition_id == "ll04e-primary-development-v1"
    assert standard.activity_policy == ll04d_latency_scaled_primary_policy()
    assert standard.required_primary_contrast_kind == "JOINT_MINUS_COMPLETE_HISTORY"
    assert standard.required_primary_metric == "NET_TOUCH_PNL_PER_COLLATERAL_SECOND_CHANGE"
    assert standard.minimum_block_count == PASSING_BLOCK_COUNT
    assert standard.minimum_scored_block_fraction == Decimal("0.80")
    assert standard.minimum_positive_scored_block_fraction == Decimal("0.60")
    assert standard.maximum_largest_positive_block_share == Decimal("0.50")
    assert standard.minimum_joint_scorable_attempt_count == EXPECTED_JOINT_SCORABLE_ATTEMPTS
    assert standard.minimum_joint_scorable_retention_fraction == Decimal("0.25")
    assert standard.maximum_joint_unresolved_entered_fraction == Decimal("0.10")


def test_advancement_api_is_public_without_changing_its_development_status() -> None:
    """The adapter surface exposes assessment, not a validation or trading operation."""
    standard = polymarket.ll04e_primary_development_standard()
    assessment = polymarket.assess_activity_gate_development_campaign(
        _campaign(),
        standard,
    )

    assert standard == ll04e_primary_development_standard()
    assert assessment.status == "ADVANCE_TO_PAPER_EXECUTION_STUDY"


def test_insufficient_campaign_stays_insufficient_instead_of_becoming_rejection() -> None:
    """Missing required breadth has its own status even when observed economics are positive."""
    assessment = assess_activity_gate_development_campaign(
        _campaign(block_count=INSUFFICIENT_BLOCK_COUNT),
        ll04e_primary_development_standard(),
    )

    assert assessment.status == "INSUFFICIENT_COVERAGE"
    assert not assessment.coverage_passes
    assert assessment.economics_passes
    failed = tuple(clause.clause_kind for clause in assessment.clauses if not clause.passes)
    assert failed == (
        "MINIMUM_CHRONOLOGICAL_BLOCKS",
        "MINIMUM_JOINT_SCORABLE_ATTEMPTS",
    )


def test_sufficient_negative_campaign_is_rejected() -> None:
    """Coverage cannot rescue a non-positive and chronologically losing activity effect."""
    assessment = assess_activity_gate_development_campaign(
        _campaign(scenario=replace(PASSING_SCENARIO, joint_pnl=Decimal("-0.05"))),
        ll04e_primary_development_standard(),
    )

    assert assessment.status == "REJECT_DEVELOPMENT"
    assert assessment.coverage_passes
    assert not assessment.economics_passes
    failed = {clause.clause_kind for clause in assessment.clauses if not clause.passes}
    assert "POSITIVE_POOLED_PRIMARY_VALUE" in failed
    assert "MINIMUM_POSITIVE_SCORED_BLOCK_FRACTION" in failed
    assert "POSITIVE_EARLY_BLOCK_MEAN" in failed
    assert "POSITIVE_LATE_BLOCK_MEAN" in failed


def test_all_fixed_clauses_advance_only_to_paper_execution() -> None:
    """Broad stable component-incremental touch evidence earns only the named next study."""
    assessment = assess_activity_gate_development_campaign(
        _campaign(),
        ll04e_primary_development_standard(),
    )
    observed = _clauses(assessment)

    assert assessment.status == "ADVANCE_TO_PAPER_EXECUTION_STUDY"
    assert assessment.coverage_passes
    assert assessment.economics_passes
    assert all(clause.passes for clause in assessment.clauses)
    assert observed["MINIMUM_SCORED_BLOCK_FRACTION"] == Decimal(1)
    assert observed["MINIMUM_JOINT_SCORABLE_RETENTION"] == Decimal("0.25")
    assert observed["MAXIMUM_JOINT_UNRESOLVED_ENTERED_FRACTION"] == Decimal(0)
    assert observed["MINIMUM_POSITIVE_SCORED_BLOCK_FRACTION"] == Decimal(1)
    assert observed["MAXIMUM_LARGEST_POSITIVE_BLOCK_SHARE"] == Decimal("0.1")


def test_joint_gate_must_beat_each_component_rival() -> None:
    """A pooled win over complete history cannot hide inferiority to recent activity alone."""
    assessment = assess_activity_gate_development_campaign(
        _campaign(
            scenario=replace(
                PASSING_SCENARIO,
                quiet_only_pnl=Decimal("-0.10"),
                recent_only_pnl=Decimal("0.06"),
                joint_failure_pnl=Decimal("-0.10"),
            ),
        ),
        ll04e_primary_development_standard(),
    )
    clauses = {clause.clause_kind: clause for clause in assessment.clauses}

    assert clauses["POSITIVE_POOLED_PRIMARY_VALUE"].passes
    assert clauses["POSITIVE_POOLED_JOINT_MINUS_QUIET_ONLY"].passes
    assert not clauses["POSITIVE_POOLED_JOINT_MINUS_RECENT_ACTIVITY_ONLY"].passes
    assert assessment.status == "REJECT_DEVELOPMENT"


def test_one_dominant_positive_block_forces_rejection() -> None:
    """A positive pooled result cannot advance when one block supplies most improvement."""
    scenarios = (
        replace(PASSING_SCENARIO, joint_pnl=Decimal("0.50")),
        *(
            replace(PASSING_SCENARIO, joint_pnl=Decimal("0.001"))
            for _ in range(PASSING_BLOCK_COUNT - 1)
        ),
    )
    assessment = assess_activity_gate_development_campaign(
        _campaign(scenarios_by_block=scenarios),
        ll04e_primary_development_standard(),
    )
    clauses = {clause.clause_kind: clause for clause in assessment.clauses}

    assert clauses["POSITIVE_POOLED_PRIMARY_VALUE"].passes
    assert clauses["MINIMUM_POSITIVE_SCORED_BLOCK_FRACTION"].passes
    assert not clauses["MAXIMUM_LARGEST_POSITIVE_BLOCK_SHARE"].passes
    assert assessment.status == "REJECT_DEVELOPMENT"


def test_campaign_primary_metric_cannot_change_after_standard_is_declared() -> None:
    """A neighboring headline metric receives a new campaign rather than silent evaluation."""
    campaign = _campaign()
    changed_definition = replace(
        campaign.definition,
        primary_metric="NET_TOUCH_PNL_PER_SHARE_MEAN_CHANGE",
    )
    changed_campaign = evaluate_activity_gate_campaign(
        changed_definition,
        tuple(block.block for block in campaign.blocks),
    )

    with pytest.raises(ValueError, match="primary identity differs"):
        assess_activity_gate_development_campaign(
            changed_campaign,
            ll04e_primary_development_standard(),
        )


def test_manual_threshold_copy_cannot_claim_ll04d_ancestry() -> None:
    """Numerically equal gates still fail when their exact derived policy identity differs."""
    campaign = _campaign(scenario=replace(PASSING_SCENARIO, exact_policy_identity=False))

    with pytest.raises(ValueError, match="exact LL-04d-derived gate identity"):
        assess_activity_gate_development_campaign(
            campaign,
            ll04e_primary_development_standard(),
        )


def test_missing_scorable_denominators_remain_insufficient() -> None:
    """Absent outcomes cannot be imputed into retention or an economic disposition."""
    assessment = assess_activity_gate_development_campaign(
        _campaign(
            scenario=replace(
                PASSING_SCENARIO,
                joint_pnl=None,
                quiet_only_pnl=None,
                recent_only_pnl=None,
                joint_failure_pnl=None,
            ),
        ),
        ll04e_primary_development_standard(),
    )
    clauses = {clause.clause_kind: clause for clause in assessment.clauses}

    assert assessment.status == "INSUFFICIENT_COVERAGE"
    assert clauses["MINIMUM_JOINT_SCORABLE_RETENTION"].observed_value is None
    assert not clauses["MINIMUM_JOINT_SCORABLE_RETENTION"].passes
    assert clauses["MAXIMUM_JOINT_UNRESOLVED_ENTERED_FRACTION"].observed_value == Decimal(1)
    assert not clauses["MAXIMUM_JOINT_UNRESOLVED_ENTERED_FRACTION"].passes


def test_standard_and_assessment_reject_invalid_or_mutated_evidence() -> None:
    """Neither decision thresholds nor stored disposition can drift after construction."""
    standard = ll04e_primary_development_standard()
    with pytest.raises(ValueError, match="valid fixed thresholds"):
        replace(standard, minimum_block_count=0)
    with pytest.raises(ValueError, match="valid fixed thresholds"):
        replace(standard, minimum_scored_block_fraction=Decimal("1.01"))

    assessment = assess_activity_gate_development_campaign(_campaign(), standard)
    with pytest.raises(ValueError, match="detached from its exact campaign"):
        replace(assessment, status="REJECT_DEVELOPMENT")
    with pytest.raises(ValueError, match="detached from its exact campaign"):
        replace(
            assessment,
            clauses=(
                replace(assessment.clauses[0], observed_value=999),
                *assessment.clauses[1:],
            ),
        )
