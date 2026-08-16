"""Deterministic and adversarial tests for the temporal scientific data boundary."""

# pyright: reportMissingImports=false, reportUnknownMemberType=false

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from research_agent.data_foundation import (
    BoundaryStatus,
    Comparison,
    DataCatalogSnapshot,
    DatasetSchema,
    EventCondition,
    FieldDefinition,
    IncompleteOutcomePolicy,
    InformationSetBuilder,
    MaturityPolicy,
    MissingnessPolicy,
    ObservationInput,
    ObservationRegistrar,
    OutcomeAlignment,
    PathReduction,
    SampleKey,
    StateAggregation,
    StateConditionedThreshold,
    TargetDefinition,
    TargetKind,
    TemporalOffset,
    TrainingSample,
    TrainingSampleBuilder,
    TrainingWindowPolicy,
    TrainingWindowSelector,
    WindowKind,
)

DAY = timedelta(days=1)
ELAPSED_DAY = TemporalOffset.elapsed(DAY)
ZERO_OFFSET = TemporalOffset.zero()
ORIGIN = datetime(2024, 1, 1, tzinfo=UTC)


def _schema(
    *,
    environment_id: str = "environment-v1",
    dimensions: tuple[str, ...] = (),
) -> DatasetSchema:
    return DatasetSchema(
        dataset_id="series",
        version="schema-v1",
        environment_id=environment_id,
        provenance_ref="artifact:schema-source-v1",
        fields=(
            FieldDefinition(
                field_id="predictor",
                semantic_name="Predictor signal",
                data_type="float",
                unit="index",
                dimensions=dimensions,
                description="A domain-neutral predictor.",
            ),
            FieldDefinition(
                field_id="outcome",
                semantic_name="Observed outcome",
                data_type="float",
                unit="units",
                dimensions=dimensions,
                description="A domain-neutral target path.",
            ),
            FieldDefinition(
                field_id="state",
                semantic_name="Decision-time scale",
                data_type="float",
                unit="units",
                dimensions=dimensions,
                description="Trailing state used by an explicit target rule.",
            ),
        ),
    )


def _row(  # noqa: PLR0913
    schema: DatasetSchema,
    field_id: str,
    value: float,
    reference_day: int,
    available_day: int,
    *,
    vintage: str = "initial",
    revision: int = 0,
    dimensions: tuple[tuple[str, str], ...] = (),
) -> ObservationInput:
    return ObservationInput(
        field_ref=schema.field_ref(field_id),
        value=value,
        reference_time=ORIGIN + DAY * reference_day,
        available_at=ORIGIN + DAY * available_day,
        vintage_id=vintage,
        revision_number=revision,
        source_ref="source:fixture",
        provenance_ref=f"artifact:{field_id}:{vintage}:{reference_day}",
        availability_rule_version="release-rule-v1",
        dimensions=dimensions,
    )


def _catalog(schema: DatasetSchema, *rows: ObservationInput) -> DataCatalogSnapshot:
    registered = ObservationRegistrar().register(schema, tuple(rows))
    return DataCatalogSnapshot(schema.environment_id, (registered,))


def _target(  # noqa: PLR0913
    schema: DatasetSchema,
    *,
    kind: TargetKind = TargetKind.ENDPOINT,
    horizon_days: int = 2,
    maturity_delay_days: int = 0,
    required_observations: int = 1,
    path_reduction: PathReduction | None = None,
    event_condition: EventCondition | None = None,
    maturity_policy: MaturityPolicy = MaturityPolicy.FULL_INTERVAL,
) -> TargetDefinition:
    horizon = TemporalOffset.elapsed(DAY * horizon_days)
    return TargetDefinition(
        task_id="task-v1",
        task_version=1,
        task_semantic_digest="task-semantic-v1",
        confirmed_task_horizon_id=horizon.identity,
        version=1,
        parent_target_id=None,
        field_ref=schema.field_ref("outcome"),
        kind=kind,
        horizon=horizon,
        outcome_start_offset=ZERO_OFFSET,
        outcome_end_offset=horizon,
        alignment=OutcomeAlignment.EXACT,
        path_reduction=path_reduction,
        event_condition=event_condition,
        maturity_delay=TemporalOffset.elapsed(DAY * maturity_delay_days),
        maturity_policy=maturity_policy,
        required_observation_count=required_observations,
        value_encoding="numeric" if kind is not TargetKind.EVENT else "boolean",
        units="units" if kind is not TargetKind.EVENT else "event",
        censoring_policy="complete declared interval",
        incomplete_outcome_policy=IncompleteOutcomePolicy.EXCLUDE,
        environment_id=schema.environment_id,
        schema_provenance_ref=schema.provenance_ref,
        provenance_refs=("research:target-resolution-v1",),
    )


