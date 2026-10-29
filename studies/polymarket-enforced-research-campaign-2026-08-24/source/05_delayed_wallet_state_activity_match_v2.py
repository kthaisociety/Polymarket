"""Re-test skilled-wallet edge after delayed entry and activity/state matching."""

fill_accounts = read("polymarket-development-taker-fills", "account")
fill_markets = read("polymarket-development-taker-fills", "market_id")
fill_events = read("polymarket-development-taker-fills", "event_chronological_ordinal")
fill_partitions = read("polymarket-development-taker-fills", "research_partition")
fill_times = read("polymarket-development-taker-fills", "fill_time_epoch_seconds")
fill_uids = read("polymarket-development-taker-fills", "fill_uid")
fill_outcomes = read("polymarket-development-taker-fills", "outcome_index")
fill_sides = read("polymarket-development-taker-fills", "side")
fill_prices = read("polymarket-development-taker-fills", "price")

price_markets = read("polymarket-development-prices", "market_id")
price_times = read("polymarket-development-prices", "observed_at_epoch_seconds")
probabilities = read("polymarket-development-prices", "market_probability")

outcome_markets = read("polymarket-development-outcomes", "market_id")
outcome_resolved_times = read(
    "polymarket-development-outcomes", "resolved_time_epoch_seconds"
)
outcome_payouts = read("polymarket-development-outcomes", "resolution_payout")

payout_by_market = {}
resolved_by_market = {}
for row in range(len(outcome_markets)):
    payout_by_market[outcome_markets[row]] = outcome_payouts[row]
    resolved_by_market[outcome_markets[row]] = outcome_resolved_times[row]


def signed_fill_edge(outcome_index, side, price, payout_zero):
    payout = payout_zero
    if outcome_index == 1:
        payout = 1.0 - payout_zero
    if side == "BUY":
        return payout - price
    return price - payout


def canonical_direction(outcome_index, side):
    if (outcome_index == 0 and side == "BUY") or (
        outcome_index == 1 and side == "SELL"
    ):
        return 1
    return -1


