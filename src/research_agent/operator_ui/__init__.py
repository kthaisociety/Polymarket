"""Read-only operator projection for research questions and reports."""

from research_agent.operator_ui.projection import (
    ProjectionError,
    ResearchLibraryProjection,
    build_research_library,
)
from research_agent.operator_ui.server import ResearchLibraryServer, serve_research_library

__all__ = [
    "ProjectionError",
    "ResearchLibraryProjection",
    "ResearchLibraryServer",
    "build_research_library",
    "serve_research_library",
]