def _sample(
    catalog: DataCatalogSnapshot,
    target: TargetDefinition,
    *,
    current_day: int,
    decision_days: tuple[int, ...] = (0,),
) -> TrainingSample:
    return TrainingSampleBuilder().build(
        catalog,
        target=target,
        predictor_fields=(catalog.datasets[0].schema.field_ref("predictor"),),
        candidate_decision_times=tuple(ORIGIN + DAY * day for day in decision_days),
        current_time=ORIGIN + DAY * current_day,
        missingness_policy=MissingnessPolicy.EXCLUDE_EXAMPLE,
    )


def test_schema_field_and_environment_provenance_are_stable() -> None:
    """Scientific identity includes schema and environment rather than a physical path."""
    schema = _schema()
    same = _schema()
    other_environment = _schema(environment_id="environment-v2")

    assert schema.identity == same.identity
    assert schema.field_ref("predictor") == same.field_ref("predictor")
    assert schema.identity != other_environment.identity
    assert (
        schema.field_ref("predictor").identity != other_environment.field_ref("predictor").identity
    )
    with pytest.raises(KeyError, match="different environment"):
        _catalog(schema).resolve_schema(other_environment.field_ref("predictor"))


def test_catalog_rejects_cross_environment_registration() -> None:
    """A current environment cannot silently reinterpret historical registrations."""
    schema = _schema()
    registration = ObservationRegistrar().register(schema, ())

    with pytest.raises(ValueError, match="cannot mix environment"):
        DataCatalogSnapshot("environment-v2", (registration,))


def test_publication_delay_and_as_known_vintage_control_information_membership() -> None:
    """Reference time cannot stand in for availability, and revisions do not backfill history."""
    schema = _schema()
    field = schema.field_ref("predictor")
    catalog = _catalog(
        schema,
        _row(schema, "predictor", 1.0, 0, 3),
        _row(schema, "predictor", 2.0, 0, 5, vintage="revision", revision=1),
    )
    builder = InformationSetBuilder()

    before_release = builder.build(
        catalog,
        decision_time=ORIGIN + DAY * 2,
        requested_fields=(field,),
    )
    initial = builder.build(
        catalog,
        decision_time=ORIGIN + DAY * 4,
        requested_fields=(field,),
    )
    revised = builder.build(
        catalog,
        decision_time=ORIGIN + DAY * 5,
        requested_fields=(field,),
    )

    assert before_release.status is BoundaryStatus.INSUFFICIENT
    assert before_release.observations == ()
    assert tuple(item.value for item in initial.observations) == (1.0,)
    assert tuple(item.vintage_id for item in initial.observations) == ("initial",)
    assert initial.observations[0].reference_time == ORIGIN
    assert initial.observations[0].available_at == ORIGIN + DAY * 3
    assert initial.observations[0].provenance_ref == "artifact:predictor:initial:0"
    assert tuple(item.value for item in revised.observations) == (2.0,)
    assert tuple(item.vintage_id for item in revised.observations) == ("revision",)


def test_endpoint_and_path_targets_have_distinct_identity_and_outcomes() -> None:
    """Equal endpoints do not erase within-horizon path meaning."""
    schema = _schema()
    catalog = _catalog(
        schema,
        _row(schema, "predictor", 3.0, -1, -1),
        _row(schema, "outcome", 10.0, 1, 1),
        _row(schema, "outcome", 1.0, 2, 2),
    )
    endpoint = _target(schema)
    path = _target(
        schema,
        kind=TargetKind.PATH,
        path_reduction=PathReduction.MAXIMUM,
        required_observations=2,
    )

    endpoint_sample = _sample(catalog, endpoint, current_day=3)
    path_sample = _sample(catalog, path, current_day=3)

    assert endpoint.identity != path.identity
    assert endpoint_sample.rows[0].label == 1.0
    expected_path_maximum = 10.0
    assert path_sample.rows[0].label == expected_path_maximum


def test_label_waits_for_declared_maturity_after_endpoint_exists() -> None:
    """An observed endpoint remains outside S_t until TargetDefinition says it is mature."""
    schema = _schema()
    catalog = _catalog(
        schema,
        _row(schema, "predictor", 3.0, -1, -1),
        _row(schema, "outcome", 5.0, 2, 2),
    )
    target = _target(schema, maturity_delay_days=2)

    early = _sample(catalog, target, current_day=3)
    mature = _sample(catalog, target, current_day=4)

    assert early.status is BoundaryStatus.INSUFFICIENT
    assert early.rows == ()
    assert "immature" in early.exclusions[0]
    assert mature.status is BoundaryStatus.READY
    assert mature.rows[0].label_matured_at == ORIGIN + DAY * 4


