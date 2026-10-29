"""LL-04f exact retained-snapshot application adversaries."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

from research_agent.data_adapters import polymarket
from research_agent.data_adapters.polymarket.book_activity_advancement import (
    ll04e_primary_development_standard,
)
from research_agent.data_adapters.polymarket.book_activity_application import (
    ActivityGateApplicationBlock,
    ActivityGateApplicationPlan,
    ActivityGateSnapshotBinding,
    run_activity_gate_application,
)
from research_agent.data_adapters.polymarket.book_activity_campaign import (
    activity_gate_parent_recipe,
)
from research_agent.data_adapters.polymarket.book_corpus import (
    BookCorpus,
    BookCorpusRequest,
    BookCorpusSnapshotRef,
    BookCorpusStore,
    BookLeg,
    BookSnapshotRecord,
)
from research_agent.data_adapters.polymarket.book_imbalance import (
    DepthImbalanceDefinition,
)
from research_agent.data_adapters.polymarket.low_latency import (
    PostJumpReversalDefinition,
)

if TYPE_CHECKING:
    from pathlib import Path

    from research_agent.data_adapters.polymarket.book_activity_gate import (
        ActivityGateParentDefinition,
        ActivityGateParentKind,
    )

START = datetime(2026, 8, 23, 12, tzinfo=UTC)
END = START + timedelta(seconds=10)
ENVIRONMENT_ID = "test-h4f"
SCOPE_AUTHORITY_REF = "scope:h4f"
ACTION_DELAY = timedelta(seconds=1)
EXPECTED_MARKET_COUNT = 2


def _post_jump_definition(market_id: str) -> PostJumpReversalDefinition:
    return PostJumpReversalDefinition(
        definition_id=f"ll03-{market_id}",
        scope_authority_ref=SCOPE_AUTHORITY_REF,
        reference_leg=BookLeg("polymarket", market_id, 0),
        complement_leg=BookLeg("polymarket", market_id, 1),
        minimum_midpoint_shock=Decimal("0.02"),
        maximum_shock_gap=timedelta(seconds=5),
        action_delay=ACTION_DELAY,
        maximum_quote_age=timedelta(seconds=2),
        reversal_distance=Decimal("0.02"),
        continuation_distance=Decimal("0.02"),
        maximum_holding_period=timedelta(seconds=2),
        minimum_entry_quantity=Decimal(1),
        round_trip_cost_per_share=Decimal("0.01"),
    )


def _depth_definition(market_id: str) -> DepthImbalanceDefinition:
    return DepthImbalanceDefinition(
        definition_id=f"ll05-{market_id}",
        scope_authority_ref=SCOPE_AUTHORITY_REF,
        reference_leg=BookLeg("polymarket", market_id, 0),
        complement_leg=BookLeg("polymarket", market_id, 1),
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
        maximum_holding_period=timedelta(seconds=2),
        minimum_entry_quantity=Decimal(1),
        round_trip_cost_per_share=Decimal("0.01"),
    )


def _retain_snapshot(
    store: BookCorpusStore,
    definition: ActivityGateParentDefinition,
    *,
    start_at: datetime = START,
    end_at: datetime = END,
    scope_authority_ref: str = SCOPE_AUTHORITY_REF,
) -> BookCorpusSnapshotRef:
    events = tuple(
        BookSnapshotRecord(
            leg=leg,
            ts=start_at + timedelta(microseconds=index),
            reference_time=start_at + timedelta(microseconds=index),
            seq=index + 1,
            bids=(("0.49", "100"), ("0.48", "50")),
            asks=(("0.51", "100"), ("0.52", "50")),
            raw={"kind": "snapshot", "market_id": leg.market_id, "index": index},
        )
        for index, leg in enumerate(sorted((definition.reference_leg, definition.complement_leg)))
    )
    request = BookCorpusRequest(
        environment_id=ENVIRONMENT_ID,
        scope_authority_ref=scope_authority_ref,
        legs=tuple(sorted((definition.reference_leg, definition.complement_leg))),
        start_at=start_at,
        end_at=end_at,
    )
    return store.retain(BookCorpus(request, events)).ref


def _parent_kind(definition: ActivityGateParentDefinition) -> ActivityGateParentKind:
    if isinstance(definition, PostJumpReversalDefinition):
        return "LL03_POST_JUMP_REVERSAL"
    return "LL05_DEPTH_IMBALANCE"


def _plan(
    definitions_and_refs: tuple[tuple[ActivityGateParentDefinition, BookCorpusSnapshotRef], ...],
    *,
    start_at: datetime = START,
    end_at: datetime = END,
    environment_id: str = ENVIRONMENT_ID,
) -> ActivityGateApplicationPlan:
    first_definition = definitions_and_refs[0][0]
    return ActivityGateApplicationPlan(
        definition_id="ll04f-test-plan",
        campaign_definition_id="ll04c-from-ll04f-test",
        environment_id=environment_id,
        scope_authority_ref=SCOPE_AUTHORITY_REF,
        parent_strategy_kind=_parent_kind(first_definition),
        parent_strategy_recipe=activity_gate_parent_recipe(first_definition),
        development_standard=ll04e_primary_development_standard(),
        blocks=(
            ActivityGateApplicationBlock(
                block_id="block-0",
                start_at=start_at,
                end_at=end_at,
                bindings=tuple(
                    ActivityGateSnapshotBinding(
                        binding_id=f"binding-{index}",
                        snapshot_ref=snapshot_ref,
                        parent_strategy_definition=definition,
                    )
                    for index, (definition, snapshot_ref) in enumerate(definitions_and_refs)
                ),
            ),
        ),
    )


def test_h3_plan_loads_verified_bytes_and_composes_through_ll04e(tmp_path: Path) -> None:
    """One exact H3 snapshot reaches an explicit insufficient development disposition."""
    store = BookCorpusStore(tmp_path)
    definition = _post_jump_definition("market-h3")
    snapshot_ref = _retain_snapshot(store, definition)
    object_path = store.object_path(snapshot_ref)
    before = object_path.read_bytes()

    plan = _plan(((definition, snapshot_ref),))
    result = polymarket.run_activity_gate_application(store, plan)

    assert object_path.read_bytes() == before
    assert isinstance(plan, polymarket.ActivityGateApplicationPlan)
    assert result.snapshots[0].ref == snapshot_ref
    assert result.campaign.definition.parent_strategy_kind == "LL03_POST_JUMP_REVERSAL"
    assert result.campaign.blocks[0].aggregate.populations[0].market_count == 1
    assert result.campaign.pooled.populations[0].economics.attempt_count == 0
    assert result.assessment.status == "INSUFFICIENT_COVERAGE"
    assert not result.assessment.coverage_passes


def test_h5_plan_uses_the_same_exact_application_boundary(tmp_path: Path) -> None:
    """The retained-snapshot runner composes H5 without substituting the H3 screen."""
    store = BookCorpusStore(tmp_path)
    definition = _depth_definition("market-h5")
    snapshot_ref = _retain_snapshot(store, definition)

    result = run_activity_gate_application(store, _plan(((definition, snapshot_ref),)))

    assert result.campaign.definition.parent_strategy_kind == "LL05_DEPTH_IMBALANCE"
    assert result.campaign.pooled.populations[0].economics.attempt_count == 0
    assert result.assessment.status == "INSUFFICIENT_COVERAGE"


@pytest.mark.parametrize("mismatch", ["coverage", "environment", "scope", "legs"])
def test_snapshot_identity_mismatch_fails_instead_of_reinterpreting_input(
    tmp_path: Path,
    mismatch: str,
) -> None:
    """Valid retained bytes cannot enter a plan with different scientific identity."""
    store = BookCorpusStore(tmp_path)
    definition = _post_jump_definition("market-exact")
    plan_definition = definition
    start_at = START
    environment_id = ENVIRONMENT_ID
    snapshot_scope = SCOPE_AUTHORITY_REF
    if mismatch == "coverage":
        start_at += timedelta(microseconds=1)
    elif mismatch == "environment":
        environment_id = "foreign-environment"
    elif mismatch == "scope":
        snapshot_scope = "scope:foreign-snapshot"
    else:
        plan_definition = replace(
            definition,
            reference_leg=BookLeg("polymarket", "foreign-market", 0),
            complement_leg=BookLeg("polymarket", "foreign-market", 1),
        )
    snapshot_ref = _retain_snapshot(
        store,
        definition,
        scope_authority_ref=snapshot_scope,
    )
    plan = _plan(
        ((plan_definition, snapshot_ref),),
        start_at=start_at,
        environment_id=environment_id,
    )

    with pytest.raises(ValueError, match="snapshot identity differs from its exact plan binding"):
        run_activity_gate_application(store, plan)


def test_plan_rejects_scope_duplicate_snapshot_recipe_and_parent_kind_drift(
    tmp_path: Path,
) -> None:
    """One plan cannot combine neighboring scope, source, recipe, or strategy identities."""
    store = BookCorpusStore(tmp_path)
    first = _post_jump_definition("market-first")
    second = _post_jump_definition("market-second")
    first_ref = _retain_snapshot(store, first)
    second_ref = _retain_snapshot(store, second)
    plan = _plan(((first, first_ref), (second, second_ref)))

    with pytest.raises(ValueError, match="scope and parent identity"):
        replace(plan, scope_authority_ref="scope:foreign")
    duplicate_binding = replace(plan.blocks[0].bindings[1], snapshot_ref=first_ref)
    with pytest.raises(ValueError, match="snapshot references must be unique"):
        replace(
            plan,
            blocks=(
                replace(plan.blocks[0], bindings=(plan.blocks[0].bindings[0], duplicate_binding)),
            ),
        )
    changed_recipe = replace(second, minimum_midpoint_shock=Decimal("0.03"))
    with pytest.raises(ValueError, match="scope and parent identity"):
        _plan(((first, first_ref), (changed_recipe, second_ref)))
    depth = _depth_definition("market-second")
    with pytest.raises(ValueError, match="scope and parent identity"):
        _plan(((first, first_ref), (depth, second_ref)))
    reversed_same_market = replace(
        first,
        definition_id="ll03-market-first-reversed",
        reference_leg=first.complement_leg,
        complement_leg=first.reference_leg,
    )
    distinct_unloaded_ref = BookCorpusSnapshotRef("1" * 64, 10)
    with pytest.raises(ValueError, match="duplicate parent market"):
        _plan(((first, first_ref), (reversed_same_market, distinct_unloaded_ref)))


def test_invalid_or_missing_snapshot_reference_fails_closed(tmp_path: Path) -> None:
    """Malformed identity fails in the plan and absent canonical bytes fail during load."""
    definition = _post_jump_definition("market-missing")
    invalid_ref = BookCorpusSnapshotRef("not-a-sha256", 10)
    with pytest.raises(ValueError, match="valid retained snapshot reference"):
        _plan(((definition, invalid_ref),))

    missing_ref = BookCorpusSnapshotRef("0" * 64, 10)
    plan = _plan(((definition, missing_ref),))
    with pytest.raises(ValueError, match="unverified book corpus snapshot"):
        run_activity_gate_application(BookCorpusStore(tmp_path), plan)


def test_result_rejects_snapshot_order_and_campaign_detachment(tmp_path: Path) -> None:
    """Stored application outputs remain recomputable from their canonical input order."""
    store = BookCorpusStore(tmp_path)
    first = _post_jump_definition("market-a")
    second = _post_jump_definition("market-b")
    first_ref = _retain_snapshot(store, first)
    second_ref = _retain_snapshot(store, second)
    result = run_activity_gate_application(
        store,
        _plan(((first, first_ref), (second, second_ref))),
    )

    assert result.campaign.pooled.populations[0].market_count == EXPECTED_MARKET_COUNT
    with pytest.raises(ValueError, match="snapshot identity differs from its exact plan binding"):
        replace(result, snapshots=tuple(reversed(result.snapshots)))
    alternate_result = run_activity_gate_application(
        store,
        replace(result.plan, campaign_definition_id="different-campaign-identity"),
    )
    with pytest.raises(ValueError, match="detached from its exact retained snapshots"):
        replace(result, campaign=alternate_result.campaign)


def test_application_blocks_must_be_ordered_nonoverlapping_and_nonempty(
    tmp_path: Path,
) -> None:
    """The application plan cannot repair or silently drop its chronological structure."""
    store = BookCorpusStore(tmp_path)
    definition = _post_jump_definition("market-blocks")
    snapshot_ref = _retain_snapshot(store, definition)
    plan = _plan(((definition, snapshot_ref),))
    first = plan.blocks[0]
    with pytest.raises(ValueError, match="requires identity, coverage, and bindings"):
        replace(first, block_id="empty", bindings=())
    overlapping = replace(
        first,
        block_id="overlap",
        start_at=first.start_at + timedelta(seconds=1),
        end_at=first.end_at + timedelta(seconds=1),
    )
    with pytest.raises(ValueError, match="ordered and non-overlapping"):
        replace(plan, blocks=(first, overlapping))
