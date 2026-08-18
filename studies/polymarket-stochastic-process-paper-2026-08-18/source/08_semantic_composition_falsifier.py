markets = read("polymarket-development-prices", "market_id")
events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")

outcome_markets = read("polymarket-development-outcomes", "market_id")
outcome_events = read("polymarket-development-outcomes", "event_chronological_ordinal")
questions = read("polymarket-development-outcomes", "question")
close_times = read("polymarket-development-outcomes", "close_time_epoch_seconds")
payouts = read("polymarket-development-outcomes", "resolution_payout")

category_names = [
    "speech_or_social_post",
    "election_or_candidate_selection",
    "armed_conflict_or_geopolitical_action",
    "office_legal_or_institutional_action",
    "other",
]
speech_tokens = [
    " say ",
    " say \"",
    "Say ",
    "post ",
    " post",
    "tweet",
    "Tweet",
    "headlines",
    "insult",
    "praise",
    "talk to",
    "speak to",
    "Truth Social",
]
election_tokens = [
    "Election",
    "election",
    "nominee",
    "Nominee",
    "primary",
    "Primary",
    "candidate",
    "valid first preference votes",
    "advance to the general election",
]
conflict_tokens = [
    "Russia",
    "Ukraine",
    "Iran",
    "Israel",
    "Israeli",
    "Hamas",
    "Lebanon",
    "NATO",
    "Strait",
    "Hormuz",
    "capture",
    "enter ",
    "strike",
    "Ceasefire",
    "ceasefire",
    "nuclear",
    "uranium",
    "airspace",
    "blockade",
]
institution_tokens = [
    " out ",
    "out as",
    "out by",
    "resign",
    "leave ",
    "arrest",
    "charged",
    "pardon",
    "sanction",
    "appointed",
    "dissolved",
    "released",
    "extradited",
    "SCOTUS",
    "court",
    "fire ",
    "Act invoked",
    "signs ",
    "declassifies",
    "charges dropped",
]


def contains_any(question, tokens):
    for token in tokens:
        if token in question:
            return True
    return False


def category_index(question):
    if contains_any(question, speech_tokens):
        return 0
    if contains_any(question, election_tokens):
        return 1
    if contains_any(question, conflict_tokens):
        return 2
    if contains_any(question, institution_tokens):
        return 3
    return 4


def safe_rate(numerator, denominator):
    if denominator == 0:
        return None
    return numerator / denominator


category_by_market = {}
event_by_market = {}
close_by_market = {}
payout_by_market = {}
market_count = [0, 0, 0, 0, 0]
event_market_count = {}
for row in range(len(outcome_markets)):
    market = outcome_markets[row]
    event = outcome_events[row]
    category = category_index(questions[row])
    category_by_market[market] = category
    event_by_market[market] = event
    close_by_market[market] = close_times[row]
    payout_by_market[market] = payouts[row]
    market_count[category] = market_count[category] + 1
    if event not in event_market_count:
        event_market_count[event] = 0
    event_market_count[event] = event_market_count[event] + 1

maximum_event = max(outcome_events)
represented_event = [[0 for unused in range(maximum_event + 1)] for category in range(5)]
linked_market_count = [0, 0, 0, 0, 0]
for row in range(len(outcome_markets)):
    market = outcome_markets[row]
    event = outcome_events[row]
    category = category_by_market[market]
    represented_event[category][event] = 1
    if event_market_count[event] > 1:
        linked_market_count[category] = linked_market_count[category] + 1

regular_count = [0, 0, 0, 0, 0]
regular_sum = [0.0, 0.0, 0.0, 0.0, 0.0]
regular_squared = [0.0, 0.0, 0.0, 0.0, 0.0]
interior_count = [0, 0, 0, 0, 0]
interior_zero = [0, 0, 0, 0, 0]
quiet_zero_count = [0, 0, 0, 0, 0]
quiet_zero_move = [0, 0, 0, 0, 0]
quiet_24_count = [0, 0, 0, 0, 0]
quiet_24_move = [0, 0, 0, 0, 0]
horizon_24_count = [0, 0, 0, 0, 0]
horizon_24_sum = [0.0, 0.0, 0.0, 0.0, 0.0]
horizon_24_squared = [0.0, 0.0, 0.0, 0.0, 0.0]
event_regular_count = [
    [0 for unused in range(maximum_event + 1)] for category in range(5)
]
event_regular_sum = [
    [0.0 for unused in range(maximum_event + 1)] for category in range(5)
]

