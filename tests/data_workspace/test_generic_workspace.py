"""Causal contracts for the source-agnostic content-addressed data workspace."""

# ruff: noqa: D103, S105

from __future__ import annotations

import json
import shutil
import threading
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING, cast

import pytest

from research_agent.data_workspace import (
    DataWorkspace,
    DerivedDatasetRef,
    DeriveStatus,
    FetchRequest,
    FetchStatus,
    SourceSnapshotRef,
)

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


class _TwoShapeApi(BaseHTTPRequestHandler):
    json_body = b'{"rows":[{"region":"A","value":1},{"region":"B","value":2}]}'
    csv_body = b"region,value\nA,1\nB,2\n"
    mutable_body = b'{"version":1}'
    captured_authorization = ""
    captured_body = b""
    redirected_target_calls = 0

    def do_GET(self) -> None:
        if self.path == "/redirect":
            self.send_response(302)
            _, port = cast("tuple[str, int]", self.server.server_address)
            self.send_header("Location", f"http://localhost:{port}/redirect-target")
            self.end_headers()
            return
        if self.path.startswith("/redirect-target"):
            type(self).redirected_target_calls += 1
            body = self.json_body
        elif self.path.startswith("/nested"):
            body = self.json_body
        elif self.path.startswith("/mutable"):
            body = self.mutable_body
        else:
            body = self.csv_body
        self.send_response(200)
        media_type = "application/json" if body == self.json_body else "text/csv"
        self.send_header("Content-Type", media_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        size = int(self.headers.get("Content-Length", "0"))
        type(self).captured_authorization = self.headers.get("Authorization", "")
        type(self).captured_body = self.rfile.read(size)
        self.send_response(503)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        _ = (format, args)


@pytest.fixture
def api_server() -> Iterator[str]:
    _TwoShapeApi.mutable_body = b'{"version":1}'
    _TwoShapeApi.redirected_target_calls = 0
    server = ThreadingHTTPServer(("127.0.0.1", 0), _TwoShapeApi)
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


def _fetch(workspace: DataWorkspace, url: str) -> SourceSnapshotRef:
    receipt = workspace.fetch(FetchRequest(url=url))
    assert receipt.status is FetchStatus.SUCCEEDED
    assert receipt.snapshot_ref is not None
    return receipt.snapshot_ref


def test_two_structurally_different_http_apis_use_the_same_generic_boundary(
    tmp_path: Path, api_server: str
) -> None:
    workspace = DataWorkspace(tmp_path / "data")

    nested = _fetch(workspace, f"{api_server}/nested")
    tabular = _fetch(workspace, f"{api_server}/tabular")

    assert nested.content_sha256 != tabular.content_sha256
    assert workspace.verify(nested).healthy is True
    assert workspace.verify(tabular).healthy is True
    assert workspace.inspect(nested).manifest_type == "source_snapshot"
    assert workspace.inspect(tabular).manifest_type == "source_snapshot"


def test_redirect_policy_refuses_contact_before_an_unapproved_target(
    tmp_path: Path, api_server: str
) -> None:
    workspace = DataWorkspace(tmp_path / "data")
    host = cast("str", urllib.parse.urlsplit(api_server).hostname)

    receipt = workspace.fetch(
        FetchRequest(
            url=f"{api_server}/redirect",
            allowed_redirect_hosts=(host,),
            permit_redirects=False,
        )
    )

    assert receipt.status is FetchStatus.FAILED
    assert receipt.error_code == "HTTP_ACQUISITION_FAILED"
    assert _TwoShapeApi.redirected_target_calls == 0


def test_fetch_publishes_no_values_and_byte_mutation_fails_verification(
    tmp_path: Path, api_server: str
) -> None:
    workspace = DataWorkspace(tmp_path / "data")
    receipt = workspace.fetch(FetchRequest(url=f"{api_server}/nested"))
    assert receipt.status is FetchStatus.SUCCEEDED
    assert receipt.snapshot_ref is not None
    assert "rows" not in json.dumps(receipt.as_dict())

    object_path = workspace.root / "objects" / receipt.snapshot_ref.content_sha256
    object_path.write_bytes(b"mutated response")

    verification = workspace.verify(receipt.snapshot_ref)
    assert verification.healthy is False
    assert verification.error_code == "CONTENT_DIGEST_MISMATCH"
    retry = workspace.fetch(FetchRequest(url=f"{api_server}/nested"))
    assert retry.status is FetchStatus.FAILED
    assert retry.snapshot_ref is None
    assert retry.error_code == "PUBLICATION_FAILED"


def test_changed_content_gets_distinct_identity_and_oversize_returns_no_ref(
    tmp_path: Path, api_server: str
) -> None:
    workspace = DataWorkspace(tmp_path / "data")
    first = _fetch(workspace, f"{api_server}/mutable")
    _TwoShapeApi.mutable_body = b'{"version":2}'
    second = _fetch(workspace, f"{api_server}/mutable")
    oversized = workspace.fetch(FetchRequest(url=f"{api_server}/nested", max_response_bytes=10))

    assert first.snapshot_id != second.snapshot_id
    assert first.content_sha256 != second.content_sha256
    assert oversized.status is FetchStatus.FAILED
    assert oversized.snapshot_ref is None
    assert oversized.error_code == "RESPONSE_TOO_LARGE"


def test_identity_survives_workspace_move_and_catalog_rebuild(
    tmp_path: Path, api_server: str
) -> None:
    first = DataWorkspace(tmp_path / "first")
    ref = _fetch(first, f"{api_server}/nested")
    shutil.copytree(first.root, tmp_path / "moved")

    restarted = DataWorkspace(tmp_path / "moved")
    assert restarted.resolve(ref.uri) == ref
    assert restarted.rebuild_catalog() == 1
    assert restarted.resolve(ref.uri) == ref
    assert restarted.verify(ref).healthy is True


def test_manifest_tampering_and_symlink_substitution_fail_closed(
    tmp_path: Path, api_server: str
) -> None:
    workspace = DataWorkspace(tmp_path / "data")
    ref = _fetch(workspace, f"{api_server}/nested")
    manifest_path = workspace.root / "manifests" / "source" / f"{ref.snapshot_id}.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["request_sha256"] = "f" * 64
    manifest_path.write_text(json.dumps(manifest))
    assert workspace.verify(ref).error_code == "REFERENCE_MANIFEST_MISMATCH"

    symlink_ref = _fetch(workspace, f"{api_server}/tabular")
    replacement = tmp_path / "replacement"
    replacement.write_bytes(_TwoShapeApi.csv_body)
    object_path = workspace.root / "objects" / symlink_ref.content_sha256
    object_path.unlink()
    object_path.symlink_to(replacement)
    verification = workspace.verify(symlink_ref)
    assert verification.healthy is False


def test_unretained_or_caller_minted_ref_cannot_become_an_authorized_view(tmp_path: Path) -> None:
    workspace = DataWorkspace(tmp_path / "data")
    invented = DerivedDatasetRef(
        dataset_id="0" * 64,
        output_sha256="1" * 64,
        size_bytes=2,
        code_sha256="2" * 64,
        input_ref_ids=("source:" + "3" * 64,),
        parameters_sha256="4" * 64,
        runtime_id="invented",
    )

    with pytest.raises(ValueError, match="verified retained derived dataset"):
        workspace.authorized_json_view(
            invented,
            view_id="invented",
            environment_ref="environment@1",
        )

    authored_only = workspace.derive(
        inputs={},
        source='result = emit({"invented": [999]})',
        parameters={},
    )
    assert authored_only.status is DeriveStatus.DENIED
    assert authored_only.dataset_ref is None
    assert authored_only.error_code == "INPUT_REFERENCE_REQUIRED"

    unretained_input = workspace.derive(
        inputs={"invented": invented},
        source='payload = json_input("invented")\nresult = emit(payload)',
        parameters={},
    )
    assert unretained_input.status is DeriveStatus.FAILED
    assert unretained_input.dataset_ref is None
    assert unretained_input.error_code == "UNVERIFIED_INPUT_REFERENCE"


def test_intermediate_workspace_symlink_is_rejected_before_external_write(tmp_path: Path) -> None:
    root = tmp_path / "data"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "manifests").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="real directory"):
        DataWorkspace(root)

    assert not (outside / "source").exists()


