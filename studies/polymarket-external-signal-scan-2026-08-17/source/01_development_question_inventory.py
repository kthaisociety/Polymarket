market_ids = read("polymarket-development-outcomes", "market_id")
event_ids = read("polymarket-development-outcomes", "event_id")
event_ordinals = read("polymarket-development-outcomes", "event_chronological_ordinal")
questions = read("polymarket-development-outcomes", "question")
outcome_labels = read("polymarket-development-outcomes", "outcome_label")
open_times = read("polymarket-development-outcomes", "open_time_epoch_seconds")
close_times = read("polymarket-development-outcomes", "close_time_epoch_seconds")
resolved_times = read("polymarket-development-outcomes", "resolved_time_epoch_seconds")
price_point_counts = read("polymarket-development-outcomes", "price_point_count")

assert len(market_ids) == len(event_ids)
assert len(market_ids) == len(event_ordinals)
assert len(market_ids) == len(questions)
assert len(market_ids) == len(outcome_labels)
assert len(market_ids) == len(open_times)
assert len(market_ids) == len(close_times)
assert len(market_ids) == len(resolved_times)
assert len(market_ids) == len(price_point_counts)

events = {}
for row in range(len(market_ids)):
    event_id = event_ids[row]
    if event_id not in events:
        events[event_id] = {
            "event_id": event_id,
            "event_ordinal": event_ordinals[row],
            "markets": [],
            "total_price_points": 0,
            "minimum_price_points": price_point_counts[row],
            "maximum_price_points": price_point_counts[row],
            "open_time_min": open_times[row],
            "close_time_max": close_times[row],
            "resolved_time_max": resolved_times[row],
        }
    event = events[event_id]
    event["markets"] = event["markets"] + [
        {
            "market_id": market_ids[row],
            "question": questions[row],
            "outcome_label": outcome_labels[row],
            "price_point_count": price_point_counts[row],
        }
    ]
    event["total_price_points"] = event["total_price_points"] + price_point_counts[row]
    event["minimum_price_points"] = min(event["minimum_price_points"], price_point_counts[row])
    event["maximum_price_points"] = max(event["maximum_price_points"], price_point_counts[row])
    event["open_time_min"] = min(event["open_time_min"], open_times[row])
    event["close_time_max"] = max(event["close_time_max"], close_times[row])
    event["resolved_time_max"] = max(event["resolved_time_max"], resolved_times[row])

inventory = []
for ordinal in range(24):
    for event_id in events:
        if events[event_id]["event_ordinal"] == ordinal:
            inventory = inventory + [events[event_id]]

assert len(inventory) == 24
assert sum(len(event["markets"]) for event in inventory) == 155

result = structured_return(
    "Exact development-event question and lifecycle inventory for external-signal selection.",
    {
        "schema_version": "polymarket-development-question-inventory/v1",
        "event_count": len(inventory),
        "market_count": len(market_ids),
        "events": inventory,
        "protected_values_exposed": False,
    },
    warnings=[
        "Questions and outcome labels describe development contracts but do not identify an external source or historical availability clock.",
        "Lifecycle close time is retained metadata, not automatically a historically available predictor.",
        "Candidate selection must be semantic and coverage-based; no probability path or payout entered this scan.",
        "The final seven event groups and forty-five markets remain unavailable.",
    ],
)
