"""Formalize and independently freeze the selected hurdle-arrival component."""

# ruff: noqa: C901, D103, E501, EM101, INP001, PLR0915, PLR2004, T201, TRY003

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

from research_agent.data_adapters.polymarket import (
    PolymarketCorpusSnapshotRef,
    PolymarketCorpusStore,
    build_polymarket_development_analysis,
    build_polymarket_replication_analysis,
    register_polymarket_resolution_corpus,
)
from research_agent.data_foundation import (
    DataCatalogSnapshot,
    MissingnessPolicy,
    ObservationInput,
    ObservationRegistrar,
    RegisteredDataset,
    RegisteredObservation,
    SampleKey,
    TemporalOffset,
    TrainingWindowPolicy,
    WindowKind,
)
from research_agent.investigation import (
    AuthoredCandidateManifest,
    AuthoredDevelopmentEvidence,
    AuthoredFreezeService,
    AuthoredProgramProposal,
    AuthoredProtectedPlan,
    DevelopmentBudget,
    InvestigationRequest,
    ProtectedEvaluationPredeclaration,
    ResearchQuestion,
    RuntimeInvestigationCoordinator,
)
from research_agent.protected_evaluation import (
    CriterionComparison,
    EvaluationScenario,
    EvaluationSpec,
    FreezeEligibilityRegistry,
    FreezeGate,
    FrozenSystemRegistry,
    MetricCriterion,
    MetricName,
    PromotionStandard,
    ProtectedContentManifest,
    ProtectedExposureStatus,
    ProtectedResourceScope,
    ResearchLedger,
    ScenarioKind,
)

SNAPSHOT_SHA256 = "8c73260377ea5cb3e569bbc3c744ce9b62a95c8f54dafb73d07671845ccec4c6"
SNAPSHOT_SIZE = 318_684_407
ANCESTOR_SHA256 = "610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f"
ANCESTOR_SIZE = 19_434_443
WORKSPACE = Path(__file__).resolve().parents[5] / "data/chronos/polymarket-corpora"
RECEIPT = Path(__file__).parents[1] / "development-receipts/14_formal_hurdle_arrival_freeze.json"
PARENT_SOURCE_SHA256 = "13ea0c25a8e65da52cad44f4fa70a863790760cb9f2d67774769744cefbb477b"
PARENT_RECEIPT_SHA256 = "2c107a29710e3dd9d13cbf24be00e655b4b0a5c3a628fd8026670a1ad88cd9c5"
SUCCESSOR_SOURCE_SHA256 = "0934e2f9283a772a65e9f1080a0b9ad5c53f310acfe29e95df205e291fd303d4"
SUCCESSOR_RECEIPT_SHA256 = "dc48119c03b492217c3ab26ae781aaf1e6a5a87342d772cbcb78057095940e13"
DATA_PROTOCOL = "protocol:data:polymarket-corpus-8c732-bounded-anchor-arrival-v2"
TRAINING_PROTOCOL = "protocol:training:authored-expanding-event-equal-arrival-v1"
VALIDATION_POLICY = "policy:validation:polymarket-arrival-holdout-v1"
RESOURCE_POLICY = "policy:protected-resource:polymarket-arrival-holdout-v1"
FEATURE_NAMES = ("probability_band", "quiet_band")

