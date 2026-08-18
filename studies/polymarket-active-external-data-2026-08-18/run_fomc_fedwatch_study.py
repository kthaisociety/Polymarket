# ruff: noqa: D103, DTZ001, DTZ007, EM101, INP001, T201, TRY003

"""Run the predeclared CME/FOMC candidate through the constrained analysis harness."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from typing import cast

from research_agent.exploration import (
    AnalysisHarness,
    AnalysisRequest,
    AnalysisStatus,
    ArtifactStore,
    AuthorizedDataView,
    CapabilityPolicy,
    DataAccessRequest,
    ResourceLimits,
)

_CME_SHA256 = "1222e3e7dc496e5d46128c0e8c21c088c3b105b0461aab955afd708147c7b8e0"
_BOOK_SHA256 = "ca8e3e58af2467f41f2d9ad89808c01c61ff2762158e82bea59f1f52386a5018"
_ENVIRONMENT = "chronos-active-external-development-2026-08-18"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cme_columns(path: Path) -> dict[str, tuple[object, ...]]:
    if _sha256(path) != _CME_SHA256:
        raise ValueError("CME CSV differs from the retained campaign vintage")
    available: list[int] = []
    values: list[float] = []
    reference_dates: list[str] = []
    with path.open(newline="") as source:
        for row in csv.DictReader(source):
            raw = row.get("(375-400)", "")
            if not raw:
                continue
            reference = datetime.strptime(cast("str", row["Date"]), "%m/%d/%Y").date()
            if not datetime(2026, 8, 6).date() <= reference <= datetime(2026, 8, 17).date():
                continue
            decision = datetime.combine(reference + timedelta(days=1), time(12), tzinfo=UTC)
            reference_dates.append(reference.isoformat())
            available.append(int(decision.timestamp()))
            values.append(float(raw))
    return {
        "reference_date": tuple(reference_dates),
        "available_at_epoch": tuple(available),
        "probability_375_400": tuple(values),
    }


def _book_columns(path: Path) -> dict[str, tuple[object, ...]]:
    if _sha256(path) != _BOOK_SHA256:
        raise ValueError("book snapshot corpus differs from the retained acquisition")
    targets: list[int] = []
    snapshots: list[int] = []
    bids: list[object] = []
    asks: list[object] = []
    with gzip.open(path, "rt") as source:
        for line in source:
            row = json.loads(line)
            if row["kind"] == "header":
                continue
            targets.append(int(datetime.fromisoformat(row["target_time"]).timestamp()))
            snapshots.append(int(datetime.fromisoformat(row["ts"]).timestamp()))
            bids.append(row["bids"])
            asks.append(row["asks"])
    return {
        "target_epoch": tuple(targets),
        "snapshot_epoch": tuple(snapshots),
        "bids": tuple(bids),
        "asks": tuple(asks),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cme-csv", type=Path, required=True)
    parser.add_argument("--books", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    cme = AuthorizedDataView(
        view_id="cme-fedwatch",
        dataset_ref=f"sha256:{_CME_SHA256}",
        environment_ref=_ENVIRONMENT,
        fields=_cme_columns(args.cme_csv),
    )
    books = AuthorizedDataView(
        view_id="polymarket-fomc-books",
        dataset_ref=f"sha256:{_BOOK_SHA256}",
        environment_ref=_ENVIRONMENT,
        fields=_book_columns(args.books),
    )
    session_id = "fomc-fedwatch-development-2026-08-18"
    source = args.source.read_text()
    requested = {
        cme.view_id: tuple(cme.fields),
        books.view_id: tuple(books.fields),
    }
    harness = AnalysisHarness(
        views={cme.view_id: cme, books.view_id: books},
        policy=CapabilityPolicy(
            session_id=session_id,
            environment_ref=_ENVIRONMENT,
            allowed_fields_by_view={key: frozenset(value) for key, value in requested.items()},
        ),
        artifacts=ArtifactStore(),
        resource_limits=ResourceLimits(wall_time_seconds=5, max_inline_bytes=20_000),
    )
    observation = harness.run(
        AnalysisRequest(
            session_id=session_id,
            action_id=f"fomc-fedwatch:{hashlib.sha256(source.encode()).hexdigest()}",
            source=source,
            data_access=tuple(
                DataAccessRequest(view_id, fields) for view_id, fields in requested.items()
            ),
        )
    )
    if observation.status is not AnalysisStatus.SUCCEEDED or observation.details is None:
        raise RuntimeError(observation.summary)
    payload = {
        "schema": "chronos-fomc-fedwatch-development-receipt/v1",
        "status": observation.status.value,
        "epistemic_status": observation.epistemic_status,
        "protected_values_exposed": False,
        "time_legality": {
            "cme_rule": "date plus one calendar day at 12:00 UTC",
            "book_rule": "last snapshot at or before decision, maximum age 15 minutes",
            "formal_temporal_registration": False,
            "reason": "operator-downloaded CME bytes have no local-import seam in DataWorkspace",
        },
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "inputs": {"cme_sha256": _CME_SHA256, "books_sha256": _BOOK_SHA256},
        "summary": observation.summary,
        "details": observation.details,
        "warnings": list(observation.warnings),
        "execution": {
            "action_id": observation.provenance.action_id,
            "code_sha256": observation.provenance.code_sha256,
            "actual_accesses": [
                {
                    "ordinal": item.ordinal,
                    "view_id": item.view_id,
                    "dataset_ref": item.dataset_ref,
                    "field_id": item.field_id,
                }
                for item in observation.provenance.accesses
            ],
        },
    }
    content = (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode()
    try:
        with args.receipt.open("xb") as output:
            output.write(content)
    except FileExistsError:
        if args.receipt.read_bytes() != content:
            raise ValueError("study receipt already contains different bytes") from None
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
