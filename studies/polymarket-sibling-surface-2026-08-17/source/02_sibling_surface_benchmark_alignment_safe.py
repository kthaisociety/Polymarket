markets = read("polymarket-development-prices", "market_id")
events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")


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
                    augmented[row][column] = (
                        augmented[row][column] - factor * augmented[pivot][column]
                    )
    return [augmented[row][size] for row in range(size)]


def fit_ridge(samples, training_events, feature_indices, target_index, penalty):
    feature_count = len(feature_indices)
    event_count = len(training_events)
    means = [0.0 for unused in feature_indices]
    target_mean = 0.0
    for event in training_events:
        rows = samples[event]
        row_weight = 1.0 / (event_count * len(rows))
        for row in rows:
            target_mean = target_mean + row[1][target_index] * row_weight
            for position in range(feature_count):
                means[position] = (
                    means[position] + row[0][feature_indices[position]] * row_weight
                )
    scales = [0.0 for unused in feature_indices]
    for event in training_events:
        rows = samples[event]
        row_weight = 1.0 / (event_count * len(rows))
        for row in rows:
            for position in range(feature_count):
                centered = row[0][feature_indices[position]] - means[position]
                scales[position] = scales[position] + centered * centered * row_weight
    for position in range(feature_count):
        scales[position] = (scales[position] + 0.000000000001) ** 0.5
    matrix = [None for unused in feature_indices]
    vector = [0.0 for unused in feature_indices]
    for left in range(feature_count):
        matrix[left] = [0.0 for unused in feature_indices]
    for event in training_events:
        rows = samples[event]
        row_weight = 1.0 / (event_count * len(rows))
        for row in rows:
            standardized = [0.0 for unused in feature_indices]
            for position in range(feature_count):
                standardized[position] = (
                    row[0][feature_indices[position]] - means[position]
                ) / scales[position]
            centered_target = row[1][target_index] - target_mean
            for left in range(feature_count):
                vector[left] = (
                    vector[left] + standardized[left] * centered_target * row_weight
                )
                for right in range(feature_count):
                    matrix[left][right] = (
                        matrix[left][right]
                        + standardized[left] * standardized[right] * row_weight
                    )
    for position in range(feature_count):
        matrix[position][position] = matrix[position][position] + penalty
    return [target_mean, means, scales, solve_linear(matrix, vector)]


def predict(model, feature_indices, features):
    value = model[0]
    for position in range(len(feature_indices)):
        value = value + model[3][position] * (
            features[feature_indices[position]] - model[1][position]
        ) / model[2][position]
    return value


def latest_ordinal(points, lengths, market, start_ordinal, cutoff):
    ordinal = min(start_ordinal, lengths[market] - 1)
    while ordinal >= 0 and points[(market, ordinal)][0] > cutoff:
        ordinal = ordinal - 1
    if ordinal >= 0:
        while (
            ordinal + 1 < lengths[market]
            and points[(market, ordinal + 1)][0] <= cutoff
        ):
            ordinal = ordinal + 1
    return ordinal


points = {}
lengths = {}
market_events = {}
event_markets = {}
for row in range(len(markets)):
    market = markets[row]
    event = events[row]
    points[(market, ordinals[row])] = [times[row], probabilities[row]]
    if market not in lengths:
        lengths[market] = 0
        market_events[market] = event
        if event not in event_markets:
            event_markets[event] = []
        event_markets[event] = event_markets[event] + [market]
    lengths[market] = max(lengths[market], ordinals[row] + 1)

