"""Independent finding or rejection resolution for frozen authored research."""

# ruff: noqa: D102, D105, D107, EM101, PLR0913, PLR0917, TRY003

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import RLock
from typing import TYPE_CHECKING, Protocol

from research_agent.data_foundation._identity import stable_identity
from research_agent.protected_evaluation import (
    AuthorizedProtectedDataView,
    BacktestDenial,
    BacktestGovernance,
    BacktestRequest,
    EvaluationReport,
    Evaluator,
    FindingPublisher,
    LoadedProtectedCatalog,
    NegativeResult,
    NegativeResultRegistry,
    ProtectedResourceScope,
    ProtectedViewBinder,
    ValidatedFinding,
    ValidationDecision,
    ValidationStatus,
    Validator,
)

if TYPE_CHECKING:
    from research_agent.data_foundation import DataCatalogSnapshot
    from research_agent.investigation.engine import RuntimeInvestigationCoordinator
    from research_agent.investigation.protected import (
        AuthoredBacktestEngine,
        AuthoredProtectedPlan,
        AuthoredProtectedPlanRegistry,
    )
    from research_agent.protected_evaluation import (
        BacktestRun,
        FrozenPredictiveSystemIdentity,
        FrozenSystemRegistry,
        PermissionGrant,
        ProtectedContentManifest,
    )


class ValidationGrantLike(Protocol):
    """Minimum independently configured validation authority surface."""

    @property
    def authority_id(self) -> str: ...

    @property
    def authority_policy_ref(self) -> str: ...

    @property
    def environment_ref(self) -> str: ...


class AuthorityResolver(Protocol):
    """Resolve governance and validation grants outside researcher control."""

    def governance_for(
        self,
        *,
        requester_id: str,
        scope: ProtectedResourceScope,
    ) -> PermissionGrant: ...

    def validation_for(
        self,
        *,
        authority_policy_ref: str,
        environment_ref: str,
    ) -> ValidationGrantLike: ...


class ProtectedResourceRegistrationLike(Protocol):
    """Exact authority-issued scope-to-content registration surface."""

    @property
    def scope(self) -> ProtectedResourceScope: ...

    @property
    def resource_binding_ref(self) -> str: ...

    @property
    def content_manifest(self) -> ProtectedContentManifest: ...

    @property
    def catalog(self) -> DataCatalogSnapshot: ...


class ProtectedResourceResolver(Protocol):
    """Resolve one exact protected resource without a friendly/latest lookup."""

    def resolve(self, scope: ProtectedResourceScope) -> ProtectedResourceRegistrationLike: ...


class AuthoredResolutionStatus(Enum):
    """Truthful protected terminal state for one authored candidate."""

    FINDING = "finding"
    REJECTED = "rejected"
    DENIED = "denied"


@dataclass(frozen=True, slots=True)
class AuthoredProtectedResolution:
    """Exact independent evidence chain; no status is supplied by the researcher."""

    resolution_id: str
    status: AuthoredResolutionStatus
    candidate_id: str
    evidence_id: str
    frozen_system_id: str
    request_id: str
    permit_or_denial_id: str
    view_id: str | None
    run_id: str | None
    report_id: str | None
    validation_decision_id: str | None
    finding_id: str | None
    negative_result_id: str | None
    evidence_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        protected_chain = (
            self.view_id,
            self.run_id,
            self.report_id,
            self.validation_decision_id,
        )
        if self.status is AuthoredResolutionStatus.FINDING and (
            self.finding_id is None
            or self.negative_result_id is not None
            or any(value is None for value in protected_chain)
        ):
            raise ValueError("finding resolution requires one finding and no negative result")
        if self.status is AuthoredResolutionStatus.REJECTED and (
            self.negative_result_id is None
            or self.finding_id is not None
            or any(value is None for value in protected_chain)
        ):
            raise ValueError("rejected resolution requires one negative result and no finding")
        if self.status is AuthoredResolutionStatus.DENIED and any(
            value is not None
            for value in (
                self.view_id,
                self.run_id,
                self.report_id,
                self.validation_decision_id,
                self.finding_id,
                self.negative_result_id,
            )
        ):
            raise ValueError("governance denial cannot claim protected evidence")
        if not self.evidence_refs or not self.reason_codes:
            raise ValueError("protected resolution requires exact evidence and reason codes")
        if self.resolution_id != stable_identity(
            "authored-protected-resolution", _resolution_payload(self)
        ):
            raise ValueError("authored protected resolution identity does not match content")


