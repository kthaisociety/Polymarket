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


def direction_path(name, values):
    changes = [values[index] - values[index - 1] for index in range(1, len(values))]
    indexes = range(50, len(values) - 20)
    deviations = [
        values[index] - mean(values[index - 49 : index + 1]) for index in indexes
    ]
    future_returns = [values[index + 20] - values[index] for index in indexes]
    midpoint = len(future_returns) // 2
    return {
        "name": name,
        "fill_count": len(values),
        "one_step_change_autocorrelation": correlation(changes[:-1], changes[1:]),
        "rolling_50_deviation_future_20_same_direction_return_correlation": correlation(
            deviations, future_returns
        ),
        "first_half_deviation_correlation": correlation(
            deviations[:midpoint], future_returns[:midpoint]
        ),
        "second_half_deviation_correlation": correlation(
            deviations[midpoint:], future_returns[midpoint:]
        ),
    }


def neutral_bucket_summary(interval_seconds):
    neutral_prices = []
    imbalances = []
    counts = []
    bucket_ids = []
    bucket_start = 0
    index = 1
    while index <= len(prices):
        boundary = index == len(prices)
        if not boundary:
            boundary = int((times[index] - times[0]) // interval_seconds) != int(
                (times[bucket_start] - times[0]) // interval_seconds
            )
        if boundary:
            buy_values = [
                prices[position]
                for position in range(bucket_start, index)
                if directions[position] > 0
            ]
            sell_values = [
                prices[position]
                for position in range(bucket_start, index)
                if directions[position] < 0
            ]
            total_size = sum(absolute_sizes[bucket_start:index])
            if len(buy_values) > 0 and len(sell_values) > 0 and total_size > 0.0:
                neutral_prices = neutral_prices + [
                    (mean(buy_values) + mean(sell_values)) / 2.0
                ]
                imbalances = imbalances + [
                    sum(signed_yes_flow[bucket_start:index]) / total_size
                ]
                counts = counts + [index - bucket_start]
                bucket_ids = bucket_ids + [
                    int((times[bucket_start] - times[0]) // interval_seconds)
                ]
            bucket_start = index
        index = index + 1
    labels = [
        neutral_prices[index + 1] - neutral_prices[index]
        for index in range(len(neutral_prices) - 1)
    ]
    signals = imbalances[:-1]
    ordered = sorted(zip(signals, labels))
    fifth = max(1, len(ordered) // 5)
    midpoint = len(labels) // 2
    return {
        "interval_seconds": interval_seconds,
        "two_sided_bucket_count": len(neutral_prices),
        "mean_fills_in_two_sided_bucket": mean(counts),
        "mean_gap_in_bucket_ids": mean(
            [bucket_ids[index + 1] - bucket_ids[index] for index in range(len(bucket_ids) - 1)]
        ),
        "imbalance_next_neutral_price_change_correlation": correlation(signals, labels),
        "first_half_correlation": correlation(signals[:midpoint], labels[:midpoint]),
        "second_half_correlation": correlation(signals[midpoint:], labels[midpoint:]),
        "bottom_imbalance_fifth_mean_change": mean(
            [pair[1] for pair in ordered[:fifth]]
        ),
        "top_imbalance_fifth_mean_change": mean(
            [pair[1] for pair in ordered[-fifth:]]
        ),
        "neutral_price_change_autocorrelation": correlation(labels[:-1], labels[1:]),
    }


prices = [
    price if outcome == 0 else 1.0 - price
    for price, outcome in zip(prices_raw, outcomes)
]
signed_yes_flow = [
    size if outcome == 0 else -size
    for size, outcome in zip(signed_sizes_raw, outcomes)
]
absolute_sizes = [abs(value) for value in signed_yes_flow]
directions = [1 if value > 0.0 else -1 for value in signed_yes_flow]
buy_prices = [price for price, direction in zip(prices, directions) if direction > 0]
sell_prices = [price for price, direction in zip(prices, directions) if direction < 0]

result = structured_return(
    "Controlled apparent reversal using separate aggressor paths and two-sided bucket prices.",
    {
        "fill_count": len(prices),
        "unique_fill_count": len(set(fill_ids)),
        "direction_paths": [
            direction_path("yes_equivalent_buys", buy_prices),
            direction_path("yes_equivalent_sells", sell_prices),
        ],
        "two_sided_bucket_controls": [
            neutral_bucket_summary(900.0),
            neutral_bucket_summary(3600.0),
        ],
    },
    warnings=[
        "EXPLORATORY only; the two-sided average is a transaction-price diagnostic, not a quote midpoint.",
        "Successive two-sided buckets may be separated by empty or one-sided intervals.",
        "Separate aggressor paths remove immediate side switching but not all execution mechanics.",
        "No formal feature, label, model, protected evidence, or memory update is produced.",
    ],
)
