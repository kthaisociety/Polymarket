markets = read("polymarket-development-prices", "market_id")
events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")
outcome_markets = read("polymarket-development-outcomes", "market_id")
close_times = read("polymarket-development-outcomes", "close_time_epoch_seconds")

VIEW_NAMES = [
    "all_probability",
    "strict_interior_probability",
    "strict_interior_log_odds",
    "more_than_168h_to_close_probability",
    "zero_to_168h_to_close_probability",
]
COARSE_VIEW_NAMES = [
    "all_probability",
    "strict_interior_probability",
    "strict_interior_log_odds",
]
MINIMUM_EVENT_COUNT = 100
MINIMUM_CONTRAST_COUNT = 50


def quantile(values, fraction):
    if len(values) == 0:
        return None
    ordered = sorted(values)
    return ordered[int((len(ordered) - 1) * fraction)]


def fixed_bootstrap_interval(values, repetitions, seed):
    if len(values) == 0:
        return [None, None]
    state = seed
    means = []
    for repetition in range(repetitions):
        total = 0.0
        for draw in range(len(values)):
            state = (1103515245 * state + 12345) % 2147483648
            total = total + values[state % len(values)]
        means = means + [total / len(values)]
    return [quantile(means, 0.025), quantile(means, 0.975)]


def log_odds(probability):
    return log(probability / (1.0 - probability))


def view_is_eligible(view, start_probability, end_probability, hours_to_close):
    if view == 0:
        return hours_to_close >= 0.0
    if view == 1 or view == 2:
        return (
            start_probability > 0.02
            and start_probability < 0.98
            and end_probability > 0.02
            and end_probability < 0.98
            and hours_to_close >= 0.0
        )
    if view == 3:
        return hours_to_close > 168.0
    return hours_to_close >= 0.0 and hours_to_close <= 168.0


def transformed_change(view, start_probability, end_probability):
    if view == 2:
        return log_odds(end_probability) - log_odds(start_probability)
    return end_probability - start_probability


def variance_from_moments(count, total, squared):
    if count == 0:
        return None
    mean = total / count
    return max(0.0, squared / count - mean * mean)


def pooled_moments(counts, totals, squares, cubes, fourths):
    count = sum(counts)
    if count == 0:
        return {"count": 0, "mean": None, "variance": None, "kurtosis": None}
    total = sum(totals)
    squared = sum(squares)
    cubed = sum(cubes)
    fourth = sum(fourths)
    mean = total / count
    second = squared / count
    variance = max(0.0, second - mean * mean)
    central_fourth = (
        fourth / count
        - 4.0 * mean * cubed / count
        + 6.0 * mean * mean * second
        - 3.0 * mean * mean * mean * mean
    )
    kurtosis = None
    if variance > 0.0:
        kurtosis = central_fourth / (variance * variance)
    return {"count": count, "mean": mean, "variance": variance, "kurtosis": kurtosis}


def summarize_event_values(values, threshold, direction):
    if len(values) == 0:
        return {
            "eligible_event_count": 0,
            "event_equal_mean": None,
            "event_median": None,
            "event_p10": None,
            "event_p90": None,
            "threshold": threshold,
            "threshold_direction": direction,
            "passing_event_count": 0,
            "passing_event_share": None,
            "early_event_equal_mean": None,
            "late_event_equal_mean": None,
            "fixed_event_bootstrap_mean_interval_95": [None, None],
        }
    passing = 0
    for value in values:
        if direction == "above" and value > threshold:
            passing = passing + 1
        if direction == "below" and value < threshold:
            passing = passing + 1
    midpoint = len(values) // 2
    early = values[:midpoint]
    late = values[midpoint:]
    return {
        "eligible_event_count": len(values),
        "event_equal_mean": sum(values) / len(values),
        "event_median": quantile(values, 0.50),
        "event_p10": quantile(values, 0.10),
        "event_p90": quantile(values, 0.90),
        "threshold": threshold,
        "threshold_direction": direction,
        "passing_event_count": passing,
        "passing_event_share": passing / len(values),
        "early_event_equal_mean": None if len(early) == 0 else sum(early) / len(early),
        "late_event_equal_mean": None if len(late) == 0 else sum(late) / len(late),
        "fixed_event_bootstrap_mean_interval_95": fixed_bootstrap_interval(
            values, 2000, 20260818
        ),
    }


