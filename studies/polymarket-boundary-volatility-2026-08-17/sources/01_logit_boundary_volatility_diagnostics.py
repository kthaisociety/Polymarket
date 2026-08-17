price_markets = read("polymarket-development-prices", "market_id")
price_events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")
outcome_markets = read("polymarket-development-outcomes", "market_id")
close_times = read("polymarket-development-outcomes", "close_time_epoch_seconds")


def logit(probability):
    return log(probability / (1.0 - probability))


def correlation(count, left_sum, right_sum, cross_sum, left_squared, right_squared):
    if count < 2:
        return None
    covariance = cross_sum - left_sum * right_sum / count
    left_variance = left_squared - left_sum * left_sum / count
    right_variance = right_squared - right_sum * right_sum / count
    if left_variance <= 0.0 or right_variance <= 0.0:
        return None
    return covariance / ((left_variance * right_variance) ** 0.5)


def quantile(values, fraction):
    ordered = sorted(values)
    index = int((len(ordered) - 1) * fraction)
    return ordered[index]


epsilon = 0.005
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

increment_capacity = len(probabilities) - len(market_order)
raw_changes = [0.0 for unused in range(increment_capacity)]
logit_changes = [0.0 for unused in range(increment_capacity)]
raw_count = 0
logit_count = 0
raw_zero_count = 0
logit_boundary_excluded = 0
raw_lag = [0.0, 0.0, 0.0, 0.0, 0.0, 0]
logit_lag = [0.0, 0.0, 0.0, 0.0, 0.0, 0]
band_count = [0, 0, 0, 0, 0]
band_stay = [0, 0, 0, 0, 0]
band_toward_boundary = [0, 0, 0, 0, 0]
time_count = [0, 0, 0, 0]
time_squared = [0.0, 0.0, 0.0, 0.0]

for market in market_order:
    length = market_lengths[market]
    previous_raw = None
    previous_logit = None
    previous_logit_legal = False
    for ordinal in range(1, length):
        previous = points[(market, ordinal - 1)]
        current = points[(market, ordinal)]
        raw_change = current[1] - previous[1]
        raw_changes[raw_count] = raw_change
        raw_count = raw_count + 1
        if raw_change == 0.0:
            raw_zero_count = raw_zero_count + 1
        if previous_raw is not None:
            raw_lag[0] = raw_lag[0] + previous_raw
            raw_lag[1] = raw_lag[1] + raw_change
            raw_lag[2] = raw_lag[2] + previous_raw * raw_change
            raw_lag[3] = raw_lag[3] + previous_raw * previous_raw
            raw_lag[4] = raw_lag[4] + raw_change * raw_change
            raw_lag[5] = raw_lag[5] + 1
        previous_raw = raw_change

        legal_logit = (
            previous[1] > epsilon
            and previous[1] < 1.0 - epsilon
            and current[1] > epsilon
            and current[1] < 1.0 - epsilon
        )
        if legal_logit:
            logit_change = logit(current[1]) - logit(previous[1])
            logit_changes[logit_count] = logit_change
            logit_count = logit_count + 1
            if previous_logit_legal and previous_logit is not None:
                logit_lag[0] = logit_lag[0] + previous_logit
                logit_lag[1] = logit_lag[1] + logit_change
                logit_lag[2] = logit_lag[2] + previous_logit * logit_change
                logit_lag[3] = logit_lag[3] + previous_logit * previous_logit
                logit_lag[4] = logit_lag[4] + logit_change * logit_change
                logit_lag[5] = logit_lag[5] + 1
            previous_logit = logit_change
            previous_logit_legal = True
        else:
            logit_boundary_excluded = logit_boundary_excluded + 1
            previous_logit = None
            previous_logit_legal = False

        probability = previous[1]
        next_probability = current[1]
        if probability <= 0.02:
            band = 0
        elif probability < 0.10:
            band = 1
        elif probability <= 0.90:
            band = 2
        elif probability < 0.98:
            band = 3
        else:
            band = 4
        if next_probability <= 0.02:
            next_band = 0
        elif next_probability < 0.10:
            next_band = 1
        elif next_probability <= 0.90:
            next_band = 2
        elif next_probability < 0.98:
            next_band = 3
        else:
            next_band = 4
        band_count[band] = band_count[band] + 1
        if next_band == band:
            band_stay[band] = band_stay[band] + 1
        if abs(next_probability - 0.5) > abs(probability - 0.5):
            band_toward_boundary[band] = band_toward_boundary[band] + 1

        hours_to_close = (close_by_market[market] - previous[0]) / 3600.0
        if hours_to_close < 24.0:
            time_bucket = 0
        elif hours_to_close < 72.0:
            time_bucket = 1
        elif hours_to_close < 168.0:
            time_bucket = 2
        else:
            time_bucket = 3
        time_count[time_bucket] = time_count[time_bucket] + 1
        time_squared[time_bucket] = time_squared[time_bucket] + raw_change * raw_change

