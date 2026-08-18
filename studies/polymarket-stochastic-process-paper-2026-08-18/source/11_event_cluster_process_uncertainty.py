markets = read("polymarket-development-prices", "market_id")
events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")


def variance(values):
    if len(values) == 0:
        return None
    mean = sum(values) / len(values)
    squared = 0.0
    for value in values:
        centered = value - mean
        squared = squared + centered * centered
    return squared / len(values)


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


def metric_summary(rows, key, threshold, direction):
    values = []
    ordinals_for_values = []
    passes = 0
    for row in rows:
        value = row[key]
        if value is not None:
            values = values + [value]
            ordinals_for_values = ordinals_for_values + [row["event_ordinal"]]
            if (direction == "below" and value < threshold) or (
                direction == "above" and value > threshold
            ):
                passes = passes + 1
    midpoint = 0.0
    if len(ordinals_for_values) > 0:
        midpoint = max(ordinals_for_values) / 2.0
    early = []
    late = []
    for position in range(len(values)):
        if ordinals_for_values[position] <= midpoint:
            early = early + [values[position]]
        else:
            late = late + [values[position]]
    return {
        "eligible_event_count": len(values),
        "event_equal_mean": None if len(values) == 0 else sum(values) / len(values),
        "event_median": quantile(values, 0.50),
        "event_p10": quantile(values, 0.10),
        "event_p90": quantile(values, 0.90),
        "threshold": threshold,
        "threshold_direction": direction,
        "passing_event_count": passes,
        "passing_event_share": None if len(values) == 0 else passes / len(values),
        "fixed_event_bootstrap_mean_interval_95": fixed_bootstrap_interval(
            values, 2000, 20260818
        ),
        "early_event_equal_mean": None if len(early) == 0 else sum(early) / len(early),
        "late_event_equal_mean": None if len(late) == 0 else sum(late) / len(late),
    }


maximum_event = max(events)
base_changes = [[] for unused in range(maximum_event + 1)]
horizon_changes = [[] for unused in range(maximum_event + 1)]
interior_count = [0 for unused in range(maximum_event + 1)]
interior_zero = [0 for unused in range(maximum_event + 1)]
quiet_zero_count = [0 for unused in range(maximum_event + 1)]
quiet_zero_move = [0 for unused in range(maximum_event + 1)]
quiet_24_count = [0 for unused in range(maximum_event + 1)]
quiet_24_move = [0 for unused in range(maximum_event + 1)]
reversal_count = [0 for unused in range(maximum_event + 1)]
reversal_move = [0 for unused in range(maximum_event + 1)]

current_market = None
previous_market = None
previous_ordinal = None
previous_time = None
previous_probability = None
quiet_seconds = 0.0
previous_nonzero_sign = 0
history_times = []
history_probabilities = []
order_break_count = 0

for row in range(len(probabilities)):
    market = markets[row]
    event = events[row]
    ordinal = ordinals[row]
    observed_time = times[row]
    probability = probabilities[row]
    if market != current_market:
        current_market = market
        previous_market = None
        previous_ordinal = None
        previous_time = None
        previous_probability = None
        quiet_seconds = 0.0
        previous_nonzero_sign = 0
        history_times = []
        history_probabilities = []
        if ordinal != 0:
            order_break_count = order_break_count + 1
    if previous_market == market:
        if ordinal != previous_ordinal + 1 or observed_time <= previous_time:
            order_break_count = order_break_count + 1
            quiet_seconds = 0.0
            previous_nonzero_sign = 0
        else:
            elapsed = observed_time - previous_time
            if elapsed >= 2700.0 and elapsed <= 4500.0:
                change = probability - previous_probability
                base_changes[event] = base_changes[event] + [change]
                if previous_probability > 0.02 and previous_probability < 0.98:
                    interior_count[event] = interior_count[event] + 1
                    if change == 0.0:
                        interior_zero[event] = interior_zero[event] + 1
                if quiet_seconds == 0.0:
                    quiet_zero_count[event] = quiet_zero_count[event] + 1
                    if change != 0.0:
                        quiet_zero_move[event] = quiet_zero_move[event] + 1
                if quiet_seconds >= 86400.0:
                    quiet_24_count[event] = quiet_24_count[event] + 1
                    if change != 0.0:
                        quiet_24_move[event] = quiet_24_move[event] + 1
                if change != 0.0:
                    sign = 1
                    if change < 0.0:
                        sign = -1
                    if previous_nonzero_sign != 0:
                        reversal_count[event] = reversal_count[event] + 1
                        if sign != previous_nonzero_sign:
                            reversal_move[event] = reversal_move[event] + 1
                    previous_nonzero_sign = sign
                    quiet_seconds = 0.0
                else:
                    quiet_seconds = quiet_seconds + elapsed
            else:
                quiet_seconds = 0.0
                previous_nonzero_sign = 0
    history_times = history_times + [observed_time]
    history_probabilities = history_probabilities + [probability]
    if len(history_times) > 25:
        history_times = history_times[1:]
        history_probabilities = history_probabilities[1:]
    if len(history_times) == 25:
        elapsed = history_times[-1] - history_times[0]
        if elapsed >= 64800.0 and elapsed <= 108000.0:
            horizon_changes[event] = horizon_changes[event] + [
                history_probabilities[-1] - history_probabilities[0]
            ]
    previous_market = market
    previous_ordinal = ordinal
    previous_time = observed_time
    previous_probability = probability

