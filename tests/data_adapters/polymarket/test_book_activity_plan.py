"""LL-04g immutable application-plan precommit adversaries."""

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
)
from research_agent.data_adapters.polymarket.book_activity_campaign import (
    activity_gate_parent_recipe,
)
from research_agent.data_adapters.polymarket.book_activity_plan import (
    ActivityGateApplicationPlanRef,
    ActivityGateApplicationPlanStore,
    run_precommitted_activity_gate_application,
)
from research_agent.data_adapters.polymarket.book_corpus import (
    BookCorpus,
    BookCorpusRequest,
    BookCorpusSnapshotRef,
    BookCorpusStore,
    BookLeg,
    BookSnapshotRecord,
)
from research_agent.data_adapters.polymarket.low_latency import PostJumpReversalDefinition

if TYPE_CHECKING:
    from pathlib import Path

START = datetime(2026, 8, 23, 12, tzinfo=UTC)
END = START + timedelta(seconds=10)
ENVIRONMENT_ID = "test-h4g"
SCOPE_AUTHORITY_REF = "scope:h4g"
EXPECTED_CHANGED_IDENTITY_COUNT = 5


def _definition(market_id: str) -> PostJumpReversalDefinition:
    return PostJumpReversalDefinition(
        definition_id=f"ll03-{market_id}",
        scope_authority_ref=SCOPE_AUTHORITY_REF,
        reference_leg=BookLeg("polymarket", market_id, 0),
        complement_leg=BookLeg("polymarket", market_id, 1),
        minimum_midpoint_shock=Decimal("0.020"),
        maximum_shock_gap=timedelta(seconds=5),
        action_delay=timedelta(seconds=1),
        maximum_quote_age=timedelta(seconds=2),
        reversal_distance=Decimal("0.02"),
        continuation_distance=Decimal("0.02"),
        maximum_holding_period=timedelta(seconds=2),
        minimum_entry_quantity=Decimal(1),
        round_trip_cost_per_share=Decimal("0.01"),
    )


