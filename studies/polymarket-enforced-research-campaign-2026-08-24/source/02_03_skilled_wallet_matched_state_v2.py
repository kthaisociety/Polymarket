"""Re-test fold-local skilled wallets on a registered parent-bound taker panel."""

fill_accounts = read("polymarket-development-taker-fills", "account")
fill_markets = read("polymarket-development-taker-fills", "market_id")
fill_events = read("polymarket-development-taker-fills", "event_chronological_ordinal")
fill_partitions = read("polymarket-development-taker-fills", "research_partition")
fill_times = read("polymarket-development-taker-fills", "fill_time_epoch_seconds")
fill_outcomes = read("polymarket-development-taker-fills", "outcome_index")
fill_sides = read("polymarket-development-taker-fills", "side")
fill_prices = read("polymarket-development-taker-fills", "price")

outcome_markets = read("polymarket-development-outcomes", "market_id")
outcome_resolved_times = read(
    "polymarket-development-outcomes", "resolved_time_epoch_seconds"
)
outcome_payouts = read("polymarket-development-outcomes", "resolution_payout")

payout_by_market = {}
resolved_time_by_market = {}
for row in range(len(outcome_markets)):
    market = outcome_markets[row]
    payout_by_market[market] = outcome_payouts[row]
    resolved_time_by_market[market] = outcome_resolved_times[row]


def signed_edge(outcome_index, side, price, payout_zero):
    payout = payout_zero
    if outcome_index == 1:
        payout = 1.0 - payout_zero
    if side == "BUY":
        return payout - price
    return price - payout


wallet_market_sum = {}
wallet_market_count = {}
for row in range(len(fill_markets)):
    if fill_partitions[row] != "TRAIN":
        continue
    market = fill_markets[row]
    if fill_times[row] >= resolved_time_by_market[market]:
        continue
    price = fill_prices[row]
    if price < 0.05 or price > 0.95:
        continue
    key = (fill_accounts[row], market)
    if key not in wallet_market_sum:
        wallet_market_sum[key] = 0.0
        wallet_market_count[key] = 0
    wallet_market_sum[key] = wallet_market_sum[key] + signed_edge(
        fill_outcomes[row], fill_sides[row], price, payout_by_market[market]
    )
    wallet_market_count[key] = wallet_market_count[key] + 1

wallet_edge_sum = {}
wallet_training_markets = {}
for key in wallet_market_sum:
    wallet = key[0]
    if wallet not in wallet_edge_sum:
        wallet_edge_sum[wallet] = 0.0
        wallet_training_markets[wallet] = 0
    wallet_edge_sum[wallet] = wallet_edge_sum[wallet] + (
        wallet_market_sum[key] / wallet_market_count[key]
    )
    wallet_training_markets[wallet] = wallet_training_markets[wallet] + 1

wallet_shrunk_edge = {}
eligible_wallet_count = 0
high_skill_wallet_count = 0
low_skill_wallet_count = 0
for wallet in wallet_edge_sum:
    market_count = wallet_training_markets[wallet]
    edge = market_count / (market_count + 10.0) * (
        wallet_edge_sum[wallet] / market_count
    )
    wallet_shrunk_edge[wallet] = edge
    if market_count >= 5:
        eligible_wallet_count = eligible_wallet_count + 1
        if edge >= 0.02:
            high_skill_wallet_count = high_skill_wallet_count + 1
        if edge <= -0.02:
            low_skill_wallet_count = low_skill_wallet_count + 1

cell_high_sum = {}
cell_high_count = {}
cell_control_sum = {}
cell_control_count = {}
evaluation_fill_count = 0
high_skill_fill_count = 0
evaluation_events = set()
high_skill_events = set()

for row in range(len(fill_markets)):
    if fill_partitions[row] != "EVALUATION":
        continue
    market = fill_markets[row]
    if fill_times[row] >= resolved_time_by_market[market]:
        continue
    price = fill_prices[row]
    if price < 0.05 or price > 0.95:
        continue
    evaluation_fill_count = evaluation_fill_count + 1
    event = fill_events[row]
    evaluation_events = evaluation_events | {event}
    hours_to_resolution = (resolved_time_by_market[market] - fill_times[row]) / 3600.0
    horizon = "GT_168H"
    if hours_to_resolution <= 24.0:
        horizon = "LE_24H"
    elif hours_to_resolution <= 72.0:
        horizon = "24_72H"
    elif hours_to_resolution <= 168.0:
        horizon = "72_168H"
    cell = (event, fill_sides[row], int(price * 20.0), horizon)
    edge = signed_edge(
        fill_outcomes[row], fill_sides[row], price, payout_by_market[market]
    )
    wallet = fill_accounts[row]
    high = (
        wallet in wallet_training_markets
        and wallet_training_markets[wallet] >= 5
        and wallet_shrunk_edge[wallet] >= 0.02
    )
    if high:
        high_skill_fill_count = high_skill_fill_count + 1
        high_skill_events = high_skill_events | {event}
        if cell not in cell_high_sum:
            cell_high_sum[cell] = 0.0
            cell_high_count[cell] = 0
        cell_high_sum[cell] = cell_high_sum[cell] + edge
        cell_high_count[cell] = cell_high_count[cell] + 1
    else:
        if cell not in cell_control_sum:
            cell_control_sum[cell] = 0.0
            cell_control_count[cell] = 0
        cell_control_sum[cell] = cell_control_sum[cell] + edge
        cell_control_count[cell] = cell_control_count[cell] + 1

