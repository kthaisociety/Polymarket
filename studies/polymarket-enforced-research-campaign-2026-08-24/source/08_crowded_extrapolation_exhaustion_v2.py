"""Test delayed fading of crowded extrapolation against component rivals."""

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

resolved_by_market = {}
payout_by_market = {}
for row in range(len(outcome_markets)):
    resolved_by_market[outcome_markets[row]] = outcome_resolved_times[row]
    payout_by_market[outcome_markets[row]] = outcome_payouts[row]


def direction(outcome_index, side):
    if (outcome_index == 0 and side == "BUY") or (
        outcome_index == 1 and side == "SELL"
    ):
        return 1
    return -1


latest_time = {}
latest_uid = {}
latest_direction = {}
vote_event = {}
for row in range(len(fill_markets)):
    if fill_partitions[row] != "EVALUATION":
        continue
    market = fill_markets[row]
    fill_time = fill_times[row]
    if fill_time >= resolved_by_market[market] or fill_prices[row] < 0.05 or fill_prices[row] > 0.95:
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
        latest_direction[key] = direction(fill_outcomes[row], fill_sides[row])
        vote_event[key] = fill_events[row]

positive = {}
negative = {}
group_event = {}
for vote in latest_direction:
    group = (vote[1], vote[2])
    if group not in positive:
        positive[group] = 0
        negative[group] = 0
        group_event[group] = vote_event[vote]
    if latest_direction[vote] == 1:
        positive[group] = positive[group] + 1
    else:
        negative[group] = negative[group] + 1

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


