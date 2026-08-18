markets = read("polymarket-development-prices", "market_id")
events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")

outcome_markets = read("polymarket-development-outcomes", "market_id")
outcome_events = read("polymarket-development-outcomes", "event_chronological_ordinal")
close_times = read("polymarket-development-outcomes", "close_time_epoch_seconds")
payouts = read("polymarket-development-outcomes", "resolution_payout")


def safe_rate(numerator, denominator):
    if denominator == 0:
        return None
    return numerator / denominator


def quantile(values, fraction):
    if len(values) == 0:
        return None
    ordered = sorted(values)
    index = int((len(ordered) - 1) * fraction)
    return ordered[index]


def state_index(probability):
    if probability <= 0.02:
        return 0
    if probability < 0.20:
        return 1
    if probability <= 0.80:
        return 2
    if probability < 0.98:
        return 3
    return 4


def close_index(hours_to_close):
    if hours_to_close <= 24.0:
        return 0
    if hours_to_close <= 72.0:
        return 1
    if hours_to_close <= 168.0:
        return 2
    return 3


def probability_index(probability):
    if probability <= 0.02:
        return 0
    if probability <= 0.10:
        return 1
    if probability <= 0.30:
        return 2
    if probability < 0.70:
        return 3
    if probability < 0.90:
        return 4
    if probability < 0.98:
        return 5
    return 6


close_by_market = {}
payout_by_market = {}
event_by_market = {}
for row in range(len(outcome_markets)):
    market = outcome_markets[row]
    close_by_market[market] = close_times[row]
    payout_by_market[market] = payouts[row]
    event_by_market[market] = outcome_events[row]

event_count = max(outcome_events) + 1
horizon_hours = [24.0, 72.0, 168.0, 336.0]
horizon_tolerances = [12.0, 12.0, 24.0, 24.0]
horizon_count = [0, 0, 0, 0]
horizon_probability = [0.0, 0.0, 0.0, 0.0]
horizon_outcome = [0.0, 0.0, 0.0, 0.0]
horizon_brier = [0.0, 0.0, 0.0, 0.0]

horizon_event_count = [[0 for unused in range(event_count)] for horizon in range(4)]
horizon_event_probability = [[0.0 for unused in range(event_count)] for horizon in range(4)]
horizon_event_outcome = [[0.0 for unused in range(event_count)] for horizon in range(4)]
horizon_event_brier = [[0.0 for unused in range(event_count)] for horizon in range(4)]

reliability_count = [[0 for band in range(7)] for horizon in range(4)]
reliability_probability = [[0.0 for band in range(7)] for horizon in range(4)]
reliability_outcome = [[0.0 for band in range(7)] for horizon in range(4)]
reliability_brier = [[0.0 for band in range(7)] for horizon in range(4)]

event_market_regular_sum = [0.0 for unused in range(event_count)]
event_market_regular_count = [0 for unused in range(event_count)]
event_market_daily_sum = [0.0 for unused in range(event_count)]
event_market_daily_count = [0 for unused in range(event_count)]

state_count = [0, 0, 0, 0, 0]
state_change = [0.0, 0.0, 0.0, 0.0, 0.0]
close_count = [0, 0, 0, 0]
close_change = [0.0, 0.0, 0.0, 0.0]
payout_increment_count = [0, 0]
payout_increment_sum = [0.0, 0.0]

observation_regular_count = 0
observation_regular_sum = 0.0
market_regular_means = []
market_daily_means = []
market_endpoint_changes = [[], []]
market_endpoint_per_hour = [[], []]
order_break_count = 0

current_market = None
current_event = None
current_payout = None
previous_ordinal = None
previous_time = None
previous_probability = None
first_time = None
first_probability = None
last_time = None
last_probability = None
market_regular_sum = 0.0
market_regular_count = 0
market_daily_sum = 0.0
market_daily_count = 0
history_times = []
history_probabilities = []
best_horizon_distance = [None, None, None, None]
best_horizon_probability = [None, None, None, None]


def retain_market():
    retained = {
        "event": current_event,
        "payout": current_payout,
        "regular_mean": safe_rate(market_regular_sum, market_regular_count),
        "daily_mean": safe_rate(market_daily_sum, market_daily_count),
        "endpoint_change": last_probability - first_probability,
        "endpoint_per_hour": safe_rate(
            last_probability - first_probability, (last_time - first_time) / 3600.0
        ),
        "horizon_probabilities": best_horizon_probability,
    }
    return retained


