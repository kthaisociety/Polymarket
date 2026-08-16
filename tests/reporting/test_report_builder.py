"""Invariant and adversarial tests for canonical finding presentation."""

# pyright: reportArgumentType=false, reportUnknownArgumentType=false
# pyright: reportUnknownVariableType=false

from __future__ import annotations

import json
from dataclasses import fields
from datetime import UTC, datetime

import pytest

from research_agent.data_foundation._identity import stable_identity
from research_agent.protected_evaluation import (
    BacktestRunStatus,
    ConcentrationView,
    EvaluationReport,
    LedgerEntry,
    MetricName,
    MetricResult,
    ResearchLedger,
    StabilityView,
    ValidatedFinding,
    ValidationDecision,
    ValidationStatus,
)
from research_agent.reporting import (
    Audience,
    CanonicalFindingEvidence,
    CanonicalReportRegistry,
    DetailLevel,
    FindingMachinePayload,
    PresentationOrder,
    ReportBuilder,
    ReportingIntegrityError,
    ReportSpecification,
    WordingStyle,
)

NOW = datetime(2026, 8, 15, 12, tzinfo=UTC)


def _identity_body(item: object) -> dict[str, object]:
    names = tuple(field.name for field in fields(item))
    return {name: getattr(item, name) for name in names[1:]}


def _report() -> EvaluationReport:
    metrics = (
        MetricResult(MetricName.MSE, 0.25, 8, 10, None),
        MetricResult(MetricName.COVERAGE, 0.8, 8, 10, "two outcomes unavailable"),
    )
    body = {
        "run_id": "run:generic-series-v1",
        "request_id": "request:protected-v1",
        "frozen_system_id": "frozen:system-v1",
        "system_id": "system:generic-v1",
        "target_id": "target:next-period-value-v1",
        "scenario_id": "scenario:historical-v1",
        "scenario_kind": "historical_walk_forward",
        "run_status": BacktestRunStatus.COMPLETED,
        "execution_valid": True,
        "evaluation_spec_id": "evaluation:quality-v1",
        "validation_standard_ref": "standard:quality-v1",
        "claim_ref": "claim:bounded-v1",
        "environment_ref": "environment:generic-v1",
        "metrics": metrics,
        "per_time": (),
        "per_dimension": (),
        "failures": (),
        "stability": StabilityView(0.1, (0.2, 0.25)),
        "concentration": ConcentrationView(0.4, NOW),
        "trial_ancestry_refs": ("trial:root", "trial:candidate"),
        "exposure_ref": "exposure:protected-v1",
        "caveats": ("coverage is incomplete", "performance varies over time"),
        "measured_at": NOW,
        "provenance_refs": ("run:generic-series-v1", "evaluation:quality-v1"),
    }
    return EvaluationReport(
        report_id=stable_identity("evaluation-report", body),
        **body,
    )


def _decision(
    report: EvaluationReport, status: ValidationStatus = ValidationStatus.PROMOTE
) -> ValidationDecision:
    reasons = (
        ("PREDECLARED_STANDARD_MET",)
        if status is ValidationStatus.PROMOTE
        else ("MSE:ABOVE_THRESHOLD",)
    )
    body = {
        "report_id": report.report_id,
        "standard_id": report.validation_standard_ref,
        "status": status,
        "authority_id": "independent-validator",
        "requester_id": "research-runtime",
        "beneficiary_id": "candidate-author",
        "reasons": reasons,
        "decided_at": NOW,
    }
    return ValidationDecision(
        decision_id=stable_identity("validation-decision", body),
        **body,
    )


def _finding(report: EvaluationReport, decision: ValidationDecision) -> ValidatedFinding:
    body = {
        "claim": "The frozen system met the declared predictive-quality standard.",
        "claim_ref": report.claim_ref,
        "claim_scope_limitations": ("applies only to the declared target and scenario",),
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
        "caveats": ("not a downstream-use decision", *report.caveats),
        "evidence_refs": (report.run_id, report.report_id, decision.decision_id),
        "trial_ancestry_refs": report.trial_ancestry_refs,
        "exposure_ref": report.exposure_ref,
        "validation_status": ValidationStatus.PROMOTE,
        "published_at": NOW,
    }
    return ValidatedFinding(
        finding_id=stable_identity("validated-finding", body),
        **body,
    )


def _registry() -> tuple[
    CanonicalReportRegistry, ValidatedFinding, EvaluationReport, ValidationDecision
]:
    report = _report()
    decision = _decision(report)
    finding = _finding(report, decision)
    ledger = ResearchLedger()
    for event_type, subject_id, status, authority_id, references, reason in (
        (
            "evaluation.run-measured",
            report.report_id,
            "measured",
            "evaluator",
            (report.run_id, report.evaluation_spec_id),
            "PREDECLARED_MEASUREMENTS",
        ),
        (
            "finding.validation-decided",
            decision.decision_id,
            "promote",
            decision.authority_id,
            (report.report_id, decision.standard_id),
            "PREDECLARED_STANDARD_MET",
        ),
        (
            "finding.validated-claim-published",
            finding.finding_id,
            "promoted",
            decision.authority_id,
            (decision.decision_id, report.report_id, report.run_id),
            "VALIDATION_PROMOTED",
        ),
    ):
        ledger.append(
            LedgerEntry.create(
                event_type=event_type,
                subject_id=subject_id,
                status=status,
                authority_id=authority_id,
                references=references,
                reason_code=reason,
                occurred_at=NOW,
            )
        )
    registry = CanonicalReportRegistry(ledger=ledger)
    registry.register(finding=finding, report=report, decision=decision)
    return registry, finding, report, decision


