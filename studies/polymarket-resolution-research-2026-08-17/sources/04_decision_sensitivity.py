markets = read("polymarket-development-prices", "market_id")
events = read("polymarket-development-prices", "event_id")
ordinals = read("polymarket-development-prices", "observation_ordinal")
probabilities = read("polymarket-development-prices", "market_probability")
outcome_markets = read("polymarket-development-outcomes", "market_id")
outcomes = read("polymarket-development-outcomes", "resolution_payout")

labels = {}
for index in range(len(outcome_markets)):
    labels[outcome_markets[index]] = outcomes[index]

checkpoints = [11, 23, 47, 95]
results = []
for checkpoint in checkpoints:
    count = 0
    loss = 0.0
    outcome_sum = 0.0
    probability_sum = 0.0
    event_set = set()
    for index in range(len(markets)):
        if ordinals[index] == checkpoint:
            outcome = labels[markets[index]]
            probability = probabilities[index]
            error = outcome - probability
            count = count + 1
            loss = loss + error * error
            outcome_sum = outcome_sum + outcome
            probability_sum = probability_sum + probability
            event_set = event_set | set([events[index]])
    if count > 0:
        results = results + [{
            "decision_ordinal": checkpoint,
            "market_count": count,
            "event_count": len(event_set),
            "market_probability_brier": loss / count,
            "mean_probability": probability_sum / count,
            "outcome_rate": outcome_sum / count,
        }]

result = structured_return(
    "Current-price calibration sensitivity across fixed observation ordinals.",
    {"checkpoints": results},
    warnings=[
        "Later ordinals condition on longer retained coverage and can change the market population.",
        "Observation ordinal is reproducible but does not imply a fixed economic horizon.",
    ],
)
