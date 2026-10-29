"""Polymarket corpus sources entering the enforced campaign boundary."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from research_agent.data_adapters.polymarket import (
    PolymarketDevelopmentAnalysis,
    PolymarketEventPartition,
    build_polymarket_campaign_analysis,
    literal_read_accesses,
)
from research_agent.data_adapters.polymarket.run_campaign_studies import load_catalog
from research_agent.exploration import (
    AnalysisDisposition,
    AnalysisHarness,
    ArtifactStore,
    AuthorizedDataView,
    CampaignManifest,
    CampaignStore,
    CapabilityPolicy,
    EvidenceTier,
    ResearchCampaignAuthority,
    ResourceLimits,
)

SESSION = "polymarket-campaign-test"
ENVIRONMENT = "polymarket-development-environment:partition"


def _development_analysis() -> PolymarketDevelopmentAnalysis:
    price_view = AuthorizedDataView(
        view_id="polymarket-development-prices",
        dataset_ref="polymarket-development-prices:partition",
        environment_ref=ENVIRONMENT,
        fields={"market_id": ("one", "two"), "market_probability": (0.2, 0.8)},
    )
    outcome_view = AuthorizedDataView(
        view_id="polymarket-development-outcomes",
        dataset_ref="polymarket-development-outcomes:partition",
        environment_ref=ENVIRONMENT,
        fields={"market_id": ("one", "two"), "resolution_payout": (0.0, 1.0)},
    )
    artifacts = ArtifactStore()
    harness = AnalysisHarness(
        views={price_view.view_id: price_view, outcome_view.view_id: outcome_view},
        policy=CapabilityPolicy(
            session_id=SESSION,
            environment_ref=ENVIRONMENT,
            allowed_fields_by_view={
                price_view.view_id: frozenset(price_view.fields),
                outcome_view.view_id: frozenset(outcome_view.fields),
            },
        ),
        artifacts=artifacts,
    )
    return PolymarketDevelopmentAnalysis(
        partition=PolymarketEventPartition(
            partition_id="partition",
            snapshot_ref="polymarket-corpus:sha256",
            development_event_ids=("event-one", "event-two"),
            protected_event_count=1,
            development_market_count=2,
            protected_market_count=1,
        ),
        price_view=price_view,
        outcome_view=outcome_view,
        registered_event_views=(),
        harness=harness,
        artifacts=artifacts,
        resource_limits=ResourceLimits(),
    )


def test_literal_source_gets_least_authority_manifest_and_campaign_receipt(
    tmp_path: Path,
) -> None:
    """Static read calls become exact required capabilities and observed provenance."""
    source = """
markets = read("polymarket-development-prices", "market_id")
prices = read("polymarket-development-prices", "market_probability")
outcomes = read("polymarket-development-outcomes", "resolution_payout")
result = structured_return("screen", {"n": len(markets), "mean": sum(prices + outcomes) / 4})
"""
    development = _development_analysis()
    item = build_polymarket_campaign_analysis(
        analysis_id="stochastic.screen.v1",
        family="stochastic-process",
        source=source,
        development_analysis=development,
        evidence_tier=EvidenceTier.EXPLORATORY_DEVELOPMENT,
    )
    manifest = CampaignManifest("campaign", "Exact corpus rerun.", (item,))
    authority = ResearchCampaignAuthority(manifest, store=CampaignStore(tmp_path))

    receipt = authority.execute(item.analysis_id, harness=development.harness, session_id=SESSION)
    completion = authority.complete({item.analysis_id: AnalysisDisposition.REJECTED})

    assert tuple((request.view_id, request.field_ids) for request in item.data_access) == (
        (
            "polymarket-development-prices",
            ("market_id", "market_probability"),
        ),
        ("polymarket-development-outcomes", ("resolution_payout",)),
    )
    assert receipt.admissible is True
    assert completion.execution_complete is True


def test_dynamic_read_requires_explicit_pre_execution_access_inventory() -> None:
    """A variable view or field cannot silently widen authority at runtime."""
    source = 'field = "market_id"\nvalues = read("polymarket-development-prices", field)'

    with pytest.raises(ValueError, match="dynamic read calls require explicit"):
        literal_read_accesses(source)
    item = build_polymarket_campaign_analysis(
        analysis_id="stochastic.dynamic.v1",
        family="stochastic-process",
        source=source,
        development_analysis=_development_analysis(),
        evidence_tier=EvidenceTier.EXPLORATORY_DEVELOPMENT,
        required_accesses=(("polymarket-development-prices", "market_id"),),
    )

    assert item.required_actual_accesses == (("polymarket-development-prices", "market_id"),)


def test_source_cannot_request_unregistered_polymarket_field() -> None:
    """Campaign construction fails before code can observe an undeclared input."""
    source = 'values = read("polymarket-development-prices", "wallet")'

    with pytest.raises(ValueError, match="absent from its registered views"):
        build_polymarket_campaign_analysis(
            analysis_id="behavioral.wallet.v1",
            family="behavioral-game-theory",
            source=source,
            development_analysis=_development_analysis(),
            evidence_tier=EvidenceTier.EXPLORATORY_DEVELOPMENT,
        )


def test_catalog_cannot_elevate_rerun_above_prior_study_ceiling(tmp_path: Path) -> None:
    """A top-level execution label cannot launder an exposed study into fresher evidence."""
    source = tmp_path / "study.py"
    source.write_text('values = read("polymarket-development-prices", "market_id")\n')
    catalog = tmp_path / "catalog.json"
    catalog.write_text(
        json.dumps(
            {
                "schema_version": "chronos-polymarket-corpus-campaign/v1",
                "campaign_id": "campaign",
                "mandate": "Do not elevate evidence.",
                "session_id": "session",
                "execution_evidence_tier": "PROTECTED_RESULT",
                "inputs": [
                    {
                        "input_id": "input",
                        "snapshot_sha256": "a" * 64,
                        "snapshot_size": 1,
                        "partition_id": "partition",
                    }
                ],
                "analyses": [
                    {
                        "analysis_id": "analysis",
                        "family": "stochastic-process",
                        "source": "study.py",
                        "input_id": "input",
                        "evidence_tier": "EXPLORATORY_DEVELOPMENT",
                        "disposition": "retained",
                    }
                ],
            }
        )
    )

    with pytest.raises(ValueError, match="exceeds a study's prior evidence ceiling"):
        load_catalog(catalog)
