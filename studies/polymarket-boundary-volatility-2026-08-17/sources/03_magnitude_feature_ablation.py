price_markets = read("polymarket-development-prices", "market_id")
price_events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")
outcome_markets = read("polymarket-development-outcomes", "market_id")
close_times = read("polymarket-development-outcomes", "close_time_epoch_seconds")


def logit(probability):
    return log(probability / (1.0 - probability))


epsilon = 0.005
feature_names = [
    "log_one_plus_hours_to_close",
    "boundary_distance",
    "raw_realized_variance_6h",
    "raw_realized_variance_24h",
    "logit_realized_variance_6h",
]
model_names = [
    "earlier_event_mean",
    "time_to_close_ols",
    "boundary_distance_ols",
    "raw_variance_6h_ols",
    "raw_variance_24h_ols",
    "logit_variance_6h_ols",
]
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
    for decision in range(24, length - 1):
        start = points[(market, decision - 24)]
        current = points[(market, decision)]
        future = points[(market, decision + 1)]
        trailing_hours = (current[0] - start[0]) / 3600.0
        future_hours = (future[0] - current[0]) / 3600.0
        if (
            trailing_hours < 18.0
            or trailing_hours > 30.0
            or future_hours < 0.75
            or future_hours > 1.25
        ):
            excluded_irregular = excluded_irregular + 1
        else:
            interior = True
            for ordinal in range(decision - 24, decision + 1):
                probability = points[(market, ordinal)][1]
                if probability <= epsilon or probability >= 1.0 - epsilon:
                    interior = False
            if not interior:
                excluded_boundary = excluded_boundary + 1
            else:
                raw_rv_6 = 0.0
                raw_rv_24 = 0.0
                logit_rv_6 = 0.0
                for ordinal in range(decision - 23, decision + 1):
                    left = points[(market, ordinal - 1)][1]
                    right = points[(market, ordinal)][1]
                    raw_step = right - left
                    raw_rv_24 = raw_rv_24 + raw_step * raw_step
                    if ordinal >= decision - 5:
                        raw_rv_6 = raw_rv_6 + raw_step * raw_step
                        logit_step = logit(right) - logit(left)
                        logit_rv_6 = logit_rv_6 + logit_step * logit_step
                probability = current[1]
                hours_to_close = max(0.0, (close_by_market[market] - current[0]) / 3600.0)
                features = [
                    log(1.0 + hours_to_close),
                    min(probability, 1.0 - probability),
                    raw_rv_6,
                    raw_rv_24,
                    logit_rv_6,
                ]
                target = abs(future[1] - probability)
                if event not in event_sample_count:
                    event_sample_count[event] = 0
                    aggregates[event] = [
                        0,
                        0.0,
                        [0.0, 0.0, 0.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0, 0.0, 0.0],
                    ]
                count = event_sample_count[event]
                samples[(event, count)] = [features, target]
                event_sample_count[event] = count + 1
                aggregate = aggregates[event]
                aggregate[0] = aggregate[0] + 1
                aggregate[1] = aggregate[1] + target
                for feature in range(5):
                    aggregate[2][feature] = aggregate[2][feature] + features[feature]
                    aggregate[3][feature] = (
                        aggregate[3][feature] + features[feature] * features[feature]
                    )
                    aggregate[4][feature] = (
                        aggregate[4][feature] + features[feature] * target
                    )

