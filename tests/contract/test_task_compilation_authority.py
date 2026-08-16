"""Authority-boundary tests for deterministic task compilation."""

from dataclasses import replace

from research_agent.data_foundation import (
    CalendarUnit,
    MonthEndPolicy,
    OffsetAnchor,
    TemporalOffset,
    TimezonePolicy,
)
from research_agent.task_compilation import (
    ResearchEnvironmentSummary,
    TaskCompiler,
    UserMandate,
)


def test_compilation_uses_metadata_without_mutating_its_inputs() -> None:
    """Compilation receives metadata, not providers, datasets, or protected values."""
    mandate = UserMandate(
        original_text="Predict claim frequency three months ahead.",
        research_objective="Predict claim frequency.",
        target_field_id="claims.claim_frequency",
        forecast_horizon=TemporalOffset.calendar(
            count=3,
            unit=CalendarUnit.MONTH,
            anchor=OffsetAnchor.EXACT_INPUT,
            month_end_policy=MonthEndPolicy.CLAMP,
            timezone_name="UTC",
            timezone_policy=TimezonePolicy.WALL_CLOCK_REJECT_TRANSITION,
        ),
        dataset_refs=("claims",),
    )
    environment = ResearchEnvironmentSummary(
        environment_id="environment-v1",
        available_field_ids=("claims.claim_frequency",),
        available_dataset_refs=("claims",),
        protected_resource_refs=("holdout-h1",),
    )
    mandate_before = replace(mandate)
    environment_before = replace(environment)

    result = TaskCompiler().compile(mandate, environment)

    assert result.proposal is not None
    assert mandate == mandate_before
    assert environment == environment_before
    assert result.proposal.environment_id == "environment-v1"
    assert "holdout-h1" not in repr(result.proposal)
