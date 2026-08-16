"""Fail-closed, read-only projections for the operator research library."""

# ruff: noqa: EM101, EM102, TRY003

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, cast

if TYPE_CHECKING:
    from pathlib import Path

type JsonValue = bool | int | float | str | list[JsonValue] | dict[str, JsonValue] | None
type JsonObject = dict[str, JsonValue]

_MAX_RECEIPT_BYTES: Final = 1_000_000
_MAX_RECEIPTS: Final = 100
_EXPLORATORY_STATUS: Final = "EXPLORATORY"
_NO_SCIENTIFIC_AUTHORITY: Final = "NONE_EXPLORATORY_ONLY"


class ProjectionError(ValueError):
    """Raised when a source record cannot be projected without changing its meaning."""


@dataclass(frozen=True, slots=True)
class ResearchLibraryProjection:
    """JSON-ready research library assembled without scientific write authority."""

    ongoing: tuple[JsonObject, ...]
    finalized: tuple[JsonObject, ...]
    finalized_empty_state: JsonObject

    def as_dict(self) -> JsonObject:
        """Return a detached JSON representation."""
        return {
            "schema_version": 1,
            "library_kind": "READ_ONLY_RESEARCH_PROJECTION",
            "counts": {
                "ongoing": len(self.ongoing),
                "finalized": len(self.finalized),
            },
            "ongoing": [_copy_json(item) for item in self.ongoing],
            "finalized": [_copy_json(item) for item in self.finalized],
            "finalized_empty_state": _copy_json(self.finalized_empty_state),
        }


def build_research_library(repository_root: Path) -> ResearchLibraryProjection:
    """Project exact exploratory receipts; never infer finalized scientific authority."""
    root = repository_root.resolve()
    research_root = root / "research"
    receipts = sorted(research_root.glob("*/*-receipt.json")) if research_root.is_dir() else []
    if len(receipts) > _MAX_RECEIPTS:
        message = f"Research library exceeds the {_MAX_RECEIPTS}-receipt safety bound."
        raise ProjectionError(message)

    ongoing = tuple(_project_exploratory_receipt(path, research_root) for path in receipts)
    return ResearchLibraryProjection(
        ongoing=ongoing,
        finalized=(),
        finalized_empty_state={
            "status": "NO_VALIDATED_FINDINGS",
            "eyebrow": "FINALIZED RESEARCH",
            "title": "No independently validated research report has been published yet.",
            "explanation": (
                "This view only admits canonical reports backed by an independently validated "
                "finding. Exploratory receipts and synthetic workflow demonstrations are excluded."
            ),
            "required_sections": [
                "Executive conclusion",
                "Key evidence",
                "Method and temporal design",
                "Robustness and failed alternatives",
                "Limitations and caveats",
                "Canonical provenance",
            ],
            "scientific_authority": "NONE_EMPTY_STATE",
            "is_scientific_record": False,
        },
    )


