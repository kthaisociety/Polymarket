price_markets = read("polymarket-development-prices", "market_id")
price_events = read("polymarket-development-prices", "event_id")
ordinals = read("polymarket-development-prices", "observation_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")
outcome_markets = read("polymarket-development-outcomes", "market_id")
outcome_events = read("polymarket-development-outcomes", "event_id")
questions = read("polymarket-development-outcomes", "question")
post_events = read("polymarket-xtracker-posts", "event_id")
post_reference_times = read("polymarket-xtracker-posts", "reference_time_epoch_seconds")
post_available_times = read("polymarket-xtracker-posts", "available_at_epoch_seconds")
post_values = read("polymarket-xtracker-posts", "post_imported")


def solve_linear(matrix, vector):
    size = len(vector)
    augmented = [None for unused in range(size)]
    for row in range(size):
        augmented[row] = [0.0 for unused in range(size + 1)]
        for column in range(size):
            augmented[row][column] = matrix[row][column]
        augmented[row][size] = vector[row]
    for pivot in range(size):
        best = pivot
        for row in range(pivot + 1, size):
            if abs(augmented[row][pivot]) > abs(augmented[best][pivot]):
                best = row
        if best != pivot:
            temporary = augmented[pivot]
            augmented[pivot] = augmented[best]
            augmented[best] = temporary
        divisor = augmented[pivot][pivot]
        if abs(divisor) < 0.000000000001:
            divisor = 0.000000000001
        for column in range(pivot, size + 1):
            augmented[pivot][column] = augmented[pivot][column] / divisor
        for row in range(size):
            if row != pivot:
                factor = augmented[row][pivot]
                for column in range(pivot, size + 1):
                    augmented[row][column] = (
                        augmented[row][column] - factor * augmented[pivot][column]
                    )
    return [augmented[row][size] for row in range(size)]


def fit_ridge(rows, feature_indices, penalty):
    count = len(rows)
    means = [0.0 for unused in feature_indices]
    target_mean = 0.0
    for row in rows:
        target_mean = target_mean + row[1]
        for position in range(len(feature_indices)):
            means[position] = means[position] + row[0][feature_indices[position]]
    target_mean = target_mean / count
    for position in range(len(feature_indices)):
        means[position] = means[position] / count
    scales = [0.0 for unused in feature_indices]
    for row in rows:
        for position in range(len(feature_indices)):
            centered = row[0][feature_indices[position]] - means[position]
            scales[position] = scales[position] + centered * centered
    for position in range(len(feature_indices)):
        scales[position] = (scales[position] / count + 0.000000000001) ** 0.5
    matrix = [None for unused in feature_indices]
    vector = [0.0 for unused in feature_indices]
    for left in range(len(feature_indices)):
        matrix[left] = [0.0 for unused in feature_indices]
    for row in rows:
        centered_target = row[1] - target_mean
        standardized = [0.0 for unused in feature_indices]
        for position in range(len(feature_indices)):
            standardized[position] = (
                row[0][feature_indices[position]] - means[position]
            ) / scales[position]
        for left in range(len(feature_indices)):
            vector[left] = vector[left] + standardized[left] * centered_target / count
            for right in range(len(feature_indices)):
                matrix[left][right] = (
                    matrix[left][right]
                    + standardized[left] * standardized[right] / count
                )
    for position in range(len(feature_indices)):
        matrix[position][position] = matrix[position][position] + penalty
    return [target_mean, means, scales, solve_linear(matrix, vector)]


def predict(model, feature_indices, features):
    value = model[0]
    for position in range(len(feature_indices)):
        value = value + model[3][position] * (
            features[feature_indices[position]] - model[1][position]
        ) / model[2][position]
    return value


event_id = "739241"
event_start = 1784995200.0
event_end = 1785167999.0
brackets = {
    "0x3ec2637fafd87b6d76f018cee6fe427bbcab164004ec81188a25c60de1889425": [65.0, 89.0],
    "0x69f0ec6e689cf7518893e9425d8ba104388b0ce2eada921c110de99bebb0e2a4": [190.0, 214.0],
    "0x8824f757cdfc6ff8ea70636997b37643d2e0b116d15bd61e6d2c372c5fb43bf6": [165.0, 189.0],
    "0x984fd44390f962b373176e05f053a9de2c14f7176cdb151a31a5652fe9463653": [140.0, 164.0],
    "0xa24ae1637db1f30a53b473f902e6110582bdcf2278d7eb77f7c5e5964b8dc517": [240.0, 999.0],
    "0xb2ca922766c388ebb31e42b3a2620406ad55f931a4859a3b2e3f7013abc8362d": [90.0, 114.0],
    "0xcabde8986b23dd57c3c818f606953db401456e377218c9aceee8a2743574dbb7": [115.0, 139.0],
    "0xff12ede179a367f20b039b65f67d19b741b79babf8c86152085f995b42e63ca2": [215.0, 239.0],
    "0xed748245068e2d6874733ff72a3f44f2efb9086480c0a7f5809a5085a1078f6d": [40.0, 64.0],
}

