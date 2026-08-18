markets = read("polymarket-development-prices", "market_id")
events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")
outcome_markets = read("polymarket-development-outcomes", "market_id")
close_times = read("polymarket-development-outcomes", "close_time_epoch_seconds")


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


def fit_ridge(row_events, targets, feature_columns, indices, training_end, penalty):
    event_counts = [0 for unused in range(training_end)]
    for row in range(len(targets)):
        event = row_events[row]
        if event < training_end:
            event_counts[event] = event_counts[event] + 1
    represented_events = sum([1 for count in event_counts if count > 0])
    feature_mean = [0.0 for unused in indices]
    feature_second = [0.0 for unused in indices]
    target_mean = 0.0
    for row in range(len(targets)):
        event = row_events[row]
        if event < training_end and event_counts[event] > 0:
            weight = 1.0 / (represented_events * event_counts[event])
            target_mean = target_mean + weight * targets[row]
            for position in range(len(indices)):
                value = feature_columns[indices[position]][row]
                feature_mean[position] = feature_mean[position] + weight * value
                feature_second[position] = feature_second[position] + weight * value * value
    feature_scale = [0.0 for unused in indices]
    for position in range(len(indices)):
        variance = feature_second[position] - feature_mean[position] * feature_mean[position]
        feature_scale[position] = max(0.000001, max(0.0, variance) ** 0.5)
    dimension = len(indices) + 1
    matrix = [[0.0 for unused in range(dimension)] for unused in range(dimension)]
    vector = [0.0 for unused in range(dimension)]
    for row in range(len(targets)):
        event = row_events[row]
        if event < training_end and event_counts[event] > 0:
            weight = 1.0 / (represented_events * event_counts[event])
            design = [1.0]
            for position in range(len(indices)):
                design = design + [
                    (feature_columns[indices[position]][row] - feature_mean[position])
                    / feature_scale[position]
                ]
            for left in range(dimension):
                vector[left] = vector[left] + weight * design[left] * targets[row]
                for right in range(dimension):
                    matrix[left][right] = (
                        matrix[left][right] + weight * design[left] * design[right]
                    )
    matrix[0][0] = matrix[0][0] + 0.000001
    for position in range(1, dimension):
        matrix[position][position] = matrix[position][position] + penalty
    parameters = solve_linear(matrix, vector)
    return [target_mean, feature_mean, feature_scale, parameters, event_counts, represented_events]


def predict(model, feature_columns, indices, row):
    value = model[3][0]
    for position in range(len(indices)):
        standardized = (feature_columns[indices[position]][row] - model[1][position]) / model[2][
            position
        ]
        value = value + model[3][position + 1] * standardized
    return value


def fit_residual_scales(model, row_events, targets, feature_columns, indices, training_end):
    squared = 0.0
    absolute = 0.0
    for row in range(len(targets)):
        event = row_events[row]
        if event < training_end and model[4][event] > 0:
            weight = 1.0 / (model[5] * model[4][event])
            residual = targets[row] - predict(model, feature_columns, indices, row)
            squared = squared + weight * residual * residual
            absolute = absolute + weight * abs(residual)
    gaussian_scale = max(0.000001, squared**0.5)
    laplace_scale = max(0.000001, absolute)
    student_t3_scale = max(0.000001, (squared / 3.0) ** 0.5)
    return [gaussian_scale, laplace_scale, student_t3_scale]