ARRIVAL_SOURCE = """
def probability_band(value):
    if value <= 0.02:
        return 0
    if value < 0.20:
        return 1
    if value <= 0.80:
        return 2
    if value < 0.98:
        return 3
    return 4

def quiet_band(value):
    if value == 0:
        return 0
    if value <= 5:
        return 1
    if value <= 23:
        return 2
    return 3

def make_features():
    observations = history("market_probability")
    current = observations[-1]
    quiet = 0
    index = len(observations) - 1
    while index > 0:
        gap = (
            observations[index]["reference_time_epoch_seconds"]
            - observations[index - 1]["reference_time_epoch_seconds"]
        )
        if gap < 2700.0 or gap > 4500.0:
            index = 0
        elif observations[index]["value"] != observations[index - 1]["value"]:
            index = 0
        else:
            quiet = quiet + 1
            index = index - 1
    return {
        "probability_band": probability_band(current["value"]),
        "quiet_band": quiet_band(quiet),
    }

def make_label():
    observations = history("market_probability")
    current = observations[-1]
    future = outcome_path()
    if len(future) == 0:
        return None
    next_observation = future[0]
    gap = (
        next_observation["reference_time_epoch_seconds"]
        - current["reference_time_epoch_seconds"]
    )
    if gap < 2700.0 or gap > 4500.0:
        return None
    if next_observation["value"] == current["value"]:
        return 0.0
    return 1.0

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
    global_total = 0.0
    cell_total = [0.0 for unused in range(20)]
    cell_weight = [0.0 for unused in range(20)]
    for row in rows:
        event = dimension_value(row, "event_id")
        weight = 1.0 / event_counts[event]
        cell = int(row["features"]["probability_band"]) * 4 + int(row["features"]["quiet_band"])
        global_total = global_total + weight * row["label"]
        cell_total[cell] = cell_total[cell] + weight * row["label"]
        cell_weight[cell] = cell_weight[cell] + weight
    global_probability = global_total / len(event_counts)
    cells = []
    for cell in range(20):
        cells = cells + [
            (cell_total[cell] + global_probability) / (cell_weight[cell] + 1.0)
        ]
    return {"global_probability": global_probability, "cells": cells}

def predict():
    state = model_state()
    values = feature_values()
    cell = int(values["probability_band"]) * 4 + int(values["quiet_band"])
    return min(0.999999999999, max(0.000000000001, state["cells"][cell]))
"""


def _catalog_for_keys(
    source: DataCatalogSnapshot,
    keys: tuple[SampleKey, ...],
) -> DataCatalogSnapshot:
    price_dataset = next(
        item for item in source.datasets if item.schema.dataset_id == "polymarket-outcome-price-series"
    )
    by_dimensions: dict[tuple[tuple[str, str], ...], list[RegisteredObservation]] = {}
    for item in price_dataset.observations:
        by_dimensions.setdefault(tuple(sorted(item.dimensions)), []).append(item)
    selected_ids: set[str] = set()
    for key in keys:
        observations = sorted(
            by_dimensions.get(key.dimensions, ()), key=lambda item: item.reference_time
        )
        history = [item for item in observations if item.reference_time <= key.decision_time]
        outcome_end = key.decision_time + timedelta(minutes=75)
        outcome = [
            item
            for item in observations
            if key.decision_time < item.reference_time <= outcome_end
        ]
        selected_ids.update(item.observation_id for item in history[-25:])
        selected_ids.update(item.observation_id for item in outcome)
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
            for item in price_dataset.observations
            if item.observation_id in selected_ids
        )
    registered = ObservationRegistrar().register(price_dataset.schema, rows)
    return DataCatalogSnapshot(source.environment_id, (registered,))


def _latest_index_at(prices: list[RegisteredObservation], anchor: datetime) -> int:
    result = -1
    for index, item in enumerate(prices):
        if item.reference_time <= anchor:
            result = index
        else:
            break
    return result


