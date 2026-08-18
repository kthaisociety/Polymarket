markets = read("polymarket-development-prices", "market_id")
events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")

PARENT_SOURCE_SHA256 = "dabe18ab627c9a95c4d066e90a03dfd2a4350d3c465464bad785381e0d627e5c"
PARENT_RECEIPT_SHA256 = "21c3d08cc236953d1ad7e2b6ddc3986db0528d90e9b7813bd31614d97f0f9314"
PARENT_SOURCE_03_RECEIPT_SHA256 = (
    "810dc73970961bc69386041973c349847b151208d8488f959aaa8e69321353b8"
)

STATE_MODEL = {
    "feature_indices": [0, 1, 2],
    "target_mean": 0.3510821749723434,
    "feature_means": [
        0.15517614372480415,
        0.12026999223814004,
        -2.6850458095273195,
    ],
    "feature_scales": [
        0.21255660832933462,
        0.14102809934951768,
        1.9784413542551837,
    ],
    "parameters": [
        -0.627919078727645,
        -0.029463581192508307,
        0.12435961753095053,
        0.23357171380431782,
    ],
    "represented_event_count": 152,
}

FULL_MODEL = {
    "feature_indices": [0, 1, 2, 3, 4],
    "target_mean": 0.3510821749723434,
    "feature_means": [
        0.15517614372480415,
        0.12026999223814004,
        -2.6850458095273195,
        1.3740711589836327,
        0.645867800834043,
    ],
    "feature_scales": [
        0.21255660832933462,
        0.14102809934951768,
        1.9784413542551837,
        1.3934628124722082,
        0.28506139161316757,
    ],
    "parameters": [
        -0.7799465703304458,
        -0.003380828460869684,
        0.05493675671970554,
        0.0975685155709,
        -0.5537737626060895,
        -0.5347412202176426,
    ],
    "represented_event_count": 152,
}


def sigmoid(value):
    clipped = min(30.0, max(-30.0, value))
    return 1.0 / (1.0 + exp(-clipped))


def clipped_probability(value):
    return min(0.999999, max(0.000001, value))


def predict_frozen(model, feature_columns, row):
    linear = model["parameters"][0]
    for position in range(len(model["feature_indices"])):
        feature_index = model["feature_indices"][position]
        standardized = (
            feature_columns[feature_index][row] - model["feature_means"][position]
        ) / model["feature_scales"][position]
        linear = linear + model["parameters"][position + 1] * standardized
    return clipped_probability(sigmoid(linear))


