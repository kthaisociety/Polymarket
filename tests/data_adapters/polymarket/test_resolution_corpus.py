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
    build_polymarket_replication_analysis,
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


def _event_grouped_corpus(event_count: int = 5) -> PolymarketCorpus:
    contracts: list[PolymarketCorpusContract] = []
    resolutions: list[PolymarketResolutionRecord] = []
    prices: list[PolymarketPricePoint] = []
    for event_number in range(event_count):
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
    request = replace(_request(), max_markets=event_count)
    return PolymarketCorpus(request, tuple(contracts), tuple(resolutions), tuple(prices))


def _corpus_prefix(corpus: PolymarketCorpus, contract_count: int) -> PolymarketCorpus:
    market_ids = frozenset(item.market_id for item in corpus.contracts[:contract_count])
    return replace(
        corpus,
        request=replace(corpus.request, max_markets=contract_count),
        contracts=corpus.contracts[:contract_count],
        resolutions=tuple(item for item in corpus.resolutions if item.market_id in market_ids),
        prices=tuple(item for item in corpus.prices if item.market_id in market_ids),
    )


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
    assert (
        first.partition.partition_id
        == "e2246f40f6c26b7824375f0ab60d75dff6c2e420ae679b79109c355a0facd18c"
    )
    assert first.partition.protected_event_count == 1
    assert protected_market.market_id not in first.price_view.fields["market_id"]
    assert first.price_view.fields == second.price_view.fields
    assert first.outcome_view.fields == second.outcome_view.fields
    assert first_result.status is AnalysisStatus.SUCCEEDED
    assert first_result.details == second_result.details


def test_replication_analysis_exposes_only_fresh_events_before_expanded_protection() -> None:
    """An ancestor corpus and the expanded final block remain absent from replication views."""
    expanded = _event_grouped_corpus(10)
    ancestor = _corpus_prefix(expanded, 5)

    analysis = build_polymarket_replication_analysis(
        PolymarketCorpusStore.from_corpus(expanded),
        PolymarketCorpusStore.from_corpus(ancestor),
        session_id="fresh-replication",
    )
    expected_events = ("event-5", "event-6", "event-7")
    protected_count = len(expanded.contracts) - len(ancestor.contracts) - len(expected_events)

    assert analysis.partition.development_event_ids == expected_events
    assert analysis.partition.partition_method == ("whole-event-chronological-fresh-replication/v1")
    assert (
        analysis.partition.ancestor_snapshot_ref
        == PolymarketCorpusStore.from_corpus(ancestor).ref.uri
    )
    assert analysis.partition.ancestor_event_count == len(ancestor.contracts)
    assert analysis.partition.embargoed_event_count == len(ancestor.contracts)
    assert analysis.partition.protected_event_count == protected_count
    assert analysis.partition.development_market_count == len(expected_events)
    assert analysis.partition.embargoed_market_count == len(ancestor.contracts)
    assert analysis.partition.protected_market_count == protected_count
    assert set(analysis.price_view.fields["event_id"]) == set(expected_events)
    assert set(analysis.outcome_view.fields["event_id"]) == set(expected_events)


