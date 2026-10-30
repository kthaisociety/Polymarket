"""Public-command adversaries for exact dual-clock L2 corpus acquisition."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest

from research_agent.data_adapters.polymarket import book_corpus_snapshot
from research_agent.data_adapters.polymarket.book_corpus import (
    BookCorpus,
    BookCorpusSnapshot,
    BookSnapshotRecord,
    register_book_corpus,
)
from research_agent.data_adapters.polymarket.database import LiveBookCorpusResult

if TYPE_CHECKING:
    from pathlib import Path

    from research_agent.data_adapters.polymarket.book_corpus import (
        BookCorpusRequest,
        BookCorpusStore,
    )

START = datetime(2026, 8, 23, 12, tzinfo=UTC)
END = START + timedelta(minutes=5)
BLOCKED_EXIT = 2
FAILED_EXIT = 3
EXPECTED_LEG_COUNT = 2
SENSITIVE_DATABASE_URL = (
    "postgresql://human_ro@example.invalid/db?sslmode=require&application_name=sensitive"
)


async def _read_exact_corpus(
    database_url: str,
    request: BookCorpusRequest,
    store: BookCorpusStore,
) -> LiveBookCorpusResult:
    assert database_url == SENSITIVE_DATABASE_URL
    events = tuple(
        BookSnapshotRecord(
            leg=leg,
            ts=START + timedelta(seconds=leg.outcome_index + 1),
            reference_time=START + timedelta(milliseconds=leg.outcome_index + 500),
            seq=leg.outcome_index + 1,
            bids=(("0.44", "10"), ("0.40", "20")),
            asks=(("0.46", "11"), ("0.50", "21")),
            raw={"asset_id": leg.market_id, "outcome_index": leg.outcome_index},
        )
        for leg in request.legs
    )
    corpus = BookCorpus(request, events)
    retention = store.retain(corpus)
    snapshot: BookCorpusSnapshot = store.load(retention.ref)
    return LiveBookCorpusResult(corpus, retention, register_book_corpus(snapshot))


def _arguments(tmp_path: Path, *, receipt: Path | None = None) -> list[str]:
    arguments = [
        "--scope-authority-ref",
        "semantic-audit:binary-market-1",
        "--leg",
        "polymarket:market-1:0",
        "--leg",
        "polymarket:market-1:1",
        "--start-at",
        START.isoformat(),
        "--end-at",
        END.isoformat(),
        "--workspace",
        str(tmp_path / "objects"),
    ]
    if receipt is not None:
        arguments.extend(("--receipt", str(receipt)))
    return arguments


def test_missing_database_url_is_explicitly_blocked(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Missing approved production access is a blocked result, never empty success."""
    monkeypatch.delenv("POLYMARKET_DATABASE_URL", raising=False)

    status = book_corpus_snapshot.main(_arguments(tmp_path))
    payload = json.loads(capsys.readouterr().out)

    assert status == BLOCKED_EXIT
    assert payload["status"] == "BLOCKED"
    assert payload["live_data_read"] is False
    assert "password" not in json.dumps(payload).casefold()


def test_command_retains_exact_scope_and_emits_only_sanitized_metadata(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """A successful run preserves exact request identity without leaking its DSN."""
    monkeypatch.setenv("POLYMARKET_DATABASE_URL", SENSITIVE_DATABASE_URL)
    monkeypatch.setattr(book_corpus_snapshot, "read_live_book_corpus", _read_exact_corpus)
    receipt = tmp_path / "receipt.json"

    status = book_corpus_snapshot.main(_arguments(tmp_path, receipt=receipt))
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert status == 0
    assert payload["status"] == "SUCCEEDED"
    assert payload["scope_authority_ref"] == "semantic-audit:binary-market-1"
    assert payload["collector_time_interval"] == {
        "start_inclusive": START.isoformat(),
        "end_exclusive": END.isoformat(),
    }
    assert payload["source_event_count"] == EXPECTED_LEG_COUNT
    assert payload["replay_state_count"] == EXPECTED_LEG_COUNT
    assert payload["leg_count"] == EXPECTED_LEG_COUNT
    assert payload["epistemic_status"] == "REGISTERED_DATA_NOT_SCIENTIFIC_EVIDENCE"
    assert payload["snapshot_ref"]["uri"].startswith("polymarket-book-corpus:")
    assert receipt.read_text() == json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n"
    assert SENSITIVE_DATABASE_URL not in output
    assert SENSITIVE_DATABASE_URL not in receipt.read_text()


@pytest.mark.parametrize(
    "replacement",
    [
        ("--start-at", START.replace(tzinfo=None).isoformat()),
        ("--leg", "polymarket:market-1:not-an-index"),
        ("--leg", "polymarket:market-1:2"),
    ],
)
def test_invalid_scope_fails_without_reading_live_data(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    replacement: tuple[str, str],
) -> None:
    """Invalid clocks and legs fail before the live reader can observe the request."""
    monkeypatch.setenv("POLYMARKET_DATABASE_URL", "postgresql://must-not-be-read")

    async def fail_if_called(
        _database_url: str,
        _request: BookCorpusRequest,
        _store: BookCorpusStore,
    ) -> LiveBookCorpusResult:
        message = "invalid request reached the live reader"
        raise AssertionError(message)

    monkeypatch.setattr(book_corpus_snapshot, "read_live_book_corpus", fail_if_called)
    arguments = _arguments(tmp_path)
    offset = arguments.index(replacement[0]) + 1
    arguments[offset] = replacement[1]

    status = book_corpus_snapshot.main(arguments)
    payload = json.loads(capsys.readouterr().out)

    assert status == FAILED_EXIT
    assert payload["status"] == "FAILED"
    assert payload["live_data_read"] is False
    assert "must-not-be-read" not in json.dumps(payload)


def test_existing_different_receipt_is_not_overwritten(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """A receipt path containing different bytes remains immutable."""
    monkeypatch.setenv("POLYMARKET_DATABASE_URL", SENSITIVE_DATABASE_URL)
    monkeypatch.setattr(book_corpus_snapshot, "read_live_book_corpus", _read_exact_corpus)
    receipt = tmp_path / "receipt.json"
    receipt.write_text("different\n")

    status = book_corpus_snapshot.main(_arguments(tmp_path, receipt=receipt))
    payload = json.loads(capsys.readouterr().out)

    assert status == FAILED_EXIT
    assert payload["status"] == "FAILED"
    assert receipt.read_text() == "different\n"
