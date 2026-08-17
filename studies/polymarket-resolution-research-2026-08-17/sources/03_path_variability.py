markets = read("polymarket-development-prices", "market_id")
events = read("polymarket-development-prices", "event_id")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")
outcome_markets = read("polymarket-development-outcomes", "market_id")
outcomes = read("polymarket-development-outcomes", "resolution_payout")

labels = {}
paths = {}
path_times = {}
event_by_market = {}
for index in range(len(outcome_markets)):
    labels[outcome_markets[index]] = outcomes[index]
for index in range(len(markets)):
    market = markets[index]
    if market not in paths:
        paths[market] = []
        path_times[market] = []
        event_by_market[market] = events[index]
    paths[market] = paths[market] + [probabilities[index]]
    path_times[market] = path_times[market] + [times[index]]

current = []
variability = []
mean_gap_hours = []
square_error = []
event_at_decision = []
for market in paths:
    path = paths[market]
    observed = path_times[market]
    if len(path) > 23:
        level = path[23]
        mean = sum(path[12:24]) / 12
        variance = 0.0
        gap = 0.0
        for index in range(12, 24):
            variance = variance + (path[index] - mean) * (path[index] - mean)
            if index > 12:
                gap = gap + (observed[index] - observed[index - 1]) / 3600
        error = labels[market] - level
        current = current + [level]
        variability = variability + [variance / 12]
        mean_gap_hours = mean_gap_hours + [gap / 11]
        square_error = square_error + [error * error]
        event_at_decision = event_at_decision + [event_by_market[market]]

mean_variability = sum(variability) / len(variability)
mean_gap = sum(mean_gap_hours) / len(mean_gap_hours)
mean_error = sum(square_error) / len(square_error)
variability_cross = 0.0
variability_square = 0.0
gap_cross = 0.0
gap_square = 0.0
for index in range(len(current)):
    centered_error = square_error[index] - mean_error
    centered_variability = variability[index] - mean_variability
    centered_gap = mean_gap_hours[index] - mean_gap
    variability_cross = variability_cross + centered_variability * centered_error
    variability_square = variability_square + centered_variability * centered_variability
    gap_cross = gap_cross + centered_gap * centered_error
    gap_square = gap_square + centered_gap * centered_gap

result = structured_return(
    "Recent path variability and sampling-gap diagnostics for probability error.",
    {
        "market_count": len(current),
        "event_count": len(set(event_at_decision)),
        "market_probability_brier": mean_error,
        "mean_recent_variance": mean_variability,
        "mean_sampling_gap_hours": mean_gap,
        "squared_error_slope_per_variance": variability_cross / variability_square,
        "squared_error_slope_per_gap_hour": gap_cross / gap_square,
    },
    warnings=[
        "Variance and gap associations diagnose forecast reliability, not outcome direction.",
        "A few large gaps can dominate an unstandardized slope and require stability checks.",
    ],
)
