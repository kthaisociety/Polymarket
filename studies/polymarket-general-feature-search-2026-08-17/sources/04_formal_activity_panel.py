"""Replay the selected legal activity model through the authored panel harness."""

# ruff: noqa: D103, E501, EM101, INP001, PLR2004, T201, TRY003

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from pathlib import Path

from research_agent.data_adapters.polymarket import (
    PolymarketCorpusSnapshot,
    PolymarketCorpusSnapshotRef,
    PolymarketCorpusStore,
    build_polymarket_development_analysis,
    register_polymarket_resolution_corpus,
)
from research_agent.data_foundation import (
    DataCatalogSnapshot,
    ObservationInput,
    ObservationRegistrar,
    RegisteredDataset,
    RegisteredObservation,
    SampleKey,
    TemporalOffset,
)
from research_agent.investigation import (
    AuthoredCandidateManifest,
    AuthoredDevelopmentEvaluator,
    AuthoredDevelopmentEvidence,
    AuthoredProgramProposal,
    CandidatePublisher,
    DevelopmentBudget,
    InvestigationRequest,
    ResearchQuestion,
)

SNAPSHOT_SHA256 = "610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f"
SNAPSHOT_SIZE = 19_434_443
WORKSPACE = Path(__file__).resolve().parents[5] / "data/chronos/polymarket-corpora"
RECEIPT = Path(__file__).parents[1] / "development-receipts/04_formal_activity_panel.json"
FEATURE_NAMES = (
    "boundary_distance",
    "current_boundary_state_002",
    "realized_variance_6h",
    "jump_concentration_24h",
    "zero_change_fraction_24h",
    "mean_absolute_change_24h",
)
RIDGE_PENALTY = 0.1
SAMPLES_PER_MARKET = 3

FEATURE_SOURCE = """
def activity_features():
    observations = history("market_probability")
    recent = observations[-25:]
    probability = recent[-1]["value"]
    rv6 = 0.0
    rv24 = 0.0
    max_step = 0.0
    zero_count = 0.0
    absolute_sum = 0.0
    for index in range(1, len(recent)):
        step = recent[index]["value"] - recent[index - 1]["value"]
        absolute_step = abs(step)
        rv24 = rv24 + step * step
        absolute_sum = absolute_sum + absolute_step
        if absolute_step == 0.0:
            zero_count = zero_count + 1.0
        if absolute_step > max_step:
            max_step = absolute_step
        if index >= len(recent) - 6:
            rv6 = rv6 + step * step
    return {
        "boundary_distance": min(probability, 1.0 - probability),
        "current_boundary_state_002": 1.0 if probability <= 0.02 or probability >= 0.98 else 0.0,
        "realized_variance_6h": rv6,
        "jump_concentration_24h": max_step / ((rv24 + 0.000000000001) ** 0.5),
        "zero_change_fraction_24h": zero_count / 24.0,
        "mean_absolute_change_24h": absolute_sum / 24.0,
    }

def make_features():
    return activity_features()

def make_label():
    current = history("market_probability")[-1]["value"]
    return abs(outcome_path()[-1]["value"] - current)
"""

BASELINE_SOURCE = (
    FEATURE_SOURCE
    + """
def fit():
    rows = training_rows()
    event_counts = {}
    for row in rows:
        event = dimension_value(row, "event_id")
        if event not in event_counts:
            event_counts[event] = 0
        event_counts[event] = event_counts[event] + 1
    total = 0.0
    for row in rows:
        event = dimension_value(row, "event_id")
        total = total + row["label"] / event_counts[event]
    return {"mean": total / len(event_counts)}

def dimension_value(row, name):
    for pair in row["dimensions"]:
        if pair[0] == name:
            return pair[1]
    return ""

def predict():
    return model_state()["mean"]
"""
)