class AuthoredProtectedResolutionConflictError(ValueError):
    """An idempotency key was reused for a different authored resolution request."""


class AuthoredProtectedResolutionService:
    """Compose issued authorities around an exact frozen authored candidate."""

    def __init__(
        self,
        *,
        investigations: RuntimeInvestigationCoordinator,
        frozen_systems: FrozenSystemRegistry,
        plans: AuthoredProtectedPlanRegistry,
        authorities: AuthorityResolver,
        protected_resources: ProtectedResourceResolver,
        governance: BacktestGovernance,
        views: ProtectedViewBinder,
        engine: AuthoredBacktestEngine,
        evaluator: Evaluator,
        validator: Validator,
        publisher: FindingPublisher,
        negatives: NegativeResultRegistry,
    ) -> None:
        self._investigations = investigations
        self._frozen_systems = frozen_systems
        self._plans = plans
        self._authorities = authorities
        self._protected_resources = protected_resources
        self._governance = governance
        self._views = views
        self._engine = engine
        self._evaluator = evaluator
        self._validator = validator
        self._publisher = publisher
        self._negatives = negatives
        self._outcomes: dict[str, tuple[str, AuthoredProtectedResolution]] = {}
        self._lock = RLock()

    def __copy__(self) -> AuthoredProtectedResolutionService:
        raise TypeError("authored protected resolution authority cannot be copied")

    def __deepcopy__(self, memo: dict[int, object]) -> AuthoredProtectedResolutionService:
        del memo
        raise TypeError("authored protected resolution authority cannot be copied")

    def resolve(
        self,
        *,
        candidate_id: str,
        evidence_id: str,
        frozen_system_id: str,
        requester_id: str,
        beneficiary_id: str,
        recipient_id: str,
        idempotency_key: str,
    ) -> AuthoredProtectedResolution:
        """Resolve an issued authored candidate into a finding, rejection, or safe denial."""
        registration, candidate, evidence = self._investigations.require_credible(
            candidate_id=candidate_id,
            evidence_id=evidence_id,
        )
        frozen = self._frozen_systems.get(frozen_system_id)
        if frozen is None:
            raise ValueError("authored resolution requires an exact issued frozen identity")
        self._frozen_systems.require_issued(frozen)
        if (
            frozen.system_id != candidate.candidate_id
            or frozen.development_evidence_refs != (evidence.evidence_id,)
            or frozen.environment_ref != candidate.manifest.environment_id
        ):
            raise ValueError("frozen identity differs from exact credible authored evidence")
        declaration = registration.request.protected_predeclaration
        if declaration is None:
            raise ValueError("authored resolution was not predeclared before development")
        plan = self._plans.resolve_predeclared(declaration)
        claim = plan.claim_for(candidate)
        semantic_digest = stable_identity(
            "authored-protected-resolution-request",
            {
                "candidate_id": candidate_id,
                "evidence_id": evidence_id,
                "frozen_system_id": frozen_system_id,
                "plan_id": plan.plan_id,
                "requester_id": requester_id,
                "beneficiary_id": beneficiary_id,
                "recipient_id": recipient_id,
                "idempotency_key": idempotency_key,
            },
        )
        with self._lock:
            replay = self._outcomes.get(idempotency_key)
            if replay is not None:
                if replay[0] != semantic_digest:
                    raise AuthoredProtectedResolutionConflictError(
                        "authored protected resolution key changed semantics"
                    )
                return replay[1]
            outcome = self._resolve_once(
                candidate_id,
                evidence_id,
                frozen,
                plan,
                claim.identity,
                requester_id,
                beneficiary_id,
                recipient_id,
                idempotency_key,
            )
            self._outcomes[idempotency_key] = (semantic_digest, outcome)
            return outcome

    def require_issued(self, resolution: AuthoredProtectedResolution) -> None:
        """Reject a self-hashed resolution absent from this exact service history."""
        with self._lock:
            if not any(outcome == resolution for _, outcome in self._outcomes.values()):
                raise ValueError("protected resolution was not issued by this authority")

    def _resolve_once(
        self,
        candidate_id: str,
        evidence_id: str,
        frozen: FrozenPredictiveSystemIdentity,
        plan: AuthoredProtectedPlan,
        claim_ref: str,
        requester_id: str,
        beneficiary_id: str,
        recipient_id: str,
        idempotency_key: str,
    ) -> AuthoredProtectedResolution:
        grant = self._authorities.governance_for(
            requester_id=requester_id,
            scope=plan.protected_scope,
        )
        request = BacktestRequest(
            frozen_system_id=frozen.frozen_system_id,
            system_id=candidate_id,
            scenario_ref=plan.scenario.identity,
            decision_times_ref=plan.scenario.decision_times_ref,
            training_protocol_ref=plan.scenario.training_protocol_ref,
            evaluation_spec_ref=plan.evaluation_spec.identity,
            validation_standard_ref=plan.promotion_standard.identity,
            claim_ref=claim_ref,
            protected_scope=plan.protected_scope,
            environment_ref=plan.scenario.environment_ref,
            ancestry_refs=frozen.ancestry_refs,
            prior_exposure_refs=(),
            requester_id=requester_id,
            beneficiary_id=beneficiary_id,
            idempotency_key=idempotency_key,
        )
        permit = self._governance.authorize(request, authority_id=grant.authority_id)
        if isinstance(permit, BacktestDenial):
            return _resolution(
                AuthoredResolutionStatus.DENIED,
                candidate_id,
                evidence_id,
                frozen.frozen_system_id,
                request.request_id,
                permit.denial_id,
                None,
                None,
                None,
                None,
                None,
                None,
                (permit.denial_id,),
                (permit.code.value,),
            )
        resource = self._protected_resources.resolve(plan.protected_scope)
        if resource.scope != plan.protected_scope:
            raise ValueError("protected resource resolver returned another scope")
        view = self._views.bind(
            permit=permit,
            request=request,
            requested_scope=plan.protected_scope,
            caller_id=requester_id,
            resolve_exact_resource=lambda _: resource.resource_binding_ref,
        )
        if not isinstance(view, AuthorizedProtectedDataView):
            return _resolution(
                AuthoredResolutionStatus.DENIED,
                candidate_id,
                evidence_id,
                frozen.frozen_system_id,
                request.request_id,
                view.denial_id,
                None,
                None,
                None,
                None,
                None,
                None,
                (view.denial_id,),
                (view.code.value,),
            )

        def load(binding_ref: str) -> LoadedProtectedCatalog:
            if binding_ref != resource.resource_binding_ref:
                raise ValueError("protected binding changed after permit issuance")
            return LoadedProtectedCatalog(resource.content_manifest, resource.catalog)

        run = self._engine.execute(
            request=request,
            permit=permit,
            view=view,
            frozen=frozen,
            plan=plan,
            recipient_id=recipient_id,
            load_protected_catalog=load,
        )
        report = self._evaluator.measure(run, plan.evaluation_spec)
        validation_grant = self._authorities.validation_for(
            authority_policy_ref=plan.promotion_standard.authority_policy_ref,
            environment_ref=plan.scenario.environment_ref,
        )
        if (
            validation_grant.authority_policy_ref != plan.promotion_standard.authority_policy_ref
            or validation_grant.environment_ref != plan.scenario.environment_ref
        ):
            raise ValueError("validation authority resolver returned another policy or environment")
        decision = self._validator.validate(
            report,
            plan.promotion_standard,
            authority_id=validation_grant.authority_id,
            requester_id=requester_id,
            beneficiary_id=beneficiary_id,
        )
        if decision.status is ValidationStatus.PROMOTE:
            finding = self._publisher.publish(
                decision,
                report,
                claim=plan.claim_for(self._investigations.resolve_candidate(candidate_id)),
            )
            return _finding_resolution(
                candidate_id, evidence_id, request, view, run, report, decision, finding
            )
        negative = _negative_for(self._negatives, decision)
        return _rejection_resolution(
            candidate_id, evidence_id, request, view, run, report, decision, negative
        )