def _event_anchor_keys(
    price_dataset: RegisteredDataset,
    allowed_markets: frozenset[str],
) -> tuple[SampleKey, ...]:
    by_event_market: dict[str, dict[str, list[RegisteredObservation]]] = {}
    for item in price_dataset.observations:
        dimensions = dict(item.dimensions)
        market_id = dimensions["market_id"]
        if market_id not in allowed_markets:
            continue
        by_event_market.setdefault(dimensions["event_id"], {}).setdefault(market_id, []).append(item)
    keys: list[SampleKey] = []
    for event_id in sorted(by_event_market):
        markets = by_event_market[event_id]
        for prices in markets.values():
            prices.sort(key=lambda item: item.reference_time)
        anchors = sorted(
            {prices[24].reference_time for prices in markets.values() if len(prices) >= 26}
        )
        best_anchor = None
        best: list[RegisteredObservation] = []
        for anchor in anchors:
            valid: list[RegisteredObservation] = []
            for market_id in sorted(markets):
                prices = markets[market_id]
                current_index = _latest_index_at(prices, anchor)
                if current_index < 24 or current_index + 1 >= len(prices):
                    continue
                current = prices[current_index]
                following = prices[current_index + 1]
                gap = (following.reference_time - current.reference_time).total_seconds()
                if (
                    2700.0 <= gap <= 4500.0
                    and following.reference_time > anchor
                    and following.reference_time <= anchor + timedelta(minutes=75)
                ):
                    valid.append(current)
            selected = valid[:5]
            if len(selected) > len(best):
                best_anchor = anchor
                best = selected
        if best_anchor is not None:
            keys.extend(SampleKey(best_anchor, item.dimensions) for item in best)
    return tuple(sorted(keys, key=lambda item: (item.decision_time, item.dimensions)))


def _manifest_for(catalog: DataCatalogSnapshot) -> ProtectedContentManifest:
    content = catalog.identity.encode()
    return ProtectedContentManifest.create(
        content_digest=hashlib.sha256(content).hexdigest(),
        byte_length=len(content),
        catalog_id=catalog.identity,
        provenance_ref=f"authority-retained:{SNAPSHOT_SHA256}",
    )


