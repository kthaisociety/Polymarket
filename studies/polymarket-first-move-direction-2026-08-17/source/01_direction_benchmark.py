markets = read("polymarket-development-prices", "market_id")
events = read("polymarket-development-prices", "event_chronological_ordinal")
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
        weight = 1.0 / (event_count * len(rows))
        for row in rows:
            target_mean = target_mean + row[1] * weight
            for position in range(feature_count):
                means[position] = means[position] + row[0][feature_indices[position]] * weight
    scales = [0.0 for unused in feature_indices]
    for event in training_events:
        rows = samples[event]
        weight = 1.0 / (event_count * len(rows))
        for row in rows:
            for position in range(feature_count):
                centered = row[0][feature_indices[position]] - means[position]
                scales[position] = scales[position] + centered * centered * weight
    for position in range(feature_count):
        scales[position] = (scales[position] + 0.000000000001) ** 0.5
    matrix = [[0.0 for unused in feature_indices] for unused in feature_indices]
    vector = [0.0 for unused in feature_indices]
    for event in training_events:
        rows = samples[event]
        weight = 1.0 / (event_count * len(rows))
        for row in rows:
            standardized = [0.0 for unused in feature_indices]
            for position in range(feature_count):
                standardized[position] = (
                    row[0][feature_indices[position]] - means[position]
                ) / scales[position]
            centered_target = row[1] - target_mean
            for left in range(feature_count):
                vector[left] = vector[left] + standardized[left] * centered_target * weight
                for right in range(feature_count):
                    matrix[left][right] = (
                        matrix[left][right]
                        + standardized[left] * standardized[right] * weight
                    )
    for position in range(feature_count):
        matrix[position][position] = matrix[position][position] + penalty
    return [target_mean, means, scales, solve_linear(matrix, vector)]


def ridge_prediction(model, feature_indices, features):
    value = model[0]
    for position in range(len(feature_indices)):
        value = value + model[3][position] * (
            features[feature_indices[position]] - model[1][position]
        ) / model[2][position]
    return min(1.0, max(-1.0, value))


def event_equal_mean(samples, training_events):
    value = 0.0
    for event in training_events:
        value = value + sum(row[1] for row in samples[event]) / len(samples[event])
    return value / len(training_events)


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
    "signed_change_6h",
    "signed_change_24h",
    "latest_nonzero_step_sign_24h",
    "zero_change_fraction_24h",
    "log_one_plus_quiet_run_hours_005",
    "signed_change_6h_x_zero_fraction_24h",
    "latest_nonzero_sign_x_log_quiet_hours",
]
samples = {}
excluded_history_span = 0
excluded_six_hour_span = 0
excluded_future_coverage = 0
up_count = 0
down_count = 0
no_crossing_count = 0
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
                zero_count = 0.0
                latest_nonzero_sign = 0.0
                for trailing_ordinal in range(decision - 23, decision + 1):
                    step = (
                        points[(market, trailing_ordinal)][1]
                        - points[(market, trailing_ordinal - 1)][1]
                    )
                    if step == 0.0:
                        zero_count = zero_count + 1.0
                    else:
                        if step > 0.0:
                            latest_nonzero_sign = 1.0
                        else:
                            latest_nonzero_sign = -1.0
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
                zero_fraction = zero_count / 24.0
                log_quiet = log(1.0 + quiet_hours)
                signed_six = probability - six_hour[1]
                features = [
                    probability,
                    min(probability, 1.0 - probability),
                    log(clipped / (1.0 - clipped)),
                    signed_six,
                    probability - history[1],
                    latest_nonzero_sign,
                    zero_fraction,
                    log_quiet,
                    signed_six * zero_fraction,
                    latest_nonzero_sign * log_quiet,
                ]
                label = 0.0
                exit_probability = probability
                future_ordinal = decision + 1
                crossed = False
                while future_ordinal <= endpoint:
                    future = points[(market, future_ordinal)]
                    elapsed_hours = (future[0] - current[0]) / 3600.0
                    if elapsed_hours <= 48.0:
                        exit_probability = future[1]
                        displacement = future[1] - probability
                        if not crossed and abs(displacement) >= 0.02:
                            if displacement > 0.0:
                                label = 1.0
                            else:
                                label = -1.0
                            crossed = True
                            future_ordinal = endpoint + 1
                        else:
                            future_ordinal = future_ordinal + 1
                    else:
                        future_ordinal = endpoint + 1
                if label > 0.0:
                    up_count = up_count + 1
                elif label < 0.0:
                    down_count = down_count + 1
                else:
                    no_crossing_count = no_crossing_count + 1
                if event not in samples:
                    samples[event] = []
                samples[event] = samples[event] + [
                    [
                        features,
                        label,
                        market,
                        current[0],
                        points[(market, decision + 1)][1],
                        exit_probability,
                    ]
                ]
        next_decision_time = current[0] + 172800.0
        decision = decision + 1
        while decision < length and points[(market, decision)][0] < next_decision_time:
            decision = decision + 1

