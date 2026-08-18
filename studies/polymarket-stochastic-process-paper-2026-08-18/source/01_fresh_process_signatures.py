markets = read("polymarket-development-prices", "market_id")
events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")

outcome_markets = read("polymarket-development-outcomes", "market_id")
close_times = read("polymarket-development-outcomes", "close_time_epoch_seconds")
payouts = read("polymarket-development-outcomes", "resolution_payout")


def quantile(values, fraction):
    if len(values) == 0:
        return None
    ordered = sorted(values)
    index = int((len(ordered) - 1) * fraction)
    return ordered[index]


def safe_rate(numerator, denominator):
    if denominator == 0:
        return None
    return numerator / denominator


def band_index(probability):
    if probability <= 0.02:
        return 0
    if probability < 0.20:
        return 1
    if probability <= 0.80:
        return 2
    if probability < 0.98:
        return 3
    return 4


def quiet_index(quiet_run):
    if quiet_run == 0:
        return 0
    if quiet_run <= 5:
        return 1
    if quiet_run <= 23:
        return 2
    return 3


def close_index(hours_to_close):
    if hours_to_close <= 24.0:
        return 0
    if hours_to_close <= 72.0:
        return 1
    if hours_to_close <= 168.0:
        return 2
    return 3


close_by_market = {}
payout_by_market = {}
for row in range(len(outcome_markets)):
    market = outcome_markets[row]
    close_by_market[market] = close_times[row]
    payout_by_market[market] = payouts[row]

maximum_event = max(events)
event_increment_count = [0 for unused in range(maximum_event + 1)]
event_zero_count = [0 for unused in range(maximum_event + 1)]
event_change_sum = [0.0 for unused in range(maximum_event + 1)]
event_squared_sum = [0.0 for unused in range(maximum_event + 1)]

state_count = [0, 0, 0, 0, 0]
state_zero = [0, 0, 0, 0, 0]
state_change = [0.0, 0.0, 0.0, 0.0, 0.0]
state_squared = [0.0, 0.0, 0.0, 0.0, 0.0]
state_wright_fisher_scale = [0.0, 0.0, 0.0, 0.0, 0.0]
state_wright_fisher_count = [0, 0, 0, 0, 0]

quiet_count = [0, 0, 0, 0]
quiet_move = [0, 0, 0, 0]
quiet_abs_change = [0.0, 0.0, 0.0, 0.0]

close_count = [0, 0, 0, 0]
close_move = [0, 0, 0, 0]
close_abs_change = [0.0, 0.0, 0.0, 0.0]

calibration_count = [0, 0, 0, 0]
calibration_probability = [0.0, 0.0, 0.0, 0.0]
calibration_outcome = [0.0, 0.0, 0.0, 0.0]
calibration_brier = [0.0, 0.0, 0.0, 0.0]

horizons = [2, 4, 8, 24]
horizon_count = [0, 0, 0, 0]
horizon_change = [0.0, 0.0, 0.0, 0.0]
horizon_squared = [0.0, 0.0, 0.0, 0.0]

regular_changes = [0.0 for unused in range(len(probabilities))]
regular_abs_changes = [0.0 for unused in range(len(probabilities))]
regular_cursor = 0
regular_interior_zero = 0
regular_interior_count = 0
all_increment_count = 0
all_zero_count = 0
order_break_count = 0
unknown_close_count = 0
negative_time_to_close_count = 0
low_boundary_count = 0
low_boundary_stay = 0
high_boundary_count = 0
high_boundary_stay = 0

waiting_hours = [0.0 for unused in range(len(probabilities))]
waiting_cursor = 0
previous_nonzero_sign = 0
nonzero_sign_count = 0
nonzero_sign_reversal = 0
adjacent_sign_count = 0
adjacent_sign_reversal = 0

market_count = 0
current_market = None
previous_market = None
previous_ordinal = None
previous_time = None
previous_probability = None
previous_change = 0.0
quiet_run = 0
last_nonzero_time = None
history_times = []
history_probabilities = []

