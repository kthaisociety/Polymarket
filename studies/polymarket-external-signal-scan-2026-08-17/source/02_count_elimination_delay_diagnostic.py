price_markets = read("polymarket-development-prices", "market_id")
price_events = read("polymarket-development-prices", "event_id")
price_times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")
outcome_markets = read("polymarket-development-outcomes", "market_id")
outcome_events = read("polymarket-development-outcomes", "event_id")
questions = read("polymarket-development-outcomes", "question")
payouts = read("polymarket-development-outcomes", "resolution_payout")

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


event_ids = ["716154", "716156", "716153", "716150", "716157"]
post_events = cz_events + zelenskyy_events + nyc_events + khamenei_events + ted_events
post_available = cz_available + zelenskyy_available + nyc_available + khamenei_available + ted_available
post_values = cz_values + zelenskyy_values + nyc_values + khamenei_values + ted_values
assert len(post_events) == len(post_available)
assert len(post_events) == len(post_values)
for value in post_values:
    assert value == 1

points = {}
for row in range(len(price_markets)):
    if price_events[row] in event_ids:
        market = price_markets[row]
        if market not in points:
            points[market] = []
        points[market] = points[market] + [[price_times[row], probabilities[row]]]

event_results = []
all_execution_probabilities = []
all_delayed_changes = []
event_decline_wins = 0
semantic_matches = 0
for event_id in event_ids:
    available_times = []
    for row in range(len(post_events)):
        if post_events[row] == event_id:
            available_times = available_times + [post_available[row]]
    final_count = len(available_times)
    event_markets = []
    winning_bracket_count = 0
    matching_payout_count = 0
    for row in range(len(outcome_markets)):
        if outcome_events[row] == event_id:
            bounds = bracket_bounds(questions[row])
            contains_final = bounds[0] <= final_count and final_count <= bounds[1]
            if contains_final:
                winning_bracket_count = winning_bracket_count + 1
            if (contains_final and payouts[row] == 1.0) or (
                not contains_final and payouts[row] == 0.0
            ):
                matching_payout_count = matching_payout_count + 1
            event_markets = event_markets + [
                [outcome_markets[row], bounds[0], bounds[1], payouts[row]]
            ]
    semantic_match = winning_bracket_count == 1 and matching_payout_count == len(event_markets)
    if semantic_match:
        semantic_matches = semantic_matches + 1

    rows = []
    execution_probability_sum = 0.0
    delayed_change_sum = 0.0
    delayed_declines = 0
    for market in event_markets:
        upper = market[2]
        if upper < 999999 and final_count > upper:
            crossing_time = None
            for candidate_time in available_times:
                count_at_candidate = 0
                for available_time in available_times:
                    if available_time <= candidate_time:
                        count_at_candidate = count_at_candidate + 1
                if count_at_candidate > upper and (
                    crossing_time is None or candidate_time < crossing_time
                ):
                    crossing_time = candidate_time
            assert crossing_time is not None
            execution = None
            delayed = None
            for point in points[market[0]]:
                if crossing_time <= point[0] and point[0] <= crossing_time + 7200.0:
                    if execution is None or point[0] < execution[0]:
                        execution = point
            if execution is not None:
                for point in points[market[0]]:
                    if execution[0] + 3600.0 <= point[0] and point[0] <= execution[0] + 10800.0:
                        if delayed is None or point[0] < delayed[0]:
                            delayed = point
            if execution is not None and delayed is not None:
                change = delayed[1] - execution[1]
                execution_probability_sum = execution_probability_sum + execution[1]
                delayed_change_sum = delayed_change_sum + change
                all_execution_probabilities = all_execution_probabilities + [execution[1]]
                all_delayed_changes = all_delayed_changes + [change]
                if change < 0.0:
                    delayed_declines = delayed_declines + 1
                rows = rows + [
                    {
                        "market_id": market[0],
                        "upper_bound": upper,
                        "crossing_time": crossing_time,
                        "execution_delay_seconds": execution[0] - crossing_time,
                        "execution_probability": execution[1],
                        "delayed_hours": (delayed[0] - execution[0]) / 3600.0,
                        "delayed_probability": delayed[1],
                        "delayed_change": change,
                        "sampled_one_cent_decline": change <= -0.01,
                    }
                ]
    event_mean_execution = None
    event_mean_change = None
    if len(rows) > 0:
        event_mean_execution = execution_probability_sum / len(rows)
        event_mean_change = delayed_change_sum / len(rows)
        if event_mean_change < 0.0:
            event_decline_wins = event_decline_wins + 1
    event_results = event_results + [
        {
            "event_id": event_id,
            "registered_post_count": final_count,
            "market_count": len(event_markets),
            "winning_bracket_count": winning_bracket_count,
            "resolution_semantic_match": semantic_match,
            "eliminated_markets_with_delayed_pair": len(rows),
            "mean_execution_probability": event_mean_execution,
            "mean_delayed_change": event_mean_change,
            "delayed_decline_share": None if len(rows) == 0 else delayed_declines / len(rows),
            "rows": rows,
        }
    ]

mean_execution_probability = None
mean_delayed_change = None
decline_share = None
one_cent_decline_share = None
if len(all_delayed_changes) > 0:
    mean_execution_probability = sum(all_execution_probabilities) / len(
        all_execution_probabilities
    )
    mean_delayed_change = sum(all_delayed_changes) / len(all_delayed_changes)
    decline_share = sum(1 for value in all_delayed_changes if value < 0.0) / len(
        all_delayed_changes
    )
    one_cent_decline_share = sum(1 for value in all_delayed_changes if value <= -0.01) / len(
        all_delayed_changes
    )

passed = (
    semantic_matches == len(event_ids)
    and len(all_delayed_changes) >= 20
    and event_decline_wins >= 3
    and mean_execution_probability is not None
    and mean_execution_probability >= 0.02
    and mean_delayed_change is not None
    and mean_delayed_change <= -0.01
    and decline_share is not None
    and decline_share >= 0.60
)

result = structured_return(
    "Conservative XTracker count-elimination and sampled execution-delay diagnostic.",
    {
        "schema_version": "xtracker-count-elimination-delay/v1",
        "event_count": len(event_ids),
        "resolution_semantic_matches": semantic_matches,
        "delayed_pair_count": len(all_delayed_changes),
        "event_mean_decline_wins": event_decline_wins,
        "mean_execution_probability": mean_execution_probability,
        "mean_delayed_change": mean_delayed_change,
        "delayed_decline_share": decline_share,
        "sampled_one_cent_decline_share": one_cent_decline_share,
        "event_results": event_results,
        "predeclared_stale_elimination_gate_passed": passed,
        "protected_values_exposed": False,
    },
    warnings=[
        "XTracker importedAt is the conservative decision-time clock; createdAt is not used for signal availability.",
        "Current retained API responses prove included records, not historical completeness or deleted-post history.",
        "Resolution payouts are used only to audit that the retained count and bracket semantics match; they never enter a decision-time signal.",
        "Historical probability samples are not executable bid or ask quotes; the one-cent screen is an underlying-signal falsifier, not a profit claim.",
        "The diagnostic tests hard count elimination only; it does not fit or tune a posting-rate model.",
    ],
)
