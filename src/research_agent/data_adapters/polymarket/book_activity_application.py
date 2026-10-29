"""Exact retained-snapshot application of the fixed LL-04 activity candidate."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from typing import TYPE_CHECKING

from research_agent.data_adapters.polymarket.book_activity import (
    BookActivityDefinition,
    build_book_activity_series,
)
from research_agent.data_adapters.polymarket.book_activity_advancement import (
    assess_activity_gate_development_campaign,
    ll04e_primary_development_standard,
)
from research_agent.data_adapters.polymarket.book_activity_campaign import (
    ActivityGateCampaignBlock,
    ActivityGateCampaignDefinition,
    activity_gate_parent_recipe,
    evaluate_activity_gate_campaign,
)
from research_agent.data_adapters.polymarket.book_activity_gate import (
    compare_activity_gate_rivals,
    compare_activity_participation_gate,
)
from research_agent.data_adapters.polymarket.book_activity_policy import (
    derive_latency_scaled_activity_gate,
)
from research_agent.data_adapters.polymarket.book_corpus import (
    BookCorpusSnapshot,
    BookCorpusSnapshotRef,
    BookCorpusStore,
    register_book_corpus,
)
from research_agent.data_adapters.polymarket.book_imbalance import screen_depth_imbalance_impulse
from research_agent.data_adapters.polymarket.low_latency import (
    PostJumpReversalDefinition,
    screen_book_post_jump_reversal,
)

if TYPE_CHECKING:
    from datetime import datetime, timedelta

    from research_agent.data_adapters.polymarket.book_activity_advancement import (
        ActivityGateDevelopmentAssessment,
        ActivityGateDevelopmentStandard,
    )
    from research_agent.data_adapters.polymarket.book_activity_campaign import (
        ActivityGateCampaignResult,
        ActivityGateParentRecipe,
    )
    from research_agent.data_adapters.polymarket.book_activity_gate import (
        ActivityGateParentDefinition,
        ActivityGateParentKind,
        ActivityGateParentScreen,
        ActivityGateRivalAblation,
    )
    from research_agent.data_adapters.polymarket.book_corpus import BookCorpusRegistration

_SHA256_LENGTH = 64


def _require_aware(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        message = f"{field} must be timezone-aware"
        raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ActivityGateSnapshotBinding:
    """One exact retained object and its complete market-specific H3/H5 parent."""

    binding_id: str
    snapshot_ref: BookCorpusSnapshotRef
    parent_strategy_definition: ActivityGateParentDefinition

    def __post_init__(self) -> None:
        """Require a usable immutable retained-object identity and supported parent."""
        digest = self.snapshot_ref.content_sha256
        invalid_digest = len(digest) != _SHA256_LENGTH or any(
            character not in "0123456789abcdef" for character in digest
        )
        if not self.binding_id or invalid_digest or self.snapshot_ref.size_bytes <= 0:
            message = "activity application binding requires a valid retained snapshot reference"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ActivityGateApplicationBlock:
    """One exact chronological collector block and its retained market bindings."""

    block_id: str
    start_at: datetime
    end_at: datetime
    bindings: tuple[ActivityGateSnapshotBinding, ...]

    def __post_init__(self) -> None:
        """Require an aware nonempty block with distinct binding identities."""
        _require_aware(self.start_at, "activity application block start_at")
        _require_aware(self.end_at, "activity application block end_at")
        if (
            not self.block_id
            or self.start_at >= self.end_at
            or not self.bindings
            or len({binding.binding_id for binding in self.bindings}) != len(self.bindings)
        ):
            message = "activity application block requires identity, coverage, and bindings"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ActivityGateApplicationPlan:
    """Predeclared exact H3/H5, retained-input, block, and LL-04d/e identity."""

    definition_id: str
    campaign_definition_id: str
    environment_id: str
    scope_authority_ref: str
    parent_strategy_kind: ActivityGateParentKind
    parent_strategy_recipe: ActivityGateParentRecipe
    development_standard: ActivityGateDevelopmentStandard
    blocks: tuple[ActivityGateApplicationBlock, ...]

    def __post_init__(self) -> None:
        """Reject chronology, input reuse, or parent/candidate identity drift."""
        if (
            not self.definition_id
            or not self.campaign_definition_id
            or not self.environment_id
            or not self.scope_authority_ref
            or self.parent_strategy_kind not in ("LL03_POST_JUMP_REVERSAL", "LL05_DEPTH_IMBALANCE")
            or self.parent_strategy_recipe.parent_strategy_kind != self.parent_strategy_kind
            or self.development_standard != ll04e_primary_development_standard()
            or not self.blocks
            or len({block.block_id for block in self.blocks}) != len(self.blocks)
        ):
            message = "activity application plan requires exact scope and parent identity"
            raise ValueError(message)
        if any(previous.end_at > current.start_at for previous, current in pairwise(self.blocks)):
            message = "activity application blocks must be ordered and non-overlapping"
            raise ValueError(message)
        bindings = tuple(binding for block in self.blocks for binding in block.bindings)
        if len({binding.binding_id for binding in bindings}) != len(bindings):
            message = "activity application binding identities must be globally unique"
            raise ValueError(message)
        snapshot_refs = tuple(binding.snapshot_ref for binding in bindings)
        if len(set(snapshot_refs)) != len(snapshot_refs):
            message = "activity application snapshot references must be unique"
            raise ValueError(message)
        for block in self.blocks:
            market_keys = tuple(
                (
                    binding.parent_strategy_definition.reference_leg.venue,
                    binding.parent_strategy_definition.reference_leg.market_id,
                )
                for binding in block.bindings
            )
            if len(set(market_keys)) != len(market_keys):
                message = "activity application block contains a duplicate parent market"
                raise ValueError(message)
        if any(
            _parent_kind(binding.parent_strategy_definition) != self.parent_strategy_kind
            or activity_gate_parent_recipe(binding.parent_strategy_definition)
            != self.parent_strategy_recipe
            or binding.parent_strategy_definition.scope_authority_ref != self.scope_authority_ref
            for binding in bindings
        ):
            message = "activity application plan requires exact scope and parent identity"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class ActivityGateApplicationResult:
    """Immutable application evidence recomputed from exact plan-ordered snapshots."""

    plan: ActivityGateApplicationPlan
    snapshots: tuple[BookCorpusSnapshot, ...]
    campaign: ActivityGateCampaignResult
    assessment: ActivityGateDevelopmentAssessment

    def __post_init__(self) -> None:
        """Reject input order or outputs detached from exact retained snapshot bytes."""
        expected_campaign, expected_assessment = _compose_activity_gate_application(
            self.plan,
            self.snapshots,
        )
        if self.campaign != expected_campaign or self.assessment != expected_assessment:
            message = "activity application result is detached from its exact retained snapshots"
            raise ValueError(message)


def run_activity_gate_application(
    store: BookCorpusStore,
    plan: ActivityGateApplicationPlan,
) -> ActivityGateApplicationResult:
    """Load verified retained bytes and run the unchanged LL-04 chain read-only."""
    bindings = _ordered_bindings(plan)
    snapshots = tuple(store.load(binding.snapshot_ref) for binding in bindings)
    campaign, assessment = _compose_activity_gate_application(plan, snapshots)
    return ActivityGateApplicationResult(
        plan=plan,
        snapshots=snapshots,
        campaign=campaign,
        assessment=assessment,
    )


def _compose_activity_gate_application(
    plan: ActivityGateApplicationPlan,
    snapshots: tuple[BookCorpusSnapshot, ...],
) -> tuple[ActivityGateCampaignResult, ActivityGateDevelopmentAssessment]:
    bindings = _ordered_bindings(plan)
    if len(snapshots) != len(bindings):
        message = "activity application snapshot count differs from its exact plan"
        raise ValueError(message)
    snapshot_iterator = iter(snapshots)
    campaign_blocks: list[ActivityGateCampaignBlock] = []
    for block in plan.blocks:
        ablations: list[ActivityGateRivalAblation] = []
        for binding in block.bindings:
            snapshot = next(snapshot_iterator)
            _validate_snapshot_binding(plan, block, binding, snapshot)
            registration = register_book_corpus(snapshot)
            screen = _run_parent_screen(registration, binding.parent_strategy_definition)
            gate = derive_latency_scaled_activity_gate(
                binding.parent_strategy_definition,
                plan.development_standard.activity_policy,
            )
            activity = build_book_activity_series(
                snapshot,
                BookActivityDefinition(gate.recent_window),
            )
            comparison = compare_activity_participation_gate(screen, activity, gate)
            ablations.append(compare_activity_gate_rivals(comparison))
        campaign_blocks.append(
            ActivityGateCampaignBlock(
                block_id=block.block_id,
                start_at=block.start_at,
                end_at=block.end_at,
                ablations=tuple(ablations),
            )
        )
    standard = plan.development_standard
    policy = standard.activity_policy
    campaign_definition = ActivityGateCampaignDefinition(
        definition_id=plan.campaign_definition_id,
        parent_strategy_kind=plan.parent_strategy_kind,
        parent_strategy_recipe=plan.parent_strategy_recipe,
        scope_authority_ref=plan.scope_authority_ref,
        recent_window=_parent_action_delay(plan) * policy.recent_window_action_delay_multiplier,
        maximum_quiet_duration=(
            _parent_action_delay(plan) * policy.maximum_quiet_action_delay_multiplier
        ),
        minimum_recent_source_event_count=policy.minimum_recent_source_event_count,
        primary_contrast_kind=standard.required_primary_contrast_kind,
        primary_metric=standard.required_primary_metric,
    )
    campaign = evaluate_activity_gate_campaign(campaign_definition, tuple(campaign_blocks))
    assessment = assess_activity_gate_development_campaign(campaign, standard)
    return campaign, assessment


def _ordered_bindings(
    plan: ActivityGateApplicationPlan,
) -> tuple[ActivityGateSnapshotBinding, ...]:
    return tuple(binding for block in plan.blocks for binding in block.bindings)


def _validate_snapshot_binding(
    plan: ActivityGateApplicationPlan,
    block: ActivityGateApplicationBlock,
    binding: ActivityGateSnapshotBinding,
    snapshot: BookCorpusSnapshot,
) -> None:
    request = snapshot.corpus.request
    parent = binding.parent_strategy_definition
    expected_legs = tuple(sorted((parent.reference_leg, parent.complement_leg)))
    canonical_ref = BookCorpusStore.from_corpus(snapshot.corpus).ref
    if (
        snapshot.ref != binding.snapshot_ref
        or canonical_ref != snapshot.ref
        or request.environment_id != plan.environment_id
        or request.scope_authority_ref != plan.scope_authority_ref
        or request.start_at != block.start_at
        or request.end_at != block.end_at
        or request.legs != expected_legs
    ):
        message = "activity snapshot identity differs from its exact plan binding"
        raise ValueError(message)


def _run_parent_screen(
    registration: BookCorpusRegistration,
    definition: ActivityGateParentDefinition,
) -> ActivityGateParentScreen:
    if isinstance(definition, PostJumpReversalDefinition):
        return screen_book_post_jump_reversal(registration, definition)
    return screen_depth_imbalance_impulse(registration, definition)


def _parent_kind(definition: ActivityGateParentDefinition) -> ActivityGateParentKind:
    if isinstance(definition, PostJumpReversalDefinition):
        return "LL03_POST_JUMP_REVERSAL"
    return "LL05_DEPTH_IMBALANCE"


def _parent_action_delay(plan: ActivityGateApplicationPlan) -> timedelta:
    first_binding = plan.blocks[0].bindings[0]
    return first_binding.parent_strategy_definition.action_delay
