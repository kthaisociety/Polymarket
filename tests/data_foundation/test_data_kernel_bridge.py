"""Causal contracts for retained derived data entering the temporal kernel."""

# ruff: noqa: D103, PLR2004

from __future__ import annotations

import copy
import io
import json
from dataclasses import replace
from datetime import UTC, datetime
from email.message import Message
from typing import TYPE_CHECKING, Self, cast

import pytest

from research_agent.data_foundation import (
    ApprovedTemporalDataset,
    BoundaryStatus,
    FieldDefinition,
    InformationSetBuilder,
    TemporalDatasetProfile,
    TemporalRegistrationAuthority,
)
from research_agent.data_workspace import (
    DataWorkspace,
    DerivedDatasetRef,
    FetchRequest,
    FetchStatus,
)

if TYPE_CHECKING:
    from pathlib import Path


class _Response:
    def __init__(self, content: bytes) -> None:
        self._stream = io.BytesIO(content)
        self.status = 200
        self.headers = Message()
        self.headers["Content-Type"] = "application/json"
        self.headers["Content-Length"] = str(len(content))

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        del args

    def geturl(self) -> str:
        return "https://example.test/temporal.json"

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)


def _profile(*, dimensions: tuple[str, ...] = ()) -> TemporalDatasetProfile:
    return TemporalDatasetProfile(
        dataset_id="generic-temporal",
        schema_version="v1",
        environment_id="environment:generic",
        semantic_provenance_ref="semantics:approved-v1",
        availability_rule_version="availability:observed-release-v1",
        fields=(
            FieldDefinition(
                "x",
                "Predictor",
                "float",
                "index",
                dimensions,
                "A generic predictor with explicitly supplied temporal semantics.",
            ),
        ),
        mandatory_caveats=("REGISTERED_FROM_EXACT_DERIVED_SNAPSHOT",),
    )


def _envelope(profile: TemporalDatasetProfile) -> dict[str, object]:
    return {
        "schema_version": "temporal-observations/v1",
        "profile_id": profile.identity,
        "observations": [
            {
                "field_id": "x",
                "value": 2.5,
                "reference_time": "2025-01-31T00:00:00+00:00",
                "available_at": "2025-02-10T00:00:00+00:00",
                "vintage_id": "initial",
                "revision_number": 0,
                "dimensions": {},
                "caveats": ["SOURCE_DECLARED_CURRENT_VIEW"],
            }
        ],
    }


def _retained(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    payload: dict[str, object],
) -> tuple[DataWorkspace, DerivedDatasetRef]:
    content = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()

    def response(*args: object, **kwargs: object) -> _Response:
        del args, kwargs
        return _Response(content)

    monkeypatch.setattr(
        "research_agent.data_workspace.workspace.urllib.request.urlopen",
        response,
    )
    workspace = DataWorkspace(tmp_path / "workspace")
    fetched = workspace.fetch(FetchRequest("https://example.test/temporal.json"))
    assert fetched.status is FetchStatus.SUCCEEDED
    assert fetched.snapshot_ref is not None
    derived = workspace.derive(
        inputs={"source": fetched.snapshot_ref},
        source='payload = json_input("source")\nresult = emit(payload)',
        parameters={},
    )
    assert derived.dataset_ref is not None
    return workspace, derived.dataset_ref


def test_exact_approved_derived_envelope_registers_with_independent_time_semantics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = _profile()
    workspace, raw_ref = _retained(tmp_path, monkeypatch, _envelope(profile))
    approval = ApprovedTemporalDataset(
        derived_ref=raw_ref,
        profile=profile,
        approval_ref="review:data-steward:1",
    )
    authority = TemporalRegistrationAuthority((approval,))

    registration = authority.register(workspace, approval)
    catalog = authority.catalog((registration,))
    authority.require_catalog(catalog)
    field = registration.dataset.schema.field_ref("x")
    before = InformationSetBuilder().build(
        catalog.snapshot,
        decision_time=datetime(2025, 2, 9, tzinfo=UTC),
        requested_fields=(field,),
    )
    after = InformationSetBuilder().build(
        catalog.snapshot,
        decision_time=datetime(2025, 2, 10, tzinfo=UTC),
        requested_fields=(field,),
    )

    assert before.status is BoundaryStatus.INSUFFICIENT
    assert after.status is BoundaryStatus.READY
    assert after.observations[0].value == 2.5
    assert after.observations[0].source_ref == approval.derived_ref.uri
    assert after.observations[0].availability_rule_version == profile.availability_rule_version
    assert after.observations[0].caveats == (
        "REGISTERED_FROM_EXACT_DERIVED_SNAPSHOT",
        "SOURCE_DECLARED_CURRENT_VIEW",
    )


def test_authority_rejects_equal_approval_substitution_and_cannot_be_copied(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = _profile()
    workspace, raw_ref = _retained(tmp_path, monkeypatch, _envelope(profile))
    approval = ApprovedTemporalDataset(
        derived_ref=raw_ref,
        profile=profile,
        approval_ref="review:data-steward:1",
    )
    authority = TemporalRegistrationAuthority((approval,))

    with pytest.raises(TypeError, match="cannot be copied"):
        copy.copy(authority)
    with pytest.raises(TypeError, match="cannot be copied"):
        copy.deepcopy(authority)
    with pytest.raises(ValueError, match="not approved"):
        authority.register(workspace, replace(approval))


def test_changed_or_unhealthy_derived_bytes_fail_before_registration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = _profile()
    workspace, raw_ref = _retained(tmp_path, monkeypatch, _envelope(profile))
    approval = ApprovedTemporalDataset(
        derived_ref=raw_ref,
        profile=profile,
        approval_ref="review:data-steward:1",
    )
    authority = TemporalRegistrationAuthority((approval,))
    output = workspace.root / "objects" / approval.derived_ref.output_sha256
    output.write_bytes(b'{"invented":999}')

    with pytest.raises(ValueError, match="exact verified retained reference"):
        authority.register(workspace, approval)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"unknown": True}, "missing or unknown keys"),
        ({"available_at": "2025-02-10"}, "available_at"),
        ({"dimensions": {"region": "A"}}, "dimensions differ"),
        ({"value": "2.5"}, "does not match field type"),
    ],
)
def test_temporal_envelope_fails_closed_on_ambiguous_scientific_meaning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: dict[str, object],
    message: str,
) -> None:
    profile = _profile()
    payload = _envelope(profile)
    observations = cast("list[object]", payload["observations"])
    observation = cast("dict[str, object]", observations[0])
    observation.update(mutation)
    workspace, raw_ref = _retained(tmp_path, monkeypatch, payload)
    approval = ApprovedTemporalDataset(
        derived_ref=raw_ref,
        profile=profile,
        approval_ref="review:data-steward:1",
    )

    with pytest.raises(ValueError, match=message):
        TemporalRegistrationAuthority((approval,)).register(workspace, approval)


def test_authoritative_catalog_rejects_equal_reconstructed_attestation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = _profile()
    workspace, raw_ref = _retained(tmp_path, monkeypatch, _envelope(profile))
    approval = ApprovedTemporalDataset(
        derived_ref=raw_ref,
        profile=profile,
        approval_ref="review:data-steward:1",
    )
    authority = TemporalRegistrationAuthority((approval,))
    registration = authority.register(workspace, approval)
    catalog = authority.catalog((registration,))

    with pytest.raises(ValueError, match="not issued"):
        authority.require_catalog(replace(catalog))
