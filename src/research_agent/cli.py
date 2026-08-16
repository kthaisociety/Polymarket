"""Small operator surface for deterministic demos and proof status."""

# ruff: noqa: EM101, EM102, PLR0911, T201, TRY003, TRY004, TRY301

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TYPE_CHECKING, cast

from research_agent.data_workspace import (
    DataWorkspace,
    DeriveStatus,
    FetchRequest,
    FetchStatus,
    RecordedSourceScoutProvider,
    ScoutedFetchStatus,
    ScoutingStatus,
    SourceScoutingService,
    SourceSearchRequest,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from research_agent.data_workspace.workspace import JsonValue


def build_parser() -> argparse.ArgumentParser:
    """Build the dependency-free command surface."""
    parser = argparse.ArgumentParser(
        prog="research-agent",
        description="Run the deterministic time-series kernel demo or inspect proof status.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser(
        "demo",
        help="execute the registered synthetic development-to-report workflow",
    )
    demo.add_argument("--world-id", default="cli-demo")
    demo.add_argument(
        "--reject",
        action="store_true",
        help="use an impossible predeclared threshold and preserve negative evidence",
    )
    demo.add_argument(
        "--report",
        action="store_true",
        help="print the canonical Markdown report after the summary when a finding is promoted",
    )
    demo.add_argument("--json", action="store_true", help="emit a machine-readable summary")

    verify = commands.add_parser(
        "verify",
        help="execute the catalog-owned production proof adapters",
    )
    verify.add_argument("--json", action="store_true", help="emit machine-readable results")

    ui = commands.add_parser(
        "ui",
        help="serve the read-only ongoing and finalized research library",
    )
    ui.add_argument("--host", default="127.0.0.1")
    ui.add_argument("--port", type=int, default=8765)
    ui.add_argument(
        "--repository-root",
        type=Path,
        default=Path.cwd(),
        help="repository containing the research directory (defaults to current directory)",
    )

    data = commands.add_parser(
        "data",
        help="retain, verify, catalog, and derive generic content-addressed data",
    )
    data_commands = data.add_subparsers(dest="data_command", required=True)
    fetch = data_commands.add_parser("fetch", help="retain exact bounded HTTP response bytes")
    _add_workspace_argument(fetch)
    fetch.add_argument("--url", required=True)
    fetch.add_argument("--method", default="GET")
    fetch.add_argument("--header", action="append", default=[])
    fetch.add_argument("--body-file", type=Path)
    fetch.add_argument("--max-bytes", type=int, default=64 * 1024 * 1024)
    fetch.add_argument("--timeout-seconds", type=float, default=30.0)

    inspect = data_commands.add_parser("inspect", help="return value-free manifest metadata")
    _add_workspace_argument(inspect)
    inspect.add_argument("--ref", required=True)

    verify_data = data_commands.add_parser("verify", help="verify exact manifest and object bytes")
    _add_workspace_argument(verify_data)
    verify_data.add_argument("--ref", required=True)

    search = data_commands.add_parser("search", help="query the rebuildable local catalog")
    _add_workspace_argument(search)
    search.add_argument("--query", default="")

    scout = data_commands.add_parser(
        "scout",
        help="record strict source proposals returned by an external scouting provider",
    )
    _add_workspace_argument(scout)
    scout.add_argument("--request", type=Path, required=True)
    scout.add_argument("--response", type=Path, required=True)
    scout.add_argument("--provider-id", required=True)
    scout.add_argument("--idempotency-key", required=True)

    acquire_scouted = data_commands.add_parser(
        "acquire-scouted",
        help="hand one exact issued source proposal to the existing bounded fetcher",
    )
    _add_workspace_argument(acquire_scouted)
    acquire_scouted.add_argument("--report", required=True)
    acquire_scouted.add_argument("--candidate", required=True)
    acquire_scouted.add_argument("--max-bytes", type=int, default=64 * 1024 * 1024)
    acquire_scouted.add_argument("--timeout-seconds", type=float, default=30.0)

    derive = data_commands.add_parser(
        "derive", help="run authored parsing/transformation code offline over verified refs"
    )
    _add_workspace_argument(derive)
    derive.add_argument("--input", action="append", required=True)
    derive.add_argument("--code", type=Path, required=True)
    derive.add_argument("--parameters", default="{}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Execute one explicit operator command and return a shell status."""
    arguments = build_parser().parse_args(argv)
    if arguments.command == "verify":
        return _verify(as_json=arguments.json)
    if arguments.command == "ui":
        return _serve_ui(
            repository_root=arguments.repository_root,
            host=arguments.host,
            port=arguments.port,
        )
    if arguments.command == "data":
        return _run_data_command(arguments)
    return _demo(
        world_id=arguments.world_id,
        reject=arguments.reject,
        include_report=arguments.report,
        as_json=arguments.json,
    )


def _verify(*, as_json: bool) -> int:
    from research_agent.verification import (  # noqa: PLC0415
        VerificationStatus,
        production_proof_registry,
        run_proof_suite,
        summarize,
    )

    results = run_proof_suite(production_proof_registry())
    counts = summarize(results)
    payload = {
        "counts": {status.value: counts[status] for status in VerificationStatus},
        "results": [
            {
                "id": result.id,
                "status": result.status.value,
                "reason": result.reason,
                "adapter_id": result.adapter_id,
            }
            for result in results
        ],
    }
    if as_json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print("Scientific-kernel production proof status")
        for status in VerificationStatus:
            print(f"  {status.value}: {counts[status]}")
        for result in results:
            print(f"  [{result.status.value}] {result.id}: {result.reason}")
    return int(
        counts[VerificationStatus.UNEXPECTED_GREEN] > 0
        or counts[VerificationStatus.HARNESS_BUG] > 0
    )


def _demo(
    *,
    world_id: str,
    reject: bool,
    include_report: bool,
    as_json: bool,
) -> int:
    from research_agent.reporting import RenderedFindingReport  # noqa: PLC0415
    from research_agent.scientific_workflow import WorkflowStatus  # noqa: PLC0415
    from research_agent.verification.scientific_workflow_fixture import (  # noqa: PLC0415
        make_toy_scientific_workflow_world,
    )

    world = make_toy_scientific_workflow_world(
        world_id=world_id,
        promotion_mse_threshold=-1.0 if reject else 0.001,
    )
    receipt = world.coordinator.execute(
        workflow_id=world.workflow.workflow_id,
        idempotency_key=f"cli:{world_id}",
        session_id=world.initialized.session.session_id,
        episode_id=world.initialized.episode.episode_id,
    )
    rendered: RenderedFindingReport | None = None
    if receipt.rendered_report_ref is not None:
        candidate = world.coordinator.evidence(receipt.rendered_report_ref)
        if not isinstance(candidate, RenderedFindingReport):
            raise TypeError("Workflow report reference did not resolve to a rendered report.")
        rendered = candidate
    payload = {
        "world_id": world_id,
        "workflow_id": receipt.workflow_id,
        "receipt_id": receipt.receipt_id,
        "status": receipt.status.value,
        "development_evidence_ref": receipt.development_evidence_ref,
        "run_ref": receipt.run_ref,
        "evaluation_report_ref": receipt.evaluation_report_ref,
        "validation_decision_ref": receipt.validation_decision_ref,
        "finding_ref": receipt.finding_ref,
        "negative_result_ref": receipt.negative_result_ref,
        "rendered_report_ref": receipt.rendered_report_ref,
        "reason_codes": receipt.reason_codes,
        "evidence_refs": receipt.evidence_refs,
        "durable_state_changed": False,
        "note": "The workflow receipt is provisional until a separate semantic commit.",
    }
    if as_json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print("Registered scientific workflow demo")
        for key, value in payload.items():
            print(f"  {key}: {value}")
    if include_report:
        if rendered is None:
            print("No report was rendered because the workflow did not promote a finding.")
        else:
            print("\n" + rendered.markdown)
    return int(receipt.status is WorkflowStatus.FAILED)


def _serve_ui(*, repository_root: Path, host: str, port: int) -> int:
    from research_agent.operator_ui import serve_research_library  # noqa: PLC0415

    print(f"Research library: http://{host}:{port}")
    print("Read-only projection; press Ctrl+C to stop.")
    try:
        serve_research_library(repository_root, host=host, port=port)
    except KeyboardInterrupt:
        print("Research library stopped.")
    return 0


def _add_workspace_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path("/data"),
        help="local append-only data workspace root (default: /data)",
    )


def _run_data_command(arguments: argparse.Namespace) -> int:
    """Execute one predictable-JSON data command without echoing raw exceptions."""
    try:
        workspace = DataWorkspace(arguments.workspace)
        if arguments.data_command == "fetch":
            headers = _key_value_arguments(arguments.header, label="header")
            body = (
                None
                if arguments.body_file is None
                else _read_bounded_file(arguments.body_file, 64 * 1024 * 1024)
            )
            receipt = workspace.fetch(
                FetchRequest(
                    url=arguments.url,
                    method=arguments.method,
                    headers=headers,
                    body=body,
                    max_response_bytes=arguments.max_bytes,
                    timeout_seconds=arguments.timeout_seconds,
                )
            )
            print(json.dumps(receipt.as_dict(), allow_nan=False, sort_keys=True))
            return int(receipt.status is not FetchStatus.SUCCEEDED)
        if arguments.data_command == "inspect":
            entry = workspace.inspect(workspace.resolve(arguments.ref))
            print(json.dumps(entry.as_dict(), allow_nan=False, sort_keys=True))
            return 0
        if arguments.data_command == "verify":
            verification = workspace.verify(workspace.resolve(arguments.ref))
            print(json.dumps(verification.as_dict(), allow_nan=False, sort_keys=True))
            return int(not verification.healthy)
        if arguments.data_command == "search":
            payload = {
                "entries": [entry.as_dict() for entry in workspace.search(arguments.query)],
                "query": arguments.query,
            }
            print(json.dumps(payload, allow_nan=False, sort_keys=True))
            return 0
        if arguments.data_command == "scout":
            request_value = json.loads(_read_bounded_file(arguments.request, 128_000))
            response_value = json.loads(_read_bounded_file(arguments.response, 1_000_000))
            if not isinstance(response_value, dict):
                raise ValueError("scout response must be a JSON object")
            request = SourceSearchRequest.from_dict(request_value)
            provider = RecordedSourceScoutProvider(
                provider_id=arguments.provider_id,
                response=cast("dict[str, JsonValue]", response_value),
            )
            receipt = SourceScoutingService(workspace, provider).scout(
                request,
                idempotency_key=arguments.idempotency_key,
            )
            print(json.dumps(receipt.as_dict(), allow_nan=False, sort_keys=True))
            return int(receipt.status is not ScoutingStatus.SUCCEEDED)
        if arguments.data_command == "acquire-scouted":
            service = SourceScoutingService(workspace)
            report_ref = service.resolve_report_uri(arguments.report)
            receipt = service.acquire_candidate(
                report_ref,
                candidate_id=arguments.candidate,
                max_response_bytes=arguments.max_bytes,
                timeout_seconds=arguments.timeout_seconds,
            )
            print(json.dumps(receipt.as_dict(), allow_nan=False, sort_keys=True))
            return int(receipt.status is not ScoutedFetchStatus.SUCCEEDED)
        bindings = _key_value_arguments(arguments.input, label="input")
        inputs = {alias: workspace.resolve(ref_uri) for alias, ref_uri in bindings.items()}
        raw_parameters = json.loads(arguments.parameters)
        if not isinstance(raw_parameters, dict):
            raise ValueError("parameters must be a JSON object")
        parameters = cast("dict[str, JsonValue]", raw_parameters)
        source = _read_bounded_file(arguments.code, 128_000).decode()
        receipt = workspace.derive(inputs=inputs, source=source, parameters=parameters)
        print(json.dumps(receipt.as_dict(), allow_nan=False, sort_keys=True))
        return int(receipt.status is not DeriveStatus.SUCCEEDED)
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        payload = {"status": "command_error", "error_code": "DATA_COMMAND_FAILED"}
        print(json.dumps(payload, sort_keys=True))
        return 2


def _key_value_arguments(values: list[str], *, label: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        key, separator, item = value.partition("=")
        if separator != "=" or not key or key in result:
            raise ValueError(f"{label} must use one unique name=value pair")
        result[key] = item
    return result


def _read_bounded_file(path: Path, limit: int) -> bytes:
    with path.open("rb") as stream:
        content = stream.read(limit + 1)
    if len(content) > limit:
        raise ValueError("input file exceeds command bound")
    return content


__all__ = ["build_parser", "main"]
