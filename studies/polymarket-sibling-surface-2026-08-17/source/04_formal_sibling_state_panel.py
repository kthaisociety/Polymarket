"""Replay the selected sibling-state magnitude model through the authored panel harness."""

# ruff: noqa: D103, E501, EM101, INP001, PLR2004, T201, TRY003

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
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
    ContextHistoryDependency,
    DevelopmentBudget,
    InvestigationRequest,
    ResearchQuestion,
)

SNAPSHOT_SHA256 = "610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f"
SNAPSHOT_SIZE = 19_434_443
WORKSPACE = Path(__file__).resolve().parents[5] / "data/chronos/polymarket-corpora"
RECEIPT = (
    Path(__file__).parents[1] / "development-receipts/04_formal_sibling_state_panel.json"
)
TARGET_FEATURE_NAMES = (
    "probability",
    "boundary_distance",
    "change_6h",
    "realized_variance_6h",
    "zero_change_fraction_24h",
    "mean_absolute_change_24h",
)
SIBLING_FEATURE_NAMES = TARGET_FEATURE_NAMES + (
    "sibling_count",
    "sibling_mean",
    "sibling_maximum",
    "sibling_minimum",
    "sibling_dispersion",
    "sibling_sum",
    "target_minus_sibling_mean",
    "target_rank_among_siblings",
)
RIDGE_PENALTY = 0.1
SAMPLES_PER_MARKET = 2

TARGET_FEATURE_SOURCE = """
def target_features():
    observations = history("market_probability")
    recent = observations[-25:]
    probability = recent[-1]["value"]
    change6 = probability - recent[-7]["value"]
    rv6 = 0.0
    zero_count = 0.0
    absolute_sum = 0.0
    for index in range(1, len(recent)):
        step = recent[index]["value"] - recent[index - 1]["value"]
        absolute_step = abs(step)
        absolute_sum = absolute_sum + absolute_step
        if absolute_step == 0.0:
            zero_count = zero_count + 1.0
        if index >= len(recent) - 6:
            rv6 = rv6 + step * step
    return {
        "probability": probability,
        "boundary_distance": min(probability, 1.0 - probability),
        "change_6h": change6,
        "realized_variance_6h": rv6,
        "zero_change_fraction_24h": zero_count / 24.0,
        "mean_absolute_change_24h": absolute_sum / 24.0,
    }

def make_features():
    return target_features()

def make_label():
    current = history("market_probability")[-1]["value"]
    return abs(outcome_path()[-1]["value"] - current)
"""

SIBLING_FEATURE_SOURCE = """
def target_features():
    observations = history("market_probability")
    recent = observations[-25:]
    probability = recent[-1]["value"]
    change6 = probability - recent[-7]["value"]
    rv6 = 0.0
    zero_count = 0.0
    absolute_sum = 0.0
    for index in range(1, len(recent)):
        step = recent[index]["value"] - recent[index - 1]["value"]
        absolute_step = abs(step)
        absolute_sum = absolute_sum + absolute_step
        if absolute_step == 0.0:
            zero_count = zero_count + 1.0
        if index >= len(recent) - 6:
            rv6 = rv6 + step * step
    return {
        "probability": probability,
        "boundary_distance": min(probability, 1.0 - probability),
        "change_6h": change6,
        "realized_variance_6h": rv6,
        "zero_change_fraction_24h": zero_count / 24.0,
        "mean_absolute_change_24h": absolute_sum / 24.0,
    }

def observation_dimension(observation, name):
    for pair in observation["dimensions"]:
        if pair[0] == name:
            return pair[1]
    return ""

def make_features():
    features = target_features()
    target = history("market_probability")[-1]
    target_market = observation_dimension(target, "market_id")
    latest = {}
    for observation in context_history("market_probability"):
        market = observation_dimension(observation, "market_id")
        if market not in latest or observation["reference_time"] > latest[market]["reference_time"]:
            latest[market] = observation
    siblings = []
    for market in latest:
        if market != target_market:
            siblings = siblings + [latest[market]["value"]]
    sibling_count = len(siblings)
    sibling_sum = sum(siblings)
    sibling_mean = sibling_sum / sibling_count
    sibling_variance = 0.0
    target_rank = 0.0
    for value in siblings:
        sibling_variance = sibling_variance + (value - sibling_mean) ** 2 / sibling_count
        if value < features["probability"]:
            target_rank = target_rank + 1.0
    features["sibling_count"] = float(sibling_count)
    features["sibling_mean"] = sibling_mean
    features["sibling_maximum"] = max(siblings)
    features["sibling_minimum"] = min(siblings)
    features["sibling_dispersion"] = sibling_variance ** 0.5
    features["sibling_sum"] = sibling_sum
    features["target_minus_sibling_mean"] = features["probability"] - sibling_mean
    features["target_rank_among_siblings"] = target_rank / sibling_count
    return features

def make_label():
    current = history("market_probability")[-1]["value"]
    return abs(outcome_path()[-1]["value"] - current)
"""


