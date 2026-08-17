price_markets = read("polymarket-development-prices", "market_id")
price_events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")
outcome_markets = read("polymarket-development-outcomes", "market_id")
close_times = read("polymarket-development-outcomes", "close_time_epoch_seconds")


def logit(probability):
    return log(probability / (1.0 - probability))


def inverse_logit(value):
    if value >= 0.0:
        negative = exp(-value)
        return 1.0 / (1.0 + negative)
    positive = exp(value)
    return positive / (1.0 + positive)


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
    solution = [0.0 for unused in range(size)]
    for row in range(size):
        solution[row] = augmented[row][size]
    return solution


def fit_equal_event_ridge(test_event, aggregates, feature_count, penalty, target_slot):
    event_weight = 0.0
    feature_mean = [0.0 for unused in range(feature_count)]
    target_mean = 0.0
    second = [None for unused in range(feature_count)]
    cross_target = [0.0 for unused in range(feature_count)]
    for left in range(feature_count):
        second[left] = [0.0 for unused in range(feature_count)]
    for event in range(test_event):
        if event in aggregates:
            aggregate = aggregates[event]
            count = aggregate[0]
            event_weight = event_weight + 1.0
            target_mean = target_mean + aggregate[target_slot] / count
            for left in range(feature_count):
                feature_mean[left] = feature_mean[left] + aggregate[1][left] / count
                cross_target[left] = (
                    cross_target[left] + aggregate[target_slot + 2][left] / count
                )
                for right in range(feature_count):
                    second[left][right] = (
                        second[left][right] + aggregate[2][left][right] / count
                    )
    target_mean = target_mean / event_weight
    for feature in range(feature_count):
        feature_mean[feature] = feature_mean[feature] / event_weight
        cross_target[feature] = cross_target[feature] / event_weight
        for right in range(feature_count):
            second[feature][right] = second[feature][right] / event_weight
    scale = [0.0 for unused in range(feature_count)]
    for feature in range(feature_count):
        variance = second[feature][feature] - feature_mean[feature] * feature_mean[feature]
        if variance < 0.000000000001:
            variance = 0.000000000001
        scale[feature] = variance ** 0.5
    covariance = [None for unused in range(feature_count)]
    target_covariance = [0.0 for unused in range(feature_count)]
    for left in range(feature_count):
        covariance[left] = [0.0 for unused in range(feature_count)]
        target_covariance[left] = (
            cross_target[left] - feature_mean[left] * target_mean
        ) / scale[left]
        for right in range(feature_count):
            covariance[left][right] = (
                second[left][right] - feature_mean[left] * feature_mean[right]
            ) / (scale[left] * scale[right])
        covariance[left][left] = covariance[left][left] + penalty
    coefficients = solve_linear(covariance, target_covariance)
    return [target_mean, feature_mean, scale, coefficients]


epsilon = 0.005
feature_count = 9
ridge_penalty = 0.1
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

close_by_market = {}
for row in range(len(outcome_markets)):
    close_by_market[outcome_markets[row]] = close_times[row]

