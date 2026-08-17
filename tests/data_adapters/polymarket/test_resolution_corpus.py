"""Causal and retention adversaries for the resolved-market research corpus."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, cast

import pytest

from research_agent.data_adapters.polymarket import (
    DatabasePolymarketCorpusReader,
    PolymarketCorpus,
    PolymarketCorpusRequest,
    PolymarketCorpusStore,
    corpus_snapshot,
    register_polymarket_resolution_corpus,
)
from research_agent.data_foundation import BoundaryStatus, InformationSetBuilder

if TYPE_CHECKING:
    from pathlib import Path

    from research_agent.data_adapters.polymarket.reader import _FetchExecutor

MARKET = "0xmarket"
EVENT = "event-1"
YES = "yes-token"
NO = "no-token"
OPENED = datetime(2026, 1, 1, tzinfo=UTC)
CLOSED = datetime(2026, 1, 15, tzinfo=UTC)
RESOLVED = datetime(2026, 1, 16, tzinfo=UTC)
AS_OF = datetime(2026, 2, 1, tzinfo=UTC)
EXPECTED_PRICE_POINTS = 2
BLOCKED_EXIT = 2


class _CorpusExecutor:
    """Exact fake for the direct, SELECT-only Chronos corpus read surface."""

    def __init__(self, *, event_id: str | None = EVENT) -> None:
        self.event_id = event_id
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    async def fetch(self, sql: str, *parameters: object) -> list[dict[str, object]]:
        self.calls.append((sql, parameters))
        if "WITH eligible" in sql:
            return [
                {
                    "market_id": MARKET,
                    "event_id": self.event_id,
                    "market_type": "binary",
                    "question": "Will the event occur?",
                    "open_time": OPENED,
                    "close_time": CLOSED,
                    "outcome_count": 2,
                    "resolved_time": RESOLVED,
                    "oracle": "uma",
                    "question_id": "question-1",
                    "payouts": [Decimal(1), Decimal(0)],
                    "resolution_tx_hash": "0xresolution",
                    "outcome_index": 0,
                    "label": "Yes",
                    "outcome_token": YES,
                    "payout": Decimal(1),
                },
                {
                    "market_id": MARKET,
                    "event_id": self.event_id,
                    "market_type": "binary",
                    "question": "Will the event occur?",
                    "open_time": OPENED,
                    "close_time": CLOSED,
                    "outcome_count": 2,
                    "resolved_time": RESOLVED,
                    "oracle": "uma",
                    "question_id": "question-1",
                    "payouts": [Decimal(1), Decimal(0)],
                    "resolution_tx_hash": "0xresolution",
                    "outcome_index": 1,
                    "label": "No",
                    "outcome_token": NO,
                    "payout": Decimal(0),
                },
            ]
        if "FROM market.price_series" in sql:
            return [
                {
                    "market_id": MARKET,
                    "outcome_index": 0,
                    "outcome_token": YES,
                    "ts": CLOSED - timedelta(days=8),
                    "price": Decimal("0.40"),
                    "fidelity": 60,
                },
                {
                    "market_id": MARKET,
                    "outcome_index": 0,
                    "outcome_token": YES,
                    "ts": CLOSED - timedelta(days=7),
                    "price": Decimal("0.45"),
                    "fidelity": 60,
                },
            ]
        message = "unexpected corpus SQL"
        raise AssertionError(message)


def _request() -> PolymarketCorpusRequest:
    return PolymarketCorpusRequest(
        environment_id="test-polymarket-corpus",
        as_of=AS_OF,
        min_points=2,
        max_markets=10,
        outcome_index=0,
    )


def _read(executor: _CorpusExecutor | None = None) -> PolymarketCorpus:
    executor = executor or _CorpusExecutor()
    reader = DatabasePolymarketCorpusReader(cast("_FetchExecutor", executor))
    return asyncio.run(reader.read_corpus(_request()))


def test_direct_corpus_reader_preserves_event_resolution_and_price_identity() -> None:
    """The server's new facts reach Chronos without close-time or market-ID substitution."""
    executor = _CorpusExecutor()

    corpus = _read(executor)

    assert corpus.request == _request()
    assert corpus.contracts[0].event_id == EVENT
    assert corpus.contracts[0].outcomes[0].outcome_token == YES
    assert corpus.resolutions[0].resolved_time == RESOLVED
    assert corpus.resolutions[0].payouts == (Decimal(1), Decimal(0))
    assert tuple(point.price for point in corpus.prices) == (
        Decimal("0.40"),
        Decimal("0.45"),
    )
    assert all("SELECT" in sql or "WITH eligible" in sql for sql, _ in executor.calls)


def test_missing_event_identity_fails_instead_of_inventing_an_independent_market() -> None:
    """A market without its server event identity cannot enter grouped research."""
    with pytest.raises(ValueError, match="event identity"):
        _read(_CorpusExecutor(event_id=None))


def test_registration_keeps_predictor_and_resolution_clocks_separate(tmp_path: Path) -> None:
    """The payout is unavailable before settlement even though its close time has passed."""
    retained = PolymarketCorpusStore(tmp_path)
    corpus = _read()
    snapshot = retained.from_corpus(corpus)
    registration = register_polymarket_resolution_corpus(snapshot)
    price_ref = registration.price_dataset.schema.field_ref("market_probability")
    payout_ref = registration.resolution_dataset.schema.field_ref("resolution_payout")

    before_resolution = InformationSetBuilder().build(
        registration.catalog,
        decision_time=RESOLVED - timedelta(microseconds=1),
        requested_fields=(price_ref, payout_ref),
    )
    at_resolution = InformationSetBuilder().build(
        registration.catalog,
        decision_time=RESOLVED,
        requested_fields=(price_ref, payout_ref),
    )

    assert before_resolution.status is BoundaryStatus.INSUFFICIENT
    assert len(before_resolution.for_field(price_ref)) == EXPECTED_PRICE_POINTS
    assert before_resolution.for_field(payout_ref) == ()
    assert len(at_resolution.for_field(payout_ref)) == 1
    label = at_resolution.for_field(payout_ref)[0]
    assert label.reference_time == CLOSED
    assert label.available_at == RESOLVED
    assert dict(label.dimensions)["event_id"] == EVENT


def test_content_addressed_snapshot_is_reusable_and_conflict_detecting(tmp_path: Path) -> None:
    """Retained canonical bytes, not the mutable live database, anchor corpus identity."""
    store = PolymarketCorpusStore(tmp_path)
    corpus = _read()

    first = store.retain(corpus)
    repeated = store.retain(corpus)
    loaded = store.load(first.ref)

    assert repeated == first
    assert loaded == store.from_corpus(corpus)
    assert store.verify(first.ref)
    object_path = store.object_path(first.ref)
    object_path.write_bytes(object_path.read_bytes() + b"changed")
    assert not store.verify(first.ref)


def test_public_corpus_command_without_database_url_is_explicitly_blocked(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """The public command never turns missing production access into fixture evidence."""
    monkeypatch.delenv("BDL__DB__URL", raising=False)

    status = corpus_snapshot.main(
        [
            "--as-of",
            AS_OF.isoformat(),
            "--min-points",
            "2",
            "--max-markets",
            "10",
            "--workspace",
            str(tmp_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert status == BLOCKED_EXIT
    assert payload["status"] == "BLOCKED"
    assert payload["live_data_read"] is False
    assert "password" not in json.dumps(payload).casefold()
