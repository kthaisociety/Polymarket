"""Honest execution and classification of deterministic composition proofs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import TYPE_CHECKING, Protocol

from research_agent.verification.catalog import (
    COMPOSITES,
    COMPOSITES_BY_ID,
    validate_production_trace,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


class VerificationStatus(StrEnum):
    """Keep application absence, proof, suspicion, and harness failure distinct."""

    EXPECTED_RED = "EXPECTED_RED"
    HARNESS_GREEN = "HARNESS_GREEN"
    UNEXPECTED_GREEN = "UNEXPECTED_GREEN"
    HARNESS_BUG = "HARNESS_BUG"


@dataclass(frozen=True, slots=True)
class ProofTrace:
    """Raw observations returned by one trusted production adapter."""

    proposition_id: str
    adapter_id: str
    facts: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class ProofEvidence:
    """Catalog-owned interpretation of one raw production trace."""

    proposition_id: str
    adapter_id: str
    production_components: tuple[str, ...]
    assertions: Mapping[str, bool]
    facts: Mapping[str, object]


class ProductionProofFailureError(RuntimeError):
    """Production execution failed before the adapter could return a complete trace."""


class ProofAdapter(Protocol):
    """Executable adapter over the production composition named by a proposition."""

    @property
    def proposition_id(self) -> str:
        """Return the exact catalog proposition this adapter proves."""
        ...

    @property
    def adapter_id(self) -> str:
        """Return stable proof-adapter identity."""
        ...

    def execute(self) -> ProofTrace:
        """Execute a fresh paired/adversarial proof world and return raw observations."""
        ...


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Auditable outcome for one deterministic composition."""

    id: str
    status: VerificationStatus
    reason: str
    adapter_id: str | None = None
    evidence: ProofEvidence | None = None


class ProofAdapterRegistry:
    """Separate declared availability from executable adapter registration."""

    def __init__(self) -> None:
        """Start with no production claims."""
        self._adapters: dict[str, ProofAdapter] = {}
        self._trusted_propositions: set[str] = set()

    def register(self, adapter: ProofAdapter) -> None:
        """Register one exact adapter; registration is not proof execution."""
        if adapter.proposition_id not in COMPOSITES_BY_ID:
            msg = f"Unknown proposition {adapter.proposition_id!r}."
            raise ValueError(msg)
        if adapter.proposition_id in self._adapters:
            msg = f"Duplicate adapter for {adapter.proposition_id!r}."
            raise ValueError(msg)
        self._adapters[adapter.proposition_id] = adapter

    def register_catalog_adapter(self, adapter: ProofAdapter) -> None:
        """Register one repository-owned adapter for catalog validation."""
        self.register(adapter)
        self._trusted_propositions.add(adapter.proposition_id)

    def adapter_for(self, proposition_id: str) -> ProofAdapter | None:
        """Return the exact registered adapter without executing it."""
        return self._adapters.get(proposition_id)

    def is_trusted(self, proposition_id: str) -> bool:
        """Return whether registration came from the repository production registry."""
        return proposition_id in self._trusted_propositions


