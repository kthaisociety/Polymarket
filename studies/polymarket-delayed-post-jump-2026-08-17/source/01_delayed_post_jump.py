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


def event_equal_mean(samples, training_events):
    value = 0.0
    for event in training_events:
        value = value + sum(row[1] for row in samples[event]) / len(samples[event])
    return value / len(training_events)


def fit_ridge(samples, training_events, feature_indices, penalty):
    feature_count = len(feature_indices)
    event_count = len(training_events)
    means = [0.0 for unused in feature_indices]
    target_mean = event_equal_mean(samples, training_events)
    for event in training_events:
        weight = 1.0 / (event_count * len(samples[event]))
        for row in samples[event]:
            for position in range(feature_count):
                means[position] = means[position] + row[0][feature_indices[position]] * weight
    scales = [0.0 for unused in feature_indices]
    for event in training_events:
        weight = 1.0 / (event_count * len(samples[event]))
        for row in samples[event]:
            for position in range(feature_count):
                centered = row[0][feature_indices[position]] - means[position]
                scales[position] = scales[position] + centered * centered * weight
    for position in range(feature_count):
        scales[position] = (scales[position] + 0.000000000001) ** 0.5
    matrix = [[0.0 for unused in feature_indices] for unused in feature_indices]
    vector = [0.0 for unused in feature_indices]
    for event in training_events:
        weight = 1.0 / (event_count * len(samples[event]))
        for row in samples[event]:
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
                        matrix[left][right] + standardized[left] * standardized[right] * weight
                    )
    for position in range(feature_count):
        matrix[position][position] = matrix[position][position] + penalty
    return [target_mean, means, scales, solve_linear(matrix, vector)]


def ridge_prediction(model, feature_indices, features):
    value = model[0]
    for position in range(len(feature_indices)):
        value = (
            value
            + model[3][position]
            * (features[feature_indices[position]] - model[1][position])
            / model[2][position]
        )
    return min(1.0, max(-1.0, value))


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
    "delayed_entry_probability",
    "boundary_distance",
    "winsorized_logit_level_005",
    "signed_shock_size",
    "absolute_shock_size",
    "entry_slippage",
    "pre_shock_zero_fraction_23",
    "log_one_plus_pre_shock_quiet_hours_005",
    "pre_shock_mean_absolute_step_23",
    "signed_shock_x_zero_fraction",
    "shock_sign_x_log_quiet_hours",
]

