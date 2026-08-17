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
        scales[position] = sqrt(scales[position] + 0.000000000001)
    matrix = [[0.0 for unused in feature_indices] for unused in feature_indices]
    vector = [0.0 for unused in feature_indices]
    for event in training_events:
        rows = samples[event]
        row_weight = 1.0 / (event_count * len(rows))
        for row in rows:
            standardized = [
                (row[0][feature_indices[position]] - means[position]) / scales[position]
                for position in range(feature_count)
            ]
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


def average_precision(pairs):
    positive_count = sum(row[1] for row in pairs)
    if positive_count == 0:
        return None
    thresholds = sorted(set(row[0] for row in pairs), reverse=True)
    true_positives = 0.0
    seen = 0
    precision_sum = 0.0
    for threshold in thresholds:
        group = [row for row in pairs if row[0] == threshold]
        group_positives = sum(row[1] for row in group)
        true_positives = true_positives + group_positives
        seen = seen + len(group)
        if group_positives > 0.0:
            precision_sum = precision_sum + (
                group_positives / positive_count
            ) * (true_positives / seen)
    return precision_sum


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
    "zero_change_fraction_24h",
    "log_one_plus_quiet_run_hours_005",
]
samples = {}
excluded_history_span = 0
excluded_six_hour_span = 0
excluded_future_coverage = 0
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
                for ordinal in range(decision - 23, decision + 1):
                    step = points[(market, ordinal)][1] - points[(market, ordinal - 1)][1]
                    if step == 0.0:
                        zero_count = zero_count + 1.0
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
                    zero_count / 24.0,
                    log(1.0 + quiet_hours),
                ]
                crossed = 0.0
                future_ordinal = decision + 1
                while future_ordinal <= endpoint:
                    elapsed_hours = (
                        points[(market, future_ordinal)][0] - current[0]
                    ) / 3600.0
                    if elapsed_hours <= 48.0 and abs(
                        points[(market, future_ordinal)][1] - probability
                    ) >= 0.02:
                        crossed = 1.0
                        future_ordinal = endpoint + 1
                    else:
                        future_ordinal = future_ordinal + 1
                if event not in samples:
                    samples[event] = []
                samples[event] = samples[event] + [[features, crossed]]
        next_decision_time = current[0] + 172800.0
        decision = decision + 1
        while decision < length and points[(market, decision)][0] < next_decision_time:
            decision = decision + 1

groups = {
    "state_only": [0, 1, 2],
    "state_staleness": [0, 1, 2, 3, 4],
}
predictions = {"event_rate": []}
for group_name in groups:
    predictions[group_name] = []

for test_event in range(8, 24):
    if test_event in samples:
        training_events = [event for event in range(test_event) if event in samples]
        if len(training_events) >= 2:
            baseline = sum(
                sum(row[1] for row in samples[event]) / len(samples[event])
                for event in training_events
            ) / len(training_events)
            models = {}
            for group_name in groups:
                models[group_name] = fit_ridge(
                    samples, training_events, groups[group_name], 0.1
                )
            for row in samples[test_event]:
                predictions["event_rate"] = predictions["event_rate"] + [
                    [test_event, baseline, row[1]]
                ]
                for group_name in groups:
                    predictions[group_name] = predictions[group_name] + [
                        [
                            test_event,
                            predict(models[group_name], groups[group_name], row[0]),
                            row[1],
                        ]
                    ]

