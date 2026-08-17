price_markets = read("polymarket-development-prices", "market_id")
event_ordinals = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")


def fit_line(weight, x_sum, y_sum, x_squared, cross):
    denominator = x_squared - x_sum * x_sum / weight
    if denominator == 0.0:
        return [y_sum / weight, 0.0]
    slope = (cross - x_sum * y_sum / weight) / denominator
    intercept = (y_sum - slope * x_sum) / weight
    return [intercept, slope]


def clipped_change(probability, predicted_change):
    predicted_price = max(0.0, min(1.0, probability + predicted_change))
    return predicted_price - probability


points = {}
market_lengths = {}
market_event_ordinals = {}
market_order = []
for row in range(len(price_markets)):
    market = price_markets[row]
    if market not in market_lengths:
        market_order.append(market)
        market_lengths[market] = 0
        market_event_ordinals[market] = event_ordinals[row]
    points[(market, ordinals[row])] = [times[row], probabilities[row]]
    market_lengths[market] = market_lengths[market] + 1

horizons = [1, 24]
cost = 0.01
variant_names = [
    "immediate_two_sided",
    "delayed_two_sided",
    "immediate_long_only",
    "delayed_long_only",
    "immediate_short_only",
    "delayed_short_only",
    "immediate_two_sided_active_1c",
    "delayed_two_sided_active_1c",
    "delayed_long_only_active_1c",
    "delayed_short_only_active_1c",
    "delayed_two_sided_low_probability",
    "delayed_two_sided_mid_probability",
    "delayed_two_sided_high_probability",
]
all_results = []

