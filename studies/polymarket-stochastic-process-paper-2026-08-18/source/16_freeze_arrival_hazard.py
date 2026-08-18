markets = read("polymarket-development-prices", "market_id")
events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")


def sigmoid(value):
    clipped = min(30.0, max(-30.0, value))
    return 1.0 / (1.0 + exp(-clipped))


def clipped_probability(value):
    return min(0.999999, max(0.000001, value))


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


def fit_logistic(row_events, labels, feature_columns, indices, training_end, penalty):
    event_counts = [0 for unused in range(training_end)]
    for row in range(len(labels)):
        event = row_events[row]
        if event < training_end:
            event_counts[event] = event_counts[event] + 1
    represented_events = sum([1 for count in event_counts if count > 0])
    feature_mean = [0.0 for unused in indices]
    feature_second = [0.0 for unused in indices]
    target_mean = 0.0
    for row in range(len(labels)):
        event = row_events[row]
        if event < training_end and event_counts[event] > 0:
            weight = 1.0 / (represented_events * event_counts[event])
            target_mean = target_mean + weight * labels[row]
            for position in range(len(indices)):
                value = feature_columns[indices[position]][row]
                feature_mean[position] = feature_mean[position] + weight * value
                feature_second[position] = feature_second[position] + weight * value * value
    feature_scale = [0.0 for unused in indices]
    for position in range(len(indices)):
        variance = feature_second[position] - feature_mean[position] * feature_mean[position]
        if variance < 0.000000000001:
            variance = 0.000000000001
        feature_scale[position] = variance**0.5
    prior = clipped_probability(target_mean)
    parameters = [0.0 for unused in range(len(indices) + 1)]
    parameters[0] = log(prior / (1.0 - prior))
    for iteration in range(4):
        gradient = [0.0 for unused in parameters]
        hessian = [[0.0 for unused in parameters] for unused in parameters]
        for row in range(len(labels)):
            event = row_events[row]
            if event < training_end and event_counts[event] > 0:
                weight = 1.0 / (represented_events * event_counts[event])
                design = [1.0]
                for position in range(len(indices)):
                    design = design + [
                        (feature_columns[indices[position]][row] - feature_mean[position])
                        / feature_scale[position]
                    ]
                linear = 0.0
                for position in range(len(parameters)):
                    linear = linear + parameters[position] * design[position]
                prediction = sigmoid(linear)
                curvature = max(0.000001, prediction * (1.0 - prediction))
                for left in range(len(parameters)):
                    gradient[left] = gradient[left] + weight * design[left] * (
                        labels[row] - prediction
                    )
                    for right in range(len(parameters)):
                        hessian[left][right] = (
                            hessian[left][right] + weight * curvature * design[left] * design[right]
                        )
        hessian[0][0] = hessian[0][0] + 0.000001
        for position in range(1, len(parameters)):
            gradient[position] = gradient[position] - penalty * parameters[position]
            hessian[position][position] = hessian[position][position] + penalty
        update = solve_linear(hessian, gradient)
        for position in range(len(parameters)):
            parameters[position] = parameters[position] + update[position]
    return [target_mean, feature_mean, feature_scale, parameters, represented_events]


def predict_logistic(model, feature_columns, indices, row):
    linear = model[3][0]
    for position in range(len(indices)):
        standardized = (feature_columns[indices[position]][row] - model[1][position]) / model[2][
            position
        ]
        linear = linear + model[3][position + 1] * standardized
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
        "observation_brier": observation_brier / len(test_labels),
        "event_macro_brier": sum(event_briers) / len(event_briers),
        "early_event_macro_brier": sum(event_briers[:midpoint]) / midpoint,
        "late_event_macro_brier": sum(event_briers[midpoint:]) / (len(event_briers) - midpoint),
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

state_indices = [0, 1, 2]
full_indices = [0, 1, 2, 3, 4]
test_events = [0 for unused in range(sample_cursor)]
test_labels = [0 for unused in range(sample_cursor)]
constant_predictions = [0.0 for unused in range(sample_cursor)]
state_predictions = [0.0 for unused in range(sample_cursor)]
full_predictions = [0.0 for unused in range(sample_cursor)]
test_cursor = 0
fold_rows = []

