"""Run one authored study source over the exact whole-event development partition."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from research_agent.data_adapters.polymarket.corpus import (
    PolymarketCorpusSnapshotRef,
    PolymarketCorpusStore,
)
from research_agent.data_adapters.polymarket.corpus_analysis import (
    build_polymarket_development_analysis,
)
from research_agent.exploration import AnalysisStatus, ResourceLimits

_CORPUS_SHA256 = "184b83f7f8012da4ca9116c8b6bad2076570ad5f0bada95b22615ee2f5cceae8"
_CORPUS_SIZE = 428_280_682


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    arguments = parser.parse_args()
    source = arguments.source.read_text(encoding="utf-8")
    source_sha256 = hashlib.sha256(source.encode()).hexdigest()
    root = Path("data/chronos/polymarket-corpora")
    snapshot = PolymarketCorpusStore(root).load(
        PolymarketCorpusSnapshotRef(_CORPUS_SHA256, _CORPUS_SIZE)
    )
    limits = ResourceLimits(
        wall_time_seconds=180.0,
        max_inline_bytes=200_000,
        max_memory_bytes=4_294_967_296,
    )
    session_id = "polymarket-behavioral-development-2026-08-24"
    analysis = build_polymarket_development_analysis(
        snapshot,
        session_id=session_id,
        resource_limits=limits,
    )
    observation = analysis.run(
        source=source,
        session_id=session_id,
        action_id=f"polymarket-behavioral-development:{source_sha256}",
    )
    if observation.status is not AnalysisStatus.SUCCEEDED:
        raise RuntimeError(
            json.dumps(
                {
                    "status": observation.status.value,
                    "summary": observation.summary,
                    "stderr": observation.stderr_preview,
                }
            )
        )
    receipt = {
        "status": observation.status.value,
        "summary": observation.summary,
        "details": observation.details,
        "warnings": list(observation.warnings),
        "epistemic_status": observation.epistemic_status,
        "formal_object_refs": list(observation.formal_object_refs),
        "durable_state_effects": list(observation.durable_state_effects),
        "source_name": arguments.source.name,
        "source_sha256": source_sha256,
        "snapshot_ref": snapshot.ref.uri,
        "partition_id": analysis.partition.partition_id,
        "partition_method": analysis.partition.partition_method,
        "development_event_count": len(analysis.partition.development_event_ids),
        "development_market_count": analysis.partition.development_market_count,
        "protected_event_count": analysis.partition.protected_event_count,
        "protected_market_count": analysis.partition.protected_market_count,
        "protected_values_exposed": False,
        "resource_limits": {
            "wall_time_seconds": limits.wall_time_seconds,
            "max_inline_bytes": limits.max_inline_bytes,
            "max_memory_bytes": limits.max_memory_bytes,
            "max_output_bytes": limits.max_output_bytes,
            "max_result_bytes": limits.max_result_bytes,
            "max_source_bytes": limits.max_source_bytes,
        },
        "execution": {
            "action_id": observation.provenance.action_id,
            "code_sha256": observation.provenance.code_sha256,
            "random_seed": observation.provenance.random_seed,
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
    print(json.dumps(receipt, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    main()
