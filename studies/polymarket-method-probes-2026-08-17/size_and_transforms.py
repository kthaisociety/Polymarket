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


def summarize_size(name, indexes, labels, values):
    selected = [values[index] for index in indexes]
    ordered = sorted(zip(selected, labels))
    fifth = max(1, len(ordered) // 5)
    midpoint = len(labels) // 2
    return {
        "name": name,
        "n": len(labels),
        "correlation": correlation(selected, labels),
        "first_half_correlation": correlation(selected[:midpoint], labels[:midpoint]),
        "second_half_correlation": correlation(selected[midpoint:], labels[midpoint:]),
        "bottom_size_fifth_mean_return": mean([pair[1] for pair in ordered[:fifth]]),
        "top_size_fifth_mean_return": mean([pair[1] for pair in ordered[-fifth:]]),
    }


def fractional_weights(order, width):
    weights = [1.0]
    lag = 1
    while lag < width:
        next_weight = -weights[-1] * (order - lag + 1.0) / lag
        weights = weights + [next_weight]
        lag = lag + 1
    return weights


def fractional_series(values, order, width):
    weights = fractional_weights(order, width)
    output = [0.0] * len(values)
    index = width - 1
    while index < len(values):
        output[index] = sum(
            weights[lag] * values[index - lag] for lag in range(width)
        )
        index = index + 1
    return output


prices = [
    price if outcome == 0 else 1.0 - price
    for price, outcome in zip(prices_raw, outcomes)
]
signed_yes_flow = [
    size if outcome == 0 else -size
    for size, outcome in zip(signed_sizes_raw, outcomes)
]
sizes = [abs(value) for value in signed_yes_flow]
directions = [1 if value > 0.0 else -1 for value in signed_yes_flow]
square_root_sizes = [value ** 0.5 for value in sizes]

calibration_count = max(100, len(prices) // 5)
calibration_sizes = sorted(sizes[:calibration_count])
cap_index = min(len(calibration_sizes) - 1, int(len(calibration_sizes) * 0.95))
size_cap = calibration_sizes[cap_index]
capped_sizes = [min(value, size_cap) for value in sizes]

next_same_direction = [-1] * len(prices)
index = 0
while index < len(prices) - 1:
    candidate = index + 1
    limit = min(len(prices), index + 101)
    while candidate < limit and directions[candidate] != directions[index]:
        candidate = candidate + 1
    if candidate < limit and times[candidate] > times[index]:
        next_same_direction[index] = candidate
    index = index + 1

evaluation_indexes = [
    index
    for index in range(calibration_count, len(prices))
    if next_same_direction[index] >= 0
]
evaluation_labels = [
    prices[next_same_direction[index]] - prices[index] for index in evaluation_indexes
]
buy_indexes = [index for index in evaluation_indexes if directions[index] > 0]
buy_labels = [
    prices[next_same_direction[index]] - prices[index] for index in buy_indexes
]
sell_indexes = [index for index in evaluation_indexes if directions[index] < 0]
sell_labels = [
    prices[next_same_direction[index]] - prices[index] for index in sell_indexes
]

price_changes = [prices[index] - prices[index - 1] for index in range(1, len(prices))]
future_20_indexes = [
    index
    for index in range(50, len(prices) - 20)
    if times[index + 20] > times[index]
]
future_20_returns = [prices[index + 20] - prices[index] for index in future_20_indexes]
levels = [prices[index] for index in future_20_indexes]
rolling_deviations = [
    prices[index] - mean(prices[index - 49 : index + 1]) for index in future_20_indexes
]
bounded_variance_states = [
    prices[index] * (1.0 - prices[index]) for index in future_20_indexes
]

fractional_results = []
for order in (0.25, 0.5, 0.75):
    transformed = fractional_series(prices, order, 50)
    signals = [transformed[index] for index in future_20_indexes]
    midpoint = len(signals) // 2
    fractional_results = fractional_results + [
        {
            "order": order,
            "fixed_width": 50,
            "signal_future_20_return_correlation": correlation(
                signals, future_20_returns
            ),
            "first_half_correlation": correlation(
                signals[:midpoint], future_20_returns[:midpoint]
            ),
            "second_half_correlation": correlation(
                signals[midpoint:], future_20_returns[midpoint:]
            ),
        }
    ]

result = structured_return(
    "Tested within-direction size and bounded-price transform diagnostics on one registered tape.",
    {
        "fill_count": len(prices),
        "unique_fill_count": len(set(fill_ids)),
        "calibration_fill_count": calibration_count,
        "early_size_95_percent_cap": size_cap,
        "same_direction_within_100_fills": {
            "all": [
                summarize_size(
                    "raw_size", evaluation_indexes, evaluation_labels, sizes
                ),
                summarize_size(
                    "square_root_size",
                    evaluation_indexes,
                    evaluation_labels,
                    square_root_sizes,
                ),
                summarize_size(
                    "early_winsorized_size",
                    evaluation_indexes,
                    evaluation_labels,
                    capped_sizes,
                ),
            ],
            "buys": summarize_size("buy_raw_size", buy_indexes, buy_labels, sizes),
            "sells": summarize_size("sell_raw_size", sell_indexes, sell_labels, sizes),
        },
        "price_dynamics": {
            "one_fill_change_autocorrelation": correlation(
                price_changes[:-1], price_changes[1:]
            ),
            "level_future_20_return_correlation": correlation(
                levels, future_20_returns
            ),
            "rolling_50_deviation_future_20_return_correlation": correlation(
                rolling_deviations, future_20_returns
            ),
            "bounded_variance_state_future_20_return_correlation": correlation(
                bounded_variance_states, future_20_returns
            ),
            "fractional_fixed_width_diagnostics": fractional_results,
        },
        "price_regime_counts": {
            "below_0_05": sum(1 for value in prices if value < 0.05),
            "0_05_to_0_25": sum(
                1 for value in prices if value >= 0.05 and value < 0.25
            ),
            "0_25_to_0_75": sum(
                1 for value in prices if value >= 0.25 and value <= 0.75
            ),
            "above_0_75": sum(1 for value in prices if value > 0.75),
        },
    },
    warnings=[
        "EXPLORATORY only; no transform, size feature, or model was selected.",
        "The early segment sets a size cap but the remainder is not protected evidence.",
        "Same-direction matching is only a spread-mechanics diagnostic and has a 100-fill cap.",
        "Fractional orders and width are examples, not stationarity-tested or fold-selected values.",
        "Multiple diagnostics were inspected and all count as selection-exposed trials.",
    ],
)
