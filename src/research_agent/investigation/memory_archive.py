"""Crash-durable question memory with deterministic Markdown/Mermaid projections."""

# ruff: noqa: D105, D107, EM101, TRY003, TRY300, TRY301

from __future__ import annotations

import html
import json
import os
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import TYPE_CHECKING, cast

from research_agent.investigation.memory import QuestionMemoryRecord, QuestionMemoryStatus

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


ARCHIVE_SCHEMA_VERSION = "question-memory-v1"


class QuestionMemoryPersistenceError(ValueError):
    """Durable publication or reconstruction failed without changing scientific meaning."""


class DurableQuestionMemoryArchive:
    """SQLite system of record plus generated human-readable research notebook."""

    def __init__(
        self,
        root: str | Path,
        *,
        markdown_writer: Callable[[Path, str], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.database_path = self.root / "question-memory.sqlite3"
        self.markdown_directory = self.root / "research"
        self.index_path = self.markdown_directory / "README.md"
        self._markdown_writer = markdown_writer or _atomic_write
        self._capability: object | None = None
        self._lock = RLock()
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            self.markdown_directory.mkdir(parents=True, exist_ok=True)
            self._initialize()
        except (OSError, sqlite3.Error) as error:
            raise QuestionMemoryPersistenceError(
                "could not initialize durable question memory"
            ) from error

    def __copy__(self) -> DurableQuestionMemoryArchive:
        raise TypeError("durable question memory archive cannot be copied")

    def __deepcopy__(self, memo: dict[int, object]) -> DurableQuestionMemoryArchive:
        del memo
        raise TypeError("durable question memory archive cannot be copied")

    def bind_authority(self, capability: object) -> None:
        """Bind one hidden in-process publication capability for this archive instance."""
        with self._lock:
            if self._capability is not None:
                raise QuestionMemoryPersistenceError(
                    "durable question memory is already bound to an authority"
                )
            self._capability = capability

    def load(self) -> tuple[QuestionMemoryRecord, ...]:
        """Reconstruct exact identity-checked records in deterministic resolution order."""
        with self._lock:
            try:
                with self._connect() as connection:
                    rows = connection.execute(
                        "SELECT record_json FROM question_memory ORDER BY resolved_at, memory_id"
                    ).fetchall()
                return tuple(_decode_record(str(row[0])) for row in rows)
            except (OSError, sqlite3.Error, TypeError, ValueError) as error:
                raise QuestionMemoryPersistenceError(
                    "durable question memory could not be reconstructed"
                ) from error

    def append_issued(
        self,
        record: QuestionMemoryRecord,
        *,
        capability: object,
    ) -> QuestionMemoryRecord:
        """Atomically append exact structured truth, then refresh derived Markdown views."""
        with self._lock:
            if capability is not self._capability:
                raise QuestionMemoryPersistenceError(
                    "question memory archive append was not authority-issued"
                )
            encoded = _encode_record(record)
            try:
                with self._connect() as connection:
                    connection.execute("BEGIN IMMEDIATE")
                    prior = connection.execute(
                        "SELECT record_json FROM question_memory WHERE question_fingerprint = ?",
                        (record.question_fingerprint,),
                    ).fetchone()
                    if prior is not None:
                        if str(prior[0]) != encoded:
                            raise QuestionMemoryPersistenceError(
                                "resolved question already has different durable evidence"
                            )
                    else:
                        collision = connection.execute(
                            "SELECT question_fingerprint FROM question_memory WHERE memory_id = ?",
                            (record.memory_id,),
                        ).fetchone()
                        if collision is not None:
                            raise QuestionMemoryPersistenceError(
                                "question memory ID collides with another fingerprint"
                            )
                        connection.execute(
                            "INSERT INTO question_memory "
                            "(question_fingerprint, memory_id, resolved_at, record_json) "
                            "VALUES (?, ?, ?, ?)",
                            (
                                record.question_fingerprint,
                                record.memory_id,
                                record.resolved_at.isoformat(),
                                encoded,
                            ),
                        )
                    connection.commit()
                records = self.load()
                if record not in records:
                    raise QuestionMemoryPersistenceError(
                        "durable archive did not return the appended record"
                    )
                self._render(records)
                return record
            except QuestionMemoryPersistenceError:
                raise
            except (OSError, sqlite3.Error, TypeError, ValueError) as error:
                raise QuestionMemoryPersistenceError(
                    "durable question memory publication failed"
                ) from error

    def refresh_markdown(self) -> None:
        """Regenerate every presentation view from authoritative structured records."""
        with self._lock:
            self._render(self.load())

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS archive_metadata "
                "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS question_memory ("
                "question_fingerprint TEXT PRIMARY KEY, "
                "memory_id TEXT NOT NULL UNIQUE, "
                "resolved_at TEXT NOT NULL, "
                "record_json TEXT NOT NULL)"
            )
            prior = connection.execute(
                "SELECT value FROM archive_metadata WHERE key = 'schema_version'"
            ).fetchone()
            if prior is None:
                connection.execute(
                    "INSERT INTO archive_metadata (key, value) VALUES ('schema_version', ?)",
                    (ARCHIVE_SCHEMA_VERSION,),
                )
            elif str(prior[0]) != ARCHIVE_SCHEMA_VERSION:
                raise QuestionMemoryPersistenceError(
                    "durable question memory schema version is unsupported"
                )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10.0)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    def _render(self, records: tuple[QuestionMemoryRecord, ...]) -> None:
        for record in records:
            self._markdown_writer(
                self.markdown_directory / f"{record.memory_id}.md",
                _render_record(record),
            )
        self._markdown_writer(self.index_path, _render_index(records))


