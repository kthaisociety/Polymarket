markets = read("polymarket-development-prices", "market_id")
events = read("polymarket-development-prices", "event_id")
ordinals = read("polymarket-development-prices", "observation_ordinal")
probabilities = read("polymarket-development-prices", "market_probability")
outcome_markets = read("polymarket-development-outcomes", "market_id")
outcomes = read("polymarket-development-outcomes", "resolution_payout")

labels = {}
paths = {}
event_by_market = {}
for index in range(len(outcome_markets)):
    labels[outcome_markets[index]] = outcomes[index]
for index in range(len(markets)):
    market = markets[index]
    if market not in paths:
        paths[market] = []
        event_by_market[market] = events[index]
    paths[market] = paths[market] + [probabilities[index]]

current = []
momentum = []
labels_at_decision = []
event_at_decision = []
for market in paths:
    path = paths[market]
    if len(path) > 23:
        current = current + [path[23]]
        momentum = momentum + [path[23] - path[11]]
        labels_at_decision = labels_at_decision + [labels[market]]
        event_at_decision = event_at_decision + [event_by_market[market]]

raw_cross = 0.0
raw_momentum_square = 0.0
controlled_cross = 0.0
controlled_momentum_square = 0.0
baseline_loss = 0.0
bin_momentum_sum = [0.0, 0.0, 0.0, 0.0, 0.0]
bin_residual_sum = [0.0, 0.0, 0.0, 0.0, 0.0]
bin_count = [0, 0, 0, 0, 0]
for index in range(len(current)):
    residual = labels_at_decision[index] - current[index]
    raw_cross = raw_cross + momentum[index] * residual
    raw_momentum_square = raw_momentum_square + momentum[index] * momentum[index]
    baseline_loss = baseline_loss + residual * residual
    bucket = min(4, int(current[index] * 5))
    bin_momentum_sum[bucket] = bin_momentum_sum[bucket] + momentum[index]
    bin_residual_sum[bucket] = bin_residual_sum[bucket] + residual
    bin_count[bucket] = bin_count[bucket] + 1
for index in range(len(current)):
    bucket = min(4, int(current[index] * 5))
    centered_momentum = momentum[index] - bin_momentum_sum[bucket] / bin_count[bucket]
    residual = labels_at_decision[index] - current[index]
    centered_residual = residual - bin_residual_sum[bucket] / bin_count[bucket]
    controlled_cross = controlled_cross + centered_momentum * centered_residual
    controlled_momentum_square = controlled_momentum_square + centered_momentum * centered_momentum

alphas = [-1.0, -0.5, 0.5, 1.0]
candidate_losses = []
for alpha in alphas:
    loss = 0.0
    for index in range(len(current)):
        prediction = current[index] + alpha * momentum[index]
        prediction = max(0.0, min(1.0, prediction))
        error = labels_at_decision[index] - prediction
        loss = loss + error * error
    candidate_losses = candidate_losses + [{
        "alpha": alpha,
        "brier": loss / len(current),
        "delta_vs_price": loss / len(current) - baseline_loss / len(current),
    }]

result = structured_return(
    "Twelve-sample momentum tested against current price and within-price-bin controls.",
    {
        "market_count": len(current),
        "event_count": len(set(event_at_decision)),
        "market_probability_brier": baseline_loss / len(current),
        "raw_residual_slope_per_momentum": raw_cross / raw_momentum_square,
        "within_price_bin_residual_slope": controlled_cross / controlled_momentum_square,
        "fixed_alpha_candidates": candidate_losses,
    },
    warnings=[
        "Within-bin control is a coarse development diagnostic, not a causal estimate.",
        "Fixed alpha variants are exploratory trials and cannot be selected on protected data.",
    ],
)
