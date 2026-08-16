"""Whole-loop tests for exact registered scientific workflow execution."""

# ruff: noqa: PLR0915

from __future__ import annotations

from dataclasses import replace
from typing import cast

import pytest

from research_agent.data_foundation import DataCatalogSnapshot
from research_agent.development import TrialStatus
from research_agent.protected_evaluation import (
    BacktestRun,
    BacktestRunStatus,
    DecisionStatus,
    EvaluationReport,
    FreezeDecision,
    FreezeEligibilityRegistry,
    IdempotencyConflictError,
    ProtectedContentManifest,
)
from research_agent.reporting import RenderedFindingReport
from research_agent.runtime.capabilities import ActionRouter, DatasetRepository
from research_agent.runtime.commit import CommitCoordinator
from research_agent.runtime.context import ContextBuilder
from research_agent.runtime.engine import AutonomousResearchRuntime
from research_agent.runtime.initialization import ResearchRuntimeInitializer
from research_agent.runtime.models import EpisodeStatus, ObservationStatus
from research_agent.runtime.provider import ScriptedModelProvider
from research_agent.scientific_workflow import (
    ProtectedResourceIssuer,
    ScientificWorkflowCoordinator,
    ScientificWorkflowIssuer,
    WorkflowAuthorityRegistry,
    WorkflowReceipt,
    WorkflowRegistryError,
    WorkflowStatus,
    configure_protected_resource_authority,
    configure_scientific_workflow_authority,
)
from research_agent.verification.scientific_workflow_fixture import (
    PROTECTED_RESOURCE_AUTHORITY_ID,
    WORKFLOW_AUTHORITY_ID,
    ToyScientificWorkflowWorld,
    fixed_clock,
    make_toy_scientific_workflow_world,
)


def _workflow_response(
    session_id: str,
    episode_id: str,
    workflow_id: str,
    *,
    action_id: str = "workflow-action",
    idempotency_key: str = "workflow-run",
) -> dict[str, object]:
    return {
        "message": "Run the exact registered scientific workflow.",
        "action": {
            "kind": "run_scientific_workflow",
            "action_id": action_id,
            "session_id": session_id,
            "episode_id": episode_id,
            "arguments": {
                "workflow_id": workflow_id,
                "idempotency_key": idempotency_key,
            },
        },
    }


def _commit_response(
    session_id: str,
    episode_id: str,
    observation_id: str,
    receipt_ref: str,
    finding_ref: str,
) -> dict[str, object]:
    return {
        "message": "Commit the independently validated finding.",
        "action": {
            "kind": "propose_episode_transition",
            "action_id": "commit-workflow-finding",
            "session_id": session_id,
            "episode_id": episode_id,
            "arguments": {
                "target_status": "resolved",
                "synthesis": "The registered workflow produced independently validated evidence.",
                "evidence_refs": [observation_id, receipt_ref],
                "state_update": {
                    "starting_state_version": 0,
                    "durable_understanding": [
                        f"Validated finding retained at exact reference {finding_ref}."
                    ],
                    "evidence_refs": [observation_id, receipt_ref],
                },
                "idempotency_key": "commit-workflow-finding",
            },
        },
    }


def _runtime(
    world: ToyScientificWorkflowWorld,
    provider: ScriptedModelProvider,
) -> AutonomousResearchRuntime:
    return AutonomousResearchRuntime(
        world.store,
        provider,
        ContextBuilder(world.store),
        ActionRouter(
            world.store,
            DatasetRepository(()),
            scientific_workflow=world.coordinator,
        ),
        CommitCoordinator(world.store),
    )


