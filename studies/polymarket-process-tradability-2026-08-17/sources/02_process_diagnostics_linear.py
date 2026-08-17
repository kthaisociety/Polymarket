price_markets = read("polymarket-development-prices", "market_id")
price_events = read("polymarket-development-prices", "event_id")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")


def quantile(values, fraction):
    ordered = sorted(values)
    index = int((len(ordered) - 1) * fraction)
    return ordered[index]


points = {}
market_events = {}
market_lengths = {}
market_order = []
for row in range(len(price_markets)):
    market = price_markets[row]
    if market not in market_lengths:
        market_order = market_order + [market]
        market_events[market] = price_events[row]
        market_lengths[market] = 0
    points[(market, ordinals[row])] = [times[row], probabilities[row]]
    market_lengths[market] = market_lengths[market] + 1

increment_count = len(probabilities) - len(market_order)
increments = [0.0 for unused in range(increment_count)]
absolute_increments = [0.0 for unused in range(increment_count)]
gaps = [0.0 for unused in range(increment_count)]
market_length_values = [0 for unused in range(len(market_order))]
cursor = 0
zero_count = 0
boundary_count = 0
ordinal_breaks = 0
same_sign = 0
opposite_sign = 0
lag_count = 0
lag_left_sum = 0.0
lag_right_sum = 0.0
lag_cross_sum = 0.0
lag_left_squared = 0.0
lag_right_squared = 0.0
bin_count = [0, 0, 0, 0, 0]
bin_change = [0.0, 0.0, 0.0, 0.0, 0.0]
bin_squared = [0.0, 0.0, 0.0, 0.0, 0.0]
bin_wright_fisher_scale = [0.0, 0.0, 0.0, 0.0, 0.0]
bin_logit_scale = [0.0, 0.0, 0.0, 0.0, 0.0]
event_change = {}
event_count = {}

for market_index in range(len(market_order)):
    market = market_order[market_index]
    length = market_lengths[market]
    market_length_values[market_index] = length
    max_ordinal = length - 1
    ordinal_breaks = ordinal_breaks + (max_ordinal + 1 - length)
    previous_change = None
    for ordinal in range(1, length):
        previous = points[(market, ordinal - 1)]
        current = points[(market, ordinal)]
        gap_hours = (current[0] - previous[0]) / 3600.0
        change = current[1] - previous[1]
        increments[cursor] = change
        absolute_increments[cursor] = abs(change)
        gaps[cursor] = gap_hours
        cursor = cursor + 1
        if change == 0.0:
            zero_count = zero_count + 1
        if previous_change is not None:
            lag_count = lag_count + 1
            lag_left_sum = lag_left_sum + previous_change
            lag_right_sum = lag_right_sum + change
            lag_cross_sum = lag_cross_sum + previous_change * change
            lag_left_squared = lag_left_squared + previous_change * previous_change
            lag_right_squared = lag_right_squared + change * change
            if previous_change != 0.0 and change != 0.0:
                if previous_change * change > 0.0:
                    same_sign = same_sign + 1
                else:
                    opposite_sign = opposite_sign + 1
        previous_change = change
        probability = previous[1]
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

increment_mean = sum(increments) / increment_count
increment_variance = 0.0
fourth_moment = 0.0
for change in increments:
    centered = change - increment_mean
    increment_variance = increment_variance + centered * centered
    fourth_moment = fourth_moment + centered * centered * centered * centered
increment_variance = increment_variance / increment_count
fourth_moment = fourth_moment / increment_count
kurtosis = fourth_moment / (increment_variance * increment_variance)

lag_covariance = lag_cross_sum - lag_left_sum * lag_right_sum / lag_count
lag_left_variance = lag_left_squared - lag_left_sum * lag_left_sum / lag_count
lag_right_variance = lag_right_squared - lag_right_sum * lag_right_sum / lag_count
lag_correlation = lag_covariance / ((lag_left_variance * lag_right_variance) ** 0.5)

price_bins = [None, None, None, None, None]
for bucket in range(5):
    count = bin_count[bucket]
    price_bins[bucket] = {
        "lower": bucket / 5.0,
        "count": count,
        "mean_change": bin_change[bucket] / count,
        "mean_squared_change": bin_squared[bucket] / count,
        "mean_wright_fisher_scale": bin_wright_fisher_scale[bucket] / count,
        "mean_logit_diffusion_scale": bin_logit_scale[bucket] / count,
    }

variance_ratios = [None, None, None, None]
horizons = [2, 4, 8, 24]
for horizon_index in range(len(horizons)):
    horizon = horizons[horizon_index]
    long_count = 0
    long_sum = 0.0
    long_squared = 0.0
    for market in market_order:
        length = market_lengths[market]
        for ordinal in range(horizon, length):
            change = points[(market, ordinal)][1] - points[(market, ordinal - horizon)][1]
            long_count = long_count + 1
            long_sum = long_sum + change
            long_squared = long_squared + change * change
    long_mean = long_sum / long_count
    long_variance = long_squared / long_count - long_mean * long_mean
    variance_ratios[horizon_index] = {
        "horizon_samples": horizon,
        "count": long_count,
        "mean_change": long_mean,
        "variance_ratio": long_variance / (horizon * increment_variance),
    }

event_mean_changes = [0.0 for unused in range(len(event_change))]
event_cursor = 0
for event in event_change:
    event_mean_changes[event_cursor] = event_change[event] / event_count[event]
    event_cursor = event_cursor + 1

result = structured_return(
    "Linear-time bounded-process diagnostics for retained hourly development probability paths.",
    {
        "market_count": len(market_order),
        "event_count": len(event_change),
        "observation_count": len(probabilities),
        "increment_count": increment_count,
        "market_length_min": min(market_length_values),
        "market_length_median": quantile(market_length_values, 0.5),
        "market_length_max": max(market_length_values),
        "ordinal_break_count": ordinal_breaks,
        "gap_hours_min": min(gaps),
        "gap_hours_median": quantile(gaps, 0.5),
        "gap_hours_p95": quantile(gaps, 0.95),
        "gap_hours_max": max(gaps),
        "increment_mean": increment_mean,
        "increment_variance": increment_variance,
        "increment_lag1_correlation": lag_correlation,
        "nonzero_same_sign_rate": same_sign / (same_sign + opposite_sign),
        "zero_increment_rate": zero_count / increment_count,
        "boundary_start_rate": boundary_count / increment_count,
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