groups = {
    "zero": [],
    "earlier_event_mean": [],
    "state_only": [0, 1, 2],
    "state_direction": [0, 1, 2, 3, 4, 5],
    "direction_after_staleness": list(range(10)),
}


def evaluate_group(group_name, feature_indices):
    evaluated = []
    event_metrics = []
    for test_event in range(8, 24):
        if test_event in samples:
            training_events = [event for event in range(test_event) if event in samples]
            if len(training_events) >= 2:
                model = None
                mean_prediction = 0.0
                if group_name == "earlier_event_mean":
                    mean_prediction = event_equal_mean(samples, training_events)
                elif group_name != "zero":
                    model = fit_ridge(samples, training_events, feature_indices, 0.1)
                squared_sum = 0.0
                absolute_sum = 0.0
                crossing_count = 0
                correct_count = 0
                event_up = 0
                event_down = 0
                for row in samples[test_event]:
                    prediction = mean_prediction
                    if model is not None:
                        prediction = ridge_prediction(model, feature_indices, row[0])
                    error = row[1] - prediction
                    squared_error = error * error
                    absolute_error = abs(error)
                    squared_sum = squared_sum + squared_error
                    absolute_sum = absolute_sum + absolute_error
                    correct = False
                    if row[1] != 0.0:
                        crossing_count = crossing_count + 1
                        if row[1] > 0.0:
                            event_up = event_up + 1
                        else:
                            event_down = event_down + 1
                        if prediction * row[1] > 0.0:
                            correct = True
                            correct_count = correct_count + 1
                    evaluated = evaluated + [
                        [
                            test_event,
                            row[1],
                            prediction,
                            squared_error,
                            absolute_error,
                            correct,
                            row[4],
                            row[5],
                        ]
                    ]
                direction_accuracy = None
                if crossing_count > 0:
                    direction_accuracy = correct_count / crossing_count
                event_metrics = event_metrics + [
                    {
                        "event": test_event,
                        "row_count": len(samples[test_event]),
                        "mse": squared_sum / len(samples[test_event]),
                        "mae": absolute_sum / len(samples[test_event]),
                        "crossing_count": crossing_count,
                        "up_count": event_up,
                        "down_count": event_down,
                        "direction_accuracy": direction_accuracy,
                    }
                ]
    squared_errors = [row[3] for row in evaluated]
    absolute_errors = [row[4] for row in evaluated]
    crossing_rows = [row for row in evaluated if row[1] != 0.0]
    midpoint = len(event_metrics) // 2
    return {
        "group": group_name,
        "feature_names": [feature_names[index] for index in feature_indices],
        "test_event_count": len(event_metrics),
        "test_row_count": len(evaluated),
        "observation_mse": sum(squared_errors) / len(squared_errors),
        "observation_mae": sum(absolute_errors) / len(absolute_errors),
        "event_macro_mse": sum(row["mse"] for row in event_metrics) / len(event_metrics),
        "event_macro_mae": sum(row["mae"] for row in event_metrics) / len(event_metrics),
        "early_event_macro_mse": sum(row["mse"] for row in event_metrics[:midpoint])
        / midpoint,
        "late_event_macro_mse": sum(row["mse"] for row in event_metrics[midpoint:])
        / (len(event_metrics) - midpoint),
        "mean_prediction": sum(row[2] for row in evaluated) / len(evaluated),
        "mean_label": sum(row[1] for row in evaluated) / len(evaluated),
        "crossing_count": len(crossing_rows),
        "crossing_direction_accuracy": sum(1 for row in crossing_rows if row[5])
        / len(crossing_rows),
        "event_metrics": event_metrics,
        "evaluated": evaluated,
    }


results = []
for group_name in groups:
    results = results + [evaluate_group(group_name, groups[group_name])]
by_group = {}
for item in results:
    by_group[item["group"]] = item

state = by_group["state_only"]
direction = by_group["state_direction"]
candidate = by_group["direction_after_staleness"]
comparators = [
    by_group["zero"],
    by_group["earlier_event_mean"],
    state,
    direction,
]
state_by_event = {row["event"]: row for row in state["event_metrics"]}
candidate_event_wins = 0
positive_improvements = []
mixed_direction_events = 0
oof_up_count = 0
oof_down_count = 0
for row in candidate["event_metrics"]:
    state_row = state_by_event[row["event"]]
    if row["mse"] < state_row["mse"]:
        candidate_event_wins = candidate_event_wins + 1
    positive_improvements = positive_improvements + [max(0.0, state_row["mse"] - row["mse"])]
    oof_up_count = oof_up_count + row["up_count"]
    oof_down_count = oof_down_count + row["down_count"]
    if row["up_count"] > 0 and row["down_count"] > 0:
        mixed_direction_events = mixed_direction_events + 1
positive_total = sum(positive_improvements)
largest_positive_share = 0.0
if positive_total > 0.0:
    largest_positive_share = max(positive_improvements) / positive_total

