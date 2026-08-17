# ruff: noqa

prices_raw = read("polymarket-development-view", "trade_price")
signed_sizes_raw = read("polymarket-development-view", "signed_trade_size")
outcomes = read("polymarket-development-view", "outcome_index")
times = read("polymarket-development-view", "reference_time_epoch_seconds")


def mean(values):
    if len(values) == 0:
        return 0.0
    return sum(values) / len(values)


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


def summarize(name, future):
    indexes = [index for index in range(len(future)) if future[index] >= 0]
    labels = [prices[future[index]] - prices[index] for index in indexes]
    signals = [signed_yes_flow[index] for index in indexes]
    buys = [label for signal, label in zip(signals, labels) if signal > 0.0]
    sells = [label for signal, label in zip(signals, labels) if signal < 0.0]
    return {
        "name": name,
        "n": len(labels),
        "signal_label_correlation": correlation(signals, labels),
        "mean_label_after_yes_equivalent_buy": mean(buys),
        "mean_label_after_yes_equivalent_sell": mean(sells),
        "buy_minus_sell_mean_label": mean(buys) - mean(sells),
        "zero_return_fraction": sum(1 for label in labels if label == 0.0) / len(labels),
        "mean_elapsed_seconds": mean([times[future[index]] - times[index] for index in indexes]),
    }


prices = [
    price if outcome == 0 else 1.0 - price
    for price, outcome in zip(prices_raw, outcomes)
]
signed_yes_flow = [
    size if outcome == 0 else -size
    for size, outcome in zip(signed_sizes_raw, outcomes)
]
directions = [1 if value > 0.0 else -1 for value in signed_yes_flow]

next_any = [-1] * len(prices)
next_same_direction = [-1] * len(prices)
next_opposite_direction = [-1] * len(prices)
index = 0
while index < len(prices) - 1:
    candidate = index + 1
    while candidate < len(prices) and times[candidate] <= times[index]:
        candidate = candidate + 1
    if candidate < len(prices):
        next_any[index] = candidate
    limit = min(len(prices), index + 101)
    same_candidate = candidate
    while (
        same_candidate < limit
        and directions[same_candidate] != directions[index]
    ):
        same_candidate = same_candidate + 1
    if same_candidate < limit and times[same_candidate] > times[index]:
        next_same_direction[index] = same_candidate
    opposite_candidate = candidate
    while (
        opposite_candidate < limit
        and directions[opposite_candidate] == directions[index]
    ):
        opposite_candidate = opposite_candidate + 1
    if opposite_candidate < limit and times[opposite_candidate] > times[index]:
        next_opposite_direction[index] = opposite_candidate
    index = index + 1

result = structured_return(
    "Tested whether apparent flow reversal survives matching the later aggressor direction.",
    {
        "contract_fill_count": len(prices),
        "distinct_canonical_price_count": len(set(prices)),
        "comparisons": [
            summarize("first_later_print_any_direction", next_any),
            summarize("first_later_print_same_direction_within_100_prints", next_same_direction),
            summarize(
                "first_later_print_opposite_direction_within_100_prints",
                next_opposite_direction,
            ),
        ],
    },
    warnings=[
        "EXPLORATORY microstructure falsifier; no formal candidate or protected evidence.",
        "Same-direction matching is a diagnostic for bid/ask bounce, not a causal adjustment.",
        "The 100-print search cap was selected after inspecting the initial reversal pattern.",
    ],
)
