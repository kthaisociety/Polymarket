price_markets = read("polymarket-development-prices", "market_id")
price_events = read("polymarket-development-prices", "event_id")
price_times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")
outcome_markets = read("polymarket-development-outcomes", "market_id")
outcome_events = read("polymarket-development-outcomes", "event_id")
questions = read("polymarket-development-outcomes", "question")


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


event_ids = [
    "716150",
    "716151",
    "716152",
    "716153",
    "716154",
    "716156",
    "716157",
    "716159",
]
event_start = 1784649600.0
signal_threshold_per_leg = 0.015
cost_screen_per_leg = 0.01
maximum_sync_span_seconds = 300.0

points = {}
for row in range(len(price_markets)):
    if price_events[row] in event_ids:
        market = price_markets[row]
        if market not in points:
            points[market] = []
        points[market] = points[market] + [[price_times[row], probabilities[row]]]

markets_by_event = {}
bounds_by_event = {}
for row in range(len(outcome_markets)):
    event_id = outcome_events[row]
    if event_id in event_ids:
        if event_id not in markets_by_event:
            markets_by_event[event_id] = []
            bounds_by_event[event_id] = []
        market = outcome_markets[row]
        markets_by_event[event_id] = markets_by_event[event_id] + [market]
        bounds_by_event[event_id] = bounds_by_event[event_id] + [
            bracket_bounds(questions[row])
        ]

semantic_audit = []
for event_id in event_ids:
    bounds = sorted(bounds_by_event[event_id])
    assert len(bounds) == len(markets_by_event[event_id])
    assert len(bounds) >= 2
    for ordinal in range(1, len(bounds)):
        assert bounds[ordinal - 1][1] < bounds[ordinal][0]
    semantic_audit = semantic_audit + [
        {
            "event_id": event_id,
            "market_count": len(bounds),
            "minimum_lower_bound": bounds[0][0],
            "maximum_upper_bound": bounds[-1][1],
            "pairwise_nonoverlapping": True,
        }
    ]

portfolio_rows = []
excluded_incomplete_snapshots = 0
excluded_execution_sync = 0
excluded_future_sync = 0
for event_id in event_ids:
    markets = markets_by_event[event_id]
    market_count = len(markets)
    for day in range(1, 6):
        decision_time = event_start + day * 86400.0
        execution_points = []
        future_points = []
        for market in markets:
            execution = None
            future = None
            for point in points[market]:
                if decision_time <= point[0] and point[0] <= decision_time + 7200.0:
                    if execution is None or point[0] < execution[0]:
                        execution = point
                if decision_time + 86400.0 <= point[0] and point[0] <= decision_time + 93600.0:
                    if future is None or point[0] < future[0]:
                        future = point
            if execution is not None:
                execution_points = execution_points + [execution]
            if future is not None:
                future_points = future_points + [future]
        if len(execution_points) != market_count or len(future_points) != market_count:
            excluded_incomplete_snapshots = excluded_incomplete_snapshots + 1
        else:
            execution_times = [point[0] for point in execution_points]
            future_times = [point[0] for point in future_points]
            execution_span = max(execution_times) - min(execution_times)
            future_span = max(future_times) - min(future_times)
            if execution_span > maximum_sync_span_seconds:
                excluded_execution_sync = excluded_execution_sync + 1
            elif future_span > maximum_sync_span_seconds:
                excluded_future_sync = excluded_future_sync + 1
            else:
                execution_sum = sum(point[1] for point in execution_points)
                future_sum = sum(point[1] for point in future_points)
                overround_per_leg = (execution_sum - 1.0) / market_count
                decline_per_leg = (execution_sum - future_sum) / market_count
                portfolio_rows = portfolio_rows + [
                    {
                        "event_id": event_id,
                        "day": day,
                        "market_count": market_count,
                        "execution_sum": execution_sum,
                        "future_sum": future_sum,
                        "overround_per_leg": overround_per_leg,
                        "next_day_decline_per_leg": decline_per_leg,
                        "one_cent_screened_decline_per_leg": (
                            decline_per_leg - cost_screen_per_leg
                        ),
                        "signal": overround_per_leg >= signal_threshold_per_leg,
                        "execution_sync_span_seconds": execution_span,
                        "future_sync_span_seconds": future_span,
                    }
                ]

