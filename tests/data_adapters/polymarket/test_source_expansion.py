"""Causal tests for exact public Polymarket source expansion."""

# ruff: noqa: D103, S106

from __future__ import annotations

import io
import json
import urllib.request
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, ClassVar, Self, cast

import pytest

from research_agent.cli import main
from research_agent.data_adapters.polymarket.source_expansion import (
    PolymarketPriceHistoryNeed,
    PolymarketSourceExpansionError,
    expand_scouted_price_history,
    price_history_search_request,
    register_retained_price_history,
)
from research_agent.data_foundation import BoundaryStatus, InformationSetBuilder
from research_agent.data_workspace import (
    DataWorkspace,
    RecordedSourceScoutProvider,
    ScoutingStatus,
    SourceScoutingReportRef,
    SourceScoutingService,
)

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.capture import CaptureFixture
    from _pytest.monkeypatch import MonkeyPatch

    from research_agent.data_workspace.workspace import JsonValue

START = datetime(2024, 1, 1, tzinfo=UTC)
END = START + timedelta(hours=1)
EXPECTED_OBSERVATIONS = 3


class _Headers:
    def __init__(self, size: int) -> None:
        self._size = size

    def get(self, name: str) -> str | None:
        return str(self._size) if name.casefold() == "content-length" else None

    def get_content_type(self) -> str:
        return "application/json"


class _Response(io.BytesIO):
    status = 200

    def __init__(self, body: bytes, url: str) -> None:
        super().__init__(body)
        self.headers = _Headers(len(body))
        self._url = url

    def geturl(self) -> str:
        return self._url

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class _Opener:
    calls: ClassVar[list[str]] = []
    user_agents: ClassVar[list[str | None]] = []
    body: ClassVar[bytes]

    def open(self, request: urllib.request.Request, *, timeout: float) -> _Response:
        del timeout
        url = request.full_url
        type(self).calls.append(url)
        type(self).user_agents.append(request.get_header("User-agent"))
        return _Response(type(self).body, url)


def _need() -> PolymarketPriceHistoryNeed:
    return PolymarketPriceHistoryNeed(
        environment_id="polymarket-production-readonly",
        market_id="market-1",
        event_id="event-1",
        outcome_index=0,
        outcome_token="12345678901234567890",
        start_time=START,
        end_time=END,
        fidelity_minutes=15,
    )


def _candidate(url: str) -> dict[str, JsonValue]:
    return {
        "title": "Official CLOB price history",
        "resource_url": url,
        "landing_page_url": (
            "https://docs.polymarket.com/api-reference/markets/get-prices-history"
        ),
        "publisher": "Polymarket",
        "description": "Documented historical probability samples for one outcome token.",
        "why_relevant": "Adds an exact public probability path for a development hypothesis.",
        "temporal_coverage": "Exact requested bounds; verify from retained response.",
        "frequency": "Exact requested fidelity; endpoint sampling behavior remains caveated.",
        "license": "Polymarket public API terms; operator must review.",
        "access_notes": "Public HTTPS GET without credentials.",
        "risks": ["Samples are not trades or executable quotes."],
        "evidence_urls": ["https://docs.polymarket.com/api-reference/markets/get-prices-history"],
    }


def _report(
    workspace: DataWorkspace,
    need: PolymarketPriceHistoryNeed,
    *,
    url: str | None = None,
) -> tuple[SourceScoutingReportRef, str]:
    provider = RecordedSourceScoutProvider(
        provider_id="recorded-official-docs-scout@1",
        response={
            "schema_version": "source-scout-response/v1",
            "candidates": [_candidate(need.resource_url if url is None else url)],
        },
    )
    receipt = SourceScoutingService(workspace, provider).scout(
        price_history_search_request(need, research_question="Does public price history help?"),
        idempotency_key=f"exact-price-history-need:{need.need_id}",
    )
    assert receipt.status is ScoutingStatus.SUCCEEDED
    assert receipt.report_ref is not None
    return receipt.report_ref, receipt.report_ref.candidate_ids[0]


def _install_response(monkeypatch: MonkeyPatch, payload: object) -> None:
    _Opener.calls = []
    _Opener.user_agents = []
    _Opener.body = json.dumps(payload).encode()

    def build_opener(*handlers: object) -> _Opener:
        del handlers
        return _Opener()

    monkeypatch.setattr(urllib.request, "build_opener", build_opener)


