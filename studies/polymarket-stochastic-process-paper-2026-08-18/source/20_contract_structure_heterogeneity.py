markets = read("polymarket-development-prices", "market_id")
events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")

outcome_events = read("polymarket-development-outcomes", "event_chronological_ordinal")
open_times = read("polymarket-development-outcomes", "open_time_epoch_seconds")
close_times = read("polymarket-development-outcomes", "close_time_epoch_seconds")
point_counts = read("polymarket-development-outcomes", "price_point_count")


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


def breadth_label(count):
    if count == 1:
        return "one_market"
    if count <= 4:
        return "two_to_four_markets"
    return "at_least_five_markets"


def lifecycle_label(days):
    if days <= 30.0:
        return "at_most_30_days"
    if days <= 180.0:
        return "31_to_180_days"
    return "more_than_180_days"


def depth_label(count):
    if count < 500:
        return "fewer_than_500_points"
    if count < 2000:
        return "500_to_1999_points"
    return "at_least_2000_points"


def metric_group_rows(event_rows, stratum_key, labels, metric_key, threshold, direction, minimum):
    rows = []
    for label_index in range(len(labels)):
        label = labels[label_index]
        values = []
        event_count = 0
        passes = 0
        for row in event_rows:
            if row[stratum_key] == label:
                event_count = event_count + 1
                value = row[metric_key]
                if value is not None:
                    values = values + [value]
                    if (direction == "above" and value > threshold) or (
                        direction == "below" and value < threshold
                    ):
                        passes = passes + 1
        mean = None
        if len(values) > 0:
            mean = sum(values) / len(values)
        rows = rows + [
            {
                "stratum": label,
                "event_count": event_count,
                "eligible_event_count": len(values),
                "minimum_eligible_events_for_gate": minimum,
                "event_equal_mean": mean,
                "event_median": quantile(values, 0.50),
                "threshold": threshold,
                "threshold_direction": direction,
                "passing_event_count": passes,
                "passing_event_share": None if len(values) == 0 else passes / len(values),
                "fixed_event_bootstrap_mean_interval_95": fixed_bootstrap_interval(
                    values, 1000, 20260818 + 1000 * label_index + len(metric_key)
                ),
            }
        ]
    return rows


def metric_gate(rows, threshold, direction, minimum, minimum_strata):
    eligible_strata = 0
    contradictions = 0
    for row in rows:
        if row["eligible_event_count"] >= minimum:
            eligible_strata = eligible_strata + 1
            value = row["event_equal_mean"]
            if (direction == "above" and value <= threshold) or (
                direction == "below" and value >= threshold
            ):
                contradictions = contradictions + 1
    return {
        "eligible_stratum_count": eligible_strata,
        "minimum_required_strata": minimum_strata,
        "directional_contradiction_count": contradictions,
        "passed": eligible_strata >= minimum_strata and contradictions == 0,
    }


maximum_event = max(events)
event_market_counts = [0 for unused in range(maximum_event + 1)]
event_lifecycles = [[] for unused in range(maximum_event + 1)]
event_depths = [[] for unused in range(maximum_event + 1)]

for row in range(len(outcome_events)):
    event = outcome_events[row]
    event_market_counts[event] = event_market_counts[event] + 1
    event_lifecycles[event] = event_lifecycles[event] + [
        (close_times[row] - open_times[row]) / 86400.0
    ]
    event_depths[event] = event_depths[event] + [point_counts[row]]

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
        horizon_elapsed = history_times[-1] - history_times[0]
        if horizon_elapsed >= 64800.0 and horizon_elapsed <= 108000.0:
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
    lifecycle_days = quantile(event_lifecycles[event], 0.50)
    median_depth = quantile(event_depths[event], 0.50)
    event_rows = event_rows + [
        {
            "event_ordinal": event,
            "market_count": event_market_counts[event],
            "median_contract_lifecycle_days": lifecycle_days,
            "median_retained_point_count": median_depth,
            "breadth_stratum": breadth_label(event_market_counts[event]),
            "lifecycle_stratum": lifecycle_label(lifecycle_days),
            "depth_stratum": depth_label(median_depth),
            "regular_interior_zero_rate": zero_rate,
            "variance_ratio_24h": variance_ratio,
            "quiet_24h_to_quiet_0_move_rate_ratio": quiet_ratio,
            "nonzero_sign_reversal_rate": reversal_rate,
        }
    ]