samples = {}
excluded_target_window = 0
excluded_single_market_event = 0
excluded_sibling_alignment = 0
for market in lengths:
    event = market_events[market]
    siblings = [item for item in event_markets[event] if item != market]
    if len(siblings) == 0:
        excluded_single_market_event = excluded_single_market_event + 1
    else:
        for decision in range(24, lengths[market] - 6, 6):
            current = points[(market, decision)]
            trailing = points[(market, decision - 24)]
            future = points[(market, decision + 6)]
            trailing_hours = (current[0] - trailing[0]) / 3600.0
            future_hours = (future[0] - current[0]) / 3600.0
            if (
                trailing_hours < 18.0
                or trailing_hours > 30.0
                or future_hours < 4.5
                or future_hours > 7.5
            ):
                excluded_target_window = excluded_target_window + 1
            else:
                sibling_values = []
                sibling_changes = []
                alignment_legal = True
                trailing_cutoff = current[0] - 21600.0
                for sibling in siblings:
                    sibling_now_ordinal = latest_ordinal(
                        points, lengths, sibling, decision, current[0]
                    )
                    sibling_then_ordinal = latest_ordinal(
                        points,
                        lengths,
                        sibling,
                        sibling_now_ordinal - 6,
                        trailing_cutoff,
                    )
                    if sibling_now_ordinal < 0 or sibling_then_ordinal < 0:
                        alignment_legal = False
                    else:
                        sibling_now = points[(sibling, sibling_now_ordinal)]
                        sibling_then = points[(sibling, sibling_then_ordinal)]
                        now_staleness = (current[0] - sibling_now[0]) / 3600.0
                        then_staleness = (trailing_cutoff - sibling_then[0]) / 3600.0
                        sibling_span = (sibling_now[0] - sibling_then[0]) / 3600.0
                        if (
                            now_staleness < 0.0
                            or now_staleness > 2.0
                            or then_staleness < 0.0
                            or then_staleness > 2.0
                            or sibling_span < 4.5
                            or sibling_span > 7.5
                        ):
                            alignment_legal = False
                        else:
                            sibling_values = sibling_values + [sibling_now[1]]
                            sibling_changes = sibling_changes + [
                                sibling_now[1] - sibling_then[1]
                            ]
                if not alignment_legal or len(sibling_values) != len(siblings):
                    excluded_sibling_alignment = excluded_sibling_alignment + 1
                else:
                    probability = current[1]
                    change6 = probability - points[(market, decision - 6)][1]
                    rv6 = 0.0
                    zero_count = 0.0
                    absolute_sum = 0.0
                    for ordinal in range(decision - 23, decision + 1):
                        step = points[(market, ordinal)][1] - points[(market, ordinal - 1)][1]
                        absolute_step = abs(step)
                        absolute_sum = absolute_sum + absolute_step
                        if ordinal >= decision - 5:
                            rv6 = rv6 + step * step
                        if absolute_step == 0.0:
                            zero_count = zero_count + 1.0
                    sibling_mean = sum(sibling_values) / len(sibling_values)
                    sibling_change_mean = sum(sibling_changes) / len(sibling_changes)
                    sibling_variance = 0.0
                    target_rank = 0.0
                    max_absolute_sibling_change = 0.0
                    for value in sibling_values:
                        sibling_variance = sibling_variance + (
                            value - sibling_mean
                        ) ** 2 / len(sibling_values)
                        if value < probability:
                            target_rank = target_rank + 1.0
                    for value in sibling_changes:
                        max_absolute_sibling_change = max(
                            max_absolute_sibling_change, abs(value)
                        )
                    features = [
                        probability,
                        min(probability, 1.0 - probability),
                        change6,
                        rv6,
                        zero_count / 24.0,
                        absolute_sum / 24.0,
                        float(len(sibling_values)),
                        sibling_mean,
                        max(sibling_values),
                        min(sibling_values),
                        sibling_variance ** 0.5,
                        sum(sibling_values),
                        probability - sibling_mean,
                        target_rank / len(sibling_values),
                        sibling_change_mean,
                        max_absolute_sibling_change,
                        sum(abs(value) for value in sibling_changes) / len(sibling_changes),
                    ]
                    signed = future[1] - probability
                    targets = [
                        signed,
                        abs(signed),
                        1.0 if abs(signed) >= 0.02 else 0.0,
                    ]
                    if event not in samples:
                        samples[event] = []
                    samples[event] = samples[event] + [[features, targets]]

