"""Contract and adversarial tests for immutable scientific formalization."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import cast

import pytest

from research_agent.data_foundation import (
    CalendarUnit,
    DataCatalogSnapshot,
    DatasetSchema,
    FieldDefinition,
    IncompleteOutcomePolicy,
    InformationSet,
    InformationSetBuilder,
    MaturityPolicy,
    MonthEndPolicy,
    ObservationInput,
    ObservationRegistrar,
    OffsetAnchor,
    OutcomeAlignment,
    TargetDefinition,
    TargetKind,
    TemporalOffset,
    TimezonePolicy,
)
from research_agent.exploration import (
    AnalysisStatus,
    ExecutionProvenance,
    StructuredObservation,
)
from research_agent.formalization import (
    CompiledFeatureExpression,
    EnsembleDefinition,
    FailureAction,
    FeatureAlignment,
    FeatureCompiler,
    FeatureDefinition,
    FeatureExpression,
    FeatureMaterializationError,
    FeatureMaterializer,
    FeatureSet,
    FeatureValueStatus,
    FittedStateRequiredError,
    FittedTransformState,
    HistoryKind,
    HistorySemantics,
    InvalidFittedStateError,
    MaterialChange,
    ModelDefinition,
    PredictiveSystemDefinition,
    TemporalMapping,
    record_material_change,
)

DAY = timedelta(days=1)
ELAPSED_DAY = TemporalOffset.elapsed(DAY)
ZERO_OFFSET = TemporalOffset.zero()
ORIGIN = datetime(2024, 1, 1, tzinfo=UTC)


def _schema() -> DatasetSchema:
    return DatasetSchema(
        dataset_id="series",
        version="schema-v1",
        environment_id="environment-v1",
        provenance_ref="artifact:schema-v1",
        fields=(
            FieldDefinition("signal", "Signal", "float", "index", (), "A legal signal."),
            FieldDefinition("other", "Other", "float", "index", (), "A second signal."),
            FieldDefinition("outcome", "Outcome", "float", "units", (), "Future outcome."),
        ),
    )


def _row(
    schema: DatasetSchema,
    field_id: str,
    value: float,
    reference_day: int,
    available_day: int,
) -> ObservationInput:
    return ObservationInput(
        field_ref=schema.field_ref(field_id),
        value=value,
        reference_time=ORIGIN + DAY * reference_day,
        available_at=ORIGIN + DAY * available_day,
        vintage_id=f"vintage-{field_id}-{available_day}",
        revision_number=0,
        source_ref="source:fixture",
        provenance_ref=f"artifact:{field_id}:{reference_day}:{available_day}",
        availability_rule_version="release-v1",
        dimensions=(),
    )


def _catalog(schema: DatasetSchema, *rows: ObservationInput) -> DataCatalogSnapshot:
    registration = ObservationRegistrar().register(schema, tuple(rows))
    return DataCatalogSnapshot(schema.environment_id, (registration,))


def _information(
    schema: DatasetSchema,
    *,
    day: int,
    include_future: bool = False,
) -> InformationSet:
    catalog = _catalog(
        schema,
        _row(schema, "signal", 1.0, 0, 0),
        _row(schema, "signal", 2.0, 1, 1),
        _row(schema, "signal", 100.0, 2, 3),
    )
    built = InformationSetBuilder().build(
        catalog,
        decision_time=ORIGIN + DAY * day,
        requested_fields=(schema.field_ref("signal"),),
    )
    if not include_future:
        return built
    future = catalog.observations[-1]
    return replace(built, observations=(*built.observations, future))


def _history(
    *,
    kind: HistoryKind = HistoryKind.EXPANDING,
    width: timedelta | None = None,
) -> HistorySemantics:
    return HistorySemantics(
        kind=kind,
        warm_up=ZERO_OFFSET,
        fixed_width=TemporalOffset.elapsed(width) if width is not None else None,
        initialization="use only declared legal observations",
        truncation="strictly apply the declared history boundary",
    )


def _feature(  # noqa: PLR0913
    schema: DatasetSchema,
    *,
    name: str = "signal_feature",
    version: int = 1,
    parent_definition_id: str | None = None,
    expression: FeatureExpression | None = None,
    history: HistorySemantics | None = None,
    fitted_procedures: tuple[tuple[str, str], ...] = (),
    evidence_refs: tuple[str, ...] = ("analysis:evidence-1",),
) -> FeatureDefinition:
    field = schema.field_ref("signal")
    return FeatureDefinition(
        name=name,
        version=version,
        parent_definition_id=parent_definition_id,
        environment_id=schema.environment_id,
        dependencies=(field,),
        expression=expression or FeatureExpression.field(field),
        temporal_mapping=TemporalMapping(FeatureAlignment.LATEST_AT_OR_BEFORE, ZERO_OFFSET),
        history=history or _history(),
        output_data_type="float",
        output_units="index",
        dimensions=(),
        missing_input=FailureAction.RETURN_MISSING,
        invalid_domain=FailureAction.FAIL,
        insufficiency=FailureAction.RETURN_MISSING,
        failure="fail without substitution",
        hypothesis="the declared signal may predict the target",
        information_intent="retain the legally available signal level",
        fitted_state_procedures=fitted_procedures,
        evidence_refs=evidence_refs,
        candidate_ancestry=("candidate:feature-1",),
        provenance_refs=(schema.provenance_ref,),
    )


def _target(schema: DatasetSchema, *, version: int = 1) -> TargetDefinition:
    return TargetDefinition(
        task_id="task-v1",
        task_version=1,
        task_semantic_digest="task-semantic-v1",
        confirmed_task_horizon_id=ELAPSED_DAY.identity,
        version=version,
        parent_target_id=None if version == 1 else "target:parent",
        field_ref=schema.field_ref("outcome"),
        kind=TargetKind.ENDPOINT,
        horizon=ELAPSED_DAY,
        outcome_start_offset=ZERO_OFFSET,
        outcome_end_offset=ELAPSED_DAY,
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


def _model(*, algorithm: str = "linear", version: int = 1) -> ModelDefinition:
    return ModelDefinition(
        name="candidate-model",
        version=version,
        parent_definition_id=None if version == 1 else "model:parent",
        environment_id="environment-v1",
        algorithm=algorithm,
        hyperparameters=(("regularization", "none"),),
        preprocessing_refs=("feature-set-bound",),
        selection_procedure_ref="selection:none",
        randomness_policy="deterministic",
        training_requirement_refs=("trainer:batch-v1",),
        evidence_refs=("development:model-analysis",),
        candidate_ancestry=("candidate:model-1",),
        provenance_refs=("implementation:model-library-v1",),
    )


def _feature_set(feature: FeatureDefinition) -> FeatureSet:
    return FeatureSet(
        name="selected-features",
        version=1,
        parent_feature_set_id=None,
        environment_id=feature.environment_id,
        members=(feature,),
        selection_ancestry=("trial:feature-selection-1",),
        provenance_refs=("research:selection-decision",),
    )


def _system(  # noqa: PLR0913
    target: TargetDefinition,
    feature_set: FeatureSet,
    model: ModelDefinition,
    *,
    ensemble: EnsembleDefinition | None = None,
    training_protocol_id: str = "training:expanding-v1",
    evaluation_protocol_id: str = "evaluation:temporal-v1",
) -> PredictiveSystemDefinition:
    return PredictiveSystemDefinition(
        name="candidate-system",
        version=1,
        parent_system_id=None,
        environment_id="environment-v1",
        target=target,
        feature_set=feature_set,
        models=(model,),
        ensemble=ensemble,
        data_protocol_id="data:registered-as-known-v1",
        training_protocol_id=training_protocol_id,
        evaluation_protocol_id=evaluation_protocol_id,
        evidence_refs=("development:system-evidence",),
        candidate_ancestry=("candidate:system-1",),
        provenance_refs=("research:system-assembly",),
    )


def test_exploratory_evidence_is_not_automatically_a_feature() -> None:
    """A successful analysis remains evidence until a definition is explicitly authored."""
    observation = StructuredObservation(
        status=AnalysisStatus.SUCCEEDED,
        summary="interesting correlation",
        details={"correlation": 0.9},
        stdout_preview="",
        stderr_preview="",
        warnings=(),
        recoverable=False,
        provenance=ExecutionProvenance(
            action_id="analysis-1",
            code_sha256="abc",
            accesses=(),
            dataset_refs=(),
            environment_refs=("environment-v1@1",),
            random_seed=None,
            execution_status=AnalysisStatus.SUCCEEDED,
        ),
        artifact_refs=(),
    )

    with pytest.raises(TypeError, match="FeatureDefinition"):
        FeatureSet(
            name="illegal",
            version=1,
            parent_feature_set_id=None,
            environment_id="environment-v1",
            members=(cast("FeatureDefinition", observation),),
            selection_ancestry=("trial:1",),
            provenance_refs=("research:selection",),
        )
    with pytest.raises(ValueError, match="evidence ancestry"):
        _feature(_schema(), evidence_refs=())


def test_materialization_can_neither_read_future_release_nor_accept_forged_information() -> None:
    """Only exact observations already admitted to I_t can reach an expression."""
    schema = _schema()
    definition = _feature(schema)
    compiled = FeatureCompiler().compile(definition)
    materializer = FeatureMaterializer()

    legal = materializer.materialize(definition, compiled, (_information(schema, day=2),))
    expected_latest_legal_value = 2.0
    assert legal.values[0].value == expected_latest_legal_value
    assert legal.values[0].status is FeatureValueStatus.PRESENT

    with pytest.raises(ValueError, match="information-set identity does not match content"):
        _information(schema, day=2, include_future=True)


def test_materialization_preserves_exact_dimension_slice() -> None:
    """Rows for different entities cannot be collapsed into one feature value."""
    schema = DatasetSchema(
        dataset_id="panel",
        version="schema-v1",
        environment_id="environment-v1",
        provenance_ref="artifact:panel-schema",
        fields=(
            FieldDefinition(
                "signal",
                "Panel signal",
                "float",
                "index",
                ("entity",),
                "Signal indexed by entity.",
            ),
        ),
    )
    field = schema.field_ref("signal")
    rows = tuple(
        ObservationInput(
            field_ref=field,
            value=value,
            reference_time=ORIGIN,
            available_at=ORIGIN,
            vintage_id=f"initial-{entity}",
            revision_number=0,
            source_ref="source:panel",
            provenance_ref=f"artifact:panel:{entity}",
            availability_rule_version="release-v1",
            dimensions=(("entity", entity),),
        )
        for entity, value in (("a", 1.0), ("b", 9.0))
    )
    catalog = _catalog(schema, *rows)
    information = InformationSetBuilder().build(
        catalog,
        decision_time=ORIGIN,
        requested_fields=(field,),
    )

    feature_a = replace(_feature(schema), dimensions=(("entity", "a"),))
    feature_b = replace(_feature(schema), dimensions=(("entity", "b"),))
    series = FeatureMaterializer().materialize(
        feature_a,
        FeatureCompiler().compile(feature_a),
        (information,),
    )

    assert series.values[0].dimensions == (("entity", "a"),)
    assert series.values[0].value == 1.0
    assert series.values[0].source_observation_ids == (catalog.observations[0].observation_id,)
    assert feature_a.identity != feature_b.identity


def test_same_name_versions_are_distinct_and_cannot_collide_in_one_feature_set() -> None:
    """Friendly names never resolve or auto-upgrade exact feature identity."""
    schema = _schema()
    first = _feature(schema)
    second = _feature(
        schema,
        version=2,
        parent_definition_id=first.identity,
        expression=FeatureExpression.lag(
            FeatureExpression.field(schema.field_ref("signal")), ELAPSED_DAY
        ),
    )

    assert first.name == second.name
    assert first.identity != second.identity
    with pytest.raises(ValueError, match="duplicate output name"):
        FeatureSet(
            name="ambiguous",
            version=1,
            parent_feature_set_id=None,
            environment_id=schema.environment_id,
            members=(first, second),
            selection_ancestry=("trial:1",),
            provenance_refs=("research:selection",),
        )


def test_expanding_and_fixed_width_history_have_different_identity() -> None:
    """Finite-history behavior is scientific meaning rather than implementation trivia."""
    schema = _schema()
    expanding = _feature(schema, history=_history())
    fixed = _feature(
        schema,
        history=_history(kind=HistoryKind.FIXED_WIDTH, width=DAY * 30),
    )

    assert expanding.identity != fixed.identity


def test_compiler_rejects_an_undeclared_field_dependency() -> None:
    """Expression compilation cannot widen a definition's exact FieldRef scope."""
    schema = _schema()
    expression = FeatureExpression.add(
        FeatureExpression.field(schema.field_ref("signal")),
        FeatureExpression.field(schema.field_ref("other")),
    )
    definition = _feature(schema, expression=expression)

    with pytest.raises(ValueError, match="dependencies"):
        FeatureCompiler().compile(definition)


