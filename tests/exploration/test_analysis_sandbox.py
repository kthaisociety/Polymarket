"""Adversarial contract tests for the exploration execution boundary."""

from __future__ import annotations

import pytest

from research_agent.exploration import (
    AnalysisHarness,
    AnalysisRequest,
    AnalysisStatus,
    ArtifactKind,
    ArtifactStore,
    AuthorizedDataView,
    CapabilityPolicy,
    DataAccessRequest,
    ResourceLimits,
)


def _view() -> AuthorizedDataView:
    return AuthorizedDataView(
        view_id="development-view",
        dataset_ref="dataset-v1",
        environment_ref="environment-v1@1",
        fields={
            "signal": (1.0, 2.0, 3.0),
            "unused": (10.0, 11.0, 12.0),
            "restricted": (99.0,),
        },
    )


def _harness(*, limits: ResourceLimits | None = None) -> AnalysisHarness:
    return AnalysisHarness(
        views={"development-view": _view()},
        policy=CapabilityPolicy(
            session_id="session-1",
            environment_ref="environment-v1@1",
            allowed_fields_by_view={"development-view": frozenset({"signal", "unused"})},
        ),
        artifacts=ArtifactStore(),
        resource_limits=limits or ResourceLimits(),
    )


def _request(code: str, *fields: str) -> AnalysisRequest:
    return AnalysisRequest(
        session_id="session-1",
        action_id="analysis-1",
        source=code,
        data_access=(DataAccessRequest("development-view", tuple(fields)),),
    )


def test_actual_access_overrides_self_reported_provenance() -> None:
    """Authored provenance cannot replace instrumented access facts."""
    harness = _harness()
    observation = harness.run(
        _request(
            """
values = read("development-view", "signal")
result = structured_return(
    "calculated a mean",
    {"mean": sum(values) / len(values)},
    claimed_provenance={"fields": ["restricted"], "dataset": "invented"},
)
""",
            "signal",
            "unused",
        )
    )

    assert observation.status is AnalysisStatus.SUCCEEDED
    assert observation.details == {"mean": 2.0}
    assert [(access.view_id, access.field_id) for access in observation.provenance.accesses] == [
        ("development-view", "signal")
    ]
    assert observation.provenance.dataset_refs == ("dataset-v1",)
    assert "self-reported provenance was ignored" in observation.warnings


def test_pure_log_and_exp_support_authored_boundary_transforms() -> None:
    """Boundary-aware research can author a true logit without host interfaces."""
    observation = _harness().run(
        _request(
            """
values = read("development-view", "signal")
probability = values[0] / 4.0
logit = log(probability / (1.0 - probability))
recovered = 1.0 / (1.0 + exp(-logit))
result = structured_return("pure logit", {"logit": logit, "recovered": recovered})
""",
            "signal",
        )
    )

    assert observation.status is AnalysisStatus.SUCCEEDED
    assert observation.details is not None
    assert observation.details["logit"] == pytest.approx(-1.0986122886681098)
    assert observation.details["recovered"] == pytest.approx(0.25)


def test_policy_denies_requested_field_without_exposing_values() -> None:
    """Policy denial occurs without returning the requested field value."""
    harness = _harness()
    observation = harness.run(
        _request(
            'result = structured_return("should not run", {"value": 99.0})',
            "restricted",
        )
    )

    assert observation.status is AnalysisStatus.DENIED
    assert observation.recoverable is False
    assert observation.provenance.accesses == ()
    assert "99.0" not in observation.summary
    assert observation.artifact_refs == ()


def test_protected_view_is_never_an_exploration_capability() -> None:
    """A field allow-list cannot turn a protected view into development data."""
    protected_view = AuthorizedDataView(
        view_id="protected-view",
        dataset_ref="protected-v1",
        environment_ref="environment-v1@1",
        fields={"target": (123.0,)},
        protected=True,
    )
    harness = AnalysisHarness(
        views={"protected-view": protected_view},
        policy=CapabilityPolicy(
            session_id="session-1",
            environment_ref="environment-v1@1",
            allowed_fields_by_view={"protected-view": frozenset({"target"})},
        ),
        artifacts=ArtifactStore(),
    )
    observation = harness.run(
        AnalysisRequest(
            session_id="session-1",
            action_id="analysis-protected",
            source='result = structured_return("must not run", {})',
            data_access=(DataAccessRequest("protected-view", ("target",)),),
        )
    )

    assert observation.status is AnalysisStatus.DENIED
    assert observation.provenance.accesses == ()


def test_runtime_surface_describes_only_exact_value_free_capability_grants() -> None:
    """Context discovery exposes usable identities, never values or disallowed fields."""
    surface = _harness().authorized_runtime_surfaces(
        session_id="session-1",
        environment_ref="environment-v1@1",
        readable_dataset_refs=("dataset-v1",),
        protected_resource_refs=(),
        investigation_dataset_refs=frozenset({"dataset-v1"}),
    )

    assert len(surface) == 1
    assert surface[0].view_id == "development-view"
    assert surface[0].dataset_ref == "dataset-v1"
    assert surface[0].environment_ref == "environment-v1@1"
    assert surface[0].field_ids == ("signal", "unused")
    assert not hasattr(surface[0], "fields")