def metric_summary(test_events, targets, predictions, comparator):
    minimum_event = min(test_events)
    event_slots = max(test_events) - minimum_event + 1
    counts = [0 for unused in range(event_slots)]
    squared = [0.0 for unused in range(event_slots)]
    absolute = [0.0 for unused in range(event_slots)]
    comparator_squared = [0.0 for unused in range(event_slots)]
    observation_squared = 0.0
    observation_absolute = 0.0
    wins = 0
    for row in range(len(targets)):
        position = test_events[row] - minimum_event
        error = targets[row] - predictions[row]
        comparator_error = targets[row] - comparator[row]
        counts[position] = counts[position] + 1
        squared[position] = squared[position] + error * error
        absolute[position] = absolute[position] + abs(error)
        comparator_squared[position] = (
            comparator_squared[position] + comparator_error * comparator_error
        )
        observation_squared = observation_squared + error * error
        observation_absolute = observation_absolute + abs(error)
    event_mse = []
    event_mae = []
    for position in range(event_slots):
        if counts[position] > 0:
            current_mse = squared[position] / counts[position]
            if current_mse < comparator_squared[position] / counts[position]:
                wins = wins + 1
            event_mse = event_mse + [current_mse]
            event_mae = event_mae + [absolute[position] / counts[position]]
    midpoint = len(event_mse) // 2
    return {
        "prediction_count": len(targets),
        "event_count": len(event_mse),
        "observation_mse": observation_squared / len(targets),
        "observation_mae": observation_absolute / len(targets),
        "event_macro_mse": sum(event_mse) / len(event_mse),
        "event_macro_mae": sum(event_mae) / len(event_mae),
        "early_event_macro_mse": sum(event_mse[:midpoint]) / midpoint,
        "late_event_macro_mse": sum(event_mse[midpoint:]) / (len(event_mse) - midpoint),
        "event_wins_vs_comparator": wins,
    }


def distribution_nll(residual, scales):
    gaussian = 0.5 * log(2.0 * pi) + log(scales[0]) + 0.5 * (residual / scales[0]) ** 2
    laplace = log(2.0 * scales[1]) + abs(residual) / scales[1]
    student_t3 = log(scales[2] * (3.0**0.5) * pi / 2.0) + 2.0 * log(
        1.0 + (residual / scales[2]) ** 2 / 3.0
    )
    return [gaussian, laplace, student_t3]


close_by_market = {}
for row in range(len(outcome_markets)):
    close_by_market[outcome_markets[row]] = close_times[row]

maximum_rows = len(probabilities)
row_events = [0 for unused in range(maximum_rows)]
targets = [0.0 for unused in range(maximum_rows)]
feature_columns = [[0.0 for unused in range(maximum_rows)] for feature in range(9)]
sample_cursor = 0
order_break_count = 0
current_market = None
previous_ordinal = None
previous_time = None
previous_probability = None
previous_nonzero_magnitude = 0.0
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
        previous_nonzero_magnitude = 0.0
        recent_changes = []
        if ordinal != 0:
            order_break_count = order_break_count + 1
    if previous_time is not None:
        if ordinal != previous_ordinal + 1 or observed_time <= previous_time:
            order_break_count = order_break_count + 1
            previous_nonzero_magnitude = 0.0
            recent_changes = []
        else:
            gap_hours = (observed_time - previous_time) / 3600.0
            if gap_hours < 0.75 or gap_hours > 1.25:
                previous_nonzero_magnitude = 0.0
                recent_changes = []
            else:
                change = probability - previous_probability
                magnitude = abs(change)
                hours_to_close = (close_by_market[market] - previous_time) / 3600.0
                if len(recent_changes) == 24 and magnitude > 0.0 and hours_to_close >= 0.0:
                    clipped = min(0.995, max(0.005, previous_probability))
                    absolute_history = [abs(value) for value in recent_changes]
                    row_events[sample_cursor] = event
                    targets[sample_cursor] = log(max(0.000001, magnitude))
                    feature_columns[0][sample_cursor] = previous_probability
                    feature_columns[1][sample_cursor] = min(
                        previous_probability, 1.0 - previous_probability
                    )
                    feature_columns[2][sample_cursor] = log(clipped / (1.0 - clipped))
                    feature_columns[3][sample_cursor] = log(1.0 + hours_to_close)
                    feature_columns[4][sample_cursor] = log(0.000001 + previous_nonzero_magnitude)
                    feature_columns[5][sample_cursor] = abs(recent_changes[-1])
                    feature_columns[6][sample_cursor] = sum(absolute_history)
                    feature_columns[7][sample_cursor] = max(absolute_history)
                    feature_columns[8][sample_cursor] = (
                        sum([1 for value in recent_changes if value == 0.0]) / 24.0
                    )
                    sample_cursor = sample_cursor + 1
                recent_changes = recent_changes + [change]
                if len(recent_changes) > 24:
                    recent_changes = recent_changes[1:]
                if magnitude > 0.0:
                    previous_nonzero_magnitude = magnitude
    previous_ordinal = ordinal
    previous_time = observed_time
    previous_probability = probability