def _rehash_finding(finding: ValidatedFinding, **changes: object) -> ValidatedFinding:
    body = _identity_body(finding)
    body.update(changes)
    return ValidatedFinding(
        finding_id=stable_identity("validated-finding", body),
        **body,
    )


def test_machine_payload_round_trip_and_presentation_invariance() -> None:
    """Different safe presentations retain one exact reconstructible scientific identity."""
    registry, finding, report, decision = _registry()
    builder = ReportBuilder(source=registry)
    concise = builder.render(finding, ReportSpecification.create())
    detailed = builder.render(
        finding,
        ReportSpecification.create(
            audience=Audience.GENERAL,
            order=PresentationOrder.EVIDENCE_FIRST,
            detail_level=DetailLevel.DETAILED,
            wording_style=WordingStyle.TECHNICAL,
        ),
    )

    round_trip = FindingMachinePayload.from_json(concise.machine_payload.to_json())
    assert round_trip == concise.machine_payload
    assert round_trip.reconstruct_finding() == finding
    assert builder.verify(concise) == finding
    assert builder.verify(detailed) == finding
    assert concise.rendered_report_id != detailed.rendered_report_id
    assert concise.scientific_fingerprint == detailed.scientific_fingerprint
    assert concise.machine_payload == detailed.machine_payload
    assert concise.canonical_report_id == report.report_id
    assert concise.validation_decision_id == decision.decision_id
    assert concise.run_ref == report.run_id
    for substantive_value in (
        finding.claim,
        finding.target_id,
        finding.system_id,
        finding.scenario_id,
        *finding.caveats,
        *finding.evidence_refs,
    ):
        assert substantive_value in concise.markdown
        assert substantive_value in detailed.markdown
    assert "insurance" not in concise.markdown.lower()
    assert "trading" not in concise.markdown.lower()


@pytest.mark.parametrize(
    ("field", "changed"),
    [
        ("claim", "The system is commercially optimal."),
        ("metrics", (MetricResult(MetricName.MSE, 0.0, 8, 10, None),)),
        ("caveats", ("not a downstream-use decision",)),
    ],
)
def test_caller_cannot_override_conclusion_metrics_or_caveats(
    field: str,
    changed: object,
) -> None:
    """A correctly rehashed caller-authored finding has no canonical reporting authority."""
    registry, finding, _, _ = _registry()
    forged = _rehash_finding(finding, **{field: changed})
    assert forged.finding_id != finding.finding_id
    with pytest.raises(ReportingIntegrityError, match="authoritative report registry"):
        ReportBuilder(source=registry).render(forged, ReportSpecification.create())


@pytest.mark.parametrize("mutation", ["omit", "reorder"])
def test_payload_omitted_or_reordered_caveat_is_detected(mutation: str) -> None:
    """Self-rehashing the envelope cannot make changed caveats reconstruct the finding."""
    registry, finding, _, _ = _registry()
    rendered = ReportBuilder(source=registry).render(finding, ReportSpecification.create())
    raw = rendered.machine_payload.as_dict()
    caveats = list(raw["caveats"])
    raw["caveats"] = caveats[:-1] if mutation == "omit" else list(reversed(caveats))
    body = {key: value for key, value in raw.items() if key != "payload_id"}
    raw["payload_id"] = stable_identity("finding-machine-payload", body)

    with pytest.raises(ReportingIntegrityError, match="reconstruct exact finding"):
        FindingMachinePayload.from_json(json.dumps(raw))


def test_forged_rehashed_finding_cannot_enter_ledger_backed_registry() -> None:
    """Content hashes prove integrity, not publication authority."""
    registry, finding, report, decision = _registry()
    forged = _rehash_finding(finding, claim="A broader post-hoc scientific claim.")

    with pytest.raises(ReportingIntegrityError, match="canonical ledger"):
        registry.register(finding=forged, report=report, decision=decision)
    with pytest.raises(ReportingIntegrityError, match="authoritative report registry"):
        ReportBuilder(source=registry).render(forged, ReportSpecification.create())


def test_rejected_or_mismatched_evidence_cannot_render_as_validated() -> None:
    """Reporting cannot upgrade rejection or splice another canonical report into a finding."""
    _, finding, report, _ = _registry()
    rejected = _decision(report, ValidationStatus.REJECT)
    with pytest.raises(ReportingIntegrityError, match="rejected decision"):
        CanonicalFindingEvidence(finding, report, rejected)

    changed_body = _identity_body(report)
    changed_body["scenario_id"] = "scenario:changed"
    changed_report = EvaluationReport(
        report_id=stable_identity("evaluation-report", changed_body),
        **changed_body,
    )
    with pytest.raises(ReportingIntegrityError, match="identities do not match"):
        CanonicalFindingEvidence(finding, changed_report, _decision(changed_report))
