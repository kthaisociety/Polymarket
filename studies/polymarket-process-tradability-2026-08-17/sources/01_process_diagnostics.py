price_markets = read("polymarket-development-prices", "market_id")
price_events = read("polymarket-development-prices", "event_id")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")


def average(values):
    if len(values) == 0:
        return None
    return sum(values) / len(values)


def quantile(values, fraction):
    ordered = sorted(values)
    if len(ordered) == 0:
        return None
    index = int((len(ordered) - 1) * fraction)
    return ordered[index]


def correlation(left, right):
    if len(left) < 2 or len(left) != len(right):
        return None
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    covariance = 0.0
    left_variance = 0.0
    right_variance = 0.0
    for index in range(len(left)):
        left_centered = left[index] - left_mean
        right_centered = right[index] - right_mean
        covariance = covariance + left_centered * right_centered
        left_variance = left_variance + left_centered * left_centered
        right_variance = right_variance + right_centered * right_centered
    if left_variance == 0.0 or right_variance == 0.0:
        return None
    return covariance / ((left_variance * right_variance) ** 0.5)


paths = {}
market_events = {}
for index in range(len(price_markets)):
    market = price_markets[index]
    if market not in paths:
        paths[market] = []
        market_events[market] = price_events[index]
    paths[market] = paths[market] + [[ordinals[index], times[index], probabilities[index]]]

increments = []
absolute_increments = []
squared_increments = []
gaps = []
lagged_left = []
lagged_right = []
same_sign = 0
opposite_sign = 0
zero_count = 0
ordinal_breaks = 0
boundary_count = 0
bin_count = [0, 0, 0, 0, 0]
bin_change = [0.0, 0.0, 0.0, 0.0, 0.0]
bin_squared = [0.0, 0.0, 0.0, 0.0, 0.0]
bin_wright_fisher_scale = [0.0, 0.0, 0.0, 0.0, 0.0]
bin_logit_scale = [0.0, 0.0, 0.0, 0.0, 0.0]
event_change = {}
event_count = {}
market_lengths = []

for market in paths:
    path = paths[market]
    market_lengths = market_lengths + [len(path)]
    previous_change = None
    for index in range(1, len(path)):
        previous = path[index - 1]
        current = path[index]
        if current[0] != previous[0] + 1:
            ordinal_breaks = ordinal_breaks + 1
        gap_hours = (current[1] - previous[1]) / 3600.0
        change = current[2] - previous[2]
        increments = increments + [change]
        absolute_increments = absolute_increments + [abs(change)]
        squared_increments = squared_increments + [change * change]
        gaps = gaps + [gap_hours]
        if change == 0.0:
            zero_count = zero_count + 1
        if previous_change is not None:
            lagged_left = lagged_left + [previous_change]
            lagged_right = lagged_right + [change]
            if previous_change != 0.0 and change != 0.0:
                if previous_change * change > 0.0:
                    same_sign = same_sign + 1
                else:
                    opposite_sign = opposite_sign + 1
        previous_change = change
        probability = previous[2]
        if probability <= 0.0 or probability >= 1.0:
            boundary_count = boundary_count + 1
        bucket = min(4, int(probability * 5))
        bin_count[bucket] = bin_count[bucket] + 1
        bin_change[bucket] = bin_change[bucket] + change
        bin_squared[bucket] = bin_squared[bucket] + change * change
        wright_fisher_shape = probability * (1.0 - probability) * gap_hours
        logit_shape = probability * probability * (1.0 - probability) * (1.0 - probability)
        logit_shape = logit_shape * gap_hours
        if wright_fisher_shape > 0.0:
            bin_wright_fisher_scale[bucket] = bin_wright_fisher_scale[bucket] + (
                change * change / wright_fisher_shape
            )
        if logit_shape > 0.0:
            bin_logit_scale[bucket] = bin_logit_scale[bucket] + (
                change * change / logit_shape
            )
        event = market_events[market]
        if event not in event_change:
            event_change[event] = 0.0
            event_count[event] = 0
        event_change[event] = event_change[event] + change
        event_count[event] = event_count[event] + 1

