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
        market_order = market_order + [market]
        market_lengths[market] = 0
        market_event_ordinals[market] = event_ordinals[row]
    points[(market, ordinals[row])] = [times[row], probabilities[row]]
    market_lengths[market] = market_lengths[market] + 1

horizons = [1, 6, 24]
models = ["martingale", "fixed_reversal", "fixed_momentum", "fitted_reversal", "state_drift"]
costs = [0.0, 0.005, 0.01, 0.02]
all_horizon_results = [None, None, None]

for horizon_index in range(len(horizons)):
    horizon = horizons[horizon_index]
    samples = {}
    event_sample_count = {}
    event_x_sum = {}
    event_y_sum = {}
    event_x_squared = {}
    event_x_y = {}
    event_p_sum = {}
    event_p_squared = {}
    event_p_y = {}
    excluded_irregular = 0
    for market in market_order:
        length = market_lengths[market]
        event = market_event_ordinals[market]
        for decision in range(horizon, length - horizon, horizon):
            trailing_start = points[(market, decision - horizon)]
            current = points[(market, decision)]
            future = points[(market, decision + horizon)]
            trailing_hours = (current[0] - trailing_start[0]) / 3600.0
            future_hours = (future[0] - current[0]) / 3600.0
            if (
                trailing_hours < 0.75 * horizon
                or trailing_hours > 1.25 * horizon
                or future_hours < 0.75 * horizon
                or future_hours > 1.25 * horizon
            ):
                excluded_irregular = excluded_irregular + 1
            else:
                x = current[1] - trailing_start[1]
                y = future[1] - current[1]
                p = current[1]
                if event not in event_sample_count:
                    event_sample_count[event] = 0
                    event_x_sum[event] = 0.0
                    event_y_sum[event] = 0.0
                    event_x_squared[event] = 0.0
                    event_x_y[event] = 0.0
                    event_p_sum[event] = 0.0
                    event_p_squared[event] = 0.0
                    event_p_y[event] = 0.0
                count = event_sample_count[event]
                samples[(event, count)] = [x, p, y]
                event_sample_count[event] = count + 1
                event_x_sum[event] = event_x_sum[event] + x
                event_y_sum[event] = event_y_sum[event] + y
                event_x_squared[event] = event_x_squared[event] + x * x
                event_x_y[event] = event_x_y[event] + x * y
                event_p_sum[event] = event_p_sum[event] + p
                event_p_squared[event] = event_p_squared[event] + p * p
                event_p_y[event] = event_p_y[event] + p * y

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
        p_sum = 0.0
        p_squared = 0.0
        p_y = 0.0
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
                p_sum = p_sum + event_p_sum[train_event] / count
                p_squared = p_squared + event_p_squared[train_event] / count
                p_y = p_y + event_p_y[train_event] / count
        fitted_reversal = fit_line(weight, x_sum, y_sum, x_squared, x_y)
        state_drift = fit_line(weight, p_sum, y_sum, p_squared, p_y)
        coefficient_paths = coefficient_paths + [
            {
                "test_event_ordinal": test_event,
                "fitted_reversal_intercept": fitted_reversal[0],
                "fitted_reversal_slope": fitted_reversal[1],
                "state_drift_intercept": state_drift[0],
                "state_drift_slope": state_drift[1],
            }
        ]
        test_events = test_events + [test_event]
        count = event_sample_count[test_event]
        for model in models:
            squared_error = 0.0
            absolute_error = 0.0
            directional_correct = 0
            directional_total = 0
            for cost in costs:
                event_metrics[(test_event, model, cost)] = [0.0, 0, 0]
            for sample_index in range(count):
                sample = samples[(test_event, sample_index)]
                x = sample[0]
                p = sample[1]
                y = sample[2]
                if model == "martingale":
                    prediction = 0.0
                elif model == "fixed_reversal":
                    prediction = clipped_change(p, -x)
                elif model == "fixed_momentum":
                    prediction = clipped_change(p, x)
                elif model == "fitted_reversal":
                    prediction = clipped_change(
                        p,
                        fitted_reversal[0] + fitted_reversal[1] * x,
                    )
                else:
                    prediction = clipped_change(p, state_drift[0] + state_drift[1] * p)
                error = y - prediction
                squared_error = squared_error + error * error
                absolute_error = absolute_error + abs(error)
                if prediction != 0.0 and y != 0.0:
                    directional_total = directional_total + 1
                    if prediction * y > 0.0:
                        directional_correct = directional_correct + 1
                for cost in costs:
                    if abs(prediction) > cost:
                        direction = 1.0
                        if prediction < 0.0:
                            direction = -1.0
                        metric = event_metrics[(test_event, model, cost)]
                        metric[0] = metric[0] + direction * y - cost
                        metric[1] = metric[1] + 1
                    event_metrics[(test_event, model, cost)][2] = count
            event_metrics[(test_event, model, "forecast")] = [
                squared_error / count,
                absolute_error / count,
                directional_correct,
                directional_total,
            ]

    model_results = []
    martingale_macro_mse = 0.0
    for event in test_events:
        martingale_macro_mse = martingale_macro_mse + event_metrics[
            (event, "martingale", "forecast")
        ][0]
    martingale_macro_mse = martingale_macro_mse / len(test_events)
    for model in models:
        macro_mse = 0.0
        macro_mae = 0.0
        market_squared = 0.0
        market_absolute = 0.0
        market_count = 0
        event_mse_wins = 0
        directional_correct = 0
        directional_total = 0
        for event in test_events:
            forecast = event_metrics[(event, model, "forecast")]
            count = event_sample_count[event]
            macro_mse = macro_mse + forecast[0]
            macro_mae = macro_mae + forecast[1]
            market_squared = market_squared + forecast[0] * count
            market_absolute = market_absolute + forecast[1] * count
            market_count = market_count + count
            directional_correct = directional_correct + forecast[2]
            directional_total = directional_total + forecast[3]
            if forecast[0] < event_metrics[(event, "martingale", "forecast")][0]:
                event_mse_wins = event_mse_wins + 1
        cost_results = []
        for cost in costs:
            event_net_means = []
            trade_count = 0
            decision_count = 0
            net_sum = 0.0
            positive_events = 0
            for event in test_events:
                metric = event_metrics[(event, model, cost)]
                event_mean = metric[0] / metric[2]
                event_net_means = event_net_means + [event_mean]
                net_sum = net_sum + metric[0]
                trade_count = trade_count + metric[1]
                decision_count = decision_count + metric[2]
                if event_mean > 0.0:
                    positive_events = positive_events + 1
            leave_one_out_min = None
            for omitted in range(len(event_net_means)):
                remaining_mean = (
                    sum(event_net_means) - event_net_means[omitted]
                ) / (len(event_net_means) - 1)
                if leave_one_out_min is None or remaining_mean < leave_one_out_min:
                    leave_one_out_min = remaining_mean
            cost_results = cost_results + [
                {
                    "round_trip_cost": cost,
                    "trade_count": trade_count,
                    "decision_count": decision_count,
                    "trade_rate": trade_count / decision_count,
                    "event_positive_count": positive_events,
                    "event_nonpositive_count": len(test_events) - positive_events,
                    "event_macro_net_per_decision": sum(event_net_means) / len(event_net_means),
                    "market_weighted_net_per_decision": net_sum / decision_count,
                    "leave_one_event_out_min_macro_net": leave_one_out_min,
                    "event_net_min": min(event_net_means),
                    "event_net_max": max(event_net_means),
                }
            ]
        model_results = model_results + [
            {
                "model": model,
                "test_event_count": len(test_events),
                "test_sample_count": market_count,
                "event_macro_mse": macro_mse / len(test_events),
                "event_macro_mse_change_vs_martingale": (
                    macro_mse / len(test_events) - martingale_macro_mse
                ),
                "market_weighted_mse": market_squared / market_count,
                "event_macro_mae": macro_mae / len(test_events),
                "market_weighted_mae": market_absolute / market_count,
                "event_mse_wins_vs_martingale": event_mse_wins,
                "directional_accuracy_nonzero": (
                    None
                    if directional_total == 0
                    else directional_correct / directional_total
                ),
                "cost_grid": cost_results,
            }
        ]
    all_horizon_results[horizon_index] = {
        "horizon_samples": horizon,
        "sampling": "non-overlapping ordinal decisions with 0.75x-1.25x elapsed-time filter",
        "excluded_irregular_decisions": excluded_irregular,
        "test_event_ordinals": test_events,
        "coefficient_paths": coefficient_paths,
        "models": model_results,
    }

result = structured_return(
    "One-event-ahead drift models and non-overlapping pseudo-trading cost grid.",
    {
        "minimum_training_event_count": 8,
        "fit_weighting": "equal event weight within every expanding training fold",
        "horizons": all_horizon_results,
        "trading_gate": {
            "required_round_trip_cost": 0.01,
            "minimum_positive_event_fraction": 0.60,
            "requires_positive_event_and_market_weighted_net": True,
            "requires_positive_leave_one_event_out_min": True,
        },
    },
    warnings=[
        "Pseudo-PnL marks entry and exit at sampled probabilities; it is not executable PnL.",
        "The cost grid is hypothetical and does not replace historical bid/ask and fillability.",
        "All learned coefficients use only earlier development event ordinals.",
        "Every tested model and cost is retained; the final seven protected events remain unavailable.",
    ],
)
