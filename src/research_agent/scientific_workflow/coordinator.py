"""Authoritative exact-reference composition of the scientific workflow."""

# ruff: noqa: C901, D105, D107, EM101, PLR0911, PLR0912, PLR0913, PLR0915, PLR2004, TRY003

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import RLock
from typing import TYPE_CHECKING

from research_agent.data_foundation import BoundaryStatus, TrainingSampleBuilder
from research_agent.data_foundation._identity import require_aware, stable_identity
from research_agent.development import (
    DevelopmentEvaluator,
    DevelopmentEvidenceRegistry,
    TrainingBlocked,
    TrialLedger,
    TrialRecord,
)
from research_agent.protected_evaluation import (
    BacktestDenial,
    BacktestEngine,
    BacktestGovernance,
    BacktestRequest,
    BacktestRunRegistry,
    DecisionStatus,
    DenialCode,
    EvaluationReportRegistry,
    Evaluator,
    ExposureRecorder,
    ExposureRegistry,
    FindingPublisher,
    FreezeEligibilityRegistration,
    FreezeEligibilityRegistry,
    FreezeEligibilityRequest,
    FreezeGate,
    FrozenSystemRegistry,
    IdempotencyConflictError,
    LoadedProtectedCatalog,
    NegativeResultRegistry,
    PermissionGrant,
    PermitRegistry,
    PrivilegedOperationCoordinator,
    ProtectedContentManifest,
    ProtectedViewBinder,
    ResearchLedger,
    ValidatedFindingRegistry,
    ValidationDecisionRegistry,
    ValidationStatus,
    Validator,
)
from research_agent.reporting import CanonicalReportRegistry, ReportBuilder, ReportSpecification
from research_agent.runtime._canonical import content_digest

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from research_agent.data_foundation import DataCatalogSnapshot, MissingnessPolicy, SampleKey
    from research_agent.development import DevelopmentProtocol
    from research_agent.formalization import PredictiveSystemDefinition
    from research_agent.protected_evaluation import (
        ClaimDefinition,
        EvaluationScenario,
        EvaluationSpec,
        PromotionStandard,
        ProtectedResourceScope,
    )
    from research_agent.runtime.store import InMemoryRuntimeStore


class WorkflowRegistryError(ValueError):
    """A workflow or one of its exact scientific bindings is invalid or absent."""


class WorkflowStatus(Enum):
    """Truthful terminal status of one registered scientific workflow request."""

    FINDING = "finding"
    REJECTED = "rejected"
    DENIED = "denied"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ValidationAuthorityGrant:
    """Independent permission to apply one exact validation authority policy."""

    authority_id: str
    authority_policy_ref: str
    environment_ref: str

    def __post_init__(self) -> None:
        if not self.authority_id or not self.authority_policy_ref or not self.environment_ref:
            raise WorkflowRegistryError("Validation authority grants must be complete.")


class WorkflowAuthorityRegistry:
    """Immutable configured governance and validation capabilities."""

    def __init__(
        self,
        *,
        governance_permissions: tuple[PermissionGrant, ...],
        validation_grants: tuple[ValidationAuthorityGrant, ...],
    ) -> None:
        if not governance_permissions or not validation_grants:
            raise WorkflowRegistryError(
                "Workflow authority configuration requires governance and validation grants."
            )
        governance_keys = tuple(
            (
                grant.actor_id,
                grant.environment_ref,
                grant.policy_ref,
                tuple(sorted(grant.scope_ids)),
            )
            for grant in governance_permissions
        )
        validation_keys = tuple(
            (grant.environment_ref, grant.authority_policy_ref) for grant in validation_grants
        )
        if len(set(governance_keys)) != len(governance_keys) or len(set(validation_keys)) != len(
            validation_keys
        ):
            raise WorkflowRegistryError("Workflow authority configuration is ambiguous.")
        self._governance_permissions = governance_permissions
        self._validation_grants = validation_grants

    def governance_for(
        self,
        *,
        requester_id: str,
        scope: ProtectedResourceScope,
    ) -> PermissionGrant:
        """Resolve one independently configured exact protected-access grant."""
        matches = tuple(
            grant
            for grant in self._governance_permissions
            if grant.actor_id == requester_id
            and grant.environment_ref == scope.environment_ref
            and grant.policy_ref == scope.policy_ref
            and scope.scope_id in grant.scope_ids
        )
        if len(matches) != 1:
            raise WorkflowRegistryError(
                "No unique configured governance grant authorizes this workflow scope."
            )
        return matches[0]

    def validation_for(
        self,
        *,
        authority_policy_ref: str,
        environment_ref: str,
    ) -> ValidationAuthorityGrant:
        """Resolve one independently configured validator for an exact policy."""
        matches = tuple(
            grant
            for grant in self._validation_grants
            if grant.authority_policy_ref == authority_policy_ref
            and grant.environment_ref == environment_ref
        )
        if len(matches) != 1:
            raise WorkflowRegistryError(
                "No unique configured validation authority serves this workflow policy."
            )
        return matches[0]


@dataclass(frozen=True, slots=True)
class ProtectedResourceRegistration:
    """Authority-issued binding from one exact protected scope to one catalog."""

    registration_id: str
    scope: ProtectedResourceScope
    resource_binding_ref: str
    content_manifest: ProtectedContentManifest
    catalog: DataCatalogSnapshot
    authority_id: str

    def __post_init__(self) -> None:
        expected = stable_identity(
            "protected-resource-registration",
            {
                "scope_id": self.scope.scope_id,
                "resource_binding_ref": self.resource_binding_ref,
                "content_manifest_id": self.content_manifest.manifest_id,
                "catalog_id": self.catalog.identity,
                "authority_id": self.authority_id,
            },
        )
        if self.registration_id != expected:
            raise WorkflowRegistryError(
                "Protected-resource registration identity does not match exact content."
            )
        if (
            not self.resource_binding_ref
            or not self.authority_id
            or self.scope.content_manifest_id != self.content_manifest.manifest_id
            or self.scope.content_identity_id != self.content_manifest.content_identity_id
            or self.content_manifest.catalog_id != self.catalog.identity
            or self.catalog.environment_id != self.scope.environment_ref
        ):
            raise WorkflowRegistryError(
                "Protected-resource registration must bind an exact catalog and environment."
            )