close_by_market = {}
for row in range(len(outcome_markets)):
    close_by_market[outcome_markets[row]] = close_times[row]

maximum_event = max(events)
event_slots = maximum_event + 1
view_count = len(VIEW_NAMES)
coarse_view_count = len(COARSE_VIEW_NAMES)

counts = [[0 for event in range(event_slots)] for view in range(view_count)]
zeros = [[0 for event in range(event_slots)] for view in range(view_count)]
totals = [[0.0 for event in range(event_slots)] for view in range(view_count)]
squares = [[0.0 for event in range(event_slots)] for view in range(view_count)]
cubes = [[0.0 for event in range(event_slots)] for view in range(view_count)]
fourths = [[0.0 for event in range(event_slots)] for view in range(view_count)]
horizon_counts = [[0 for event in range(event_slots)] for view in range(view_count)]
horizon_totals = [[0.0 for event in range(event_slots)] for view in range(view_count)]
horizon_squares = [[0.0 for event in range(event_slots)] for view in range(view_count)]
quiet_active_counts = [[0 for event in range(event_slots)] for view in range(view_count)]
quiet_active_moves = [[0 for event in range(event_slots)] for view in range(view_count)]
quiet_stale_counts = [[0 for event in range(event_slots)] for view in range(view_count)]
quiet_stale_moves = [[0 for event in range(event_slots)] for view in range(view_count)]
reversal_counts = [[0 for event in range(event_slots)] for view in range(view_count)]
reversal_moves = [[0 for event in range(event_slots)] for view in range(view_count)]

coarse_counts = [
    [0 for event in range(event_slots)] for view in range(coarse_view_count)
]
coarse_zeros = [
    [0 for event in range(event_slots)] for view in range(coarse_view_count)
]
coarse_totals = [
    [0.0 for event in range(event_slots)] for view in range(coarse_view_count)
]
coarse_squares = [
    [0.0 for event in range(event_slots)] for view in range(coarse_view_count)
]

order_break_count = 0
current_market = None
previous_ordinal = None
previous_time = None
previous_probability = None
quiet_run = 0
previous_nonzero_signs = [0 for view in range(view_count)]
history_ordinals = []
history_times = []
history_probabilities = []

