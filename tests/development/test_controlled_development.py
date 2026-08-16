"""Adversarial Milestone 5 tests for fitting and development validation."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from research_agent.data_foundation import (
    BoundaryStatus,
    CalendarUnit,
    DataCatalogSnapshot,
    DatasetSchema,
    FieldDefinition,
    IncompleteOutcomePolicy,
    InformationSetBuilder,
    MaturityPolicy,
    MonthEndPolicy,
    ObservationInput,
    ObservationRegistrar,
    OffsetAnchor,
    OutcomeAlignment,
    PredictorValue,
    TargetDefinition,
    TargetKind,
    TemporalOffset,
    TimezonePolicy,
    TrainingRow,
    TrainingSample,
    TrainingWindow,
)
from research_agent.data_foundation._identity import stable_identity
from research_agent.development import (
    DevelopmentEvaluator,
    DevelopmentProtocol,
    DevelopmentStatus,
    FittedSystemRegistry,
    OutcomeRecorder,
    SystemPredictor,
    SystemTrainer,
    TemporalFoldBuilder,
    TrainingBlocked,
    TrainingFailureCode,
    TrialLedger,
    TrialStatus,
)
from research_agent.formalization import (
    FailureAction,
    FeatureAlignment,
    FeatureCompiler,
    FeatureDefinition,
    FeatureExpression,
    FeatureMaterializer,
    FeatureSeries,
    FeatureSeriesStatus,
    FeatureSet,
    FeatureValue,
    FeatureValueStatus,
    HistoryKind,
    HistorySemantics,
    ModelDefinition,
    PredictiveSystemDefinition,
    TemporalMapping,
)

DAY = timedelta(days=1)
ZERO_OFFSET = TemporalOffset.zero()
ORIGIN = datetime(2024, 1, 1, tzinfo=UTC)
FORGED_VALUE = 999_999.0


def _schema() -> DatasetSchema:
    return DatasetSchema(
        dataset_id="development-fixture",
        version="schema-v1",
        environment_id="environment-v1",
        provenance_ref="artifact:schema-v1",
        fields=(
            FieldDefinition("x1", "X1", "float", "index", (), "First signal."),
            FieldDefinition("x2", "X2", "float", "index", (), "Second signal."),
            FieldDefinition("outcome", "Outcome", "float", "units", (), "Outcome."),
        ),
    )


def _target(
    schema: DatasetSchema,
    *,
    horizon: timedelta | TemporalOffset = DAY,
) -> TargetDefinition:
    offset = horizon if isinstance(horizon, TemporalOffset) else TemporalOffset.elapsed(horizon)
    return TargetDefinition(
        task_id="task-v1",
        task_version=1,
        task_semantic_digest="task-semantic-v1",
        confirmed_task_horizon_id=offset.identity,
        version=1,
        parent_target_id=None,
        field_ref=schema.field_ref("outcome"),
        kind=TargetKind.ENDPOINT,
        horizon=offset,
        outcome_start_offset=ZERO_OFFSET,
        outcome_end_offset=offset,
        alignment=OutcomeAlignment.EXACT,
        path_reduction=None,
        event_condition=None,
        maturity_delay=ZERO_OFFSET,
        maturity_policy=MaturityPolicy.FULL_INTERVAL,
        required_observation_count=1,
        value_encoding="numeric",
        units="units",
        censoring_policy="complete interval",
        incomplete_outcome_policy=IncompleteOutcomePolicy.EXCLUDE,
        environment_id=schema.environment_id,
        schema_provenance_ref=schema.provenance_ref,
        provenance_refs=("research:target",),
    )


def _feature(
    schema: DatasetSchema,
    field: str,
    *,
    standardized: bool = False,
    dimensions: tuple[tuple[str, str], ...] = (),
) -> FeatureDefinition:
    expression = FeatureExpression.field(schema.field_ref(field))
    procedures: tuple[tuple[str, str], ...] = ()
    if standardized:
        expression = FeatureExpression.standardize(expression, state_slot=f"scale-{field}")
        procedures = ((f"scale-{field}", "fit:standardize-v1"),)
    return FeatureDefinition(
        name=field,
        version=1,
        parent_definition_id=None,
        environment_id=schema.environment_id,
        dependencies=(schema.field_ref(field),),
        expression=expression,
        temporal_mapping=TemporalMapping(FeatureAlignment.LATEST_AT_OR_BEFORE, ZERO_OFFSET),
        history=HistorySemantics(
            HistoryKind.EXPANDING,
            ZERO_OFFSET,
            None,
            "use exact legal history",
            "no truncation",
        ),
        output_data_type="float",
        output_units="index",
        dimensions=dimensions,
        missing_input=FailureAction.FAIL,
        invalid_domain=FailureAction.FAIL,
        insufficiency=FailureAction.FAIL,
        failure="fail without substitution",
        hypothesis=f"{field} may predict the target",
        information_intent="retain exact legal signal",
        fitted_state_procedures=procedures,
        evidence_refs=("analysis:feature",),
        candidate_ancestry=("candidate:feature",),
        provenance_refs=(schema.provenance_ref,),
    )


def _model(
    *,
    algorithm: str = "linear_regression",
    ridge: float = 0.0,
) -> ModelDefinition:
    hyperparameters = () if algorithm == "mean" else (("fit_intercept", True), ("ridge", ridge))
    return ModelDefinition(
        name="model",
        version=1,
        parent_definition_id=None,
        environment_id="environment-v1",
        algorithm=algorithm,
        hyperparameters=hyperparameters,
        preprocessing_refs=("feature-set-bound",),
        selection_procedure_ref="selection:none",
        randomness_policy="deterministic",
        training_requirement_refs=("trainer:controlled-v1",),
        evidence_refs=("development:model",),
        candidate_ancestry=("candidate:model",),
        provenance_refs=("implementation:stdlib-models",),
    )


def _system(
    schema: DatasetSchema,
    target: TargetDefinition,
    features: tuple[FeatureDefinition, ...],
    *,
    model: ModelDefinition | None = None,
    evaluation_protocol_id: str = "evaluation:development-v1",
) -> PredictiveSystemDefinition:
    feature_set = FeatureSet(
        name="features",
        version=1,
        parent_feature_set_id=None,
        environment_id=schema.environment_id,
        members=features,
        selection_ancestry=("trial:feature-selection",),
        provenance_refs=("research:selection",),
    )
    return PredictiveSystemDefinition(
        name="candidate",
        version=1,
        parent_system_id=None,
        environment_id=schema.environment_id,
        target=target,
        feature_set=feature_set,
        models=(model or _model(),),
        ensemble=None,
        data_protocol_id="data:as-known-v1",
        training_protocol_id="training:controlled-v1",
        evaluation_protocol_id=evaluation_protocol_id,
        evidence_refs=("development:candidate",),
        candidate_ancestry=("candidate:system",),
        provenance_refs=("research:assembly",),
    )


def _row(  # noqa: PLR0913
    schema: DatasetSchema,
    target: TargetDefinition,
    day: int,
    x1: float,
    label: float,
    *,
    x2: float = 0.0,
    entity: str | None = None,
) -> TrainingRow:
    dimensions = () if entity is None else (("entity", entity),)
    predictors = (
        PredictorValue(schema.field_ref("x1"), x1, f"observation:x1:{day}:{entity}"),
        PredictorValue(schema.field_ref("x2"), x2, f"observation:x2:{day}:{entity}"),
    )
    payload = {
        "decision_time": ORIGIN + DAY * day,
        "dimensions": dimensions,
        "target_id": target.identity,
        "predictors": predictors,
        "label": label,
        "label_matured_at": target.horizon.apply(ORIGIN + DAY * day),
        "label_observation_ids": (f"outcome:{day}",),
        "label_threshold": None,
    }
    return TrainingRow(
        row_id=stable_identity("training-row", payload),
        decision_time=ORIGIN + DAY * day,
        dimensions=dimensions,
        target_id=target.identity,
        predictors=predictors,
        label=label,
        label_matured_at=target.horizon.apply(ORIGIN + DAY * day),
        label_observation_ids=(f"outcome:{day}",),
        label_threshold=None,
    )


def _sample(
    schema: DatasetSchema,
    target: TargetDefinition,
    rows: tuple[TrainingRow, ...],
) -> TrainingSample:
    payload = {
        "current_time": max(row.label_matured_at for row in rows),
        "target_id": target.identity,
        "catalog_id": "catalog:fixture",
        "predictor_fields": (schema.field_ref("x1"), schema.field_ref("x2")),
        "row_ids": tuple(row.row_id for row in rows),
        "status": BoundaryStatus.READY,
        "exclusions": (),
    }
    return TrainingSample(
        sample_id=stable_identity("training-sample", payload),
        current_time=max(row.label_matured_at for row in rows),
        target_id=target.identity,
        environment_id=schema.environment_id,
        catalog_id="catalog:fixture",
        predictor_fields=(schema.field_ref("x1"), schema.field_ref("x2")),
        rows=rows,
        status=BoundaryStatus.READY,
        exclusions=(),
    )


def _row_at(
    schema: DatasetSchema,
    target: TargetDefinition,
    decision_time: datetime,
    ordinal: int,
) -> TrainingRow:
    predictors = (
        PredictorValue(schema.field_ref("x1"), float(ordinal), f"observation:x1:{ordinal}"),
        PredictorValue(schema.field_ref("x2"), 0.0, f"observation:x2:{ordinal}"),
    )
    matured_at = target.horizon.apply(decision_time)
    payload = {
        "decision_time": decision_time,
        "dimensions": (),
        "target_id": target.identity,
        "predictors": predictors,
        "label": float(ordinal),
        "label_matured_at": matured_at,
        "label_observation_ids": (f"outcome:{ordinal}",),
        "label_threshold": None,
    }
    return TrainingRow(
        row_id=stable_identity("training-row", payload),
        decision_time=decision_time,
        dimensions=(),
        target_id=target.identity,
        predictors=predictors,
        label=float(ordinal),
        label_matured_at=matured_at,
        label_observation_ids=(f"outcome:{ordinal}",),
        label_threshold=None,
    )


def _window(sample: TrainingSample, rows: tuple[TrainingRow, ...]) -> TrainingWindow:
    payload = {
        "sample_id": sample.sample_id,
        "policy_id": "window:fixture",
        "row_ids": tuple(row.row_id for row in rows),
        "status": BoundaryStatus.READY,
        "insufficiency": None,
    }
    return TrainingWindow(
        stable_identity("training-window", payload),
        sample.sample_id,
        "window:fixture",
        rows,
        BoundaryStatus.READY,
        None,
    )


def _protocol(
    *,
    purge: bool = False,
    embargo: timedelta | None = None,
    minimum: int = 3,
    validation: int = 2,
) -> DevelopmentProtocol:
    return DevelopmentProtocol(
        name="ordered-development",
        version=1,
        minimum_training_rows=minimum,
        validation_rows=validation,
        step_rows=validation,
        purge_overlapping_labels=purge,
        embargo=embargo,
        metric_names=("mse", "mae"),
        feature_analysis_methods=("permutation", "ablation", "single_feature"),
        environment_id="environment-v1",
        provenance_refs=("protocol:development-v1",),
    )


def test_fitting_and_preprocessing_see_only_ready_window() -> None:
    """A poisoned row outside W_t cannot change learned transform or model state."""
    schema = _schema()
    target = _target(schema)
    feature = _feature(schema, "x1", standardized=True)
    system = _system(schema, target, (feature,))
    legal = tuple(_row(schema, target, day, float(day), 2.0 * day + 1.0) for day in range(4))
    clean = _sample(schema, target, (*legal, _row(schema, target, 4, 4.0, 9.0)))
    poisoned = _sample(schema, target, (*legal, _row(schema, target, 4, 1_000_000.0, -9e9)))

    clean_fit = SystemTrainer().fit(system, _window(clean, legal))
    poisoned_fit = SystemTrainer().fit(system, _window(poisoned, legal))

    assert clean_fit.transforms[0].parameters == poisoned_fit.transforms[0].parameters
    assert clean_fit.models[0].coefficients == poisoned_fit.models[0].coefficients
    expected_location = 1.5
    assert dict(clean_fit.transforms[0].parameters)["location"] == expected_location
    assert clean_fit.fit_record.row_ids == tuple(row.row_id for row in legal)


def test_prediction_materializes_legal_series_and_cannot_learn() -> None:
    """Inference consumes trainer state and an InformationSet without changing learned state."""
    schema = _schema()
    target = _target(schema)
    feature = _feature(schema, "x1", standardized=True)
    system = _system(schema, target, (feature,))
    rows = tuple(_row(schema, target, day, float(day), 2.0 * day + 1.0) for day in range(4))
    registry = FittedSystemRegistry()
    trainer = SystemTrainer(registry=registry)
    fitted = trainer.fit(system, _window(_sample(schema, target, rows), rows))
    predictor_observation = ObservationInput(
        field_ref=schema.field_ref("x1"),
        value=4.0,
        reference_time=ORIGIN + DAY * 4,
        available_at=ORIGIN + DAY * 4,
        vintage_id="initial",
        revision_number=0,
        source_ref="source:fixture",
        provenance_ref="artifact:x1:4",
        availability_rule_version="release-v1",
        dimensions=(),
    )
    catalog = DataCatalogSnapshot(
        schema.environment_id,
        (ObservationRegistrar().register(schema, (predictor_observation,)),),
    )
    information = InformationSetBuilder().build(
        catalog,
        decision_time=ORIGIN + DAY * 4,
        requested_fields=(schema.field_ref("x1"),),
    )
    before = repr(fitted)

    prediction = SystemPredictor(registry).predict(system, fitted, information)

    assert prediction.value == pytest.approx(9.0)
    assert prediction.dimensions == ()
    assert repr(fitted) == before
    assert not hasattr(SystemPredictor(registry), "fit")
    assert not hasattr(FeatureMaterializer(), "fit")
    assert prediction.feature_definition_ids == (feature.identity,)


def test_unsupported_or_singular_recipe_blocks_without_fallback() -> None:
    """Formal failure returns no partial fitted system and never changes algorithms."""
    schema = _schema()
    target = _target(schema)
    rows = tuple(_row(schema, target, day, 1.0, float(day)) for day in range(3))
    sample = _sample(schema, target, rows)
    unsupported = _system(schema, target, (_feature(schema, "x1"),), model=_model(algorithm="svm"))

    with pytest.raises(TrainingBlocked) as captured:
        SystemTrainer().fit(unsupported, _window(sample, rows))

    assert captured.value.failure.code is TrainingFailureCode.UNSUPPORTED_RECIPE
    assert "no fallback" in captured.value.failure.detail


def test_fitted_system_cannot_hide_missing_learned_components_behind_a_new_hash() -> None:
    """Content identity does not replace structural validation of complete fitted state."""
    schema = _schema()
    target = _target(schema)
    feature = _feature(schema, "x1")
    system = _system(schema, target, (feature,))
    rows = tuple(_row(schema, target, day, float(day), float(day)) for day in range(3))
    fitted = SystemTrainer().fit(system, _window(_sample(schema, target, rows), rows))
    forged_payload = {
        "system_definition_id": fitted.system_definition_id,
        "feature_set_id": fitted.feature_set_id,
        "target_id": fitted.target_id,
        "environment_id": fitted.environment_id,
        "fit_record": fitted.fit_record,
        "models": (),
        "transforms": fitted.transforms,
        "ensemble_weights": (),
    }

    with pytest.raises(ValueError, match="requires one weight"):
        replace(
            fitted,
            fitted_system_id=stable_identity("fitted-predictive-system", forged_payload),
            models=(),
            ensemble_weights=(),
        )


def test_rehashed_caller_authored_fitted_state_has_no_prediction_authority() -> None:
    """Content hashes cannot grant caller-authored coefficients trainer authority."""
    schema = _schema()
    target = _target(schema)
    feature = _feature(schema, "x1")
    system = _system(schema, target, (feature,))
    rows = tuple(_row(schema, target, day, float(day), 2.0 * day + 1.0) for day in range(4))
    registry = FittedSystemRegistry()
    fitted = SystemTrainer(registry=registry).fit(
        system,
        _window(_sample(schema, target, rows), rows),
    )
    original_model = fitted.models[0]
    forged_model_payload = {
        "model_definition_id": original_model.model_definition_id,
        "training_window_id": original_model.training_window_id,
        "algorithm": original_model.algorithm,
        "input_feature_ids": original_model.input_feature_ids,
        "coefficients": (0.0,),
        "intercept": FORGED_VALUE,
        "expansion_terms": original_model.expansion_terms,
        "provenance_refs": original_model.provenance_refs,
    }
    forged_model = replace(
        original_model,
        fitted_model_id=stable_identity("fitted-model-state", forged_model_payload),
        coefficients=(0.0,),
        intercept=FORGED_VALUE,
    )
    forged_record_payload = {
        "system_definition_id": fitted.fit_record.system_definition_id,
        "training_window_id": fitted.fit_record.training_window_id,
        "training_sample_id": fitted.fit_record.training_sample_id,
        "environment_id": fitted.fit_record.environment_id,
        "fitted_through": fitted.fit_record.fitted_through,
        "row_ids": fitted.fit_record.row_ids,
        "model_state_ids": (forged_model.fitted_model_id,),
        "transform_state_ids": fitted.fit_record.transform_state_ids,
        "procedure_refs": fitted.fit_record.procedure_refs,
        "provenance_refs": fitted.fit_record.provenance_refs,
        "status": DevelopmentStatus.DEVELOPMENT,
    }
    forged_record = replace(
        fitted.fit_record,
        fit_id=stable_identity("fit-record", forged_record_payload),
        model_state_ids=(forged_model.fitted_model_id,),
    )
    forged_system_payload = {
        "system_definition_id": fitted.system_definition_id,
        "feature_set_id": fitted.feature_set_id,
        "target_id": fitted.target_id,
        "environment_id": fitted.environment_id,
        "fit_record": forged_record,
        "models": (forged_model,),
        "transforms": fitted.transforms,
        "ensemble_weights": fitted.ensemble_weights,
    }
    forged = replace(
        fitted,
        fitted_system_id=stable_identity("fitted-predictive-system", forged_system_payload),
        fit_record=forged_record,
        models=(forged_model,),
    )
    observation = ObservationInput(
        field_ref=schema.field_ref("x1"),
        value=4.0,
        reference_time=ORIGIN + DAY * 4,
        available_at=ORIGIN + DAY * 4,
        vintage_id="initial",
        revision_number=0,
        source_ref="source:fixture",
        provenance_ref="artifact:x1:4",
        availability_rule_version="release-v1",
        dimensions=(),
    )
    information = InformationSetBuilder().build(
        DataCatalogSnapshot(
            schema.environment_id,
            (ObservationRegistrar().register(schema, (observation,)),),
        ),
        decision_time=ORIGIN + DAY * 4,
        requested_fields=(schema.field_ref("x1"),),
    )

    with pytest.raises(ValueError, match="not issued"):
        SystemPredictor(registry).predict(system, forged, information)


def test_training_sample_rejects_future_decisions_and_immature_labels() -> None:
    """A recomputed content hash cannot turn future or immature rows into legal S_t."""
    schema = _schema()
    target = _target(schema)
    rows = tuple(_row(schema, target, day, float(day), float(day)) for day in range(3))
    sample = _sample(schema, target, rows)
    forged_time = ORIGIN
    payload = {
        "current_time": forged_time,
        "target_id": sample.target_id,
        "catalog_id": sample.catalog_id,
        "predictor_fields": sample.predictor_fields,
        "row_ids": tuple(row.row_id for row in sample.rows),
        "status": sample.status,
        "exclusions": sample.exclusions,
    }

    with pytest.raises(ValueError, match="future decision or immature label"):
        replace(
            sample,
            sample_id=stable_identity("training-sample", payload),
            current_time=forged_time,
        )


def test_overlap_is_purged_and_non_overlap_gets_no_ceremonial_embargo() -> None:
    """Purge follows label intervals; embargo appears only when explicitly configured."""
    schema = _schema()
    overlapping = _target(schema, horizon=DAY * 2)
    rows = tuple(_row(schema, overlapping, day, float(day), float(day)) for day in range(7))
    sample = _sample(schema, overlapping, rows)
    purged = TemporalFoldBuilder().build(sample, overlapping, _protocol(purge=True))[0]
    unavailable = TemporalFoldBuilder().build(sample, overlapping, _protocol(purge=False))[0]

    assert rows[2].row_id in purged.purged_row_ids
    assert rows[2].row_id in unavailable.unavailable_row_ids
    assert rows[2].row_id not in unavailable.training_row_ids
    assert purged.embargoed_row_ids == ()

    non_overlapping = _target(schema, horizon=DAY)
    legal_rows = tuple(
        _row(schema, non_overlapping, day, float(day), float(day)) for day in range(7)
    )
    legal_sample = _sample(schema, non_overlapping, legal_rows)
    plain = TemporalFoldBuilder().build(legal_sample, non_overlapping, _protocol(purge=True))[0]
    explicit = TemporalFoldBuilder().build(
        legal_sample,
        non_overlapping,
        _protocol(purge=True, embargo=DAY),
    )[0]

    assert plain.purged_row_ids == ()
    assert plain.unavailable_row_ids == ()
    assert plain.embargoed_row_ids == ()
    assert explicit.embargoed_row_ids != ()


def test_fold_overlap_uses_calendar_quarter_not_ninety_elapsed_days() -> None:
    """Oct 31 overlaps a Jan 30 validation interval only under the declared calendar quarter."""
    schema = _schema()
    quarter = TemporalOffset.calendar(
        count=1,
        unit=CalendarUnit.QUARTER,
        anchor=OffsetAnchor.EXACT_INPUT,
        month_end_policy=MonthEndPolicy.PRESERVE,
        timezone_name="UTC",
        timezone_policy=TimezonePolicy.WALL_CLOCK_REJECT_TRANSITION,
    )
    dates = (
        datetime(2024, 8, 1, tzinfo=UTC),
        datetime(2024, 9, 1, tzinfo=UTC),
        datetime(2024, 10, 31, tzinfo=UTC),
        datetime(2025, 1, 30, tzinfo=UTC),
    )
    calendar_target = _target(schema, horizon=quarter)
    calendar_rows = tuple(
        _row_at(schema, calendar_target, moment, ordinal) for ordinal, moment in enumerate(dates)
    )
    calendar_fold = TemporalFoldBuilder().build(
        _sample(schema, calendar_target, calendar_rows),
        calendar_target,
        _protocol(purge=True, minimum=3, validation=1),
    )[0]

    elapsed_target = _target(schema, horizon=TemporalOffset.elapsed(timedelta(days=90)))
    elapsed_rows = tuple(
        _row_at(schema, elapsed_target, moment, ordinal) for ordinal, moment in enumerate(dates)
    )
    elapsed_fold = TemporalFoldBuilder().build(
        _sample(schema, elapsed_target, elapsed_rows),
        elapsed_target,
        _protocol(purge=True, minimum=3, validation=1),
    )[0]

    assert calendar_rows[2].row_id in calendar_fold.purged_row_ids
    assert elapsed_rows[2].row_id in elapsed_fold.training_row_ids


def test_development_evidence_keeps_conflicting_methods_and_interactions() -> None:
    """Single-feature weakness cannot gate an interaction-capable full system."""
    schema = _schema()
    target = _target(schema)
    features = (_feature(schema, "x1"), _feature(schema, "x2"))
    protocol = _protocol(minimum=6, validation=2)
    system = _system(
        schema,
        target,
        features,
        model=_model(algorithm="linear_interactions", ridge=0.1),
        evaluation_protocol_id=protocol.identity,
    )
    patterns = ((-1.0, -1.0), (-1.0, 1.0), (1.0, -1.0), (1.0, 1.0)) * 3
    rows = tuple(
        _row(schema, target, day, x1, x1 * x2, x2=x2) for day, (x1, x2) in enumerate(patterns)
    )
    original_members = system.feature_set.members

    evidence = DevelopmentEvaluator().evaluate(
        system,
        _sample(schema, target, rows),
        protocol,
    )

    methods = {
        (item.feature_definition_id, item.method) for item in evidence.feature_analysis.evidence
    }
    assert len(methods) == len(features) * 3
    single = tuple(
        item for item in evidence.feature_analysis.evidence if item.method == "single_feature"
    )
    assert all(item.aggregate is not None for item in single)
    assert evidence.metrics[0].aggregate < max(item.aggregate or 0.0 for item in single)
    assert "conflicting methods" in " ".join(evidence.feature_analysis.warnings)
    assert system.feature_set.members == original_members
    assert evidence.status is DevelopmentStatus.DEVELOPMENT


def test_row_local_development_evidence_cannot_supply_freeze_inputs() -> None:
    """Catalog-free compatibility evaluation is explicit development, never promotable evidence."""
    schema = _schema()
    target = _target(schema)
    protocol = _protocol(minimum=4, validation=2)
    system = _system(
        schema,
        target,
        (_feature(schema, "x1"),),
        evaluation_protocol_id=protocol.identity,
    )
    rows = tuple(_row(schema, target, day, float(day), 2.0 * day + 1.0) for day in range(10))
    evaluator = DevelopmentEvaluator()

    evidence = evaluator.evaluate(system, _sample(schema, target, rows), protocol, catalog=None)

    assert "non-promotable" in " ".join(evidence.warnings)
    assert all(item.training_information_bundle_id is None for item in evidence.fit_records)
    with pytest.raises(ValueError, match="no evaluator-issued freeze inputs"):
        evaluator.evidence_registry.resolve_freeze_inputs(evidence)


def test_correlated_substitutes_remain_visible_without_automatic_drop() -> None:
    """Redundant signals retain each method's evidence and exact FeatureSet membership."""
    schema = _schema()
    target = _target(schema)
    features = (_feature(schema, "x1"), _feature(schema, "x2"))
    protocol = _protocol(minimum=6, validation=2)
    system = _system(
        schema,
        target,
        features,
        model=_model(ridge=0.1),
        evaluation_protocol_id=protocol.identity,
    )
    rows = tuple(
        _row(schema, target, day, float(day), float(day), x2=float(day)) for day in range(12)
    )

    evidence = DevelopmentEvaluator().evaluate(
        system,
        _sample(schema, target, rows),
        protocol,
    )

    by_feature = {
        feature.identity: tuple(
            item
            for item in evidence.feature_analysis.evidence
            if item.feature_definition_id == feature.identity
        )
        for feature in features
    }
    assert all(
        {item.method for item in items} == {"permutation", "ablation", "single_feature"}
        for items in by_feature.values()
    )
    assert system.feature_set.members == features
    assert "correlated substitutes" in " ".join(evidence.feature_analysis.warnings)


