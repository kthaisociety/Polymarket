"""Causal and provenance adversaries for the Polymarket tape adapter."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from research_agent.data_adapters.polymarket import (
    PolymarketBlockVintage,
    PolymarketContractRecord,
    PolymarketFillRecord,
    PolymarketImportRequest,
    PolymarketIngestionResult,
    PolymarketOutcomeRecord,
    ingest_polymarket_contract_tape,
)
from research_agent.data_foundation import BoundaryStatus, InformationSetBuilder

MARKET = "0xmarket"
YES_ASSET_ID = "asset-yes"
NO_ASSET_ID = "asset-no"
ORIGIN = datetime(2026, 1, 1, tzinfo=UTC)
EXPECTED_INCLUDED = 2
EXPECTED_EXCLUDED = 2
EXPECTED_OBSERVATIONS = 8


class _Reader:
    """Protocol executor with exact records and no database behavior."""

    def __init__(self, fills: tuple[PolymarketFillRecord, ...]) -> None:
        self.fills = fills

    async def read_vintage(self) -> PolymarketBlockVintage:
        return PolymarketBlockVintage(100, 200, "history", "forward")

    async def read_contracts(
        self, market_ids: tuple[str, ...]
    ) -> tuple[PolymarketContractRecord, ...]:
        assert market_ids == (MARKET,)
        return (_contract(),)

    async def read_fills(self, market_id: str) -> tuple[PolymarketFillRecord, ...]:
        assert market_id == MARKET
        return self.fills


def _contract() -> PolymarketContractRecord:
    return PolymarketContractRecord(
        market_id=MARKET,
        outcome_count=2,
        outcomes=(
            PolymarketOutcomeRecord(0, YES_ASSET_ID, Decimal(1)),
            PolymarketOutcomeRecord(1, NO_ASSET_ID, Decimal(0)),
        ),
        close_time=ORIGIN + timedelta(days=30),
        resolved=True,
    )


def _fill(uid: str, minute: int, block: int | None, *, side: str = "BUY") -> PolymarketFillRecord:
    return PolymarketFillRecord(
        fill_uid=uid,
        fill_time=ORIGIN + timedelta(minutes=minute),
        market_id=MARKET,
        outcome_index=0,
        outcome_token=YES_ASSET_ID,
        side=side,
        price=Decimal("0.40") + Decimal(minute) / Decimal(100),
        size=Decimal(10),
        block_number=block,
        transaction_hash=f"0xtx-{uid}",
    )


def _ingest(reader: _Reader) -> PolymarketIngestionResult:
    return asyncio.run(
        ingest_polymarket_contract_tape(
            reader,
            PolymarketImportRequest((MARKET,), "test-polymarket-environment"),
        )
    )


def test_registration_is_block_windowed_and_temporally_causal() -> None:
    """Only the pinned tape enters the legal information boundary at block time."""
    result = _ingest(
        _Reader(
            (
                _fill("before", 0, 99),
                _fill("first", 1, 110),
                _fill("second", 2, 150, side="SELL"),
                _fill("after", 3, 201),
            )
        )
    )

    assert result.included_fill_count == EXPECTED_INCLUDED
    assert result.excluded_fill_count == EXPECTED_EXCLUDED
    assert len(result.registered.observations) == EXPECTED_OBSERVATIONS
    assert {item.vintage_id for item in result.registered.observations} == {
        "polygon-blocks:100-200"
    }
    assert all(item.reference_time == item.available_at for item in result.registered.observations)
    assert all(
        item.availability_rule_version == "polymarket-onchain-block-inclusion/v1"
        for item in result.registered.observations
    )

    price = result.registered.schema.field_ref("trade_price")
    before_second = InformationSetBuilder().build(
        result.catalog,
        decision_time=ORIGIN + timedelta(minutes=2) - timedelta(microseconds=1),
        requested_fields=(price,),
    )
    at_second = InformationSetBuilder().build(
        result.catalog,
        decision_time=ORIGIN + timedelta(minutes=2),
        requested_fields=(price,),
    )
    assert before_second.status is BoundaryStatus.READY
    assert len(before_second.observations) == 1
    assert len(at_second.observations) == EXPECTED_INCLUDED


def test_missing_block_fails_instead_of_inventing_a_vintage() -> None:
    """A print without an exact block cannot be placed in the declared vintage."""
    with pytest.raises(ValueError, match="no exact block"):
        _ingest(_Reader((_fill("missing", 1, None),)))


def test_contract_and_outcome_substitution_fail_closed() -> None:
    """Nearby market and outcome identities never substitute for the requested tape."""
    wrong_market = replace(_fill("wrong", 1, 110), market_id="0xother")
    unknown_outcome = "asset-replacement"
    wrong_outcome = replace(_fill("outcome", 1, 110), outcome_token=unknown_outcome)

    with pytest.raises(ValueError, match="different contract"):
        _ingest(_Reader((wrong_market,)))
    with pytest.raises(ValueError, match="unknown outcome"):
        _ingest(_Reader((wrong_outcome,)))


def test_in_window_scope_repair_changes_digest_but_cannot_reconstruct_prior_bytes() -> None:
    """A late in-window insert moves identity while the cursor window stays unchanged."""
    first = _ingest(_Reader((_fill("first", 1, 110),)))
    repaired = _ingest(_Reader((_fill("first", 1, 110), _fill("late-backfill", 0, 105))))

    assert first.vintage == repaired.vintage
    assert first.source_digest != repaired.source_digest
    assert first.registered.registration_id != repaired.registered.registration_id
    assert any("cannot reconstruct prior bytes" in item for item in repaired.snapshot_caveats)


def test_resolved_payout_is_metadata_not_a_registered_label() -> None:
    """Payout cannot become a label without exact resolution availability."""
    result = _ingest(_Reader((_fill("first", 1, 110),)))

    assert result.contracts[0].outcomes[0].resolved_payout == Decimal(1)
    assert "resolution_payout" not in {field.field_id for field in result.registered.schema.fields}
    assert any("resolution availability" in item for item in result.snapshot_caveats)
    assert any("event/group identity" in item for item in result.snapshot_caveats)
