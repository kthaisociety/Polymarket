"""Contract tests for UserMandate -> ResearchTask compilation."""

from dataclasses import replace

import pytest

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
    TaskConfirmation,
    TaskPublisher,
    UserMandate,
)


def _calendar_months(count: int) -> TemporalOffset:
    return TemporalOffset.calendar(
        count=count,
        unit=CalendarUnit.MONTH,
        anchor=OffsetAnchor.EXACT_INPUT,
        month_end_policy=MonthEndPolicy.CLAMP,
        timezone_name="UTC",
        timezone_policy=TimezonePolicy.WALL_CLOCK_REJECT_TRANSITION,
    )


ONE_MONTH_HORIZON = _calendar_months(1)
TWO_MONTH_HORIZON = _calendar_months(2)
THREE_MONTH_HORIZON = _calendar_months(3)
TWELVE_MONTH_HORIZON = _calendar_months(12)
EXPLICIT_MANDATE_TEXT = (
    "Determine whether macroeconomic data helps predict monthly claim frequency "
    "three months ahead using the claims and macro datasets, while excluding "
    "protected holdout data."
)


def test_explicit_scientific_identity_and_constraints_are_preserved() -> None:
    """Compilation preserves every explicit part of the human's scientific problem."""
    mandate = UserMandate(
        original_text=EXPLICIT_MANDATE_TEXT,
        research_objective="Determine whether macroeconomic data predicts claim frequency.",
        target_field_id="claims.claim_frequency",
        forecast_horizon=THREE_MONTH_HORIZON,
        dataset_refs=("claims", "macro"),
        constraints=("exclude protected holdout data",),
    )
    environment = ResearchEnvironmentSummary(
        environment_id="environment-v1",
        available_field_ids=(
            "claims.claim_frequency",
            "claims.claim_severity",
            "claims.loss_ratio",
        ),
        available_dataset_refs=("claims", "macro"),
    )

    result = TaskCompiler().compile(mandate, environment)

    assert result.status is CompilationStatus.RESOLVED
    assert result.proposal is not None
    assert result.proposal.original_mandate == EXPLICIT_MANDATE_TEXT
    assert result.proposal.research_objective == mandate.research_objective
    assert result.proposal.target_field_id == "claims.claim_frequency"
    assert result.proposal.forecast_horizon == THREE_MONTH_HORIZON
    assert result.proposal.dataset_refs == ("claims", "macro")
    assert result.proposal.constraints == ("exclude protected holdout data",)
    assert result.proposal.environment_id == "environment-v1"
    assert "Original mandate" in result.proposal.readback


def test_missing_horizon_remains_explicitly_unresolved() -> None:
    """The compiler does not invent a forecast horizon absent from the mandate."""
    original_text = "See if macro data helps predict claims."
    mandate = UserMandate(
        original_text=original_text,
        research_objective="Determine whether macro data helps predict claims.",
        target_field_id="claims.claim_frequency",
        dataset_refs=("claims", "macro"),
    )
    environment = ResearchEnvironmentSummary(
        environment_id="environment-v1",
        available_field_ids=("claims.claim_frequency",),
        available_dataset_refs=("claims", "macro"),
    )

    result = TaskCompiler().compile(mandate, environment)

    assert result.status is CompilationStatus.PARTIALLY_RESOLVED
    assert result.proposal is not None
    assert result.proposal.original_mandate == original_text
    assert result.proposal.forecast_horizon is None
    assert "forecast_horizon" in result.unresolved_fields


def test_explicit_target_is_not_substituted_from_environment() -> None:
    """Nearby available fields cannot replace the target selected by the human."""
    mandate = UserMandate(
        original_text="Predict claim frequency three months ahead.",
        research_objective="Predict claim frequency.",
        target_field_id="claims.claim_frequency",
        forecast_horizon=THREE_MONTH_HORIZON,
        dataset_refs=("claims",),
    )
    environment = ResearchEnvironmentSummary(
        environment_id="environment-v1",
        available_field_ids=(
            "claims.loss_ratio",
            "claims.claim_severity",
            "claims.claim_frequency",
        ),
        available_dataset_refs=("claims",),
    )

    result = TaskCompiler().compile(mandate, environment)

    assert result.proposal is not None
    assert result.proposal.target_field_id == "claims.claim_frequency"


