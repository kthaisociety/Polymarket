"""Causal boundary tests for provider-neutral source scouting."""

# ruff: noqa: D103

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING, ClassVar, cast

import pytest

from research_agent.cli import main
from research_agent.data_workspace import DataWorkspace, FetchStatus
from research_agent.data_workspace.scouting import (
    RecordedSourceScoutProvider,
    ScoutedFetchStatus,
    ScoutingConflictError,
    ScoutingResolutionError,
    ScoutingStatus,
    SourceScoutingReceipt,
    SourceScoutingReportRef,
    SourceScoutingService,
    SourceSearchRequest,
)

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping
    from pathlib import Path

    from _pytest.capture import CaptureFixture

    from research_agent.data_workspace.workspace import JsonValue


def _recorded(
    response: Mapping[str, JsonValue] | None = None,
    *,
    provider_id: str = "test-web-scout@1",
    error_code: str | None = None,
) -> RecordedSourceScoutProvider:
    return RecordedSourceScoutProvider(
        provider_id=provider_id,
        response=response,
        error_code=error_code,
    )


def _request(*, question: str = "What predicts regional waiting times?") -> SourceSearchRequest:
    return SourceSearchRequest(
        research_question=question,
        data_need="Regional quarterly capacity and demand predictors with historical coverage.",
        search_queries=("Sweden regional healthcare capacity quarterly open data",),
        requirements=(
            "official or documented publisher",
            "machine-readable resource",
            "historical temporal coverage",
        ),
        max_candidates=4,
    )


def _candidate(
    resource_url: str,
    *,
    title: str = "Regional capacity API",
    publisher: str = "Official publisher",
) -> dict[str, JsonValue]:
    return {
        "title": title,
        "resource_url": resource_url,
        "landing_page_url": "https://publisher.example/datasets/capacity",
        "publisher": publisher,
        "description": "Quarterly regional capacity observations.",
        "why_relevant": "Could test whether capacity predicts later waiting-time outcomes.",
        "temporal_coverage": "2010 onward; unverified until acquisition and profiling",
        "frequency": "quarterly; unverified until acquisition and profiling",
        "license": "open-data terms; verify at source",
        "access_notes": "Direct machine-readable endpoint.",
        "risks": ["release timestamps and historical revisions are not yet established"],
        "evidence_urls": ["https://publisher.example/docs/capacity-api"],
    }


def _response(*candidates: dict[str, JsonValue]) -> dict[str, JsonValue]:
    return {"schema_version": "source-scout-response/v1", "candidates": list(candidates)}


def test_scouting_is_proposal_only_and_one_seam_handles_different_data_needs(
    tmp_path: Path,
) -> None:
    workspace = DataWorkspace(tmp_path / "data")
    provider = _recorded(_response(_candidate("https://publisher.example/api/capacity.csv")))
    service = SourceScoutingService(workspace, provider)

    waiting_times = service.scout(_request(), idempotency_key="waiting-times")
    insurance = service.scout(
        _request(question="What predicts quarterly claims severity?"),
        idempotency_key="claims-severity",
    )

    assert waiting_times.status is ScoutingStatus.SUCCEEDED
    assert insurance.status is ScoutingStatus.SUCCEEDED
    assert waiting_times.report_ref is not None
    assert insurance.report_ref is not None
    assert waiting_times.report_ref.request_id != insurance.report_ref.request_id
    assert tuple((workspace.root / "manifests" / "source").glob("*.json")) == ()
    assert workspace.search("") == ()
    assert waiting_times.as_dict()["scientific_authority"] == "NONE_PROPOSAL_ONLY"
    assert waiting_times.as_dict()["provider_identity_authority"] == "UNVERIFIED_CALLER_LABEL"
    assert waiting_times.as_dict()["registered_dataset_refs"] == []


def test_service_rejects_executable_provider_objects_without_calling_them(tmp_path: Path) -> None:
    class ExecutableProvider:
        provider_id = "malicious-provider@1"
        called = False

        def search(self, request: SourceSearchRequest) -> Mapping[str, JsonValue]:
            _ = request
            self.called = True
            return _response(_candidate("https://publisher.example/data.csv"))

    executable = ExecutableProvider()

    with pytest.raises(TypeError, match="passive recorded responses"):
        SourceScoutingService(
            DataWorkspace(tmp_path / "data"),
            cast("RecordedSourceScoutProvider", executable),
        )

    assert executable.called is False


