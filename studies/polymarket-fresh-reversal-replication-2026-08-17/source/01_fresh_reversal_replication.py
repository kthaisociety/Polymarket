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
        scales[position] = variance**0.5
    prior = min(0.999, max(0.001, target_mean))
    parameters = [0.0 for unused in range(len(indices) + 1)]
    parameters[0] = log(prior / (1.0 - prior))
    for iteration in range(4):
        gradient = [0.0 for unused in parameters]
        hessian = [[0.0 for unused in parameters] for unused in parameters]
        for row in training:
            weight = 1.0 / (event_total * event_counts[row[0]])
            design = [1.0]
            for position in range(len(indices)):
                design = design + [
                    (row[1][indices[position]] - feature_mean[position]) / scales[position]
                ]
            linear = 0.0
            for position in range(len(parameters)):
                linear = linear + parameters[position] * design[position]
            prediction = sigmoid(linear)
            curvature = max(0.000001, prediction * (1.0 - prediction))
            for left in range(len(parameters)):
                gradient[left] = gradient[left] + weight * design[left] * (row[2] - prediction)
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


def top_quintile(rows, prediction_index):
    predictions = [row[prediction_index] for row in rows]
    ranked = sorted(predictions, reverse=True)
    target_count = max(1, len(ranked) // 5)
    cutoff = ranked[target_count - 1]
    selected = [row for row in rows if row[prediction_index] >= cutoff]
    positives = sum(row[1] for row in selected)
    return [cutoff, len(selected), positives, positives / len(selected)]


def metric_summary(rows, prediction_index, comparator_index):
    event_groups = {}
    squared_sum = 0.0
    prediction_sum = 0.0
    target_sum = 0
    for row in rows:
        event = row[0]
        error = row[1] - row[prediction_index]
        comparator_error = row[1] - row[comparator_index]
        squared_sum = squared_sum + error * error
        prediction_sum = prediction_sum + row[prediction_index]
        target_sum = target_sum + row[1]
        if event not in event_groups:
            event_groups[event] = [0, 0.0, 0.0, 0, []]
        group = event_groups[event]
        group[0] = group[0] + 1
        group[1] = group[1] + error * error
        group[2] = group[2] + comparator_error * comparator_error
        group[3] = group[3] + row[1]
        group[4] = group[4] + [row]
    event_metrics = []
    event_average_precisions = []
    event_wins = 0
    positive_top_lift_events = 0
    eligible_top_lift_events = 0
    for event in sorted(event_groups):
        group = event_groups[event]
        brier = group[1] / group[0]
        comparator_brier = group[2] / group[0]
        rate = group[3] / group[0]
        if brier < comparator_brier:
            event_wins = event_wins + 1
        current_ap = average_precision(group[4], prediction_index)
        if current_ap is not None:
            event_average_precisions = event_average_precisions + [current_ap]
        top = top_quintile(group[4], prediction_index)
        top_lift = top[3] - rate
        if group[3] > 0 and group[3] < group[0]:
            eligible_top_lift_events = eligible_top_lift_events + 1
            if top_lift > 0.0:
                positive_top_lift_events = positive_top_lift_events + 1
        event_metrics = event_metrics + [
            {
                "event": event,
                "row_count": group[0],
                "positive_count": group[3],
                "observed_rate": rate,
                "brier": brier,
                "comparator_brier": comparator_brier,
                "average_precision": current_ap,
                "top_quintile_precision": top[3],
                "top_quintile_lift": top_lift,
            }
        ]
    midpoint = len(event_metrics) // 2
    early = event_metrics[:midpoint]
    late = event_metrics[midpoint:]
    pooled_top = top_quintile(rows, prediction_index)
    observed_rate = target_sum / len(rows)
    event_macro_ap = None
    if len(event_average_precisions) > 0:
        event_macro_ap = sum(event_average_precisions) / len(event_average_precisions)
    positive_lift_share = None
    if eligible_top_lift_events > 0:
        positive_lift_share = positive_top_lift_events / eligible_top_lift_events
    aggregate = {
        "observation_brier": squared_sum / len(rows),
        "event_macro_brier": sum(row["brier"] for row in event_metrics) / len(event_metrics),
        "early_event_macro_brier": sum(row["brier"] for row in early) / len(early),
        "late_event_macro_brier": sum(row["brier"] for row in late) / len(late),
        "pooled_average_precision": average_precision(rows, prediction_index),
        "event_macro_average_precision": event_macro_ap,
        "event_average_precision_count": len(event_average_precisions),
        "event_wins_vs_comparator": event_wins,
        "represented_event_count": len(event_metrics),
        "observed_rate": observed_rate,
        "mean_prediction": prediction_sum / len(rows),
        "top_quintile_cutoff": pooled_top[0],
        "top_quintile_count": pooled_top[1],
        "top_quintile_positive": pooled_top[2],
        "top_quintile_precision": pooled_top[3],
        "top_quintile_lift": pooled_top[3] - observed_rate,
        "positive_event_top_quintile_lift_share": positive_lift_share,
        "eligible_event_top_quintile_lift_count": eligible_top_lift_events,
    }
    return [aggregate, event_metrics]


def improvement_concentration(candidate_events):
    improvements = []
    for row in candidate_events:
        improvements = improvements + [max(0.0, row["comparator_brier"] - row["brier"])]
    total = sum(improvements)
    if total <= 0.0:
        return 0.0
    return max(improvements) / total


def cost_screen(rows, prediction_index):
    trade_events = {}
    positive_shock_nets = []
    negative_shock_nets = []
    for row in rows:
        if row[prediction_index] >= 0.65:
            side = -row[6]
            net = side * (row[8] - row[7]) - 0.01
            if row[0] not in trade_events:
                trade_events[row[0]] = []
            trade_events[row[0]] = trade_events[row[0]] + [net]
            if row[6] > 0.0:
                positive_shock_nets = positive_shock_nets + [net]
            else:
                negative_shock_nets = negative_shock_nets + [net]
    event_metrics = []
    all_nets = []
    for event in sorted(trade_events):
        event_mean = sum(trade_events[event]) / len(trade_events[event])
        event_metrics = event_metrics + [
            {"event": event, "mean_net_sampled_change": event_mean, "trade_count": len(trade_events[event])}
        ]
        all_nets = all_nets + trade_events[event]
    observation_mean = None
    event_macro_mean = None
    positive_event_share = None
    leave_one_event_out_minimum = None
    positive_shock_mean = None
    negative_shock_mean = None
    if len(all_nets) > 0:
        observation_mean = sum(all_nets) / len(all_nets)
        event_macro_mean = sum(row["mean_net_sampled_change"] for row in event_metrics) / len(
            event_metrics
        )
        positive_event_share = sum(
            1 for row in event_metrics if row["mean_net_sampled_change"] > 0.0
        ) / len(event_metrics)
    if len(event_metrics) > 1:
        leave_one_values = []
        for omitted in range(len(event_metrics)):
            leave_one_values = leave_one_values + [
                sum(
                    event_metrics[position]["mean_net_sampled_change"]
                    for position in range(len(event_metrics))
                    if position != omitted
                )
                / (len(event_metrics) - 1)
            ]
        leave_one_event_out_minimum = min(leave_one_values)
    if len(positive_shock_nets) > 0:
        positive_shock_mean = sum(positive_shock_nets) / len(positive_shock_nets)
    if len(negative_shock_nets) > 0:
        negative_shock_mean = sum(negative_shock_nets) / len(negative_shock_nets)
    passed = (
        len(all_nets) >= 100
        and len(event_metrics) >= 20
        and observation_mean is not None
        and observation_mean > 0.0
        and event_macro_mean is not None
        and event_macro_mean > 0.0
        and positive_event_share is not None
        and positive_event_share >= 0.60
        and leave_one_event_out_minimum is not None
        and leave_one_event_out_minimum > 0.0
        and len(positive_shock_nets) >= 25
        and len(negative_shock_nets) >= 25
        and positive_shock_mean is not None
        and positive_shock_mean >= 0.0
        and negative_shock_mean is not None
        and negative_shock_mean >= 0.0
    )
    return {
        "prediction_threshold": 0.65,
        "round_trip_cost": 0.01,
        "trade_count": len(all_nets),
        "represented_event_count": len(event_metrics),
        "observation_mean_net_sampled_change": observation_mean,
        "event_macro_mean_net_sampled_change": event_macro_mean,
        "positive_event_share": positive_event_share,
        "leave_one_event_out_minimum": leave_one_event_out_minimum,
        "positive_shock_trade_count": len(positive_shock_nets),
        "positive_shock_mean_net_sampled_change": positive_shock_mean,
        "negative_shock_trade_count": len(negative_shock_nets),
        "negative_shock_mean_net_sampled_change": negative_shock_mean,
        "event_metrics": event_metrics,
        "passed": passed,
    }


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
    "shock_sign",
    "absolute_shock_size",
    "shock_signed_entry_slippage",
    "immediate_retracement_fraction_clipped_2",
    "reversal_direction_headroom",
    "continuation_direction_headroom",
    "pre_shock_zero_fraction_23",
    "log_one_plus_pre_shock_quiet_hours_005",
    "pre_shock_mean_absolute_step_23",
]
state_shock_indices = [0, 1, 2, 3, 4, 5]
full_indices = list(range(12))
samples = {}
excluded_shock_gap = 0
excluded_history_span = 0
excluded_entry_gap = 0
excluded_entry_boundary = 0
excluded_future_coverage = 0
all_reversal_first = 0
all_other = 0
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
                final_ordinal = boundary
                if points[(market, boundary)][0] > target_time:
                    final_ordinal = boundary - 1
                final_point = points[(market, final_ordinal)]
                final_hours = (final_point[0] - shock[0]) / 3600.0
                if (
                    coverage_hours > 30.0
                    or final_ordinal <= decision + 1
                    or final_hours < 18.0
                    or final_hours > 24.0
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
                    shock_sign = 1.0
                    if signed_shock < 0.0:
                        shock_sign = -1.0
                    shock_size = abs(signed_shock)
                    signed_slippage = shock_sign * (entry[1] - shock[1])
                    retracement_fraction = min(2.0, max(-2.0, -signed_slippage / shock_size))
                    reversal_headroom = entry[1]
                    continuation_headroom = 1.0 - entry[1]
                    if shock_sign < 0.0:
                        reversal_headroom = 1.0 - entry[1]
                        continuation_headroom = entry[1]
                    clipped = min(0.995, max(0.005, entry[1]))
                    features = [
                        entry[1],
                        min(entry[1], 1.0 - entry[1]),
                        log(clipped / (1.0 - clipped)),
                        shock_sign,
                        shock_size,
                        signed_slippage,
                        retracement_fraction,
                        reversal_headroom,
                        continuation_headroom,
                        zero_count / 23.0,
                        log(1.0 + quiet_hours),
                        absolute_step_sum / 23.0,
                    ]
                    label = 0
                    diagnostic_exit = final_point[1]
                    future_ordinal = decision + 2
                    crossing_found = False
                    while future_ordinal <= final_ordinal and not crossing_found:
                        future_probability = points[(market, future_ordinal)][1]
                        oriented_move = shock_sign * (future_probability - entry[1])
                        if oriented_move <= -0.02:
                            label = 1
                            diagnostic_exit = future_probability
                            crossing_found = True
                        elif oriented_move >= 0.02:
                            diagnostic_exit = future_probability
                            crossing_found = True
                        future_ordinal = future_ordinal + 1
                    if label == 1:
                        all_reversal_first = all_reversal_first + 1
                    else:
                        all_other = all_other + 1
                    if event not in samples:
                        samples[event] = []
                    samples[event] = samples[event] + [
                        [event, features, label, market, shock_sign, entry[1], diagnostic_exit]
                    ]
                    next_eligible_time = shock[0] + 86400.0
        decision = decision + 1

evaluated = []
for test_event in sorted(samples):
    if test_event >= 8:
        training = []
        training_event_count = 0
        baseline = 0.0
        for train_event in sorted(samples):
            if train_event < test_event:
                event_rows = samples[train_event]
                training_event_count = training_event_count + 1
                event_positive = 0
                for row in event_rows:
                    training = training + [row]
                    event_positive = event_positive + row[2]
                baseline = baseline + event_positive / len(event_rows)
        if training_event_count >= 2:
            baseline = min(0.999, max(0.001, baseline / training_event_count))
            state_shock_model = fit_logistic(training, state_shock_indices, 0.1)
            full_model = fit_logistic(training, full_indices, 0.1)
            for row in samples[test_event]:
                state_prediction = predict_logistic(state_shock_model, state_shock_indices, row[1])
                full_prediction = predict_logistic(full_model, full_indices, row[1])
                evaluated = evaluated + [
                    [
                        row[0],
                        row[2],
                        baseline,
                        state_prediction,
                        full_prediction,
                        row[3],
                        row[4],
                        row[5],
                        row[6],
                    ]
                ]

rate_result = metric_summary(evaluated, 2, 2)
state_result = metric_summary(evaluated, 3, 2)
full_result = metric_summary(evaluated, 4, 3)
rate_metrics = rate_result[0]
state_metrics = state_result[0]
full_metrics = full_result[0]
rate_events = rate_result[1]
state_events = state_result[1]
full_events = full_result[1]

market_counts = {}
event_counts = {}
for row in evaluated:
    if row[5] not in market_counts:
        market_counts[row[5]] = 0
    market_counts[row[5]] = market_counts[row[5]] + 1
    if row[0] not in event_counts:
        event_counts[row[0]] = 0
    event_counts[row[0]] = event_counts[row[0]] + 1
market_count_values = [market_counts[market] for market in market_counts]
event_count_values = [event_counts[event] for event in event_counts]
largest_market_row_share = max(market_count_values) / len(evaluated)
largest_event_row_share = max(event_count_values) / len(evaluated)
state_improvement_concentration = improvement_concentration(state_events)
full_improvement_concentration = improvement_concentration(full_events)

primary_state_replication_passed = (
    len(evaluated) >= 1000
    and sum(row[1] for row in evaluated) >= 300
    and len(evaluated) - sum(row[1] for row in evaluated) >= 300
    and len(market_counts) >= 100
    and state_metrics["represented_event_count"] >= 30
    and largest_market_row_share <= 0.10
    and largest_event_row_share <= 0.20
    and state_metrics["observation_brier"] < rate_metrics["observation_brier"]
    and state_metrics["event_macro_brier"] < rate_metrics["event_macro_brier"]
    and state_metrics["early_event_macro_brier"] < rate_metrics["early_event_macro_brier"]
    and state_metrics["late_event_macro_brier"] < rate_metrics["late_event_macro_brier"]
    and state_metrics["pooled_average_precision"] > rate_metrics["pooled_average_precision"]
    and state_metrics["event_macro_average_precision"] is not None
    and rate_metrics["event_macro_average_precision"] is not None
    and state_metrics["event_macro_average_precision"]
    > rate_metrics["event_macro_average_precision"]
    and state_metrics["event_wins_vs_comparator"] * 5
    >= state_metrics["represented_event_count"] * 3
    and abs(state_metrics["mean_prediction"] - state_metrics["observed_rate"]) <= 0.10
    and state_metrics["top_quintile_lift"] >= 0.10
    and state_metrics["positive_event_top_quintile_lift_share"] is not None
    and state_metrics["positive_event_top_quintile_lift_share"] >= 0.60
    and state_improvement_concentration <= 0.25
)

secondary_full_incremental_passed = (
    len(evaluated) >= 1000
    and sum(row[1] for row in evaluated) >= 300
    and len(evaluated) - sum(row[1] for row in evaluated) >= 300
    and len(market_counts) >= 100
    and full_metrics["represented_event_count"] >= 30
    and largest_market_row_share <= 0.10
    and largest_event_row_share <= 0.20
    and full_metrics["observation_brier"] < state_metrics["observation_brier"]
    and full_metrics["event_macro_brier"] < state_metrics["event_macro_brier"]
    and full_metrics["early_event_macro_brier"] < state_metrics["early_event_macro_brier"]
    and full_metrics["late_event_macro_brier"] < state_metrics["late_event_macro_brier"]
    and full_metrics["pooled_average_precision"] > state_metrics["pooled_average_precision"]
    and full_metrics["event_macro_average_precision"] is not None
    and state_metrics["event_macro_average_precision"] is not None
    and full_metrics["event_macro_average_precision"]
    > state_metrics["event_macro_average_precision"]
    and full_metrics["event_wins_vs_comparator"] * 5
    >= full_metrics["represented_event_count"] * 3
    and abs(full_metrics["mean_prediction"] - full_metrics["observed_rate"]) <= 0.10
    and full_metrics["top_quintile_lift"] >= 0.15
    and full_metrics["positive_event_top_quintile_lift_share"] is not None
    and full_metrics["positive_event_top_quintile_lift_share"] >= 0.60
    and full_improvement_concentration <= 0.25
)

state_cost_screen = cost_screen(evaluated, 3)
full_cost_screen = cost_screen(evaluated, 4)
per_event_evidence = []
for position in range(len(state_events)):
    per_event_evidence = per_event_evidence + [
        {
            "event": state_events[position]["event"],
            "row_count": state_events[position]["row_count"],
            "positive_count": state_events[position]["positive_count"],
            "observed_rate": state_events[position]["observed_rate"],
            "rate_brier": rate_events[position]["brier"],
            "state_brier": state_events[position]["brier"],
            "full_brier": full_events[position]["brier"],
            "rate_average_precision": rate_events[position]["average_precision"],
            "state_average_precision": state_events[position]["average_precision"],
            "full_average_precision": full_events[position]["average_precision"],
            "state_top_quintile_lift": state_events[position]["top_quintile_lift"],
            "full_top_quintile_lift": full_events[position]["top_quintile_lift"],
        }
    ]

result = structured_return(
    "Fresh-event post-jump reversal-first hazard replication.",
    {
        "schema_version": "polymarket-fresh-post-jump-reversal-first-hazard/v1",
        "selection_exposed_parent_source_sha256": "25baa10e9273e19b8ff969e4e9f6659b2ccaf4110f6deb7e485feb34a68fcc3a",
        "selection_exposed_parent_receipt_sha256": "65e9a70ce16551f560b38d4e90155fa00fb25b00ddb3c95558fc8bcc7b73b442",
        "label": "two-cent reversal from delayed entry before two-cent continuation within shock plus 24h",
        "sample_rule": "greedy non-overlapping two-cent shocks with one-observation delayed entry",
        "sample_count": sum(len(samples[event]) for event in samples),
        "sample_event_count": len(samples),
        "all_reversal_first_count": all_reversal_first,
        "all_other_count": all_other,
        "excluded_shock_gap": excluded_shock_gap,
        "excluded_history_span": excluded_history_span,
        "excluded_entry_gap": excluded_entry_gap,
        "excluded_entry_boundary": excluded_entry_boundary,
        "excluded_future_coverage": excluded_future_coverage,
        "feature_names": feature_names,
        "state_shock_indices": state_shock_indices,
        "full_indices": full_indices,
        "ridge_penalty": 0.1,
        "newton_iteration_count": 4,
        "first_test_event_ordinal": 8,
        "oof_row_count": len(evaluated),
        "oof_positive_count": sum(row[1] for row in evaluated),
        "oof_negative_count": len(evaluated) - sum(row[1] for row in evaluated),
        "oof_market_count": len(market_counts),
        "oof_event_count": len(event_counts),
        "largest_market_row_share": largest_market_row_share,
        "largest_event_row_share": largest_event_row_share,
        "rate_baseline": rate_metrics,
        "state_shock_logistic": state_metrics,
        "full_path_regime_logistic": full_metrics,
        "state_positive_brier_improvement_concentration": state_improvement_concentration,
        "full_positive_brier_improvement_concentration": full_improvement_concentration,
        "primary_state_replication_passed": primary_state_replication_passed,
        "secondary_full_incremental_passed": secondary_full_incremental_passed,
        "state_shock_one_cent_cost_screen": state_cost_screen,
        "full_path_one_cent_cost_screen": full_cost_screen,
        "per_event_evidence": per_event_evidence,
        "protected_values_exposed": False,
    },
    warnings=[
        "Population, label, features, folds, logistic recipes, gates, and cost screens were fixed before fresh path access.",
        "The original 31-event corpus selected this hypothesis and is not confirmation evidence.",
        "Every test event uses only earlier fresh event groups with fold-local scaling and equal event fit weight.",
        "Non-overlap is enforced within market; contracts sharing an event remain dependent.",
        "Cost screens use sampled complementary probabilities, not executable historical quotes.",
        "The expanded final whole-event block and every ancestor event remain unavailable.",
    ],
)
