price_markets = read("polymarket-development-prices", "market_id")
price_events = read("polymarket-development-prices", "event_id")
ordinals = read("polymarket-development-prices", "observation_ordinal")
probabilities = read("polymarket-development-prices", "market_probability")
outcome_markets = read("polymarket-development-outcomes", "market_id")
outcomes = read("polymarket-development-outcomes", "resolution_payout")

labels = {}
for index in range(len(outcome_markets)):
    labels[outcome_markets[index]] = outcomes[index]

decision_probability = []
decision_outcome = []
decision_event = []
for index in range(len(price_markets)):
    if ordinals[index] == 23:
        decision_probability = decision_probability + [probabilities[index]]
        decision_outcome = decision_outcome + [labels[price_markets[index]]]
        decision_event = decision_event + [price_events[index]]

baseline_loss = 0.0
constant_loss = 0.0
prevalence = sum(decision_outcome) / len(decision_outcome)
bin_counts = [0, 0, 0, 0, 0]
bin_probability = [0.0, 0.0, 0.0, 0.0, 0.0]
bin_outcome = [0.0, 0.0, 0.0, 0.0, 0.0]
event_losses = {}
event_counts = {}
for index in range(len(decision_probability)):
    probability = decision_probability[index]
    outcome = decision_outcome[index]
    error = (outcome - probability) * (outcome - probability)
    baseline_loss = baseline_loss + error
    constant_loss = constant_loss + (outcome - prevalence) * (outcome - prevalence)
    bucket = min(4, int(probability * 5))
    bin_counts[bucket] = bin_counts[bucket] + 1
    bin_probability[bucket] = bin_probability[bucket] + probability
    bin_outcome[bucket] = bin_outcome[bucket] + outcome
    event = decision_event[index]
    if event not in event_losses:
        event_losses[event] = 0.0
        event_counts[event] = 0
    event_losses[event] = event_losses[event] + error
    event_counts[event] = event_counts[event] + 1

calibration = []
for bucket in range(5):
    count = bin_counts[bucket]
    if count > 0:
        calibration = calibration + [{
            "lower": bucket / 5,
            "count": count,
            "mean_probability": bin_probability[bucket] / count,
            "outcome_rate": bin_outcome[bucket] / count,
        }]

event_mean_losses = []
for event in event_losses:
    event_mean_losses = event_mean_losses + [event_losses[event] / event_counts[event]]

result = structured_return(
    "Fixed 24th-sample calibration and current-price baseline.",
    {
        "decision_ordinal": 23,
        "market_count": len(decision_probability),
        "event_count": len(set(decision_event)),
        "outcome_rate": prevalence,
        "market_probability_brier": baseline_loss / len(decision_probability),
        "development_prevalence_brier": constant_loss / len(decision_probability),
        "calibration_bins": calibration,
        "event_mean_brier_min": min(event_mean_losses),
        "event_mean_brier_max": max(event_mean_losses),
    },
    warnings=[
        "Sampled probabilities are observations, not executable quotes.",
        "The development prevalence comparator is descriptive and was fit on the same sample.",
        "Corpus inclusion conditions on eventual resolution and at least 24 retained samples.",
    ],
)