row_events = row_events[:sample_cursor]
targets = targets[:sample_cursor]
feature_columns = [column[:sample_cursor] for column in feature_columns]
state_indices = [0, 1, 2, 3]
full_indices = [0, 1, 2, 3, 4, 5, 6, 7, 8]
test_events = [0 for unused in range(sample_cursor)]
test_targets = [0.0 for unused in range(sample_cursor)]
constant_predictions = [0.0 for unused in range(sample_cursor)]
state_predictions = [0.0 for unused in range(sample_cursor)]
full_predictions = [0.0 for unused in range(sample_cursor)]
distribution_losses = [[0.0 for unused in range(sample_cursor)] for distribution in range(3)]
test_cursor = 0
fold_rows = []

test_start = 40
while test_start <= max(row_events):
    test_end = min(test_start + 15, max(row_events) + 1)
    state_model = fit_ridge(row_events, targets, feature_columns, state_indices, test_start, 0.1)
    full_model = fit_ridge(row_events, targets, feature_columns, full_indices, test_start, 0.1)
    scales = fit_residual_scales(
        full_model, row_events, targets, feature_columns, full_indices, test_start
    )
    fold_count = 0
    for row in range(sample_cursor):
        event = row_events[row]
        if event >= test_start and event < test_end:
            state_prediction = predict(state_model, feature_columns, state_indices, row)
            full_prediction = predict(full_model, feature_columns, full_indices, row)
            test_events[test_cursor] = event
            test_targets[test_cursor] = targets[row]
            constant_predictions[test_cursor] = state_model[0]
            state_predictions[test_cursor] = state_prediction
            full_predictions[test_cursor] = full_prediction
            losses = distribution_nll(targets[row] - full_prediction, scales)
            for distribution in range(3):
                distribution_losses[distribution][test_cursor] = losses[distribution]
            test_cursor = test_cursor + 1
            fold_count = fold_count + 1
    fold_rows = fold_rows + [
        {
            "train_event_end_exclusive": test_start,
            "test_event_start": test_start,
            "test_event_end_exclusive": test_end,
            "prediction_count": fold_count,
            "training_event_count": full_model[5],
            "state_parameters": state_model[3],
            "full_parameters": full_model[3],
            "residual_scales_gaussian_laplace_student_t3": scales,
        }
    ]
    test_start = test_end

test_events = test_events[:test_cursor]
test_targets = test_targets[:test_cursor]
constant_predictions = constant_predictions[:test_cursor]
state_predictions = state_predictions[:test_cursor]
full_predictions = full_predictions[:test_cursor]
distribution_losses = [losses[:test_cursor] for losses in distribution_losses]
constant_metrics = metric_summary(
    test_events, test_targets, constant_predictions, constant_predictions
)
state_metrics = metric_summary(test_events, test_targets, state_predictions, constant_predictions)
full_metrics = metric_summary(test_events, test_targets, full_predictions, state_predictions)

event_slots = max(test_events) - min(test_events) + 1
distribution_counts = [0 for unused in range(event_slots)]
distribution_event_sums = [[0.0 for unused in range(event_slots)] for distribution in range(3)]
distribution_observation_sums = [0.0, 0.0, 0.0]
for row in range(test_cursor):
    position = test_events[row] - min(test_events)
    distribution_counts[position] = distribution_counts[position] + 1
    for distribution in range(3):
        loss = distribution_losses[distribution][row]
        distribution_event_sums[distribution][position] = (
            distribution_event_sums[distribution][position] + loss
        )
        distribution_observation_sums[distribution] = (
            distribution_observation_sums[distribution] + loss
        )
