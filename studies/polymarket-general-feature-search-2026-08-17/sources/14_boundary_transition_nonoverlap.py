price_markets = read("polymarket-development-prices", "market_id")
price_events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")


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


def boundary_state(probability):
    if probability <= 0.02 or probability >= 0.98:
        return 1
    return 0


def boundary_distance(probability):
    return min(probability, 1.0 - probability)


def sigmoid(value):
    clipped = min(30.0, max(-30.0, value))
    return 1.0 / (1.0 + exp(-clipped))


def fit_logistic(training, indices, penalty):
    event_counts = {}
    for row in training:
        event = row[0]
        if event not in event_counts:
            event_counts[event] = 0
        event_counts[event] = event_counts[event] + 1
    event_total = len(event_counts)
    feature_mean = [0.0 for unused in indices]
    second = [0.0 for unused in indices]
    target_mean = 0.0
    for row in training:
        weight = 1.0 / (event_total * event_counts[row[0]])
        target_mean = target_mean + weight * row[2]
        for position in range(len(indices)):
            value = row[1][indices[position]]
            feature_mean[position] = feature_mean[position] + weight * value
            second[position] = second[position] + weight * value * value
    scales = [0.0 for unused in indices]
    for position in range(len(indices)):
        variance = second[position] - feature_mean[position] * feature_mean[position]
        if variance < 0.000000000001:
            variance = 0.000000000001
        scales[position] = variance ** 0.5
    prior = min(0.999, max(0.001, target_mean))
    parameters = [0.0 for unused in range(len(indices) + 1)]
    parameters[0] = log(prior / (1.0 - prior))
    for iteration in range(4):
        gradient = [0.0 for unused in parameters]
        hessian = [[0.0 for unused in parameters] for unused in parameters]
        for row in training:
            event = row[0]
            weight = 1.0 / (event_total * event_counts[event])
            design = [1.0]
            for position in range(len(indices)):
                design = design + [(row[1][indices[position]] - feature_mean[position]) / scales[position]]
            linear = 0.0
            for position in range(len(parameters)):
                linear = linear + parameters[position] * design[position]
            prediction = sigmoid(linear)
            curvature = max(0.000001, prediction * (1.0 - prediction))
            for left in range(len(parameters)):
                gradient[left] = gradient[left] + weight * design[left] * (row[2] - prediction)
                for right in range(len(parameters)):
                    hessian[left][right] = hessian[left][right] + weight * curvature * design[left] * design[right]
        hessian[0][0] = hessian[0][0] + 0.000001
        for position in range(1, len(parameters)):
            gradient[position] = gradient[position] - penalty * parameters[position]
            hessian[position][position] = hessian[position][position] + penalty
        update = solve_linear(hessian, gradient)
        for position in range(len(parameters)):
            parameters[position] = parameters[position] + update[position]
    return [feature_mean, scales, parameters]


def predict_logistic(model, indices, features):
    linear = model[2][0]
    for position in range(len(indices)):
        standardized = (features[indices[position]] - model[0][position]) / model[1][position]
        linear = linear + model[2][position + 1] * standardized
    return sigmoid(linear)


def average_precision(rows, prediction_index):
    pairs = []
    positives = 0
    for row in rows:
        pairs = pairs + [[row[prediction_index], row[1]]]
        positives = positives + row[1]
    if positives == 0:
        return None
    ranked = sorted(pairs, reverse=True)
    seen = 0
    seen_positive = 0
    precision_sum = 0.0
    position = 0
    while position < len(ranked):
        end = position
        group_positive = 0
        while end < len(ranked) and ranked[end][0] == ranked[position][0]:
            group_positive = group_positive + ranked[end][1]
            end = end + 1
        seen = end
        seen_positive = seen_positive + group_positive
        precision_sum = precision_sum + group_positive * seen_positive / seen
        position = end
    return precision_sum / positives


