"""Compatibility import surface for the production verification framework."""

from research_agent.verification import (
    COMPOSITES,
    FAMILIES,
    AgentScenario,
    BehavioralDecision,
    BehavioralExecutionStatus,
    BehavioralRunResult,
    HarnessValidity,
    ProductionProofFailureError,
    ProofAdapterRegistry,
    ProofEvidence,
    ProofTrace,
    Proposition,
    ResearcherQuality,
    ScenarioFamily,
    ScenarioGrade,
    VerificationResult,
    VerificationStatus,
    generate_family,
    grade_dispositions,
    production_proof_registry,
    run_behavioral_family,
    run_proof_suite,
    summarize,
)


def run_red_suite(
    available_mechanisms: frozenset[str] = frozenset(),
) -> tuple[VerificationResult, ...]:
    """Preserve the pre-production call while refusing registration-only proof."""
    return run_proof_suite(declared_mechanisms=available_mechanisms)


__all__ = [
    "COMPOSITES",
    "FAMILIES",
    "AgentScenario",
    "BehavioralDecision",
    "BehavioralExecutionStatus",
    "BehavioralRunResult",
    "HarnessValidity",
    "ProductionProofFailureError",
    "ProofAdapterRegistry",
    "ProofEvidence",
    "ProofTrace",
    "Proposition",
    "ResearcherQuality",
    "ScenarioFamily",
    "ScenarioGrade",
    "VerificationResult",
    "VerificationStatus",
    "generate_family",
    "grade_dispositions",
    "production_proof_registry",
    "run_behavioral_family",
    "run_proof_suite",
    "run_red_suite",
    "summarize",
]
