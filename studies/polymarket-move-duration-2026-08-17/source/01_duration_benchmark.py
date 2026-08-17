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


def fit_ridge(samples, training_events, feature_indices, penalty):
    feature_count = len(feature_indices)
    event_count = len(training_events)
    means = [0.0 for unused in feature_indices]
    target_mean = 0.0
    for event in training_events:
        rows = samples[event]
        row_weight = 1.0 / (event_count * len(rows))
        for row in rows:
            target_mean = target_mean + row[1] * row_weight
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
            centered_target = row[1] - target_mean
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
    return min(1.0, max(0.0, value))


points = {}
lengths = {}
market_events = {}
for row in range(len(markets)):
    market = markets[row]
    points[(market, ordinals[row])] = [times[row], probabilities[row]]
    if market not in lengths:
        lengths[market] = 0
        market_events[market] = events[row]
    lengths[market] = max(lengths[market], ordinals[row] + 1)

feature_names = [
    "probability_level",
    "boundary_distance",
    "winsorized_logit_level_005",
    "realized_variance_6h",
    "realized_variance_24h",
    "zero_change_fraction_24h",
    "mean_absolute_change_24h",
    "maximum_absolute_change_24h",
    "signed_change_6h",
    "log_one_plus_quiet_run_hours_005",
]
samples = {}
excluded_history_span = 0
excluded_six_hour_span = 0
excluded_future_coverage = 0
crossing_count = 0
capped_count = 0
for market in lengths:
    length = lengths[market]
    event = market_events[market]
    decision = 24
    while decision < length - 1:
        current = points[(market, decision)]
        history = points[(market, decision - 24)]
        six_hour = points[(market, decision - 6)]
        history_hours = (current[0] - history[0]) / 3600.0
        six_hour_span = (current[0] - six_hour[0]) / 3600.0
        endpoint = decision + 1
        while endpoint < length and points[(market, endpoint)][0] < current[0] + 172800.0:
            endpoint = endpoint + 1
        if history_hours < 18.0 or history_hours > 30.0:
            excluded_history_span = excluded_history_span + 1
        elif six_hour_span < 4.5 or six_hour_span > 7.5:
            excluded_six_hour_span = excluded_six_hour_span + 1
        elif endpoint >= length:
            excluded_future_coverage = excluded_future_coverage + 1
        else:
            endpoint_hours = (points[(market, endpoint)][0] - current[0]) / 3600.0
            if endpoint_hours < 42.0 or endpoint_hours > 54.0:
                excluded_future_coverage = excluded_future_coverage + 1
            else:
                probability = current[1]
                clipped = min(0.995, max(0.005, probability))
                rv6 = 0.0
                rv24 = 0.0
                zero_count = 0.0
                absolute_sum = 0.0
                maximum_step = 0.0
                for ordinal in range(decision - 23, decision + 1):
                    step = points[(market, ordinal)][1] - points[(market, ordinal - 1)][1]
                    absolute_step = abs(step)
                    rv24 = rv24 + step * step
                    absolute_sum = absolute_sum + absolute_step
                    maximum_step = max(maximum_step, absolute_step)
                    if absolute_step == 0.0:
                        zero_count = zero_count + 1.0
                    if ordinal >= decision - 5:
                        rv6 = rv6 + step * step
                quiet_start = decision
                quiet_ordinal = decision
                while quiet_ordinal > decision - 24:
                    quiet_step = abs(
                        points[(market, quiet_ordinal)][1]
                        - points[(market, quiet_ordinal - 1)][1]
                    )
                    if quiet_step >= 0.005:
                        quiet_ordinal = decision - 24
                    else:
                        quiet_start = quiet_ordinal - 1
                        quiet_ordinal = quiet_ordinal - 1
                quiet_hours = (current[0] - points[(market, quiet_start)][0]) / 3600.0
                features = [
                    probability,
                    min(probability, 1.0 - probability),
                    log(clipped / (1.0 - clipped)),
                    rv6,
                    rv24,
                    zero_count / 24.0,
                    absolute_sum / 24.0,
                    maximum_step,
                    probability - six_hour[1],
                    log(1.0 + quiet_hours),
                ]
                crossing_hours = 48.0
                future_ordinal = decision + 1
                crossed = False
                while future_ordinal <= endpoint:
                    elapsed_hours = (
                        points[(market, future_ordinal)][0] - current[0]
                    ) / 3600.0
                    if elapsed_hours <= 48.0 and abs(
                        points[(market, future_ordinal)][1] - probability
                    ) >= 0.02:
                        crossing_hours = elapsed_hours
                        crossed = True
                        future_ordinal = endpoint + 1
                    else:
                        future_ordinal = future_ordinal + 1
                if crossed:
                    crossing_count = crossing_count + 1
                else:
                    capped_count = capped_count + 1
                if event not in samples:
                    samples[event] = []
                samples[event] = samples[event] + [
                    [features, min(1.0, max(0.0, crossing_hours / 48.0)), crossed]
                ]
        next_decision_time = current[0] + 172800.0
        decision = decision + 1
        while decision < length and points[(market, decision)][0] < next_decision_time:
            decision = decision + 1