wallet_market_sum = {}
wallet_market_count = {}
for row in range(len(fill_markets)):
    if fill_partitions[row] != "TRAIN":
        continue
    market = fill_markets[row]
    price = fill_prices[row]
    if fill_times[row] >= resolved_by_market[market] or price < 0.05 or price > 0.95:
        continue
    key = (fill_accounts[row], market)
    if key not in wallet_market_sum:
        wallet_market_sum[key] = 0.0
        wallet_market_count[key] = 0
    wallet_market_sum[key] = wallet_market_sum[key] + signed_fill_edge(
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

wallet_is_high = {}
for wallet in wallet_edge_sum:
    market_count = wallet_training_markets[wallet]
    shrunk_edge = market_count / (market_count + 10.0) * (
        wallet_edge_sum[wallet] / market_count
    )
    wallet_is_high[wallet] = market_count >= 5 and shrunk_edge >= 0.02

latest_time = {}
latest_uid = {}
latest_direction = {}
vote_event = {}
vote_is_high = {}
for row in range(len(fill_markets)):
    if fill_partitions[row] != "EVALUATION":
        continue
    market = fill_markets[row]
    fill_time = fill_times[row]
    price = fill_prices[row]
    if fill_time >= resolved_by_market[market] or price < 0.05 or price > 0.95:
        continue
    hour = int(fill_time // 3600.0) * 3600.0
    key = (fill_accounts[row], market, hour)
    if (
        key not in latest_time
        or fill_time > latest_time[key]
        or (fill_time == latest_time[key] and fill_uids[row] > latest_uid[key])
    ):
        latest_time[key] = fill_time
        latest_uid[key] = fill_uids[row]
        latest_direction[key] = canonical_direction(
            fill_outcomes[row], fill_sides[row]
        )
        vote_event[key] = fill_events[row]
        wallet = fill_accounts[row]
        vote_is_high[key] = wallet in wallet_is_high and wallet_is_high[wallet]

activity_count = {}
for vote in latest_time:
    group = (vote[1], vote[2])
    if group not in activity_count:
        activity_count[group] = 0
    activity_count[group] = activity_count[group] + 1

price_start = {}
price_end = {}
for row in range(len(price_markets)):
    market = price_markets[row]
    if market not in price_start:
        price_start[market] = row
    price_end[market] = row + 1


def first_mark(market, lower, upper):
    if market not in price_start:
        return None
    for row in range(price_start[market], price_end[market]):
        observed = price_times[row]
        if observed >= lower and observed <= upper:
            return probabilities[row]
        if observed > upper:
            return None
    return None


def last_mark(market, lower, upper):
    if market not in price_start:
        return None
    value = None
    for row in range(price_start[market], price_end[market]):
        observed = price_times[row]
        if observed >= lower and observed <= upper:
            value = probabilities[row]
        if observed > upper:
            return value
    return value


cell_high_sum = {}
cell_high_count = {}
cell_control_sum = {}
cell_control_count = {}
high_coverage = 0
control_coverage = 0
high_eligible = 0
control_eligible = 0
for vote in latest_time:
    market = vote[1]
    signal_time = latest_time[vote]
    prior = last_mark(market, signal_time - 2.0 * 3600.0, signal_time)
    delayed = first_mark(
        market, signal_time + 1.0 * 3600.0, signal_time + 2.0 * 3600.0
    )
    high = vote_is_high[vote]
    if prior is not None and delayed is not None:
        if high:
            high_coverage = high_coverage + 1
        else:
            control_coverage = control_coverage + 1
    if prior is None or delayed is None:
        continue
    direction = latest_direction[vote]
    momentum = "FLAT"
    if delayed - prior <= -0.02:
        momentum = "DOWN"
    elif delayed - prior >= 0.02:
        momentum = "UP"
    hours_to_resolution = (resolved_by_market[market] - signal_time) / 3600.0
    horizon = "GT_168H"
    if hours_to_resolution <= 24.0:
        horizon = "LE_24H"
    elif hours_to_resolution <= 72.0:
        horizon = "24_72H"
    elif hours_to_resolution <= 168.0:
        horizon = "72_168H"
    count = activity_count[(market, vote[2])]
    activity = "ACTIVITY_10_PLUS"
    if count == 1:
        activity = "ACTIVITY_1"
    elif count <= 4:
        activity = "ACTIVITY_2_4"
    elif count <= 9:
        activity = "ACTIVITY_5_9"
    event = vote_event[vote]
    cell = (event, direction, int(delayed * 20.0), horizon, momentum, activity)
    edge = direction * (payout_by_market[market] - delayed) - 0.01
    if high:
        high_eligible = high_eligible + 1
        if cell not in cell_high_sum:
            cell_high_sum[cell] = 0.0
            cell_high_count[cell] = 0
        cell_high_sum[cell] = cell_high_sum[cell] + edge
        cell_high_count[cell] = cell_high_count[cell] + 1
    else:
        control_eligible = control_eligible + 1
        if cell not in cell_control_sum:
            cell_control_sum[cell] = 0.0
            cell_control_count[cell] = 0
        cell_control_sum[cell] = cell_control_sum[cell] + edge
        cell_control_count[cell] = cell_control_count[cell] + 1

event_high_sum = {}
event_control_sum = {}
event_difference_sum = {}
event_cell_count = {}
high_signal_count = 0
control_signal_count = 0
matched_cell_count = 0
for cell in cell_high_sum:
    if (
        cell in cell_control_sum
        and cell_high_count[cell] >= 3
        and cell_control_count[cell] >= 3
    ):
        event = cell[0]
        high_edge = cell_high_sum[cell] / cell_high_count[cell]
        control_edge = cell_control_sum[cell] / cell_control_count[cell]
        if event not in event_cell_count:
            event_high_sum[event] = 0.0
            event_control_sum[event] = 0.0
            event_difference_sum[event] = 0.0
            event_cell_count[event] = 0
        event_high_sum[event] = event_high_sum[event] + high_edge
        event_control_sum[event] = event_control_sum[event] + control_edge
        event_difference_sum[event] = event_difference_sum[event] + high_edge - control_edge
        event_cell_count[event] = event_cell_count[event] + 1
        high_signal_count = high_signal_count + cell_high_count[cell]
        control_signal_count = control_signal_count + cell_control_count[cell]
        matched_cell_count = matched_cell_count + 1

events = sorted(event_cell_count)
late_start = None
if len(events) > 0:
    late_start = events[len(events) // 2]
high_edges = []
control_edges = []
differences = []
early_high = []
late_high = []
early_difference = []
late_difference = []
positive_count = 0
for event in event_cell_count:
    cells = event_cell_count[event]
    high_edge = event_high_sum[event] / cells
    control_edge = event_control_sum[event] / cells
    difference = event_difference_sum[event] / cells
    high_edges = high_edges + [high_edge]
    control_edges = control_edges + [control_edge]
    differences = differences + [difference]
    if difference > 0.0:
        positive_count = positive_count + 1
    if late_start is not None and event < late_start:
        early_high = early_high + [high_edge]
        early_difference = early_difference + [difference]
    else:
        late_high = late_high + [high_edge]
        late_difference = late_difference + [difference]


def safe_mean(values):
    if len(values) == 0:
        return None
    return sum(values) / len(values)


overall_high = safe_mean(high_edges)
overall_difference = safe_mean(differences)
early_high_edge = safe_mean(early_high)
late_high_edge = safe_mean(late_high)
early_increment = safe_mean(early_difference)
late_increment = safe_mean(late_difference)
passed = (
    len(events) >= 25
    and matched_cell_count >= 75
    and overall_difference is not None
    and overall_difference >= 0.01
    and early_increment is not None
    and early_increment >= 0.0
    and late_increment is not None
    and late_increment >= 0.0
    and early_high_edge is not None
    and early_high_edge > 0.0
    and late_high_edge is not None
    and late_high_edge > 0.0
)

result = structured_return(
    "Delayed skilled-wallet state-and-activity-matched falsification.",
    {
        "schema_version": "polymarket-delayed-wallet-state-activity-match/v2",
        "decision": (
            "RETAIN_FOR_EXECUTABLE_REPLAY"
            if passed
            else "REJECT_FIXED_DELAYED_STATE_ACTIVITY_CANDIDATE"
        ),
        "coverage": {
            "high_signal_count": sum(1 for vote in latest_time if vote_is_high[vote]),
            "control_signal_count": sum(1 for vote in latest_time if not vote_is_high[vote]),
            "high_state_eligible_count": high_coverage,
            "control_state_eligible_count": control_coverage,
            "high_eligible_count": high_eligible,
            "control_eligible_count": control_eligible,
        },
        "matched_result": {
            "matched_event_count": len(events),
            "matched_cell_count": matched_cell_count,
            "high_signal_count": high_signal_count,
            "control_signal_count": control_signal_count,
            "high_event_macro_net_edge": overall_high,
            "control_event_macro_net_edge": safe_mean(control_edges),
            "high_minus_control_event_macro_net_edge": overall_difference,
            "early_high_event_macro_net_edge": early_high_edge,
            "late_high_event_macro_net_edge": late_high_edge,
            "early_high_minus_control_edge": early_increment,
            "late_high_minus_control_edge": late_increment,
            "positive_event_share": (
                positive_count / len(events) if len(events) > 0 else None
            ),
        },
        "fixed_rule": {
            "minimum_training_markets": 5,
            "skill_shrinkage": 10.0,
            "high_skill_edge": 0.02,
            "entry_delay_hours": 1.0,
            "adverse_execution_hurdle": 0.01,
            "minimum_signals_per_cohort_cell": 3,
            "minimum_events": 25,
            "minimum_cells": 75,
            "minimum_incremental_edge": 0.01,
        },
    },
    warnings=[
        "This is reproduction evidence on an exposed parent corpus.",
        "Matching controls direction, delayed price, resolution horizon, momentum, and activity.",
        "Hourly sampled marks are not executable quotes.",
        "The one-cent hurdle is a stress assumption rather than observed execution cost.",
    ],
)