class ProtectedResourceRegistry:
    """Authority-owned exact protected scope, binding, and catalog registry."""

    def __init__(
        self,
        *,
        issuing_authority_id: str,
        issuance_capability: object,
    ) -> None:
        if not issuing_authority_id:
            raise WorkflowRegistryError(
                "Protected-resource registry requires an issuing authority."
            )
        self._issuing_authority_id = issuing_authority_id
        self._issuance_capability = issuance_capability
        self._lock = RLock()
        self._registrations: dict[str, ProtectedResourceRegistration] = {}
        self._period_by_content_identity: dict[str, str] = {}
        self._period_by_resource_slice: dict[tuple[str, str, str, str], str] = {}

    def _issue(
        self,
        registration: ProtectedResourceRegistration,
        *,
        authority_id: str,
        issuance_capability: object,
    ) -> ProtectedResourceRegistration:
        """Publish only through the configured protected-resource authority."""
        if (
            issuance_capability is not self._issuance_capability
            or authority_id != self._issuing_authority_id
            or registration.authority_id != authority_id
        ):
            raise WorkflowRegistryError(
                "Protected-resource registration was not issued by the configured authority."
            )
        with self._lock:
            prior = self._registrations.get(registration.scope.scope_id)
            if prior is not None and prior != registration:
                raise WorkflowRegistryError(
                    "Protected scope already has a different authoritative binding or catalog."
                )
            content_period = self._period_by_content_identity.get(
                registration.content_manifest.content_identity_id
            )
            if (
                content_period is not None
                and content_period != registration.scope.exposure_period_id
            ):
                raise WorkflowRegistryError(
                    "Identical protected content cannot be assigned a fresh epistemic period."
                )
            resource_period_key = (
                registration.scope.resource_id,
                registration.scope.slice_id,
                registration.scope.environment_ref,
                registration.scope.policy_ref,
            )
            resource_period = self._period_by_resource_slice.get(resource_period_key)
            if (
                resource_period is not None
                and resource_period != registration.scope.exposure_period_id
            ):
                raise WorkflowRegistryError(
                    "A resource revision cannot be assigned a fresh epistemic period."
                )
            self._registrations[registration.scope.scope_id] = registration
            self._period_by_content_identity[registration.content_manifest.content_identity_id] = (
                registration.scope.exposure_period_id
            )
            self._period_by_resource_slice[resource_period_key] = (
                registration.scope.exposure_period_id
            )
            return registration

    def resolve(self, scope: ProtectedResourceScope) -> ProtectedResourceRegistration:
        """Resolve one exact issued protected resource without latest fallback."""
        with self._lock:
            registration = self._registrations.get(scope.scope_id)
            if registration is None or registration.scope != scope:
                raise WorkflowRegistryError("The exact protected resource is not registered.")
            return registration


class ProtectedResourceIssuer:
    """Configured capability for publishing exact protected-resource bindings."""

    def __init__(
        self,
        *,
        authority_id: str,
        registry: ProtectedResourceRegistry,
        issuance_capability: object,
    ) -> None:
        if not authority_id:
            raise WorkflowRegistryError("Protected-resource issuer requires an authority identity.")
        self._authority_id = authority_id
        self._registry = registry
        self._issuance_capability = issuance_capability

    def issue(
        self,
        *,
        scope: ProtectedResourceScope,
        resource_binding_ref: str,
        content_manifest: ProtectedContentManifest,
        catalog: DataCatalogSnapshot,
    ) -> ProtectedResourceRegistration:
        """Create and publish one exact scope-to-catalog authority record."""
        registration = ProtectedResourceRegistration(
            registration_id=stable_identity(
                "protected-resource-registration",
                {
                    "scope_id": scope.scope_id,
                    "resource_binding_ref": resource_binding_ref,
                    "content_manifest_id": content_manifest.manifest_id,
                    "catalog_id": catalog.identity,
                    "authority_id": self._authority_id,
                },
            ),
            scope=scope,
            resource_binding_ref=resource_binding_ref,
            content_manifest=content_manifest,
            catalog=catalog,
            authority_id=self._authority_id,
        )
        return self._registry._issue(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            registration,
            authority_id=self._authority_id,
            issuance_capability=self._issuance_capability,
        )


def configure_protected_resource_authority(
    authority_id: str,
) -> tuple[ProtectedResourceRegistry, ProtectedResourceIssuer]:
    """Create one registry and its non-reconstructible issuance capability."""
    capability = object()
    registry = ProtectedResourceRegistry(
        issuing_authority_id=authority_id,
        issuance_capability=capability,
    )
    return registry, ProtectedResourceIssuer(
        authority_id=authority_id,
        registry=registry,
        issuance_capability=capability,
    )