@pytest.mark.parametrize(
    ("extra_key", "extra_value"),
    [
        ("available_at", "2010-01-01T00:00:00Z"),
        ("snapshot_ref", "source:" + "a" * 64),
        ("scientific_authority", "VALIDATED"),
        ("response_preview", "1,2,3"),
    ],
)
def test_provider_cannot_smuggle_data_or_scientific_authority_into_proposals(
    tmp_path: Path,
    extra_key: str,
    extra_value: str,
) -> None:
    candidate = _candidate("https://publisher.example/api/capacity.csv")
    candidate[extra_key] = extra_value
    provider = _recorded(_response(candidate))
    service = SourceScoutingService(DataWorkspace(tmp_path / "data"), provider)

    receipt = service.scout(_request(), idempotency_key=f"unknown-{extra_key}")

    assert receipt.status is ScoutingStatus.FAILED
    assert receipt.report_ref is None
    assert receipt.error_code == "INVALID_PROVIDER_RESPONSE"


@pytest.mark.parametrize(
    "resource_url",
    [
        "https://user:password@publisher.example/data.csv",
        "https://publisher.example/data.csv?api_key=secret-sentinel",
        "https://publisher.example/data.csv?q=FAKE_SECRET",
        "file:///tmp/invented.csv",
        "https://publisher.example/data.csv#local-fragment",
    ],
)
def test_candidate_resource_url_must_be_public_http_without_secret_material(
    tmp_path: Path,
    resource_url: str,
) -> None:
    service = SourceScoutingService(
        DataWorkspace(tmp_path / "data"),
        _recorded(_response(_candidate(resource_url))),
    )

    receipt = service.scout(_request(), idempotency_key="secret-url")

    assert receipt.status is ScoutingStatus.FAILED
    assert receipt.report_ref is None
    public_text = "".join(path.read_text() for path in service.ledger_root.rglob("*.json"))
    assert "secret-sentinel" not in public_text
    assert "password" not in public_text


@pytest.mark.parametrize(
    ("field", "secret_text"),
    [
        ("description", "authorization: Bearer fake-credential"),
        ("access_notes", "api_key=fake-credential"),
        ("why_relevant", "password: fake-credential"),
    ],
)
def test_obvious_credential_assignments_are_not_retained_in_free_text(
    tmp_path: Path,
    field: str,
    secret_text: str,
) -> None:
    candidate = _candidate("https://publisher.example/data.csv")
    candidate[field] = secret_text
    service = SourceScoutingService(
        DataWorkspace(tmp_path / "data"),
        _recorded(_response(candidate)),
    )

    receipt = service.scout(_request(), idempotency_key=f"secret-text-{field}")

    assert receipt.status is ScoutingStatus.FAILED
    assert secret_text not in "".join(
        path.read_text() for path in service.ledger_root.rglob("*.json")
    )


def test_untrusted_numeric_or_promotion_claims_cannot_become_data_or_authority(
    tmp_path: Path,
) -> None:
    candidate = _candidate("https://publisher.example/data.csv")
    candidate["description"] = "Claims region SE has value 73 and calls it a validated finding."
    workspace = DataWorkspace(tmp_path / "data")
    service = SourceScoutingService(workspace, _recorded(_response(candidate)))

    receipt = service.scout(_request(), idempotency_key="untrusted-claims")

    assert receipt.status is ScoutingStatus.SUCCEEDED
    assert receipt.report_ref is not None
    report = service.resolve_report(receipt.report_ref)
    assert "value 73" in report.candidates[0].description
    assert report.as_dict()["scientific_authority"] == "NONE_PROPOSAL_ONLY"
    assert report.as_dict()["source_snapshot_refs"] == []
    assert tuple((workspace.root / "manifests" / "source").glob("*.json")) == ()


