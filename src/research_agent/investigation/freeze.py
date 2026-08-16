"""Independent freeze assessment for exact credible authored candidates."""

# ruff: noqa: D107, EM101, SLF001, TRY003

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import TYPE_CHECKING

from research_agent.protected_evaluation import (
    DecisionStatus,
    FreezeDecision,
    FreezeEligibilityRegistration,
    FreezeEligibilityRegistry,
    FreezeEligibilityRequest,
    FreezeGate,
    FrozenPredictiveSystemIdentity,
)

if TYPE_CHECKING:
    from research_agent.investigation.engine import RuntimeInvestigationCoordinator


@dataclass(frozen=True, slots=True)
class AuthoredFreezeOutcome:
    """Exact independent decision and optional sealed authored-system identity."""

    request: FreezeEligibilityRequest
    decision: FreezeDecision
    frozen: FrozenPredictiveSystemIdentity | None


class AuthoredFreezeService:
    """Resolve coordinator evidence and issue no caller-selected freeze outcome."""

    def __init__(
        self,
        *,
        authority_id: str,
        investigations: RuntimeInvestigationCoordinator,
        eligibility: FreezeEligibilityRegistry,
        gate: FreezeGate,
    ) -> None:
        if not authority_id:
            raise ValueError("authored freeze authority must be explicit")
        self._authority_id = authority_id
        self._investigations = investigations
        self._eligibility = eligibility
        self._gate = gate
        self._outcomes: dict[str, AuthoredFreezeOutcome] = {}
        self._lock = RLock()

    def __copy__(self) -> AuthoredFreezeService:
        """Prevent a second object from sharing this service's issuance authority."""
        raise TypeError("authored freeze authority cannot be copied")

    def __deepcopy__(self, memo: dict[int, object]) -> AuthoredFreezeService:
        """Prevent deep-copy substitution of the configured authority boundary."""
        del memo
        raise TypeError("authored freeze authority cannot be copied")

    def assess_credible(
        self,
        *,
        candidate_id: str,
        evidence_id: str,
        requester_id: str,
        beneficiary_id: str,
    ) -> AuthoredFreezeOutcome:
        """Assess only the exact candidate/evidence pair issued as credible by development."""
        registration, candidate, evidence = self._investigations.require_credible(
            candidate_id=candidate_id,
            evidence_id=evidence_id,
        )
        request_scope = registration.request
        predeclared = request_scope.protected_predeclaration
        if predeclared is None:
            raise ValueError("protected evaluation was not predeclared before development")
        if (
            evidence.candidate_id != candidate.candidate_id
            or evidence.catalog_id != request_scope.catalog.identity
            or evidence.budget_id != request_scope.budget.identity
            or candidate.manifest.question_id != request_scope.question.question_id
            or candidate.manifest.environment_id != request_scope.catalog.environment_id
        ):
            raise ValueError("credible evidence differs from its exact registered investigation")
        if self._authority_id in {requester_id, beneficiary_id}:
            raise ValueError("freeze authority cannot be requester or beneficiary")
        ancestry = tuple(
            dict.fromkeys(
                (
                    request_scope.question.question_id,
                    evidence.trial_id,
                    *candidate.parent_trial_ids,
                )
            )
        )
        request = FreezeEligibilityRequest(
            system_id=candidate.candidate_id,
            candidate_version=candidate.source_sha256,
            ancestry_refs=ancestry,
            development_evidence_refs=(evidence.evidence_id,),
            protocol_refs=predeclared.protocol_refs,
            environment_ref=candidate.manifest.environment_id,
            standard_ref=predeclared.freeze_standard_ref,
            requester_id=requester_id,
            beneficiary_id=beneficiary_id,
        )
        with self._lock:
            prior = self._outcomes.get(request.request_id)
            if prior is not None:
                return prior
            issued = FreezeEligibilityRegistration._issue(  # pyright: ignore[reportPrivateUsage]
                request,
                authority_id=self._authority_id,
                status=DecisionStatus.ACCEPT,
                reason_code="PREDECLARED_DEVELOPMENT_RULE_MET",
            )
            self._eligibility._issue(issued)  # pyright: ignore[reportPrivateUsage]
            decision = self._gate.assess(request)
            frozen = (
                self._gate.seal(request, decision)
                if decision.status is DecisionStatus.ACCEPT
                else None
            )
            outcome = AuthoredFreezeOutcome(request, decision, frozen)
            self._outcomes[request.request_id] = outcome
            return outcome


__all__ = ["AuthoredFreezeOutcome", "AuthoredFreezeService"]
