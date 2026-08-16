"""Ordered development validation, diagnostics, and selection-aware evidence."""

# ruff: noqa: ARG002, D102, D105, D107, E501, PLR0917, PLR2004, SLF001, TRY301

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean
from threading import RLock
from typing import TYPE_CHECKING

from research_agent.data_foundation._identity import stable_identity
from research_agent.data_foundation.information import BoundaryStatus, InformationSetBuilder
from research_agent.data_foundation.windows import TrainingWindow
from research_agent.development.records import (
    DevelopmentProtocol,
    DevelopmentStatus,
    FitRecord,
    FittedPredictiveSystem,
    PredictionRecord,
    TemporalFold,
    TrainingBlocked,
    TrainingFailure,
    TrainingFailureCode,
    TrialLedger,
    TrialStatus,
)
from research_agent.development.training import SystemPredictor, SystemTrainer
from research_agent.development.training_information import TrainingInformationBuilder
from research_agent.formalization import (
    FeatureCompiler,
    FeatureMaterializer,
    FeatureSeriesStatus,
    FeatureValueStatus,
    FittedTransformState,
)

if TYPE_CHECKING:
    from research_agent.data_foundation.information import InformationSet
    from research_agent.data_foundation.observations import DataCatalogSnapshot
    from research_agent.data_foundation.samples import TrainingRow, TrainingSample
    from research_agent.data_foundation.schema import FieldRef
    from research_agent.data_foundation.targets import TargetDefinition
    from research_agent.formalization import FeatureDefinition, PredictiveSystemDefinition


@dataclass(frozen=True, slots=True)
class MetricEvidence:
    """Per-fold and aggregate development metric with explicit direction."""

    name: str
    fold_values: tuple[float, ...]
    aggregate: float
    direction: str
    sample_size: int


@dataclass(frozen=True, slots=True)
class FeatureEvidence:
    """One method's evidence about one feature; never an automatic selection action."""

    feature_definition_id: str
    method: str
    applicability: str
    metric_name: str
    baseline: float | None
    fold_values: tuple[float | None, ...]
    aggregate: float | None
    direction: str
    sample_size: int
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FeatureAnalysis:
    """Structured, potentially conflicting feature evidence at DEVELOPMENT status."""

    analysis_id: str
    candidate_id: str
    feature_set_id: str
    model_definition_ids: tuple[str, ...]
    protocol_id: str
    fold_ids: tuple[str, ...]
    data_id: str
    environment_id: str
    evidence: tuple[FeatureEvidence, ...]
    warnings: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    status: DevelopmentStatus = DevelopmentStatus.DEVELOPMENT

    def __post_init__(self) -> None:
        payload = {
            "candidate_id": self.candidate_id,
            "feature_set_id": self.feature_set_id,
            "model_definition_ids": self.model_definition_ids,
            "protocol_id": self.protocol_id,
            "fold_ids": self.fold_ids,
            "data_id": self.data_id,
            "environment_id": self.environment_id,
            "evidence": self.evidence,
            "warnings": self.warnings,
            "provenance_refs": self.provenance_refs,
            "status": self.status,
        }
        if self.analysis_id != stable_identity("feature-analysis", payload):
            msg = "feature-analysis identity does not match content"
            raise ValueError(msg)
        if self.status is not DevelopmentStatus.DEVELOPMENT:
            msg = "feature analysis cannot claim protected validation"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class DevelopmentEvidence:
    """Immutable out-of-fold evidence for one exact candidate trial."""

    evidence_id: str
    trial_id: str
    candidate_id: str
    protocol_id: str
    data_id: str
    environment_id: str
    folds: tuple[TemporalFold, ...]
    fit_records: tuple[FitRecord, ...]
    predictions: tuple[PredictionRecord, ...]
    outcomes: tuple[float, ...]
    metrics: tuple[MetricEvidence, ...]
    feature_analysis: FeatureAnalysis
    warnings: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    status: DevelopmentStatus = DevelopmentStatus.DEVELOPMENT

    def __post_init__(self) -> None:
        payload = {
            name: getattr(self, name) for name in self.__dataclass_fields__ if name != "evidence_id"
        }
        if self.evidence_id != stable_identity("development-evidence", payload):
            msg = "development-evidence identity does not match content"
            raise ValueError(msg)
        if self.status is not DevelopmentStatus.DEVELOPMENT:
            msg = "development evidence cannot claim protected validation"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class DevelopmentFreezeInputs:
    """Exact system and predeclared protocols bound by evaluator-issued evidence."""

    evidence_id: str
    system_id: str
    candidate_version: str
    ancestry_refs: tuple[str, ...]
    protocol_refs: tuple[str, ...]
    protected_evaluation_spec_ref: str | None
    validation_standard_ref: str | None
    environment_id: str


