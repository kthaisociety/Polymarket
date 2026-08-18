markets = read("polymarket-development-prices", "market_id")
events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")
outcome_markets = read("polymarket-development-outcomes", "market_id")
close_times = read("polymarket-development-outcomes", "close_time_epoch_seconds")

PI = 3.141592653589793
CELL_PRIOR_EVENT_WEIGHT = 1.0
MEASUREMENT_HALF_WIDTH = 0.0005


def clipped_probability(value):
    return min(0.999999999999, max(0.000000000001, value))


def probability_band(value):
    if value <= 0.02:
        return 0
    if value < 0.20:
        return 1
    if value <= 0.80:
        return 2
    if value < 0.98:
        return 3
    return 4


def close_band(hours):
    if hours <= 24.0:
        return 0
    if hours <= 72.0:
        return 1
    if hours <= 168.0:
        return 2
    return 3


def quiet_band(quiet_run):
    if quiet_run == 0:
        return 0
    if quiet_run <= 5:
        return 1
    if quiet_run <= 23:
        return 2
    return 3


def magnitude_band(magnitude):
    if magnitude == 0.0:
        return 0
    if magnitude <= 0.005:
        return 1
    if magnitude <= 0.02:
        return 2
    if magnitude <= 0.10:
        return 3
    return 4


def normal_cdf(value):
    absolute = abs(value)
    tail = 1.0 / (1.0 + 0.2316419 * absolute)
    density = 0.3989422804014327 * exp(-0.5 * absolute * absolute)
    polynomial = tail * (
        0.319381530
        + tail
        * (-0.356563782 + tail * (1.781477937 + tail * (-1.821255978 + tail * 1.330274429)))
    )
    result = 1.0 - density * polynomial
    if value < 0.0:
        result = 1.0 - result
    return min(1.0, max(0.0, result))


def normal_interval_probability(value, mean, scale, half_width):
    bounded_scale = max(0.000001, scale)
    upper = normal_cdf((value + half_width - mean) / bounded_scale)
    lower = normal_cdf((value - half_width - mean) / bounded_scale)
    return clipped_probability(upper - lower)


def lognormal_interval_probability(magnitude, mean, scale, half_width):
    lower_value = max(0.000001, magnitude - half_width)
    upper_value = min(1.0, magnitude + half_width)
    bounded_scale = max(0.05, scale)
    upper = normal_cdf((log(upper_value) - mean) / bounded_scale)
    lower = normal_cdf((log(lower_value) - mean) / bounded_scale)
    return clipped_probability(upper - lower)


def shrunken_probability(success, weight, prior):
    return clipped_probability(
        (success + CELL_PRIOR_EVENT_WEIGHT * prior) / (weight + CELL_PRIOR_EVENT_WEIGHT)
    )


def shrunken_normal(total, second, weight, prior_mean, prior_second):
    denominator = weight + CELL_PRIOR_EVENT_WEIGHT
    mean = (total + CELL_PRIOR_EVENT_WEIGHT * prior_mean) / denominator
    second_moment = (second + CELL_PRIOR_EVENT_WEIGHT * prior_second) / denominator
    variance = max(0.0025, second_moment - mean * mean)
    return [mean, variance**0.5]