def test_trial_ledger_retains_failed_rejected_selected_and_parent_history() -> None:
    """Selection cannot collapse development history into winner-only evidence."""
    ledger = TrialLedger()
    ledger.append(
        trial_id="failed",
        candidate_id="candidate:a",
        protocol_id="protocol:v1",
        parent_trial_ids=(),
        status=TrialStatus.ATTEMPTED,
        rationale="try candidate A",
    )
    ledger.append(
        trial_id="failed",
        candidate_id="candidate:a",
        protocol_id="protocol:v1",
        parent_trial_ids=(),
        status=TrialStatus.FAILED,
        rationale="exact fit failed",
        failure_id="failure:a",
    )
    with pytest.raises(ValueError, match="cannot be rewritten"):
        ledger.append(
            trial_id="failed",
            candidate_id="candidate:a",
            protocol_id="protocol:v1",
            parent_trial_ids=(),
            status=TrialStatus.SELECTED,
            rationale="illegal winner rewrite",
        )
    ledger.append(
        trial_id="rejected",
        candidate_id="candidate:b",
        protocol_id="protocol:v1",
        parent_trial_ids=("failed",),
        status=TrialStatus.ATTEMPTED,
        rationale="revise A into B",
    )
    ledger.append(
        trial_id="rejected",
        candidate_id="candidate:b",
        protocol_id="protocol:v1",
        parent_trial_ids=("failed",),
        status=TrialStatus.SUCCEEDED,
        rationale="development evidence was generated",
        evidence_refs=("development:evidence-b",),
    )
    ledger.append(
        trial_id="rejected",
        candidate_id="candidate:b",
        protocol_id="protocol:v1",
        parent_trial_ids=("failed",),
        status=TrialStatus.REJECTED,
        rationale="development evidence was weak",
    )
    ledger.append(
        trial_id="winner",
        candidate_id="candidate:c",
        protocol_id="protocol:v1",
        parent_trial_ids=("rejected",),
        status=TrialStatus.ATTEMPTED,
        rationale="revise B into C",
    )
    ledger.append(
        trial_id="winner",
        candidate_id="candidate:c",
        protocol_id="protocol:v1",
        parent_trial_ids=("rejected",),
        status=TrialStatus.SUCCEEDED,
        rationale="development evidence was generated",
        evidence_refs=("development:evidence-c",),
    )
    ledger.append(
        trial_id="winner",
        candidate_id="candidate:c",
        protocol_id="protocol:v1",
        parent_trial_ids=("rejected",),
        status=TrialStatus.SELECTED,
        rationale="request independent freeze assessment",
        evidence_refs=("development:evidence-c",),
    )

    assert {item.status for item in ledger.records} == {
        TrialStatus.ATTEMPTED,
        TrialStatus.SUCCEEDED,
        TrialStatus.FAILED,
        TrialStatus.REJECTED,
        TrialStatus.SELECTED,
    }
    assert {item.trial_id for item in ledger.ancestry("winner")} == {
        "failed",
        "rejected",
        "winner",
    }