for row in range(len(probabilities)):
    market = markets[row]
    event = events[row]
    ordinal = ordinals[row]
    observed_time = times[row]
    probability = probabilities[row]
    if market != current_market:
        market_count = market_count + 1
        current_market = market
        previous_market = None
        previous_ordinal = None
        previous_time = None
        previous_probability = None
        previous_change = 0.0
        quiet_run = 0
        last_nonzero_time = None
        previous_nonzero_sign = 0
        history_times = []
        history_probabilities = []
        if ordinal != 0:
            order_break_count = order_break_count + 1
    if previous_market == market:
        if ordinal != previous_ordinal + 1 or observed_time <= previous_time:
            order_break_count = order_break_count + 1
        else:
            gap_hours = (observed_time - previous_time) / 3600.0
            change = probability - previous_probability
            all_increment_count = all_increment_count + 1
            if change == 0.0:
                all_zero_count = all_zero_count + 1
            if previous_probability <= 0.02:
                low_boundary_count = low_boundary_count + 1
                if probability <= 0.02:
                    low_boundary_stay = low_boundary_stay + 1
            if previous_probability >= 0.98:
                high_boundary_count = high_boundary_count + 1
                if probability >= 0.98:
                    high_boundary_stay = high_boundary_stay + 1
            if gap_hours >= 0.75 and gap_hours <= 1.25:
                regular_changes[regular_cursor] = change
                regular_abs_changes[regular_cursor] = abs(change)
                regular_cursor = regular_cursor + 1
                event_increment_count[event] = event_increment_count[event] + 1
                event_change_sum[event] = event_change_sum[event] + change
                event_squared_sum[event] = event_squared_sum[event] + change * change
                if change == 0.0:
                    event_zero_count[event] = event_zero_count[event] + 1
                if previous_probability > 0.02 and previous_probability < 0.98:
                    regular_interior_count = regular_interior_count + 1
                    if change == 0.0:
                        regular_interior_zero = regular_interior_zero + 1
                state = band_index(previous_probability)
                state_count[state] = state_count[state] + 1
                state_change[state] = state_change[state] + change
                state_squared[state] = state_squared[state] + change * change
                if change == 0.0:
                    state_zero[state] = state_zero[state] + 1
                wright_fisher_shape = previous_probability * (1.0 - previous_probability)
                if wright_fisher_shape > 0.0:
                    state_wright_fisher_scale[state] = (
                        state_wright_fisher_scale[state] + change * change / wright_fisher_shape
                    )
                    state_wright_fisher_count[state] = state_wright_fisher_count[state] + 1
                quiet = quiet_index(quiet_run)
                quiet_count[quiet] = quiet_count[quiet] + 1
                quiet_abs_change[quiet] = quiet_abs_change[quiet] + abs(change)
                if change != 0.0:
                    quiet_move[quiet] = quiet_move[quiet] + 1
                if market in close_by_market:
                    hours_to_close = (close_by_market[market] - previous_time) / 3600.0
                    if hours_to_close < 0.0:
                        negative_time_to_close_count = negative_time_to_close_count + 1
                    else:
                        close_band = close_index(hours_to_close)
                        close_count[close_band] = close_count[close_band] + 1
                        close_abs_change[close_band] = close_abs_change[close_band] + abs(change)
                        if change != 0.0:
                            close_move[close_band] = close_move[close_band] + 1
                else:
                    unknown_close_count = unknown_close_count + 1
                if previous_change != 0.0 and change != 0.0:
                    adjacent_sign_count = adjacent_sign_count + 1
                    if previous_change * change < 0.0:
                        adjacent_sign_reversal = adjacent_sign_reversal + 1
                if change != 0.0:
                    current_sign = 1
                    if change < 0.0:
                        current_sign = -1
                    if previous_nonzero_sign != 0:
                        nonzero_sign_count = nonzero_sign_count + 1
                        if current_sign != previous_nonzero_sign:
                            nonzero_sign_reversal = nonzero_sign_reversal + 1
                    previous_nonzero_sign = current_sign
                    if last_nonzero_time is not None:
                        waiting_hours[waiting_cursor] = (observed_time - last_nonzero_time) / 3600.0
                        waiting_cursor = waiting_cursor + 1
                    last_nonzero_time = observed_time
                    quiet_run = 0
                else:
                    quiet_run = quiet_run + 1
                previous_change = change
    history_times = history_times + [observed_time]
    history_probabilities = history_probabilities + [probability]
    if len(history_times) > 25:
        history_times = history_times[1:]
        history_probabilities = history_probabilities[1:]
    for horizon_position in range(len(horizons)):
        horizon = horizons[horizon_position]
        if len(history_times) > horizon:
            elapsed_hours = (history_times[-1] - history_times[-horizon - 1]) / 3600.0
            if elapsed_hours >= 0.75 * horizon and elapsed_hours <= 1.25 * horizon:
                horizon_value = history_probabilities[-1] - history_probabilities[-horizon - 1]
                horizon_count[horizon_position] = horizon_count[horizon_position] + 1
                horizon_change[horizon_position] = horizon_change[horizon_position] + horizon_value
                horizon_squared[horizon_position] = (
                    horizon_squared[horizon_position] + horizon_value * horizon_value
                )
    if ordinal % 24 == 0 and market in close_by_market:
        hours_to_close = (close_by_market[market] - observed_time) / 3600.0
        if hours_to_close >= 0.0:
            close_band = close_index(hours_to_close)
            outcome = payout_by_market[market]
            error = outcome - probability
            calibration_count[close_band] = calibration_count[close_band] + 1
            calibration_probability[close_band] = calibration_probability[close_band] + probability
            calibration_outcome[close_band] = calibration_outcome[close_band] + outcome
            calibration_brier[close_band] = calibration_brier[close_band] + error * error
    previous_market = market
    previous_ordinal = ordinal
    previous_time = observed_time
    previous_probability = probability

