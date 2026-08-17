"""Harness-owned matching for explicitly declared contextual histories."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from research_agent.data_foundation.information import InformationSet
    from research_agent.data_foundation.observations import RegisteredObservation
    from research_agent.investigation.records import ContextHistoryDependency


def matching_context_observations(
    information: InformationSet,
    dependencies: tuple[ContextHistoryDependency, ...],
    sample_dimensions: tuple[tuple[str, str], ...],
    decision_time: datetime,
) -> dict[str, tuple[RegisteredObservation, ...]]:
    """Match context rows on only the manifest-declared sample dimensions."""
    sample = dict(sample_dimensions)
    return {
        dependency.field.field_id: tuple(
            item
            for item in information.for_field(dependency.field)
            if item.reference_time <= decision_time
            and all(
                dict(item.dimensions).get(name) == sample[name]
                for name in dependency.match_dimension_names
            )
        )
        for dependency in dependencies
    }


__all__ = ["matching_context_observations"]