def test_trial_ledger_rejects_ancestry_rewrite_missing_parent_and_illegal_transition() -> None:
    """One trial keeps exact ancestry and follows one legal append-only lifecycle."""
    ledger = TrialLedger()
    ledger.append(
        trial_id="root",
        candidate_id="candidate:a",
        protocol_id="protocol:a",
        parent_trial_ids=(),
        status=TrialStatus.ATTEMPTED,
        rationale="attempt root",
    )

    with pytest.raises(ValueError, match="existing trial"):
        ledger.append(
            trial_id="child",
            candidate_id="candidate:b",
            protocol_id="protocol:a",
            parent_trial_ids=("missing",),
            status=TrialStatus.ATTEMPTED,
            rationale="orphan child",
        )
    with pytest.raises(ValueError, match="legal trial transition"):
        ledger.append(
            trial_id="root",
            candidate_id="candidate:a",
            protocol_id="protocol:a",
            parent_trial_ids=(),
            status=TrialStatus.SELECTED,
            rationale="selection before evidence",
        )

    ledger.append(
        trial_id="root",
        candidate_id="candidate:a",
        protocol_id="protocol:a",
        parent_trial_ids=(),
        status=TrialStatus.SUCCEEDED,
        rationale="root evidence",
        evidence_refs=("evidence:a",),
    )
    with pytest.raises(ValueError, match="identity and ancestry cannot change"):
        ledger.append(
            trial_id="root",
            candidate_id="candidate:forged",
            protocol_id="protocol:forged",
            parent_trial_ids=(),
            status=TrialStatus.SELECTED,
            rationale="rewrite root",
        )


