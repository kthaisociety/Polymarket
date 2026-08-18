"""Resolve the exact frozen continuous arrival hazard on one protected holdout."""

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
    AuthoredBacktestEngine,
    AuthoredCandidateManifest,
    AuthoredDevelopmentEvidence,
    AuthoredFreezeService,
    AuthoredProgramProposal,
    AuthoredProtectedPlan,
    AuthoredProtectedResolutionService,
    DevelopmentBudget,
    InvestigationRequest,
    ProtectedEvaluationPredeclaration,
    ResearchQuestion,
    RuntimeInvestigationCoordinator,
    configure_authored_protected_plan_authority,
)
from research_agent.protected_evaluation import (
    BacktestGovernance,
    CriterionComparison,
    EvaluationScenario,
    EvaluationSpec,
    Evaluator,
    ExposureRecorder,
    ExposureRegistry,
    FindingPublisher,
    FreezeEligibilityRegistry,
    FreezeGate,
    FrozenSystemRegistry,
    MetricCriterion,
    MetricName,
    NegativeResultRegistry,
    PermissionGrant,
    PermitRegistry,
    PromotionStandard,
    ProtectedContentManifest,
    ProtectedExposureStatus,
    ProtectedResourceScope,
    ProtectedViewBinder,
    ResearchLedger,
    ScenarioKind,
    Validator,
)
from research_agent.scientific_workflow import (
    ValidationAuthorityGrant,
    WorkflowAuthorityRegistry,
    configure_protected_resource_authority,
)

SNAPSHOT_SHA256 = "8c73260377ea5cb3e569bbc3c744ce9b62a95c8f54dafb73d07671845ccec4c6"
SNAPSHOT_SIZE = 318_684_407
ANCESTOR_SHA256 = "610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f"
ANCESTOR_SIZE = 19_434_443
WORKSPACE = Path(__file__).resolve().parents[5] / "data/chronos/polymarket-corpora"
RECEIPT = Path(__file__).parents[1] / "protected-receipts/19_continuous_arrival_hazard_protected_resolution.json"
PARENT_SOURCE_SHA256 = "dabe18ab627c9a95c4d066e90a03dfd2a4350d3c465464bad785381e0d627e5c"
PARENT_RECEIPT_SHA256 = "21c3d08cc236953d1ad7e2b6ddc3986db0528d90e9b7813bd31614d97f0f9314"
SUCCESSOR_SOURCE_SHA256 = "aaf439a67f61d42f50e5b4f711a8f6255a2fefce9733f9b3b43f6a91d7dc2f95"
SUCCESSOR_RECEIPT_SHA256 = "0ffda46feea1e16ea9398ac9054ad70bc5b7cc1992874926b6b4e6abdbb8843f"
DATA_PROTOCOL = "protocol:data:polymarket-corpus-8c732-continuous-anchor-arrival-v1"
TRAINING_PROTOCOL = "protocol:training:authored-expanding-event-equal-logistic-arrival-v1"
VALIDATION_POLICY = "policy:validation:polymarket-continuous-arrival-holdout-v1"
RESOURCE_POLICY = "policy:protected-resource:polymarket-continuous-arrival-holdout-v1"
FEATURE_NAMES = ("probability_level", "boundary_distance", "logit_level", "log_quiet_run", "zero_fraction_24")
EXPECTED_CANDIDATE_ID = (
    "authored-candidate:10b63992c977425e8b92bcc8d510a753775c1ed3708c89cbeff27734819b9de9"
)
EXPECTED_EVIDENCE_ID = (
    "authored-development-evidence:59ac537cb54a61360d7662a3e921178d7a79261ed2379890d5b16bc2d14bb60a"
)
EXPECTED_FROZEN_SYSTEM_ID = (
    "frozen-system:7b69995916de44043510c7d82a95b165d9aee6e2843d4bc00ca111808107b8eb"
)
EXPECTED_PLAN_ID = (
    "authored-protected-plan:691e74db76eb262808b111e83956f23b462745c51b4e2e5d4e8233b27595f962"
)