results = []
result_by_name = {}
for model_name in ["event_rate", "state_only", "state_staleness"]:
    rows = predictions[model_name]
    squared_errors = [(row[2] - row[1]) * (row[2] - row[1]) for row in rows]
    event_metrics = []
    event_average_precisions = []
    for event in range(8, 24):
        event_rows = [row for row in rows if row[0] == event]
        if len(event_rows) > 0:
            event_brier = sum(
                (row[2] - row[1]) * (row[2] - row[1]) for row in event_rows
            ) / len(event_rows)
            event_ap = average_precision([[row[1], row[2]] for row in event_rows])
            event_metrics = event_metrics + [
                {
                    "event": event,
                    "row_count": len(event_rows),
                    "positive_count": sum(row[2] for row in event_rows),
                    "brier": event_brier,
                    "average_precision": event_ap,
                }
            ]
            if event_ap is not None:
                event_average_precisions = event_average_precisions + [event_ap]
    midpoint = len(event_metrics) // 2
    result_item = {
        "model": model_name,
        "feature_names": []
        if model_name == "event_rate"
        else [feature_names[index] for index in groups[model_name]],
        "prediction_count": len(rows),
        "positive_count": sum(row[2] for row in rows),
        "observation_brier": sum(squared_errors) / len(squared_errors),
        "event_macro_brier": sum(row["brier"] for row in event_metrics)
        / len(event_metrics),
        "pooled_average_precision": average_precision(
            [[row[1], row[2]] for row in rows]
        ),
        "event_macro_average_precision": sum(event_average_precisions)
        / len(event_average_precisions),
        "early_event_macro_brier": sum(
            row["brier"] for row in event_metrics[:midpoint]
        )
        / midpoint,
        "late_event_macro_brier": sum(
            row["brier"] for row in event_metrics[midpoint:]
        )
        / (len(event_metrics) - midpoint),
        "mean_prediction": sum(row[1] for row in rows) / len(rows),
        "incidence": sum(row[2] for row in rows) / len(rows),
        "event_metrics": event_metrics,
    }
    results = results + [result_item]
    result_by_name[model_name] = result_item

baseline = result_by_name["event_rate"]
state = result_by_name["state_only"]
candidate = result_by_name["state_staleness"]
state_event_by_id = {row["event"]: row for row in state["event_metrics"]}
event_wins = sum(
    1
    for row in candidate["event_metrics"]
    if row["brier"] < state_event_by_id[row["event"]]["brier"]
)
mixed_events = sum(
    1
    for row in candidate["event_metrics"]
    if row["positive_count"] > 0 and row["positive_count"] < row["row_count"]
)
negative_count = candidate["prediction_count"] - candidate["positive_count"]
gate_passed = (
    candidate["prediction_count"] >= 500
    and candidate["positive_count"] >= 100
    and negative_count >= 100
    and mixed_events >= 10
    and candidate["observation_brier"] < baseline["observation_brier"]
    and candidate["event_macro_brier"] < baseline["event_macro_brier"]
    and candidate["observation_brier"] < state["observation_brier"]
    and candidate["event_macro_brier"] < state["event_macro_brier"]
    and candidate["pooled_average_precision"] > baseline["pooled_average_precision"]
    and candidate["event_macro_average_precision"]
    > baseline["event_macro_average_precision"]
    and candidate["pooled_average_precision"] > state["pooled_average_precision"]
    and candidate["event_macro_average_precision"]
    > state["event_macro_average_precision"]
    and candidate["early_event_macro_brier"] < state["early_event_macro_brier"]
    and candidate["late_event_macro_brier"] < state["late_event_macro_brier"]
    and event_wins >= 0.60 * len(candidate["event_metrics"])
    and candidate["observation_brier"] <= 0.20
    and candidate["event_macro_brier"] <= 0.20
    and abs(candidate["mean_prediction"] - candidate["incidence"]) <= 0.10
)


