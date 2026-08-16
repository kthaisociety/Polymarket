"""Contract checks for the project-local scientific guidance skills."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / ".agents" / "skills"


def _read(skill: str, relative: str = "SKILL.md") -> str:
    return (SKILLS / skill / relative).read_text(encoding="utf-8")


def test_analysis_skill_preserves_exploratory_status_and_both_time_axes() -> None:
    """Analysis guidance cannot upgrade observations or collapse scientific clocks."""
    skill = _read("analyze-time-series-data")
    principles = _read("analyze-time-series-data", "references/principles.md")

    assert "reference_time" in skill
    assert "available_at" in skill
    assert "epistemic status `EXPLORATORY`" in skill
    assert "Do not emit a `FeatureDefinition`" in skill
    assert "actual access" in skill
    assert "Keep predictor availability and label maturity separate" in principles


def test_feature_skill_is_mechanism_driven_without_a_mandatory_recipe() -> None:
    """Feature guidance keeps candidate choice open while preserving fit legality."""
    skill = _read("design-time-series-feature-set")
    principles = _read("design-time-series-feature-set", "references/principles.md")

    assert "A label is part of the hypothesis" in skill
    assert "smallest feature set" in skill
    assert "inside the legal training window" in skill
    assert "Keep `predict()` inference-only" in skill
    assert "No score directly mutates the feature set" in principles
    assert "winning feature family" in skill
    assert "mandatory recipe" in skill


def test_backtest_skill_cannot_self_authorize_or_tune_on_protected_results() -> None:
    """Backtest guidance preserves independent authority and exposure finality."""
    skill = _read("review-backtest-gate")
    principles = _read("review-backtest-gate", "references/principles.md")

    assert "independent governance and validation alone may authorize or promote" in skill
    assert "never recommend approval by the benefiting actor" in skill
    assert "Do not tune, replace, repair, rescore, or relabel" in skill
    assert "the exposed period remains exposed" in skill
    assert "Failure after disclosure does not restore freshness" in principles
    assert "The backtest engine records what happened" in principles


def test_agents_routes_three_skills_without_transferring_authority() -> None:
    """Repository routing names the skills without granting their outputs authority."""
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    for skill in (
        "$analyze-time-series-data",
        "$design-time-series-feature-set",
        "$review-backtest-gate",
    ):
        assert skill in agents
    assert "These skills guide researcher judgment" in agents
    assert "They do not grant data" in agents


def test_skill_feedback_requires_traceable_generalization_and_counterexample() -> None:
    """Research feedback must update guidance through general, falsifiable lessons."""
    for skill in (
        "analyze-time-series-data",
        "design-time-series-feature-set",
        "review-backtest-gate",
    ):
        content = _read(skill)
        assert "trace" in content.lower()
        assert "counterexample" in content.lower()
        assert "preserve" in content.lower()