def _plan(
    full_catalog: DataCatalogSnapshot,
    protected_keys: tuple[SampleKey, ...],
    all_keys: tuple[SampleKey, ...],
) -> tuple[AuthoredProtectedPlan, ProtectedContentManifest]:
    content_manifest = _manifest_for(full_catalog)
    scope = ProtectedResourceScope(
        resource_id="polymarket-retained-arrival-holdout",
        resource_version="v2",
        slice_id="final-47-events",
        environment_ref=full_catalog.environment_id,
        policy_ref=RESOURCE_POLICY,
        content_manifest_id=content_manifest.manifest_id,
        content_identity_id=content_manifest.content_identity_id,
        epistemic_period_ref="period:polymarket-corpus-8c732-final-47-events",
        exposure_status=ProtectedExposureStatus.UNSEEN,
    )
    scenario = EvaluationScenario(
        name="Polymarket registered hourly move-arrival holdout",
        version=1,
        kind=ScenarioKind.HISTORICAL_WALK_FORWARD,
        decision_sample_keys=protected_keys,
        training_candidate_keys=all_keys,
        outcome_recorded_at=max(item.available_at for item in full_catalog.observations),
        training_protocol_ref=TRAINING_PROTOCOL,
        window_policy=TrainingWindowPolicy(1, WindowKind.EXPANDING, 100, None, TRAINING_PROTOCOL),
        missingness_policy=MissingnessPolicy.EXCLUDE_EXAMPLE,
        interpretation="one untouched whole-event chronological Polymarket arrival holdout",
        environment_ref=full_catalog.environment_id,
        data_protocol_ref=DATA_PROTOCOL,
        provenance_refs=(
            f"polymarket-corpus:{SNAPSHOT_SHA256}",
            "partition:whole-event-chronological-final-47-v1",
            "sampling:metadata-only-common-event-anchor-up-to-five-markets-v1",
            "projection:last-25-history-plus-next-75-minutes-per-declared-anchor-v2",
        ),
    )
    specification = EvaluationSpec(
        name="Polymarket registered hourly move-arrival protected quality",
        version=1,
        protocol_ref="protocol:evaluation:arrival-brier-coverage-stability-v1",
        metric_names=(MetricName.MSE, MetricName.MAE, MetricName.COVERAGE, MetricName.FAILURE_RATE),
        rolling_window=20,
        include_per_time=False,
        include_dimension_views=False,
        include_stability=True,
        include_concentration=True,
        benchmark_refs=(PARENT_RECEIPT_SHA256, SUCCESSOR_RECEIPT_SHA256),
        provenance_refs=(
            "gate-memo:polymarket-stochastic-process-hurdle-arrival-v1",
            PARENT_SOURCE_SHA256,
            SUCCESSOR_SOURCE_SHA256,
        ),
    )
    standard = PromotionStandard(
        name="Polymarket registered hourly move-arrival protected standard",
        version=1,
        evaluation_spec_id=specification.identity,
        criteria=(
            MetricCriterion(MetricName.MSE, CriterionComparison.LESS_THAN_OR_EQUAL, 0.20),
            MetricCriterion(MetricName.MAE, CriterionComparison.LESS_THAN_OR_EQUAL, 0.40),
            MetricCriterion(MetricName.COVERAGE, CriterionComparison.GREATER_THAN_OR_EQUAL, 0.95),
            MetricCriterion(MetricName.FAILURE_RATE, CriterionComparison.LESS_THAN_OR_EQUAL, 0.05),
        ),
        maximum_stability_stddev=0.30,
        maximum_error_concentration=0.05,
        required_scenario_kind=ScenarioKind.HISTORICAL_WALK_FORWARD,
        authority_policy_ref=VALIDATION_POLICY,
        provenance_refs=(
            "gate-memo:polymarket-stochastic-process-hurdle-arrival-v1",
            "standard:fixed-before-protected-disclosure",
        ),
    )
    return (
        AuthoredProtectedPlan.create(
            scenario=scenario,
            evaluation_spec=specification,
            promotion_standard=standard,
            protected_scope=scope,
            claim_name="Polymarket registered hourly move-arrival finding",
            claim_version=1,
            claim_statement="The exact frozen state-and-quiet-duration hurdle arrival recipe met its predeclared binary sampled-move quality standard on the retained final-47-event holdout.",
            claim_scope_limitations=(
                "Applies only to the exact retained corpus, metadata-only event-anchor schedule, and final-47-event holdout.",
                "Predicts whether the next regular registered hourly sample changes, not direction, resolution, latent belief, executable return, or profitability.",
            ),
            claim_required_caveats=(
                "A registered sampled value is not necessarily a trade, quote, or efficient price.",
                "Quiet duration may partly describe the observation mechanism rather than information arrival.",
                "The protected standard is absolute and does not establish superiority to every comparator.",
            ),
            claim_provenance_refs=(
                "claim-template:sampled-hourly-hurdle-arrival-v1",
                PARENT_RECEIPT_SHA256,
                SUCCESSOR_RECEIPT_SHA256,
            ),
        ),
        content_manifest,
    )


def _summary(evidence: AuthoredDevelopmentEvidence) -> dict[str, object]:
    by_event: dict[str, list[tuple[float, float]]] = {}
    first_by_event = {}
    for key, prediction, outcome in zip(
        evidence.row_keys, evidence.predictions, evidence.outcomes, strict=True
    ):
        event = dict(key.dimensions)["event_id"]
        by_event.setdefault(event, []).append((prediction, outcome))
        first_by_event[event] = min(key.decision_time, first_by_event.get(event, key.decision_time))
    event_rows = []
    for event in sorted(by_event, key=lambda item: (first_by_event[item], item)):
        rows = by_event[event]
        squared = [(prediction - outcome) ** 2 for prediction, outcome in rows]
        event_rows.append(
            {
                "event_id": event,
                "row_count": len(rows),
                "mse": sum(squared) / len(squared),
                "mean_prediction": sum(prediction for prediction, _ in rows) / len(rows),
                "mean_outcome": sum(outcome for _, outcome in rows) / len(rows),
            }
        )
    midpoint = len(event_rows) // 2
    squared_errors = [
        (prediction - outcome) ** 2
        for prediction, outcome in zip(evidence.predictions, evidence.outcomes, strict=True)
    ]
    total_squared = sum(squared_errors)
    event_squared = [row["mse"] * row["row_count"] for row in event_rows]
    return {
        "prediction_count": len(evidence.predictions),
        "event_count": len(event_rows),
        "observation_mse": sum(squared_errors) / len(squared_errors),
        "event_macro_mse": sum(row["mse"] for row in event_rows) / len(event_rows),
        "early_event_macro_mse": sum(row["mse"] for row in event_rows[:midpoint]) / midpoint,
        "late_event_macro_mse": sum(row["mse"] for row in event_rows[midpoint:]) / (len(event_rows) - midpoint),
        "mean_prediction": sum(evidence.predictions) / len(evidence.predictions),
        "mean_outcome": sum(evidence.outcomes) / len(evidence.outcomes),
        "largest_event_squared_error_share": max(event_squared) / total_squared,
        "event_rows": event_rows,
    }


