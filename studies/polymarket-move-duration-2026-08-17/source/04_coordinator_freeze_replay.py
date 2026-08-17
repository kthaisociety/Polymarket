"""Replay and independently freeze the exact credible sampled-duration candidate."""

# ruff: noqa: C901, D103, E501, EM101, INP001, PLR0915, PLR2004, T201, TRY003

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
    AuthoredDevelopmentEvidence,
    AuthoredFreezeService,
    AuthoredProgramProposal,
    DevelopmentBudget,
    InvestigationRequest,
    ProtectedEvaluationPredeclaration,
    ResearchQuestion,
    RuntimeInvestigationCoordinator,
)
from research_agent.protected_evaluation import (
    FreezeEligibilityRegistry,
    FreezeGate,
    FrozenSystemRegistry,
    ResearchLedger,
)

SNAPSHOT_SHA256 = "610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f"
SNAPSHOT_SIZE = 19_434_443
WORKSPACE = Path(__file__).resolve().parents[5] / "data/chronos/polymarket-corpora"
RECEIPT = Path(__file__).parents[1] / "development-receipts/04_coordinator_freeze_replay.json"
EXPECTED_CANDIDATE_ID = (
    "authored-candidate:bb76fb6846cd5bb935934e16d53c520865f5649d230c53b0cc1ca5c3e1be770d"
)
EXPECTED_EVIDENCE_ID = (
    "authored-development-evidence:7729af09c56fed64323cc805df708ab2643ec547aa90877dda30e53a6e9c5372"
)
STATE_FEATURE_NAMES = (
    "probability_level",
    "boundary_distance",
    "winsorized_logit_level_005",
)
STALENESS_FEATURE_NAMES = (
    *STATE_FEATURE_NAMES,
    "zero_change_fraction_24h",
    "log_one_plus_quiet_run_hours_005",
)
RIDGE_PENALTY = 0.1

STATE_FEATURE_SOURCE = """
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
    current = history("market_probability")[-1]
    current_value = current["value"]
    current_time = current["reference_time_epoch_seconds"]
    for observation in outcome_path():
        if abs(observation["value"] - current_value) >= 0.02:
            elapsed = (observation["reference_time_epoch_seconds"] - current_time) / 172800.0
            return min(1.0, max(0.0, elapsed))
    return 1.0
"""

STALENESS_FEATURE_SOURCE = """
def make_features():
    observations = history("market_probability")
    recent = observations[-25:]
    probability = recent[-1]["value"]
    clipped = min(0.995, max(0.005, probability))
    zero_count = 0.0
    for index in range(1, len(recent)):
        if recent[index]["value"] == recent[index - 1]["value"]:
            zero_count = zero_count + 1.0
    quiet_start = len(recent) - 1
    index = len(recent) - 1
    while index > 0:
        step = abs(recent[index]["value"] - recent[index - 1]["value"])
        if step >= 0.005:
            index = 0
        else:
            quiet_start = index - 1
            index = index - 1
    quiet_hours = (
        recent[-1]["reference_time_epoch_seconds"]
        - recent[quiet_start]["reference_time_epoch_seconds"]
    ) / 3600.0
    return {
        "probability_level": probability,
        "boundary_distance": min(probability, 1.0 - probability),
        "winsorized_logit_level_005": log(clipped / (1.0 - clipped)),
        "zero_change_fraction_24h": zero_count / 24.0,
        "log_one_plus_quiet_run_hours_005": log(1.0 + quiet_hours),
    }

def make_label():
    current = history("market_probability")[-1]
    current_value = current["value"]
    current_time = current["reference_time_epoch_seconds"]
    for observation in outcome_path():
        if abs(observation["value"] - current_value) >= 0.02:
            elapsed = (observation["reference_time_epoch_seconds"] - current_time) / 172800.0
            return min(1.0, max(0.0, elapsed))
    return 1.0
"""


