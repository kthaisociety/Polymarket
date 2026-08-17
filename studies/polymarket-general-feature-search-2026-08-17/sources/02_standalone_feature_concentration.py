price_markets = read("polymarket-development-prices", "market_id")
price_events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")
outcome_markets = read("polymarket-development-outcomes", "market_id")
close_times = read("polymarket-development-outcomes", "close_time_epoch_seconds")


feature_names = [
    "boundary_distance",
    "current_boundary_state_002",
    "log_one_plus_hours_to_close",
    "realized_variance_6h",
    "realized_variance_24h",
    "bipower_jump_variation_24h",
    "jump_concentration_24h",
    "zero_change_fraction_24h",
    "raw_change_6h",
    "mean_absolute_change_24h",
    "boundary_x_expiry",
    "jump_x_expiry",
    "boundary_closeness_x_variance_6h",
]
label_names = ["absolute_change_6h", "large_move_002"]
feature_count = len(feature_names)
label_count = len(label_names)
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
event_counts = {}
aggregates = {}
excluded_irregular = 0
for market in market_order:
    event = market_events[market]
    length = market_lengths[market]
    for decision in range(24, length - 6, 6):
        current = points[(market, decision)]
        trailing = points[(market, decision - 24)]
        future = points[(market, decision + 6)]
        trailing_hours = (current[0] - trailing[0]) / 3600.0
        future_hours = (future[0] - current[0]) / 3600.0
        if trailing_hours < 18.0 or trailing_hours > 30.0 or future_hours < 4.5 or future_hours > 7.5:
            excluded_irregular = excluded_irregular + 1
        else:
            probability = current[1]
            boundary_distance = min(probability, 1.0 - probability)
            boundary_state = 1.0 if probability <= 0.02 or probability >= 0.98 else 0.0
            expiry = log(1.0 + max(0.0, (close_by_market[market] - current[0]) / 3600.0))
            rv6 = 0.0
            rv24 = 0.0
            bipower = 0.0
            max_step = 0.0
            zero_count = 0.0
            absolute_sum = 0.0
            previous_abs = 0.0
            for ordinal in range(decision - 23, decision + 1):
                step = points[(market, ordinal)][1] - points[(market, ordinal - 1)][1]
                absolute_step = abs(step)
                rv24 = rv24 + step * step
                absolute_sum = absolute_sum + absolute_step
                if absolute_step == 0.0:
                    zero_count = zero_count + 1.0
                if absolute_step > max_step:
                    max_step = absolute_step
                if ordinal > decision - 23:
                    bipower = bipower + previous_abs * absolute_step
                previous_abs = absolute_step
                if ordinal >= decision - 5:
                    rv6 = rv6 + step * step
            jump_variation = max(0.0, rv24 - 1.5707963267948966 * bipower)
            jump_concentration = max_step / ((rv24 + 0.000000000001) ** 0.5)
            change6 = probability - points[(market, decision - 6)][1]
            boundary_closeness = 1.0 - 2.0 * boundary_distance
            features = [
                boundary_distance,
                boundary_state,
                expiry,
                rv6,
                rv24,
                jump_variation,
                jump_concentration,
                zero_count / 24.0,
                change6,
                absolute_sum / 24.0,
                boundary_distance * expiry,
                jump_concentration * expiry,
                boundary_closeness * rv6,
            ]
            magnitude = abs(future[1] - probability)
            labels = [magnitude, 1.0 if magnitude >= 0.02 else 0.0]
            if event not in event_counts:
                event_counts[event] = 0
                aggregates[event] = [
                    0,
                    [0.0 for unused in range(feature_count)],
                    [0.0 for unused in range(feature_count)],
                    [0.0 for unused in range(label_count)],
                    [[0.0 for unused in range(feature_count)] for unused in range(label_count)],
                ]
            count = event_counts[event]
            event_counts[event] = count + 1
            samples[(event, count)] = [features, labels]
            aggregate = aggregates[event]
            aggregate[0] = aggregate[0] + 1
            for feature in range(feature_count):
                aggregate[1][feature] = aggregate[1][feature] + features[feature]
                aggregate[2][feature] = aggregate[2][feature] + features[feature] * features[feature]
                for label in range(label_count):
                    aggregate[4][label][feature] = aggregate[4][label][feature] + features[feature] * labels[label]
            for label in range(label_count):
                aggregate[3][label] = aggregate[3][label] + labels[label]