horizon_hours = [24.0, 72.0, 168.0, 336.0]
horizon_tolerances = [12.0, 12.0, 24.0, 24.0]
best_distance_by_market = {}
best_probability_by_market = {}
for market in outcome_markets:
    best_distance_by_market[market] = [None, None, None, None]
    best_probability_by_market[market] = [None, None, None, None]

order_break_count = 0
current_market = None
previous_ordinal = None
previous_time = None
previous_probability = None
quiet_run = 0
history_times = []
history_probabilities = []

for row in range(len(probabilities)):
    market = markets[row]
    event = events[row]
    ordinal = ordinals[row]
    observed_time = times[row]
    probability = probabilities[row]
    category = category_by_market[market]
    if market != current_market:
        current_market = market
        previous_ordinal = None
        previous_time = None
        previous_probability = None
        quiet_run = 0
        history_times = []
        history_probabilities = []
        if ordinal != 0:
            order_break_count = order_break_count + 1
    elif ordinal != previous_ordinal + 1 or observed_time <= previous_time:
        order_break_count = order_break_count + 1
    if previous_time is not None and ordinal == previous_ordinal + 1:
        gap_hours = (observed_time - previous_time) / 3600.0
        if gap_hours >= 0.75 and gap_hours <= 1.25:
            change = probability - previous_probability
            regular_count[category] = regular_count[category] + 1
            regular_sum[category] = regular_sum[category] + change
            regular_squared[category] = regular_squared[category] + change * change
            event_regular_count[category][event] = event_regular_count[category][event] + 1
            event_regular_sum[category][event] = event_regular_sum[category][event] + change
            if previous_probability > 0.02 and previous_probability < 0.98:
                interior_count[category] = interior_count[category] + 1
                if change == 0.0:
                    interior_zero[category] = interior_zero[category] + 1
            if quiet_run == 0:
                quiet_zero_count[category] = quiet_zero_count[category] + 1
                if change != 0.0:
                    quiet_zero_move[category] = quiet_zero_move[category] + 1
            if quiet_run >= 24:
                quiet_24_count[category] = quiet_24_count[category] + 1
                if change != 0.0:
                    quiet_24_move[category] = quiet_24_move[category] + 1
            if change == 0.0:
                quiet_run = quiet_run + 1
            else:
                quiet_run = 0
    history_times = history_times + [observed_time]
    history_probabilities = history_probabilities + [probability]
    if len(history_times) > 25:
        history_times = history_times[1:]
        history_probabilities = history_probabilities[1:]
    if len(history_times) == 25:
        elapsed_hours = (history_times[-1] - history_times[0]) / 3600.0
        if elapsed_hours >= 18.0 and elapsed_hours <= 30.0:
            horizon_change = history_probabilities[-1] - history_probabilities[0]
            horizon_24_count[category] = horizon_24_count[category] + 1
            horizon_24_sum[category] = horizon_24_sum[category] + horizon_change
            horizon_24_squared[category] = (
                horizon_24_squared[category] + horizon_change * horizon_change
            )
    hours_to_close = (close_by_market[market] - observed_time) / 3600.0
    if hours_to_close >= 0.0:
        for horizon in range(4):
            distance = abs(hours_to_close - horizon_hours[horizon])
            best_distance = best_distance_by_market[market][horizon]
            if distance <= horizon_tolerances[horizon] and (
                best_distance is None or distance < best_distance
            ):
                best_distance_by_market[market][horizon] = distance
                best_probability_by_market[market][horizon] = probability
    previous_ordinal = ordinal
    previous_time = observed_time
    previous_probability = probability

calibration_count = [[0, 0, 0, 0] for category in range(5)]
calibration_probability = [[0.0, 0.0, 0.0, 0.0] for category in range(5)]
calibration_outcome = [[0.0, 0.0, 0.0, 0.0] for category in range(5)]
calibration_event_count = [
    [[0 for unused in range(maximum_event + 1)] for horizon in range(4)]
    for category in range(5)
]
calibration_event_probability = [
    [[0.0 for unused in range(maximum_event + 1)] for horizon in range(4)]
    for category in range(5)
]
calibration_event_outcome = [
    [[0.0 for unused in range(maximum_event + 1)] for horizon in range(4)]
    for category in range(5)
]

