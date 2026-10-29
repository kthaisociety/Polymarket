"""LL-04d latency-scaled activity-policy identity and arithmetic adversaries."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest

from research_agent.data_adapters.polymarket.book_activity_campaign import (
    ActivityGateCampaignDefinition,
    activity_gate_parent_recipe,
)
from research_agent.data_adapters.polymarket.book_activity_policy import (
    ActivityGateLatencyScaledPolicy,
    derive_latency_scaled_activity_gate,
    ll04d_latency_scaled_primary_policy,
)
from research_agent.data_adapters.polymarket.book_corpus import BookLeg
from research_agent.data_adapters.polymarket.book_imbalance import DepthImbalanceDefinition
from research_agent.data_adapters.polymarket.low_latency import PostJumpReversalDefinition

YES = BookLeg("polymarket", "market-policy", 0)
NO = BookLeg("polymarket", "market-policy", 1)
ACTION_DELAY = timedelta(microseconds=123_457)
EXPECTED_MINIMUM_RECENT_SOURCE_EVENT_COUNT = 2


def _post_jump_definition(
    *,
    action_delay: timedelta = ACTION_DELAY,
) -> PostJumpReversalDefinition:
    return PostJumpReversalDefinition(
        definition_id="ll03-policy-parent",
        scope_authority_ref="scope:ll04d",
        reference_leg=YES,
        complement_leg=NO,
        minimum_midpoint_shock=Decimal("0.02"),
        maximum_shock_gap=timedelta(seconds=5),
        action_delay=action_delay,
        maximum_quote_age=timedelta(seconds=2),
        reversal_distance=Decimal("0.02"),
        continuation_distance=Decimal("0.02"),
        maximum_holding_period=timedelta(seconds=10),
        minimum_entry_quantity=Decimal(1),
        round_trip_cost_per_share=Decimal("0.01"),
    )


def _depth_definition() -> DepthImbalanceDefinition:
    return DepthImbalanceDefinition(
        definition_id="ll05-policy-parent",
        scope_authority_ref="scope:ll04d",
        reference_leg=YES,
        complement_leg=NO,
        entry_imbalance_threshold=Decimal("0.50"),
        exit_imbalance_threshold=Decimal("0.10"),
        maximum_spread=Decimal("0.03"),
        minimum_total_depth=Decimal(50),
        minimum_reference_midpoint=Decimal("0.10"),
        maximum_reference_midpoint=Decimal("0.90"),
        action_delay=ACTION_DELAY,
        maximum_quote_age=timedelta(seconds=2),
        take_profit_distance=Decimal("0.02"),
        stop_loss_distance=Decimal("0.02"),
        maximum_holding_period=timedelta(seconds=10),
        minimum_entry_quantity=Decimal(1),
        round_trip_cost_per_share=Decimal("0.01"),
    )


def test_named_primary_policy_has_one_exact_unfitted_candidate() -> None:
    """The authored trial budget has one stable multiplier/count identity."""
    policy = ll04d_latency_scaled_primary_policy()

    assert policy == ActivityGateLatencyScaledPolicy(
        definition_id="ll04d-latency-scaled-primary-v1",
        recent_window_action_delay_multiplier=5,
        maximum_quiet_action_delay_multiplier=1,
        minimum_recent_source_event_count=2,
    )


def test_post_jump_policy_derivation_preserves_microsecond_exact_latency_scale() -> None:
    """Elapsed windows multiply the declared H3 delay without rounding or wall-clock defaults."""
    parent = _post_jump_definition()
    policy = ll04d_latency_scaled_primary_policy()

    gate = derive_latency_scaled_activity_gate(parent, policy)

    assert gate.parent_strategy_kind == "LL03_POST_JUMP_REVERSAL"
    assert gate.parent_strategy_definition_id == parent.definition_id
    assert gate.scope_authority_ref == parent.scope_authority_ref
    assert gate.reference_leg == parent.reference_leg
    assert gate.maximum_quiet_duration == ACTION_DELAY
    assert gate.recent_window == ACTION_DELAY * 5
    assert gate.minimum_recent_source_event_count == EXPECTED_MINIMUM_RECENT_SOURCE_EVENT_COUNT
    assert gate.definition_id.startswith(
        "ll04d-latency-scaled-primary-v1:LL03_POST_JUMP_REVERSAL:ll03-policy-parent:"
    )


def test_depth_policy_uses_the_same_dimensionless_candidate() -> None:
    """H5 receives identical multipliers while retaining its distinct parent kind and recipe."""
    parent = _depth_definition()

    gate = derive_latency_scaled_activity_gate(parent, ll04d_latency_scaled_primary_policy())

    assert gate.parent_strategy_kind == "LL05_DEPTH_IMBALANCE"
    assert gate.maximum_quiet_duration == ACTION_DELAY
    assert gate.recent_window == ACTION_DELAY * 5
    assert gate.parent_strategy_definition_id == parent.definition_id


def test_parent_meaning_changes_derived_gate_identity_even_with_reused_label() -> None:
    """A caller cannot mutate a parent recipe under one definition label without a new gate ID."""
    parent = _post_jump_definition()
    changed_parent = replace(parent, minimum_midpoint_shock=Decimal("0.03"))
    policy = ll04d_latency_scaled_primary_policy()

    original_gate = derive_latency_scaled_activity_gate(parent, policy)
    changed_gate = derive_latency_scaled_activity_gate(changed_parent, policy)

    assert original_gate.definition_id != changed_gate.definition_id
    assert original_gate.recent_window == changed_gate.recent_window
    assert derive_latency_scaled_activity_gate(parent, policy) == original_gate


def test_zero_parent_action_delay_fails_instead_of_inventing_elapsed_windows() -> None:
    """A zero-delay upper bound cannot silently become a positive activity-time candidate."""
    parent = _post_jump_definition(action_delay=timedelta(0))

    with pytest.raises(ValueError, match="positive parent action delay"):
        derive_latency_scaled_activity_gate(parent, ll04d_latency_scaled_primary_policy())


def test_policy_rejects_missing_or_incoherent_dimensionless_thresholds() -> None:
    """No multiplier or count threshold arrives through a default or invalid geometry."""
    policy = ll04d_latency_scaled_primary_policy()

    with pytest.raises(ValueError, match="exact positive threshold identity"):
        replace(policy, definition_id="")
    with pytest.raises(ValueError, match="exact positive threshold identity"):
        replace(policy, recent_window_action_delay_multiplier=0)
    with pytest.raises(ValueError, match="exact positive threshold identity"):
        replace(policy, maximum_quiet_action_delay_multiplier=0)
    with pytest.raises(ValueError, match="exact positive threshold identity"):
        replace(
            policy,
            recent_window_action_delay_multiplier=1,
            maximum_quiet_action_delay_multiplier=2,
        )
    with pytest.raises(ValueError, match="exact positive threshold identity"):
        replace(policy, minimum_recent_source_event_count=0)


def test_derived_policy_composes_exactly_with_campaign_identity() -> None:
    """LL-04c receives the derived activity fields and unchanged complete parent recipe."""
    parent = _post_jump_definition()
    gate = derive_latency_scaled_activity_gate(parent, ll04d_latency_scaled_primary_policy())

    campaign = ActivityGateCampaignDefinition(
        definition_id="ll04c-from-ll04d-test",
        parent_strategy_kind=gate.parent_strategy_kind,
        parent_strategy_recipe=activity_gate_parent_recipe(parent),
        scope_authority_ref=gate.scope_authority_ref,
        recent_window=gate.recent_window,
        maximum_quiet_duration=gate.maximum_quiet_duration,
        minimum_recent_source_event_count=gate.minimum_recent_source_event_count,
        primary_contrast_kind="JOINT_MINUS_COMPLETE_HISTORY",
        primary_metric="NET_TOUCH_PNL_PER_COLLATERAL_SECOND_CHANGE",
    )

    assert campaign.parent_strategy_recipe == activity_gate_parent_recipe(parent)
    assert campaign.recent_window == ACTION_DELAY * 5
    assert campaign.maximum_quiet_duration == ACTION_DELAY
    assert campaign.minimum_recent_source_event_count == EXPECTED_MINIMUM_RECENT_SOURCE_EVENT_COUNT