def test_exact_retry_and_restart_replay_retained_response(tmp_path: Path) -> None:
    workspace = DataWorkspace(tmp_path / "data")
    provider = _recorded(_response(_candidate("https://publisher.example/api/capacity.csv")))
    first_service = SourceScoutingService(workspace, provider)
    first = first_service.scout(_request(), idempotency_key="stable-operation")
    replay = first_service.scout(_request(), idempotency_key="stable-operation")

    assert replay == first
    changed_response = _recorded(
        _response(_candidate("https://publisher.example/api/a-different-source.csv")),
        provider_id=provider.provider_id,
    )
    restarted = SourceScoutingService(DataWorkspace(workspace.root), changed_response)
    after_restart = restarted.scout(_request(), idempotency_key="stable-operation")

    assert after_restart == first
    assert first.report_ref is not None
    assert restarted.resolve_report(first.report_ref) == first_service.resolve_report(
        first.report_ref
    )


def test_concurrent_services_converge_on_one_operation(tmp_path: Path) -> None:
    workspace_path = tmp_path / "data"
    provider = _recorded(_response(_candidate("https://publisher.example/api/capacity.csv")))
    services = [
        SourceScoutingService(DataWorkspace(workspace_path), provider),
        SourceScoutingService(DataWorkspace(workspace_path), provider),
    ]
    receipts: list[SourceScoutingReceipt] = []

    def execute(service: SourceScoutingService) -> None:
        receipts.append(service.scout(_request(), idempotency_key="one-concurrent-search"))

    threads = [threading.Thread(target=execute, args=(service,)) for service in services]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert receipts[0] == receipts[1]
    assert len(tuple((workspace_path / "scouting" / "operations").glob("*.json"))) == 1


def test_changed_request_under_same_provider_and_idempotency_key_conflicts(tmp_path: Path) -> None:
    provider = _recorded(_response(_candidate("https://publisher.example/api/capacity.csv")))
    service = SourceScoutingService(DataWorkspace(tmp_path / "data"), provider)
    service.scout(_request(), idempotency_key="one-logical-search")

    with pytest.raises(ScoutingConflictError, match="different scouting request"):
        service.scout(
            _request(question="A changed research question"),
            idempotency_key="one-logical-search",
        )


def test_failed_external_attempt_is_preserved_and_replayed_without_fetch(tmp_path: Path) -> None:
    provider = _recorded(error_code="EXTERNAL_SCOUT_FAILED")
    workspace = DataWorkspace(tmp_path / "data")
    service = SourceScoutingService(workspace, provider)

    first = service.scout(_request(), idempotency_key="failed-search")
    replay = service.scout(_request(), idempotency_key="failed-search")

    assert first == replay
    assert first.status is ScoutingStatus.FAILED
    assert first.error_code == "EXTERNAL_SCOUT_FAILED"
    assert first.report_ref is None
    assert tuple((workspace.root / "manifests" / "source").glob("*.json")) == ()


class _CandidateServer(BaseHTTPRequestHandler):
    requested_paths: ClassVar[list[str]] = []

    def do_GET(self) -> None:
        type(self).requested_paths.append(self.path)
        body = b"region,quarter,value\nA,2024Q1,1\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/csv")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        _ = (format, args)


@pytest.fixture
def candidate_server() -> Iterator[str]:
    _CandidateServer.requested_paths = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _CandidateServer)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host = cast("str", server.server_address[0])
        port = server.server_address[1]
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_only_exact_selected_candidate_reaches_existing_fetch_boundary(
    tmp_path: Path,
    candidate_server: str,
) -> None:
    workspace = DataWorkspace(tmp_path / "data")
    provider = _recorded(
        _response(
            _candidate(f"{candidate_server}/selected.csv", title="Selected source"),
            _candidate(f"{candidate_server}/unselected.csv", title="Unselected source"),
        )
    )
    service = SourceScoutingService(workspace, provider)
    scouting = service.scout(_request(), idempotency_key="select-one")
    assert scouting.report_ref is not None
    report = service.resolve_report(scouting.report_ref)

    acquired = service.acquire_candidate(
        scouting.report_ref,
        candidate_id=report.candidates[0].candidate_id,
    )

    assert acquired.status is ScoutedFetchStatus.SUCCEEDED
    assert acquired.fetch_receipt is not None
    assert acquired.fetch_receipt.status is FetchStatus.SUCCEEDED
    assert acquired.fetch_receipt.snapshot_ref is not None
    assert _CandidateServer.requested_paths == ["/selected.csv"]
    assert workspace.verify(acquired.fetch_receipt.snapshot_ref).healthy
    assert acquired.as_dict()["registered_dataset_refs"] == []
    assert acquired.as_dict()["scientific_authority"] == "NONE_ACQUISITION_ONLY"