event_market_count = 0
for row in range(len(outcome_markets)):
    if outcome_events[row] == event_id:
        event_market_count = event_market_count + 1
        assert outcome_markets[row] in brackets
        assert len(questions[row]) > 0
assert event_market_count == len(brackets)
assert len(post_events) == len(post_available_times)
assert len(post_events) == len(post_reference_times)
assert len(post_events) == len(post_values)
assert len(post_events) > 0
for row in range(len(post_events)):
    assert post_events[row] == event_id
    assert post_reference_times[row] <= post_available_times[row]
    assert post_values[row] == 1

points = {}
market_lengths = {}
for row in range(len(price_markets)):
    if price_events[row] == event_id:
        market = price_markets[row]
        points[(market, ordinals[row])] = [times[row], probabilities[row]]
        if market not in market_lengths:
            market_lengths[market] = 0
        market_lengths[market] = max(market_lengths[market], ordinals[row] + 1)
assert len(market_lengths) == len(brackets)

samples_by_block = {}
excluded_windows = 0
for block in range(1, 7):
    target_time = event_start + block * 21600.0
    rows = []
    for market in brackets:
        best_ordinal = -1
        best_gap = 999999.0
        for ordinal in range(market_lengths[market]):
            point_time = points[(market, ordinal)][0]
            gap = abs(point_time - target_time)
            if gap < best_gap:
                best_gap = gap
                best_ordinal = ordinal
        if best_ordinal < 6 or best_ordinal + 6 >= market_lengths[market]:
            excluded_windows = excluded_windows + 1
        else:
            current = points[(market, best_ordinal)]
            trailing = points[(market, best_ordinal - 6)]
            future = points[(market, best_ordinal + 6)]
            trailing_hours = (current[0] - trailing[0]) / 3600.0
            future_hours = (future[0] - current[0]) / 3600.0
            if (
                best_gap > 2700.0
                or trailing_hours < 4.5
                or trailing_hours > 7.5
                or future_hours < 4.5
                or future_hours > 7.5
            ):
                excluded_windows = excluded_windows + 1
            else:
                count = 0.0
                recent1 = 0.0
                recent3 = 0.0
                recent6 = 0.0
                for post in range(len(post_available_times)):
                    available = post_available_times[post]
                    if available <= current[0]:
                        count = count + post_values[post]
                        if available > current[0] - 3600.0:
                            recent1 = recent1 + post_values[post]
                        if available > current[0] - 10800.0:
                            recent3 = recent3 + post_values[post]
                        if available > current[0] - 21600.0:
                            recent6 = recent6 + post_values[post]
                elapsed = max(1.0, (current[0] - event_start) / 3600.0)
                remaining = max(1.0, (event_end - current[0]) / 3600.0)
                projected_linear = count * 48.0 / elapsed
                projected_recent = count + recent6 * remaining / 6.0
                lower = brackets[market][0]
                upper = brackets[market][1]
                capped_upper = min(264.0, upper)
                gap_linear = 0.0
                gap_recent = 0.0
                if projected_linear < lower:
                    gap_linear = lower - projected_linear
                if projected_linear > upper:
                    gap_linear = projected_linear - upper
                if projected_recent < lower:
                    gap_recent = lower - projected_recent
                if projected_recent > upper:
                    gap_recent = projected_recent - upper
                eliminated = 1.0 if count > upper else 0.0
                required_rate = max(0.0, lower - count) / remaining
                probability = current[1]
                change6 = probability - trailing[1]
                rv6 = 0.0
                zero_count = 0.0
                for ordinal in range(best_ordinal - 5, best_ordinal + 1):
                    step = points[(market, ordinal)][1] - points[(market, ordinal - 1)][1]
                    rv6 = rv6 + step * step
                    if step == 0.0:
                        zero_count = zero_count + 1.0
                features = [
                    probability,
                    min(probability, 1.0 - probability),
                    change6,
                    rv6,
                    zero_count / 6.0,
                    lower / 264.0,
                    capped_upper / 264.0,
                    count / 264.0,
                    recent1 / 20.0,
                    recent3 / 40.0,
                    recent6 / 80.0,
                    projected_linear / 264.0,
                    projected_recent / 264.0,
                    gap_linear / 264.0,
                    gap_recent / 264.0,
                    eliminated,
                    required_rate / 20.0,
                ]
                rows = rows + [[features, future[1] - probability, market, current[0]]]
    samples_by_block[block] = rows