def test_feature_perturbations_have_exact_out_of_fold_effects() -> None:
    """Permutation and ablation evidence causally depends on the perturbed vectors."""
    schema = _schema()
    target = _target(schema)
    protocol = replace(
        _protocol(minimum=3, validation=2),
        feature_analysis_methods=("permutation", "ablation"),
    )
    feature = _feature(schema, "x1")
    system = _system(
        schema,
        target,
        (feature,),
        evaluation_protocol_id=protocol.identity,
    )
    rows = tuple(_row(schema, target, day, float(day), 2.0 * day + 1.0) for day in range(7))

    evidence = DevelopmentEvaluator().evaluate(
        system,
        _sample(schema, target, rows),
        protocol,
    )
    by_method = {item.method: item for item in evidence.feature_analysis.evidence}

    assert by_method["permutation"].fold_values == pytest.approx((4.0, 4.0))
    assert by_method["permutation"].aggregate == pytest.approx(4.0)
    assert by_method["ablation"].fold_values == pytest.approx((50.0, 122.0))
    assert by_method["ablation"].aggregate == pytest.approx(86.0)


def test_prediction_and_outcome_preserve_dimension_and_maturity_identity() -> None:
    """Entity identity survives inference and outcome stays unavailable until maturity."""
    schema = DatasetSchema(
        dataset_id="panel-fixture",
        version="schema-v1",
        environment_id="environment-v1",
        provenance_ref="artifact:panel-schema-v1",
        fields=(
            FieldDefinition("x1", "X1", "float", "index", ("entity",), "Panel signal."),
            FieldDefinition("x2", "X2", "float", "index", ("entity",), "Second signal."),
            FieldDefinition(
                "outcome",
                "Outcome",
                "float",
                "units",
                ("entity",),
                "Panel outcome.",
            ),
        ),
    )
    target = _target(schema)
    dimensions = (("entity", "a"),)
    feature = _feature(schema, "x1", dimensions=dimensions)
    system = _system(schema, target, (feature,))
    rows = tuple(_row(schema, target, day, float(day), float(day), entity="a") for day in range(3))
    registry = FittedSystemRegistry()
    fitted = SystemTrainer(registry=registry).fit(
        system,
        _window(_sample(schema, target, rows), rows),
    )
    predictor_observation = ObservationInput(
        field_ref=schema.field_ref("x1"),
        value=3.0,
        reference_time=ORIGIN + DAY * 3,
        available_at=ORIGIN + DAY * 3,
        vintage_id="entity-a-initial",
        revision_number=0,
        source_ref="source:panel",
        provenance_ref="artifact:panel:a:3",
        availability_rule_version="release-v1",
        dimensions=dimensions,
    )
    outcome_observation = ObservationInput(
        field_ref=schema.field_ref("outcome"),
        value=4.0,
        reference_time=ORIGIN + DAY * 4,
        available_at=ORIGIN + DAY * 4,
        vintage_id="entity-a-outcome",
        revision_number=0,
        source_ref="source:panel",
        provenance_ref="artifact:panel:a:outcome:4",
        availability_rule_version="release-v1",
        dimensions=dimensions,
    )
    catalog = DataCatalogSnapshot(
        schema.environment_id,
        (
            ObservationRegistrar().register(
                schema,
                (predictor_observation, outcome_observation),
            ),
        ),
    )
    information = InformationSetBuilder().build(
        catalog,
        decision_time=ORIGIN + DAY * 3,
        requested_fields=(schema.field_ref("x1"),),
    )
    prediction = SystemPredictor(registry).predict(system, fitted, information)

    assert prediction.dimensions == dimensions
    with pytest.raises(ValueError, match="not yet complete"):
        OutcomeRecorder().record(
            prediction,
            target,
            catalog=catalog,
            decision_information=information,
            current_time=prediction.decision_time,
        )
    mature_at = prediction.decision_time + DAY
    outcome = OutcomeRecorder().record(
        prediction,
        target,
        catalog=catalog,
        decision_information=information,
        current_time=mature_at,
    )
    assert outcome.prediction_id == prediction.prediction_id
    assert outcome.target_id == target.identity


