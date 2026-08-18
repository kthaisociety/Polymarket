markets = read("polymarket-development-outcomes", "market_id")
events = read("polymarket-development-outcomes", "event_id")
event_ordinals = read("polymarket-development-outcomes", "event_chronological_ordinal")
questions = read("polymarket-development-outcomes", "question")
open_times = read("polymarket-development-outcomes", "open_time_epoch_seconds")
close_times = read("polymarket-development-outcomes", "close_time_epoch_seconds")
point_counts = read("polymarket-development-outcomes", "price_point_count")

target_event_ordinals = [10, 25, 40, 55, 70, 85, 100, 115, 130, 145]
catalog = [None for unused in range(len(markets))]
selected = []

for index in range(len(markets)):
    item = {
        "market_id": markets[index],
        "event_id": events[index],
        "event_chronological_ordinal": event_ordinals[index],
        "question": questions[index],
        "open_time_epoch_seconds": open_times[index],
        "close_time_epoch_seconds": close_times[index],
        "price_point_count": point_counts[index],
    }
    catalog[index] = item
    if event_ordinals[index] in target_event_ordinals:
        already_selected = False
        for retained in selected:
            if retained["event_chronological_ordinal"] == event_ordinals[index]:
                already_selected = True
        if not already_selected:
            selected = selected + [item]

result = structured_return(
    "Development-only semantic inventory and fixed measurement-expansion selection.",
    {
        "schema_version": "polymarket-development-semantic-inventory/v1",
        "contract_count": len(catalog),
        "target_event_ordinals": target_event_ordinals,
        "selected_count": len(selected),
        "selected_first_market_per_target_event": selected,
        "catalog": catalog,
    },
    warnings=[
        "Questions and lifecycle fields describe development contracts only.",
        "Question wording does not prove mutual exclusivity, exhaustiveness, or category identity.",
        "Selection uses fixed event ordinals and first registered market order, not outcomes or paths.",
        "The inventory contains no payout, probability value, fitted result, or protected metadata.",
        "A selected market still requires exact outcome-token lookup from retained source identity.",
    ],
)
