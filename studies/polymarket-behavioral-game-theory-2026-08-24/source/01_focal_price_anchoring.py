# Copyright (c) 2026 Eigen Kapital. All rights reserved.
# Proprietary and confidential. See the LICENSE file in the project root.
"""Test focal probability crossings against fixed nearby control crossings."""

markets = read("polymarket-development-prices", "market_id")
events = read("polymarket-development-prices", "event_chronological_ordinal")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")

focal_levels = [0.10, 0.25, 0.50, 0.75, 0.90]
control_levels = [0.15, 0.30, 0.55, 0.70, 0.85]
horizon_hours = [6.0, 24.0]
horizon_tolerances = [1.0, 2.0]
local_window = 0.05
minimum_regular_hours = 0.75
maximum_regular_hours = 1.25
minimum_effect = 0.0025

event_count = max(events) + 1
group_count = 2
horizon_count = 2
level_count = 5

event_sums = [
    [[0.0 for event in range(event_count)] for horizon in range(horizon_count)]
    for group in range(group_count)
]
event_counts = [
    [[0 for event in range(event_count)] for horizon in range(horizon_count)]
    for group in range(group_count)
]
event_positive = [
    [[0 for event in range(event_count)] for horizon in range(horizon_count)]
    for group in range(group_count)
]
level_sums = [
    [[0.0 for level in range(level_count)] for horizon in range(horizon_count)]
    for group in range(group_count)
]
level_counts = [
    [[0 for level in range(level_count)] for horizon in range(horizon_count)]
    for group in range(group_count)
]
crossing_counts = [[0 for level in range(level_count)] for group in range(group_count)]
order_break_count = 0


def crossing_direction(previous_probability, probability, level):
    if previous_probability < level and probability >= level:
        return 1.0
    if previous_probability > level and probability <= level:
        return -1.0
    return None


def nearest_target_probability(market_times, market_probabilities, start, target_hours, tolerance):
    best_probability = None
    best_distance = None
    target_seconds = target_hours * 3600.0
    tolerance_seconds = tolerance * 3600.0
    for target_index in range(start + 1, len(market_times)):
        elapsed = market_times[target_index] - market_times[start]
        if elapsed > target_seconds + tolerance_seconds:
            break
        distance = abs(elapsed - target_seconds)
        if distance <= tolerance_seconds and (
            best_distance is None or distance < best_distance
        ):
            best_distance = distance
            best_probability = market_probabilities[target_index]
    return best_probability


def record_crossing(
    group,
    level_index,
    event,
    crossing_index,
    direction,
    market_times,
    market_probabilities,
):
    crossing_counts[group][level_index] = crossing_counts[group][level_index] + 1
    crossing_probability = market_probabilities[crossing_index]
    for horizon in range(horizon_count):
        target_probability = nearest_target_probability(
            market_times,
            market_probabilities,
            crossing_index,
            horizon_hours[horizon],
            horizon_tolerances[horizon],
        )
        if target_probability is not None:
            signed_return = direction * (target_probability - crossing_probability)
            event_counts[group][horizon][event] = event_counts[group][horizon][event] + 1
            event_sums[group][horizon][event] = (
                event_sums[group][horizon][event] + signed_return
            )
            if signed_return > 0.0:
                event_positive[group][horizon][event] = (
                    event_positive[group][horizon][event] + 1
                )
            level_counts[group][horizon][level_index] = (
                level_counts[group][horizon][level_index] + 1
            )
            level_sums[group][horizon][level_index] = (
                level_sums[group][horizon][level_index] + signed_return
            )


def process_market(event, market_times, market_probabilities):
    seen = [[False for level in range(level_count)] for group in range(group_count)]
    level_groups = [focal_levels, control_levels]
    for index in range(1, len(market_times)):
        gap_hours = (market_times[index] - market_times[index - 1]) / 3600.0
        if gap_hours < minimum_regular_hours or gap_hours > maximum_regular_hours:
            continue
        previous_probability = market_probabilities[index - 1]
        probability = market_probabilities[index]
        for group in range(group_count):
            for level_index in range(level_count):
                if seen[group][level_index]:
                    continue
                level = level_groups[group][level_index]
                direction = crossing_direction(previous_probability, probability, level)
                if direction is not None and (
                    abs(previous_probability - level) <= local_window
                    and abs(probability - level) <= local_window
                ):
                    seen[group][level_index] = True
                    record_crossing(
                        group,
                        level_index,
                        event,
                        index,
                        direction,
                        market_times,
                        market_probabilities,
                    )


current_market = None
current_event = None
previous_ordinal = None
previous_time = None
market_times = []
market_probabilities = []

for row in range(len(probabilities)):
    market = markets[row]
    event = events[row]
    ordinal = ordinals[row]
    observed_time = times[row]
    probability = probabilities[row]
    if market != current_market:
        if current_market is not None:
            process_market(current_event, market_times, market_probabilities)
        current_market = market
        current_event = event
        previous_ordinal = None
        previous_time = None
        market_times = []
        market_probabilities = []
        if ordinal != 0:
            order_break_count = order_break_count + 1
    elif ordinal != previous_ordinal + 1 or observed_time <= previous_time:
        order_break_count = order_break_count + 1
    market_times = market_times + [observed_time]
    market_probabilities = market_probabilities + [probability]
    previous_ordinal = ordinal
    previous_time = observed_time

if current_market is not None:
    process_market(current_event, market_times, market_probabilities)


def safe_rate(numerator, denominator):
    if denominator == 0:
        return None
    return numerator / denominator


