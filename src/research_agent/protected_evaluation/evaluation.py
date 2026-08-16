"""Pure protected measurement, independent validation, and finding publication."""

# ruff: noqa: C901, D105, D107, PLR0912, PLR0913, PLR0915

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from statistics import fmean, pstdev
from threading import RLock
from typing import TYPE_CHECKING

from research_agent.data_foundation._identity import stable_identity
from research_agent.protected_evaluation.idempotency import PrivilegedOperationCoordinator
from research_agent.protected_evaluation.ledger import LedgerEntry, ResearchLedger
from research_agent.protected_evaluation.protocols import (
    ClaimDefinition,
    CriterionComparison,
    EvaluationSpec,
    MetricName,
    PromotionStandard,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from research_agent.data_foundation.observations import DimensionValues
    from research_agent.protected_evaluation.execution import BacktestRun

from research_agent.protected_evaluation.execution import BacktestRunRegistry, BacktestRunStatus


@dataclass(frozen=True, slots=True)
class MetricResult:
    """One declared metric, including insufficiency instead of favorable fallback."""

    name: MetricName
    value: float | None
    sample_size: int
    denominator: int
    warning: str | None

    def __post_init__(self) -> None:
        if self.value is not None and not isfinite(self.value):
            msg = "metric values must be finite or explicitly insufficient"
            raise ValueError(msg)
        if min(self.sample_size, self.denominator) < 0 or self.sample_size > self.denominator:
            msg = "metric sample size must be within its declared denominator"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class TimeErrorView:
    """Per-time error retained for temporal and concentration inspection."""

    decision_time: datetime
    dimensions: DimensionValues
    prediction: float
    outcome: float
    absolute_error: float
    squared_error: float

    def __post_init__(self) -> None:
        if not all(
            isfinite(value)
            for value in (
                self.prediction,
                self.outcome,
                self.absolute_error,
                self.squared_error,
            )
        ):
            msg = "per-time evidence values must be finite"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class DimensionMetricView:
    """Task-neutral error view for one exact dimension slice."""

    dimensions: DimensionValues
    sample_size: int
    mse: float
    mae: float

    def __post_init__(self) -> None:
        if self.sample_size < 0 or not all(isfinite(value) for value in (self.mse, self.mae)):
            msg = "dimension metrics must be finite with a non-negative sample size"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class FailureCount:
    """Explicit count of a typed execution failure."""

    code: str
    count: int


@dataclass(frozen=True, slots=True)
class StabilityView:
    """Temporal dispersion and rolling error behavior."""

    absolute_error_stddev: float | None
    rolling_mse: tuple[float, ...]

    def __post_init__(self) -> None:
        if (
            self.absolute_error_stddev is not None and not isfinite(self.absolute_error_stddev)
        ) or any(not isfinite(value) for value in self.rolling_mse):
            msg = "stability values must be finite or explicitly unavailable"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class ConcentrationView:
    """Share of total squared error carried by the worst decision."""

    maximum_squared_error_share: float | None
    worst_decision_time: datetime | None

    def __post_init__(self) -> None:
        if self.maximum_squared_error_share is not None and not isfinite(
            self.maximum_squared_error_share
        ):
            msg = "concentration values must be finite or explicitly unavailable"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    """Immutable multidimensional measurement of a sealed run."""

    report_id: str
    run_id: str
    request_id: str
    frozen_system_id: str
    system_id: str
    target_id: str
    scenario_id: str
    scenario_kind: str
    run_status: BacktestRunStatus
    execution_valid: bool
    evaluation_spec_id: str
    validation_standard_ref: str
    claim_ref: str
    environment_ref: str
    metrics: tuple[MetricResult, ...]
    per_time: tuple[TimeErrorView, ...]
    per_dimension: tuple[DimensionMetricView, ...]
    failures: tuple[FailureCount, ...]
    stability: StabilityView
    concentration: ConcentrationView
    trial_ancestry_refs: tuple[str, ...]
    exposure_ref: str | None
    caveats: tuple[str, ...]
    measured_at: datetime
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        expected_validity = self.run_status in {
            BacktestRunStatus.COMPLETED,
            BacktestRunStatus.COMPLETED_WITH_FAILURES,
        }
        if self.execution_valid is not expected_validity:
            msg = "report execution validity must reflect the exact sealed run status"
            raise ValueError(msg)
        if self.report_id != stable_identity("evaluation-report", _without_id(self)):
            msg = "evaluation report identity does not match content"
            raise ValueError(msg)

    def metric(self, name: MetricName) -> MetricResult:
        """Resolve one exact declared measurement without a default."""
        matches = tuple(item for item in self.metrics if item.name is name)
        if len(matches) != 1:
            msg = f"evaluation report does not contain exact metric {name.value!r}"
            raise KeyError(msg)
        return matches[0]


class EvaluationReportRegistry:
    """Evaluator-owned authoritative publication history for reports."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._reports: dict[str, EvaluationReport] = {}
        self._publication_ids: dict[str, str] = {}

    def _issue(
        self,
        report: EvaluationReport,
        *,
        publication: LedgerEntry,
        ledger: ResearchLedger,
    ) -> EvaluationReport:
        if (
            not ledger.authoritative(publication)
            or publication.event_type != "evaluation.run-measured"
            or publication.subject_id != report.report_id
        ):
            msg = "evaluation-report issuance requires its exact evaluator event"
            raise ValueError(msg)
        with self._lock:
            prior = self._reports.get(report.report_id)
            if prior is not None and prior != report:
                msg = "evaluation-report identity was reused with changed semantics"
                raise ValueError(msg)
            self._reports[report.report_id] = report
            self._publication_ids[report.report_id] = publication.entry_id
            return report

    def require_issued(self, report: EvaluationReport) -> None:
        """Reject a rehashed caller report not published by this evaluator."""
        with self._lock:
            if (
                self._reports.get(report.report_id) != report
                or report.report_id not in self._publication_ids
            ):
                msg = "evaluation report was not issued by the required evaluator"
                raise ValueError(msg)


class Evaluator:
    """Measure sealed evidence only; this class has no fit, trainer, or selection channel."""

    def __init__(
        self,
        *,
        ledger: ResearchLedger,
        runs: BacktestRunRegistry,
        clock: Callable[[], datetime],
        reports: EvaluationReportRegistry | None = None,
        operations: PrivilegedOperationCoordinator | None = None,
    ) -> None:
        self._ledger = ledger
        self._runs = runs
        self._clock = clock
        self._reports = reports or EvaluationReportRegistry()
        self._operations = operations or PrivilegedOperationCoordinator()

    def measure(self, run: BacktestRun, spec: EvaluationSpec) -> EvaluationReport:
        """Compute only predeclared stdlib metrics and multidimensional views."""
        self._runs.require_issued(run)
        if run.evaluation_spec_ref != spec.identity:
            msg = "sealed run and EvaluationSpec identities differ"
            raise ValueError(msg)
        payload = (("run_id", run.run_id), ("evaluation_spec_id", spec.identity))
        return self._operations.execute(
            operation_key=f"evaluation:{run.run_id}:{spec.identity}",
            semantic_payload=payload,
            effect=lambda: self._measure_once(run, spec),
        ).result

    @property
    def issued_reports(self) -> EvaluationReportRegistry:
        """Expose exact measured reports to independent validation."""
        return self._reports

    def _measure_once(self, run: BacktestRun, spec: EvaluationSpec) -> EvaluationReport:
        total = len(run.decisions)
        per_time: list[TimeErrorView] = []
        non_finite_count = 0
        for decision in run.decisions:
            prediction = decision.prediction
            outcome = decision.outcome
            if prediction is None or outcome is None:
                continue
            if isinstance(outcome.value, bool) or not isinstance(outcome.value, (int, float)):
                continue
            realized = float(outcome.value)
            if not isfinite(prediction.value) or not isfinite(realized):
                non_finite_count += 1
                continue
            error = prediction.value - realized
            per_time.append(
                TimeErrorView(
                    decision_time=decision.decision_time,
                    dimensions=decision.dimensions,
                    prediction=prediction.value,
                    outcome=realized,
                    absolute_error=abs(error),
                    squared_error=error**2,
                )
            )
        pairs = tuple(per_time)
        metrics = tuple(self._metric(name, pairs, run, total) for name in spec.metric_names)
        dimensions: tuple[DimensionMetricView, ...] = ()
        if spec.include_dimension_views:
            by_dimension: dict[DimensionValues, list[TimeErrorView]] = {}
            for item in pairs:
                by_dimension.setdefault(item.dimensions, []).append(item)
            dimensions = tuple(
                DimensionMetricView(
                    dimensions=key,
                    sample_size=len(values),
                    mse=fmean(item.squared_error for item in values),
                    mae=fmean(item.absolute_error for item in values),
                )
                for key, values in sorted(by_dimension.items())
            )
        failure_counts: dict[str, int] = {}
        for failure in run.failures:
            failure_counts[failure.code.value] = failure_counts.get(failure.code.value, 0) + 1
        if non_finite_count:
            failure_counts["non_finite_evidence"] = non_finite_count
        failures = tuple(
            FailureCount(code, count) for code, count in sorted(failure_counts.items())
        )
        rolling: tuple[float, ...] = ()
        deviation: float | None = None
        if spec.include_stability and pairs:
            deviation = pstdev(item.absolute_error for item in pairs)
            rolling = tuple(
                fmean(
                    item.squared_error
                    for item in pairs[max(0, index - spec.rolling_window + 1) : index + 1]
                )
                for index in range(len(pairs))
            )
        concentration_value: float | None = None
        worst_time: datetime | None = None
        if spec.include_concentration and pairs:
            worst = max(pairs, key=lambda item: item.squared_error)
            total_squared = sum(item.squared_error for item in pairs)
            concentration_value = 0.0 if total_squared == 0 else worst.squared_error / total_squared
            worst_time = worst.decision_time
        caveats: list[str] = []
        if len(pairs) < total:
            caveats.append(
                "coverage is incomplete; failed or unavailable decisions remain in denominator"
            )
        if run.failures:
            caveats.append("the sealed run contains typed execution failures")
        if non_finite_count:
            caveats.append("non-finite prediction or outcome evidence is formally insufficient")
        if run.status not in {
            BacktestRunStatus.COMPLETED,
            BacktestRunStatus.COMPLETED_WITH_FAILURES,
        }:
            caveats.append("the sealed run is unsupported or incomplete and cannot be promoted")
        if not pairs:
            caveats.append("no paired numeric predictions and outcomes were measurable")
        if run.scenario_kind.value != "historical_walk_forward":
            caveats.append("scenario evidence is not a literal historical walk-forward result")
        measured_at = self._clock()
        report_payload = {
            "run_id": run.run_id,
            "request_id": run.request_id,
            "frozen_system_id": run.frozen_system_id,
            "system_id": run.system_id,
            "target_id": run.target_id,
            "scenario_id": run.scenario_id,
            "scenario_kind": run.scenario_kind.value,
            "run_status": run.status,
            "execution_valid": run.status
            in {BacktestRunStatus.COMPLETED, BacktestRunStatus.COMPLETED_WITH_FAILURES},
            "evaluation_spec_id": spec.identity,
            "validation_standard_ref": run.validation_standard_ref,
            "claim_ref": run.claim_ref,
            "environment_ref": run.environment_ref,
            "metrics": metrics,
            "per_time": pairs if spec.include_per_time else (),
            "per_dimension": dimensions,
            "failures": failures,
            "stability": StabilityView(deviation, rolling),
            "concentration": ConcentrationView(concentration_value, worst_time),
            "trial_ancestry_refs": run.ancestry_refs,
            "exposure_ref": run.exposure_id,
            "caveats": tuple(caveats),
            "measured_at": measured_at,
            "provenance_refs": (run.run_id, spec.identity, *run.provenance_refs),
        }
        report = EvaluationReport(
            report_id=stable_identity("evaluation-report", report_payload),
            run_id=run.run_id,
            request_id=run.request_id,
            frozen_system_id=run.frozen_system_id,
            system_id=run.system_id,
            target_id=run.target_id,
            scenario_id=run.scenario_id,
            scenario_kind=run.scenario_kind.value,
            run_status=run.status,
            execution_valid=run.status
            in {BacktestRunStatus.COMPLETED, BacktestRunStatus.COMPLETED_WITH_FAILURES},
            evaluation_spec_id=spec.identity,
            validation_standard_ref=run.validation_standard_ref,
            claim_ref=run.claim_ref,
            environment_ref=run.environment_ref,
            metrics=metrics,
            per_time=pairs if spec.include_per_time else (),
            per_dimension=dimensions,
            failures=failures,
            stability=StabilityView(deviation, rolling),
            concentration=ConcentrationView(concentration_value, worst_time),
            trial_ancestry_refs=run.ancestry_refs,
            exposure_ref=run.exposure_id,
            caveats=tuple(caveats),
            measured_at=measured_at,
            provenance_refs=(run.run_id, spec.identity, *run.provenance_refs),
        )
        publication = self._ledger.append(
            LedgerEntry.create(
                event_type="evaluation.run-measured",
                subject_id=report.report_id,
                status="measured",
                authority_id="evaluator",
                references=(run.run_id, spec.identity),
                reason_code="PREDECLARED_MEASUREMENTS",
                occurred_at=measured_at,
            )
        )
        self._reports._issue(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            report,
            publication=publication,
            ledger=self._ledger,
        )
        return report

    @staticmethod
    def _metric(
        name: MetricName,
        pairs: tuple[TimeErrorView, ...],
        run: BacktestRun,
        total: int,
    ) -> MetricResult:
        if name is MetricName.COVERAGE:
            return MetricResult(name, len(pairs) / total if total else 0.0, len(pairs), total, None)
        if name is MetricName.FAILURE_RATE:
            failed = sum(bool(item.failures) for item in run.decisions)
            return MetricResult(name, failed / total if total else 0.0, failed, total, None)
        if not pairs:
            return MetricResult(name, None, 0, total, "no paired numeric evidence")
        values = (
            tuple(item.squared_error for item in pairs)
            if name is MetricName.MSE
            else tuple(item.absolute_error for item in pairs)
        )
        return MetricResult(name, fmean(values), len(values), total, None)


class ValidationStatus(Enum):
    """Independent binary scientific promotion outcome."""

    PROMOTE = "promote"
    REJECT = "reject"


@dataclass(frozen=True, slots=True)
class ValidationDecision:
    """Immutable application of an exact standard under independent authority."""

    decision_id: str
    report_id: str
    standard_id: str
    status: ValidationStatus
    authority_id: str
    requester_id: str
    beneficiary_id: str
    reasons: tuple[str, ...]
    decided_at: datetime

    def __post_init__(self) -> None:
        if self.decision_id != stable_identity("validation-decision", _without_id(self)):
            msg = "validation decision identity does not match content"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class NegativeResult:
    """Append-only rejection retained with exact evidence and authority identity."""

    negative_id: str
    subject_id: str
    kind: str
    reason_codes: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    authority_id: str
    recorded_at: datetime

    def __post_init__(self) -> None:
        if self.negative_id != stable_identity("negative-result", _without_id(self)):
            msg = "negative result identity does not match content"
            raise ValueError(msg)


class NegativeResultRegistry:
    """Append-only negative evidence history with exact replay convergence."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: tuple[NegativeResult, ...] = ()
        self._by_id: dict[str, NegativeResult] = {}
        self._publication_ids: dict[str, str] = {}

    def _issue(
        self,
        record: NegativeResult,
        *,
        publication: LedgerEntry,
        ledger: ResearchLedger,
    ) -> NegativeResult:
        if (
            not ledger.authoritative(publication)
            or publication.event_type != "ledger.negative-result-recorded"
            or publication.subject_id != record.negative_id
        ):
            msg = "negative-result issuance requires its exact rejection event"
            raise ValueError(msg)
        with self._lock:
            prior = self._by_id.get(record.negative_id)
            if prior is not None:
                if prior != record:
                    msg = "negative-result identity was reused with changed semantics"
                    raise ValueError(msg)
                return prior
            self._by_id[record.negative_id] = record
            self._publication_ids[record.negative_id] = publication.entry_id
            self._records = (*self._records, record)
            return record

    def records(self) -> tuple[NegativeResult, ...]:
        """Return every rejection; no delete or winner-only projection exists."""
        with self._lock:
            return self._records


class ValidationDecisionRegistry:
    """Validator-owned authoritative publication history for decisions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._decisions: dict[str, ValidationDecision] = {}
        self._publication_ids: dict[str, str] = {}

    def _issue(
        self,
        decision: ValidationDecision,
        *,
        publication: LedgerEntry,
        ledger: ResearchLedger,
    ) -> ValidationDecision:
        if (
            not ledger.authoritative(publication)
            or publication.event_type != "finding.validation-decided"
            or publication.subject_id != decision.decision_id
        ):
            msg = "validation-decision issuance requires its exact validator event"
            raise ValueError(msg)
        with self._lock:
            prior = self._decisions.get(decision.decision_id)
            if prior is not None and prior != decision:
                msg = "validation-decision identity was reused with changed semantics"
                raise ValueError(msg)
            self._decisions[decision.decision_id] = decision
            self._publication_ids[decision.decision_id] = publication.entry_id
            return decision

    def require_issued(self, decision: ValidationDecision) -> None:
        """Reject a rehashed decision not published by this validator."""
        with self._lock:
            if (
                self._decisions.get(decision.decision_id) != decision
                or decision.decision_id not in self._publication_ids
            ):
                msg = "validation decision was not issued by the required validator"
                raise ValueError(msg)


class Validator:
    """Apply one exact predeclared standard without tuning or self-promotion."""

    def __init__(
        self,
        *,
        authorized_authority_ids: frozenset[str],
        authority_policy_ref: str,
        ledger: ResearchLedger,
        reports: EvaluationReportRegistry,
        negatives: NegativeResultRegistry,
        clock: Callable[[], datetime],
        decisions: ValidationDecisionRegistry | None = None,
        operations: PrivilegedOperationCoordinator | None = None,
    ) -> None:
        if not authorized_authority_ids or not authority_policy_ref:
            msg = "validator requires configured independent authority and policy"
            raise ValueError(msg)
        self._authorities = authorized_authority_ids
        self._authority_policy_ref = authority_policy_ref
        self._ledger = ledger
        self._reports = reports
        self._negatives = negatives
        self._clock = clock
        self._decisions = decisions or ValidationDecisionRegistry()
        self._operations = operations or PrivilegedOperationCoordinator()

    def validate(
        self,
        report: EvaluationReport,
        standard: PromotionStandard,
        *,
        authority_id: str,
        requester_id: str,
        beneficiary_id: str,
    ) -> ValidationDecision:
        """Return PROMOTE or REJECT; never rewrite thresholds from observed evidence."""
        self._reports.require_issued(report)
        if report.evaluation_spec_id != standard.evaluation_spec_id:
            msg = "promotion standard belongs to another EvaluationSpec"
            raise ValueError(msg)
        if report.validation_standard_ref != standard.identity:
            msg = "report was not predeclared against this promotion standard"
            raise ValueError(msg)
        if standard.authority_policy_ref != self._authority_policy_ref:
            msg = "promotion standard belongs to another validation authority policy"
            raise ValueError(msg)
        payload = (
            ("report_id", report.report_id),
            ("standard_id", standard.identity),
            ("authority_id", authority_id),
            ("requester_id", requester_id),
            ("beneficiary_id", beneficiary_id),
        )
        return self._operations.execute(
            operation_key=f"validation:{report.report_id}:{standard.identity}",
            semantic_payload=payload,
            effect=lambda: self._validate_once(
                report,
                standard,
                authority_id,
                requester_id,
                beneficiary_id,
            ),
        ).result

    @property
    def issued_decisions(self) -> ValidationDecisionRegistry:
        """Expose exact decisions to the finding publication authority."""
        return self._decisions

    def _validate_once(
        self,
        report: EvaluationReport,
        standard: PromotionStandard,
        authority_id: str,
        requester_id: str,
        beneficiary_id: str,
    ) -> ValidationDecision:
        reasons: list[str] = []
        if authority_id not in self._authorities:
            reasons.append("AUTHORITY_NOT_AUTHORIZED")
        if authority_id in {requester_id, beneficiary_id}:
            reasons.append("SELF_VALIDATION_DENIED")
        if report.scenario_kind != standard.required_scenario_kind.value:
            reasons.append("SCENARIO_KIND_MISMATCH")
        if not report.execution_valid or report.run_status in {
            BacktestRunStatus.INCOMPLETE,
            BacktestRunStatus.UNSUPPORTED,
        }:
            reasons.append("RUN_EXECUTION_INVALID")
        if not self._report_values_are_finite(report):
            reasons.append("NON_FINITE_REPORT_EVIDENCE")
        if any(failure.code == "non_finite_evidence" for failure in report.failures):
            reasons.append("NON_FINITE_SOURCE_EVIDENCE")
        for criterion in standard.criteria:
            result = report.metric(criterion.metric)
            if result.value is None:
                reasons.append(f"{criterion.metric.value}:INSUFFICIENT")
            elif criterion.comparison is CriterionComparison.LESS_THAN_OR_EQUAL:
                if result.value > criterion.threshold:
                    reasons.append(f"{criterion.metric.value}:ABOVE_THRESHOLD")
            elif result.value < criterion.threshold:
                reasons.append(f"{criterion.metric.value}:BELOW_THRESHOLD")
        deviation = report.stability.absolute_error_stddev
        if standard.maximum_stability_stddev is not None and (
            deviation is None or deviation > standard.maximum_stability_stddev
        ):
            reasons.append("STABILITY_STANDARD_NOT_MET")
        concentration = report.concentration.maximum_squared_error_share
        if standard.maximum_error_concentration is not None and (
            concentration is None or concentration > standard.maximum_error_concentration
        ):
            reasons.append("CONCENTRATION_STANDARD_NOT_MET")
        status = ValidationStatus.REJECT if reasons else ValidationStatus.PROMOTE
        decided_at = self._clock()
        decision_payload = {
            "report_id": report.report_id,
            "standard_id": standard.identity,
            "status": status,
            "authority_id": authority_id,
            "requester_id": requester_id,
            "beneficiary_id": beneficiary_id,
            "reasons": tuple(reasons) or ("PREDECLARED_STANDARD_MET",),
            "decided_at": decided_at,
        }
        decision = ValidationDecision(
            decision_id=stable_identity("validation-decision", decision_payload),
            report_id=report.report_id,
            standard_id=standard.identity,
            status=status,
            authority_id=authority_id,
            requester_id=requester_id,
            beneficiary_id=beneficiary_id,
            reasons=tuple(reasons) or ("PREDECLARED_STANDARD_MET",),
            decided_at=decided_at,
        )
        publication = self._ledger.append(
            LedgerEntry.create(
                event_type="finding.validation-decided",
                subject_id=decision.decision_id,
                status=status.value,
                authority_id=authority_id,
                references=(report.report_id, standard.identity),
                reason_code="|".join(decision.reasons),
                occurred_at=decided_at,
            )
        )
        self._decisions._issue(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            decision,
            publication=publication,
            ledger=self._ledger,
        )
        if status is ValidationStatus.REJECT:
            negative_payload = {
                "subject_id": decision.decision_id,
                "kind": "validation-rejection",
                "reason_codes": decision.reasons,
                "evidence_refs": (report.report_id, standard.identity),
                "authority_id": authority_id,
                "recorded_at": decided_at,
            }
            negative = NegativeResult(
                negative_id=stable_identity("negative-result", negative_payload),
                subject_id=decision.decision_id,
                kind="validation-rejection",
                reason_codes=decision.reasons,
                evidence_refs=(report.report_id, standard.identity),
                authority_id=authority_id,
                recorded_at=decided_at,
            )
            negative_publication = self._ledger.append(
                LedgerEntry.create(
                    event_type="ledger.negative-result-recorded",
                    subject_id=negative.negative_id,
                    status="rejected",
                    authority_id=authority_id,
                    references=(decision.decision_id, report.report_id, standard.identity),
                    reason_code="VALIDATION_REJECTED",
                    occurred_at=decided_at,
                )
            )
            self._negatives._issue(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
                negative,
                publication=negative_publication,
                ledger=self._ledger,
            )
        return decision

    @staticmethod
    def _report_values_are_finite(report: EvaluationReport) -> bool:
        """Independently fail closed even if report construction was bypassed."""
        values: list[float] = []
        values.extend(item.value for item in report.metrics if item.value is not None)
        for item in report.per_time:
            values.extend((item.prediction, item.outcome, item.absolute_error, item.squared_error))
        for item in report.per_dimension:
            values.extend((item.mse, item.mae))
        if report.stability.absolute_error_stddev is not None:
            values.append(report.stability.absolute_error_stddev)
        values.extend(report.stability.rolling_mse)
        if report.concentration.maximum_squared_error_share is not None:
            values.append(report.concentration.maximum_squared_error_share)
        return all(isfinite(value) for value in values)


@dataclass(frozen=True, slots=True)
class ValidatedFinding:
    """Immutable scientific substance published only from a PROMOTE decision."""

    finding_id: str
    claim: str
    claim_ref: str
    claim_scope_limitations: tuple[str, ...]
    validation_decision_id: str
    validation_standard_id: str
    validation_authority_id: str
    report_id: str
    frozen_system_id: str
    system_id: str
    target_id: str
    environment_ref: str
    scenario_id: str
    metrics: tuple[MetricResult, ...]
    stability: StabilityView
    concentration: ConcentrationView
    caveats: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    trial_ancestry_refs: tuple[str, ...]
    exposure_ref: str | None
    validation_status: ValidationStatus
    published_at: datetime

    def __post_init__(self) -> None:
        if self.validation_status is not ValidationStatus.PROMOTE:
            msg = "ValidatedFinding requires a promoting decision"
            raise ValueError(msg)
        if self.finding_id != stable_identity("validated-finding", _without_id(self)):
            msg = "validated finding identity does not match content"
            raise ValueError(msg)


class ValidatedFindingRegistry:
    """Publisher-owned authoritative history of validated scientific findings."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._findings: dict[str, ValidatedFinding] = {}
        self._publication_ids: dict[str, str] = {}

    def _issue(
        self,
        finding: ValidatedFinding,
        *,
        publication: LedgerEntry,
        ledger: ResearchLedger,
    ) -> ValidatedFinding:
        if (
            not ledger.authoritative(publication)
            or publication.event_type != "finding.validated-claim-published"
            or publication.subject_id != finding.finding_id
        ):
            msg = "validated-finding issuance requires its exact publication event"
            raise ValueError(msg)
        with self._lock:
            prior = self._findings.get(finding.finding_id)
            if prior is not None and prior != finding:
                msg = "validated-finding identity was reused with changed semantics"
                raise ValueError(msg)
            self._findings[finding.finding_id] = finding
            self._publication_ids[finding.finding_id] = publication.entry_id
            return finding

    def require_issued(self, finding: ValidatedFinding) -> None:
        """Reject a rehashed finding not published by this authority."""
        with self._lock:
            if (
                self._findings.get(finding.finding_id) != finding
                or finding.finding_id not in self._publication_ids
            ):
                msg = "validated finding was not issued by the required publisher"
                raise ValueError(msg)


class FindingPublisher:
    """Seal evidence-supported substance without changing validation authority."""

    def __init__(
        self,
        *,
        ledger: ResearchLedger,
        reports: EvaluationReportRegistry,
        decisions: ValidationDecisionRegistry,
        clock: Callable[[], datetime],
        findings: ValidatedFindingRegistry | None = None,
        operations: PrivilegedOperationCoordinator | None = None,
    ) -> None:
        self._ledger = ledger
        self._reports = reports
        self._decisions = decisions
        self._clock = clock
        self._findings = findings or ValidatedFindingRegistry()
        self._operations = operations or PrivilegedOperationCoordinator()

    def publish(
        self,
        decision: ValidationDecision,
        report: EvaluationReport,
        *,
        claim: ClaimDefinition,
    ) -> ValidatedFinding:
        """Create exactly one finding only after the exact report was promoted."""
        if decision.status is not ValidationStatus.PROMOTE:
            msg = "a rejected validation decision cannot publish a finding"
            raise ValueError(msg)
        self._decisions.require_issued(decision)
        self._reports.require_issued(report)
        if (
            decision.report_id != report.report_id
            or claim.identity != report.claim_ref
            or claim.system_id != report.system_id
            or claim.target_id != report.target_id
        ):
            msg = "finding inputs do not match exact promoted evidence and claim"
            raise ValueError(msg)
        payload = (
            ("decision_id", decision.decision_id),
            ("report_id", report.report_id),
            ("claim_ref", claim.identity),
        )
        return self._operations.execute(
            operation_key=f"finding:{decision.decision_id}",
            semantic_payload=payload,
            effect=lambda: self._publish_once(decision, report, claim),
        ).result

    def _publish_once(
        self,
        decision: ValidationDecision,
        report: EvaluationReport,
        claim: ClaimDefinition,
    ) -> ValidatedFinding:
        published_at = self._clock()
        finding_payload = {
            "claim": claim.statement,
            "claim_ref": claim.identity,
            "claim_scope_limitations": claim.scope_limitations,
            "validation_decision_id": decision.decision_id,
            "validation_standard_id": decision.standard_id,
            "validation_authority_id": decision.authority_id,
            "report_id": report.report_id,
            "frozen_system_id": report.frozen_system_id,
            "system_id": report.system_id,
            "target_id": report.target_id,
            "environment_ref": report.environment_ref,
            "scenario_id": report.scenario_id,
            "metrics": report.metrics,
            "stability": report.stability,
            "concentration": report.concentration,
            "caveats": tuple(dict.fromkeys((*claim.required_caveats, *report.caveats))),
            "evidence_refs": (report.run_id, report.report_id, decision.decision_id),
            "trial_ancestry_refs": report.trial_ancestry_refs,
            "exposure_ref": report.exposure_ref,
            "validation_status": ValidationStatus.PROMOTE,
            "published_at": published_at,
        }
        finding = ValidatedFinding(
            finding_id=stable_identity("validated-finding", finding_payload),
            claim=claim.statement,
            claim_ref=claim.identity,
            claim_scope_limitations=claim.scope_limitations,
            validation_decision_id=decision.decision_id,
            validation_standard_id=decision.standard_id,
            validation_authority_id=decision.authority_id,
            report_id=report.report_id,
            frozen_system_id=report.frozen_system_id,
            system_id=report.system_id,
            target_id=report.target_id,
            environment_ref=report.environment_ref,
            scenario_id=report.scenario_id,
            metrics=report.metrics,
            stability=report.stability,
            concentration=report.concentration,
            caveats=tuple(dict.fromkeys((*claim.required_caveats, *report.caveats))),
            evidence_refs=(report.run_id, report.report_id, decision.decision_id),
            trial_ancestry_refs=report.trial_ancestry_refs,
            exposure_ref=report.exposure_ref,
            validation_status=ValidationStatus.PROMOTE,
            published_at=published_at,
        )
        publication = self._ledger.append(
            LedgerEntry.create(
                event_type="finding.validated-claim-published",
                subject_id=finding.finding_id,
                status="promoted",
                authority_id=decision.authority_id,
                references=(decision.decision_id, report.report_id, report.run_id),
                reason_code="VALIDATION_PROMOTED",
                occurred_at=published_at,
            )
        )
        self._findings._issue(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            finding,
            publication=publication,
            ledger=self._ledger,
        )
        return finding

    @property
    def issued_findings(self) -> ValidatedFindingRegistry:
        """Expose canonical findings to the presentation layer."""
        return self._findings


def _without_id(item: object) -> dict[str, object]:
    fields = getattr(item, "__dataclass_fields__", {})
    identity_name = next(iter(fields), None)
    return {name: getattr(item, name) for name in fields if name != identity_name}


__all__ = [
    "ConcentrationView",
    "DimensionMetricView",
    "EvaluationReport",
    "EvaluationReportRegistry",
    "Evaluator",
    "FailureCount",
    "FindingPublisher",
    "MetricResult",
    "NegativeResult",
    "NegativeResultRegistry",
    "StabilityView",
    "TimeErrorView",
    "ValidatedFinding",
    "ValidatedFindingRegistry",
    "ValidationDecision",
    "ValidationDecisionRegistry",
    "ValidationStatus",
    "Validator",
]