def test_forged_feature_series_has_no_public_prediction_authority() -> None:
    """Caller-authored values cannot bypass InformationSet legality to create a record."""
    schema = _schema()
    target = _target(schema)
    feature = _feature(schema, "x1")
    system = _system(schema, target, (feature,))
    rows = tuple(_row(schema, target, day, float(day), float(day)) for day in range(3))
    registry = FittedSystemRegistry()
    _ = SystemTrainer(registry=registry).fit(system, _window(_sample(schema, target, rows), rows))
    forged_value = FeatureValue(
        decision_time=ORIGIN + DAY * 3,
        dimensions=(),
        information_set_id="copied-information-id",
        value=FORGED_VALUE,
        status=FeatureValueStatus.PRESENT,
        source_observation_ids=("forged-observation",),
        failure_detail=None,
    )
    forged = FeatureSeries(
        series_id="caller-supplied-unverified-id",
        definition_id=feature.identity,
        environment_id=schema.environment_id,
        compiled_expression_id=FeatureCompiler().compile(feature).identity,
        values=(forged_value,),
        fitted_state_ids=(),
        status=FeatureSeriesStatus.READY,
    )
    predictor = SystemPredictor(registry)

    assert forged.values[0].value == FORGED_VALUE
    assert not hasattr(predictor, "predict_series")


