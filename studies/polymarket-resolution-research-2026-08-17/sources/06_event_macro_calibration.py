price_markets = read("polymarket-development-prices", "market_id")
price_events = read("polymarket-development-prices", "event_id")
ordinals = read("polymarket-development-prices", "observation_ordinal")
probabilities = read("polymarket-development-prices", "market_probability")
outcome_markets = read("polymarket-development-outcomes", "market_id")
outcome_events = read("polymarket-development-outcomes", "event_id")
outcomes = read("polymarket-development-outcomes", "resolution_payout")

labels = {}
event_order = []
for index in range(len(outcome_markets)):
    labels[outcome_markets[index]] = outcomes[index]
    if outcome_events[index] not in event_order:
        event_order = event_order + [outcome_events[index]]

sample_probability = []
sample_outcome = []
sample_event = []
for index in range(len(price_markets)):
    if ordinals[index] == 23:
        sample_probability = sample_probability + [probabilities[index]]
        sample_outcome = sample_outcome + [labels[price_markets[index]]]
        sample_event = sample_event + [price_events[index]]

event_results = []
macro_baseline = 0.0
macro_scalar = 0.0
market_baseline = 0.0
market_scalar = 0.0
market_count = 0
wins = 0
for test_event_index in range(8, len(event_order)):
    train_events = event_order[:test_event_index]
    test_event = event_order[test_event_index]
    numerator = 0.0
    denominator = 0.0
    for index in range(len(sample_probability)):
        if sample_event[index] in train_events:
            numerator = numerator + sample_probability[index] * sample_outcome[index]
            denominator = denominator + sample_probability[index] * sample_probability[index]
    scalar = max(0.0, min(1.5, numerator / denominator))
    baseline_loss = 0.0
    scalar_loss = 0.0
    count = 0
    for index in range(len(sample_probability)):
        if sample_event[index] == test_event:
            probability = sample_probability[index]
            outcome = sample_outcome[index]
            prediction = max(0.0, min(1.0, scalar * probability))
            baseline_loss = baseline_loss + (outcome - probability) * (outcome - probability)
            scalar_loss = scalar_loss + (outcome - prediction) * (outcome - prediction)
            count = count + 1
    event_baseline = baseline_loss / count
    event_scalar = scalar_loss / count
    macro_baseline = macro_baseline + event_baseline
    macro_scalar = macro_scalar + event_scalar
    market_baseline = market_baseline + baseline_loss
    market_scalar = market_scalar + scalar_loss
    market_count = market_count + count
    if event_scalar < event_baseline:
        wins = wins + 1
    event_results = event_results + [{
        "test_event_ordinal": test_event_index,
        "test_market_count": count,
        "scalar": scalar,
        "market_probability_brier": event_baseline,
        "scalar_calibration_brier": event_scalar,
        "delta": event_scalar - event_baseline,
    }]

event_count = len(event_results)
result = structured_return(
    "Rolling one-event-ahead scalar calibration under market and equal-event estimands.",
    {
        "test_event_count": event_count,
        "test_market_count": market_count,
        "event_wins": wins,
        "event_losses_or_ties": event_count - wins,
        "event_macro_market_probability_brier": macro_baseline / event_count,
        "event_macro_scalar_calibration_brier": macro_scalar / event_count,
        "market_weighted_market_probability_brier": market_baseline / market_count,
        "market_weighted_scalar_calibration_brier": market_scalar / market_count,
        "events": event_results,
    },
    warnings=[
        "Equal-event and market-weighted Brier answer different population questions.",
        "Each event is tested once after at least eight earlier development events.",
        "The seven final protected events remain unavailable to this program.",
    ],
)
