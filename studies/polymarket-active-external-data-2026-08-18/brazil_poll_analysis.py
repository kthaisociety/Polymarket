# ruff: noqa: ANN001, ANN201, D100, D103, E501, F821, INP001, PLR0912, PLR0915, PLR2004

poll_time = read("brazil-poll-vintages", "available_epoch")
poll_institute = read("brazil-poll-vintages", "institute")
poll_margin = read("brazil-poll-vintages", "lula_margin_pp")
poll_register = read("brazil-poll-vintages", "register_tse")

fill_time = read("brazil-fills", "fill_epoch")
fill_market = read("brazil-fills", "market_id")
fill_side = read("brazil-fills", "side")
fill_price = read("brazil-fills", "price")
fill_size = read("brazil-fills", "size")

market_ids = read("brazil-markets", "market_id")
market_candidate = read("brazil-markets", "candidate")
market_open = read("brazil-markets", "open_epoch")
market_close = read("brazil-markets", "close_epoch")


def median(values):
    ordered = sorted(values)
    count = len(ordered)
    if count % 2 == 1:
        return float(ordered[count // 2])
    return (float(ordered[count // 2 - 1]) + float(ordered[count // 2])) / 2.0


def execute(market_id, direction, action, start, end, shares):
    required_side = "BUY"
    invert = False
    if direction == "YES" and action == "SELL":
        required_side = "SELL"
    if direction == "NO" and action == "BUY":
        required_side = "SELL"
        invert = True
    if direction == "NO" and action == "SELL":
        required_side = "BUY"
        invert = True
    remaining = shares
    notional = 0.0
    fees = 0.0
    filled = 0.0
    for i in range(len(fill_time)):
        if (
            fill_market[i] == market_id
            and fill_side[i] == required_side
            and int(fill_time[i]) >= start
            and int(fill_time[i]) <= end
            and remaining > 0.0000001
        ):
            price = float(fill_price[i])
            if invert:
                price = 1.0 - price
            size = float(fill_size[i])
            take = min(remaining, size)
            notional = notional + take * price
            fees = fees + take * 0.05 * price * (1.0 - price)
            filled = filled + take
            remaining = remaining - take
    return (notional, fees, filled)


def round_trip(market_id, direction, decision_time, horizon_hours):
    entry, entry_fee, entry_fill = execute(
        market_id, direction, "BUY", decision_time, decision_time + 21600, 100.0
    )
    exit_start = decision_time + horizon_hours * 3600
    exit_value, exit_fee, exit_fill = execute(
        market_id, direction, "SELL", exit_start, exit_start + 21600, 100.0
    )
    if entry_fill < 100.0 or exit_fill < 100.0:
        return None
    return {
        "pnl": exit_value - entry - entry_fee - exit_fee,
        "fees": entry_fee + exit_fee,
        "entry_cost": entry + entry_fee,
    }


candidate_market = {}
for i in range(len(market_ids)):
    candidate_market[market_candidate[i]] = market_ids[i]

# Polls appearing in one immutable commit are one decision event. The event margin is
# the median of simultaneous releases so one data-source batch cannot generate repeated trades.
events = []
cursor = 0
while cursor < len(poll_time):
    available = int(poll_time[cursor])
    margins = []
    institutes = []
    registers = []
    while cursor < len(poll_time) and int(poll_time[cursor]) == available:
        margins = margins + [float(poll_margin[cursor])]
        institutes = institutes + [poll_institute[cursor]]
        registers = registers + [poll_register[cursor]]
        cursor = cursor + 1
    events = events + [
        {
            "time": available,
            "margin": median(margins),
            "institutes": institutes,
            "margins": margins,
            "registers": registers,
        }
    ]

last_by_institute = {}
for event_index in range(len(events)):
    event = events[event_index]
    features = {}
    if event_index > 0:
        features["latest_release_change"] = event["margin"] - events[event_index - 1]["margin"]
    if event_index >= 3:
        current_window = [events[i]["margin"] for i in range(event_index - 2, event_index + 1)]
        prior_window = [events[i]["margin"] for i in range(event_index - 3, event_index)]
        features["rolling3_median_change"] = median(current_window) - median(prior_window)
    if event_index >= 5:
        prior_five = [events[i]["margin"] for i in range(event_index - 5, event_index)]
        features["surprise_vs_prior5"] = event["margin"] - median(prior_five)
    same_pollster_changes = []
    for item_index in range(len(event["institutes"])):
        institute = event["institutes"][item_index]
        margin = float(event["margins"][item_index])
        if institute in last_by_institute:
            same_pollster_changes = same_pollster_changes + [margin - last_by_institute[institute]]
        last_by_institute[institute] = margin
    if len(same_pollster_changes) > 0:
        features["same_pollster_change"] = median(same_pollster_changes)
    event["features"] = features

results = []
event_rows = []
for horizon_hours in [24, 72, 168]:
    opportunities = []
    for event_index in range(len(events)):
        event = events[event_index]
        decision_time = int(event["time"])
        if decision_time < int(market_open[0]) or decision_time >= int(market_close[0]):
            continue
        pro_lula_legs = [
            round_trip(candidate_market["lula"], "YES", decision_time, horizon_hours),
            round_trip(candidate_market["flavio"], "NO", decision_time, horizon_hours),
        ]
        anti_lula_legs = [
            round_trip(candidate_market["lula"], "NO", decision_time, horizon_hours),
            round_trip(candidate_market["flavio"], "YES", decision_time, horizon_hours),
        ]
        if None not in pro_lula_legs and None not in anti_lula_legs:
            directions = [["pro_lula", pro_lula_legs], ["anti_lula", anti_lula_legs]]
            for direction_item in directions:
                direction_name = direction_item[0]
                legs = direction_item[1]
                opportunities = opportunities + [
                    {
                        "event_index": event_index,
                        "direction": direction_name,
                        "features": event["features"],
                        "pnl": sum(leg["pnl"] for leg in legs),
                        "fees": sum(leg["fees"] for leg in legs),
                        "entry_cost": sum(leg["entry_cost"] for leg in legs),
                    }
                ]
        rounded_features = {}
        for feature_key in [
            "latest_release_change",
            "rolling3_median_change",
            "surprise_vs_prior5",
            "same_pollster_change",
        ]:
            if feature_key in event["features"]:
                rounded_features[feature_key] = round(
                    float(event["features"][feature_key]), 4
                )
        event_rows = event_rows + [
            {
                "horizon_hours": horizon_hours,
                "event_index": event_index,
                "available_epoch": decision_time,
                "registers": event["registers"],
                "margin": round(float(event["margin"]), 4),
                "features": rounded_features,
                "pair_executable": None not in pro_lula_legs and None not in anti_lula_legs,
            }
        ]
    for feature_name in [
        "latest_release_change",
        "rolling3_median_change",
        "surprise_vs_prior5",
        "same_pollster_change",
    ]:
        for stance in ["follow", "fade"]:
            for threshold in [0.0, 2.0, 4.0]:
                selected = []
                for item in opportunities:
                    if feature_name not in item["features"]:
                        continue
                    signal = float(item["features"][feature_name])
                    desired = "pro_lula" if signal > 0.0 else "anti_lula"
                    if stance == "fade":
                        desired = "anti_lula" if signal > 0.0 else "pro_lula"
                    if item["direction"] == desired and abs(signal) > threshold:
                        selected = selected + [item]
                pnl = sum(item["pnl"] for item in selected)
                entry_cost = sum(item["entry_cost"] for item in selected)
                results = results + [
                    {
                        "horizon_hours": horizon_hours,
                        "feature": feature_name,
                        "stance": stance,
                        "minimum_abs_pp": threshold,
                        "trades": len(selected),
                        "wins": sum(1 for item in selected if item["pnl"] > 0.0),
                        "net_pnl_100_share_pair": round(pnl, 4),
                        "fees": round(sum(item["fees"] for item in selected), 4),
                        "return_on_entry_cost": round(pnl / entry_cost, 6) if entry_cost > 0.0 else None,
                        "independent_elections": 1 if len(selected) > 0 else 0,
                    }
                ]

remaining_rankable = [item for item in results if item["trades"] >= 5]
rankable = []
while len(remaining_rankable) > 0:
    best_index = 0
    for candidate_index in range(1, len(remaining_rankable)):
        if (
            remaining_rankable[candidate_index]["net_pnl_100_share_pair"]
            > remaining_rankable[best_index]["net_pnl_100_share_pair"]
        ):
            best_index = candidate_index
    rankable = rankable + [remaining_rankable[best_index]]
    remaining_rankable = [
        remaining_rankable[i]
        for i in range(len(remaining_rankable))
        if i != best_index
    ]
result = structured_return(
    "Versioned, TSE-matched runoff-poll changes were tested against executable Lula/Flavio relative trades.",
    {
        "poll_vintages": len(poll_time),
        "decision_events": len(events),
        "feature_rule_results": results,
        "ranked_minimum_five_trade_rules": rankable,
        "event_audit": event_rows,
        "trade_ready": False,
    },
    warnings=[
        "All observations belong to one election and are strongly dependent.",
        "Poll runoff percentages measure voting intention, not contract win probability.",
        "Canonical taker-side historical fills are real opportunities but not guaranteed fills for Chronos.",
        "The rule grid is exploratory development; no protected evidence was exposed.",
        "A 5% p*(1-p) fee approximation is charged on every simulated entry and exit leg.",
    ],
)