def fit_process(training_end):
    event_counts = [0 for unused in range(training_end)]
    nonzero_event_counts = [0 for unused in range(training_end)]
    for row in range(sample_count):
        event = row_events[row]
        if event < training_end:
            event_counts[event] = event_counts[event] + 1
            if move_labels[row] == 1:
                nonzero_event_counts[event] = nonzero_event_counts[event] + 1
    represented = sum([1 for count in event_counts if count > 0])

    move_weight = 0.0
    move_success = 0.0
    nonzero_weight = 0.0
    positive_success = 0.0
    log_total = 0.0
    log_second = 0.0
    diffusion_total = 0.0
    diffusion_weight = 0.0

    arrival_state_weight = [0.0 for unused in range(20)]
    arrival_state_success = [0.0 for unused in range(20)]
    arrival_full_weight = [0.0 for unused in range(20)]
    arrival_full_success = [0.0 for unused in range(20)]
    sign_state_weight = [0.0 for unused in range(20)]
    sign_state_success = [0.0 for unused in range(20)]
    sign_full_weight = [0.0 for unused in range(15)]
    sign_full_success = [0.0 for unused in range(15)]
    magnitude_state_weight = [0.0 for unused in range(20)]
    magnitude_state_total = [0.0 for unused in range(20)]
    magnitude_state_second = [0.0 for unused in range(20)]
    magnitude_full_weight = [0.0 for unused in range(25)]
    magnitude_full_total = [0.0 for unused in range(25)]
    magnitude_full_second = [0.0 for unused in range(25)]
    diffusion_state_weight = [0.0 for unused in range(20)]
    diffusion_state_total = [0.0 for unused in range(20)]

    for row in range(sample_count):
        event = row_events[row]
        if event < training_end and event_counts[event] > 0:
            weight = 1.0 / event_counts[event]
            move = move_labels[row]
            state = probability_bands[row] * 4 + close_bands[row]
            arrival_full = probability_bands[row] * 4 + quiet_bands[row]
            move_weight = move_weight + weight
            move_success = move_success + weight * move
            arrival_state_weight[state] = arrival_state_weight[state] + weight
            arrival_state_success[state] = arrival_state_success[state] + weight * move
            arrival_full_weight[arrival_full] = arrival_full_weight[arrival_full] + weight
            arrival_full_success[arrival_full] = arrival_full_success[arrival_full] + weight * move
            shape = max(0.001, probability_levels[row] * (1.0 - probability_levels[row]))
            diffusion_scaled_square = changes[row] * changes[row] / shape
            diffusion_total = diffusion_total + weight * diffusion_scaled_square
            diffusion_weight = diffusion_weight + weight
            diffusion_state_weight[state] = diffusion_state_weight[state] + weight
            diffusion_state_total[state] = (
                diffusion_state_total[state] + weight * diffusion_scaled_square
            )
            if move == 1:
                mark_weight = 1.0 / nonzero_event_counts[event]
                positive = positive_labels[row]
                log_magnitude = log_magnitudes[row]
                sign_full = probability_bands[row] * 3 + prior_sign_bands[row]
                magnitude_full = probability_bands[row] * 5 + prior_magnitude_bands[row]
                nonzero_weight = nonzero_weight + mark_weight
                positive_success = positive_success + mark_weight * positive
                log_total = log_total + mark_weight * log_magnitude
                log_second = log_second + mark_weight * log_magnitude * log_magnitude
                sign_state_weight[state] = sign_state_weight[state] + mark_weight
                sign_state_success[state] = sign_state_success[state] + mark_weight * positive
                sign_full_weight[sign_full] = sign_full_weight[sign_full] + mark_weight
                sign_full_success[sign_full] = (
                    sign_full_success[sign_full] + mark_weight * positive
                )
                magnitude_state_weight[state] = magnitude_state_weight[state] + mark_weight
                magnitude_state_total[state] = (
                    magnitude_state_total[state] + mark_weight * log_magnitude
                )
                magnitude_state_second[state] = (
                    magnitude_state_second[state]
                    + mark_weight * log_magnitude * log_magnitude
                )
                magnitude_full_weight[magnitude_full] = (
                    magnitude_full_weight[magnitude_full] + mark_weight
                )
                magnitude_full_total[magnitude_full] = (
                    magnitude_full_total[magnitude_full] + mark_weight * log_magnitude
                )
                magnitude_full_second[magnitude_full] = (
                    magnitude_full_second[magnitude_full]
                    + mark_weight * log_magnitude * log_magnitude
                )

    global_move = clipped_probability(move_success / move_weight)
    global_positive = clipped_probability(positive_success / nonzero_weight)
    global_log_mean = log_total / nonzero_weight
    global_log_second = log_second / nonzero_weight
    global_log_scale = max(0.05, global_log_second - global_log_mean * global_log_mean) ** 0.5
    global_diffusion_scale = max(0.000000000001, diffusion_total / diffusion_weight)

    arrival_state = []
    arrival_full = []
    sign_state = []
    sign_full = []
    magnitude_state = []
    magnitude_full = []
    diffusion_state = []
    for cell in range(20):
        arrival_state = arrival_state + [
            shrunken_probability(
                arrival_state_success[cell], arrival_state_weight[cell], global_move
            )
        ]
        magnitude_state = magnitude_state + [
            shrunken_normal(
                magnitude_state_total[cell],
                magnitude_state_second[cell],
                magnitude_state_weight[cell],
                global_log_mean,
                global_log_second,
            )
        ]
        sign_state = sign_state + [
            shrunken_probability(sign_state_success[cell], sign_state_weight[cell], global_positive)
        ]
        diffusion_state = diffusion_state + [
            (
                diffusion_state_total[cell]
                + CELL_PRIOR_EVENT_WEIGHT * global_diffusion_scale
            )
            / (diffusion_state_weight[cell] + CELL_PRIOR_EVENT_WEIGHT)
        ]
        arrival_full = arrival_full + [
            shrunken_probability(
                arrival_full_success[cell], arrival_full_weight[cell], global_move
            )
        ]
    for cell in range(15):
        sign_full = sign_full + [
            shrunken_probability(sign_full_success[cell], sign_full_weight[cell], global_positive)
        ]
    for cell in range(25):
        magnitude_full = magnitude_full + [
            shrunken_normal(
                magnitude_full_total[cell],
                magnitude_full_second[cell],
                magnitude_full_weight[cell],
                global_log_mean,
                global_log_second,
            )
        ]
    return [
        represented,
        global_move,
        global_positive,
        global_log_mean,
        global_log_scale,
        global_diffusion_scale,
        arrival_state,
        arrival_full,
        sign_state,
        sign_full,
        magnitude_state,
        magnitude_full,
        diffusion_state,
    ]


