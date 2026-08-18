hourly_markets = read("polymarket-development-prices", "market_id")
hourly_times = read("polymarket-development-prices", "observed_at_epoch_seconds")
hourly_probabilities = read("polymarket-development-prices", "market_probability")

view_ids = [
    "polymarket-clob-five-minute-event-010",
    "polymarket-clob-five-minute-event-025",
    "polymarket-clob-five-minute-event-040",
    "polymarket-clob-five-minute-event-055",
    "polymarket-clob-five-minute-event-070",
    "polymarket-clob-five-minute-event-085",
    "polymarket-clob-five-minute-event-100",
    "polymarket-clob-five-minute-event-115",
    "polymarket-clob-five-minute-event-130",
    "polymarket-clob-five-minute-event-145",
]


def safe_rate(numerator, denominator):
    if denominator == 0:
        return None
    return numerator / denominator


def variance(values):
    if len(values) == 0:
        return None
    mean = sum(values) / len(values)
    squared = 0.0
    for value in values:
        centered = value - mean
        squared = squared + centered * centered
    return squared / len(values)


def quiet_band(seconds):
    if seconds == 0.0:
        return 0
    if seconds <= 7200.0:
        return 1
    if seconds < 86400.0:
        return 2
    return 3


def summarize(paths, nominal_seconds, horizon_hours):
    changes = []
    interior_count = 0
    interior_zero = 0
    zero_count = 0
    quiet_count = [0, 0, 0, 0]
    quiet_move = [0, 0, 0, 0]
    quiet_absolute = [0.0, 0.0, 0.0, 0.0]
    nonzero_count = 0
    nonzero_reversal = 0
    adjacent_count = 0
    adjacent_reversal = 0
    grid_nonzero_count = 0
    grid_mill_count = 0
    horizon_values = [[] for unused in horizon_hours]
    path_rows = []
    order_break_count = 0

    for path in paths:
        times = path["times"]
        probabilities = path["probabilities"]
        path_change_count = 0
        path_zero_count = 0
        prior_nonzero_sign = 0
        previous_regular_change = 0.0
        quiet_seconds = 0.0
        for row in range(1, len(probabilities)):
            elapsed = times[row] - times[row - 1]
            if elapsed <= 0.0:
                order_break_count = order_break_count + 1
            if elapsed >= 0.8 * nominal_seconds and elapsed <= 1.2 * nominal_seconds:
                change = probabilities[row] - probabilities[row - 1]
                changes = changes + [change]
                path_change_count = path_change_count + 1
                if change == 0.0:
                    zero_count = zero_count + 1
                    path_zero_count = path_zero_count + 1
                if probabilities[row - 1] > 0.02 and probabilities[row - 1] < 0.98:
                    interior_count = interior_count + 1
                    if change == 0.0:
                        interior_zero = interior_zero + 1
                band = quiet_band(quiet_seconds)
                quiet_count[band] = quiet_count[band] + 1
                quiet_absolute[band] = quiet_absolute[band] + abs(change)
                if change != 0.0:
                    quiet_move[band] = quiet_move[band] + 1
                    sign = 1
                    if change < 0.0:
                        sign = -1
                    if prior_nonzero_sign != 0:
                        nonzero_count = nonzero_count + 1
                        if sign != prior_nonzero_sign:
                            nonzero_reversal = nonzero_reversal + 1
                    prior_nonzero_sign = sign
                    if previous_regular_change != 0.0:
                        adjacent_count = adjacent_count + 1
                        if previous_regular_change * change < 0.0:
                            adjacent_reversal = adjacent_reversal + 1
                    grid_nonzero_count = grid_nonzero_count + 1
                    scaled = change * 1000.0
                    if abs(scaled - round(scaled)) < 0.00000001:
                        grid_mill_count = grid_mill_count + 1
                    quiet_seconds = 0.0
                else:
                    quiet_seconds = quiet_seconds + elapsed
                previous_regular_change = change
            else:
                quiet_seconds = 0.0
                previous_regular_change = 0.0

        for horizon_position in range(len(horizon_hours)):
            steps = int(horizon_hours[horizon_position] * 3600.0 / nominal_seconds)
            for row in range(steps, len(probabilities)):
                elapsed = times[row] - times[row - steps]
                target = horizon_hours[horizon_position] * 3600.0
                if elapsed >= 0.8 * target and elapsed <= 1.2 * target:
                    horizon_values[horizon_position] = horizon_values[horizon_position] + [
                        probabilities[row] - probabilities[row - steps]
                    ]
        path_rows = path_rows + [
            {
                "market_id": path["market_id"],
                "observation_count": len(probabilities),
                "regular_increment_count": path_change_count,
                "regular_zero_rate": safe_rate(path_zero_count, path_change_count),
                "first_time": times[0],
                "last_time": times[-1],
            }
        ]

    base_variance = variance(changes)
    centered_fourth = 0.0
    kurtosis = None
    if len(changes) > 0 and base_variance is not None and base_variance > 0.0:
        mean_change = sum(changes) / len(changes)
        for change in changes:
            centered = change - mean_change
            centered_fourth = centered_fourth + centered * centered * centered * centered
        kurtosis = centered_fourth / len(changes) / (base_variance * base_variance)

    variance_rows = []
    for horizon_position in range(len(horizon_hours)):
        horizon = horizon_hours[horizon_position]
        horizon_variance = variance(horizon_values[horizon_position])
        steps = horizon * 3600.0 / nominal_seconds
        ratio = None
        if base_variance is not None and base_variance > 0.0 and horizon_variance is not None:
            ratio = horizon_variance / (steps * base_variance)
        variance_rows = variance_rows + [
            {
                "horizon_hours": horizon,
                "count": len(horizon_values[horizon_position]),
                "variance_ratio": ratio,
            }
        ]

    quiet_rows = []
    quiet_labels = ["quiet_0", "quiet_le_2h", "quiet_2h_24h", "quiet_24h_plus"]
    for band in range(4):
        quiet_rows = quiet_rows + [
            {
                "band": quiet_labels[band],
                "count": quiet_count[band],
                "next_move_rate": safe_rate(quiet_move[band], quiet_count[band]),
                "mean_absolute_change": safe_rate(quiet_absolute[band], quiet_count[band]),
            }
        ]

    return {
        "path_count": len(paths),
        "observation_count": sum([len(path["probabilities"]) for path in paths]),
        "regular_increment_count": len(changes),
        "regular_zero_rate": safe_rate(zero_count, len(changes)),
        "regular_interior_zero_rate": safe_rate(interior_zero, interior_count),
        "regular_increment_kurtosis": kurtosis,
        "nonzero_sign_reversal_rate": safe_rate(nonzero_reversal, nonzero_count),
        "adjacent_nonzero_sign_reversal_rate": safe_rate(adjacent_reversal, adjacent_count),
        "nonzero_mill_grid_share": safe_rate(grid_mill_count, grid_nonzero_count),
        "quiet_elapsed_bands": quiet_rows,
        "variance_scaling": variance_rows,
        "path_rows": path_rows,
        "order_break_count": order_break_count,
    }