def _negative_for(registry: NegativeResultRegistry, decision: ValidationDecision) -> NegativeResult:
    matches = tuple(item for item in registry.records() if item.subject_id == decision.decision_id)
    if len(matches) != 1:
        raise ValueError("validation rejection did not publish one exact negative result")
    return matches[0]


def _finding_resolution(
    candidate_id: str,
    evidence_id: str,
    request: BacktestRequest,
    view: AuthorizedProtectedDataView,
    run: BacktestRun,
    report: EvaluationReport,
    decision: ValidationDecision,
    finding: ValidatedFinding,
) -> AuthoredProtectedResolution:
    return _resolution(
        AuthoredResolutionStatus.FINDING,
        candidate_id,
        evidence_id,
        run.frozen_system_id,
        request.request_id,
        run.permit_id,
        view.view_id,
        run.run_id,
        report.report_id,
        decision.decision_id,
        finding.finding_id,
        None,
        (run.run_id, report.report_id, decision.decision_id, finding.finding_id),
        decision.reasons,
    )


def _rejection_resolution(
    candidate_id: str,
    evidence_id: str,
    request: BacktestRequest,
    view: AuthorizedProtectedDataView,
    run: BacktestRun,
    report: EvaluationReport,
    decision: ValidationDecision,
    negative: NegativeResult,
) -> AuthoredProtectedResolution:
    return _resolution(
        AuthoredResolutionStatus.REJECTED,
        candidate_id,
        evidence_id,
        run.frozen_system_id,
        request.request_id,
        run.permit_id,
        view.view_id,
        run.run_id,
        report.report_id,
        decision.decision_id,
        None,
        negative.negative_id,
        (run.run_id, report.report_id, decision.decision_id, negative.negative_id),
        decision.reasons,
    )


