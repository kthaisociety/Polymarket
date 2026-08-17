"""Formalize one earliest-per-market reversal sample under exact label maturity."""

# ruff: noqa: ANN001, ANN202, C901, D103, E501, EM101, INP001, PLR0912, PLR2004, T201, TRY003

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from pathlib import Path

from research_agent.data_adapters.polymarket import (
    PolymarketCorpus,
    PolymarketCorpusRequest,
    PolymarketCorpusSnapshotRef,
    PolymarketCorpusStore,
    build_polymarket_replication_analysis,
    register_polymarket_resolution_corpus,
)
from research_agent.data_foundation import SampleKey, TemporalOffset
from research_agent.investigation import (
    AuthoredCandidateManifest,
    AuthoredDevelopmentEvaluator,
    AuthoredDevelopmentEvidence,
    AuthoredProgramProposal,
    CandidatePublisher,
    DevelopmentBudget,
    InvestigationRequest,
    ProgramLimits,
    ResearchQuestion,
    ScientificProgramHarness,
)

SNAPSHOT_SHA256 = "8c73260377ea5cb3e569bbc3c744ce9b62a95c8f54dafb73d07671845ccec4c6"
SNAPSHOT_SIZE = 318_684_407
ANCESTOR_SHA256 = "610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f"
ANCESTOR_SIZE = 19_434_443
WORKSPACE = Path(__file__).resolve().parents[5] / "data/chronos/polymarket-corpora"
RECEIPT = Path(__file__).parents[1] / "formal-receipts/02_formal_time_legal_reversal.json"
FEATURE_NAMES = (
    "delayed_entry_probability",
    "boundary_distance",
    "winsorized_logit_level_005",
    "shock_sign",
    "absolute_shock_size",
    "shock_signed_entry_slippage",
)

FEATURE_LABEL_SOURCE = """
def make_features():
    observations = history("market_probability")
    recent = observations[-26:]
    entry = recent[-1]["value"]
    shock = recent[-2]["value"]
    prior = recent[-3]["value"]
    signed_shock = shock - prior
    shock_sign = 1.0
    if signed_shock < 0.0:
        shock_sign = -1.0
    clipped = min(0.995, max(0.005, entry))
    return {
        "delayed_entry_probability": entry,
        "boundary_distance": min(entry, 1.0 - entry),
        "winsorized_logit_level_005": log(clipped / (1.0 - clipped)),
        "shock_sign": shock_sign,
        "absolute_shock_size": abs(signed_shock),
        "shock_signed_entry_slippage": shock_sign * (entry - shock),
    }

def make_label():
    observations = history("market_probability")
    entry = observations[-1]["value"]
    shock = observations[-2]["value"]
    prior = observations[-3]["value"]
    shock_sign = 1.0
    if shock - prior < 0.0:
        shock_sign = -1.0
    for observation in outcome_path():
        oriented = shock_sign * (observation["value"] - entry)
        if oriented <= -0.02:
            return 1.0
        if oriented >= 0.02:
            return 0.0
    return 0.0
"""

BASELINE_SOURCE = (
    FEATURE_LABEL_SOURCE
    + """
def dimension_value(row, name):
    for pair in row["dimensions"]:
        if pair[0] == name:
            return pair[1]
    return ""

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
    return {"rate": min(0.999, max(0.001, total / len(event_counts)))}

def predict():
    return model_state()["rate"]
"""
)