def test_scripted_runtime_runs_registered_workflow_then_commits_validated_finding() -> None:
    """The whole kernel reaches durable state only through the later semantic commit."""
    world = make_toy_scientific_workflow_world()
    session_id = world.initialized.session.session_id
    episode_id = world.initialized.episode.episode_id
    provider = ScriptedModelProvider(
        (_workflow_response(session_id, episode_id, world.workflow.workflow_id),)
    )
    runtime = _runtime(world, provider)

    workflow_turn = runtime.advance_one_turn(session_id)

    observation = workflow_turn.observation
    assert workflow_turn.action_kind == "run_scientific_workflow"
    assert observation is not None
    assert observation.status is ObservationStatus.SUCCEEDED
    assert observation.payload["workflow_status"] == WorkflowStatus.FINDING.value
    receipt_id = observation.payload["receipt_id"]
    assert isinstance(receipt_id, str)
    receipt = world.coordinator.evidence(receipt_id)
    assert isinstance(receipt, WorkflowReceipt)
    assert receipt.status is WorkflowStatus.FINDING
    assert receipt.finding_ref is not None
    assert receipt.rendered_report_ref is not None
    rendered = world.coordinator.evidence(receipt.rendered_report_ref)
    assert isinstance(rendered, RenderedFindingReport)
    assert rendered.finding_id == receipt.finding_ref
    assert observation.payload["report_ref"] == rendered.rendered_report_id
    observation_evidence_refs = observation.payload["evidence_refs"]
    assert isinstance(observation_evidence_refs, tuple)
    assert observation_evidence_refs == receipt.evidence_refs
    receipt_ref = observation.artifact_refs[0]
    _, _, _, state_before, episode_before = world.store.coherent_view(session_id)
    assert state_before.version == 0
    assert state_before.durable_understanding == ()
    assert episode_before.status is EpisodeStatus.ACTIVE

    run = world.coordinator.evidence(receipt.run_ref or "")
    assert isinstance(run, BacktestRun)
    assert world.future_poison_observation_id
    assert all(
        world.future_poison_observation_id not in decision.information_observation_ids
        for decision in run.decisions
    )
    provider.queue_response(
        _commit_response(
            session_id,
            episode_id,
            observation.observation_id,
            receipt_ref,
            receipt.finding_ref,
        )
    )

    committed = runtime.advance_one_turn(session_id)

    assert committed.commit_result is not None
    assert committed.commit_result.committed
    packet_seen = provider.calls[-1]
    assert packet_seen.working_observations[-1].payload["finding_ref"] == receipt.finding_ref
    _, _, _, state_after, episode_after = world.store.coherent_view(session_id)
    assert state_after.version == 1
    assert state_after.evidence_refs == (observation.observation_id, receipt_ref)
    assert episode_after.status is EpisodeStatus.RESOLVED
    runtime_events = tuple(item.event_type for item in world.store.events_for(session_id))
    assert runtime_events.index("action.authorized") < runtime_events.index("capability.executed")
    assert runtime_events.index("capability.executed") < runtime_events.index(
        "observation.assembled"
    )
    assert runtime_events.index("observation.assembled") < runtime_events.index("commit.published")
    scientific_events = tuple(item.event_type for item in world.coordinator.ledger.entries())
    assert scientific_events == (
        "freeze.eligibility-decided",
        "freeze.system-sealed",
        "backtest.authorization-decided",
        "exposure.protected-disclosed",
        "backtest.run-sealed",
        "evaluation.run-measured",
        "finding.validation-decided",
        "finding.validated-claim-published",
    )


def test_future_poison_counterpart_cannot_change_protected_predictions_or_fit_sizes() -> None:
    """A post-decision revision is causally irrelevant to every as-known protected boundary."""
    poisoned = make_toy_scientific_workflow_world(
        world_id="poisoned",
        include_future_poison=True,
    )
    clean = make_toy_scientific_workflow_world(
        world_id="clean",
        include_future_poison=False,
    )

    poisoned_receipt = poisoned.coordinator.execute(
        workflow_id=poisoned.workflow.workflow_id,
        idempotency_key="poisoned",
        session_id=poisoned.initialized.session.session_id,
        episode_id=poisoned.initialized.episode.episode_id,
    )
    clean_receipt = clean.coordinator.execute(
        workflow_id=clean.workflow.workflow_id,
        idempotency_key="clean",
        session_id=clean.initialized.session.session_id,
        episode_id=clean.initialized.episode.episode_id,
    )
    poisoned_run = poisoned.coordinator.evidence(poisoned_receipt.run_ref or "")
    clean_run = clean.coordinator.evidence(clean_receipt.run_ref or "")
    assert isinstance(poisoned_run, BacktestRun)
    assert isinstance(clean_run, BacktestRun)
    assert poisoned.future_poison_observation_id
    assert tuple(
        decision.prediction.value if decision.prediction is not None else None
        for decision in poisoned_run.decisions
    ) == tuple(
        decision.prediction.value if decision.prediction is not None else None
        for decision in clean_run.decisions
    )
    assert tuple(len(decision.training_row_ids) for decision in poisoned_run.decisions) == tuple(
        len(decision.training_row_ids) for decision in clean_run.decisions
    )
    assert all(
        poisoned.future_poison_observation_id not in decision.information_observation_ids
        for decision in poisoned_run.decisions
    )