groups = {
    "state_only": [0, 1, 2],
    "path_persistence": list(range(10)),
}
group_results = []
baseline_event_metrics = []
baseline_absolute_errors = []
baseline_squared_errors = []
for test_event in range(8, 24):
    if test_event in samples:
        training_events = [event for event in range(test_event) if event in samples]
        if len(training_events) >= 2:
            baseline = 0.0
            for event in training_events:
                baseline = baseline + sum(row[1] for row in samples[event]) / len(samples[event])
            baseline = baseline / len(training_events)
            absolute_sum = 0.0
            squared_sum = 0.0
            event_crossings = 0
            for row in samples[test_event]:
                error = row[1] - baseline
                absolute_sum = absolute_sum + abs(error)
                squared_sum = squared_sum + error * error
                baseline_absolute_errors = baseline_absolute_errors + [abs(error)]
                baseline_squared_errors = baseline_squared_errors + [error * error]
                if row[2]:
                    event_crossings = event_crossings + 1
            baseline_event_metrics = baseline_event_metrics + [
                {
                    "event": test_event,
                    "row_count": len(samples[test_event]),
                    "uncapped_crossing_count": event_crossings,
                    "mae": absolute_sum / len(samples[test_event]),
                    "mse": squared_sum / len(samples[test_event]),
                }
            ]

for group_name in groups:
    feature_indices = groups[group_name]
    event_metrics = []
    absolute_errors = []
    squared_errors = []
    for test_event in range(8, 24):
        if test_event in samples:
            training_events = [event for event in range(test_event) if event in samples]
            if len(training_events) >= 2:
                model = fit_ridge(samples, training_events, feature_indices, 0.1)
                absolute_sum = 0.0
                squared_sum = 0.0
                for row in samples[test_event]:
                    prediction = predict(model, feature_indices, row[0])
                    error = row[1] - prediction
                    absolute_sum = absolute_sum + abs(error)
                    squared_sum = squared_sum + error * error
                    absolute_errors = absolute_errors + [abs(error)]
                    squared_errors = squared_errors + [error * error]
                event_metrics = event_metrics + [
                    {
                        "event": test_event,
                        "row_count": len(samples[test_event]),
                        "mae": absolute_sum / len(samples[test_event]),
                        "mse": squared_sum / len(samples[test_event]),
                    }
                ]
    midpoint = len(event_metrics) // 2
    group_results = group_results + [
        {
            "group": group_name,
            "feature_names": [feature_names[index] for index in feature_indices],
            "test_event_count": len(event_metrics),
            "test_row_count": len(absolute_errors),
            "observation_mae": sum(absolute_errors) / len(absolute_errors),
            "observation_mse": sum(squared_errors) / len(squared_errors),
            "event_macro_mae": sum(row["mae"] for row in event_metrics) / len(event_metrics),
            "event_macro_mse": sum(row["mse"] for row in event_metrics) / len(event_metrics),
            "early_event_macro_mae": sum(row["mae"] for row in event_metrics[:midpoint]) / midpoint,
            "late_event_macro_mae": sum(row["mae"] for row in event_metrics[midpoint:]) / (len(event_metrics) - midpoint),
            "event_metrics": event_metrics,
        }
    ]