samples = {}
excluded_shock_gap = 0
excluded_history_span = 0
excluded_entry_gap = 0
excluded_entry_boundary = 0
excluded_future_coverage = 0
all_positive_labels = 0
all_negative_labels = 0
all_zero_labels = 0
all_positive_shocks = 0
all_negative_shocks = 0
for market in lengths:
    length = lengths[market]
    event = market_events[market]
    next_eligible_time = -1.0
    decision = 24
    while decision < length - 2:
        shock = points[(market, decision)]
        prior = points[(market, decision - 1)]
        signed_shock = shock[1] - prior[1]
        if shock[0] >= next_eligible_time and abs(signed_shock) >= 0.02:
            shock_gap = (shock[0] - prior[0]) / 3600.0
            history = points[(market, decision - 24)]
            history_span = (shock[0] - history[0]) / 3600.0
            entry = points[(market, decision + 1)]
            entry_gap = (entry[0] - shock[0]) / 3600.0
            target_time = shock[0] + 86400.0
            boundary = decision + 2
            while boundary < length and points[(market, boundary)][0] < target_time:
                boundary = boundary + 1
            if shock_gap < 0.5 or shock_gap > 3.0:
                excluded_shock_gap = excluded_shock_gap + 1
            elif history_span < 18.0 or history_span > 30.0:
                excluded_history_span = excluded_history_span + 1
            elif entry_gap < 0.5 or entry_gap > 3.0:
                excluded_entry_gap = excluded_entry_gap + 1
            elif entry[1] < 0.05 or entry[1] > 0.95:
                excluded_entry_boundary = excluded_entry_boundary + 1
            elif boundary >= length:
                excluded_future_coverage = excluded_future_coverage + 1
            else:
                coverage_hours = (points[(market, boundary)][0] - shock[0]) / 3600.0
                exit_ordinal = boundary
                if points[(market, boundary)][0] > target_time:
                    exit_ordinal = boundary - 1
                exit_point = points[(market, exit_ordinal)]
                exit_hours = (exit_point[0] - shock[0]) / 3600.0
                if (
                    coverage_hours > 30.0
                    or exit_ordinal <= decision + 1
                    or exit_hours < 18.0
                    or exit_hours > 24.0
                ):
                    excluded_future_coverage = excluded_future_coverage + 1
                else:
                    zero_count = 0.0
                    absolute_step_sum = 0.0
                    for trailing in range(decision - 23, decision):
                        trailing_step = abs(
                            points[(market, trailing)][1] - points[(market, trailing - 1)][1]
                        )
                        absolute_step_sum = absolute_step_sum + trailing_step
                        if trailing_step == 0.0:
                            zero_count = zero_count + 1.0
                    quiet_start = decision - 1
                    quiet_ordinal = decision - 1
                    keep_searching = True
                    while quiet_ordinal > decision - 24 and keep_searching:
                        quiet_step = abs(
                            points[(market, quiet_ordinal)][1]
                            - points[(market, quiet_ordinal - 1)][1]
                        )
                        if quiet_step >= 0.005:
                            keep_searching = False
                        else:
                            quiet_start = quiet_ordinal - 1
                            quiet_ordinal = quiet_ordinal - 1
                    quiet_hours = (prior[0] - points[(market, quiet_start)][0]) / 3600.0
                    zero_fraction = zero_count / 23.0
                    log_quiet = log(1.0 + quiet_hours)
                    clipped = min(0.995, max(0.005, entry[1]))
                    shock_sign = 1.0
                    if signed_shock < 0.0:
                        shock_sign = -1.0
                    features = [
                        entry[1],
                        min(entry[1], 1.0 - entry[1]),
                        log(clipped / (1.0 - clipped)),
                        signed_shock,
                        abs(signed_shock),
                        entry[1] - shock[1],
                        zero_fraction,
                        log_quiet,
                        absolute_step_sum / 23.0,
                        signed_shock * zero_fraction,
                        shock_sign * log_quiet,
                    ]
                    label = exit_point[1] - entry[1]
                    if label > 0.0:
                        all_positive_labels = all_positive_labels + 1
                    elif label < 0.0:
                        all_negative_labels = all_negative_labels + 1
                    else:
                        all_zero_labels = all_zero_labels + 1
                    if signed_shock > 0.0:
                        all_positive_shocks = all_positive_shocks + 1
                    else:
                        all_negative_shocks = all_negative_shocks + 1
                    if event not in samples:
                        samples[event] = []
                    samples[event] = samples[event] + [
                        [
                            features,
                            label,
                            market,
                            shock_sign,
                            signed_shock,
                            entry[1],
                            exit_point[1],
                        ]
                    ]
                    next_eligible_time = shock[0] + 86400.0
        decision = decision + 1

groups = {
    "zero": [],
    "state": [0, 1, 2],
    "shock_only": [3, 4, 5],
    "shock_plus_staleness": list(range(11)),
}