def test_failed_development_trial_is_visible_without_evidence_fallback() -> None:
    """Evaluator records the failed path and returns no development success object."""
    schema = _schema()
    target = _target(schema)
    rows = tuple(_row(schema, target, day, float(day), float(day)) for day in range(7))
    protocol = _protocol()
    system = _system(
        schema,
        target,
        (_feature(schema, "x1"),),
        model=_model(algorithm="svm"),
        evaluation_protocol_id=protocol.identity,
    )
    evaluator = DevelopmentEvaluator()

    with pytest.raises(TrainingBlocked):
        evaluator.evaluate(system, _sample(schema, target, rows), protocol)

    assert tuple(item.status for item in evaluator.ledger.records) == (
        TrialStatus.ATTEMPTED,
        TrialStatus.FAILED,
    )


def test_protocol_mismatch_and_fold_failure_remain_in_trial_history() -> None:
    """Precondition and fold failures are attempted trials, never invisible calls."""
    schema = _schema()
    target = _target(schema)
    protocol = _protocol()
    mismatched = _system(schema, target, (_feature(schema, "x1"),))
    rows = tuple(_row(schema, target, day, float(day), float(day)) for day in range(7))
    mismatch_evaluator = DevelopmentEvaluator()

    with pytest.raises(TrainingBlocked, match="evaluation protocol"):
        mismatch_evaluator.evaluate(mismatched, _sample(schema, target, rows), protocol)
    assert tuple(item.status for item in mismatch_evaluator.ledger.records) == (
        TrialStatus.ATTEMPTED,
        TrialStatus.FAILED,
    )

    bound = _system(
        schema,
        target,
        (_feature(schema, "x1"),),
        evaluation_protocol_id=protocol.identity,
    )
    fold_evaluator = DevelopmentEvaluator()
    with pytest.raises(TrainingBlocked, match="cannot construct"):
        fold_evaluator.evaluate(bound, _sample(schema, target, rows[:2]), protocol)
    assert tuple(item.status for item in fold_evaluator.ledger.records) == (
        TrialStatus.ATTEMPTED,
        TrialStatus.FAILED,
    )