def fit_scalar(test_event, feature, label):
    event_weight = 0.0
    mean_x = 0.0
    mean_x2 = 0.0
    mean_y = 0.0
    mean_xy = 0.0
    for event in range(test_event):
        if event in aggregates:
            count = aggregates[event][0]
            event_weight = event_weight + 1.0
            mean_x = mean_x + aggregates[event][1][feature] / count
            mean_x2 = mean_x2 + aggregates[event][2][feature] / count
            mean_y = mean_y + aggregates[event][3][label] / count
            mean_xy = mean_xy + aggregates[event][4][label][feature] / count
    mean_x = mean_x / event_weight
    mean_x2 = mean_x2 / event_weight
    mean_y = mean_y / event_weight
    mean_xy = mean_xy / event_weight
    variance = mean_x2 - mean_x * mean_x
    slope = 0.0
    if variance > 0.000000000001:
        slope = (mean_xy - mean_x * mean_y) / variance
    return [mean_y - slope * mean_x, slope, mean_y]


metrics = {}
event_label_rates = []
test_events = []
for test_event in range(8, 24):
    if test_event not in event_counts:
        continue
    test_events = test_events + [test_event]
    rates = [aggregates[test_event][3][label] / aggregates[test_event][0] for label in range(label_count)]
    event_label_rates = event_label_rates + [{"event": test_event, "sample_count": event_counts[test_event], "mean_absolute_change": rates[0], "large_move_rate": rates[1]}]
    fitted = {}
    for label in range(label_count):
        metrics[(test_event, label, -1)] = [0.0, 0.0, 0]
        for feature in range(feature_count):
            fitted[(label, feature)] = fit_scalar(test_event, feature, label)
            metrics[(test_event, label, feature)] = [0.0, 0.0, 0]
    for sample_index in range(event_counts[test_event]):
        sample = samples[(test_event, sample_index)]
        for label in range(label_count):
            baseline = fit_scalar(test_event, 0, label)[2]
            error = sample[1][label] - baseline
            metric = metrics[(test_event, label, -1)]
            metric[0] = metric[0] + error * error
            metric[1] = metric[1] + abs(error)
            metric[2] = metric[2] + 1
            for feature in range(feature_count):
                model = fitted[(label, feature)]
                prediction = model[0] + model[1] * sample[0][feature]
                if label == 0:
                    prediction = max(0.0, prediction)
                else:
                    prediction = min(1.0, max(0.0, prediction))
                error = sample[1][label] - prediction
                metric = metrics[(test_event, label, feature)]
                metric[0] = metric[0] + error * error
                metric[1] = metric[1] + abs(error)
                metric[2] = metric[2] + 1

results = []
for label in range(label_count):
    baseline_event = {}
    for event in test_events:
        metric = metrics[(event, label, -1)]
        baseline_event[event] = metric[0] / metric[2]
    for feature in range(-1, feature_count):
        event_deltas = []
        event_values = []
        total_squared = 0.0
        total_count = 0
        wins = 0
        positive_total = 0.0
        largest_positive = 0.0
        for event in test_events:
            metric = metrics[(event, label, feature)]
            mse = metric[0] / metric[2]
            delta = baseline_event[event] - mse
            event_values = event_values + [mse]
            event_deltas = event_deltas + [delta]
            total_squared = total_squared + metric[0]
            total_count = total_count + metric[2]
            if delta > 0.0:
                wins = wins + 1
                positive_total = positive_total + delta
                if delta > largest_positive:
                    largest_positive = delta
        largest_share = 0.0
        if positive_total > 0.0:
            largest_share = largest_positive / positive_total
        results = results + [{
            "label": label_names[label],
            "model": "baseline" if feature == -1 else feature_names[feature],
            "event_macro_mse": sum(event_values) / len(event_values),
            "observation_weighted_mse": total_squared / total_count,
            "early_event_macro_mse": sum(event_values[:8]) / 8.0,
            "late_event_macro_mse": sum(event_values[8:]) / 8.0,
            "event_mse_wins_vs_baseline": wins,
            "largest_positive_improvement_share": largest_share,
            "event_mse_improvement_vs_baseline": event_deltas,
        }]

result = structured_return(
    "Stand-alone feature attribution and event-concentration diagnostic.",
    {
        "feature_names": feature_names,
        "label_names": label_names,
        "excluded_irregular": excluded_irregular,
        "development_sample_count": sum(event_counts[event] for event in event_counts),
        "test_events": test_events,
        "event_label_rates": event_label_rates,
        "results": results,
    },
    warnings=[
        "Scalar OLS shows stand-alone association and intentionally misses substitution and interactions.",
        "Every coefficient and baseline uses equal-weighted earlier events only.",
        "Early/late stability and concentration are development diagnostics, not independent validation.",
        "The two-cent large-move threshold was frozen before benchmark 01 and was not retuned.",
        "Protected values remain unavailable.",
    ],
)
