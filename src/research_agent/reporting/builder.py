"""Canonical report rendering without scientific or promotion authority."""

# ruff: noqa: D102, D105, D107, EM101, EM102, TRY003

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, Protocol, cast

from research_agent.data_foundation._identity import stable_identity
from research_agent.protected_evaluation import (
    ConcentrationView,
    EvaluationReport,
    MetricName,
    MetricResult,
    StabilityView,
    ValidatedFinding,
    ValidationDecision,
    ValidationStatus,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from research_agent.protected_evaluation import ResearchLedger


class ReportingIntegrityError(ValueError):
    """Canonical evidence or rendered substance failed exact verification."""


class Audience(Enum):
    """Presentation audience; it has no effect on scientific fields."""

    RESEARCHER = "researcher"
    GENERAL = "general"


class PresentationOrder(Enum):
    """Safe organization choices for the same required content."""

    CONCLUSION_FIRST = "conclusion_first"
    EVIDENCE_FIRST = "evidence_first"


class DetailLevel(Enum):
    """Presentation density; all canonical fields remain present at every level."""

    CONCISE = "concise"
    DETAILED = "detailed"


class WordingStyle(Enum):
    """Predefined labels that cannot introduce caller-authored claims."""

    PLAIN = "plain"
    TECHNICAL = "technical"


@dataclass(frozen=True, slots=True)
class ReportSpecification:
    """Content-addressed presentation choices with no scientific override channel."""

    specification_id: str
    version: int
    audience: Audience
    order: PresentationOrder
    detail_level: DetailLevel
    wording_style: WordingStyle

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ReportingIntegrityError("report specification version must be positive")
        if self.specification_id != stable_identity(
            "report-specification", _without_first_identity(self)
        ):
            raise ReportingIntegrityError("report specification identity does not match content")

    @classmethod
    def create(
        cls,
        *,
        version: int = 1,
        audience: Audience = Audience.RESEARCHER,
        order: PresentationOrder = PresentationOrder.CONCLUSION_FIRST,
        detail_level: DetailLevel = DetailLevel.CONCISE,
        wording_style: WordingStyle = WordingStyle.PLAIN,
    ) -> ReportSpecification:
        payload = {
            "version": version,
            "audience": audience,
            "order": order,
            "detail_level": detail_level,
            "wording_style": wording_style,
        }
        return cls(
            specification_id=stable_identity("report-specification", payload),
            version=version,
            audience=audience,
            order=order,
            detail_level=detail_level,
            wording_style=wording_style,
        )


@dataclass(frozen=True, slots=True)
class MachineMetric:
    """JSON-safe exact representation of one canonical metric."""

    name: str
    value: float | None
    sample_size: int
    denominator: int
    warning: str | None


@dataclass(frozen=True, slots=True)
class FindingMachinePayload:
    """Versioned, content-addressed machine representation of a finding."""

    payload_id: str
    schema_version: int
    scientific_fingerprint: str
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
    metrics: tuple[MachineMetric, ...]
    stability_absolute_error_stddev: float | None
    stability_rolling_mse: tuple[float, ...]
    concentration_maximum_squared_error_share: float | None
    concentration_worst_decision_time: str | None
    caveats: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    trial_ancestry_refs: tuple[str, ...]
    exposure_ref: str | None
    validation_status: str
    published_at: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ReportingIntegrityError("unsupported finding payload schema")
        if self.payload_id != stable_identity("finding-machine-payload", _payload_body(self)):
            raise ReportingIntegrityError("machine payload identity does not match content")
        finding = self.reconstruct_finding()
        expected = _scientific_fingerprint(finding)
        if self.scientific_fingerprint != expected:
            raise ReportingIntegrityError("machine payload scientific fingerprint is invalid")

    @classmethod
    def from_finding(cls, finding: ValidatedFinding) -> FindingMachinePayload:
        fingerprint = _scientific_fingerprint(finding)
        fields: dict[str, object] = {
            "schema_version": 1,
            "scientific_fingerprint": fingerprint,
            "finding_id": finding.finding_id,
            "claim": finding.claim,
            "claim_ref": finding.claim_ref,
            "claim_scope_limitations": finding.claim_scope_limitations,
            "validation_decision_id": finding.validation_decision_id,
            "validation_standard_id": finding.validation_standard_id,
            "validation_authority_id": finding.validation_authority_id,
            "report_id": finding.report_id,
            "frozen_system_id": finding.frozen_system_id,
            "system_id": finding.system_id,
            "target_id": finding.target_id,
            "environment_ref": finding.environment_ref,
            "scenario_id": finding.scenario_id,
            "metrics": tuple(
                MachineMetric(
                    metric.name.value,
                    metric.value,
                    metric.sample_size,
                    metric.denominator,
                    metric.warning,
                )
                for metric in finding.metrics
            ),
            "stability_absolute_error_stddev": finding.stability.absolute_error_stddev,
            "stability_rolling_mse": finding.stability.rolling_mse,
            "concentration_maximum_squared_error_share": (
                finding.concentration.maximum_squared_error_share
            ),
            "concentration_worst_decision_time": (
                finding.concentration.worst_decision_time.isoformat()
                if finding.concentration.worst_decision_time is not None
                else None
            ),
            "caveats": finding.caveats,
            "evidence_refs": finding.evidence_refs,
            "trial_ancestry_refs": finding.trial_ancestry_refs,
            "exposure_ref": finding.exposure_ref,
            "validation_status": finding.validation_status.value,
            "published_at": finding.published_at.isoformat(),
        }
        return cls(
            payload_id=stable_identity("finding-machine-payload", fields),
            schema_version=1,
            scientific_fingerprint=fingerprint,
            finding_id=finding.finding_id,
            claim=finding.claim,
            claim_ref=finding.claim_ref,
            claim_scope_limitations=finding.claim_scope_limitations,
            validation_decision_id=finding.validation_decision_id,
            validation_standard_id=finding.validation_standard_id,
            validation_authority_id=finding.validation_authority_id,
            report_id=finding.report_id,
            frozen_system_id=finding.frozen_system_id,
            system_id=finding.system_id,
            target_id=finding.target_id,
            environment_ref=finding.environment_ref,
            scenario_id=finding.scenario_id,
            metrics=cast("tuple[MachineMetric, ...]", fields["metrics"]),
            stability_absolute_error_stddev=finding.stability.absolute_error_stddev,
            stability_rolling_mse=finding.stability.rolling_mse,
            concentration_maximum_squared_error_share=(
                finding.concentration.maximum_squared_error_share
            ),
            concentration_worst_decision_time=cast(
                "str | None", fields["concentration_worst_decision_time"]
            ),
            caveats=finding.caveats,
            evidence_refs=finding.evidence_refs,
            trial_ancestry_refs=finding.trial_ancestry_refs,
            exposure_ref=finding.exposure_ref,
            validation_status=finding.validation_status.value,
            published_at=finding.published_at.isoformat(),
        )

    def reconstruct_finding(self) -> ValidatedFinding:
        """Reconstruct the exact protected type; its own identity check is mandatory."""
        try:
            metrics = tuple(
                MetricResult(
                    name=MetricName(item.name),
                    value=item.value,
                    sample_size=item.sample_size,
                    denominator=item.denominator,
                    warning=item.warning,
                )
                for item in self.metrics
            )
            worst_time = (
                datetime.fromisoformat(self.concentration_worst_decision_time)
                if self.concentration_worst_decision_time is not None
                else None
            )
            return ValidatedFinding(
                finding_id=self.finding_id,
                claim=self.claim,
                claim_ref=self.claim_ref,
                claim_scope_limitations=self.claim_scope_limitations,
                validation_decision_id=self.validation_decision_id,
                validation_standard_id=self.validation_standard_id,
                validation_authority_id=self.validation_authority_id,
                report_id=self.report_id,
                frozen_system_id=self.frozen_system_id,
                system_id=self.system_id,
                target_id=self.target_id,
                environment_ref=self.environment_ref,
                scenario_id=self.scenario_id,
                metrics=metrics,
                stability=StabilityView(
                    self.stability_absolute_error_stddev,
                    self.stability_rolling_mse,
                ),
                concentration=ConcentrationView(
                    self.concentration_maximum_squared_error_share,
                    worst_time,
                ),
                caveats=self.caveats,
                evidence_refs=self.evidence_refs,
                trial_ancestry_refs=self.trial_ancestry_refs,
                exposure_ref=self.exposure_ref,
                validation_status=ValidationStatus(self.validation_status),
                published_at=datetime.fromisoformat(self.published_at),
            )
        except (TypeError, ValueError) as error:
            raise ReportingIntegrityError(
                "machine payload cannot reconstruct exact finding"
            ) from error

    def as_dict(self) -> dict[str, object]:
        """Return a fresh JSON-safe dictionary without mutable internal state."""
        return {
            "payload_id": self.payload_id,
            "schema_version": self.schema_version,
            "scientific_fingerprint": self.scientific_fingerprint,
            "finding_id": self.finding_id,
            "claim": self.claim,
            "claim_ref": self.claim_ref,
            "claim_scope_limitations": list(self.claim_scope_limitations),
            "validation_decision_id": self.validation_decision_id,
            "validation_standard_id": self.validation_standard_id,
            "validation_authority_id": self.validation_authority_id,
            "report_id": self.report_id,
            "frozen_system_id": self.frozen_system_id,
            "system_id": self.system_id,
            "target_id": self.target_id,
            "environment_ref": self.environment_ref,
            "scenario_id": self.scenario_id,
            "metrics": [
                {
                    "name": item.name,
                    "value": item.value,
                    "sample_size": item.sample_size,
                    "denominator": item.denominator,
                    "warning": item.warning,
                }
                for item in self.metrics
            ],
            "stability_absolute_error_stddev": self.stability_absolute_error_stddev,
            "stability_rolling_mse": list(self.stability_rolling_mse),
            "concentration_maximum_squared_error_share": (
                self.concentration_maximum_squared_error_share
            ),
            "concentration_worst_decision_time": self.concentration_worst_decision_time,
            "caveats": list(self.caveats),
            "evidence_refs": list(self.evidence_refs),
            "trial_ancestry_refs": list(self.trial_ancestry_refs),
            "exposure_ref": self.exposure_ref,
            "validation_status": self.validation_status,
            "published_at": self.published_at,
        }

    def to_json(self) -> str:
        """Serialize deterministically for storage or API transport."""
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, serialized: str) -> FindingMachinePayload:
        """Parse a strict payload and rerun all content and finding identity checks."""
        try:
            decoded: object = json.loads(serialized)
            if not isinstance(decoded, dict):
                raise ReportingIntegrityError("machine payload has unexpected fields")
            raw = cast("dict[str, object]", decoded)
            if set(raw) != _PAYLOAD_KEYS:
                raise ReportingIntegrityError("machine payload has unexpected fields")
            metric_values = raw["metrics"]
            if not isinstance(metric_values, list):
                raise ReportingIntegrityError("machine payload metrics must be a list")
            metrics = tuple(_machine_metric(value) for value in cast("list[object]", metric_values))
            return cls(
                payload_id=_string(raw, "payload_id"),
                schema_version=_integer(raw, "schema_version"),
                scientific_fingerprint=_string(raw, "scientific_fingerprint"),
                finding_id=_string(raw, "finding_id"),
                claim=_string(raw, "claim"),
                claim_ref=_string(raw, "claim_ref"),
                claim_scope_limitations=_strings(raw, "claim_scope_limitations"),
                validation_decision_id=_string(raw, "validation_decision_id"),
                validation_standard_id=_string(raw, "validation_standard_id"),
                validation_authority_id=_string(raw, "validation_authority_id"),
                report_id=_string(raw, "report_id"),
                frozen_system_id=_string(raw, "frozen_system_id"),
                system_id=_string(raw, "system_id"),
                target_id=_string(raw, "target_id"),
                environment_ref=_string(raw, "environment_ref"),
                scenario_id=_string(raw, "scenario_id"),
                metrics=metrics,
                stability_absolute_error_stddev=_optional_float(
                    raw, "stability_absolute_error_stddev"
                ),
                stability_rolling_mse=_floats(raw, "stability_rolling_mse"),
                concentration_maximum_squared_error_share=_optional_float(
                    raw, "concentration_maximum_squared_error_share"
                ),
                concentration_worst_decision_time=_optional_string(
                    raw, "concentration_worst_decision_time"
                ),
                caveats=_strings(raw, "caveats"),
                evidence_refs=_strings(raw, "evidence_refs"),
                trial_ancestry_refs=_strings(raw, "trial_ancestry_refs"),
                exposure_ref=_optional_string(raw, "exposure_ref"),
                validation_status=_string(raw, "validation_status"),
                published_at=_string(raw, "published_at"),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            if isinstance(error, ReportingIntegrityError):
                raise
            raise ReportingIntegrityError("invalid machine payload") from error


@dataclass(frozen=True, slots=True)
class CanonicalFindingEvidence:
    """Exact finding, measurement, and decision bundle admitted for reporting."""

    finding: ValidatedFinding
    report: EvaluationReport
    decision: ValidationDecision

    def __post_init__(self) -> None:
        finding = self.finding
        report = self.report
        decision = self.decision
        if decision.status is not ValidationStatus.PROMOTE:
            raise ReportingIntegrityError("rejected decision cannot back a validated report")
        if (
            finding.validation_status is not ValidationStatus.PROMOTE
            or finding.validation_decision_id != decision.decision_id
            or finding.validation_standard_id != decision.standard_id
            or finding.validation_authority_id != decision.authority_id
            or finding.report_id != report.report_id
            or decision.report_id != report.report_id
        ):
            raise ReportingIntegrityError("finding, decision, and report identities do not match")
        if (
            finding.claim_ref != report.claim_ref
            or finding.frozen_system_id != report.frozen_system_id
            or finding.system_id != report.system_id
            or finding.target_id != report.target_id
            or finding.environment_ref != report.environment_ref
            or finding.scenario_id != report.scenario_id
            or finding.metrics != report.metrics
            or finding.stability != report.stability
            or finding.concentration != report.concentration
            or finding.trial_ancestry_refs != report.trial_ancestry_refs
            or finding.exposure_ref != report.exposure_ref
            or finding.evidence_refs != (report.run_id, report.report_id, decision.decision_id)
        ):
            raise ReportingIntegrityError("finding substance does not match canonical evidence")
        if not _ordered_subsequence(report.caveats, finding.caveats):
            raise ReportingIntegrityError("finding omitted or reordered evaluation caveats")


class CanonicalReportSource(Protocol):
    """Read-only authoritative source used by the presentation boundary."""

    def resolve(self, finding_id: str) -> CanonicalFindingEvidence:
        """Resolve an exact already-published evidence bundle."""
        ...


class CanonicalReportRegistry:
    """Ledger-verified, append-only source for reportable findings."""

    def __init__(self, *, ledger: ResearchLedger) -> None:
        self._ledger = ledger
        self._records: Mapping[str, CanonicalFindingEvidence] = MappingProxyType({})

    def register(
        self,
        *,
        finding: ValidatedFinding,
        report: EvaluationReport,
        decision: ValidationDecision,
    ) -> CanonicalFindingEvidence:
        """Admit only a bundle whose exact authority path exists in the canonical ledger."""
        bundle = CanonicalFindingEvidence(finding, report, decision)
        entries = self._ledger.entries()
        required = (
            (
                "evaluation.run-measured",
                report.report_id,
                "measured",
                "evaluator",
                (report.run_id, report.evaluation_spec_id),
            ),
            (
                "finding.validation-decided",
                decision.decision_id,
                "promote",
                decision.authority_id,
                (report.report_id, decision.standard_id),
            ),
            (
                "finding.validated-claim-published",
                finding.finding_id,
                "promoted",
                decision.authority_id,
                (decision.decision_id, report.report_id, report.run_id),
            ),
        )
        for event_type, subject_id, status, authority_id, references in required:
            matches = tuple(
                entry
                for entry in entries
                if entry.event_type == event_type
                and entry.subject_id == subject_id
                and entry.status == status
                and entry.authority_id == authority_id
                and entry.references == references
            )
            if len(matches) != 1:
                raise ReportingIntegrityError(
                    f"canonical ledger does not contain exact {event_type!r} authority event"
                )
        existing = self._records.get(finding.finding_id)
        if existing is not None:
            if existing != bundle:
                raise ReportingIntegrityError(
                    "finding identity was reused with different canonical evidence"
                )
            return existing
        updated = dict(self._records)
        updated[finding.finding_id] = bundle
        self._records = MappingProxyType(updated)
        return bundle

    def resolve(self, finding_id: str) -> CanonicalFindingEvidence:
        try:
            return self._records[finding_id]
        except KeyError as error:
            raise ReportingIntegrityError(
                "finding is not present in the authoritative report registry"
            ) from error


@dataclass(frozen=True, slots=True)
class RenderedFindingReport:
    """Immutable presentation plus exact machine-verifiable scientific payload."""

    rendered_report_id: str
    report_specification_id: str
    scientific_fingerprint: str
    finding_id: str
    canonical_report_id: str
    validation_decision_id: str
    run_ref: str
    markdown: str
    machine_payload: FindingMachinePayload

    def __post_init__(self) -> None:
        if self.rendered_report_id != stable_identity(
            "rendered-finding-report", _without_first_identity(self)
        ):
            raise ReportingIntegrityError("rendered report identity does not match content")
        finding = self.machine_payload.reconstruct_finding()
        if (
            self.finding_id != finding.finding_id
            or self.scientific_fingerprint != self.machine_payload.scientific_fingerprint
            or self.canonical_report_id != finding.report_id
            or self.validation_decision_id != finding.validation_decision_id
            or not finding.evidence_refs
            or self.run_ref != finding.evidence_refs[0]
        ):
            raise ReportingIntegrityError("rendered report references do not match machine payload")


class ReportBuilder:
    """Render verified substance; never evaluate, validate, promote, or decide usefulness."""

    def __init__(self, *, source: CanonicalReportSource) -> None:
        self._source = source

    def render(
        self,
        finding: ValidatedFinding,
        specification: ReportSpecification,
    ) -> RenderedFindingReport:
        """Render only an exact finding resolved independently from canonical storage."""
        canonical = self._source.resolve(finding.finding_id)
        if canonical.finding != finding:
            raise ReportingIntegrityError("caller finding differs from canonical finding")
        payload = FindingMachinePayload.from_finding(canonical.finding)
        markdown = _render_markdown(canonical.finding, specification)
        fields = {
            "report_specification_id": specification.specification_id,
            "scientific_fingerprint": payload.scientific_fingerprint,
            "finding_id": finding.finding_id,
            "canonical_report_id": canonical.report.report_id,
            "validation_decision_id": canonical.decision.decision_id,
            "run_ref": canonical.report.run_id,
            "markdown": markdown,
            "machine_payload": payload,
        }
        rendered = RenderedFindingReport(
            rendered_report_id=stable_identity("rendered-finding-report", fields),
            report_specification_id=specification.specification_id,
            scientific_fingerprint=payload.scientific_fingerprint,
            finding_id=finding.finding_id,
            canonical_report_id=canonical.report.report_id,
            validation_decision_id=canonical.decision.decision_id,
            run_ref=canonical.report.run_id,
            markdown=markdown,
            machine_payload=payload,
        )
        self.verify(rendered)
        return rendered

    def verify(self, rendered: RenderedFindingReport) -> ValidatedFinding:
        """Recheck a report against canonical evidence, independent of its self-hashes."""
        canonical = self._source.resolve(rendered.finding_id)
        reconstructed = rendered.machine_payload.reconstruct_finding()
        if reconstructed != canonical.finding:
            raise ReportingIntegrityError(
                "rendered machine substance differs from canonical finding"
            )
        if (
            rendered.scientific_fingerprint != _scientific_fingerprint(canonical.finding)
            or rendered.canonical_report_id != canonical.report.report_id
            or rendered.validation_decision_id != canonical.decision.decision_id
            or rendered.run_ref != canonical.report.run_id
        ):
            raise ReportingIntegrityError("rendered canonical evidence references are invalid")
        return reconstructed


def _render_markdown(finding: ValidatedFinding, spec: ReportSpecification) -> str:
    conclusion_heading = (
        "Scientific conclusion" if spec.wording_style is WordingStyle.TECHNICAL else "Finding"
    )
    evidence_heading = (
        "Canonical measurements" if spec.wording_style is WordingStyle.TECHNICAL else "Evidence"
    )
    conclusion = [
        f"## {conclusion_heading}",
        "",
        _md_text(finding.claim),
        "",
        f"Validation status: `{finding.validation_status.value}`",
        f"Target: `{finding.target_id}`",
        f"System: `{finding.system_id}`",
        f"Protected scenario: `{finding.scenario_id}`",
    ]
    metric_rows = [
        "| Metric | Value | Sample size | Denominator | Warning |",
        "|---|---:|---:|---:|---|",
        *(
            "| "
            + " | ".join(
                (
                    _md_text(metric.name.value),
                    "not measurable" if metric.value is None else repr(metric.value),
                    str(metric.sample_size),
                    str(metric.denominator),
                    _md_text(metric.warning or "none"),
                )
            )
            + " |"
            for metric in finding.metrics
        ),
    ]
    evidence = [
        f"## {evidence_heading}",
        "",
        *metric_rows,
        "",
        "### Robustness and stability",
        "",
        "- Absolute-error standard deviation: " + repr(finding.stability.absolute_error_stddev),
        "- Rolling MSE: " + _tuple_text(finding.stability.rolling_mse),
        "- Maximum squared-error share: " + repr(finding.concentration.maximum_squared_error_share),
        "- Worst decision time: "
        + (
            finding.concentration.worst_decision_time.isoformat()
            if finding.concentration.worst_decision_time is not None
            else "none"
        ),
    ]
    qualifications = [
        "## Scope limitations",
        "",
        *(_bullets(finding.claim_scope_limitations)),
        "",
        "## Required caveats and warnings",
        "",
        *(_bullets(finding.caveats)),
    ]
    traceability = [
        "## Traceability",
        "",
        f"- Finding: `{finding.finding_id}`",
        f"- Claim definition: `{finding.claim_ref}`",
        f"- Canonical evaluation report: `{finding.report_id}`",
        f"- Validation decision: `{finding.validation_decision_id}`",
        f"- Validation standard: `{finding.validation_standard_id}`",
        f"- Validation authority: `{finding.validation_authority_id}`",
        f"- Frozen system: `{finding.frozen_system_id}`",
        f"- Environment: `{finding.environment_ref}`",
        "- Evidence references: " + _refs(finding.evidence_refs),
        "- Trial ancestry: " + _refs(finding.trial_ancestry_refs),
        "- Protected exposure: "
        + (f"`{finding.exposure_ref}`" if finding.exposure_ref else "none"),
        f"- Published at: `{finding.published_at.isoformat()}`",
    ]
    sections = (
        (conclusion, evidence)
        if spec.order is PresentationOrder.CONCLUSION_FIRST
        else (evidence, conclusion)
    )
    audience_note = (
        "This report presents a promoted scientific finding; it does not make a downstream "
        "business or economic decision."
    )
    detail_note = (
        "All values and references below are rendered from the exact canonical finding."
        if spec.detail_level is DetailLevel.DETAILED
        else "Canonical scientific content follows."
    )
    return "\n".join(
        (
            "# Validated scientific finding",
            "",
            audience_note,
            detail_note,
            "",
            *sections[0],
            "",
            *sections[1],
            "",
            *qualifications,
            "",
            *traceability,
            "",
        )
    )


def _scientific_fingerprint(finding: ValidatedFinding) -> str:
    return stable_identity("reported-scientific-substance", finding)


def _ordered_subsequence(required: tuple[str, ...], actual: tuple[str, ...]) -> bool:
    if not required:
        return True
    positions = iter(actual)
    return all(any(candidate == item for candidate in positions) for item in required)


def _bullets(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(f"- {_md_text(item)}" for item in values) or ("- none declared",)


def _refs(values: tuple[str, ...]) -> str:
    return ", ".join(f"`{item}`" for item in values) or "none"


def _tuple_text(values: tuple[float, ...]) -> str:
    return "[" + ", ".join(repr(item) for item in values) + "]"


def _md_text(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("\n", " ")
    for token in ("|", "*", "_", "[", "]", "<", ">", "#"):
        escaped = escaped.replace(token, f"\\{token}")
    return escaped


def _without_first_identity(item: object) -> dict[str, object]:
    fields = getattr(item, "__dataclass_fields__", {})
    identity = next(iter(fields), None)
    return {name: getattr(item, name) for name in fields if name != identity}


def _payload_body(payload: FindingMachinePayload) -> dict[str, object]:
    return _without_first_identity(payload)


def _machine_metric(value: object) -> MachineMetric:
    if not isinstance(value, dict):
        raise ReportingIntegrityError("machine metric has unexpected fields")
    values = cast("dict[str, object]", value)
    if set(values) != {
        "name",
        "value",
        "sample_size",
        "denominator",
        "warning",
    }:
        raise ReportingIntegrityError("machine metric has unexpected fields")
    return MachineMetric(
        name=_string(values, "name"),
        value=_optional_float(values, "value"),
        sample_size=_integer(values, "sample_size"),
        denominator=_integer(values, "denominator"),
        warning=_optional_string(values, "warning"),
    )


def _string(values: Mapping[str, object], key: str) -> str:
    value = values[key]
    if not isinstance(value, str) or not value:
        raise ReportingIntegrityError(f"{key} must be a non-empty string")
    return value


def _optional_string(values: Mapping[str, object], key: str) -> str | None:
    value = values[key]
    if value is not None and not isinstance(value, str):
        raise ReportingIntegrityError(f"{key} must be a string or null")
    return value


def _integer(values: Mapping[str, object], key: str) -> int:
    value = values[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReportingIntegrityError(f"{key} must be an integer")
    return value


def _optional_float(values: Mapping[str, object], key: str) -> float | None:
    value = values[key]
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReportingIntegrityError(f"{key} must be numeric or null")
    return float(value)


def _strings(values: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = values[key]
    if not isinstance(value, list):
        raise ReportingIntegrityError(f"{key} must be a list of strings")
    items = cast("list[object]", value)
    if any(not isinstance(item, str) for item in items):
        raise ReportingIntegrityError(f"{key} must be a list of strings")
    return tuple(cast("str", item) for item in items)


def _floats(values: Mapping[str, object], key: str) -> tuple[float, ...]:
    value = values[key]
    if not isinstance(value, list):
        raise ReportingIntegrityError(f"{key} must be a list of numbers")
    items = cast("list[object]", value)
    if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in items):
        raise ReportingIntegrityError(f"{key} must be a list of numbers")
    return tuple(float(cast("int | float", item)) for item in items)


_PAYLOAD_KEYS = {
    "payload_id",
    "schema_version",
    "scientific_fingerprint",
    "finding_id",
    "claim",
    "claim_ref",
    "claim_scope_limitations",
    "validation_decision_id",
    "validation_standard_id",
    "validation_authority_id",
    "report_id",
    "frozen_system_id",
    "system_id",
    "target_id",
    "environment_ref",
    "scenario_id",
    "metrics",
    "stability_absolute_error_stddev",
    "stability_rolling_mse",
    "concentration_maximum_squared_error_share",
    "concentration_worst_decision_time",
    "caveats",
    "evidence_refs",
    "trial_ancestry_refs",
    "exposure_ref",
    "validation_status",
    "published_at",
}


__all__ = [
    "Audience",
    "CanonicalFindingEvidence",
    "CanonicalReportRegistry",
    "DetailLevel",
    "FindingMachinePayload",
    "PresentationOrder",
    "RenderedFindingReport",
    "ReportBuilder",
    "ReportSpecification",
    "ReportingIntegrityError",
    "WordingStyle",
]
