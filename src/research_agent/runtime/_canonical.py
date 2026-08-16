"""Canonical immutable values and content identities for runtime records."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass
from enum import Enum
from hashlib import sha256
from types import MappingProxyType
from typing import cast


def freeze_value(value: object) -> object:
    """Recursively detach JSON-like content from caller-owned mutable objects."""
    if isinstance(value, Mapping):
        mapping = cast("Mapping[object, object]", value)
        if not all(isinstance(key, str) for key in mapping):
            msg = "Canonical runtime mappings require string keys."
            raise TypeError(msg)
        frozen = {cast("str", key): freeze_value(item) for key, item in mapping.items()}
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        sequence = cast("Sequence[object]", value)
        return tuple(freeze_value(item) for item in sequence)
    if isinstance(value, (set, frozenset)):
        items = cast("set[object] | frozenset[object]", value)
        return tuple(sorted((freeze_value(item) for item in items), key=repr))
    return value


def canonical_value(value: object) -> object:
    """Convert supported immutable runtime content to deterministic JSON data."""
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: canonical_value(getattr(value, field.name))
            for field in fields(value)
            if field.name not in {"content_digest", "checkpoint_id"}
        }
    if isinstance(value, Mapping):
        mapping = cast("Mapping[object, object]", value)
        if not all(isinstance(key, str) for key in mapping):
            msg = "Canonical runtime mappings require string keys."
            raise TypeError(msg)
        return {
            cast("str", key): canonical_value(item)
            for key, item in sorted(mapping.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        sequence = cast("Sequence[object]", value)
        return [canonical_value(item) for item in sequence]
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    msg = f"Unsupported canonical runtime value: {type(value).__name__}."
    raise TypeError(msg)


def canonical_bytes(value: object) -> bytes:
    """Serialize supported content deterministically."""
    return json.dumps(
        canonical_value(value),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


def content_digest(value: object) -> str:
    """Return a deterministic SHA-256 identity for semantic content."""
    return sha256(canonical_bytes(value)).hexdigest()


def freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    """Freeze a typed string-keyed mapping recursively."""
    return cast("Mapping[str, object]", freeze_value(value))


__all__ = ["canonical_bytes", "canonical_value", "content_digest", "freeze_mapping", "freeze_value"]