def top_quintile_metrics(rows):
    event_metrics = []
    for event in range(8, 24):
        event_rows = [row for row in rows if row[0] == event]
        positive_count = sum(row[2] for row in event_rows)
        if (
            len(event_rows) >= 2
            and positive_count > 0.0
            and positive_count < len(event_rows)
        ):
            target_count = max(1, (len(event_rows) + 4) // 5)
            ordered_scores = sorted(
                [row[1] for row in event_rows], reverse=True
            )
            threshold = ordered_scores[target_count - 1]
            selected = [row for row in event_rows if row[1] >= threshold]
            remainder = [row for row in event_rows if row[1] < threshold]
            if len(remainder) > 0:
                selected_incidence = sum(row[2] for row in selected) / len(selected)
                remainder_incidence = sum(row[2] for row in remainder) / len(remainder)
                event_metrics = event_metrics + [
                    {
                        "event": event,
                        "row_count": len(event_rows),
                        "selected_count": len(selected),
                        "selected_fraction": len(selected) / len(event_rows),
                        "selected_incidence": selected_incidence,
                        "remainder_incidence": remainder_incidence,
                        "incidence_lift": selected_incidence - remainder_incidence,
                    }
                ]
    midpoint = len(event_metrics) // 2
    return {
        "eligible_event_count": len(event_metrics),
        "positive_lift_event_count": sum(
            1 for row in event_metrics if row["incidence_lift"] > 0.0
        ),
        "event_macro_incidence_lift": sum(
            row["incidence_lift"] for row in event_metrics
        )
        / len(event_metrics),
        "early_event_macro_incidence_lift": sum(
            row["incidence_lift"] for row in event_metrics[:midpoint]
        )
        / midpoint,
        "late_event_macro_incidence_lift": sum(
            row["incidence_lift"] for row in event_metrics[midpoint:]
        )
        / (len(event_metrics) - midpoint),
        "event_metrics": event_metrics,
    }


state_quintile = top_quintile_metrics(predictions["state_only"])
candidate_quintile = top_quintile_metrics(predictions["state_staleness"])
state_quintile_by_event = {
    row["event"]: row for row in state_quintile["event_metrics"]
}
quintile_event_wins = sum(
    1
    for row in candidate_quintile["event_metrics"]
    if row["incidence_lift"]
    > state_quintile_by_event[row["event"]]["incidence_lift"]
)
quintile_gate_passed = (
    candidate_quintile["eligible_event_count"] >= 10
    and candidate_quintile["event_macro_incidence_lift"] >= 0.20
    and candidate_quintile["positive_lift_event_count"]
    >= 0.60 * candidate_quintile["eligible_event_count"]
    and candidate_quintile["early_event_macro_incidence_lift"] >= 0.10
    and candidate_quintile["late_event_macro_incidence_lift"] >= 0.10
    and candidate_quintile["event_macro_incidence_lift"]
    > state_quintile["event_macro_incidence_lift"]
    and quintile_event_wins >= 0.60 * candidate_quintile["eligible_event_count"]
)

result = structured_return(
    "Top-quintile stability test for 48-hour sampled movement-risk ranking.",
    {
        "schema_version": "polymarket-48h-move-top-quintile/v1",
        "feature_names": feature_names,
        "sampling": {
            "excluded_history_span": excluded_history_span,
            "excluded_six_hour_span": excluded_six_hour_span,
            "excluded_future_coverage": excluded_future_coverage,
        },
        "results": results,
        "state_staleness_event_wins_vs_state": event_wins,
        "mixed_test_event_count": mixed_events,
        "negative_count": negative_count,
        "predeclared_transfer_gate_passed": gate_passed,
        "top_quintile": {
            "state_only": state_quintile,
            "state_staleness": candidate_quintile,
            "state_staleness_event_wins_vs_state": quintile_event_wins,
            "predeclared_top_quintile_gate_passed": quintile_gate_passed,
        },
        "protected_values_exposed": False,
    },
    warnings=[
        "Features were selected on the related continuous-duration development question.",
        "A sampled crossing is not continuous-time passage or executable-price evidence.",
        "Non-overlapping outcome windows reduce but do not eliminate dependence.",
        "The within-event top quintile was fixed before execution; ties remain selected.",
        "Passing this diagnostic would support ranking interpretation, not calibration.",
        "Protected values remain unavailable.",
    ],
)
