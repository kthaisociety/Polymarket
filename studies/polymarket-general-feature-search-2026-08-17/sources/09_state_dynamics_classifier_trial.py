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


def fit_models(training):
    feature_count = 11
    event_counts = {}
    for row in training:
        event = row[3]
        if event not in event_counts:
            event_counts[event] = 0
        event_counts[event] = event_counts[event] + 1
    event_total = len(event_counts)
    target_mean = 0.0
    feature_mean = [0.0 for unused in range(feature_count)]
    second = [[0.0 for unused in range(feature_count)] for unused in range(feature_count)]
    cross_target = [0.0 for unused in range(feature_count)]
    for row in training:
        weight = 1.0 / (event_total * event_counts[row[3]])
        target_mean = target_mean + weight * row[7]
        for left in range(feature_count):
            left_value = row[6][left]
            feature_mean[left] = feature_mean[left] + weight * left_value
            cross_target[left] = cross_target[left] + weight * left_value * row[7]
            for right in range(feature_count):
                second[left][right] = second[left][right] + weight * left_value * row[6][right]
    scale = [0.0 for unused in range(feature_count)]
    covariance = [[0.0 for unused in range(feature_count)] for unused in range(feature_count)]
    target_covariance = [0.0 for unused in range(feature_count)]
    for left in range(feature_count):
        variance = second[left][left] - feature_mean[left] * feature_mean[left]
        if variance < 0.000000000001:
            variance = 0.000000000001
        scale[left] = variance ** 0.5
    for left in range(feature_count):
        target_covariance[left] = (cross_target[left] - feature_mean[left] * target_mean) / scale[left]
        for right in range(feature_count):
            covariance[left][right] = (
                second[left][right] - feature_mean[left] * feature_mean[right]
            ) / (scale[left] * scale[right])
        covariance[left][left] = covariance[left][left] + 0.1
    return [target_mean, feature_mean, scale, solve_linear(covariance, target_covariance)]


def ridge_prediction(model, features):
    prediction = model[0]
    for index in range(11):
        prediction = prediction + model[3][index] * (
            features[index] - model[1][index]
        ) / model[2][index]
    return min(1.0, max(0.0, prediction))


def fit_stage(training, target_kind, regime):
    selected = []
    for row in training:
        include = True
        if regime == "small" and row[7] >= 0.05:
            include = False
        if regime == "large" and row[7] < 0.05:
            include = False
        if include:
            target = row[7]
            if target_kind == "gate":
                target = 1.0 if row[7] >= 0.05 else 0.0
            if target_kind == "gate002":
                target = 1.0 if row[7] >= 0.02 else 0.0
            selected = selected + [[row, target]]
    event_counts = {}
    for item in selected:
        event = item[0][3]
        if event not in event_counts:
            event_counts[event] = 0
        event_counts[event] = event_counts[event] + 1
    event_total = len(event_counts)
    target_mean = 0.0
    for item in selected:
        event = item[0][3]
        target_mean = target_mean + item[1] / (event_total * event_counts[event])
    if len(selected) < 8:
        return [
            target_mean,
            [0.0 for unused in range(11)],
            [1.0 for unused in range(11)],
            [0.0 for unused in range(11)],
            len(selected),
        ]
    feature_mean = [0.0 for unused in range(11)]
    second = [[0.0 for unused in range(11)] for unused in range(11)]
    cross_target = [0.0 for unused in range(11)]
    for item in selected:
        row = item[0]
        event = row[3]
        weight = 1.0 / (event_total * event_counts[event])
        for left in range(11):
            left_value = row[6][left]
            feature_mean[left] = feature_mean[left] + weight * left_value
            cross_target[left] = cross_target[left] + weight * left_value * item[1]
            for right in range(11):
                second[left][right] = second[left][right] + weight * left_value * row[6][right]
    scale = [0.0 for unused in range(11)]
    covariance = [[0.0 for unused in range(11)] for unused in range(11)]
    target_covariance = [0.0 for unused in range(11)]
    for left in range(11):
        variance = second[left][left] - feature_mean[left] * feature_mean[left]
        if variance < 0.000000000001:
            variance = 0.000000000001
        scale[left] = variance ** 0.5
    for left in range(11):
        target_covariance[left] = (
            cross_target[left] - feature_mean[left] * target_mean
        ) / scale[left]
        for right in range(11):
            covariance[left][right] = (
                second[left][right] - feature_mean[left] * feature_mean[right]
            ) / (scale[left] * scale[right])
        covariance[left][left] = covariance[left][left] + 0.1
    return [
        target_mean,
        feature_mean,
        scale,
        solve_linear(covariance, target_covariance),
        len(selected),
    ]


