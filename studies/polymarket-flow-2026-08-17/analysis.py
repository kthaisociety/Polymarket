# ruff: noqa

prices_raw = read("polymarket-development-view", "trade_price")
signed_sizes_raw = read("polymarket-development-view", "signed_trade_size")
outcomes = read("polymarket-development-view", "outcome_index")
times = read("polymarket-development-view", "reference_time_epoch_seconds")
fill_ids = read("polymarket-development-view", "fill_uid")


def mean(values):
    if len(values) == 0:
        return 0.0
    return sum(values) / len(values)


def standard_deviation(values):
    if len(values) < 2:
        return 0.0
    center = mean(values)
    return (sum((value - center) ** 2 for value in values) / (len(values) - 1)) ** 0.5


def correlation(left, right):
    if len(left) < 2 or len(left) != len(right):
        return 0.0
    left_center = mean(left)
    right_center = mean(right)
    numerator = sum(
        (left_value - left_center) * (right_value - right_center)
        for left_value, right_value in zip(left, right)
    )
    denominator = (
        sum((value - left_center) ** 2 for value in left)
        * sum((value - right_center) ** 2 for value in right)
    ) ** 0.5
    if denominator == 0.0:
        return 0.0
    return numerator / denominator


def directional_accuracy(signal, labels):
    usable = [
        (signal_value, label)
        for signal_value, label in zip(signal, labels)
        if signal_value != 0.0 and label != 0.0
    ]
    if len(usable) == 0:
        return 0.0
    return sum(
        1
        for signal_value, label in usable
        if (signal_value > 0.0 and label > 0.0)
        or (signal_value < 0.0 and label < 0.0)
    ) / len(usable)


def summarize(name, indexes, future_indexes, signal):
    labels = [prices[future_indexes[index]] - prices[index] for index in indexes]
    selected_signal = [signal[index] for index in indexes]
    ordered = sorted(zip(selected_signal, labels))
    fifth = max(1, len(ordered) // 5)
    midpoint = len(indexes) // 2
    low_prices = [
        labels[position]
        for position, index in enumerate(indexes)
        if prices[index] < 0.25
    ]
    middle_prices = [
        labels[position]
        for position, index in enumerate(indexes)
        if prices[index] >= 0.25 and prices[index] <= 0.75
    ]
    high_prices = [
        labels[position]
        for position, index in enumerate(indexes)
        if prices[index] > 0.75
    ]
    return {
        "name": name,
        "n": len(labels),
        "label_mean": mean(labels),
        "label_standard_deviation": standard_deviation(labels),
        "signal_label_correlation": correlation(selected_signal, labels),
        "directional_accuracy_excluding_zeros": directional_accuracy(selected_signal, labels),
        "bottom_signal_fifth_mean_label": mean([pair[1] for pair in ordered[:fifth]]),
        "top_signal_fifth_mean_label": mean([pair[1] for pair in ordered[-fifth:]]),
        "first_half_correlation": correlation(
            selected_signal[:midpoint], labels[:midpoint]
        ),
        "second_half_correlation": correlation(
            selected_signal[midpoint:], labels[midpoint:]
        ),
        "mean_label_when_price_below_0_25": mean(low_prices),
        "n_price_below_0_25": len(low_prices),
        "mean_label_when_price_0_25_to_0_75": mean(middle_prices),
        "n_price_0_25_to_0_75": len(middle_prices),
        "mean_label_when_price_above_0_75": mean(high_prices),
        "n_price_above_0_75": len(high_prices),
    }


prices = [
    price if outcome == 0 else 1.0 - price
    for price, outcome in zip(prices_raw, outcomes)
]
signed_yes_flow = [
    size if outcome == 0 else -size
    for size, outcome in zip(signed_sizes_raw, outcomes)
]
rolling_20_flow = [
    sum(signed_yes_flow[max(0, index - 19) : index + 1])
    for index in range(len(signed_yes_flow))
]

event_results = []
for horizon in (1, 5, 20):
    future = [index + horizon for index in range(len(prices) - horizon)]
    indexes = [
        index
        for index in range(len(prices) - horizon)
        if times[index + horizon] > times[index]
    ]
    event_results = event_results + [
        summarize(
            "current_yes_flow_event_horizon_" + str(horizon),
            indexes,
            future,
            signed_yes_flow,
        ),
        summarize(
            "rolling_20_yes_flow_event_horizon_" + str(horizon),
            indexes,
            future,
            rolling_20_flow,
        ),
    ]

five_minute_future = [-1] * len(prices)
left = 0
right = 0
while left < len(prices):
    if right <= left:
        right = left + 1
    while right < len(prices) and times[right] < times[left] + 300.0:
        right = right + 1
    if right < len(prices) and times[right] <= times[left] + 900.0:
        five_minute_future[left] = right
    left = left + 1
five_minute_indexes = [
    index for index in range(len(prices)) if five_minute_future[index] >= 0
]
elapsed_results = [
    summarize(
        "current_yes_flow_first_print_5_to_15_minutes_later",
        five_minute_indexes,
        five_minute_future,
        signed_yes_flow,
    ),
    summarize(
        "rolling_20_yes_flow_first_print_5_to_15_minutes_later",
        five_minute_indexes,
        five_minute_future,
        rolling_20_flow,
    ),
]

result = structured_return(
    "Explored whether aggressor-signed YES-equivalent flow predicts later YES-equivalent prices.",
    {
        "contract_fill_count": len(prices),
        "unique_fill_count": len(set(fill_ids)),
        "first_epoch_seconds": min(times),
        "last_epoch_seconds": max(times),
        "canonical_price_mean": mean(prices),
        "canonical_price_standard_deviation": standard_deviation(prices),
        "buy_equivalent_fraction": sum(1 for value in signed_yes_flow if value > 0.0)
        / len(signed_yes_flow),
        "event_time_results": event_results,
        "elapsed_time_results": elapsed_results,
    },
    warnings=[
        "EXPLORATORY only; no formal feature, label, candidate, or protected evidence.",
        "The contract question and event grouping are unavailable through this adapter.",
        "Prints are observational and irregular; these statistics do not establish causality.",
        "Multiple horizons and signals were inspected without multiplicity correction.",
    ],
)
