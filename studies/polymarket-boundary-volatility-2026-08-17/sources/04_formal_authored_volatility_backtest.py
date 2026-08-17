"""Run the frozen Fed-contract volatility trial through Chronos's authored harness."""

# ruff: noqa: D103, E501, EM101, INP001, PLR2004, T201, TRY003

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from pathlib import Path

from research_agent.data_adapters.polymarket import (
    PolymarketCorpusSnapshotRef,
    PolymarketCorpusStore,
    build_polymarket_development_analysis,
    register_polymarket_resolution_corpus,
)
from research_agent.data_foundation import (
    DataCatalogSnapshot,
    ObservationInput,
    ObservationRegistrar,
    SampleKey,
    TemporalOffset,
)
from research_agent.investigation import (
    AuthoredCandidateManifest,
    AuthoredDevelopmentEvaluator,
    AuthoredProgramProposal,
    CandidatePublisher,
    DevelopmentBudget,
    InvestigationRequest,
    ResearchQuestion,
)

SNAPSHOT_SHA256 = "610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f"
SNAPSHOT_SIZE = 19_434_443
WORKSPACE = Path(__file__).resolve().parents[5] / "data/chronos/polymarket-corpora"
MARKET_ID = "0x8bf1c1536ecb1c08fe13c6b71e8ab1f58bf3461c4cb79f5f1679f869a06aef86"
RECEIPT = Path(__file__).parents[1] / "development-receipts/04_formal_authored_volatility_backtest.json"

BASELINE_SOURCE = """
def make_features():
    values = history("market_probability")
    recent = values[-25:]
    variance = sum((recent[index]["value"] - recent[index - 1]["value"]) ** 2 for index in range(1, len(recent)))
    return {"raw_realized_variance_24h": variance}

def make_label():
    current = history("market_probability")[-1]["value"]
    return abs(outcome_path()[-1]["value"] - current)

def fit():
    rows = training_rows()
    return {"mean": sum(row["label"] for row in rows) / len(rows)}

def predict():
    return model_state()["mean"]
"""

VOLATILITY_SOURCE = """
def make_features():
    values = history("market_probability")
    recent = values[-25:]
    variance = sum((recent[index]["value"] - recent[index - 1]["value"]) ** 2 for index in range(1, len(recent)))
    return {"raw_realized_variance_24h": variance}

def make_label():
    current = history("market_probability")[-1]["value"]
    return abs(outcome_path()[-1]["value"] - current)

def fit():
    rows = training_rows()
    mean_x = sum(row["features"]["raw_realized_variance_24h"] for row in rows) / len(rows)
    mean_y = sum(row["label"] for row in rows) / len(rows)
    denominator = sum((row["features"]["raw_realized_variance_24h"] - mean_x) ** 2 for row in rows)
    slope = 0.0
    if denominator > 0.0:
        slope = sum((row["features"]["raw_realized_variance_24h"] - mean_x) * (row["label"] - mean_y) for row in rows) / denominator
    return {"intercept": mean_y - slope * mean_x, "slope": slope}

def predict():
    estimate = model_state()["intercept"] + model_state()["slope"] * feature_values()["raw_realized_variance_24h"]
    return min(1.0, max(0.0, estimate))
"""