def test_request_secrets_never_enter_refs_manifests_or_errors(
    tmp_path: Path, api_server: str
) -> None:
    workspace = DataWorkspace(tmp_path / "data")
    header_secret = "header-secret-sentinel"
    body_secret = b"body-secret-sentinel"
    receipt = workspace.fetch(
        FetchRequest(
            url=f"{api_server}/fail?token=query-secret-sentinel",
            method="POST",
            headers={"Authorization": f"Bearer {header_secret}"},
            body=body_secret,
        )
    )

    assert receipt.status is FetchStatus.FAILED
    assert receipt.snapshot_ref is None
    assert _TwoShapeApi.captured_authorization == f"Bearer {header_secret}"
    assert _TwoShapeApi.captured_body == body_secret
    public_bytes = b"".join(path.read_bytes() for path in workspace.root.rglob("*.json"))
    for secret in (header_secret, body_secret.decode(), "query-secret-sentinel"):
        assert secret.encode() not in public_bytes
        assert secret not in json.dumps(receipt.as_dict())


def test_exact_retry_is_idempotent_and_concurrent_safe(tmp_path: Path, api_server: str) -> None:
    workspace = DataWorkspace(tmp_path / "data")
    request = FetchRequest(url=f"{api_server}/nested")
    with ThreadPoolExecutor(max_workers=8) as pool:
        receipts = tuple(pool.map(workspace.fetch, (request,) * 16))

    refs = {receipt.snapshot_ref for receipt in receipts}
    assert all(receipt.status is FetchStatus.SUCCEEDED for receipt in receipts)
    assert len(refs) == 1
    assert len(tuple((workspace.root / "manifests" / "source").glob("*.json"))) == 1