for row in range(len(probabilities)):
    market = markets[row]
    event = events[row]
    ordinal = ordinals[row]
    observed_time = times[row]
    probability = probabilities[row]
    if market != current_market:
        current_market = market
        previous_ordinal = None
        previous_time = None
        previous_probability = None
        quiet_run = 0
        previous_nonzero_signs = [0 for view in range(view_count)]
        history_ordinals = []
        history_times = []
        history_probabilities = []
        if ordinal != 0:
            order_break_count = order_break_count + 1
    if previous_time is not None:
        regular = (
            ordinal == previous_ordinal + 1
            and observed_time > previous_time
            and observed_time - previous_time >= 2700.0
            and observed_time - previous_time <= 4500.0
        )
        if not regular:
            if ordinal != previous_ordinal + 1 or observed_time <= previous_time:
                order_break_count = order_break_count + 1
            quiet_run = 0
            previous_nonzero_signs = [0 for view in range(view_count)]
        else:
            hours_to_close = (close_by_market[market] - previous_time) / 3600.0
            raw_change = probability - previous_probability
            for view in range(view_count):
                if view_is_eligible(view, previous_probability, probability, hours_to_close):
                    change = transformed_change(view, previous_probability, probability)
                    counts[view][event] = counts[view][event] + 1
                    totals[view][event] = totals[view][event] + change
                    squares[view][event] = squares[view][event] + change * change
                    cubes[view][event] = cubes[view][event] + change * change * change
                    fourths[view][event] = fourths[view][event] + change * change * change * change
                    if change == 0.0:
                        zeros[view][event] = zeros[view][event] + 1
                    if quiet_run == 0:
                        quiet_active_counts[view][event] = quiet_active_counts[view][event] + 1
                        if change != 0.0:
                            quiet_active_moves[view][event] = quiet_active_moves[view][event] + 1
                    if quiet_run >= 24:
                        quiet_stale_counts[view][event] = quiet_stale_counts[view][event] + 1
                        if change != 0.0:
                            quiet_stale_moves[view][event] = quiet_stale_moves[view][event] + 1
                    if change != 0.0:
                        sign = 1
                        if change < 0.0:
                            sign = -1
                        if previous_nonzero_signs[view] != 0:
                            reversal_counts[view][event] = reversal_counts[view][event] + 1
                            if sign != previous_nonzero_signs[view]:
                                reversal_moves[view][event] = reversal_moves[view][event] + 1
                        previous_nonzero_signs[view] = sign
                else:
                    previous_nonzero_signs[view] = 0
            if raw_change == 0.0:
                quiet_run = quiet_run + 1
            else:
                quiet_run = 0

    history_ordinals = history_ordinals + [ordinal]
    history_times = history_times + [observed_time]
    history_probabilities = history_probabilities + [probability]
    if len(history_ordinals) > 25:
        history_ordinals = history_ordinals[1:]
        history_times = history_times[1:]
        history_probabilities = history_probabilities[1:]

    if len(history_ordinals) >= 7:
        start_position = len(history_ordinals) - 7
        if (
            ordinal - history_ordinals[start_position] == 6
            and observed_time - history_times[start_position] >= 16200.0
            and observed_time - history_times[start_position] <= 27000.0
        ):
            start_probability = history_probabilities[start_position]
            hours_to_close = (close_by_market[market] - history_times[start_position]) / 3600.0
            for view in range(coarse_view_count):
                if view_is_eligible(view, start_probability, probability, hours_to_close):
                    change = transformed_change(view, start_probability, probability)
                    coarse_counts[view][event] = coarse_counts[view][event] + 1
                    coarse_totals[view][event] = coarse_totals[view][event] + change
                    coarse_squares[view][event] = coarse_squares[view][event] + change * change
                    if change == 0.0:
                        coarse_zeros[view][event] = coarse_zeros[view][event] + 1

    if len(history_ordinals) == 25:
        if (
            ordinal - history_ordinals[0] == 24
            and observed_time - history_times[0] >= 64800.0
            and observed_time - history_times[0] <= 108000.0
        ):
            start_probability = history_probabilities[0]
            hours_to_close = (close_by_market[market] - history_times[0]) / 3600.0
            for view in range(view_count):
                if view_is_eligible(view, start_probability, probability, hours_to_close):
                    change = transformed_change(view, start_probability, probability)
                    horizon_counts[view][event] = horizon_counts[view][event] + 1
                    horizon_totals[view][event] = horizon_totals[view][event] + change
                    horizon_squares[view][event] = (
                        horizon_squares[view][event] + change * change
                    )

    previous_ordinal = ordinal
    previous_time = observed_time
    previous_probability = probability