test_start = 40
while test_start <= max(row_events):
    test_end = min(test_start + 15, max(row_events) + 1)
    state_model = fit_logistic(row_events, labels, feature_columns, state_indices, test_start, 0.1)
    full_model = fit_logistic(row_events, labels, feature_columns, full_indices, test_start, 0.1)
    fold_prediction_count = 0
    for row in range(sample_cursor):
        event = row_events[row]
        if event >= test_start and event < test_end:
            test_events[test_cursor] = event
            test_labels[test_cursor] = labels[row]
            constant_predictions[test_cursor] = clipped_probability(state_model[0])
            state_predictions[test_cursor] = predict_logistic(
                state_model, feature_columns, state_indices, row
            )
            full_predictions[test_cursor] = predict_logistic(
                full_model, feature_columns, full_indices, row
            )
            test_cursor = test_cursor + 1
            fold_prediction_count = fold_prediction_count + 1
    fold_rows = fold_rows + [
        {
            "train_event_end_exclusive": test_start,
            "test_event_start": test_start,
            "test_event_end_exclusive": test_end,
            "prediction_count": fold_prediction_count,
            "training_event_count": full_model[4],
            "training_move_rate": full_model[0],
            "state_parameters": state_model[3],
            "full_parameters": full_model[3],
        }
    ]
    test_start = test_end

test_events = test_events[:test_cursor]
test_labels = test_labels[:test_cursor]
constant_predictions = constant_predictions[:test_cursor]
state_predictions = state_predictions[:test_cursor]
full_predictions = full_predictions[:test_cursor]

constant_metrics = metric_summary(
    test_events, test_labels, constant_predictions, constant_predictions
)
state_metrics = metric_summary(test_events, test_labels, state_predictions, constant_predictions)
full_metrics = metric_summary(test_events, test_labels, full_predictions, state_predictions)

event_brier_relative_improvement = (
    state_metrics["event_macro_brier"] - full_metrics["event_macro_brier"]
) / state_metrics["event_macro_brier"]
arrival_gate_passed = (
    full_metrics["observation_brier"] < state_metrics["observation_brier"]
    and full_metrics["event_macro_brier"] < state_metrics["event_macro_brier"]
    and full_metrics["event_macro_log_loss"] < state_metrics["event_macro_log_loss"]
    and event_brier_relative_improvement >= 0.05
    and full_metrics["event_wins_vs_comparator"] / full_metrics["event_count"] >= 0.60
    and full_metrics["early_event_macro_brier"] < state_metrics["early_event_macro_brier"]
    and full_metrics["late_event_macro_brier"] < state_metrics["late_event_macro_brier"]
)

final_training_end = max(row_events) + 1
final_state_model = fit_logistic(
    row_events, labels, feature_columns, state_indices, final_training_end, 0.1
)
final_full_model = fit_logistic(
    row_events, labels, feature_columns, full_indices, final_training_end, 0.1
)

result = structured_return(
    "Chronological next-hour update-arrival model comparison for the process paper.",
    {
        "schema_version": "polymarket-update-arrival-comparison/v1",
        "feature_names": [
            "probability_level",
            "boundary_distance",
            "winsorized_logit_level_005",
            "log_one_plus_prior_quiet_run_observations",
            "prior_24_regular_zero_fraction",
        ],
        "sample_count": sample_cursor,
        "test_prediction_count": test_cursor,
        "test_event_start": 40,
        "test_event_end_inclusive": max(test_events),
        "warmup_regular_increment_count": 24,
        "fixed_test_block_event_count": 15,
        "ridge_penalty": 0.1,
        "newton_update_count": 4,
        "coverage_checks": {"order_break_count": order_break_count},
        "constant_rate": constant_metrics,
        "state_logistic": state_metrics,
        "state_plus_staleness_logistic": full_metrics,
        "event_macro_brier_relative_improvement_vs_state": (event_brier_relative_improvement),
        "arrival_gate_passed": arrival_gate_passed,
        "folds": fold_rows,
        "final_development_models": {
            "state": {
                "feature_indices": state_indices,
                "target_mean": final_state_model[0],
                "feature_means": final_state_model[1],
                "feature_scales": final_state_model[2],
                "parameters": final_state_model[3],
                "represented_event_count": final_state_model[4],
            },
            "state_plus_staleness": {
                "feature_indices": full_indices,
                "target_mean": final_full_model[0],
                "feature_means": final_full_model[1],
                "feature_scales": final_full_model[2],
                "parameters": final_full_model[3],
                "represented_event_count": final_full_model[4],
            },
        },
    },
    warnings=[
        "The label is a change in the next registered hourly probability sample, not a trade.",
        "Irregular gaps reset the 24-increment warm-up and are excluded from this estimand.",
        "All feature scaling, priors, and coefficients use only earlier whole events.",
        "Each represented training event receives equal total weight in every fit.",
        "All-development models retain fitted means, scales, and coefficients solely for a literal successor replay.",
        "Staleness may describe the public sampling process as well as economic inactivity.",
        "Arrival prediction does not imply direction, executable price, or profit.",
        "Ancestor and final protected events remain unavailable.",
    ],
)