def test_predictor_release_and_label_maturity_advance_independently() -> None:
    """A predictor-only event changes I_t before a later label-only change to S_t."""
    schema = _schema()
    predictor = schema.field_ref("predictor")
    catalog = _catalog(
        schema,
        _row(schema, "predictor", 1.0, -1, -1),
        _row(schema, "predictor", 2.0, 0, 1),
        _row(schema, "outcome", 7.0, 2, 3),
    )
    target = _target(schema)
    information_builder = InformationSetBuilder()

    before_predictor = information_builder.build(
        catalog,
        decision_time=ORIGIN,
        requested_fields=(predictor,),
    )
    after_predictor = information_builder.build(
        catalog,
        decision_time=ORIGIN + DAY,
        requested_fields=(predictor,),
    )
    sample_after_predictor = _sample(catalog, target, current_day=1)
    sample_after_label = _sample(catalog, target, current_day=3)

    assert len(before_predictor.observations) == 1
    expected_released_predictors = 2
    assert len(after_predictor.observations) == expected_released_predictors
    assert sample_after_predictor.rows == ()
    assert len(sample_after_label.rows) == 1


def test_future_aware_state_conditioned_target_rule_is_rejected() -> None:
    """A target cannot disguise post-decision state as a local threshold."""
    schema = _schema()

    with pytest.raises(ValueError, match="cannot inspect after decision time"):
        StateConditionedThreshold(
            field_ref=schema.field_ref("state"),
            lookback=TemporalOffset.elapsed(DAY * 5),
            as_of_offset=ELAPSED_DAY,
            aggregation=StateAggregation.MEAN,
            multiplier=1.0,
            additive=0.0,
        )


def test_state_conditioned_target_ignores_future_scale_shift() -> None:
    """The threshold sees legal trailing state, never a later regime shift."""
    schema = _schema()
    state_rule = StateConditionedThreshold(
        field_ref=schema.field_ref("state"),
        lookback=TemporalOffset.elapsed(DAY * 5),
        as_of_offset=ZERO_OFFSET,
        aggregation=StateAggregation.MEAN,
        multiplier=1.0,
        additive=0.0,
    )
    target = _target(
        schema,
        kind=TargetKind.EVENT,
        event_condition=EventCondition(Comparison.GREATER_THAN, None, state_rule),
    )
    catalog = _catalog(
        schema,
        _row(schema, "predictor", 1.0, -1, -1),
        _row(schema, "state", 10.0, -1, -1),
        _row(schema, "state", 1_000.0, 1, 1),
        _row(schema, "outcome", 15.0, 2, 2),
    )

    sample = _sample(catalog, target, current_day=3)

    assert sample.rows[0].label is True


def test_event_maturity_policy_can_declare_early_completion() -> None:
    """An observed event matures early only when the target identity explicitly permits it."""
    schema = _schema()
    condition = EventCondition(Comparison.GREATER_THAN, 10.0, None)
    full_interval = _target(
        schema,
        kind=TargetKind.EVENT,
        event_condition=condition,
    )
    event_or_end = _target(
        schema,
        kind=TargetKind.EVENT,
        event_condition=condition,
        maturity_policy=MaturityPolicy.EVENT_OR_INTERVAL_END,
    )
    catalog = _catalog(
        schema,
        _row(schema, "predictor", 1.0, -1, -1),
        _row(schema, "outcome", 15.0, 1, 1),
    )

    still_open = _sample(catalog, full_interval, current_day=1)
    completed_event = _sample(catalog, event_or_end, current_day=1)

    assert full_interval.identity != event_or_end.identity
    assert still_open.status is BoundaryStatus.INSUFFICIENT
    assert completed_event.rows[0].label is True
    assert completed_event.rows[0].label_matured_at == ORIGIN + DAY


def test_missing_predictor_and_insufficient_window_fail_explicitly() -> None:
    """Neither sample nor window machinery silently repairs insufficient input."""
    schema = _schema()
    catalog = _catalog(schema, _row(schema, "outcome", 5.0, 2, 2))
    sample = _sample(catalog, _target(schema), current_day=3)
    policy = TrainingWindowPolicy(
        version=1,
        kind=WindowKind.ROLLING,
        minimum_samples=2,
        maximum_samples=3,
        provenance_ref="research:window-v1",
    )

    window = TrainingWindowSelector().select(sample, policy)

    assert sample.status is BoundaryStatus.INSUFFICIENT
    assert "missing legal predictor" in sample.exclusions[0]
    assert window.status is BoundaryStatus.INSUFFICIENT
    assert window.rows == ()
    assert window.insufficiency == "requires 2 samples but only 0 are legal"