candidate_trade_rows = [row for row in candidate["evaluated"] if row[2] > 0.10]
trade_events = {}
for row in candidate_trade_rows:
    event = row[0]
    net = row[7] - row[6] - 0.01
    if event not in trade_events:
        trade_events[event] = []
    trade_events[event] = trade_events[event] + [net]
trade_event_means = []
for event in sorted(trade_events):
    trade_event_means = trade_event_means + [
        [event, sum(trade_events[event]) / len(trade_events[event]), len(trade_events[event])]
    ]
trade_observation_mean = None
trade_event_mean = None
trade_positive_event_share = None
leave_one_event_out_minimum = None
if len(candidate_trade_rows) > 0:
    all_trade_nets = []
    for event in trade_events:
        all_trade_nets = all_trade_nets + trade_events[event]
    trade_observation_mean = sum(all_trade_nets) / len(all_trade_nets)
    trade_event_mean = sum(row[1] for row in trade_event_means) / len(trade_event_means)
    trade_positive_event_share = sum(1 for row in trade_event_means if row[1] > 0.0) / len(
        trade_event_means
    )
    leave_one_values = []
    if len(trade_event_means) > 1:
        for omitted in range(len(trade_event_means)):
            leave_one_values = leave_one_values + [
                sum(
                    trade_event_means[position][1]
                    for position in range(len(trade_event_means))
                    if position != omitted
                )
                / (len(trade_event_means) - 1)
            ]
        leave_one_event_out_minimum = min(leave_one_values)

predictive_gate_passed = (
    candidate["test_row_count"] >= 500
    and oof_up_count >= 100
    and oof_down_count >= 100
    and mixed_direction_events >= 10
    and all(candidate["observation_mse"] < comparator["observation_mse"] for comparator in comparators)
    and all(candidate["event_macro_mse"] < comparator["event_macro_mse"] for comparator in comparators)
    and candidate["early_event_macro_mse"] < state["early_event_macro_mse"]
    and candidate["late_event_macro_mse"] < state["late_event_macro_mse"]
    and candidate_event_wins * 5 >= candidate["test_event_count"] * 3
    and candidate["crossing_direction_accuracy"] >= 0.55
    and candidate["crossing_direction_accuracy"]
    >= state["crossing_direction_accuracy"] + 0.03
    and abs(candidate["mean_prediction"] - candidate["mean_label"]) <= 0.10
    and largest_positive_share <= 0.50
)

execution_falsifier_passed = (
    len(candidate_trade_rows) >= 100
    and trade_observation_mean is not None
    and trade_observation_mean > 0.0
    and trade_event_mean is not None
    and trade_event_mean > 0.0
    and trade_positive_event_share is not None
    and trade_positive_event_share >= 0.60
    and leave_one_event_out_minimum is not None
    and leave_one_event_out_minimum > 0.0
)

for item in results:
    del item["evaluated"]

result = structured_return(
    "Chronological benchmark for signed 48-hour sampled first passage.",
    {
        "schema_version": "polymarket-first-move-direction/v1",
        "label": "first sampled two-cent crossing direction within 48 elapsed hours: -1 down, 0 none, +1 up",
        "decision_rule": "greedy decisions at least 48 elapsed hours apart after 24-observation warmup",
        "sample_count": sum(len(samples[event]) for event in samples),
        "sample_event_count": len(samples),
        "all_sample_up_count": up_count,
        "all_sample_down_count": down_count,
        "all_sample_no_crossing_count": no_crossing_count,
        "oof_up_count": oof_up_count,
        "oof_down_count": oof_down_count,
        "oof_mixed_direction_event_count": mixed_direction_events,
        "excluded_history_span": excluded_history_span,
        "excluded_six_hour_span": excluded_six_hour_span,
        "excluded_future_coverage": excluded_future_coverage,
        "ridge_penalty": 0.1,
        "results": results,
        "candidate_event_wins_vs_state": candidate_event_wins,
        "largest_positive_state_relative_mse_improvement_share": largest_positive_share,
        "predictive_gate_passed": predictive_gate_passed,
        "delayed_long_only_cost_falsifier": {
            "prediction_threshold": 0.10,
            "round_trip_cost": 0.01,
            "trade_count": len(candidate_trade_rows),
            "represented_event_count": len(trade_event_means),
            "observation_mean_net_sampled_change": trade_observation_mean,
            "event_macro_mean_net_sampled_change": trade_event_mean,
            "positive_event_share": trade_positive_event_share,
            "leave_one_event_out_minimum": leave_one_event_out_minimum,
            "event_metrics": [
                {"event": row[0], "mean_net_sampled_change": row[1], "trade_count": row[2]}
                for row in trade_event_means
            ],
            "passed": execution_falsifier_passed,
        },
        "protected_values_exposed": False,
    },
    warnings=[
        "The signed first-passage label and all gates were fixed before this source read development values.",
        "Sampled crossing direction is not continuous-time passage or executable-price evidence.",
        "The long-only diagnostic uses delayed retained samples, not historical bid/ask quotes or fills.",
        "Non-overlapping within-market windows do not make same-event contracts independent.",
        "Passing prediction would authorize one formal replay only; protected values remain unavailable.",
    ],
)