def evaluate_group(group_name, feature_indices):
    evaluated = []
    event_metrics = []
    for test_event in range(8, 24):
        if test_event in samples:
            training_events = [event for event in range(test_event) if event in samples]
            if len(training_events) >= 2:
                model = None
                if group_name != "zero":
                    model = fit_ridge(samples, training_events, feature_indices, 0.1)
                squared_sum = 0.0
                absolute_sum = 0.0
                meaningful_count = 0
                meaningful_correct = 0
                event_positive_meaningful = 0
                event_negative_meaningful = 0
                for row in samples[test_event]:
                    prediction = 0.0
                    if model is not None:
                        prediction = ridge_prediction(model, feature_indices, row[0])
                    error = row[1] - prediction
                    squared_error = error * error
                    absolute_error = abs(error)
                    squared_sum = squared_sum + squared_error
                    absolute_sum = absolute_sum + absolute_error
                    correct = False
                    if abs(row[1]) >= 0.01:
                        meaningful_count = meaningful_count + 1
                        if row[1] > 0.0:
                            event_positive_meaningful = event_positive_meaningful + 1
                        else:
                            event_negative_meaningful = event_negative_meaningful + 1
                        if prediction * row[1] > 0.0:
                            meaningful_correct = meaningful_correct + 1
                            correct = True
                    evaluated = evaluated + [
                        [
                            test_event,
                            row[1],
                            prediction,
                            squared_error,
                            absolute_error,
                            correct,
                            row[2],
                            row[3],
                            row[4],
                        ]
                    ]
                event_direction_accuracy = None
                if meaningful_count > 0:
                    event_direction_accuracy = meaningful_correct / meaningful_count
                event_metrics = event_metrics + [
                    {
                        "event": test_event,
                        "row_count": len(samples[test_event]),
                        "mse": squared_sum / len(samples[test_event]),
                        "mae": absolute_sum / len(samples[test_event]),
                        "meaningful_count": meaningful_count,
                        "meaningful_positive_count": event_positive_meaningful,
                        "meaningful_negative_count": event_negative_meaningful,
                        "meaningful_direction_accuracy": event_direction_accuracy,
                    }
                ]
    squared_errors = [row[3] for row in evaluated]
    absolute_errors = [row[4] for row in evaluated]
    meaningful = [row for row in evaluated if abs(row[1]) >= 0.01]
    midpoint = len(event_metrics) // 2
    direction_accuracy = None
    if len(meaningful) > 0:
        direction_accuracy = sum(1 for row in meaningful if row[5]) / len(meaningful)
    return {
        "group": group_name,
        "feature_names": [feature_names[index] for index in feature_indices],
        "test_event_count": len(event_metrics),
        "test_row_count": len(evaluated),
        "observation_mse": sum(squared_errors) / len(squared_errors),
        "observation_mae": sum(absolute_errors) / len(absolute_errors),
        "event_macro_mse": sum(row["mse"] for row in event_metrics) / len(event_metrics),
        "event_macro_mae": sum(row["mae"] for row in event_metrics) / len(event_metrics),
        "early_event_macro_mse": sum(row["mse"] for row in event_metrics[:midpoint]) / midpoint,
        "late_event_macro_mse": sum(row["mse"] for row in event_metrics[midpoint:])
        / (len(event_metrics) - midpoint),
        "mean_prediction": sum(row[2] for row in evaluated) / len(evaluated),
        "mean_label": sum(row[1] for row in evaluated) / len(evaluated),
        "meaningful_count": len(meaningful),
        "meaningful_positive_count": sum(1 for row in meaningful if row[1] > 0.0),
        "meaningful_negative_count": sum(1 for row in meaningful if row[1] < 0.0),
        "meaningful_direction_accuracy": direction_accuracy,
        "event_metrics": event_metrics,
        "evaluated": evaluated,
    }


results = []
for group_name in groups:
    results = results + [evaluate_group(group_name, groups[group_name])]
by_group = {}
for item in results:
    by_group[item["group"]] = item

state = by_group["state"]
shock_only = by_group["shock_only"]
candidate = by_group["shock_plus_staleness"]
comparators = [by_group["zero"], state, shock_only]
shock_by_event = {row["event"]: row for row in shock_only["event_metrics"]}
candidate_event_wins = 0
positive_improvements = []
for row in candidate["event_metrics"]:
    comparator_row = shock_by_event[row["event"]]
    improvement = comparator_row["mse"] - row["mse"]
    if improvement > 0.0:
        candidate_event_wins = candidate_event_wins + 1
    positive_improvements = positive_improvements + [max(0.0, improvement)]
positive_total = sum(positive_improvements)
largest_positive_improvement_share = 0.0
if positive_total > 0.0:
    largest_positive_improvement_share = max(positive_improvements) / positive_total

market_counts = {}
event_counts = {}
for row in candidate["evaluated"]:
    if row[6] not in market_counts:
        market_counts[row[6]] = 0
    market_counts[row[6]] = market_counts[row[6]] + 1
    if row[0] not in event_counts:
        event_counts[row[0]] = 0
    event_counts[row[0]] = event_counts[row[0]] + 1
market_count_values = [market_counts[market] for market in market_counts]
event_count_values = [event_counts[event] for event in event_counts]
largest_market_row_share = max(market_count_values) / candidate["test_row_count"]
largest_event_row_share = max(event_count_values) / candidate["test_row_count"]
market_count_rows = sorted([[market, market_counts[market]] for market in market_counts])

