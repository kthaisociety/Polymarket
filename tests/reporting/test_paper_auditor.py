"""Invariant and adversarial tests for receipt-backed paper acceptance."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from research_agent.data_foundation._identity import stable_identity
from research_agent.reporting import (
    AlternativeHypothesis,
    CampaignReference,
    ClaimDeclaration,
    ClaimKind,
    EffectDirection,
    EffectInterval,
    EvidenceAssertion,
    EvidenceLocator,
    EvidenceUnit,
    ExecutionDataKind,
    ExecutionEvidence,
    HypothesisFamily,
    HypothesisTest,
    PaperAuditError,
    PaperAuditor,
    PaperDecision,
    PaperProtocol,
    ValueFormat,
    bootstrap_mean_interval,
    verify_paper_audit_json,
)

EXPECTED_EXECUTION_COUNT = 90
EXPECTED_UNIQUE_ANALYSIS_COUNT = 48
EXPECTED_LEGACY_EXECUTION_COUNT = 42


def _json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode()


def _write_campaign(
    root: Path,
    *,
    directory: str = "campaign",
    analyses: tuple[tuple[str, str], ...] = (("analysis.one", "FRESH_DEVELOPMENT_REPLICATION"),),
) -> CampaignReference:
    campaign_root = root / directory
    executions_root = campaign_root / "executions"
    executions_root.mkdir(parents=True)
    manifest_analyses: list[dict[str, object]] = []
    execution_receipt_ids: list[str] = []
    dispositions: list[list[str]] = []
    campaign_id = f"campaign-{directory}"
    mandate = "Test exact retained evidence."
    for analysis_id, evidence_tier in analyses:
        source = 'result = structured_return("test", {"value": 1})\n'
        source_sha256 = hashlib.sha256(source.encode()).hexdigest()
        analysis_body = {
            "analysis_id": analysis_id,
            "family": "stochastic-process",
            "source_sha256": source_sha256,
            "data_access": (("view", ("value",)),),
            "required_actual_accesses": (("view", "value"),),
            "expected_dataset_refs": ("dataset:one",),
            "expected_environment_refs": ("environment:one",),
            "expected_harness_binding_identity": "harness:one",
            "evidence_tier": evidence_tier,
        }
        analysis_identity = stable_identity("campaign-analysis", analysis_body)
        manifest_analyses.append(
            {
                "analysis_id": analysis_id,
                "analysis_identity": analysis_identity,
                "family": "stochastic-process",
                "source": source,
                "source_sha256": source_sha256,
                "data_access": [{"view_id": "view", "field_ids": ["value"]}],
                "required_actual_accesses": [["view", "value"]],
                "expected_dataset_refs": ["dataset:one"],
                "expected_environment_refs": ["environment:one"],
                "expected_harness_binding_identity": "harness:one",
                "evidence_tier": evidence_tier,
            }
        )
    campaign_identity = stable_identity(
        "research-campaign",
        {
            "campaign_id": campaign_id,
            "mandate": mandate,
            "analysis_ids": tuple(item["analysis_identity"] for item in manifest_analyses),
        },
    )
    for analysis in manifest_analyses:
        execution_body = {
            "campaign_identity": campaign_identity,
            "analysis_identity": analysis["analysis_identity"],
            "analysis_id": analysis["analysis_id"],
            "source_sha256": analysis["source_sha256"],
            "harness_binding_identity": "harness:one",
            "harness_action_id": f"action:{analysis['analysis_id']}",
            "harness_execution_status": "succeeded",
            "actual_accesses": [["view", "dataset:one", "environment:one", "value"]],
            "dataset_refs": ["dataset:one"],
            "environment_refs": ["environment:one"],
            "summary": "Exact test result.",
            "details": {"value": 1},
            "warnings": [],
            "artifacts": [],
            "admissible": True,
            "admission_errors": [],
        }
        receipt_id = stable_identity("campaign-execution-receipt", execution_body)
        execution = {"receipt_id": receipt_id, **execution_body}
        execution_name = hashlib.sha256(str(analysis["analysis_id"]).encode()).hexdigest()
        (executions_root / f"{execution_name}.json").write_bytes(_json_bytes(execution))
        execution_receipt_ids.append(receipt_id)
        dispositions.append([str(analysis["analysis_id"]), "retained"])
    manifest = {
        "campaign_id": campaign_id,
        "mandate": mandate,
        "campaign_identity": campaign_identity,
        "analyses": manifest_analyses,
    }
    completion_body = {
        "campaign_identity": campaign_identity,
        "execution_complete": True,
        "dispositions": dispositions,
        "receipt_ids": execution_receipt_ids,
        "maximum_evidence_tier": max(tier for _, tier in analyses),
        "execution_validated_strategy_count": 0,
        "warnings": ["completion is not promotion"],
    }
    completion = {
        "receipt_id": stable_identity("campaign-completion-receipt", completion_body),
        **completion_body,
    }
    manifest_bytes = _json_bytes(manifest)
    completion_bytes = _json_bytes(completion)
    (campaign_root / "manifest.json").write_bytes(manifest_bytes)
    (campaign_root / "completion.json").write_bytes(completion_bytes)
    return CampaignReference(
        reference_id=directory,
        directory_ref=directory,
        manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        completion_sha256=hashlib.sha256(completion_bytes).hexdigest(),
    )


def _protocol(
    campaign: CampaignReference,
    *,
    claims: tuple[ClaimDeclaration, ...],
    intervals: tuple[EffectInterval, ...] = (),
    tests: tuple[HypothesisTest, ...] = (),
    families: tuple[HypothesisFamily, ...] = (),
) -> PaperProtocol:
    return PaperProtocol.create(
        title="A bounded paper",
        campaigns=(campaign,),
        claims=claims,
        intervals=intervals,
        tests=tests,
        families=families,
        alpha=0.05,
    )


def test_auditor_verifies_campaign_and_accepts_bounded_audit_fact(tmp_path: Path) -> None:
    """An exact complete campaign may back a bounded execution fact."""
    campaign = _write_campaign(tmp_path)
    evidence = EvidenceLocator("campaign", "analysis.one")
    claim = ClaimDeclaration(
        claim_id="C01",
        statement="The retained campaign completed this exact analysis.",
        kind=ClaimKind.AUDIT_FACT,
        evidence=(evidence,),
        assertions=(),
        interval_id=None,
        test_id=None,
        falsification_refs=(),
        stability_refs=(),
        frozen_before_evaluation=False,
        causal_design_ref=None,
        execution_evidence=None,
        limitations=("This is an execution fact, not scientific promotion.",),
    )

    report = PaperAuditor(root=tmp_path).audit(_protocol(campaign, claims=(claim,)))

    assert report.decision is PaperDecision.ACCEPT
    assert len(report.trials) == 1
    assert report.unique_analysis_count == 1
    assert report.claims[0].passed
    assert json.loads(report.to_json())["report_id"] == report.report_id
    assert verify_paper_audit_json(report.to_json()) == report.report_id

    changed = report.to_json().replace("exact analysis", "changed analysis")
    with pytest.raises(PaperAuditError, match="receipt identity"):
        verify_paper_audit_json(changed)


def test_replicated_process_claim_uses_event_inference_and_holm_family(tmp_path: Path) -> None:
    """A general process claim needs event uncertainty and complete-family adjustment."""
    campaign = _write_campaign(
        tmp_path,
        analyses=(
            ("analysis.one", "FRESH_DEVELOPMENT_REPLICATION"),
            ("analysis.two", "FRESH_DEVELOPMENT_REPLICATION"),
        ),
    )
    first = EvidenceLocator("campaign", "analysis.one")
    second = EvidenceLocator("campaign", "analysis.two")
    interval = EffectInterval(
        interval_id="interval:one",
        evidence=first,
        unit=EvidenceUnit.EVENT,
        method="whole-event bootstrap",
        confidence_level=0.95,
        estimate=0.2,
        lower=0.1,
        upper=0.3,
        null_value=0.0,
        direction=EffectDirection.ABOVE,
        repetitions=2000,
    )
    first_test = HypothesisTest(
        test_id="test:one",
        evidence=first,
        family_id="family:process",
        unit=EvidenceUnit.EVENT,
        successes=10,
        trials=10,
        null_probability=0.5,
        alternative=AlternativeHypothesis.GREATER,
    )
    second_test = HypothesisTest(
        test_id="test:two",
        evidence=second,
        family_id="family:process",
        unit=EvidenceUnit.EVENT,
        successes=8,
        trials=10,
        null_probability=0.5,
        alternative=AlternativeHypothesis.GREATER,
    )
    family = HypothesisFamily(
        family_id="family:process",
        test_ids=("test:one", "test:two"),
        search_evidence=(first, second),
        complete_test_inventory=True,
    )
    claim = ClaimDeclaration(
        claim_id="C02",
        statement="The process feature value 1 replicated across fresh events.",
        kind=ClaimKind.PROCESS_GENERALIZATION,
        evidence=(first, second),
        assertions=(EvidenceAssertion(first, ("value",), 1, ValueFormat.INTEGER),),
        interval_id="interval:one",
        test_id="test:one",
        falsification_refs=(second,),
        stability_refs=(first,),
        frozen_before_evaluation=True,
        causal_design_ref=None,
        execution_evidence=None,
        limitations=("The result concerns registered samples.",),
    )

    report = PaperAuditor(root=tmp_path).audit(
        _protocol(
            campaign,
            claims=(claim,),
            intervals=(interval,),
            tests=(first_test, second_test),
            families=(family,),
        )
    )

    assert report.decision is PaperDecision.ACCEPT
    adjusted = {result.test_id: result.adjusted_p_value for result in report.tests}
    assert adjusted["test:one"] == pytest.approx(0.001953125)
    assert report.claims[0].passed

    row_interval = replace(interval, unit=EvidenceUnit.ROW)
    row_report = PaperAuditor(root=tmp_path).audit(
        _protocol(
            campaign,
            claims=(claim,),
            intervals=(row_interval,),
            tests=(first_test, second_test),
            families=(family,),
        )
    )
    assert row_report.decision is PaperDecision.REJECT
    assert not next(
        check for check in row_report.claims[0].checks if check.code == "DEPENDENCE_AWARE_INTERVAL"
    ).passed


def test_incomplete_search_family_uses_all_trials_as_bonferroni_penalty(tmp_path: Path) -> None:
    """Unscored searched trials conservatively increase the winner's penalty."""
    campaign = _write_campaign(
        tmp_path,
        analyses=tuple((f"analysis.{index}", "EXPLORATORY_DEVELOPMENT") for index in range(1, 6)),
    )
    winner = EvidenceLocator("campaign", "analysis.1")
    test = HypothesisTest(
        test_id="test:winner",
        evidence=winner,
        family_id="family:searched",
        unit=EvidenceUnit.EVENT,
        successes=9,
        trials=10,
        null_probability=0.5,
        alternative=AlternativeHypothesis.GREATER,
    )
    family = HypothesisFamily(
        family_id="family:searched",
        test_ids=("test:winner",),
        search_evidence=tuple(
            EvidenceLocator("campaign", f"analysis.{index}") for index in range(1, 6)
        ),
        complete_test_inventory=False,
    )
    claim = ClaimDeclaration(
        claim_id="C03",
        statement="The development result value 1 survived the recorded search penalty.",
        kind=ClaimKind.DEVELOPMENT_RESULT,
        evidence=(winner,),
        assertions=(EvidenceAssertion(winner, ("value",), 1, ValueFormat.INTEGER),),
        interval_id=None,
        test_id="test:winner",
        falsification_refs=(),
        stability_refs=(),
        frozen_before_evaluation=False,
        causal_design_ref=None,
        execution_evidence=None,
        limitations=("This remains selection-exposed development evidence.",),
    )

    report = PaperAuditor(root=tmp_path).audit(
        _protocol(
            campaign,
            claims=(claim,),
            tests=(test,),
            families=(family,),
        )
    )

    result = report.tests[0]
    assert result.adjustment_method == "bonferroni-recorded-search"
    assert result.adjusted_p_value == pytest.approx(result.raw_p_value * 5)