def test_runtime_surface_fails_closed_for_foreign_or_protected_scope() -> None:
    """Capability discovery cannot launder session, catalog, or protected authority."""
    harness = _harness()
    with pytest.raises(PermissionError, match="runtime authority"):
        harness.authorized_runtime_surfaces(
            session_id="foreign-session",
            environment_ref="environment-v1@1",
            readable_dataset_refs=("dataset-v1",),
            protected_resource_refs=(),
            investigation_dataset_refs=frozenset({"dataset-v1"}),
        )
    assert (
        harness.authorized_runtime_surfaces(
            session_id="session-1",
            environment_ref="environment-v1@1",
            readable_dataset_refs=("dataset-v1",),
            protected_resource_refs=("dataset-v1",),
            investigation_dataset_refs=frozenset({"dataset-v1"}),
        )
        == ()
    )


def test_runtime_data_probe_outside_exact_grant_is_denied() -> None:
    """Executed code cannot widen a previously issued data grant."""
    harness = _harness()
    observation = harness.run(
        _request(
            """
read("development-view", "unused")
result = structured_return("should not succeed", {})
""",
            "signal",
        )
    )

    assert observation.status is AnalysisStatus.DENIED
    assert observation.recoverable is False
    assert observation.provenance.accesses == ()
    assert "unused" not in observation.summary


def test_host_resource_interfaces_are_not_available() -> None:
    """Imports and host filesystem entry points are absent from the language subset."""
    harness = _harness()

    import_attempt = harness.run(_request("import os\nresult = structured_return('x', {})"))
    file_attempt = harness.run(
        _request("value = open('/etc/passwd').read()\nresult = structured_return('x', {})")
    )

    assert import_attempt.status is AnalysisStatus.DENIED
    assert file_attempt.status is AnalysisStatus.DENIED
    assert import_attempt.provenance.accesses == ()
    assert file_attempt.provenance.accesses == ()


def test_operational_exception_is_recoverable_with_full_traceback_artifact() -> None:
    """Operational failure remains concise, recoverable, and fully drillable."""
    harness = _harness()
    observation = harness.run(
        _request(
            """
values = read("development-view", "signal")
failure = values[0] / 0
result = structured_return("unreachable", {"failure": failure})
""",
            "signal",
        )
    )

    assert observation.status is AnalysisStatus.FAILED
    assert observation.recoverable is True
    assert "ZeroDivisionError" in observation.summary
    assert "Traceback" not in observation.summary
    traceback_ref = next(
        ref for ref in observation.artifact_refs if ref.kind is ArtifactKind.TRACEBACK
    )
    traceback = harness.artifacts.read(traceback_ref, session_id="session-1").decode()
    assert "Traceback (most recent call last)" in traceback
    assert "ZeroDivisionError" in traceback
    assert "failure = values[0] / 0" in traceback


def test_large_stdout_and_result_details_stay_out_of_observation() -> None:
    """Large content remains external while a bounded preview survives."""
    printed_bytes = 4096
    limits = ResourceLimits(max_inline_bytes=128, max_output_bytes=16_000)
    harness = _harness(limits=limits)
    observation = harness.run(
        _request(
            """
print("z" * 4096)
result = structured_return("large diagnostic", {"table": [1] * 2048})
"""
        )
    )

    assert observation.status is AnalysisStatus.SUCCEEDED
    assert observation.details is None
    assert len(observation.stdout_preview.encode()) <= limits.max_inline_bytes
    stdout_ref = next(ref for ref in observation.artifact_refs if ref.kind is ArtifactKind.STDOUT)
    details_ref = next(ref for ref in observation.artifact_refs if ref.kind is ArtifactKind.RESULT)
    assert len(harness.artifacts.read(stdout_ref, session_id="session-1")) > printed_bytes
    assert b'"table"' in harness.artifacts.read(details_ref, session_id="session-1")


def test_exploration_cannot_create_formal_identity_or_durable_state_effect() -> None:
    """A successful analysis is still provisional and effect-free."""
    harness = _harness()
    observation = harness.run(
        _request('result = structured_return("candidate idea", {"formula": "x * 2"})')
    )

    assert observation.status is AnalysisStatus.SUCCEEDED
    assert observation.epistemic_status == "EXPLORATORY"
    assert observation.formal_object_refs == ()
    assert observation.durable_state_effects == ()


def test_timeout_is_explicit_and_recoverable() -> None:
    """The parent terminates an analysis that exceeds its wall-clock budget."""
    harness = _harness(limits=ResourceLimits(wall_time_seconds=0.05))
    observation = harness.run(_request("while True:\n    pass"))

    assert observation.status is AnalysisStatus.FAILED
    assert observation.recoverable is True
    assert "time limit" in observation.summary