continuation_values = [row[7] * row[1] for row in candidate["evaluated"]]
meaningful_continuation = [row for row in candidate["evaluated"] if abs(row[1]) >= 0.01]

trade_events = {}
trade_sides = {"YES": [], "NO": []}
trade_count = 0
for row in candidate["evaluated"]:
    side = 0.0
    side_name = ""
    if row[2] > 0.01:
        side = 1.0
        side_name = "YES"
    elif row[2] < -0.01:
        side = -1.0
        side_name = "NO"
    if side != 0.0:
        net = side * row[1] - 0.01
        if row[0] not in trade_events:
            trade_events[row[0]] = []
        trade_events[row[0]] = trade_events[row[0]] + [net]
        trade_sides[side_name] = trade_sides[side_name] + [net]
        trade_count = trade_count + 1
trade_event_means = []
for event in sorted(trade_events):
    trade_event_means = trade_event_means + [
        [event, sum(trade_events[event]) / len(trade_events[event]), len(trade_events[event])]
    ]
trade_observation_mean = None
trade_event_macro_mean = None
trade_positive_event_share = None
trade_leave_one_event_out_minimum = None
if trade_count > 0:
    all_trade_nets = []
    for event in trade_events:
        all_trade_nets = all_trade_nets + trade_events[event]
    trade_observation_mean = sum(all_trade_nets) / len(all_trade_nets)
    trade_event_macro_mean = sum(row[1] for row in trade_event_means) / len(trade_event_means)
    trade_positive_event_share = sum(1 for row in trade_event_means if row[1] > 0.0) / len(
        trade_event_means
    )
    if len(trade_event_means) > 1:
        leave_one_values = []
        for omitted in range(len(trade_event_means)):
            leave_one_values = leave_one_values + [
                sum(
                    trade_event_means[position][1]
                    for position in range(len(trade_event_means))
                    if position != omitted
                )
                / (len(trade_event_means) - 1)
            ]
        trade_leave_one_event_out_minimum = min(leave_one_values)
yes_mean = None
no_mean = None
if len(trade_sides["YES"]) > 0:
    yes_mean = sum(trade_sides["YES"]) / len(trade_sides["YES"])
if len(trade_sides["NO"]) > 0:
    no_mean = sum(trade_sides["NO"]) / len(trade_sides["NO"])

predictive_gate_passed = (
    candidate["test_row_count"] >= 150
    and len(market_counts) >= 30
    and candidate["test_event_count"] >= 10
    and largest_market_row_share <= 0.20
    and largest_event_row_share <= 0.30
    and candidate["meaningful_positive_count"] >= 50
    and candidate["meaningful_negative_count"] >= 50
    and all(
        candidate["observation_mse"] < comparator["observation_mse"] for comparator in comparators
    )
    and all(
        candidate["event_macro_mse"] < comparator["event_macro_mse"] for comparator in comparators
    )
    and candidate["early_event_macro_mse"] < shock_only["early_event_macro_mse"]
    and candidate["late_event_macro_mse"] < shock_only["late_event_macro_mse"]
    and candidate_event_wins * 5 >= candidate["test_event_count"] * 3
    and candidate["meaningful_direction_accuracy"] is not None
    and candidate["meaningful_direction_accuracy"] >= 0.55
    and shock_only["meaningful_direction_accuracy"] is not None
    and candidate["meaningful_direction_accuracy"]
    >= shock_only["meaningful_direction_accuracy"] + 0.03
    and abs(candidate["mean_prediction"] - candidate["mean_label"]) <= 0.01
    and largest_positive_improvement_share <= 0.50
)

cost_falsifier_passed = (
    trade_count >= 40
    and len(trade_event_means) >= 8
    and trade_observation_mean is not None
    and trade_observation_mean > 0.0
    and trade_event_macro_mean is not None
    and trade_event_macro_mean > 0.0
    and trade_positive_event_share is not None
    and trade_positive_event_share >= 0.60
    and trade_leave_one_event_out_minimum is not None
    and trade_leave_one_event_out_minimum > 0.0
    and len(trade_sides["YES"]) >= 10
    and len(trade_sides["NO"]) >= 10
    and yes_mean is not None
    and yes_mean >= 0.0
    and no_mean is not None
    and no_mean >= 0.0
)

