"""Exposure irreversibility, negative history, and retry tests."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from research_agent.protected_evaluation import (
    BacktestDenial,
    BacktestGovernance,
    BacktestRequest,
    DecisionStatus,
    DenialCode,
    DisclosureEvent,
    ExposureRecorder,
    ExposureRegistry,
    FreezeEligibilityRegistration,
    FreezeEligibilityRegistry,
    FreezeEligibilityRequest,
    FreezeGate,
    FrozenPredictiveSystemIdentity,
    FrozenSystemRegistry,
    IdempotencyConflictError,
    LedgerConflictError,
    LedgerEntry,
    PermissionGrant,
    PermitRegistry,
    PrivilegedOperationCoordinator,
    PrivilegedOperationPhase,
    ProtectedExposureStatus,
    ProtectedResourceScope,
    ResearchLedger,
)

NOW = datetime(2026, 8, 15, 12, tzinfo=UTC)


def _clock() -> datetime:
    return NOW


def _scope() -> ProtectedResourceScope:
    return ProtectedResourceScope(
        "holdout",
        "v1",
        "2025",
        "env@1",
        "policy@1",
        "protected-content-manifest:holdout-2025",
        "protected-content:holdout-2025",
        "epistemic-period:holdout-2025",
        ProtectedExposureStatus.UNSEEN,
    )


def _frozen(
    ledger: ResearchLedger,
    registry: FrozenSystemRegistry,
    *,
    system_id: str = "system:a",
    ancestry_refs: tuple[str, ...] = ("candidate:parent",),
) -> FrozenPredictiveSystemIdentity:
    request = FreezeEligibilityRequest(
        system_id=system_id,
        candidate_version="3",
        ancestry_refs=ancestry_refs,
        development_evidence_refs=("development:3",),
        protocol_refs=("training:3", "evaluation:2", "validation:1"),
        environment_ref="env@1",
        standard_ref="standard:1",
        requester_id="agent",
        beneficiary_id="candidate-team",
    )
    eligibility = FreezeEligibilityRegistry()
    registration = FreezeEligibilityRegistration._issue(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        request,
        authority_id="freeze-governor",
        status=DecisionStatus.ACCEPT,
        reason_code="DEVELOPMENT_STANDARD_MET",
    )
    eligibility._issue(registration)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    gate = FreezeGate(
        ledger=ledger,
        registry=registry,
        eligibility=eligibility,
        decision_authority_id="freeze-governor",
        clock=_clock,
    )
    decision = gate.assess(request)
    return gate.seal(request, decision)


def _request(
    frozen: FrozenPredictiveSystemIdentity,
    *,
    system_id: str | None = None,
    ancestry: tuple[str, ...] = ("candidate:parent",),
    key: str = "request-1",
) -> BacktestRequest:
    return BacktestRequest(
        frozen_system_id=frozen.frozen_system_id,
        system_id=system_id or frozen.system_id,
        scenario_ref="walk-forward:1",
        decision_times_ref="times:2025",
        training_protocol_ref="training:3",
        evaluation_spec_ref="evaluation:2",
        validation_standard_ref="validation:1",
        claim_ref="claim:1",
        protected_scope=_scope(),
        environment_ref="env@1",
        ancestry_refs=ancestry,
        prior_exposure_refs=(),
        requester_id="agent",
        beneficiary_id="candidate-team",
        idempotency_key=key,
    )


def _event(*, status: str = "failed-after-disclosure") -> DisclosureEvent:
    return DisclosureEvent(
        disclosure_key="disclosure-1",
        view_id="view:1",
        permit_id="permit:1",
        request_id="request:1",
        frozen_system_id="frozen:system-a",
        system_id="system:a",
        lineage_refs=("candidate:parent",),
        scope=_scope(),
        recipient_id="research-process:1",
        disclosure_status=status,
    )


def test_failed_disclosure_is_irreversible_and_denies_descendant_as_unseen() -> None:
    """Even failed work after disclosure permanently contaminates descendant freshness."""
    ledger = ResearchLedger()
    exposures = ExposureRegistry()
    recorder = ExposureRecorder(registry=exposures, ledger=ledger, clock=_clock)
    record = recorder.record(_event())
    replay = recorder.record(_event())

    assert replay == record
    assert len(exposures.records()) == 1
    assert record.disclosure_status == "failed-after-disclosure"

    registry = FrozenSystemRegistry()
    descendant_frozen = _frozen(
        ledger,
        registry,
        system_id="system:descendant",
        ancestry_refs=("system:a", "candidate:parent"),
    )
    descendant = _request(
        descendant_frozen,
        system_id="system:descendant",
        ancestry=("system:a", "candidate:parent"),
        key="descendant-request",
    )
    governance = BacktestGovernance(
        ledger=ledger,
        frozen_systems=registry,
        exposures=exposures,
        permits=PermitRegistry(),
        permissions=(
            PermissionGrant(
                "agent",
                "backtest-governor",
                frozenset({_scope().scope_id}),
                "policy@1",
                "env@1",
            ),
        ),
        current_environment_ref="env@1",
        current_policy_ref="policy@1",
        clock=_clock,
    )
    denial = governance.authorize(descendant, authority_id="backtest-governor")
    assert isinstance(denial, BacktestDenial)
    assert denial.code is DenialCode.PRIOR_EXPOSURE


def test_resource_version_bump_does_not_restore_holdout_freshness() -> None:
    """Exposure period identity survives v1-to-v2 resource publication for descendants."""
    ledger = ResearchLedger()
    exposures = ExposureRegistry()
    ExposureRecorder(registry=exposures, ledger=ledger, clock=_clock).record(_event())
    registry = FrozenSystemRegistry()
    descendant = _frozen(
        ledger,
        registry,
        system_id="system:descendant",
        ancestry_refs=("system:a", "candidate:parent"),
    )
    version_two = replace(_scope(), resource_version="v2")
    assert version_two.scope_id != _scope().scope_id
    assert version_two.exposure_period_id == _scope().exposure_period_id
    request = replace(
        _request(
            descendant,
            system_id=descendant.system_id,
            ancestry=descendant.ancestry_refs,
            key="version-two-descendant",
        ),
        protected_scope=version_two,
    )
    governance = BacktestGovernance(
        ledger=ledger,
        frozen_systems=registry,
        exposures=exposures,
        permits=PermitRegistry(),
        permissions=(
            PermissionGrant(
                "agent",
                "backtest-governor",
                frozenset({version_two.scope_id}),
                "policy@1",
                "env@1",
            ),
        ),
        current_environment_ref="env@1",
        current_policy_ref="policy@1",
        clock=_clock,
    )
    denial = governance.authorize(request, authority_id="backtest-governor")
    assert isinstance(denial, BacktestDenial)
    assert denial.code is DenialCode.PRIOR_EXPOSURE


def test_resource_alias_does_not_restore_identical_epistemic_period() -> None:
    """A second path/resource label remains contaminated when authority binds one period."""
    ledger = ResearchLedger()
    exposures = ExposureRegistry()
    ExposureRecorder(registry=exposures, ledger=ledger, clock=_clock).record(_event())
    registry = FrozenSystemRegistry()
    descendant = _frozen(
        ledger,
        registry,
        system_id="system:descendant-alias",
        ancestry_refs=("system:a", "candidate:parent"),
    )
    alias = replace(_scope(), resource_id="holdout-alias")
    assert alias.scope_id != _scope().scope_id
    assert alias.exposure_period_id == _scope().exposure_period_id
    request = replace(
        _request(
            descendant,
            system_id=descendant.system_id,
            ancestry=descendant.ancestry_refs,
            key="aliased-descendant",
        ),
        protected_scope=alias,
    )
    governance = BacktestGovernance(
        ledger=ledger,
        frozen_systems=registry,
        exposures=exposures,
        permits=PermitRegistry(),
        permissions=(
            PermissionGrant(
                "agent",
                "backtest-governor",
                frozenset({alias.scope_id}),
                "policy@1",
                "env@1",
            ),
        ),
        current_environment_ref="env@1",
        current_policy_ref="policy@1",
        clock=_clock,
    )
    denial = governance.authorize(request, authority_id="backtest-governor")
    assert isinstance(denial, BacktestDenial)
    assert denial.code is DenialCode.PRIOR_EXPOSURE


def test_changed_disclosure_payload_conflicts_without_second_exposure() -> None:
    """Stable disclosure keys cannot hide changed protected semantics."""
    ledger = ResearchLedger()
    exposures = ExposureRegistry()
    recorder = ExposureRecorder(registry=exposures, ledger=ledger, clock=_clock)
    recorder.record(_event())

    with pytest.raises(IdempotencyConflictError, match="changed semantics"):
        recorder.record(_event(status="successful"))
    assert len(exposures.records()) == 1


def test_privileged_retry_returns_original_and_changed_payload_never_reexecutes() -> None:
    """Exact retries converge and semantic conflicts occur before another effect."""
    coordinator = PrivilegedOperationCoordinator()
    effect_count = 0

    def effect() -> str:
        nonlocal effect_count
        effect_count += 1
        return "permit:original"

    first = coordinator.execute(
        operation_key="op-1",
        semantic_payload=(("request_id", "request:1"),),
        effect=effect,
    )
    replay = coordinator.execute(
        operation_key="op-1",
        semantic_payload=(("request_id", "request:1"),),
        effect=effect,
    )
    assert first.result == replay.result == "permit:original"
    assert first.replayed is False
    assert replay.replayed is True
    assert effect_count == 1

    with pytest.raises(IdempotencyConflictError, match="changed semantics"):
        coordinator.execute(
            operation_key="op-1",
            semantic_payload=(("request_id", "request:changed"),),
            effect=effect,
        )
    assert effect_count == 1
    assert len(coordinator.records()) == 1


def test_retry_after_sealed_effect_and_lost_ack_returns_original() -> None:
    """An acknowledgement failure after sealing cannot execute the effect twice."""
    acknowledgements = 0

    def lose_first_ack(_operation_key: str) -> None:
        nonlocal acknowledgements
        acknowledgements += 1
        if acknowledgements == 1:
            message = "acknowledgement lost"
            raise ConnectionError(message)

    coordinator = PrivilegedOperationCoordinator(after_effect_sealed=lose_first_ack)
    effects = 0

    def effect() -> str:
        nonlocal effects
        effects += 1
        return "sealed-result"

    with pytest.raises(ConnectionError, match="lost"):
        coordinator.execute(
            operation_key="lost-ack",
            semantic_payload=(("request", "exact"),),
            effect=effect,
        )
    assert coordinator.records()[0].phase is PrivilegedOperationPhase.EFFECT_SEALED
    replay = coordinator.execute(
        operation_key="lost-ack",
        semantic_payload=(("request", "exact"),),
        effect=effect,
    )
    assert replay.result == "sealed-result"
    assert replay.replayed is True
    assert effects == 1
    assert coordinator.records()[0].phase is PrivilegedOperationPhase.ACKNOWLEDGED


def test_append_only_ledger_preserves_negative_history_and_rejects_rewrite() -> None:
    """Later success cannot delete or rewrite an earlier negative event."""
    ledger = ResearchLedger()
    denial = LedgerEntry.create(
        event_type="backtest.authorization-decided",
        subject_id="request:denied",
        status="deny",
        authority_id="governor",
        references=("frozen:1", "scope:1"),
        reason_code="PRIOR_EXPOSURE",
        occurred_at=NOW,
    )
    ledger.append(denial)
    accepted = LedgerEntry.create(
        event_type="backtest.authorization-decided",
        subject_id="request:later",
        status="permit",
        authority_id="governor",
        references=("frozen:2", "scope:2"),
        reason_code="AUTHORIZED",
        occurred_at=NOW,
    )
    ledger.append(accepted)

    assert ledger.entries() == (denial, accepted)
    assert ledger.entries_for("request:denied") == (denial,)
    assert not hasattr(ledger, "delete")
    rewritten = replace(denial, status="permit")
    with pytest.raises(LedgerConflictError, match="changed semantics"):
        ledger.append(rewritten)
    assert ledger.entries() == (denial, accepted)