@dataclass(frozen=True, slots=True)
class RegisteredScientificWorkflow:
    """One exact task/session/environment-scoped, non-authoritative experiment graph."""

    task_id: str
    task_version: int
    task_semantic_digest: str
    session_id: str
    episode_id: str
    environment_ref: str
    environment_content_digest: str
    development_catalog: DataCatalogSnapshot
    system: PredictiveSystemDefinition
    development_protocol: DevelopmentProtocol
    development_candidate_keys: tuple[SampleKey, ...]
    development_current_time: datetime
    development_missingness_policy: MissingnessPolicy
    scenario: EvaluationScenario
    evaluation_spec: EvaluationSpec
    promotion_standard: PromotionStandard
    claim: ClaimDefinition
    protected_scope: ProtectedResourceScope
    requester_id: str
    beneficiary_id: str
    protected_recipient_id: str
    freeze_eligibility_registration: FreezeEligibilityRegistration

    def __post_init__(self) -> None:
        """Reject a graph whose exact identities do not compose."""
        require_aware(self.development_current_time, "development_current_time")
        text_values = (
            self.task_id,
            self.task_semantic_digest,
            self.session_id,
            self.episode_id,
            self.environment_ref,
            self.environment_content_digest,
            self.requester_id,
            self.beneficiary_id,
            self.protected_recipient_id,
            self.freeze_authority_id,
        )
        if self.task_version < 1 or not all(text_values):
            raise WorkflowRegistryError("Workflow identity and requester fields are required.")
        if not self.development_candidate_keys or len(set(self.development_candidate_keys)) != len(
            self.development_candidate_keys
        ):
            raise WorkflowRegistryError("Development sample keys must be explicit and unique.")
        environments = {
            self.development_catalog.environment_id,
            self.system.environment_id,
            self.development_protocol.environment_id,
            self.scenario.environment_ref,
            self.protected_scope.environment_ref,
        }
        if environments != {self.environment_ref}:
            raise WorkflowRegistryError("Every scientific object must bind the exact environment.")
        if self.system.target.task_id != self.task_id:
            raise WorkflowRegistryError("The formal target belongs to another confirmed task.")
        if self.system.evaluation_protocol_id != self.development_protocol.identity:
            raise WorkflowRegistryError("System and development protocol identities differ.")
        if self.scenario.training_protocol_ref != self.system.training_protocol_id:
            raise WorkflowRegistryError("Scenario and system training protocol identities differ.")
        if self.evaluation_spec.protocol_ref != self.system.evaluation_protocol_id:
            raise WorkflowRegistryError("EvaluationSpec does not bind the system protocol.")
        if self.promotion_standard.evaluation_spec_id != self.evaluation_spec.identity:
            raise WorkflowRegistryError("PromotionStandard belongs to another EvaluationSpec.")
        if (
            self.claim.system_id != self.system.identity
            or self.claim.target_id != self.system.target.identity
        ):
            raise WorkflowRegistryError("Claim does not bind the exact system and target.")
        if self.promotion_standard.authority_policy_ref == "":
            raise WorkflowRegistryError("Workflow authority policies must be explicit and exact.")
        if self.development_current_time >= self.scenario.decision_sample_keys[0].decision_time:
            raise WorkflowRegistryError(
                "Development must close before the first protected decision boundary."
            )
        registration = self.freeze_eligibility_registration
        if len(registration.request.development_evidence_refs) != 1 or (
            registration.request
            != self.freeze_request(registration.request.development_evidence_refs[0])
        ):
            raise WorkflowRegistryError(
                "Freeze eligibility does not bind this exact workflow and development evidence."
            )
        dependencies = tuple(
            dict.fromkeys(
                dependency
                for feature in self.system.feature_set.members
                for dependency in feature.dependencies
            )
        )
        self.development_catalog.resolve_schema(self.system.target.field_ref)
        for dependency in dependencies:
            self.development_catalog.resolve_schema(dependency)

    @property
    def freeze_authority_id(self) -> str:
        """Return the independently issued freeze authority identity."""
        return self.freeze_eligibility_registration.authority_id

    def freeze_request(self, development_evidence_ref: str) -> FreezeEligibilityRequest:
        """Compose the exact evaluator-bound request without choosing its outcome."""
        protocol_refs = tuple(
            dict.fromkeys(
                (
                    self.system.data_protocol_id,
                    self.system.training_protocol_id,
                    self.system.evaluation_protocol_id,
                    self.evaluation_spec.identity,
                    self.promotion_standard.identity,
                )
            )
        )
        return FreezeEligibilityRequest(
            system_id=self.system.identity,
            candidate_version=str(self.system.version),
            ancestry_refs=self.system.candidate_ancestry,
            development_evidence_refs=(development_evidence_ref,),
            protocol_refs=protocol_refs,
            environment_ref=self.environment_ref,
            standard_ref=self.promotion_standard.identity,
            requester_id=self.requester_id,
            beneficiary_id=self.beneficiary_id,
        )

    @property
    def workflow_id(self) -> str:
        """Return the exact identity of every non-authoritative scientific input."""
        return stable_identity(
            "registered-scientific-workflow",
            {
                "task_id": self.task_id,
                "task_version": self.task_version,
                "task_semantic_digest": self.task_semantic_digest,
                "session_id": self.session_id,
                "episode_id": self.episode_id,
                "environment_ref": self.environment_ref,
                "environment_content_digest": self.environment_content_digest,
                "development_catalog_id": self.development_catalog.identity,
                "system_id": self.system.identity,
                "development_protocol_id": self.development_protocol.identity,
                "development_candidate_keys": self.development_candidate_keys,
                "development_current_time": self.development_current_time,
                "development_missingness_policy": self.development_missingness_policy,
                "scenario_id": self.scenario.identity,
                "evaluation_spec_id": self.evaluation_spec.identity,
                "promotion_standard_id": self.promotion_standard.identity,
                "claim_id": self.claim.identity,
                "protected_scope_id": self.protected_scope.scope_id,
                "requester_id": self.requester_id,
                "beneficiary_id": self.beneficiary_id,
                "protected_recipient_id": self.protected_recipient_id,
                "freeze_eligibility_registration_id": (
                    self.freeze_eligibility_registration.registration_id
                ),
            },
        )