def test_rolling_and_expanding_windows_select_exact_declared_rows() -> None:
    """Window selection is deterministic and never substitutes one policy for another."""
    schema = _schema()
    catalog = _catalog(
        schema,
        _row(schema, "predictor", 1.0, -3, -3),
        _row(schema, "outcome", 3.0, 0, 0),
        _row(schema, "outcome", 4.0, 1, 1),
        _row(schema, "outcome", 5.0, 2, 2),
    )
    sample = _sample(catalog, _target(schema), current_day=3, decision_days=(-2, -1, 0))
    expanding = TrainingWindowPolicy(
        version=1,
        kind=WindowKind.EXPANDING,
        minimum_samples=2,
        maximum_samples=None,
        provenance_ref="research:expanding-v1",
    )
    rolling = TrainingWindowPolicy(
        version=1,
        kind=WindowKind.ROLLING,
        minimum_samples=2,
        maximum_samples=2,
        provenance_ref="research:rolling-v1",
    )

    expanding_window = TrainingWindowSelector().select(sample, expanding)
    rolling_window = TrainingWindowSelector().select(sample, rolling)

    assert expanding_window.status is BoundaryStatus.READY
    assert tuple(row.decision_time for row in expanding_window.rows) == (
        ORIGIN - DAY * 2,
        ORIGIN - DAY,
        ORIGIN,
    )
    assert tuple(row.decision_time for row in rolling_window.rows) == (
        ORIGIN - DAY,
        ORIGIN,
    )


def test_target_meaning_change_creates_new_identity_without_mutating_parent() -> None:
    """Maturity and outcome semantics participate in immutable target identity."""
    schema = _schema()
    original = _target(schema)
    revised = replace(
        original,
        version=2,
        parent_target_id=original.identity,
        maturity_delay=ELAPSED_DAY,
    )

    assert revised.identity != original.identity
    assert revised.parent_target_id == original.identity
    assert original.maturity_delay == ZERO_OFFSET


def test_incomplete_fail_policy_blocks_the_entire_sample() -> None:
    """A FAIL target cannot silently keep the complete subset of requested examples."""
    schema = _schema()
    catalog = _catalog(
        schema,
        _row(schema, "predictor", 1.0, -3, -3),
        _row(schema, "outcome", 4.0, 1, 1),
    )
    target = replace(
        _target(schema),
        incomplete_outcome_policy=IncompleteOutcomePolicy.FAIL,
    )

    sample = _sample(catalog, target, current_day=2, decision_days=(-1, 0))

    assert sample.status is BoundaryStatus.INSUFFICIENT
    assert sample.rows == ()
    assert "incomplete or immature" in sample.exclusions[-1]


def test_population_sample_keys_preserve_dimension_alignment() -> None:
    """Predictors and labels are joined only within the exact named population slice."""
    schema = _schema(dimensions=("entity",))
    catalog = _catalog(
        schema,
        _row(schema, "predictor", 1.0, -1, -1, dimensions=(("entity", "A"),)),
        _row(schema, "predictor", 99.0, -1, -1, dimensions=(("entity", "B"),)),
        _row(schema, "outcome", 10.0, 1, 1, dimensions=(("entity", "A"),)),
        _row(schema, "outcome", 990.0, 1, 1, dimensions=(("entity", "B"),)),
    )

    sample = TrainingSampleBuilder().build(
        catalog,
        target=_target(schema, horizon_days=1),
        predictor_fields=(schema.field_ref("predictor"),),
        candidate_sample_keys=(
            SampleKey(ORIGIN, (("entity", "A"),)),
            SampleKey(ORIGIN, (("entity", "B"),)),
        ),
        current_time=ORIGIN + DAY * 2,
        missingness_policy=MissingnessPolicy.EXCLUDE_EXAMPLE,
    )

    assert tuple((row.dimensions, row.predictors[0].value, row.label) for row in sample.rows) == (
        ((("entity", "A"),), 1.0, 10.0),
        ((("entity", "B"),), 99.0, 990.0),
    )

    with pytest.raises(ValueError, match="sample-key dimensions must exactly cover"):
        TrainingSampleBuilder().build(
            catalog,
            target=_target(schema, horizon_days=1),
            predictor_fields=(schema.field_ref("predictor"),),
            candidate_decision_times=(ORIGIN,),
            current_time=ORIGIN + DAY * 2,
            missingness_policy=MissingnessPolicy.EXCLUDE_EXAMPLE,
        )