class DevelopmentEvidenceRegistry:
    """Evaluator-owned authority over exact development evidence."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._evidence: dict[str, DevelopmentEvidence] = {}
        self._freeze_inputs: dict[str, DevelopmentFreezeInputs] = {}

    def _issue(
        self,
        evidence: DevelopmentEvidence,
        *,
        definition: PredictiveSystemDefinition,
        protocol: DevelopmentProtocol,
        protected_evaluation_spec_ref: str | None,
        validation_standard_ref: str | None,
    ) -> DevelopmentEvidence:
        """Publish evidence only from the controlled evaluator path."""
        formal_fit = bool(evidence.fit_records) and all(
            record.training_information_bundle_id is not None
            and len(record.information_set_ids) == len(record.row_ids)
            and bool(record.feature_series_ids)
            and bool(record.compiled_feature_ids)
            for record in evidence.fit_records
        )
        freeze_inputs = (
            DevelopmentFreezeInputs(
                evidence_id=evidence.evidence_id,
                system_id=definition.identity,
                candidate_version=str(definition.version),
                ancestry_refs=definition.candidate_ancestry,
                protocol_refs=tuple(
                    dict.fromkeys(
                        (
                            definition.data_protocol_id,
                            definition.training_protocol_id,
                            definition.evaluation_protocol_id,
                            protocol.identity,
                            *(
                                (protected_evaluation_spec_ref, validation_standard_ref)
                                if protected_evaluation_spec_ref is not None
                                and validation_standard_ref is not None
                                else ()
                            ),
                        )
                    )
                ),
                protected_evaluation_spec_ref=protected_evaluation_spec_ref,
                validation_standard_ref=validation_standard_ref,
                environment_id=definition.environment_id,
            )
            if formal_fit
            else None
        )
        with self._lock:
            prior = self._evidence.get(evidence.evidence_id)
            prior_inputs = self._freeze_inputs.get(evidence.evidence_id)
            if (prior is not None and prior != evidence) or (
                prior_inputs is not None and prior_inputs != freeze_inputs
            ):
                msg = "development evidence identity was reused with changed semantics"
                raise ValueError(msg)
            self._evidence[evidence.evidence_id] = evidence
            if freeze_inputs is not None:
                self._freeze_inputs[evidence.evidence_id] = freeze_inputs
            return evidence

    def require_issued(self, evidence: DevelopmentEvidence) -> None:
        """Reject caller-rehashed development evidence."""
        with self._lock:
            if self._evidence.get(evidence.evidence_id) != evidence:
                msg = "development evidence was not issued by the required evaluator"
                raise ValueError(msg)

    def resolve_freeze_inputs(self, evidence: DevelopmentEvidence) -> DevelopmentFreezeInputs:
        """Resolve the evaluator-owned system/protocol binding for exact evidence."""
        self.require_issued(evidence)
        with self._lock:
            inputs = self._freeze_inputs.get(evidence.evidence_id)
            if inputs is None:
                msg = "development evidence has no evaluator-issued freeze inputs"
                raise ValueError(msg)
            return inputs


class TemporalFoldBuilder:
    """Construct ordered folds and remove only declared temporal contamination."""

    def build(
        self,
        sample: TrainingSample,
        target: TargetDefinition,
        protocol: DevelopmentProtocol,
    ) -> tuple[TemporalFold, ...]:
        if sample.status is not BoundaryStatus.READY:
            msg = "development folds require a READY TrainingSample"
            raise ValueError(msg)
        if sample.target_id != target.identity:
            msg = "sample and fold target identities differ"
            raise ValueError(msg)
        if sample.environment_id != protocol.environment_id:
            msg = "sample and protocol environment identities differ"
            raise ValueError(msg)
        rows = tuple(sorted(sample.rows, key=lambda row: (row.decision_time, row.dimensions)))
        folds: list[TemporalFold] = []
        start = protocol.minimum_training_rows
        ordinal = 0
        while start < len(rows):
            validation = rows[start : start + protocol.validation_rows]
            if not validation:
                break
            candidates = rows[:start]
            purged: tuple[TrainingRow, ...] = ()
            if protocol.purge_overlapping_labels:
                purged = tuple(
                    row
                    for row in candidates
                    if any(self._labels_overlap(target, row, held_out) for held_out in validation)
                )
            unavailable = tuple(
                row
                for row in candidates
                if row not in purged and row.label_matured_at > validation[0].decision_time
            )
            retained = tuple(
                row for row in candidates if row not in purged and row not in unavailable
            )
            embargoed: tuple[TrainingRow, ...] = ()
            if protocol.embargo is not None:
                validation_start = validation[0].decision_time
                embargoed = tuple(
                    row
                    for row in retained
                    if validation_start - row.decision_time <= protocol.embargo
                )
                retained = tuple(row for row in retained if row not in embargoed)
            payload = {
                "protocol_id": protocol.identity,
                "target_id": target.identity,
                "ordinal": ordinal,
                "training_row_ids": tuple(row.row_id for row in retained),
                "validation_row_ids": tuple(row.row_id for row in validation),
                "unavailable_row_ids": tuple(row.row_id for row in unavailable),
                "purged_row_ids": tuple(row.row_id for row in purged),
                "embargoed_row_ids": tuple(row.row_id for row in embargoed),
                "validation_start": validation[0].decision_time,
                "validation_end": validation[-1].decision_time,
            }
            folds.append(
                TemporalFold(
                    fold_id=stable_identity("temporal-fold", payload),
                    protocol_id=protocol.identity,
                    target_id=target.identity,
                    ordinal=ordinal,
                    training_row_ids=tuple(row.row_id for row in retained),
                    validation_row_ids=tuple(row.row_id for row in validation),
                    unavailable_row_ids=tuple(row.row_id for row in unavailable),
                    purged_row_ids=tuple(row.row_id for row in purged),
                    embargoed_row_ids=tuple(row.row_id for row in embargoed),
                    validation_start=validation[0].decision_time,
                    validation_end=validation[-1].decision_time,
                )
            )
            ordinal += 1
            start += protocol.step_rows
        if not folds:
            msg = "protocol cannot construct one temporal development fold"
            raise ValueError(msg)
        return tuple(folds)

    @staticmethod
    def _labels_overlap(
        target: TargetDefinition,
        left: TrainingRow,
        right: TrainingRow,
    ) -> bool:
        left_start, left_end = target.interval(left.decision_time)
        right_start, right_end = target.interval(right.decision_time)
        return left_start < right_end and right_start < left_end


class DevelopmentEvaluator:
    """Generate iterative OOF evidence while retaining every trial and failure."""

    _METHODS = frozenset({"permutation", "ablation", "single_feature"})

    def __init__(
        self,
        *,
        trainer: SystemTrainer | None = None,
        ledger: TrialLedger | None = None,
        evidence_registry: DevelopmentEvidenceRegistry | None = None,
    ) -> None:
        self.trainer = trainer or SystemTrainer()
        self.ledger = ledger or TrialLedger()
        self.evidence_registry = evidence_registry or DevelopmentEvidenceRegistry()

    def evaluate(  # noqa: PLR0913
        self,
        definition: PredictiveSystemDefinition,
        sample: TrainingSample,
        protocol: DevelopmentProtocol,
        *,
        parent_trial_ids: tuple[str, ...] = (),
        protected_evaluation_spec_ref: str | None = None,
        validation_standard_ref: str | None = None,
        catalog: DataCatalogSnapshot | None = None,
    ) -> DevelopmentEvidence:
        trial_payload = {
            "candidate_id": definition.identity,
            "protocol_id": protocol.identity,
            "data_id": sample.sample_id,
            "parent_trial_ids": parent_trial_ids,
            "attempt_ordinal": len(self.ledger.records),
        }
        trial_id = stable_identity("development-trial", trial_payload)
        self.ledger.append(
            trial_id=trial_id,
            candidate_id=definition.identity,
            protocol_id=protocol.identity,
            parent_trial_ids=parent_trial_ids,
            status=TrialStatus.ATTEMPTED,
            rationale="execute exact temporal development protocol",
        )
        try:
            self._validate_request(definition, protocol)
            self._validate_protected_predeclaration(
                protected_evaluation_spec_ref,
                validation_standard_ref,
            )
            folds = TemporalFoldBuilder().build(sample, definition.target, protocol)
            if catalog is not None and catalog.identity != sample.catalog_id:
                msg = "development catalog does not match the exact training sample"
                raise ValueError(msg)
            requested_fields = self._feature_dependencies(definition)
            row_index = {row.row_id: row for row in sample.rows}
            fits: list[FittedPredictiveSystem] = []
            fold_predictions: list[tuple[float, ...]] = []
            fold_outcomes: list[tuple[float, ...]] = []
            all_prediction_records: list[PredictionRecord] = []
            for fold in folds:
                train_rows = tuple(row_index[row_id] for row_id in fold.training_row_ids)
                if not train_rows:
                    msg = "purge/embargo left a fold with no legal training rows"
                    raise ValueError(msg)
                window = self._window(sample.sample_id, fold, train_rows)
                training_information = (
                    None
                    if catalog is None
                    else TrainingInformationBuilder(
                        self.trainer.training_information_registry
                    ).build(
                        catalog,
                        sample,
                        window,
                        requested_fields=requested_fields,
                    )
                )
                fitted = self.trainer.fit(definition, window, training_information)
                fits.append(fitted)
                validation_rows = tuple(row_index[row_id] for row_id in fold.validation_row_ids)
                if catalog is None:
                    predictions = tuple(
                        self._predict_row(definition, fitted, row) for row in validation_rows
                    )
                else:
                    predictor = SystemPredictor(self.trainer.registry)
                    predictions = tuple(
                        predictor.predict(
                            definition,
                            fitted,
                            self._information_for_row(catalog, definition, row),
                        )
                        for row in validation_rows
                    )
                outcomes = tuple(self._numeric_label(row) for row in validation_rows)
                fold_predictions.append(tuple(item.value for item in predictions))
                fold_outcomes.append(outcomes)
                all_prediction_records.extend(predictions)

            metrics = tuple(
                self._metric(name, fold_predictions, fold_outcomes)
                for name in protocol.metric_names
            )
            analysis = self._feature_analysis(
                definition,
                protocol,
                sample,
                folds,
                fits,
                fold_predictions,
                fold_outcomes,
                row_index,
                catalog,
            )
            provenance = (*protocol.provenance_refs, *definition.provenance_refs)
            warnings = (
                "development evidence is selection-exposed and is not protected validation",
                *(
                    ("row-local development without an authoritative catalog is non-promotable",)
                    if catalog is None
                    else ()
                ),
            )
            evidence_payload = {
                "trial_id": trial_id,
                "candidate_id": definition.identity,
                "protocol_id": protocol.identity,
                "data_id": sample.sample_id,
                "environment_id": definition.environment_id,
                "folds": folds,
                "fit_records": tuple(item.fit_record for item in fits),
                "predictions": tuple(all_prediction_records),
                "outcomes": tuple(value for fold in fold_outcomes for value in fold),
                "metrics": metrics,
                "feature_analysis": analysis,
                "warnings": warnings,
                "provenance_refs": provenance,
                "status": DevelopmentStatus.DEVELOPMENT,
            }
            evidence = DevelopmentEvidence(
                evidence_id=stable_identity("development-evidence", evidence_payload),
                trial_id=trial_id,
                candidate_id=definition.identity,
                protocol_id=protocol.identity,
                data_id=sample.sample_id,
                environment_id=definition.environment_id,
                folds=folds,
                fit_records=tuple(item.fit_record for item in fits),
                predictions=tuple(all_prediction_records),
                outcomes=tuple(value for fold in fold_outcomes for value in fold),
                metrics=metrics,
                feature_analysis=analysis,
                warnings=warnings,
                provenance_refs=provenance,
                status=DevelopmentStatus.DEVELOPMENT,
            )
        except TrainingBlocked as error:
            self.ledger.append(
                trial_id=trial_id,
                candidate_id=definition.identity,
                protocol_id=protocol.identity,
                parent_trial_ids=parent_trial_ids,
                status=TrialStatus.FAILED,
                rationale="exact fitting recipe failed without fallback",
                failure_id=error.failure.failure_id,
            )
            raise
        except (TypeError, ValueError) as error:
            failure = self._development_failure(definition, sample.sample_id, str(error))
            self.ledger.append(
                trial_id=trial_id,
                candidate_id=definition.identity,
                protocol_id=protocol.identity,
                parent_trial_ids=parent_trial_ids,
                status=TrialStatus.FAILED,
                rationale="development protocol could not execute exactly",
                failure_id=failure.failure_id,
            )
            raise TrainingBlocked(failure) from error
        self.ledger.append(
            trial_id=trial_id,
            candidate_id=definition.identity,
            protocol_id=protocol.identity,
            parent_trial_ids=parent_trial_ids,
            status=TrialStatus.SUCCEEDED,
            rationale="development evidence generated; no selection decision implied",
            evidence_refs=(evidence.evidence_id,),
        )
        return self.evidence_registry._issue(  # pyright: ignore[reportPrivateUsage]
            evidence,
            definition=definition,
            protocol=protocol,
            protected_evaluation_spec_ref=protected_evaluation_spec_ref,
            validation_standard_ref=validation_standard_ref,
        )

    @staticmethod
    def _validate_protected_predeclaration(
        evaluation_spec_ref: str | None,
        validation_standard_ref: str | None,
    ) -> None:
        """Require both exact downstream refs when protected evaluation is intended."""
        supplied = (evaluation_spec_ref is not None, validation_standard_ref is not None)
        if supplied == (False, False):
            return
        if supplied != (True, True) or not evaluation_spec_ref or not validation_standard_ref:
            msg = "protected evaluation spec and validation standard must be predeclared together"
            raise ValueError(msg)
        if evaluation_spec_ref == validation_standard_ref:
            msg = "protected evaluation spec and validation standard require distinct identities"
            raise ValueError(msg)

    @classmethod
    def _validate_request(
        cls,
        definition: PredictiveSystemDefinition,
        protocol: DevelopmentProtocol,
    ) -> None:
        if definition.environment_id != protocol.environment_id:
            msg = "candidate and protocol environment identities differ"
            raise ValueError(msg)
        if definition.evaluation_protocol_id != protocol.identity:
            msg = "candidate is not bound to this exact development evaluation protocol"
            raise ValueError(msg)
        unknown_methods = set(protocol.feature_analysis_methods) - cls._METHODS
        if unknown_methods:
            msg = f"unsupported feature-analysis methods: {sorted(unknown_methods)!r}"
            raise ValueError(msg)
        unknown_metrics = set(protocol.metric_names) - {"mse", "mae"}
        if unknown_metrics:
            msg = f"unsupported development metrics: {sorted(unknown_metrics)!r}"
            raise ValueError(msg)

    @staticmethod
    def _window(
        sample_id: str,
        fold: TemporalFold,
        rows: tuple[TrainingRow, ...],
    ) -> TrainingWindow:
        payload = {
            "sample_id": sample_id,
            "policy_id": f"development-fold:{fold.fold_id}",
            "row_ids": tuple(row.row_id for row in rows),
            "status": BoundaryStatus.READY,
            "insufficiency": None,
        }
        return TrainingWindow(
            window_id=stable_identity("training-window", payload),
            sample_id=sample_id,
            policy_id=f"development-fold:{fold.fold_id}",
            rows=rows,
            status=BoundaryStatus.READY,
            insufficiency=None,
        )

    def _predict_row(
        self,
        definition: PredictiveSystemDefinition,
        fitted: FittedPredictiveSystem,
        row: TrainingRow,
        *,
        override: tuple[float, ...] | None = None,
    ) -> PredictionRecord:
        self.trainer.registry.require_issued(fitted)
        if row.decision_time < fitted.fit_record.fitted_through:
            msg = "development prediction precedes the latest admitted label maturity"
            raise ValueError(msg)
        states = {
            feature.identity: {
                state.state_slot: dict(state.parameters)
                for state in fitted.transforms
                if state.feature_definition_id == feature.identity
            }
            for feature in definition.feature_set.members
        }
        vector = override or tuple(
            SystemTrainer.evaluate_row_expression(
                feature.expression,
                row.predictors,
                states[feature.identity],
            )
            for feature in definition.feature_set.members
        )
        predictions = tuple(
            SystemPredictor._infer_model(model, vector)  # pyright: ignore[reportPrivateUsage]
            for model in fitted.models
        )
        value = sum(
            weight * prediction
            for weight, prediction in zip(fitted.ensemble_weights, predictions, strict=True)
        )
        information_id = stable_identity(
            "training-row-information",
            {"row_id": row.row_id, "decision_time": row.decision_time},
        )
        feature_ids = tuple(feature.identity for feature in definition.feature_set.members)
        feature_series_ids = tuple(
            stable_identity(
                "development-row-feature",
                {
                    "row_id": row.row_id,
                    "feature_id": feature_id,
                    "fit_id": fitted.fit_record.fit_id,
                    "value": feature_value,
                },
            )
            for feature_id, feature_value in zip(feature_ids, vector, strict=True)
        )
        payload = {
            "fitted_system_id": fitted.fitted_system_id,
            "system_definition_id": definition.identity,
            "fit_record_id": fitted.fit_record.fit_id,
            "information_set_id": information_id,
            "feature_series_ids": feature_series_ids,
            "feature_definition_ids": feature_ids,
            "decision_time": row.decision_time,
            "dimensions": row.dimensions,
            "target_id": definition.target.identity,
            "value": value,
            "environment_id": definition.environment_id,
            "provenance_refs": (row.row_id, fitted.fit_record.fit_id),
            "status": DevelopmentStatus.DEVELOPMENT,
        }
        return PredictionRecord(
            prediction_id=stable_identity("prediction-record", payload),
            fitted_system_id=fitted.fitted_system_id,
            system_definition_id=definition.identity,
            fit_record_id=fitted.fit_record.fit_id,
            information_set_id=information_id,
            feature_series_ids=feature_series_ids,
            feature_definition_ids=feature_ids,
            decision_time=row.decision_time,
            dimensions=row.dimensions,
            target_id=definition.target.identity,
            value=value,
            environment_id=definition.environment_id,
            provenance_refs=(row.row_id, fitted.fit_record.fit_id),
            status=DevelopmentStatus.DEVELOPMENT,
        )

    def _feature_analysis(  # noqa: PLR0913
        self,
        definition: PredictiveSystemDefinition,
        protocol: DevelopmentProtocol,
        sample: TrainingSample,
        folds: tuple[TemporalFold, ...],
        fits: list[FittedPredictiveSystem],
        baseline_predictions: list[tuple[float, ...]],
        fold_outcomes: list[tuple[float, ...]],
        row_index: dict[str, TrainingRow],
        catalog: DataCatalogSnapshot | None,
    ) -> FeatureAnalysis:
        evidence: list[FeatureEvidence] = []
        baseline_mse = tuple(
            self._mse(predictions, outcomes)
            for predictions, outcomes in zip(
                baseline_predictions,
                fold_outcomes,
                strict=True,
            )
        )
        for feature_index, feature in enumerate(definition.feature_set.members):
            for method in protocol.feature_analysis_methods:
                fold_values: list[float | None] = []
                warnings: list[str] = []
                for fold, fitted, outcomes, baseline in zip(
                    folds,
                    fits,
                    fold_outcomes,
                    baseline_mse,
                    strict=True,
                ):
                    rows = tuple(row_index[row_id] for row_id in fold.validation_row_ids)
                    vectors = tuple(
                        self._row_vector(definition, fitted, row, catalog=catalog) for row in rows
                    )
                    if method == "permutation":
                        if len(vectors) < 2:
                            fold_values.append(None)
                            warnings.append("permutation requires at least two validation rows")
                            continue
                        rotated = (
                            *tuple(vector[feature_index] for vector in vectors[1:]),
                            vectors[0][feature_index],
                        )
                        changed = tuple(
                            (*vector[:feature_index], value, *vector[feature_index + 1 :])
                            for vector, value in zip(vectors, rotated, strict=True)
                        )
                        perturbed = tuple(self._infer_vector(fitted, vector) for vector in changed)
                        fold_values.append(self._mse(perturbed, outcomes) - baseline)
                    elif method == "ablation":
                        changed = tuple(
                            (*vector[:feature_index], 0.0, *vector[feature_index + 1 :])
                            for vector in vectors
                        )
                        perturbed = tuple(self._infer_vector(fitted, vector) for vector in changed)
                        fold_values.append(self._mse(perturbed, outcomes) - baseline)
                    else:
                        fold_values.append(
                            self._single_feature_mse(
                                definition,
                                fitted,
                                feature,
                                feature_index,
                                rows,
                                outcomes,
                                row_index,
                                fold,
                                catalog,
                            )
                        )
                        warnings.append(
                            "single-feature evidence intentionally omits interactions and substitutes"
                        )
                present = tuple(value for value in fold_values if value is not None)
                aggregate = fmean(present) if present else None
                is_dependence = method in {"permutation", "ablation"}
                evidence.append(
                    FeatureEvidence(
                        feature_definition_id=feature.identity,
                        method=method,
                        applicability=(
                            "out-of-fold predictive dependence"
                            if is_dependence
                            else "stand-alone out-of-fold predictive performance"
                        ),
                        metric_name="mse_change" if is_dependence else "mse",
                        baseline=fmean(baseline_mse),
                        fold_values=tuple(fold_values),
                        aggregate=aggregate,
                        direction="higher_is_more_dependent"
                        if is_dependence
                        else "lower_is_better",
                        sample_size=sum(len(item) for item in fold_outcomes),
                        warnings=tuple(dict.fromkeys(warnings)),
                    )
                )
        analysis_warnings = (
            "correlated substitutes may dilute permutation or ablation evidence",
            "conflicting methods are retained and do not mutate FeatureSet membership",
            "single-feature evidence can miss interactions",
        )
        payload = {
            "candidate_id": definition.identity,
            "feature_set_id": definition.feature_set.identity,
            "model_definition_ids": tuple(model.identity for model in definition.models),
            "protocol_id": protocol.identity,
            "fold_ids": tuple(fold.fold_id for fold in folds),
            "data_id": sample.sample_id,
            "environment_id": definition.environment_id,
            "evidence": tuple(evidence),
            "warnings": analysis_warnings,
            "provenance_refs": (*protocol.provenance_refs, sample.sample_id),
            "status": DevelopmentStatus.DEVELOPMENT,
        }
        return FeatureAnalysis(
            analysis_id=stable_identity("feature-analysis", payload),
            candidate_id=definition.identity,
            feature_set_id=definition.feature_set.identity,
            model_definition_ids=tuple(model.identity for model in definition.models),
            protocol_id=protocol.identity,
            fold_ids=tuple(fold.fold_id for fold in folds),
            data_id=sample.sample_id,
            environment_id=definition.environment_id,
            evidence=tuple(evidence),
            warnings=analysis_warnings,
            provenance_refs=(*protocol.provenance_refs, sample.sample_id),
            status=DevelopmentStatus.DEVELOPMENT,
        )

    def _single_feature_mse(  # noqa: PLR0913
        self,
        definition: PredictiveSystemDefinition,
        fitted: FittedPredictiveSystem,
        feature: FeatureDefinition,
        feature_index: int,
        validation_rows: tuple[TrainingRow, ...],
        outcomes: tuple[float, ...],
        row_index: dict[str, TrainingRow],
        fold: TemporalFold,
        catalog: DataCatalogSnapshot | None,
    ) -> float | None:
        model_definition = definition.models[0]
        if len(definition.models) != 1 or definition.ensemble is not None:
            return None
        training_rows = tuple(row_index[row_id] for row_id in fold.training_row_ids)
        training_vectors = tuple(
            (
                self._row_vector(
                    definition,
                    fitted,
                    row,
                    catalog=catalog,
                    training=True,
                )[feature_index],
            )
            for row in training_rows
        )
        labels = tuple(self._numeric_label(row) for row in training_rows)
        if model_definition.algorithm == "mean":
            predictions = (fmean(labels),) * len(validation_rows)
        else:
            parameters = dict(model_definition.hyperparameters)
            fit_intercept = parameters.get("fit_intercept", True)
            ridge = parameters.get("ridge", 0.0)
            if not isinstance(fit_intercept, bool) or isinstance(ridge, bool):
                return None
            try:
                coefficients, intercept = SystemTrainer.least_squares(
                    training_vectors,
                    labels,
                    fit_intercept=fit_intercept,
                    ridge=float(ridge) if isinstance(ridge, (int, float)) else 0.0,
                )
            except ValueError:
                return None
            validation_values = tuple(
                self._row_vector(definition, fitted, row, catalog=catalog)[feature_index]
                for row in validation_rows
            )
            predictions = tuple(intercept + coefficients[0] * value for value in validation_values)
        return self._mse(predictions, outcomes)

    @staticmethod
    def _row_vector(
        definition: PredictiveSystemDefinition,
        fitted: FittedPredictiveSystem,
        row: TrainingRow,
        *,
        catalog: DataCatalogSnapshot | None,
        training: bool = False,
    ) -> tuple[float, ...]:
        if catalog is not None:
            information = DevelopmentEvaluator._information_for_row(catalog, definition, row)
            values: list[float] = []
            for feature in definition.feature_set.members:
                states = tuple(
                    FittedTransformState(
                        state_slot=state.state_slot,
                        feature_definition_id=state.feature_definition_id,
                        environment_id=definition.environment_id,
                        training_window_id=state.training_window_id,
                        information_set_id=information.information_set_id,
                        fitted_through=state.fitted_through,
                        parameters=state.parameters,
                        provenance_refs=state.provenance_refs,
                    )
                    for state in fitted.transforms
                    if state.feature_definition_id == feature.identity
                )
                materializer = FeatureMaterializer()
                compiled = FeatureCompiler().compile(feature)
                series = (
                    materializer.materialize_training(
                        feature,
                        compiled,
                        (information,),
                        fitted_states=states,
                        training_window_id=fitted.fit_record.training_window_id,
                    )
                    if training
                    else materializer.materialize(
                        feature,
                        compiled,
                        (information,),
                        fitted_states=states,
                    )
                )
                value = series.values[0]
                if (
                    series.status is not FeatureSeriesStatus.READY
                    or value.status is not FeatureValueStatus.PRESENT
                    or value.value is None
                ):
                    msg = "development diagnostic lacks an exact formal feature value"
                    raise ValueError(msg)
                values.append(float(value.value))
            return tuple(values)
        states = {
            feature.identity: {
                state.state_slot: dict(state.parameters)
                for state in fitted.transforms
                if state.feature_definition_id == feature.identity
            }
            for feature in definition.feature_set.members
        }
        return tuple(
            SystemTrainer.evaluate_row_expression(
                feature.expression,
                row.predictors,
                states[feature.identity],
            )
            for feature in definition.feature_set.members
        )

    @staticmethod
    def _feature_dependencies(
        definition: PredictiveSystemDefinition,
    ) -> tuple[FieldRef, ...]:
        return tuple(
            dict.fromkeys(
                dependency
                for feature in definition.feature_set.members
                for dependency in feature.dependencies
            )
        )

    @staticmethod
    def _information_for_row(
        catalog: DataCatalogSnapshot,
        definition: PredictiveSystemDefinition,
        row: TrainingRow,
    ) -> InformationSet:
        information = InformationSetBuilder().build(
            catalog,
            decision_time=row.decision_time,
            requested_fields=DevelopmentEvaluator._feature_dependencies(definition),
        )
        if information.status is not BoundaryStatus.READY:
            msg = "development row lacks a READY formal InformationSet"
            raise ValueError(msg)
        return information

    @staticmethod
    def _infer_vector(fitted: FittedPredictiveSystem, vector: tuple[float, ...]) -> float:
        predictions = tuple(
            SystemPredictor._infer_model(model, vector)  # pyright: ignore[reportPrivateUsage]
            for model in fitted.models
        )
        return sum(
            weight * prediction
            for weight, prediction in zip(fitted.ensemble_weights, predictions, strict=True)
        )

    @staticmethod
    def _metric(
        name: str,
        fold_predictions: list[tuple[float, ...]],
        fold_outcomes: list[tuple[float, ...]],
    ) -> MetricEvidence:
        if name == "mse":
            values = tuple(
                DevelopmentEvaluator._mse(predictions, outcomes)
                for predictions, outcomes in zip(fold_predictions, fold_outcomes, strict=True)
            )
        elif name == "mae":
            values = tuple(
                fmean(
                    abs(prediction - outcome)
                    for prediction, outcome in zip(predictions, outcomes, strict=True)
                )
                for predictions, outcomes in zip(fold_predictions, fold_outcomes, strict=True)
            )
        else:
            msg = f"unsupported metric {name!r}; no metric fallback exists"
            raise ValueError(msg)
        return MetricEvidence(
            name=name,
            fold_values=values,
            aggregate=fmean(values),
            direction="lower_is_better",
            sample_size=sum(len(item) for item in fold_outcomes),
        )

    @staticmethod
    def _mse(predictions: tuple[float, ...], outcomes: tuple[float, ...]) -> float:
        return fmean(
            (prediction - outcome) ** 2
            for prediction, outcome in zip(predictions, outcomes, strict=True)
        )

    @staticmethod
    def _numeric_label(row: TrainingRow) -> float:
        if isinstance(row.label, bool) or not isinstance(row.label, (int, float)):
            msg = "development metrics require numeric labels"
            raise TypeError(msg)
        return float(row.label)

    @staticmethod
    def _development_failure(
        definition: PredictiveSystemDefinition,
        sample_id: str,
        detail: str,
    ) -> TrainingFailure:
        return TrainingFailure.create(
            TrainingFailureCode.FIT_FAILED,
            system_definition_id=definition.identity,
            training_window_id=f"development-sample:{sample_id}",
            detail=detail,
            provenance_refs=definition.provenance_refs,
        )
