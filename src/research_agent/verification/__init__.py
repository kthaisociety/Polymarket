"""Executable deterministic and behavioral verification infrastructure."""

from research_agent.verification.behavioral import (
    FAMILIES,
    AgentScenario,
    BehavioralDecision,
    BehavioralExecutionStatus,
    BehavioralRunResult,
    HarnessValidity,
    ResearcherQuality,
    ScenarioFamily,
    ScenarioGrade,
    generate_family,
    grade_dispositions,
    run_behavioral_family,
)
from research_agent.verification.catalog import COMPOSITES, Proposition
from research_agent.verification.composites import (
    ProductionProofFailureError,
    ProofAdapterRegistry,
    ProofEvidence,
    ProofTrace,
    VerificationResult,
    VerificationStatus,
    run_proof_suite,
    summarize,
)
from research_agent.verification.production_adapters import production_proof_registry

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
    "summarize",
]