def test_later_environment_changes_do_not_rewrite_compiled_task_identity() -> None:
    """A compiled task retains the environment identity under which it was resolved."""
    mandate = UserMandate(
        original_text="Predict claim frequency three months ahead.",
        research_objective="Predict claim frequency.",
        target_field_id="claims.claim_frequency",
        forecast_horizon=THREE_MONTH_HORIZON,
        dataset_refs=("claims",),
    )
    environment_v1 = ResearchEnvironmentSummary(
        environment_id="environment-v1",
        available_field_ids=("claims.claim_frequency",),
        available_dataset_refs=("claims",),
    )

    proposal = TaskCompiler().compile(mandate, environment_v1).proposal
    environment_v2 = replace(
        environment_v1,
        environment_id="environment-v2",
        available_dataset_refs=("claims", "new-macro-dataset"),
    )

    assert proposal is not None
    assert environment_v2.environment_id == "environment-v2"
    assert proposal.environment_id == "environment-v1"
    assert proposal.dataset_refs == ("claims",)


def test_material_rescope_creates_new_version_with_parent_lineage() -> None:
    """Changing target and horizon creates a new task version without mutating its parent."""
    compiler = TaskCompiler()
    environment = ResearchEnvironmentSummary(
        environment_id="environment-v1",
        available_field_ids=(
            "claims.claim_frequency",
            "claims.claim_severity",
        ),
        available_dataset_refs=("claims",),
    )
    original = UserMandate(
        original_text="Predict claim frequency three months ahead.",
        research_objective="Predict claim frequency.",
        target_field_id="claims.claim_frequency",
        forecast_horizon=THREE_MONTH_HORIZON,
        dataset_refs=("claims",),
    )
    rescope = UserMandate(
        original_text="Instead predict claim severity twelve months ahead.",
        research_objective="Predict claim severity.",
        target_field_id="claims.claim_severity",
        forecast_horizon=TWELVE_MONTH_HORIZON,
        dataset_refs=("claims",),
    )

    first = compiler.compile(original, environment).proposal
    assert first is not None
    second = compiler.revise(first, rescope, environment).proposal

    assert second is not None
    assert second.proposal_id != first.proposal_id
    assert second.version == first.version + 1
    assert second.parent_proposal_id == first.proposal_id
    assert second.target_field_id == "claims.claim_severity"
    assert second.forecast_horizon == TWELVE_MONTH_HORIZON
    assert first.target_field_id == "claims.claim_frequency"
    assert first.forecast_horizon == THREE_MONTH_HORIZON


def test_exact_human_confirmation_is_required_and_idempotent() -> None:
    """Compilation alone is not authority; exact confirmation publishes once."""
    mandate = UserMandate(
        original_text="Inspect the toy dataset.",
        research_objective="Describe the authorized toy dataset.",
        target_field_id="target_value",
        forecast_horizon=ONE_MONTH_HORIZON,
        dataset_refs=("toy-monthly",),
    )
    environment = ResearchEnvironmentSummary(
        environment_id="environment-v1",
        available_field_ids=("target_value",),
        available_dataset_refs=("toy-monthly",),
    )
    proposal = TaskCompiler().compile(mandate, environment).proposal
    assert proposal is not None
    publisher = TaskPublisher()
    confirmation = TaskConfirmation(
        confirmation_id="confirm-1",
        proposal_id=proposal.proposal_id,
        proposal_version=proposal.version,
        semantic_digest=proposal.semantic_digest,
        approved=True,
    )

    first = publisher.confirm(proposal, confirmation)
    replay = publisher.confirm(proposal, confirmation)

    assert first.task is not None
    assert replay.task == first.task
    assert first.task.confirmed_proposal_id == proposal.proposal_id


def test_stale_confirmation_cannot_publish_changed_proposal() -> None:
    """Human authority cannot carry over to a materially changed proposal."""
    environment = ResearchEnvironmentSummary(
        environment_id="environment-v1",
        available_field_ids=("target_value",),
        available_dataset_refs=("toy-monthly",),
    )
    compiler = TaskCompiler()
    first = compiler.compile(
        UserMandate(
            "Inspect.", "Inspect toy.", "target_value", ONE_MONTH_HORIZON, ("toy-monthly",)
        ),
        environment,
    ).proposal
    assert first is not None
    second = compiler.revise(
        first,
        UserMandate(
            "Inspect later.",
            "Inspect toy later.",
            "target_value",
            TWO_MONTH_HORIZON,
            ("toy-monthly",),
        ),
        environment,
    ).proposal
    assert second is not None
    stale = TaskConfirmation(
        confirmation_id="confirm-stale",
        proposal_id=first.proposal_id,
        proposal_version=first.version,
        semantic_digest=first.semantic_digest,
        approved=True,
    )

    result = TaskPublisher().confirm(second, stale)

    assert result.task is None


def test_numeric_month_horizon_is_not_silently_converted() -> None:
    """Legacy numeric months require an explicit calendar-policy migration."""
    with pytest.raises(TypeError, match="TemporalOffset"):
        UserMandate("Predict.", "Predict target.", "target_value", 3)  # type: ignore[arg-type]