def _plan(
    definitions_and_refs: tuple[tuple[PostJumpReversalDefinition, BookCorpusSnapshotRef], ...],
) -> ActivityGateApplicationPlan:
    first_definition = definitions_and_refs[0][0]
    return ActivityGateApplicationPlan(
        definition_id="ll04f-precommitted-test",
        campaign_definition_id="ll04c-precommitted-test",
        environment_id=ENVIRONMENT_ID,
        scope_authority_ref=SCOPE_AUTHORITY_REF,
        parent_strategy_kind="LL03_POST_JUMP_REVERSAL",
        parent_strategy_recipe=activity_gate_parent_recipe(first_definition),
        development_standard=ll04e_primary_development_standard(),
        blocks=(
            ActivityGateApplicationBlock(
                block_id="block-0",
                start_at=START,
                end_at=END,
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


def _retain_snapshot(
    store: BookCorpusStore,
    definition: PostJumpReversalDefinition,
) -> BookCorpusSnapshotRef:
    legs = tuple(sorted((definition.reference_leg, definition.complement_leg)))
    events = tuple(
        BookSnapshotRecord(
            leg=leg,
            ts=START + timedelta(microseconds=index),
            reference_time=START + timedelta(microseconds=index),
            seq=index + 1,
            bids=(("0.49", "100"),),
            asks=(("0.51", "100"),),
            raw={"kind": "snapshot", "market_id": leg.market_id, "index": index},
        )
        for index, leg in enumerate(legs)
    )
    request = BookCorpusRequest(
        environment_id=ENVIRONMENT_ID,
        scope_authority_ref=SCOPE_AUTHORITY_REF,
        legs=legs,
        start_at=START,
        end_at=END,
    )
    return store.retain(BookCorpus(request, events)).ref


def test_plan_ref_is_path_independent_deterministic_and_semantically_canonical(
    tmp_path: Path,
) -> None:
    """Equivalent scalar spellings retain one identity across store locations."""
    definition = _definition("market-a")
    snapshot_ref = BookCorpusSnapshotRef("a" * 64, 100)
    plan = _plan(((definition, snapshot_ref),))
    equivalent_definition = replace(
        definition,
        minimum_midpoint_shock=Decimal("0.02"),
        action_delay=timedelta(microseconds=1_000_000),
    )
    equivalent_plan = _plan(((equivalent_definition, snapshot_ref),))

    first = ActivityGateApplicationPlanStore(tmp_path / "first")
    second = ActivityGateApplicationPlanStore(tmp_path / "second")

    assert first.from_plan(plan) == second.from_plan(equivalent_plan)
    assert first.from_plan(plan).uri.startswith("polymarket-activity-application-plan:")


def test_plan_ref_changes_for_nested_parent_snapshot_block_and_sequence_identity(
    tmp_path: Path,
) -> None:
    """Every accepted meaning-changing plan mutation changes content identity."""
    first_definition = _definition("market-a")
    second_definition = _definition("market-b")
    first_ref = BookCorpusSnapshotRef("a" * 64, 100)
    second_ref = BookCorpusSnapshotRef("b" * 64, 200)
    plan = _plan(((first_definition, first_ref), (second_definition, second_ref)))
    store = ActivityGateApplicationPlanStore(tmp_path)
    baseline = store.from_plan(plan)
    changed_parent = replace(first_definition, minimum_midpoint_shock=Decimal("0.03"))
    changed_second_parent = replace(second_definition, minimum_midpoint_shock=Decimal("0.03"))
    parent_plan = _plan(((changed_parent, first_ref), (changed_second_parent, second_ref)))
    changed_ref = replace(first_ref, size_bytes=101)
    ref_plan = _plan(((first_definition, changed_ref), (second_definition, second_ref)))
    changed_block = replace(plan.blocks[0], block_id="block-renamed")
    block_plan = replace(plan, blocks=(changed_block,))
    reordered_block = replace(
        plan.blocks[0],
        bindings=tuple(reversed(plan.blocks[0].bindings)),
    )
    reordered_plan = replace(plan, blocks=(reordered_block,))

    changed = {
        store.from_plan(parent_plan),
        store.from_plan(ref_plan),
        store.from_plan(block_plan),
        store.from_plan(reordered_plan),
        store.from_plan(replace(plan, definition_id="new-plan-identity")),
    }
    assert baseline not in changed
    assert len(changed) == EXPECTED_CHANGED_IDENTITY_COUNT


def test_retain_is_exact_idempotent_verified_and_path_sanitized(tmp_path: Path) -> None:
    """Exact retries preserve one canonical object and expose no local path."""
    store = ActivityGateApplicationPlanStore(tmp_path / "plans")
    plan = _plan(((_definition("market-a"), BookCorpusSnapshotRef("a" * 64, 100)),))

    first = store.retain(plan)
    second = store.retain(plan)

    assert first == second
    assert store.verify(first.ref)
    assert store.require(plan, first.ref) == first.ref
    assert str(tmp_path) not in first.ref.uri
    assert tuple((tmp_path / "plans" / "objects").rglob("*.json")) == (
        store.object_path(first.ref),
    )


def test_missing_tampered_and_conflicting_plan_objects_fail_closed(tmp_path: Path) -> None:
    """An absent or corrupted identity cannot be repaired or overwritten as success."""
    store = ActivityGateApplicationPlanStore(tmp_path)
    plan = _plan(((_definition("market-a"), BookCorpusSnapshotRef("a" * 64, 100)),))
    missing_ref = ActivityGateApplicationPlanRef("0" * 64, 10)
    with pytest.raises(ValueError, match="unverified activity application plan"):
        store.require(plan, missing_ref)

    retention = store.retain(plan)
    path = store.object_path(retention.ref)
    path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="unverified activity application plan"):
        store.require(plan, retention.ref)
    before = path.read_bytes()
    with pytest.raises(ValueError, match="identity conflicts with changed bytes"):
        store.retain(plan)
    assert path.read_bytes() == before


def test_changed_plan_is_rejected_before_any_corpus_load(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An old receipt cannot expose corpus values for a structurally changed plan."""
    definition = _definition("market-a")
    snapshot_ref = BookCorpusSnapshotRef("a" * 64, 100)
    plan = _plan(((definition, snapshot_ref),))
    plan_store = ActivityGateApplicationPlanStore(tmp_path / "plans")
    receipt = plan_store.retain(plan)
    corpus_store = BookCorpusStore(tmp_path / "corpora")
    corpus_load_called = False

    def fail_if_loaded(_store: BookCorpusStore, _ref: BookCorpusSnapshotRef) -> None:
        nonlocal corpus_load_called
        corpus_load_called = True
        pytest.fail("corpus load occurred before plan verification")

    monkeypatch.setattr(BookCorpusStore, "load", fail_if_loaded)
    changed_plan = replace(plan, definition_id="changed-after-receipt")

    with pytest.raises(ValueError, match="does not match its retained reference"):
        run_precommitted_activity_gate_application(
            corpus_store,
            plan_store,
            receipt.ref,
            changed_plan,
        )
    assert not corpus_load_called


def test_verified_precommit_composes_the_unchanged_ll04f_application(tmp_path: Path) -> None:
    """The exact retained plan delegates to LL-04f without changing its result."""
    corpus_store = BookCorpusStore(tmp_path / "corpora")
    definition = _definition("market-a")
    snapshot_ref = _retain_snapshot(corpus_store, definition)
    plan = _plan(((definition, snapshot_ref),))
    plan_store = ActivityGateApplicationPlanStore(tmp_path / "plans")
    receipt = plan_store.retain(plan)

    result = run_precommitted_activity_gate_application(
        corpus_store,
        plan_store,
        receipt.ref,
        plan,
    )

    assert result.plan == plan
    assert result.snapshots[0].ref == snapshot_ref
    assert result.assessment.status == "INSUFFICIENT_COVERAGE"
    assert isinstance(receipt.ref, polymarket.ActivityGateApplicationPlanRef)
    assert polymarket.run_precommitted_activity_gate_application is (
        run_precommitted_activity_gate_application
    )
