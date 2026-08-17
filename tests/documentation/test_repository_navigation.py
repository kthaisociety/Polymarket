"""Regression checks for the GitHub-facing visual documentation map."""

import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
DOCS_README = ROOT / "docs" / "README.md"
ARCHITECTURE = ROOT / "docs" / "architecture"
EXPECTED_ROOT_MERMAID_BLOCKS = 4
EXPECTED_ROOT_FENCE_MARKERS = 16
BLOCKS = (
    "mission",
    "runtime",
    "data-foundation",
    "exploration",
    "autonomous-investigation",
    "formalization",
    "development",
    "protected-evaluation",
    "reporting",
    "operator-interface",
    "learning",
    "orchestration",
)


def _local_links(markdown: str) -> tuple[str, ...]:
    targets = re.findall(r"(?<!!)\[[^]]+\]\(([^)]+)\)", markdown)
    return tuple(
        unquote(target.split("#", maxsplit=1)[0])
        for target in targets
        if target and "://" not in target and not target.startswith(("mailto:", "#"))
    )


def test_root_readme_is_a_renderable_visual_entry_point() -> None:
    """The GitHub landing page must expose diagrams before deep specification reading."""
    content = README.read_text(encoding="utf-8")

    assert content.count("```mermaid") == EXPECTED_ROOT_MERMAID_BLOCKS
    assert content.count("```") == EXPECTED_ROOT_FENCE_MARKERS
    assert 'FREEZE{"Independent freeze assessment"}' in content
    assert 'GOVERNANCE{"Protected-data governance"}' in content
    assert 'VALIDATOR{"Independent validation"}' in content
    assert "development evidence" in content
    assert "A true backtest is a separate protected" in content


def test_root_readme_local_links_resolve() -> None:
    """Every local entry-point link must reach a current file or directory."""
    for target in _local_links(README.read_text(encoding="utf-8")):
        assert (ROOT / target).exists(), target


def test_docs_index_bounds_context_and_classifies_records() -> None:
    """The documentation entry point prevents historical records becoming default context."""
    content = DOCS_README.read_text(encoding="utf-8")

    assert "Do not bulk-load `docs/`" in content
    assert "Canonical authority" in content
    assert "Historical/provisional" in content
    assert "not replacement authority" in content
    assert "$start-polymarket-research" in content
    for target in _local_links(content):
        assert (DOCS_README.parent / target).exists(), target


def test_active_skill_copy_uses_chronos_identity() -> None:
    """Vendored Insurance wording cannot remain in active skill metadata."""
    active = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            ROOT / ".agents/skills/execute-work-packet/SKILL.md",
            ROOT / ".agents/skills/fundamentals-review/SKILL.md",
            ROOT / ".agents/skills/fundamentals-review/references/project-fundamentals.md",
            ROOT / ".agents/skills/fundamentals-review/agents/openai.yaml",
        )
    )

    assert "Chronos" in active
    assert "Insurance project" not in active
    assert "Insurance architectural" not in active


def test_every_linked_architecture_block_starts_with_mermaid() -> None:
    """A contributor can understand each block visually before reading implementation detail."""
    for block in BLOCKS:
        content = (ARCHITECTURE / block / "README.md").read_text(encoding="utf-8")
        assert "```mermaid" in content, block


def test_completed_migration_and_legacy_archive_are_absent() -> None:
    """Superseded code and migration scaffolding cannot look current on GitHub."""
    assert not (ROOT / "archive").exists()
    assert not (ARCHITECTURE / "RESTRUCTURE_PLAN.md").exists()
    assert not (ARCHITECTURE / "TRANSITION_CATALOG.md").exists()
    architecture = (ARCHITECTURE / "README.md").read_text(encoding="utf-8")
    assert "review architecture and migration" not in architecture
    assert "Numeric `Sxxx`" not in architecture


def test_landing_page_does_not_restore_outdated_handoff_copy() -> None:
    """The root page describes the current executable product instead of milestone-one plans."""
    content = README.read_text(encoding="utf-8")

    assert "Read these files in this order" not in content
    assert "First build target" not in content
    assert "does **not** yet load" not in content
    assert "does not yet perform autonomous feature discovery" not in content
