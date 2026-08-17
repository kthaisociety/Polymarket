"""Replay the exact elapsed-24-hour boundary-entry model through the authored panel harness."""

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
RECEIPT = Path(__file__).parents[1] / "development-receipts/16_formal_boundary_entry_panel.json"
FEATURE_NAMES = (
    "probability_level",
    "boundary_distance",
    "winsorized_logit_level_005",
)
RIDGE_PENALTY = 0.1
NEWTON_ITERATIONS = 4

FEATURE_SOURCE = """
def state_features():
    observations = history("market_probability")
    probability = observations[-1]["value"]
    clipped = min(0.995, max(0.005, probability))
    return {
        "probability_level": probability,
        "boundary_distance": min(probability, 1.0 - probability),
        "winsorized_logit_level_005": log(clipped / (1.0 - clipped)),
    }

def make_features():
    return state_features()

def make_label():
    future = outcome_path()[-1]["value"]
    return 1.0 if future <= 0.02 or future >= 0.98 else 0.0
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

LOGISTIC_SOURCE = (
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

def sigmoid(value):
    clipped = min(30.0, max(-30.0, value))
    return 1.0 / (1.0 + exp(-clipped))

def fit():
    rows = training_rows()
    names = [
        "probability_level",
        "boundary_distance",
        "winsorized_logit_level_005",
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
    second = [0.0 for unused in names]
    for row in rows:
        event = dimension_value(row, "event_id")
        weight = 1.0 / (event_total * event_counts[event])
        target_mean = target_mean + weight * row["label"]
        for index in range(len(names)):
            value = row["features"][names[index]]
            feature_mean[index] = feature_mean[index] + weight * value
            second[index] = second[index] + weight * value * value
    scale = [0.0 for unused in names]
    for index in range(len(names)):
        variance = second[index] - feature_mean[index] * feature_mean[index]
        if variance < 0.000000000001:
            variance = 0.000000000001
        scale[index] = variance ** 0.5
    prior = min(0.999, max(0.001, target_mean))
    parameters = [0.0 for unused in range(len(names) + 1)]
    parameters[0] = log(prior / (1.0 - prior))
    for iteration in range(4):
        gradient = [0.0 for unused in parameters]
        hessian = [[0.0 for unused in parameters] for unused in parameters]
        for row in rows:
            event = dimension_value(row, "event_id")
            weight = 1.0 / (event_total * event_counts[event])
            design = [1.0]
            for index in range(len(names)):
                design = design + [(row["features"][names[index]] - feature_mean[index]) / scale[index]]
            linear = 0.0
            for index in range(len(parameters)):
                linear = linear + parameters[index] * design[index]
            prediction = sigmoid(linear)
            curvature = max(0.000001, prediction * (1.0 - prediction))
            for left in range(len(parameters)):
                gradient[left] = gradient[left] + weight * design[left] * (row["label"] - prediction)
                for right in range(len(parameters)):
                    hessian[left][right] = hessian[left][right] + weight * curvature * design[left] * design[right]
        hessian[0][0] = hessian[0][0] + 0.000001
        for index in range(1, len(parameters)):
            gradient[index] = gradient[index] - 0.1 * parameters[index]
            hessian[index][index] = hessian[index][index] + 0.1
        update = solve_linear(hessian, gradient)
        for index in range(len(parameters)):
            parameters[index] = parameters[index] + update[index]
    return {
        "feature_mean": feature_mean,
        "scale": scale,
        "parameters": parameters,
    }

def predict():
    names = [
        "probability_level",
        "boundary_distance",
        "winsorized_logit_level_005",
    ]
    state = model_state()
    values = feature_values()
    estimate = state["parameters"][0]
    for index in range(len(names)):
        estimate = estimate + state["parameters"][index + 1] * (values[names[index]] - state["feature_mean"][index]) / state["scale"][index]
    return sigmoid(estimate)
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
        last_decision_time = None
        for index in range(24, len(prices) - 1):
            decision_time = prices[index].reference_time
            if last_decision_time is not None and decision_time - last_decision_time < timedelta(
                hours=24
            ):
                continue
            trailing_hours = (
                decision_time - prices[index - 24].reference_time
            ).total_seconds() / 3600.0
            horizon_end = decision_time + timedelta(hours=24)
            future_index = index + 1
            while (
                future_index + 1 < len(prices)
                and prices[future_index + 1].reference_time <= horizon_end
            ):
                future_index += 1
            future_hours = (
                prices[future_index].reference_time - decision_time
            ).total_seconds() / 3600.0
            if not (18.0 <= trailing_hours <= 30.0 and 18.0 <= future_hours <= 24.0):
                continue
            last_decision_time = decision_time
            probability = float(prices[index].value)
            if 0.02 < probability < 0.98:
                keys.append(SampleKey(decision_time, prices[index].dimensions))
    return tuple(sorted(keys, key=lambda item: (item.decision_time, item.dimensions)))


def _average_precision(predictions: tuple[float, ...], outcomes: tuple[float, ...]) -> float:
    positives = int(sum(outcomes))
    if positives == 0:
        raise ValueError("average precision requires a positive outcome")
    ranked = sorted(zip(predictions, outcomes, strict=True), reverse=True)
    seen = 0
    seen_positive = 0.0
    precision_sum = 0.0
    position = 0
    while position < len(ranked):
        end = position
        group_positive = 0.0
        while end < len(ranked) and ranked[end][0] == ranked[position][0]:
            group_positive += ranked[end][1]
            end += 1
        seen = end
        seen_positive += group_positive
        precision_sum += group_positive * seen_positive / seen
        position = end
    return precision_sum / positives


def _rich_metrics(
    evidence: AuthoredDevelopmentEvidence,
    comparator: AuthoredDevelopmentEvidence | None = None,
) -> dict[str, float | int]:
    if comparator is not None and evidence.row_keys != comparator.row_keys:
        raise ValueError("metric comparator evaluated different formal rows")
    comparator_predictions = (
        comparator.predictions if comparator is not None else evidence.predictions
    )
    by_event: dict[str, list[tuple[float, float, float]]] = {}
    for key, prediction, outcome, comparator_prediction in zip(
        evidence.row_keys,
        evidence.predictions,
        evidence.outcomes,
        comparator_predictions,
        strict=True,
    ):
        event_id = dict(key.dimensions)["event_id"]
        by_event.setdefault(event_id, []).append((prediction, outcome, comparator_prediction))
    event_mse = []
    event_average_precision = []
    event_mean_prediction = []
    event_mean_outcome = []
    event_wins = 0
    for event in sorted(by_event):
        rows = by_event[event]
        squared = sum((prediction - outcome) ** 2 for prediction, outcome, _ in rows)
        comparator_squared = sum((prediction - outcome) ** 2 for _, outcome, prediction in rows)
        event_mse.append(squared / len(rows))
        event_mean_prediction.append(sum(row[0] for row in rows) / len(rows))
        event_mean_outcome.append(sum(row[1] for row in rows) / len(rows))
        if squared < comparator_squared:
            event_wins += 1
        event_outcomes = tuple(row[1] for row in rows)
        if sum(event_outcomes) > 0:
            event_average_precision.append(
                _average_precision(tuple(row[0] for row in rows), event_outcomes)
            )
    ranked_predictions = sorted(evidence.predictions, reverse=True)
    target_count = max(1, len(ranked_predictions) // 10)
    cutoff = ranked_predictions[target_count - 1]
    selected_outcomes = tuple(
        outcome
        for prediction, outcome in zip(evidence.predictions, evidence.outcomes, strict=True)
        if prediction >= cutoff
    )
    positives = int(sum(evidence.outcomes))
    return {
        "prediction_count": len(evidence.predictions),
        "positive_count": positives,
        "observation_brier": sum(
            (prediction - outcome) ** 2
            for prediction, outcome in zip(evidence.predictions, evidence.outcomes, strict=True)
        )
        / len(evidence.predictions),
        "event_count": len(event_mse),
        "event_macro_brier": sum(event_mse) / len(event_mse),
        "event_wins_vs_comparator": event_wins,
        "pooled_average_precision": _average_precision(evidence.predictions, evidence.outcomes),
        "event_macro_average_precision": sum(event_average_precision)
        / len(event_average_precision),
        "event_average_precision_count": len(event_average_precision),
        "observed_rate": positives / len(evidence.outcomes),
        "mean_prediction": sum(evidence.predictions) / len(evidence.predictions),
        "event_macro_observed_rate": sum(event_mean_outcome) / len(event_mean_outcome),
        "event_macro_mean_prediction": sum(event_mean_prediction) / len(event_mean_prediction),
        "top_score_cutoff": cutoff,
        "top_score_count": len(selected_outcomes),
        "top_score_positive": int(sum(selected_outcomes)),
        "top_score_precision": sum(selected_outcomes) / len(selected_outcomes),
    }


def main() -> None:
    ref = PolymarketCorpusSnapshotRef(SNAPSHOT_SHA256, SNAPSHOT_SIZE)
    snapshot = PolymarketCorpusStore(WORKSPACE).load(ref)
    analysis = build_polymarket_development_analysis(
        snapshot,
        session_id="formal-boundary-entry-panel-2026-08-17",
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
        "question:polymarket-elapsed-24h-boundary-entry-panel",
        "Does the current internal probability state predict entry into the fixed two-percent boundary region over the next exact elapsed 24 hours?",
        catalog.environment_id,
        "task:polymarket-general-feature-label-search",
        (
            "exploration:boundary-transition-coverage-10",
            "exploration:boundary-transition-models-13",
            "exploration:boundary-transition-nonoverlap-14",
            "exploration:boundary-transition-elapsed-alignment-15",
        ),
    )
    request = InvestigationRequest(
        question=question,
        catalog=catalog,
        sample_keys=keys,
        current_time=max(item.available_at for item in catalog.observations),
        budget=DevelopmentBudget(2, 40, 200, "mse", 0.04),
        random_seed=43,
    )
    manifest = AuthoredCandidateManifest(
        question_id=question.question_id,
        environment_id=catalog.environment_id,
        predictor_fields=(probability,),
        outcome_field=probability,
        horizon=TemporalOffset.elapsed(timedelta(hours=24)),
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
            "Event-equal expanding historical boundary-entry hazard baseline.",
            (),
        ),
        expected_parent_trial_id=None,
    )
    baseline_evidence = evaluator.evaluate(request, baseline)
    candidate = publisher.publish(
        request,
        AuthoredProgramProposal(
            LOGISTIC_SOURCE,
            manifest,
            "Four-update fixed-penalty event-equal ridge logistic over the exact three-feature state set.",
            (baseline_evidence.trial_id,),
        ),
        expected_parent_trial_id=baseline_evidence.trial_id,
    )
    candidate_evidence = evaluator.evaluate(request, candidate)
    if baseline_evidence.row_keys != candidate_evidence.row_keys:
        raise ValueError("formal baseline and candidate evaluated different rows")
    baseline_metrics = dict(baseline_evidence.metrics)
    candidate_metrics = dict(candidate_evidence.metrics)
    baseline_summary = _rich_metrics(baseline_evidence)
    candidate_summary = _rich_metrics(candidate_evidence, baseline_evidence)
    formal_gate_pass = (
        candidate_summary["positive_count"] >= 40
        and candidate_summary["observation_brier"] <= 0.04
        and candidate_summary["observation_brier"] < baseline_summary["observation_brier"]
        and candidate_summary["event_macro_brier"] < baseline_summary["event_macro_brier"]
        and candidate_summary["pooled_average_precision"]
        > baseline_summary["pooled_average_precision"]
        and candidate_summary["event_macro_average_precision"]
        > baseline_summary["event_macro_average_precision"]
        and candidate_summary["event_wins_vs_comparator"] > candidate_summary["event_count"] / 2
        and candidate_summary["top_score_precision"] >= 2.0 * candidate_summary["observed_rate"]
        and candidate_summary["event_macro_mean_prediction"]
        >= 0.5 * candidate_summary["event_macro_observed_rate"]
        and candidate_summary["event_macro_mean_prediction"]
        <= 2.0 * candidate_summary["event_macro_observed_rate"]
    )
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
        "sample_selection": "greedy legal decisions from ordinal 24 with at least 24 elapsed hours between grid decisions; interior-risk keys only",
        "population_dimension_names": list(manifest.population_dimension_names),
        "feature_names": list(FEATURE_NAMES),
        "label": "entry into probability <= .02 or >= .98 at the last retained observation no later than 24 elapsed hours",
        "ridge_penalty": RIDGE_PENALTY,
        "newton_iteration_count": NEWTON_ITERATIONS,
        "minimum_future_coverage_hours": 18,
        "outcome_horizon_hours": 24,
        "training_weights": "equal total weight per observed event in every expanding fit",
        "baseline": {
            "candidate_id": baseline.candidate_id,
            "source_sha256": baseline.source_sha256,
            "trial_id": baseline_evidence.trial_id,
            "evidence_id": baseline_evidence.evidence_id,
            "kernel_metrics": baseline_metrics,
            **baseline_summary,
        },
        "state_logistic": {
            "candidate_id": candidate.candidate_id,
            "source_sha256": candidate.source_sha256,
            "trial_id": candidate_evidence.trial_id,
            "evidence_id": candidate_evidence.evidence_id,
            "parent_trial_ids": list(candidate.parent_trial_ids),
            "kernel_metrics": candidate_metrics,
            **candidate_summary,
        },
        "mse_delta_vs_baseline": candidate_metrics["mse"] - baseline_metrics["mse"],
        "formal_credibility_gate_pass": formal_gate_pass,
        "actual_program_accesses": {
            "features": sorted(
                {(item.interface, item.field_id) for item in candidate_evidence.feature_accesses}
            ),
            "labels": sorted(
                {(item.interface, item.field_id) for item in candidate_evidence.label_accesses}
            ),
            "fit": sorted(
                {(item.interface, item.field_id) for item in candidate_evidence.fit_accesses}
            ),
            "prediction": sorted(
                {(item.interface, item.field_id) for item in candidate_evidence.prediction_accesses}
            ),
        },
        "protected_backtest_run": False,
        "warnings": [
            "This is selection-exposed formal development evidence, not protected validation.",
            "The exact candidate population conditions on an interior current probability using only decision-time state.",
            "Greedy grid construction consumes legal boundary and interior decisions before filtering to the entry risk set.",
            "The formal harness uses decision-time expanding replay; it does not duplicate exploratory whole-event folds.",
            "Boundary-entry probability is not direction, executable-price, or trading evidence.",
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
                "event_wins": candidate_summary["event_wins_vs_comparator"],
                "formal_credibility_gate_pass": formal_gate_pass,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
