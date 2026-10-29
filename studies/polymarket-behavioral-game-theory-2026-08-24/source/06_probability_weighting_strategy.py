"""Test fixed longshot-fade and favorite-follow rules against adjacent state rivals."""

markets = read("polymarket-development-prices", "market_id")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")

outcome_markets = read("polymarket-development-outcomes", "market_id")
outcome_events = read(
    "polymarket-development-outcomes", "event_chronological_ordinal"
)
outcome_labels = read("polymarket-development-outcomes", "outcome_label")
close_times = read("polymarket-development-outcomes", "close_time_epoch_seconds")
payouts = read("polymarket-development-outcomes", "resolution_payout")

horizon_hours = [72.0, 168.0]
horizon_tolerances = [12.0, 24.0]
strategy_names = [
    "LONGSHOT_FADE",
    "ADJACENT_LOW_FADE",
    "FAVORITE_FOLLOW",
    "ADJACENT_HIGH_FOLLOW",
]
adverse_execution_hurdle = 0.02
minimum_incremental_edge = 0.01
event_count = max(outcome_events) + 1

event_by_market = {}
close_by_market = {}
payout_by_market = {}
best_distance_by_market = {}
best_probability_by_market = {}
label_counts = {}
for row in range(len(outcome_markets)):
    market = outcome_markets[row]
    event_by_market[market] = outcome_events[row]
    close_by_market[market] = close_times[row]
    payout_by_market[market] = payouts[row]
    best_distance_by_market[market] = [None, None]
    best_probability_by_market[market] = [None, None]
    label = outcome_labels[row]
    if label not in label_counts:
        label_counts[label] = 0
    label_counts[label] = label_counts[label] + 1

order_break_count = 0
current_market = None
previous_ordinal = None
previous_time = None
for row in range(len(probabilities)):
    market = markets[row]
    ordinal = ordinals[row]
    observed_time = times[row]
    probability = probabilities[row]
    if market != current_market:
        current_market = market
        previous_ordinal = None
        previous_time = None
        if ordinal != 0:
            order_break_count = order_break_count + 1
    elif ordinal != previous_ordinal + 1 or observed_time <= previous_time:
        order_break_count = order_break_count + 1
    hours_to_close = (close_by_market[market] - observed_time) / 3600.0
    if hours_to_close >= 0.0:
        for horizon in range(2):
            distance = abs(hours_to_close - horizon_hours[horizon])
            best_distance = best_distance_by_market[market][horizon]
            if distance <= horizon_tolerances[horizon] and (
                best_distance is None or distance < best_distance
            ):
                best_distance_by_market[market][horizon] = distance
                best_probability_by_market[market][horizon] = probability
    previous_ordinal = ordinal
    previous_time = observed_time


def strategy_index(probability):
    if probability >= 0.02 and probability < 0.10:
        return 0
    if probability >= 0.10 and probability < 0.20:
        return 1
    if probability > 0.90 and probability <= 0.98:
        return 2
    if probability > 0.80 and probability <= 0.90:
        return 3
    return None


def safe_rate(numerator, denominator):
    if denominator == 0:
        return None
    return numerator / denominator


event_signal_count = [
    [[0 for event in range(event_count)] for horizon in range(2)]
    for strategy in range(4)
]
event_net_edge_sum = [
    [[0.0 for event in range(event_count)] for horizon in range(2)]
    for strategy in range(4)
]
market_count = [[0, 0] for strategy in range(4)]

for market in outcome_markets:
    event = event_by_market[market]
    payout = payout_by_market[market]
    for horizon in range(2):
        probability = best_probability_by_market[market][horizon]
        if probability is None:
            continue
        strategy = strategy_index(probability)
        if strategy is None:
            continue
        if strategy <= 1:
            gross_edge = probability - payout
        else:
            gross_edge = payout - probability
        net_edge = gross_edge - adverse_execution_hurdle
        market_count[strategy][horizon] = market_count[strategy][horizon] + 1
        event_signal_count[strategy][horizon][event] = (
            event_signal_count[strategy][horizon][event] + 1
        )
        event_net_edge_sum[strategy][horizon][event] = (
            event_net_edge_sum[strategy][horizon][event] + net_edge
        )

strategy_rows = []
strategy_metrics = [[None, None] for strategy in range(4)]
for strategy in range(4):
    for horizon in range(2):
        event_edges = []
        early_edges = []
        late_edges = []
        positive_event_count = 0
        for event in range(event_count):
            count = event_signal_count[strategy][horizon][event]
            if count > 0:
                edge = event_net_edge_sum[strategy][horizon][event] / count
                event_edges = event_edges + [edge]
                if edge > 0.0:
                    positive_event_count = positive_event_count + 1
                if event < event_count // 2:
                    early_edges = early_edges + [edge]
                else:
                    late_edges = late_edges + [edge]
        metrics = {
            "strategy": strategy_names[strategy],
            "hours_before_close": horizon_hours[horizon],
            "market_count": market_count[strategy][horizon],
            "event_count": len(event_edges),
            "event_macro_net_edge": safe_rate(sum(event_edges), len(event_edges)),
            "early_event_macro_net_edge": safe_rate(sum(early_edges), len(early_edges)),
            "late_event_macro_net_edge": safe_rate(sum(late_edges), len(late_edges)),
            "positive_event_share": safe_rate(positive_event_count, len(event_edges)),
        }
        strategy_metrics[strategy][horizon] = metrics
        strategy_rows = strategy_rows + [metrics]

