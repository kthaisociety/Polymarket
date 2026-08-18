markets = read("polymarket-development-outcomes", "market_id")
events = read("polymarket-development-outcomes", "event_id")
event_ordinals = read("polymarket-development-outcomes", "event_chronological_ordinal")
outcome_indices = read("polymarket-development-outcomes", "outcome_index")
outcome_tokens = read("polymarket-development-outcomes", "outcome_token")
open_times = read("polymarket-development-outcomes", "open_time_epoch_seconds")
close_times = read("polymarket-development-outcomes", "close_time_epoch_seconds")

target_event_ordinals = [10, 25, 40, 55, 70, 85, 100, 115, 130, 145]
seven_days_seconds = 7 * 24 * 60 * 60
selected = []

for target in target_event_ordinals:
    for index in range(len(markets)):
        if event_ordinals[index] == target:
            close_ts = int(close_times[index])
            open_ts = int(open_times[index])
            if float(open_ts) < open_times[index]:
                open_ts = open_ts + 1
            start_ts = close_ts - seven_days_seconds
            if open_ts > start_ts:
                start_ts = open_ts
            selected = selected + [
                {
                    "environment_id": "bdl-polymarket-production-readonly",
                    "market_id": markets[index],
                    "event_id": events[index],
                    "event_chronological_ordinal": target,
                    "outcome_index": outcome_indices[index],
                    "outcome_token": outcome_tokens[index],
                    "start_time_epoch_seconds": start_ts,
                    "end_time_epoch_seconds": close_ts,
                    "fidelity_minutes": 5,
                }
            ]
            break

result = structured_return(
    "Exact development-only CLOB measurement-expansion manifest.",
    {
        "schema_version": "polymarket-fixed-clob-measurement-manifest/v1",
        "target_event_ordinals": target_event_ordinals,
        "selected_count": len(selected),
        "selected": selected,
    },
    warnings=[
        "Outcome index and token are copied from retained server contract identity.",
        "Each window is capped at the final seven days before recorded close and begins no earlier than open.",
        "Five-minute CLOB history values will remain sampled probabilities, not trades or quotes.",
        "This manifest contains no probability, payout, ancestor, or protected value.",
        "Missing target ordinals remain missing and cannot be replaced after inspection.",
    ],
)