def test_exact_retry_converges_changed_payload_conflicts_and_prior_exposure_denies() -> None:
    """Workflow retry is exact while changed semantics and fresh-holdout reuse fail closed."""
    world = make_toy_scientific_workflow_world()
    kwargs = {
        "workflow_id": world.workflow.workflow_id,
        "idempotency_key": "exact-key",
        "session_id": world.initialized.session.session_id,
        "episode_id": world.initialized.episode.episode_id,
    }

    first = world.coordinator.execute(**kwargs)
    ledger_size = len(world.coordinator.ledger.entries())
    replay = world.coordinator.execute(**kwargs)

    assert replay is first
    assert len(world.coordinator.exposures.records()) == 1
    assert len(world.coordinator.ledger.entries()) == ledger_size
    assert tuple(
        item.status
        for item in world.coordinator.development_trial_records(world.workflow.workflow_id)
    ) == (
        TrialStatus.ATTEMPTED,
        TrialStatus.SUCCEEDED,
    )
    changed = replace(
        world.workflow,
        protected_recipient_id="research-process:changed",
    )
    world.workflow_issuer.issue(changed)
    with pytest.raises(IdempotencyConflictError, match="changed semantics"):
        world.coordinator.execute(
            workflow_id=changed.workflow_id,
            idempotency_key="exact-key",
            session_id=world.initialized.session.session_id,
            episode_id=world.initialized.episode.episode_id,
        )
    assert len(world.coordinator.exposures.records()) == 1

    denied = world.coordinator.execute(
        workflow_id=world.workflow.workflow_id,
        idempotency_key="new-attempt-after-exposure",
        session_id=world.initialized.session.session_id,
        episode_id=world.initialized.episode.episode_id,
    )

    assert denied.status is WorkflowStatus.DENIED
    assert denied.reason_codes == ("PRIOR_EXPOSURE",)
    assert denied.finding_ref is None
    assert len(world.coordinator.exposures.records()) == 1
    assert tuple(
        item.status
        for item in world.coordinator.development_trial_records(world.workflow.workflow_id)
    ) == (
        TrialStatus.ATTEMPTED,
        TrialStatus.SUCCEEDED,
    )


def test_validation_rejection_is_negative_evidence_and_never_success() -> None:
    """An impossible predeclared threshold retains rejection and emits no finding."""
    world = make_toy_scientific_workflow_world(promotion_mse_threshold=-1.0)
    session_id = world.initialized.session.session_id
    episode_id = world.initialized.episode.episode_id
    provider = ScriptedModelProvider(
        (_workflow_response(session_id, episode_id, world.workflow.workflow_id),)
    )

    turn = _runtime(world, provider).advance_one_turn(session_id)

    assert turn.observation is not None
    assert turn.observation.status is ObservationStatus.REJECTED
    assert turn.observation.payload["workflow_status"] == WorkflowStatus.REJECTED.value
    assert turn.observation.payload["finding_ref"] is None
    assert turn.observation.payload["report_ref"] is None
    evidence_refs = cast("tuple[object, ...]", turn.observation.payload["evidence_refs"])
    assert isinstance(evidence_refs, tuple)
    for reference in evidence_refs:
        assert isinstance(reference, str)
        assert not isinstance(world.coordinator.evidence(reference), RenderedFindingReport)
    negative_ref = turn.observation.payload["negative_result_ref"]
    assert isinstance(negative_ref, str)
    assert world.coordinator.evidence(negative_ref) in world.coordinator.negatives.records()
    _, _, _, state, episode = world.store.coherent_view(session_id)
    assert state.version == 0
    assert episode.status is EpisodeStatus.ACTIVE


