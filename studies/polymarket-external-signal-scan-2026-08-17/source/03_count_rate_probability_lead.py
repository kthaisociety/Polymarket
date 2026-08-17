price_markets = read("polymarket-development-prices", "market_id")
price_events = read("polymarket-development-prices", "event_id")
price_times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")
outcome_markets = read("polymarket-development-outcomes", "market_id")
outcome_events = read("polymarket-development-outcomes", "event_id")
questions = read("polymarket-development-outcomes", "question")

cz_events = read("polymarket-xtracker-cz-posts", "event_id")
cz_available = read("polymarket-xtracker-cz-posts", "available_at_epoch_seconds")
cz_values = read("polymarket-xtracker-cz-posts", "post_imported")
zelenskyy_events = read("polymarket-xtracker-zelenskyy-posts", "event_id")
zelenskyy_available = read("polymarket-xtracker-zelenskyy-posts", "available_at_epoch_seconds")
zelenskyy_values = read("polymarket-xtracker-zelenskyy-posts", "post_imported")
nyc_events = read("polymarket-xtracker-nyc_mayor-posts", "event_id")
nyc_available = read("polymarket-xtracker-nyc_mayor-posts", "available_at_epoch_seconds")
nyc_values = read("polymarket-xtracker-nyc_mayor-posts", "post_imported")
khamenei_events = read("polymarket-xtracker-khamenei-posts", "event_id")
khamenei_available = read("polymarket-xtracker-khamenei-posts", "available_at_epoch_seconds")
khamenei_values = read("polymarket-xtracker-khamenei-posts", "post_imported")
ted_events = read("polymarket-xtracker-ted_cruz-posts", "event_id")
ted_available = read("polymarket-xtracker-ted_cruz-posts", "available_at_epoch_seconds")
ted_values = read("polymarket-xtracker-ted_cruz-posts", "post_imported")


def bracket_bounds(question):
    values = []
    digits = ""
    plus_after_first = False
    for character in question:
        if "0" <= character and character <= "9":
            digits = digits + character
        else:
            if len(digits) > 0:
                values = values + [int(digits)]
                digits = ""
                if len(values) == 1 and character == "+":
                    plus_after_first = True
                    break
                if len(values) == 2:
                    break
    if len(digits) > 0 and len(values) < 2:
        values = values + [int(digits)]
    assert len(values) >= 1
    if plus_after_first:
        return [values[0], 999999]
    assert len(values) >= 2
    return [values[0], values[1]]


def poisson_below(mean, cutoff):
    if cutoff <= 0:
        return 0.0
    probability = exp(-mean)
    total = probability
    for value in range(1, cutoff):
        probability = probability * mean / value
        total = total + probability
    return min(1.0, max(0.0, total))


def bracket_probability(current_count, future_mean, lower, upper):
    if current_count > upper:
        return 0.0
    future_lower = max(0, lower - current_count)
    if upper >= 999999:
        return 1.0 - poisson_below(future_mean, future_lower)
    future_upper = upper - current_count
    return max(
        0.0,
        poisson_below(future_mean, future_upper + 1)
        - poisson_below(future_mean, future_lower),
    )


event_ids = ["716154", "716156", "716153", "716150", "716157"]
event_start = 1784649600.0
event_end = 1785254399.0
post_events = cz_events + zelenskyy_events + nyc_events + khamenei_events + ted_events
post_available = cz_available + zelenskyy_available + nyc_available + khamenei_available + ted_available
post_values = cz_values + zelenskyy_values + nyc_values + khamenei_values + ted_values
assert len(post_events) == len(post_available)
assert len(post_events) == len(post_values)

points = {}
for row in range(len(price_markets)):
    if price_events[row] in event_ids:
        market = price_markets[row]
        if market not in points:
            points[market] = []
        points[market] = points[market] + [[price_times[row], probabilities[row]]]

market_bounds = {}
markets_by_event = {}
for row in range(len(outcome_markets)):
    if outcome_events[row] in event_ids:
        market_bounds[outcome_markets[row]] = bracket_bounds(questions[row])
        event_id = outcome_events[row]
        if event_id not in markets_by_event:
            markets_by_event[event_id] = []
        markets_by_event[event_id] = markets_by_event[event_id] + [outcome_markets[row]]

recipes = ["elapsed_rate_poisson", "trailing_24h_rate_poisson"]
metrics = {}
event_rows = {}
for event_id in event_ids:
    event_rows[event_id] = []
    for recipe in recipes + ["current_probability"]:
        metrics[(event_id, recipe)] = [0.0, 0.0, 0]

