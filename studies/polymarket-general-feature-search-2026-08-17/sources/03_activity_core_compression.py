price_markets = read("polymarket-development-prices", "market_id")
price_events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")
outcome_markets = read("polymarket-development-outcomes", "market_id")
close_times = read("polymarket-development-outcomes", "close_time_epoch_seconds")


def solve_linear(matrix, vector):
    size = len(vector)
    augmented = [None for unused in range(size)]
    for row in range(size):
        augmented[row] = [0.0 for unused in range(size + 1)]
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


def fit_group(test_event, indices, target, penalty):
    event_weight = 0.0
    target_mean = 0.0
    feature_mean = [0.0 for unused in indices]
    second = [[0.0 for unused in indices] for unused in indices]
    cross_target = [0.0 for unused in indices]
    for event in range(test_event):
        if event in aggregates:
            aggregate = aggregates[event]
            count = aggregate[0]
            event_weight = event_weight + 1.0
            target_mean = target_mean + aggregate[3][target] / count
            for left in range(len(indices)):
                feature = indices[left]
                feature_mean[left] = feature_mean[left] + aggregate[1][feature] / count
                cross_target[left] = cross_target[left] + aggregate[4][target][feature] / count
                for right in range(len(indices)):
                    second[left][right] = second[left][right] + aggregate[2][feature][indices[right]] / count
    target_mean = target_mean / event_weight
    for left in range(len(indices)):
        feature_mean[left] = feature_mean[left] / event_weight
        cross_target[left] = cross_target[left] / event_weight
        for right in range(len(indices)):
            second[left][right] = second[left][right] / event_weight
    scale = [0.0 for unused in indices]
    for left in range(len(indices)):
        variance = second[left][left] - feature_mean[left] * feature_mean[left]
        if variance < 0.000000000001:
            variance = 0.000000000001
        scale[left] = variance ** 0.5
    covariance = [[0.0 for unused in indices] for unused in indices]
    target_covariance = [0.0 for unused in indices]
    for left in range(len(indices)):
        target_covariance[left] = (cross_target[left] - feature_mean[left] * target_mean) / scale[left]
        for right in range(len(indices)):
            covariance[left][right] = (
                second[left][right] - feature_mean[left] * feature_mean[right]
            ) / (scale[left] * scale[right])
        covariance[left][left] = covariance[left][left] + penalty
    return [target_mean, feature_mean, scale, solve_linear(covariance, target_covariance)]


def predict_group(model, indices, features):
    prediction = model[0]
    for position in range(len(indices)):
        prediction = prediction + model[3][position] * (
            features[indices[position]] - model[1][position]
        ) / model[2][position]
    return prediction


feature_names = [
    "boundary_distance",
    "current_boundary_state_002",
    "log_one_plus_hours_to_close",
    "realized_variance_6h",
    "jump_concentration_24h",
    "zero_change_fraction_24h",
    "mean_absolute_change_24h",
]
label_names = ["absolute_change_6h", "large_move_002"]
groups = {
    "activity_core": [0, 1, 2, 3, 4, 5, 6],
    "activity_no_expiry": [0, 1, 3, 4, 5, 6],
}
group_names = ["activity_core", "activity_no_expiry"]
feature_count = len(feature_names)
label_count = len(label_names)
ridge_penalty = 0.1
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
close_by_market = {}
for row in range(len(outcome_markets)):
    close_by_market[outcome_markets[row]] = close_times[row]

samples = {}
event_counts = {}
aggregates = {}
excluded_irregular = 0
for market in market_order:
    event = market_events[market]
    for decision in range(24, market_lengths[market] - 6, 6):
        current = points[(market, decision)]
        trailing = points[(market, decision - 24)]
        future = points[(market, decision + 6)]
        trailing_hours = (current[0] - trailing[0]) / 3600.0
        future_hours = (future[0] - current[0]) / 3600.0
        if trailing_hours < 18.0 or trailing_hours > 30.0 or future_hours < 4.5 or future_hours > 7.5:
            excluded_irregular = excluded_irregular + 1
        else:
            probability = current[1]
            boundary_distance = min(probability, 1.0 - probability)
            boundary_state = 1.0 if probability <= 0.02 or probability >= 0.98 else 0.0
            expiry = log(1.0 + max(0.0, (close_by_market[market] - current[0]) / 3600.0))
            rv6 = 0.0
            rv24 = 0.0
            max_step = 0.0
            zero_count = 0.0
            absolute_sum = 0.0
            for ordinal in range(decision - 23, decision + 1):
                step = points[(market, ordinal)][1] - points[(market, ordinal - 1)][1]
                absolute_step = abs(step)
                rv24 = rv24 + step * step
                absolute_sum = absolute_sum + absolute_step
                if absolute_step == 0.0:
                    zero_count = zero_count + 1.0
                if absolute_step > max_step:
                    max_step = absolute_step
                if ordinal >= decision - 5:
                    rv6 = rv6 + step * step
            jump_concentration = max_step / ((rv24 + 0.000000000001) ** 0.5)
            features = [
                boundary_distance,
                boundary_state,
                expiry,
                rv6,
                jump_concentration,
                zero_count / 24.0,
                absolute_sum / 24.0,
            ]
            magnitude = abs(future[1] - probability)
            targets = [magnitude, 1.0 if magnitude >= 0.02 else 0.0]
            if event not in event_counts:
                event_counts[event] = 0
                aggregates[event] = [
                    0,
                    [0.0 for unused in range(feature_count)],
                    [[0.0 for unused in range(feature_count)] for unused in range(feature_count)],
                    [0.0 for unused in range(label_count)],
                    [[0.0 for unused in range(feature_count)] for unused in range(label_count)],
                ]
            count = event_counts[event]
            event_counts[event] = count + 1
            samples[(event, count)] = [features, targets]
            aggregate = aggregates[event]
            aggregate[0] = aggregate[0] + 1
            for target in range(label_count):
                aggregate[3][target] = aggregate[3][target] + targets[target]
            for left in range(feature_count):
                aggregate[1][left] = aggregate[1][left] + features[left]
                for target in range(label_count):
                    aggregate[4][target][left] = aggregate[4][target][left] + features[left] * targets[target]
                for right in range(feature_count):
                    aggregate[2][left][right] = aggregate[2][left][right] + features[left] * features[right]