def _persist(payload: dict[str, object]) -> None:
    content = (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode()
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    try:
        with RECEIPT.open("xb") as handle:
            handle.write(content)
    except FileExistsError:
        if RECEIPT.read_bytes() != content:
            raise ValueError("formal arrival receipt path already contains different bytes") from None


def main() -> None:
    ref = PolymarketCorpusSnapshotRef(SNAPSHOT_SHA256, SNAPSHOT_SIZE)
    snapshot = PolymarketCorpusStore(WORKSPACE).load(ref)
    ancestor = PolymarketCorpusStore(WORKSPACE).load(
        PolymarketCorpusSnapshotRef(ANCESTOR_SHA256, ANCESTOR_SIZE)
    )
    standard_analysis = build_polymarket_development_analysis(
        snapshot, session_id="formal-stochastic-process-arrival-standard-partition-2026-08-18"
    )
    analysis = build_polymarket_replication_analysis(
        snapshot,
        ancestor,
        session_id="formal-stochastic-process-arrival-2026-08-18",
    )
    development_events = frozenset(analysis.partition.development_event_ids)
    standard_development_events = frozenset(standard_analysis.partition.development_event_ids)
    development_markets = frozenset(
        contract.market_id for contract in snapshot.corpus.contracts if contract.event_id in development_events
    )
    protected_markets = frozenset(
        contract.market_id
        for contract in snapshot.corpus.contracts
        if contract.event_id not in standard_development_events
    )
    source_catalog = register_polymarket_resolution_corpus(snapshot).catalog
    source_prices = next(
        item for item in source_catalog.datasets if item.schema.dataset_id == "polymarket-outcome-price-series"
    )
    development_keys = _event_anchor_keys(source_prices, development_markets)
    protected_keys = _event_anchor_keys(source_prices, protected_markets)
    all_keys = tuple(sorted((*development_keys, *protected_keys), key=lambda item: (item.decision_time, item.dimensions)))
    development_catalog = _catalog_for_keys(source_catalog, development_keys)
    full_catalog = _catalog_for_keys(source_catalog, all_keys)
    development_prices = next(
        item for item in development_catalog.datasets if item.schema.dataset_id == "polymarket-outcome-price-series"
    )
    if not development_keys or not protected_keys:
        raise ValueError("arrival decision schedule is empty")
    if any(dict(key.dimensions)["market_id"] in protected_markets for key in development_keys):
        raise ValueError("protected market entered development decision schedule")

    plan, content_manifest = _plan(full_catalog, protected_keys, all_keys)
    probability = development_prices.schema.field_ref("market_probability")
    question = ResearchQuestion(
        "question:polymarket-registered-hourly-hurdle-arrival",
        "Does the selected probability-state and quiet-duration hurdle law forecast whether the next regular registered hourly Polymarket probability sample changes?",
        development_catalog.environment_id,
        "task:polymarket-stochastic-process-paper",
        (PARENT_RECEIPT_SHA256, SUCCESSOR_RECEIPT_SHA256, "gate-memo:polymarket-stochastic-process-hurdle-arrival-v1"),
    )
    declaration = ProtectedEvaluationPredeclaration(
        data_protocol_ref=plan.scenario.data_protocol_ref,
        training_protocol_ref=plan.scenario.training_protocol_ref,
        scenario_ref=plan.scenario.identity,
        decision_times_ref=plan.scenario.decision_times_ref,
        evaluation_spec_ref=plan.evaluation_spec.identity,
        validation_standard_ref=plan.promotion_standard.identity,
        protected_scope_id=plan.protected_scope.scope_id,
        claim_template_ref=plan.claim_template_ref,
        freeze_standard_ref="standard:freeze:formal-hurdle-arrival-gate-v1",
    )
    plan.require_predeclared(declaration)
    request = InvestigationRequest(
        question=question,
        catalog=development_catalog,
        sample_keys=development_keys,
        current_time=max(item.available_at for item in development_catalog.observations),
        budget=DevelopmentBudget(1, 100, 300, "mse", 0.20),
        random_seed=47,
        protected_predeclaration=declaration,
    )
    population_names = tuple(sorted(development_prices.schema.resolve("market_probability").dimensions))
    manifest = AuthoredCandidateManifest(
        question_id=question.question_id,
        environment_id=development_catalog.environment_id,
        predictor_fields=(probability,),
        outcome_field=probability,
        horizon=TemporalOffset.elapsed(timedelta(minutes=75)),
        minimum_outcome_points=1,
        population_dimensions=(),
        feature_names=FEATURE_NAMES,
        missing_value_policy="exclude_example",
        evidence_refs=question.evidence_refs,
        provenance_refs=(ref.uri, PARENT_SOURCE_SHA256, SUCCESSOR_SOURCE_SHA256),
        population_dimension_names=population_names,
    )
    session_id = "session:chronos-polymarket-formal-hurdle-arrival"
    episode_id = "episode:chronos-polymarket-formal-hurdle-arrival"
    coordinator = RuntimeInvestigationCoordinator()
    registration = coordinator.register(request, session_id=session_id, episode_id=episode_id)
    runtime = coordinator.execute(
        registration.registration_id,
        AuthoredProgramProposal(
            ARRIVAL_SOURCE,
            manifest,
            "Selected event-equal state-and-quiet-duration Bernoulli hurdle arrival law with one-event cell shrinkage.",
            (),
        ),
        session_id=session_id,
        episode_id=episode_id,
        idempotency_key="formal-hurdle-arrival:selected-law",
    )
    if runtime.candidate_id is None or runtime.evidence_id is None:
        raise ValueError(
            f"formal arrival replay did not issue candidate evidence: {runtime.failure_detail}"
        )
    candidate = coordinator.resolve_candidate(runtime.candidate_id)
    evidence = coordinator.resolve_evidence(runtime.evidence_id)
    summary = _summary(evidence)
    gate = (
        summary["prediction_count"] >= 300
        and summary["event_count"] >= 80
        and summary["observation_mse"] <= 0.20
        and summary["event_macro_mse"] <= 0.20
        and summary["early_event_macro_mse"] <= 0.22
        and summary["late_event_macro_mse"] <= 0.22
        and abs(summary["mean_prediction"] - summary["mean_outcome"]) <= 0.05
        and summary["largest_event_squared_error_share"] <= 0.10
    )
    if not gate:
        raise ValueError("formal hurdle-arrival replay failed its fixed development gate")

    ledger = ResearchLedger()
    eligibility = FreezeEligibilityRegistry()
    frozen_systems = FrozenSystemRegistry()
    clock_time = max(item.available_at for item in development_catalog.observations) + timedelta(seconds=1)
    freeze = AuthoredFreezeService(
        authority_id="authority:independent-polymarket-hurdle-arrival-freeze",
        investigations=coordinator,
        eligibility=eligibility,
        gate=FreezeGate(
            ledger=ledger,
            registry=frozen_systems,
            eligibility=eligibility,
            decision_authority_id="authority:independent-polymarket-hurdle-arrival-freeze",
            clock=lambda: clock_time,
        ),
    ).assess_credible(
        candidate_id=candidate.candidate_id,
        evidence_id=evidence.evidence_id,
        requester_id=session_id,
        beneficiary_id=question.task_ref,
    )
    if freeze.frozen is None:
        raise ValueError("independent freeze did not seal the formal arrival candidate")

    payload = {
        "status": "succeeded",
        "epistemic_status": "FROZEN_DEVELOPMENT_CANDIDATE",
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "snapshot_ref": ref.uri,
        "partition_id": analysis.partition.partition_id,
        "development_event_count": len(development_events),
        "protected_event_count": analysis.partition.protected_event_count,
        "development_market_count": len(development_markets),
        "protected_market_count": len(protected_markets),
        "development_decision_count": len(development_keys),
        "protected_decision_count": len(protected_keys),
        "development_catalog_observation_count": len(development_catalog.observations),
        "evaluation_catalog_observation_count": len(full_catalog.observations),
        "protected_values_exposed": False,
        "parent_source_sha256": PARENT_SOURCE_SHA256,
        "parent_receipt_sha256": PARENT_RECEIPT_SHA256,
        "successor_source_sha256": SUCCESSOR_SOURCE_SHA256,
        "successor_receipt_sha256": SUCCESSOR_RECEIPT_SHA256,
        "candidate_id": candidate.candidate_id,
        "candidate_source_sha256": candidate.source_sha256,
        "trial_id": evidence.trial_id,
        "evidence_id": evidence.evidence_id,
        "kernel_metrics": dict(evidence.metrics),
        "formal_summary": summary,
        "formal_credibility_gate_pass": gate,
        "protected_plan": {
            "plan_id": plan.plan_id,
            "scenario_id": plan.scenario.identity,
            "evaluation_spec_id": plan.evaluation_spec.identity,
            "promotion_standard_id": plan.promotion_standard.identity,
            "protected_scope_id": plan.protected_scope.scope_id,
            "claim_template_ref": plan.claim_template_ref,
            "content_manifest_id": content_manifest.manifest_id,
        },
        "freeze": {
            "request_id": freeze.request.request_id,
            "decision_id": freeze.decision.decision_id,
            "decision_status": freeze.decision.status.value,
            "frozen_system_id": freeze.frozen.frozen_system_id,
            "candidate_version": freeze.frozen.candidate_version,
            "protocol_refs": list(freeze.frozen.protocol_refs),
        },
        "actual_program_accesses": {
            "features": sorted({(item.interface, item.field_id) for item in evidence.feature_accesses}),
            "labels": sorted({(item.interface, item.field_id) for item in evidence.label_accesses}),
            "fit": sorted({(item.interface, item.field_id) for item in evidence.fit_accesses}),
            "prediction": sorted({(item.interface, item.field_id) for item in evidence.prediction_accesses}),
        },
        "warnings": [
            "This is selection-exposed formal development evidence, not protected validation.",
            "The full distributional law remains development-plus-successor evidence because the current protected evaluator has no distributional log-score plugin.",
            "The candidate forecasts registered sampled moves, not trades, quotes, latent beliefs, direction, resolution, or executable returns.",
            "The final 47 event groups remain unavailable to authored code.",
            "The authority registered only the last 25 history samples and next 75 minutes required by each fixed decision; this projection changes no feature, label, threshold, or decision key.",
        ],
    }
    _persist(payload)
    print(json.dumps({key: payload[key] for key in ("status", "epistemic_status", "candidate_id", "evidence_id", "formal_credibility_gate_pass", "protected_values_exposed")}, sort_keys=True))


if __name__ == "__main__":
    main()