def main() -> None:
    ref = PolymarketCorpusSnapshotRef(SNAPSHOT_SHA256, SNAPSHOT_SIZE)
    snapshot = PolymarketCorpusStore(WORKSPACE).load(ref)
    analysis = build_polymarket_development_analysis(snapshot, session_id="formal-volatility-2026-08-17")
    development_events = frozenset(analysis.partition.development_event_ids)
    development_markets = frozenset(
        contract.market_id for contract in snapshot.corpus.contracts if contract.event_id in development_events
    )
    if MARKET_ID not in development_markets:
        raise ValueError("predeclared formal market is not in the development partition")

    registration = register_polymarket_resolution_corpus(snapshot)
    datasets = []
    for dataset in registration.catalog.datasets:
        rows = tuple(
            ObservationInput(
                item.field_ref,
                item.value,
                item.reference_time,
                item.available_at,
                item.vintage_id,
                item.revision_number,
                item.source_ref,
                item.provenance_ref,
                item.availability_rule_version,
                item.dimensions,
                item.caveats,
            )
            for item in dataset.observations
            if dict(item.dimensions)["market_id"] in development_markets
        )
        datasets.append(ObservationRegistrar().register(dataset.schema, rows))
    catalog = DataCatalogSnapshot(registration.catalog.environment_id, tuple(datasets))
    if any(dict(item.dimensions)["market_id"] not in development_markets for item in catalog.observations):
        raise ValueError("protected market entered the development catalog")

    price_dataset = next(
        item
        for item in catalog.datasets
        if item.schema.dataset_id == "polymarket-outcome-price-series"
    )
    probability = price_dataset.schema.field_ref("market_probability")
    prices = sorted(
        (item for item in price_dataset.observations if dict(item.dimensions)["market_id"] == MARKET_ID),
        key=lambda item: item.reference_time,
    )
    keys = []
    for index in range(24, len(prices), 24):
        trailing_hours = (prices[index].reference_time - prices[index - 24].reference_time).total_seconds() / 3600.0
        if 18.0 <= trailing_hours <= 30.0:
            keys.append(SampleKey(prices[index].reference_time, prices[index].dimensions))

    question = ResearchQuestion(
        "question:fed-no-change-24h-volatility",
        "Does trailing 24-hour realized variance predict the next 24-hour absolute probability move?",
        catalog.environment_id,
        "task:polymarket-boundary-volatility-alternative-data",
        ("exploration:polymarket-magnitude-ablation-03",),
    )
    budget = DevelopmentBudget(2, 20, 20, "mse", 0.0)
    request = InvestigationRequest(
        question,
        catalog,
        tuple(keys),
        max(item.available_at for item in catalog.observations),
        budget,
        41,
    )
    manifest = AuthoredCandidateManifest(
        question.question_id,
        catalog.environment_id,
        (probability,),
        probability,
        TemporalOffset.elapsed(timedelta(hours=24)),
        1,
        prices[0].dimensions,
        ("raw_realized_variance_24h",),
        "exclude_example",
        ("exploration:polymarket-magnitude-ablation-03",),
        (ref.uri, "researcher:chronos-authored-program"),
    )
    publisher = CandidatePublisher()
    evaluator = AuthoredDevelopmentEvaluator(candidates=publisher.registry)
    baseline = publisher.publish(
        request,
        AuthoredProgramProposal(BASELINE_SOURCE, manifest, "Expanding historical-mean magnitude baseline.", ()),
        expected_parent_trial_id=None,
    )
    baseline_evidence = evaluator.evaluate(request, baseline)
    volatility = publisher.publish(
        request,
        AuthoredProgramProposal(
            VOLATILITY_SOURCE,
            manifest,
            "Expanding OLS test of the predeclared 24-hour realized-variance feature.",
            (baseline_evidence.trial_id,),
        ),
        expected_parent_trial_id=baseline_evidence.trial_id,
    )
    volatility_evidence = evaluator.evaluate(request, volatility)
    baseline_metrics = dict(baseline_evidence.metrics)
    volatility_metrics = dict(volatility_evidence.metrics)
    wins = sum(
        (forecast - actual) ** 2 < (base - actual) ** 2
        for forecast, base, actual in zip(
            volatility_evidence.predictions,
            baseline_evidence.predictions,
            volatility_evidence.outcomes,
            strict=True,
        )
    )
    payload = {
        "status": "succeeded",
        "epistemic_status": "FORMAL_DEVELOPMENT",
        "snapshot_ref": ref.uri,
        "partition_id": analysis.partition.partition_id,
        "development_event_count": len(development_events),
        "protected_event_count": analysis.partition.protected_event_count,
        "development_catalog_observation_count": len(catalog.observations),
        "protected_values_exposed": False,
        "market_id": MARKET_ID,
        "question": question.text,
        "feature_names": list(manifest.feature_names),
        "label": "absolute probability move over next elapsed 24 hours",
        "model_recipes": ["expanding historical mean", "expanding one-feature OLS clipped to [0,1]"],
        "sample_key_count": len(keys),
        "baseline": {
            "candidate_id": baseline.candidate_id,
            "source_sha256": baseline.source_sha256,
            "trial_id": baseline_evidence.trial_id,
            "evidence_id": baseline_evidence.evidence_id,
            "metrics": baseline_metrics,
            "oof_prediction_count": len(baseline_evidence.predictions),
        },
        "volatility": {
            "candidate_id": volatility.candidate_id,
            "source_sha256": volatility.source_sha256,
            "trial_id": volatility_evidence.trial_id,
            "evidence_id": volatility_evidence.evidence_id,
            "parent_trial_ids": list(volatility.parent_trial_ids),
            "metrics": volatility_metrics,
            "oof_prediction_count": len(volatility_evidence.predictions),
            "squared_error_wins_vs_baseline": wins,
        },
        "mse_delta_vs_baseline": volatility_metrics["mse"] - baseline_metrics["mse"],
        "actual_program_accesses": {
            "features": sorted({(item.interface, item.field_id) for item in volatility_evidence.feature_accesses}),
            "labels": sorted({(item.interface, item.field_id) for item in volatility_evidence.label_accesses}),
            "fit": sorted({(item.interface, item.field_id) for item in volatility_evidence.fit_accesses}),
            "prediction": sorted({(item.interface, item.field_id) for item in volatility_evidence.prediction_accesses}),
        },
        "protected_backtest_run": False,
        "warnings": [
            "This is selection-exposed chronological development evidence on one predeclared contract.",
            "Absolute-move prediction is not directional or executable trading evidence.",
            "The final seven event groups were omitted from the formal development catalog.",
        ],
    }
    content = json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n"
    if RECEIPT.exists() and RECEIPT.read_text() != content:
        raise ValueError("formal receipt path already contains different bytes")
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(content)
    print(json.dumps({"status": "SUCCEEDED", "receipt": str(RECEIPT), "receipt_sha256": hashlib.sha256(content.encode()).hexdigest(), "mse_delta_vs_baseline": payload["mse_delta_vs_baseline"]}, sort_keys=True))


if __name__ == "__main__":
    main()
