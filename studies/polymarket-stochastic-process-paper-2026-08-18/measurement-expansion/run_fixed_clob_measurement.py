"""Reopen the exact retained CLOB panel and run one authored measurement source."""

# ruff: noqa: EM101, INP001, T201, TRY003

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import cast

from research_agent.data_adapters.polymarket import (
    PolymarketCorpusSnapshotRef,
    PolymarketCorpusStore,
    PolymarketPriceHistoryNeed,
    PolymarketRegisteredEventField,
    build_polymarket_replication_analysis,
    register_retained_price_history,
)
from research_agent.exploration import AnalysisStatus, ResourceLimits

_EXPECTED_NEEDS = (
    "event-010.json",
    "event-025.json",
    "event-040.json",
    "event-055.json",
    "event-070.json",
    "event-085.json",
    "event-100.json",
    "event-115.json",
    "event-130.json",
    "event-145.json",
)


def _persist(payload: dict[str, object], path: Path) -> None:
    content = (
        json.dumps(payload, allow_nan=False, separators=(",", ":"), sort_keys=True) + "\n"
    ).encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as receipt_file:
            receipt_file.write(content)
    except FileExistsError:
        if path.read_bytes() != content:
            raise ValueError("measurement study receipt already contains different bytes") from None


def main() -> int:
    """Verify exact retained authority, execute the authored source, and retain its receipt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-workspace", required=True, type=Path)
    parser.add_argument("--snapshot-sha256", required=True)
    parser.add_argument("--snapshot-size", required=True, type=int)
    parser.add_argument("--ancestor-snapshot-sha256", required=True)
    parser.add_argument("--ancestor-snapshot-size", required=True, type=int)
    parser.add_argument("--data-workspace", required=True, type=Path)
    parser.add_argument("--need-directory", required=True, type=Path)
    parser.add_argument("--acquisition-receipt", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--session-id", default="polymarket-five-minute-measurement-2026-08-18")
    arguments = parser.parse_args()

    acquisition_bytes = arguments.acquisition_receipt.read_bytes()
    acquisition = cast("dict[str, object]", json.loads(acquisition_bytes))
    slices = cast("list[dict[str, object]]", acquisition.get("slices"))
    if (
        acquisition.get("schema_version") != "polymarket-fixed-clob-acquisition-receipt/v1"
        or acquisition.get("status") != "succeeded"
        or acquisition.get("requested_slice_count") != len(_EXPECTED_NEEDS)
        or acquisition.get("succeeded_slice_count") != len(_EXPECTED_NEEDS)
        or acquisition.get("sample_values_emitted") is not False
        or acquisition.get("production_database_writes") is not False
        or not isinstance(slices, list)
        or len(slices) != len(_EXPECTED_NEEDS)
    ):
        raise ValueError("measurement study requires the exact successful acquisition receipt")

    from research_agent.data_workspace import DataWorkspace  # noqa: PLC0415

    workspace = DataWorkspace(arguments.data_workspace)
    registered_fields = []
    registration_ids = []
    for expected_name, raw_slice in zip(_EXPECTED_NEEDS, slices, strict=True):
        if raw_slice.get("need_file") != expected_name or raw_slice.get("status") != "succeeded":
            raise ValueError("measurement acquisition slice order or status changed")
        need = PolymarketPriceHistoryNeed.from_dict(
            json.loads((arguments.need_directory / expected_name).read_text())
        )
        if raw_slice.get("need_id") != need.need_id:
            raise ValueError("measurement need identity differs from acquisition")
        registration = register_retained_price_history(
            workspace,
            need=need,
            source_ref_uri=cast("str", raw_slice.get("source_ref")),
            derived_ref_uri=cast("str", raw_slice.get("derived_ref")),
        )
        if registration.attestation_id != raw_slice.get("registration_attestation_id"):
            raise ValueError("reopened registration differs from acquisition attestation")
        view_id = f"polymarket-clob-five-minute-{expected_name.removesuffix('.json')}"
        registered_fields.append(
            PolymarketRegisteredEventField(
                view_id=view_id,
                registration=registration,
                field_id="market_probability",
            )
        )
        registration_ids.append(registration.attestation_id)

    corpus_store = PolymarketCorpusStore(arguments.corpus_workspace)
    snapshot = corpus_store.load(
        PolymarketCorpusSnapshotRef(arguments.snapshot_sha256, arguments.snapshot_size)
    )
    ancestor = corpus_store.load(
        PolymarketCorpusSnapshotRef(
            arguments.ancestor_snapshot_sha256,
            arguments.ancestor_snapshot_size,
        )
    )
    analysis = build_polymarket_replication_analysis(
        snapshot,
        ancestor,
        session_id=arguments.session_id,
        registered_event_fields=tuple(registered_fields),
        resource_limits=ResourceLimits(
            wall_time_seconds=180.0,
            max_memory_bytes=4_000_000_000,
            max_inline_bytes=500_000,
            max_result_bytes=4_000_000,
        ),
    )
    source = arguments.source.read_text()
    source_sha256 = hashlib.sha256(source.encode()).hexdigest()
    observation = analysis.run(
        source=source,
        session_id=arguments.session_id,
        action_id=f"polymarket-fixed-clob-measurement:{source_sha256}",
    )
    payload: dict[str, object] = {
        "status": observation.status.value,
        "epistemic_status": observation.epistemic_status,
        "snapshot_ref": analysis.partition.snapshot_ref,
        "ancestor_snapshot_ref": analysis.partition.ancestor_snapshot_ref,
        "partition_id": analysis.partition.partition_id,
        "partition_method": analysis.partition.partition_method,
        "development_event_count": len(analysis.partition.development_event_ids),
        "protected_event_count": analysis.partition.protected_event_count,
        "development_market_count": analysis.partition.development_market_count,
        "protected_market_count": analysis.partition.protected_market_count,
        "protected_values_exposed": False,
        "acquisition_receipt_sha256": hashlib.sha256(acquisition_bytes).hexdigest(),
        "registration_attestation_ids": registration_ids,
        "source_name": arguments.source.name,
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
    _persist(payload, arguments.receipt)
    print(json.dumps(payload, allow_nan=False, sort_keys=True))
    return 0 if observation.status is AnalysisStatus.SUCCEEDED else 3


if __name__ == "__main__":
    raise SystemExit(main())