RIDGE_SOURCE = (
    FEATURE_SOURCE
    + """
def dimension_value(row, name):
    for pair in row["dimensions"]:
        if pair[0] == name:
            return pair[1]
    return ""

def solve_linear(matrix, vector):
    size = len(vector)
    augmented = [[0.0 for unused in range(size + 1)] for unused in range(size)]
    for row in range(size):
        for column in range(size):
            augmented[row][column] = matrix[row][column]
        augmented[row][size] = vector[row]
    for pivot in range(size):
        best = pivot
        for row in range(pivot + 1, size):
            if abs(augmented[row][pivot]) > abs(augmented[best][pivot]):
                best = row
        if best != pivot:
            temporary = augmented[pivot]
            augmented[pivot] = augmented[best]
            augmented[best] = temporary
        divisor = augmented[pivot][pivot]
        if abs(divisor) < 0.000000000001:
            divisor = 0.000000000001
        for column in range(pivot, size + 1):
            augmented[pivot][column] = augmented[pivot][column] / divisor
        for row in range(size):
            if row != pivot:
                factor = augmented[row][pivot]
                for column in range(pivot, size + 1):
                    augmented[row][column] = augmented[row][column] - factor * augmented[pivot][column]
    return [augmented[row][size] for row in range(size)]

def fit():
    rows = training_rows()
    names = [
        "boundary_distance",
        "current_boundary_state_002",
        "realized_variance_6h",
        "jump_concentration_24h",
        "zero_change_fraction_24h",
        "mean_absolute_change_24h",
    ]
    event_counts = {}
    for row in rows:
        event = dimension_value(row, "event_id")
        if event not in event_counts:
            event_counts[event] = 0
        event_counts[event] = event_counts[event] + 1
    event_total = len(event_counts)
    feature_mean = [0.0 for unused in names]
    target_mean = 0.0
    second = [[0.0 for unused in names] for unused in names]
    cross_target = [0.0 for unused in names]
    for row in rows:
        event = dimension_value(row, "event_id")
        weight = 1.0 / (event_total * event_counts[event])
        target_mean = target_mean + weight * row["label"]
        for left in range(len(names)):
            left_value = row["features"][names[left]]
            feature_mean[left] = feature_mean[left] + weight * left_value
            cross_target[left] = cross_target[left] + weight * left_value * row["label"]
            for right in range(len(names)):
                second[left][right] = second[left][right] + weight * left_value * row["features"][names[right]]
    scale = [0.0 for unused in names]
    covariance = [[0.0 for unused in names] for unused in names]
    target_covariance = [0.0 for unused in names]
    for left in range(len(names)):
        variance = second[left][left] - feature_mean[left] * feature_mean[left]
        if variance < 0.000000000001:
            variance = 0.000000000001
        scale[left] = variance ** 0.5
    for left in range(len(names)):
        target_covariance[left] = (cross_target[left] - feature_mean[left] * target_mean) / scale[left]
        for right in range(len(names)):
            covariance[left][right] = (second[left][right] - feature_mean[left] * feature_mean[right]) / (scale[left] * scale[right])
        covariance[left][left] = covariance[left][left] + 0.1
    return {
        "target_mean": target_mean,
        "feature_mean": feature_mean,
        "scale": scale,
        "coefficients": solve_linear(covariance, target_covariance),
    }

def predict():
    names = [
        "boundary_distance",
        "current_boundary_state_002",
        "realized_variance_6h",
        "jump_concentration_24h",
        "zero_change_fraction_24h",
        "mean_absolute_change_24h",
    ]
    state = model_state()
    values = feature_values()
    estimate = state["target_mean"]
    for index in range(len(names)):
        estimate = estimate + state["coefficients"][index] * (values[names[index]] - state["feature_mean"][index]) / state["scale"][index]
    return min(1.0, max(0.0, estimate))
"""
)


def _development_catalog(
    snapshot: PolymarketCorpusSnapshot,
    development_markets: frozenset[str],
) -> DataCatalogSnapshot:
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
    return DataCatalogSnapshot(registration.catalog.environment_id, tuple(datasets))