five_minute_paths = []
selected_market_ids = []
identity_break_count = 0
for view_id in view_ids:
    markets = read(view_id, "market_id")
    events = read(view_id, "event_id")
    fidelities = read(view_id, "fidelity_minutes")
    times = read(view_id, "reference_time_epoch_seconds")
    available_times = read(view_id, "available_at_epoch_seconds")
    probabilities = read(view_id, "market_probability")
    if (
        len(markets) != len(times)
        or len(events) != len(times)
        or len(fidelities) != len(times)
        or len(available_times) != len(times)
        or len(probabilities) != len(times)
        or len(times) == 0
    ):
        identity_break_count = identity_break_count + 1
    else:
        market_id = markets[0]
        event_id = events[0]
        for row in range(len(times)):
            if (
                markets[row] != market_id
                or events[row] != event_id
                or fidelities[row] != "5"
                or available_times[row] != times[row]
            ):
                identity_break_count = identity_break_count + 1
        selected_market_ids = selected_market_ids + [market_id]
        five_minute_paths = five_minute_paths + [
            {
                "market_id": market_id,
                "event_id": event_id,
                "times": list(times),
                "probabilities": list(probabilities),
            }
        ]

hourly_paths = []
for five_path in five_minute_paths:
    market_id = five_path["market_id"]
    first_time = five_path["times"][0]
    last_time = five_path["times"][-1]
    selected_times = []
    selected_probabilities = []
    for row in range(len(hourly_markets)):
        if (
            hourly_markets[row] == market_id
            and hourly_times[row] >= first_time
            and hourly_times[row] <= last_time
        ):
            selected_times = selected_times + [hourly_times[row]]
            selected_probabilities = selected_probabilities + [hourly_probabilities[row]]
    hourly_paths = hourly_paths + [
        {
            "market_id": market_id,
            "times": selected_times,
            "probabilities": selected_probabilities,
        }
    ]

