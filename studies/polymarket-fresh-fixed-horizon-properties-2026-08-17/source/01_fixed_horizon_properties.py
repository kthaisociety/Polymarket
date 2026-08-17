markets = read("polymarket-development-prices", "market_id")
events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")


def solve_linear(matrix, vector):
    size = len(vector)
    augmented = []
    for row in range(size):
        augmented = augmented + [matrix[row] + [vector[row]]]
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


def fit_logistic(training, target_index, feature_indices):
    event_counts = {}
    for row in training:
        event = row[0]
        if event not in event_counts:
            event_counts[event] = 0
        event_counts[event] = event_counts[event] + 1
    event_total = len(event_counts)
    means = [0.0 for unused in feature_indices]
    seconds = [0.0 for unused in feature_indices]
    target_mean = 0.0
    for row in training:
        weight = 1.0 / (event_total * event_counts[row[0]])
        target_mean = target_mean + weight * row[3][target_index]
        for position in range(len(feature_indices)):
            value = row[2][feature_indices[position]]
            means[position] = means[position] + weight * value
            seconds[position] = seconds[position] + weight * value * value
    scales = []
    for position in range(len(feature_indices)):
        variance = seconds[position] - means[position] * means[position]
        scales = scales + [max(0.000000000001, variance) ** 0.5]
    prior = min(0.999, max(0.001, target_mean))
    parameters = [log(prior / (1.0 - prior))]
    parameters = parameters + [0.0 for unused in feature_indices]
    size = len(parameters)
    for iteration in range(4):
        gradient = [0.0 for unused in parameters]
        hessian = [[0.0 for unused in parameters] for unused in parameters]
        for row in training:
            weight = 1.0 / (event_total * event_counts[row[0]])
            design = [1.0]
            for position in range(len(feature_indices)):
                index = feature_indices[position]
                design = design + [(row[2][index] - means[position]) / scales[position]]
            linear = 0.0
            for position in range(size):
                linear = linear + parameters[position] * design[position]
            prediction = sigmoid(linear)
            curvature = max(0.000001, prediction * (1.0 - prediction))
            for left in range(size):
                gradient[left] = gradient[left] + weight * design[left] * (
                    row[3][target_index] - prediction
                )
                for right in range(left + 1):
                    addition = weight * curvature * design[left] * design[right]
                    hessian[left][right] = hessian[left][right] + addition
                    if left != right:
                        hessian[right][left] = hessian[right][left] + addition
        hessian[0][0] = hessian[0][0] + 0.000001
        for position in range(1, size):
            gradient[position] = gradient[position] - 0.1 * parameters[position]
            hessian[position][position] = hessian[position][position] + 0.1
        update = solve_linear(hessian, gradient)
        for position in range(size):
            parameters[position] = parameters[position] + update[position]
    return [means, scales, parameters]


def predict_logistic(model, feature_indices, features):
    linear = model[2][0]
    for position in range(len(feature_indices)):
        index = feature_indices[position]
        standardized = (features[index] - model[0][position]) / model[1][position]
        linear = linear + model[2][position + 1] * standardized
    return sigmoid(linear)


def average_precision(rows, target_index, prediction_index):
    pairs = []
    positives = 0
    for row in rows:
        label = row[2][target_index]
        pairs = pairs + [[row[3][target_index][prediction_index], label]]
        positives = positives + label
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


