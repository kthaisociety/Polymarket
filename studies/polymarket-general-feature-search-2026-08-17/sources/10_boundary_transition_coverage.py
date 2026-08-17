price_markets = read("polymarket-development-prices", "market_id")
price_events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")


def boundary_state(probability):
    if probability <= 0.02 or probability >= 0.98:
        return 1
    return 0


def transition_side(current_probability, future_probability, transition):
    if transition == "entry":
        if future_probability <= 0.02:
            return "lower"
        if future_probability >= 0.98:
            return "upper"
    if current_probability <= 0.02:
        return "lower"
    return "upper"


points = {}
market_lengths = {}
market_events = {}
market_order = []
for row in range(len(price_markets)):
    market = price_markets[row]
    if market not in market_lengths:
        market_order = market_order + [market]
        market_lengths[market] = 0
        market_events[market] = price_events[row]
    points[(market, ordinals[row])] = [times[row], probabilities[row]]
    market_lengths[market] = market_lengths[market] + 1

definitions = [
    ["entry_24h", "entry", 24, 18.0, 30.0],
    ["escape_24h", "escape", 24, 18.0, 30.0],
    ["entry_6h", "entry", 6, 4.5, 7.5],
    ["escape_6h", "escape", 6, 4.5, 7.5],
]
event_stats = {}
irregular_by_horizon = {6: 0, 24: 0}
legal_decisions_by_horizon = {6: 0, 24: 0}

for market in market_order:
    length = market_lengths[market]
    event = market_events[market]
    for definition in definitions:
        name = definition[0]
        transition = definition[1]
        horizon = definition[2]
        minimum_hours = definition[3]
        maximum_hours = definition[4]
        for decision in range(24, length - horizon, 6):
            current = points[(market, decision)]
            trailing = points[(market, decision - 24)]
            future = points[(market, decision + horizon)]
            trailing_hours = (current[0] - trailing[0]) / 3600.0
            future_hours = (future[0] - current[0]) / 3600.0
            regular = True
            if trailing_hours < 18.0 or trailing_hours > 30.0:
                regular = False
            if future_hours < minimum_hours or future_hours > maximum_hours:
                regular = False
            if not regular:
                if transition == "entry":
                    irregular_by_horizon[horizon] = irregular_by_horizon[horizon] + 1
            else:
                if transition == "entry":
                    legal_decisions_by_horizon[horizon] = legal_decisions_by_horizon[horizon] + 1
                current_state = boundary_state(current[1])
                future_state = boundary_state(future[1])
                include = False
                label = 0
                if transition == "entry" and current_state == 0:
                    include = True
                    label = future_state
                if transition == "escape" and current_state == 1:
                    include = True
                    label = 1 - future_state
                if include:
                    key = (name, event)
                    if key not in event_stats:
                        event_stats[key] = [0, 0, 0, 0]
                    stats = event_stats[key]
                    stats[0] = stats[0] + 1
                    stats[1] = stats[1] + label
                    if label == 1:
                        side = transition_side(current[1], future[1], transition)
                        if side == "lower":
                            stats[2] = stats[2] + 1
                        else:
                            stats[3] = stats[3] + 1

results = []
eligible_names = []
for definition in definitions:
    name = definition[0]
    all_count = 0
    all_positive = 0
    oof_count = 0
    oof_positive = 0
    lower_positive = 0
    upper_positive = 0
    oof_event_count = 0
    positive_events = 0
    negative_events = 0
    both_class_events = 0
    event_rows = []
    for event in range(24):
        key = (name, event)
        if key in event_stats:
            stats = event_stats[key]
            all_count = all_count + stats[0]
            all_positive = all_positive + stats[1]
            if event >= 8:
                oof_event_count = oof_event_count + 1
                oof_count = oof_count + stats[0]
                oof_positive = oof_positive + stats[1]
                lower_positive = lower_positive + stats[2]
                upper_positive = upper_positive + stats[3]
                if stats[1] > 0:
                    positive_events = positive_events + 1
                if stats[0] - stats[1] > 0:
                    negative_events = negative_events + 1
                if stats[1] > 0 and stats[0] - stats[1] > 0:
                    both_class_events = both_class_events + 1
                event_rows = event_rows + [{
                    "event": event,
                    "count": stats[0],
                    "positive": stats[1],
                    "rate": stats[1] / stats[0],
                }]
    oof_negative = oof_count - oof_positive
    eligible = (
        oof_count >= 400
        and oof_positive >= 40
        and oof_negative >= 40
        and both_class_events >= 8
    )
    if eligible and len(eligible_names) < 2:
        eligible_names = eligible_names + [name]
    results = results + [{
        "label": name,
        "all_development_count": all_count,
        "all_development_positive": all_positive,
        "all_development_rate": all_positive / all_count,
        "oof_count": oof_count,
        "oof_positive": oof_positive,
        "oof_negative": oof_negative,
        "oof_rate": oof_positive / oof_count,
        "oof_event_count": oof_event_count,
        "positive_events": positive_events,
        "negative_events": negative_events,
        "both_class_events": both_class_events,
        "lower_positive": lower_positive,
        "upper_positive": upper_positive,
        "model_eligible": eligible,
        "event_rows": event_rows,
    }]

result = structured_return(
    "Fixed boundary-entry and boundary-escape label coverage at six- and 24-hour horizons.",
    {
        "boundary_threshold": 0.02,
        "decision_stride_observations": 6,
        "history_warmup_observations": 24,
        "definitions_in_priority_order": [definition[0] for definition in definitions],
        "eligibility": {
            "minimum_oof_rows": 400,
            "minimum_oof_positives": 40,
            "minimum_oof_negatives": 40,
            "minimum_both_class_events": 8,
            "maximum_selected_labels": 2,
        },
        "selected_eligible_labels": eligible_names,
        "legal_decisions_by_horizon": legal_decisions_by_horizon,
        "irregular_by_horizon": irregular_by_horizon,
        "results": results,
    },
    warnings=[
        "This is a pre-model coverage diagnostic and cannot establish predictability.",
        "Entry and escape are conditional hazards with different at-risk populations.",
        "Overlapping horizons are counted for coverage and are not represented as independent evidence.",
        "The fixed priority and coverage gates were declared before label rates were observed.",
        "Sampled probabilities are not executable quotes and protected values remain unavailable.",
    ],
)