view_rows = []
for view in range(view_count):
    zero_values = []
    variance_ratio_values = []
    quiet_ratio_values = []
    reversal_values = []
    for event in range(event_slots):
        if counts[view][event] >= MINIMUM_EVENT_COUNT:
            zero_values = zero_values + [zeros[view][event] / counts[view][event]]
        base_variance = variance_from_moments(
            counts[view][event], totals[view][event], squares[view][event]
        )
        horizon_variance = variance_from_moments(
            horizon_counts[view][event],
            horizon_totals[view][event],
            horizon_squares[view][event],
        )
        if (
            counts[view][event] >= MINIMUM_EVENT_COUNT
            and horizon_counts[view][event] >= MINIMUM_EVENT_COUNT
            and base_variance is not None
            and base_variance > 0.0
            and horizon_variance is not None
        ):
            variance_ratio_values = variance_ratio_values + [
                horizon_variance / (24.0 * base_variance)
            ]
        if (
            quiet_active_counts[view][event] >= MINIMUM_CONTRAST_COUNT
            and quiet_stale_counts[view][event] >= MINIMUM_CONTRAST_COUNT
        ):
            active_rate = quiet_active_moves[view][event] / quiet_active_counts[view][event]
            stale_rate = quiet_stale_moves[view][event] / quiet_stale_counts[view][event]
            if active_rate > 0.0:
                quiet_ratio_values = quiet_ratio_values + [stale_rate / active_rate]
        if reversal_counts[view][event] >= MINIMUM_CONTRAST_COUNT:
            reversal_values = reversal_values + [
                reversal_moves[view][event] / reversal_counts[view][event]
            ]
    moments = pooled_moments(
        counts[view], totals[view], squares[view], cubes[view], fourths[view]
    )
    view_rows = view_rows + [
        {
            "view": VIEW_NAMES[view],
            "pooled": {
                "increment_count": moments["count"],
                "mean_change": moments["mean"],
                "variance": moments["variance"],
                "raw_kurtosis": moments["kurtosis"],
                "exact_zero_rate": sum(zeros[view]) / sum(counts[view]),
                "horizon_24h_count": sum(horizon_counts[view]),
            },
            "event_summaries": {
                "exact_zero_rate": summarize_event_values(zero_values, 0.20, "above"),
                "variance_ratio_24h": summarize_event_values(
                    variance_ratio_values, 0.75, "below"
                ),
                "quiet_24_plus_to_quiet_0_move_rate_ratio": summarize_event_values(
                    quiet_ratio_values, 0.50, "below"
                ),
                "nonzero_sign_reversal_rate": summarize_event_values(
                    reversal_values, 0.50, "above"
                ),
            },
        }
    ]

coarse_rows = []
for view in range(coarse_view_count):
    zero_values = []
    variance_ratio_values = []
    for event in range(event_slots):
        if coarse_counts[view][event] >= MINIMUM_EVENT_COUNT:
            zero_values = zero_values + [
                coarse_zeros[view][event] / coarse_counts[view][event]
            ]
        coarse_variance = variance_from_moments(
            coarse_counts[view][event],
            coarse_totals[view][event],
            coarse_squares[view][event],
        )
        horizon_variance = variance_from_moments(
            horizon_counts[view][event],
            horizon_totals[view][event],
            horizon_squares[view][event],
        )
        if (
            coarse_counts[view][event] >= MINIMUM_EVENT_COUNT
            and horizon_counts[view][event] >= MINIMUM_EVENT_COUNT
            and coarse_variance is not None
            and coarse_variance > 0.0
            and horizon_variance is not None
        ):
            variance_ratio_values = variance_ratio_values + [
                horizon_variance / (4.0 * coarse_variance)
            ]
    coarse_rows = coarse_rows + [
        {
            "view": COARSE_VIEW_NAMES[view],
            "six_hour_increment_count": sum(coarse_counts[view]),
            "six_hour_exact_zero_rate": sum(coarse_zeros[view]) / sum(coarse_counts[view]),
            "event_summaries": {
                "six_hour_exact_zero_rate": summarize_event_values(
                    zero_values, 0.20, "above"
                ),
                "variance_ratio_24h_relative_to_6h": summarize_event_values(
                    variance_ratio_values, 0.75, "below"
                ),
            },
        }
    ]

