"""Causal tests for formal temporal features crossing the training boundary."""

from __future__ import annotations

import copy
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from research_agent.data_foundation import (
    BoundaryStatus,
    DataCatalogSnapshot,
    DatasetSchema,
    FieldDefinition,
    IncompleteOutcomePolicy,
    InformationSetBuilder,
    MaturityPolicy,
    MissingnessPolicy,
    ObservationInput,
    ObservationRegistrar,
    OutcomeAlignment,
    SampleKey,
    TargetDefinition,
    TargetKind,
    TemporalOffset,
    TrainingSample,
    TrainingSampleBuilder,
    TrainingWindow,
)
from research_agent.data_foundation._identity import stable_identity
from research_agent.development import (
    DevelopmentEvaluator,
    DevelopmentProtocol,
    FittedSystemRegistry,
    SystemPredictor,
    SystemTrainer,
    TrainingBlocked,
    TrainingInformationBuilder,
    TrainingInformationRegistry,
)
from research_agent.formalization import (
    FailureAction,
    FeatureAlignment,
    FeatureDefinition,
    FeatureExpression,
    FeatureSet,
    HistoryKind,
    HistorySemantics,
    ModelDefinition,
    PredictiveSystemDefinition,
    TemporalMapping,
)

DAY = timedelta(days=1)
ORIGIN = datetime(2024, 1, 1, tzinfo=UTC)


def _world() -> tuple[DatasetSchema, DataCatalogSnapshot, TargetDefinition]:
    schema = DatasetSchema(
        dataset_id="temporal-training",
        version="v1",
        environment_id="temporal-environment",
        provenance_ref="schema:temporal-v1",
        fields=(
            FieldDefinition("x", "Signal", "float", "index", (), "Irregular signal."),
            FieldDefinition("y", "Outcome", "float", "units", (), "Next-day outcome."),
        ),
    )
    signal = (1.0, 10.0, 2.0, 20.0, 3.0, 30.0, 4.0, 40.0, 5.0)
    inputs: list[ObservationInput] = []
    for day, value in enumerate(signal):
        instant = ORIGIN + DAY * day
        inputs.append(
            ObservationInput(
                schema.field_ref("x"),
                value,
                instant,
                instant,
                "initial",
                0,
                "source:signal",
                f"artifact:x:{day}",
                "release:v1",
                (),
            )
        )
    for decision_day in range(1, 8):
        outcome_day = decision_day + 1
        instant = ORIGIN + DAY * outcome_day
        inputs.append(
            ObservationInput(
                schema.field_ref("y"),
                3.0 * signal[decision_day - 1] + 2.0,
                instant,
                instant,
                "initial",
                0,
                "source:outcome",
                f"artifact:y:{outcome_day}",
                "release:v1",
                (),
            )
        )
    catalog = DataCatalogSnapshot(
        schema.environment_id,
        (ObservationRegistrar().register(schema, tuple(inputs)),),
    )
    one_day = TemporalOffset.elapsed(DAY)
    target = TargetDefinition(
        task_id="task:temporal",
        task_version=1,
        task_semantic_digest="task:temporal:digest",
        confirmed_task_horizon_id=one_day.identity,
        version=1,
        parent_target_id=None,
        field_ref=schema.field_ref("y"),
        kind=TargetKind.ENDPOINT,
        horizon=one_day,
        outcome_start_offset=TemporalOffset.zero(),
        outcome_end_offset=one_day,
        alignment=OutcomeAlignment.EXACT,
        path_reduction=None,
        event_condition=None,
        maturity_delay=TemporalOffset.zero(),
        maturity_policy=MaturityPolicy.FULL_INTERVAL,
        required_observation_count=1,
        value_encoding="numeric",
        units="units",
        censoring_policy="complete interval",
        incomplete_outcome_policy=IncompleteOutcomePolicy.EXCLUDE,
        environment_id=schema.environment_id,
        schema_provenance_ref=schema.provenance_ref,
        provenance_refs=("target:temporal",),
    )
    return schema, catalog, target


