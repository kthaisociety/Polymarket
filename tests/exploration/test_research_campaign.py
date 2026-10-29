"""Enforced research-campaign admission and completion tests."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from research_agent.exploration import (
    AnalysisHarness,
    ArtifactStore,
    AuthorizedDataView,
    CapabilityPolicy,
    DataAccessRequest,
    ResourceLimits,
)
from research_agent.exploration.campaign import (
    AnalysisDisposition,
    CampaignAnalysis,
    CampaignCompletionError,
    CampaignManifest,
    CampaignStore,
    EvidenceTier,
    ResearchCampaignAuthority,
)

SESSION = "campaign-session"
ENVIRONMENT = "campaign-environment"
VIEW = "registered-prices"
DATASET = "dataset:prices:sha256"
SOURCE = """
prices = read("registered-prices", "price")
result = structured_return(
    "fixed development screen",
    {"decision": "REJECT", "mean": sum(prices) / len(prices)},
)
"""


def _harness(
    *,
    limits: ResourceLimits | None = None,
    prices: tuple[float, ...] = (0.2, 0.4, 0.6),
) -> AnalysisHarness:
    view = AuthorizedDataView(
        view_id=VIEW,
        dataset_ref=DATASET,
        environment_ref=ENVIRONMENT,
        fields={"price": prices, "future": (0.9,)},
    )
    return AnalysisHarness(
        views={VIEW: view},
        policy=CapabilityPolicy(
            session_id=SESSION,
            environment_ref=ENVIRONMENT,
            allowed_fields_by_view={VIEW: frozenset({"price"})},
        ),
        artifacts=ArtifactStore(),
        resource_limits=limits,
    )


def _analysis(
    *,
    analysis_id: str = "behavioral.focal-anchor.v1",
    source: str = SOURCE,
    tier: EvidenceTier = EvidenceTier.EXPLORATORY_DEVELOPMENT,
) -> CampaignAnalysis:
    harness = _harness()
    return CampaignAnalysis(
        analysis_id=analysis_id,
        family="behavioral-game-theory",
        source=source,
        data_access=(DataAccessRequest(VIEW, ("price",)),),
        required_actual_accesses=((VIEW, "price"),),
        expected_dataset_refs=(DATASET,),
        expected_environment_refs=(ENVIRONMENT,),
        expected_harness_binding_identity=harness.binding_identity,
        evidence_tier=tier,
    )


def _authority(root: Path, *analyses: CampaignAnalysis) -> ResearchCampaignAuthority:
    manifest = CampaignManifest(
        campaign_id="polymarket-rerun-2026-08-24",
        mandate="Rerun exact behavioral and stochastic analyses through Chronos.",
        analyses=analyses,
    )
    return ResearchCampaignAuthority(manifest, store=CampaignStore(root))


def test_campaign_completes_only_from_its_own_harness_issued_receipts(
    tmp_path: Path,
) -> None:
    """Accept only receipts minted by this authority's harness execution."""
    analysis = _analysis()
    authority = _authority(tmp_path, analysis)

    receipt = authority.execute(
        analysis.analysis_id,
        harness=_harness(),
        session_id=SESSION,
    )
    completion = authority.complete({analysis.analysis_id: AnalysisDisposition.REJECTED})

    assert receipt.source_sha256 == hashlib.sha256(SOURCE.encode()).hexdigest()
    assert receipt.actual_accesses == ((VIEW, DATASET, ENVIRONMENT, "price"),)
    assert receipt.harness_execution_status == "succeeded"
    assert completion.execution_complete is True
    assert completion.maximum_evidence_tier is EvidenceTier.EXPLORATORY_DEVELOPMENT
    assert completion.execution_validated_strategy_count == 0
    assert completion.receipt_ids == (receipt.receipt_id,)


def test_legacy_or_manually_asserted_receipt_cannot_enter_campaign(
    tmp_path: Path,
) -> None:
    """Reject evidence assembled outside the campaign authority."""
    analysis = _analysis()
    authority = _authority(tmp_path, analysis)

    with pytest.raises(TypeError, match="campaign accepts no external execution receipts"):
        authority.admit_external_receipt(  # type: ignore[attr-defined]
            {"source_sha256": hashlib.sha256(SOURCE.encode()).hexdigest()}
        )
    with pytest.raises(CampaignCompletionError, match="missing harness execution"):
        authority.complete({analysis.analysis_id: AnalysisDisposition.REJECTED})


def test_direct_database_source_is_denied_and_cannot_complete_campaign(
    tmp_path: Path,
) -> None:
    """Prevent a study source from bypassing registered data views."""
    source = """
import asyncpg
result = structured_return("bypass", {})
"""
    analysis = _analysis(source=source)
    authority = _authority(tmp_path, analysis)

    receipt = authority.execute(
        analysis.analysis_id,
        harness=_harness(),
        session_id=SESSION,
    )

    assert receipt.harness_execution_status == "denied"
    with pytest.raises(CampaignCompletionError, match="did not succeed"):
        authority.complete({analysis.analysis_id: AnalysisDisposition.REJECTED})


def test_missing_required_field_access_cannot_complete_campaign(tmp_path: Path) -> None:
    """Require actual consumption of every scientifically material input."""
    source = 'result = structured_return("did not read the data", {"decision": "REJECT"})'
    analysis = _analysis(source=source)
    authority = _authority(tmp_path, analysis)

    receipt = authority.execute(
        analysis.analysis_id,
        harness=_harness(),
        session_id=SESSION,
    )

    assert receipt.harness_execution_status == "succeeded"
    assert receipt.admissible is False
    with pytest.raises(CampaignCompletionError, match="required actual accesses"):
        authority.complete({analysis.analysis_id: AnalysisDisposition.REJECTED})