interior_probability = view_rows[1]
interior_log_odds = view_rows[2]
far_from_close = view_rows[3]
near_close = view_rows[4]
coarse_all = coarse_rows[0]
robustness_gate_passed = (
    interior_probability["event_summaries"]["exact_zero_rate"]["eligible_event_count"] >= 30
    and interior_probability["event_summaries"]["exact_zero_rate"]["event_equal_mean"] > 0.20
    and interior_probability["event_summaries"]["variance_ratio_24h"]["eligible_event_count"] >= 30
    and interior_probability["event_summaries"]["variance_ratio_24h"]["event_equal_mean"] < 0.75
    and interior_log_odds["event_summaries"]["exact_zero_rate"]["eligible_event_count"] >= 30
    and interior_log_odds["event_summaries"]["exact_zero_rate"]["event_equal_mean"] > 0.20
    and interior_log_odds["event_summaries"]["variance_ratio_24h"]["eligible_event_count"] >= 30
    and interior_log_odds["event_summaries"]["variance_ratio_24h"]["event_equal_mean"] < 0.75
    and interior_log_odds["pooled"]["raw_kurtosis"] > 20.0
    and far_from_close["event_summaries"]["exact_zero_rate"]["eligible_event_count"] >= 20
    and far_from_close["event_summaries"]["exact_zero_rate"]["event_equal_mean"] > 0.20
    and far_from_close["event_summaries"]["variance_ratio_24h"]["eligible_event_count"] >= 20
    and far_from_close["event_summaries"]["variance_ratio_24h"]["event_equal_mean"] < 0.75
    and near_close["event_summaries"]["exact_zero_rate"]["eligible_event_count"] >= 20
    and near_close["event_summaries"]["exact_zero_rate"]["event_equal_mean"] > 0.20
    and near_close["event_summaries"]["variance_ratio_24h"]["eligible_event_count"] >= 20
    and near_close["event_summaries"]["variance_ratio_24h"]["event_equal_mean"] < 0.75
    and interior_probability["event_summaries"]["quiet_24_plus_to_quiet_0_move_rate_ratio"]["eligible_event_count"] >= 20
    and interior_probability["event_summaries"]["quiet_24_plus_to_quiet_0_move_rate_ratio"]["event_equal_mean"] < 0.50
    and coarse_all["six_hour_exact_zero_rate"] > 0.20
    and coarse_all["event_summaries"]["variance_ratio_24h_relative_to_6h"]["event_equal_mean"] < 0.75
)

result = structured_return(
    "Fixed representation, boundary, maturity, and sampling-clock robustness checks.",
    {
        "schema_version": "polymarket-process-representation-robustness/v1",
        "view_definitions": VIEW_NAMES,
        "coarse_clock_view_definitions": COARSE_VIEW_NAMES,
        "minimum_event_count": MINIMUM_EVENT_COUNT,
        "minimum_contrast_count": MINIMUM_CONTRAST_COUNT,
        "view_rows": view_rows,
        "coarse_clock_rows": coarse_rows,
        "robustness_gate_passed": robustness_gate_passed,
        "coverage_checks": {"order_break_count": order_break_count},
        "protected_values_exposed": False,
    },
    warnings=[
        "All views and thresholds were fixed before execution against this development capability.",
        "Log-odds increments use only rows with both probabilities strictly inside (0.02, 0.98); no clipping is applied.",
        "Six-hour and 24-hour increments require exact ordinal separation and fixed elapsed-time tolerances.",
        "Events are the uncertainty unit; repeated markets and observations within an event are dependent.",
        "Variance-ratio paths overlap and remain descriptive rather than IID test statistics.",
        "Maturity views use recorded close time, which need not equal resolution-information arrival time.",
        "These are sampled probabilities, not trades, quotes, latent beliefs, or executable returns.",
        "Ancestor and protected values remain unavailable.",
    ],
)