assert len(portfolio_rows) > 0
mean_overround = sum(row["overround_per_leg"] for row in portfolio_rows) / len(
    portfolio_rows
)
mean_decline = sum(row["next_day_decline_per_leg"] for row in portfolio_rows) / len(
    portfolio_rows
)
covariance = sum(
    (row["overround_per_leg"] - mean_overround)
    * (row["next_day_decline_per_leg"] - mean_decline)
    for row in portfolio_rows
)
overround_variance = sum(
    (row["overround_per_leg"] - mean_overround)
    * (row["overround_per_leg"] - mean_overround)
    for row in portfolio_rows
)
decline_variance = sum(
    (row["next_day_decline_per_leg"] - mean_decline)
    * (row["next_day_decline_per_leg"] - mean_decline)
    for row in portfolio_rows
)
correlation = None
if overround_variance > 0.0 and decline_variance > 0.0:
    correlation = covariance / sqrt(overround_variance * decline_variance)

signal_rows = [row for row in portfolio_rows if row["signal"]]
signal_count = len(signal_rows)
mean_screened_decline = None
positive_screened_share = None
if signal_count > 0:
    mean_screened_decline = sum(
        row["one_cent_screened_decline_per_leg"] for row in signal_rows
    ) / signal_count
    positive_screened_share = sum(
        1 for row in signal_rows if row["one_cent_screened_decline_per_leg"] > 0.0
    ) / signal_count

event_results = []
positive_event_mean_count = 0
for event_id in event_ids:
    event_values = [
        row["one_cent_screened_decline_per_leg"]
        for row in signal_rows
        if row["event_id"] == event_id
    ]
    event_mean = None
    if len(event_values) > 0:
        event_mean = sum(event_values) / len(event_values)
        if event_mean > 0.0:
            positive_event_mean_count = positive_event_mean_count + 1
    event_results = event_results + [
        {"event_id": event_id, "signal_count": len(event_values), "mean": event_mean}
    ]

gate_passed = (
    signal_count >= 10
    and mean_screened_decline is not None
    and mean_screened_decline > 0.0
    and positive_screened_share is not None
    and positive_screened_share >= 0.60
    and positive_event_mean_count >= 4
    and correlation is not None
    and correlation >= 0.20
)

result = structured_return(
    "Fixed discovery test of sampled mutually-exclusive bracket overround compression.",
    {
        "schema_version": "polymarket-bracket-overround-compression/v1",
        "event_ids": event_ids,
        "semantic_audit": semantic_audit,
        "eligible_portfolio_count": len(portfolio_rows),
        "excluded_incomplete_snapshots": excluded_incomplete_snapshots,
        "excluded_execution_sync": excluded_execution_sync,
        "excluded_future_sync": excluded_future_sync,
        "signal_threshold_per_leg": signal_threshold_per_leg,
        "cost_screen_per_leg": cost_screen_per_leg,
        "signal_count": signal_count,
        "mean_signal_screened_decline_per_leg": mean_screened_decline,
        "positive_signal_screened_share": positive_screened_share,
        "positive_signal_event_mean_count": positive_event_mean_count,
        "overround_to_next_day_decline_correlation": correlation,
        "event_results": event_results,
        "portfolio_rows": portfolio_rows,
        "predeclared_discovery_gate_passed": gate_passed,
        "protected_values_exposed": False,
    },
    warnings=[
        "Pairwise non-overlap establishes mutual exclusion but not bracket completeness.",
        "Cross-market snapshots are admitted only when all legs fall inside a five-minute span.",
        "Retained probabilities are sampled beliefs, not executable bid or ask quotes.",
        "The one-cent-per-leg screen is a falsifier, not a realized profit estimate.",
        "Shorting feasibility, collateral, spread, fees, fill probability, and legging risk are unavailable.",
        "Protected values remain unavailable.",
    ],
)
