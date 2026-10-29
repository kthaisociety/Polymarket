"""Rerun the fixed five-minute stochastic falsifier through campaign authority."""

# ruff: noqa: INP001, T201

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast

from research_agent.data_adapters.polymarket import (
    PolymarketCorpusSnapshotRef,
    PolymarketCorpusStore,
    PolymarketPriceHistoryNeed,
    PolymarketRegisteredEventField,
    build_polymarket_campaign_analysis,
    build_polymarket_replication_analysis,
    register_retained_price_history,
)
from research_agent.data_workspace import DataWorkspace
from research_agent.exploration import (
    AnalysisDisposition,
    CampaignManifest,
    CampaignStore,
    EvidenceTier,
    ResearchCampaignAuthority,
    ResourceLimits,
)

_EXPECTED_NEEDS = tuple(f"event-{number:03d}.json" for number in range(10, 146, 15))


def main() -> int:
    """Reopen exact registrations, execute one source, and close its campaign."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-workspace", required=True, type=Path)
    parser.add_argument("--data-workspace", required=True, type=Path)
    parser.add_argument("--need-directory", required=True, type=Path)
    parser.add_argument("--acquisition-receipt", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--campaign-directory", required=True, type=Path)
    arguments = parser.parse_args()

    acquisition = cast(
        "dict[str, object]", json.loads(arguments.acquisition_receipt.read_bytes())
    )
    slices = cast("list[dict[str, object]]", acquisition.get("slices"))
    if (
        acquisition.get("schema_version")
        != "polymarket-fixed-clob-acquisition-receipt/v1"
        or acquisition.get("status") != "succeeded"
        or not isinstance(slices, list)
        or len(slices) != len(_EXPECTED_NEEDS)
    ):
        message = "fixed CLOB campaign requires the exact successful acquisition receipt"
        raise ValueError(message)

    workspace = DataWorkspace(arguments.data_workspace)
    registered_fields = []
    view_ids = []
    for expected_name, raw_slice in zip(_EXPECTED_NEEDS, slices, strict=True):
        if raw_slice.get("need_file") != expected_name or raw_slice.get("status") != "succeeded":
            message = "fixed CLOB acquisition slice identity changed"
            raise ValueError(message)
        need = PolymarketPriceHistoryNeed.from_dict(
            json.loads((arguments.need_directory / expected_name).read_text())
        )
        registration = register_retained_price_history(
            workspace,
            need=need,
            source_ref_uri=cast("str", raw_slice["source_ref"]),
            derived_ref_uri=cast("str", raw_slice["derived_ref"]),
        )
        if registration.attestation_id != raw_slice.get("registration_attestation_id"):
            message = "fixed CLOB registration attestation changed"
            raise ValueError(message)
        view_id = f"polymarket-clob-five-minute-{expected_name.removesuffix('.json')}"
        view_ids.append(view_id)
        registered_fields.append(
            PolymarketRegisteredEventField(
                view_id=view_id,
                registration=registration,
                field_id="market_probability",
            )
        )

    corpus_store = PolymarketCorpusStore(arguments.corpus_workspace)
    snapshot = corpus_store.load(
        PolymarketCorpusSnapshotRef(
            "8c73260377ea5cb3e569bbc3c744ce9b62a95c8f54dafb73d07671845ccec4c6",
            318684407,
        )
    )
    ancestor = corpus_store.load(
        PolymarketCorpusSnapshotRef(
            "610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f",
            19434443,
        )
    )
    session_id = "polymarket-enforced-five-minute-reproduction-2026-08-24"
    analysis = build_polymarket_replication_analysis(
        snapshot,
        ancestor,
        session_id=session_id,
        registered_event_fields=tuple(registered_fields),
        resource_limits=ResourceLimits(
            wall_time_seconds=300.0,
            max_memory_bytes=4_000_000_000,
            max_inline_bytes=500_000,
            max_result_bytes=4_000_000,
        ),
    )
    required_accesses = (
        ("polymarket-development-prices", "market_id"),
        ("polymarket-development-prices", "observed_at_epoch_seconds"),
        ("polymarket-development-prices", "market_probability"),
        *tuple(
            (view_id, field_id)
            for view_id in view_ids
            for field_id in (
                "market_id",
                "event_id",
                "fidelity_minutes",
                "reference_time_epoch_seconds",
                "available_at_epoch_seconds",
                "market_probability",
            )
        ),
    )
    source = arguments.source.read_text()
    campaign_analysis = build_polymarket_campaign_analysis(
        analysis_id="stochastic.paper.five-minute-measurement-falsifier.v1",
        family="stochastic-process",
        source=source,
        development_analysis=analysis,
        evidence_tier=EvidenceTier.EXPOSED_REPRODUCTION,
        required_accesses=required_accesses,
    )
    authority = ResearchCampaignAuthority(
        CampaignManifest(
            "polymarket-five-minute-enforced-reproduction-2026-08-24",
            "Reproduce the fixed five-minute measurement falsifier without restoring freshness.",
            (campaign_analysis,),
        ),
        store=CampaignStore(arguments.campaign_directory),
    )
    execution = authority.execute(
        campaign_analysis.analysis_id,
        harness=analysis.harness,
        session_id=session_id,
    )
    completion = authority.complete(
        {campaign_analysis.analysis_id: AnalysisDisposition.RETAINED}
    )
    print(
        json.dumps(
            {
                "status": "SUCCEEDED",
                "execution_receipt_id": execution.receipt_id,
                "completion_receipt_id": completion.receipt_id,
                "admissible": execution.admissible,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
