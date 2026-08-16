"""Adversarial tests for action decoding, authority, and provenance."""

from typing import cast

import pytest

from research_agent.runtime.actions import ActionDecodeError, InspectDatasetAction, decode_action
from research_agent.runtime.capabilities import (
    ActionRouter,
    DatasetRepository,
    make_toy_monthly_dataset,
)
from research_agent.runtime.context import ContextBuilder
from research_agent.runtime.models import FailureCode, ObservationStatus
from research_agent.runtime.provider import ModelResponse, ScriptedModelProvider
from tests.runtime.support import initialized_runtime

PREVIEW_LIMIT = 3
TOY_ROW_COUNT = 18


def test_scripted_provider_normalizes_and_decoder_returns_typed_action() -> None:
    """Provider-native mappings end at the neutral response boundary."""
    store, initialized = initialized_runtime()
    raw = {
        "message": "Inspect the authorized dataset.",
        "action": {
            "kind": "inspect_dataset",
            "action_id": "action-1",
            "session_id": initialized.session.session_id,
            "episode_id": initialized.episode.episode_id,
            "arguments": {"dataset_ref": "toy-monthly", "preview_limit": PREVIEW_LIMIT},
        },
        "provider_metadata": {"native": "discarded"},
    }
    provider = ScriptedModelProvider((raw,))
    response = provider.complete(
        ContextBuilder(store).build_current_context(initialized.session.session_id)
    )
    action = decode_action(response)

    assert isinstance(response, ModelResponse)
    assert isinstance(action, InspectDatasetAction)
    assert action.preview_limit == PREVIEW_LIMIT


def test_unknown_action_fails_before_capability_execution() -> None:
    """An unknown provider action cannot become a permissive generic tool call."""
    response = ModelResponse(
        message="Try an unknown action.",
        action={
            "kind": "unknown",
            "action_id": "action-unknown",
            "session_id": "session-1",
            "episode_id": "episode-1",
            "arguments": {},
        },
        provider_metadata={},
    )

    with pytest.raises(ActionDecodeError):
        decode_action(response)


def test_scientific_workflow_action_rejects_unexpected_argument() -> None:
    """Provider validation cannot be the sole guard for privileged workflow requests."""
    response = ModelResponse(
        message="Run a registered workflow.",
        action={
            "kind": "run_scientific_workflow",
            "action_id": "action-workflow",
            "session_id": "session-1",
            "episode_id": "episode-1",
            "arguments": {
                "workflow_id": "workflow-1",
                "idempotency_key": "workflow-key-1",
                "authority_override": "caller-supplied",
            },
        },
        provider_metadata={},
    )

    with pytest.raises(ActionDecodeError, match="exact schema"):
        decode_action(response)


def test_authorized_inspection_is_bounded_read_only_and_harness_provenanced() -> None:
    """Only authorized values enter a bounded observation with actual access provenance."""
    store, initialized = initialized_runtime()
    dataset = make_toy_monthly_dataset()
    before = dataset.rows
    router = ActionRouter(store, DatasetRepository((dataset,)))
    action = InspectDatasetAction(
        "action-1",
        initialized.session.session_id,
        initialized.episode.episode_id,
        "toy-monthly",
        ("reference_time", "predictor_value"),
        PREVIEW_LIMIT,
    )

    observation = router.execute_inspection(action)

    assert observation.status is ObservationStatus.SUCCEEDED
    assert observation.payload["row_count"] == TOY_ROW_COUNT
    preview = observation.payload["preview"]
    assert isinstance(preview, tuple)
    assert len(cast("tuple[object, ...]", preview)) == PREVIEW_LIMIT
    assert dataset.rows == before
    assert observation.provenance is not None
    assert observation.provenance.authorized_dataset_ref == "toy-monthly"
    assert observation.provenance.selected_field_ids == ("reference_time", "predictor_value")
    assert observation.artifact_refs[0] in store.artifacts


def test_unauthorized_dataset_denial_leaks_no_values() -> None:
    """Authority denial occurs before dataset rows enter any observation."""
    store, initialized = initialized_runtime(readable=False)
    router = ActionRouter(store, DatasetRepository((make_toy_monthly_dataset(),)))
    action = InspectDatasetAction(
        "action-denied",
        initialized.session.session_id,
        initialized.episode.episode_id,
        "toy-monthly",
        (),
        PREVIEW_LIMIT,
    )

    observation = router.execute_inspection(action)

    assert observation.failure is not None
    assert observation.failure.code is FailureCode.AUTHORITY_DENIED
    assert "predictor_value" not in repr(observation)
    assert "target_value" not in repr(observation)