increment_mean = sum(increments) / len(increments)
increment_variance = 0.0
fourth_moment = 0.0
for change in increments:
    centered = change - increment_mean
    increment_variance = increment_variance + centered * centered
    fourth_moment = fourth_moment + centered * centered * centered * centered
increment_variance = increment_variance / len(increments)
fourth_moment = fourth_moment / len(increments)
kurtosis = fourth_moment / (increment_variance * increment_variance)

price_bins = []
for bucket in range(5):
    count = bin_count[bucket]
    price_bins = price_bins + [
        {
            "lower": bucket / 5.0,
            "count": count,
            "mean_change": bin_change[bucket] / count,
            "mean_squared_change": bin_squared[bucket] / count,
            "mean_wright_fisher_scale": bin_wright_fisher_scale[bucket] / count,
            "mean_logit_diffusion_scale": bin_logit_scale[bucket] / count,
        }
    ]

variance_ratios = []
for horizon in [2, 4, 8, 24]:
    long_changes = []
    for market in paths:
        path = paths[market]
        for index in range(horizon, len(path)):
            long_changes = long_changes + [path[index][2] - path[index - horizon][2]]
    long_mean = sum(long_changes) / len(long_changes)
    long_variance = 0.0
    for change in long_changes:
        long_variance = long_variance + (change - long_mean) * (change - long_mean)
    long_variance = long_variance / len(long_changes)
    variance_ratios = variance_ratios + [
        {
            "horizon_samples": horizon,
            "count": len(long_changes),
            "mean_change": long_mean,
            "variance_ratio": long_variance / (horizon * increment_variance),
        }
    ]

event_mean_changes = []
for event in event_change:
    event_mean_changes = event_mean_changes + [event_change[event] / event_count[event]]

result = structured_return(
    "Bounded-process diagnostics for retained hourly development probability paths.",
    {
        "market_count": len(paths),
        "event_count": len(set(price_events)),
        "observation_count": len(probabilities),
        "increment_count": len(increments),
        "market_length_min": min(market_lengths),
        "market_length_median": quantile(market_lengths, 0.5),
        "market_length_max": max(market_lengths),
        "ordinal_break_count": ordinal_breaks,
        "gap_hours_min": min(gaps),
        "gap_hours_median": quantile(gaps, 0.5),
        "gap_hours_p95": quantile(gaps, 0.95),
        "gap_hours_max": max(gaps),
        "increment_mean": increment_mean,
        "increment_variance": increment_variance,
        "increment_lag1_correlation": correlation(lagged_left, lagged_right),
        "nonzero_same_sign_rate": same_sign / (same_sign + opposite_sign),
        "zero_increment_rate": zero_count / len(increments),
        "boundary_start_rate": boundary_count / len(increments),
        "absolute_change_median": quantile(absolute_increments, 0.5),
        "absolute_change_p90": quantile(absolute_increments, 0.9),
        "absolute_change_p99": quantile(absolute_increments, 0.99),
        "increment_kurtosis": kurtosis,
        "price_state_bins": price_bins,
        "variance_ratios": variance_ratios,
        "event_mean_change_min": min(event_mean_changes),
        "event_mean_change_median": quantile(event_mean_changes, 0.5),
        "event_mean_change_max": max(event_mean_changes),
        "event_positive_mean_change_count": sum(
            [1 for value in event_mean_changes if value > 0.0]
        ),
        "event_negative_or_zero_mean_change_count": sum(
            [1 for value in event_mean_changes if value <= 0.0]
        ),
    },
    warnings=[
        "Hourly price_series values are sampled probabilities, not fills or executable quotes.",
        "Variance ratios use overlapping paths and are process diagnostics, not IID test statistics.",
        "The retained resolved cohort conditions on eventual resolution and minimum path coverage.",
        "The final seven protected events and all their values remain unavailable.",
    ],
)
