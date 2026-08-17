"""Causal and retention adversaries for the resolved-market research corpus."""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, cast

import pytest

from research_agent.data_adapters.polymarket import (
    DatabasePolymarketCorpusReader,
    PolymarketCorpus,
    PolymarketCorpusContract,
    PolymarketCorpusOutcome,
    PolymarketCorpusRequest,
    PolymarketCorpusStore,
    PolymarketPricePoint,
    PolymarketRegisteredEventField,
    PolymarketResolutionRecord,
    build_polymarket_development_analysis,
    corpus_snapshot,
    register_polymarket_resolution_corpus,
    run_corpus_studies,
)
from research_agent.data_foundation import (
    BoundaryStatus,
    DatasetSchema,
    FieldDefinition,
    InformationSetBuilder,
    ObservationInput,
    ObservationRegistrar,
    RegisteredTemporalDataset,
)
from research_agent.data_foundation._identity import stable_identity
from research_agent.exploration import (
    AnalysisRequest,
    AnalysisStatus,
    DataAccessRequest,
    ResourceLimits,
)

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


def _event_grouped_corpus() -> PolymarketCorpus:
    contracts: list[PolymarketCorpusContract] = []
    resolutions: list[PolymarketResolutionRecord] = []
    prices: list[PolymarketPricePoint] = []
    for event_number in range(5):
        market_id = f"market-{event_number}"
        event_id = f"event-{event_number}"
        token = f"yes-{event_number}"
        close = CLOSED + timedelta(days=event_number)
        payout = Decimal(event_number % 2)
        contracts.append(
            PolymarketCorpusContract(
                market_id=market_id,
                event_id=event_id,
                market_type="binary",
                question=f"Question {event_number}?",
                open_time=OPENED,
                close_time=close,
                outcomes=(
                    PolymarketCorpusOutcome(0, "Yes", token, payout),
                    PolymarketCorpusOutcome(1, "No", f"no-{event_number}", 1 - payout),
                ),
            )
        )
        resolutions.append(
            PolymarketResolutionRecord(
                market_id=market_id,
                resolved_time=close + timedelta(hours=1),
                payouts=(payout, 1 - payout),
                oracle="uma",
                question_id=f"question-{event_number}",
                transaction_hash=f"tx-{event_number}",
            )
        )
        prices.extend(
            [
                PolymarketPricePoint(
                    market_id=market_id,
                    outcome_index=0,
                    outcome_token=token,
                    observed_at=OPENED + timedelta(hours=point_number),
                    price=Decimal("0.2") + Decimal("0.1") * point_number,
                    fidelity=60,
                )
                for point_number in range(3)
            ]
        )
    request = replace(_request(), max_markets=5)
    return PolymarketCorpus(request, tuple(contracts), tuple(resolutions), tuple(prices))


def test_development_analysis_hides_latest_whole_event_and_is_counterfactual_stable() -> None:
    """Changing any protected value cannot affect a development capability or authored result."""
    corpus = _event_grouped_corpus()
    snapshot = PolymarketCorpusStore.from_corpus(corpus)
    first = build_polymarket_development_analysis(snapshot, session_id="session")
    source = """
prices = read("polymarket-development-prices", "market_probability")
labels = read("polymarket-development-outcomes", "resolution_payout")
result = structured_return(
    "Development-only means.",
    {"price_mean": sum(prices) / len(prices), "label_mean": sum(labels) / len(labels)},
)
"""
    first_result = first.run(source=source, session_id="session", action_id="first")

    protected_market = corpus.contracts[-1]
    changed_contract = replace(
        protected_market,
        question="PROTECTED QUESTION MUST NOT ENTER DEVELOPMENT",
        outcomes=(
            replace(protected_market.outcomes[0], payout=Decimal(1)),
            replace(protected_market.outcomes[1], payout=Decimal(0)),
        ),
    )
    changed_resolution = replace(corpus.resolutions[-1], payouts=(Decimal(1), Decimal(0)))
    changed_prices = tuple(
        replace(point, price=Decimal("0.99"))
        if point.market_id == protected_market.market_id
        else point
        for point in corpus.prices
    )
    changed = replace(
        corpus,
        contracts=(*corpus.contracts[:-1], changed_contract),
        resolutions=(*corpus.resolutions[:-1], changed_resolution),
        prices=changed_prices,
    )
    second = build_polymarket_development_analysis(
        PolymarketCorpusStore.from_corpus(changed),
        session_id="session",
    )
    second_result = second.run(source=source, session_id="session", action_id="second")

    assert first.partition.development_event_ids == tuple(f"event-{number}" for number in range(4))
    assert first.partition.protected_event_count == 1
    assert protected_market.market_id not in first.price_view.fields["market_id"]
    assert first.price_view.fields == second.price_view.fields
    assert first.outcome_view.fields == second.outcome_view.fields
    assert first_result.status is AnalysisStatus.SUCCEEDED
    assert first_result.details == second_result.details