retained_markets = []

for row in range(len(probabilities)):
    market = markets[row]
    event = events[row]
    ordinal = ordinals[row]
    observed_time = times[row]
    probability = probabilities[row]
    if market != current_market:
        if current_market is not None:
            retained_markets = retained_markets + [retain_market()]
        current_market = market
        current_event = event
        current_payout = int(payout_by_market[market])
        previous_ordinal = None
        previous_time = None
        previous_probability = None
        first_time = observed_time
        first_probability = probability
        last_time = observed_time
        last_probability = probability
        market_regular_sum = 0.0
        market_regular_count = 0
        market_daily_sum = 0.0
        market_daily_count = 0
        history_times = []
        history_probabilities = []
        best_horizon_distance = [None, None, None, None]
        best_horizon_probability = [None, None, None, None]
        if ordinal != 0:
            order_break_count = order_break_count + 1
    elif ordinal != previous_ordinal + 1 or observed_time <= previous_time:
        order_break_count = order_break_count + 1
    if previous_time is not None and ordinal == previous_ordinal + 1:
        gap_hours = (observed_time - previous_time) / 3600.0
        if gap_hours >= 0.75 and gap_hours <= 1.25:
            change = probability - previous_probability
            observation_regular_count = observation_regular_count + 1
            observation_regular_sum = observation_regular_sum + change
            market_regular_count = market_regular_count + 1
            market_regular_sum = market_regular_sum + change
            payout_increment_count[current_payout] = payout_increment_count[current_payout] + 1
            payout_increment_sum[current_payout] = payout_increment_sum[current_payout] + change
            state = state_index(previous_probability)
            state_count[state] = state_count[state] + 1
            state_change[state] = state_change[state] + change
            hours_to_close = (close_by_market[market] - previous_time) / 3600.0
            if hours_to_close >= 0.0:
                close_band = close_index(hours_to_close)
                close_count[close_band] = close_count[close_band] + 1
                close_change[close_band] = close_change[close_band] + change
    history_times = history_times + [observed_time]
    history_probabilities = history_probabilities + [probability]
    if len(history_times) > 25:
        history_times = history_times[1:]
        history_probabilities = history_probabilities[1:]
    if ordinal > 0 and ordinal % 24 == 0 and len(history_times) == 25:
        elapsed_hours = (history_times[-1] - history_times[0]) / 3600.0
        if elapsed_hours >= 18.0 and elapsed_hours <= 30.0:
            daily_change = history_probabilities[-1] - history_probabilities[0]
            market_daily_count = market_daily_count + 1
            market_daily_sum = market_daily_sum + daily_change
    hours_to_close = (close_by_market[market] - observed_time) / 3600.0
    if hours_to_close >= 0.0:
        for horizon in range(4):
            distance = abs(hours_to_close - horizon_hours[horizon])
            if distance <= horizon_tolerances[horizon] and (
                best_horizon_distance[horizon] is None or distance < best_horizon_distance[horizon]
            ):
                best_horizon_distance[horizon] = distance
                best_horizon_probability[horizon] = probability
    last_time = observed_time
    last_probability = probability
    previous_ordinal = ordinal
    previous_time = observed_time
    previous_probability = probability

if current_market is not None:
    retained_markets = retained_markets + [retain_market()]