samples = {}
event_sample_count = {}
aggregates = {}
excluded_irregular = 0
excluded_boundary = 0
for market in market_order:
    event = market_events[market]
    length = market_lengths[market]
    for decision in range(24, length - 2):
        start = points[(market, decision - 24)]
        current = points[(market, decision)]
        next_point = points[(market, decision + 1)]
        delayed_exit = points[(market, decision + 2)]
        trailing_hours = (current[0] - start[0]) / 3600.0
        next_hours = (next_point[0] - current[0]) / 3600.0
        delayed_hours = (delayed_exit[0] - next_point[0]) / 3600.0
        if (
            trailing_hours < 18.0
            or trailing_hours > 30.0
            or next_hours < 0.75
            or next_hours > 1.25
            or delayed_hours < 0.75
            or delayed_hours > 1.25
        ):
            excluded_irregular = excluded_irregular + 1
        else:
            interior = True
            raw_rv_6 = 0.0
            raw_rv_24 = 0.0
            logit_rv_6 = 0.0
            for ordinal in range(decision - 24, decision + 1):
                probability = points[(market, ordinal)][1]
                if probability <= epsilon or probability >= 1.0 - epsilon:
                    interior = False
            if not interior:
                excluded_boundary = excluded_boundary + 1
            else:
                for ordinal in range(decision - 23, decision + 1):
                    left = points[(market, ordinal - 1)][1]
                    right = points[(market, ordinal)][1]
                    raw_step = right - left
                    raw_rv_24 = raw_rv_24 + raw_step * raw_step
                    if ordinal >= decision - 5:
                        raw_rv_6 = raw_rv_6 + raw_step * raw_step
                        logit_step = logit(right) - logit(left)
                        logit_rv_6 = logit_rv_6 + logit_step * logit_step
                previous = points[(market, decision - 1)][1]
                probability = current[1]
                raw_change = probability - previous
                logit_change = logit(probability) - logit(previous)
                boundary_distance = min(probability, 1.0 - probability)
                hours_to_close = max(0.0, (close_by_market[market] - current[0]) / 3600.0)
                features = [
                    raw_change,
                    logit_change,
                    logit(probability),
                    boundary_distance,
                    raw_rv_6,
                    raw_rv_24,
                    logit_rv_6,
                    raw_change * raw_rv_6,
                    log(1.0 + hours_to_close),
                ]
                direction_target = next_point[1] - probability
                magnitude_target = abs(direction_target)
                delayed_target = delayed_exit[1] - next_point[1]
                if event not in event_sample_count:
                    event_sample_count[event] = 0
                    feature_sum = [0.0 for unused in range(feature_count)]
                    feature_cross = [None for unused in range(feature_count)]
                    for left in range(feature_count):
                        feature_cross[left] = [0.0 for unused in range(feature_count)]
                    aggregates[event] = [
                        0,
                        feature_sum,
                        feature_cross,
                        0.0,
                        0.0,
                        [0.0 for unused in range(feature_count)],
                        [0.0 for unused in range(feature_count)],
                    ]
                count = event_sample_count[event]
                samples[(event, count)] = [
                    features,
                    probability,
                    direction_target,
                    magnitude_target,
                    delayed_target,
                ]
                event_sample_count[event] = count + 1
                aggregate = aggregates[event]
                aggregate[0] = aggregate[0] + 1
                aggregate[3] = aggregate[3] + direction_target
                aggregate[4] = aggregate[4] + magnitude_target
                for left in range(feature_count):
                    aggregate[1][left] = aggregate[1][left] + features[left]
                    aggregate[5][left] = (
                        aggregate[5][left] + features[left] * direction_target
                    )
                    aggregate[6][left] = (
                        aggregate[6][left] + features[left] * magnitude_target
                    )
                    for right in range(feature_count):
                        aggregate[2][left][right] = (
                            aggregate[2][left][right] + features[left] * features[right]
                        )

