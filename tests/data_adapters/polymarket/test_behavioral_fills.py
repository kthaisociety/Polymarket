"""Retention and registered-view adversaries for behavioral taker fills."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest

from research_agent.data_adapters.polymarket import (
    BehavioralFillCorpus,
    BehavioralFillRequest,
    BehavioralFillStore,
    BehavioralTakerFill,
    DatabaseBehavioralFillReader,
    PolymarketCorpus,
    PolymarketCorpusContract,
    PolymarketCorpusOutcome,
    PolymarketCorpusRequest,
    PolymarketCorpusStore,
    PolymarketPricePoint,
    PolymarketResolutionRecord,
    build_behavioral_fill_analysis,
)
from research_agent.exploration import AnalysisStatus

if TYPE_CHECKING:
    from collections.abc import Mapping

ORIGIN = datetime(2026, 1, 1, tzinfo=UTC)
AS_OF = datetime(2026, 3, 1, tzinfo=UTC)


def _parent_corpus(event_count: int = 5) -> PolymarketCorpus:
    contracts: list[PolymarketCorpusContract] = []
    resolutions: list[PolymarketResolutionRecord] = []
    prices: list[PolymarketPricePoint] = []
    for number in range(event_count):
        market_id = f"market-{number}"
        event_id = f"event-{number}"
        close = ORIGIN + timedelta(days=10 + number)
        payout = Decimal(number % 2)
        contracts.append(
            PolymarketCorpusContract(
                market_id=market_id,
                event_id=event_id,
                market_type="binary",
                question=f"Question {number}?",
                open_time=ORIGIN,
                close_time=close,
                outcomes=(
                    PolymarketCorpusOutcome(0, "Yes", f"yes-{number}", payout),
                    PolymarketCorpusOutcome(1, "No", f"no-{number}", 1 - payout),
                ),
            )
        )
        resolutions.append(
            PolymarketResolutionRecord(
                market_id=market_id,
                resolved_time=close + timedelta(hours=1),
                payouts=(payout, 1 - payout),
                oracle="uma",
                question_id=f"question-{number}",
                transaction_hash=f"resolution-{number}",
            )
        )
        prices.extend(
            PolymarketPricePoint(
                market_id=market_id,
                outcome_index=0,
                outcome_token=f"yes-{number}",
                observed_at=ORIGIN + timedelta(hours=hour),
                price=Decimal("0.2") + Decimal("0.1") * hour,
                fidelity=60,
            )
            for hour in range(3)
        )
    return PolymarketCorpus(
        PolymarketCorpusRequest(
            environment_id="test-behavioral-fills",
            as_of=AS_OF,
            min_points=2,
            max_markets=event_count,
            outcome_index=0,
        ),
        tuple(contracts),
        tuple(resolutions),
        tuple(prices),
    )


def _fill(number: int, *, price: str = "0.40") -> BehavioralTakerFill:
    return BehavioralTakerFill(
        account=f"wallet-{number}",
        market_id=f"market-{number}",
        fill_time=ORIGIN + timedelta(days=number),
        fill_uid=f"fill-{number}",
        outcome_index=number % 2,
        side="BUY" if number % 2 == 0 else "SELL",
        price=Decimal(price),
        size=Decimal(10),
        block_number=100 + number,
        transaction_hash=f"tx-{number}",
    )


def _fill_corpus(parent_ref: str, *, changed_price: bool = False) -> BehavioralFillCorpus:
    return BehavioralFillCorpus(
        BehavioralFillRequest("test-behavioral-fills", AS_OF, parent_ref),
        tuple(
            _fill(number, price="0.99" if changed_price and number == 0 else "0.40")
            for number in range(5)
        ),
    )


def test_fill_store_round_trip_is_content_addressed_and_conflict_detecting(
    tmp_path: Path,
) -> None:
    """Canonical account-level rows reopen with exact path-independent identity."""
    parent = PolymarketCorpusStore.from_corpus(_parent_corpus())
    corpus = _fill_corpus(parent.ref.uri)
    store = BehavioralFillStore(tmp_path)

    first = store.retain(corpus)
    repeated = store.retain(corpus)
    loaded = store.load(first)

    assert first == repeated
    assert loaded.corpus == corpus
    assert store.verify(first)
    store.object_path(first).write_bytes(store.object_path(first).read_bytes() + b"changed")
    assert store.verify(first) is False


def test_registered_fill_view_excludes_parent_protected_event_and_binds_values() -> None:
    """Only visible event rows enter the sandbox and exact fill values affect binding."""
    parent = PolymarketCorpusStore.from_corpus(_parent_corpus())
    fills = BehavioralFillStore.from_corpus(_fill_corpus(parent.ref.uri))
    changed = BehavioralFillStore.from_corpus(_fill_corpus(parent.ref.uri, changed_price=True))
    analysis = build_behavioral_fill_analysis(parent, fills, session_id="behavioral-session")
    changed_analysis = build_behavioral_fill_analysis(
        parent,
        changed,
        session_id="behavioral-session",
    )
    source = """
