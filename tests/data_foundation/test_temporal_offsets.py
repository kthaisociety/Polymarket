"""Calendar/elapsed temporal identity and confirmed-task target binding adversaries."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from research_agent.data_foundation import (
    CalendarUnit,
    DatasetSchema,
    FieldDefinition,
    IncompleteOutcomePolicy,
    MaturityPolicy,
    MonthEndPolicy,
    OffsetAnchor,
    OutcomeAlignment,
    TargetDefinition,
    TargetKind,
    TemporalOffset,
    TimezonePolicy,
)
from research_agent.task_compilation import (
    ResearchEnvironmentSummary,
    ResearchTask,
    TaskCompiler,
    TaskConfirmation,
    TaskPublisher,
    UserMandate,
)


def _calendar(
    count: int,
    unit: CalendarUnit,
    *,
    month_end: MonthEndPolicy,
    timezone_name: str = "UTC",
    timezone_policy: TimezonePolicy = TimezonePolicy.WALL_CLOCK_REJECT_TRANSITION,
) -> TemporalOffset:
    return TemporalOffset.calendar(
        count=count,
        unit=unit,
        anchor=OffsetAnchor.EXACT_INPUT,
        month_end_policy=month_end,
        timezone_name=timezone_name,
        timezone_policy=timezone_policy,
    )


def _confirmed_task(horizon: TemporalOffset | None) -> ResearchTask:
    mandate = UserMandate(
        original_text="Predict the target one calendar quarter ahead.",
        research_objective="Predict the exact target.",
        target_field_id="target",
        forecast_horizon=horizon,
        dataset_refs=("dataset",),
    )
    environment = ResearchEnvironmentSummary(
        environment_id="environment-v1",
        available_field_ids=("target",),
        available_dataset_refs=("dataset",),
    )
    proposal = TaskCompiler().compile(mandate, environment).proposal
    assert proposal is not None
    result = TaskPublisher().confirm(
        proposal,
        TaskConfirmation(
            confirmation_id="confirmation",
            proposal_id=proposal.proposal_id,
            proposal_version=proposal.version,
            semantic_digest=proposal.semantic_digest,
            approved=True,
        ),
    )
    assert result.task is not None
    return result.task


def _schema() -> DatasetSchema:
    return DatasetSchema(
        dataset_id="dataset",
        version="schema-v1",
        environment_id="environment-v1",
        provenance_ref="schema-provenance",
        fields=(FieldDefinition("target", "Target", "float", "count", (), "Target value."),),
    )


def test_calendar_month_end_policies_are_explicit_and_do_not_drift() -> None:
    """Jan 31 and leap-day behavior follows the identity-bearing declared policy."""
    utc = ZoneInfo("UTC")
    january_end = datetime(2024, 1, 31, 9, 15, tzinfo=utc)
    clamp = _calendar(1, CalendarUnit.MONTH, month_end=MonthEndPolicy.CLAMP)
    preserve = _calendar(1, CalendarUnit.MONTH, month_end=MonthEndPolicy.PRESERVE)
    reject = _calendar(1, CalendarUnit.MONTH, month_end=MonthEndPolicy.REJECT)

    assert clamp.apply(january_end) == datetime(2024, 2, 29, 9, 15, tzinfo=utc)
    assert preserve.apply(january_end) == datetime(2024, 2, 29, 9, 15, tzinfo=utc)
    assert preserve.apply(datetime(2024, 2, 29, 9, 15, tzinfo=utc)) == datetime(
        2024, 3, 31, 9, 15, tzinfo=utc
    )
    assert clamp.apply(datetime(2024, 2, 29, 9, 15, tzinfo=utc)) == datetime(
        2024, 3, 29, 9, 15, tzinfo=utc
    )
    calendar_year = _calendar(12, CalendarUnit.MONTH, month_end=MonthEndPolicy.PRESERVE)
    assert calendar_year.apply(datetime(2024, 2, 29, 9, 15, tzinfo=utc)) == datetime(
        2025, 2, 28, 9, 15, tzinfo=utc
    )
    with pytest.raises(ValueError, match="month-end"):
        reject.apply(january_end)
    policy_count = 3
    assert len({clamp.identity, preserve.identity, reject.identity}) == policy_count


def test_calendar_quarter_is_not_a_ninety_day_approximation() -> None:
    """Quarter identity and endpoints retain calendar meaning across unequal quarters."""
    utc = ZoneInfo("UTC")
    quarter = _calendar(1, CalendarUnit.QUARTER, month_end=MonthEndPolicy.PRESERVE)
    ninety_days = TemporalOffset.elapsed(timedelta(days=90))

    assert quarter.identity != ninety_days.identity
    assert quarter.apply(datetime(2024, 7, 31, tzinfo=utc)) == datetime(2024, 10, 31, tzinfo=utc)
    assert ninety_days.apply(datetime(2024, 7, 31, tzinfo=utc)) == datetime(
        2024, 10, 29, tzinfo=utc
    )
    clamp_quarter = _calendar(1, CalendarUnit.QUARTER, month_end=MonthEndPolicy.CLAMP)
    april_quarter_days = 91
    july_quarter_days = 92
    assert (
        clamp_quarter.apply(datetime(2024, 4, 30, tzinfo=utc)) - datetime(2024, 4, 30, tzinfo=utc)
    ).days == april_quarter_days
    assert (
        quarter.apply(datetime(2024, 7, 31, tzinfo=utc)) - datetime(2024, 7, 31, tzinfo=utc)
    ).days == july_quarter_days


def test_elapsed_and_calendar_timezone_semantics_diverge_at_dst() -> None:
    """Elapsed time advances on the UTC timeline; calendar time validates local DST state."""
    stockholm = ZoneInfo("Europe/Stockholm")
    elapsed_day = TemporalOffset.elapsed(timedelta(days=1))
    before_spring = datetime(2024, 3, 30, 12, tzinfo=stockholm)
    assert elapsed_day.apply(before_spring) == datetime(2024, 3, 31, 13, tzinfo=stockholm)

    into_gap = _calendar(
        2,
        CalendarUnit.MONTH,
        month_end=MonthEndPolicy.CLAMP,
        timezone_name="Europe/Stockholm",
    )
    with pytest.raises(ValueError, match="nonexistent or ambiguous"):
        into_gap.apply(datetime(2024, 1, 31, 2, 30, tzinfo=stockholm))
    with pytest.raises(ValueError, match="timezone"):
        into_gap.apply(datetime(2024, 1, 31, 2, 30, tzinfo=UTC))
    into_ambiguous_hour = _calendar(
        2,
        CalendarUnit.MONTH,
        month_end=MonthEndPolicy.CLAMP,
        timezone_name="Europe/Stockholm",
    )
    with pytest.raises(ValueError, match="nonexistent or ambiguous"):
        into_ambiguous_hour.apply(datetime(2024, 8, 27, 2, 30, tzinfo=stockholm))
    preserve_fold = _calendar(
        2,
        CalendarUnit.MONTH,
        month_end=MonthEndPolicy.CLAMP,
        timezone_name="Europe/Stockholm",
        timezone_policy=TimezonePolicy.WALL_CLOCK_PRESERVE_FOLD,
    )
    resolved = preserve_fold.apply(datetime(2024, 8, 27, 2, 30, tzinfo=stockholm))
    assert resolved == datetime(2024, 10, 27, 2, 30, tzinfo=stockholm, fold=0)
    assert preserve_fold.identity != into_ambiguous_hour.identity


def test_offset_identity_changes_with_calendar_unit_timezone_or_policy() -> None:
    """A meaning mutation cannot retain temporal identity."""
    base = _calendar(3, CalendarUnit.MONTH, month_end=MonthEndPolicy.CLAMP)
    variants = (
        _calendar(1, CalendarUnit.QUARTER, month_end=MonthEndPolicy.CLAMP),
        _calendar(3, CalendarUnit.MONTH, month_end=MonthEndPolicy.PRESERVE),
        _calendar(
            3,
            CalendarUnit.MONTH,
            month_end=MonthEndPolicy.CLAMP,
            timezone_name="Europe/Stockholm",
        ),
    )
    assert all(item.identity != base.identity for item in variants)
    with pytest.raises((TypeError, ValueError)):
        replace(base, calendar_count=1, calendar_unit=None)
    with pytest.raises(TypeError, match="exact enum"):
        replace(base, month_end_policy="clamp")  # type: ignore[arg-type]


def test_confirmed_task_horizon_binds_exact_target_identity_and_interval() -> None:
    """TargetDefinition consumes the exact confirmed horizon without conversion or default."""
    horizon = _calendar(1, CalendarUnit.QUARTER, month_end=MonthEndPolicy.PRESERVE)
    task = _confirmed_task(horizon)
    schema = _schema()
    target = TargetDefinition.from_confirmed_task(
        task,
        field_ref=schema.field_ref("target"),
        version=1,
        parent_target_id=None,
        kind=TargetKind.ENDPOINT,
        outcome_start_offset=TemporalOffset.zero(),
        alignment=OutcomeAlignment.EXACT,
        path_reduction=None,
        event_condition=None,
        maturity_delay=TemporalOffset.zero(),
        maturity_policy=MaturityPolicy.FULL_INTERVAL,
        required_observation_count=1,
        value_encoding="continuous",
        units="count",
        censoring_policy="none",
        incomplete_outcome_policy=IncompleteOutcomePolicy.EXCLUDE,
        schema_provenance_ref="schema-provenance",
        provenance_refs=("target-resolution",),
    )

    assert target.horizon is horizon
    assert target.confirmed_task_horizon_id == horizon.identity
    assert target.task_semantic_digest == task.semantic_digest
    assert target.interval(datetime(2024, 1, 31, tzinfo=ZoneInfo("UTC"))) == (
        datetime(2024, 1, 31, tzinfo=ZoneInfo("UTC")),
        datetime(2024, 4, 30, tzinfo=ZoneInfo("UTC")),
    )
    substituted = TemporalOffset.elapsed(timedelta(days=90))
    with pytest.raises(ValueError, match="confirmed task horizon"):
        replace(target, horizon=substituted, outcome_end_offset=substituted)


def test_unresolved_task_horizon_cannot_publish_target() -> None:
    """Target formalization does not choose a horizon for the confirmed human mission."""
    task = _confirmed_task(None)
    schema = _schema()
    with pytest.raises(ValueError, match="unresolved horizon"):
        TargetDefinition.from_confirmed_task(
            task,
            field_ref=schema.field_ref("target"),
            version=1,
            parent_target_id=None,
            kind=TargetKind.ENDPOINT,
            outcome_start_offset=TemporalOffset.zero(),
            alignment=OutcomeAlignment.EXACT,
            path_reduction=None,
            event_condition=None,
            maturity_delay=TemporalOffset.zero(),
            maturity_policy=MaturityPolicy.FULL_INTERVAL,
            required_observation_count=1,
            value_encoding="continuous",
            units="count",
            censoring_policy="none",
            incomplete_outcome_policy=IncompleteOutcomePolicy.EXCLUDE,
            schema_provenance_ref="schema-provenance",
            provenance_refs=("target-resolution",),
        )
