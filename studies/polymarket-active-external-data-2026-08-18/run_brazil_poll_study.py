# ruff: noqa: D103, EM101, INP001, T201, TRY003

"""Run the Brazil poll-vintage study through the constrained Chronos harness."""

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

_VINTAGES_SHA256 = "77b02785451523c9ee31d6f9b898b138d02da613c44bcc77276e690a8e86cd67"
_FILLS_SHA256 = "26f88953ce89400499b9096449b89458f1e12e5726e6b7f8b3222eb9fa24fd52"
_AUDIT_SHA256 = "614d9bcbaa3d2d0d280f323ad20f1b6232af8c91c1440214bc45dadfcf8786a3"
_ENVIRONMENT = "chronos-brazil-polls-development-2026-08-18"
_CANDIDATES = {
    "0xdf8e2dc5860027decbe6164555c3c1c9645c3bd33e16b9dc57ca87125047d4a8": "lula",
    "0x1a01bf78f56a507fcb666d564d8c8b91b0750679163ed6e96746102c9b7d285d": "flavio",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _vintage_view(path: Path) -> AuthorizedDataView:
    if _sha256(path) != _VINTAGES_SHA256:
        raise ValueError("Brazil poll-vintage receipt hash mismatch")
    vintages = json.loads(path.read_text())["vintages"]
    return AuthorizedDataView(
        view_id="brazil-poll-vintages",
        dataset_ref=f"sha256:{_VINTAGES_SHA256}",
        environment_ref=_ENVIRONMENT,
        fields={
            "available_epoch": tuple(
                int(datetime.fromisoformat(item["available_at"]).timestamp()) for item in vintages
            ),
            "institute": tuple(item["institute"] for item in vintages),
            "lula_margin_pp": tuple(item["lula_margin_pp"] for item in vintages),
            "register_tse": tuple(item["register_tse"] for item in vintages),
        },
    )


def _fills_view(path: Path) -> AuthorizedDataView:
    if _sha256(path) != _FILLS_SHA256:
        raise ValueError("Brazil fills hash mismatch")
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
        view_id="brazil-fills",
        dataset_ref=f"sha256:{_FILLS_SHA256}",
        environment_ref=_ENVIRONMENT,
        fields={key: tuple(value) for key, value in columns.items()},
    )


def _markets_view(path: Path) -> AuthorizedDataView:
    if _sha256(path) != _AUDIT_SHA256:
        raise ValueError("Brazil candidate-audit hash mismatch")
    markets = [
        item for item in json.loads(path.read_text())["markets"] if item["market_id"] in _CANDIDATES
    ]
    markets.sort(key=lambda item: _CANDIDATES[item["market_id"]])
    return AuthorizedDataView(
        view_id="brazil-markets",
        dataset_ref=f"sha256:{_AUDIT_SHA256}",
        environment_ref=_ENVIRONMENT,
        fields={
            "market_id": tuple(item["market_id"] for item in markets),
            "candidate": tuple(_CANDIDATES[item["market_id"]] for item in markets),
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
    views = (_vintage_view(args.vintages), _fills_view(args.fills), _markets_view(args.audit))
    requested = {view.view_id: tuple(view.fields) for view in views}
    session_id = "brazil-poll-vintage-development-2026-08-18"
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
            wall_time_seconds=45,
            max_inline_bytes=1_500_000,
            max_memory_bytes=768_000_000,
        ),
    )
    observation = harness.run(
        AnalysisRequest(
            session_id=session_id,
            action_id=f"brazil-polls:{hashlib.sha256(source.encode()).hexdigest()}",
            source=source,
            data_access=tuple(
                DataAccessRequest(view_id, fields) for view_id, fields in requested.items()
            ),
        )
    )
    if observation.status is not AnalysisStatus.SUCCEEDED or observation.details is None:
        raise RuntimeError(observation.summary)
    payload = {
        "schema": "chronos-brazil-poll-development/v1",
        "status": observation.status.value,
        "epistemic_status": observation.epistemic_status,
        "protected_values_exposed": False,
        "time_legality": {
            "external": "earliest immutable AFOS Git commit containing exact TSE-matched result",
            "market": "fills strictly after each decision in fixed six-hour execution windows",
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
    print(
        json.dumps(
            {
                "status": payload["status"],
                "summary": payload["summary"],
                "receipt_sha256": hashlib.sha256(content).hexdigest(),
                "receipt": str(args.receipt),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