def top_score_set(rows, prediction_index):
    predictions = []
    for row in rows:
        predictions = predictions + [row[prediction_index]]
    ranked = sorted(predictions, reverse=True)
    target_count = max(1, len(ranked) // 10)
    cutoff = ranked[target_count - 1]
    selected = 0
    positives = 0
    for row in rows:
        if row[prediction_index] >= cutoff:
            selected = selected + 1
            positives = positives + row[1]
    return [cutoff, selected, positives, positives / selected]


def metric_summary(rows, prediction_index, comparator_index):
    event_groups = {}
    squared = 0.0
    prediction_sum = 0.0
    target_sum = 0
    for row in rows:
        event = row[0]
        error = row[1] - row[prediction_index]
        comparator_error = row[1] - row[comparator_index]
        squared = squared + error * error
        prediction_sum = prediction_sum + row[prediction_index]
        target_sum = target_sum + row[1]
        if event not in event_groups:
            event_groups[event] = [0, 0.0, 0.0, [], 0.0, 0]
        group = event_groups[event]
        group[0] = group[0] + 1
        group[1] = group[1] + error * error
        group[2] = group[2] + comparator_error * comparator_error
        group[3] = group[3] + [row]
        group[4] = group[4] + row[prediction_index]
        group[5] = group[5] + row[1]
    event_mse = []
    event_ap = []
    event_prediction_means = []
    event_target_means = []
    event_wins = 0
    for event in sorted(event_groups):
        group = event_groups[event]
        mse = group[1] / group[0]
        event_mse = event_mse + [mse]
        event_prediction_means = event_prediction_means + [group[4] / group[0]]
        event_target_means = event_target_means + [group[5] / group[0]]
        if group[1] < group[2]:
            event_wins = event_wins + 1
        current_ap = average_precision(group[3], prediction_index)
        if current_ap is not None:
            event_ap = event_ap + [current_ap]
    top = top_score_set(rows, prediction_index)
    return {
        "observation_brier": squared / len(rows),
        "event_macro_brier": sum(event_mse) / len(event_mse),
        "pooled_average_precision": average_precision(rows, prediction_index),
        "event_macro_average_precision": sum(event_ap) / len(event_ap),
        "event_average_precision_count": len(event_ap),
        "event_wins_vs_comparator": event_wins,
        "represented_event_count": len(event_mse),
        "positive_count": target_sum,
        "observed_rate": target_sum / len(rows),
        "mean_prediction": prediction_sum / len(rows),
        "event_macro_observed_rate": sum(event_target_means) / len(event_target_means),
        "event_macro_mean_prediction": sum(event_prediction_means) / len(event_prediction_means),
        "top_score_cutoff": top[0],
        "top_score_count": top[1],
        "top_score_positive": top[2],
        "top_score_precision": top[3],
    }


points = {}
market_lengths = {}
market_events = {}
market_order = []
for row in range(len(price_markets)):
    market = price_markets[row]
    if market not in market_lengths:
        market_order = market_order + [market]
        market_lengths[market] = 0
        market_events[market] = price_events[row]
    points[(market, ordinals[row])] = [times[row], probabilities[row]]
    market_lengths[market] = market_lengths[market] + 1

label_names = ["entry_24h", "escape_24h"]
feature_names = [
    "probability_level",
    "boundary_distance",
    "winsorized_logit_level_005",
    "boundary_distance_change_6h",
    "boundary_distance_change_24h",
    "realized_variance_6h",
    "realized_variance_24h",
    "jump_concentration_24h",
    "zero_change_fraction_24h",
    "mean_absolute_change_24h",
    "log_current_regime_run_length",
]
state_indices = [0, 1, 2]
full_indices = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
ridge_penalty = 0.1
samples = {}

for market in market_order:
    length = market_lengths[market]
    event = market_events[market]
    for decision in range(24, length - 24, 24):
        current = points[(market, decision)]
        trailing = points[(market, decision - 24)]
        future = points[(market, decision + 24)]
        trailing_hours = (current[0] - trailing[0]) / 3600.0
        future_hours = (future[0] - current[0]) / 3600.0
        if 18.0 <= trailing_hours <= 30.0 and 18.0 <= future_hours <= 30.0:
            probability = current[1]
            clipped = min(0.995, max(0.005, probability))
            current_state = boundary_state(probability)
            future_state = boundary_state(future[1])
            rv6 = 0.0
            rv24 = 0.0
            max_step = 0.0
            zero_count = 0
            absolute_sum = 0.0
            for ordinal in range(decision - 23, decision + 1):
                step = points[(market, ordinal)][1] - points[(market, ordinal - 1)][1]
                absolute_step = abs(step)
                rv24 = rv24 + step * step
                absolute_sum = absolute_sum + absolute_step
                if ordinal >= decision - 5:
                    rv6 = rv6 + step * step
                if absolute_step > max_step:
                    max_step = absolute_step
                if absolute_step == 0.0:
                    zero_count = zero_count + 1
            run_length = 1
            previous_ordinal = decision - 1
            while previous_ordinal >= 0 and boundary_state(points[(market, previous_ordinal)][1]) == current_state:
                run_length = run_length + 1
                previous_ordinal = previous_ordinal - 1
            features = [
                probability,
                boundary_distance(probability),
                log(clipped / (1.0 - clipped)),
                boundary_distance(probability) - boundary_distance(points[(market, decision - 6)][1]),
                boundary_distance(probability) - boundary_distance(points[(market, decision - 24)][1]),
                rv6,
                rv24,
                max_step / ((rv24 + 0.000000000001) ** 0.5),
                zero_count / 24.0,
                absolute_sum / 24.0,
                log(1.0 + run_length),
            ]
            if current_state == 0:
                label = future_state
                name = "entry_24h"
            else:
                label = 1 - future_state
                name = "escape_24h"
            key = (name, event)
            if key not in samples:
                samples[key] = []
            samples[key] = samples[key] + [[event, features, label]]

results = []
for name in label_names:
    evaluated = []
    for test_event in range(8, 24):
        test_key = (name, test_event)
        if test_key not in samples:
            continue
        training = []
        training_event_count = 0
        baseline = 0.0
        for train_event in range(test_event):
            train_key = (name, train_event)
            if train_key in samples:
                event_rows = samples[train_key]
                training_event_count = training_event_count + 1
                event_target = 0
                for row in event_rows:
                    training = training + [row]
                    event_target = event_target + row[2]
                baseline = baseline + event_target / len(event_rows)
        baseline = baseline / training_event_count
        baseline = min(0.999, max(0.001, baseline))
        state_model = fit_logistic(training, state_indices, ridge_penalty)
        full_model = fit_logistic(training, full_indices, ridge_penalty)
        for row in samples[test_key]:
            state_prediction = predict_logistic(state_model, state_indices, row[1])
            full_prediction = predict_logistic(full_model, full_indices, row[1])
            evaluated = evaluated + [[row[0], row[2], baseline, state_prediction, full_prediction]]
    rate_metrics = metric_summary(evaluated, 2, 2)
    state_metrics = metric_summary(evaluated, 3, 2)
    full_metrics = metric_summary(evaluated, 4, 3)
    gate_pass = (
        full_metrics["observation_brier"] < state_metrics["observation_brier"]
        and full_metrics["observation_brier"] < rate_metrics["observation_brier"]
        and full_metrics["event_macro_brier"] < state_metrics["event_macro_brier"]
        and full_metrics["event_macro_brier"] < rate_metrics["event_macro_brier"]
        and full_metrics["pooled_average_precision"] > state_metrics["pooled_average_precision"]
        and full_metrics["event_macro_average_precision"] > state_metrics["event_macro_average_precision"]
        and full_metrics["event_wins_vs_comparator"] > full_metrics["represented_event_count"] / 2
        and full_metrics["top_score_precision"] >= 2.0 * full_metrics["observed_rate"]
        and full_metrics["mean_prediction"] >= 0.5 * full_metrics["observed_rate"]
        and full_metrics["mean_prediction"] <= 2.0 * full_metrics["observed_rate"]
    )
    state_robustness_pass = (
        state_metrics["positive_count"] >= 40
        and state_metrics["observation_brier"] < rate_metrics["observation_brier"]
        and state_metrics["event_macro_brier"] < rate_metrics["event_macro_brier"]
        and state_metrics["pooled_average_precision"] > rate_metrics["pooled_average_precision"]
        and state_metrics["event_macro_average_precision"] > rate_metrics["event_macro_average_precision"]
        and state_metrics["event_wins_vs_comparator"] > state_metrics["represented_event_count"] / 2
        and state_metrics["top_score_precision"] >= 2.0 * state_metrics["observed_rate"]
        and state_metrics["event_macro_mean_prediction"] >= 0.5 * state_metrics["event_macro_observed_rate"]
        and state_metrics["event_macro_mean_prediction"] <= 2.0 * state_metrics["event_macro_observed_rate"]
    )
    results = results + [{
        "label": name,
        "prediction_count": len(evaluated),
        "rate_baseline": rate_metrics,
        "state_logistic": state_metrics,
        "full_kinematics_logistic": full_metrics,
        "closed_full_model_original_gate_replay": gate_pass,
        "state_nonoverlap_robustness_pass": state_robustness_pass,
    }]

result = structured_return(
    "Non-overlapping 24-hour robustness replay for fixed boundary-transition models.",
    {
        "parent_coverage_source_sha256": "2191c8d1c116da54edadfa1e87349efc08cb82e9179946ca3859551d8e260952",
        "runtime_parent_source_sha256": "1060d86bf23ca5e375b676e095fb49edac306a8191cac12373e45634bab1262b",
        "initial_runtime_parent_source_sha256": "2b7b61352ea26e7cbfbe70e9e534f3d6deec112ab2326449e49660a9a58db7cf",
        "research_parent_source_sha256": "c00d6ae9595c267f0d92d56dcd4a1d1628f538cfe0d741bfdb45035bb9552c83",
        "labels": label_names,
        "feature_names": feature_names,
        "state_indices": state_indices,
        "full_indices": full_indices,
        "ridge_penalty": ridge_penalty,
        "newton_iteration_count": 4,
        "decision_stride_observations": 24,
        "minimum_training_events": 8,
        "test_event_range": [8, 23],
        "results": results,
    },
    warnings=[
        "All means, scales, priors, and coefficients use only earlier whole event groups with equal event weight.",
        "The fixed entry and escape labels condition on different at-risk populations and are not directly comparable.",
        "Average precision supplements Brier because both hazards are rare; zero-positive event AP is omitted.",
        "The fixed top-decile score set includes all observations tied at its cutoff.",
        "Four fixed Newton updates bound runtime; no data-dependent convergence rule or fallback is used.",
        "Successive 24-hour labels do not overlap; the fixed starting phase is observation ordinal 24.",
        "The full kinematics replay is audit-only and cannot reopen the rejected feature family.",
        "Protected values remain unavailable.",
    ],
)
