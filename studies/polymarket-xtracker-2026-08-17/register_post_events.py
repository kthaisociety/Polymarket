"""Register one exact retained XTracker temporal envelope and emit a value-free audit."""

# ruff: noqa: INP001, T201

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from research_agent.data_foundation import (
    ApprovedTemporalDataset,
    FieldDefinition,
    InformationSetBuilder,
    TemporalDatasetProfile,
    TemporalRegistrationAuthority,
)
from research_agent.data_workspace import DataWorkspace, DerivedDatasetRef


def _profile() -> TemporalDatasetProfile:
    return TemporalDatasetProfile(
        dataset_id="polymarket-xtracker-post-events",
        schema_version="v1",
        environment_id="bdl-polymarket-production-readonly",
        semantic_provenance_ref="https://xtracker.polymarket.com/docs@2026-08-17",
        availability_rule_version="xtracker-imported-at/v1",
        fields=(
            FieldDefinition(
                "post_imported",
                "XTracker observed post event",
                "integer",
                "post",
                ("event_id", "tracking_id", "user_handle", "platform", "platform_post_id"),
                "One post present in the exact retained XTracker response; reference time is the "
                "platform creation timestamp and availability is the later XTracker import "
                "timestamp.",
            ),
        ),
        mandatory_caveats=(
            "XTRACKER_IMPORTED_AT_IS_CONSERVATIVE_AVAILABILITY",
            "CURRENT_API_SNAPSHOT_MAY_OMIT_DELETED_OR_REVISED_POSTS",
            "POST_CONTENT_EXCLUDED_FROM_DERIVED_DATASET",
        ),
    )


def main() -> None:
    """Register the exact derived envelope and print its sanitized audit identity."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--derived", required=True)
    arguments = parser.parse_args()

    workspace = DataWorkspace(arguments.workspace)
    resolved = workspace.resolve(arguments.derived)
    if not isinstance(resolved, DerivedDatasetRef):
        msg = "--derived must resolve to an exact derived dataset"
        raise TypeError(msg)

    profile = _profile()
    approval = ApprovedTemporalDataset(
        derived_ref=resolved,
        profile=profile,
        approval_ref="work-packet:polymarket.test-xtracker-post-count-signal@bbb79f2b",
    )
    authority = TemporalRegistrationAuthority((approval,))
    registration = authority.register(workspace, approval)
    catalog = authority.catalog((registration,))
    authority.require_catalog(catalog)

    observations = registration.dataset.observations
    field = registration.dataset.schema.field_ref("post_imported")
    before = InformationSetBuilder().build(
        catalog.snapshot,
        decision_time=min(item.available_at for item in observations),
        requested_fields=(field,),
    )
    end = InformationSetBuilder().build(
        catalog.snapshot,
        decision_time=datetime(2026, 7, 27, 15, 59, 59, tzinfo=UTC),
        requested_fields=(field,),
    )
    payload = {
        "schema_version": "xtracker-temporal-registration-audit/v1",
        "epistemic_status": "REGISTERED_DEVELOPMENT_DATA_NOT_A_RESEARCH_RESULT",
        "derived_ref": resolved.uri,
        "profile_id": profile.identity,
        "schema_id": registration.dataset.schema.identity,
        "registration_attestation_id": registration.attestation_id,
        "registration_id": registration.dataset.registration_id,
        "catalog_attestation_id": catalog.catalog_attestation_id,
        "catalog_snapshot_id": catalog.snapshot.identity,
        "observation_count": len(observations),
        "reference_time_min": min(item.reference_time for item in observations).isoformat(),
        "reference_time_max": max(item.reference_time for item in observations).isoformat(),
        "available_at_min": min(item.available_at for item in observations).isoformat(),
        "available_at_max": max(item.available_at for item in observations).isoformat(),
        "maximum_import_delay_seconds": max(
            (item.available_at - item.reference_time).total_seconds() for item in observations
        ),
        "information_set_at_first_import_count": len(before.observations),
        "information_set_at_market_end_count": len(end.observations),
        "protected_data_accessed": False,
        "caveats": list(profile.mandatory_caveats),
    }
    print(json.dumps(payload, allow_nan=False, sort_keys=True))


if __name__ == "__main__":
    main()