markets = read("polymarket-development-taker-fills", "market_id")
partitions = read("polymarket-development-taker-fills", "research_partition")
prices = read("polymarket-development-taker-fills", "price")
result = structured_return(
    "registered behavioral rows",
    {"markets": markets, "partitions": partitions, "prices": prices},
)
"""

    result = analysis.run(source=source, session_id="behavioral-session", action_id="screen")

    assert result.status is AnalysisStatus.SUCCEEDED
    assert result.details == {
        "markets": ("market-0", "market-1", "market-2", "market-3"),
        "partitions": ("TRAIN", "TRAIN", "TRAIN", "EVALUATION"),
        "prices": (0.4, 0.4, 0.4, 0.4),
    }
    assert analysis.harness.binding_identity != changed_analysis.harness.binding_identity
    assert "market-4" not in analysis.registered_event_views[0].fields["market_id"]


class _Connection:
    def __init__(self) -> None:
        self.query = ""
        self.arguments: tuple[object, ...] = ()

    async def fetch(self, query: str, *args: object) -> list[Mapping[str, object]]:
        self.query = query
        self.arguments = args
        fill = _fill(0)
        return [
            {
                "account": fill.account,
                "market_id": fill.market_id,
                "fill_time": fill.fill_time,
                "fill_uid": fill.fill_uid,
                "outcome_index": fill.outcome_index,
                "side": fill.side,
                "price": fill.price,
                "size": fill.size,
                "block_number": fill.block_number,
                "transaction_hash": fill.transaction_hash,
            }
        ]


def test_database_reader_uses_bounded_parent_ids_and_taker_predicate() -> None:
    """The production seam cannot broaden beyond parent markets or double-count both legs."""
    parent = PolymarketCorpusStore.from_corpus(_parent_corpus())
    request = BehavioralFillRequest("test-behavioral-fills", AS_OF, parent.ref.uri)
    connection = _Connection()

    corpus = asyncio.run(
        DatabaseBehavioralFillReader(connection).read_corpus(
            request,
            market_ids=("market-0",),
        )
    )

    assert corpus.fills == (_fill(0),)
    assert connection.arguments == (("market-0",), AS_OF)
    assert "market_id = ANY($1::text[])" in connection.query
    assert "right(f.raw->'topics'->>3, 40)" in connection.query


def test_fill_corpus_rejects_duplicates_and_rows_after_ceiling() -> None:
    """Ambiguous match identities and future data fail before registration."""
    request = BehavioralFillRequest("test", AS_OF, "parent")
    fill = _fill(0)

    with pytest.raises(ValueError, match="duplicate fill"):
        BehavioralFillCorpus(request, (fill, fill))
    with pytest.raises(ValueError, match="as-of ceiling"):
        BehavioralFillCorpus(
            request,
            (replace(fill, fill_time=AS_OF + timedelta(seconds=1)),),
        )


@pytest.mark.parametrize(
    "source_name",
    [
        "02_03_skilled_wallet_matched_state_v2.py",
        "04_delayed_expert_consensus_v2.py",
        "05_delayed_wallet_state_activity_match_v2.py",
        "08_crowded_extrapolation_exhaustion_v2.py",
    ],
)
def test_revised_behavioral_sources_execute_on_registered_panel(source_name: str) -> None:
    """The versioned wallet sources are valid harness programs even with sparse coverage."""
    parent = PolymarketCorpusStore.from_corpus(_parent_corpus())
    fills = BehavioralFillStore.from_corpus(_fill_corpus(parent.ref.uri))
    analysis = build_behavioral_fill_analysis(parent, fills, session_id="source-test")
    source_path = (
        Path(__file__).parents[3]
        / "studies"
        / "polymarket-enforced-research-campaign-2026-08-24"
        / "source"
        / source_name
    )

    result = analysis.run(
        source=source_path.read_text(),
        session_id="source-test",
        action_id=source_name,
    )

    assert result.status is AnalysisStatus.SUCCEEDED
    decision = cast("dict[str, object]", result.details)["decision"]
    assert isinstance(decision, str)
    assert decision.startswith("REJECT_FIXED_")
