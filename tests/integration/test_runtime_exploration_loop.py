"""Whole-loop proofs for the runtime-to-exploration integration seam."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import TYPE_CHECKING, cast

import pytest

from research_agent.exploration import (
    AnalysisHarness,
    ArtifactKind,
    ArtifactRef,
    ArtifactStore,
    AuthorizedDataView,
    CapabilityPolicy,
    ResourceLimits,
)
from research_agent.runtime.capabilities import (
    ActionRouter,
    DatasetRepository,
    make_toy_monthly_dataset,
)
from research_agent.runtime.commit import CommitCoordinator
from research_agent.runtime.context import ContextBuilder
from research_agent.runtime.engine import AutonomousResearchRuntime
from research_agent.runtime.initialization import ResearchRuntimeInitializer
from research_agent.runtime.models import (
    AnalysisExecutionProvenance,
    ObservationStatus,
)
from research_agent.runtime.provider import ModelProvider, ModelResponse
from research_agent.runtime.store import InMemoryRuntimeStore
from tests.runtime.support import confirmed_toy_task, toy_environment

if TYPE_CHECKING:
    from research_agent.runtime.models import ContextPacket, RuntimeInitialization

EXPECTED_MEAN = 2.0
EXPECTED_LARGE_ARTIFACTS = 2
EPISODE_TURN_BOUND = 3


def _analysis_response(  # noqa: PLR0913
    session_id: str,
    episode_id: str,
    *,
    action_id: str,
    source: str,
    view_id: str = "development-view",
    field_ids: tuple[str, ...] = ("signal",),
) -> Mapping[str, object]:
    return {
        "action": {
            "kind": "run_analysis",
            "action_id": action_id,
            "session_id": session_id,
            "episode_id": episode_id,
            "arguments": {
                "source": source,
                "data_access": [{"view_id": view_id, "field_ids": list(field_ids)}],
                "random_seed": 7,
            },
        }
    }


class ObservationDrivenProvider:
    """Choose every action from the rebuilt packet, never retained transcript state."""

    def __init__(self, session_id: str, episode_id: str) -> None:
        """Bind model-claimed identities; tests may rebind before the first call."""
        self._session_id = session_id
        self._episode_id = episode_id
        self.packets: list[ContextPacket] = []

    def complete(self, packet: ContextPacket) -> ModelResponse:
        """Use only the supplied packet to choose the next analysis."""
        self.packets.append(packet)
        if not packet.working_observations:
            action = _analysis_response(
                self._session_id,
                self._episode_id,
                action_id="analysis-mean",
                source=(
                    'values = read("development-view", "signal")\n'
                    'result = structured_return("mean is two", '
                    '{"mean": sum(values) / len(values)})'
                ),
            )["action"]
        else:
            details = packet.working_observations[-1].payload.get("details")
            typed_details: Mapping[str, object]
            if isinstance(details, Mapping):
                typed_details = cast("Mapping[str, object]", details)
            else:
                typed_details = {}
            mean = typed_details.get("mean")
            marker = "used-mean" if mean == EXPECTED_MEAN else "missing-mean"
            action = _analysis_response(
                self._session_id,
                self._episode_id,
                action_id=f"analysis-{marker}",
                source=f'result = structured_return("{marker}", {{"decision": "{marker}"}})',
                field_ids=(),
            )["action"]
        assert isinstance(action, Mapping)
        return ModelResponse("", cast("Mapping[str, object]", action), {})

    def bind(self, session_id: str, episode_id: str) -> None:
        """Set the exact initialized identities before provider execution."""
        self._session_id = session_id
        self._episode_id = episode_id


class RepairingProvider:
    """Repair only when the rebuilt packet contains a repairable analysis failure."""

    def __init__(self, session_id: str, episode_id: str) -> None:
        """Bind the exact runtime identities used in authored actions."""
        self._session_id = session_id
        self._episode_id = episode_id

    def complete(self, packet: ContextPacket) -> ModelResponse:
        """Choose the repaired source only from the prior structured failure."""
        failed = bool(
            packet.working_observations
            and packet.working_observations[-1].status is ObservationStatus.FAILED
        )
        source = (
            'result = structured_return("repaired", {"value": 2})'
            if failed
            else 'broken = 1 / 0\nresult = structured_return("unreachable", {})'
        )
        action = _analysis_response(
            self._session_id,
            self._episode_id,
            action_id=(
                f"analysis-repair-{packet.total_observation_count}"
                if failed
                else f"analysis-failure-{packet.total_observation_count}"
            ),
            source=source,
            field_ids=(),
        )["action"]
        assert isinstance(action, Mapping)
        return ModelResponse("", cast("Mapping[str, object]", action), {})

    def bind(self, session_id: str, episode_id: str) -> None:
        """Set the exact initialized identities before provider execution."""
        self._session_id = session_id
        self._episode_id = episode_id


class PacketBoundActionProvider:
    """Return one fixed intent with either current or deliberately forged identity."""

    def __init__(self, response: Mapping[str, object], *, forged: bool = False) -> None:
        """Retain neutral intent and configure whether packet identity may replace claims."""
        self._response = response
        self._forged = forged

    def complete(self, packet: ContextPacket) -> ModelResponse:
        """Bind honest actions to the packet while preserving deliberately forged claims."""
        raw_action = self._response.get("action")
        assert isinstance(raw_action, Mapping)
        action = dict(cast("Mapping[str, object]", raw_action))
        if not self._forged:
            action["session_id"] = packet.session_id
            action["episode_id"] = packet.episode_id
        return ModelResponse("", action, {})


def _runtime_fixture(  # noqa: PLR0913
    provider: ModelProvider,
    *,
    protected: bool = False,
    authorize_capability: bool = True,
    limits: ResourceLimits | None = None,
    view_dataset_ref: str = "toy-monthly",
    view_environment_ref: str | None = None,
    protected_resource_refs: tuple[str, ...] = (),
) -> tuple[AutonomousResearchRuntime, InMemoryRuntimeStore, RuntimeInitialization, ArtifactStore]:
    store = InMemoryRuntimeStore()
    environment = replace(
        toy_environment(),
        capability_names=("inspect_dataset", "run_analysis")
        if authorize_capability
        else ("inspect_dataset",),
        protected_resource_refs=protected_resource_refs,
    )
    initialized = ResearchRuntimeInitializer(store).initialize(
        confirmed_toy_task(), environment, request_id="runtime-exploration"
    )
    artifact_store = ArtifactStore()
    view = AuthorizedDataView(
        view_id="development-view" if not protected else "protected-view",
        dataset_ref=view_dataset_ref,
        environment_ref=view_environment_ref or environment.snapshot_ref,
        fields={"signal": (1.0, 2.0, 3.0)},
        protected=protected,
    )
    harness = AnalysisHarness(
        views={view.view_id: view},
        policy=CapabilityPolicy(
            session_id=initialized.session.session_id,
            environment_ref=environment.snapshot_ref,
            allowed_fields_by_view={view.view_id: frozenset({"signal"})},
        ),
        artifacts=artifact_store,
        resource_limits=limits,
    )
    runtime = AutonomousResearchRuntime(
        store,
        provider,
        ContextBuilder(store, max_observations=4),
        ActionRouter(
            store,
            DatasetRepository((make_toy_monthly_dataset(),)),
            analysis_harnesses={initialized.session.session_id: harness},
        ),
        CommitCoordinator(store),
    )
    return runtime, store, initialized, artifact_store


def test_analysis_meaning_alone_changes_the_next_packet_driven_action() -> None:
    """Actual returned semantics survive episode persistence and drive the next turn."""
    provider = ObservationDrivenProvider("pending", "pending")
    runtime, store, initialized, _ = _runtime_fixture(provider)
    provider.bind(initialized.session.session_id, initialized.episode.episode_id)

    first = runtime.advance_one_turn(initialized.session.session_id)
    second = runtime.advance_one_turn(initialized.session.session_id)

    assert first.observation is not None
    assert second.observation is not None
    assert second.observation.summary == "used-mean"
    assert provider.packets[1].working_observations[-1].payload["details"] == {"mean": 2.0}
    _, _, _, state, episode = store.coherent_view(initialized.session.session_id)
    assert state.version == 0
    assert state.durable_understanding == ()
    assert episode.observation_ids == (
        first.observation.observation_id,
        second.observation.observation_id,
    )


def test_analysis_failure_is_repairable_without_durable_state_mutation() -> None:
    """An operational exception returns working evidence that enables a new action."""
    provider = RepairingProvider("pending", "pending")
    runtime, store, initialized, artifacts = _runtime_fixture(provider)
    provider.bind(initialized.session.session_id, initialized.episode.episode_id)

    failed = runtime.advance_one_turn(initialized.session.session_id)
    repaired = runtime.advance_one_turn(initialized.session.session_id)

    assert failed.observation is not None
    assert failed.observation.status is ObservationStatus.FAILED
    assert failed.observation.failure is not None
    assert repaired.observation is not None
    assert repaired.observation.status is ObservationStatus.SUCCEEDED
    traceback_ref = next(iter(failed.observation.artifact_refs))
    stored_ref = store.artifacts[traceback_ref]
    assert isinstance(stored_ref, ArtifactRef)
    assert stored_ref.kind is ArtifactKind.TRACEBACK
    assert artifacts.read(stored_ref, session_id=initialized.session.session_id)
    _, _, _, state, episode = store.coherent_view(initialized.session.session_id)
    assert state.version == 0
    assert episode.status.value == "active"


def test_analysis_episode_stops_at_the_configured_turn_bound() -> None:
    """Repeated repairable exploration cannot turn a bounded run into an infinite loop."""
    provider = RepairingProvider("pending", "pending")
    runtime, store, initialized, _ = _runtime_fixture(provider)
    provider.bind(initialized.session.session_id, initialized.episode.episode_id)

    result = runtime.run_until_terminal(
        initialized.session.session_id, max_turns=EPISODE_TURN_BOUND
    )

    assert len(result.turns) == EPISODE_TURN_BOUND
    assert result.terminal_status.value == "active"
    _, _, _, state, episode = store.coherent_view(initialized.session.session_id)
    assert state.version == 0
    assert len(episode.observation_ids) == EPISODE_TURN_BOUND


def test_forged_identity_capability_and_protected_view_deny_before_execution() -> None:
    """No forged authority path reaches sandbox execution or exposes values."""
    # Forged session identity is rejected by runtime currentness before router execution.
    forged_provider = PacketBoundActionProvider(
        _analysis_response(
            "foreign-session",
            "foreign-episode",
            action_id="forged",
            source='print("must-not-run")\nresult = structured_return("x", {})',
        ),
        forged=True,
    )
    runtime, store, initialized, artifacts = _runtime_fixture(forged_provider)
    forged = runtime.advance_one_turn(initialized.session.session_id)
    assert forged.observation is not None
    assert forged.observation.status is ObservationStatus.FAILED
    assert len(artifacts) == 0
    assert "action.authorized" not in {
        event.event_type for event in store.events_for(initialized.session.session_id)
    }

    # Missing environment capability is denied by the router before the harness runs.
    denied_provider = PacketBoundActionProvider(
        _analysis_response(
            "pending",
            "pending",
            action_id="capability-denied",
            source='result = structured_return("x", {"secret": 99})',
        )
    )
    denied_runtime, _, denied_initialized, denied_artifacts = _runtime_fixture(
        denied_provider, authorize_capability=False
    )
    denied = denied_runtime.advance_one_turn(denied_initialized.session.session_id)
    assert denied.observation is not None
    assert denied.observation.status is ObservationStatus.REJECTED
    assert denied.observation.payload == {"failure_code": "AUTHORITY_DENIED"}
    assert "secret" not in repr(denied.observation)
    assert len(denied_artifacts) == 0

    # Even an allow-listed protected view cannot become an exploratory capability.
    protected_provider = PacketBoundActionProvider(
        _analysis_response(
            "pending",
            "pending",
            action_id="protected-denied",
            source='result = structured_return("x", {})',
            view_id="protected-view",
            field_ids=("signal",),
        )
    )
    protected_runtime, _, protected_initialized, protected_artifacts = _runtime_fixture(
        protected_provider, protected=True
    )
    protected_result = protected_runtime.advance_one_turn(protected_initialized.session.session_id)
    assert protected_result.observation is not None
    assert protected_result.observation.status is ObservationStatus.REJECTED
    assert len(protected_artifacts) == 0


@pytest.mark.parametrize(
    ("view_dataset_ref", "view_environment_ref", "protected_resource_refs"),
    [
        ("dataset-not-in-environment", None, ()),
        ("toy-monthly", "environment-v1@0", ()),
        ("toy-monthly", None, ("toy-monthly",)),
    ],
)
def test_analysis_view_must_match_exact_readable_unprotected_environment_scope(
    view_dataset_ref: str,
    view_environment_ref: str | None,
    protected_resource_refs: tuple[str, ...],
) -> None:
    """A session-bound harness cannot launder absent, stale, or protected data views."""
    provider = PacketBoundActionProvider(
        _analysis_response(
            "pending",
            "pending",
            action_id="scope-attack",
            source=(
                'values = read("development-view", "signal")\n'
                'result = structured_return("must not run", {"secret": values[0]})'
            ),
        )
    )
    runtime, store, initialized, artifacts = _runtime_fixture(
        provider,
        view_dataset_ref=view_dataset_ref,
        view_environment_ref=view_environment_ref,
        protected_resource_refs=protected_resource_refs,
    )

    result = runtime.advance_one_turn(initialized.session.session_id)

    assert result.observation is not None
    assert result.observation.status is ObservationStatus.REJECTED
    assert result.observation.payload == {"failure_code": "AUTHORITY_DENIED"}
    assert "secret" not in repr(result.observation)
    assert len(artifacts) == 0
    assert "action.authorized" not in {
        event.event_type for event in store.events_for(initialized.session.session_id)
    }


def test_large_analysis_artifacts_and_actual_access_provenance_remain_references() -> None:
    """The adapter retains exact access facts while keeping large output out of context."""
    provider = PacketBoundActionProvider(
        _analysis_response(
            "pending",
            "pending",
            action_id="analysis-large",
            source=(
                'values = read("development-view", "signal")\n'
                'print("z" * 4096)\n'
                'result = structured_return("large", {"table": [sum(values)] * 2048}, '
                'warnings=["retain caveat"])'
            ),
        )
    )
    runtime, store, initialized, _ = _runtime_fixture(
        provider, limits=ResourceLimits(max_inline_bytes=128, max_output_bytes=16_000)
    )
    result = runtime.advance_one_turn(initialized.session.session_id)
    packet = ContextBuilder(store).build_current_context(initialized.session.session_id)

    assert result.observation is not None
    observation = result.observation
    assert observation.payload["details"] is None
    assert "z" * 256 not in repr(observation)
    assert len(observation.artifact_refs) == EXPECTED_LARGE_ARTIFACTS
    assert all(ref in store.artifacts for ref in observation.artifact_refs)
    assert observation.warnings == ("retain caveat",)
    assert observation.epistemic_status == "EXPLORATORY"
    assert isinstance(observation.provenance, AnalysisExecutionProvenance)
    assert tuple(access.field_id for access in observation.provenance.accesses) == ("signal",)
    projected = packet.working_observations[-1]
    assert projected.provenance == observation.provenance
    assert projected.artifact_refs == observation.artifact_refs
    assert projected.warnings == ("retain caveat",)
    assert projected.epistemic_status == "EXPLORATORY"