def _feature(
    schema: DatasetSchema,
    *,
    lag_days: int,
    standardized: bool = False,
) -> FeatureDefinition:
    lag = TemporalOffset.elapsed(DAY * lag_days)
    expression = FeatureExpression.lag(FeatureExpression.field(schema.field_ref("x")), lag)
    procedures: tuple[tuple[str, str], ...] = ()
    if standardized:
        expression = FeatureExpression.standardize(expression, state_slot="scale-lag")
        procedures = (("scale-lag", "fit:standardize-v1"),)
    return FeatureDefinition(
        name=f"signal-lag-{lag_days}",
        version=1,
        parent_definition_id=None,
        environment_id=schema.environment_id,
        dependencies=(schema.field_ref("x"),),
        expression=expression,
        temporal_mapping=TemporalMapping(
            FeatureAlignment.LATEST_AT_OR_BEFORE,
            TemporalOffset.zero(),
        ),
        history=HistorySemantics(
            HistoryKind.EXPANDING,
            lag,
            None,
            "require exact declared lag history",
            "never replace lag with latest value",
        ),
        output_data_type="float",
        output_units="index",
        dimensions=(),
        missing_input=FailureAction.FAIL,
        invalid_domain=FailureAction.FAIL,
        insufficiency=FailureAction.FAIL,
        failure="fail without a temporal shortcut",
        hypothesis="lagged signal predicts the next-day outcome",
        information_intent="separate historical signal from current signal",
        fitted_state_procedures=procedures,
        evidence_refs=("hypothesis:lag",),
        candidate_ancestry=("candidate:lag",),
        provenance_refs=(schema.provenance_ref,),
    )


def _system(
    schema: DatasetSchema,
    target: TargetDefinition,
    feature: FeatureDefinition,
    *,
    protocol_id: str = "development:temporal",
) -> PredictiveSystemDefinition:
    feature_set = FeatureSet(
        "temporal-features",
        1,
        None,
        schema.environment_id,
        (feature,),
        ("selection:none",),
        ("feature-set:temporal",),
    )
    model = ModelDefinition(
        "linear",
        1,
        None,
        schema.environment_id,
        "linear_regression",
        (("fit_intercept", True), ("ridge", 0.0)),
        (feature_set.identity,),
        "selection:none",
        "deterministic",
        ("training:formal-information",),
        ("evidence:development",),
        ("candidate:model",),
        ("implementation:stdlib",),
    )
    return PredictiveSystemDefinition(
        "temporal-system",
        1,
        None,
        schema.environment_id,
        target,
        feature_set,
        (model,),
        None,
        "data:as-known",
        "training:formal-information",
        protocol_id,
        ("evidence:system",),
        ("candidate:system",),
        ("assembly:temporal",),
    )


def _sample_and_window(
    schema: DatasetSchema,
    catalog: DataCatalogSnapshot,
    target: TargetDefinition,
) -> tuple[TrainingSample, TrainingWindow]:
    sample = TrainingSampleBuilder().build(
        catalog,
        target=target,
        predictor_fields=(schema.field_ref("x"),),
        candidate_sample_keys=tuple(SampleKey(ORIGIN + DAY * day) for day in range(1, 7)),
        current_time=ORIGIN + DAY * 8,
        missingness_policy=MissingnessPolicy.EXCLUDE_EXAMPLE,
    )
    assert sample.status is BoundaryStatus.READY
    payload = {
        "sample_id": sample.sample_id,
        "policy_id": "window:all-legal",
        "row_ids": tuple(row.row_id for row in sample.rows),
        "status": BoundaryStatus.READY,
        "insufficiency": None,
    }
    window = TrainingWindow(
        stable_identity("training-window", payload),
        sample.sample_id,
        "window:all-legal",
        sample.rows,
        BoundaryStatus.READY,
        None,
    )
    return sample, window


def test_temporal_fit_requires_and_records_exact_legal_information() -> None:
    """Lag learning uses I_t history and cannot degrade into a latest-value shortcut."""
    schema, catalog, target = _world()
    feature = _feature(schema, lag_days=1)
    system = _system(schema, target, feature)
    sample, window = _sample_and_window(schema, catalog, target)
    information_registry = TrainingInformationRegistry()
    bundle = TrainingInformationBuilder(information_registry).build(
        catalog,
        sample,
        window,
        requested_fields=(schema.field_ref("x"),),
    )
    registry = FittedSystemRegistry()
    fitted = SystemTrainer(
        registry=registry,
        training_information_registry=information_registry,
    ).fit(system, window, bundle)

    assert fitted.models[0].coefficients == pytest.approx((3.0,))
    assert fitted.models[0].intercept == pytest.approx(2.0)
    assert fitted.fit_record.training_information_bundle_id == bundle.bundle_id
    assert fitted.fit_record.information_set_ids == tuple(
        item.information_set_id for item in bundle.information_sets
    )
    assert len(fitted.fit_record.feature_series_ids) == 1
    assert len(fitted.fit_record.compiled_feature_ids) == 1

    prediction_information = InformationSetBuilder().build(
        catalog,
        decision_time=ORIGIN + DAY * 8,
        requested_fields=(schema.field_ref("x"),),
    )
    prediction = SystemPredictor(registry).predict(system, fitted, prediction_information)
    assert prediction.value == pytest.approx(122.0)