baseline_midpoint = len(baseline_event_metrics) // 2
baseline_result = {
    "model": "earlier_event_equal_mean_duration",
    "test_event_count": len(baseline_event_metrics),
    "test_row_count": len(baseline_absolute_errors),
    "observation_mae": sum(baseline_absolute_errors) / len(baseline_absolute_errors),
    "observation_mse": sum(baseline_squared_errors) / len(baseline_squared_errors),
    "event_macro_mae": sum(row["mae"] for row in baseline_event_metrics) / len(baseline_event_metrics),
    "event_macro_mse": sum(row["mse"] for row in baseline_event_metrics) / len(baseline_event_metrics),
    "early_event_macro_mae": sum(row["mae"] for row in baseline_event_metrics[:baseline_midpoint]) / baseline_midpoint,
    "late_event_macro_mae": sum(row["mae"] for row in baseline_event_metrics[baseline_midpoint:]) / (len(baseline_event_metrics) - baseline_midpoint),
    "event_metrics": baseline_event_metrics,
}

by_group = {}
for item in group_results:
    by_group[item["group"]] = item
state = by_group["state_only"]
candidate = by_group["path_persistence"]
event_wins = 0
positive_improvements = []
mixed_test_events = 0
oof_crossings = 0
for position in range(len(candidate["event_metrics"])):
    candidate_event = candidate["event_metrics"][position]
    state_event = state["event_metrics"][position]
    baseline_event = baseline_event_metrics[position]
    assert candidate_event["event"] == state_event["event"]
    assert candidate_event["event"] == baseline_event["event"]
    if candidate_event["mae"] < state_event["mae"]:
        event_wins = event_wins + 1
    positive_improvements = positive_improvements + [
        max(0.0, state_event["mae"] - candidate_event["mae"])
    ]
    oof_crossings = oof_crossings + baseline_event["uncapped_crossing_count"]
    if (
        baseline_event["uncapped_crossing_count"] > 0
        and baseline_event["uncapped_crossing_count"] < baseline_event["row_count"]
    ):
        mixed_test_events = mixed_test_events + 1
positive_total = sum(positive_improvements)
largest_positive_share = 0.0
if positive_total > 0.0:
    largest_positive_share = max(positive_improvements) / positive_total

gate_passed = (
    candidate["test_row_count"] >= 500
    and oof_crossings >= 100
    and mixed_test_events >= 10
    and candidate["observation_mae"] < baseline_result["observation_mae"]
    and candidate["observation_mse"] < baseline_result["observation_mse"]
    and candidate["event_macro_mae"] < baseline_result["event_macro_mae"]
    and candidate["event_macro_mse"] < baseline_result["event_macro_mse"]
    and candidate["observation_mae"] < state["observation_mae"]
    and candidate["observation_mse"] < state["observation_mse"]
    and candidate["event_macro_mae"] < state["event_macro_mae"]
    and candidate["event_macro_mse"] < state["event_macro_mse"]
    and candidate["event_macro_mae"] <= 0.95 * state["event_macro_mae"]
    and candidate["early_event_macro_mae"] < state["early_event_macro_mae"]
    and candidate["late_event_macro_mae"] < state["late_event_macro_mae"]
    and event_wins * 5 >= candidate["test_event_count"] * 3
    and largest_positive_share <= 0.5
)

result = structured_return(
    "Non-overlapping time-to-next-move benchmark completed.",
    {
        "schema_version": "polymarket-time-to-next-move/v1",
        "label": "elapsed hours to first sampled absolute displacement >= 0.02, capped at 48 hours and normalized by 48",
        "decision_rule": "greedy decisions at least 48 elapsed hours apart after 24-observation warmup",
        "sample_count": sum(len(samples[event]) for event in samples),
        "sample_event_count": len(samples),
        "all_sample_uncapped_crossing_count": crossing_count,
        "all_sample_capped_count": capped_count,
        "oof_uncapped_crossing_count": oof_crossings,
        "oof_mixed_test_event_count": mixed_test_events,
        "excluded_history_span": excluded_history_span,
        "excluded_six_hour_span": excluded_six_hour_span,
        "excluded_future_coverage": excluded_future_coverage,
        "ridge_penalty": 0.1,
        "baseline": baseline_result,
        "group_results": group_results,
        "path_persistence_event_wins_vs_state": event_wins,
        "largest_positive_mae_improvement_share": largest_positive_share,
        "predeclared_gate_passed": gate_passed,
        "protected_values_exposed": False,
    },
    warnings=[
        "Sampled first passage is not continuous-time first passage or executable-price evidence.",
        "The 48-hour cap turns unresolved durations into an administrative restricted-mean endpoint, not known event times.",
        "All thresholds, features, folds, and gates were fixed before inspecting this receipt.",
    ],
)