direction_models = [
    "martingale",
    "raw_ols",
    "fixed_logit_reversal",
    "boundary_volatility_ridge",
]
magnitude_models = ["earlier_event_mean", "boundary_volatility_ridge"]
direction_metrics = {}
magnitude_metrics = {}
coefficient_paths = []
test_events = []
for test_event in range(8, 24):
    if test_event not in event_sample_count or event_sample_count[test_event] == 0:
        continue
    ridge_direction = fit_equal_event_ridge(
        test_event, aggregates, feature_count, ridge_penalty, 3
    )
    ridge_magnitude = fit_equal_event_ridge(
        test_event, aggregates, feature_count, ridge_penalty, 4
    )
    raw_variance = ridge_direction[2][0] * ridge_direction[2][0]
    raw_covariance = 0.0
    raw_event_weight = 0.0
    for train_event in range(test_event):
        if train_event in aggregates:
            aggregate = aggregates[train_event]
            count = aggregate[0]
            raw_covariance = raw_covariance + aggregate[5][0] / count
            raw_event_weight = raw_event_weight + 1.0
    raw_covariance = raw_covariance / raw_event_weight
    raw_covariance = raw_covariance - ridge_direction[1][0] * ridge_direction[0]
    raw_slope = raw_covariance / raw_variance
    coefficient_paths = coefficient_paths + [
        {
            "test_event_ordinal": test_event,
            "raw_ols_intercept": ridge_direction[0] - raw_slope * ridge_direction[1][0],
            "raw_ols_slope": raw_slope,
            "ridge_direction_intercept_on_standardized_features": ridge_direction[0],
            "ridge_direction_coefficients": ridge_direction[3],
            "ridge_magnitude_intercept_on_standardized_features": ridge_magnitude[0],
            "ridge_magnitude_coefficients": ridge_magnitude[3],
        }
    ]
    test_events = test_events + [test_event]
    for model in direction_models:
        direction_metrics[(test_event, model)] = [
            0.0,
            0.0,
            0,
            0,
            0.0,
            0.0,
            0,
            0.0,
            0,
            0.0,
        ]
    for model in magnitude_models:
        magnitude_metrics[(test_event, model)] = [0.0, 0.0, 0]
    count = event_sample_count[test_event]
    for sample_index in range(count):
        sample = samples[(test_event, sample_index)]
        features = sample[0]
        probability = sample[1]
        target = sample[2]
        magnitude = sample[3]
        delayed_target = sample[4]
        ridge_prediction = ridge_direction[0]
        magnitude_prediction = ridge_magnitude[0]
        for feature in range(feature_count):
            standardized = (
                features[feature] - ridge_direction[1][feature]
            ) / ridge_direction[2][feature]
            ridge_prediction = (
                ridge_prediction + ridge_direction[3][feature] * standardized
            )
            standardized_magnitude = (
                features[feature] - ridge_magnitude[1][feature]
            ) / ridge_magnitude[2][feature]
            magnitude_prediction = (
                magnitude_prediction + ridge_magnitude[3][feature] * standardized_magnitude
            )
        magnitude_prediction = max(0.0, magnitude_prediction)
        for model in direction_models:
            if model == "martingale":
                prediction = 0.0
            elif model == "raw_ols":
                prediction = ridge_direction[0] + raw_slope * (
                    features[0] - ridge_direction[1][0]
                )
            elif model == "fixed_logit_reversal":
                predicted_probability = inverse_logit(features[2] - features[1])
                prediction = predicted_probability - probability
            else:
                prediction = max(-probability, min(1.0 - probability, ridge_prediction))
            metric = direction_metrics[(test_event, model)]
            error = target - prediction
            metric[0] = metric[0] + error * error
            metric[1] = metric[1] + abs(error)
            metric[2] = metric[2] + 1
            if prediction != 0.0 and target != 0.0:
                metric[3] = metric[3] + 1
                if prediction * target > 0.0:
                    metric[4] = metric[4] + 1
            if abs(prediction) > 0.01:
                direction = 1.0
                if prediction < 0.0:
                    direction = -1.0
                metric[5] = metric[5] + direction * target - 0.01
                metric[6] = metric[6] + 1
                metric[7] = metric[7] + direction * delayed_target - 0.01
                if direction > 0.0:
                    metric[8] = metric[8] + 1
                    metric[9] = metric[9] + delayed_target - 0.01
        baseline_magnitude = ridge_magnitude[0]
        for model in magnitude_models:
            if model == "earlier_event_mean":
                prediction = baseline_magnitude
            else:
                prediction = magnitude_prediction
            metric = magnitude_metrics[(test_event, model)]
            error = magnitude - prediction
            metric[0] = metric[0] + error * error
            metric[1] = metric[1] + abs(error)
            metric[2] = metric[2] + 1

direction_results = []
martingale_event_mse = {}
for event in test_events:
    metric = direction_metrics[(event, "martingale")]
    martingale_event_mse[event] = metric[0] / metric[2]