def hurdle_probability(model, family, row):
    state = probability_bands[row] * 4 + close_bands[row]
    if family == "constant":
        move_probability = model[1]
        positive_probability = model[2]
        magnitude_parameters = [model[3], model[4]]
    elif family == "state":
        move_probability = model[6][state]
        positive_probability = model[8][state]
        magnitude_parameters = model[10][state]
    else:
        arrival_cell = probability_bands[row] * 4 + quiet_bands[row]
        sign_cell = probability_bands[row] * 3 + prior_sign_bands[row]
        magnitude_cell = probability_bands[row] * 5 + prior_magnitude_bands[row]
        move_probability = model[7][arrival_cell]
        positive_probability = model[9][sign_cell]
        magnitude_parameters = model[11][magnitude_cell]
    if move_labels[row] == 0:
        return clipped_probability(1.0 - move_probability)
    sign_probability = positive_probability
    if positive_labels[row] == 0:
        sign_probability = 1.0 - positive_probability
    magnitude_probability = lognormal_interval_probability(
        abs(changes[row]),
        magnitude_parameters[0],
        magnitude_parameters[1],
        MEASUREMENT_HALF_WIDTH,
    )
    return clipped_probability(move_probability * sign_probability * magnitude_probability)


def diffusion_probability(model, row):
    state = probability_bands[row] * 4 + close_bands[row]
    shape = max(0.001, probability_levels[row] * (1.0 - probability_levels[row]))
    scale = (max(0.000000000001, model[12][state]) * shape) ** 0.5
    return normal_interval_probability(
        changes[row], 0.0, scale, MEASUREMENT_HALF_WIDTH
    )


def summarize_scores(test_events, losses, comparator_losses):
    first_event = min(test_events)
    slots = max(test_events) - first_event + 1
    counts = [0 for unused in range(slots)]
    totals = [0.0 for unused in range(slots)]
    comparator_totals = [0.0 for unused in range(slots)]
    observation_total = 0.0
    wins = 0
    for row in range(len(test_events)):
        position = test_events[row] - first_event
        counts[position] = counts[position] + 1
        totals[position] = totals[position] + losses[row]
        comparator_totals[position] = comparator_totals[position] + comparator_losses[row]
        observation_total = observation_total + losses[row]
    event_values = []
    event_rows = []
    for position in range(slots):
        if counts[position] > 0:
            value = totals[position] / counts[position]
            comparator = comparator_totals[position] / counts[position]
            if value < comparator:
                wins = wins + 1
            event_values = event_values + [value]
            event_rows = event_rows + [
                {
                    "event": first_event + position,
                    "count": counts[position],
                    "mean_nll": value,
                    "comparator_mean_nll": comparator,
                }
            ]
    midpoint = len(event_values) // 2
    return {
        "prediction_count": len(test_events),
        "event_count": len(event_values),
        "observation_mean_nll": observation_total / len(test_events),
        "event_macro_mean_nll": sum(event_values) / len(event_values),
        "early_event_macro_mean_nll": sum(event_values[:midpoint]) / midpoint,
        "late_event_macro_mean_nll": sum(event_values[midpoint:])
        / (len(event_values) - midpoint),
        "event_wins_vs_comparator": wins,
        "event_rows": event_rows,
    }


close_by_market = {}
for row in range(len(outcome_markets)):
    close_by_market[outcome_markets[row]] = close_times[row]