for horizon in horizons:
    samples = {}
    event_sample_count = {}
    event_x_sum = {}
    event_y_sum = {}
    event_x_squared = {}
    event_x_y = {}
    excluded_irregular = 0
    for market in market_order:
        length = market_lengths[market]
        event = market_event_ordinals[market]
        for decision in range(horizon, length - horizon - 1, horizon):
            trailing_start = points[(market, decision - horizon)]
            current = points[(market, decision)]
            delayed_entry = points[(market, decision + 1)]
            immediate_exit = points[(market, decision + horizon)]
            delayed_exit = points[(market, decision + horizon + 1)]
            trailing_hours = (current[0] - trailing_start[0]) / 3600.0
            delay_hours = (delayed_entry[0] - current[0]) / 3600.0
            immediate_hours = (immediate_exit[0] - current[0]) / 3600.0
            delayed_hours = (delayed_exit[0] - delayed_entry[0]) / 3600.0
            if (
                trailing_hours < 0.75 * horizon
                or trailing_hours > 1.25 * horizon
                or delay_hours < 0.75
                or delay_hours > 1.25
                or immediate_hours < 0.75 * horizon
                or immediate_hours > 1.25 * horizon
                or delayed_hours < 0.75 * horizon
                or delayed_hours > 1.25 * horizon
            ):
                excluded_irregular = excluded_irregular + 1
            else:
                x = current[1] - trailing_start[1]
                immediate_y = immediate_exit[1] - current[1]
                delayed_y = delayed_exit[1] - delayed_entry[1]
                if event not in event_sample_count:
                    event_sample_count[event] = 0
                    event_x_sum[event] = 0.0
                    event_y_sum[event] = 0.0
                    event_x_squared[event] = 0.0
                    event_x_y[event] = 0.0
                count = event_sample_count[event]
                samples[(event, count)] = [
                    x,
                    current[1],
                    immediate_y,
                    delayed_entry[1],
                    delayed_y,
                ]
                event_sample_count[event] = count + 1
                event_x_sum[event] = event_x_sum[event] + x
                event_y_sum[event] = event_y_sum[event] + immediate_y
                event_x_squared[event] = event_x_squared[event] + x * x
                event_x_y[event] = event_x_y[event] + x * immediate_y

    event_metrics = {}
    coefficient_paths = []
    test_events = []
    for test_event in range(8, 24):
        if test_event not in event_sample_count or event_sample_count[test_event] == 0:
            continue
        weight = 0.0
        x_sum = 0.0
        y_sum = 0.0
        x_squared = 0.0
        x_y = 0.0
        for train_event in range(test_event):
            count = 0
            if train_event in event_sample_count:
                count = event_sample_count[train_event]
            if count > 0:
                weight = weight + 1.0
                x_sum = x_sum + event_x_sum[train_event] / count
                y_sum = y_sum + event_y_sum[train_event] / count
                x_squared = x_squared + event_x_squared[train_event] / count
                x_y = x_y + event_x_y[train_event] / count
        fitted = fit_line(weight, x_sum, y_sum, x_squared, x_y)
        coefficient_paths.append(
            {
                "test_event_ordinal": test_event,
                "intercept": fitted[0],
                "slope": fitted[1],
            }
        )
        test_events.append(test_event)
        for variant in variant_names:
            event_metrics[(test_event, variant)] = [0.0, 0, 0]
        count = event_sample_count[test_event]
        for sample_index in range(count):
            sample = samples[(test_event, sample_index)]
            x = sample[0]
            immediate_p = sample[1]
            immediate_y = sample[2]
            delayed_y = sample[4]
            prediction = clipped_change(immediate_p, fitted[0] + fitted[1] * x)
            active = abs(x) >= 0.01
            low = immediate_p < 0.2
            mid = immediate_p >= 0.2 and immediate_p <= 0.8
            high = immediate_p > 0.8
            for variant in variant_names:
                eligible = True
                realized = immediate_y
                if "delayed" in variant:
                    realized = delayed_y
                if "long_only" in variant and prediction <= cost:
                    eligible = False
                if "short_only" in variant and prediction >= -cost:
                    eligible = False
                if "two_sided" in variant and abs(prediction) <= cost:
                    eligible = False
                if "active_1c" in variant and not active:
                    eligible = False
                if "low_probability" in variant and not low:
                    eligible = False
                if "mid_probability" in variant and not mid:
                    eligible = False
                if "high_probability" in variant and not high:
                    eligible = False
                metric = event_metrics[(test_event, variant)]
                if eligible:
                    direction = 1.0
                    if prediction < 0.0:
                        direction = -1.0
                    metric[0] = metric[0] + direction * realized - cost
                    metric[1] = metric[1] + 1
                metric[2] = metric[2] + 1

    variant_results = []
    for variant in variant_names:
        event_net_means = []
        net_sum = 0.0
        trade_count = 0
        decision_count = 0
        positive_events = 0
        for event in test_events:
            metric = event_metrics[(event, variant)]
            event_mean = metric[0] / metric[2]
            event_net_means.append(event_mean)
            net_sum = net_sum + metric[0]
            trade_count = trade_count + metric[1]
            decision_count = decision_count + metric[2]
            if event_mean > 0.0:
                positive_events = positive_events + 1
        leave_one_out_min = None
        for omitted in range(len(event_net_means)):
            remaining = (
                sum(event_net_means) - event_net_means[omitted]
            ) / (len(event_net_means) - 1)
            if leave_one_out_min is None or remaining < leave_one_out_min:
                leave_one_out_min = remaining
        variant_results.append(
            {
                "variant": variant,
                "trade_count": trade_count,
                "decision_count": decision_count,
                "trade_rate": trade_count / decision_count,
                "event_positive_count": positive_events,
                "test_event_count": len(test_events),
                "event_macro_net_per_decision": sum(event_net_means) / len(event_net_means),
                "observation_weighted_net_per_decision": net_sum / decision_count,
                "net_per_trade": None if trade_count == 0 else net_sum / trade_count,
                "leave_one_event_out_min_macro_net": leave_one_out_min,
                "passes_declared_stability_components": (
                    sum(event_net_means) / len(event_net_means) > 0.0
                    and net_sum / decision_count > 0.0
                    and positive_events / len(test_events) >= 0.60
                    and leave_one_out_min > 0.0
                ),
            }
        )
    all_results.append(
        {
            "horizon_samples": horizon,
            "excluded_irregular_decisions": excluded_irregular,
            "coefficient_paths": coefficient_paths,
            "variants": variant_results,
        }
    )

result = structured_return(
    "Predeclared execution-delay and position-side falsifiers for fitted reversal.",
    {
        "minimum_training_event_count": 8,
        "round_trip_cost": cost,
        "fit_weighting": "equal event weight within each expanding training fold",
        "decision_sampling": "non-overlapping by horizon; all variants share delay-eligible samples",
        "horizons": all_results,
        "candidate_survival_rule": (
            "delayed_two_sided and delayed_long_only must each pass all reported stability components"
        ),
    },
    warnings=[
        "Entry and exit remain sampled probabilities, not executable quotes.",
        "A one-observation delay is an execution falsifier, not a fill simulation.",
        "Long-only is directly interpretable as buy-then-sell; short-only requires separate authority.",
        "Probability regimes and active-move variants are diagnostics, not selectable gates.",
        "All coefficients use only earlier development events; protected values remain unavailable.",
    ],
)
