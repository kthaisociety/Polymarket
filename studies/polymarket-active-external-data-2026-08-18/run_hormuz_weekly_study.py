# ruff: noqa: D103, EM101, INP001, T201, TRY003

"""Run the historical-vintage Hormuz study through the constrained Chronos harness."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from datetime import datetime
from pathlib import Path

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

_VINTAGES_SHA256 = "05e9b1066d84f4fe7c7c109182cf9afcee1d2a33599b77e7e8252896186c3986"
_FILLS_SHA256 = "db7f689812794ce0aa3daaa29b74e9d0c2f183143fb7a8990fd1bf5ab4e4a824"
_AUDIT_SHA256 = "be4ea7d593cf265840cc7254e67d171d81cbe5767500f2ed577f96a218db1ddd"
_ENVIRONMENT = "chronos-hormuz-external-development-2026-08-18"
_SELECTED_MARKETS = {
    "0x5c79dfde05559b79a9cb9f7c4187e4d49632dd042572ae676952f812732591cc",
    "0x60c2c085ee8c16bc8f2419739a94971d4c9d00f637ead10fc0f540afa1be64e8",
    "0xa08a5ce99e14ce0b22767af6f16c08a2ab012249444c20887193a9a3e98e11fc",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _vintage_view(path: Path) -> AuthorizedDataView:
    if _sha256(path) != _VINTAGES_SHA256:
        raise ValueError("historical vintage receipt hash mismatch")
    payload = json.loads(path.read_text())
    vintages = payload["vintages"]
    return AuthorizedDataView(
        view_id="hormuz-git-vintages",
        dataset_ref=f"sha256:{_VINTAGES_SHA256}",
        environment_ref=_ENVIRONMENT,
        fields={
            "available_epoch": tuple(
                int(datetime.fromisoformat(item["committed_at"]).timestamp()) for item in vintages
            ),
            "latest_date": tuple(item["latest_date"] for item in vintages),
            "rolling7": tuple(item["rolling7"] for item in vintages),
            "delta7": tuple(item["delta7"] for item in vintages),
            "source_lag_days": tuple(item["source_lag_days"] for item in vintages),
            "commit": tuple(item["commit"] for item in vintages),
        },
    )


def _fills_view(path: Path) -> AuthorizedDataView:
    if _sha256(path) != _FILLS_SHA256:
        raise ValueError("Hormuz fills hash mismatch")
    columns: dict[str, list[object]] = {
        "fill_epoch": [],
        "market_id": [],
        "side": [],
        "price": [],
        "size": [],
    }
    with gzip.open(path, "rt") as source:
        for line in source:
            item = json.loads(line)
            if item["kind"] == "header":
                continue
            columns["fill_epoch"].append(int(datetime.fromisoformat(item["fill_time"]).timestamp()))
            columns["market_id"].append(item["market_id"])
            columns["side"].append(item["side"])
            columns["price"].append(float(item["price"]))
            columns["size"].append(float(item["size"]))
    return AuthorizedDataView(
        view_id="hormuz-fills",
        dataset_ref=f"sha256:{_FILLS_SHA256}",
        environment_ref=_ENVIRONMENT,
        fields={key: tuple(value) for key, value in columns.items()},
    )


def _markets_view(path: Path) -> AuthorizedDataView:
    if _sha256(path) != _AUDIT_SHA256:
        raise ValueError("Hormuz candidate audit hash mismatch")
    payload = json.loads(path.read_text())
    markets = [item for item in payload["markets"] if item["market_id"] in _SELECTED_MARKETS]
    return AuthorizedDataView(
        view_id="hormuz-markets",
        dataset_ref=f"sha256:{_AUDIT_SHA256}",
        environment_ref=_ENVIRONMENT,
        fields={
            "market_id": tuple(item["market_id"] for item in markets),
            "open_epoch": tuple(
                int(datetime.fromisoformat(item["open_time"]).timestamp()) for item in markets
            ),
            "close_epoch": tuple(
                int(datetime.fromisoformat(item["close_time"]).timestamp()) for item in markets
            ),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vintages", type=Path, required=True)
    parser.add_argument("--fills", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    views = (
        _vintage_view(args.vintages),
        _fills_view(args.fills),
        _markets_view(args.audit),
    )
    requested = {view.view_id: tuple(view.fields) for view in views}
    session_id = "hormuz-weekly-vintage-development-2026-08-18"
    source = args.source.read_text()
    harness = AnalysisHarness(
        views={view.view_id: view for view in views},
        policy=CapabilityPolicy(
            session_id=session_id,
            environment_ref=_ENVIRONMENT,
            allowed_fields_by_view={key: frozenset(value) for key, value in requested.items()},
        ),
        artifacts=ArtifactStore(),
        resource_limits=ResourceLimits(
            wall_time_seconds=30,
            max_inline_bytes=50_000,
            max_memory_bytes=768_000_000,
        ),
    )
    observation = harness.run(
        AnalysisRequest(
            session_id=session_id,
            action_id=f"hormuz-weekly:{hashlib.sha256(source.encode()).hexdigest()}",
            source=source,
            data_access=tuple(
                DataAccessRequest(view_id, fields) for view_id, fields in requested.items()
            ),
        )
    )
    if observation.status is not AnalysisStatus.SUCCEEDED or observation.details is None:
        raise RuntimeError(observation.summary)
    payload = {
        "schema": "chronos-hormuz-weekly-development/v1",
        "status": observation.status.value,
        "epistemic_status": observation.epistemic_status,
        "protected_values_exposed": False,
        "time_legality": {
            "external": "exact OCHA Git commit timestamp and blob",
            "market": "fills strictly after each decision within fixed six-hour execution windows",
            "historical_vintage_reconstructed": True,
        },
        "inputs": {
            "vintages_sha256": _VINTAGES_SHA256,
            "fills_sha256": _FILLS_SHA256,
            "audit_sha256": _AUDIT_SHA256,
        },
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
    temporary = args.receipt.with_suffix(f"{args.receipt.suffix}.partial")
    try:
        with temporary.open("xb") as output:
            output.write(content)
        temporary.replace(args.receipt)
    finally:
        temporary.unlink(missing_ok=True)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