event_rows = []
for event in range(maximum_event + 1):
    zero_rate = None
    variance_ratio = None
    quiet_ratio = None
    reversal_rate = None
    if interior_count[event] >= 100:
        zero_rate = interior_zero[event] / interior_count[event]
    base_variance = variance(base_changes[event])
    horizon_variance = variance(horizon_changes[event])
    if (
        len(base_changes[event]) >= 100
        and len(horizon_changes[event]) >= 100
        and base_variance is not None
        and base_variance > 0.0
        and horizon_variance is not None
    ):
        variance_ratio = horizon_variance / (24.0 * base_variance)
    if quiet_zero_count[event] >= 50 and quiet_24_count[event] >= 50:
        zero_move_rate = quiet_zero_move[event] / quiet_zero_count[event]
        quiet_move_rate = quiet_24_move[event] / quiet_24_count[event]
        if zero_move_rate > 0.0:
            quiet_ratio = quiet_move_rate / zero_move_rate
    if reversal_count[event] >= 50:
        reversal_rate = reversal_move[event] / reversal_count[event]
    event_rows = event_rows + [
        {
            "event_ordinal": event,
            "interior_increment_count": interior_count[event],
            "regular_interior_zero_rate": zero_rate,
            "base_increment_count": len(base_changes[event]),
            "horizon_24h_count": len(horizon_changes[event]),
            "variance_ratio_24h": variance_ratio,
            "quiet_0_count": quiet_zero_count[event],
            "quiet_24h_count": quiet_24_count[event],
            "quiet_24h_to_quiet_0_move_rate_ratio": quiet_ratio,
            "nonzero_reversal_pair_count": reversal_count[event],
            "nonzero_sign_reversal_rate": reversal_rate,
        }
    ]

result = structured_return(
    "Whole-event uncertainty and prevalence for fixed Polymarket process signatures.",
    {
        "schema_version": "polymarket-event-cluster-process-uncertainty/v1",
        "event_count": maximum_event + 1,
        "minimum_counts": {
            "interior_zero": 100,
            "variance_base_and_24h": 100,
            "quiet_0_and_quiet_24h": 50,
            "nonzero_reversal_pairs": 50,
        },
        "summaries": {
            "regular_interior_zero_rate": metric_summary(
                event_rows, "regular_interior_zero_rate", 0.20, "above"
            ),
            "variance_ratio_24h": metric_summary(
                event_rows, "variance_ratio_24h", 0.75, "below"
            ),
            "quiet_24h_to_quiet_0_move_rate_ratio": metric_summary(
                event_rows, "quiet_24h_to_quiet_0_move_rate_ratio", 0.50, "below"
            ),
            "nonzero_sign_reversal_rate": metric_summary(
                event_rows, "nonzero_sign_reversal_rate", 0.50, "above"
            ),
        },
        "event_rows": event_rows,
        "coverage_checks": {"order_break_count": order_break_count},
        "protected_values_exposed": False,
    },
    warnings=[
        "The event is the uncertainty unit; markets and repeated samples within an event are dependent.",
        "Fixed minimum counts leave sparse event metrics missing rather than pooling them after inspection.",
        "The deterministic event bootstrap summarizes eligible-event means and assumes sampled events are exchangeable.",
        "Variance ratios use overlapping paths and remain descriptive rather than IID test statistics.",
        "Threshold prevalence is a robustness diagnostic, not a null-hypothesis significance test.",
        "These are sampled probabilities, not trades, quotes, latent beliefs, or executable returns.",
        "Ancestor and protected events remain unavailable.",
    ],
)