daily_seen = {}
cohort_event_settlement_sum = {}
cohort_event_fade_6h_sum = {}
cohort_event_fade_24h_sum = {}
cohort_event_count = {}
cohort_signal_count = {}
for group in positive:
    wallet_count = positive[group] + negative[group]
    if positive[group] == negative[group]:
        continue
    consensus = 1 if positive[group] > negative[group] else -1
    agreement = max(positive[group], negative[group]) / wallet_count
    market = group[0]
    hour = group[1]
    event = group_event[group]
    decision_time = hour + 3600.0
    current = first_mark(market, decision_time - 2.0 * 3600.0, decision_time)
    prior = first_mark(market, decision_time - 8.0 * 3600.0, decision_time - 6.0 * 3600.0)
    entry = first_mark(market, decision_time + 3600.0, decision_time + 2.0 * 3600.0)
    if current is None or prior is None or entry is None:
        continue
    prior_move = current - prior
    cohort = None
    if wallet_count >= 5 and agreement >= 0.75 and consensus * prior_move >= 0.05:
        cohort = "CROWDED_CHASE"
    elif wallet_count >= 5 and agreement >= 0.75 and abs(prior_move) < 0.02:
        cohort = "CROWDED_FLAT"
    elif wallet_count <= 2 and agreement == 1.0 and consensus * prior_move >= 0.05:
        cohort = "THIN_CHASE"
    if cohort is None:
        continue
    daily_key = (cohort, market, int(hour // 86400.0))
    if daily_key in daily_seen:
        continue
    daily_seen[daily_key] = True
    key = (cohort, event)
    if key not in cohort_event_count:
        cohort_event_count[key] = 0
        cohort_event_settlement_sum[key] = 0.0
        cohort_event_fade_6h_sum[key] = 0.0
        cohort_event_fade_24h_sum[key] = 0.0
        cohort_signal_count[key] = [0, 0]
    cohort_event_count[key] = cohort_event_count[key] + 1
    cohort_event_settlement_sum[key] = cohort_event_settlement_sum[key] + (
        -consensus * (payout_by_market[market] - entry) - 0.01
    )
    exit_6h = first_mark(
        market, decision_time + 7.0 * 3600.0, decision_time + 10.0 * 3600.0
    )
    if exit_6h is not None:
        cohort_event_fade_6h_sum[key] = cohort_event_fade_6h_sum[key] + (
            -consensus * (exit_6h - entry)
        )
        cohort_signal_count[key][0] = cohort_signal_count[key][0] + 1
    exit_24h = first_mark(
        market, decision_time + 25.0 * 3600.0, decision_time + 30.0 * 3600.0
    )
    if exit_24h is not None:
        cohort_event_fade_24h_sum[key] = cohort_event_fade_24h_sum[key] + (
            -consensus * (exit_24h - entry)
        )
        cohort_signal_count[key][1] = cohort_signal_count[key][1] + 1


def cohort_metrics(cohort):
    settlement = []
    fade_6h = []
    fade_24h = []
    total = 0
    for key in cohort_event_count:
        if key[0] != cohort:
            continue
        count = cohort_event_count[key]
        settlement = settlement + [cohort_event_settlement_sum[key] / count]
        total = total + count
        if cohort_signal_count[key][0] > 0:
            fade_6h = fade_6h + [
                cohort_event_fade_6h_sum[key] / cohort_signal_count[key][0]
            ]
        if cohort_signal_count[key][1] > 0:
            fade_24h = fade_24h + [
                cohort_event_fade_24h_sum[key] / cohort_signal_count[key][1]
            ]
    return {
        "covered_signal_count": total,
        "event_count": len(settlement),
        "event_macro_settlement_net_edge": (
            sum(settlement) / len(settlement) if len(settlement) > 0 else None
        ),
        "event_macro_fade_return_6h": (
            sum(fade_6h) / len(fade_6h) if len(fade_6h) > 0 else None
        ),
        "event_macro_fade_return_24h": (
            sum(fade_24h) / len(fade_24h) if len(fade_24h) > 0 else None
        ),
    }


candidate = cohort_metrics("CROWDED_CHASE")
thin = cohort_metrics("THIN_CHASE")
flat = cohort_metrics("CROWDED_FLAT")
candidate_edge = candidate["event_macro_settlement_net_edge"]
thin_edge = thin["event_macro_settlement_net_edge"]
flat_edge = flat["event_macro_settlement_net_edge"]
passed = (
    candidate["covered_signal_count"] >= 300
    and candidate["event_count"] >= 30
    and candidate["event_macro_fade_return_6h"] is not None
    and candidate["event_macro_fade_return_6h"] > 0.0
    and candidate["event_macro_fade_return_24h"] is not None
    and candidate["event_macro_fade_return_24h"] > 0.0
    and candidate_edge is not None
    and thin_edge is not None
    and flat_edge is not None
    and candidate_edge - thin_edge >= 0.01
    and candidate_edge - flat_edge >= 0.01
)

result = structured_return(
    "Delayed crowded-extrapolation fade against breadth and state rivals.",
    {
        "schema_version": "polymarket-crowded-extrapolation/v2",
        "decision": (
            "RETAIN_FOR_FRESH_REPLICATION"
            if passed
            else "REJECT_FIXED_CROWDED_EXTRAPOLATION_CANDIDATE"
        ),
        "crowded_chase": candidate,
        "thin_chase": thin,
        "crowded_flat": flat,
        "candidate_minus_thin_settlement_edge": (
            candidate_edge - thin_edge
            if candidate_edge is not None and thin_edge is not None
            else None
        ),
        "candidate_minus_flat_settlement_edge": (
            candidate_edge - flat_edge
            if candidate_edge is not None and flat_edge is not None
            else None
        ),
        "fixed_rule": {
            "crowd_min_wallets": 5,
            "crowd_min_agreement": 0.75,
            "thin_max_wallets": 2,
            "chase_min_move": 0.05,
            "flat_max_move": 0.02,
            "entry_delay_hours": 1.0,
            "daily_signal_cap": 1,
            "adverse_execution_hurdle": 0.01,
        },
    },
    warnings=[
        "This is reproduction evidence on an exposed parent corpus.",
        "Hourly sampled marks are not executable quotes.",
        "The parent-bound panel does not carry a mutable repair-status field; no post-hoc repair filter is used.",
        "Crowd breadth and prior motion can both proxy common public news.",
    ],
)
