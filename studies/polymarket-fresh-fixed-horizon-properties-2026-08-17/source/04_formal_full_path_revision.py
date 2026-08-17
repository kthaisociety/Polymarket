"""Run the one predeclared full-path revision under exact label maturity."""

# ruff: noqa: ANN202, D103, E501, EM101, INP001, PLR2004, SLF001, T201, TRY003

from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import timedelta
from pathlib import Path

from research_agent.data_adapters.polymarket import (
    PolymarketCorpusSnapshotRef,
    PolymarketCorpusStore,
    build_polymarket_replication_analysis,
)
from research_agent.data_foundation import TemporalOffset
from research_agent.investigation import (
    AuthoredCandidateManifest,
    AuthoredDevelopmentEvaluator,
    AuthoredProgramProposal,
    CandidatePublisher,
    DevelopmentBudget,
    InvestigationRequest,
    ProgramLimits,
    ResearchQuestion,
    ScientificProgramHarness,
)

PARENT_SOURCE = Path(__file__).with_name("02_formal_time_legal_reversal.py")
ORDER_SOURCE = Path(__file__).with_name("03_formal_time_legal_reversal_ordered.py")
RECEIPT = Path(__file__).parents[1] / "formal-receipts/04_formal_full_path_revision.json"
FULL_FEATURE_NAMES = (
    "delayed_entry_probability",
    "boundary_distance",
    "winsorized_logit_level_005",
    "shock_sign",
    "absolute_shock_size",
    "shock_signed_entry_slippage",
    "immediate_retracement_fraction_clipped_2",
    "reversal_direction_headroom",
    "continuation_direction_headroom",
    "pre_shock_zero_fraction_23",
    "log_one_plus_pre_shock_quiet_hours_005",
    "pre_shock_mean_absolute_step_23",
)

FULL_FEATURE_LABEL_SOURCE = """
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
    shock_size = abs(signed_shock)
    signed_slippage = shock_sign * (entry - shock)
    retracement = min(2.0, max(-2.0, -signed_slippage / shock_size))
    reversal_headroom = entry
    continuation_headroom = 1.0 - entry
    if shock_sign < 0.0:
        reversal_headroom = 1.0 - entry
        continuation_headroom = entry
    zero_count = 0.0
    absolute_step_sum = 0.0
    for index in range(1, 24):
        step = abs(recent[index]["value"] - recent[index - 1]["value"])
        absolute_step_sum = absolute_step_sum + step
        if step == 0.0:
            zero_count = zero_count + 1.0
    quiet_start = 23
    index = 23
    searching = True
    while index > 0 and searching:
        step = abs(recent[index]["value"] - recent[index - 1]["value"])
        if step >= 0.005:
            searching = False
        else:
            quiet_start = index - 1
            index = index - 1
    quiet_hours = (
        recent[23]["reference_time_epoch_seconds"]
        - recent[quiet_start]["reference_time_epoch_seconds"]
    ) / 3600.0
    clipped = min(0.995, max(0.005, entry))
    return {
        "delayed_entry_probability": entry,
        "boundary_distance": min(entry, 1.0 - entry),
        "winsorized_logit_level_005": log(clipped / (1.0 - clipped)),
        "shock_sign": shock_sign,
        "absolute_shock_size": shock_size,
        "shock_signed_entry_slippage": signed_slippage,
        "immediate_retracement_fraction_clipped_2": retracement,
        "reversal_direction_headroom": reversal_headroom,
        "continuation_direction_headroom": continuation_headroom,
        "pre_shock_zero_fraction_23": zero_count / 23.0,
        "log_one_plus_pre_shock_quiet_hours_005": log(1.0 + quiet_hours),
        "pre_shock_mean_absolute_step_23": absolute_step_sum / 23.0,
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


def _logistic_source(feature_source: str, names: tuple[str, ...]) -> str:
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

def sigmoid(value):
    clipped = min(30.0, max(-30.0, value))
    return 1.0 / (1.0 + exp(-clipped))

def fit():
    names = FEATURE_NAMES
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
    names = FEATURE_NAMES
    state = model_state()
    values = feature_values()
    linear = state["parameters"][0]
    for position in range(len(names)):
        standardized = (values[names[position]] - state["means"][position]) / state["scales"][position]
        linear = linear + state["parameters"][position + 1] * standardized
    return sigmoid(linear)
""".replace("FEATURE_NAMES", repr(list(names)))
    )


