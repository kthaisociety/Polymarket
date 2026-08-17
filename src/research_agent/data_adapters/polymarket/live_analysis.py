"""Public live Polymarket registration-to-exploration command."""

# ruff: noqa: T201

from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from research_agent.data_adapters.polymarket.analysis import (
    PolymarketAnalysisRequest,
    PolymarketExploratoryAnalysis,
    analyze_registered_polymarket_tape,
)
from research_agent.data_adapters.polymarket.database import read_live_polymarket_tape
from research_agent.data_adapters.polymarket.models import PolymarketImportRequest
from research_agent.exploration import AnalysisStatus, ResourceLimits

if TYPE_CHECKING:
    from collections.abc import Sequence

_DATABASE_URL_ENV = "BDL__DB__URL"


def build_parser() -> argparse.ArgumentParser:
    """Build the explicit live authored-analysis command surface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--market-id", action="append", required=True)
    parser.add_argument("--decision-time", required=True)
    parser.add_argument("--code", type=Path, required=True)
    parser.add_argument("--field", action="append", required=True)
    parser.add_argument("--environment-id", default="bdl-polymarket-production-readonly")
    parser.add_argument("--session-id", default="polymarket-live-exploration")
    parser.add_argument("--action-id", default="analyze-registered-polymarket-tape")
    parser.add_argument("--random-seed", type=int)
    parser.add_argument("--wall-time-seconds", type=float, default=10.0)
    parser.add_argument("--artifact-directory", type=Path)
    parser.add_argument("--receipt", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Read live data and return a sanitized provisional observation receipt."""
    arguments = build_parser().parse_args(argv)
    database_url = os.environ.get(_DATABASE_URL_ENV)
    if database_url is None:
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "error_code": "READ_ONLY_DATABASE_URL_UNSET",
                    "required_action": "open the approved human_ro tunnel and set BDL__DB__URL",
                    "live_data_read": False,
                },
                sort_keys=True,
            )
        )
        return 2
    try:
        decision_time = _parse_aware_datetime(arguments.decision_time)
        source = arguments.code.read_text(encoding="utf-8")
        payload = asyncio.run(
            _run_live_analysis(
                _LiveAnalysisRequest(
                    database_url=database_url,
                    market_ids=tuple(arguments.market_id),
                    environment_id=arguments.environment_id,
                    decision_time=decision_time,
                    source=source,
                    requested_view_fields=tuple(arguments.field),
                    session_id=arguments.session_id,
                    action_id=arguments.action_id,
                    random_seed=arguments.random_seed,
                    wall_time_seconds=arguments.wall_time_seconds,
                    artifact_directory=arguments.artifact_directory,
                )
            )
        )
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        print(
            json.dumps(
                {
                    "status": "FAILED",
                    "error_code": "POLYMARKET_LIVE_ANALYSIS_FAILED",
                    "error_type": type(error).__name__,
                    "live_data_read": False,
                },
                sort_keys=True,
            )
        )
        return 3
    if arguments.receipt is not None:
        _persist_receipt(payload, arguments.receipt)
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["analysis_status"] == AnalysisStatus.SUCCEEDED.value else 4


@dataclass(frozen=True, slots=True)
class _LiveAnalysisRequest:
    database_url: str
    market_ids: tuple[str, ...]
    environment_id: str
    decision_time: datetime
    source: str
    requested_view_fields: tuple[str, ...]
    session_id: str
    action_id: str
    random_seed: int | None
    wall_time_seconds: float
    artifact_directory: Path | None