raw_changes = raw_changes[:raw_count]
logit_changes = logit_changes[:logit_count]
raw_mean = sum(raw_changes) / raw_count
raw_variance = sum([(value - raw_mean) ** 2 for value in raw_changes]) / raw_count
logit_mean = sum(logit_changes) / logit_count
logit_variance = sum([(value - logit_mean) ** 2 for value in logit_changes]) / logit_count

variance_results = [None, None, None, None]
horizons = [2, 4, 8, 24]
for horizon_index in range(len(horizons)):
    horizon = horizons[horizon_index]
    raw_long_count = 0
    raw_long_sum = 0.0
    raw_long_squared = 0.0
    logit_long_count = 0
    logit_long_sum = 0.0
    logit_long_squared = 0.0
    for market in market_order:
        length = market_lengths[market]
        for ordinal in range(horizon, length):
            previous = points[(market, ordinal - horizon)]
            current = points[(market, ordinal)]
            raw_long_change = current[1] - previous[1]
            raw_long_count = raw_long_count + 1
            raw_long_sum = raw_long_sum + raw_long_change
            raw_long_squared = raw_long_squared + raw_long_change * raw_long_change
            if (
                previous[1] > epsilon
                and previous[1] < 1.0 - epsilon
                and current[1] > epsilon
                and current[1] < 1.0 - epsilon
            ):
                logit_long_change = logit(current[1]) - logit(previous[1])
                logit_long_count = logit_long_count + 1
                logit_long_sum = logit_long_sum + logit_long_change
                logit_long_squared = (
                    logit_long_squared + logit_long_change * logit_long_change
                )
    raw_long_mean = raw_long_sum / raw_long_count
    raw_long_variance = raw_long_squared / raw_long_count - raw_long_mean * raw_long_mean
    logit_long_mean = logit_long_sum / logit_long_count
    logit_long_variance = (
        logit_long_squared / logit_long_count - logit_long_mean * logit_long_mean
    )
    variance_results[horizon_index] = {
        "horizon_samples": horizon,
        "raw_count": raw_long_count,
        "raw_variance_ratio": raw_long_variance / (horizon * raw_variance),
        "logit_count": logit_long_count,
        "logit_variance_ratio": logit_long_variance / (horizon * logit_variance),
    }