def test_temporal_operator_without_information_bundle_fails_closed() -> None:
    """A row containing the current value cannot silently stand in for lagged history."""
    schema, catalog, target = _world()
    system = _system(schema, target, _feature(schema, lag_days=1))
    _, window = _sample_and_window(schema, catalog, target)

    with pytest.raises(TrainingBlocked, match="pre-materialized temporal history"):
        SystemTrainer().fit(system, window)


def test_fold_fitted_standardization_can_consume_a_temporal_operand() -> None:
    """Scaling learns only from W_t while its operand still comes from legal lag history."""
    schema, catalog, target = _world()
    feature = _feature(schema, lag_days=1, standardized=True)
    system = _system(schema, target, feature)
    sample, window = _sample_and_window(schema, catalog, target)
    information_registry = TrainingInformationRegistry()
    bundle = TrainingInformationBuilder(information_registry).build(
        catalog,
        sample,
        window,
        requested_fields=(schema.field_ref("x"),),
    )
    registry = FittedSystemRegistry()
    fitted = SystemTrainer(
        registry=registry,
        training_information_registry=information_registry,
    ).fit(system, window, bundle)

    assert len(fitted.transforms) == 1
    assert any(item.startswith("operand-series:") for item in fitted.transforms[0].provenance_refs)
    information = InformationSetBuilder().build(
        catalog,
        decision_time=ORIGIN + DAY * 8,
        requested_fields=(schema.field_ref("x"),),
    )
    assert SystemPredictor(registry).predict(system, fitted, information).value == pytest.approx(
        122.0
    )


def test_development_folds_use_formal_information_for_temporal_features() -> None:
    """Development evidence records formal fit provenance for every temporal fold."""
    schema, catalog, target = _world()
    protocol = DevelopmentProtocol(
        name="temporal-development",
        version=1,
        minimum_training_rows=3,
        validation_rows=2,
        step_rows=2,
        purge_overlapping_labels=False,
        embargo=None,
        metric_names=("mse",),
        feature_analysis_methods=("permutation", "ablation", "single_feature"),
        environment_id=schema.environment_id,
        provenance_refs=("protocol:temporal",),
    )
    system = _system(schema, target, _feature(schema, lag_days=1), protocol_id=protocol.identity)
    sample, _ = _sample_and_window(schema, catalog, target)

    evidence = DevelopmentEvaluator().evaluate(
        system,
        sample,
        protocol,
        catalog=catalog,
    )

    assert evidence.fit_records
    assert all(item.training_information_bundle_id for item in evidence.fit_records)
    assert all(item.feature_series_ids for item in evidence.fit_records)


def test_training_information_requires_exact_configured_issuance() -> None:
    """A self-consistent reconstructed bundle cannot change the legal feature matrix."""
    schema, catalog, target = _world()
    system = _system(schema, target, _feature(schema, lag_days=1))
    sample, window = _sample_and_window(schema, catalog, target)
    information_registry = TrainingInformationRegistry()
    builder = TrainingInformationBuilder(information_registry)
    issued = builder.build(
        catalog,
        sample,
        window,
        requested_fields=(schema.field_ref("x"),),
    )
    replay = builder.build(
        catalog,
        sample,
        window,
        requested_fields=(schema.field_ref("x"),),
    )
    trainer = SystemTrainer(training_information_registry=information_registry)

    assert replay is issued
    assert trainer.fit(system, window, issued).fit_record.training_information_bundle_id
    with pytest.raises(TrainingBlocked) as captured:
        trainer.fit(system, window, replace(issued))
    assert captured.value.failure.code.value == "invalid_training_data"
    with pytest.raises(TypeError, match="cannot be copied"):
        copy.copy(information_registry)
    with pytest.raises(TypeError, match="cannot be copied"):
        copy.deepcopy(information_registry)