def test_parser_change_creates_new_derived_identity_and_exact_lineage(
    tmp_path: Path, api_server: str
) -> None:
    workspace = DataWorkspace(tmp_path / "data")
    source_ref = _fetch(workspace, f"{api_server}/nested")
    first = workspace.derive(
        inputs={"api": source_ref},
        source=(
            'payload = json_input("api")\nresult = emit({"value": [payload["rows"][0]["value"]]})'
        ),
        parameters={"row": 0},
    )
    replay = workspace.derive(
        inputs={"api": source_ref},
        source=(
            'payload = json_input("api")\nresult = emit({"value": [payload["rows"][0]["value"]]})'
        ),
        parameters={"row": 0},
    )
    second = workspace.derive(
        inputs={"api": source_ref},
        source=(
            'payload = json_input("api")\nresult = emit({"value": [payload["rows"][1]["value"]]})'
        ),
        parameters={"row": 1},
    )

    assert first.status is DeriveStatus.SUCCEEDED
    assert replay.status is DeriveStatus.SUCCEEDED
    assert second.status is DeriveStatus.SUCCEEDED
    assert first.dataset_ref is not None
    assert replay.dataset_ref == first.dataset_ref
    assert second.dataset_ref is not None
    assert first.dataset_ref.dataset_id != second.dataset_ref.dataset_id
    assert first.dataset_ref.code_sha256 != second.dataset_ref.code_sha256
    manifest = workspace.inspect(first.dataset_ref)
    assert manifest.input_ref_ids == (source_ref.uri,)
    assert manifest.output_sha256 == first.dataset_ref.output_sha256
    view = workspace.authorized_json_view(
        first.dataset_ref,
        view_id="derived-view",
        environment_ref="environment@1",
    )
    assert view.fields["value"] == (1,)