def test_compiler_and_evaluator_preserve_causal_operation_order() -> None:
    """Compilation evaluates the exact non-commutative causal expression."""
    schema = _schema()
    field = FeatureExpression.field(schema.field_ref("signal"))
    expression = FeatureExpression.divide(
        FeatureExpression.difference(field, ELAPSED_DAY),
        FeatureExpression.lag(field, ELAPSED_DAY),
    )
    definition = _feature(schema, expression=expression)

    series = FeatureMaterializer().materialize(
        definition,
        FeatureCompiler().compile(definition),
        (_information(schema, day=1),),
    )

    assert series.values[0].value == 1.0


def test_calendar_feature_lag_is_not_replaced_by_thirty_elapsed_days() -> None:
    """A calendar-month feature boundary reaches Feb 29 while 30 elapsed days reaches Mar 1."""
    schema = _schema()
    field_ref = schema.field_ref("signal")
    rows = (
        ObservationInput(
            field_ref,
            2.0,
            datetime(2024, 2, 29, tzinfo=UTC),
            datetime(2024, 2, 29, tzinfo=UTC),
            "february",
            0,
            "source:calendar",
            "artifact:february",
            "release-v1",
            (),
        ),
        ObservationInput(
            field_ref,
            3.0,
            datetime(2024, 3, 1, tzinfo=UTC),
            datetime(2024, 3, 1, tzinfo=UTC),
            "march",
            0,
            "source:calendar",
            "artifact:march",
            "release-v1",
            (),
        ),
    )
    information = InformationSetBuilder().build(
        _catalog(schema, *rows),
        decision_time=datetime(2024, 3, 31, tzinfo=UTC),
        requested_fields=(field_ref,),
    )
    calendar_month = TemporalOffset.calendar(
        count=1,
        unit=CalendarUnit.MONTH,
        anchor=OffsetAnchor.EXACT_INPUT,
        month_end_policy=MonthEndPolicy.PRESERVE,
        timezone_name="UTC",
        timezone_policy=TimezonePolicy.WALL_CLOCK_REJECT_TRANSITION,
    )
    calendar_definition = replace(
        _feature(
            schema,
            expression=FeatureExpression.lag(FeatureExpression.field(field_ref), calendar_month),
        ),
        temporal_mapping=TemporalMapping(FeatureAlignment.EXACT, ZERO_OFFSET),
    )
    elapsed_definition = replace(
        calendar_definition,
        expression=FeatureExpression.lag(
            FeatureExpression.field(field_ref), TemporalOffset.elapsed(timedelta(days=30))
        ),
    )

    calendar_series = FeatureMaterializer().materialize(
        calendar_definition,
        FeatureCompiler().compile(calendar_definition),
        (information,),
    )
    elapsed_series = FeatureMaterializer().materialize(
        elapsed_definition,
        FeatureCompiler().compile(elapsed_definition),
        (information,),
    )

    calendar_expected = 2.0
    elapsed_expected = 3.0
    assert calendar_definition.identity != elapsed_definition.identity
    assert calendar_series.values[0].value == calendar_expected
    assert elapsed_series.values[0].value == elapsed_expected