def _event_mean_program(feature_source: str) -> str:
    return (
        feature_source
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
    return {"mean": total / len(event_counts)}

def predict():
    return model_state()["mean"]
"""
    )


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
    names = FEATURE_NAMES
    rows = training_rows()
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
    matrix = [[0.0 for unused in names] for unused in names]
    vector = [0.0 for unused in names]
    for row in rows:
        event = dimension_value(row, "event_id")
        weight = 1.0 / (event_total * event_counts[event])
        standardized = []
        for index in range(len(names)):
            standardized = standardized + [
                (row["features"][names[index]] - feature_mean[index]) / scale[index]
            ]
        centered_target = row["label"] - target_mean
        for left in range(len(names)):
            vector[left] = vector[left] + weight * standardized[left] * centered_target
            for right in range(len(names)):
                matrix[left][right] = matrix[left][right] + weight * standardized[left] * standardized[right]
    for index in range(len(names)):
        matrix[index][index] = matrix[index][index] + 0.1
    return {
        "target_mean": target_mean,
        "feature_mean": feature_mean,
        "scale": scale,
        "coefficients": solve_linear(matrix, vector),
    }

def predict():
    names = FEATURE_NAMES
    state = model_state()
    values = feature_values()
    estimate = state["target_mean"]
    for index in range(len(names)):
        estimate = estimate + state["coefficients"][index] * (
            values[names[index]] - state["feature_mean"][index]
        ) / state["scale"][index]
    return min(1.0, max(0.0, estimate))
""".replace("FEATURE_NAMES", names)
    )


EVENT_MEAN_SOURCE = _event_mean_program(STATE_FEATURE_SOURCE)
STATE_RIDGE_SOURCE = _ridge_program(STATE_FEATURE_SOURCE, STATE_FEATURE_NAMES)
STALENESS_RIDGE_SOURCE = _ridge_program(STALENESS_FEATURE_SOURCE, STALENESS_FEATURE_NAMES)


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
        decision = 24
        while decision < len(prices) - 1:
            current = prices[decision]
            history_hours = (
                current.reference_time - prices[decision - 24].reference_time
            ).total_seconds() / 3600.0
            six_hour_span = (
                current.reference_time - prices[decision - 6].reference_time
            ).total_seconds() / 3600.0
            endpoint = decision + 1
            boundary = current.reference_time + timedelta(hours=48)
            while endpoint < len(prices) and prices[endpoint].reference_time < boundary:
                endpoint += 1
            endpoint_hours = None
            if endpoint < len(prices):
                endpoint_hours = (
                    prices[endpoint].reference_time - current.reference_time
                ).total_seconds() / 3600.0
            if (
                18.0 <= history_hours <= 30.0
                and 4.5 <= six_hour_span <= 7.5
                and endpoint_hours is not None
                and 42.0 <= endpoint_hours <= 54.0
            ):
                keys.append(SampleKey(current.reference_time, current.dimensions))
            decision += 1
            while decision < len(prices) and prices[decision].reference_time < boundary:
                decision += 1
    return tuple(sorted(keys, key=lambda item: (item.decision_time, item.dimensions)))