regular_values = regular_changes[:regular_cursor]
regular_absolute_values = regular_abs_changes[:regular_cursor]
regular_mean = sum(regular_values) / regular_cursor
regular_variance_sum = 0.0
regular_fourth_sum = 0.0
for change in regular_values:
    centered = change - regular_mean
    regular_variance_sum = regular_variance_sum + centered * centered
    regular_fourth_sum = regular_fourth_sum + centered * centered * centered * centered
regular_variance = regular_variance_sum / regular_cursor
regular_kurtosis = regular_fourth_sum / regular_cursor / (regular_variance * regular_variance)

state_rows = []
state_labels = ["p_le_002", "p_002_020", "p_020_080", "p_080_098", "p_ge_098"]
for state in range(5):
    count = state_count[state]
    mean_change = None
    variance = None
    mean_wright_fisher_scale = None
    if count > 0:
        mean_change = state_change[state] / count
        variance = state_squared[state] / count - mean_change * mean_change
        mean_wright_fisher_scale = safe_rate(
            state_wright_fisher_scale[state], state_wright_fisher_count[state]
        )
    state_rows = state_rows + [
        {
            "band": state_labels[state],
            "count": count,
            "zero_rate": safe_rate(state_zero[state], count),
            "mean_change": mean_change,
            "variance": variance,
            "mean_wright_fisher_scaled_square": mean_wright_fisher_scale,
        }
    ]

quiet_rows = []
quiet_labels = ["quiet_0", "quiet_1_5", "quiet_6_23", "quiet_24_plus"]
for quiet in range(4):
    quiet_rows = quiet_rows + [
        {
            "band": quiet_labels[quiet],
            "count": quiet_count[quiet],
            "next_move_rate": safe_rate(quiet_move[quiet], quiet_count[quiet]),
            "mean_absolute_change": safe_rate(quiet_abs_change[quiet], quiet_count[quiet]),
        }
    ]

close_rows = []
close_labels = ["le_24h", "24_72h", "72_168h", "gt_168h"]
for close_band in range(4):
    close_rows = close_rows + [
        {
            "band": close_labels[close_band],
            "count": close_count[close_band],
            "next_move_rate": safe_rate(close_move[close_band], close_count[close_band]),
            "mean_absolute_change": safe_rate(
                close_abs_change[close_band], close_count[close_band]
            ),
        }
    ]

calibration_rows = []
for close_band in range(4):
    calibration_rows = calibration_rows + [
        {
            "band": close_labels[close_band],
            "count": calibration_count[close_band],
            "mean_probability": safe_rate(
                calibration_probability[close_band], calibration_count[close_band]
            ),
            "outcome_rate": safe_rate(
                calibration_outcome[close_band], calibration_count[close_band]
            ),
            "brier": safe_rate(calibration_brier[close_band], calibration_count[close_band]),
        }
    ]

variance_rows = []
for horizon_position in range(len(horizons)):
    count = horizon_count[horizon_position]
    mean_change = horizon_change[horizon_position] / count
    variance = horizon_squared[horizon_position] / count - mean_change * mean_change
    variance_rows = variance_rows + [
        {
            "horizon_hours": horizons[horizon_position],
            "count": count,
            "mean_change": mean_change,
            "variance_ratio": variance / (horizons[horizon_position] * regular_variance),
        }
    ]

event_rows = []
event_zero_rates = []
event_mean_changes = []
event_variances = []
for event in range(maximum_event + 1):
    count = event_increment_count[event]
    if count > 0:
        mean_change = event_change_sum[event] / count
        variance = event_squared_sum[event] / count - mean_change * mean_change
        zero_rate = event_zero_count[event] / count
        event_zero_rates = event_zero_rates + [zero_rate]
        event_mean_changes = event_mean_changes + [mean_change]
        event_variances = event_variances + [variance]
        event_rows = event_rows + [
            {
                "event_ordinal": event,
                "count": count,
                "zero_rate": zero_rate,
                "mean_change": mean_change,
                "variance": variance,
            }
        ]