def test_trading_claim_rejects_sampled_marks_and_missing_execution_facts(tmp_path: Path) -> None:
    """Sampled marks cannot satisfy the execution or trading-evidence gates."""
    campaign = _write_campaign(tmp_path)
    evidence = EvidenceLocator("campaign", "analysis.one")
    interval = EffectInterval(
        interval_id="interval:edge",
        evidence=evidence,
        unit=EvidenceUnit.EVENT,
        method="whole-event bootstrap",
        confidence_level=0.95,
        estimate=0.04,
        lower=0.01,
        upper=0.08,
        null_value=0.0,
        direction=EffectDirection.ABOVE,
        repetitions=2000,
    )
    test = HypothesisTest(
        test_id="test:edge",
        evidence=evidence,
        family_id="family:edge",
        unit=EvidenceUnit.EVENT,
        successes=10,
        trials=10,
        null_probability=0.5,
        alternative=AlternativeHypothesis.GREATER,
    )
    family = HypothesisFamily(
        family_id="family:edge",
        test_ids=("test:edge",),
        search_evidence=(evidence,),
        complete_test_inventory=True,
    )
    claim = ClaimDeclaration(
        claim_id="C04",
        statement="The value 1 strategy is profitable after executable trading costs.",
        kind=ClaimKind.TRADING_STRATEGY,
        evidence=(evidence,),
        assertions=(EvidenceAssertion(evidence, ("value",), 1, ValueFormat.INTEGER),),
        interval_id="interval:edge",
        test_id="test:edge",
        falsification_refs=(evidence,),
        stability_refs=(evidence,),
        frozen_before_evaluation=True,
        causal_design_ref=None,
        execution_evidence=ExecutionEvidence(
            data_kind=ExecutionDataKind.SAMPLED_MARKS,
            observed_spreads=False,
            observed_fees=False,
            modeled_latency=False,
            modeled_queue_position=False,
            modeled_partial_fills=False,
        ),
        limitations=(),
    )

    report = PaperAuditor(root=tmp_path).audit(
        _protocol(
            campaign,
            claims=(claim,),
            intervals=(interval,),
            tests=(test,),
            families=(family,),
        )
    )

    assert report.decision is PaperDecision.REJECT
    failed_codes = {check.code for check in report.claims[0].checks if not check.passed}
    assert "EXECUTION_TIER_INSUFFICIENT" in failed_codes
    assert "EXECUTION_DATA_INSUFFICIENT" in failed_codes