def _duration_metrics(
    evidence: AuthoredDevelopmentEvidence,
    comparator: AuthoredDevelopmentEvidence | None = None,
) -> dict[str, object]:
    if comparator is not None and evidence.row_keys != comparator.row_keys:
        raise ValueError("metric comparator evaluated different formal rows")
    comparator_predictions = (
        comparator.predictions if comparator is not None else evidence.predictions
    )
    by_event: dict[str, list[tuple[float, float, float]]] = {}
    first_decision_by_event: dict[str, datetime] = {}
    for key, prediction, outcome, comparator_prediction in zip(
        evidence.row_keys,
        evidence.predictions,
        evidence.outcomes,
        comparator_predictions,
        strict=True,
    ):
        event = dict(key.dimensions)["event_id"]
        by_event.setdefault(event, []).append((prediction, outcome, comparator_prediction))
        if (
            event not in first_decision_by_event
            or key.decision_time < first_decision_by_event[event]
        ):
            first_decision_by_event[event] = key.decision_time
    event_rows = []
    positive_improvements = []
    for event in sorted(by_event, key=lambda item: (first_decision_by_event[item], item)):
        rows = by_event[event]
        mae = sum(abs(prediction - outcome) for prediction, outcome, _ in rows) / len(rows)
        mse = sum((prediction - outcome) ** 2 for prediction, outcome, _ in rows) / len(rows)
        comparator_mae = sum(
            abs(comparator_prediction - outcome) for _, outcome, comparator_prediction in rows
        ) / len(rows)
        improvement = comparator_mae - mae
        if improvement > 0.0:
            positive_improvements.append(improvement)
        capped = sum(outcome >= 0.999999999999 for _, outcome, _ in rows)
        event_rows.append(
            {
                "event_id": event,
                "first_oof_decision_time": first_decision_by_event[event].isoformat(),
                "row_count": len(rows),
                "capped_count": capped,
                "uncapped_count": len(rows) - capped,
                "mae": mae,
                "mse": mse,
                "comparator_mae": comparator_mae,
                "mae_improvement": improvement,
            }
        )
    midpoint = len(event_rows) // 2
    early = event_rows[:midpoint]
    late = event_rows[midpoint:]
    positive_total = sum(positive_improvements)
    return {
        "prediction_count": len(evidence.predictions),
        "event_count": len(event_rows),
        "observation_mae": sum(
            abs(prediction - outcome)
            for prediction, outcome in zip(evidence.predictions, evidence.outcomes, strict=True)
        )
        / len(evidence.predictions),
        "observation_mse": sum(
            (prediction - outcome) ** 2
            for prediction, outcome in zip(evidence.predictions, evidence.outcomes, strict=True)
        )
        / len(evidence.predictions),
        "event_macro_mae": sum(row["mae"] for row in event_rows) / len(event_rows),
        "event_macro_mse": sum(row["mse"] for row in event_rows) / len(event_rows),
        "early_event_macro_mae": sum(row["mae"] for row in early) / len(early),
        "late_event_macro_mae": sum(row["mae"] for row in late) / len(late),
        "early_comparator_macro_mae": sum(row["comparator_mae"] for row in early) / len(early),
        "late_comparator_macro_mae": sum(row["comparator_mae"] for row in late) / len(late),
        "event_wins_vs_comparator": sum(row["mae_improvement"] > 0.0 for row in event_rows),
        "largest_positive_mae_improvement_share": (
            max(positive_improvements) / positive_total if positive_total > 0.0 else 1.0
        ),
        "capped_count": sum(outcome >= 0.999999999999 for outcome in evidence.outcomes),
        "uncapped_count": sum(outcome < 0.999999999999 for outcome in evidence.outcomes),
        "mixed_event_count": sum(
            row["capped_count"] > 0 and row["uncapped_count"] > 0 for row in event_rows
        ),
        "mean_prediction": sum(evidence.predictions) / len(evidence.predictions),
        "mean_outcome": sum(evidence.outcomes) / len(evidence.outcomes),
        "event_rows": event_rows,
    }