public_results = []
for item in results:
    public_results = public_results + [
        {
            "group": item["group"],
            "feature_names": item["feature_names"],
            "test_event_count": item["test_event_count"],
            "test_row_count": item["test_row_count"],
            "observation_mse": item["observation_mse"],
            "observation_mae": item["observation_mae"],
            "event_macro_mse": item["event_macro_mse"],
            "event_macro_mae": item["event_macro_mae"],
            "early_event_macro_mse": item["early_event_macro_mse"],
            "late_event_macro_mse": item["late_event_macro_mse"],
            "mean_prediction": item["mean_prediction"],
            "mean_label": item["mean_label"],
            "meaningful_count": item["meaningful_count"],
            "meaningful_positive_count": item["meaningful_positive_count"],
            "meaningful_negative_count": item["meaningful_negative_count"],
            "meaningful_direction_accuracy": item["meaningful_direction_accuracy"],
            "event_metrics": item["event_metrics"],
        }
    ]

result = structured_return(
    "Delayed post-jump continuation benchmark across chronological Polymarket events.",
    {
        "schema_version": "polymarket-delayed-post-jump/v1",
        "shock_rule": "one retained step of at least two cents over 0.5-3 elapsed hours",
        "entry_rule": "first retained observation 0.5-3 hours after shock; entry in [0.05,0.95]",
        "label": "last sampled probability no later than shock plus 24h minus delayed entry probability",
        "sample_selection": "greedy non-overlapping 24-hour post-shock windows within market",
        "sample_count": sum(len(samples[event]) for event in samples),
        "sample_event_count": len(samples),
        "all_positive_shock_count": all_positive_shocks,
        "all_negative_shock_count": all_negative_shocks,
        "all_positive_label_count": all_positive_labels,
        "all_negative_label_count": all_negative_labels,
        "all_zero_label_count": all_zero_labels,
        "excluded_shock_gap": excluded_shock_gap,
        "excluded_history_span": excluded_history_span,
        "excluded_entry_gap": excluded_entry_gap,
        "excluded_entry_boundary": excluded_entry_boundary,
        "excluded_future_coverage": excluded_future_coverage,
        "ridge_penalty": 0.1,
        "results": public_results,
        "candidate_event_wins_vs_shock_only": candidate_event_wins,
        "largest_positive_improvement_share": largest_positive_improvement_share,
        "oof_market_count": len(market_counts),
        "largest_market_row_share": largest_market_row_share,
        "largest_event_row_share": largest_event_row_share,
        "oof_market_row_counts": market_count_rows,
        "fixed_shock_sign_diagnostic": {
            "mean_shock_signed_future_change": sum(continuation_values) / len(continuation_values),
            "meaningful_continuation_share": sum(
                1 for row in meaningful_continuation if row[7] * row[1] > 0.0
            )
            / len(meaningful_continuation),
        },
        "predictive_gate_passed": predictive_gate_passed,
        "delayed_one_cent_cost_falsifier": {
            "prediction_threshold": 0.01,
            "round_trip_cost": 0.01,
            "trade_count": trade_count,
            "represented_event_count": len(trade_event_means),
            "observation_mean_net_sampled_change": trade_observation_mean,
            "event_macro_mean_net_sampled_change": trade_event_macro_mean,
            "positive_event_share": trade_positive_event_share,
            "leave_one_event_out_minimum": trade_leave_one_event_out_minimum,
            "yes_trade_count": len(trade_sides["YES"]),
            "yes_mean_net_sampled_change": yes_mean,
            "no_trade_count": len(trade_sides["NO"]),
            "no_mean_net_sampled_change": no_mean,
            "event_metrics": [
                {"event": row[0], "mean_net_sampled_change": row[1], "trade_count": row[2]}
                for row in trade_event_means
            ],
            "passed": cost_falsifier_passed,
        },
        "protected_values_exposed": False,
    },
    warnings=[
        "The sample, label, feature groups, ridge penalty, and gates were fixed before this source read development outcomes.",
        "Every test event is predicted from earlier whole event groups with equal event fit weight.",
        "Post-jump windows do not overlap within a market; contracts in the same event are still dependent.",
        "The one-observation entry delay removes immediate shock execution but not historical bid/ask uncertainty.",
        "YES/NO sampled returns assume complementary probabilities and are not executable quote evidence.",
        "Passing development authorizes one formal replay only; protected values remain unavailable.",
    ],
)
