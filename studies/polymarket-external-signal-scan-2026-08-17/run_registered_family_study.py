"""Register exact XTracker family events and compose one development analysis."""

# ruff: noqa: D103, EM101, INP001, T201, TRY003

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Final

from research_agent.data_adapters.polymarket import (
    PolymarketCorpusSnapshotRef,
    PolymarketCorpusStore,
    PolymarketRegisteredEventField,
    build_polymarket_development_analysis,
)
from research_agent.data_foundation import (
    ApprovedTemporalDataset,
    FieldDefinition,
    TemporalDatasetProfile,
    TemporalRegistrationAuthority,
)
from research_agent.data_workspace import DataWorkspace, DerivedDatasetRef
from research_agent.exploration import AnalysisStatus

ALIASES: Final[tuple[str, ...]] = (
    "cz",
    "zelenskyy",
    "nyc_mayor",
    "khamenei",
    "ted_cruz",
)


def _profile(alias: str) -> TemporalDatasetProfile:
    if alias not in ALIASES:
        raise ValueError(alias)
    return TemporalDatasetProfile(
        dataset_id=f"polymarket-xtracker-{alias.replace('_', '-')}-post-events",
        schema_version="v1",
        environment_id="polymarket-production-readonly",
        semantic_provenance_ref="https://xtracker.polymarket.com/docs@2026-08-17",
        availability_rule_version="xtracker-imported-at/v1",
        fields=(
            FieldDefinition(
                "post_imported",
                "XTracker observed post event",
                "integer",
                "post",
                ("event_id", "user_handle", "platform", "platform_post_id"),
                "One post present in an exact retained XTracker response; reference time is the "
                "platform creation timestamp and availability is the later XTracker import "
                "timestamp.",
            ),
        ),
        mandatory_caveats=(
            "XTRACKER_IMPORTED_AT_IS_CONSERVATIVE_AVAILABILITY",
            "CURRENT_API_SNAPSHOT_MAY_OMIT_DELETED_OR_REVISED_POSTS",
            "POST_CONTENT_EXCLUDED_FROM_DERIVED_DATASET",
            "OVERLAPPING_EVENT_WINDOWS_DUPLICATE_POSTS_ONLY_ACROSS_EXACT_EVENT_DIMENSIONS",
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-workspace", type=Path, required=True)
    parser.add_argument("--snapshot-sha256", required=True)
    parser.add_argument("--snapshot-size", type=int, required=True)
    parser.add_argument("--data-workspace", type=Path, required=True)
    parser.add_argument("--derived", action="append", required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    arguments = parser.parse_args()

    snapshot = PolymarketCorpusStore(arguments.corpus_workspace).load(
        PolymarketCorpusSnapshotRef(arguments.snapshot_sha256, arguments.snapshot_size)
    )
    workspace = DataWorkspace(arguments.data_workspace)
    derived_uris: dict[str, str] = {}
    for value in arguments.derived:
        alias, separator, uri = value.partition("=")
        if separator != "=" or alias not in ALIASES or alias in derived_uris:
            raise ValueError("--derived must provide each exact alias once")
        derived_uris[alias] = uri
    if set(derived_uris) != set(ALIASES):
        raise ValueError("--derived must provide all exact XTracker family aliases")
    resolved_by_alias = {alias: workspace.resolve(uri) for alias, uri in derived_uris.items()}
    if any(not isinstance(item, DerivedDatasetRef) for item in resolved_by_alias.values()):
        raise TypeError("every --derived value must resolve to an exact derived dataset")
    profiles = {alias: _profile(alias) for alias in ALIASES}
    approvals = tuple(
        ApprovedTemporalDataset(
            derived_ref=resolved_by_alias[alias],
            profile=profiles[alias],
            approval_ref=(
                "work-packet:polymarket.scan-development-external-signal-candidates@43bb5c5c"
            ),
        )
        for alias in ALIASES
    )
    authority = TemporalRegistrationAuthority(approvals)
    registrations = tuple(authority.register(workspace, item) for item in approvals)
    catalog = authority.catalog(registrations)
    authority.require_catalog(catalog)
    supplements = tuple(
        PolymarketRegisteredEventField(
            view_id=f"polymarket-xtracker-{alias}-posts",
            registration=registrations[ordinal],
            field_id="post_imported",
        )
        for ordinal, alias in enumerate(ALIASES)
    )
    session_id = "polymarket-xtracker-family-development-2026-08-17"
    analysis = build_polymarket_development_analysis(
        snapshot,
        session_id=session_id,
        registered_event_fields=supplements,
    )
    source = arguments.source.read_text()
    source_sha256 = hashlib.sha256(source.encode()).hexdigest()
    observation = analysis.run(
        source=source,
        session_id=session_id,
        action_id=f"polymarket-xtracker-family-study:{source_sha256}",
    )
    if observation.status is AnalysisStatus.SUCCEEDED and observation.details is None:
        raise ValueError("successful details cannot remain only in ephemeral storage")
    payload = {
        "status": observation.status.value,
        "epistemic_status": observation.epistemic_status,
        "snapshot_ref": analysis.partition.snapshot_ref,
        "partition_id": analysis.partition.partition_id,
        "development_event_count": len(analysis.partition.development_event_ids),
        "development_market_count": analysis.partition.development_market_count,
        "protected_event_count": analysis.partition.protected_event_count,
        "protected_market_count": analysis.partition.protected_market_count,
        "protected_values_exposed": False,
        "registered_external_fields": [
            {
                "alias": alias,
                "derived_ref": resolved_by_alias[alias].uri,
                "profile_id": profiles[alias].identity,
                "registration_attestation_id": registrations[ordinal].attestation_id,
                "catalog_attestation_id": catalog.catalog_attestation_id,
                "view_id": supplements[ordinal].view_id,
                "field_id": supplements[ordinal].field_id,
            }
            for ordinal, alias in enumerate(ALIASES)
        ],
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
    content = (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode()
    arguments.receipt.parent.mkdir(parents=True, exist_ok=True)
    try:
        with arguments.receipt.open("xb") as receipt_file:
            receipt_file.write(content)
    except FileExistsError:
        if arguments.receipt.read_bytes() != content:
            raise ValueError("receipt path already contains different bytes") from None
    print(json.dumps(payload, sort_keys=True))
    if observation.status is not AnalysisStatus.SUCCEEDED:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