volatility_results = [None, None]
windows = [6, 24]
for window_index in range(len(windows)):
    window = windows[window_index]
    raw_stats = [0.0, 0.0, 0.0, 0.0, 0.0, 0]
    logit_stats = [0.0, 0.0, 0.0, 0.0, 0.0, 0]
    event_raw_stats = {}
    for market in market_order:
        event = market_events[market]
        length = market_lengths[market]
        for ordinal in range(window, length - 1):
            start = points[(market, ordinal - window)]
            current = points[(market, ordinal)]
            future = points[(market, ordinal + 1)]
            trailing_hours = (current[0] - start[0]) / 3600.0
            future_hours = (future[0] - current[0]) / 3600.0
            if (
                trailing_hours >= 0.75 * window
                and trailing_hours <= 1.25 * window
                and future_hours >= 0.75
                and future_hours <= 1.25
            ):
                raw_rv = 0.0
                logit_rv = 0.0
                interior = True
                for lag in range(ordinal - window + 1, ordinal + 1):
                    left = points[(market, lag - 1)][1]
                    right = points[(market, lag)][1]
                    raw_step = right - left
                    raw_rv = raw_rv + raw_step * raw_step
                    if (
                        left > epsilon
                        and left < 1.0 - epsilon
                        and right > epsilon
                        and right < 1.0 - epsilon
                    ):
                        logit_step = logit(right) - logit(left)
                        logit_rv = logit_rv + logit_step * logit_step
                    else:
                        interior = False
                future_absolute = abs(future[1] - current[1])
                raw_stats[0] = raw_stats[0] + raw_rv
                raw_stats[1] = raw_stats[1] + future_absolute
                raw_stats[2] = raw_stats[2] + raw_rv * future_absolute
                raw_stats[3] = raw_stats[3] + raw_rv * raw_rv
                raw_stats[4] = raw_stats[4] + future_absolute * future_absolute
                raw_stats[5] = raw_stats[5] + 1
                if event not in event_raw_stats:
                    event_raw_stats[event] = [0.0, 0.0, 0.0, 0.0, 0.0, 0]
                event_stat = event_raw_stats[event]
                event_stat[0] = event_stat[0] + raw_rv
                event_stat[1] = event_stat[1] + future_absolute
                event_stat[2] = event_stat[2] + raw_rv * future_absolute
                event_stat[3] = event_stat[3] + raw_rv * raw_rv
                event_stat[4] = event_stat[4] + future_absolute * future_absolute
                event_stat[5] = event_stat[5] + 1
                if interior:
                    logit_stats[0] = logit_stats[0] + logit_rv
                    logit_stats[1] = logit_stats[1] + future_absolute
                    logit_stats[2] = logit_stats[2] + logit_rv * future_absolute
                    logit_stats[3] = logit_stats[3] + logit_rv * logit_rv
                    logit_stats[4] = logit_stats[4] + future_absolute * future_absolute
                    logit_stats[5] = logit_stats[5] + 1
    event_correlations = []
    for event in event_raw_stats:
        stat = event_raw_stats[event]
        if stat[5] >= 20:
            event_correlation = correlation(
                stat[5], stat[0], stat[1], stat[2], stat[3], stat[4]
            )
            if event_correlation is not None:
                event_correlations = event_correlations + [event_correlation]
    volatility_results[window_index] = {
        "window_samples": window,
        "raw_count": raw_stats[5],
        "raw_rv_future_absolute_correlation": correlation(
            raw_stats[5], raw_stats[0], raw_stats[1], raw_stats[2], raw_stats[3], raw_stats[4]
        ),
        "event_correlation_count": len(event_correlations),
        "event_correlation_median": quantile(event_correlations, 0.5),
        "event_correlation_min": min(event_correlations),
        "event_correlation_max": max(event_correlations),
        "logit_interior_count": logit_stats[5],
        "logit_rv_future_absolute_correlation": correlation(
            logit_stats[5],
            logit_stats[0],
            logit_stats[1],
            logit_stats[2],
            logit_stats[3],
            logit_stats[4],
        ),
    }

band_results = [None, None, None, None, None]
band_names = ["low_boundary", "low_near", "interior", "high_near", "high_boundary"]
for band in range(5):
    band_results[band] = {
        "band": band_names[band],
        "count": band_count[band],
        "stay_fraction": band_stay[band] / band_count[band],
        "toward_boundary_fraction": band_toward_boundary[band] / band_count[band],
    }

time_results = [None, None, None, None]
time_names = ["under_24h", "24_to_72h", "72_to_168h", "over_168h"]
for time_bucket in range(4):
    time_results[time_bucket] = {
        "time_to_close_band": time_names[time_bucket],
        "count": time_count[time_bucket],
        "mean_squared_next_change": time_squared[time_bucket] / time_count[time_bucket],
    }

result = structured_return(
    "Raw/logit dynamics, boundary transitions, and realized-volatility diagnostics.",
    {
        "epsilon": epsilon,
        "raw_increment_count": raw_count,
        "raw_zero_fraction": raw_zero_count / raw_count,
        "logit_increment_count": logit_count,
        "logit_boundary_excluded_count": logit_boundary_excluded,
        "raw_lag_one_correlation": correlation(
            raw_lag[5], raw_lag[0], raw_lag[1], raw_lag[2], raw_lag[3], raw_lag[4]
        ),
        "logit_lag_one_correlation": correlation(
            logit_lag[5],
            logit_lag[0],
            logit_lag[1],
            logit_lag[2],
            logit_lag[3],
            logit_lag[4],
        ),
        "variance_scaling": variance_results,
        "boundary_transitions": band_results,
        "time_to_close_volatility": time_results,
        "volatility_prediction": volatility_results,
    },
    warnings=[
        "Logit statistics exclude every step touching p <= 0.005 or p >= 0.995; no clipping is used.",
        "Realized-volatility correlation predicts magnitude, not direction or tradability.",
        "Sampled probabilities are not executable quotes and repeated windows are dependent.",
        "Event-level correlation dispersion is retained to expose concentration.",
        "Protected values remain unavailable.",
    ],
)
