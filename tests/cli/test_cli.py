"""Operator CLI acceptance tests."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

from research_agent.cli import main

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.capture import CaptureFixture


def _json_output(capsys: CaptureFixture[str]) -> dict[str, object]:
    return cast("dict[str, object]", json.loads(capsys.readouterr().out))


def test_verify_command_reports_honest_green_and_red_counts(
    capsys: CaptureFixture[str],
) -> None:
    """The CLI must expose expected reds without treating them as process failure."""
    assert main(("verify", "--json")) == 0
    payload = _json_output(capsys)
    counts = cast("dict[str, int]", payload["counts"])
    assert counts == {
        "EXPECTED_RED": 5,
        "HARNESS_BUG": 0,
        "HARNESS_GREEN": 10,
        "UNEXPECTED_GREEN": 0,
    }


def test_demo_emits_promoted_finding_but_no_automatic_durable_state(
    capsys: CaptureFixture[str],
) -> None:
    """The happy demo reaches a canonical finding but remains provisional."""
    assert main(("demo", "--world-id", "cli-finding", "--json")) == 0
    payload = _json_output(capsys)
    assert payload["status"] == "finding"
    assert isinstance(payload["finding_ref"], str)
    assert isinstance(payload["rendered_report_ref"], str)
    assert payload["negative_result_ref"] is None
    assert payload["durable_state_changed"] is False


def test_demo_rejection_preserves_negative_evidence_and_renders_no_report(
    capsys: CaptureFixture[str],
) -> None:
    """The negative demo retains rejection evidence and never fabricates a report."""
    assert main(("demo", "--world-id", "cli-rejection", "--reject", "--json")) == 0
    payload = _json_output(capsys)
    assert payload["status"] == "rejected"
    assert isinstance(payload["negative_result_ref"], str)
    assert payload["finding_ref"] is None
    assert payload["rendered_report_ref"] is None


def test_data_commands_are_composable_predictable_json(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    """Empty catalog search is stable JSON and all seven commands are registered."""
    workspace_path = tmp_path / "data"
    assert main(("data", "search", "--workspace", str(workspace_path), "--query", "source")) == 0
    search_payload = _json_output(capsys)
    assert search_payload == {"entries": [], "query": "source"}

    from research_agent.cli import build_parser  # noqa: PLC0415

    examples = {
        "fetch": ("data", "fetch", "--url", "https://example.test/data"),
        "inspect": ("data", "inspect", "--ref", "source:" + "a" * 64),
        "verify": ("data", "verify", "--ref", "source:" + "a" * 64),
        "search": ("data", "search"),
        "scout": (
            "data",
            "scout",
            "--request",
            str(tmp_path / "need.json"),
            "--response",
            str(tmp_path / "proposals.json"),
            "--provider-id",
            "codex-task",
            "--idempotency-key",
            "attempt-1",
        ),
        "acquire-scouted": (
            "data",
            "acquire-scouted",
            "--report",
            "scouting:" + "b" * 64,
            "--candidate",
            "c" * 64,
        ),
        "derive": (
            "data",
            "derive",
            "--input",
            "api=source:" + "a" * 64,
            "--code",
            str(tmp_path / "parser.py"),
        ),
    }
    for command, arguments in examples.items():
        assert build_parser().parse_args(arguments).data_command == command
