"""Smoke tests for the source package."""

from importlib import import_module


def test_source_package_imports() -> None:
    """The configured source package is importable."""
    assert import_module("research_agent").__name__ == "research_agent"
