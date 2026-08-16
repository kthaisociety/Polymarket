"""Typed fixtures for the Milestone 1 runtime tests."""

from research_agent.data_foundation import (
    CalendarUnit,
    MonthEndPolicy,
    OffsetAnchor,
    TemporalOffset,
    TimezonePolicy,
)
from research_agent.runtime.initialization import ResearchRuntimeInitializer
from research_agent.runtime.models import ResearchEnvironmentSnapshot, RuntimeInitialization
from research_agent.runtime.store import InMemoryRuntimeStore
from research_agent.task_compilation import (
    ResearchEnvironmentSummary,
    ResearchTask,
    TaskCompiler,
    TaskConfirmation,
    TaskPublisher,
    UserMandate,
)


def confirmed_toy_task(
    *,
    objective: str = "Describe the authorized toy dataset.",
    constraints: tuple[str, ...] = (),
) -> ResearchTask:
    """Create a task only through compile, readback, and exact confirmation."""
    proposal = (
        TaskCompiler()
        .compile(
            UserMandate(
                original_text="Inspect the toy monthly dataset and describe its structure.",
                research_objective=objective,
                target_field_id="target_value",
                forecast_horizon=TemporalOffset.calendar(
                    count=1,
                    unit=CalendarUnit.MONTH,
                    anchor=OffsetAnchor.EXACT_INPUT,
                    month_end_policy=MonthEndPolicy.CLAMP,
                    timezone_name="UTC",
                    timezone_policy=TimezonePolicy.WALL_CLOCK_REJECT_TRANSITION,
                ),
                dataset_refs=("toy-monthly",),
                constraints=constraints,
            ),
            ResearchEnvironmentSummary(
                environment_id="environment-v1",
                available_field_ids=("target_value", "predictor_value"),
                available_dataset_refs=("toy-monthly",),
            ),
        )
        .proposal
    )
    assert proposal is not None
    result = TaskPublisher().confirm(
        proposal,
        TaskConfirmation(
            confirmation_id=f"confirmation:{proposal.proposal_id}",
            proposal_id=proposal.proposal_id,
            proposal_version=proposal.version,
            semantic_digest=proposal.semantic_digest,
            approved=True,
        ),
    )
    assert result.task is not None
    return result.task


def toy_environment(*, readable: bool = True) -> ResearchEnvironmentSnapshot:
    """Create exact authority for the deterministic toy dataset."""
    return ResearchEnvironmentSnapshot(
        environment_id="environment-v1",
        version=1,
        dataset_refs=("toy-monthly",),
        readable_dataset_refs=("toy-monthly",) if readable else (),
        capability_names=("inspect_dataset",),
        warnings=("Milestone 1 does not establish temporal legality.",),
    )


def initialized_runtime(
    *,
    request_id: str = "initialize-1",
    readable: bool = True,
) -> tuple[InMemoryRuntimeStore, RuntimeInitialization]:
    """Initialize one complete task/environment attempt."""
    store = InMemoryRuntimeStore()
    initialization = ResearchRuntimeInitializer(store).initialize(
        confirmed_toy_task(),
        toy_environment(readable=readable),
        request_id=request_id,
    )
    return store, initialization