maximum_rows = len(probabilities)
row_events = [0 for unused in range(maximum_rows)]
changes = [0.0 for unused in range(maximum_rows)]
probability_levels = [0.0 for unused in range(maximum_rows)]
probability_bands = [0 for unused in range(maximum_rows)]
close_bands = [0 for unused in range(maximum_rows)]
quiet_bands = [0 for unused in range(maximum_rows)]
prior_sign_bands = [1 for unused in range(maximum_rows)]
prior_magnitude_bands = [0 for unused in range(maximum_rows)]
move_labels = [0 for unused in range(maximum_rows)]
positive_labels = [0 for unused in range(maximum_rows)]
log_magnitudes = [0.0 for unused in range(maximum_rows)]
sample_count = 0
order_break_count = 0
current_market = None
previous_ordinal = None
previous_time = None
previous_probability = None
previous_nonzero_sign = 0
previous_nonzero_magnitude = 0.0
quiet_run = 0
recent_changes = []

for row in range(len(probabilities)):
    market = markets[row]
    event = events[row]
    ordinal = ordinals[row]
    observed_time = times[row]
    probability = probabilities[row]
    if market != current_market:
        current_market = market
        previous_ordinal = None
        previous_time = None
        previous_probability = None
        previous_nonzero_sign = 0
        previous_nonzero_magnitude = 0.0
        quiet_run = 0
        recent_changes = []
        if ordinal != 0:
            order_break_count = order_break_count + 1
    if previous_time is not None:
        if ordinal != previous_ordinal + 1 or observed_time <= previous_time:
            order_break_count = order_break_count + 1
            previous_nonzero_sign = 0
            previous_nonzero_magnitude = 0.0
            quiet_run = 0
            recent_changes = []
        else:
            gap_hours = (observed_time - previous_time) / 3600.0
            if gap_hours < 0.75 or gap_hours > 1.25:
                previous_nonzero_sign = 0
                previous_nonzero_magnitude = 0.0
                quiet_run = 0
                recent_changes = []
            else:
                change = probability - previous_probability
                hours_to_close = (close_by_market[market] - previous_time) / 3600.0
                if len(recent_changes) == 24 and hours_to_close >= 0.0:
                    row_events[sample_count] = event
                    changes[sample_count] = change
                    probability_levels[sample_count] = previous_probability
                    probability_bands[sample_count] = probability_band(previous_probability)
                    close_bands[sample_count] = close_band(hours_to_close)
                    quiet_bands[sample_count] = quiet_band(quiet_run)
                    prior_sign_bands[sample_count] = previous_nonzero_sign + 1
                    prior_magnitude_bands[sample_count] = magnitude_band(
                        previous_nonzero_magnitude
                    )
                    if change != 0.0:
                        move_labels[sample_count] = 1
                        log_magnitudes[sample_count] = log(max(0.000001, abs(change)))
                        if change > 0.0:
                            positive_labels[sample_count] = 1
                    sample_count = sample_count + 1
                recent_changes = recent_changes + [change]
                if len(recent_changes) > 24:
                    recent_changes = recent_changes[1:]
                if change == 0.0:
                    quiet_run = quiet_run + 1
                else:
                    quiet_run = 0
                    previous_nonzero_magnitude = abs(change)
                    previous_nonzero_sign = 1
                    if change < 0.0:
                        previous_nonzero_sign = -1
    previous_ordinal = ordinal
    previous_time = observed_time
    previous_probability = probability

row_events = row_events[:sample_count]
changes = changes[:sample_count]
probability_levels = probability_levels[:sample_count]
probability_bands = probability_bands[:sample_count]
close_bands = close_bands[:sample_count]
quiet_bands = quiet_bands[:sample_count]
prior_sign_bands = prior_sign_bands[:sample_count]
prior_magnitude_bands = prior_magnitude_bands[:sample_count]
move_labels = move_labels[:sample_count]
positive_labels = positive_labels[:sample_count]
log_magnitudes = log_magnitudes[:sample_count]

test_events = []
diffusion_losses = []
constant_losses = []
state_losses = []
full_losses = []
folds = []
test_start = 40
while test_start <= max(row_events):
    test_end = min(test_start + 15, max(row_events) + 1)
    model = fit_process(test_start)
    fold_count = 0
    for row in range(sample_count):
        event = row_events[row]
        if event >= test_start and event < test_end:
            test_events = test_events + [event]
            diffusion_losses = diffusion_losses + [-log(diffusion_probability(model, row))]
            constant_losses = constant_losses + [
                -log(hurdle_probability(model, "constant", row))
            ]
            state_losses = state_losses + [-log(hurdle_probability(model, "state", row))]
            full_losses = full_losses + [-log(hurdle_probability(model, "full", row))]
            fold_count = fold_count + 1
    folds = folds + [
        {
            "train_event_end_exclusive": test_start,
            "test_event_start": test_start,
            "test_event_end_exclusive": test_end,
            "training_event_count": model[0],
            "prediction_count": fold_count,
        }
    ]
    test_start = test_end