match_count = 0
match_eligible_count = 0
exact_match_count = 0
within_one_cent_count = 0
absolute_discrepancy = 0.0
market_alignment = []
for path_position in range(len(five_minute_paths)):
    five_path = five_minute_paths[path_position]
    hourly_path = hourly_paths[path_position]
    five_times = five_path["times"]
    five_probabilities = five_path["probabilities"]
    aligned = 0
    aligned_absolute = 0.0
    cursor = 0
    for hourly_row in range(len(hourly_path["times"])):
        target_time = hourly_path["times"][hourly_row]
        match_eligible_count = match_eligible_count + 1
        while cursor + 1 < len(five_times) and abs(five_times[cursor + 1] - target_time) <= abs(
            five_times[cursor] - target_time
        ):
            cursor = cursor + 1
        distance = abs(five_times[cursor] - target_time)
        if distance <= 600.0:
            discrepancy = abs(five_probabilities[cursor] - hourly_path["probabilities"][hourly_row])
            match_count = match_count + 1
            aligned = aligned + 1
            absolute_discrepancy = absolute_discrepancy + discrepancy
            aligned_absolute = aligned_absolute + discrepancy
            if discrepancy < 0.000000000001:
                exact_match_count = exact_match_count + 1
            if discrepancy <= 0.01:
                within_one_cent_count = within_one_cent_count + 1
    market_alignment = market_alignment + [
        {
            "market_id": five_path["market_id"],
            "hourly_observation_count": len(hourly_path["times"]),
            "matched_count": aligned,
            "mean_absolute_discrepancy": safe_rate(aligned_absolute, aligned),
        }
    ]

five_summary = summarize(five_minute_paths, 300.0, [1.0, 4.0, 24.0])
hourly_summary = summarize(hourly_paths, 3600.0, [1.0, 4.0, 24.0])
five_quiet = five_summary["quiet_elapsed_bands"]
five_variance = five_summary["variance_scaling"]

alignment_coverage = safe_rate(match_count, match_eligible_count)
alignment_mae = safe_rate(absolute_discrepancy, match_count)
alignment_within_one_cent = safe_rate(within_one_cent_count, match_count)
measurement_alignment_gate = (
    alignment_coverage is not None
    and alignment_mae is not None
    and alignment_within_one_cent is not None
    and alignment_coverage >= 0.80
    and alignment_mae <= 0.01
    and alignment_within_one_cent >= 0.90
)
sticky_gate = (
    five_summary["regular_interior_zero_rate"] is not None
    and five_summary["regular_interior_zero_rate"] >= 0.50
)
duration_gate = (
    five_quiet[0]["next_move_rate"] is not None
    and five_quiet[3]["next_move_rate"] is not None
    and five_quiet[3]["next_move_rate"] <= 0.50 * five_quiet[0]["next_move_rate"]
)
subdiffusion_gate = (
    five_variance[2]["variance_ratio"] is not None
    and five_variance[2]["variance_ratio"] < 0.75
)
reversal_gate = (
    five_summary["nonzero_sign_reversal_rate"] is not None
    and five_summary["nonzero_sign_reversal_rate"] > 0.55
)

result = structured_return(
    "Fixed five-minute measurement falsifier for registered Polymarket probability samples.",
    {
        "schema_version": "polymarket-five-minute-measurement-falsifier/v1",
        "identity_break_count": identity_break_count,
        "selected_market_count": len(selected_market_ids),
        "five_minute": five_summary,
        "same_window_hourly": hourly_summary,
        "cross_source_alignment": {
            "eligible_hourly_count": match_eligible_count,
            "matched_count": match_count,
            "coverage": alignment_coverage,
            "mean_absolute_discrepancy": alignment_mae,
            "exact_match_rate": safe_rate(exact_match_count, match_count),
            "within_one_cent_rate": alignment_within_one_cent,
            "market_rows": market_alignment,
        },
        "predeclared_checks": {
            "measurement_alignment_gate": measurement_alignment_gate,
            "five_minute_sticky_gate": sticky_gate,
            "elapsed_duration_dependence_gate": duration_gate,
            "five_minute_24h_subdiffusion_gate": subdiffusion_gate,
            "five_minute_nonzero_reversal_gate": reversal_gate,
        },
        "protected_values_exposed": False,
    },
    warnings=[
        "Both series are sampled probabilities, not trades, quotes, or executable returns.",
        "The ten markets were fixed by development event ordinals before any five-minute value was read.",
        "Five-minute endpoint timestamps are treated as available at their documented sample time.",
        "Variance ratios are overlapping descriptive estimands and are not IID test statistics.",
        "Hourly/five-minute matching uses the nearest five-minute sample within a fixed ten-minute tolerance.",
        "Exact zeros and cross-source discrepancies may reflect sampling mechanics as well as economics.",
        "The measurement panel is deliberately small and cannot establish population-wide prevalence.",
        "Ancestor and protected events remain unavailable.",
    ],
)