partitions = [
    {
        "name": "event_breadth",
        "event_row_key": "breadth_stratum",
        "labels": ["one_market", "two_to_four_markets", "at_least_five_markets"],
    },
    {
        "name": "median_contract_lifecycle",
        "event_row_key": "lifecycle_stratum",
        "labels": ["at_most_30_days", "31_to_180_days", "more_than_180_days"],
    },
    {
        "name": "median_retained_sampling_depth",
        "event_row_key": "depth_stratum",
        "labels": [
            "fewer_than_500_points",
            "500_to_1999_points",
            "at_least_2000_points",
        ],
    },
]

partition_results = []
gate_passed = order_break_count == 0
for partition in partitions:
    zero_rows = metric_group_rows(
        event_rows,
        partition["event_row_key"],
        partition["labels"],
        "regular_interior_zero_rate",
        0.20,
        "above",
        10,
    )
    variance_rows = metric_group_rows(
        event_rows,
        partition["event_row_key"],
        partition["labels"],
        "variance_ratio_24h",
        0.75,
        "below",
        10,
    )
    reversal_rows = metric_group_rows(
        event_rows,
        partition["event_row_key"],
        partition["labels"],
        "nonzero_sign_reversal_rate",
        0.50,
        "above",
        10,
    )
    quiet_rows = metric_group_rows(
        event_rows,
        partition["event_row_key"],
        partition["labels"],
        "quiet_24h_to_quiet_0_move_rate_ratio",
        0.50,
        "below",
        5,
    )
    zero_gate = metric_gate(zero_rows, 0.20, "above", 10, 2)
    variance_gate = metric_gate(variance_rows, 0.75, "below", 10, 2)
    reversal_gate = metric_gate(reversal_rows, 0.50, "above", 10, 2)
    quiet_gate = metric_gate(quiet_rows, 0.50, "below", 5, 2)
    partition_passed = (
        zero_gate["passed"]
        and variance_gate["passed"]
        and reversal_gate["passed"]
        and quiet_gate["passed"]
    )
    if not partition_passed:
        gate_passed = False
    partition_results = partition_results + [
        {
            "partition": partition["name"],
            "strata": partition["labels"],
            "regular_interior_zero_rate": zero_rows,
            "variance_ratio_24h": variance_rows,
            "nonzero_sign_reversal_rate": reversal_rows,
            "quiet_24h_to_quiet_0_move_rate_ratio": quiet_rows,
            "gates": {
                "regular_interior_zero_rate": zero_gate,
                "variance_ratio_24h": variance_gate,
                "nonzero_sign_reversal_rate": reversal_gate,
                "quiet_24h_to_quiet_0_move_rate_ratio": quiet_gate,
            },
            "partition_gate_passed": partition_passed,
        }
    ]

result = structured_return(
    "Contract-structure heterogeneity of fixed Polymarket process signatures.",
    {
        "schema_version": "polymarket-contract-structure-heterogeneity/v1",
        "event_count": maximum_event + 1,
        "fixed_strata": {
            "event_breadth": [1, 4],
            "median_contract_lifecycle_days": [30.0, 180.0],
            "median_retained_point_count": [500, 2000],
        },
        "fixed_metric_thresholds": {
            "regular_interior_zero_rate": ["above", 0.20, 10],
            "variance_ratio_24h": ["below", 0.75, 10],
            "nonzero_sign_reversal_rate": ["above", 0.50, 10],
            "quiet_24h_to_quiet_0_move_rate_ratio": ["below", 0.50, 5],
        },
        "event_rows": event_rows,
        "partition_results": partition_results,
        "coverage_checks": {"order_break_count": order_break_count},
        "contract_structure_heterogeneity_gate_passed": gate_passed,
        "protected_values_exposed": False,
    },
    warnings=[
        "The event is the uncertainty unit; markets and repeated samples within an event are dependent.",
        "Every structural bin and eligibility threshold was fixed before stratified results were observed.",
        "Sparse strata remain visible and cannot be pooled or relabeled after inspection.",
        "Lifecycle and retained depth are corpus properties, not causal mechanisms.",
        "These are sampled probabilities, not trades, quotes, latent beliefs, or executable returns.",
        "Ancestor and final protected events remain unavailable.",
    ],
)