def test_forged_or_changed_report_is_denied_before_any_http_request(
    tmp_path: Path,
    candidate_server: str,
) -> None:
    workspace = DataWorkspace(tmp_path / "data")
    service = SourceScoutingService(
        workspace,
        _recorded(_response(_candidate(f"{candidate_server}/real.csv", title="Real source"))),
    )
    scouting = service.scout(_request(), idempotency_key="real-report")
    assert scouting.report_ref is not None
    forged = SourceScoutingReportRef(
        report_id="f" * 64,
        request_id=scouting.report_ref.request_id,
        provider_id=scouting.report_ref.provider_id,
        candidate_ids=scouting.report_ref.candidate_ids,
    )

    denied = service.acquire_candidate(forged, candidate_id=forged.candidate_ids[0])
    wrong_candidate = service.acquire_candidate(
        scouting.report_ref,
        candidate_id="e" * 64,
    )

    assert denied.status is ScoutedFetchStatus.DENIED
    assert denied.error_code == "UNISSUED_SCOUTING_REPORT"
    assert wrong_candidate.status is ScoutedFetchStatus.DENIED
    assert wrong_candidate.error_code == "UNKNOWN_SOURCE_CANDIDATE"
    assert _CandidateServer.requested_paths == []
    assert tuple((workspace.root / "manifests" / "source").glob("*.json")) == ()


def test_report_uri_cannot_escape_the_workspace_ledger(tmp_path: Path) -> None:
    service = SourceScoutingService(DataWorkspace(tmp_path / "data"))
    path_like_identity = "../" + "a" * 61

    with pytest.raises(ScoutingResolutionError, match="invalid scouting report URI"):
        service.resolve_report_uri("scouting:" + path_like_identity)


def test_report_parent_symlink_swap_cannot_redirect_publication(tmp_path: Path) -> None:
    workspace = DataWorkspace(tmp_path / "data")
    service = SourceScoutingService(
        workspace,
        _recorded(_response(_candidate("https://publisher.example/data.csv"))),
    )
    reports = service.ledger_root / "reports"
    reports.rename(service.ledger_root / "reports-original")
    external = tmp_path / "external"
    external.mkdir()
    reports.symlink_to(external, target_is_directory=True)

    with pytest.raises(OSError, match=r"symbolic links|Not a directory"):
        service.scout(_request(), idempotency_key="symlink-swap")

    assert tuple(external.iterdir()) == ()


def test_ledger_root_symlink_swap_stays_on_anchored_directory(
    tmp_path: Path,
    candidate_server: str,
) -> None:
    workspace = DataWorkspace(tmp_path / "data")
    service = SourceScoutingService(
        workspace,
        _recorded(_response(_candidate(f"{candidate_server}/anchored.csv"))),
    )
    first = service.scout(_request(), idempotency_key="before-root-swap")
    assert first.report_ref is not None
    original = workspace.root / "scouting-original"
    service.ledger_root.rename(original)
    external = tmp_path / "external-root"
    external.mkdir()
    for child in ("requests", "reports", "operations", "acquisitions"):
        (external / child).mkdir()
    service.ledger_root.symlink_to(external, target_is_directory=True)

    replay = service.scout(_request(), idempotency_key="before-root-swap")
    second = service.scout(
        _request(question="A need recorded after root replacement"),
        idempotency_key="after-root-swap",
    )
    acquired = service.acquire_candidate(
        first.report_ref,
        candidate_id=first.report_ref.candidate_ids[0],
    )

    assert replay == first
    assert second.status is ScoutingStatus.SUCCEEDED
    assert acquired.status is ScoutedFetchStatus.SUCCEEDED
    assert _CandidateServer.requested_paths == ["/anchored.csv"]
    assert tuple(external.rglob("*.json")) == ()
    assert tuple((original / "requests").glob("*.json"))
    assert tuple((original / "reports").glob("*.json"))
    assert tuple((original / "operations").glob("*.json"))
    assert tuple((original / "acquisitions").glob("*.json"))
    with pytest.raises(ValueError, match="real directories"):
        SourceScoutingService(DataWorkspace(workspace.root))