def _ridge_program(feature_source: str, feature_names: tuple[str, ...]) -> str:
    names = repr(list(feature_names))
    return (
        feature_source
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
    names = """
        + names
        + """
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
    names = """
        + names
        + """
    state = model_state()
    values = feature_values()
    estimate = state["target_mean"]
    for index in range(len(names)):
        estimate = estimate + state["coefficients"][index] * (values[names[index]] - state["feature_mean"][index]) / state["scale"][index]
    return min(1.0, max(0.0, estimate))
"""
    )


TARGET_RIDGE_SOURCE = _ridge_program(TARGET_FEATURE_SOURCE, TARGET_FEATURE_NAMES)
SIBLING_RIDGE_SOURCE = _ridge_program(SIBLING_FEATURE_SOURCE, SIBLING_FEATURE_NAMES)


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
    by_event: dict[str, dict[str, list[RegisteredObservation]]] = {}
    for item in price_dataset.observations:
        dimensions = dict(item.dimensions)
        by_event.setdefault(dimensions["event_id"], {}).setdefault(
            dimensions["market_id"], []
        ).append(item)
    keys: list[SampleKey] = []
    for event_id in sorted(by_event):
        event_markets = by_event[event_id]
        if len(event_markets) < 2:
            continue
        ordered = {
            market_id: sorted(values, key=lambda item: item.reference_time)
            for market_id, values in event_markets.items()
        }
        for market_id in sorted(ordered):
            prices = ordered[market_id]
            siblings = [item for item in sorted(ordered) if item != market_id]
            legal: list[SampleKey] = []
            for index in range(24, len(prices), 6):
                decision_time = prices[index].reference_time
                outcome_end = decision_time + timedelta(hours=6)
                future = [
                    item
                    for item in prices[index + 1 :]
                    if item.reference_time <= outcome_end
                ]
                if not future:
                    continue
                target_future_hours = (
                    future[-1].reference_time - decision_time
                ).total_seconds() / 3600.0
                if target_future_hours < 4.5:
                    continue
                trailing_hours = (
                    decision_time - prices[index - 24].reference_time
                ).total_seconds() / 3600.0
                if not 18.0 <= trailing_hours <= 30.0:
                    continue
                then_time = decision_time - timedelta(hours=6)
                alignment_legal = True
                for sibling in siblings:
                    sibling_now = _latest_at_or_before(ordered[sibling], decision_time)
                    sibling_then = _latest_at_or_before(ordered[sibling], then_time)
                    if sibling_now is None or sibling_then is None:
                        alignment_legal = False
                        break
                    now_staleness = (
                        decision_time - sibling_now.reference_time
                    ).total_seconds() / 3600.0
                    then_staleness = (
                        then_time - sibling_then.reference_time
                    ).total_seconds() / 3600.0
                    sibling_span = (
                        sibling_now.reference_time - sibling_then.reference_time
                    ).total_seconds() / 3600.0
                    if (
                        now_staleness > 2.0
                        or then_staleness > 2.0
                        or not 4.5 <= sibling_span <= 7.5
                    ):
                        alignment_legal = False
                        break
                if alignment_legal:
                    legal.append(SampleKey(decision_time, prices[index].dimensions))
            if not legal:
                continue
            selected_indices = sorted({0, len(legal) - 1})
            keys.extend(legal[index] for index in selected_indices[:SAMPLES_PER_MARKET])
    return tuple(sorted(keys, key=lambda item: (item.decision_time, item.dimensions)))


def _latest_at_or_before(
    observations: list[RegisteredObservation],
    boundary: datetime,
) -> RegisteredObservation | None:
    latest = None
    for item in observations:
        if item.reference_time <= boundary:
            latest = item
        else:
            break
    return latest


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


def _comparison_diagnostics(
    baseline: AuthoredDevelopmentEvidence,
    candidate: AuthoredDevelopmentEvidence,
) -> dict[str, object]:
    baseline_by_event: dict[tuple[int, str], list[float]] = {}
    candidate_by_event: dict[tuple[int, str], list[float]] = {}
    for key, baseline_prediction, candidate_prediction, outcome in zip(
        candidate.row_keys,
        baseline.predictions,
        candidate.predictions,
        candidate.outcomes,
        strict=True,
    ):
        dimensions = dict(key.dimensions)
        event = (int(dimensions["event_chronological_ordinal"]), dimensions["event_id"])
        baseline_by_event.setdefault(event, []).append((baseline_prediction - outcome) ** 2)
        candidate_by_event.setdefault(event, []).append((candidate_prediction - outcome) ** 2)
    event_rows = []
    positive_improvements = []
    for event in sorted(candidate_by_event):
        baseline_mse = sum(baseline_by_event[event]) / len(baseline_by_event[event])
        candidate_mse = sum(candidate_by_event[event]) / len(candidate_by_event[event])
        improvement = baseline_mse - candidate_mse
        if improvement > 0.0:
            positive_improvements.append(improvement)
        event_rows.append(
            {
                "event_chronological_ordinal": event[0],
                "event_id": event[1],
                "row_count": len(candidate_by_event[event]),
                "baseline_mse": baseline_mse,
                "candidate_mse": candidate_mse,
                "improvement": improvement,
            }
        )
    midpoint = len(event_rows) // 2
    early = event_rows[:midpoint]
    late = event_rows[midpoint:]
    positive_total = sum(positive_improvements)
    largest_positive_share = (
        max(positive_improvements) / positive_total if positive_total > 0.0 else 1.0
    )
    return {
        "event_rows": event_rows,
        "event_count": len(event_rows),
        "event_wins": sum(row["improvement"] > 0.0 for row in event_rows),
        "early_baseline_mse": sum(row["baseline_mse"] for row in early) / len(early),
        "early_candidate_mse": sum(row["candidate_mse"] for row in early) / len(early),
        "late_baseline_mse": sum(row["baseline_mse"] for row in late) / len(late),
        "late_candidate_mse": sum(row["candidate_mse"] for row in late) / len(late),
        "largest_positive_improvement_share": largest_positive_share,
    }


def main() -> None:
    ref = PolymarketCorpusSnapshotRef(SNAPSHOT_SHA256, SNAPSHOT_SIZE)
    snapshot = PolymarketCorpusStore(WORKSPACE).load(ref)
    analysis = build_polymarket_development_analysis(
        snapshot,
        session_id="formal-sibling-state-panel-2026-08-17",
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
        "question:polymarket-six-hour-sibling-state-panel",
        "Does legal same-event sibling probability state improve six-hour absolute-move forecasts beyond a target contract's own path?",
        catalog.environment_id,
        "task:polymarket-sibling-surface-search",
        (
            "exploration:sibling-surface-benchmark-02",
            "exploration:sibling-surface-compression-03",
            "implementation:manifest-scoped-context-history-918ff6a9",
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
    population_names = tuple(
        sorted(price_dataset.schema.resolve("market_probability").dimensions)
    )
    baseline_manifest = AuthoredCandidateManifest(
        question_id=question.question_id,
        environment_id=catalog.environment_id,
        predictor_fields=(probability,),
        outcome_field=probability,
        horizon=TemporalOffset.elapsed(timedelta(hours=6)),
        minimum_outcome_points=1,
        population_dimensions=(),
        feature_names=TARGET_FEATURE_NAMES,
        missing_value_policy="exclude_example",
        evidence_refs=question.evidence_refs,
        provenance_refs=(ref.uri, "researcher:chronos-authored-program"),
        population_dimension_names=population_names,
    )
    sibling_manifest = AuthoredCandidateManifest(
        question_id=question.question_id,
        environment_id=catalog.environment_id,
        predictor_fields=(probability,),
        outcome_field=probability,
        horizon=TemporalOffset.elapsed(timedelta(hours=6)),
        minimum_outcome_points=1,
        population_dimensions=(),
        feature_names=SIBLING_FEATURE_NAMES,
        missing_value_policy="exclude_example",
        evidence_refs=question.evidence_refs,
        provenance_refs=(ref.uri, "researcher:chronos-authored-program"),
        population_dimension_names=population_names,
        context_history_dependencies=(
            ContextHistoryDependency(probability, ("event_id",)),
        ),
    )
    publisher = CandidatePublisher()
    evaluator = AuthoredDevelopmentEvaluator(candidates=publisher.registry)
    baseline = publisher.publish(
        request,
        AuthoredProgramProposal(
            TARGET_RIDGE_SOURCE,
            baseline_manifest,
            "Fixed-penalty event-equal ridge over the six target-path features.",
            (),
        ),
        expected_parent_trial_id=None,
    )
    baseline_evidence = evaluator.evaluate(request, baseline)
    sibling = publisher.publish(
        request,
        AuthoredProgramProposal(
            SIBLING_RIDGE_SOURCE,
            sibling_manifest,
            "The exact selected 14-feature target-plus-static-sibling-state ridge recipe.",
            (baseline_evidence.trial_id,),
        ),
        expected_parent_trial_id=baseline_evidence.trial_id,
    )
    sibling_evidence = evaluator.evaluate(request, sibling)
    if baseline_evidence.row_keys != sibling_evidence.row_keys:
        raise ValueError("formal baseline and candidate evaluated different rows")
    candidate_feature_accesses = sorted(
        {(item.interface, item.field_id) for item in sibling_evidence.feature_accesses}
    )
    if ("context_history", "market_probability") not in candidate_feature_accesses:
        raise ValueError("formal sibling candidate did not use its declared context grant")
    baseline_metrics = dict(baseline_evidence.metrics)
    sibling_metrics = dict(sibling_evidence.metrics)
    comparison = _comparison_diagnostics(baseline_evidence, sibling_evidence)
    baseline_event = _event_metrics(baseline_evidence)
    sibling_event = _event_metrics(sibling_evidence)
    event_count = int(comparison["event_count"])
    event_wins = int(comparison["event_wins"])
    gate_passed = (
        sibling_metrics["mse"] <= 0.003
        and sibling_metrics["mse"] < baseline_metrics["mse"]
        and float(sibling_event["event_macro_mse"])
        < float(baseline_event["event_macro_mse"])
        and float(comparison["early_candidate_mse"])
        < float(comparison["early_baseline_mse"])
        and float(comparison["late_candidate_mse"])
        < float(comparison["late_baseline_mse"])
        and event_wins / event_count >= 0.60
        and float(comparison["largest_positive_improvement_share"]) <= 0.50
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
        "sample_selection": "first and last legal elapsed-six-hour decision per development market after target and sibling alignment gates",
        "population_dimension_names": list(population_names),
        "target_feature_names": list(TARGET_FEATURE_NAMES),
        "sibling_feature_names": list(SIBLING_FEATURE_NAMES),
        "context_history_dependencies": [
            {
                "field_id": "market_probability",
                "match_dimension_names": ["event_id"],
            }
        ],
        "label": "absolute probability move over next elapsed six hours",
        "ridge_penalty": RIDGE_PENALTY,
        "training_weights": "equal total weight per observed event in every expanding fit",
        "target_only_ridge": {
            "candidate_id": baseline.candidate_id,
            "source_sha256": baseline.source_sha256,
            "trial_id": baseline_evidence.trial_id,
            "evidence_id": baseline_evidence.evidence_id,
            "metrics": baseline_metrics,
            "oof_prediction_count": len(baseline_evidence.predictions),
            **baseline_event,
        },
        "sibling_state_ridge": {
            "candidate_id": sibling.candidate_id,
            "source_sha256": sibling.source_sha256,
            "trial_id": sibling_evidence.trial_id,
            "evidence_id": sibling_evidence.evidence_id,
            "parent_trial_ids": list(sibling.parent_trial_ids),
            "metrics": sibling_metrics,
            "oof_prediction_count": len(sibling_evidence.predictions),
            "event_mse_wins_vs_baseline": event_wins,
            **sibling_event,
        },
        "comparison": comparison,
        "predeclared_gate_passed": gate_passed,
        "mse_delta_vs_target_only": sibling_metrics["mse"] - baseline_metrics["mse"],
        "actual_program_accesses": {
            "features": candidate_feature_accesses,
            "labels": sorted(
                {(item.interface, item.field_id) for item in sibling_evidence.label_accesses}
            ),
            "fit": sorted(
                {(item.interface, item.field_id) for item in sibling_evidence.fit_accesses}
            ),
            "prediction": sorted(
                {(item.interface, item.field_id) for item in sibling_evidence.prediction_accesses}
            ),
        },
        "protected_backtest_run": False,
        "warnings": [
            "This is selection-exposed formal development evidence, not protected validation.",
            "The formal harness uses decision-time expanding replay; it does not duplicate the exploratory whole-event folds.",
            "Absolute-move prediction is not directional or executable trading evidence.",
            "Server event_id supplies grouping only; no exclusivity or exhaustiveness is assumed.",
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
                "mse_delta_vs_target_only": payload["mse_delta_vs_target_only"],
                "event_wins": event_wins,
                "predeclared_gate_passed": gate_passed,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