def test_exact_selected_source_becomes_a_time_legal_registered_dataset(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    need = _need()
    payload = {
        "history": [
            {"t": need.start_ts, "p": 0.41},
            {"t": need.start_ts + 900, "p": 0.44},
            {"t": need.start_ts + 1800, "p": 0.47},
        ]
    }
    _install_response(monkeypatch, payload)
    workspace = DataWorkspace(tmp_path / "data")
    report_ref, candidate_id = _report(workspace, need)

    expansion = expand_scouted_price_history(
        workspace,
        report_ref=report_ref,
        candidate_id=candidate_id,
        need=need,
    )

    assert _Opener.calls == [need.resource_url]
    assert _Opener.user_agents == ["ChronosResearch/0.1 (+https://github.com/)"]
    assert len(expansion.registered.dataset.observations) == EXPECTED_OBSERVATIONS
    fetch_receipt = expansion.scouted_fetch.fetch_receipt
    assert fetch_receipt is not None
    assert fetch_receipt.snapshot_ref is not None
    assert workspace.verify(fetch_receipt.snapshot_ref).healthy
    field = expansion.registered.dataset.schema.field_ref("market_probability")
    before = InformationSetBuilder().build(
        expansion.catalog.snapshot,
        decision_time=START - timedelta(microseconds=1),
        requested_fields=(field,),
    )
    at_start = InformationSetBuilder().build(
        expansion.catalog.snapshot,
        decision_time=START,
        requested_fields=(field,),
    )
    assert before.status is BoundaryStatus.INSUFFICIENT
    assert at_start.status is BoundaryStatus.READY
    assert len(at_start.observations) == 1
    public = expansion.as_dict()
    assert public["observation_count"] == EXPECTED_OBSERVATIONS
    assert public["sample_values_emitted"] is False
    assert "0.41" not in json.dumps(public)

    replay = expand_scouted_price_history(
        workspace,
        report_ref=report_ref,
        candidate_id=candidate_id,
        need=need,
    )
    assert replay.as_dict() == public

    fetch_receipt = expansion.scouted_fetch.fetch_receipt
    assert fetch_receipt is not None
    assert fetch_receipt.snapshot_ref is not None
    reopened = register_retained_price_history(
        workspace,
        need=need,
        source_ref_uri=fetch_receipt.snapshot_ref.uri,
        derived_ref_uri=expansion.registered.derived_ref_uri,
    )
    assert reopened == expansion.registered


def test_retained_registration_rejects_a_different_exact_need(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    need = _need()
    _install_response(
        monkeypatch,
        {"history": [{"t": need.start_ts, "p": 0.41}]},
    )
    workspace = DataWorkspace(tmp_path / "data")
    report_ref, candidate_id = _report(workspace, need)
    expansion = expand_scouted_price_history(
        workspace,
        report_ref=report_ref,
        candidate_id=candidate_id,
        need=need,
    )
    fetch_receipt = expansion.scouted_fetch.fetch_receipt
    assert fetch_receipt is not None
    assert fetch_receipt.snapshot_ref is not None
    changed_need = PolymarketPriceHistoryNeed(
        environment_id=need.environment_id,
        market_id="changed-market",
        event_id=need.event_id,
        outcome_index=need.outcome_index,
        outcome_token=need.outcome_token,
        start_time=need.start_time,
        end_time=need.end_time,
        fidelity_minutes=need.fidelity_minutes,
    )

    with pytest.raises(PolymarketSourceExpansionError, match="does not match"):
        register_retained_price_history(
            workspace,
            need=changed_need,
            source_ref_uri=fetch_receipt.snapshot_ref.uri,
            derived_ref_uri=expansion.registered.derived_ref_uri,
        )


def test_changed_token_url_is_denied_before_any_network_contact(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    need = _need()
    _install_response(monkeypatch, {"history": [{"t": need.start_ts, "p": 0.5}]})
    workspace = DataWorkspace(tmp_path / "data")
    mutated_url = need.resource_url.replace(need.outcome_token, "999999")
    report_ref, candidate_id = _report(workspace, need, url=mutated_url)

    with pytest.raises(PolymarketSourceExpansionError, match="does not exactly match"):
        expand_scouted_price_history(
            workspace,
            report_ref=report_ref,
            candidate_id=candidate_id,
            need=need,
        )

    assert _Opener.calls == []


def test_distinct_needs_receive_distinct_dataset_schema_identity(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    first_need = _need()
    second_need = PolymarketPriceHistoryNeed(
        environment_id=first_need.environment_id,
        market_id="market-2",
        event_id="event-2",
        outcome_index=first_need.outcome_index,
        outcome_token="98765432109876543210",
        start_time=first_need.start_time,
        end_time=first_need.end_time,
        fidelity_minutes=first_need.fidelity_minutes,
    )
    _install_response(
        monkeypatch,
        {"history": [{"t": first_need.start_ts, "p": 0.5}]},
    )
    workspace = DataWorkspace(tmp_path / "data")
    first_report, first_candidate = _report(workspace, first_need)
    second_report, second_candidate = _report(workspace, second_need)

    first = expand_scouted_price_history(
        workspace,
        report_ref=first_report,
        candidate_id=first_candidate,
        need=first_need,
    )
    second = expand_scouted_price_history(
        workspace,
        report_ref=second_report,
        candidate_id=second_candidate,
        need=second_need,
    )

    assert first.registered.dataset.schema.dataset_id != second.registered.dataset.schema.dataset_id


@pytest.mark.parametrize(
    "payload",
    [
        {"history": []},
        {"history": [{"t": int(END.timestamp()) + 1, "p": 0.5}]},
        {"history": [{"t": int(START.timestamp()), "p": 1.01}]},
        {
            "history": [
                {"t": int(START.timestamp()) + 10, "p": 0.5},
                {"t": int(START.timestamp()), "p": 0.4},
            ]
        },
        {"history": [{"t": int(START.timestamp()), "p": 0.5, "extra": 1}]},
    ],
)
def test_malformed_or_time_illegal_response_never_registers(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    payload: object,
) -> None:
    need = _need()
    _install_response(monkeypatch, payload)
    workspace = DataWorkspace(tmp_path / "data")
    report_ref, candidate_id = _report(workspace, need)

    with pytest.raises(PolymarketSourceExpansionError, match="strict derivation"):
        expand_scouted_price_history(
            workspace,
            report_ref=report_ref,
            candidate_id=candidate_id,
            need=need,
        )


def test_public_request_command_is_exact_and_contains_no_data_values(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    need_path = tmp_path / "need.json"
    need_path.write_text(json.dumps(_need().as_dict()))

    assert (
        main(
            (
                "data",
                "polymarket-price-history-request",
                "--need",
                str(need_path),
                "--research-question",
                "Can another public probability series improve calibration?",
            )
        )
        == 0
    )
    payload = cast("dict[str, object]", json.loads(capsys.readouterr().out))
    assert payload["schema_version"] == "source-search-request/v1"
    assert "candidates" not in payload
    assert "history" not in payload


def test_public_registration_command_emits_only_sanitized_evidence(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    need = _need()
    _install_response(
        monkeypatch,
        {"history": [{"t": need.start_ts, "p": 0.37}]},
    )
    workspace_path = tmp_path / "data"
    workspace = DataWorkspace(workspace_path)
    report_ref, candidate_id = _report(workspace, need)
    need_path = tmp_path / "need.json"
    need_path.write_text(json.dumps(need.as_dict()))

    assert (
        main(
            (
                "data",
                "register-polymarket-price-history",
                "--workspace",
                str(workspace_path),
                "--need",
                str(need_path),
                "--report",
                report_ref.uri,
                "--candidate",
                candidate_id,
            )
        )
        == 0
    )
    payload = cast("dict[str, object]", json.loads(capsys.readouterr().out))
    assert payload["status"] == "succeeded"
    assert payload["observation_count"] == 1
    assert payload["sample_values_emitted"] is False
    assert "0.37" not in json.dumps(payload)


def test_corrupted_retained_source_cannot_be_reused_for_registration(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    need = _need()
    _install_response(
        monkeypatch,
        {"history": [{"t": need.start_ts, "p": 0.5}]},
    )
    workspace = DataWorkspace(tmp_path / "data")
    report_ref, candidate_id = _report(workspace, need)
    expansion = expand_scouted_price_history(
        workspace,
        report_ref=report_ref,
        candidate_id=candidate_id,
        need=need,
    )
    fetch_receipt = expansion.scouted_fetch.fetch_receipt
    assert fetch_receipt is not None
    assert fetch_receipt.snapshot_ref is not None
    object_path = workspace.root / "objects" / fetch_receipt.snapshot_ref.content_sha256
    object_path.write_bytes(b"corrupted")

    with pytest.raises(PolymarketSourceExpansionError, match="acquisition failed"):
        expand_scouted_price_history(
            workspace,
            report_ref=report_ref,
            candidate_id=candidate_id,
            need=need,
        )
