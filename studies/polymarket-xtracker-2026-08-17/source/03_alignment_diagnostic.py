price_markets = read("polymarket-development-prices", "market_id")
price_events = read("polymarket-development-prices", "event_id")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
outcome_markets = read("polymarket-development-outcomes", "market_id")
outcome_events = read("polymarket-development-outcomes", "event_id")
post_events = read("polymarket-xtracker-posts", "event_id")
post_reference_times = read("polymarket-xtracker-posts", "reference_time_epoch_seconds")
post_available_times = read("polymarket-xtracker-posts", "available_at_epoch_seconds")
post_values = read("polymarket-xtracker-posts", "post_imported")

event_id = "739241"
event_start = 1784995200.0
market_count = 0
for row in range(len(outcome_markets)):
    if outcome_events[row] == event_id:
        market_count = market_count + 1

points = {}
market_lengths = {}
for row in range(len(price_markets)):
    if price_events[row] == event_id:
        market = price_markets[row]
        points[(market, ordinals[row])] = times[row]
        if market not in market_lengths:
            market_lengths[market] = 0
        market_lengths[market] = max(market_lengths[market], ordinals[row] + 1)

blocks = []
for block in range(1, 7):
    target_time = event_start + block * 21600.0
    available_rows = 0
    legal_rows = 0
    min_gap = 999999.0
    max_gap = 0.0
    min_trailing_hours = 999.0
    max_trailing_hours = 0.0
    min_future_hours = 999.0
    max_future_hours = 0.0
    for market in market_lengths:
        best_ordinal = -1
        best_gap = 999999.0
        for ordinal in range(market_lengths[market]):
            gap = abs(points[(market, ordinal)] - target_time)
            if gap < best_gap:
                best_gap = gap
                best_ordinal = ordinal
        min_gap = min(min_gap, best_gap)
        max_gap = max(max_gap, best_gap)
        if best_ordinal >= 6 and best_ordinal + 6 < market_lengths[market]:
            available_rows = available_rows + 1
            trailing_hours = (
                points[(market, best_ordinal)] - points[(market, best_ordinal - 6)]
            ) / 3600.0
            future_hours = (
                points[(market, best_ordinal + 6)] - points[(market, best_ordinal)]
            ) / 3600.0
            min_trailing_hours = min(min_trailing_hours, trailing_hours)
            max_trailing_hours = max(max_trailing_hours, trailing_hours)
            min_future_hours = min(min_future_hours, future_hours)
            max_future_hours = max(max_future_hours, future_hours)
            if (
                best_gap <= 2700.0
                and trailing_hours >= 4.5
                and trailing_hours <= 7.5
                and future_hours >= 4.5
                and future_hours <= 7.5
            ):
                legal_rows = legal_rows + 1
    blocks = blocks + [
        {
            "block": block,
            "available_rows": available_rows,
            "legal_rows": legal_rows,
            "min_gap_seconds": min_gap,
            "max_gap_seconds": max_gap,
            "min_trailing_hours": min_trailing_hours,
            "max_trailing_hours": max_trailing_hours,
            "min_future_hours": min_future_hours,
            "max_future_hours": max_future_hours,
        }
    ]

result = structured_return(
    "XTracker and event-price alignment diagnostic.",
    {
        "event_market_count": market_count,
        "price_market_count": len(market_lengths),
        "post_count": len(post_events),
        "post_event_match_count": sum(1 for item in post_events if item == event_id),
        "post_value_sum": sum(post_values),
        "temporal_inversion_count": sum(
            1
            for reference_time, available_at in zip(
                post_reference_times, post_available_times
            )
            if reference_time > available_at
        ),
        "blocks": blocks,
        "protected_values_exposed": False,
    },
)
