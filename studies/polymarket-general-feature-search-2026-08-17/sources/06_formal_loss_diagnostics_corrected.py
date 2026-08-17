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
for ordinal in range(len(examples)):
    if ordinal >= 40:
        validation = examples[ordinal]
        training = [row for row in examples[:ordinal] if row[1] <= validation[0]]
        if len(training) >= 40:
            model = fit_models(training)
            baseline = model[0]
            ridge = ridge_prediction(model, validation[6])
            baseline_squared = (baseline - validation[7]) ** 2
            ridge_squared = (ridge - validation[7]) ** 2
            evaluated = evaluated + [validation + [baseline_squared, ridge_squared, baseline, ridge]]

baseline_mse = sum(row[9] for row in evaluated) / len(evaluated)
ridge_mse = sum(row[10] for row in evaluated) / len(evaluated)
event_groups = {}
market_groups = {}
position_groups = {}
boundary_groups = {}
label_groups = {}
for row in evaluated:
    add_group(event_groups, str(row[3]), row)
    add_group(market_groups, row[2], row)
    add_group(position_groups, row[4], row)
    distance = row[6][0]
    boundary_group = "d_gt_025"
    if distance <= 0.02:
        boundary_group = "d_le_002"
    elif distance <= 0.10:
        boundary_group = "d_002_010"
    elif distance <= 0.25:
        boundary_group = "d_010_025"
    add_group(boundary_groups, boundary_group, row)
    label_group = "move_ge_005"
    if row[7] < 0.01:
        label_group = "move_lt_001"
    elif row[7] < 0.02:
        label_group = "move_001_002"
    elif row[7] < 0.05:
        label_group = "move_002_005"
    add_group(label_groups, label_group, row)

event_rows = group_rows(event_groups)
event_wins = sum(1 for row in event_rows if row["ridge_improvement"] > 0.0)
market_errors = sorted([market_groups[name][2] for name in market_groups], reverse=True)
row_errors = sorted([row[10] for row in evaluated], reverse=True)
total_market_error = sum(market_errors)
total_row_error = sum(row_errors)

result = structured_return(
    "Exact formal-panel loss attribution under the unchanged expanding replay.",
    {
        "parent_formal_source_sha256": "0c4fcbdb0b33fc55dd32a889b1d740337ebf516eef28de80aac436aa74221da5",
        "declared_sample_count": len(examples),
        "oof_prediction_count": len(evaluated),
        "baseline_mse": baseline_mse,
        "ridge_mse": ridge_mse,
        "formal_baseline_mse_difference": baseline_mse - 0.006012147376061004,
        "formal_ridge_mse_difference": ridge_mse - 0.005546054042085273,
        "event_mse_wins_vs_baseline": event_wins,
        "event_rows": event_rows,
        "position_rows": group_rows(position_groups),
        "boundary_rows": group_rows(boundary_groups),
        "label_magnitude_rows": group_rows(label_groups),
        "ridge_error_concentration": {
            "largest_row_share": row_errors[0] / total_row_error,
            "top_1_percent_row_share": sum(row_errors[:max(1, len(row_errors) // 100)]) / total_row_error,
            "top_5_percent_row_share": sum(row_errors[:max(1, len(row_errors) // 20)]) / total_row_error,
            "largest_market_share": market_errors[0] / total_market_error,
            "top_5_market_share": sum(market_errors[:5]) / total_market_error,
            "top_10_market_share": sum(market_errors[:10]) / total_market_error,
        },
    },
    warnings=[
        "This diagnostic is selection-exposed and cannot make the failed candidate freeze-eligible.",
        "Groups use matured labels for diagnosis only; label-magnitude buckets are not predictors.",
        "Current close time and all protected events remain unavailable to this source.",
        "The diagnostic must reproduce formal receipt 04 before its slices are interpreted.",
    ],
)
