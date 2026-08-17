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

folds = [[0, 12, 16], [0, 16, 20], [0, 20, 24]]
fold_results = []
total_count = 0
total_baseline = 0.0
total_scalar = 0.0
total_affine = 0.0
macro_baseline = 0.0
macro_scalar = 0.0
macro_affine = 0.0
macro_event_count = 0
for fold in folds:
    train_events = event_order[fold[0]:fold[1]]
    test_events = event_order[fold[1]:fold[2]]
    train_probability = []
    train_outcome = []
    for index in range(len(sample_probability)):
        if sample_event[index] in train_events:
            train_probability = train_probability + [sample_probability[index]]
            train_outcome = train_outcome + [sample_outcome[index]]
    scalar_numerator = 0.0
    scalar_denominator = 0.0
    mean_probability = sum(train_probability) / len(train_probability)
    mean_outcome = sum(train_outcome) / len(train_outcome)
    affine_cross = 0.0
    affine_square = 0.0
    for index in range(len(train_probability)):
        probability = train_probability[index]
        outcome = train_outcome[index]
        scalar_numerator = scalar_numerator + probability * outcome
        scalar_denominator = scalar_denominator + probability * probability
        affine_cross = affine_cross + (probability - mean_probability) * (outcome - mean_outcome)
        affine_square = affine_square + (probability - mean_probability) * (probability - mean_probability)
    scalar = max(0.0, min(1.5, scalar_numerator / scalar_denominator))
    slope = affine_cross / affine_square
    intercept = mean_outcome - slope * mean_probability
    fold_count = 0
    fold_baseline = 0.0
    fold_scalar = 0.0
    fold_affine = 0.0
    event_baseline = {}
    event_scalar = {}
    event_affine = {}
    event_count = {}
    for index in range(len(sample_probability)):
        event = sample_event[index]
        if event in test_events:
            probability = sample_probability[index]
            outcome = sample_outcome[index]
            scalar_prediction = max(0.0, min(1.0, scalar * probability))
            affine_prediction = max(0.0, min(1.0, intercept + slope * probability))
            baseline_error = (outcome - probability) * (outcome - probability)
            scalar_error = (outcome - scalar_prediction) * (outcome - scalar_prediction)
            affine_error = (outcome - affine_prediction) * (outcome - affine_prediction)
            fold_count = fold_count + 1
            fold_baseline = fold_baseline + baseline_error
            fold_scalar = fold_scalar + scalar_error
            fold_affine = fold_affine + affine_error
            if event not in event_count:
                event_count[event] = 0
                event_baseline[event] = 0.0
                event_scalar[event] = 0.0
                event_affine[event] = 0.0
            event_count[event] = event_count[event] + 1
            event_baseline[event] = event_baseline[event] + baseline_error
            event_scalar[event] = event_scalar[event] + scalar_error
            event_affine[event] = event_affine[event] + affine_error
    fold_macro_baseline = 0.0
    fold_macro_scalar = 0.0
    fold_macro_affine = 0.0
    for event in event_count:
        fold_macro_baseline = fold_macro_baseline + event_baseline[event] / event_count[event]
        fold_macro_scalar = fold_macro_scalar + event_scalar[event] / event_count[event]
        fold_macro_affine = fold_macro_affine + event_affine[event] / event_count[event]
    fold_macro_baseline = fold_macro_baseline / len(event_count)
    fold_macro_scalar = fold_macro_scalar / len(event_count)
    fold_macro_affine = fold_macro_affine / len(event_count)
    total_count = total_count + fold_count
    total_baseline = total_baseline + fold_baseline
    total_scalar = total_scalar + fold_scalar
    total_affine = total_affine + fold_affine
    macro_baseline = macro_baseline + fold_macro_baseline * len(event_count)
    macro_scalar = macro_scalar + fold_macro_scalar * len(event_count)
    macro_affine = macro_affine + fold_macro_affine * len(event_count)
    macro_event_count = macro_event_count + len(event_count)
    fold_results = fold_results + [{
        "train_event_count": len(train_events),
        "test_event_count": len(test_events),
        "test_market_count": fold_count,
        "scalar": scalar,
        "affine_intercept": intercept,
        "affine_slope": slope,
        "market_probability_brier": fold_baseline / fold_count,
        "scalar_calibration_brier": fold_scalar / fold_count,
        "affine_calibration_brier": fold_affine / fold_count,
        "event_macro_market_probability_brier": fold_macro_baseline,
        "event_macro_scalar_brier": fold_macro_scalar,
        "event_macro_affine_brier": fold_macro_affine,
    }]

result = structured_return(
    "Expanding whole-event walk-forward calibration at the fixed 24th sample.",
    {
        "folds": fold_results,
        "aggregate_test_market_count": total_count,
        "aggregate_market_probability_brier": total_baseline / total_count,
        "aggregate_scalar_calibration_brier": total_scalar / total_count,
        "aggregate_affine_calibration_brier": total_affine / total_count,
        "aggregate_event_macro_market_probability_brier": macro_baseline / macro_event_count,
        "aggregate_event_macro_scalar_brier": macro_scalar / macro_event_count,
        "aggregate_event_macro_affine_brier": macro_affine / macro_event_count,
    },
    warnings=[
        "Only development events are used; the final chronological event block remains unexposed.",
        "Three expanding folds are a small stability sample and do not establish generality.",
        "Calibration parameters are re-fit inside each fold and predictions are clipped to [0, 1].",
    ],
)
