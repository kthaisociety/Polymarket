outcome_markets = read("polymarket-development-outcomes", "market_id")
outcome_events = read("polymarket-development-outcomes", "event_chronological_ordinal")
price_markets = read("polymarket-development-prices", "market_id")
price_events = read("polymarket-development-prices", "event_chronological_ordinal")
times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")


def quantile(values, fraction):
    ordered = sorted(values)
    index = int((len(ordered) - 1) * fraction)
    return ordered[index]


complete_events = [0, 8, 11, 15]
costs = [0.0, 0.005, 0.01]
event_leg_count = {}
for event in complete_events:
    event_leg_count[event] = 0
for row in range(len(outcome_markets)):
    event = outcome_events[row]
    if event in complete_events:
        event_leg_count[event] = event_leg_count[event] + 1

last_by_market_hour = {}
for row in range(len(price_markets)):
    event = price_events[row]
    if event in complete_events:
        hour = int(times[row] / 3600.0)
        last_by_market_hour[(event, hour, price_markets[row])] = [
            times[row],
            probabilities[row],
        ]

hourly = {}
for key in last_by_market_hour:
    event = key[0]
    hour = key[1]
    point = last_by_market_hour[key]
    if (event, hour) not in hourly:
        hourly[(event, hour)] = [0.0, 0, point[0], point[0]]
    aggregate = hourly[(event, hour)]
    aggregate[0] = aggregate[0] + point[1]
    aggregate[1] = aggregate[1] + 1
    aggregate[2] = min(aggregate[2], point[0])
    aggregate[3] = max(aggregate[3], point[0])

edges = {}
for event in complete_events:
    edges[event] = {}
for key in hourly:
    event = key[0]
    hour = key[1]
    aggregate = hourly[key]
    if aggregate[1] == event_leg_count[event] and aggregate[3] - aggregate[2] <= 300.0:
        edges[event][hour] = 1.0 - aggregate[0]

event_results = [None, None, None, None]
for event_index in range(len(complete_events)):
    event = complete_events[event_index]
    event_edges = [0.0 for unused in range(len(edges[event]))]
    edge_cursor = 0
    for hour in edges[event]:
        event_edges[edge_cursor] = edges[event][hour]
        edge_cursor = edge_cursor + 1
    cost_results = [None, None, None]
    for cost_index in range(len(costs)):
        cost = costs[cost_index]
        per_bundle_cost = event_leg_count[event] * cost
        net_edges = [0.0 for unused in range(len(event_edges))]
        for edge_index in range(len(event_edges)):
            net_edges[edge_index] = event_edges[edge_index] - per_bundle_cost
        positive_count = 0
        for net_edge in net_edges:
            if net_edge > 0.0:
                positive_count = positive_count + 1
        delayed_current_count = 0
        delayed_positive_count = 0
        delayed_next_sum = 0.0
        for hour in edges[event]:
            current_net = edges[event][hour] - per_bundle_cost
            if current_net > 0.0 and hour + 1 in edges[event]:
                delayed_current_count = delayed_current_count + 1
                next_net = edges[event][hour + 1] - per_bundle_cost
                delayed_next_sum = delayed_next_sum + next_net
                if next_net > 0.0:
                    delayed_positive_count = delayed_positive_count + 1
        cost_results[cost_index] = {
            "cost_per_leg": cost,
            "bundle_cost": per_bundle_cost,
            "positive_count": positive_count,
            "positive_fraction": positive_count / len(net_edges),
            "net_p10": quantile(net_edges, 0.10),
            "net_median": quantile(net_edges, 0.50),
            "net_p90": quantile(net_edges, 0.90),
            "net_min": min(net_edges),
            "net_max": max(net_edges),
            "current_opportunities_with_next_hour": delayed_current_count,
            "next_hour_positive_fraction": (
                None
                if delayed_current_count == 0
                else delayed_positive_count / delayed_current_count
            ),
            "next_hour_mean_net": (
                None
                if delayed_current_count == 0
                else delayed_next_sum / delayed_current_count
            ),
        }
    event_results[event_index] = {
        "event_chronological_ordinal": event,
        "leg_count": event_leg_count[event],
        "synchronized_hour_count": len(event_edges),
        "gross_edge_mean": sum(event_edges) / len(event_edges),
        "gross_edge_min": min(event_edges),
        "gross_edge_max": max(event_edges),
        "cost_grid": cost_results,
    }

one_cent_median_positive = 0
one_cent_p10_positive = 0
one_cent_persistence_pass = 0
for event_result in event_results:
    one_cent = event_result["cost_grid"][2]
    if one_cent["net_median"] > 0.0:
        one_cent_median_positive = one_cent_median_positive + 1
    if one_cent["net_p10"] > 0.0:
        one_cent_p10_positive = one_cent_p10_positive + 1
    if (
        one_cent["next_hour_positive_fraction"] is not None
        and one_cent["next_hour_positive_fraction"] >= 0.60
    ):
        one_cent_persistence_pass = one_cent_persistence_pass + 1

result = structured_return(
    "Synchronized exhaustive-bucket underround and one-hour persistence diagnostics.",
    {
        "semantic_event_ordinals": complete_events,
        "maximum_sync_span_seconds": 300,
        "event_results": event_results,
        "declared_live_quote_candidate_gate": {
            "all_event_medians_positive_at_one_cent_per_leg": one_cent_median_positive == 4,
            "at_least_three_event_p10_positive_at_one_cent_per_leg": one_cent_p10_positive >= 3,
            "all_event_one_hour_persistence_at_least_sixty_percent": (
                one_cent_persistence_pass == 4
            ),
            "passes_all": (
                one_cent_median_positive == 4
                and one_cent_p10_positive >= 3
                and one_cent_persistence_pass == 4
            ),
        },
    },
    warnings=[
        "Sampled YES probabilities are not simultaneous executable asks.",
        "The per-leg cost grid is hypothetical and omits size, fees, and partial-fill risk.",
        "Repeated hourly observations are opportunity diagnostics, not independent PnL samples.",
        "Only four semantically explicit exhaustive development event groups are included.",
        "Protected events and values remain unavailable.",
    ],
)