def test_duplicate_candidate_decisions_cannot_inflate_window_sample_count() -> None:
    """One scientific example cannot satisfy a two-example minimum by repetition."""
    schema = _schema()
    catalog = _catalog(
        schema,
        _row(schema, "predictor", 1.0, -1, -1),
        _row(schema, "outcome", 4.0, 2, 2),
    )

    with pytest.raises(ValueError, match="candidate sample keys must be unique"):
        _sample(catalog, _target(schema), current_day=3, decision_days=(0, 0))


def test_stale_registration_identity_cannot_relabel_changed_content() -> None:
    """Frozen records reject replacement content carrying a prior content identity."""
    schema = _schema()
    catalog = _catalog(schema, _row(schema, "predictor", 1.0, 0, 0))
    registration = catalog.datasets[0]

    with pytest.raises(ValueError, match="observation identity does not match content"):
        replace(registration.observations[0], value=999.0)

    changed_registration = ObservationRegistrar().register(
        schema,
        (_row(schema, "predictor", 999.0, 0, 0),),
    )
    with pytest.raises(ValueError, match="registration identity does not match content"):
        type(registration)(
            registration.registration_id,
            schema,
            changed_registration.observations,
        )


def test_derived_boundary_records_reject_stale_content_identity() -> None:
    """I_t, S_t, and W_t cannot retain an ID after their content changes."""
    schema = _schema()
    predictor = schema.field_ref("predictor")
    catalog = _catalog(
        schema,
        _row(schema, "predictor", 1.0, -1, -1),
        _row(schema, "outcome", 4.0, 1, 1),
    )
    information = InformationSetBuilder().build(
        catalog,
        decision_time=ORIGIN,
        requested_fields=(predictor,),
    )
    sample = _sample(catalog, _target(schema, horizon_days=1), current_day=2)
    policy = TrainingWindowPolicy(1, WindowKind.EXPANDING, 1, None, "window:v1")
    window = TrainingWindowSelector().select(sample, policy)

    with pytest.raises(ValueError, match="information-set identity does not match content"):
        replace(information, exclusions=("forged",))
    with pytest.raises(ValueError, match="training-row identity does not match content"):
        replace(sample.rows[0], label=999.0)
    with pytest.raises(ValueError, match="training-sample identity does not match content"):
        replace(sample, exclusions=("forged",))
    with pytest.raises(ValueError, match="training-window identity does not match content"):
        replace(window, insufficiency="forged")


def test_ambiguous_revision_history_is_rejected_instead_of_tie_broken() -> None:
    """Vintage text cannot arbitrarily decide between conflicting cell revisions."""
    schema = _schema()
    rows = (
        _row(schema, "predictor", 1.0, 0, 1, vintage="source-a", revision=0),
        _row(schema, "predictor", 2.0, 0, 1, vintage="source-b", revision=0),
    )

    with pytest.raises(ValueError, match="ambiguous revision history"):
        ObservationRegistrar().register(schema, rows)

    non_coherent = (
        _row(schema, "predictor", 1.0, 0, 2, vintage="initial", revision=0),
        _row(schema, "predictor", 2.0, 0, 1, vintage="revision", revision=1),
    )
    with pytest.raises(ValueError, match="non-coherent revision history"):
        ObservationRegistrar().register(schema, non_coherent)


def test_early_event_label_freezes_at_first_event_observation() -> None:
    """Post-event path arrivals cannot rewrite an already complete event label."""
    schema = _schema()
    target = _target(
        schema,
        kind=TargetKind.EVENT,
        event_condition=EventCondition(Comparison.GREATER_THAN, 10.0, None),
        maturity_policy=MaturityPolicy.EVENT_OR_INTERVAL_END,
    )
    catalog = _catalog(
        schema,
        _row(schema, "predictor", 1.0, -1, -1),
        _row(schema, "outcome", 15.0, 1, 1),
        _row(schema, "outcome", 2.0, 2, 2),
    )

    at_event = _sample(catalog, target, current_day=1)
    after_later_path_point = _sample(catalog, target, current_day=2)

    assert at_event.rows[0].row_id == after_later_path_point.rows[0].row_id
    assert after_later_path_point.rows[0].label_matured_at == ORIGIN + DAY
    assert after_later_path_point.rows[0].label_observation_ids == (
        at_event.rows[0].label_observation_ids[0],
    )