signal_rows = []
for event_id in event_ids:
    for day in range(1, 6):
        decision_time = event_start + day * 86400.0
        current_count = 0
        trailing_count = 0
        for row in range(len(post_events)):
            if post_events[row] == event_id and post_available[row] <= decision_time:
                current_count = current_count + post_values[row]
                if post_available[row] > decision_time - 86400.0:
                    trailing_count = trailing_count + post_values[row]
        elapsed_days = day + 0.0
        remaining_days = (event_end - decision_time) / 86400.0
        elapsed_future_mean = current_count / elapsed_days * remaining_days
        trailing_future_mean = trailing_count * remaining_days
        for market in markets_by_event[event_id]:
            execution = None
            future = None
            for point in points[market]:
                if decision_time <= point[0] and point[0] <= decision_time + 7200.0:
                    if execution is None or point[0] < execution[0]:
                        execution = point
                if decision_time + 86400.0 <= point[0] and point[0] <= decision_time + 93600.0:
                    if future is None or point[0] < future[0]:
                        future = point
            if execution is not None and future is not None:
                bounds = market_bounds[market]
                elapsed_prediction = bracket_probability(
                    current_count, elapsed_future_mean, bounds[0], bounds[1]
                )
                trailing_prediction = bracket_probability(
                    current_count, trailing_future_mean, bounds[0], bounds[1]
                )
                predictions = [elapsed_prediction, trailing_prediction]
                for recipe_ordinal in range(len(recipes)):
                    prediction = predictions[recipe_ordinal]
                    error = future[1] - prediction
                    metric = metrics[(event_id, recipes[recipe_ordinal])]
                    metric[0] = metric[0] + error * error
                    metric[1] = metric[1] + abs(error)
                    metric[2] = metric[2] + 1
                baseline_error = future[1] - execution[1]
                baseline = metrics[(event_id, "current_probability")]
                baseline[0] = baseline[0] + baseline_error * baseline_error
                baseline[1] = baseline[1] + abs(baseline_error)
                baseline[2] = baseline[2] + 1
                event_rows[event_id] = event_rows[event_id] + [1]
                for recipe_ordinal in range(len(recipes)):
                    prediction = predictions[recipe_ordinal]
                    gap = prediction - execution[1]
                    if abs(gap) >= 0.02:
                        direction = 1.0 if gap > 0.0 else -1.0
                        realized = direction * (future[1] - execution[1])
                        signal_rows = signal_rows + [
                            {
                                "event_id": event_id,
                                "day": day,
                                "market_id": market,
                                "recipe": recipes[recipe_ordinal],
                                "current_count": current_count,
                                "trailing_24h_count": trailing_count,
                                "execution_probability": execution[1],
                                "structural_probability": prediction,
                                "future_probability": future[1],
                                "absolute_gap": abs(gap),
                                "directional_sampled_change": realized,
                                "one_cent_screened_change": realized - 0.01,
                            }
                        ]

results = []
aggregate = {}
for recipe in recipes + ["current_probability"]:
    total_squared = 0.0
    total_absolute = 0.0
    total_count = 0
    event_mse = []
    event_wins = 0
    for event_id in event_ids:
        metric = metrics[(event_id, recipe)]
        assert metric[2] > 0
        mse = metric[0] / metric[2]
        event_mse = event_mse + [mse]
        total_squared = total_squared + metric[0]
        total_absolute = total_absolute + metric[1]
        total_count = total_count + metric[2]
        if recipe != "current_probability":
            baseline = metrics[(event_id, "current_probability")]
            if mse < baseline[0] / baseline[2]:
                event_wins = event_wins + 1
    aggregate[recipe] = [
        total_squared / total_count,
        sum(event_mse) / len(event_mse),
        total_absolute / total_count,
        event_wins,
    ]
    results = results + [
        {
            "recipe": recipe,
            "observation_mse": aggregate[recipe][0],
            "event_macro_mse": aggregate[recipe][1],
            "observation_mae": aggregate[recipe][2],
            "event_mse_wins_vs_current_probability": event_wins,
            "prediction_count": total_count,
        }
    ]

signal_summaries = []
for recipe in recipes:
    selected = [row for row in signal_rows if row["recipe"] == recipe]
    event_means = []
    event_positive = 0
    for event_id in event_ids:
        values = [
            row["one_cent_screened_change"]
            for row in selected
            if row["event_id"] == event_id
        ]
        if len(values) > 0:
            event_mean = sum(values) / len(values)
            event_means = event_means + [event_mean]
            if event_mean > 0.0:
                event_positive = event_positive + 1
    positive_share = None
    mean_screened_change = None
    if len(selected) > 0:
        positive_share = sum(
            1 for row in selected if row["one_cent_screened_change"] > 0.0
        ) / len(selected)
        mean_screened_change = sum(row["one_cent_screened_change"] for row in selected) / len(
            selected
        )
    signal_summaries = signal_summaries + [
        {
            "recipe": recipe,
            "signal_count": len(selected),
            "mean_one_cent_screened_change": mean_screened_change,
            "positive_screened_share": positive_share,
            "represented_event_count": len(event_means),
            "positive_event_mean_count": event_positive,
        }
    ]

passed_recipes = []
for summary in signal_summaries:
    recipe = summary["recipe"]
    if (
        aggregate[recipe][0] <= 0.90 * aggregate["current_probability"][0]
        and aggregate[recipe][1] <= 0.90 * aggregate["current_probability"][1]
        and aggregate[recipe][3] >= 3
        and summary["signal_count"] >= 40
        and summary["mean_one_cent_screened_change"] is not None
        and summary["mean_one_cent_screened_change"] > 0.0
        and summary["positive_screened_share"] is not None
        and summary["positive_screened_share"] >= 0.60
        and summary["positive_event_mean_count"] >= 3
    ):
        passed_recipes = passed_recipes + [recipe]

result = structured_return(
    "Fixed count-rate probability forecasts versus next-day retained market probabilities.",
    {
        "schema_version": "xtracker-count-rate-probability-lead/v1",
        "event_ids": event_ids,
        "decision_days": [1, 2, 3, 4, 5],
        "results": results,
        "signal_summaries": signal_summaries,
        "passed_recipes": passed_recipes,
        "predeclared_lead_gate_passed": len(passed_recipes) > 0,
        "protected_values_exposed": False,
    },
    warnings=[
        "Every source count uses importedAt no later than the decision; createdAt is not the availability clock.",
        "Poisson count rates are fixed within-event plug-in recipes, not tuned process claims.",
        "Next-day retained probabilities are sampled beliefs, not executable quotes or terminal outcomes.",
        "Repeated decisions within one event share information and are summarized by event as well as observation.",
        "A one-cent screened sampled change is a falsifier for a trading lead, not a profit estimate.",
        "Protected values remain unavailable.",
    ],
)