@dataclass(frozen=True, slots=True)
class ScientificWorkflowIssuance:
    """Authority-owned execution binding for one immutable workflow definition."""

    issuance_id: str
    workflow: RegisteredScientificWorkflow
    workflow_authority_id: str
    governance_permission: PermissionGrant
    validation_grant: ValidationAuthorityGrant
    protected_resource: ProtectedResourceRegistration

    def __post_init__(self) -> None:
        expected = stable_identity(
            "scientific-workflow-issuance",
            _workflow_issuance_payload(
                self.workflow,
                workflow_authority_id=self.workflow_authority_id,
                governance_permission=self.governance_permission,
                validation_grant=self.validation_grant,
                protected_resource=self.protected_resource,
            ),
        )
        if self.issuance_id != expected:
            raise WorkflowRegistryError("Scientific-workflow issuance identity is invalid.")


class WorkflowRegistry:
    """Authority-owned exact workflow registry with no public mutation API."""

    def __init__(
        self,
        *,
        freeze_eligibility: FreezeEligibilityRegistry,
        authorities: WorkflowAuthorityRegistry,
        protected_resources: ProtectedResourceRegistry,
        issuing_authority_id: str,
        issuance_capability: object,
    ) -> None:
        if not issuing_authority_id:
            raise WorkflowRegistryError("Workflow registry requires an issuing authority.")
        self.freeze_eligibility = freeze_eligibility
        self._authorities = authorities
        self._protected_resources = protected_resources
        self._issuing_authority_id = issuing_authority_id
        self._issuance_capability = issuance_capability
        self._lock = RLock()
        self._issuances: dict[str, ScientificWorkflowIssuance] = {}

    def _issue(
        self,
        workflow: RegisteredScientificWorkflow,
        *,
        authority_id: str,
        issuance_capability: object,
    ) -> ScientificWorkflowIssuance:
        """Publish only through the configured workflow authority capability."""
        if (
            issuance_capability is not self._issuance_capability
            or authority_id != self._issuing_authority_id
        ):
            raise WorkflowRegistryError(
                "Scientific workflow was not issued by the configured workflow authority."
            )
        workflow_id = workflow.workflow_id
        self.freeze_eligibility.require_issued(workflow.freeze_eligibility_registration)
        governance_permission = self._authorities.governance_for(
            requester_id=workflow.requester_id,
            scope=workflow.protected_scope,
        )
        validation_grant = self._authorities.validation_for(
            authority_policy_ref=workflow.promotion_standard.authority_policy_ref,
            environment_ref=workflow.environment_ref,
        )
        protected_resource = self._protected_resources.resolve(workflow.protected_scope)
        configured_authorities = {
            workflow.freeze_authority_id,
            governance_permission.authority_id,
            validation_grant.authority_id,
        }
        if len(configured_authorities) != 3 or configured_authorities.intersection(
            {workflow.requester_id, workflow.beneficiary_id}
        ):
            raise WorkflowRegistryError(
                "Freeze, governance, and validation require distinct independent authorities."
            )
        if authority_id in {workflow.requester_id, workflow.beneficiary_id}:
            raise WorkflowRegistryError("Workflow beneficiary cannot issue its own workflow.")
        if protected_resource.authority_id in {
            workflow.requester_id,
            workflow.beneficiary_id,
        }:
            raise WorkflowRegistryError(
                "Workflow beneficiary cannot issue its own protected-resource binding."
            )
        if workflow.development_catalog.identity == protected_resource.catalog.identity:
            raise WorkflowRegistryError(
                "Development and protected catalogs must be distinct registered snapshots."
            )
        dependencies = tuple(
            dict.fromkeys(
                dependency
                for feature in workflow.system.feature_set.members
                for dependency in feature.dependencies
            )
        )
        protected_resource.catalog.resolve_schema(workflow.system.target.field_ref)
        for dependency in dependencies:
            protected_resource.catalog.resolve_schema(dependency)
        issuance_payload = _workflow_issuance_payload(
            workflow,
            workflow_authority_id=authority_id,
            governance_permission=governance_permission,
            validation_grant=validation_grant,
            protected_resource=protected_resource,
        )
        issuance = ScientificWorkflowIssuance(
            issuance_id=stable_identity("scientific-workflow-issuance", issuance_payload),
            workflow=workflow,
            workflow_authority_id=authority_id,
            governance_permission=governance_permission,
            validation_grant=validation_grant,
            protected_resource=protected_resource,
        )
        with self._lock:
            prior = self._issuances.get(workflow_id)
            if prior is not None and prior != issuance:
                raise WorkflowRegistryError("Workflow identity was reused with changed authority.")
            self._issuances[workflow_id] = issuance
            return issuance

    def resolve(self, workflow_id: str) -> ScientificWorkflowIssuance:
        """Resolve an exact authority-issued workflow execution binding."""
        with self._lock:
            issuance = self._issuances.get(workflow_id)
            if issuance is None:
                raise WorkflowRegistryError("The exact issued workflow was not found.")
            if issuance.workflow.workflow_id != workflow_id:
                raise WorkflowRegistryError("Issued workflow content no longer matches identity.")
            return issuance

    def get(self, workflow_id: str) -> RegisteredScientificWorkflow:
        """Resolve one exact identity; no latest-version fallback exists."""
        return self.resolve(workflow_id).workflow


class ScientificWorkflowIssuer:
    """Configured capability for admitting exact workflows to runtime execution."""

    def __init__(
        self,
        *,
        authority_id: str,
        registry: WorkflowRegistry,
        issuance_capability: object,
    ) -> None:
        if not authority_id:
            raise WorkflowRegistryError(
                "Scientific-workflow issuer requires an authority identity."
            )
        self._authority_id = authority_id
        self._registry = registry
        self._issuance_capability = issuance_capability

    def issue(self, workflow: RegisteredScientificWorkflow) -> str:
        """Resolve every independent input and publish one exact issuance."""
        return self._registry._issue(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            workflow,
            authority_id=self._authority_id,
            issuance_capability=self._issuance_capability,
        ).workflow.workflow_id