def stage_prediction(model, features):
    prediction = model[0]
    for index in range(11):
        prediction = prediction + model[3][index] * (
            features[index] - model[1][index]
        ) / model[2][index]
    return min(1.0, max(0.0, prediction))


def event_summary(evaluated, error_index, comparator_index):
    groups = {}
    for row in evaluated:
        event = row[3]
        if event not in groups:
            groups[event] = [0, 0.0, 0.0]
        groups[event][0] = groups[event][0] + 1
        groups[event][1] = groups[event][1] + row[error_index]
        groups[event][2] = groups[event][2] + row[comparator_index]
    values = []
    wins = 0
    early = []
    late = []
    for event in sorted(groups):
        mse = groups[event][1] / groups[event][0]
        comparator = groups[event][2] / groups[event][0]
        values = values + [mse]
        if mse < comparator:
            wins = wins + 1
        if event < 12:
            early = early + [mse]
        else:
            late = late + [mse]
    return {
        "event_count": len(values),
        "event_macro_mse": sum(values) / len(values),
        "event_wins_vs_activity_ridge": wins,
        "early_event_macro_mse": sum(early) / len(early),
        "late_event_macro_mse": sum(late) / len(late),
    }


def add_group(groups, name, row):
    if name not in groups:
        groups[name] = [0, 0.0, 0.0, 0.0, 0, 0.0]
    group = groups[name]
    group[0] = group[0] + 1
    group[1] = group[1] + row[9]
    group[2] = group[2] + row[10]
    group[3] = group[3] + row[7]
    if row[7] >= 0.02:
        group[4] = group[4] + 1
    group[5] = group[5] + row[8]


def group_rows(groups):
    result = []
    for name in sorted(groups):
        group = groups[name]
        result = result + [{
            "group": name,
            "count": group[0],
            "baseline_mse": group[1] / group[0],
            "ridge_mse": group[2] / group[0],
            "ridge_improvement": (group[1] - group[2]) / group[0],
            "mean_label": group[3] / group[0],
            "large_move_rate_002": group[4] / group[0],
            "mean_probability": group[5] / group[0],
        }]
    return result


def example_order(row):
    return [row[0], row[3], row[2]]


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

