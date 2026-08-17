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
    feature_count = 6
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
    for index in range(6):
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
            [0.0 for unused in range(6)],
            [1.0 for unused in range(6)],
            [0.0 for unused in range(6)],
            len(selected),
        ]
    feature_mean = [0.0 for unused in range(6)]
    second = [[0.0 for unused in range(6)] for unused in range(6)]
    cross_target = [0.0 for unused in range(6)]
    for item in selected:
        row = item[0]
        event = row[3]
        weight = 1.0 / (event_total * event_counts[event])
        for left in range(6):
            left_value = row[6][left]
            feature_mean[left] = feature_mean[left] + weight * left_value
            cross_target[left] = cross_target[left] + weight * left_value * item[1]
            for right in range(6):
                second[left][right] = second[left][right] + weight * left_value * row[6][right]
    scale = [0.0 for unused in range(6)]
    covariance = [[0.0 for unused in range(6)] for unused in range(6)]
    target_covariance = [0.0 for unused in range(6)]
    for left in range(6):
        variance = second[left][left] - feature_mean[left] * feature_mean[left]
        if variance < 0.000000000001:
            variance = 0.000000000001
        scale[left] = variance ** 0.5
    for left in range(6):
        target_covariance[left] = (
            cross_target[left] - feature_mean[left] * target_mean
        ) / scale[left]
        for right in range(6):
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
    for index in range(6):
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
                max_step = 0.0
                zero_count = 0.0
                absolute_sum = 0.0
                for index in range(1, len(recent)):
                    step = recent[index] - recent[index - 1]
                    absolute_step = abs(step)
                    rv24 = rv24 + step * step
                    absolute_sum = absolute_sum + absolute_step
                    if absolute_step == 0.0:
                        zero_count = zero_count + 1.0
                    if absolute_step > max_step:
                        max_step = absolute_step
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
                    features = [
                        min(probability, 1.0 - probability),
                        1.0 if probability <= 0.02 or probability >= 0.98 else 0.0,
                        rv6,
                        max_step / ((rv24 + 0.000000000001) ** 0.5),
                        zero_count / 24.0,
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
large_warmup_predictions = 0
for ordinal in range(len(examples)):
    if ordinal >= 40:
        validation = examples[ordinal]
        training = [row for row in examples[:ordinal] if row[1] <= validation[0]]
        if len(training) >= 40:
            activity_model = fit_models(training)
            activity_ridge = ridge_prediction(activity_model, validation[6])
            gate_model = fit_stage(training, "gate", "all")
            small_model = fit_stage(training, "magnitude", "small")
            large_model = fit_stage(training, "magnitude", "large")
            probability_large = stage_prediction(gate_model, validation[6])
            hurdle_mean = (
                (1.0 - probability_large) * small_model[0]
                + probability_large * large_model[0]
            )
            hurdle_ridge = (
                (1.0 - probability_large) * stage_prediction(small_model, validation[6])
                + probability_large * stage_prediction(large_model, validation[6])
            )
            if large_model[4] < 8:
                large_warmup_predictions = large_warmup_predictions + 1
            actual = validation[7]
            gate_actual = 1.0 if actual >= 0.05 else 0.0
            evaluated = evaluated + [validation + [
                (activity_ridge - actual) ** 2,
                (hurdle_mean - actual) ** 2,
                (hurdle_ridge - actual) ** 2,
                (probability_large - gate_actual) ** 2,
                activity_ridge,
                hurdle_mean,
                hurdle_ridge,
                probability_large,
            ]]

activity_mse = sum(row[9] for row in evaluated) / len(evaluated)
hurdle_mean_mse = sum(row[10] for row in evaluated) / len(evaluated)
hurdle_ridge_mse = sum(row[11] for row in evaluated) / len(evaluated)
gate_brier = sum(row[12] for row in evaluated) / len(evaluated)
large_rate = sum(1 for row in evaluated if row[7] >= 0.05) / len(evaluated)
mean_gate_prediction = sum(row[16] for row in evaluated) / len(evaluated)

result = structured_return(
    "Two fixed fold-local hurdle recipes on the exact formal activity-panel replay.",
    {
        "parent_diagnostic_source_sha256": "20445367ff299f2e8d7ce187b90de0e66bf8774d052dedd4be6b60a1936650f7",
        "declared_sample_count": len(examples),
        "oof_prediction_count": len(evaluated),
        "large_move_threshold": 0.05,
        "ridge_penalty": 0.1,
        "conditional_ridge_minimum_rows": 8,
        "large_regime_warmup_prediction_count": large_warmup_predictions,
        "observed_large_move_rate": large_rate,
        "mean_predicted_large_move_probability": mean_gate_prediction,
        "large_move_gate_brier": gate_brier,
        "activity_ridge": {
            "observation_weighted_mse": activity_mse,
            **event_summary(evaluated, 9, 9),
        },
        "hurdle_conditional_means": {
            "observation_weighted_mse": hurdle_mean_mse,
            "mse_delta_vs_activity_ridge": hurdle_mean_mse - activity_mse,
            **event_summary(evaluated, 10, 9),
        },
        "hurdle_conditional_ridges": {
            "observation_weighted_mse": hurdle_ridge_mse,
            "mse_delta_vs_activity_ridge": hurdle_ridge_mse - activity_mse,
            **event_summary(evaluated, 11, 9),
        },
    },
    warnings=[
        "The five-cent gate was selected from development loss diagnostics and is selection-exposed.",
        "Every gate, conditional mean, and conditional ridge is refit from legally matured rows at each decision.",
        "The intercept-only conditional warm-up below eight legal regime rows is predeclared model behavior.",
        "This two-recipe budget does not authorize threshold search or protected exposure.",
    ],
)