def metric_summary(test_events, test_labels, predictions, comparator):
    maximum_event = max(test_events)
    minimum_event = min(test_events)
    event_count = maximum_event - minimum_event + 1
    counts = [0 for unused in range(event_count)]
    positives = [0 for unused in range(event_count)]
    brier = [0.0 for unused in range(event_count)]
    comparator_brier = [0.0 for unused in range(event_count)]
    log_loss = [0.0 for unused in range(event_count)]
    comparator_log_loss = [0.0 for unused in range(event_count)]
    prediction_sum = 0.0
    target_sum = 0
    observation_brier = 0.0
    observation_log_loss = 0.0
    for row in range(len(test_labels)):
        event_position = test_events[row] - minimum_event
        target = test_labels[row]
        prediction = clipped_probability(predictions[row])
        comparison = clipped_probability(comparator[row])
        error = target - prediction
        comparator_error = target - comparison
        current_log_loss = -target * log(prediction) - (1 - target) * log(1.0 - prediction)
        current_comparator_log_loss = -target * log(comparison) - (1 - target) * log(
            1.0 - comparison
        )
        counts[event_position] = counts[event_position] + 1
        positives[event_position] = positives[event_position] + target
        brier[event_position] = brier[event_position] + error * error
        comparator_brier[event_position] = (
            comparator_brier[event_position] + comparator_error * comparator_error
        )
        log_loss[event_position] = log_loss[event_position] + current_log_loss
        comparator_log_loss[event_position] = (
            comparator_log_loss[event_position] + current_comparator_log_loss
        )
        observation_brier = observation_brier + error * error
        observation_log_loss = observation_log_loss + current_log_loss
        prediction_sum = prediction_sum + prediction
        target_sum = target_sum + target
    event_briers = []
    event_log_losses = []
    event_rows = []
    event_wins = 0
    for position in range(event_count):
        if counts[position] > 0:
            current_brier = brier[position] / counts[position]
            current_comparator_brier = comparator_brier[position] / counts[position]
            current_log_loss = log_loss[position] / counts[position]
            current_comparator_log_loss = comparator_log_loss[position] / counts[position]
            if current_brier < current_comparator_brier:
                event_wins = event_wins + 1
            event_briers = event_briers + [current_brier]
            event_log_losses = event_log_losses + [current_log_loss]
            event_rows = event_rows + [
                {
                    "event": position + minimum_event,
                    "count": counts[position],
                    "positive_count": positives[position],
                    "brier": current_brier,
                    "comparator_brier": current_comparator_brier,
                    "log_loss": current_log_loss,
                    "comparator_log_loss": current_comparator_log_loss,
                }
            ]
    midpoint = len(event_briers) // 2
    return {
        "prediction_count": len(test_labels),
        "event_count": len(event_briers),
        "observed_rate": target_sum / len(test_labels),
        "mean_prediction": prediction_sum / len(test_labels),
        "absolute_calibration_gap": abs(
            prediction_sum / len(test_labels) - target_sum / len(test_labels)
        ),
        "observation_brier": observation_brier / len(test_labels),
        "event_macro_brier": sum(event_briers) / len(event_briers),
        "early_event_macro_brier": sum(event_briers[:midpoint]) / midpoint,
        "late_event_macro_brier": sum(event_briers[midpoint:])
        / (len(event_briers) - midpoint),
        "observation_log_loss": observation_log_loss / len(test_labels),
        "event_macro_log_loss": sum(event_log_losses) / len(event_log_losses),
        "event_wins_vs_comparator": event_wins,
        "event_rows": event_rows,
    }


maximum_rows = len(probabilities)
row_events = [0 for unused in range(maximum_rows)]
labels = [0 for unused in range(maximum_rows)]
probability_level = [0.0 for unused in range(maximum_rows)]
boundary_distance = [0.0 for unused in range(maximum_rows)]
logit_level = [0.0 for unused in range(maximum_rows)]
log_quiet_run = [0.0 for unused in range(maximum_rows)]
zero_fraction_24 = [0.0 for unused in range(maximum_rows)]
sample_cursor = 0
order_break_count = 0

current_market = None
previous_ordinal = None
previous_time = None
previous_probability = None
quiet_run = 0
recent_changes = []

for row in range(len(probabilities)):
    market = markets[row]
    event = events[row]
    ordinal = ordinals[row]
    observed_time = times[row]
    probability = probabilities[row]
    if market != current_market:
        current_market = market
        previous_ordinal = None
        previous_time = None
        previous_probability = None
        quiet_run = 0
        recent_changes = []
        if ordinal != 0:
            order_break_count = order_break_count + 1
    if previous_time is not None:
        if ordinal != previous_ordinal + 1 or observed_time <= previous_time:
            order_break_count = order_break_count + 1
            quiet_run = 0
            recent_changes = []
        else:
            gap_hours = (observed_time - previous_time) / 3600.0
            if gap_hours < 0.75 or gap_hours > 1.25:
                quiet_run = 0
                recent_changes = []
            else:
                change = probability - previous_probability
                if len(recent_changes) == 24:
                    clipped = min(0.995, max(0.005, previous_probability))
                    zero_count = sum([1 for value in recent_changes if value == 0.0])
                    row_events[sample_cursor] = event
                    labels[sample_cursor] = int(change != 0.0)
                    probability_level[sample_cursor] = previous_probability
                    boundary_distance[sample_cursor] = min(
                        previous_probability, 1.0 - previous_probability
                    )
                    logit_level[sample_cursor] = log(clipped / (1.0 - clipped))
                    log_quiet_run[sample_cursor] = log(1.0 + quiet_run)
                    zero_fraction_24[sample_cursor] = zero_count / 24.0
                    sample_cursor = sample_cursor + 1
                recent_changes = recent_changes + [change]
                if len(recent_changes) > 24:
                    recent_changes = recent_changes[1:]
                if change == 0.0:
                    quiet_run = quiet_run + 1
                else:
                    quiet_run = 0
    previous_ordinal = ordinal
    previous_time = observed_time
    previous_probability = probability