def test_changed_receipt_bytes_fail_before_claim_evaluation(tmp_path: Path) -> None:
    """Changed execution bytes fail before scientific wording is considered."""
    campaign = _write_campaign(tmp_path)
    receipt = next((tmp_path / "campaign" / "executions").glob("*.json"))
    changed = receipt.read_text().replace('"value":1', '"value":2')
    receipt.write_text(changed)
    claim = ClaimDeclaration(
        claim_id="C05",
        statement="The retained campaign completed this exact analysis.",
        kind=ClaimKind.AUDIT_FACT,
        evidence=(EvidenceLocator("campaign", "analysis.one"),),
        assertions=(),
        interval_id=None,
        test_id=None,
        falsification_refs=(),
        stability_refs=(),
        frozen_before_evaluation=False,
        causal_design_ref=None,
        execution_evidence=None,
        limitations=(),
    )

    with pytest.raises(PaperAuditError, match="execution receipt identity"):
        PaperAuditor(root=tmp_path).audit(_protocol(campaign, claims=(claim,)))


def test_claim_display_value_must_match_exact_receipt_value(tmp_path: Path) -> None:
    """A plausible but changed manuscript number turns the publication decision red."""
    campaign = _write_campaign(
        tmp_path,
        analyses=(("analysis.one", "EXPLORATORY_DEVELOPMENT"),),
    )
    evidence = EvidenceLocator("campaign", "analysis.one")
    claim = ClaimDeclaration(
        claim_id="C06",
        statement="The retained development result had value 2.",
        kind=ClaimKind.DEVELOPMENT_RESULT,
        evidence=(evidence,),
        assertions=(EvidenceAssertion(evidence, ("value",), 1, ValueFormat.INTEGER),),
        interval_id=None,
        test_id=None,
        falsification_refs=(),
        stability_refs=(),
        frozen_before_evaluation=False,
        causal_design_ref=None,
        execution_evidence=None,
        limitations=("Development evidence only.",),
    )

    report = PaperAuditor(root=tmp_path).audit(_protocol(campaign, claims=(claim,)))

    assert report.decision is PaperDecision.REJECT
    assert not next(
        check for check in report.claims[0].checks if check.code == "EVIDENCE_VALUE_ASSERTIONS"
    ).passed