def _encode_record(record: QuestionMemoryRecord) -> str:
    return json.dumps(
        _record_payload(record),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _record_payload(record: QuestionMemoryRecord) -> dict[str, object]:
    return {
        "memory_id": record.memory_id,
        "question_fingerprint": record.question_fingerprint,
        "question_id": record.question_id,
        "question_text": record.question_text,
        "environment_id": record.environment_id,
        "catalog_id": record.catalog_id,
        "registration_id": record.registration_id,
        "candidate_id": record.candidate_id,
        "development_evidence_id": record.development_evidence_id,
        "protected_resolution_id": record.protected_resolution_id,
        "status": record.status.value,
        "terminal_evidence_ref": record.terminal_evidence_ref,
        "evidence_refs": record.evidence_refs,
        "reason_codes": record.reason_codes,
        "resolved_at": record.resolved_at.isoformat(),
    }


def _decode_record(encoded: str) -> QuestionMemoryRecord:
    loaded = cast("object", json.loads(encoded))
    if not isinstance(loaded, dict):
        raise TypeError("question memory JSON schema is invalid")
    raw = cast("dict[str, object]", loaded)
    if set(raw) != {
        "memory_id",
        "question_fingerprint",
        "question_id",
        "question_text",
        "environment_id",
        "catalog_id",
        "registration_id",
        "candidate_id",
        "development_evidence_id",
        "protected_resolution_id",
        "status",
        "terminal_evidence_ref",
        "evidence_refs",
        "reason_codes",
        "resolved_at",
    }:
        raise ValueError("question memory JSON schema is invalid")
    payload: Mapping[str, object] = raw
    return QuestionMemoryRecord(
        _string(payload, "memory_id"),
        _string(payload, "question_fingerprint"),
        _string(payload, "question_id"),
        _string(payload, "question_text"),
        _string(payload, "environment_id"),
        _string(payload, "catalog_id"),
        _string(payload, "registration_id"),
        _string(payload, "candidate_id"),
        _string(payload, "development_evidence_id"),
        _string(payload, "protected_resolution_id"),
        QuestionMemoryStatus(_string(payload, "status")),
        _string(payload, "terminal_evidence_ref"),
        _string_tuple(payload, "evidence_refs"),
        _string_tuple(payload, "reason_codes"),
        datetime.fromisoformat(_string(payload, "resolved_at")),
    )


def _string(payload: Mapping[str, object], name: str) -> str:
    value = payload.get(name)
    if not isinstance(value, str) or not value:
        message = f"question memory {name} must be a non-empty string"
        raise ValueError(message)
    return value


def _string_tuple(payload: Mapping[str, object], name: str) -> tuple[str, ...]:
    value = payload.get(name)
    if not isinstance(value, list):
        message = f"question memory {name} must be a non-empty string array"
        raise TypeError(message)
    items = cast("list[object]", value)
    if not items or not all(isinstance(item, str) and item for item in items):
        message = f"question memory {name} must be a non-empty string array"
        raise ValueError(message)
    return tuple(cast("str", item) for item in items)


def _render_index(records: tuple[QuestionMemoryRecord, ...]) -> str:
    lines = [
        "# Validated research memory",
        "",
        "> Generated from the structured question-memory archive. Markdown is a presentation ",
        "> view and has no scientific publication authority.",
        "",
        "```mermaid",
        "flowchart TD",
        '    AUTH["Issued protected resolutions"] --> MEMORY["Validated question memory"]',
    ]
    if records:
        for index, record in enumerate(records, start=1):
            label = (
                "Validated finding"
                if record.status is QuestionMemoryStatus.VALIDATED_FINDING
                else "Protected rejection"
            )
            lines.append(f'    MEMORY --> M{index:04d}["{index}. {label}"]')
    else:
        lines.append('    MEMORY --> EMPTY["No terminal questions recorded"]')
    lines.extend(("```", "", "## Resolved questions", ""))
    if not records:
        lines.append("No validated findings or protected rejections have been recorded.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(("| Status | Question | Resolved | Record |", "|---|---|---|---|"))
    lines.extend(
        (
            "| "
            f"{_markdown(record.status.value)} | "
            f"{_markdown(record.question_text)} | "
            f"{_markdown(record.resolved_at.isoformat())} | "
            f"[{record.memory_id[:12]}]({record.memory_id}.md) |"
        )
        for record in records
    )
    lines.append("")
    return "\n".join(lines)


def _render_record(record: QuestionMemoryRecord) -> str:
    terminal = (
        "Validated finding"
        if record.status is QuestionMemoryStatus.VALIDATED_FINDING
        else "Protected rejection"
    )
    lines = [
        f"# {_markdown(record.question_text)}",
        "",
        f"> **{terminal}.** This page is generated from immutable structured evidence. Editing ",
        "> this Markdown does not change scientific status or memory.",
        "",
        "```mermaid",
        "flowchart LR",
        '    Q["Research question"] --> DEV["Temporal development evidence"]',
        '    DEV --> FREEZE["Independent exact freeze"]',
        '    FREEZE --> RUN["Protected authored-program run"]',
        '    RUN --> VALIDATE["Independent validation"]',
        f'    VALIDATE --> TERMINAL["{terminal}"]',
        '    TERMINAL --> MEMORY["Validated question memory"]',
        "```",
        "",
        "## Resolution",
        "",
        f"- Status: `{record.status.value}`",
        f"- Resolved at: `{record.resolved_at.isoformat()}`",
        f"- Memory ID: `{record.memory_id}`",
        f"- Question fingerprint: `{record.question_fingerprint}`",
        f"- Environment: `{record.environment_id}`",
        f"- Catalog: `{record.catalog_id}`",
        f"- Terminal evidence: `{record.terminal_evidence_ref}`",
        "",
        "## Scientific ancestry",
        "",
        f"- Registration: `{record.registration_id}`",
        f"- Authored candidate: `{record.candidate_id}`",
        f"- Development evidence: `{record.development_evidence_id}`",
        f"- Protected resolution: `{record.protected_resolution_id}`",
        "",
        "## Evidence references",
        "",
        *(f"- `{_markdown(item)}`" for item in record.evidence_refs),
        "",
        "## Decision reasons",
        "",
        *(f"- `{_markdown(item)}`" for item in record.reason_codes),
        "",
    ]
    return "\n".join(lines)


def _markdown(value: str) -> str:
    return html.escape(value, quote=False).replace("|", "\\|").replace("\n", " ")


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if temporary.exists():
            temporary.unlink()


__all__ = [
    "ARCHIVE_SCHEMA_VERSION",
    "DurableQuestionMemoryArchive",
    "QuestionMemoryPersistenceError",
]