def test_materializer_rejects_a_compiled_graph_that_drops_declared_lag() -> None:
    """A forged graph cannot retain the definition ID while changing its mapping."""
    schema = _schema()
    field = FeatureExpression.field(schema.field_ref("signal"))
    definition = _feature(schema, expression=FeatureExpression.lag(field, ELAPSED_DAY))
    compiled = FeatureCompiler().compile(definition)
    forged = CompiledFeatureExpression(
        definition_id=compiled.definition_id,
        compiler_version=compiled.compiler_version,
        expression=field,
        operations=compiled.operations,
    )

    with pytest.raises(FeatureMaterializationError, match="exact supported representation"):
        FeatureMaterializer().materialize(
            definition,
            forged,
            (_information(schema, day=1),),
        )


def test_fitted_transform_requires_exact_window_bound_state() -> None:
    """A fitted node consumes trainer-supplied state and never creates its own."""
    schema = _schema()
    expression = FeatureExpression.standardize(
        FeatureExpression.field(schema.field_ref("signal")),
        state_slot="scale-state",
    )
    definition = _feature(
        schema,
        expression=expression,
        fitted_procedures=(("scale-state", "fit:standardize-v1"),),
    )
    compiled = FeatureCompiler().compile(definition)
    information = _information(schema, day=1)
    materializer = FeatureMaterializer()

    with pytest.raises(FittedStateRequiredError, match="scale-state"):
        materializer.materialize(definition, compiled, (information,))

    wrong_window = FittedTransformState(
        state_slot="scale-state",
        feature_definition_id="feature:other",
        environment_id=schema.environment_id,
        training_window_id="window:legal-1",
        information_set_id=information.information_set_id,
        fitted_through=ORIGIN,
        parameters=(("location", 1.0), ("scale", 1.0)),
        provenance_refs=("fit:record-1",),
    )
    with pytest.raises(InvalidFittedStateError, match="definition"):
        materializer.materialize(
            definition,
            compiled,
            (information,),
            fitted_states=(wrong_window,),
        )

    legal_state = replace(wrong_window, feature_definition_id=definition.identity)
    series = materializer.materialize(
        definition,
        compiled,
        (information,),
        fitted_states=(legal_state,),
    )
    assert series.values[0].value == 1.0
    assert series.fitted_state_ids == (legal_state.identity,)