baseline_indices = [0, 1, 2, 3, 4, 5]
augmented_indices = list(range(17))
label_names = ["signed_change_6h", "absolute_change_6h", "large_move_002"]
results = []
for target_index in range(3):
    event_metrics = []
    observation_baseline_squared = []
    observation_augmented_squared = []
    observation_naive_squared = []
    baseline_direction_correct = 0
    augmented_direction_correct = 0
    directional_count = 0
    for test_event in range(8, 24):
        if test_event in samples:
            training_events = [
                event for event in range(test_event) if event in samples
            ]
            if len(training_events) >= 2:
                baseline_model = fit_ridge(
                    samples, training_events, baseline_indices, target_index, 0.1
                )
                augmented_model = fit_ridge(
                    samples, training_events, augmented_indices, target_index, 0.1
                )
                naive = 0.0
                if target_index > 0:
                    for event in training_events:
                        event_sum = 0.0
                        for row in samples[event]:
                            event_sum = event_sum + row[1][target_index]
                        naive = naive + event_sum / len(samples[event])
                    naive = naive / len(training_events)
                baseline_sum = 0.0
                augmented_sum = 0.0
                naive_sum = 0.0
                for row in samples[test_event]:
                    actual = row[1][target_index]
                    baseline_prediction = predict(
                        baseline_model, baseline_indices, row[0]
                    )
                    augmented_prediction = predict(
                        augmented_model, augmented_indices, row[0]
                    )
                    if target_index > 0:
                        baseline_prediction = min(1.0, max(0.0, baseline_prediction))
                        augmented_prediction = min(1.0, max(0.0, augmented_prediction))
                    baseline_error = (actual - baseline_prediction) ** 2
                    augmented_error = (actual - augmented_prediction) ** 2
                    naive_error = (actual - naive) ** 2
                    baseline_sum = baseline_sum + baseline_error
                    augmented_sum = augmented_sum + augmented_error
                    naive_sum = naive_sum + naive_error
                    observation_baseline_squared = (
                        observation_baseline_squared + [baseline_error]
                    )
                    observation_augmented_squared = (
                        observation_augmented_squared + [augmented_error]
                    )
                    observation_naive_squared = observation_naive_squared + [naive_error]
                    if target_index == 0 and actual != 0.0:
                        directional_count = directional_count + 1
                        if baseline_prediction * actual > 0.0:
                            baseline_direction_correct = baseline_direction_correct + 1
                        if augmented_prediction * actual > 0.0:
                            augmented_direction_correct = augmented_direction_correct + 1
                count = len(samples[test_event])
                event_metrics = event_metrics + [
                    {
                        "event": test_event,
                        "row_count": count,
                        "baseline_mse": baseline_sum / count,
                        "augmented_mse": augmented_sum / count,
                        "naive_mse": naive_sum / count,
                    }
                ]
    event_count = len(event_metrics)
    baseline_observation_mse = sum(observation_baseline_squared) / len(
        observation_baseline_squared
    )
    augmented_observation_mse = sum(observation_augmented_squared) / len(
        observation_augmented_squared
    )
    naive_observation_mse = sum(observation_naive_squared) / len(
        observation_naive_squared
    )
    baseline_macro_mse = sum(row["baseline_mse"] for row in event_metrics) / event_count
    augmented_macro_mse = sum(row["augmented_mse"] for row in event_metrics) / event_count
    naive_macro_mse = sum(row["naive_mse"] for row in event_metrics) / event_count
    wins = sum(
        1 for row in event_metrics if row["augmented_mse"] < row["baseline_mse"]
    )
    midpoint = event_count // 2
    early_baseline = sum(row["baseline_mse"] for row in event_metrics[:midpoint]) / midpoint
    early_augmented = sum(row["augmented_mse"] for row in event_metrics[:midpoint]) / midpoint
    late_count = event_count - midpoint
    late_baseline = sum(row["baseline_mse"] for row in event_metrics[midpoint:]) / late_count
    late_augmented = sum(row["augmented_mse"] for row in event_metrics[midpoint:]) / late_count
    positive_improvements = [
        max(0.0, row["baseline_mse"] - row["augmented_mse"])
        for row in event_metrics
    ]
    positive_total = sum(positive_improvements)
    largest_share = 0.0
    if positive_total > 0.0:
        largest_share = max(positive_improvements) / positive_total
    baseline_direction = 0.0
    augmented_direction = 0.0
    if directional_count > 0:
        baseline_direction = baseline_direction_correct / directional_count
        augmented_direction = augmented_direction_correct / directional_count
    passed = (
        event_count >= 12
        and augmented_observation_mse < baseline_observation_mse
        and augmented_macro_mse < baseline_macro_mse
        and augmented_observation_mse < naive_observation_mse
        and augmented_macro_mse < naive_macro_mse
        and early_augmented < early_baseline
        and late_augmented < late_baseline
        and wins * 5 >= event_count * 3
        and largest_share <= 0.5
    )
    if target_index == 0:
        passed = (
            passed
            and augmented_direction > 0.5
            and augmented_direction > baseline_direction
        )
    results = results + [
        {
            "label": label_names[target_index],
            "test_event_count": event_count,
            "test_row_count": len(observation_augmented_squared),
            "baseline_observation_mse": baseline_observation_mse,
            "augmented_observation_mse": augmented_observation_mse,
            "naive_observation_mse": naive_observation_mse,
            "baseline_event_macro_mse": baseline_macro_mse,
            "augmented_event_macro_mse": augmented_macro_mse,
            "naive_event_macro_mse": naive_macro_mse,
            "early_baseline_mse": early_baseline,
            "early_augmented_mse": early_augmented,
            "late_baseline_mse": late_baseline,
            "late_augmented_mse": late_augmented,
            "event_wins": wins,
            "largest_positive_improvement_share": largest_share,
            "baseline_directional_accuracy": baseline_direction,
            "augmented_directional_accuracy": augmented_direction,
            "predeclared_gate_passed": passed,
            "event_metrics": event_metrics,
        }
    ]

result = structured_return(
    "Same-event sibling probability-surface benchmark completed.",
    {
        "schema_version": "polymarket-sibling-surface-benchmark/v1",
        "sample_event_count": len(samples),
        "sample_count": sum(len(samples[event]) for event in samples),
        "excluded_target_window": excluded_target_window,
        "excluded_single_market_event": excluded_single_market_event,
        "excluded_sibling_alignment": excluded_sibling_alignment,
        "baseline_feature_count": len(baseline_indices),
        "augmented_feature_count": len(augmented_indices),
        "ridge_penalty": 0.1,
        "results": results,
        "protected_values_exposed": False,
        "mutual_exclusivity_assumed": False,
    },
)