ARRIVAL_SOURCE = """
def clipped_probability(value):
    return min(0.999999, max(0.000001, value))

def sigmoid(value):
    clipped = min(30.0, max(-30.0, value))
    return 1.0 / (1.0 + exp(-clipped))

def make_features():
    observations = history("market_probability")
    recent = observations[-25:]
    changes = []
    for index in range(1, len(recent)):
        changes = changes + [recent[index]["value"] - recent[index - 1]["value"]]
    current_probability = recent[-1]["value"]
    clipped = min(0.995, max(0.005, current_probability))
    quiet_run = 0
    index = len(changes) - 1
    while index >= 0 and changes[index] == 0.0:
        quiet_run = quiet_run + 1
        index = index - 1
    zero_count = sum([1 for value in changes if value == 0.0])
    return {
        "probability_level": current_probability,
        "boundary_distance": min(current_probability, 1.0 - current_probability),
        "logit_level": log(clipped / (1.0 - clipped)),
        "log_quiet_run": log(1.0 + quiet_run),
        "zero_fraction_24": zero_count / 24.0,
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
                    augmented[row][column] = (
                        augmented[row][column] - factor * augmented[pivot][column]
                    )
    return [augmented[row][size] for row in range(size)]

def fit():
    rows = training_rows()
    feature_names = [
        "probability_level",
        "boundary_distance",
        "logit_level",
        "log_quiet_run",
        "zero_fraction_24",
    ]
    event_counts = {}
    for row in rows:
        event = dimension_value(row, "event_id")
        if event not in event_counts:
            event_counts[event] = 0
        event_counts[event] = event_counts[event] + 1
    represented_events = len(event_counts)
    feature_mean = [0.0 for unused in feature_names]
    feature_second = [0.0 for unused in feature_names]
    target_mean = 0.0
    for row in rows:
        event = dimension_value(row, "event_id")
        weight = 1.0 / (represented_events * event_counts[event])
        target_mean = target_mean + weight * row["label"]
        for position in range(len(feature_names)):
            value = row["features"][feature_names[position]]
            feature_mean[position] = feature_mean[position] + weight * value
            feature_second[position] = feature_second[position] + weight * value * value
    feature_scale = [0.0 for unused in feature_names]
    for position in range(len(feature_names)):
        variance = feature_second[position] - feature_mean[position] * feature_mean[position]
        if variance < 0.000000000001:
            variance = 0.000000000001
        feature_scale[position] = variance**0.5
    prior = clipped_probability(target_mean)
    parameters = [0.0 for unused in range(len(feature_names) + 1)]
    parameters[0] = log(prior / (1.0 - prior))
    for iteration in range(4):
        gradient = [0.0 for unused in parameters]
        hessian = [[0.0 for unused in parameters] for unused in parameters]
        for row in rows:
            event = dimension_value(row, "event_id")
            weight = 1.0 / (represented_events * event_counts[event])
            design = [1.0]
            for position in range(len(feature_names)):
                design = design + [
                    (row["features"][feature_names[position]] - feature_mean[position])
                    / feature_scale[position]
                ]
            linear = 0.0
            for position in range(len(parameters)):
                linear = linear + parameters[position] * design[position]
            prediction = sigmoid(linear)
            curvature = max(0.000001, prediction * (1.0 - prediction))
            for left in range(len(parameters)):
                gradient[left] = gradient[left] + weight * design[left] * (
                    row["label"] - prediction
                )
                for right in range(len(parameters)):
                    hessian[left][right] = (
                        hessian[left][right] + weight * curvature * design[left] * design[right]
                    )
        hessian[0][0] = hessian[0][0] + 0.000001
        for position in range(1, len(parameters)):
            gradient[position] = gradient[position] - 0.1 * parameters[position]
            hessian[position][position] = hessian[position][position] + 0.1
        update = solve_linear(hessian, gradient)
        for position in range(len(parameters)):
            parameters[position] = parameters[position] + update[position]
    return {
        "feature_names": feature_names,
        "feature_mean": feature_mean,
        "feature_scale": feature_scale,
        "parameters": parameters,
        "represented_event_count": represented_events,
    }

def predict():
    state = model_state()
    values = feature_values()
    linear = state["parameters"][0]
    for position in range(len(state["feature_names"])):
        name = state["feature_names"][position]
        standardized = (
            values[name] - state["feature_mean"][position]
        ) / state["feature_scale"][position]
        linear = linear + state["parameters"][position + 1] * standardized
    return clipped_probability(sigmoid(linear))
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


def _keys_with_regular_history(
    price_dataset: RegisteredDataset,
    keys: tuple[SampleKey, ...],
) -> tuple[SampleKey, ...]:
    by_dimensions: dict[tuple[tuple[str, str], ...], list[RegisteredObservation]] = {}
    for item in price_dataset.observations:
        by_dimensions.setdefault(tuple(sorted(item.dimensions)), []).append(item)
    retained: list[SampleKey] = []
    for key in keys:
        observations = sorted(
            by_dimensions.get(key.dimensions, ()), key=lambda item: item.reference_time
        )
        current_index = _latest_index_at(observations, key.decision_time)
        if current_index < 24:
            continue
        recent = observations[current_index - 24 : current_index + 1]
        regular = True
        for index in range(1, len(recent)):
            gap = (recent[index].reference_time - recent[index - 1].reference_time).total_seconds()
            if gap < 2700.0 or gap > 4500.0:
                regular = False
        if regular:
            retained.append(key)
    return tuple(retained)


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
            "gate-memo:polymarket-stochastic-process-continuous-arrival-hazard-v1",
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
            "gate-memo:polymarket-stochastic-process-continuous-arrival-hazard-v1",
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
            claim_statement="The exact frozen continuous state-and-staleness logistic arrival-hazard recipe met its predeclared binary sampled-move quality standard on the retained final-47-event holdout.",
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
                "claim-template:sampled-hourly-continuous-logistic-arrival-hazard-v1",
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


def _metric_json(item) -> dict[str, object]:
    return {
        "name": item.name.value,
        "value": item.value,
        "sample_size": item.sample_size,
        "denominator": item.denominator,
        "warning": item.warning,
    }


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
    development_keys = _keys_with_regular_history(
        source_prices, _event_anchor_keys(source_prices, development_markets)
    )
    protected_keys = _keys_with_regular_history(
        source_prices, _event_anchor_keys(source_prices, protected_markets)
    )
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
        "question:polymarket-registered-hourly-continuous-arrival-hazard",
        "Does the selected continuous state-and-staleness logistic hazard forecast whether the next regular registered hourly Polymarket probability sample changes?",
        development_catalog.environment_id,
        "task:polymarket-stochastic-process-paper",
        (PARENT_RECEIPT_SHA256, SUCCESSOR_RECEIPT_SHA256, "gate-memo:polymarket-stochastic-process-continuous-arrival-hazard-v1"),
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
        freeze_standard_ref="standard:freeze:formal-continuous-arrival-hazard-gate-v1",
    )
    plan.require_predeclared(declaration)
    request = InvestigationRequest(
        question=question,
        catalog=development_catalog,
        sample_keys=development_keys,
        current_time=max(item.available_at for item in development_catalog.observations),
        budget=DevelopmentBudget(1, 100, 200, "mse", 0.20),
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
    session_id = "session:chronos-polymarket-formal-continuous-arrival-hazard"
    episode_id = "episode:chronos-polymarket-formal-continuous-arrival-hazard"
    coordinator = RuntimeInvestigationCoordinator()
    registration = coordinator.register(request, session_id=session_id, episode_id=episode_id)
    runtime = coordinator.execute(
        registration.registration_id,
        AuthoredProgramProposal(
            ARRIVAL_SOURCE,
            manifest,
            "Selected event-equal continuous state-and-staleness logistic arrival hazard with fold-local scaling and event-equal fitting.",
            (),
        ),
        session_id=session_id,
        episode_id=episode_id,
        idempotency_key="formal-continuous-arrival-hazard:selected-law",
    )
    if runtime.candidate_id is None or runtime.evidence_id is None:
        message = f"formal arrival replay did not issue candidate evidence: {runtime.failure_detail}"
        raise ValueError(message)
    candidate = coordinator.resolve_candidate(runtime.candidate_id)
    evidence = coordinator.resolve_evidence(runtime.evidence_id)
    if candidate.candidate_id != EXPECTED_CANDIDATE_ID or evidence.evidence_id != EXPECTED_EVIDENCE_ID:
        raise ValueError("protected replay changed the exact candidate or development evidence")
    summary = _summary(evidence)
    gate = (
        summary["prediction_count"] >= 200
        and summary["event_count"] >= 80
        and summary["observation_mse"] <= 0.20
        and summary["event_macro_mse"] <= 0.20
        and summary["early_event_macro_mse"] <= 0.22
        and summary["late_event_macro_mse"] <= 0.22
        and abs(summary["mean_prediction"] - summary["mean_outcome"]) <= 0.05
        and summary["largest_event_squared_error_share"] <= 0.10
    )
    if not gate:
        rejection = {
            "status": "succeeded",
            "epistemic_status": "FORMAL_DEVELOPMENT_REJECTION",
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
            "formal_credibility_gate_pass": False,
            "freeze": None,
            "protected_backtest_run": False,
            "warnings": [
                "The fixed formal development gate failed; no independent freeze or protected request is permitted.",
                "This rejection cannot be repaired by changing the threshold after seeing evidence.",
                "The continuous hazard has a frozen later replay, but this formal schedule remains selection-exposed development evidence.",
                "The final 47-event protected block remains unexposed.",
            ],
        }
        _persist(rejection)
        print(
            json.dumps(
                {
                    key: rejection[key]
                    for key in (
                        "status",
                        "epistemic_status",
                        "candidate_id",
                        "evidence_id",
                        "formal_credibility_gate_pass",
                        "protected_values_exposed",
                    )
                },
                sort_keys=True,
            )
        )
        return

    ledger = ResearchLedger()
    eligibility = FreezeEligibilityRegistry()
    frozen_systems = FrozenSystemRegistry()
    clock_time = max(item.available_at for item in development_catalog.observations) + timedelta(seconds=1)
    freeze = AuthoredFreezeService(
        authority_id="authority:independent-polymarket-continuous-arrival-hazard-freeze",
        investigations=coordinator,
        eligibility=eligibility,
        gate=FreezeGate(
            ledger=ledger,
            registry=frozen_systems,
            eligibility=eligibility,
            decision_authority_id="authority:independent-polymarket-continuous-arrival-hazard-freeze",
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

    if freeze.frozen.frozen_system_id != EXPECTED_FROZEN_SYSTEM_ID:
        raise ValueError("protected replay changed the exact frozen system")
    if plan.plan_id != EXPECTED_PLAN_ID:
        raise ValueError("protected replay changed the exact authored plan")

    plan_registry, plan_issuer = configure_authored_protected_plan_authority(
        "authority:polymarket-continuous-arrival-protected-plan"
    )
    plan_issuer.issue(plan)
    resource_registry, resource_issuer = configure_protected_resource_authority(
        "authority:polymarket-retained-corpus"
    )
    resource_registration = resource_issuer.issue(
        scope=plan.protected_scope,
        resource_binding_ref=(
            f"binding:polymarket-corpus:{SNAPSHOT_SHA256}:continuous-arrival-holdout-v1"
        ),
        content_manifest=content_manifest,
        catalog=full_catalog,
    )

    exposures = ExposureRegistry()
    permits = PermitRegistry()
    governance_grant = PermissionGrant(
        session_id,
        "authority:independent-polymarket-continuous-arrival-governance",
        frozenset((plan.protected_scope.scope_id,)),
        plan.protected_scope.policy_ref,
        development_catalog.environment_id,
    )
    validation_grant = ValidationAuthorityGrant(
        "authority:independent-polymarket-continuous-arrival-validation",
        plan.promotion_standard.authority_policy_ref,
        development_catalog.environment_id,
    )
    authorities = WorkflowAuthorityRegistry(
        governance_permissions=(governance_grant,),
        validation_grants=(validation_grant,),
    )
    governance = BacktestGovernance(
        ledger=ledger,
        frozen_systems=frozen_systems,
        exposures=exposures,
        permits=permits,
        permissions=(governance_grant,),
        current_environment_ref=development_catalog.environment_id,
        current_policy_ref=plan.protected_scope.policy_ref,
        clock=lambda: clock_time,
    )
    binder = ProtectedViewBinder(
        permits=permits,
        clock=lambda: clock_time,
        current_environment_ref=development_catalog.environment_id,
        current_policy_ref=plan.protected_scope.policy_ref,
    )
    recorder = ExposureRecorder(registry=exposures, ledger=ledger, clock=lambda: clock_time)
    engine = AuthoredBacktestEngine(
        investigations=coordinator,
        plans=plan_registry,
        permits=permits,
        frozen_systems=frozen_systems,
        views=binder,
        exposures=recorder,
        ledger=ledger,
        clock=lambda: clock_time,
    )
    evaluator = Evaluator(ledger=ledger, runs=engine.issued_runs, clock=lambda: clock_time)
    negatives = NegativeResultRegistry()
    validator = Validator(
        authorized_authority_ids=frozenset((validation_grant.authority_id,)),
        authority_policy_ref=validation_grant.authority_policy_ref,
        ledger=ledger,
        reports=evaluator.issued_reports,
        negatives=negatives,
        clock=lambda: clock_time,
    )
    publisher = FindingPublisher(
        ledger=ledger,
        reports=evaluator.issued_reports,
        decisions=validator.issued_decisions,
        clock=lambda: clock_time,
    )
    resolution_service = AuthoredProtectedResolutionService(
        investigations=coordinator,
        frozen_systems=frozen_systems,
        plans=plan_registry,
        authorities=authorities,
        protected_resources=resource_registry,
        governance=governance,
        views=binder,
        engine=engine,
        evaluator=evaluator,
        validator=validator,
        publisher=publisher,
        negatives=negatives,
    )
    resolution = resolution_service.resolve(
        candidate_id=candidate.candidate_id,
        evidence_id=evidence.evidence_id,
        frozen_system_id=freeze.frozen.frozen_system_id,
        requester_id=session_id,
        beneficiary_id=question.task_ref,
        recipient_id="researcher:chronos-polymarket-continuous-arrival",
        idempotency_key="polymarket-continuous-arrival-protected-resolution-v1",
    )

    base_payload = {
        "status": "succeeded",
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "snapshot_ref": ref.uri,
        "partition_id": analysis.partition.partition_id,
        "development_event_count": len(development_events),
        "protected_event_count": analysis.partition.protected_event_count,
        "development_market_count": len(development_markets),
        "protected_market_count": len(protected_markets),
        "development_decision_count": len(development_keys),
        "protected_decision_count": len(protected_keys),
        "training_candidate_key_count": len(all_keys),
        "development_catalog_observation_count": len(development_catalog.observations),
        "evaluation_catalog_observation_count": len(full_catalog.observations),
        "candidate_id": candidate.candidate_id,
        "candidate_source_sha256": candidate.source_sha256,
        "trial_id": evidence.trial_id,
        "evidence_id": evidence.evidence_id,
        "formal_summary": summary,
        "formal_credibility_gate_pass": gate,
        "protected_plan": {
            "plan_id": plan.plan_id,
            "scenario_id": plan.scenario.identity,
            "decision_times_ref": plan.scenario.decision_times_ref,
            "evaluation_spec_id": plan.evaluation_spec.identity,
            "promotion_standard_id": plan.promotion_standard.identity,
            "protected_scope_id": plan.protected_scope.scope_id,
            "claim_template_ref": plan.claim_template_ref,
            "content_manifest_id": content_manifest.manifest_id,
            "criteria": [
                {
                    "metric": item.metric.value,
                    "comparison": item.comparison.value,
                    "threshold": item.threshold,
                }
                for item in plan.promotion_standard.criteria
            ],
            "maximum_stability_stddev": plan.promotion_standard.maximum_stability_stddev,
            "maximum_error_concentration": plan.promotion_standard.maximum_error_concentration,
        },
        "resource_registration_id": resource_registration.registration_id,
        "freeze": {
            "request_id": freeze.request.request_id,
            "decision_id": freeze.decision.decision_id,
            "frozen_system_id": freeze.frozen.frozen_system_id,
            "candidate_version": freeze.frozen.candidate_version,
            "protocol_refs": list(freeze.frozen.protocol_refs),
            "authority_id": freeze.frozen.freeze_authority_id,
        },
        "resolution": {
            "resolution_id": resolution.resolution_id,
            "status": resolution.status.value,
            "request_id": resolution.request_id,
            "permit_or_denial_id": resolution.permit_or_denial_id,
            "view_id": resolution.view_id,
            "run_id": resolution.run_id,
            "report_id": resolution.report_id,
            "validation_decision_id": resolution.validation_decision_id,
            "finding_id": resolution.finding_id,
            "negative_result_id": resolution.negative_result_id,
            "reason_codes": list(resolution.reason_codes),
        },
    }
    if resolution.run_id is None or resolution.report_id is None:
        payload = {
            **base_payload,
            "epistemic_status": "PROTECTED_REQUEST_DENIED_UNEXPOSED",
            "protected_values_exposed": False,
            "exposure": None,
            "run": None,
            "report": None,
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
                for item in ledger.entries()
            ],
            "warnings": [
                "Independent governance denied the request before protected disclosure.",
                "The protected period remains unexposed.",
            ],
        }
        _persist(payload)
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "epistemic_status": payload["epistemic_status"],
                    "protected_values_exposed": payload["protected_values_exposed"],
                    "reason_codes": list(resolution.reason_codes),
                },
                sort_keys=True,
            )
        )
        return

    run = engine.issued_runs.get(resolution.run_id)
    if run is None:
        raise ValueError("protected resolution referenced an unissued run")
    report = evaluator.measure(run, plan.evaluation_spec)
    if report.report_id != resolution.report_id:
        raise ValueError("protected report replay changed identity")
    exposure_records = exposures.records()
    if len(exposure_records) != 1 or report.exposure_ref != exposure_records[0].exposure_id:
        raise ValueError("protected resolution did not retain exactly one exposure")

    payload = {
        **base_payload,
        "epistemic_status": resolution.status.value.upper(),
        "protected_values_exposed": True,
        "exposure": {
            "exposure_id": exposure_records[0].exposure_id,
            "exposure_period_id": exposure_records[0].exposure_period_id,
            "disclosure_status": exposure_records[0].disclosure_status,
            "recipient_id": exposure_records[0].recipient_id,
            "disclosed_at": exposure_records[0].disclosed_at.isoformat(),
        },
        "run": {
            "run_id": run.run_id,
            "status": run.status.value,
            "decision_count": len(run.decisions),
            "failure_count": len(run.failures),
        },
        "report": {
            "report_id": report.report_id,
            "execution_valid": report.execution_valid,
            "metrics": [_metric_json(item) for item in report.metrics],
            "failures": [
                {"code": item.code, "count": item.count} for item in report.failures
            ],
            "stability": {
                "absolute_error_stddev": report.stability.absolute_error_stddev,
                "rolling_mse": list(report.stability.rolling_mse),
            },
            "concentration": {
                "maximum_squared_error_share": (
                    report.concentration.maximum_squared_error_share
                ),
                "worst_decision_time": (
                    report.concentration.worst_decision_time.isoformat()
                    if report.concentration.worst_decision_time is not None
                    else None
                ),
            },
            "per_time_count": len(report.per_time),
            "per_dimension_count": len(report.per_dimension),
            "caveats": list(report.caveats),
        },
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
            for item in ledger.entries()
        ],
        "warnings": [
            "This is one irreversibly exposed historical holdout, not reusable development data.",
            "The finding or rejection applies only to registered sampled-move probability on the exact schedule.",
            "The claim does not establish direction, execution, profitability, latent belief, or causality.",
        ],
    }
    _persist(payload)
    print(
        json.dumps(
            {
                "status": "SUCCEEDED",
                "resolution_status": resolution.status.value,
                "frozen_system_id": freeze.frozen.frozen_system_id,
                "protected_decision_count": len(protected_keys),
                "metrics": {item.name.value: item.value for item in report.metrics},
                "protected_values_exposed": True,
                "receipt": str(RECEIPT),
            },
            sort_keys=True,
        )
    )

if __name__ == "__main__":
    main()