def _project_exploratory_receipt(path: Path, research_root: Path) -> JsonObject:
    resolved = path.resolve()
    if not resolved.is_relative_to(research_root.resolve()):
        raise ProjectionError("Research receipt resolves outside the research directory.")
    try:
        size = resolved.stat().st_size
    except OSError as error:
        raise ProjectionError(f"Cannot inspect research receipt: {path.name}") from error
    if size > _MAX_RECEIPT_BYTES:
        raise ProjectionError(f"Research receipt exceeds safety bound: {path.name}")

    try:
        raw = cast("JsonValue", json.loads(resolved.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProjectionError(f"Cannot parse research receipt: {path.name}") from error
    receipt = _object(raw, "receipt")
    status = _text(receipt, "status")
    authority = _text(receipt, "scientific_authority")
    memory_effect = _text(receipt, "validated_question_memory_effect")
    if status != _EXPLORATORY_STATUS:
        raise ProjectionError(f"Unsupported research status in {path.name}: {status}")
    if authority != _NO_SCIENTIFIC_AUTHORITY:
        raise ProjectionError(f"Exploratory receipt claims scientific authority: {path.name}")
    if memory_effect != "NONE":
        raise ProjectionError(f"Exploratory receipt claims validated memory effect: {path.name}")

    source = _object(receipt.get("source"), "source")
    sample = _object(receipt.get("sample"), "sample")
    results = _object(receipt.get("results"), "results")
    selection = _object(results.get("selection"), "results.selection")
    audit = _object(results.get("independent_audit"), "results.independent_audit")
    harness = _object(receipt.get("harness"), "harness")
    actions = _objects(harness.get("actions"), "harness.actions")

    benchmarks = [
        _benchmark("Selected candidate", selection, "selected_test_mse", "candidate"),
        _benchmark("Training-mean baseline", selection, "mean_baseline_test_mse", "baseline"),
        _benchmark(
            "Regional linear trend",
            selection,
            "region_linear_trend_test_mse",
            "baseline",
        ),
        _benchmark(
            "Previous-year persistence",
            selection,
            "region_persistence_test_mse",
            "strongest_baseline",
        ),
    ]
    actual_accesses = sorted(
        {
            access
            for action in actions
            for access in _texts(action.get("actual_field_accesses"), "actual_field_accesses")
        }
    )
    caveats = _texts(receipt.get("mandatory_caveats"), "mandatory_caveats")
    question = _text(receipt, "research_question")
    folder = path.parent.name
    return cast(
        "JsonObject",
        {
            "id": f"ongoing:{folder}:{path.stem}",
            "record_kind": "EXPLORATORY_RESEARCH_RECEIPT",
            "title": "Swedish healthcare waiting queues",
            "question": question,
            "status": status,
            "scientific_authority": authority,
            "validated_question_memory_effect": memory_effect,
            "updated_at": _text(source, "retrieved_at"),
            "source_label": f"{_text(source, 'publisher')} {_text(source, 'api_version')}",
            "current_conclusion": (
                "The tested lagged capacity, staffing, demand, utilization, and cost variables did "
                "not improve the untouched 2023 prediction over previous-year regional waiting "
                "performance. The candidate is rejected and the question remains open."
            ),
            "disposition": _text(results, "disposition"),
            "audit_verdict": _text(audit, "verdict"),
            "sample": {
                "regions": _integer(sample, "regions"),
                "rows": _integer(sample, "rows"),
                "target_years": _numbers(sample.get("target_years"), "sample.target_years"),
                "test_year": _integer(selection, "test_year"),
            },
            "selected_candidate": _text(selection, "selected"),
            "benchmarks": benchmarks,
            "method_steps": [
                "Pin exact source responses and metadata by SHA-256.",
                "Align each region's predictors to the following year's waiting-time outcome.",
                "Select one of eight univariate candidates using 2021-2022 only.",
                "Evaluate once on untouched 2023 and compare with strong regional baselines.",
                "Audit within-region direction, first differences, multiplicity, and missingness.",
            ],
            "next_step": (
                "Freeze a genuinely new hypothesis, then wait for a later release or obtain a "
                "separately protected specialty-level panel with historical release timestamps."
            ),
            "caveats": caveats,
            "actual_field_accesses": actual_accesses,
            "harness_action_count": len(actions),
            "provenance": {
                "publisher": _text(source, "publisher"),
                "api_version": _text(source, "api_version"),
                "retrieved_at": _text(source, "retrieved_at"),
                "target_kpi": _text(source, "target_kpi"),
                "panel_response_sha256": _text(source, "panel_response_sha256"),
                "environment_ref": _text(harness, "environment_ref"),
                "view_id": _text(harness, "view_id"),
                "receipt_path": str(resolved.relative_to(root_from_research(research_root))),
            },
        },
    )


def root_from_research(research_root: Path) -> Path:
    """Return the repository root for a canonical `<root>/research` directory."""
    return research_root.parent.resolve()


def _benchmark(label: str, source: JsonObject, key: str, role: str) -> JsonObject:
    return {"label": label, "mse": _number(source, key), "role": role}


def _copy_json(value: JsonValue) -> JsonValue:
    if isinstance(value, dict):
        return {key: _copy_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy_json(item) for item in value]
    return value


def _object(value: JsonValue, label: str) -> JsonObject:
    if not isinstance(value, dict):
        raise ProjectionError(f"{label} must be a JSON object.")
    return value


def _objects(value: JsonValue, label: str) -> list[JsonObject]:
    if not isinstance(value, list):
        raise ProjectionError(f"{label} must be a JSON array.")
    return [_object(item, label) for item in value]


def _text(source: JsonObject, key: str) -> str:
    value = source.get(key)
    if not isinstance(value, str) or not value:
        raise ProjectionError(f"{key} must be a non-empty string.")
    return value


def _texts(value: JsonValue, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ProjectionError(f"{label} must be a string array.")
    return cast("list[str]", value)


def _number(source: JsonObject, key: str) -> float:
    value = source.get(key)
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ProjectionError(f"{key} must be numeric.")
    return float(value)


def _integer(source: JsonObject, key: str) -> int:
    value = source.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ProjectionError(f"{key} must be an integer.")
    return value


def _numbers(value: JsonValue, label: str) -> list[int | float]:
    if not isinstance(value, list):
        raise ProjectionError(f"{label} must be a numeric array.")
    if not all(isinstance(item, int | float) and not isinstance(item, bool) for item in value):
        raise ProjectionError(f"{label} must be a numeric array.")
    return cast("list[int | float]", value)


__all__ = [
    "ProjectionError",
    "ResearchLibraryProjection",
    "build_research_library",
]