def test_replication_analysis_is_stable_to_ancestor_and_expanded_protected_values() -> None:
    """Changing hidden old or final values cannot affect fresh capability contents or results."""
    expanded = _event_grouped_corpus(10)
    ancestor = _corpus_prefix(expanded, 5)
    first = build_polymarket_replication_analysis(
        PolymarketCorpusStore.from_corpus(expanded),
        PolymarketCorpusStore.from_corpus(ancestor),
        session_id="fresh-replication",
    )
    hidden_markets = {"market-4", "market-9"}
    changed_contracts = tuple(
        replace(
            contract,
            question="HIDDEN VALUE CHANGED",
            outcomes=(
                replace(contract.outcomes[0], payout=Decimal(1)),
                replace(contract.outcomes[1], payout=Decimal(0)),
            ),
        )
        if contract.market_id in hidden_markets
        else contract
        for contract in expanded.contracts
    )
    changed = replace(
        expanded,
        contracts=changed_contracts,
        resolutions=tuple(
            replace(item, payouts=(Decimal(1), Decimal(0)))
            if item.market_id in hidden_markets
            else item
            for item in expanded.resolutions
        ),
        prices=tuple(
            replace(item, price=Decimal("0.99")) if item.market_id in hidden_markets else item
            for item in expanded.prices
        ),
    )
    second = build_polymarket_replication_analysis(
        PolymarketCorpusStore.from_corpus(changed),
        PolymarketCorpusStore.from_corpus(ancestor),
        session_id="fresh-replication",
    )
    source = """
prices = read("polymarket-development-prices", "market_probability")
labels = read("polymarket-development-outcomes", "resolution_payout")
result = structured_return(
    "Fresh-only means.",
    {"price_mean": sum(prices) / len(prices), "label_mean": sum(labels) / len(labels)},
)
"""

    first_result = first.run(source=source, session_id="fresh-replication", action_id="first")
    second_result = second.run(source=source, session_id="fresh-replication", action_id="second")

    assert first.price_view.fields == second.price_view.fields
    assert first.outcome_view.fields == second.outcome_view.fields
    assert first_result.status is AnalysisStatus.SUCCEEDED
    assert first_result.details == second_result.details


@pytest.mark.parametrize("mutation", ["order", "event", "resolution"])
def test_replication_analysis_rejects_changed_ancestor_identity_or_chronology(
    mutation: str,
) -> None:
    """A caller cannot use a merely similar corpus to establish a fresh replication boundary."""
    expanded = _event_grouped_corpus(10)
    ancestor = _corpus_prefix(expanded, 5)
    if mutation == "order":
        ancestor = replace(
            ancestor,
            contracts=(ancestor.contracts[1], ancestor.contracts[0], *ancestor.contracts[2:]),
            resolutions=(
                ancestor.resolutions[1],
                ancestor.resolutions[0],
                *ancestor.resolutions[2:],
            ),
        )
    elif mutation == "event":
        ancestor = replace(
            ancestor,
            contracts=(
                replace(ancestor.contracts[0], event_id="changed-event"),
                *ancestor.contracts[1:],
            ),
        )
    else:
        ancestor = replace(
            ancestor,
            resolutions=(
                replace(ancestor.resolutions[0], resolved_time=RESOLVED + timedelta(minutes=1)),
                *ancestor.resolutions[1:],
            ),
        )

    with pytest.raises(ValueError, match="ancestor"):
        build_polymarket_replication_analysis(
            PolymarketCorpusStore.from_corpus(expanded),
            PolymarketCorpusStore.from_corpus(ancestor),
            session_id="fresh-replication",
        )


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
indices = read("polymarket-development-outcomes", "outcome_index")
tokens = read("polymarket-development-outcomes", "outcome_token")
result = structured_return(
    "Development contract catalog.",
    {
        "markets": markets,
        "questions": questions,
        "labels": labels,
        "indices": indices,
        "tokens": tokens,
    },
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
        "indices": (0, 0, 0, 0),
        "tokens": ("yes-0", "yes-1", "yes-2", "yes-3"),
    }
    assert "Question 4?" not in result.details["questions"]
    assert "yes-4" not in result.details["tokens"]


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


def test_default_study_receipt_schema_remains_unchanged(tmp_path: Path) -> None:
    """Adding the replication path cannot change byte identity for ordinary study receipts."""
    analysis = build_polymarket_development_analysis(
        PolymarketCorpusStore.from_corpus(_event_grouped_corpus()),
        session_id="session",
    )
    observation = analysis.run(
        source='result = structured_return("ok", {"value": 1})',
        session_id="session",
        action_id="ordinary",
    )

    receipt = run_corpus_studies._receipt_payload(  # noqa: SLF001
        analysis=analysis,
        source_path=tmp_path / "ordinary.py",
        source_sha256="source-sha",
        observation=observation,
    )

    assert "ancestor_snapshot_ref" not in receipt
    assert "ancestor_event_count" not in receipt
    assert "embargoed_event_count" not in receipt
    assert "embargoed_market_count" not in receipt