def test_independent_freeze_denial_returns_evidence_without_protected_disclosure() -> None:
    """Runtime cannot override the independently issued freeze eligibility outcome."""
    world = make_toy_scientific_workflow_world(freeze_status=DecisionStatus.DENY)

    receipt = world.coordinator.execute(
        workflow_id=world.workflow.workflow_id,
        idempotency_key="freeze-denied",
        session_id=world.initialized.session.session_id,
        episode_id=world.initialized.episode.episode_id,
    )

    assert receipt.status is WorkflowStatus.DENIED
    assert receipt.reason_codes == ("INDEPENDENT_FREEZE_REJECTED",)
    assert receipt.development_evidence_ref is not None
    freeze_decision = world.coordinator.evidence(receipt.evidence_refs[-1])
    assert isinstance(freeze_decision, FreezeDecision)
    assert freeze_decision.status is DecisionStatus.DENY
    assert receipt.frozen_system_ref is None
    assert receipt.exposure_ref is None
    assert receipt.run_ref is None
    assert receipt.finding_ref is None
    assert receipt.rendered_report_ref is None
    assert world.coordinator.exposures.records() == ()


def test_protected_execution_failure_is_retained_as_rejection_evidence() -> None:
    """A protected run with formal failures cannot be promoted or reported as success."""
    world = make_toy_scientific_workflow_world(protected_final_day=10)
    session_id = world.initialized.session.session_id
    episode_id = world.initialized.episode.episode_id
    provider = ScriptedModelProvider(
        (_workflow_response(session_id, episode_id, world.workflow.workflow_id),)
    )

    turn = _runtime(world, provider).advance_one_turn(session_id)

    assert turn.observation is not None
    assert turn.observation.status is ObservationStatus.REJECTED
    assert turn.observation.payload["workflow_status"] == WorkflowStatus.REJECTED.value
    receipt_id = turn.observation.payload["receipt_id"]
    assert isinstance(receipt_id, str)
    receipt = world.coordinator.evidence(receipt_id)
    assert isinstance(receipt, WorkflowReceipt)
    run = world.coordinator.evidence(receipt.run_ref or "")
    report = world.coordinator.evidence(receipt.evaluation_report_ref or "")
    assert isinstance(run, BacktestRun)
    assert isinstance(report, EvaluationReport)
    assert run.status is BacktestRunStatus.COMPLETED_WITH_FAILURES
    assert report.failures
    assert receipt.negative_result_ref is not None
    assert receipt.finding_ref is None
    assert receipt.rendered_report_ref is None


def test_unknown_or_foreign_workflow_is_denied_before_protected_disclosure() -> None:
    """Caller-authored IDs and cross-session specs cannot reach protected content."""
    world = make_toy_scientific_workflow_world()
    session_id = world.initialized.session.session_id
    episode_id = world.initialized.episode.episode_id
    provider = ScriptedModelProvider(
        (_workflow_response(session_id, episode_id, "workflow:caller-authored"),)
    )

    turn = _runtime(world, provider).advance_one_turn(session_id)

    assert turn.observation is not None
    assert turn.observation.status is ObservationStatus.REJECTED
    assert turn.observation.failure is not None
    assert turn.observation.payload == {"failure_code": "AUTHORITY_DENIED"}
    assert world.coordinator.exposures.records() == ()
    assert world.coordinator.ledger.entries() == ()
    event_types = tuple(item.event_type for item in world.store.events_for(session_id))
    assert "action.authorized" not in event_types
    assert event_types[-1] == "episode.observation-recorded"


def test_workflow_registry_rejects_registration_not_issued_by_its_freeze_authority() -> None:
    """A caller cannot carry a valid-looking registration into another authority registry."""
    world = make_toy_scientific_workflow_world()
    _, foreign_issuer = configure_scientific_workflow_authority(
        authority_id=WORKFLOW_AUTHORITY_ID,
        freeze_eligibility=FreezeEligibilityRegistry(),
        authorities=world.authorities,
        protected_resources=world.protected_resources,
    )
    with pytest.raises(ValueError, match="not issued"):
        foreign_issuer.issue(world.workflow)


