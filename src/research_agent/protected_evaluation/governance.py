"""Independent freeze and protected-backtest governance."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import TYPE_CHECKING

from research_agent.protected_evaluation._identity import scientific_identity
from research_agent.protected_evaluation.idempotency import PrivilegedOperationCoordinator
from research_agent.protected_evaluation.ledger import LedgerEntry, ResearchLedger
from research_agent.protected_evaluation.records import (
    BacktestDenial,
    BacktestPermit,
    BacktestRequest,
    DecisionStatus,
    DenialCode,
    FreezeDecision,
    FreezeEligibilityRequest,
    FrozenPredictiveSystemIdentity,
    ProtectedExposureStatus,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from research_agent.development import (
        DevelopmentEvidence,
        DevelopmentEvidenceRegistry,
        TrialLedger,
    )
    from research_agent.protected_evaluation.exposure import ExposureRegistry

GovernanceResult = BacktestPermit | BacktestDenial


@dataclass(frozen=True, slots=True)
class PermissionGrant:
    """Current independent permission for exact protected scopes."""

    actor_id: str
    authority_id: str
    scope_ids: frozenset[str]
    policy_ref: str
    environment_ref: str


@dataclass(frozen=True, slots=True)
class FreezeEligibilityRegistration:
    """Independent pre-registration of one exact freeze request and its inputs."""

    registration_id: str
    request: FreezeEligibilityRequest
    authority_id: str
    status: DecisionStatus
    reason_code: str

    def __post_init__(self) -> None:
        """Reject altered registrations and incomplete decision authority."""
        if not self.authority_id or not self.reason_code:
            msg = "freeze eligibility registration requires authority and reason"
            raise ValueError(msg)
        expected = scientific_identity(
            "freeze-eligibility-registration",
            (
                ("request_id", self.request.request_id),
                ("system_id", self.request.system_id),
                ("candidate_version", self.request.candidate_version),
                ("ancestry_refs", self.request.ancestry_refs),
                (
                    "development_evidence_refs",
                    self.request.development_evidence_refs,
                ),
                ("protocol_refs", self.request.protocol_refs),
                ("environment_ref", self.request.environment_ref),
                ("standard_ref", self.request.standard_ref),
                ("authority_id", self.authority_id),
                ("status", self.status.value),
                ("reason_code", self.reason_code),
            ),
        )
        if self.registration_id != expected:
            msg = "freeze eligibility registration identity does not match content"
            raise ValueError(msg)

    @classmethod
    def _issue(
        cls,
        request: FreezeEligibilityRequest,
        *,
        authority_id: str,
        status: DecisionStatus,
        reason_code: str,
    ) -> FreezeEligibilityRegistration:
        """Create a record only through the upstream-validating authority service."""
        registration_id = scientific_identity(
            "freeze-eligibility-registration",
            (
                ("request_id", request.request_id),
                ("system_id", request.system_id),
                ("candidate_version", request.candidate_version),
                ("ancestry_refs", request.ancestry_refs),
                ("development_evidence_refs", request.development_evidence_refs),
                ("protocol_refs", request.protocol_refs),
                ("environment_ref", request.environment_ref),
                ("standard_ref", request.standard_ref),
                ("authority_id", authority_id),
                ("status", status.value),
                ("reason_code", reason_code),
            ),
        )
        return cls(registration_id, request, authority_id, status, reason_code)


class FreezeEligibilityIssuer:
    """Issue exact registrations only from canonical development authority."""

    def __init__(
        self,
        *,
        authority_id: str,
        development_evidence: DevelopmentEvidenceRegistry,
        trial_ledger: TrialLedger,
        eligibility: FreezeEligibilityRegistry,
    ) -> None:
        """Bind one independent authority to evaluator and complete trial history."""
        if not authority_id:
            msg = "freeze eligibility issuer requires independent authority"
            raise ValueError(msg)
        self._authority_id = authority_id
        self._development_evidence = development_evidence
        self._trial_ledger = trial_ledger
        self._eligibility = eligibility

    def issue(
        self,
        request: FreezeEligibilityRequest,
        *,
        evidence: DevelopmentEvidence,
        status: DecisionStatus,
        reason_code: str,
    ) -> FreezeEligibilityRegistration:
        """Resolve exact system, evidence, protocol, and selected-trial inputs."""
        freeze_inputs = self._development_evidence.resolve_freeze_inputs(evidence)
        if (
            freeze_inputs.protected_evaluation_spec_ref is None
            or freeze_inputs.validation_standard_ref is None
        ):
            msg = "freeze eligibility requires predeclared protected evaluation protocols"
            raise ValueError(msg)
        trial_records = tuple(
            item for item in self._trial_ledger.records if item.trial_id == evidence.trial_id
        )
        if (
            not trial_records
            or trial_records[-1].status.value != "selected"
            or any(
                item.candidate_id != freeze_inputs.system_id
                or item.protocol_id != evidence.protocol_id
                for item in trial_records
            )
            or not any(evidence.evidence_id in item.evidence_refs for item in trial_records)
        ):
            msg = "freeze eligibility requires exact selected trial history and issued evidence"
            raise ValueError(msg)
        if (
            request.system_id != freeze_inputs.system_id
            or request.candidate_version != freeze_inputs.candidate_version
            or request.ancestry_refs != freeze_inputs.ancestry_refs
            or request.development_evidence_refs != (evidence.evidence_id,)
            or request.environment_ref != freeze_inputs.environment_id
            or request.protocol_refs != freeze_inputs.protocol_refs
        ):
            msg = "freeze request differs from authoritative system/development/protocol inputs"
            raise ValueError(msg)
        if self._authority_id in {request.requester_id, request.beneficiary_id}:
            msg = "freeze eligibility issuer cannot be the requester or beneficiary"
            raise ValueError(msg)
        registration = FreezeEligibilityRegistration._issue(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            request,
            authority_id=self._authority_id,
            status=status,
            reason_code=reason_code,
        )
        return self._eligibility._issue(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            registration
        )


class FreezeEligibilityRegistry:
    """Immutable configured authority over exact upstream freeze inputs.

    There is deliberately no public mutation method. The trusted composition root
    supplies decisions before a research caller can request assessment; the caller
    cannot mint an authority label or favorable outcome on ``assess``.
    """

    def __init__(self) -> None:
        """Start with no issued registrations and no public mutation API."""
        self._registrations: dict[str, FreezeEligibilityRegistration] = {}

    def _issue(self, registration: FreezeEligibilityRegistration) -> FreezeEligibilityRegistration:
        """Publish one authority-issued exact registration."""
        request_id = registration.request.request_id
        prior = self._registrations.get(request_id)
        if prior is not None and prior != registration:
            msg = "freeze request has conflicting eligibility registrations"
            raise ValueError(msg)
        self._registrations[request_id] = registration
        return registration

    def require_issued(self, registration: FreezeEligibilityRegistration) -> None:
        """Reject a content-valid registration absent from this authority registry."""
        if self._registrations.get(registration.request.request_id) != registration:
            msg = "freeze eligibility registration was not issued by the configured authority"
            raise ValueError(msg)

    def resolve(
        self,
        request: FreezeEligibilityRequest,
    ) -> FreezeEligibilityRegistration | None:
        """Return a registration only for the exact request and all bound input refs."""
        registration = self._registrations.get(request.request_id)
        return (
            registration if registration is not None and registration.request == request else None
        )


class FrozenSystemRegistry:
    """Exact frozen identities; no latest-version resolution is available."""

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._lock = RLock()
        self._systems: dict[str, FrozenPredictiveSystemIdentity] = {}
        self._publication_ids: dict[str, str] = {}

    def _issue(
        self,
        frozen: FrozenPredictiveSystemIdentity,
        *,
        publication: LedgerEntry,
        ledger: ResearchLedger,
    ) -> FrozenPredictiveSystemIdentity:
        """Publish only a gate-sealed identity with its authoritative ledger event."""
        if (
            not ledger.authoritative(publication)
            or publication.event_type != "freeze.system-sealed"
            or publication.subject_id != frozen.frozen_system_id
            or frozen.freeze_decision_id not in publication.references
        ):
            msg = "frozen-system issuance requires its exact authoritative seal event"
            raise ValueError(msg)
        with self._lock:
            prior = self._systems.get(frozen.frozen_system_id)
            if prior is not None and prior != frozen:
                msg = "Frozen system identity was reused with changed semantics."
                raise ValueError(msg)
            self._systems[frozen.frozen_system_id] = frozen
            self._publication_ids[frozen.frozen_system_id] = publication.entry_id
            return frozen

    def get(self, frozen_system_id: str) -> FrozenPredictiveSystemIdentity | None:
        """Resolve one exact frozen identity without fallback."""
        with self._lock:
            return self._systems.get(frozen_system_id)

    def require_issued(self, frozen: FrozenPredictiveSystemIdentity) -> None:
        """Reject a content-valid frozen identity not sealed by this gate registry."""
        with self._lock:
            if (
                self._systems.get(frozen.frozen_system_id) != frozen
                or frozen.frozen_system_id not in self._publication_ids
            ):
                msg = "frozen system was not issued by the required freeze authority"
                raise ValueError(msg)


class PermitRegistry:
    """Authoritative permits actually issued by configured governance."""

    def __init__(self) -> None:
        """Initialize an empty issued-permit registry."""
        self._lock = RLock()
        self._permits: dict[str, BacktestPermit] = {}
        self._publication_ids: dict[str, str] = {}

    def _issue(
        self,
        permit: BacktestPermit,
        *,
        publication: LedgerEntry,
        ledger: ResearchLedger,
    ) -> BacktestPermit:
        """Publish only a governance-issued permit with its exact decision event."""
        if (
            not ledger.authoritative(publication)
            or publication.event_type != "backtest.authorization-decided"
            or publication.subject_id != permit.request_id
            or publication.status != "permit"
            or permit.permit_id not in publication.references
        ):
            msg = "permit issuance requires its exact authoritative governance event"
            raise ValueError(msg)
        with self._lock:
            prior = self._permits.get(permit.permit_id)
            if prior is not None and prior != permit:
                msg = "Permit identity was reused with changed authority semantics."
                raise ValueError(msg)
            self._permits[permit.permit_id] = permit
            self._publication_ids[permit.permit_id] = publication.entry_id
            return permit

    def get(self, permit_id: str) -> BacktestPermit | None:
        """Resolve only a permit issued through this governance boundary."""
        with self._lock:
            return self._permits.get(permit_id)

    def require_issued(self, permit: BacktestPermit) -> None:
        """Reject a hash-consistent permit not issued by this governance instance."""
        with self._lock:
            if (
                self._permits.get(permit.permit_id) != permit
                or permit.permit_id not in self._publication_ids
            ):
                msg = "permit was not issued by the required governance authority"
                raise ValueError(msg)


class FreezeGate:
    """Structurally assess and seal exact upstream predictive-system identities."""

    def __init__(
        self,
        *,
        ledger: ResearchLedger,
        registry: FrozenSystemRegistry,
        eligibility: FreezeEligibilityRegistry,
        decision_authority_id: str,
        clock: Callable[[], datetime],
    ) -> None:
        """Bind the gate to independent history, registry, and time authority."""
        self._ledger = ledger
        self._registry = registry
        self._eligibility = eligibility
        if not decision_authority_id:
            msg = "Freeze gate requires one configured independent decision authority."
            raise ValueError(msg)
        self._decision_authority_id = decision_authority_id
        self._clock = clock
        self._decisions: dict[str, FreezeDecision] = {}

    def assess(self, request: FreezeEligibilityRequest) -> FreezeDecision:
        """Apply the configured pre-issued decision; the requester supplies no authority."""
        authority_id = self._decision_authority_id
        registration = self._eligibility.resolve(request)
        if registration is None:
            status = DecisionStatus.DENY
            safe_reason = DenialCode.INCOMPLETE_PREDECLARATION.value
        elif registration.authority_id != authority_id:
            status = DecisionStatus.DENY
            safe_reason = DenialCode.AUTHORITY_NOT_AUTHORIZED.value
        elif authority_id in {request.requester_id, request.beneficiary_id}:
            status = DecisionStatus.DENY
            safe_reason = DenialCode.SELF_AUTHORIZATION.value
        else:
            status = registration.status
            safe_reason = registration.reason_code
        decided_at = self._clock()
        decision_id = scientific_identity(
            "freeze-decision",
            (
                ("request_id", request.request_id),
                ("authority_id", authority_id),
                ("status", status.value),
                ("reason_code", safe_reason),
                ("decided_at", decided_at.isoformat()),
            ),
        )
        decision = FreezeDecision(
            decision_id=decision_id,
            request_id=request.request_id,
            system_id=request.system_id,
            authority_id=authority_id,
            status=status,
            reason_code=safe_reason,
            decided_at=decided_at,
        )
        self._ledger.append(
            LedgerEntry.create(
                event_type="freeze.eligibility-decided",
                subject_id=request.system_id,
                status=status.value,
                authority_id=authority_id,
                references=(request.request_id, *request.ancestry_refs),
                reason_code=safe_reason,
                occurred_at=decided_at,
            )
        )
        self._decisions[decision.decision_id] = decision
        return decision

    def seal(
        self,
        request: FreezeEligibilityRequest,
        decision: FreezeDecision,
    ) -> FrozenPredictiveSystemIdentity:
        """Seal only an accepted decision bound to the exact request and system."""
        if (
            self._decisions.get(decision.decision_id) != decision
            or decision.status is not DecisionStatus.ACCEPT
            or decision.request_id != request.request_id
            or decision.system_id != request.system_id
        ):
            msg = "Freeze decision does not accept this exact candidate request."
            raise ValueError(msg)
        frozen_at = self._clock()
        frozen_system_id = scientific_identity(
            "frozen-system",
            (
                ("system_id", request.system_id),
                ("candidate_version", request.candidate_version),
                ("ancestry_refs", request.ancestry_refs),
                ("development_evidence_refs", request.development_evidence_refs),
                ("protocol_refs", request.protocol_refs),
                ("environment_ref", request.environment_ref),
                ("standard_ref", request.standard_ref),
                ("freeze_decision_id", decision.decision_id),
            ),
        )
        prior = self._registry.get(frozen_system_id)
        if prior is not None:
            return prior
        frozen = FrozenPredictiveSystemIdentity(
            frozen_system_id=frozen_system_id,
            system_id=request.system_id,
            candidate_version=request.candidate_version,
            ancestry_refs=request.ancestry_refs,
            development_evidence_refs=request.development_evidence_refs,
            protocol_refs=request.protocol_refs,
            environment_ref=request.environment_ref,
            standard_ref=request.standard_ref,
            freeze_decision_id=decision.decision_id,
            freeze_authority_id=decision.authority_id,
            frozen_at=frozen_at,
        )
        publication = self._ledger.append(
            LedgerEntry.create(
                event_type="freeze.system-sealed",
                subject_id=frozen_system_id,
                status="frozen",
                authority_id=decision.authority_id,
                references=(
                    request.system_id,
                    decision.decision_id,
                    *request.ancestry_refs,
                    *request.protocol_refs,
                ),
                reason_code="ELIGIBLE",
                occurred_at=frozen_at,
            )
        )
        self._registry._issue(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            frozen,
            publication=publication,
            ledger=self._ledger,
        )
        return frozen


class BacktestGovernance:
    """Issue exact permits or safe denials without access to protected content."""

    def __init__(  # noqa: PLR0913
        self,
        *,
        ledger: ResearchLedger,
        frozen_systems: FrozenSystemRegistry,
        exposures: ExposureRegistry,
        permits: PermitRegistry,
        permissions: tuple[PermissionGrant, ...],
        current_environment_ref: str,
        current_policy_ref: str,
        clock: Callable[[], datetime],
        operations: PrivilegedOperationCoordinator | None = None,
    ) -> None:
        """Configure authoritative metadata only; protected bytes are not accepted."""
        self._ledger = ledger
        self._frozen_systems = frozen_systems
        self._exposures = exposures
        self._permits = permits
        self._permissions = permissions
        self._environment_ref = current_environment_ref
        self._policy_ref = current_policy_ref
        self._clock = clock
        self._operations = operations or PrivilegedOperationCoordinator()

    @property
    def issued_permits(self) -> PermitRegistry:
        """Expose the authoritative registry required by protected-view binding."""
        return self._permits

    def authorize(self, request: BacktestRequest, *, authority_id: str) -> GovernanceResult:
        """Return a scope-bound permit or safe fail-closed denial idempotently."""
        payload = (("request_id", request.request_id), ("authority_id", authority_id))
        return self._operations.execute(
            operation_key=f"authorize:{request.idempotency_key}",
            semantic_payload=payload,
            effect=lambda: self._decide(request, authority_id),
        ).result

    def _decide(self, request: BacktestRequest, authority_id: str) -> GovernanceResult:
        code = self._denial_code(request, authority_id)
        if code is not None:
            return self._deny(request, authority_id, code)
        issued_at = self._clock()
        permit_id = scientific_identity(
            "backtest-permit",
            (
                ("request_id", request.request_id),
                ("scope_id", request.protected_scope.scope_id),
                ("authority_id", authority_id),
                ("policy_ref", self._policy_ref),
            ),
        )
        permit = BacktestPermit(
            permit_id=permit_id,
            request_id=request.request_id,
            frozen_system_id=request.frozen_system_id,
            system_id=request.system_id,
            scenario_ref=request.scenario_ref,
            scope=request.protected_scope,
            requester_id=request.requester_id,
            authority_id=authority_id,
            policy_ref=self._policy_ref,
            issued_at=issued_at,
        )
        publication = self._record_decision(
            request,
            decision_id=permit_id,
            status="permit",
            authority_id=authority_id,
            reason_code="AUTHORIZED",
            occurred_at=issued_at,
        )
        self._permits._issue(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            permit,
            publication=publication,
            ledger=self._ledger,
        )
        return permit

    def _denial_code(  # noqa: C901, PLR0911
        self, request: BacktestRequest, authority_id: str
    ) -> DenialCode | None:
        frozen = self._frozen_systems.get(request.frozen_system_id)
        if authority_id in {request.requester_id, request.beneficiary_id}:
            return DenialCode.SELF_AUTHORIZATION
        if frozen is None:
            return DenialCode.UNFROZEN_SYSTEM
        if frozen.system_id != request.system_id or (
            request.environment_ref != self._environment_ref
            or request.protected_scope.environment_ref != self._environment_ref
            or request.protected_scope.policy_ref != self._policy_ref
        ):
            return DenialCode.STALE_IDENTITY
        if (
            request.ancestry_refs != frozen.ancestry_refs
            or request.training_protocol_ref not in frozen.protocol_refs
            or request.evaluation_spec_ref not in frozen.protocol_refs
            or request.validation_standard_ref not in frozen.protocol_refs
        ):
            return DenialCode.INCOMPLETE_PREDECLARATION
        grant = self._grant_for(request.requester_id)
        if grant is None:
            return DenialCode.CALLER_NOT_AUTHORIZED
        if authority_id != grant.authority_id:
            return DenialCode.AUTHORITY_NOT_AUTHORIZED
        if authority_id in {grant.actor_id, request.beneficiary_id}:
            return DenialCode.SELF_AUTHORIZATION
        if grant.policy_ref != self._policy_ref or grant.environment_ref != self._environment_ref:
            return DenialCode.STALE_IDENTITY
        if request.protected_scope.scope_id not in grant.scope_ids:
            return DenialCode.SCOPE_NOT_AUTHORIZED
        if request.protected_scope.exposure_status is ProtectedExposureStatus.PREEXPOSED:
            return DenialCode.PRIOR_EXPOSURE
        lineage = frozenset((request.system_id, *frozen.ancestry_refs))
        exposure_refs = self._exposures.references_for(
            exposure_period_id=request.protected_scope.exposure_period_id,
            lineage_refs=lineage,
        )
        if exposure_refs:
            return DenialCode.PRIOR_EXPOSURE
        if request.prior_exposure_refs:
            return DenialCode.STALE_IDENTITY
        return None

    def _grant_for(self, actor_id: str) -> PermissionGrant | None:
        return next((grant for grant in self._permissions if grant.actor_id == actor_id), None)

    def _deny(
        self,
        request: BacktestRequest,
        authority_id: str,
        code: DenialCode,
    ) -> BacktestDenial:
        denied_at = self._clock()
        denial_id = scientific_identity(
            "backtest-denial",
            (
                ("request_id", request.request_id),
                ("authority_id", authority_id),
                ("code", code.value),
            ),
        )
        denial = BacktestDenial(
            denial_id=denial_id,
            request_id=request.request_id,
            code=code,
            message="Protected evaluation was denied by governance metadata checks.",
            authority_id=authority_id,
            denied_at=denied_at,
        )
        self._record_decision(
            request,
            decision_id=denial_id,
            status="deny",
            authority_id=authority_id,
            reason_code=code.value,
            occurred_at=denied_at,
        )
        return denial

    def _record_decision(  # noqa: PLR0913
        self,
        request: BacktestRequest,
        *,
        decision_id: str,
        status: str,
        authority_id: str,
        reason_code: str,
        occurred_at: datetime,
    ) -> LedgerEntry:
        return self._ledger.append(
            LedgerEntry.create(
                event_type="backtest.authorization-decided",
                subject_id=request.request_id,
                status=status,
                authority_id=authority_id,
                references=(
                    decision_id,
                    request.frozen_system_id,
                    request.protected_scope.scope_id,
                ),
                reason_code=reason_code,
                occurred_at=occurred_at,
            )
        )


__all__ = [
    "BacktestGovernance",
    "FreezeEligibilityIssuer",
    "FreezeEligibilityRegistration",
    "FreezeEligibilityRegistry",
    "FreezeGate",
    "FrozenSystemRegistry",
    "GovernanceResult",
    "PermissionGrant",
    "PermitRegistry",
]