def test_public_study_runner_builds_fresh_replication_view_from_exact_ancestry(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The offline entry point binds two retained snapshots into one fresh-only receipt."""
    expanded = _event_grouped_corpus(10)
    ancestor = _corpus_prefix(expanded, 5)
    store = PolymarketCorpusStore(tmp_path / "corpus")
    expanded_ref = store.retain(expanded).ref
    ancestor_ref = store.retain(ancestor).ref
    source_path = tmp_path / "fresh_events.py"
    source_path.write_text(
        """
events = read("polymarket-development-outcomes", "event_id")
result = structured_return("Fresh event count.", {"event_count": len(set(events))})
"""
    )
    receipt_directory = tmp_path / "receipts"

    status = run_corpus_studies.main(
        [
            "--snapshot-sha256",
            expanded_ref.content_sha256,
            "--snapshot-size",
            str(expanded_ref.size_bytes),
            "--ancestor-snapshot-sha256",
            ancestor_ref.content_sha256,
            "--ancestor-snapshot-size",
            str(ancestor_ref.size_bytes),
            "--workspace",
            str(store.root),
            "--source",
            str(source_path),
            "--receipt-directory",
            str(receipt_directory),
            "--session-id",
            "fresh-replication",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    receipt = output["receipts"][0]
    expected_event_count = len({"event-5", "event-6", "event-7"})

    assert status == 0
    assert receipt["status"] == AnalysisStatus.SUCCEEDED.value
    assert receipt["partition_method"] == "whole-event-chronological-fresh-replication/v1"
    assert receipt["ancestor_snapshot_ref"] == ancestor_ref.uri
    assert receipt["development_event_count"] == expected_event_count
    assert receipt["details"] == {"event_count": expected_event_count}
    assert receipt["embargoed_event_count"] == len(ancestor.contracts)
    assert receipt["protected_values_exposed"] is False
    assert receipt_directory.joinpath("fresh_events.json").is_file()


def test_public_study_runner_binds_and_records_explicit_finite_resource_limits(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A large offline study can declare enforced limits without changing its data authority."""
    expanded = _event_grouped_corpus(10)
    ancestor = _corpus_prefix(expanded, 5)
    store = PolymarketCorpusStore(tmp_path / "corpus")
    expanded_ref = store.retain(expanded).ref
    ancestor_ref = store.retain(ancestor).ref
    source_path = tmp_path / "bounded.py"
    source_path.write_text('result = structured_return("Bounded.", {"ok": True})')
    receipt_directory = tmp_path / "bounded-receipts"

    status = run_corpus_studies.main(
        [
            "--snapshot-sha256",
            expanded_ref.content_sha256,
            "--snapshot-size",
            str(expanded_ref.size_bytes),
            "--ancestor-snapshot-sha256",
            ancestor_ref.content_sha256,
            "--ancestor-snapshot-size",
            str(ancestor_ref.size_bytes),
            "--workspace",
            str(store.root),
            "--source",
            str(source_path),
            "--receipt-directory",
            str(receipt_directory),
            "--session-id",
            "bounded-replication",
            "--wall-time-seconds",
            "12.5",
            "--max-memory-bytes",
            "700000000",
            "--max-inline-bytes",
            "300000",
            "--max-result-bytes",
            "400000",
        ]
    )
    receipt = json.loads(capsys.readouterr().out)["receipts"][0]

    assert status == 0
    assert receipt["resource_limits"] == {
        "wall_time_seconds": 12.5,
        "max_source_bytes": ResourceLimits().max_source_bytes,
        "max_inline_bytes": 300_000,
        "max_output_bytes": ResourceLimits().max_output_bytes,
        "max_result_bytes": 400_000,
        "max_memory_bytes": 700_000_000,
    }


def test_public_study_runner_rejects_nonpositive_resource_limits() -> None:
    """An explicit zero cannot silently restore a default or become an unbounded sentinel."""
    arguments = run_corpus_studies.build_parser().parse_args(
        [
            "--snapshot-sha256",
            "a" * 64,
            "--snapshot-size",
            "1",
            "--workspace",
            "/unused/corpus",
            "--source",
            "/unused/source.py",
            "--receipt-directory",
            "/unused/receipts",
            "--max-memory-bytes",
            "0",
        ]
    )

    with pytest.raises(ValueError, match="byte limits"):
        run_corpus_studies._resource_limits(arguments)  # noqa: SLF001