def test_materializer_has_no_fit_hook_and_rejects_future_fitted_state() -> None:
    """Materialization cannot learn, update, or accept state learned after prediction time."""
    schema = _schema()
    expression = FeatureExpression.standardize(
        FeatureExpression.field(schema.field_ref("signal")),
        state_slot="scale-state",
    )
    definition = _feature(
        schema,
        expression=expression,
        fitted_procedures=(("scale-state", "fit:standardize-v1"),),
    )
    state = FittedTransformState(
        state_slot="scale-state",
        feature_definition_id=definition.identity,
        environment_id=schema.environment_id,
        training_window_id="window:future",
        information_set_id=_information(schema, day=1).information_set_id,
        fitted_through=ORIGIN + DAY * 2,
        parameters=(("location", 1.0), ("scale", 1.0)),
        provenance_refs=("fit:future",),
    )

    assert not hasattr(FeatureMaterializer(), "fit")
    with pytest.raises(InvalidFittedStateError, match="after decision time"):
        FeatureMaterializer().materialize(
            definition,
            FeatureCompiler().compile(definition),
            (_information(schema, day=1),),
            fitted_states=(state,),
        )


def test_material_change_creates_lineage_without_mutating_parent() -> None:
    """A changed mapping becomes a child identity and leaves the old object intact."""
    schema = _schema()
    parent = _feature(schema)
    child = _feature(
        schema,
        version=2,
        parent_definition_id=parent.identity,
        expression=FeatureExpression.lag(
            FeatureExpression.field(schema.field_ref("signal")), ELAPSED_DAY
        ),
    )

    change = record_material_change(
        parent,
        child,
        reason="declare one-day lag",
        provenance_refs=("research:revision-decision",),
    )

    assert isinstance(change, MaterialChange)
    assert change.parent_id == parent.identity
    assert change.child_id == child.identity
    assert parent.version == 1
    expected_child_version = 2
    assert child.version == expected_child_version