for market in outcome_markets:
    category = category_by_market[market]
    event = event_by_market[market]
    payout = payout_by_market[market]
    for horizon in range(4):
        probability = best_probability_by_market[market][horizon]
        if probability is not None:
            calibration_count[category][horizon] = calibration_count[category][horizon] + 1
            calibration_probability[category][horizon] = (
                calibration_probability[category][horizon] + probability
            )
            calibration_outcome[category][horizon] = (
                calibration_outcome[category][horizon] + payout
            )
            calibration_event_count[category][horizon][event] = (
                calibration_event_count[category][horizon][event] + 1
            )
            calibration_event_probability[category][horizon][event] = (
                calibration_event_probability[category][horizon][event] + probability
            )
            calibration_event_outcome[category][horizon][event] = (
                calibration_event_outcome[category][horizon][event] + payout
            )

category_rows = []
for category in range(5):
    regular_mean = safe_rate(regular_sum[category], regular_count[category])
    regular_variance = None
    if regular_mean is not None:
        regular_variance = (
            regular_squared[category] / regular_count[category] - regular_mean * regular_mean
        )
    horizon_mean = safe_rate(horizon_24_sum[category], horizon_24_count[category])
    horizon_variance = None
    if horizon_mean is not None:
        horizon_variance = (
            horizon_24_squared[category] / horizon_24_count[category]
            - horizon_mean * horizon_mean
        )
    variance_ratio_24 = None
    if regular_variance is not None and regular_variance > 0.0 and horizon_variance is not None:
        variance_ratio_24 = horizon_variance / (24.0 * regular_variance)
    event_drift_values = []
    represented_event_count = 0
    for event in range(maximum_event + 1):
        if represented_event[category][event] == 1:
            represented_event_count = represented_event_count + 1
        if event_regular_count[category][event] > 0:
            event_drift_values = event_drift_values + [
                event_regular_sum[category][event] / event_regular_count[category][event]
            ]
    calibration_rows = []
    for horizon in range(4):
        count = calibration_count[category][horizon]
        event_differences = []
        for event in range(maximum_event + 1):
            event_count = calibration_event_count[category][horizon][event]
            if event_count > 0:
                event_differences = event_differences + [
                    (
                        calibration_event_probability[category][horizon][event]
                        - calibration_event_outcome[category][horizon][event]
                    )
                    / event_count
                ]
        calibration_rows = calibration_rows + [
            {
                "hours_before_close": horizon_hours[horizon],
                "market_count": count,
                "event_count": len(event_differences),
                "market_probability_minus_outcome": safe_rate(
                    calibration_probability[category][horizon]
                    - calibration_outcome[category][horizon],
                    count,
                ),
                "event_macro_probability_minus_outcome": safe_rate(
                    sum(event_differences), len(event_differences)
                ),
            }
        ]
    category_rows = category_rows + [
        {
            "category": category_names[category],
            "market_count": market_count[category],
            "event_count": represented_event_count,
            "linked_surface_market_count": linked_market_count[category],
            "regular_increment_count": regular_count[category],
            "regular_interior_zero_rate": safe_rate(
                interior_zero[category], interior_count[category]
            ),
            "quiet_0_next_move_rate": safe_rate(
                quiet_zero_move[category], quiet_zero_count[category]
            ),
            "quiet_24_plus_next_move_rate": safe_rate(
                quiet_24_move[category], quiet_24_count[category]
            ),
            "variance_ratio_24h": variance_ratio_24,
            "event_equal_regular_drift": safe_rate(
                sum(event_drift_values), len(event_drift_values)
            ),
            "positive_drift_event_count": sum(
                1 for value in event_drift_values if value > 0.0
            ),
            "drift_event_count": len(event_drift_values),
            "fixed_horizon_calibration": calibration_rows,
        }
    ]

result = structured_return(
    "Predeclared semantic-composition falsifier for process and calibration signatures.",
    {
        "schema_version": "polymarket-semantic-composition-falsifier/v1",
        "category_precedence": category_names,
        "category_rows": category_rows,
        "coverage_checks": {"order_break_count": order_break_count},
    },
    warnings=[
        "Categories are deterministic question-text heuristics fixed after identity-only inventory.",
        "A category is a stability diagnostic, not a claim of complete economic semantics.",
        "Related markets remain dependent even when event-macro summaries are reported.",
        "Sparse category-horizon cells remain visible and are not merged after inspection.",
        "Sampled probabilities are not trades, quotes, latent beliefs, or executable returns.",
        "Ancestor and final protected events remain unavailable.",
    ],
)