def test_whole_event_bootstrap_is_deterministic_and_keeps_event_unit() -> None:
    """The bootstrap is exactly replayable for a fixed whole-event vector."""
    first = bootstrap_mean_interval((0.1, 0.2, 0.3, 0.4), repetitions=2000, seed=17)
    second = bootstrap_mean_interval((0.1, 0.2, 0.3, 0.4), repetitions=2000, seed=17)

    assert first == second
    assert first[0] < sum((0.1, 0.2, 0.3, 0.4)) / 4 < first[1]


def test_retained_polymarket_paper_receipt_is_accepted_and_complete() -> None:
    """The real retained paper receipt covers every governed campaign execution."""
    path = Path(
        "studies/polymarket-paper-acceptance-audit-2026-08-24/paper-acceptance-receipt.json"
    )
    serialized = path.read_text()
    decoded = cast("dict[str, object]", json.loads(serialized))
    claims = cast("list[dict[str, object]]", decoded["claims"])
    campaigns = cast("list[dict[str, object]]", decoded["campaigns"])

    assert verify_paper_audit_json(serialized) == decoded["report_id"]
    assert decoded["decision"] == "accept"
    assert len(cast("list[object]", decoded["trials"])) == EXPECTED_EXECUTION_COUNT
    assert decoded["unique_analysis_count"] == EXPECTED_UNIQUE_ANALYSIS_COUNT
    assert decoded["duplicate_execution_count"] == EXPECTED_LEGACY_EXECUTION_COUNT
    assert all(cast("bool", claim["passed"]) for claim in claims)
    assert (
        sum(cast("int", campaign["legacy_unbound_execution_count"]) for campaign in campaigns)
        == EXPECTED_LEGACY_EXECUTION_COUNT
    )
