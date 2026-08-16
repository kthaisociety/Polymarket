"""Explicit failure tests for task compilation."""

from research_agent.data_foundation import (
    CalendarUnit,
    MonthEndPolicy,
    OffsetAnchor,
    TemporalOffset,
    TimezonePolicy,
)
from research_agent.task_compilation import (
    CompilationStatus,
    ResearchEnvironmentSummary,
    TaskCompiler,
    UserMandate,
)


def test_unknown_resource_references_are_reported_as_unresolvable() -> None:
    """Invalid references fail explicitly instead of producing a plausible task."""
    mandate = UserMandate(
        original_text="Predict unknown claims from an unknown dataset.",
        research_objective="Predict an unavailable target.",
        target_field_id="claims.unknown_target",
        forecast_horizon=TemporalOffset.calendar(
            count=3,
            unit=CalendarUnit.MONTH,
            anchor=OffsetAnchor.EXACT_INPUT,
            month_end_policy=MonthEndPolicy.CLAMP,
            timezone_name="UTC",
            timezone_policy=TimezonePolicy.WALL_CLOCK_REJECT_TRANSITION,
        ),
        dataset_refs=("unknown-dataset",),
    )
    environment = ResearchEnvironmentSummary(
        environment_id="environment-v1",
        available_field_ids=("claims.claim_frequency",),
        available_dataset_refs=("claims",),
    )

    result = TaskCompiler().compile(mandate, environment)

    assert result.status is CompilationStatus.UNRESOLVABLE
    assert result.proposal is None
    assert result.invalid_references == (
        "dataset:unknown-dataset",
        "field:claims.unknown_target",
    )