def test_workflow_cannot_carry_or_mint_privileged_authority_labels() -> None:
    """The former caller-label substitution is impossible before protected disclosure."""
    world = make_toy_scientific_workflow_world(world_id="authority-substitution")

    assert not hasattr(world.registry, "register")
    assert not hasattr(world.workflow, "governance_authority_id")
    assert not hasattr(world.workflow, "validation_authority_id")
    with pytest.raises(TypeError, match="governance_authority_id"):
        replace(
            world.workflow,
            governance_authority_id="attacker-appointed-governance",
            validation_authority_id="attacker-appointed-validation",
        )
    attacker = ScientificWorkflowIssuer(
        authority_id=WORKFLOW_AUTHORITY_ID,
        registry=world.registry,
        issuance_capability=object(),
    )
    with pytest.raises(WorkflowRegistryError, match="configured workflow authority"):
        attacker.issue(world.workflow)

    assert world.coordinator.ledger.entries() == ()
    assert world.coordinator.exposures.records() == ()


def test_protected_authority_binding_and_catalog_substitution_conflict_before_disclosure() -> None:
    """The former caller-owned protected catalog cannot replace an issued scope binding."""
    world = make_toy_scientific_workflow_world(world_id="resource-substitution")
    registration = world.protected_resource_registration
    assert not hasattr(world.protected_resources, "register")
    assert not hasattr(world.workflow, "protected_catalog")
    assert not hasattr(world.workflow, "protected_resource_binding_ref")
    with pytest.raises(TypeError, match="protected_catalog"):
        replace(
            world.workflow,
            protected_catalog=DataCatalogSnapshot(
                environment_id=registration.catalog.environment_id,
                datasets=(),
            ),
            protected_resource_binding_ref="attacker-binding:changed",
        )
    attacker = ProtectedResourceIssuer(
        authority_id=PROTECTED_RESOURCE_AUTHORITY_ID,
        registry=world.protected_resources,
        issuance_capability=object(),
    )
    with pytest.raises(WorkflowRegistryError, match="configured authority"):
        attacker.issue(
            scope=registration.scope,
            resource_binding_ref=registration.resource_binding_ref,
            content_manifest=registration.content_manifest,
            catalog=registration.catalog,
        )
    with pytest.raises(WorkflowRegistryError, match=r"exact catalog|different authoritative"):
        world.protected_resource_issuer.issue(
            scope=registration.scope,
            resource_binding_ref="attacker-binding:changed",
            content_manifest=registration.content_manifest,
            catalog=registration.catalog,
        )
    substituted_catalog = DataCatalogSnapshot(
        environment_id=registration.catalog.environment_id,
        datasets=(),
    )
    with pytest.raises(WorkflowRegistryError, match=r"exact catalog|different authoritative"):
        world.protected_resource_issuer.issue(
            scope=registration.scope,
            resource_binding_ref=registration.resource_binding_ref,
            content_manifest=registration.content_manifest,
            catalog=substituted_catalog,
        )

    assert world.coordinator.ledger.entries() == ()
    assert world.coordinator.exposures.records() == ()


def test_identical_content_alias_cannot_acquire_a_fresh_epistemic_period() -> None:
    """A different resource label cannot launder already-identical protected bytes."""
    world = make_toy_scientific_workflow_world(world_id="content-alias")
    registration = world.protected_resource_registration
    alias_manifest = ProtectedContentManifest.create(
        content_digest=registration.content_manifest.content_digest,
        byte_length=registration.content_manifest.byte_length,
        catalog_id=registration.content_manifest.catalog_id,
        provenance_ref="fixture:alias-path-to-identical-bytes",
    )
    assert alias_manifest.manifest_id != registration.content_manifest.manifest_id
    assert alias_manifest.content_identity_id == registration.content_manifest.content_identity_id
    fresh_alias = replace(
        registration.scope,
        resource_id="attacker-alias",
        content_manifest_id=alias_manifest.manifest_id,
        epistemic_period_ref="attacker-claims-fresh-period",
    )
    with pytest.raises(WorkflowRegistryError, match="Identical protected content"):
        world.protected_resource_issuer.issue(
            scope=fresh_alias,
            resource_binding_ref="protected-binding:alias",
            content_manifest=alias_manifest,
            catalog=registration.catalog,
        )

    same_period_alias = replace(
        fresh_alias,
        epistemic_period_ref=registration.scope.epistemic_period_ref,
    )
    alias = world.protected_resource_issuer.issue(
        scope=same_period_alias,
        resource_binding_ref="protected-binding:alias",
        content_manifest=alias_manifest,
        catalog=registration.catalog,
    )
    assert alias.scope.scope_id != registration.scope.scope_id
    assert alias.scope.exposure_period_id == registration.scope.exposure_period_id


