"""Regression tests for the authored cross-venue source-time lead-lag scout."""

from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol, cast

import pytest

_STUDY_PATH = (
    Path(__file__).parents[3]
    / "studies"
    / "polymarket-active-external-data-2026-08-18"
    / "brazil_cross_venue_fill_lead_lag.py"
)
_PM = "0xdf8e2dc5860027decbe6164555c3c1c9645c3bd33e16b9dc57ca87125047d4a8"
_KALSHI = "KXBRPRES-26-LULA"
_START = datetime(2026, 1, 1, tzinfo=UTC)
_MISSING_SIDE_TRIGGER_COUNT = 2


class _Study(Protocol):
    def analyze_rows(self, header: object, rows: tuple[object, ...]) -> dict[str, object]: ...

    def validate_audit(self, raw: object) -> None: ...


def _load_study() -> _Study:
    spec = importlib.util.spec_from_file_location("_cross_venue_lead_lag_study", _STUDY_PATH)
    if spec is None or spec.loader is None:
        message = "could not load authored lead-lag study"
        raise RuntimeError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast("_Study", module)


def _header() -> dict[str, object]:
    return {
        "kind": "header",
        "schema": "chronos-brazil-cross-venue-taker-fills/v1",
        "environment_id": "test",
        "outcome_index": 0,
        "start": _START.isoformat(),
        "end": (_START + timedelta(days=1)).isoformat(),
        "kalshi_market_ids": ["KXBRPRES-26-LULA", "KXBRPRES-26-FBOL"],
        "polymarket_market_ids": [
            _PM,
            "0x1a01bf78f56a507fcb666d564d8c8b91b0750679163ed6e96746102c9b7d285d",
        ],
        "row_semantics": {"side": "aggressor's YES-outcome side"},
    }


def _fill(  # noqa: PLR0913, PLR0917
    venue: str,
    market_id: str,
    seconds: int,
    side: str,
    price: str,
    sequence: int,
) -> dict[str, object]:
    return {
        "kind": "fill",
        "venue": venue,
        "market_id": market_id,
        "fill_time": (_START + timedelta(seconds=seconds)).isoformat(),
        "fill_uid": f"{venue}-{sequence}",
        "outcome_index": 0,
        "side": side,
        "price": price,
        "size": "10",
    }


def _overall(result: dict[str, object], horizon: int = 30) -> dict[str, object]:
    rows = cast("list[dict[str, object]]", result["primary_overall"])
    return next(
        row for row in rows if row["source_venue"] == "kalshi" and row["horizon_seconds"] == horizon
    )


def test_same_aggressor_path_does_not_turn_a_side_switch_into_response() -> None:
    """The primary response stays zero when only the target aggressor side changes."""
    study = _load_study()
    rows = (
        _fill("kalshi", _KALSHI, 0, "BUY", "0.50", 1),
        _fill("polymarket", _PM, 5, "BUY", "0.40", 2),
        _fill("polymarket", _PM, 9, "SELL", "0.60", 3),
        _fill("kalshi", _KALSHI, 10, "BUY", "0.52", 4),
        _fill("polymarket", _PM, 20, "BUY", "0.40", 5),
    )

    result = study.analyze_rows(_header(), rows)
    summary = _overall(result)

    assert result["trigger_count"] == 1
    assert summary["post_same_side_mean_aligned_change"] == 0.0
    assert summary["post_any_side_mean_aligned_change"] == pytest.approx(-0.20)


def test_future_target_print_cannot_become_the_pre_trigger_baseline() -> None:
    """The strict baseline precedes the trigger even when a closer print follows it."""
    study = _load_study()
    rows = (
        _fill("kalshi", _KALSHI, 0, "BUY", "0.50", 1),
        _fill("polymarket", _PM, 5, "BUY", "0.40", 2),
        _fill("kalshi", _KALSHI, 10, "BUY", "0.52", 3),
        _fill("polymarket", _PM, 11, "BUY", "0.90", 4),
        _fill("polymarket", _PM, 20, "BUY", "0.90", 5),
    )

    result = study.analyze_rows(_header(), rows)

    assert _overall(result)["post_same_side_mean_aligned_change"] == pytest.approx(0.50)


def test_missing_response_is_excluded_and_fragmented_triggers_obey_cooldown() -> None:
    """No target update remains missing and nearby source innovations do not multiply trials."""
    study = _load_study()
    rows = (
        _fill("polymarket", _PM, 1, "BUY", "0.40", 1),
        _fill("kalshi", _KALSHI, 2, "BUY", "0.50", 2),
        _fill("kalshi", _KALSHI, 10, "BUY", "0.52", 3),
        _fill("kalshi", _KALSHI, 20, "BUY", "0.54", 4),
    )

    first = study.analyze_rows(_header(), rows)
    second = study.analyze_rows(_header(), rows)
    summary = _overall(first)

    assert first == second
    assert first["trigger_count"] == 1
    assert summary["post_same_side_count"] == 0
    assert summary["post_same_side_mean_aligned_change"] is None


def test_semantic_audit_rejects_reversed_or_changed_authority() -> None:
    """The study cannot grant itself a different cross-venue payout direction."""
    study = _load_study()
    invalid = {
        "schema": "chronos-brazil-cross-venue-semantic-audit/v1",
        "pairs": [
            {
                "candidate": candidate,
                "kalshi_market_id": kalshi_id,
                "polymarket_market_id": polymarket_id,
                "conservative_dominance_pair": "buy Kalshi NO plus buy Polymarket YES",
                "minimum_combined_payout_under_documented_outcomes": 1.0,
            }
            for candidate, kalshi_id, polymarket_id in (
                ("lula", "KXBRPRES-26-LULA", _PM),
                (
                    "flavio",
                    "KXBRPRES-26-FBOL",
                    "0x1a01bf78f56a507fcb666d564d8c8b91b0750679163ed6e96746102c9b7d285d",
                ),
            )
        ],
    }

    with pytest.raises(ValueError, match="authorized payout direction"):
        study.validate_audit(invalid)


def test_missing_kalshi_sell_path_excludes_polymarket_sell_trigger() -> None:
    """An omitted outcome leg is missing population, not a zero matched response."""
    study = _load_study()
    rows = (
        _fill("polymarket", _PM, 0, "SELL", "0.50", 1),
        _fill("kalshi", _KALSHI, 5, "BUY", "0.40", 2),
        _fill("polymarket", _PM, 10, "SELL", "0.52", 3),
        _fill("kalshi", _KALSHI, 20, "BUY", "0.42", 4),
    )

    result = study.analyze_rows(_header(), rows)

    assert result["raw_trigger_count"] == _MISSING_SIDE_TRIGGER_COUNT
    assert result["trigger_count"] == 0
    assert result["excluded_missing_matched_side_trigger_count"] == _MISSING_SIDE_TRIGGER_COUNT