def _resolution(
    status: AuthoredResolutionStatus,
    candidate_id: str,
    evidence_id: str,
    frozen_system_id: str,
    request_id: str,
    permit_or_denial_id: str,
    view_id: str | None,
    run_id: str | None,
    report_id: str | None,
    validation_decision_id: str | None,
    finding_id: str | None,
    negative_result_id: str | None,
    evidence_refs: tuple[str, ...],
    reason_codes: tuple[str, ...],
) -> AuthoredProtectedResolution:
    payload = {
        "status": status,
        "candidate_id": candidate_id,
        "evidence_id": evidence_id,
        "frozen_system_id": frozen_system_id,
        "request_id": request_id,
        "permit_or_denial_id": permit_or_denial_id,
        "view_id": view_id,
        "run_id": run_id,
        "report_id": report_id,
        "validation_decision_id": validation_decision_id,
        "finding_id": finding_id,
        "negative_result_id": negative_result_id,
        "evidence_refs": evidence_refs,
        "reason_codes": reason_codes,
    }
    return AuthoredProtectedResolution(
        stable_identity("authored-protected-resolution", payload),
        status,
        candidate_id,
        evidence_id,
        frozen_system_id,
        request_id,
        permit_or_denial_id,
        view_id,
        run_id,
        report_id,
        validation_decision_id,
        finding_id,
        negative_result_id,
        evidence_refs,
        reason_codes,
    )


def _resolution_payload(resolution: AuthoredProtectedResolution) -> dict[str, object]:
    return {
        name: getattr(resolution, name)
        for name in resolution.__dataclass_fields__
        if name != "resolution_id"
    }


__all__ = [
    "AuthoredProtectedResolution",
    "AuthoredProtectedResolutionConflictError",
    "AuthoredProtectedResolutionService",
    "AuthoredResolutionStatus",
    "AuthorityResolver",
    "ProtectedResourceResolver",
]
