"""Deterministic identities for immutable scientific data objects."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, cast


def _json_default(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, timedelta):
        return value.total_seconds()
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(cast("Any", value))
    msg = f"cannot construct scientific identity from {type(value).__name__}"
    raise TypeError(msg)


def stable_identity(kind: str, payload: Any) -> str:  # noqa: ANN401
    """Return a content identity independent of process and physical storage."""
    canonical = json.dumps(
        payload,
        default=_json_default,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    return f"{kind}:{digest}"


def require_aware(moment: datetime, name: str) -> None:
    """Reject ambiguous naive timestamps at the scientific boundary."""
    if moment.tzinfo is None or moment.utcoffset() is None:
        msg = f"{name} must be timezone-aware"
        raise ValueError(msg)