def _sample_keys(price_dataset: RegisteredDataset) -> tuple[SampleKey, ...]:
    by_market: dict[str, list[RegisteredObservation]] = {}
    for item in price_dataset.observations:
        market_id = dict(item.dimensions)["market_id"]
        by_market.setdefault(market_id, []).append(item)
    keys = []
    for market_id in sorted(by_market):
        prices = sorted(by_market[market_id], key=lambda item: item.reference_time)
        legal = []
        for index in range(24, len(prices) - 6, 6):
            trailing_hours = (
                prices[index].reference_time - prices[index - 24].reference_time
            ).total_seconds() / 3600.0
            future_hours = (
                prices[index + 6].reference_time - prices[index].reference_time
            ).total_seconds() / 3600.0
            if 18.0 <= trailing_hours <= 30.0 and 4.5 <= future_hours <= 7.5:
                legal.append(SampleKey(prices[index].reference_time, prices[index].dimensions))
        if not legal:
            continue
        selected_indices = sorted({0, len(legal) // 2, len(legal) - 1})
        keys.extend(legal[index] for index in selected_indices[:SAMPLES_PER_MARKET])
    return tuple(sorted(keys, key=lambda item: (item.decision_time, item.dimensions)))


def _event_metrics(evidence: AuthoredDevelopmentEvidence) -> dict[str, float | int]:
    squared_by_event: dict[str, list[float]] = {}
    for key, prediction, outcome in zip(
        evidence.row_keys,
        evidence.predictions,
        evidence.outcomes,
        strict=True,
    ):
        event_id = dict(key.dimensions)["event_id"]
        squared_by_event.setdefault(event_id, []).append((prediction - outcome) ** 2)
    event_mse = [sum(values) / len(values) for values in squared_by_event.values()]
    return {
        "event_count": len(event_mse),
        "event_macro_mse": sum(event_mse) / len(event_mse),
    }


def main() -> None:
    ref = PolymarketCorpusSnapshotRef(SNAPSHOT_SHA256, SNAPSHOT_SIZE)
    snapshot = PolymarketCorpusStore(WORKSPACE).load(ref)
    analysis = build_polymarket_development_analysis(
        snapshot,
        session_id="formal-activity-panel-2026-08-17",
    )
    development_events = frozenset(analysis.partition.development_event_ids)
    development_markets = frozenset(
        contract.market_id
        for contract in snapshot.corpus.contracts
        if contract.event_id in development_events
    )
    catalog = _development_catalog(snapshot, development_markets)
    if any(
        dict(item.dimensions)["market_id"] not in development_markets
        for item in catalog.observations
    ):
        raise ValueError("protected market entered the formal development catalog")
    price_dataset = next(
        item
        for item in catalog.datasets
        if item.schema.dataset_id == "polymarket-outcome-price-series"
    )
    probability = price_dataset.schema.field_ref("market_probability")
    keys = _sample_keys(price_dataset)
    question = ResearchQuestion(
        "question:polymarket-six-hour-activity-panel",
        "Do six legal internal activity features predict the next six-hour absolute probability move across development contracts?",
        catalog.environment_id,
        "task:polymarket-general-feature-label-search",
        (
            "exploration:general-feature-benchmark-01",
            "exploration:activity-attribution-02",
            "exploration:activity-compression-03",
        ),
    )
    request = InvestigationRequest(
        question=question,
        catalog=catalog,
        sample_keys=keys,
        current_time=max(item.available_at for item in catalog.observations),
        budget=DevelopmentBudget(2, 40, 200, "mse", 0.003),
        random_seed=43,
    )
    manifest = AuthoredCandidateManifest(
        question_id=question.question_id,
        environment_id=catalog.environment_id,
        predictor_fields=(probability,),
        outcome_field=probability,
        horizon=TemporalOffset.elapsed(timedelta(hours=6)),
        minimum_outcome_points=1,
        population_dimensions=(),
        feature_names=FEATURE_NAMES,
        missing_value_policy="exclude_example",
        evidence_refs=question.evidence_refs,
        provenance_refs=(ref.uri, "researcher:chronos-authored-program"),
        population_dimension_names=tuple(
            sorted(price_dataset.schema.resolve("market_probability").dimensions)
        ),
    )
    publisher = CandidatePublisher()
    evaluator = AuthoredDevelopmentEvaluator(candidates=publisher.registry)
    baseline = publisher.publish(
        request,
        AuthoredProgramProposal(
            BASELINE_SOURCE,
            manifest,
            "Event-equal expanding historical-mean magnitude baseline.",
            (),
        ),
        expected_parent_trial_id=None,
    )
    baseline_evidence = evaluator.evaluate(request, baseline)
    ridge = publisher.publish(
        request,
        AuthoredProgramProposal(
            RIDGE_SOURCE,
            manifest,
            "Fixed-penalty event-equal ridge over the selected legal six-feature activity set.",
            (baseline_evidence.trial_id,),
        ),
        expected_parent_trial_id=baseline_evidence.trial_id,
    )
    ridge_evidence = evaluator.evaluate(request, ridge)
    if baseline_evidence.row_keys != ridge_evidence.row_keys:
        raise ValueError("formal baseline and candidate evaluated different rows")
    baseline_by_event: dict[str, list[float]] = {}
    ridge_by_event: dict[str, list[float]] = {}
    for key, baseline_prediction, ridge_prediction, outcome in zip(
        ridge_evidence.row_keys,
        baseline_evidence.predictions,
        ridge_evidence.predictions,
        ridge_evidence.outcomes,
        strict=True,
    ):
        event_id = dict(key.dimensions)["event_id"]
        baseline_by_event.setdefault(event_id, []).append((baseline_prediction - outcome) ** 2)
        ridge_by_event.setdefault(event_id, []).append((ridge_prediction - outcome) ** 2)
    event_wins = sum(
        sum(ridge_by_event[event]) / len(ridge_by_event[event])
        < sum(baseline_by_event[event]) / len(baseline_by_event[event])
        for event in ridge_by_event
    )
    baseline_metrics = dict(baseline_evidence.metrics)
    ridge_metrics = dict(ridge_evidence.metrics)
    payload = {
        "status": "succeeded",
        "epistemic_status": "FORMAL_DEVELOPMENT",
        "snapshot_ref": ref.uri,
        "partition_id": analysis.partition.partition_id,
        "development_event_count": len(development_events),
        "development_market_count": len(development_markets),
        "protected_event_count": analysis.partition.protected_event_count,
        "protected_market_count": analysis.partition.protected_market_count,
        "protected_values_exposed": False,
        "development_catalog_observation_count": len(catalog.observations),
        "sample_key_count": len(keys),
        "sample_selection": "first, middle, and last legal six-hour decision per development market",
        "population_dimension_names": list(manifest.population_dimension_names),
        "feature_names": list(FEATURE_NAMES),
        "label": "absolute probability move over next elapsed six hours",
        "ridge_penalty": RIDGE_PENALTY,
        "training_weights": "equal total weight per observed event in every expanding fit",
        "baseline": {
            "candidate_id": baseline.candidate_id,
            "source_sha256": baseline.source_sha256,
            "trial_id": baseline_evidence.trial_id,
            "evidence_id": baseline_evidence.evidence_id,
            "metrics": baseline_metrics,
            "oof_prediction_count": len(baseline_evidence.predictions),
            **_event_metrics(baseline_evidence),
        },
        "activity_ridge": {
            "candidate_id": ridge.candidate_id,
            "source_sha256": ridge.source_sha256,
            "trial_id": ridge_evidence.trial_id,
            "evidence_id": ridge_evidence.evidence_id,
            "parent_trial_ids": list(ridge.parent_trial_ids),
            "metrics": ridge_metrics,
            "oof_prediction_count": len(ridge_evidence.predictions),
            "event_mse_wins_vs_baseline": event_wins,
            **_event_metrics(ridge_evidence),
        },
        "mse_delta_vs_baseline": ridge_metrics["mse"] - baseline_metrics["mse"],
        "actual_program_accesses": {
            "features": sorted(
                {(item.interface, item.field_id) for item in ridge_evidence.feature_accesses}
            ),
            "labels": sorted(
                {(item.interface, item.field_id) for item in ridge_evidence.label_accesses}
            ),
            "fit": sorted(
                {(item.interface, item.field_id) for item in ridge_evidence.fit_accesses}
            ),
            "prediction": sorted(
                {(item.interface, item.field_id) for item in ridge_evidence.prediction_accesses}
            ),
        },
        "protected_backtest_run": False,
        "warnings": [
            "This is selection-exposed formal development evidence, not protected validation.",
            "The formal harness uses decision-time expanding replay; it does not duplicate the exploratory whole-event folds.",
            "Current close time was excluded because the retained source has no historical close-time revision clock.",
            "Absolute-move prediction is not directional or executable trading evidence.",
            "The final seven event groups and 45 markets remained outside the formal catalog.",
        ],
    }
    content = json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n"
    if RECEIPT.exists() and RECEIPT.read_text() != content:
        raise ValueError("formal panel receipt path already contains different bytes")
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(content)
    print(
        json.dumps(
            {
                "status": "SUCCEEDED",
                "receipt": str(RECEIPT),
                "receipt_sha256": hashlib.sha256(content.encode()).hexdigest(),
                "mse_delta_vs_baseline": payload["mse_delta_vs_baseline"],
                "event_wins": event_wins,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
