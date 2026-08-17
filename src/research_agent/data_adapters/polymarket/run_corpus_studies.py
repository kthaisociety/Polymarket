"""Run exact authored studies over a protected event-grouped Polymarket corpus."""

# ruff: noqa: T201

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING

from research_agent.data_adapters.polymarket.corpus import (
    PolymarketCorpusSnapshotRef,
    PolymarketCorpusStore,
)
from research_agent.data_adapters.polymarket.corpus_analysis import (
    build_polymarket_development_analysis,
)
from research_agent.exploration import AnalysisStatus

if TYPE_CHECKING:
    from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """Build the offline, exact-snapshot study command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-sha256", required=True)
    parser.add_argument("--snapshot-size", required=True, type=int)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--source", required=True, action="append", type=Path)
    parser.add_argument("--receipt-directory", required=True, type=Path)
    parser.add_argument("--session-id", default="polymarket-resolution-development-2026-08-17")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Execute each authored source and retain a conflict-detecting receipt."""
    arguments = build_parser().parse_args(argv)
    try:
        ref = PolymarketCorpusSnapshotRef(
            arguments.snapshot_sha256,
            arguments.snapshot_size,
        )
        snapshot = PolymarketCorpusStore(arguments.workspace).load(ref)
        analysis = build_polymarket_development_analysis(
            snapshot,
            session_id=arguments.session_id,
        )
        receipts: list[dict[str, object]] = []
        for index, source_path in enumerate(arguments.source):
            source = source_path.read_text()
            source_sha256 = hashlib.sha256(source.encode()).hexdigest()
            observation = analysis.run(
                source=source,
                session_id=arguments.session_id,
                action_id=f"polymarket-development-study:{index}:{source_sha256}",
            )
            payload = _receipt_payload(
                analysis=analysis,
                source_path=source_path,
                source_sha256=source_sha256,
                observation=observation,
            )
            receipt_path = arguments.receipt_directory / f"{source_path.stem}.json"
            _persist_receipt(payload, receipt_path)
            receipts.append(payload)
        if any(item["status"] != AnalysisStatus.SUCCEEDED.value for item in receipts):
            print(json.dumps({"status": "FAILED", "receipts": receipts}, sort_keys=True))
            return 3
    except (OSError, TypeError, ValueError) as error:
        print(
            json.dumps(
                {
                    "status": "FAILED",
                    "error_code": "POLYMARKET_DEVELOPMENT_STUDY_FAILED",
                    "error_type": type(error).__name__,
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps({"status": "SUCCEEDED", "receipts": receipts}, sort_keys=True))
    return 0


def _receipt_payload(
    *, analysis: object, source_path: Path, source_sha256: str, observation: object
) -> dict[str, object]:
    from research_agent.data_adapters.polymarket.corpus_analysis import (  # noqa: PLC0415
        PolymarketDevelopmentAnalysis,
    )
    from research_agent.exploration import StructuredObservation  # noqa: PLC0415

    if not isinstance(analysis, PolymarketDevelopmentAnalysis) or not isinstance(
        observation, StructuredObservation
    ):
        msg = "study receipt requires exact analysis and observation records"
        raise TypeError(msg)
    if observation.status is AnalysisStatus.SUCCEEDED and observation.details is None:
        msg = "successful study details cannot remain only in an ephemeral artifact store"
        raise ValueError(msg)
    return {
        "status": observation.status.value,
        "epistemic_status": observation.epistemic_status,
        "snapshot_ref": analysis.partition.snapshot_ref,
        "partition_id": analysis.partition.partition_id,
        "partition_method": "whole-event-chronological-latest-resolution/v1",
        "development_event_count": len(analysis.partition.development_event_ids),
        "protected_event_count": analysis.partition.protected_event_count,
        "development_market_count": analysis.partition.development_market_count,
        "protected_market_count": analysis.partition.protected_market_count,
        "protected_values_exposed": False,
        "source_name": source_path.name,
        "source_sha256": source_sha256,
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
            "random_seed": observation.provenance.random_seed,
        },
        "formal_object_refs": list(observation.formal_object_refs),
        "durable_state_effects": list(observation.durable_state_effects),
    }


def _persist_receipt(payload: dict[str, object], path: Path) -> None:
    content = (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as receipt_file:
            receipt_file.write(content)
    except FileExistsError:
        if path.read_bytes() != content:
            msg = "study receipt path already contains different bytes"
            raise ValueError(msg) from None


if __name__ == "__main__":
    raise SystemExit(main())
