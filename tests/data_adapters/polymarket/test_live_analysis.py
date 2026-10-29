"""Registration-to-sandbox integration tests for live Polymarket exploration."""

# ruff: noqa: SLF001
# pyright: reportPrivateUsage=false

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from research_agent.data_adapters.polymarket import (
    PolymarketAnalysisRequest,
    PolymarketBlockVintage,
    PolymarketContractRecord,
    PolymarketFillRecord,
    PolymarketImportRequest,
    PolymarketIngestionResult,
    PolymarketOutcomeRecord,
    analyze_registered_polymarket_tape,
    ingest_polymarket_contract_tape,
    live_analysis,
)
from research_agent.exploration import AnalysisStatus

MARKET = "0xmarket"
ORIGIN = datetime(2026, 1, 1, tzinfo=UTC)
VIEW_FIELDS = ("trade_price", "reference_time", "fill_uid")
OUTCOME_ASSET_ID = "yes-asset"
EXPECTED_LEGAL_OBSERVATIONS = 4
BLOCKED_EXIT = 2


class _Reader:
    async def read_vintage(self) -> PolymarketBlockVintage:
        return PolymarketBlockVintage(100, 200, "history", "forward")

    async def read_contracts(
        self, market_ids: tuple[str, ...]
    ) -> tuple[PolymarketContractRecord, ...]:
        assert market_ids == (MARKET,)
        return (
            PolymarketContractRecord(
                market_id=MARKET,
                outcome_count=2,
                outcomes=(
                    PolymarketOutcomeRecord(0, OUTCOME_ASSET_ID, None),
                    PolymarketOutcomeRecord(1, "no-token", None),
                ),
                close_time=ORIGIN + timedelta(days=30),
                resolved=False,
            ),
        )

    async def read_fills(self, market_id: str) -> tuple[PolymarketFillRecord, ...]:
        assert market_id == MARKET
        return (
            _fill("first", minute=1, price="0.40", block=110),
            _fill("future", minute=2, price="0.99", block=120),
        )


def _fill(uid: str, *, minute: int, price: str, block: int) -> PolymarketFillRecord:
    return PolymarketFillRecord(
        fill_uid=uid,
        fill_time=ORIGIN + timedelta(minutes=minute),
        market_id=MARKET,
        outcome_index=0,
        outcome_token=OUTCOME_ASSET_ID,
        side="BUY",
        price=Decimal(price),
        size=Decimal(10),
        block_number=block,
        transaction_hash=f"0xtx-{uid}",
    )


def _registered() -> PolymarketIngestionResult:
    return asyncio.run(
        ingest_polymarket_contract_tape(
            _Reader(), PolymarketImportRequest((MARKET,), "test-production-readonly")
        )
    )


def test_registered_tape_enters_sandbox_only_through_legal_information_set() -> None:
    """A post-decision fill cannot enter the authorized exploratory view."""
    source = """
prices = read("polymarket-development-view", "trade_price")
times = read("polymarket-development-view", "reference_time")
fills = read("polymarket-development-view", "fill_uid")
result = structured_return(
    "inspected the legal registered tape",
    {
        "row_count": len(prices),
        "fill_ids": sorted(set(fills)),
        "prices": list(prices),
        "first_time": min(times),
        "last_time": max(times),
    },
)
"""
    registered = _registered()

    result = analyze_registered_polymarket_tape(
        registered,
        PolymarketAnalysisRequest(
            decision_time=ORIGIN + timedelta(minutes=1, seconds=30),
            source=source,
            requested_view_fields=VIEW_FIELDS,
            session_id="session-live-analysis",
            action_id="analysis-live-tape",
        ),
    )

    assert result.information_set.decision_time == ORIGIN + timedelta(minutes=1, seconds=30)
    assert len(result.information_set.observations) == EXPECTED_LEGAL_OBSERVATIONS
    assert result.observation.status is AnalysisStatus.SUCCEEDED
    assert result.observation.details == {
        "row_count": 1,
        "fill_ids": ["first"],
        "prices": [0.4],
        "first_time": "2026-01-01T00:01:00+00:00",
        "last_time": "2026-01-01T00:01:00+00:00",
    }
    assert result.observation.provenance.dataset_refs == (registered.registered.registration_id,)
    assert result.observation.provenance.environment_refs == (registered.catalog.identity,)
    assert result.observation.provenance.code_sha256 == hashlib.sha256(source.encode()).hexdigest()
    assert (
        tuple(access.field_id for access in result.observation.provenance.accesses) == VIEW_FIELDS
    )
    assert result.observation.epistemic_status == "EXPLORATORY"
    assert result.observation.formal_object_refs == ()
    assert result.observation.durable_state_effects == ()


def test_unknown_view_field_fails_before_sandbox_execution() -> None:
    """A caller cannot widen the registered observation view with an invented field."""
    with pytest.raises(ValueError, match="unknown Polymarket exploratory view field"):
        analyze_registered_polymarket_tape(
            _registered(),
            PolymarketAnalysisRequest(
                decision_time=ORIGIN + timedelta(minutes=3),
                source='result = structured_return("must not run", {})',
                requested_view_fields=("secret",),
                session_id="session-live-analysis",
                action_id="analysis-live-tape",
            ),
        )


def test_externalized_analysis_result_persists_exact_drill_down_artifact(
    tmp_path: Path,
) -> None:
    """A result above the inline limit remains readable after the command exits."""
    result = analyze_registered_polymarket_tape(
        _registered(),
        PolymarketAnalysisRequest(
            decision_time=ORIGIN + timedelta(minutes=3),
            source=('result = structured_return("large result", {"values": list(range(1000))})'),
            requested_view_fields=("trade_price",),
            session_id="session-artifact",
            action_id="analysis-artifact",
        ),
    )

    persisted = live_analysis._persist_artifacts(
        result,
        session_id="session-artifact",
        directory=tmp_path,
    )

    assert result.observation.details is None
    assert len(persisted) == 1
    path = Path(str(persisted[0]["path"]))
    content = path.read_bytes()
    assert hashlib.sha256(content).hexdigest() == persisted[0]["sha256"]
    assert json.loads(content)["details"]["values"] == list(range(1000))


def test_live_receipt_persistence_is_exact_and_conflict_detecting(tmp_path: Path) -> None:
    """A command receipt is idempotent only for identical sanitized bytes."""
    path = tmp_path / "receipt.json"
    payload: dict[str, object] = {"status": "SUCCEEDED", "value": 1}

    live_analysis._persist_receipt(payload, path)
    live_analysis._persist_receipt(payload, path)

    assert json.loads(path.read_text(encoding="utf-8")) == payload
    with pytest.raises(ValueError, match="different bytes"):
        live_analysis._persist_receipt({"status": "SUCCEEDED", "value": 2}, path)


def test_live_analysis_without_database_url_is_explicitly_blocked(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The public analysis command never converts missing live access into fixture evidence."""
    monkeypatch.delenv("BDL__DB__URL", raising=False)

    status = live_analysis.main(
        [
            "--market-id",
            MARKET,
            "--decision-time",
            "2026-01-02T00:00:00+00:00",
            "--code",
            "missing-analysis.py",
            "--field",
            "value",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert status == BLOCKED_EXIT
    assert payload == {
        "error_code": "READ_ONLY_DATABASE_URL_UNSET",
        "live_data_read": False,
        "required_action": "open the approved human_ro tunnel and set BDL__DB__URL",
        "status": "BLOCKED",
    }
