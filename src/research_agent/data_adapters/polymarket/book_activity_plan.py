"""Immutable local precommit receipts for exact LL-04f application plans."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Final, cast

from research_agent.data_adapters.polymarket.book_activity_application import (
    ActivityGateApplicationPlan,
    ActivityGateApplicationResult,
    run_activity_gate_application,
)

if TYPE_CHECKING:
    from pathlib import Path

    from research_agent.data_adapters.polymarket.book_corpus import BookCorpusStore

_PLAN_SCHEMA: Final[str] = "polymarket-activity-application-plan/v1"
_SHA256_LENGTH: Final[int] = 64
_MICROSECONDS_PER_SECOND: Final[int] = 1_000_000
_SECONDS_PER_DAY: Final[int] = 86_400


@dataclass(frozen=True, slots=True)
class ActivityGateApplicationPlanRef:
    """Path-independent identity of one exact canonical LL-04f plan."""

    content_sha256: str
    size_bytes: int

    def __post_init__(self) -> None:
        """Reject malformed content identity before resolving a local path."""
        invalid_digest = len(self.content_sha256) != _SHA256_LENGTH or any(
            character not in "0123456789abcdef" for character in self.content_sha256
        )
        if invalid_digest or self.size_bytes <= 0:
            message = "activity application plan reference requires SHA-256 and positive size"
            raise ValueError(message)

    @property
    def uri(self) -> str:
        """Return the stable sanitized provenance reference."""
        return f"polymarket-activity-application-plan:{self.content_sha256}"


@dataclass(frozen=True, slots=True)
class ActivityGateApplicationPlanRetention:
    """Sanitized receipt for one immutable locally retained application plan."""

    ref: ActivityGateApplicationPlanRef


class ActivityGateApplicationPlanStore:
    """Content-addressed local store for canonical LL-04f plan bytes."""

    root: Final[Path]

    def __init__(self, root: Path) -> None:
        """Bind an operator-selected root without adding it to plan identity."""
        self.root = root.absolute()

    @staticmethod
    def from_plan(plan: ActivityGateApplicationPlan) -> ActivityGateApplicationPlanRef:
        """Derive deterministic path-independent identity from the complete plan."""
        content = _canonical_plan_bytes(plan)
        return ActivityGateApplicationPlanRef(
            content_sha256=hashlib.sha256(content).hexdigest(),
            size_bytes=len(content),
        )

    def retain(self, plan: ActivityGateApplicationPlan) -> ActivityGateApplicationPlanRetention:
        """Publish canonical plan bytes once and verify exact persistence.

        Args:
            plan: Complete valid LL-04f application plan to retain.

        Returns:
            Sanitized content-addressed retention receipt.

        Raises:
            ValueError: If existing bytes conflict or retained bytes fail verification.

        """
        content = _canonical_plan_bytes(plan)
        ref = self.from_plan(plan)
        path = self.object_path(ref)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            if path.read_bytes() != content:
                message = "retained activity application plan identity conflicts with changed bytes"
                raise ValueError(message) from None
        else:
            with os.fdopen(descriptor, "wb") as output:
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
        if not self.verify(ref):
            message = "retained activity application plan failed content verification"
            raise ValueError(message)
        return ActivityGateApplicationPlanRetention(ref)

    def verify(self, ref: ActivityGateApplicationPlanRef) -> bool:
        """Check exact retained byte size and SHA-256 identity."""
        try:
            content = self.object_path(ref).read_bytes()
        except OSError:
            return False
        return (
            len(content) == ref.size_bytes
            and hashlib.sha256(content).hexdigest() == ref.content_sha256
        )

    def require(
        self,
        plan: ActivityGateApplicationPlan,
        ref: ActivityGateApplicationPlanRef,
    ) -> ActivityGateApplicationPlanRef:
        """Verify retained bytes and require the caller plan to have exact identity.

        Args:
            plan: Executable LL-04f plan supplied for the later application.
            ref: Previously retained content-addressed plan identity.

        Returns:
            The exact verified reference.

        Raises:
            ValueError: If the object is unhealthy or the supplied plan differs.

        """
        if not self.verify(ref):
            message = "cannot use an unverified activity application plan"
            raise ValueError(message)
        if self.from_plan(plan) != ref:
            message = "activity application plan does not match its retained reference"
            raise ValueError(message)
        return ref

    def object_path(self, ref: ActivityGateApplicationPlanRef) -> Path:
        """Return local object path without making it scientific identity."""
        digest = ref.content_sha256
        return self.root / "objects" / digest[:2] / f"{digest}.json"


def run_precommitted_activity_gate_application(
    corpus_store: BookCorpusStore,
    plan_store: ActivityGateApplicationPlanStore,
    plan_ref: ActivityGateApplicationPlanRef,
    plan: ActivityGateApplicationPlan,
) -> ActivityGateApplicationResult:
    """Verify the retained plan before allowing LL-04f to load corpus values."""
    plan_store.require(plan, plan_ref)
    return run_activity_gate_application(corpus_store, plan)


def _canonical_plan_bytes(plan: ActivityGateApplicationPlan) -> bytes:
    parent_types = [
        type(binding.parent_strategy_definition).__name__
        for block in plan.blocks
        for binding in block.bindings
    ]
    payload = {
        "schema_version": _PLAN_SCHEMA,
        "binding_parent_types": parent_types,
        "plan": _canonical_value(asdict(plan)),
    }
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


def _canonical_value(value: object) -> object:
    if isinstance(value, Mapping):
        mapping = cast("Mapping[object, object]", value)
        if any(not isinstance(key, str) for key in mapping):
            message = "activity application plan mappings require string keys"
            raise TypeError(message)
        return {
            cast("str", key): _canonical_value(item)
            for key, item in sorted(mapping.items(), key=lambda pair: cast("str", pair[0]))
        }
    if isinstance(value, list | tuple):
        return [_canonical_value(item) for item in cast("Sequence[object]", value)]
    if isinstance(value, Decimal):
        normalized = value.normalize()
        return {"decimal": "0" if normalized == 0 else format(normalized, "f")}
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            message = "activity application plan datetime must be timezone-aware"
            raise ValueError(message)
        return {"datetime_utc": value.astimezone(UTC).isoformat().replace("+00:00", "Z")}
    if isinstance(value, timedelta):
        microseconds = (
            value.days * _SECONDS_PER_DAY + value.seconds
        ) * _MICROSECONDS_PER_SECOND + value.microseconds
        return {"duration_microseconds": microseconds}
    if value is None or isinstance(value, str | int | bool):
        return value
    message = f"unsupported activity application plan value: {type(value).__name__}"
    raise TypeError(message)
