"""Parent-latency-scaled fixed activity policy for LL-04d."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from research_agent.data_adapters.polymarket.book_activity_campaign import (
    activity_gate_parent_recipe,
)
from research_agent.data_adapters.polymarket.book_activity_gate import (
    ActivityGateParentDefinition,
    ActivityGateParentKind,
    ActivityParticipationGateDefinition,
)
from research_agent.data_adapters.polymarket.low_latency import PostJumpReversalDefinition


@dataclass(frozen=True, slots=True)
class ActivityGateLatencyScaledPolicy:
    """Dimensionless activity thresholds relative to a parent's declared action delay."""

    definition_id: str
    recent_window_action_delay_multiplier: int
    maximum_quiet_action_delay_multiplier: int
    minimum_recent_source_event_count: int

    def __post_init__(self) -> None:
        """Reject missing identity or incoherent dimensionless activity thresholds."""
        if (
            not self.definition_id
            or self.recent_window_action_delay_multiplier <= 0
            or self.maximum_quiet_action_delay_multiplier <= 0
            or self.maximum_quiet_action_delay_multiplier
            > self.recent_window_action_delay_multiplier
            or self.minimum_recent_source_event_count <= 0
        ):
            message = "latency-scaled activity policy requires exact positive threshold identity"
            raise ValueError(message)


def ll04d_latency_scaled_primary_policy() -> ActivityGateLatencyScaledPolicy:
    """Return the single predeclared LL-04d primary candidate without fitted state."""
    return ActivityGateLatencyScaledPolicy(
        definition_id="ll04d-latency-scaled-primary-v1",
        recent_window_action_delay_multiplier=5,
        maximum_quiet_action_delay_multiplier=1,
        minimum_recent_source_event_count=2,
    )


def derive_latency_scaled_activity_gate(
    parent: ActivityGateParentDefinition,
    policy: ActivityGateLatencyScaledPolicy,
) -> ActivityParticipationGateDefinition:
    """Bind one explicit dimensionless policy to an exact H3 or H5 parent definition."""
    parent_kind, action_delay = _parent_kind_and_action_delay(parent)
    if action_delay <= timedelta(0):
        message = "latency-scaled activity policy requires a positive parent action delay"
        raise ValueError(message)
    recent_window = action_delay * policy.recent_window_action_delay_multiplier
    maximum_quiet_duration = action_delay * policy.maximum_quiet_action_delay_multiplier
    return ActivityParticipationGateDefinition(
        definition_id=(
            f"{policy.definition_id}:{parent_kind}:{parent.definition_id}:"
            f"{_parent_definition_sha256(parent)}"
        ),
        parent_strategy_kind=parent_kind,
        parent_strategy_definition_id=parent.definition_id,
        scope_authority_ref=parent.scope_authority_ref,
        reference_leg=parent.reference_leg,
        recent_window=recent_window,
        maximum_quiet_duration=maximum_quiet_duration,
        minimum_recent_source_event_count=policy.minimum_recent_source_event_count,
    )


def _parent_kind_and_action_delay(
    parent: ActivityGateParentDefinition,
) -> tuple[ActivityGateParentKind, timedelta]:
    if isinstance(parent, PostJumpReversalDefinition):
        return "LL03_POST_JUMP_REVERSAL", parent.action_delay
    return "LL05_DEPTH_IMBALANCE", parent.action_delay


def _parent_definition_sha256(parent: ActivityGateParentDefinition) -> str:
    recipe = activity_gate_parent_recipe(parent)
    payload = {
        "complement_leg": _leg_identity(parent.complement_leg),
        "definition_id": parent.definition_id,
        "kind": recipe.parent_strategy_kind,
        "parameters": [[name, _canonical_recipe_value(value)] for name, value in recipe.parameters],
        "reference_leg": _leg_identity(parent.reference_leg),
        "scope_authority_ref": parent.scope_authority_ref,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def _leg_identity(leg: object) -> list[str | int]:
    venue = getattr(leg, "venue", None)
    market_id = getattr(leg, "market_id", None)
    outcome_index = getattr(leg, "outcome_index", None)
    if (
        not isinstance(venue, str)
        or not isinstance(market_id, str)
        or not isinstance(outcome_index, int)
    ):
        message = "latency-scaled activity policy parent leg identity is invalid"
        raise TypeError(message)
    return [venue, market_id, outcome_index]


def _canonical_recipe_value(value: Decimal | timedelta | int | None) -> str | int | None:
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    if isinstance(value, timedelta):
        return (value.days * 86_400 + value.seconds) * 1_000_000 + value.microseconds
    return value
