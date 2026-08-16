"""Deterministic identity helpers for protected-evaluation records."""

from __future__ import annotations

import hashlib
import json

IdentityValue = str | tuple[str, ...]
IdentityFields = tuple[tuple[str, IdentityValue], ...]


def scientific_identity(kind: str, fields: IdentityFields) -> str:
    """Return an exact content identity for a tuple of semantic fields."""
    canonical = json.dumps(fields, ensure_ascii=True, separators=(",", ":"))
    return f"{kind}:{hashlib.sha256(canonical.encode()).hexdigest()}"


def require_text(value: str, name: str) -> None:
    """Reject missing identity dimensions at formal boundaries."""
    if not value.strip():
        msg = f"{name} must be non-empty"
        raise ValueError(msg)


def require_refs(values: tuple[str, ...], name: str) -> None:
    """Reject empty or malformed reference collections."""
    if not values or any(not value.strip() for value in values):
        msg = f"{name} must contain non-empty references"
        raise ValueError(msg)