def run_proof_suite(  # noqa: C901
    registry: ProofAdapterRegistry | None = None,
    *,
    declared_mechanisms: frozenset[str] = frozenset(),
) -> tuple[VerificationResult, ...]:
    """Execute adapters and classify every proposition without swallowing defects."""
    active_registry = registry or ProofAdapterRegistry()
    results: list[VerificationResult] = []
    for proposition in COMPOSITES:
        adapter = active_registry.adapter_for(proposition.id)
        if adapter is None:
            if proposition.id in declared_mechanisms:
                results.append(
                    VerificationResult(
                        proposition.id,
                        VerificationStatus.UNEXPECTED_GREEN,
                        (
                            "mechanism declared available without an executable architecture "
                            "proof adapter"
                        ),
                    )
                )
            else:
                results.append(
                    VerificationResult(
                        proposition.id,
                        VerificationStatus.EXPECTED_RED,
                        f"production composition absent: {proposition.name}",
                    )
                )
            continue
        if not active_registry.is_trusted(proposition.id):
            results.append(
                VerificationResult(
                    proposition.id,
                    VerificationStatus.UNEXPECTED_GREEN,
                    "untrusted adapter registration cannot establish production proof",
                    adapter.adapter_id,
                )
            )
            continue
        try:
            trace = adapter.execute()
        except ProductionProofFailureError as error:
            results.append(
                VerificationResult(
                    proposition.id,
                    VerificationStatus.EXPECTED_RED,
                    f"production proof execution failed: {error}",
                    adapter.adapter_id,
                )
            )
            continue
        except Exception as error:  # noqa: BLE001 - classification boundary must preserve crashes
            results.append(
                VerificationResult(
                    proposition.id,
                    VerificationStatus.HARNESS_BUG,
                    f"proof adapter crashed: {type(error).__name__}: {error}",
                    adapter.adapter_id,
                )
            )
            continue
        malformed = _malformed_trace(proposition.id, adapter, trace)
        if malformed is not None:
            results.append(
                VerificationResult(
                    proposition.id,
                    VerificationStatus.HARNESS_BUG,
                    malformed,
                    adapter.adapter_id,
                )
            )
            continue
        validation = validate_production_trace(proposition, trace.facts)
        if validation is None:
            results.append(
                VerificationResult(
                    proposition.id,
                    VerificationStatus.HARNESS_BUG,
                    "catalog could not validate the raw production trace",
                    adapter.adapter_id,
                )
            )
            continue
        if validation.production_components != proposition.expected_components:
            results.append(
                VerificationResult(
                    proposition.id,
                    VerificationStatus.HARNESS_BUG,
                    "catalog validation did not prove the exact expected production components",
                    adapter.adapter_id,
                )
            )
            continue
        evidence = ProofEvidence(
            proposition.id,
            adapter.adapter_id,
            validation.production_components,
            validation.assertions,
            trace.facts,
        )
        missing = tuple(
            name for name in proposition.required_evidence if name not in evidence.assertions
        )
        if missing:
            results.append(
                VerificationResult(
                    proposition.id,
                    VerificationStatus.HARNESS_BUG,
                    f"catalog validation omitted required assertions: {', '.join(missing)}",
                    adapter.adapter_id,
                    evidence,
                )
            )
            continue
        failed = tuple(
            name for name in proposition.required_evidence if not evidence.assertions[name]
        )
        if failed:
            results.append(
                VerificationResult(
                    proposition.id,
                    VerificationStatus.EXPECTED_RED,
                    f"executed production proof failed: {', '.join(failed)}",
                    adapter.adapter_id,
                    evidence,
                )
            )
            continue
        results.append(
            VerificationResult(
                proposition.id,
                VerificationStatus.HARNESS_GREEN,
                "executed production composition satisfied every required invariant assertion",
                adapter.adapter_id,
                evidence,
            )
        )
    return tuple(results)


def _malformed_trace(
    proposition_id: str,
    adapter: ProofAdapter,
    trace: ProofTrace,
) -> str | None:
    if trace.proposition_id != proposition_id or trace.adapter_id != adapter.adapter_id:
        return "proof trace identity does not match the registered adapter and proposition"
    if not trace.facts:
        return "proof trace contains no raw production observations"
    return None


def summarize(results: tuple[VerificationResult, ...]) -> Mapping[VerificationStatus, int]:
    """Count all status classes without collapsing their meaning."""
    return MappingProxyType(
        {
            status: sum(result.status == status for result in results)
            for status in VerificationStatus
        }
    )


__all__ = [
    "ProductionProofFailureError",
    "ProofAdapter",
    "ProofAdapterRegistry",
    "ProofEvidence",
    "ProofTrace",
    "VerificationResult",
    "VerificationStatus",
    "run_proof_suite",
    "summarize",
]