distribution_rows = []
distribution_names = ["gaussian", "laplace", "student_t_df3"]
for distribution in range(3):
    event_losses = []
    for position in range(event_slots):
        if distribution_counts[position] > 0:
            event_losses = event_losses + [
                distribution_event_sums[distribution][position] / distribution_counts[position]
            ]
    distribution_rows = distribution_rows + [
        {
            "distribution": distribution_names[distribution],
            "observation_mean_nll": distribution_observation_sums[distribution] / test_cursor,
            "event_macro_mean_nll": sum(event_losses) / len(event_losses),
        }
    ]

relative_improvement = (
    state_metrics["event_macro_mse"] - full_metrics["event_macro_mse"]
) / state_metrics["event_macro_mse"]
magnitude_gate_passed = (
    full_metrics["observation_mse"] < state_metrics["observation_mse"]
    and full_metrics["event_macro_mse"] < state_metrics["event_macro_mse"]
    and full_metrics["event_macro_mae"] < state_metrics["event_macro_mae"]
    and relative_improvement >= 0.02
    and full_metrics["event_wins_vs_comparator"] / full_metrics["event_count"] >= 0.60
    and full_metrics["early_event_macro_mse"] < state_metrics["early_event_macro_mse"]
    and full_metrics["late_event_macro_mse"] < state_metrics["late_event_macro_mse"]
)
heavy_tail_gate_passed = min(
    distribution_rows[1]["observation_mean_nll"], distribution_rows[2]["observation_mean_nll"]
) < distribution_rows[0]["observation_mean_nll"] - 0.02 * abs(
    distribution_rows[0]["observation_mean_nll"]
) and min(
    distribution_rows[1]["event_macro_mean_nll"], distribution_rows[2]["event_macro_mean_nll"]
) < distribution_rows[0]["event_macro_mean_nll"] - 0.02 * abs(
    distribution_rows[0]["event_macro_mean_nll"]
)

result = structured_return(
    "Chronological nonzero-update magnitude and residual-law comparison for the process paper.",
    {
        "schema_version": "polymarket-nonzero-magnitude-comparison/v1",
        "target": "log_max_1e-6_absolute_registered_hourly_change",
        "feature_names": [
            "probability_level",
            "boundary_distance",
            "winsorized_logit_level_005",
            "log_one_plus_hours_to_close",
            "log_prior_nonzero_magnitude",
            "prior_regular_absolute_change",
            "prior_24_absolute_variation",
            "prior_24_maximum_absolute_change",
            "prior_24_zero_fraction",
        ],
        "sample_count": sample_cursor,
        "test_prediction_count": test_cursor,
        "test_event_start": 40,
        "test_event_end_inclusive": max(test_events),
        "warmup_regular_increment_count": 24,
        "fixed_test_block_event_count": 15,
        "ridge_penalty": 0.1,
        "constant_log_magnitude": constant_metrics,
        "state_ridge": state_metrics,
        "state_plus_path_ridge": full_metrics,
        "event_macro_mse_relative_improvement_vs_state": relative_improvement,
        "residual_distribution_comparison": distribution_rows,
        "magnitude_gate_passed": magnitude_gate_passed,
        "heavy_tail_gate_passed": heavy_tail_gate_passed,
        "folds": fold_rows,
        "coverage_checks": {"order_break_count": order_break_count},
    },
    warnings=[
        "Magnitude is conditional on a nonzero registered hourly sample change, not a trade return.",
        "The log-magnitude floor is fixed at 1e-6 and does not alter nonzero source values above it.",
        "Distribution likelihoods compare residual laws on the same log-magnitude scale.",
        "All fits and scales use only earlier whole events with equal total event weight.",
        "Grid rounding, sampling, and bounded support remain outside the residual laws.",
        "Magnitude prediction does not establish executable profit.",
        "Ancestor and final protected events remain unavailable.",
    ],
)
