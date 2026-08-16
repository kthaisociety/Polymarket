"""Causal tests for the read-only operator projection."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from research_agent.operator_ui import ProjectionError, build_research_library

if TYPE_CHECKING:
    from pathlib import Path


def _write_receipt(root: Path, **overrides: object) -> Path:
    receipt: dict[str, object] = {
        "schema_version": 1,
        "research_question": "Can lagged capacity predict waiting-time performance?",
        "status": "EXPLORATORY",
        "scientific_authority": "NONE_EXPLORATORY_ONLY",
        "validated_question_memory_effect": "NONE",
        "source": {
            "publisher": "Official source",
            "api_version": "v1",
            "retrieved_at": "2026-08-16T13:58:30+02:00",
            "target_kpi": "target",
            "panel_response_sha256": "a" * 64,
        },
        "sample": {"regions": 2, "rows": 6, "target_years": [2021, 2022, 2023]},
        "harness": {
            "environment_ref": "environment@v1",
            "view_id": "authorized-view",
            "actions": [
                {
                    "actual_field_accesses": ["target", "lagged_capacity"],
                    "formal_object_refs": [],
                    "durable_state_effects": [],
                }
            ],
        },
        "results": {
            "selection": {
                "selected": "lagged_capacity",
                "test_year": 2023,
                "selected_test_mse": 20.0,
                "mean_baseline_test_mse": 15.0,
                "region_linear_trend_test_mse": 7.0,
                "region_persistence_test_mse": 3.0,
            },
            "independent_audit": {"verdict": "REJECT_PREDICTIVE_CLAIM"},
            "disposition": "RETAIN_NEGATIVE_EVIDENCE",
        },
        "mandatory_caveats": ["OBSERVATIONAL_ASSOCIATION_NOT_CAUSAL_EFFECT"],
    }
    receipt.update(overrides)
    path = root / "research" / "question-one" / "2026-08-16-receipt.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(receipt), encoding="utf-8")
    return path


def test_projection_preserves_exploratory_status_and_keeps_finalized_empty(tmp_path: Path) -> None:
    """Exploratory evidence must never enter the finalized collection."""
    _write_receipt(tmp_path)

    projection = build_research_library(tmp_path).as_dict()

    assert projection["counts"] == {"ongoing": 1, "finalized": 0}
    ongoing = projection["ongoing"]
    assert isinstance(ongoing, list)
    item = ongoing[0]
    assert isinstance(item, dict)
    assert item["status"] == "EXPLORATORY"
    assert item["scientific_authority"] == "NONE_EXPLORATORY_ONLY"
    assert item["validated_question_memory_effect"] == "NONE"
    assert projection["finalized"] == []
    empty = projection["finalized_empty_state"]
    assert isinstance(empty, dict)
    assert empty["is_scientific_record"] is False


@pytest.mark.parametrize(
    ("override", "match"),
    [
        ({"status": "VALIDATED"}, "Unsupported research status"),
        ({"scientific_authority": "CALLER_ASSERTED"}, "claims scientific authority"),
        ({"validated_question_memory_effect": "PUBLISHED"}, "validated memory effect"),
    ],
)
def test_projection_rejects_receipt_that_upgrades_its_own_authority(
    tmp_path: Path,
    override: dict[str, object],
    match: str,
) -> None:
    """Caller-authored authority upgrades must fail closed."""
    _write_receipt(tmp_path, **override)

    with pytest.raises(ProjectionError, match=match):
        build_research_library(tmp_path)


def test_projection_records_actual_accesses_and_exact_provenance(tmp_path: Path) -> None:
    """The presentation must use actual access and exact source provenance."""
    _write_receipt(tmp_path)

    projection = build_research_library(tmp_path).as_dict()
    ongoing = projection["ongoing"]
    assert isinstance(ongoing, list)
    item = ongoing[0]
    assert isinstance(item, dict)
    assert item["actual_field_accesses"] == ["lagged_capacity", "target"]
    provenance = item["provenance"]
    assert isinstance(provenance, dict)
    assert provenance["panel_response_sha256"] == "a" * 64
    assert provenance["receipt_path"] == ("research/question-one/2026-08-16-receipt.json")