smooth_diffusion_contradicted = (
    safe_rate(regular_interior_zero, regular_interior_count) >= 0.25
    or regular_kurtosis >= 20.0
    or variance_rows[3]["variance_ratio"] < 0.75
    or variance_rows[3]["variance_ratio"] > 1.25
)

quiet_initial_rate = safe_rate(quiet_move[0], quiet_count[0])
quiet_long_rate = safe_rate(quiet_move[3], quiet_count[3])
quiet_rate_ratio = None
if quiet_initial_rate is not None and quiet_initial_rate > 0.0 and quiet_long_rate is not None:
    quiet_rate_ratio = quiet_long_rate / quiet_initial_rate

result = structured_return(
    "Fresh-development stochastic-process signatures for the Polymarket paper mandate.",
    {
        "schema_version": "polymarket-stochastic-process-signatures/v1",
        "market_count": market_count,
        "event_count": len(event_rows),
        "observation_count": len(probabilities),
        "all_increment_count": all_increment_count,
        "all_zero_rate": safe_rate(all_zero_count, all_increment_count),
        "regular_increment_count": regular_cursor,
        "regular_increment_mean": regular_mean,
        "regular_increment_variance": regular_variance,
        "regular_increment_kurtosis": regular_kurtosis,
        "regular_interior_zero_rate": safe_rate(regular_interior_zero, regular_interior_count),
        "regular_absolute_change_quantiles": {
            "p50": quantile(regular_absolute_values, 0.50),
            "p90": quantile(regular_absolute_values, 0.90),
            "p99": quantile(regular_absolute_values, 0.99),
            "p999": quantile(regular_absolute_values, 0.999),
        },
        "elapsed_wait_between_nonzero_moves_hours": {
            "count": waiting_cursor,
            "p50": quantile(waiting_hours[:waiting_cursor], 0.50),
            "p90": quantile(waiting_hours[:waiting_cursor], 0.90),
            "p99": quantile(waiting_hours[:waiting_cursor], 0.99),
        },
        "nonzero_sign_reversal_rate": safe_rate(nonzero_sign_reversal, nonzero_sign_count),
        "adjacent_nonzero_reversal_rate": safe_rate(adjacent_sign_reversal, adjacent_sign_count),
        "low_boundary_next_sample_persistence": safe_rate(low_boundary_stay, low_boundary_count),
        "high_boundary_next_sample_persistence": safe_rate(high_boundary_stay, high_boundary_count),
        "state_bands": state_rows,
        "quiet_run_bands": quiet_rows,
        "quiet_24_plus_to_quiet_0_move_rate_ratio": quiet_rate_ratio,
        "time_to_close_bands": close_rows,
        "terminal_calibration_by_time_to_close": calibration_rows,
        "variance_scaling": variance_rows,
        "event_distribution": {
            "event_count": len(event_rows),
            "zero_rate_p10_p50_p90": [
                quantile(event_zero_rates, 0.10),
                quantile(event_zero_rates, 0.50),
                quantile(event_zero_rates, 0.90),
            ],
            "mean_change_min_p50_max": [
                min(event_mean_changes),
                quantile(event_mean_changes, 0.50),
                max(event_mean_changes),
            ],
            "variance_p10_p50_p90": [
                quantile(event_variances, 0.10),
                quantile(event_variances, 0.50),
                quantile(event_variances, 0.90),
            ],
            "positive_mean_change_event_count": sum(
                [1 for value in event_mean_changes if value > 0.0]
            ),
            "rows": event_rows,
        },
        "coverage_checks": {
            "order_break_count": order_break_count,
            "unknown_close_count": unknown_close_count,
            "negative_time_to_close_count": negative_time_to_close_count,
        },
        "predeclared_signature_checks": {
            "smooth_continuous_diffusion_contradicted": smooth_diffusion_contradicted,
            "constant_intensity_questioned_by_factor_two": (
                quiet_rate_ratio is not None and (quiet_rate_ratio < 0.5 or quiet_rate_ratio > 2.0)
            ),
        },
    },
    warnings=[
        "These are registered sampled YES probabilities, not latent beliefs or executable quotes.",
        "The cohort conditions on resolved binary contracts with at least 24 retained samples.",
        "Exact zeros may reflect the source sampling and stale observations as well as economics.",
        "Variance ratios use overlapping paths and are descriptive rather than IID test statistics.",
        "Close time is a market lifecycle field, while terminal payout becomes available at resolution.",
        "No fitted model, trade rule, protected value, or terminal scientific conclusion is produced.",
    ],
)