def test_model_definition_is_distinct_from_fitted_state() -> None:
    """A recipe has no learned coefficients or artifact identity."""
    model = _model()

    assert not hasattr(model, "learned_parameters")
    assert not hasattr(model, "fitted_artifact_ref")


def test_system_identity_changes_with_each_material_component() -> None:
    """The system digest binds exact target, feature, model, ensemble, and protocols."""
    schema = _schema()
    feature = _feature(schema)
    feature_set = _feature_set(feature)
    model = _model()
    base = _system(_target(schema), feature_set, model)
    other_feature = _feature(
        schema,
        version=2,
        parent_definition_id=feature.identity,
        expression=FeatureExpression.lag(
            FeatureExpression.field(schema.field_ref("signal")), ELAPSED_DAY
        ),
    )
    other_model = _model(algorithm="tree")
    ensemble = EnsembleDefinition(
        name="single-model-wrapper",
        version=1,
        parent_definition_id=None,
        environment_id=schema.environment_id,
        members=(model,),
        method="fixed_weighted_mean",
        fixed_weights=(1.0,),
        weight_learning_procedure_ref=None,
        evidence_refs=("development:ensemble",),
        candidate_ancestry=("candidate:ensemble-1",),
        provenance_refs=("research:ensemble",),
    )
    variants = (
        _system(_target(schema, version=2), feature_set, model),
        _system(_target(schema), _feature_set(other_feature), model),
        _system(_target(schema), feature_set, other_model),
        _system(_target(schema), feature_set, model, ensemble=ensemble),
        _system(
            _target(schema),
            feature_set,
            model,
            training_protocol_id="training:rolling-v1",
        ),
        _system(
            _target(schema),
            feature_set,
            model,
            evaluation_protocol_id="evaluation:blocked-v2",
        ),
    )

    assert all(item.identity != base.identity for item in variants)
    assert len({item.identity for item in (base, *variants)}) == len(variants) + 1