def test_derived_output_larger_than_process_pipe_is_drained_before_join(
    tmp_path: Path, api_server: str
) -> None:
    """A bounded valid transform cannot deadlock because its message exceeds a pipe buffer."""
    payload_bytes = 200_000
    workspace = DataWorkspace(tmp_path / "data")
    source_ref = _fetch(workspace, f"{api_server}/nested")

    derived = workspace.derive(
        inputs={"api": source_ref},
        source=(
            f'payload = input_text("api")\nresult = emit({{"payload": "z" * {payload_bytes}}})'
        ),
        parameters={},
        wall_time_seconds=2.0,
        max_output_bytes=300_000,
    )

    assert derived.status is DeriveStatus.SUCCEEDED
    assert derived.dataset_ref is not None
    assert derived.dataset_ref.size_bytes > payload_bytes


@pytest.mark.parametrize(
    "source",
    [
        "import urllib.request\nresult = emit({})",
        'result = emit({"secret": open("/etc/passwd").read()})',
        'result = emit({"network": socket("127.0.0.1", 80)})',
    ],
)
def test_derivation_network_and_filesystem_escape_is_denied(
    tmp_path: Path, api_server: str, source: str
) -> None:
    workspace = DataWorkspace(tmp_path / "data")
    source_ref = _fetch(workspace, f"{api_server}/nested")

    receipt = workspace.derive(inputs={"api": source_ref}, source=source, parameters={})

    assert receipt.status is DeriveStatus.DENIED
    assert receipt.dataset_ref is None
    assert receipt.error_code == "TRANSFORMATION_POLICY_DENIED"


def test_derived_output_mutation_and_parser_failure_never_return_healthy_refs(
    tmp_path: Path, api_server: str
) -> None:
    workspace = DataWorkspace(tmp_path / "data")
    source_ref = _fetch(workspace, f"{api_server}/tabular")
    failed = workspace.derive(
        inputs={"api": source_ref},
        source='rows = csv_input("api")\nresult = emit(rows[99])',
        parameters={},
    )
    assert failed.status is DeriveStatus.FAILED
    assert failed.dataset_ref is None

    healthy = workspace.derive(
        inputs={"api": source_ref},
        source='rows = csv_input("api")\nresult = emit({"region": [rows[1][0]]})',
        parameters={},
    )
    assert healthy.dataset_ref is not None
    output_path = workspace.root / "objects" / healthy.dataset_ref.output_sha256
    output_path.write_bytes(b"{}")
    assert workspace.verify(healthy.dataset_ref).healthy is False


def test_derivation_timeout_and_output_limit_fail_without_refs(
    tmp_path: Path, api_server: str
) -> None:
    workspace = DataWorkspace(tmp_path / "data")
    source_ref = _fetch(workspace, f"{api_server}/nested")
    timed_out = workspace.derive(
        inputs={"api": source_ref},
        source='payload = input_text("api")\nwhile True:\n    pass',
        parameters={},
        wall_time_seconds=0.05,
    )
    oversized = workspace.derive(
        inputs={"api": source_ref},
        source='payload = input_text("api")\nresult = emit({"value": [payload]})',
        parameters={},
        max_output_bytes=10,
    )

    assert timed_out.status is DeriveStatus.FAILED
    assert timed_out.dataset_ref is None
    assert timed_out.error_code == "TRANSFORMATION_TIMEOUT"
    assert oversized.status is DeriveStatus.FAILED
    assert oversized.dataset_ref is None


def test_search_and_restart_reconstruct_exact_source_and_derived_refs(
    tmp_path: Path, api_server: str
) -> None:
    root = tmp_path / "data"
    workspace = DataWorkspace(root)
    source_ref = _fetch(workspace, f"{api_server}/nested")
    derived = workspace.derive(
        inputs={"api": source_ref},
        source='payload = json_input("api")\nresult = emit({"region": ["A", "B"]})',
        parameters={},
    )
    assert derived.dataset_ref is not None

    restarted = DataWorkspace(root)
    found = restarted.search("source_snapshot") + restarted.search("derived_dataset")
    assert {item.ref_uri for item in found} == {source_ref.uri, derived.dataset_ref.uri}
    assert restarted.resolve(source_ref.uri) == source_ref
    assert restarted.resolve(derived.dataset_ref.uri) == derived.dataset_ref