def test_source_identity_is_manifest_owned_and_exact_retry_converges(
    tmp_path: Path,
) -> None:
    """Freeze source identity and make an exact execution retry idempotent."""
    analysis = _analysis()
    authority = _authority(tmp_path, analysis)

    first = authority.execute(
        analysis.analysis_id,
        harness=_harness(),
        session_id=SESSION,
    )
    second = authority.execute(
        analysis.analysis_id,
        harness=_harness(),
        session_id=SESSION,
    )

    assert first == second
    with pytest.raises(ValueError, match="manifest analysis identity conflict"):
        CampaignManifest(
            campaign_id="polymarket-rerun-2026-08-24",
            mandate="Rerun exact behavioral and stochastic analyses through Chronos.",
            analyses=(analysis, _analysis(source=SOURCE + "\n")),
        )


def test_completion_requires_every_declared_analysis_and_disposition(
    tmp_path: Path,
) -> None:
    """Refuse closure while any manifest item or interpretation is absent."""
    behavioral = _analysis()
    stochastic = _analysis(analysis_id="stochastic.jump-law.v1")
    authority = _authority(tmp_path, behavioral, stochastic)
    authority.execute(behavioral.analysis_id, harness=_harness(), session_id=SESSION)

    with pytest.raises(CampaignCompletionError, match="missing harness execution"):
        authority.complete(
            {
                behavioral.analysis_id: AnalysisDisposition.REJECTED,
                stochastic.analysis_id: AnalysisDisposition.REJECTED,
            }
        )

    authority.execute(stochastic.analysis_id, harness=_harness(), session_id=SESSION)
    with pytest.raises(CampaignCompletionError, match="missing disposition"):
        authority.complete({behavioral.analysis_id: AnalysisDisposition.REJECTED})


def test_exploratory_execution_cannot_be_declared_execution_validated(
    tmp_path: Path,
) -> None:
    """Keep scientific evidence ceilings separate from execution success."""
    analysis = _analysis()
    authority = _authority(tmp_path, analysis)
    authority.execute(analysis.analysis_id, harness=_harness(), session_id=SESSION)

    with pytest.raises(CampaignCompletionError, match="exceeds the manifest evidence tier"):
        authority.complete({analysis.analysis_id: AnalysisDisposition.EXECUTION_VALIDATED})


def test_campaign_store_recovers_exact_receipts_without_reexecution(tmp_path: Path) -> None:
    """A restarted authority verifies and reuses its immutable receipt bytes."""
    analysis = _analysis()
    first_authority = _authority(tmp_path, analysis)
    first = first_authority.execute(
        analysis.analysis_id,
        harness=_harness(),
        session_id=SESSION,
    )

    restarted = _authority(tmp_path, analysis)
    recovered = restarted.execute(
        analysis.analysis_id,
        harness=_harness(),
        session_id=SESSION,
    )
    completion = restarted.complete({analysis.analysis_id: AnalysisDisposition.REJECTED})
    restarted_after_completion = _authority(tmp_path, analysis)

    assert recovered == first
    assert (
        restarted_after_completion.complete({analysis.analysis_id: AnalysisDisposition.REJECTED})
        == completion
    )
    assert json.loads((tmp_path / "manifest.json").read_text())["campaign_identity"] == (
        first.campaign_identity
    )
    with pytest.raises(ValueError, match="immutable campaign content conflicts"):
        _authority(tmp_path, _analysis(source=SOURCE + "\n"))


def test_campaign_store_durably_retains_externalized_result(tmp_path: Path) -> None:
    """Oversized structured details remain verifiable after process exit."""
    source = """
prices = read("registered-prices", "price")
result = structured_return("externalized", {"values": list(range(1000)), "n": len(prices)})
"""
    externalizing_harness = _harness(limits=ResourceLimits(max_inline_bytes=100))
    analysis = CampaignAnalysis(
        analysis_id="behavioral.focal-anchor.v1",
        family="behavioral-game-theory",
        source=source,
        data_access=(DataAccessRequest(VIEW, ("price",)),),
        required_actual_accesses=((VIEW, "price"),),
        expected_dataset_refs=(DATASET,),
        expected_environment_refs=(ENVIRONMENT,),
        expected_harness_binding_identity=externalizing_harness.binding_identity,
        evidence_tier=EvidenceTier.EXPLORATORY_DEVELOPMENT,
    )
    authority = _authority(tmp_path, analysis)

    receipt = authority.execute(
        analysis.analysis_id,
        harness=externalizing_harness,
        session_id=SESSION,
    )
    restarted = _authority(tmp_path, analysis)

    assert receipt.details is None
    assert len(receipt.artifacts) == 1
    artifact = receipt.artifacts[0]
    content = (tmp_path / artifact.object_ref).read_bytes()
    assert hashlib.sha256(content).hexdigest() == artifact.sha256
    assert json.loads(content)["details"]["values"] == list(range(1000))
    assert (
        restarted.execute(
            analysis.analysis_id,
            harness=externalizing_harness,
            session_id=SESSION,
        )
        == receipt
    )


def test_copied_dataset_labels_cannot_substitute_different_view_values(
    tmp_path: Path,
) -> None:
    """Bind receipts to exact authorized values, not caller-copied reference strings."""
    analysis = _analysis()
    authority = _authority(tmp_path, analysis)

    with pytest.raises(ValueError, match="harness binding differs"):
        authority.execute(
            analysis.analysis_id,
            harness=_harness(prices=(0.99, 0.99, 0.99)),
            session_id=SESSION,
        )
    with pytest.raises(CampaignCompletionError, match="missing harness execution"):
        authority.complete({analysis.analysis_id: AnalysisDisposition.REJECTED})