metrics = {}
coefficient_paths = []
test_events = []
for test_event in range(8, 24):
    if test_event not in event_sample_count or event_sample_count[test_event] == 0:
        continue
    event_weight = 0.0
    target_mean = 0.0
    feature_mean = [0.0, 0.0, 0.0, 0.0, 0.0]
    feature_second = [0.0, 0.0, 0.0, 0.0, 0.0]
    feature_target = [0.0, 0.0, 0.0, 0.0, 0.0]
    for train_event in range(test_event):
        if train_event in aggregates:
            aggregate = aggregates[train_event]
            count = aggregate[0]
            event_weight = event_weight + 1.0
            target_mean = target_mean + aggregate[1] / count
            for feature in range(5):
                feature_mean[feature] = (
                    feature_mean[feature] + aggregate[2][feature] / count
                )
                feature_second[feature] = (
                    feature_second[feature] + aggregate[3][feature] / count
                )
                feature_target[feature] = (
                    feature_target[feature] + aggregate[4][feature] / count
                )
    target_mean = target_mean / event_weight
    intercepts = [target_mean, 0.0, 0.0, 0.0, 0.0, 0.0]
    slopes = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    for feature in range(5):
        feature_mean[feature] = feature_mean[feature] / event_weight
        feature_second[feature] = feature_second[feature] / event_weight
        feature_target[feature] = feature_target[feature] / event_weight
        variance = (
            feature_second[feature] - feature_mean[feature] * feature_mean[feature]
        )
        covariance = feature_target[feature] - feature_mean[feature] * target_mean
        slope = 0.0 if variance <= 0.000000000001 else covariance / variance
        slopes[feature + 1] = slope
        intercepts[feature + 1] = target_mean - slope * feature_mean[feature]
    coefficient_paths = coefficient_paths + [
        {
            "test_event_ordinal": test_event,
            "intercepts": intercepts,
            "slopes": slopes,
        }
    ]
    test_events = test_events + [test_event]
    for model in model_names:
        metrics[(test_event, model)] = [0.0, 0.0, 0]
    count = event_sample_count[test_event]
    for sample_index in range(count):
        sample = samples[(test_event, sample_index)]
        for model_index in range(len(model_names)):
            if model_index == 0:
                prediction = target_mean
            else:
                prediction = (
                    intercepts[model_index]
                    + slopes[model_index] * sample[0][model_index - 1]
                )
            prediction = max(0.0, prediction)
            error = sample[1] - prediction
            metric = metrics[(test_event, model_names[model_index])]
            metric[0] = metric[0] + error * error
            metric[1] = metric[1] + abs(error)
            metric[2] = metric[2] + 1

baseline_event_mse = {}
for event in test_events:
    metric = metrics[(event, "earlier_event_mean")]
    baseline_event_mse[event] = metric[0] / metric[2]

model_results = []
for model in model_names:
    event_mse = []
    event_mae = []
    total_squared = 0.0
    total_absolute = 0.0
    total_count = 0
    event_wins = 0
    for event in test_events:
        metric = metrics[(event, model)]
        current_mse = metric[0] / metric[2]
        event_mse = event_mse + [current_mse]
        event_mae = event_mae + [metric[1] / metric[2]]
        total_squared = total_squared + metric[0]
        total_absolute = total_absolute + metric[1]
        total_count = total_count + metric[2]
        if current_mse < baseline_event_mse[event]:
            event_wins = event_wins + 1
    model_results = model_results + [
        {
            "model": model,
            "event_macro_mse": sum(event_mse) / len(event_mse),
            "observation_weighted_mse": total_squared / total_count,
            "event_macro_mae": sum(event_mae) / len(event_mae),
            "observation_weighted_mae": total_absolute / total_count,
            "event_mse_wins_vs_mean": event_wins,
            "test_event_count": len(test_events),
        }
    ]

result = structured_return(
    "One-event-ahead magnitude-feature ablation on a fixed common population.",
    {
        "epsilon": epsilon,
        "feature_names": feature_names,
        "excluded_irregular": excluded_irregular,
        "excluded_boundary": excluded_boundary,
        "test_events": test_events,
        "coefficient_paths": coefficient_paths,
        "models": model_results,
    },
    warnings=[
        "Every scalar coefficient uses equal-weighted earlier events only.",
        "All models use the same hourly-regular interior sample.",
        "Magnitude forecasts do not imply direction, execution, or tradability.",
        "Protected values remain unavailable.",
    ],
)