def test_development_analysis_denies_an_ungranted_field_before_disclosure() -> None:
    """The sandbox cannot request a field absent from its exact development capability."""
    analysis = build_polymarket_development_analysis(
        PolymarketCorpusStore.from_corpus(_event_grouped_corpus()),
        session_id="session",
    )

    result = analysis.harness.run(
        AnalysisRequest(
            session_id="session",
            action_id="forged-field",
            source=(
                'result = structured_return("bad", '
                'read("polymarket-development-outcomes", "oracle"))'
            ),
            data_access=(DataAccessRequest("polymarket-development-outcomes", ("oracle",)),),
        )
    )

    assert result.status is AnalysisStatus.DENIED
    assert result.provenance.accesses == ()


def test_development_analysis_exposes_contract_questions_for_semantic_discovery() -> None:
    """Development research can identify a contract's meaning without protected disclosure."""
    analysis = build_polymarket_development_analysis(
        PolymarketCorpusStore.from_corpus(_event_grouped_corpus()),
        session_id="semantic-discovery",
    )
    source = """
markets = read("polymarket-development-outcomes", "market_id")
questions = read("polymarket-development-outcomes", "question")
labels = read("polymarket-development-outcomes", "outcome_label")
result = structured_return(
    "Development contract catalog.",
    {"markets": markets, "questions": questions, "labels": labels},
)
"""

    result = analysis.run(
        source=source,
        session_id="semantic-discovery",
        action_id="inspect-development-questions",
    )

    assert result.status is AnalysisStatus.SUCCEEDED
    assert result.details == {
        "markets": ("market-0", "market-1", "market-2", "market-3"),
        "questions": ("Question 0?", "Question 1?", "Question 2?", "Question 3?"),
        "labels": ("Yes", "Yes", "Yes", "Yes"),
    }
    assert "Question 4?" not in result.details["questions"]


def _registered_event_field(
    event_id: str,
    *,
    environment_id: str = "test-polymarket-corpus",
) -> PolymarketRegisteredEventField:
    schema = DatasetSchema(
        dataset_id="public-event-series",
        version="v1",
        environment_id=environment_id,
        provenance_ref="source:public-event-series",
        fields=(
            FieldDefinition(
                "external_count",
                "External event count",
                "integer",
                "count",
                ("event_id", "source_item_id"),
                "One externally observed event with an explicit availability time.",
            ),
        ),
    )
    dataset = ObservationRegistrar().register(
        schema,
        (
            ObservationInput(
                field_ref=schema.field_ref("external_count"),
                value=1,
                reference_time=OPENED + timedelta(hours=1),
                available_at=OPENED + timedelta(hours=1, minutes=5),
                vintage_id="source-item-1",
                revision_number=0,
                source_ref="source:exact",
                provenance_ref="derived:exact",
                availability_rule_version="public-import-time/v1",
                dimensions=(("event_id", event_id), ("source_item_id", "item-1")),
            ),
        ),
    )
    approval_id = "approved-temporal-dataset:test"
    derived_ref_uri = "derived:test"
    profile_id = "temporal-dataset-profile:test"
    attestation_id = stable_identity(
        "registered-temporal-dataset",
        {
            "approval_id": approval_id,
            "derived_ref_uri": derived_ref_uri,
            "profile_id": profile_id,
            "registration_id": dataset.registration_id,
        },
    )
    registration = RegisteredTemporalDataset(
        attestation_id=attestation_id,
        approval_id=approval_id,
        derived_ref_uri=derived_ref_uri,
        profile_id=profile_id,
        dataset=dataset,
    )
    return PolymarketRegisteredEventField(
        view_id="registered-public-event-series",
        registration=registration,
        field_id="external_count",
    )