paired_rows = []
paired_metrics = [[None, None], [None, None]]
pair_names = ["LONGSHOT_MINUS_ADJACENT_LOW", "FAVORITE_MINUS_ADJACENT_HIGH"]
for pair in range(2):
    strategy = pair * 2
    control = strategy + 1
    for horizon in range(2):
        differences = []
        early_differences = []
        late_differences = []
        for event in range(event_count):
            strategy_count = event_signal_count[strategy][horizon][event]
            control_count = event_signal_count[control][horizon][event]
            if strategy_count > 0 and control_count > 0:
                strategy_edge = (
                    event_net_edge_sum[strategy][horizon][event] / strategy_count
                )
                control_edge = event_net_edge_sum[control][horizon][event] / control_count
                difference = strategy_edge - control_edge
                differences = differences + [difference]
                if event < event_count // 2:
                    early_differences = early_differences + [difference]
                else:
                    late_differences = late_differences + [difference]
        metrics = {
            "comparison": pair_names[pair],
            "hours_before_close": horizon_hours[horizon],
            "paired_event_count": len(differences),
            "paired_event_macro_difference": safe_rate(
                sum(differences), len(differences)
            ),
            "early_paired_difference": safe_rate(
                sum(early_differences), len(early_differences)
            ),
            "late_paired_difference": safe_rate(
                sum(late_differences), len(late_differences)
            ),
        }
        paired_metrics[pair][horizon] = metrics
        paired_rows = paired_rows + [metrics]


def strategy_passed(strategy, pair, minimum_markets, minimum_events):
    for horizon in range(2):
        row = strategy_metrics[strategy][horizon]
        paired = paired_metrics[pair][horizon]
        if (
            row["market_count"] < minimum_markets
            or row["event_count"] < minimum_events
            or row["event_macro_net_edge"] is None
            or row["event_macro_net_edge"] <= 0.0
            or paired["paired_event_macro_difference"] is None
            or paired["paired_event_macro_difference"] < minimum_incremental_edge
        ):
            return False
    final_row = strategy_metrics[strategy][1]
    return (
        final_row["early_event_macro_net_edge"] is not None
        and final_row["late_event_macro_net_edge"] is not None
        and final_row["early_event_macro_net_edge"] > 0.0
        and final_row["late_event_macro_net_edge"] > 0.0
    )


longshot_passed = strategy_passed(0, 0, 100, 30)
favorite_passed = strategy_passed(2, 1, 30, 20)
result = structured_return(
    "Fixed probability-weighting strategy screen against adjacent probability-state rivals.",
    {
        "schema_version": "polymarket-probability-weighting-strategy/v1",
        "adverse_execution_hurdle": adverse_execution_hurdle,
        "minimum_incremental_edge": minimum_incremental_edge,
        "horizon_hours": horizon_hours,
        "horizon_tolerances": horizon_tolerances,
        "probability_bands": {
            "LONGSHOT_FADE": "[0.02,0.10)",
            "ADJACENT_LOW_FADE": "[0.10,0.20)",
            "FAVORITE_FOLLOW": "(0.90,0.98]",
            "ADJACENT_HIGH_FOLLOW": "(0.80,0.90]",
        },
        "label_counts": label_counts,
        "all_paths_are_yes_labeled": label_counts == {"Yes": len(outcome_markets)},
        "order_break_count": order_break_count,
        "strategy_rows": strategy_rows,
        "paired_rows": paired_rows,
        "decisions": {
            "LONGSHOT_FADE": {
                "passed": longshot_passed,
                "status": (
                    "RETAIN_FOR_FRESH_EVALUATION"
                    if longshot_passed
                    else "REJECT_FIXED_CANDIDATE"
                ),
                "minimum_markets": 100,
                "minimum_events": 30,
            },
            "FAVORITE_FOLLOW": {
                "passed": favorite_passed,
                "status": (
                    "RETAIN_FOR_FRESH_EVALUATION"
                    if favorite_passed
                    else "REJECT_FIXED_CANDIDATE"
                ),
                "minimum_markets": 30,
                "minimum_events": 20,
            },
        },
    },
    warnings=[
        "The whole-event development partition is selection-exposed; protected values remain hidden.",
        "Sampled probabilities are not executable bid or ask quotes.",
        "Each market contributes at most one sample per fixed horizon.",
        "Event-macro and paired-event summaries preserve the primary dependence boundary.",
        "The two-cent hurdle is a stress screen, not an observed spread, fee, depth, or impact model.",
        "Passing permits only fresh immutable evaluation, never promotion or trading.",
    ],
)