def main() -> None:
    ref = PolymarketCorpusSnapshotRef(SNAPSHOT_SHA256, SNAPSHOT_SIZE)
    snapshot = PolymarketCorpusStore(WORKSPACE).load(ref)
    analysis = build_polymarket_development_analysis(
        snapshot,
        session_id="formal-move-duration-panel-2026-08-17",
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
        "question:polymarket-sampled-first-passage-duration-panel",
        "Does decision-time sampled-price staleness improve capped 48-hour two-cent first-passage duration prediction beyond probability state?",
        catalog.environment_id,
        "task:polymarket-move-duration-search",
        (
            "exploration:duration-benchmark-01",
            "exploration:duration-mechanism-compression-02",
            "implementation:authored-numeric-temporal-payload",
        ),
    )
    request = InvestigationRequest(
        question=question,
        catalog=catalog,
        sample_keys=keys,
        current_time=max(item.available_at for item in catalog.observations),
        budget=DevelopmentBudget(3, 40, 500, "mse", 0.15),
        random_seed=43,
        protected_predeclaration=ProtectedEvaluationPredeclaration(
            data_protocol_ref="protocol:data:polymarket-corpus-610b8b9-final-seven-events-v1",
            training_protocol_ref="protocol:training:authored-expanding-event-equal-duration-v1",
            scenario_ref="scenario:polymarket-duration-protected-greedy-48h-v1",
            decision_times_ref="decision-times:polymarket-duration-protected-greedy-48h-v1",
            evaluation_spec_ref="protocol:evaluation:duration-mae-mse-event-macro-v1",
            validation_standard_ref="protocol:validation:duration-protected-improvement-v1",
            protected_scope_id="scope:polymarket-corpus-610b8b9-final-seven-events",
            claim_template_ref="claim-template:sampled-two-cent-first-passage-duration-v1",
            freeze_standard_ref="standard:freeze:formal-duration-gate-v1",
        ),
    )
    population_names = tuple(sorted(price_dataset.schema.resolve("market_probability").dimensions))

    def manifest(feature_names: tuple[str, ...]) -> AuthoredCandidateManifest:
        return AuthoredCandidateManifest(
            question_id=question.question_id,
            environment_id=catalog.environment_id,
            predictor_fields=(probability,),
            outcome_field=probability,
            horizon=TemporalOffset.elapsed(timedelta(hours=48)),
            minimum_outcome_points=1,
            population_dimensions=(),
            feature_names=feature_names,
            missing_value_policy="exclude_example",
            evidence_refs=question.evidence_refs,
            provenance_refs=(ref.uri, "researcher:chronos-authored-program"),
            population_dimension_names=population_names,
        )

    session_id = "session:chronos-polymarket-duration-freeze"
    episode_id = "episode:chronos-polymarket-duration-freeze"
    coordinator = RuntimeInvestigationCoordinator()
    registration = coordinator.register(
        request,
        session_id=session_id,
        episode_id=episode_id,
    )
    baseline_runtime = coordinator.execute(
        registration.registration_id,
        AuthoredProgramProposal(
            EVENT_MEAN_SOURCE,
            manifest(STATE_FEATURE_NAMES),
            "Event-equal expanding historical normalized-duration mean.",
            (),
        ),
        session_id=session_id,
        episode_id=episode_id,
        idempotency_key="duration-freeze:baseline",
    )
    if baseline_runtime.evidence_id is None or baseline_runtime.trial_id is None:
        raise ValueError("coordinator baseline did not issue formal evidence")
    baseline_evidence = coordinator.resolve_evidence(baseline_runtime.evidence_id)
    baseline = coordinator.resolve_candidate(baseline_runtime.candidate_id or "")
    state_runtime = coordinator.execute(
        registration.registration_id,
        AuthoredProgramProposal(
            STATE_RIDGE_SOURCE,
            manifest(STATE_FEATURE_NAMES),
            "Fixed-penalty event-equal ridge over exact probability state.",
            (baseline_runtime.trial_id,),
        ),
        session_id=session_id,
        episode_id=episode_id,
        idempotency_key="duration-freeze:state",
    )
    if state_runtime.evidence_id is None or state_runtime.trial_id is None:
        raise ValueError("coordinator state comparator did not issue formal evidence")
    state_evidence = coordinator.resolve_evidence(state_runtime.evidence_id)
    state = coordinator.resolve_candidate(state_runtime.candidate_id or "")
    staleness_runtime = coordinator.execute(
        registration.registration_id,
        AuthoredProgramProposal(
            STALENESS_RIDGE_SOURCE,
            manifest(STALENESS_FEATURE_NAMES),
            "Selected five-feature state-staleness ridge with fixed event weights and penalty.",
            (state_runtime.trial_id,),
        ),
        session_id=session_id,
        episode_id=episode_id,
        idempotency_key="duration-freeze:state-staleness",
    )
    if staleness_runtime.evidence_id is None or staleness_runtime.trial_id is None:
        raise ValueError("coordinator staleness candidate did not issue formal evidence")
    staleness_evidence = coordinator.resolve_evidence(staleness_runtime.evidence_id)
    staleness = coordinator.resolve_candidate(staleness_runtime.candidate_id or "")
    if not (baseline_evidence.row_keys == state_evidence.row_keys == staleness_evidence.row_keys):
        raise ValueError("formal duration candidates evaluated different rows")
    baseline_summary = _duration_metrics(baseline_evidence)
    state_summary = _duration_metrics(state_evidence, baseline_evidence)
    staleness_summary = _duration_metrics(staleness_evidence, state_evidence)
    if (
        abs(float(staleness_summary["observation_mse"]) - dict(staleness_evidence.metrics)["mse"])
        > 1e-12
    ):
        raise ValueError("formal duration metric reconstruction disagrees with kernel")
    formal_gate_pass = (
        int(staleness_summary["prediction_count"]) >= 500
        and int(staleness_summary["event_count"]) >= 12
        and int(staleness_summary["capped_count"]) >= 100
        and int(staleness_summary["uncapped_count"]) >= 100
        and int(staleness_summary["mixed_event_count"]) >= 10
        and float(staleness_summary["observation_mae"]) <= 0.30
        and float(staleness_summary["event_macro_mae"]) <= 0.30
        and float(staleness_summary["observation_mse"]) <= 0.15
        and float(staleness_summary["event_macro_mse"]) <= 0.15
        and float(staleness_summary["observation_mae"]) < float(baseline_summary["observation_mae"])
        and float(staleness_summary["observation_mse"]) < float(baseline_summary["observation_mse"])
        and float(staleness_summary["event_macro_mae"]) < float(baseline_summary["event_macro_mae"])
        and float(staleness_summary["event_macro_mse"]) < float(baseline_summary["event_macro_mse"])
        and float(staleness_summary["observation_mae"]) < float(state_summary["observation_mae"])
        and float(staleness_summary["observation_mse"]) < float(state_summary["observation_mse"])
        and float(staleness_summary["event_macro_mae"]) < float(state_summary["event_macro_mae"])
        and float(staleness_summary["event_macro_mse"]) < float(state_summary["event_macro_mse"])
        and float(staleness_summary["event_macro_mae"])
        <= 0.95 * float(state_summary["event_macro_mae"])
        and float(staleness_summary["early_event_macro_mae"])
        < float(staleness_summary["early_comparator_macro_mae"])
        and float(staleness_summary["late_event_macro_mae"])
        < float(staleness_summary["late_comparator_macro_mae"])
        and int(staleness_summary["event_wins_vs_comparator"]) * 5
        >= int(staleness_summary["event_count"]) * 3
        and float(staleness_summary["largest_positive_mae_improvement_share"]) <= 0.50
        and abs(
            float(staleness_summary["mean_prediction"]) - float(staleness_summary["mean_outcome"])
        )
        <= 0.10
    )
    if not formal_gate_pass:
        raise ValueError("coordinator replay did not reproduce the declared formal gate")
    if (
        staleness.candidate_id != EXPECTED_CANDIDATE_ID
        or staleness_evidence.evidence_id != EXPECTED_EVIDENCE_ID
    ):
        raise ValueError(
            "coordinator replay changed the exact formal candidate or evidence identity"
        )
    if request.protected_predeclaration is None:
        raise ValueError("freeze replay lost its protected protocol predeclaration")
    freeze_ledger = ResearchLedger()
    eligibility = FreezeEligibilityRegistry()
    frozen_systems = FrozenSystemRegistry()
    freeze_clock = max(item.available_at for item in catalog.observations) + timedelta(seconds=1)
    freeze = AuthoredFreezeService(
        authority_id="authority:independent-polymarket-duration-freeze",
        investigations=coordinator,
        eligibility=eligibility,
        gate=FreezeGate(
            ledger=freeze_ledger,
            registry=frozen_systems,
            eligibility=eligibility,
            decision_authority_id="authority:independent-polymarket-duration-freeze",
            clock=lambda: freeze_clock,
        ),
    ).assess_credible(
        candidate_id=staleness.candidate_id,
        evidence_id=staleness_evidence.evidence_id,
        requester_id=session_id,
        beneficiary_id=question.task_ref,
    )
    if freeze.frozen is None:
        raise ValueError("independent freeze authority did not seal the exact credible candidate")
    payload = {
        "status": "succeeded",
        "epistemic_status": "FROZEN_DEVELOPMENT_CANDIDATE",
        "snapshot_ref": ref.uri,
        "partition_id": analysis.partition.partition_id,
        "development_event_count": len(development_events),
        "development_market_count": len(development_markets),
        "protected_event_count": analysis.partition.protected_event_count,
        "protected_market_count": analysis.partition.protected_market_count,
        "protected_values_exposed": False,
        "development_catalog_observation_count": len(catalog.observations),
        "sample_key_count": len(keys),
        "sample_selection": "greedy decisions from ordinal 24 at least 48 elapsed hours apart; 18-30h trailing span, 4.5-7.5h six-step span, and first post-48h endpoint within 42-54h",
        "population_dimension_names": list(population_names),
        "label": "elapsed time to first sampled absolute displacement >= .02 inside exact 48h horizon, capped at 48h and normalized by 48",
        "state_feature_names": list(STATE_FEATURE_NAMES),
        "staleness_feature_names": list(STALENESS_FEATURE_NAMES),
        "ridge_penalty": RIDGE_PENALTY,
        "training_weights": "equal total weight per observed event in every expanding fit",
        "protected_predeclaration": {
            "data_protocol_ref": request.protected_predeclaration.data_protocol_ref,
            "training_protocol_ref": request.protected_predeclaration.training_protocol_ref,
            "scenario_ref": request.protected_predeclaration.scenario_ref,
            "decision_times_ref": request.protected_predeclaration.decision_times_ref,
            "evaluation_spec_ref": request.protected_predeclaration.evaluation_spec_ref,
            "validation_standard_ref": request.protected_predeclaration.validation_standard_ref,
            "protected_scope_id": request.protected_predeclaration.protected_scope_id,
            "claim_template_ref": request.protected_predeclaration.claim_template_ref,
            "freeze_standard_ref": request.protected_predeclaration.freeze_standard_ref,
        },
        "coordinator_registration_id": registration.registration_id,
        "runtime_trial_receipts": [
            {
                "receipt_id": item.receipt_id,
                "trial_ordinal": item.trial_ordinal,
                "trial_id": item.trial_id,
                "candidate_id": item.candidate_id,
                "evidence_id": item.evidence_id,
                "execution_status": item.execution_status,
                "disposition": item.disposition.value,
                "question_status": item.question_status.value,
                "primary_metric": item.primary_metric,
                "ledger_event_ids": list(item.ledger_event_ids),
            }
            for item in (baseline_runtime, state_runtime, staleness_runtime)
        ],
        "event_mean": {
            "candidate_id": baseline.candidate_id,
            "source_sha256": baseline.source_sha256,
            "trial_id": baseline_evidence.trial_id,
            "evidence_id": baseline_evidence.evidence_id,
            "kernel_metrics": dict(baseline_evidence.metrics),
            **baseline_summary,
        },
        "state_ridge": {
            "candidate_id": state.candidate_id,
            "source_sha256": state.source_sha256,
            "trial_id": state_evidence.trial_id,
            "evidence_id": state_evidence.evidence_id,
            "parent_trial_ids": list(state.parent_trial_ids),
            "kernel_metrics": dict(state_evidence.metrics),
            **state_summary,
        },
        "state_staleness_ridge": {
            "candidate_id": staleness.candidate_id,
            "source_sha256": staleness.source_sha256,
            "trial_id": staleness_evidence.trial_id,
            "evidence_id": staleness_evidence.evidence_id,
            "parent_trial_ids": list(staleness.parent_trial_ids),
            "kernel_metrics": dict(staleness_evidence.metrics),
            **staleness_summary,
        },
        "formal_credibility_gate_pass": formal_gate_pass,
        "exact_identity_match": True,
        "freeze": {
            "request_id": freeze.request.request_id,
            "decision_id": freeze.decision.decision_id,
            "decision_status": freeze.decision.status.value,
            "decision_reason_code": freeze.decision.reason_code,
            "authority_id": freeze.decision.authority_id,
            "frozen_system_id": freeze.frozen.frozen_system_id,
            "system_id": freeze.frozen.system_id,
            "candidate_version": freeze.frozen.candidate_version,
            "development_evidence_refs": list(freeze.frozen.development_evidence_refs),
            "protocol_refs": list(freeze.frozen.protocol_refs),
            "standard_ref": freeze.frozen.standard_ref,
            "frozen_at": freeze.frozen.frozen_at.isoformat(),
            "ledger_entries": [
                {
                    "entry_id": item.entry_id,
                    "event_type": item.event_type,
                    "subject_id": item.subject_id,
                    "status": item.status,
                    "authority_id": item.authority_id,
                    "references": list(item.references),
                    "reason_code": item.reason_code,
                    "occurred_at": item.occurred_at.isoformat(),
                }
                for item in freeze_ledger.entries()
            ],
        },
        "actual_program_accesses": {
            "features": sorted(
                {(item.interface, item.field_id) for item in staleness_evidence.feature_accesses}
            ),
            "labels": sorted(
                {(item.interface, item.field_id) for item in staleness_evidence.label_accesses}
            ),
            "fit": sorted(
                {(item.interface, item.field_id) for item in staleness_evidence.fit_accesses}
            ),
            "prediction": sorted(
                {(item.interface, item.field_id) for item in staleness_evidence.prediction_accesses}
            ),
        },
        "protected_backtest_run": False,
        "warnings": [
            "This is selection-exposed formal development evidence, not protected validation.",
            "Sampled first passage is not continuous-time first passage or executable-price evidence.",
            "A capped path without a sampled crossing is an administrative restricted-mean endpoint.",
            "The candidate may describe the retained observation process rather than tradable information arrival.",
            "The final seven event groups and 45 markets remained outside the formal catalog.",
            "The sealed identity is not a protected evaluation permit and exposes no protected values.",
        ],
    }
    content = json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n"
    if RECEIPT.exists() and RECEIPT.read_text() != content:
        raise ValueError("coordinator freeze receipt path already contains different bytes")
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(content)
    print(
        json.dumps(
            {
                "status": "SUCCEEDED",
                "receipt": str(RECEIPT),
                "receipt_sha256": hashlib.sha256(content.encode()).hexdigest(),
                "sample_key_count": len(keys),
                "prediction_count": staleness_summary["prediction_count"],
                "event_count": staleness_summary["event_count"],
                "event_wins": staleness_summary["event_wins_vs_comparator"],
                "formal_credibility_gate_pass": formal_gate_pass,
                "frozen_system_id": freeze.frozen.frozen_system_id,
                "protected_values_exposed": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