for item in retained_markets:
    event = item["event"]
    payout = item["payout"]
    regular_mean = item["regular_mean"]
    daily_mean = item["daily_mean"]
    if regular_mean is not None:
        market_regular_means = market_regular_means + [regular_mean]
        event_market_regular_count[event] = event_market_regular_count[event] + 1
        event_market_regular_sum[event] = event_market_regular_sum[event] + regular_mean
    if daily_mean is not None:
        market_daily_means = market_daily_means + [daily_mean]
        event_market_daily_count[event] = event_market_daily_count[event] + 1
        event_market_daily_sum[event] = event_market_daily_sum[event] + daily_mean
    market_endpoint_changes[payout] = market_endpoint_changes[payout] + [item["endpoint_change"]]
    market_endpoint_per_hour[payout] = market_endpoint_per_hour[payout] + [
        item["endpoint_per_hour"]
    ]
    for horizon in range(4):
        probability = item["horizon_probabilities"][horizon]
        if probability is not None:
            error = payout - probability
            horizon_count[horizon] = horizon_count[horizon] + 1
            horizon_probability[horizon] = horizon_probability[horizon] + probability
            horizon_outcome[horizon] = horizon_outcome[horizon] + payout
            horizon_brier[horizon] = horizon_brier[horizon] + error * error
            horizon_event_count[horizon][event] = horizon_event_count[horizon][event] + 1
            horizon_event_probability[horizon][event] = (
                horizon_event_probability[horizon][event] + probability
            )
            horizon_event_outcome[horizon][event] = horizon_event_outcome[horizon][event] + payout
            horizon_event_brier[horizon][event] = (
                horizon_event_brier[horizon][event] + error * error
            )
            band = probability_index(probability)
            reliability_count[horizon][band] = reliability_count[horizon][band] + 1
            reliability_probability[horizon][band] = (
                reliability_probability[horizon][band] + probability
            )
            reliability_outcome[horizon][band] = reliability_outcome[horizon][band] + payout
            reliability_brier[horizon][band] = reliability_brier[horizon][band] + error * error

event_regular_means = []
early_event_regular_means = []
late_event_regular_means = []
event_daily_means = []
positive_event_regular_count = 0
for event in range(event_count):
    if event_market_regular_count[event] > 0:
        value = event_market_regular_sum[event] / event_market_regular_count[event]
        event_regular_means = event_regular_means + [value]
        if value > 0.0:
            positive_event_regular_count = positive_event_regular_count + 1
        if event < event_count // 2:
            early_event_regular_means = early_event_regular_means + [value]
        else:
            late_event_regular_means = late_event_regular_means + [value]
    if event_market_daily_count[event] > 0:
        event_daily_means = event_daily_means + [
            event_market_daily_sum[event] / event_market_daily_count[event]
        ]

state_rows = []
state_labels = ["p_le_002", "p_002_020", "p_020_080", "p_080_098", "p_ge_098"]
for state in range(5):
    state_rows = state_rows + [
        {
            "band": state_labels[state],
            "count": state_count[state],
            "mean_change": safe_rate(state_change[state], state_count[state]),
        }
    ]

close_rows = []
close_labels = ["le_24h", "24_72h", "72_168h", "gt_168h"]
for close_band in range(4):
    close_rows = close_rows + [
        {
            "band": close_labels[close_band],
            "count": close_count[close_band],
            "mean_change": safe_rate(close_change[close_band], close_count[close_band]),
        }
    ]

calibration_rows = []
reliability_rows = []
market_overpricing_count = 0
event_overpricing_count = 0
probability_labels = [
    "p_le_002",
    "p_002_010",
    "p_010_030",
    "p_030_070",
    "p_070_090",
    "p_090_098",
    "p_ge_098",
]
for horizon in range(4):
    count = horizon_count[horizon]
    mean_probability = horizon_probability[horizon] / count
    outcome_rate = horizon_outcome[horizon] / count
    event_probabilities = []
    event_outcomes = []
    event_briers = []
    for event in range(event_count):
        current_count = horizon_event_count[horizon][event]
        if current_count > 0:
            event_probabilities = event_probabilities + [
                horizon_event_probability[horizon][event] / current_count
            ]
            event_outcomes = event_outcomes + [
                horizon_event_outcome[horizon][event] / current_count
            ]
            event_briers = event_briers + [horizon_event_brier[horizon][event] / current_count]
    event_mean_probability = sum(event_probabilities) / len(event_probabilities)
    event_outcome_rate = sum(event_outcomes) / len(event_outcomes)
    market_gap = mean_probability - outcome_rate
    event_gap = event_mean_probability - event_outcome_rate
    if market_gap >= 0.02:
        market_overpricing_count = market_overpricing_count + 1
    if event_gap >= 0.02:
        event_overpricing_count = event_overpricing_count + 1
    calibration_rows = calibration_rows + [
        {
            "hours_before_close": horizon_hours[horizon],
            "market_count": count,
            "event_count": len(event_probabilities),
            "mean_probability": mean_probability,
            "outcome_rate": outcome_rate,
            "probability_minus_outcome": market_gap,
            "brier": horizon_brier[horizon] / count,
            "event_macro_mean_probability": event_mean_probability,
            "event_macro_outcome_rate": event_outcome_rate,
            "event_macro_probability_minus_outcome": event_gap,
            "event_macro_brier": sum(event_briers) / len(event_briers),
        }
    ]
    for band in range(7):
        band_count = reliability_count[horizon][band]
        reliability_rows = reliability_rows + [
            {
                "hours_before_close": horizon_hours[horizon],
                "probability_band": probability_labels[band],
                "count": band_count,
                "mean_probability": safe_rate(reliability_probability[horizon][band], band_count),
                "outcome_rate": safe_rate(reliability_outcome[horizon][band], band_count),
                "brier": safe_rate(reliability_brier[horizon][band], band_count),
            }
        ]