async def _run_live_analysis(request: _LiveAnalysisRequest) -> dict[str, object]:
    ingestion = await read_live_polymarket_tape(
        request.database_url,
        PolymarketImportRequest(request.market_ids, request.environment_id),
    )
    analysis = analyze_registered_polymarket_tape(
        ingestion,
        PolymarketAnalysisRequest(
            decision_time=request.decision_time,
            source=request.source,
            requested_view_fields=request.requested_view_fields,
            session_id=request.session_id,
            action_id=request.action_id,
            random_seed=request.random_seed,
            resource_limits=ResourceLimits(wall_time_seconds=request.wall_time_seconds),
        ),
    )
    observation = analysis.observation
    persisted_artifacts = _persist_artifacts(
        analysis,
        session_id=request.session_id,
        directory=request.artifact_directory,
    )
    return {
        "status": "SUCCEEDED",
        "live_data_read": True,
        "database_role": "human_ro",
        "default_transaction_read_only": True,
        "market_ids": list(request.market_ids),
        "vintage": ingestion.vintage.identity,
        "included_fill_count": ingestion.included_fill_count,
        "excluded_fill_count": ingestion.excluded_fill_count,
        "registered_observation_count": len(ingestion.registered.observations),
        "source_digest": ingestion.source_digest,
        "registration_id": ingestion.registered.registration_id,
        "catalog_id": ingestion.catalog.identity,
        "information_set_id": analysis.information_set.information_set_id,
        "decision_time": request.decision_time.isoformat(),
        "legal_observation_count": len(analysis.information_set.observations),
        "view_id": analysis.view.view_id,
        "requested_view_fields": list(request.requested_view_fields),
        "analysis_status": observation.status.value,
        "epistemic_status": observation.epistemic_status,
        "summary": observation.summary,
        "details": observation.details,
        "warnings": list(observation.warnings),
        "recoverable": observation.recoverable,
        "code_sha256": observation.provenance.code_sha256,
        "actual_accesses": [
            {
                "ordinal": access.ordinal,
                "view_id": access.view_id,
                "dataset_ref": access.dataset_ref,
                "environment_ref": access.environment_ref,
                "field_id": access.field_id,
            }
            for access in observation.provenance.accesses
        ],
        "artifact_refs": [
            {
                "artifact_id": ref.artifact_id,
                "kind": ref.kind.value,
                "size_bytes": ref.size_bytes,
                "sha256": ref.sha256,
            }
            for ref in observation.artifact_refs
        ],
        "persisted_artifacts": persisted_artifacts,
        "snapshot_caveats": list(ingestion.snapshot_caveats),
        "formal_object_refs": list(observation.formal_object_refs),
        "durable_state_effects": list(observation.durable_state_effects),
    }


def _persist_artifacts(
    analysis: PolymarketExploratoryAnalysis,
    *,
    session_id: str,
    directory: Path | None,
) -> list[dict[str, object]]:
    refs = analysis.observation.artifact_refs
    if not refs:
        return []
    if directory is None:
        msg = "analysis produced external artifacts; --artifact-directory is required"
        raise ValueError(msg)
    directory.mkdir(parents=True, exist_ok=True)
    persisted: list[dict[str, object]] = []
    for ref in refs:
        content = analysis.artifacts.read(ref, session_id=session_id)
        path = directory / f"{ref.artifact_id}.{ref.kind.value}"
        try:
            with path.open("xb") as artifact_file:
                artifact_file.write(content)
        except FileExistsError:
            if path.read_bytes() != content:
                msg = "artifact path already contains different bytes"
                raise ValueError(msg) from None
        persisted.append(
            {
                "artifact_id": ref.artifact_id,
                "kind": ref.kind.value,
                "path": str(path.resolve()),
                "size_bytes": ref.size_bytes,
                "sha256": ref.sha256,
            }
        )
    return persisted


def _parse_aware_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = "decision time must be timezone-aware ISO-8601"
        raise ValueError(msg)
    return parsed


def _persist_receipt(payload: dict[str, object], path: Path) -> None:
    content = (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as receipt_file:
            receipt_file.write(content)
    except FileExistsError:
        if path.read_bytes() != content:
            msg = "receipt path already contains different bytes"
            raise ValueError(msg) from None


if __name__ == "__main__":
    raise SystemExit(main())