diffusion_metrics = summarize_scores(test_events, diffusion_losses, diffusion_losses)
constant_metrics = summarize_scores(test_events, constant_losses, diffusion_losses)
state_metrics = summarize_scores(test_events, state_losses, constant_losses)
full_vs_state_metrics = summarize_scores(test_events, full_losses, state_losses)
full_vs_diffusion_metrics = summarize_scores(test_events, full_losses, diffusion_losses)
relative_improvement = (
    state_metrics["event_macro_mean_nll"] - full_vs_state_metrics["event_macro_mean_nll"]
) / state_metrics["event_macro_mean_nll"]
gate_passed = (
    full_vs_state_metrics["observation_mean_nll"] < state_metrics["observation_mean_nll"]
    and full_vs_state_metrics["event_macro_mean_nll"] < state_metrics["event_macro_mean_nll"]
    and full_vs_diffusion_metrics["observation_mean_nll"]
    < diffusion_metrics["observation_mean_nll"]
    and full_vs_diffusion_metrics["event_macro_mean_nll"]
    < diffusion_metrics["event_macro_mean_nll"]
    and relative_improvement >= 0.02
    and full_vs_state_metrics["event_wins_vs_comparator"]
    / full_vs_state_metrics["event_count"]
    >= 0.60
    and full_vs_diffusion_metrics["event_wins_vs_comparator"]
    / full_vs_diffusion_metrics["event_count"]
    >= 0.60
    and full_vs_state_metrics["early_event_macro_mean_nll"]
    < state_metrics["early_event_macro_mean_nll"]
    and full_vs_state_metrics["late_event_macro_mean_nll"]
    < state_metrics["late_event_macro_mean_nll"]
    and full_vs_diffusion_metrics["early_event_macro_mean_nll"]
    < diffusion_metrics["early_event_macro_mean_nll"]
    and full_vs_diffusion_metrics["late_event_macro_mean_nll"]
    < diffusion_metrics["late_event_macro_mean_nll"]
)
final_model = fit_process(max(row_events) + 1)

result = structured_return(
    "Chronological composed stochastic-process family comparison.",
    {
        "schema_version": "polymarket-composed-process-family-comparison/v1",
        "families": [
            "bounded_state_dependent_zero_drift_gaussian_diffusion",
            "memoryless_zero_inflated_lognormal_marked_jump",
            "state_conditioned_zero_inflated_lognormal_marked_jump",
            "state_duration_path_zero_inflated_lognormal_marked_jump",
        ],
        "measurement_half_width_probability": MEASUREMENT_HALF_WIDTH,
        "cell_prior_event_weight": CELL_PRIOR_EVENT_WEIGHT,
        "warmup_regular_increment_count": 24,
        "fixed_test_block_event_count": 15,
        "sample_count": sample_count,
        "test_prediction_count": len(test_events),
        "test_event_start": 40,
        "test_event_end_inclusive": max(test_events),
        "coverage_checks": {"order_break_count": order_break_count},
        "bounded_diffusion": diffusion_metrics,
        "memoryless_hurdle": constant_metrics,
        "state_hurdle": state_metrics,
        "full_hurdle_vs_state": full_vs_state_metrics,
        "full_hurdle_vs_diffusion": full_vs_diffusion_metrics,
        "full_event_macro_nll_relative_improvement_vs_state": relative_improvement,
        "composed_process_gate_passed": gate_passed,
        "folds": folds,
        "final_development_model": final_model,
        "protected_values_exposed": False,
    },
    warnings=[
        "Scores are probabilities of the same fixed 0.001-wide observation interval.",
        "The hurdle gives exact zero a point mass and uses a lognormal interval law only for nonzero magnitude.",
        "The diffusion baseline has zero drift and state/time-to-close variance proportional to p(1-p).",
        "Cell estimates use one fixed event-weight prior toward the event-equal global law.",
        "All fitted quantities use only earlier whole events in every chronological fold.",
        "The final development model is emitted for an independently frozen successor replay, not evaluated here.",
        "These are sampled probabilities, not trades, quotes, latent beliefs, or executable returns.",
        "Grid width is a measurement convention and does not identify exchange tick or order-book mechanics.",
        "Ancestor and protected values remain unavailable.",
    ],
)