def top_quintile(rows, target_index, prediction_index):
    predictions = [row[3][target_index][prediction_index] for row in rows]
    ranked = sorted(predictions, reverse=True)
    target_count = max(1, len(ranked) // 5)
    cutoff = ranked[target_count - 1]
    selected = [row for row in rows if row[3][target_index][prediction_index] >= cutoff]
    positives = sum(row[2][target_index] for row in selected)
    return [cutoff, len(selected), positives, positives / len(selected)]


def metric_summary(rows, target_index, prediction_index, comparator_index):
    groups = {}
    squared_sum = 0.0
    prediction_sum = 0.0
    target_sum = 0
    for row in rows:
        event = row[0]
        label = row[2][target_index]
        prediction = row[3][target_index][prediction_index]
        comparator = row[3][target_index][comparator_index]
        squared_sum = squared_sum + (label - prediction) ** 2
        prediction_sum = prediction_sum + prediction
        target_sum = target_sum + label
        if event not in groups:
            groups[event] = [0, 0.0, 0.0, 0, []]
        group = groups[event]
        group[0] = group[0] + 1
        group[1] = group[1] + (label - prediction) ** 2
        group[2] = group[2] + (label - comparator) ** 2
        group[3] = group[3] + label
        group[4] = group[4] + [row]
    event_metrics = []
    event_aps = []
    wins = 0
    positive_lift_events = 0
    eligible_lift_events = 0
    for event in sorted(groups):
        group = groups[event]
        brier = group[1] / group[0]
        comparator_brier = group[2] / group[0]
        rate = group[3] / group[0]
        if brier < comparator_brier:
            wins = wins + 1
        current_ap = average_precision(group[4], target_index, prediction_index)
        if current_ap is not None:
            event_aps = event_aps + [current_ap]
        top = top_quintile(group[4], target_index, prediction_index)
        lift = top[3] - rate
        if group[3] > 0 and group[3] < group[0]:
            eligible_lift_events = eligible_lift_events + 1
            if lift > 0.0:
                positive_lift_events = positive_lift_events + 1
        event_metrics = event_metrics + [
            {
                "event": event,
                "row_count": group[0],
                "positive_count": group[3],
                "observed_rate": rate,
                "brier": brier,
                "comparator_brier": comparator_brier,
                "average_precision": current_ap,
                "top_quintile_lift": lift,
            }
        ]
    midpoint = len(event_metrics) // 2
    early = event_metrics[:midpoint]
    late = event_metrics[midpoint:]
    pooled_top = top_quintile(rows, target_index, prediction_index)
    observed_rate = target_sum / len(rows)
    macro_ap = None
    if len(event_aps) > 0:
        macro_ap = sum(event_aps) / len(event_aps)
    positive_lift_share = None
    if eligible_lift_events > 0:
        positive_lift_share = positive_lift_events / eligible_lift_events
    return [
        {
            "observation_brier": squared_sum / len(rows),
            "event_macro_brier": sum(row["brier"] for row in event_metrics)
            / len(event_metrics),
            "early_event_macro_brier": sum(row["brier"] for row in early) / len(early),
            "late_event_macro_brier": sum(row["brier"] for row in late) / len(late),
            "pooled_average_precision": average_precision(rows, target_index, prediction_index),
            "event_macro_average_precision": macro_ap,
            "event_wins_vs_comparator": wins,
            "represented_event_count": len(event_metrics),
            "observed_rate": observed_rate,
            "mean_prediction": prediction_sum / len(rows),
            "top_quintile_count": pooled_top[1],
            "top_quintile_precision": pooled_top[3],
            "top_quintile_lift": pooled_top[3] - observed_rate,
            "positive_event_top_quintile_lift_share": positive_lift_share,
            "eligible_event_top_quintile_lift_count": eligible_lift_events,
        },
        event_metrics,
    ]


def concentration(candidate_events):
    improvements = [
        max(0.0, row["comparator_brier"] - row["brier"]) for row in candidate_events
    ]
    total = sum(improvements)
    if total <= 0.0:
        return 0.0
    return max(improvements) / total


def cost_screen(rows, prediction_index):
    by_event = {}
    positive_sign = []
    negative_sign = []
    for row in rows:
        if row[3][0][prediction_index] >= 0.65:
            net = -row[4] * (row[6] - row[5]) - 0.01
            if row[0] not in by_event:
                by_event[row[0]] = []
            by_event[row[0]] = by_event[row[0]] + [net]
            if row[4] > 0.0:
                positive_sign = positive_sign + [net]
            else:
                negative_sign = negative_sign + [net]
    event_means = [sum(by_event[event]) / len(by_event[event]) for event in sorted(by_event)]
    all_nets = []
    for event in sorted(by_event):
        all_nets = all_nets + by_event[event]
    observation_mean = None
    event_mean = None
    positive_event_share = None
    loo_minimum = None
    positive_sign_mean = None
    negative_sign_mean = None
    if len(all_nets) > 0:
        observation_mean = sum(all_nets) / len(all_nets)
        event_mean = sum(event_means) / len(event_means)
        positive_event_share = sum(value > 0.0 for value in event_means) / len(event_means)
    if len(event_means) > 1:
        loo = []
        for omitted in range(len(event_means)):
            loo = loo + [
                sum(event_means[position] for position in range(len(event_means)) if position != omitted)
                / (len(event_means) - 1)
            ]
        loo_minimum = min(loo)
    if len(positive_sign) > 0:
        positive_sign_mean = sum(positive_sign) / len(positive_sign)
    if len(negative_sign) > 0:
        negative_sign_mean = sum(negative_sign) / len(negative_sign)
    passed = (
        len(all_nets) >= 100
        and len(event_means) >= 20
        and observation_mean is not None
        and observation_mean > 0.0
        and event_mean is not None
        and event_mean > 0.0
        and positive_event_share is not None
        and positive_event_share >= 0.60
        and loo_minimum is not None
        and loo_minimum > 0.0
        and len(positive_sign) >= 25
        and len(negative_sign) >= 25
        and positive_sign_mean is not None
        and positive_sign_mean >= 0.0
        and negative_sign_mean is not None
        and negative_sign_mean >= 0.0
    )
    return {
        "prediction_threshold": 0.65,
        "round_trip_cost": 0.01,
        "trade_count": len(all_nets),
        "represented_event_count": len(event_means),
        "observation_mean_net_sampled_change": observation_mean,
        "event_macro_mean_net_sampled_change": event_mean,
        "positive_event_share": positive_event_share,
        "leave_one_event_out_minimum": loo_minimum,
        "positive_shock_trade_count": len(positive_sign),
        "positive_shock_mean_net_sampled_change": positive_sign_mean,
        "negative_shock_trade_count": len(negative_sign),
        "negative_shock_mean_net_sampled_change": negative_sign_mean,
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
state_indices = [0, 1, 2, 3, 4, 5]
full_indices = list(range(12))
label_names = ["reversal_first_2c", "any_move_2c", "boundary_entry_02_98"]
samples = {}
exclusions = {
    "shock_gap": 0,
    "history_span": 0,
    "entry_gap": 0,
    "entry_boundary": 0,
    "future_coverage": 0,
}
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
            target_time = entry[0] + 21.0 * 3600.0
            boundary = decision + 2
            while boundary < length and points[(market, boundary)][0] < target_time:
                boundary = boundary + 1
            if shock_gap < 0.5 or shock_gap > 3.0:
                exclusions["shock_gap"] = exclusions["shock_gap"] + 1
            elif history_span < 18.0 or history_span > 30.0:
                exclusions["history_span"] = exclusions["history_span"] + 1
            elif entry_gap < 0.5 or entry_gap > 3.0:
                exclusions["entry_gap"] = exclusions["entry_gap"] + 1
            elif entry[1] < 0.05 or entry[1] > 0.95:
                exclusions["entry_boundary"] = exclusions["entry_boundary"] + 1
            elif boundary >= length:
                exclusions["future_coverage"] = exclusions["future_coverage"] + 1
            else:
                coverage_hours = (points[(market, boundary)][0] - entry[0]) / 3600.0
                final_ordinal = boundary
                if points[(market, boundary)][0] > target_time:
                    final_ordinal = boundary - 1
                final_point = points[(market, final_ordinal)]
                final_hours = (final_point[0] - entry[0]) / 3600.0
                if coverage_hours > 27.0 or final_ordinal <= decision + 1 or final_hours < 15.0:
                    exclusions["future_coverage"] = exclusions["future_coverage"] + 1
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
                    searching = True
                    while quiet_ordinal > decision - 24 and searching:
                        quiet_step = abs(
                            points[(market, quiet_ordinal)][1]
                            - points[(market, quiet_ordinal - 1)][1]
                        )
                        if quiet_step >= 0.005:
                            searching = False
                        else:
                            quiet_start = quiet_ordinal - 1
                            quiet_ordinal = quiet_ordinal - 1
                    quiet_hours = (prior[0] - points[(market, quiet_start)][0]) / 3600.0
                    shock_sign = 1.0
                    if signed_shock < 0.0:
                        shock_sign = -1.0
                    shock_size = abs(signed_shock)
                    signed_slippage = shock_sign * (entry[1] - shock[1])
                    retracement = min(2.0, max(-2.0, -signed_slippage / shock_size))
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
                        retracement,
                        reversal_headroom,
                        continuation_headroom,
                        zero_count / 23.0,
                        log(1.0 + quiet_hours),
                        absolute_step_sum / 23.0,
                    ]
                    reversal = 0
                    any_move = 0
                    boundary_entry = 0
                    exit_probability = final_point[1]
                    crossing_found = False
                    future = decision + 2
                    while future <= final_ordinal:
                        future_probability = points[(market, future)][1]
                        oriented = shock_sign * (future_probability - entry[1])
                        if abs(future_probability - entry[1]) >= 0.02:
                            any_move = 1
                        if future_probability <= 0.02 or future_probability >= 0.98:
                            boundary_entry = 1
                        if not crossing_found and oriented <= -0.02:
                            reversal = 1
                            exit_probability = future_probability
                            crossing_found = True
                        elif not crossing_found and oriented >= 0.02:
                            exit_probability = future_probability
                            crossing_found = True
                        future = future + 1
                    if event not in samples:
                        samples[event] = []
                    samples[event] = samples[event] + [
                        [
                            event,
                            market,
                            features,
                            [reversal, any_move, boundary_entry],
                            shock_sign,
                            entry[1],
                            exit_probability,
                        ]
                    ]
                    next_eligible_time = shock[0] + 24.0 * 3600.0
        decision = decision + 1

evaluated = []
for test_event in sorted(samples):
    if test_event >= 8:
        training = []
        earlier_events = []
        for train_event in sorted(samples):
            if train_event < test_event:
                training = training + samples[train_event]
                earlier_events = earlier_events + [train_event]
        if len(earlier_events) >= 2:
            baselines = []
            state_models = []
            full_models = []
            for target_index in range(3):
                baseline = 0.0
                for train_event in earlier_events:
                    baseline = baseline + sum(
                        row[3][target_index] for row in samples[train_event]
                    ) / len(samples[train_event])
                baselines = baselines + [min(0.999, max(0.001, baseline / len(earlier_events)))]
                state_models = state_models + [fit_logistic(training, target_index, state_indices)]
                full_models = full_models + [fit_logistic(training, target_index, full_indices)]
            for row in samples[test_event]:
                predictions = []
                for target_index in range(3):
                    predictions = predictions + [
                        [
                            baselines[target_index],
                            predict_logistic(state_models[target_index], state_indices, row[2]),
                            predict_logistic(full_models[target_index], full_indices, row[2]),
                        ]
                    ]
                evaluated = evaluated + [
                    [row[0], row[1], row[3], predictions, row[4], row[5], row[6]]
                ]

market_counts = {}
event_counts = {}
for row in evaluated:
    if row[1] not in market_counts:
        market_counts[row[1]] = 0
    market_counts[row[1]] = market_counts[row[1]] + 1
    if row[0] not in event_counts:
        event_counts[row[0]] = 0
    event_counts[row[0]] = event_counts[row[0]] + 1
largest_market_share = max(market_counts[market] for market in market_counts) / len(evaluated)
largest_event_share = max(event_counts[event] for event in event_counts) / len(evaluated)

target_results = []
for target_index in range(3):
    rate = metric_summary(evaluated, target_index, 0, 0)
    state = metric_summary(evaluated, target_index, 1, 0)
    full = metric_summary(evaluated, target_index, 2, 1)
    target_results = target_results + [
        {
            "label": label_names[target_index],
            "positive_count": sum(row[2][target_index] for row in evaluated),
            "negative_count": len(evaluated)
            - sum(row[2][target_index] for row in evaluated),
            "rate_baseline": rate[0],
            "state_shock_logistic": state[0],
            "full_path_logistic": full[0],
            "state_positive_brier_improvement_concentration": concentration(state[1]),
            "full_positive_brier_improvement_concentration": concentration(full[1]),
            "per_event": [
                {
                    "event": state[1][position]["event"],
                    "row_count": state[1][position]["row_count"],
                    "positive_count": state[1][position]["positive_count"],
                    "rate_brier": rate[1][position]["brier"],
                    "state_brier": state[1][position]["brier"],
                    "full_brier": full[1][position]["brier"],
                }
                for position in range(len(state[1]))
            ],
        }
    ]

reversal = target_results[0]
rate_metrics = reversal["rate_baseline"]
state_metrics = reversal["state_shock_logistic"]
full_metrics = reversal["full_path_logistic"]
state_gate = (
    len(evaluated) >= 1000
    and reversal["positive_count"] >= 300
    and reversal["negative_count"] >= 300
    and len(market_counts) >= 100
    and len(event_counts) >= 30
    and largest_market_share <= 0.10
    and largest_event_share <= 0.20
    and state_metrics["observation_brier"] < rate_metrics["observation_brier"]
    and state_metrics["event_macro_brier"] < rate_metrics["event_macro_brier"]
    and state_metrics["early_event_macro_brier"] < rate_metrics["early_event_macro_brier"]
    and state_metrics["late_event_macro_brier"] < rate_metrics["late_event_macro_brier"]
    and state_metrics["pooled_average_precision"] > rate_metrics["pooled_average_precision"]
    and state_metrics["event_macro_average_precision"]
    > rate_metrics["event_macro_average_precision"]
    and state_metrics["event_wins_vs_comparator"] * 5
    >= state_metrics["represented_event_count"] * 3
    and abs(state_metrics["mean_prediction"] - state_metrics["observed_rate"]) <= 0.10
    and state_metrics["top_quintile_lift"] >= 0.10
    and state_metrics["positive_event_top_quintile_lift_share"] >= 0.60
    and reversal["state_positive_brier_improvement_concentration"] <= 0.25
)
full_gate = (
    state_gate
    and full_metrics["observation_brier"] < state_metrics["observation_brier"]
    and full_metrics["event_macro_brier"] < state_metrics["event_macro_brier"]
    and full_metrics["early_event_macro_brier"] < state_metrics["early_event_macro_brier"]
    and full_metrics["late_event_macro_brier"] < state_metrics["late_event_macro_brier"]
    and full_metrics["pooled_average_precision"] > state_metrics["pooled_average_precision"]
    and full_metrics["event_macro_average_precision"]
    > state_metrics["event_macro_average_precision"]
    and full_metrics["event_wins_vs_comparator"] * 5
    >= full_metrics["represented_event_count"] * 3
    and abs(full_metrics["mean_prediction"] - full_metrics["observed_rate"]) <= 0.10
    and full_metrics["top_quintile_lift"] >= 0.15
    and full_metrics["positive_event_top_quintile_lift_share"] >= 0.60
    and reversal["full_positive_brier_improvement_concentration"] <= 0.25
)

result = structured_return(
    "Fresh-contract fixed-horizon path properties evaluated.",
    {
        "schema_version": "polymarket-fresh-fixed-horizon-properties/v1",
        "selection_parent_receipt_sha256": "e777f93b48c87604d845dfd08160036449b2accdd13277a0acf55d243d658c77",
        "fixed_horizon_hours_from_delayed_entry": 21,
        "sample_count": sum(len(samples[event]) for event in samples),
        "sample_event_count": len(samples),
        "oof_row_count": len(evaluated),
        "oof_market_count": len(market_counts),
        "oof_event_count": len(event_counts),
        "largest_market_row_share": largest_market_share,
        "largest_event_row_share": largest_event_share,
        "exclusions": exclusions,
        "feature_names": feature_names,
        "state_indices": state_indices,
        "full_indices": full_indices,
        "ridge_penalty": 0.1,
        "newton_iteration_count": 4,
        "first_test_event_ordinal": 8,
        "target_results": target_results,
        "reversal_state_gate_passed": state_gate,
        "reversal_full_incremental_gate_passed": full_gate,
        "reversal_state_one_cent_cost_screen": cost_screen(evaluated, 1),
        "reversal_full_one_cent_cost_screen": cost_screen(evaluated, 2),
        "protected_values_exposed": False,
    },
    warnings=[
        "This fixed-horizon revision is selection-exposed and is not a second independent replication.",
        "Every test event is predicted only from earlier fresh event groups with equal event fit weight.",
        "Resolution labels, current close-time metadata, ancestor events, and protected events are unused.",
        "Movement and boundary targets are mechanism controls and cannot replace a failed reversal target.",
        "Cost screens use sampled complementary probabilities rather than executable historical quotes.",
    ],
)
