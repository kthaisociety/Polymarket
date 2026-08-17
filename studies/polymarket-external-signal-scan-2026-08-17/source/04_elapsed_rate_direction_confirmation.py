price_markets = read("polymarket-development-prices", "market_id")
price_events = read("polymarket-development-prices", "event_id")
price_times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")
outcome_markets = read("polymarket-development-outcomes", "market_id")
outcome_events = read("polymarket-development-outcomes", "event_id")
questions = read("polymarket-development-outcomes", "question")

elon_events = read("polymarket-xtracker-elon-decision-counts", "event_id")
elon_times = read(
    "polymarket-xtracker-elon-decision-counts", "reference_time_epoch_seconds"
)
elon_counts = read(
    "polymarket-xtracker-elon-decision-counts", "cumulative_post_count"
)
white_house_events = read("polymarket-xtracker-white_house-decision-counts", "event_id")
white_house_times = read(
    "polymarket-xtracker-white_house-decision-counts", "reference_time_epoch_seconds"
)
white_house_counts = read(
    "polymarket-xtracker-white_house-decision-counts", "cumulative_post_count"
)
trump_events = read("polymarket-xtracker-trump_truth-decision-counts", "event_id")
trump_times = read(
    "polymarket-xtracker-trump_truth-decision-counts", "reference_time_epoch_seconds"
)
trump_counts = read(
    "polymarket-xtracker-trump_truth-decision-counts", "cumulative_post_count"
)


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


event_ids = ["716159", "716151", "716152"]
event_start = 1784649600.0
event_end = 1785254399.0
count_events = elon_events + white_house_events + trump_events
count_times = elon_times + white_house_times + trump_times
count_values = elon_counts + white_house_counts + trump_counts
assert len(count_events) == len(count_times)
assert len(count_events) == len(count_values)

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

signal_rows = []
all_rows = []
decision_counts = []
for event_id in event_ids:
    for day in range(1, 6):
        decision_time = event_start + day * 86400.0
        matches = [
            count_values[row]
            for row in range(len(count_events))
            if count_events[row] == event_id and count_times[row] == decision_time
        ]
        assert len(matches) == 1
        current_count = matches[0]
        decision_counts = decision_counts + [
            {"event_id": event_id, "day": day, "cumulative_count": current_count}
        ]
        elapsed_days = day + 0.0
        remaining_days = (event_end - decision_time) / 86400.0
        future_mean = current_count / elapsed_days * remaining_days
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
                structural = bracket_probability(
                    current_count, future_mean, bounds[0], bounds[1]
                )
                gap = structural - execution[1]
                direction = 1.0 if gap > 0.0 else -1.0
                realized = direction * (future[1] - execution[1])
                row = {
                    "event_id": event_id,
                    "day": day,
                    "market_id": market,
                    "absolute_gap": abs(gap),
                    "directional_sampled_change": realized,
                    "one_cent_screened_change": realized - 0.01,
                }
                all_rows = all_rows + [row]
                if abs(gap) >= 0.02:
                    signal_rows = signal_rows + [row]

event_results = []
positive_event_mean_count = 0
for event_id in event_ids:
    values = [
        row["one_cent_screened_change"]
        for row in signal_rows
        if row["event_id"] == event_id
    ]
    mean_value = None
    positive_share = None
    if len(values) > 0:
        mean_value = sum(values) / len(values)
        positive_share = sum(1 for value in values if value > 0.0) / len(values)
        if mean_value > 0.0:
            positive_event_mean_count = positive_event_mean_count + 1
    event_results = event_results + [
        {
            "event_id": event_id,
            "signal_count": len(values),
            "mean_one_cent_screened_change": mean_value,
            "positive_screened_share": positive_share,
        }
    ]

signal_count = len(signal_rows)
mean_screened_change = None
positive_screened_share = None
if signal_count > 0:
    mean_screened_change = sum(
        row["one_cent_screened_change"] for row in signal_rows
    ) / signal_count
    positive_screened_share = sum(
        1 for row in signal_rows if row["one_cent_screened_change"] > 0.0
    ) / signal_count

gate_passed = (
    signal_count >= 40
    and mean_screened_change is not None
    and mean_screened_change > 0.0
    and positive_screened_share is not None
    and positive_screened_share >= 0.60
    and positive_event_mean_count >= 2
)

result = structured_return(
    "Held-out development confirmation of elapsed-rate Poisson discrepancy direction.",
    {
        "schema_version": "xtracker-elapsed-rate-direction-confirmation/v1",
        "event_ids": event_ids,
        "decision_days": [1, 2, 3, 4, 5],
        "decision_counts": decision_counts,
        "eligible_row_count": len(all_rows),
        "signal_count": signal_count,
        "mean_one_cent_screened_change": mean_screened_change,
        "positive_screened_share": positive_screened_share,
        "positive_event_mean_count": positive_event_mean_count,
        "event_results": event_results,
        "predeclared_direction_confirmation_gate_passed": gate_passed,
        "protected_values_exposed": False,
    },
    warnings=[
        "The elapsed-rate direction rule was selected on five earlier development events.",
        "Confirmation events were fixed before their price paths were read by this analysis.",
        "Counts include only records with importedAt no later than the decision.",
        "Retained probabilities are sampled beliefs, not executable bid or ask quotes.",
        "The one-cent screen is a directional falsifier, not a realized profit estimate.",
        "Probability calibration was already rejected and is not reclaimed here.",
        "Protected values remain unavailable.",
    ],
)