def configure_scientific_workflow_authority(
    *,
    authority_id: str,
    freeze_eligibility: FreezeEligibilityRegistry,
    authorities: WorkflowAuthorityRegistry,
    protected_resources: ProtectedResourceRegistry,
) -> tuple[WorkflowRegistry, ScientificWorkflowIssuer]:
    """Create one workflow registry and its non-reconstructible issuance capability."""
    capability = object()
    registry = WorkflowRegistry(
        freeze_eligibility=freeze_eligibility,
        authorities=authorities,
        protected_resources=protected_resources,
        issuing_authority_id=authority_id,
        issuance_capability=capability,
    )
    return registry, ScientificWorkflowIssuer(
        authority_id=authority_id,
        registry=registry,
        issuance_capability=capability,
    )


@dataclass(frozen=True, slots=True)
class WorkflowReceipt:
    """Immutable provisional result spanning exact scientific and governance evidence."""

    receipt_id: str
    workflow_id: str
    session_id: str
    episode_id: str
    idempotency_key: str
    status: WorkflowStatus
    development_evidence_ref: str | None
    frozen_system_ref: str | None
    permit_ref: str | None
    view_ref: str | None
    exposure_ref: str | None
    run_ref: str | None
    evaluation_report_ref: str | None
    validation_decision_ref: str | None
    finding_ref: str | None
    negative_result_ref: str | None
    rendered_report_ref: str | None
    evidence_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    completed_at: datetime

    def __post_init__(self) -> None:
        expected = stable_identity("workflow-receipt", _without_first_field(self))
        if self.receipt_id != expected:
            raise ValueError("Workflow receipt identity does not match exact content.")
        if self.status is WorkflowStatus.FINDING and self.finding_ref is None:
            raise ValueError("A finding receipt requires an exact ValidatedFinding reference.")
        if self.status is WorkflowStatus.REJECTED and self.negative_result_ref is None:
            raise ValueError("A rejection receipt requires retained negative evidence.")
        if self.status is not WorkflowStatus.FINDING and self.rendered_report_ref is not None:
            raise ValueError("Only a validated finding may carry a rendered report reference.")