event_difference_sum = {}
event_cell_count = {}
event_high_edge_sum = {}
event_control_edge_sum = {}
matched_cell_count = 0
matched_high_fill_count = 0
matched_control_fill_count = 0
for cell in cell_high_sum:
    if (
        cell in cell_control_sum
        and cell_high_count[cell] >= 5
        and cell_control_count[cell] >= 5
    ):
        event = cell[0]
        high_edge = cell_high_sum[cell] / cell_high_count[cell]
        control_edge = cell_control_sum[cell] / cell_control_count[cell]
        if event not in event_difference_sum:
            event_difference_sum[event] = 0.0
            event_high_edge_sum[event] = 0.0
            event_control_edge_sum[event] = 0.0
            event_cell_count[event] = 0
        event_difference_sum[event] = event_difference_sum[event] + high_edge - control_edge
        event_high_edge_sum[event] = event_high_edge_sum[event] + high_edge
        event_control_edge_sum[event] = event_control_edge_sum[event] + control_edge
        event_cell_count[event] = event_cell_count[event] + 1
        matched_cell_count = matched_cell_count + 1
        matched_high_fill_count = matched_high_fill_count + cell_high_count[cell]
        matched_control_fill_count = matched_control_fill_count + cell_control_count[cell]

event_differences = []
event_high_edges = []
event_control_edges = []
early_differences = []
late_differences = []
positive_event_count = 0
evaluation_event_ordinals = sorted(evaluation_events)
evaluation_midpoint = len(evaluation_event_ordinals) // 2
late_start = None
if len(evaluation_event_ordinals) > 0:
    late_start = evaluation_event_ordinals[evaluation_midpoint]
for event in event_difference_sum:
    difference = event_difference_sum[event] / event_cell_count[event]
    event_differences = event_differences + [difference]
    event_high_edges = event_high_edges + [
        event_high_edge_sum[event] / event_cell_count[event]
    ]
    event_control_edges = event_control_edges + [
        event_control_edge_sum[event] / event_cell_count[event]
    ]
    if difference > 0.0:
        positive_event_count = positive_event_count + 1
    if late_start is not None and event < late_start:
        early_differences = early_differences + [difference]
    else:
        late_differences = late_differences + [difference]


def safe_mean(values):
    if len(values) == 0:
        return None
    return sum(values) / len(values)


overall_difference = safe_mean(event_differences)
early_difference = safe_mean(early_differences)
late_difference = safe_mean(late_differences)
passed = (
    len(event_differences) >= 30
    and matched_cell_count >= 100
    and overall_difference is not None
    and overall_difference >= 0.01
    and early_difference is not None
    and early_difference >= 0.0
    and late_difference is not None
    and late_difference >= 0.0
)

result = structured_return(
    "Parent-bound fold-local skilled-wallet matched-state screen.",
    {
        "schema_version": "polymarket-skilled-wallet-matched-state/v2",
        "decision": "RETAIN_FOR_DELAYED_ENTRY" if passed else "REJECT_FIXED_CANDIDATE",
        "skill_population": {
            "wallet_count": len(wallet_edge_sum),
            "eligible_wallet_count": eligible_wallet_count,
            "high_skill_wallet_count": high_skill_wallet_count,
            "low_skill_wallet_count": low_skill_wallet_count,
        },
        "coverage": {
            "evaluation_fill_count": evaluation_fill_count,
            "high_skill_fill_count": high_skill_fill_count,
            "evaluation_event_count": len(evaluation_events),
            "high_skill_event_count": len(high_skill_events),
        },
        "matched_result": {
            "matched_event_count": len(event_differences),
            "matched_cell_count": matched_cell_count,
            "high_fill_count": matched_high_fill_count,
            "control_fill_count": matched_control_fill_count,
            "high_event_macro_edge": safe_mean(event_high_edges),
            "control_event_macro_edge": safe_mean(event_control_edges),
            "high_minus_control_event_macro_edge": overall_difference,
            "early_high_minus_control_edge": early_difference,
            "late_high_minus_control_edge": late_difference,
            "positive_event_share": (
                positive_event_count / len(event_differences)
                if len(event_differences) > 0
                else None
            ),
        },
        "fixed_rule": {
            "minimum_training_markets": 5,
            "skill_shrinkage": 10.0,
            "high_skill_edge": 0.02,
            "minimum_fills_per_cohort_cell": 5,
            "price_band_width": 0.05,
            "minimum_events": 30,
            "minimum_cells": 100,
            "minimum_incremental_edge": 0.01,
        },
    },
    warnings=[
        "This is a reproduction on an already exposed parent corpus, not fresh evidence.",
        "Account rows are exact aggregate taker legs registered before authored analysis.",
        "Recorded fill edge is not a delayed executable quote and omits fees and impact.",
        "Event, side, price state, and time-to-resolution cells are controls, not randomization.",
    ],
)
