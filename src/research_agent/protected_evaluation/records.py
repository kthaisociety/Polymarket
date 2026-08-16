"""Immutable authority and identity records for protected evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from research_agent.protected_evaluation._identity import (
    require_refs,
    require_text,
    scientific_identity,
)

if TYPE_CHECKING:
    from datetime import datetime

    from research_agent.data_foundation import DataCatalogSnapshot

SHA256_HEX_LENGTH = 64


class DecisionStatus(Enum):
    """Outcome of an independent privileged decision."""

    ACCEPT = "accept"
    DENY = "deny"


class DenialCode(Enum):
    """Safe, non-content-bearing governance denial classes."""

    UNFROZEN_SYSTEM = "UNFROZEN_SYSTEM"
    INCOMPLETE_PREDECLARATION = "INCOMPLETE_PREDECLARATION"
    SELF_AUTHORIZATION = "SELF_AUTHORIZATION"
    AUTHORITY_NOT_AUTHORIZED = "AUTHORITY_NOT_AUTHORIZED"
    STALE_IDENTITY = "STALE_IDENTITY"
    SCOPE_NOT_AUTHORIZED = "SCOPE_NOT_AUTHORIZED"
    PRIOR_EXPOSURE = "PRIOR_EXPOSURE"
    CALLER_NOT_AUTHORIZED = "CALLER_NOT_AUTHORIZED"
    PERMIT_MISMATCH = "PERMIT_MISMATCH"
    PERMIT_ALREADY_CONSUMED = "PERMIT_ALREADY_CONSUMED"


class ProtectedExposureStatus(Enum):
    """Authoritative freshness status of a protected content period."""

    UNSEEN = "unseen"
    PREEXPOSED = "preexposed"


@dataclass(frozen=True, slots=True)
class ProtectedContentManifest:
    """Content identity verified by the protected-resource authority.

    The digest is intentionally absent from request and denial records.  Callers receive only the
    opaque ``manifest_id`` carried by ``ProtectedResourceScope``.  A production protected loader
    computes the digest over the resolved bytes and returns this exact manifest only after exposure
    has been recorded.
    """

    manifest_id: str
    digest_algorithm: str
    content_digest: str
    byte_length: int
    catalog_id: str
    provenance_ref: str

    @property
    def content_identity_id(self) -> str:
        """Return path/provenance-independent identity of the exact protected bytes."""
        return scientific_identity(
            "protected-content",
            (
                ("digest_algorithm", self.digest_algorithm),
                ("content_digest", self.content_digest),
                ("byte_length", str(self.byte_length)),
            ),
        )

    def __post_init__(self) -> None:
        """Reject malformed or stale caller-supplied manifest identity."""
        for name, value in (
            ("digest_algorithm", self.digest_algorithm),
            ("content_digest", self.content_digest),
            ("catalog_id", self.catalog_id),
            ("provenance_ref", self.provenance_ref),
        ):
            require_text(value, name)
        if self.byte_length < 0:
            msg = "protected content byte length cannot be negative"
            raise ValueError(msg)
        if self.digest_algorithm != "sha256" or len(self.content_digest) != SHA256_HEX_LENGTH:
            msg = "protected content manifest requires an exact sha256 digest"
            raise ValueError(msg)
        try:
            int(self.content_digest, 16)
        except ValueError as error:
            msg = "protected content manifest requires an exact sha256 digest"
            raise ValueError(msg) from error
        expected = scientific_identity(
            "protected-content-manifest",
            (
                ("digest_algorithm", self.digest_algorithm),
                ("content_digest", self.content_digest),
                ("byte_length", str(self.byte_length)),
                ("catalog_id", self.catalog_id),
                ("provenance_ref", self.provenance_ref),
            ),
        )
        if self.manifest_id != expected:
            msg = "protected content manifest identity does not match content"
            raise ValueError(msg)

    @classmethod
    def create(
        cls,
        *,
        content_digest: str,
        byte_length: int,
        catalog_id: str,
        provenance_ref: str,
        digest_algorithm: str = "sha256",
    ) -> ProtectedContentManifest:
        """Create one exact content manifest from authority-verified digest facts."""
        manifest_id = scientific_identity(
            "protected-content-manifest",
            (
                ("digest_algorithm", digest_algorithm),
                ("content_digest", content_digest),
                ("byte_length", str(byte_length)),
                ("catalog_id", catalog_id),
                ("provenance_ref", provenance_ref),
            ),
        )
        return cls(
            manifest_id=manifest_id,
            digest_algorithm=digest_algorithm,
            content_digest=content_digest,
            byte_length=byte_length,
            catalog_id=catalog_id,
            provenance_ref=provenance_ref,
        )


@dataclass(frozen=True, slots=True)
class LoadedProtectedCatalog:
    """Catalog returned after disclosure together with its verified content manifest."""

    manifest: ProtectedContentManifest
    catalog: DataCatalogSnapshot

    def __post_init__(self) -> None:
        """Keep parsed catalog identity bound to the verified content manifest."""
        if self.manifest.catalog_id != self.catalog.identity:
            msg = "loaded protected catalog does not match its content manifest"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class ProtectedResourceScope:
    """Exact protected resource, version, slice, environment, and policy scope."""

    resource_id: str
    resource_version: str
    slice_id: str
    environment_ref: str
    policy_ref: str
    content_manifest_id: str
    content_identity_id: str
    epistemic_period_ref: str
    exposure_status: ProtectedExposureStatus

    def __post_init__(self) -> None:
        """Require every scope dimension to be explicit."""
        for name, value in (
            ("resource_id", self.resource_id),
            ("resource_version", self.resource_version),
            ("slice_id", self.slice_id),
            ("environment_ref", self.environment_ref),
            ("policy_ref", self.policy_ref),
            ("content_manifest_id", self.content_manifest_id),
            ("content_identity_id", self.content_identity_id),
            ("epistemic_period_ref", self.epistemic_period_ref),
        ):
            require_text(value, name)

    @property
    def scope_id(self) -> str:
        """Return an exact non-broadenable scope identity."""
        return scientific_identity(
            "protected-scope",
            (
                ("resource_id", self.resource_id),
                ("resource_version", self.resource_version),
                ("slice_id", self.slice_id),
                ("environment_ref", self.environment_ref),
                ("policy_ref", self.policy_ref),
                ("content_manifest_id", self.content_manifest_id),
                ("content_identity_id", self.content_identity_id),
                ("epistemic_period_ref", self.epistemic_period_ref),
                ("exposure_status", self.exposure_status.value),
            ),
        )

    @property
    def exposure_period_id(self) -> str:
        """Return alias-independent holdout identity, excluding resource label and version.

        A corrected or republished resource version does not make an already disclosed
        holdout period epistemically fresh. An authority assigns one ``epistemic_period_ref`` to
        aliases and revisions of the same holdout period. Changing policy is the explicit
        authority boundary for a different treatment of that period.
        """
        return scientific_identity(
            "protected-exposure-period",
            (
                ("epistemic_period_ref", self.epistemic_period_ref),
                ("slice_id", self.slice_id),
                ("environment_ref", self.environment_ref),
                ("policy_ref", self.policy_ref),
            ),
        )


@dataclass(frozen=True, slots=True)
class FreezeEligibilityRequest:
    """Exact candidate identity submitted to an independent freeze gate."""

    system_id: str
    candidate_version: str
    ancestry_refs: tuple[str, ...]
    development_evidence_refs: tuple[str, ...]
    protocol_refs: tuple[str, ...]
    environment_ref: str
    standard_ref: str
    requester_id: str
    beneficiary_id: str

    def __post_init__(self) -> None:
        """Reject structurally incomplete freeze requests."""
        for name, value in (
            ("system_id", self.system_id),
            ("candidate_version", self.candidate_version),
            ("environment_ref", self.environment_ref),
            ("standard_ref", self.standard_ref),
            ("requester_id", self.requester_id),
            ("beneficiary_id", self.beneficiary_id),
        ):
            require_text(value, name)
        require_refs(self.ancestry_refs, "ancestry_refs")
        require_refs(self.development_evidence_refs, "development_evidence_refs")
        require_refs(self.protocol_refs, "protocol_refs")

    @property
    def request_id(self) -> str:
        """Return the semantic request identity, independent of transport."""
        return scientific_identity(
            "freeze-request",
            (
                ("system_id", self.system_id),
                ("candidate_version", self.candidate_version),
                ("ancestry_refs", self.ancestry_refs),
                ("development_evidence_refs", self.development_evidence_refs),
                ("protocol_refs", self.protocol_refs),
                ("environment_ref", self.environment_ref),
                ("standard_ref", self.standard_ref),
                ("requester_id", self.requester_id),
                ("beneficiary_id", self.beneficiary_id),
            ),
        )


@dataclass(frozen=True, slots=True)
class FreezeDecision:
    """Independent freeze eligibility outcome; acceptance is not a frozen object."""

    decision_id: str
    request_id: str
    system_id: str
    authority_id: str
    status: DecisionStatus
    reason_code: str
    decided_at: datetime


@dataclass(frozen=True, slots=True)
class FrozenPredictiveSystemIdentity:
    """Immutable binding to an exact upstream predictive-system identity.

    ``system_id`` is deliberately opaque. The formalization layer must provide a
    content/version identity for the complete ``PredictiveSystemDefinition``.
    This module neither imports that implementation nor resolves a "latest" object.
    """

    frozen_system_id: str
    system_id: str
    candidate_version: str
    ancestry_refs: tuple[str, ...]
    development_evidence_refs: tuple[str, ...]
    protocol_refs: tuple[str, ...]
    environment_ref: str
    standard_ref: str
    freeze_decision_id: str
    freeze_authority_id: str
    frozen_at: datetime


@dataclass(frozen=True, slots=True)
class BacktestRequest:
    """Exact predeclared protected experiment request, never a permit."""

    frozen_system_id: str
    system_id: str
    scenario_ref: str
    decision_times_ref: str
    training_protocol_ref: str
    evaluation_spec_ref: str
    validation_standard_ref: str
    claim_ref: str
    protected_scope: ProtectedResourceScope
    environment_ref: str
    ancestry_refs: tuple[str, ...]
    prior_exposure_refs: tuple[str, ...]
    requester_id: str
    beneficiary_id: str
    idempotency_key: str

    def __post_init__(self) -> None:
        """Require all semantic and authority dimensions before governance."""
        for name, value in (
            ("frozen_system_id", self.frozen_system_id),
            ("system_id", self.system_id),
            ("scenario_ref", self.scenario_ref),
            ("decision_times_ref", self.decision_times_ref),
            ("training_protocol_ref", self.training_protocol_ref),
            ("evaluation_spec_ref", self.evaluation_spec_ref),
            ("validation_standard_ref", self.validation_standard_ref),
            ("claim_ref", self.claim_ref),
            ("environment_ref", self.environment_ref),
            ("requester_id", self.requester_id),
            ("beneficiary_id", self.beneficiary_id),
            ("idempotency_key", self.idempotency_key),
        ):
            require_text(value, name)
        require_refs(self.ancestry_refs, "ancestry_refs")

    @property
    def request_id(self) -> str:
        """Return the identity of the full predeclared experiment."""
        return scientific_identity(
            "backtest-request",
            (
                ("frozen_system_id", self.frozen_system_id),
                ("system_id", self.system_id),
                ("scenario_ref", self.scenario_ref),
                ("decision_times_ref", self.decision_times_ref),
                ("training_protocol_ref", self.training_protocol_ref),
                ("evaluation_spec_ref", self.evaluation_spec_ref),
                ("validation_standard_ref", self.validation_standard_ref),
                ("claim_ref", self.claim_ref),
                ("protected_scope_id", self.protected_scope.scope_id),
                ("environment_ref", self.environment_ref),
                ("ancestry_refs", self.ancestry_refs),
                ("prior_exposure_refs", self.prior_exposure_refs),
                ("requester_id", self.requester_id),
                ("beneficiary_id", self.beneficiary_id),
                ("idempotency_key", self.idempotency_key),
            ),
        )


@dataclass(frozen=True, slots=True)
class BacktestPermit:
    """Immutable least-authority permit for one exact request and scope."""

    permit_id: str
    request_id: str
    frozen_system_id: str
    system_id: str
    scenario_ref: str
    scope: ProtectedResourceScope
    requester_id: str
    authority_id: str
    policy_ref: str
    issued_at: datetime


@dataclass(frozen=True, slots=True)
class BacktestDenial:
    """Safe denial that contains no protected content or content-derived detail."""

    denial_id: str
    request_id: str
    code: DenialCode
    message: str
    authority_id: str
    denied_at: datetime


@dataclass(frozen=True, slots=True)
class AuthorizedProtectedDataView:
    """Metadata-only least-authority view binding for later execution."""

    view_id: str
    permit_id: str
    request_id: str
    frozen_system_id: str
    scenario_ref: str
    scope: ProtectedResourceScope
    resource_binding_ref: str
    caller_id: str
    bound_at: datetime


@dataclass(frozen=True, slots=True)
class ExposureRecord:
    """Irreversible fact that protected information crossed a disclosure boundary."""

    exposure_id: str
    disclosure_key: str
    view_id: str
    permit_id: str
    request_id: str
    frozen_system_id: str
    system_id: str
    lineage_refs: tuple[str, ...]
    scope: ProtectedResourceScope
    content_manifest_id: str
    content_identity_id: str
    exposure_period_id: str
    recipient_id: str
    disclosure_status: str
    disclosed_at: datetime


__all__ = [
    "AuthorizedProtectedDataView",
    "BacktestDenial",
    "BacktestPermit",
    "BacktestRequest",
    "DecisionStatus",
    "DenialCode",
    "ExposureRecord",
    "FreezeDecision",
    "FreezeEligibilityRequest",
    "FrozenPredictiveSystemIdentity",
    "LoadedProtectedCatalog",
    "ProtectedContentManifest",
    "ProtectedExposureStatus",
    "ProtectedResourceScope",
]