class ScientificWorkflowCoordinator:
    """Execute only registered workflows through existing scientific authorities."""

    def __init__(
        self,
        *,
        registry: WorkflowRegistry,
        runtime_store: InMemoryRuntimeStore,
        clock: Callable[[], datetime],
        ledger: ResearchLedger | None = None,
    ) -> None:
        self._registry = registry
        self._runtime_store = runtime_store
        self._clock = clock
        self.ledger = ledger or ResearchLedger()
        self.exposures = ExposureRegistry()
        self.negatives = NegativeResultRegistry()
        self._development_trials: dict[str, TrialLedger] = {}
        self._development_evidence = DevelopmentEvidenceRegistry()
        self._frozen = FrozenSystemRegistry()
        self._permits = PermitRegistry()
        self._operations = PrivilegedOperationCoordinator()
        self.runs = BacktestRunRegistry()
        self.evaluation_reports = EvaluationReportRegistry()
        self.validation_decisions = ValidationDecisionRegistry()
        self.findings = ValidatedFindingRegistry()
        self._canonical_reports = CanonicalReportRegistry(ledger=self.ledger)
        self._report_builder = ReportBuilder(source=self._canonical_reports)
        self._report_specification = ReportSpecification.create()
        self._evidence: dict[str, object] = {}

    def development_trial_records(self, workflow_id: str) -> tuple[TrialRecord, ...]:
        """Return exact retained trial history for one registered workflow."""
        ledger = self._development_trials.get(workflow_id)
        return () if ledger is None else ledger.records

    def evidence(self, evidence_ref: str) -> object:
        """Resolve one exact emitted object without a latest or friendly-name lookup."""
        evidence = self._evidence.get(evidence_ref)
        if evidence is None:
            raise KeyError(evidence_ref)
        return evidence

    def execute(
        self,
        *,
        workflow_id: str,
        idempotency_key: str,
        session_id: str,
        episode_id: str,
    ) -> WorkflowReceipt:
        """Resolve authoritative runtime state and execute one exact registered graph once."""
        issuance = self._authorize(workflow_id, session_id, episode_id)
        workflow = issuance.workflow
        payload = (
            ("workflow_id", workflow_id),
            ("issuance_id", issuance.issuance_id),
            ("task_id", workflow.task_id),
            ("task_version", str(workflow.task_version)),
            ("session_id", session_id),
            ("episode_id", episode_id),
            ("environment_ref", workflow.environment_ref),
        )
        return self._operations.execute(
            operation_key=f"scientific-workflow:{session_id}:{idempotency_key}",
            semantic_payload=payload,
            effect=lambda: self._execute_once(issuance, idempotency_key),
        ).result

    def authorize(
        self,
        *,
        workflow_id: str,
        session_id: str,
        episode_id: str,
    ) -> str:
        """Verify exact current authority without executing or disclosing workflow evidence."""
        return self._authorize(workflow_id, session_id, episode_id).workflow.workflow_id

    def _authorize(
        self,
        workflow_id: str,
        session_id: str,
        episode_id: str,
    ) -> ScientificWorkflowIssuance:
        issuance = self._registry.resolve(workflow_id)
        workflow = issuance.workflow
        task, environment, session, _, episode = self._runtime_store.coherent_view(session_id)
        runtime_binding = (
            task.task_id,
            task.version,
            session.session_id,
            episode.episode_id,
            environment.snapshot_ref,
        )
        expected_binding = (
            workflow.task_id,
            workflow.task_version,
            workflow.session_id,
            workflow.episode_id,
            workflow.environment_ref,
        )
        if runtime_binding != expected_binding or episode_id != episode.episode_id:
            raise WorkflowRegistryError(
                "Workflow does not bind the current task, session, episode, and environment."
            )
        if (
            workflow.task_semantic_digest != task.semantic_digest
            or workflow.environment_content_digest != content_digest(environment)
        ):
            raise WorkflowRegistryError(
                "Workflow task or environment content differs from its registered authority."
            )
        if task.target_field_id != workflow.system.target.field_ref.field_id:
            raise WorkflowRegistryError(
                "Confirmed task and registered target field identities differ."
            )
        dataset_ids = {
            workflow.system.target.field_ref.dataset_id,
            *(
                dependency.dataset_id
                for feature in workflow.system.feature_set.members
                for dependency in feature.dependencies
            ),
        }
        if not dataset_ids.issubset(set(task.dataset_refs)):
            raise WorkflowRegistryError("Registered scientific data exceeds the confirmed task.")
        if workflow.protected_scope.resource_id not in environment.protected_resource_refs:
            raise WorkflowRegistryError(
                "Registered protected scope is not authorized by the session environment."
            )
        return issuance

    def _execute_once(
        self,
        issuance: ScientificWorkflowIssuance,
        idempotency_key: str,
    ) -> WorkflowReceipt:
        workflow = issuance.workflow
        prior_exposure_refs = self.exposures.references_for(
            exposure_period_id=workflow.protected_scope.exposure_period_id,
            lineage_refs=frozenset((workflow.system.identity, *workflow.system.candidate_ancestry)),
        )
        if prior_exposure_refs:
            return self._receipt(
                workflow,
                idempotency_key,
                WorkflowStatus.DENIED,
                exposure_ref=prior_exposure_refs[-1],
                evidence_refs=prior_exposure_refs,
                reason_codes=(DenialCode.PRIOR_EXPOSURE.value,),
            )
        dependencies = tuple(
            dict.fromkeys(
                dependency
                for feature in workflow.system.feature_set.members
                for dependency in feature.dependencies
            )
        )
        sample = TrainingSampleBuilder().build(
            workflow.development_catalog,
            target=workflow.system.target,
            predictor_fields=dependencies,
            candidate_sample_keys=workflow.development_candidate_keys,
            current_time=workflow.development_current_time,
            missingness_policy=workflow.development_missingness_policy,
        )
        self._record_evidence(sample.sample_id, sample)
        if sample.status is not BoundaryStatus.READY:
            return self._receipt(
                workflow,
                idempotency_key,
                WorkflowStatus.FAILED,
                evidence_refs=(sample.sample_id,),
                reason_codes=("DEVELOPMENT_SAMPLE_NOT_READY",),
            )
        try:
            development_trials = self._development_trials.setdefault(
                workflow.workflow_id, TrialLedger()
            )
            development = DevelopmentEvaluator(
                ledger=development_trials,
                evidence_registry=self._development_evidence,
            ).evaluate(
                workflow.system,
                sample,
                workflow.development_protocol,
                protected_evaluation_spec_ref=workflow.evaluation_spec.identity,
                validation_standard_ref=workflow.promotion_standard.identity,
                catalog=workflow.development_catalog,
            )
        except TrainingBlocked as error:
            return self._receipt(
                workflow,
                idempotency_key,
                WorkflowStatus.FAILED,
                evidence_refs=(sample.sample_id, error.failure.failure_id),
                reason_codes=(error.failure.code.value,),
            )
        self._record_evidence(development.evidence_id, development)
        freeze_request = workflow.freeze_request(development.evidence_id)
        freeze_gate = FreezeGate(
            ledger=self.ledger,
            registry=self._frozen,
            eligibility=self._registry.freeze_eligibility,
            decision_authority_id=workflow.freeze_authority_id,
            clock=self._clock,
        )
        freeze_decision = freeze_gate.assess(freeze_request)
        self._record_evidence(freeze_decision.decision_id, freeze_decision)
        if freeze_decision.status is not DecisionStatus.ACCEPT:
            return self._receipt(
                workflow,
                idempotency_key,
                WorkflowStatus.DENIED,
                development_evidence_ref=development.evidence_id,
                evidence_refs=(development.evidence_id, freeze_decision.decision_id),
                reason_codes=(freeze_decision.reason_code,),
            )
        frozen = freeze_gate.seal(freeze_request, freeze_decision)
        self._record_evidence(frozen.frozen_system_id, frozen)
        request = BacktestRequest(
            frozen_system_id=frozen.frozen_system_id,
            system_id=workflow.system.identity,
            scenario_ref=workflow.scenario.identity,
            decision_times_ref=workflow.scenario.decision_times_ref,
            training_protocol_ref=workflow.system.training_protocol_id,
            evaluation_spec_ref=workflow.evaluation_spec.identity,
            validation_standard_ref=workflow.promotion_standard.identity,
            claim_ref=workflow.claim.identity,
            protected_scope=workflow.protected_scope,
            environment_ref=workflow.environment_ref,
            ancestry_refs=frozen.ancestry_refs,
            prior_exposure_refs=self.exposures.references_for(
                exposure_period_id=workflow.protected_scope.exposure_period_id,
                lineage_refs=frozenset((workflow.system.identity, *frozen.ancestry_refs)),
            ),
            requester_id=workflow.requester_id,
            beneficiary_id=workflow.beneficiary_id,
            idempotency_key=f"{workflow.workflow_id}:{idempotency_key}",
        )
        governance = BacktestGovernance(
            ledger=self.ledger,
            frozen_systems=self._frozen,
            exposures=self.exposures,
            permits=self._permits,
            permissions=(issuance.governance_permission,),
            current_environment_ref=workflow.environment_ref,
            current_policy_ref=workflow.protected_scope.policy_ref,
            clock=self._clock,
            operations=self._operations,
        )
        permit = governance.authorize(
            request,
            authority_id=issuance.governance_permission.authority_id,
        )
        if isinstance(permit, BacktestDenial):
            self._record_evidence(permit.denial_id, permit)
            return self._receipt(
                workflow,
                idempotency_key,
                WorkflowStatus.DENIED,
                development_evidence_ref=development.evidence_id,
                frozen_system_ref=frozen.frozen_system_id,
                evidence_refs=(
                    development.evidence_id,
                    freeze_decision.decision_id,
                    frozen.frozen_system_id,
                    permit.denial_id,
                ),
                reason_codes=(permit.code.value,),
            )
        self._record_evidence(permit.permit_id, permit)
        binder = ProtectedViewBinder(
            permits=self._permits,
            clock=self._clock,
            current_environment_ref=workflow.environment_ref,
            current_policy_ref=workflow.protected_scope.policy_ref,
        )
        view = binder.bind(
            permit=permit,
            request=request,
            requested_scope=workflow.protected_scope,
            caller_id=workflow.requester_id,
            resolve_exact_resource=lambda scope: self._resolve_protected_binding(issuance, scope),
        )
        if isinstance(view, BacktestDenial):
            self._record_evidence(view.denial_id, view)
            return self._receipt(
                workflow,
                idempotency_key,
                WorkflowStatus.DENIED,
                development_evidence_ref=development.evidence_id,
                frozen_system_ref=frozen.frozen_system_id,
                permit_ref=permit.permit_id,
                evidence_refs=(development.evidence_id, permit.permit_id, view.denial_id),
                reason_codes=(view.code.value,),
            )
        self._record_evidence(view.view_id, view)
        engine = BacktestEngine(
            permits=self._permits,
            frozen_systems=self._frozen,
            views=binder,
            exposures=ExposureRecorder(
                registry=self.exposures,
                ledger=self.ledger,
                clock=self._clock,
            ),
            ledger=self.ledger,
            clock=self._clock,
            runs=self.runs,
            operations=self._operations,
        )
        run = engine.execute(
            request=request,
            permit=permit,
            view=view,
            frozen=frozen,
            definition=workflow.system,
            scenario=workflow.scenario,
            recipient_id=workflow.protected_recipient_id,
            load_protected_catalog=lambda binding: self._load_protected_catalog(issuance, binding),
        )
        self._record_evidence(run.run_id, run)
        if run.exposure_id is not None:
            exposure = next(
                item for item in self.exposures.records() if item.exposure_id == run.exposure_id
            )
            self._record_evidence(exposure.exposure_id, exposure)
        evaluator = Evaluator(
            ledger=self.ledger,
            runs=engine.issued_runs,
            clock=self._clock,
            reports=self.evaluation_reports,
            operations=self._operations,
        )
        report = evaluator.measure(
            run,
            workflow.evaluation_spec,
        )
        self._record_evidence(report.report_id, report)
        validator = Validator(
            authorized_authority_ids=frozenset({issuance.validation_grant.authority_id}),
            authority_policy_ref=issuance.validation_grant.authority_policy_ref,
            ledger=self.ledger,
            reports=evaluator.issued_reports,
            negatives=self.negatives,
            clock=self._clock,
            decisions=self.validation_decisions,
            operations=self._operations,
        )
        decision = validator.validate(
            report,
            workflow.promotion_standard,
            authority_id=issuance.validation_grant.authority_id,
            requester_id=workflow.requester_id,
            beneficiary_id=workflow.beneficiary_id,
        )
        self._record_evidence(decision.decision_id, decision)
        exposure_ref = run.exposure_id
        common_refs = (
            development.evidence_id,
            freeze_decision.decision_id,
            frozen.frozen_system_id,
            permit.permit_id,
            view.view_id,
            *(item for item in (exposure_ref,) if item is not None),
            run.run_id,
            report.report_id,
            decision.decision_id,
        )
        if decision.status is ValidationStatus.REJECT:
            negative = next(
                item for item in self.negatives.records() if item.subject_id == decision.decision_id
            )
            self._record_evidence(negative.negative_id, negative)
            return self._receipt(
                workflow,
                idempotency_key,
                WorkflowStatus.REJECTED,
                development_evidence_ref=development.evidence_id,
                frozen_system_ref=frozen.frozen_system_id,
                permit_ref=permit.permit_id,
                view_ref=view.view_id,
                exposure_ref=exposure_ref,
                run_ref=run.run_id,
                evaluation_report_ref=report.report_id,
                validation_decision_ref=decision.decision_id,
                negative_result_ref=negative.negative_id,
                evidence_refs=(*common_refs, negative.negative_id),
                reason_codes=decision.reasons,
            )
        publisher = FindingPublisher(
            ledger=self.ledger,
            reports=evaluator.issued_reports,
            decisions=validator.issued_decisions,
            clock=self._clock,
            findings=self.findings,
            operations=self._operations,
        )
        finding = publisher.publish(
            decision,
            report,
            claim=workflow.claim,
        )
        publisher.issued_findings.require_issued(finding)
        self._record_evidence(finding.finding_id, finding)
        self._canonical_reports.register(finding=finding, report=report, decision=decision)
        rendered = self._report_builder.render(finding, self._report_specification)
        self._record_evidence(rendered.rendered_report_id, rendered)
        return self._receipt(
            workflow,
            idempotency_key,
            WorkflowStatus.FINDING,
            development_evidence_ref=development.evidence_id,
            frozen_system_ref=frozen.frozen_system_id,
            permit_ref=permit.permit_id,
            view_ref=view.view_id,
            exposure_ref=exposure_ref,
            run_ref=run.run_id,
            evaluation_report_ref=report.report_id,
            validation_decision_ref=decision.decision_id,
            finding_ref=finding.finding_id,
            rendered_report_ref=rendered.rendered_report_id,
            evidence_refs=(*common_refs, finding.finding_id, rendered.rendered_report_id),
            reason_codes=decision.reasons,
        )

    @staticmethod
    def _resolve_protected_binding(
        issuance: ScientificWorkflowIssuance,
        scope: ProtectedResourceScope,
    ) -> str:
        if scope != issuance.workflow.protected_scope:
            raise WorkflowRegistryError("Protected scope is not the registered exact scope.")
        if issuance.protected_resource.scope != scope:
            raise WorkflowRegistryError("Protected scope has no authoritative resource binding.")
        return issuance.protected_resource.resource_binding_ref

    @staticmethod
    def _load_protected_catalog(
        issuance: ScientificWorkflowIssuance,
        resource_binding_ref: str,
    ) -> LoadedProtectedCatalog:
        resource = issuance.protected_resource
        if resource_binding_ref != resource.resource_binding_ref:
            raise WorkflowRegistryError("Protected catalog binding is not registered.")
        return LoadedProtectedCatalog(
            manifest=resource.content_manifest,
            catalog=resource.catalog,
        )

    def _receipt(
        self,
        workflow: RegisteredScientificWorkflow,
        idempotency_key: str,
        status: WorkflowStatus,
        *,
        development_evidence_ref: str | None = None,
        frozen_system_ref: str | None = None,
        permit_ref: str | None = None,
        view_ref: str | None = None,
        exposure_ref: str | None = None,
        run_ref: str | None = None,
        evaluation_report_ref: str | None = None,
        validation_decision_ref: str | None = None,
        finding_ref: str | None = None,
        negative_result_ref: str | None = None,
        rendered_report_ref: str | None = None,
        evidence_refs: tuple[str, ...],
        reason_codes: tuple[str, ...],
    ) -> WorkflowReceipt:
        completed_at = self._clock()
        payload = {
            "workflow_id": workflow.workflow_id,
            "session_id": workflow.session_id,
            "episode_id": workflow.episode_id,
            "idempotency_key": idempotency_key,
            "status": status,
            "development_evidence_ref": development_evidence_ref,
            "frozen_system_ref": frozen_system_ref,
            "permit_ref": permit_ref,
            "view_ref": view_ref,
            "exposure_ref": exposure_ref,
            "run_ref": run_ref,
            "evaluation_report_ref": evaluation_report_ref,
            "validation_decision_ref": validation_decision_ref,
            "finding_ref": finding_ref,
            "negative_result_ref": negative_result_ref,
            "rendered_report_ref": rendered_report_ref,
            "evidence_refs": evidence_refs,
            "reason_codes": reason_codes,
            "completed_at": completed_at,
        }
        receipt = WorkflowReceipt(
            receipt_id=stable_identity("workflow-receipt", payload),
            workflow_id=workflow.workflow_id,
            session_id=workflow.session_id,
            episode_id=workflow.episode_id,
            idempotency_key=idempotency_key,
            status=status,
            development_evidence_ref=development_evidence_ref,
            frozen_system_ref=frozen_system_ref,
            permit_ref=permit_ref,
            view_ref=view_ref,
            exposure_ref=exposure_ref,
            run_ref=run_ref,
            evaluation_report_ref=evaluation_report_ref,
            validation_decision_ref=validation_decision_ref,
            finding_ref=finding_ref,
            negative_result_ref=negative_result_ref,
            rendered_report_ref=rendered_report_ref,
            evidence_refs=evidence_refs,
            reason_codes=reason_codes,
            completed_at=completed_at,
        )
        self._record_evidence(receipt.receipt_id, receipt)
        return receipt

    def _record_evidence(self, evidence_ref: str, evidence: object) -> None:
        prior = self._evidence.get(evidence_ref)
        if prior is not None and prior != evidence:
            raise WorkflowRegistryError("Evidence identity was reused with changed semantics.")
        self._evidence[evidence_ref] = evidence