def test_changed_recorded_timestamp_invalidates_retained_report(tmp_path: Path) -> None:
    service = SourceScoutingService(
        DataWorkspace(tmp_path / "data"),
        _recorded(_response(_candidate("https://publisher.example/data.csv"))),
    )
    receipt = service.scout(_request(), idempotency_key="timestamp-integrity")
    assert receipt.report_ref is not None
    path = service.ledger_root / "reports" / f"{receipt.report_ref.report_id}.json"
    value = cast("dict[str, object]", json.loads(path.read_text()))
    value["recorded_at"] = "2000-01-01T00:00:00+00:00"
    path.write_text(json.dumps(value))

    with pytest.raises(ScoutingResolutionError, match="not issued"):
        service.resolve_report(receipt.report_ref)


def test_report_uri_content_substitution_denies_cli_before_fetch(
    tmp_path: Path,
    candidate_server: str,
    capsys: CaptureFixture[str],
) -> None:
    workspace_path = tmp_path / "data"
    first_service = SourceScoutingService(
        DataWorkspace(workspace_path),
        _recorded(
            _response(_candidate(f"{candidate_server}/first.csv")),
            provider_id="recorded-scout@1",
        ),
    )
    first = first_service.scout(_request(), idempotency_key="first-report")
    second_service = SourceScoutingService(
        DataWorkspace(workspace_path),
        _recorded(
            _response(_candidate(f"{candidate_server}/second.csv")),
            provider_id="recorded-scout@1",
        ),
    )
    second = second_service.scout(
        _request(question="A second source need"),
        idempotency_key="second-report",
    )
    assert first.report_ref is not None
    assert second.report_ref is not None
    reports = first_service.ledger_root / "reports"
    first_path = reports / f"{first.report_ref.report_id}.json"
    second_path = reports / f"{second.report_ref.report_id}.json"
    first_path.write_bytes(second_path.read_bytes())

    exit_code = main(
        (
            "data",
            "acquire-scouted",
            "--workspace",
            str(workspace_path),
            "--report",
            first.report_ref.uri,
            "--candidate",
            second.report_ref.candidate_ids[0],
        )
    )

    command_error = 2
    assert exit_code == command_error
    assert json.loads(capsys.readouterr().out)["error_code"] == "DATA_COMMAND_FAILED"
    assert _CandidateServer.requested_paths == []


def test_cli_records_external_subagent_result_then_acquires_exact_candidate(
    tmp_path: Path,
    candidate_server: str,
    capsys: CaptureFixture[str],
) -> None:
    workspace = tmp_path / "data"
    request_path = tmp_path / "request.json"
    response_path = tmp_path / "response.json"
    request_path.write_text(json.dumps(_request().as_dict()))
    response_path.write_text(
        json.dumps(_response(_candidate(f"{candidate_server}/from-subagent.csv")))
    )

    assert (
        main(
            (
                "data",
                "scout",
                "--workspace",
                str(workspace),
                "--request",
                str(request_path),
                "--response",
                str(response_path),
                "--provider-id",
                "codex-scout-adapter@1",
                "--idempotency-key",
                "cli-scout",
            )
        )
        == 0
    )
    scouting_payload = cast("dict[str, object]", json.loads(capsys.readouterr().out))
    report_ref = cast("dict[str, object]", scouting_payload["report_ref"])
    candidate_id = cast("list[str]", report_ref["candidate_ids"])[0]

    assert _CandidateServer.requested_paths == []
    assert (
        main(
            (
                "data",
                "acquire-scouted",
                "--workspace",
                str(workspace),
                "--report",
                cast("str", report_ref["uri"]),
                "--candidate",
                candidate_id,
            )
        )
        == 0
    )
    acquisition = cast("dict[str, object]", json.loads(capsys.readouterr().out))
    assert acquisition["status"] == "succeeded"
    assert acquisition["registered_dataset_refs"] == []
    assert _CandidateServer.requested_paths == ["/from-subagent.csv"]
