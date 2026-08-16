"""Repeatable harness-causality fixtures with evaluator-private truth."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Mapping


_CASE_TEMPLATES = {
    "signal-discrimination": ("strengthen", "reject", "uncertain"),
    "belief-revision-under-contradiction": ("revise", "hold", "strengthen"),
    "creative-discovery-under-sparse-clues": ("discover", "reject", "uncertain"),
    "information-efficient-experimental-judgment": ("stop", "investigate", "investigate"),
    "recovery-preserving-scientific-intent": ("repair", "version", "deny"),
    "long-horizon-coherence-after-context-loss": ("continue", "retrieve", "correct-stale"),
    "premature-commitment-and-claim-calibration": ("commit", "reject", "defer"),
    "hypothesis-falsification": ("retain", "falsify", "qualify"),
    "appropriate-research-rescoping": ("rescope", "respecify", "persist"),
    "retrieval-and-use-of-prior-evidence": ("use-current", "ignore-stale", "respect-denial"),
    "positive-cross-task-validated-transfer": ("transfer", "adapt", "ignore"),
    "avoid-harmful-lesson-overgeneralization": ("use", "test", "decline"),
}

# Public metadata intentionally contains no case order or correct dispositions.
FAMILIES = frozenset(_CASE_TEMPLATES)
_OPAQUE_ID_SALT = "harness-causality-fixture-v2"
MIN_COMPLEMENTARY_DISPOSITIONS = 2


class HarnessValidity(StrEnum):
    """Whether the evaluator produced a structurally interpretable run."""

    VALID = "VALID"
    INVALID = "INVALID"


class ResearcherQuality(StrEnum):
    """Real researcher quality is never inferred from scripted harness fixtures."""

    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_ASSESSED = "NOT_ASSESSED"


class BehavioralExecutionStatus(StrEnum):
    """Keep policy/runtime failure separate from evaluator validity."""

    NOT_RUN = "NOT_RUN"
    COMPLETED = "COMPLETED"
    POLICY_FAILED = "POLICY_FAILED"
    NONDETERMINISTIC = "NONDETERMINISTIC"
    PROTOCOL_VIOLATION = "PROTOCOL_VIOLATION"


@dataclass(frozen=True, slots=True)
class AgentScenario:
    """Complete policy-visible payload, excluding seed, order, and evaluator truth."""

    family_id: str
    scenario_id: str
    task: str
    surface_evidence: str


@dataclass(frozen=True, slots=True)
class _EvaluatorScenario:
    """Evaluator-owned truth paired with one opaque agent view."""

    agent_view: AgentScenario
    required_disposition: str
    generator_label: str


@dataclass(frozen=True, slots=True)
class ScenarioFamily:
    """Reproducible family whose truth and root seed never enter policy payloads."""

    family_id: str
    run_id: str
    agent_views: tuple[AgentScenario, ...]
    evaluator_cases: tuple[_EvaluatorScenario, ...] = field(repr=False)
    root_seed: int = field(repr=False)


@dataclass(frozen=True, slots=True)
class BehavioralDecision:
    """One provider-neutral disposition and its observable evidence references."""

    policy_id: str
    scenario_id: str
    disposition: str
    evidence_refs: tuple[str, ...] = ()


class DeterministicBehaviorPolicy(Protocol):
    """Policy seam used only for repeatable harness-causality trials."""

    @property
    def policy_id(self) -> str:
        """Return stable policy/provider identity for the complete run."""
        ...

    def decide(self, scenario: AgentScenario) -> BehavioralDecision:
        """Return one decision from the policy-visible scenario."""
        ...


@dataclass(frozen=True, slots=True)
class ScenarioGrade:
    """Evaluator-owned per-scenario mechanical grading evidence."""

    scenario_id: str
    expected_disposition: str
    observed_disposition: str
    disposition_correct: bool
    identity_preserved: bool
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BehavioralRunResult:
    """Harness result that never promotes a scripted fixture into researcher quality."""

    family_id: str
    run_id: str
    policy_id: str
    harness_validity: HarnessValidity
    execution_status: BehavioralExecutionStatus
    researcher_quality: ResearcherQuality
    evidence_level: str
    score: float | None
    constant_policy_baselines: Mapping[str, float]
    property_evidence: Mapping[str, bool]
    scenario_grades: tuple[ScenarioGrade, ...]
    reason: str


def generate_family(family_id: str, seed: int) -> ScenarioFamily:
    """Generate a reproducible, privately shuffled complementary triplet."""
    outcomes = _CASE_TEMPLATES.get(family_id)
    if outcomes is None:
        msg = f"Unknown behavioral family {family_id!r}."
        raise ValueError(msg)
    cases = [
        _EvaluatorScenario(
            agent_view=AgentScenario(
                family_id=family_id,
                scenario_id=_opaque_scenario_id(family_id, seed, case_key),
                task=f"fixture-task-{_opaque_token(family_id, seed, case_key, 'task')}",
                surface_evidence=(
                    f"fixture-evidence-{_opaque_token(family_id, seed, case_key, 'evidence')}"
                ),
            ),
            required_disposition=outcome,
            generator_label=f"private-case-{case_key}",
        )
        for case_key, outcome in enumerate(outcomes)
    ]
    shuffle_seed = int(_opaque_token(family_id, seed, -1, "shuffle"), 16)
    random.Random(shuffle_seed).shuffle(cases)  # noqa: S311 - reproducibility, not security
    evaluator_cases = tuple(cases)
    return ScenarioFamily(
        family_id=family_id,
        run_id=f"run-{_opaque_token(family_id, seed, -1, 'run')}",
        agent_views=tuple(case.agent_view for case in evaluator_cases),
        evaluator_cases=evaluator_cases,
        root_seed=seed,
    )


def run_behavioral_family(
    family: ScenarioFamily,
    policy: DeterministicBehaviorPolicy,
) -> BehavioralRunResult:
    """Run and mechanically grade one harness-causality fixture family."""
    structural_error = _family_error(family)
    if structural_error is not None:
        return _invalid_result(family, policy.policy_id, structural_error)

    decisions: list[BehavioralDecision] = []
    try:
        for scenario in family.agent_views:
            first = policy.decide(scenario)
            second = policy.decide(scenario)
            if first != second:
                return _policy_failure_result(
                    family,
                    policy.policy_id,
                    BehavioralExecutionStatus.NONDETERMINISTIC,
                    "policy violated the deterministic fixture protocol",
                )
            decisions.append(first)
    except Exception as error:  # noqa: BLE001 - policy failure is an observed run outcome
        return _policy_failure_result(
            family,
            policy.policy_id,
            BehavioralExecutionStatus.POLICY_FAILED,
            f"policy execution failed: {type(error).__name__}: {error}",
        )

    truth_by_id = {
        case.agent_view.scenario_id: case.required_disposition for case in family.evaluator_cases
    }
    grades = tuple(
        ScenarioGrade(
            scenario_id=scenario.scenario_id,
            expected_disposition=truth_by_id[scenario.scenario_id],
            observed_disposition=decision.disposition,
            disposition_correct=decision.disposition == truth_by_id[scenario.scenario_id],
            identity_preserved=(
                decision.policy_id == policy.policy_id
                and decision.scenario_id == scenario.scenario_id
            ),
            evidence_refs=decision.evidence_refs,
        )
        for scenario, decision in zip(family.agent_views, decisions, strict=True)
    )
    identities_preserved = all(grade.identity_preserved for grade in grades)
    if not identities_preserved:
        return _policy_failure_result(
            family,
            policy.policy_id,
            BehavioralExecutionStatus.PROTOCOL_VIOLATION,
            "policy response identity did not match the visible scenario",
            grades=grades,
        )
    properties = MappingProxyType(
        {
            "complete_family": True,
            "hidden_truth_isolated": all(_view_is_opaque(view) for view in family.agent_views),
            "deterministic_policy": True,
            "decision_identity_preserved": True,
            "complementary_worlds": (
                len(set(truth_by_id.values())) >= MIN_COMPLEMENTARY_DISPOSITIONS
            ),
        }
    )
    if not all(properties.values()):
        return BehavioralRunResult(
            family.family_id,
            family.run_id,
            policy.policy_id,
            HarnessValidity.INVALID,
            BehavioralExecutionStatus.NOT_RUN,
            ResearcherQuality.NOT_ASSESSED,
            "HARNESS_CAUSALITY_ONLY",
            None,
            MappingProxyType({}),
            properties,
            grades,
            "evaluator property validation failed",
        )
    score = sum(grade.disposition_correct for grade in grades) / len(grades)
    return BehavioralRunResult(
        family.family_id,
        family.run_id,
        policy.policy_id,
        HarnessValidity.VALID,
        BehavioralExecutionStatus.COMPLETED,
        ResearcherQuality.NOT_ASSESSED,
        "HARNESS_CAUSALITY_ONLY",
        score,
        _constant_policy_scores(family),
        properties,
        grades,
        "complete mechanical fixture grading; researcher quality not assessed",
    )


def grade_dispositions(family: ScenarioFamily, dispositions: tuple[str, ...]) -> float:
    """Mechanically grade a complete exact fixture family."""
    if _family_error(family) is not None or len(dispositions) != len(family.evaluator_cases):
        msg = "a complete valid non-empty scenario family is required"
        raise ValueError(msg)
    return sum(
        disposition == scenario.required_disposition
        for scenario, disposition in zip(family.evaluator_cases, dispositions, strict=True)
    ) / len(dispositions)


@dataclass(frozen=True, slots=True)
class _EvaluatorFixturePolicy:
    """Evaluator-owned oracle used only to prove harness grading mechanics."""

    dispositions: Mapping[str, str]
    policy_id: str = "evaluator-owned-fixture-oracle"

    def decide(self, scenario: AgentScenario) -> BehavioralDecision:
        return BehavioralDecision(
            policy_id=self.policy_id,
            scenario_id=scenario.scenario_id,
            disposition=self.dispositions[scenario.scenario_id],
            evidence_refs=(f"fixture-evidence:{scenario.scenario_id}",),
        )


def evaluator_fixture_policy(family: ScenarioFamily) -> _EvaluatorFixturePolicy:
    """Build an explicitly evaluator-owned oracle; never expose it to a real policy."""
    return _EvaluatorFixturePolicy(
        MappingProxyType(
            {
                case.agent_view.scenario_id: case.required_disposition
                for case in family.evaluator_cases
            }
        )
    )


def _family_error(family: ScenarioFamily) -> str | None:
    expected = _CASE_TEMPLATES.get(family.family_id)
    if expected is None or not family.agent_views or not family.evaluator_cases:
        return "unknown or empty scenario family"
    if len(family.agent_views) != len(expected) or len(family.evaluator_cases) != len(expected):
        return "incomplete scenario family"
    private_views = tuple(case.agent_view for case in family.evaluator_cases)
    if private_views != family.agent_views:
        return "public and evaluator-private scenario identity/order mismatch"
    actual_outcomes = sorted(case.required_disposition for case in family.evaluator_cases)
    if actual_outcomes != sorted(expected):
        return "scenario family evaluator truth mismatch"
    if len({view.scenario_id for view in family.agent_views}) != len(family.agent_views):
        return "scenario family contains duplicate opaque identities"
    return None


def _view_is_opaque(view: AgentScenario) -> bool:
    return (
        view.scenario_id.startswith("scenario-")
        and len(view.scenario_id) == len("scenario-") + 24
        and view.scenario_id.removeprefix("scenario-").isalnum()
        and not any(
            outcome in view.scenario_id
            for outcomes in _CASE_TEMPLATES.values()
            for outcome in outcomes
        )
    )


def _constant_policy_scores(family: ScenarioFamily) -> Mapping[str, float]:
    dispositions = tuple(
        dict.fromkeys(case.required_disposition for case in family.evaluator_cases)
    )
    return MappingProxyType(
        {
            disposition: grade_dispositions(
                family,
                tuple(disposition for _ in family.agent_views),
            )
            for disposition in dispositions
        }
    )


def _invalid_result(
    family: ScenarioFamily,
    policy_id: str,
    reason: str,
) -> BehavioralRunResult:
    return BehavioralRunResult(
        family.family_id,
        family.run_id,
        policy_id,
        HarnessValidity.INVALID,
        BehavioralExecutionStatus.NOT_RUN,
        ResearcherQuality.NOT_ASSESSED,
        "HARNESS_CAUSALITY_ONLY",
        None,
        MappingProxyType({}),
        MappingProxyType({"complete_family": False}),
        (),
        reason,
    )


def _policy_failure_result(
    family: ScenarioFamily,
    policy_id: str,
    status: BehavioralExecutionStatus,
    reason: str,
    *,
    grades: tuple[ScenarioGrade, ...] = (),
) -> BehavioralRunResult:
    return BehavioralRunResult(
        family.family_id,
        family.run_id,
        policy_id,
        HarnessValidity.VALID,
        status,
        ResearcherQuality.NOT_ASSESSED,
        "HARNESS_CAUSALITY_ONLY",
        None,
        MappingProxyType({}),
        MappingProxyType({"complete_family": True}),
        grades,
        reason,
    )


def _opaque_scenario_id(family_id: str, seed: int, case_key: int) -> str:
    return f"scenario-{_opaque_token(family_id, seed, case_key, 'scenario')}"


def _opaque_token(family_id: str, seed: int, case_key: int, purpose: str) -> str:
    material = f"{_OPAQUE_ID_SALT}|{family_id}|{seed}|{case_key}|{purpose}".encode()
    return hashlib.sha256(material).hexdigest()[:24]


__all__ = [
    "FAMILIES",
    "AgentScenario",
    "BehavioralDecision",
    "BehavioralExecutionStatus",
    "BehavioralRunResult",
    "DeterministicBehaviorPolicy",
    "HarnessValidity",
    "ResearcherQuality",
    "ScenarioFamily",
    "ScenarioGrade",
    "generate_family",
    "grade_dispositions",
    "run_behavioral_family",
]