event_equal_regular_mean = sum(event_regular_means) / len(event_regular_means)
early_event_equal_regular_mean = sum(early_event_regular_means) / len(early_event_regular_means)
late_event_equal_regular_mean = sum(late_event_regular_means) / len(late_event_regular_means)
event_equal_daily_mean = sum(event_daily_means) / len(event_daily_means)

negative_drift_survives = (
    event_equal_regular_mean < 0.0
    and early_event_equal_regular_mean < 0.0
    and late_event_equal_regular_mean < 0.0
    and event_equal_daily_mean < 0.0
)
broad_overpricing_survives = market_overpricing_count >= 3 and event_overpricing_count >= 3

result = structured_return(
    "Fixed composition and terminal-convergence falsifier for the process-paper drift lead.",
    {
        "schema_version": "polymarket-drift-composition/v1",
        "market_count": len(retained_markets),
        "event_count": event_count,
        "coverage_checks": {"order_break_count": order_break_count},
        "regular_drift": {
            "observation_count": observation_regular_count,
            "observation_weighted_mean": observation_regular_sum / observation_regular_count,
            "market_count": len(market_regular_means),
            "market_equal_mean": sum(market_regular_means) / len(market_regular_means),
            "event_count": len(event_regular_means),
            "event_equal_mean": event_equal_regular_mean,
            "early_event_equal_mean": early_event_equal_regular_mean,
            "late_event_equal_mean": late_event_equal_regular_mean,
            "positive_event_count": positive_event_regular_count,
            "event_mean_p10_p50_p90": [
                quantile(event_regular_means, 0.10),
                quantile(event_regular_means, 0.50),
                quantile(event_regular_means, 0.90),
            ],
        },
        "nonoverlap_daily_drift": {
            "market_count": len(market_daily_means),
            "market_equal_mean": sum(market_daily_means) / len(market_daily_means),
            "event_count": len(event_daily_means),
            "event_equal_mean": event_equal_daily_mean,
            "event_mean_p10_p50_p90": [
                quantile(event_daily_means, 0.10),
                quantile(event_daily_means, 0.50),
                quantile(event_daily_means, 0.90),
            ],
        },
        "payout_diagnostics": [
            {
                "payout": payout,
                "increment_count": payout_increment_count[payout],
                "observation_weighted_mean_increment": safe_rate(
                    payout_increment_sum[payout], payout_increment_count[payout]
                ),
                "market_count": len(market_endpoint_changes[payout]),
                "endpoint_change_mean": safe_rate(
                    sum(market_endpoint_changes[payout]), len(market_endpoint_changes[payout])
                ),
                "endpoint_change_median": quantile(market_endpoint_changes[payout], 0.50),
                "endpoint_change_per_hour_mean": safe_rate(
                    sum(market_endpoint_per_hour[payout]),
                    len(market_endpoint_per_hour[payout]),
                ),
            }
            for payout in range(2)
        ],
        "state_drift": state_rows,
        "time_to_close_drift": close_rows,
        "fixed_horizon_calibration": calibration_rows,
        "fixed_horizon_reliability": reliability_rows,
        "predeclared_falsifiers": {
            "negative_drift_survives_composition": negative_drift_survives,
            "broad_two_point_overpricing_survives": broad_overpricing_survives,
            "market_overpricing_horizon_count": market_overpricing_count,
            "event_overpricing_horizon_count": event_overpricing_count,
        },
    },
    warnings=[
        "Realized payout is used only for ex-post composition and calibration diagnostics.",
        "Payout, close time, and future observations cannot enter a decision-time predictor.",
        "Fixed-horizon samples are closest retained values within declared tolerances, not quotes.",
        "Related contracts and incomplete event surfaces may still affect cross-market weighting.",
        "A negative average change is not by itself a tradable drift or market inefficiency.",
        "All ancestor and final protected events remain unavailable.",
    ],
)
