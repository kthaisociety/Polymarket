"""Test delayed expert-wallet consensus against raw crowd consensus."""

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
    if fill_times[row] >= resolved_time_by_market[market] or price < 0.05 or price > 0.95:
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

wallet_is_high = {}
for wallet in wallet_edge_sum:
    market_count = wallet_training_markets[wallet]
    shrunk_edge = market_count / (market_count + 10.0) * (
        wallet_edge_sum[wallet] / market_count
    )
    wallet_is_high[wallet] = market_count >= 5 and shrunk_edge >= 0.02

latest_vote_time = {}
latest_vote_uid = {}
latest_vote_direction = {}
vote_event = {}
vote_is_high = {}
for row in range(len(fill_markets)):
    if fill_partitions[row] != "EVALUATION":
        continue
    market = fill_markets[row]
    fill_time = fill_times[row]
    if fill_time >= resolved_time_by_market[market]:
        continue
    signal_hour = int(fill_time // 3600.0) * 3600.0
    key = (fill_accounts[row], market, signal_hour)
    uid = fill_uids[row]
    if (
        key not in latest_vote_time
        or fill_time > latest_vote_time[key]
        or (fill_time == latest_vote_time[key] and uid > latest_vote_uid[key])
    ):
        latest_vote_time[key] = fill_time
        latest_vote_uid[key] = uid
        latest_vote_direction[key] = canonical_direction(
            fill_outcomes[row], fill_sides[row]
        )
        vote_event[key] = fill_events[row]
        wallet = fill_accounts[row]
        vote_is_high[key] = wallet in wallet_is_high and wallet_is_high[wallet]

all_positive = {}
all_negative = {}
expert_positive = {}
expert_negative = {}
group_event = {}
for vote in latest_vote_direction:
    group = (vote[1], vote[2])
    if group not in all_positive:
        all_positive[group] = 0
        all_negative[group] = 0
        expert_positive[group] = 0
        expert_negative[group] = 0
        group_event[group] = vote_event[vote]
    direction = latest_vote_direction[vote]
    if direction == 1:
        all_positive[group] = all_positive[group] + 1
        if vote_is_high[vote]:
            expert_positive[group] = expert_positive[group] + 1
    else:
        all_negative[group] = all_negative[group] + 1
        if vote_is_high[vote]:
            expert_negative[group] = expert_negative[group] + 1

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


event_expert_return_sum_6h = {}
event_raw_return_sum_6h = {}
event_expert_return_sum_24h = {}
event_raw_return_sum_24h = {}
event_signal_count_6h = {}
event_signal_count_24h = {}
signal_count = 0
for group in all_positive:
    expert_count = expert_positive[group] + expert_negative[group]
    if expert_count < 3 or expert_positive[group] == expert_negative[group]:
        continue
    market = group[0]
    signal_hour = group[1]
    event = group_event[group]
    expert_direction = 1 if expert_positive[group] > expert_negative[group] else -1
    raw_direction = 1 if all_positive[group] > all_negative[group] else -1
    decision_time = signal_hour + 3600.0
    entry = first_mark(market, decision_time, decision_time + 3600.0)
    if entry is None:
        continue
    signal_count = signal_count + 1
    exit_6h = first_mark(market, decision_time + 6.0 * 3600.0, decision_time + 8.0 * 3600.0)
    if exit_6h is not None:
        if event not in event_signal_count_6h:
            event_signal_count_6h[event] = 0
            event_expert_return_sum_6h[event] = 0.0
            event_raw_return_sum_6h[event] = 0.0
        event_signal_count_6h[event] = event_signal_count_6h[event] + 1
        event_expert_return_sum_6h[event] = event_expert_return_sum_6h[event] + (
            expert_direction * (exit_6h - entry) - 0.01
        )
        event_raw_return_sum_6h[event] = event_raw_return_sum_6h[event] + (
            raw_direction * (exit_6h - entry) - 0.01
        )
    exit_24h = first_mark(
        market, decision_time + 24.0 * 3600.0, decision_time + 28.0 * 3600.0
    )
    if exit_24h is not None:
        if event not in event_signal_count_24h:
            event_signal_count_24h[event] = 0
            event_expert_return_sum_24h[event] = 0.0
            event_raw_return_sum_24h[event] = 0.0
        event_signal_count_24h[event] = event_signal_count_24h[event] + 1
        event_expert_return_sum_24h[event] = event_expert_return_sum_24h[event] + (
            expert_direction * (exit_24h - entry) - 0.01
        )
        event_raw_return_sum_24h[event] = event_raw_return_sum_24h[event] + (
            raw_direction * (exit_24h - entry) - 0.01
        )


def horizon_metrics(counts, expert_sums, raw_sums):
    expert_edges = []
    raw_edges = []
    differences = []
    early_differences = []
    late_differences = []
    events = sorted(counts)
    midpoint = len(events) // 2
    late_start = None
    if len(events) > 0:
        late_start = events[midpoint]
    total_signals = 0
    for event in counts:
        count = counts[event]
        expert_edge = expert_sums[event] / count
        raw_edge = raw_sums[event] / count
        difference = expert_edge - raw_edge
        expert_edges = expert_edges + [expert_edge]
        raw_edges = raw_edges + [raw_edge]
        differences = differences + [difference]
        total_signals = total_signals + count
        if late_start is not None and event < late_start:
            early_differences = early_differences + [difference]
        else:
            late_differences = late_differences + [difference]
    return {
        "signal_count": total_signals,
        "event_count": len(events),
        "expert_event_macro_net_return": (
            sum(expert_edges) / len(expert_edges) if len(expert_edges) > 0 else None
        ),
        "raw_event_macro_net_return": (
            sum(raw_edges) / len(raw_edges) if len(raw_edges) > 0 else None
        ),
        "expert_minus_raw_event_macro": (
            sum(differences) / len(differences) if len(differences) > 0 else None
        ),
        "early_expert_minus_raw": (
            sum(early_differences) / len(early_differences)
            if len(early_differences) > 0
            else None
        ),
        "late_expert_minus_raw": (
            sum(late_differences) / len(late_differences)
            if len(late_differences) > 0
            else None
        ),
    }


metrics_6h = horizon_metrics(
    event_signal_count_6h, event_expert_return_sum_6h, event_raw_return_sum_6h
)
metrics_24h = horizon_metrics(
    event_signal_count_24h, event_expert_return_sum_24h, event_raw_return_sum_24h
)


def horizon_passed(metrics):
    return (
        metrics["signal_count"] >= 100
        and metrics["event_count"] >= 20
        and metrics["expert_event_macro_net_return"] is not None
        and metrics["expert_event_macro_net_return"] > 0.0
        and metrics["expert_minus_raw_event_macro"] is not None
        and metrics["expert_minus_raw_event_macro"] >= 0.01
        and metrics["early_expert_minus_raw"] is not None
        and metrics["early_expert_minus_raw"] >= 0.0
        and metrics["late_expert_minus_raw"] is not None
        and metrics["late_expert_minus_raw"] >= 0.0
    )


passed = horizon_passed(metrics_6h) and horizon_passed(metrics_24h)
result = structured_return(
    "Delayed expert-wallet consensus versus raw crowd consensus.",
    {
        "schema_version": "polymarket-delayed-expert-consensus/v2",
        "decision": "RETAIN_FOR_EXECUTABLE_REPLAY" if passed else "REJECT_FIXED_CANDIDATE",
        "eligible_signal_group_count": signal_count,
        "six_hour": metrics_6h,
        "twenty_four_hour": metrics_24h,
        "fixed_rule": {
            "minimum_training_markets": 5,
            "high_skill_edge": 0.02,
            "minimum_expert_wallets": 3,
            "entry_delay_hours": 1.0,
            "adverse_execution_hurdle": 0.01,
            "minimum_incremental_edge": 0.01,
        },
    },
    warnings=[
        "This is reproduction evidence on an exposed parent corpus.",
        "Hourly sampled marks are not executable bid/ask quotes.",
        "Wallet agreement may share public information and is not independent private evidence.",
        "The one-cent hurdle is a stress assumption rather than observed spread or impact.",
    ],
)
