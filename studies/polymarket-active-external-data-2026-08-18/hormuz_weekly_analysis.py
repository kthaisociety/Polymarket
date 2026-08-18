# ruff: noqa: ANN001, ANN201, D100, D103, E501, F821, INP001, PLR0913, PLR0917, PLR2004, RUF005

vintage_time = read("hormuz-git-vintages", "available_epoch")
vintage_latest_date = read("hormuz-git-vintages", "latest_date")
vintage_rolling7 = read("hormuz-git-vintages", "rolling7")
vintage_delta7 = read("hormuz-git-vintages", "delta7")
vintage_lag = read("hormuz-git-vintages", "source_lag_days")

fill_time = read("hormuz-fills", "fill_epoch")
fill_market = read("hormuz-fills", "market_id")
fill_side = read("hormuz-fills", "side")
fill_price = read("hormuz-fills", "price")
fill_size = read("hormuz-fills", "size")

market_ids = read("hormuz-markets", "market_id")
market_open = read("hormuz-markets", "open_epoch")
market_close = read("hormuz-markets", "close_epoch")


def execute(market_id, direction, action, start, end, shares):
    required_side = "SELL"
    invert = False
    if direction == "YES" and action == "SELL":
        required_side = "BUY"
    if direction == "NO" and action == "BUY":
        required_side = "BUY"
        invert = True
    if direction == "NO" and action == "SELL":
        required_side = "SELL"
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


eligible_vintages = []
previous_latest = ""
for i in range(len(vintage_time)):
    fresh = vintage_latest_date[i] > previous_latest
    if fresh:
        previous_latest = vintage_latest_date[i]
    if fresh and int(vintage_lag[i]) <= 7:
        eligible_vintages = eligible_vintages + [i]

horizon_results = []
for horizon_hours in [24, 168]:
    decisions = []
    for vintage_index in eligible_vintages:
        decision_time = int(vintage_time[vintage_index])
        for market_index in range(len(market_ids)):
            if decision_time >= int(market_open[market_index]) and decision_time < int(
                market_close[market_index]
            ):
                for direction in ["YES", "NO"]:
                    entry, entry_fee, entry_fill = execute(
                        market_ids[market_index],
                        direction,
                        "BUY",
                        decision_time,
                        decision_time + 21600,
                        100.0,
                    )
                    exit_start = decision_time + horizon_hours * 3600
                    exit_value, exit_fee, exit_fill = execute(
                        market_ids[market_index],
                        direction,
                        "SELL",
                        exit_start,
                        exit_start + 21600,
                        100.0,
                    )
                    if entry_fill >= 100.0 and exit_fill >= 100.0:
                        decisions = decisions + [
                            {
                                "vintage_index": vintage_index,
                                "market_id": market_ids[market_index],
                                "direction": direction,
                                "rolling7": round(float(vintage_rolling7[vintage_index]), 4),
                                "delta7": round(float(vintage_delta7[vintage_index]), 4),
                                "pnl": round(exit_value - entry - entry_fee - exit_fee, 4),
                                "fees": round(entry_fee + exit_fee, 4),
                            }
                        ]
    follow_rules = []
    for threshold in [0.0, 2.0, 5.0, 10.0]:
        selected = []
        for item in decisions:
            desired = "YES"
            if item["delta7"] < 0.0:
                desired = "NO"
            if item["direction"] == desired and abs(item["delta7"]) > threshold:
                selected = selected + [item]
        follow_rules = follow_rules + [
            {
                "minimum_abs_delta7": threshold,
                "trades": len(selected),
                "wins": sum(1 for item in selected if item["pnl"] > 0.0),
                "net_pnl_100_shares": round(sum(item["pnl"] for item in selected), 4),
                "market_count": len({item["market_id"] for item in selected}),
            }
        ]
    low_state_rules = []
    for ceiling in [10.0, 20.0, 40.0]:
        selected = [
            item for item in decisions if item["direction"] == "NO" and item["rolling7"] < ceiling
        ]
        low_state_rules = low_state_rules + [
            {
                "rolling7_ceiling": ceiling,
                "trades": len(selected),
                "wins": sum(1 for item in selected if item["pnl"] > 0.0),
                "net_pnl_100_shares": round(sum(item["pnl"] for item in selected), 4),
                "market_count": len({item["market_id"] for item in selected}),
            }
        ]
    horizon_results = horizon_results + [
        {
            "horizon_hours": horizon_hours,
            "eligible_publication_vintages": len(eligible_vintages),
            "directional_executable_rows": len(decisions),
            "follow_change_rules": follow_rules,
            "low_state_no_rules": low_state_rules,
        }
    ]

result = structured_return(
    "Historical PortWatch publication vintages were evaluated against direction-specific Polymarket fills.",
    {
        "horizons": horizon_results,
        "latest_retained_rolling7": round(float(vintage_rolling7[-1]), 4),
        "latest_retained_delta7": round(float(vintage_delta7[-1]), 4),
        "trade_ready": False,
    },
    warnings=[
        "All decisions belong to one geopolitical episode and are dependent across deadlines.",
        "Direction-specific fills are real transaction opportunities, not guaranteed fills for Chronos.",
        "Rules and thresholds are development-selected and have no protected event-family confirmation.",
    ],
)
