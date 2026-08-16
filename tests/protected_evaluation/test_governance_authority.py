"""Adversarial authority and protected-view binding tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from threading import Barrier, Lock
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest

from research_agent.development import (
    DevelopmentEvidence,
    DevelopmentEvidenceRegistry,
    DevelopmentProtocol,
    TrialLedger,
    TrialStatus,
)
from research_agent.protected_evaluation import (
    AuthorizedProtectedDataView,
    BacktestDenial,
    BacktestGovernance,
    BacktestPermit,
    BacktestRequest,
    DecisionStatus,
    DenialCode,
    DisclosureEvent,
    ExposureRecorder,
    ExposureRegistry,
    FreezeEligibilityIssuer,
    FreezeEligibilityRegistration,
    FreezeEligibilityRegistry,
    FreezeEligibilityRequest,
    FreezeGate,
    FrozenPredictiveSystemIdentity,
    FrozenSystemRegistry,
    IdempotencyConflictError,
    PermissionGrant,
    PermitRegistry,
    ProtectedExposureStatus,
    ProtectedResourceScope,
    ProtectedViewBinder,
    ResearchLedger,
)
from research_agent.protected_evaluation._identity import scientific_identity

if TYPE_CHECKING:
    from collections.abc import Callable

    from research_agent.formalization import PredictiveSystemDefinition

NOW = datetime(2026, 8, 15, 12, tzinfo=UTC)


def _clock() -> datetime:
    return NOW


def _scope(*, slice_id: str = "holdout-2025", environment: str = "env@1") -> ProtectedResourceScope:
    return ProtectedResourceScope(
        resource_id="protected-outcomes",
        resource_version="v1",
        slice_id=slice_id,
        environment_ref=environment,
        policy_ref="policy@1",
        content_manifest_id="protected-content-manifest:holdout-2025",
        content_identity_id="protected-content:holdout-2025",
        epistemic_period_ref="epistemic-period:holdout-2025",
        exposure_status=ProtectedExposureStatus.UNSEEN,
    )


def _freeze(
    ledger: ResearchLedger, registry: FrozenSystemRegistry
) -> tuple[FreezeEligibilityRequest, FrozenPredictiveSystemIdentity]:
    request = FreezeEligibilityRequest(
        system_id="system:exact-content-id",
        candidate_version="7",
        ancestry_refs=("trial:failed", "candidate:parent"),
        development_evidence_refs=("development-report:7",),
        protocol_refs=(
            "training-protocol:3",
            "evaluation-spec:4",
            "promotion-standard:1",
        ),
        environment_ref="env@1",
        standard_ref="development-standard:2",
        requester_id="research-agent",
        beneficiary_id="candidate-team",
    )
    gate = FreezeGate(
        ledger=ledger,
        registry=registry,
        eligibility=_eligibility(request, authority_id="freeze-governor"),
        decision_authority_id="freeze-governor",
        clock=_clock,
    )
    decision = gate.assess(request)
    return request, gate.seal(request, decision)


def _eligibility(
    *requests: FreezeEligibilityRequest,
    authority_id: str,
    status: DecisionStatus = DecisionStatus.ACCEPT,
    reason_code: str = "DEVELOPMENT_STANDARD_MET",
) -> FreezeEligibilityRegistry:
    registry = FreezeEligibilityRegistry()
    for request in requests:
        registration = FreezeEligibilityRegistration._issue(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            request,
            authority_id=authority_id,
            status=status,
            reason_code=reason_code,
        )
        registry._issue(registration)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    return registry


def _backtest_request(  # noqa: PLR0913
    *,
    frozen_system_id: str,
    system_id: str = "system:exact-content-id",
    scope: ProtectedResourceScope | None = None,
    environment_ref: str = "env@1",
    requester_id: str = "research-agent",
    key: str = "backtest-1",
    ancestry_refs: tuple[str, ...] = ("trial:failed", "candidate:parent"),
) -> BacktestRequest:
    return BacktestRequest(
        frozen_system_id=frozen_system_id,
        system_id=system_id,
        scenario_ref="historical-walk-forward:1",
        decision_times_ref="decision-times:2025",
        training_protocol_ref="training-protocol:3",
        evaluation_spec_ref="evaluation-spec:4",
        validation_standard_ref="promotion-standard:1",
        claim_ref="claim:predictive-improvement",
        protected_scope=scope or _scope(),
        environment_ref=environment_ref,
        ancestry_refs=ancestry_refs,
        prior_exposure_refs=(),
        requester_id=requester_id,
        beneficiary_id="candidate-team",
        idempotency_key=key,
    )


def _governance(
    *,
    ledger: ResearchLedger,
    registry: FrozenSystemRegistry,
    exposures: ExposureRegistry,
    allowed_scope: ProtectedResourceScope,
) -> BacktestGovernance:
    return BacktestGovernance(
        ledger=ledger,
        frozen_systems=registry,
        exposures=exposures,
        permits=PermitRegistry(),
        permissions=(
            PermissionGrant(
                actor_id="research-agent",
                authority_id="backtest-governor",
                scope_ids=frozenset({allowed_scope.scope_id}),
                policy_ref="policy@1",
                environment_ref="env@1",
            ),
        ),
        current_environment_ref="env@1",
        current_policy_ref="policy@1",
        clock=_clock,
    )


def test_freeze_rejects_self_approval_and_seals_exact_upstream_identity() -> None:
    """A beneficiary cannot approve itself and material change creates new identity."""
    ledger = ResearchLedger()
    registry = FrozenSystemRegistry()
    request = FreezeEligibilityRequest(
        system_id="system:exact",
        candidate_version="1",
        ancestry_refs=("trial:1",),
        development_evidence_refs=("development:1",),
        protocol_refs=("protocol:1",),
        environment_ref="env@1",
        standard_ref="standard:1",
        requester_id="agent",
        beneficiary_id="team",
    )
    self_gate = FreezeGate(
        ledger=ledger,
        registry=registry,
        eligibility=_eligibility(request, authority_id="agent"),
        decision_authority_id="agent",
        clock=_clock,
    )
    denied = self_gate.assess(request)
    assert denied.status is DecisionStatus.DENY
    assert denied.reason_code == DenialCode.SELF_AUTHORIZATION.value
    with pytest.raises(ValueError, match="does not accept"):
        self_gate.seal(request, denied)

    wrong_authority_gate = FreezeGate(
        ledger=ledger,
        registry=registry,
        eligibility=_eligibility(request, authority_id="independent-freezer"),
        decision_authority_id="unconfigured-freezer",
        clock=_clock,
    )
    unauthorized = wrong_authority_gate.assess(request)
    assert unauthorized.status is DecisionStatus.DENY
    assert unauthorized.reason_code == DenialCode.AUTHORITY_NOT_AUTHORIZED.value

    changed = replace(request, protocol_refs=("protocol:2",))
    gate = FreezeGate(
        ledger=ledger,
        registry=registry,
        eligibility=_eligibility(
            request,
            changed,
            authority_id="independent-freezer",
            reason_code="STANDARD_MET",
        ),
        decision_authority_id="independent-freezer",
        clock=_clock,
    )
    accepted = gate.assess(request)
    with pytest.raises(ValueError, match="does not accept"):
        gate.seal(request, replace(accepted, decision_id="fabricated-decision"))
    frozen = gate.seal(request, accepted)
    assert gate.seal(request, accepted) is frozen
    changed_decision = gate.assess(changed)
    changed_frozen = gate.seal(changed, changed_decision)

    assert frozen.system_id == "system:exact"
    assert frozen.protocol_refs == ("protocol:1",)
    assert changed_frozen.frozen_system_id != frozen.frozen_system_id
    assert registry.get(frozen.frozen_system_id) == frozen


@pytest.mark.parametrize(
    "mutation",
    [
        {"system_id": "invented-system"},
        {"development_evidence_refs": ("invented-development-evidence",)},
        {"protocol_refs": ("invented-protocol",)},
        {"ancestry_refs": ("invented-trial",)},
    ],
)
def test_freeze_denies_forged_upstream_refs_absent_from_authority_registration(
    mutation: dict[str, object],
) -> None:
    """Self-consistent hashes cannot replace pre-registered upstream authority."""
    ledger = ResearchLedger()
    registry = FrozenSystemRegistry()
    registered = FreezeEligibilityRequest(
        system_id="system:registered",
        candidate_version="1",
        ancestry_refs=("trial:registered",),
        development_evidence_refs=("development:registered",),
        protocol_refs=("protocol:registered",),
        environment_ref="env@1",
        standard_ref="standard:registered",
        requester_id="agent",
        beneficiary_id="team",
    )
    gate = FreezeGate(
        ledger=ledger,
        registry=registry,
        eligibility=_eligibility(registered, authority_id="independent-freezer"),
        decision_authority_id="independent-freezer",
        clock=_clock,
    )
    forged = replace(registered, **mutation)

    denied = gate.assess(forged)

    assert denied.status is DecisionStatus.DENY
    assert denied.reason_code == DenialCode.INCOMPLETE_PREDECLARATION.value
    with pytest.raises(ValueError, match="does not accept"):
        gate.seal(forged, denied)


def test_freeze_requester_cannot_supply_authority_or_approval_at_assessment_time() -> None:
    """The public call consumes a configured decision instead of caller-authored approval."""
    request = FreezeEligibilityRequest(
        system_id="system:registered",
        candidate_version="1",
        ancestry_refs=("trial:registered",),
        development_evidence_refs=("development:registered",),
        protocol_refs=("protocol:registered",),
        environment_ref="env@1",
        standard_ref="standard:registered",
        requester_id="agent",
        beneficiary_id="team",
    )
    gate = FreezeGate(
        ledger=ResearchLedger(),
        registry=FrozenSystemRegistry(),
        eligibility=_eligibility(
            request,
            authority_id="independent-freezer",
            status=DecisionStatus.DENY,
            reason_code="EVIDENCE_INSUFFICIENT",
        ),
        decision_authority_id="independent-freezer",
        clock=_clock,
    )

    assessment = cast("Callable[..., object]", gate.assess)
    with pytest.raises(TypeError):
        assessment(
            request,
            authority_id="independent-freezer",
            approve=True,
        )
    decision = gate.assess(request)
    assert decision.status is DecisionStatus.DENY
    assert decision.reason_code == "EVIDENCE_INSUFFICIENT"


def test_content_valid_registration_is_powerless_until_authority_registry_issues_it() -> None:
    """A caller-created decision record cannot become configured gate authority."""
    request = FreezeEligibilityRequest(
        system_id="system:registered",
        candidate_version="1",
        ancestry_refs=("trial:registered",),
        development_evidence_refs=("development:registered",),
        protocol_refs=("protocol:registered",),
        environment_ref="env@1",
        standard_ref="standard:registered",
        requester_id="agent",
        beneficiary_id="team",
    )
    unissued = FreezeEligibilityRegistration._issue(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        request,
        authority_id="independent-freezer",
        status=DecisionStatus.ACCEPT,
        reason_code="CLAIMED_VALID",
    )
    eligibility = FreezeEligibilityRegistry()
    gate = FreezeGate(
        ledger=ResearchLedger(),
        registry=FrozenSystemRegistry(),
        eligibility=eligibility,
        decision_authority_id="independent-freezer",
        clock=_clock,
    )

    with pytest.raises(ValueError, match="not issued"):
        eligibility.require_issued(unissued)
    denied = gate.assess(request)
    assert denied.status is DecisionStatus.DENY
    assert denied.reason_code == DenialCode.INCOMPLETE_PREDECLARATION.value


def test_public_eligibility_issuer_rejects_invented_system_or_development_refs() -> None:
    """The original invented-system attack fails before an authority record is issued."""
    evidence_registry = DevelopmentEvidenceRegistry()
    evidence = cast(
        "DevelopmentEvidence",
        SimpleNamespace(
            evidence_id="development:issued",
            trial_id="trial:issued",
            candidate_id="system:issued",
            protocol_id="development-protocol:issued",
            environment_id="env@1",
            fit_records=(
                SimpleNamespace(
                    training_information_bundle_id="training-information:issued",
                    information_set_ids=("information-set:issued",),
                    row_ids=("row:issued",),
                    feature_series_ids=("feature-series:issued",),
                    compiled_feature_ids=("compiled-feature:issued",),
                ),
            ),
        ),
    )
    definition = cast(
        "PredictiveSystemDefinition",
        SimpleNamespace(
            identity="system:issued",
            version=1,
            candidate_ancestry=("trial:parent",),
            environment_id="env@1",
            data_protocol_id="data:issued",
            training_protocol_id="training:issued",
            evaluation_protocol_id="development-protocol:issued",
        ),
    )
    protocol = cast(
        "DevelopmentProtocol",
        SimpleNamespace(identity="development-protocol:issued", environment_id="env@1"),
    )
    evidence_registry._issue(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        evidence,
        definition=definition,
        protocol=protocol,
        protected_evaluation_spec_ref="protected-spec:issued",
        validation_standard_ref="validation-standard:issued",
    )
    trial_ledger = TrialLedger()
    trial_ledger.append(
        trial_id="trial:issued",
        candidate_id="system:issued",
        protocol_id="development-protocol:issued",
        parent_trial_ids=(),
        status=TrialStatus.ATTEMPTED,
        rationale="attempt",
    )
    trial_ledger.append(
        trial_id="trial:issued",
        candidate_id="system:issued",
        protocol_id="development-protocol:issued",
        parent_trial_ids=(),
        status=TrialStatus.SUCCEEDED,
        rationale="issued development evidence",
        evidence_refs=("development:issued",),
    )
    trial_ledger.append(
        trial_id="trial:issued",
        candidate_id="system:issued",
        protocol_id="development-protocol:issued",
        parent_trial_ids=(),
        status=TrialStatus.SELECTED,
        rationale="selected for independent freeze assessment",
        evidence_refs=("development:issued",),
    )
    eligibility = FreezeEligibilityRegistry()
    issuer = FreezeEligibilityIssuer(
        authority_id="freeze-board",
        development_evidence=evidence_registry,
        trial_ledger=trial_ledger,
        eligibility=eligibility,
    )
    legitimate = FreezeEligibilityRequest(
        system_id="system:issued",
        candidate_version="1",
        ancestry_refs=("trial:parent",),
        development_evidence_refs=("development:issued",),
        protocol_refs=(
            "data:issued",
            "training:issued",
            "development-protocol:issued",
            "protected-spec:issued",
            "validation-standard:issued",
        ),
        environment_ref="env@1",
        standard_ref="freeze-standard:issued",
        requester_id="research-agent",
        beneficiary_id="candidate-team",
    )
    registration = issuer.issue(
        legitimate,
        evidence=evidence,
        status=DecisionStatus.ACCEPT,
        reason_code="DEVELOPMENT_STANDARD_MET",
    )
    assert registration.request == legitimate
    eligibility.require_issued(registration)

    for forged in (
        replace(legitimate, system_id="invented-system"),
        replace(legitimate, development_evidence_refs=("invented-evidence",)),
        replace(legitimate, protocol_refs=("invented-protocol",)),
    ):
        with pytest.raises(ValueError, match="authoritative system/development/protocol"):
            issuer.issue(
                forged,
                evidence=evidence,
                status=DecisionStatus.ACCEPT,
                reason_code="CLAIMED_VALID",
            )


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("unfrozen", DenialCode.UNFROZEN_SYSTEM),
        ("self-approved", DenialCode.SELF_AUTHORIZATION),
        ("unauthorized-authority", DenialCode.AUTHORITY_NOT_AUTHORIZED),
        ("stale", DenialCode.STALE_IDENTITY),
        ("scope", DenialCode.SCOPE_NOT_AUTHORIZED),
    ],
)
def test_invalid_requests_deny_before_any_protected_resolution(
    case: str, expected: DenialCode
) -> None:
    """Unfrozen, self-approved, stale, and scope-invalid requests read nothing."""
    ledger = ResearchLedger()
    registry = FrozenSystemRegistry()
    _, frozen = _freeze(ledger, registry)
    allowed_scope = _scope()
    governance = _governance(
        ledger=ledger,
        registry=registry,
        exposures=ExposureRegistry(),
        allowed_scope=allowed_scope,
    )
    request = _backtest_request(
        frozen_system_id=frozen.frozen_system_id,
        key=f"backtest-{case}",
    )
    authority = "backtest-governor"
    if case == "unfrozen":
        request = replace(request, frozen_system_id="frozen:missing")
    elif case == "self-approved":
        authority = "research-agent"
    elif case == "unauthorized-authority":
        authority = "unconfigured-governor"
    elif case == "stale":
        request = replace(request, environment_ref="env@stale")
    elif case == "scope":
        request = replace(request, protected_scope=_scope(slice_id="neighboring-holdout"))

    decision = governance.authorize(request, authority_id=authority)
    assert isinstance(decision, BacktestDenial)
    assert decision.code is expected
    assert "protected-outcome-sentinel=91.7" not in decision.message

    resolution_count = 0

    def fail_if_resolved(_scope_value: ProtectedResourceScope) -> str:
        nonlocal resolution_count
        resolution_count += 1
        return "must-not-be-resolved"

    bound = ProtectedViewBinder(
        permits=governance.issued_permits,
        clock=_clock,
        current_environment_ref="env@1",
        current_policy_ref="policy@1",
    ).bind(
        permit=decision,
        request=request,
        requested_scope=request.protected_scope,
        caller_id=request.requester_id,
        resolve_exact_resource=fail_if_resolved,
    )
    assert bound == decision
    assert resolution_count == 0


def test_exact_permit_binds_only_its_scope_and_caller() -> None:
    """A valid permit cannot be swapped to another protected slice."""
    ledger = ResearchLedger()
    registry = FrozenSystemRegistry()
    _, frozen = _freeze(ledger, registry)
    scope = _scope()
    exposures = ExposureRegistry()
    governance = _governance(
        ledger=ledger,
        registry=registry,
        exposures=exposures,
        allowed_scope=scope,
    )
    request = _backtest_request(frozen_system_id=frozen.frozen_system_id)
    permit = governance.authorize(request, authority_id="backtest-governor")
    assert isinstance(permit, BacktestPermit)
    resolutions: list[str] = []

    def resolve(scope_value: ProtectedResourceScope) -> str:
        resolutions.append(scope_value.scope_id)
        return "protected-binding:exact-v1-slice"

    stale_binder = ProtectedViewBinder(
        permits=governance.issued_permits,
        clock=_clock,
        current_environment_ref="env@1",
        current_policy_ref="policy@2",
    )
    stale = stale_binder.bind(
        permit=permit,
        request=request,
        requested_scope=scope,
        caller_id="research-agent",
        resolve_exact_resource=resolve,
    )
    assert isinstance(stale, BacktestDenial)
    assert resolutions == []

    binder = ProtectedViewBinder(
        permits=governance.issued_permits,
        clock=_clock,
        current_environment_ref="env@1",
        current_policy_ref="policy@1",
    )
    fabricated = binder.bind(
        permit=replace(permit, permit_id="permit:fabricated"),
        request=request,
        requested_scope=scope,
        caller_id="research-agent",
        resolve_exact_resource=resolve,
    )
    assert isinstance(fabricated, BacktestDenial)
    assert fabricated.code is DenialCode.PERMIT_MISMATCH
    assert resolutions == []

    swapped = binder.bind(
        permit=permit,
        request=request,
        requested_scope=_scope(slice_id="neighboring-holdout"),
        caller_id="research-agent",
        resolve_exact_resource=resolve,
    )
    assert isinstance(swapped, BacktestDenial)
    assert resolutions == []

    view = binder.bind(
        permit=permit,
        request=request,
        requested_scope=scope,
        caller_id="research-agent",
        resolve_exact_resource=resolve,
    )
    assert isinstance(view, AuthorizedProtectedDataView)
    assert view.scope == permit.scope == request.protected_scope
    assert resolutions == [scope.scope_id]

    replay = binder.bind(
        permit=permit,
        request=request,
        requested_scope=scope,
        caller_id="research-agent",
        resolve_exact_resource=resolve,
    )
    assert replay == view
    assert resolutions == [scope.scope_id]

    exposure = ExposureRecorder(registry=exposures, ledger=ledger, clock=_clock).record(
        DisclosureEvent(
            disclosure_key="view-disclosure-1",
            view_id=view.view_id,
            permit_id=permit.permit_id,
            request_id=request.request_id,
            frozen_system_id=frozen.frozen_system_id,
            system_id=frozen.system_id,
            lineage_refs=frozen.ancestry_refs,
            scope=view.scope,
            recipient_id="research-process:1",
            disclosure_status="failed-after-read",
        )
    )
    assert exposure.view_id == view.view_id
    assert exposure.scope == view.scope


def test_preexposed_content_is_denied_before_protected_resolution() -> None:
    """Previously public or inspected bytes cannot be relabeled as unseen holdout evidence."""
    ledger = ResearchLedger()
    registry = FrozenSystemRegistry()
    _, frozen = _freeze(ledger, registry)
    scope = replace(_scope(), exposure_status=ProtectedExposureStatus.PREEXPOSED)
    governance = _governance(
        ledger=ledger,
        registry=registry,
        exposures=ExposureRegistry(),
        allowed_scope=scope,
    )
    request = replace(
        _backtest_request(frozen_system_id=frozen.frozen_system_id),
        protected_scope=scope,
        idempotency_key="preexposed-content",
    )
    denial = governance.authorize(request, authority_id="backtest-governor")
    assert isinstance(denial, BacktestDenial)
    assert denial.code is DenialCode.PRIOR_EXPOSURE

    resolutions = 0

    def resolve(_scope_value: ProtectedResourceScope) -> str:
        nonlocal resolutions
        resolutions += 1
        return "must-not-resolve"

    bound = ProtectedViewBinder(
        permits=governance.issued_permits,
        clock=_clock,
        current_environment_ref="env@1",
        current_policy_ref="policy@1",
    ).bind(
        permit=denial,
        request=request,
        requested_scope=scope,
        caller_id=request.requester_id,
        resolve_exact_resource=resolve,
    )
    assert bound == denial
    assert resolutions == 0


def test_rehashed_unissued_permit_is_rejected_and_registries_have_no_caller_add() -> None:
    """Content addressing cannot turn a caller-created permit into governance authority."""
    ledger = ResearchLedger()
    registry = FrozenSystemRegistry()
    _, frozen = _freeze(ledger, registry)
    scope = _scope()
    governance = _governance(
        ledger=ledger,
        registry=registry,
        exposures=ExposureRegistry(),
        allowed_scope=scope,
    )
    request = _backtest_request(frozen_system_id=frozen.frozen_system_id)
    permit = governance.authorize(request, authority_id="backtest-governor")
    assert isinstance(permit, BacktestPermit)
    forged_authority = "caller-forged-governor"
    forged_id = scientific_identity(
        "backtest-permit",
        (
            ("request_id", request.request_id),
            ("scope_id", scope.scope_id),
            ("authority_id", forged_authority),
            ("policy_ref", "policy@1"),
        ),
    )
    forged = replace(permit, permit_id=forged_id, authority_id=forged_authority)
    binder = ProtectedViewBinder(
        permits=governance.issued_permits,
        clock=_clock,
        current_environment_ref="env@1",
        current_policy_ref="policy@1",
    )
    reads = 0

    def resolve(_scope_value: ProtectedResourceScope) -> str:
        nonlocal reads
        reads += 1
        return "forbidden"

    denial = binder.bind(
        permit=forged,
        request=request,
        requested_scope=scope,
        caller_id="research-agent",
        resolve_exact_resource=resolve,
    )
    assert isinstance(denial, BacktestDenial)
    assert denial.code is DenialCode.PERMIT_MISMATCH
    assert reads == 0
    assert not hasattr(governance.issued_permits, "add")
    assert not hasattr(registry, "add")


def test_protected_view_binding_is_concurrent_and_resolves_once() -> None:
    """Two callers racing the same exact permit converge on one resolved view."""
    ledger = ResearchLedger()
    registry = FrozenSystemRegistry()
    _, frozen = _freeze(ledger, registry)
    scope = _scope()
    governance = _governance(
        ledger=ledger,
        registry=registry,
        exposures=ExposureRegistry(),
        allowed_scope=scope,
    )
    request = _backtest_request(frozen_system_id=frozen.frozen_system_id)
    permit = governance.authorize(request, authority_id="backtest-governor")
    assert isinstance(permit, BacktestPermit)
    binder = ProtectedViewBinder(
        permits=governance.issued_permits,
        clock=_clock,
        current_environment_ref="env@1",
        current_policy_ref="policy@1",
    )
    barrier = Barrier(2)
    count_lock = Lock()
    resolutions = 0

    def bind() -> AuthorizedProtectedDataView | BacktestDenial:
        nonlocal resolutions
        barrier.wait()

        def resolve(_scope_value: ProtectedResourceScope) -> str:
            nonlocal resolutions
            with count_lock:
                resolutions += 1
            return "protected-binding:concurrent"

        return binder.bind(
            permit=permit,
            request=request,
            requested_scope=scope,
            caller_id="research-agent",
            resolve_exact_resource=resolve,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(bind)
        second = pool.submit(bind)
        results = (first.result(), second.result())
    assert isinstance(results[0], AuthorizedProtectedDataView)
    assert results[0] is results[1]
    assert resolutions == 1


def test_request_cannot_launder_frozen_ancestry() -> None:
    """Omitting a losing or exposed parent is not a valid request for the frozen system."""
    ledger = ResearchLedger()
    registry = FrozenSystemRegistry()
    _, frozen = _freeze(ledger, registry)
    governance = _governance(
        ledger=ledger,
        registry=registry,
        exposures=ExposureRegistry(),
        allowed_scope=_scope(),
    )
    laundered = _backtest_request(
        frozen_system_id=frozen.frozen_system_id,
        ancestry_refs=("candidate:parent",),
        key="laundered-ancestry",
    )
    decision = governance.authorize(laundered, authority_id="backtest-governor")
    assert isinstance(decision, BacktestDenial)
    assert decision.code is DenialCode.INCOMPLETE_PREDECLARATION


def test_changed_request_under_same_key_conflicts_before_second_decision() -> None:
    """Idempotency identity covers the full predeclared BacktestRequest semantics."""
    ledger = ResearchLedger()
    registry = FrozenSystemRegistry()
    _, frozen = _freeze(ledger, registry)
    scope = _scope()
    governance = _governance(
        ledger=ledger,
        registry=registry,
        exposures=ExposureRegistry(),
        allowed_scope=scope,
    )
    request = _backtest_request(frozen_system_id=frozen.frozen_system_id, key="stable-key")
    first = governance.authorize(request, authority_id="backtest-governor")
    assert isinstance(first, BacktestPermit)
    changed = replace(request, evaluation_spec_ref="evaluation-spec:changed")

    with pytest.raises(IdempotencyConflictError, match="changed semantics"):
        governance.authorize(changed, authority_id="backtest-governor")
    decisions = [
        entry for entry in ledger.entries() if entry.event_type == "backtest.authorization-decided"
    ]
    assert len(decisions) == 1