metrics = {}
test_events = []
for test_event in range(8, 24):
    if test_event not in event_counts:
        continue
    test_events = test_events + [test_event]
    fitted = {}
    baseline_means = [0.0 for unused in range(label_count)]
    event_weight = 0.0
    for train_event in range(test_event):
        if train_event in aggregates:
            event_weight = event_weight + 1.0
            for target in range(label_count):
                baseline_means[target] = baseline_means[target] + aggregates[train_event][3][target] / aggregates[train_event][0]
    for target in range(label_count):
        baseline_means[target] = baseline_means[target] / event_weight
        metrics[(test_event, target, "baseline")] = [0.0, 0.0, 0]
        for group in group_names:
            fitted[(target, group)] = fit_group(test_event, groups[group], target, ridge_penalty)
            metrics[(test_event, target, group)] = [0.0, 0.0, 0]
    for sample_index in range(event_counts[test_event]):
        sample = samples[(test_event, sample_index)]
        for target in range(label_count):
            error = sample[1][target] - baseline_means[target]
            metric = metrics[(test_event, target, "baseline")]
            metric[0] = metric[0] + error * error
            metric[1] = metric[1] + abs(error)
            metric[2] = metric[2] + 1
            for group in group_names:
                prediction = predict_group(fitted[(target, group)], groups[group], sample[0])
                if target == 0:
                    prediction = max(0.0, prediction)
                else:
                    prediction = min(1.0, max(0.0, prediction))
                error = sample[1][target] - prediction
                metric = metrics[(test_event, target, group)]
                metric[0] = metric[0] + error * error
                metric[1] = metric[1] + abs(error)
                metric[2] = metric[2] + 1

results = []
for target in range(label_count):
    baseline_by_event = {}
    for event in test_events:
        metric = metrics[(event, target, "baseline")]
        baseline_by_event[event] = metric[0] / metric[2]
    for model_name in ["baseline"] + group_names:
        event_values = []
        event_deltas = []
        total_squared = 0.0
        total_count = 0
        wins = 0
        for event in test_events:
            metric = metrics[(event, target, model_name)]
            mse = metric[0] / metric[2]
            event_values = event_values + [mse]
            event_deltas = event_deltas + [baseline_by_event[event] - mse]
            total_squared = total_squared + metric[0]
            total_count = total_count + metric[2]
            if mse < baseline_by_event[event]:
                wins = wins + 1
        results = results + [{
            "label": label_names[target],
            "model": model_name,
            "event_macro_mse": sum(event_values) / len(event_values),
            "observation_weighted_mse": total_squared / total_count,
            "early_event_macro_mse": sum(event_values[:8]) / 8.0,
            "late_event_macro_mse": sum(event_values[8:]) / 8.0,
            "event_mse_wins_vs_baseline": wins,
            "event_mse_improvement_vs_baseline": event_deltas,
            "prediction_count": total_count,
        }]

result = structured_return(
    "Final bounded activity-core compression trial on the unchanged six-hour sample.",
    {
        "parent_benchmark_source_sha256": "16fefb285aa33cc016deae54a18f9ee9542ba533f3c3f3b8c1a2b4abcddd7d91",
        "parent_attribution_source_sha256": "08cd78ffac3f553b311bfdb391b81a845d95296e377f496adcdc9d7fbe2448ea",
        "feature_names": feature_names,
        "feature_groups": groups,
        "label_names": label_names,
        "ridge_penalty": ridge_penalty,
        "development_sample_count": sum(event_counts[event] for event in event_counts),
        "excluded_irregular": excluded_irregular,
        "test_events": test_events,
        "results": results,
    },
    warnings=[
        "This is the final subset comparison allowed by the current packet trial budget.",
        "Every fitted mean, scale, and ridge coefficient uses equal-weighted earlier events only.",
        "The retained full-interaction comparator is benchmark 01 and is not rerun as a fresh trial.",
        "Magnitude and large-move forecasts do not imply direction or executable trading value.",
        "Protected values remain unavailable.",
    ],
)