summary_rows = []
paired_differences = [[], []]
early_differences = [[], []]
late_differences = [[], []]
for horizon in range(horizon_count):
    group_event_means = [[], []]
    group_signal_count = [0, 0]
    group_signal_sum = [0.0, 0.0]
    group_positive_count = [0, 0]
    for event in range(event_count):
        for group in range(group_count):
            count = event_counts[group][horizon][event]
            if count > 0:
                group_event_means[group] = group_event_means[group] + [
                    event_sums[group][horizon][event] / count
                ]
                group_signal_count[group] = group_signal_count[group] + count
                group_signal_sum[group] = (
                    group_signal_sum[group] + event_sums[group][horizon][event]
                )
                group_positive_count[group] = (
                    group_positive_count[group] + event_positive[group][horizon][event]
                )
        focal_count = event_counts[0][horizon][event]
        control_count = event_counts[1][horizon][event]
        if focal_count > 0 and control_count > 0:
            difference = (
                event_sums[0][horizon][event] / focal_count
                - event_sums[1][horizon][event] / control_count
            )
            paired_differences[horizon] = paired_differences[horizon] + [difference]
            if event < event_count // 2:
                early_differences[horizon] = early_differences[horizon] + [difference]
            else:
                late_differences[horizon] = late_differences[horizon] + [difference]
    summary_rows = summary_rows + [
        {
            "horizon_hours": horizon_hours[horizon],
            "focal_signal_count": group_signal_count[0],
            "control_signal_count": group_signal_count[1],
            "focal_event_count": len(group_event_means[0]),
            "control_event_count": len(group_event_means[1]),
            "paired_event_count": len(paired_differences[horizon]),
            "focal_signal_mean": safe_rate(group_signal_sum[0], group_signal_count[0]),
            "control_signal_mean": safe_rate(group_signal_sum[1], group_signal_count[1]),
            "focal_event_macro_mean": safe_rate(
                sum(group_event_means[0]), len(group_event_means[0])
            ),
            "control_event_macro_mean": safe_rate(
                sum(group_event_means[1]), len(group_event_means[1])
            ),
            "paired_event_macro_focal_minus_control": safe_rate(
                sum(paired_differences[horizon]), len(paired_differences[horizon])
            ),
            "early_paired_difference": safe_rate(
                sum(early_differences[horizon]), len(early_differences[horizon])
            ),
            "late_paired_difference": safe_rate(
                sum(late_differences[horizon]), len(late_differences[horizon])
            ),
            "focal_positive_continuation_rate": safe_rate(
                group_positive_count[0], group_signal_count[0]
            ),
            "control_positive_continuation_rate": safe_rate(
                group_positive_count[1], group_signal_count[1]
            ),
        }
    ]

level_rows = []
for level_index in range(level_count):
    for horizon in range(horizon_count):
        level_rows = level_rows + [
            {
                "horizon_hours": horizon_hours[horizon],
                "focal_level": focal_levels[level_index],
                "control_level": control_levels[level_index],
                "focal_crossing_count": crossing_counts[0][level_index],
                "control_crossing_count": crossing_counts[1][level_index],
                "focal_target_count": level_counts[0][horizon][level_index],
                "control_target_count": level_counts[1][horizon][level_index],
                "focal_mean_signed_return": safe_rate(
                    level_sums[0][horizon][level_index],
                    level_counts[0][horizon][level_index],
                ),
                "control_mean_signed_return": safe_rate(
                    level_sums[1][horizon][level_index],
                    level_counts[1][horizon][level_index],
                ),
            }
        ]

six_hour = summary_rows[0]
twenty_four_hour = summary_rows[1]
six_difference = six_hour["paired_event_macro_focal_minus_control"]
twenty_four_difference = twenty_four_hour["paired_event_macro_focal_minus_control"]
early_difference = twenty_four_hour["early_paired_difference"]
late_difference = twenty_four_hour["late_paired_difference"]
coverage_passed = (
    twenty_four_hour["focal_signal_count"] >= 100
    and twenty_four_hour["paired_event_count"] >= 30
)

screen_outcome = "NO_STABLE_FOCAL_EFFECT"
if coverage_passed and (
    six_difference is not None
    and twenty_four_difference is not None
    and early_difference is not None
    and late_difference is not None
):
    if (
        six_difference <= -minimum_effect
        and twenty_four_difference <= -minimum_effect
        and early_difference < 0.0
        and late_difference < 0.0
    ):
        screen_outcome = "FOCAL_BARRIER_SUPPORT"
    elif (
        six_difference >= minimum_effect
        and twenty_four_difference >= minimum_effect
        and early_difference > 0.0
        and late_difference > 0.0
    ):
        screen_outcome = "FOCAL_BREAKOUT_SUPPORT"

result = structured_return(
    "Predeclared focal-price anchoring barrier-versus-breakout screen.",
    {
        "schema_version": "polymarket-focal-price-anchoring/v1",
        "screen_outcome": screen_outcome,
        "coverage_passed": coverage_passed,
        "order_break_count": order_break_count,
        "focal_levels": focal_levels,
        "control_levels": control_levels,
        "local_window": local_window,
        "minimum_effect": minimum_effect,
        "summary_rows": summary_rows,
        "level_rows": level_rows,
    },
    warnings=[
        "The whole-event development partition is selection-exposed; protected values remain hidden.",
        "Sampled probabilities are not executable quotes, fills, or latent beliefs.",
        "First crossings reduce repeated-signal dependence but markets within an event remain dependent.",
        "Matched nearby levels are a bounded-state rival, not a randomized causal control.",
        "A screen outcome is provisional and cannot authorize freeze, promotion, or trading.",
    ],
)