row_events = row_events[:sample_cursor]
labels = labels[:sample_cursor]
feature_columns = [
    probability_level[:sample_cursor],
    boundary_distance[:sample_cursor],
    logit_level[:sample_cursor],
    log_quiet_run[:sample_cursor],
    zero_fraction_24[:sample_cursor],
]

state_predictions = [0.0 for unused in range(sample_cursor)]
full_predictions = [0.0 for unused in range(sample_cursor)]
for row in range(sample_cursor):
    state_predictions[row] = predict_frozen(STATE_MODEL, feature_columns, row)
    full_predictions[row] = predict_frozen(FULL_MODEL, feature_columns, row)

state_metrics = metric_summary(
    row_events, labels, state_predictions, state_predictions
)
full_metrics = metric_summary(row_events, labels, full_predictions, state_predictions)
relative_improvement = (
    state_metrics["event_macro_brier"] - full_metrics["event_macro_brier"]
) / state_metrics["event_macro_brier"]
replay_gate_passed = (
    full_metrics["observation_brier"] < state_metrics["observation_brier"]
    and full_metrics["event_macro_brier"] < state_metrics["event_macro_brier"]
    and full_metrics["observation_log_loss"] < state_metrics["observation_log_loss"]
    and full_metrics["event_macro_log_loss"] < state_metrics["event_macro_log_loss"]
    and relative_improvement >= 0.05
    and full_metrics["event_wins_vs_comparator"] / full_metrics["event_count"] >= 0.60
    and full_metrics["early_event_macro_brier"] < state_metrics["early_event_macro_brier"]
    and full_metrics["late_event_macro_brier"] < state_metrics["late_event_macro_brier"]
    and full_metrics["observation_brier"] <= 0.20
    and full_metrics["event_macro_brier"] <= 0.20
    and full_metrics["absolute_calibration_gap"] <= 0.05
    and full_metrics["event_count"] >= 20
    and full_metrics["prediction_count"] >= 5000
)

result = structured_return(
    "No-refit replay of the frozen continuous Polymarket update-arrival hazard.",
    {
        "schema_version": "polymarket-frozen-arrival-hazard-successor-replay/v1",
        "parent_source_sha256": PARENT_SOURCE_SHA256,
        "parent_receipt_sha256": PARENT_RECEIPT_SHA256,
        "parent_source_03_receipt_sha256": PARENT_SOURCE_03_RECEIPT_SHA256,
        "feature_names": [
            "probability_level",
            "boundary_distance",
            "winsorized_logit_level_005",
            "log_one_plus_prior_quiet_run_observations",
            "prior_24_regular_zero_fraction",
        ],
        "frozen_state_model": STATE_MODEL,
        "frozen_state_plus_staleness_model": FULL_MODEL,
        "sample_count": sample_cursor,
        "warmup_regular_increment_count": 24,
        "coverage_checks": {"order_break_count": order_break_count},
        "state_logistic": state_metrics,
        "state_plus_staleness_logistic": full_metrics,
        "event_macro_brier_relative_improvement_vs_state": relative_improvement,
        "fixed_gates": {
            "minimum_relative_event_macro_brier_improvement": 0.05,
            "minimum_event_win_share": 0.60,
            "maximum_observation_brier": 0.20,
            "maximum_event_macro_brier": 0.20,
            "maximum_absolute_calibration_gap": 0.05,
            "minimum_event_count": 20,
            "minimum_prediction_count": 5000,
            "require_brier_and_log_loss_improvement": True,
            "require_both_chronological_halves": True,
        },
        "replay_gate_passed": replay_gate_passed,
        "protected_values_exposed": False,
    },
    warnings=[
        "The literal models, lineage hashes, features, and gates were fixed before this replay.",
        "No fitting, scaling, calibration, or threshold selection occurs on the successor cohort.",
        "The successor cohort was used by earlier distinct process analyses and is not a protected holdout.",
        "The label is a change in the next registered hourly probability sample, not a trade.",
        "Irregular gaps reset the 24-increment warm-up and are excluded from this estimand.",
        "Arrival prediction does not imply direction, executable price, or profit.",
        "Ancestor and protected values remain unavailable.",
    ],
)