for model in direction_models:
    event_mse = []
    event_mae = []
    event_immediate_net = []
    event_delayed_net = []
    event_delayed_long_net = []
    total_squared = 0.0
    total_absolute = 0.0
    total_count = 0
    total_immediate_net = 0.0
    total_delayed_net = 0.0
    total_delayed_long_net = 0.0
    total_trade_count = 0
    total_long_count = 0
    mse_wins = 0
    delayed_positive = 0
    delayed_long_positive = 0
    for event in test_events:
        metric = direction_metrics[(event, model)]
        count = metric[2]
        current_mse = metric[0] / count
        event_mse = event_mse + [current_mse]
        event_mae = event_mae + [metric[1] / count]
        event_immediate_net = event_immediate_net + [metric[5] / count]
        event_delayed_net = event_delayed_net + [metric[7] / count]
        long_net = metric[9] / count
        event_delayed_long_net = event_delayed_long_net + [long_net]
        total_squared = total_squared + metric[0]
        total_absolute = total_absolute + metric[1]
        total_count = total_count + count
        total_immediate_net = total_immediate_net + metric[5]
        total_delayed_net = total_delayed_net + metric[7]
        total_trade_count = total_trade_count + metric[6]
        total_long_count = total_long_count + metric[8]
        total_delayed_long_net = total_delayed_long_net + metric[9]
        if current_mse < martingale_event_mse[event]:
            mse_wins = mse_wins + 1
        if metric[7] / count > 0.0:
            delayed_positive = delayed_positive + 1
        if long_net > 0.0:
            delayed_long_positive = delayed_long_positive + 1
    direction_results = direction_results + [
        {
            "model": model,
            "event_macro_mse": sum(event_mse) / len(event_mse),
            "observation_weighted_mse": total_squared / total_count,
            "event_macro_mae": sum(event_mae) / len(event_mae),
            "observation_weighted_mae": total_absolute / total_count,
            "event_mse_wins_vs_martingale": mse_wins,
            "test_event_count": len(test_events),
            "trade_count_at_one_cent": total_trade_count,
            "immediate_event_macro_net_per_decision": (
                sum(event_immediate_net) / len(event_immediate_net)
            ),
            "delayed_event_macro_net_per_decision": (
                sum(event_delayed_net) / len(event_delayed_net)
            ),
            "delayed_observation_weighted_net_per_decision": total_delayed_net / total_count,
            "delayed_positive_event_count": delayed_positive,
            "delayed_long_event_macro_net_per_decision": (
                sum(event_delayed_long_net) / len(event_delayed_long_net)
            ),
            "delayed_long_observation_weighted_net_per_decision": (
                total_delayed_long_net / total_count
            ),
            "delayed_long_positive_event_count": delayed_long_positive,
            "long_trade_count_at_one_cent": total_long_count,
        }
    ]

magnitude_results = []
baseline_event_mse = {}
for event in test_events:
    metric = magnitude_metrics[(event, "earlier_event_mean")]
    baseline_event_mse[event] = metric[0] / metric[2]
for model in magnitude_models:
    event_mse = []
    event_mae = []
    total_squared = 0.0
    total_absolute = 0.0
    total_count = 0
    event_wins = 0
    for event in test_events:
        metric = magnitude_metrics[(event, model)]
        current_mse = metric[0] / metric[2]
        event_mse = event_mse + [current_mse]
        event_mae = event_mae + [metric[1] / metric[2]]
        total_squared = total_squared + metric[0]
        total_absolute = total_absolute + metric[1]
        total_count = total_count + metric[2]
        if current_mse < baseline_event_mse[event]:
            event_wins = event_wins + 1
    magnitude_results = magnitude_results + [
        {
            "model": model,
            "event_macro_mse": sum(event_mse) / len(event_mse),
            "observation_weighted_mse": total_squared / total_count,
            "event_macro_mae": sum(event_mae) / len(event_mae),
            "observation_weighted_mae": total_absolute / total_count,
            "event_mse_wins_vs_earlier_event_mean": event_wins,
            "test_event_count": len(test_events),
        }
    ]

result = structured_return(
    "Fold-fitted boundary/logit/volatility models for magnitude and direction.",
    {
        "epsilon": epsilon,
        "feature_names": [
            "raw_change_1h",
            "logit_change_1h",
            "logit_state",
            "boundary_distance",
            "raw_realized_variance_6h",
            "raw_realized_variance_24h",
            "logit_realized_variance_6h",
            "raw_change_x_raw_variance_6h",
            "log_one_plus_hours_to_close",
        ],
        "ridge_penalty": ridge_penalty,
        "minimum_training_events": 8,
        "excluded_irregular": excluded_irregular,
        "excluded_boundary": excluded_boundary,
        "test_events": test_events,
        "coefficient_paths": coefficient_paths,
        "direction_models": direction_results,
        "magnitude_models": magnitude_results,
    },
    warnings=[
        "Every fitted mean, scale, coefficient, and magnitude baseline uses only earlier events.",
        "All events have equal total weight during fitting; both event and observation metrics are retained.",
        "Logit models exclude boundary-touching 24-hour windows rather than clipping them.",
        "Delayed pseudo-PnL enters one sample after signal calculation and is not executable PnL.",
        "Magnitude predictability is not directional or tradable evidence.",
        "Protected values remain unavailable.",
    ],
)
