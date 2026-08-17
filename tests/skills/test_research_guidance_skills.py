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


def test_agents_routes_research_skills_without_transferring_authority() -> None:
    """Repository routing names startup/stage skills without granting output authority."""
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    for skill in (
        "$start-polymarket-research",
        "$analyze-time-series-data",
        "$design-time-series-feature-set",
        "$review-backtest-gate",
    ):
        assert skill in agents
    assert "These skills guide researcher judgment" in agents
    assert "They do not grant data" in agents


def test_polymarket_startup_is_lean_optional_and_fail_closed() -> None:
    """Startup guidance preserves real adapter reds without prescribing a finance recipe."""
    skill = _read("start-polymarket-research")
    boundary = _read("start-polymarket-research", "references/polymarket-boundary.md")

    assert "Do not load it by default" in skill
    assert "menu of possible probes" in skill
    assert "$analyze-time-series-data" in skill
    assert "$design-time-series-feature-set" in skill
    assert "$review-backtest-gate" in skill
    assert "human_ro" in boundary
    assert "not resolution-availability time" in boundary
    assert "do not reconstruct immutable prior" in boundary
    assert "Event/group identity is unavailable" in boundary
    assert "write terminal question memory" in boundary


def test_financial_method_examples_remain_optional_and_fold_legal() -> None:
    """Financial ideas expand creativity without becoming mandatory defaults."""
    catalog = (ROOT / "docs/research-guidance/financial-machine-learning-ideas.md").read_text(
        encoding="utf-8"
    )
    combined = "\n".join(
        _read(skill, "references/principles.md")
        for skill in (
            "analyze-time-series-data",
            "design-time-series-feature-set",
            "review-backtest-gate",
        )
    )

    assert "optional research guidance" in catalog
    assert "Do not assemble every section into a canonical pipeline" in catalog
    assert "fit transformation parameters inside legal folds" in combined
    assert "No family is a default" in combined
    assert "Add embargo only for a named" in combined


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