LOGISTIC_SOURCE = (
    FEATURE_LABEL_SOURCE
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
    names = [
        "delayed_entry_probability",
        "boundary_distance",
        "winsorized_logit_level_005",
        "shock_sign",
        "absolute_shock_size",
        "shock_signed_entry_slippage",
    ]
    rows = training_rows()
    event_counts = {}
    for row in rows:
        event = dimension_value(row, "event_id")
        if event not in event_counts:
            event_counts[event] = 0
        event_counts[event] = event_counts[event] + 1
    event_total = len(event_counts)
    means = [0.0 for unused in names]
    seconds = [0.0 for unused in names]
    target_mean = 0.0
    for row in rows:
        event = dimension_value(row, "event_id")
        weight = 1.0 / (event_total * event_counts[event])
        target_mean = target_mean + weight * row["label"]
        for position in range(len(names)):
            value = row["features"][names[position]]
            means[position] = means[position] + weight * value
            seconds[position] = seconds[position] + weight * value * value
    scales = []
    for position in range(len(names)):
        variance = seconds[position] - means[position] * means[position]
        scales = scales + [max(0.000000000001, variance) ** 0.5]
    prior = min(0.999, max(0.001, target_mean))
    parameters = [log(prior / (1.0 - prior))] + [0.0 for unused in names]
    size = len(parameters)
    for iteration in range(4):
        gradient = [0.0 for unused in parameters]
        hessian = [[0.0 for unused in parameters] for unused in parameters]
        for row in rows:
            event = dimension_value(row, "event_id")
            weight = 1.0 / (event_total * event_counts[event])
            design = [1.0]
            for position in range(len(names)):
                design = design + [
                    (row["features"][names[position]] - means[position]) / scales[position]
                ]
            linear = 0.0
            for position in range(size):
                linear = linear + parameters[position] * design[position]
            prediction = sigmoid(linear)
            curvature = max(0.000001, prediction * (1.0 - prediction))
            for left in range(size):
                gradient[left] = gradient[left] + weight * design[left] * (row["label"] - prediction)
                for right in range(size):
                    hessian[left][right] = hessian[left][right] + weight * curvature * design[left] * design[right]
        hessian[0][0] = hessian[0][0] + 0.000001
        for position in range(1, size):
            gradient[position] = gradient[position] - 0.1 * parameters[position]
            hessian[position][position] = hessian[position][position] + 0.1
        update = solve_linear(hessian, gradient)
        for position in range(size):
            parameters[position] = parameters[position] + update[position]
    return {"means": means, "scales": scales, "parameters": parameters}

def predict():
    names = [
        "delayed_entry_probability",
        "boundary_distance",
        "winsorized_logit_level_005",
        "shock_sign",
        "absolute_shock_size",
        "shock_signed_entry_slippage",
    ]
    state = model_state()
    values = feature_values()
    linear = state["parameters"][0]
    for position in range(len(names)):
        standardized = (values[names[position]] - state["means"][position]) / state["scales"][position]
        linear = linear + state["parameters"][position + 1] * standardized
    return sigmoid(linear)
"""
)


def _select_windows(snapshot, development_events: frozenset[str]):
    contract_by_market = {
        item.market_id: item
        for item in snapshot.corpus.contracts
        if item.event_id in development_events
    }
    by_market = {market_id: [] for market_id in contract_by_market}
    for point in snapshot.corpus.prices:
        if point.market_id in by_market:
            by_market[point.market_id].append(point)
    selected = {}
    exclusions = {
        "shock_gap": 0,
        "history_span": 0,
        "entry_gap": 0,
        "entry_boundary": 0,
        "future_coverage": 0,
        "no_eligible_shock": 0,
    }
    for market_id in sorted(by_market):
        prices = by_market[market_id]
        decision = 24
        while decision < len(prices) - 2 and market_id not in selected:
            shock = prices[decision]
            prior = prices[decision - 1]
            signed_shock = float(shock.price - prior.price)
            if abs(signed_shock) >= 0.02:
                shock_gap = (shock.observed_at - prior.observed_at).total_seconds() / 3600.0
                history_span = (
                    shock.observed_at - prices[decision - 24].observed_at
                ).total_seconds() / 3600.0
                entry = prices[decision + 1]
                entry_gap = (entry.observed_at - shock.observed_at).total_seconds() / 3600.0
                target = entry.observed_at + timedelta(hours=21)
                boundary = decision + 2
                while boundary < len(prices) and prices[boundary].observed_at < target:
                    boundary += 1
                if not 0.5 <= shock_gap <= 3.0:
                    exclusions["shock_gap"] += 1
                elif not 18.0 <= history_span <= 30.0:
                    exclusions["history_span"] += 1
                elif not 0.5 <= entry_gap <= 3.0:
                    exclusions["entry_gap"] += 1
                elif not 0.05 <= float(entry.price) <= 0.95:
                    exclusions["entry_boundary"] += 1
                elif boundary >= len(prices):
                    exclusions["future_coverage"] += 1
                else:
                    coverage_hours = (
                        prices[boundary].observed_at - entry.observed_at
                    ).total_seconds() / 3600.0
                    final_ordinal = boundary
                    if prices[boundary].observed_at > target:
                        final_ordinal = boundary - 1
                    final_hours = (
                        prices[final_ordinal].observed_at - entry.observed_at
                    ).total_seconds() / 3600.0
                    if coverage_hours > 27.0 or final_ordinal <= decision + 1 or final_hours < 15.0:
                        exclusions["future_coverage"] += 1
                    else:
                        selected[market_id] = {
                            "decision_time": entry.observed_at,
                            "points": tuple(prices[decision - 24 : boundary + 1]),
                        }
            decision += 1
        if market_id not in selected:
            exclusions["no_eligible_shock"] += 1
    return selected, exclusions


def _formal_catalog(snapshot, selected):
    selected_ids = frozenset(selected)
    contracts = tuple(item for item in snapshot.corpus.contracts if item.market_id in selected_ids)
    resolution_by_market = {item.market_id: item for item in snapshot.corpus.resolutions}
    resolutions = tuple(resolution_by_market[item.market_id] for item in contracts)
    prices = tuple(
        point for contract in contracts for point in selected[contract.market_id]["points"]
    )
    request = snapshot.corpus.request
    sliced_request = PolymarketCorpusRequest(
        environment_id=request.environment_id,
        as_of=request.as_of,
        min_points=request.min_points,
        max_markets=len(contracts),
        outcome_index=request.outcome_index,
        fidelity=request.fidelity,
    )
    sliced = PolymarketCorpus(sliced_request, contracts, resolutions, prices)
    derived_snapshot = PolymarketCorpusStore.from_corpus(sliced)
    registration = register_polymarket_resolution_corpus(derived_snapshot)
    probability_dataset = registration.price_dataset
    observation_by_key = {
        (dict(item.dimensions)["market_id"], item.reference_time): item
        for item in probability_dataset.observations
    }
    keys = tuple(
        SampleKey(
            selected[market_id]["decision_time"],
            observation_by_key[(market_id, selected[market_id]["decision_time"])].dimensions,
        )
        for market_id in sorted(selected)
    )
    return registration.catalog, probability_dataset, derived_snapshot.ref, keys


def _average_precision(predictions, outcomes):
    positives = sum(outcomes)
    if positives <= 0.0:
        return None
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


def _metrics(
    evidence: AuthoredDevelopmentEvidence,
    event_order: dict[str, int],
    comparator: AuthoredDevelopmentEvidence | None = None,
):
    if comparator is not None and evidence.row_keys != comparator.row_keys:
        raise ValueError("formal comparator evaluated different rows")
    comparator_predictions = (
        comparator.predictions if comparator is not None else evidence.predictions
    )
    by_event = {}
    for key, prediction, outcome, comparator_prediction in zip(
        evidence.row_keys,
        evidence.predictions,
        evidence.outcomes,
        comparator_predictions,
        strict=True,
    ):
        event = dict(key.dimensions)["event_id"]
        by_event.setdefault(event, []).append((prediction, outcome, comparator_prediction))
    event_rows = []
    for event in sorted(by_event, key=lambda value: event_order[value]):
        rows = by_event[event]
        brier = sum((prediction - outcome) ** 2 for prediction, outcome, _ in rows) / len(rows)
        comparator_brier = sum(
            (prediction - outcome) ** 2 for _, outcome, prediction in rows
        ) / len(rows)
        event_rows.append(
            {
                "event_id": event,
                "event_ordinal": event_order[event],
                "row_count": len(rows),
                "positive_count": sum(outcome for _, outcome, _ in rows),
                "brier": brier,
                "comparator_brier": comparator_brier,
                "average_precision": _average_precision(
                    tuple(prediction for prediction, _, _ in rows),
                    tuple(outcome for _, outcome, _ in rows),
                ),
            }
        )
    midpoint = len(event_rows) // 2
    early = event_rows[:midpoint]
    late = event_rows[midpoint:]
    event_aps = [
        row["average_precision"] for row in event_rows if row["average_precision"] is not None
    ]
    ranked = sorted(evidence.predictions, reverse=True)
    cutoff = ranked[max(1, len(ranked) // 5) - 1]
    top_outcomes = [
        outcome
        for prediction, outcome in zip(evidence.predictions, evidence.outcomes, strict=True)
        if prediction >= cutoff
    ]
    incidence = sum(evidence.outcomes) / len(evidence.outcomes)
    largest_event_share = max(row["row_count"] for row in event_rows) / len(evidence.outcomes)
    return {
        "prediction_count": len(evidence.predictions),
        "market_count": len({dict(key.dimensions)["market_id"] for key in evidence.row_keys}),
        "event_count": len(event_rows),
        "positive_count": sum(evidence.outcomes),
        "negative_count": len(evidence.outcomes) - sum(evidence.outcomes),
        "observation_brier": sum(
            (prediction - outcome) ** 2
            for prediction, outcome in zip(evidence.predictions, evidence.outcomes, strict=True)
        )
        / len(evidence.outcomes),
        "event_macro_brier": sum(row["brier"] for row in event_rows) / len(event_rows),
        "early_event_macro_brier": sum(row["brier"] for row in early) / len(early),
        "late_event_macro_brier": sum(row["brier"] for row in late) / len(late),
        "pooled_average_precision": _average_precision(evidence.predictions, evidence.outcomes),
        "event_macro_average_precision": sum(event_aps) / len(event_aps),
        "event_average_precision_count": len(event_aps),
        "event_wins_vs_comparator": sum(
            row["brier"] < row["comparator_brier"] for row in event_rows
        ),
        "incidence": incidence,
        "mean_prediction": sum(evidence.predictions) / len(evidence.predictions),
        "top_quintile_count": len(top_outcomes),
        "top_quintile_precision": sum(top_outcomes) / len(top_outcomes),
        "top_quintile_lift": sum(top_outcomes) / len(top_outcomes) - incidence,
        "largest_event_row_share": largest_event_share,
        "event_rows": event_rows,
    }


def main() -> None:
    ref = PolymarketCorpusSnapshotRef(SNAPSHOT_SHA256, SNAPSHOT_SIZE)
    ancestor_ref = PolymarketCorpusSnapshotRef(ANCESTOR_SHA256, ANCESTOR_SIZE)
    store = PolymarketCorpusStore(WORKSPACE)
    snapshot = store.load(ref)
    ancestor = store.load(ancestor_ref)
    analysis = build_polymarket_replication_analysis(
        snapshot,
        ancestor,
        session_id="formal-time-legal-reversal-2026-08-17",
    )
    development_events = frozenset(analysis.partition.development_event_ids)
    selected, exclusions = _select_windows(snapshot, development_events)
    catalog, price_dataset, derived_ref, keys = _formal_catalog(snapshot, selected)
    if any(
        dict(item.dimensions)["event_id"] not in development_events for item in catalog.observations
    ):
        raise ValueError("ancestor or protected event entered formal catalog")
    probability = price_dataset.schema.field_ref("market_probability")
    question = ResearchQuestion(
        "question:polymarket-time-legal-fixed-horizon-reversal",
        "Does internal state at one delayed post-shock decision predict two-cent reversal before continuation during the next 21 elapsed hours across contracts?",
        catalog.environment_id,
        "task:polymarket-fresh-fixed-horizon-properties",
        (
            "sha256:e777f93b48c87604d845dfd08160036449b2accdd13277a0acf55d243d658c77",
            "sha256:7fab2899d9f29c6b559f1dd1bfe3754c324243a6f38b1453659abd2e387aeeb2",
            "work-packet:polymarket-fresh-fixed-horizon-properties",
        ),
    )
    request = InvestigationRequest(
        question=question,
        catalog=catalog,
        sample_keys=keys,
        current_time=max(item.available_at for item in catalog.observations),
        budget=DevelopmentBudget(2, 100, 200, "mse", 0.245),
        random_seed=43,
    )
    manifest = AuthoredCandidateManifest(
        question_id=question.question_id,
        environment_id=catalog.environment_id,
        predictor_fields=(probability,),
        outcome_field=probability,
        horizon=TemporalOffset.elapsed(timedelta(hours=21)),
        minimum_outcome_points=1,
        population_dimensions=(),
        feature_names=FEATURE_NAMES,
        missing_value_policy="fail_trial",
        evidence_refs=question.evidence_refs,
        provenance_refs=(
            ref.uri,
            ancestor_ref.uri,
            derived_ref.uri,
            "researcher:chronos-authored-program",
        ),
        population_dimension_names=tuple(
            sorted(price_dataset.schema.resolve("market_probability").dimensions)
        ),
    )
    publisher = CandidatePublisher()
    programs = ScientificProgramHarness(
        ProgramLimits(wall_time_seconds=10.0, max_memory_bytes=1_000_000_000)
    )
    evaluator = AuthoredDevelopmentEvaluator(candidates=publisher.registry, programs=programs)
    baseline = publisher.publish(
        request,
        AuthoredProgramProposal(
            BASELINE_SOURCE,
            manifest,
            "Exact event-equal matured-label reversal-rate baseline.",
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
            "Fixed six-feature event-equal ridge-logistic candidate under exact label maturity.",
            (baseline_evidence.trial_id,),
        ),
        expected_parent_trial_id=baseline_evidence.trial_id,
    )
    candidate_evidence = evaluator.evaluate(request, candidate)
    event_order = {
        event_id: ordinal
        for ordinal, event_id in enumerate(analysis.partition.development_event_ids)
    }
    baseline_metrics = _metrics(baseline_evidence, event_order)
    candidate_metrics = _metrics(candidate_evidence, event_order, baseline_evidence)
    formal_gate_passed = (
        candidate_metrics["prediction_count"] >= 200
        and candidate_metrics["market_count"] >= 100
        and candidate_metrics["event_count"] >= 30
        and candidate_metrics["positive_count"] >= 75
        and candidate_metrics["negative_count"] >= 75
        and candidate_metrics["observation_brier"] <= 0.245
        and candidate_metrics["observation_brier"] < baseline_metrics["observation_brier"]
        and candidate_metrics["event_macro_brier"] < baseline_metrics["event_macro_brier"]
        and candidate_metrics["early_event_macro_brier"]
        < baseline_metrics["early_event_macro_brier"]
        and candidate_metrics["late_event_macro_brier"] < baseline_metrics["late_event_macro_brier"]
        and candidate_metrics["pooled_average_precision"]
        > baseline_metrics["pooled_average_precision"]
        and candidate_metrics["event_macro_average_precision"]
        > baseline_metrics["event_macro_average_precision"]
        and candidate_metrics["event_wins_vs_comparator"] * 5
        >= candidate_metrics["event_count"] * 3
        and abs(candidate_metrics["mean_prediction"] - candidate_metrics["incidence"]) <= 0.10
        and candidate_metrics["top_quintile_lift"] >= 0.08
        and candidate_metrics["largest_event_row_share"] <= 0.20
    )
    if (
        abs(candidate_metrics["observation_brier"] - dict(candidate_evidence.metrics)["mse"])
        > 1e-12
    ):
        raise ValueError("formal metric reconstruction disagrees with kernel evidence")
    payload = {
        "status": "succeeded",
        "epistemic_status": "FORMAL_DEVELOPMENT",
        "snapshot_ref": ref.uri,
        "ancestor_snapshot_ref": ancestor_ref.uri,
        "derived_formal_catalog_ref": derived_ref.uri,
        "partition_id": analysis.partition.partition_id,
        "partition_method": analysis.partition.partition_method,
        "development_event_count": len(development_events),
        "development_market_count": analysis.partition.development_market_count,
        "embargoed_event_count": analysis.partition.embargoed_event_count,
        "protected_event_count": analysis.partition.protected_event_count,
        "protected_values_exposed": False,
        "selected_market_count": len(selected),
        "declared_sample_key_count": len(keys),
        "sample_selection": "earliest eligible fixed-horizon shock per market",
        "selection_exclusions": exclusions,
        "label": "two-cent reversal before continuation in 21 elapsed hours from delayed entry",
        "feature_names": list(FEATURE_NAMES),
        "fit_recipe": "event-equal fold-local standardization, L2 0.1, four Newton updates",
        "maturity_rule": "training labels admitted only when label_matured_at <= validation decision_time",
        "baseline": {
            "candidate_id": baseline.candidate_id,
            "source_sha256": baseline.source_sha256,
            "trial_id": baseline_evidence.trial_id,
            "evidence_id": baseline_evidence.evidence_id,
            "kernel_metrics": dict(baseline_evidence.metrics),
            "metrics": baseline_metrics,
        },
        "state_shock_candidate": {
            "candidate_id": candidate.candidate_id,
            "source_sha256": candidate.source_sha256,
            "trial_id": candidate_evidence.trial_id,
            "evidence_id": candidate_evidence.evidence_id,
            "parent_trial_ids": list(candidate.parent_trial_ids),
            "kernel_metrics": dict(candidate_evidence.metrics),
            "metrics": candidate_metrics,
            "actual_program_accesses": {
                "features": sorted(
                    {
                        (item.interface, item.field_id)
                        for item in candidate_evidence.feature_accesses
                    }
                ),
                "labels": sorted(
                    {(item.interface, item.field_id) for item in candidate_evidence.label_accesses}
                ),
                "fit": sorted(
                    {(item.interface, item.field_id) for item in candidate_evidence.fit_accesses}
                ),
                "prediction": sorted(
                    {
                        (item.interface, item.field_id)
                        for item in candidate_evidence.prediction_accesses
                    }
                ),
            },
        },
        "formal_gate_passed": formal_gate_passed,
        "protected_backtest_run": False,
        "warnings": [
            "This is selection-exposed formal development evidence, not protected validation.",
            "One earliest eligible shock per market removes repeated-market observations.",
            "Chronological replay enforces exact label maturity but may use matured sibling-contract rows from the same event.",
            "Sampled probabilities are not historical executable quotes.",
            "Every ancestor event and the expanded final protected block remained outside the formal catalog.",
        ],
    }
    content = json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n"
    if RECEIPT.exists() and RECEIPT.read_text() != content:
        raise ValueError("formal receipt path already contains different bytes")
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(content)
    print(
        json.dumps(
            {
                "status": "SUCCEEDED",
                "receipt": str(RECEIPT),
                "receipt_sha256": hashlib.sha256(content.encode()).hexdigest(),
                "formal_gate_passed": formal_gate_passed,
                "candidate_id": candidate.candidate_id,
                "candidate_mse": candidate_metrics["observation_brier"],
                "baseline_mse": baseline_metrics["observation_brier"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