baseline_indices = [0, 1, 2, 3, 4, 5, 6]
external_indices = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
baseline_squared = []
external_squared = []
zero_squared = []
block_metrics = []
baseline_wins = 0
zero_wins = 0
for test_block in range(3, 7):
    training = []
    test_time = event_start + test_block * 21600.0
    for train_block in range(1, test_block):
        for row in samples_by_block[train_block]:
            if row[3] + 27000.0 <= test_time:
                training = training + [row]
    assert len(training) >= 8
    baseline_model = fit_ridge(training, baseline_indices, 0.1)
    external_model = fit_ridge(training, external_indices, 0.1)
    block_baseline = 0.0
    block_external = 0.0
    block_zero = 0.0
    block_count = 0
    for row in samples_by_block[test_block]:
        actual = row[1]
        baseline_prediction = predict(baseline_model, baseline_indices, row[0])
        external_prediction = predict(external_model, external_indices, row[0])
        baseline_error = (actual - baseline_prediction) ** 2
        external_error = (actual - external_prediction) ** 2
        zero_error = actual * actual
        baseline_squared = baseline_squared + [baseline_error]
        external_squared = external_squared + [external_error]
        zero_squared = zero_squared + [zero_error]
        block_baseline = block_baseline + baseline_error
        block_external = block_external + external_error
        block_zero = block_zero + zero_error
        block_count = block_count + 1
    block_baseline = block_baseline / block_count
    block_external = block_external / block_count
    block_zero = block_zero / block_count
    if block_external < block_baseline:
        baseline_wins = baseline_wins + 1
    if block_external < block_zero:
        zero_wins = zero_wins + 1
    block_metrics = block_metrics + [
        {
            "block": test_block,
            "row_count": block_count,
            "baseline_mse": block_baseline,
            "external_mse": block_external,
            "zero_change_mse": block_zero,
        }
    ]

baseline_mse = sum(baseline_squared) / len(baseline_squared)
external_mse = sum(external_squared) / len(external_squared)
zero_mse = sum(zero_squared) / len(zero_squared)
baseline_macro = sum(row["baseline_mse"] for row in block_metrics) / len(block_metrics)
external_macro = sum(row["external_mse"] for row in block_metrics) / len(block_metrics)
zero_macro = sum(row["zero_change_mse"] for row in block_metrics) / len(block_metrics)
passed = (
    external_mse <= 0.9 * baseline_mse
    and external_macro <= 0.9 * baseline_macro
    and external_mse < zero_mse
    and external_macro < zero_macro
    and baseline_wins >= 3
    and zero_wins >= 3
)

result = structured_return(
    "XTracker incremental six-hour trial completed under imported-at availability.",
    {
        "schema_version": "polymarket-xtracker-incremental-trial/v1",
        "event_id": event_id,
        "market_count": len(brackets),
        "registered_post_count": len(post_events),
        "decision_block_count": len(samples_by_block),
        "test_block_count": len(block_metrics),
        "test_row_count": len(external_squared),
        "excluded_windows": excluded_windows,
        "baseline_model": "fixed-ridge-0.1-target-path-and-static-bracket",
        "external_model": "fixed-ridge-0.1-plus-imported-count-pace-and-bracket-gap",
        "label": "six-hour-sampled-probability-change",
        "baseline_observation_mse": baseline_mse,
        "external_observation_mse": external_mse,
        "zero_change_observation_mse": zero_mse,
        "baseline_block_macro_mse": baseline_macro,
        "external_block_macro_mse": external_macro,
        "zero_change_block_macro_mse": zero_macro,
        "external_wins_vs_baseline": baseline_wins,
        "external_wins_vs_zero": zero_wins,
        "block_metrics": block_metrics,
        "predeclared_replication_gate_passed": passed,
        "protected_values_exposed": False,
        "claim_scope": "single-development-event-replication-candidate-only",
    },
)