def test_registered_event_field_enters_development_harness_with_temporal_provenance() -> None:
    """An authority-issued event field enters the same tracked sandbox capability surface."""
    corpus = _event_grouped_corpus()
    supplement = _registered_event_field("event-1")
    analysis = build_polymarket_development_analysis(
        PolymarketCorpusStore.from_corpus(corpus),
        session_id="registered-development-field",
        registered_event_fields=(supplement,),
    )
    source = """
events = read("registered-public-event-series", "event_id")
available = read("registered-public-event-series", "available_at_epoch_seconds")
counts = read("registered-public-event-series", "external_count")
result = structured_return(
    "Registered event field is available to development code.",
    {"events": events, "available": available, "counts": counts},
)
"""

    result = analysis.run(
        source=source,
        session_id="registered-development-field",
        action_id="registered-field-access",
    )

    assert result.status is AnalysisStatus.SUCCEEDED
    assert result.details == {
        "events": ("event-1",),
        "available": ((OPENED + timedelta(hours=1, minutes=5)).timestamp(),),
        "counts": (1,),
    }
    assert [item.dataset_ref for item in result.provenance.accesses[-3:]] == [
        supplement.registration.attestation_id,
        supplement.registration.attestation_id,
        supplement.registration.attestation_id,
    ]


@pytest.mark.parametrize(
    ("event_id", "environment_id", "message"),
    [
        ("event-4", "test-polymarket-corpus", "unknown or protected"),
        ("event-1", "another-environment", "different corpus environment"),
    ],
)
def test_registered_event_field_cannot_cross_protected_or_environment_boundary(
    event_id: str,
    environment_id: str,
    message: str,
) -> None:
    """Supplementary observations must belong to this corpus and only its development events."""
    with pytest.raises(ValueError, match=message):
        build_polymarket_development_analysis(
            PolymarketCorpusStore.from_corpus(_event_grouped_corpus()),
            session_id="registered-development-field",
            registered_event_fields=(
                _registered_event_field(event_id, environment_id=environment_id),
            ),
        )


def test_development_view_issues_authoritative_chronological_event_ordinals() -> None:
    """Authored walk-forward code must not infer fold order from physical contract order."""
    corpus = _event_grouped_corpus()
    physically_reversed = replace(
        corpus,
        contracts=tuple(reversed(corpus.contracts)),
        resolutions=tuple(reversed(corpus.resolutions)),
    )
    analysis = build_polymarket_development_analysis(
        PolymarketCorpusStore.from_corpus(physically_reversed),
        session_id="chronological-event-authority",
    )
    expected = {
        event_id: ordinal
        for ordinal, event_id in enumerate(analysis.partition.development_event_ids)
    }

    price_events = analysis.price_view.fields["event_id"]
    price_ordinals = analysis.price_view.fields["event_chronological_ordinal"]
    outcome_events = analysis.outcome_view.fields["event_id"]
    outcome_ordinals = analysis.outcome_view.fields["event_chronological_ordinal"]

    assert all(
        expected[event] == ordinal
        for event, ordinal in zip(price_events, price_ordinals, strict=True)
    )
    assert all(
        expected[event] == ordinal
        for event, ordinal in zip(outcome_events, outcome_ordinals, strict=True)
    )


def test_study_receipt_rejects_success_detail_left_only_in_ephemeral_artifact(
    tmp_path: Path,
) -> None:
    """A command cannot call an in-memory-only large result reproducible evidence."""
    analysis = build_polymarket_development_analysis(
        PolymarketCorpusStore.from_corpus(_event_grouped_corpus()),
        session_id="session",
        resource_limits=ResourceLimits(max_inline_bytes=1),
    )
    source = """
prices = read("polymarket-development-prices", "market_probability")
result = structured_return("large", {"prices": prices})
"""
    observation = analysis.run(source=source, session_id="session", action_id="large")

    assert observation.status is AnalysisStatus.SUCCEEDED
    assert observation.details is None
    with pytest.raises(ValueError, match="ephemeral artifact"):
        run_corpus_studies._receipt_payload(  # noqa: SLF001
            analysis=analysis,
            source_path=tmp_path / "large.py",
            source_sha256="source-sha",
            observation=observation,
        )