examples = []
for market in market_order:
    legal = []
    for decision in range(24, market_lengths[market] - 6, 6):
        current = points[(market, decision)]
        trailing = points[(market, decision - 24)]
        future = points[(market, decision + 6)]
        trailing_hours = (current[0] - trailing[0]) / 3600.0
        future_hours = (future[0] - current[0]) / 3600.0
        if 18.0 <= trailing_hours <= 30.0 and 4.5 <= future_hours <= 7.5:
            legal = legal + [decision]
    if len(legal) > 0:
        selected = [0, len(legal) // 2, len(legal) - 1]
        used = {}
        for position_index in range(len(selected)):
            legal_index = selected[position_index]
            if legal_index not in used:
                used[legal_index] = True
                decision = legal[legal_index]
                current = points[(market, decision)]
                recent = [points[(market, index)][1] for index in range(decision - 24, decision + 1)]
                probability = current[1]
                rv6 = 0.0
                rv24 = 0.0
                bipower = 0.0
                max_step = 0.0
                zero_count = 0.0
                absolute_sum = 0.0
                previous_abs = 0.0
                for index in range(1, len(recent)):
                    step = recent[index] - recent[index - 1]
                    absolute_step = abs(step)
                    rv24 = rv24 + step * step
                    absolute_sum = absolute_sum + absolute_step
                    if absolute_step == 0.0:
                        zero_count = zero_count + 1.0
                    if absolute_step > max_step:
                        max_step = absolute_step
                    if index > 1:
                        bipower = bipower + previous_abs * absolute_step
                    previous_abs = absolute_step
                    if index >= len(recent) - 6:
                        rv6 = rv6 + step * step
                outcome_end = current[0] + 6.0 * 3600.0
                outcome_value = None
                for future_index in range(decision + 1, market_lengths[market]):
                    future_point = points[(market, future_index)]
                    if future_point[0] <= outcome_end:
                        outcome_value = future_point[1]
                    else:
                        break
                if outcome_value is not None:
                    clipped = min(0.995, max(0.005, probability))
                    jump_variation = max(
                        0.0,
                        rv24 - 1.5707963267948966 * bipower,
                    )
                    features = [
                        probability,
                        min(probability, 1.0 - probability),
                        log(clipped / (1.0 - clipped)),
                        1.0 if probability <= 0.02 or probability >= 0.98 else 0.0,
                        rv6,
                        rv24,
                        jump_variation,
                        max_step / ((rv24 + 0.000000000001) ** 0.5),
                        zero_count / 24.0,
                        probability - points[(market, decision - 6)][1],
                        absolute_sum / 24.0,
                    ]
                    position = "first"
                    if position_index == 1:
                        position = "middle"
                    if position_index == 2:
                        position = "last"
                    examples = examples + [[
                        current[0],
                        outcome_end,
                        market,
                        market_events[market],
                        position,
                        decision,
                        features,
                        abs(outcome_value - probability),
                        probability,
                    ]]

examples = sorted(examples, key=example_order)
evaluated = []
for ordinal in range(len(examples)):
    if ordinal >= 40:
        validation = examples[ordinal]
        training = [row for row in examples[:ordinal] if row[1] <= validation[0]]
        if len(training) >= 40:
            gate_model = fit_stage(training, "gate002", "all")
            baseline_probability = gate_model[0]
            ridge_probability = stage_prediction(gate_model, validation[6])
            actual = 1.0 if validation[7] >= 0.02 else 0.0
            evaluated = evaluated + [validation + [
                (baseline_probability - actual) ** 2,
                (ridge_probability - actual) ** 2,
                baseline_probability,
                ridge_probability,
                actual,
            ]]

baseline_brier = sum(row[9] for row in evaluated) / len(evaluated)
ridge_brier = sum(row[10] for row in evaluated) / len(evaluated)
observed_rate = sum(row[13] for row in evaluated) / len(evaluated)
mean_baseline = sum(row[11] for row in evaluated) / len(evaluated)
mean_ridge = sum(row[12] for row in evaluated) / len(evaluated)

result = structured_return(
    "Benchmark-derived state-plus-dynamics classifier on the exact formal panel replay.",
    {
        "parent_compact_classifier_source_sha256": "6f8f900131330ae0e315e879d143258cb39cebd76da4db6b91c19561c3c97273",
        "declared_sample_count": len(examples),
        "oof_prediction_count": len(evaluated),
        "large_move_threshold": 0.02,
        "ridge_penalty": 0.1,
        "feature_names": [
            "probability_level",
            "boundary_distance",
            "winsorized_logit_level_005",
            "current_boundary_state_002",
            "realized_variance_6h",
            "realized_variance_24h",
            "bipower_jump_variation_24h",
            "jump_concentration_24h",
            "zero_change_fraction_24h",
            "raw_change_6h",
            "mean_absolute_change_24h",
        ],
        "observed_large_move_rate": observed_rate,
        "mean_baseline_probability": mean_baseline,
        "mean_ridge_probability": mean_ridge,
        "event_rate_baseline": {
            "observation_weighted_brier": baseline_brier,
            **event_summary(evaluated, 9, 9),
        },
        "state_plus_dynamics_linear_probability_ridge": {
            "observation_weighted_brier": ridge_brier,
            "brier_delta_vs_baseline": ridge_brier - baseline_brier,
            **event_summary(evaluated, 10, 9),
        },
        "preformal_gate": {
            "maximum_brier": 0.15,
            "minimum_event_wins": 12,
            "requires_both_aggregate_improvements": True,
        },
    },
    warnings=[
        "The two-cent label and threshold were fixed in benchmark 01 rather than selected here.",
        "The exact no-expiry feature set is benchmark 01 state_plus_dynamics, not a new subset search.",
        "Every event rate, feature mean, scale, and ridge coefficient is refit from legally matured rows.",
        "This is selection-exposed development evidence and not a protected calibration claim.",
        "Classification of movement incidence does not predict direction or executable value.",
    ],
)