def test_different_registered_subject_uses_same_coordinator_without_kernel_plugin() -> None:
    """A second confirmed task/session enters by registration rather than domain code."""
    eligibility = FreezeEligibilityRegistry()
    first_world = make_toy_scientific_workflow_world(
        world_id="subject-a", freeze_eligibility=eligibility
    )
    other_world = make_toy_scientific_workflow_world(
        world_id="subject-b",
        freeze_eligibility=eligibility,
        outcome_slope=3.0,
    )
    other_task, other_environment, _, _, _ = other_world.store.coherent_view(
        other_world.initialized.session.session_id
    )
    initialized_other = ResearchRuntimeInitializer(first_world.store).initialize(
        other_task,
        other_environment,
        request_id="initialize:subject-b:on-shared-coordinator",
    )
    other_workflow = replace(
        other_world.workflow,
        session_id=initialized_other.session.session_id,
        episode_id=initialized_other.episode.episode_id,
    )
    first_issuance = first_world.registry.resolve(first_world.workflow.workflow_id)
    other_issuance = other_world.registry.resolve(other_world.workflow.workflow_id)
    resources, resource_issuer = configure_protected_resource_authority(
        PROTECTED_RESOURCE_AUTHORITY_ID
    )
    for issuance in (first_issuance, other_issuance):
        resource = issuance.protected_resource
        resource_issuer.issue(
            scope=resource.scope,
            resource_binding_ref=resource.resource_binding_ref,
            content_manifest=resource.content_manifest,
            catalog=resource.catalog,
        )
    authorities = WorkflowAuthorityRegistry(
        governance_permissions=(
            first_issuance.governance_permission,
            other_issuance.governance_permission,
        ),
        validation_grants=(first_issuance.validation_grant,),
    )
    registry, issuer = configure_scientific_workflow_authority(
        authority_id=WORKFLOW_AUTHORITY_ID,
        freeze_eligibility=eligibility,
        authorities=authorities,
        protected_resources=resources,
    )
    issuer.issue(first_world.workflow)
    issuer.issue(other_workflow)
    coordinator = ScientificWorkflowCoordinator(
        registry=registry,
        runtime_store=first_world.store,
        clock=fixed_clock,
    )

    first = coordinator.execute(
        workflow_id=first_world.workflow.workflow_id,
        idempotency_key="subject-a",
        session_id=first_world.initialized.session.session_id,
        episode_id=first_world.initialized.episode.episode_id,
    )
    second = coordinator.execute(
        workflow_id=other_workflow.workflow_id,
        idempotency_key="subject-b",
        session_id=initialized_other.session.session_id,
        episode_id=initialized_other.episode.episode_id,
    )

    assert first.status is WorkflowStatus.FINDING
    assert second.status is WorkflowStatus.FINDING
    assert first.workflow_id != second.workflow_id
    assert first.session_id != second.session_id
    expected_exposure_count = 2
    assert len(coordinator.exposures.records()) == expected_exposure_count


def test_environment_without_protected_scope_denies_before_workflow_execution() -> None:
    """Registry presence cannot broaden the current session environment's authority."""
    world = make_toy_scientific_workflow_world(readable_protected_resource=False)
    session_id = world.initialized.session.session_id
    episode_id = world.initialized.episode.episode_id
    provider = ScriptedModelProvider(
        (_workflow_response(session_id, episode_id, world.workflow.workflow_id),)
    )

    turn = _runtime(world, provider).advance_one_turn(session_id)

    assert turn.observation is not None
    assert turn.observation.status is ObservationStatus.REJECTED
    assert turn.observation.payload == {"failure_code": "AUTHORITY_DENIED"}
    assert world.coordinator.exposures.records() == ()
    assert world.coordinator.ledger.entries() == ()