def _workflow_issuance_payload(
    workflow: RegisteredScientificWorkflow,
    *,
    workflow_authority_id: str,
    governance_permission: PermissionGrant,
    validation_grant: ValidationAuthorityGrant,
    protected_resource: ProtectedResourceRegistration,
) -> dict[str, object]:
    return {
        "workflow_id": workflow.workflow_id,
        "workflow_authority_id": workflow_authority_id,
        "governance_permission": {
            "actor_id": governance_permission.actor_id,
            "authority_id": governance_permission.authority_id,
            "scope_ids": tuple(sorted(governance_permission.scope_ids)),
            "policy_ref": governance_permission.policy_ref,
            "environment_ref": governance_permission.environment_ref,
        },
        "validation_grant": {
            "authority_id": validation_grant.authority_id,
            "authority_policy_ref": validation_grant.authority_policy_ref,
            "environment_ref": validation_grant.environment_ref,
        },
        "protected_resource_registration_id": protected_resource.registration_id,
        "freeze_eligibility_registration_id": (
            workflow.freeze_eligibility_registration.registration_id
        ),
    }


def _without_first_field(item: object) -> dict[str, object]:
    fields = getattr(item, "__dataclass_fields__", {})
    first = next(iter(fields), None)
    return {name: getattr(item, name) for name in fields if name != first}


__all__ = [
    "IdempotencyConflictError",
    "ProtectedResourceIssuer",
    "ProtectedResourceRegistration",
    "ProtectedResourceRegistry",
    "RegisteredScientificWorkflow",
    "ScientificWorkflowCoordinator",
    "ScientificWorkflowIssuance",
    "ScientificWorkflowIssuer",
    "ValidationAuthorityGrant",
    "WorkflowAuthorityRegistry",
    "WorkflowReceipt",
    "WorkflowRegistry",
    "WorkflowRegistryError",
    "WorkflowStatus",
    "configure_protected_resource_authority",
    "configure_scientific_workflow_authority",
]
