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


def summarize_clock(name, closes, flows, absolute_sizes, counts, durations):
    signals = [
        flow / absolute_size if absolute_size > 0.0 else 0.0
        for flow, absolute_size in zip(flows[:-1], absolute_sizes[:-1])
    ]
    labels = [closes[index + 1] - closes[index] for index in range(len(closes) - 1)]
    ordered = sorted(zip(signals, labels))
    fifth = max(1, len(ordered) // 5)
    midpoint = len(labels) // 2
    return {
        "name": name,
        "bucket_count": len(closes),
        "comparison_count": len(labels),
        "mean_fills_per_bucket": mean(counts),
        "mean_duration_seconds": mean(durations),
        "flow_imbalance_next_bucket_return_correlation": correlation(signals, labels),
        "first_half_correlation": correlation(signals[:midpoint], labels[:midpoint]),
        "second_half_correlation": correlation(signals[midpoint:], labels[midpoint:]),
        "bottom_flow_fifth_next_return": mean([pair[1] for pair in ordered[:fifth]]),
        "top_flow_fifth_next_return": mean([pair[1] for pair in ordered[-fifth:]]),
        "zero_next_return_fraction": sum(1 for value in labels if value == 0.0)
        / len(labels),
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

trade_closes = []
trade_flows = []
trade_sizes = []
trade_counts = []
trade_durations = []
trade_bucket_size = 50
start = 0
while start + trade_bucket_size <= len(prices):
    end = start + trade_bucket_size
    trade_closes = trade_closes + [prices[end - 1]]
    trade_flows = trade_flows + [sum(signed_yes_flow[start:end])]
    trade_sizes = trade_sizes + [sum(absolute_sizes[start:end])]
    trade_counts = trade_counts + [trade_bucket_size]
    trade_durations = trade_durations + [times[end - 1] - times[start]]
    start = end

time_closes = []
time_flows = []
time_sizes = []
time_counts = []
time_durations = []
time_seconds = 900.0
bucket_start = 0
index = 1
while index <= len(prices):
    boundary = index == len(prices)
    if not boundary:
        boundary = int((times[index] - times[0]) // time_seconds) != int(
            (times[bucket_start] - times[0]) // time_seconds
        )
    if boundary:
        time_closes = time_closes + [prices[index - 1]]
        time_flows = time_flows + [sum(signed_yes_flow[bucket_start:index])]
        time_sizes = time_sizes + [sum(absolute_sizes[bucket_start:index])]
        time_counts = time_counts + [index - bucket_start]
        time_durations = time_durations + [times[index - 1] - times[bucket_start]]
        bucket_start = index
    index = index + 1

calibration_count = max(100, len(prices) // 5)
size_threshold = mean(absolute_sizes[:calibration_count]) * trade_bucket_size
size_closes = []
size_flows = []
size_totals = []
size_counts = []
size_durations = []
bucket_start = 0
running_size = 0.0
index = 0
while index < len(prices):
    running_size = running_size + absolute_sizes[index]
    if running_size >= size_threshold:
        size_closes = size_closes + [prices[index]]
        size_flows = size_flows + [sum(signed_yes_flow[bucket_start : index + 1])]
        size_totals = size_totals + [running_size]
        size_counts = size_counts + [index - bucket_start + 1]
        size_durations = size_durations + [times[index] - times[bucket_start]]
        bucket_start = index + 1
        running_size = 0.0
    index = index + 1

rolling_20_imbalance = []
for index in range(len(prices)):
    start = max(0, index - 19)
    flow = sum(signed_yes_flow[start : index + 1])
    size = sum(absolute_sizes[start : index + 1])
    rolling_20_imbalance = rolling_20_imbalance + [flow / size if size > 0.0 else 0.0]

imbalance_event_indexes = [
    index
    for index in range(20, len(prices) - 20)
    if abs(rolling_20_imbalance[index]) >= 0.8
    and abs(rolling_20_imbalance[index - 1]) < 0.8
    and times[index + 20] > times[index]
]
imbalance_signals = [rolling_20_imbalance[index] for index in imbalance_event_indexes]
imbalance_labels = [prices[index + 20] - prices[index] for index in imbalance_event_indexes]

run_event_indexes = []
run_length = 1
for index in range(1, len(prices) - 20):
    if directions[index] == directions[index - 1]:
        run_length = run_length + 1
    else:
        run_length = 1
    if run_length == 5 and times[index + 20] > times[index]:
        run_event_indexes = run_event_indexes + [index]
run_signals = [directions[index] for index in run_event_indexes]
run_labels = [prices[index + 20] - prices[index] for index in run_event_indexes]

result = structured_return(
    "Compared activity clocks and event-triggered flow diagnostics on one registered tape.",
    {
        "fill_count": len(prices),
        "unique_fill_count": len(set(fill_ids)),
        "coverage_epoch_seconds": [min(times), max(times)],
        "clock_results": [
            summarize_clock(
                "non_overlapping_50_fill_buckets",
                trade_closes,
                trade_flows,
                trade_sizes,
                trade_counts,
                trade_durations,
            ),
            summarize_clock(
                "nonempty_15_minute_buckets",
                time_closes,
                time_flows,
                time_sizes,
                time_counts,
                time_durations,
            ),
            summarize_clock(
                "early_calibrated_size_buckets",
                size_closes,
                size_flows,
                size_totals,
                size_counts,
                size_durations,
            ),
        ],
        "size_bucket_calibration_fill_count": calibration_count,
        "size_bucket_threshold": size_threshold,
        "imbalance_crossing": {
            "threshold": 0.8,
            "rolling_fills": 20,
            "future_fills": 20,
            "event_count": len(imbalance_labels),
            "signal_future_return_correlation": correlation(
                imbalance_signals, imbalance_labels
            ),
            "positive_event_mean_return": mean(
                [
                    label
                    for signal, label in zip(imbalance_signals, imbalance_labels)
                    if signal > 0.0
                ]
            ),
            "negative_event_mean_return": mean(
                [
                    label
                    for signal, label in zip(imbalance_signals, imbalance_labels)
                    if signal < 0.0
                ]
            ),
        },
        "five_fill_aggressor_runs": {
            "event_count": len(run_labels),
            "direction_future_return_correlation": correlation(run_signals, run_labels),
            "positive_run_mean_return": mean(
                [label for signal, label in zip(run_signals, run_labels) if signal > 0]
            ),
            "negative_run_mean_return": mean(
                [label for signal, label in zip(run_signals, run_labels) if signal < 0]
            ),
        },
    },
    warnings=[
        "EXPLORATORY only; activity clocks are alternative views, not selected features.",
        "The size-bucket threshold uses only the first fifth of the tape but is not fold validation.",
        "Imbalance and run thresholds were fixed for this probe and still count as inspected trials.",
        "Transaction-price changes remain exposed to aggressor-direction and spread mechanics.",
    ],
)