FULL_LOGISTIC_SOURCE = _logistic_source(FULL_FEATURE_LABEL_SOURCE, FULL_FEATURE_NAMES)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("could not load frozen formal dependency")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parent = _load(PARENT_SOURCE, "chronos_full_revision_parent")
    ordered = _load(ORDER_SOURCE, "chronos_full_revision_ordering")
    ref = PolymarketCorpusSnapshotRef(parent.SNAPSHOT_SHA256, parent.SNAPSHOT_SIZE)
    ancestor_ref = PolymarketCorpusSnapshotRef(parent.ANCESTOR_SHA256, parent.ANCESTOR_SIZE)
    store = PolymarketCorpusStore(parent.WORKSPACE)
    snapshot = store.load(ref)
    ancestor = store.load(ancestor_ref)
    analysis = build_polymarket_replication_analysis(
        snapshot,
        ancestor,
        session_id="formal-full-path-reversal-2026-08-17",
    )
    development_events = frozenset(analysis.partition.development_event_ids)
    selected, exclusions = parent._select_windows(snapshot, development_events)
    catalog, price_dataset, derived_ref, keys = ordered._formal_catalog(snapshot, selected)
    if any(
        dict(item.dimensions)["event_id"] not in development_events for item in catalog.observations
    ):
        raise ValueError("ancestor or protected event entered full revision catalog")
    probability = price_dataset.schema.field_ref("market_probability")
    question = ResearchQuestion(
        "question:polymarket-time-legal-fixed-horizon-reversal",
        "Does internal state at one delayed post-shock decision predict two-cent reversal before continuation during the next 21 elapsed hours across contracts?",
        catalog.environment_id,
        "task:polymarket-fresh-fixed-horizon-properties",
        (
            "sha256:e777f93b48c87604d845dfd08160036449b2accdd13277a0acf55d243d658c77",
            "sha256:7fab2899d9f29c6b559f1dd1bfe3754c324243a6f38b1453659abd2e387aeeb2",
            "sha256:03a77f2c6535a4dab6c4c042365bf175516ea46229d29c78dc7233e7684e6f12",
            "work-packet:polymarket-fresh-fixed-horizon-properties",
        ),
    )
    request = InvestigationRequest(
        question=question,
        catalog=catalog,
        sample_keys=keys,
        current_time=max(item.available_at for item in catalog.observations),
        budget=DevelopmentBudget(3, 100, 200, "mse", 0.245),
        random_seed=43,
    )
    population_names = tuple(sorted(price_dataset.schema.resolve("market_probability").dimensions))

    def manifest(feature_names: tuple[str, ...]) -> AuthoredCandidateManifest:
        return AuthoredCandidateManifest(
            question_id=question.question_id,
            environment_id=catalog.environment_id,
            predictor_fields=(probability,),
            outcome_field=probability,
            horizon=TemporalOffset.elapsed(timedelta(hours=21)),
            minimum_outcome_points=1,
            population_dimensions=(),
            feature_names=feature_names,
            missing_value_policy="fail_trial",
            evidence_refs=question.evidence_refs,
            provenance_refs=(
                ref.uri,
                ancestor_ref.uri,
                derived_ref.uri,
                "researcher:chronos-authored-program",
            ),
            population_dimension_names=population_names,
        )

    publisher = CandidatePublisher()
    programs = ScientificProgramHarness(
        ProgramLimits(wall_time_seconds=10.0, max_memory_bytes=1_000_000_000)
    )
    evaluator = AuthoredDevelopmentEvaluator(candidates=publisher.registry, programs=programs)
    baseline = publisher.publish(
        request,
        AuthoredProgramProposal(
            parent.BASELINE_SOURCE,
            manifest(parent.FEATURE_NAMES),
            "Exact event-equal matured-label reversal-rate baseline.",
            (),
        ),
        expected_parent_trial_id=None,
    )
    baseline_evidence = evaluator.evaluate(request, baseline)
    state = publisher.publish(
        request,
        AuthoredProgramProposal(
            parent.LOGISTIC_SOURCE,
            manifest(parent.FEATURE_NAMES),
            "Fixed six-feature event-equal ridge-logistic comparator under exact label maturity.",
            (baseline_evidence.trial_id,),
        ),
        expected_parent_trial_id=baseline_evidence.trial_id,
    )
    state_evidence = evaluator.evaluate(request, state)
    full = publisher.publish(
        request,
        AuthoredProgramProposal(
            FULL_LOGISTIC_SOURCE,
            manifest(FULL_FEATURE_NAMES),
            "Predeclared 12-feature path-regime revision under exact label maturity.",
            (state_evidence.trial_id,),
        ),
        expected_parent_trial_id=state_evidence.trial_id,
    )
    full_evidence = evaluator.evaluate(request, full)
    if not (baseline_evidence.row_keys == state_evidence.row_keys == full_evidence.row_keys):
        raise ValueError("formal revision candidates evaluated different rows")
    event_order = {
        event_id: ordinal
        for ordinal, event_id in enumerate(analysis.partition.development_event_ids)
    }
    baseline_metrics = parent._metrics(baseline_evidence, event_order)
    state_metrics = parent._metrics(state_evidence, event_order, baseline_evidence)
    full_vs_state = parent._metrics(full_evidence, event_order, state_evidence)
    full_vs_baseline = parent._metrics(full_evidence, event_order, baseline_evidence)
    formal_gate_passed = (
        full_vs_state["prediction_count"] >= 200
        and full_vs_state["market_count"] >= 100
        and full_vs_state["event_count"] >= 30
        and full_vs_state["positive_count"] >= 75
        and full_vs_state["negative_count"] >= 75
        and full_vs_state["observation_brier"] <= 0.245
        and full_vs_state["observation_brier"] < state_metrics["observation_brier"]
        and full_vs_state["event_macro_brier"] < state_metrics["event_macro_brier"]
        and full_vs_state["early_event_macro_brier"] < state_metrics["early_event_macro_brier"]
        and full_vs_state["late_event_macro_brier"] < state_metrics["late_event_macro_brier"]
        and full_vs_baseline["observation_brier"] < baseline_metrics["observation_brier"]
        and full_vs_baseline["event_macro_brier"] < baseline_metrics["event_macro_brier"]
        and full_vs_baseline["early_event_macro_brier"]
        < baseline_metrics["early_event_macro_brier"]
        and full_vs_baseline["late_event_macro_brier"] < baseline_metrics["late_event_macro_brier"]
        and full_vs_state["pooled_average_precision"] > state_metrics["pooled_average_precision"]
        and full_vs_state["event_macro_average_precision"]
        > state_metrics["event_macro_average_precision"]
        and full_vs_state["event_wins_vs_comparator"] * 5 >= full_vs_state["event_count"] * 3
        and abs(full_vs_state["mean_prediction"] - full_vs_state["incidence"]) <= 0.10
        and full_vs_state["top_quintile_lift"] >= 0.12
        and full_vs_state["largest_event_row_share"] <= 0.20
    )
    payload = {
        "status": "succeeded",
        "epistemic_status": "FORMAL_DEVELOPMENT_REVISION",
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
        "selection_exclusions": exclusions,
        "sample_selection": "identical earliest eligible fixed-horizon shock per market",
        "label": "two-cent reversal before continuation in 21 elapsed hours from delayed entry",
        "maturity_rule": "training labels admitted only when label_matured_at <= validation decision_time",
        "baseline": {
            "candidate_id": baseline.candidate_id,
            "trial_id": baseline_evidence.trial_id,
            "evidence_id": baseline_evidence.evidence_id,
            "metrics": baseline_metrics,
        },
        "state_comparator": {
            "candidate_id": state.candidate_id,
            "trial_id": state_evidence.trial_id,
            "evidence_id": state_evidence.evidence_id,
            "metrics": state_metrics,
        },
        "full_path_revision": {
            "candidate_id": full.candidate_id,
            "source_sha256": full.source_sha256,
            "trial_id": full_evidence.trial_id,
            "evidence_id": full_evidence.evidence_id,
            "parent_trial_ids": list(full.parent_trial_ids),
            "feature_names": list(FULL_FEATURE_NAMES),
            "metrics_vs_state": full_vs_state,
            "metrics_vs_baseline": full_vs_baseline,
            "actual_program_accesses": {
                "features": sorted(
                    {(item.interface, item.field_id) for item in full_evidence.feature_accesses}
                ),
                "labels": sorted(
                    {(item.interface, item.field_id) for item in full_evidence.label_accesses}
                ),
                "fit": sorted(
                    {(item.interface, item.field_id) for item in full_evidence.fit_accesses}
                ),
                "prediction": sorted(
                    {(item.interface, item.field_id) for item in full_evidence.prediction_accesses}
                ),
            },
        },
        "formal_gate_passed": formal_gate_passed,
        "driver_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "parent_source_sha256": hashlib.sha256(PARENT_SOURCE.read_bytes()).hexdigest(),
        "ordering_source_sha256": hashlib.sha256(ORDER_SOURCE.read_bytes()).hexdigest(),
        "protected_backtest_run": False,
        "warnings": [
            "This is the final predeclared feature revision; no further subset or threshold search is authorized.",
            "All training labels satisfy exact maturity at each validation decision.",
            "The online panel may use already-matured sibling-contract rows from the same event.",
            "Sampled probabilities are not historical executable quotes.",
            "Every ancestor event and the expanded final protected block remained unavailable.",
        ],
    }
    content = json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n"
    if RECEIPT.exists() and RECEIPT.read_text() != content:
        raise ValueError("full revision receipt path already contains different bytes")
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(content)
    print(
        json.dumps(
            {
                "status": "SUCCEEDED",
                "receipt": str(RECEIPT),
                "receipt_sha256": hashlib.sha256(content.encode()).hexdigest(),
                "formal_gate_passed": formal_gate_passed,
                "candidate_id": full.candidate_id,
                "full_brier": full_vs_state["observation_brier"],
                "state_brier": state_metrics["observation_brier"],
                "baseline_brier": baseline_metrics["observation_brier"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
