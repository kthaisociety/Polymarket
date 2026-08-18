# ruff: noqa: ANN001, ANN201, D100, D103, E501, F821, FBT003, INP001, PLR2004, RUF005

cme_times = read("cme-fedwatch", "available_at_epoch")
cme_values = read("cme-fedwatch", "probability_375_400")
book_targets = read("polymarket-fomc-books", "target_epoch")
book_times = read("polymarket-fomc-books", "snapshot_epoch")
book_bids = read("polymarket-fomc-books", "bids")
book_asks = read("polymarket-fomc-books", "asks")


def levels_at(target):
    for i in range(len(book_targets)):
        if book_targets[i] == target:
            return (book_bids[i], book_asks[i], book_times[i])
    return ([], [], 0)


def buy(levels, shares, ascending):
    ordered = sorted(levels)
    if not ascending:
        ordered = sorted(levels, reverse=True)
    remaining = shares
    notional = 0.0
    fees = 0.0
    filled = 0.0
    for level in ordered:
        price = float(level[0])
        size = float(level[1])
        take = min(remaining, size)
        notional = notional + take * price
        fees = fees + take * 0.05 * price * (1.0 - price)
        remaining = remaining - take
        filled = filled + take
        if remaining <= 0.0000001:
            break
    if filled < shares:
        return (0.0, 0.0, filled)
    return (notional, fees, filled)


def sell(levels, shares, ascending):
    return buy(levels, shares, ascending)


horizon_results = []
for horizon_hours in [6, 12, 24, 48]:
    trades = []
    for i in range(len(cme_times)):
        entry_target = int(cme_times[i])
        exit_target = entry_target + horizon_hours * 3600
        entry_bids, entry_asks, entry_time = levels_at(entry_target)
        exit_bids, exit_asks, exit_time = levels_at(exit_target)
        if (
            len(entry_bids) > 0
            and len(entry_asks) > 0
            and len(exit_bids) > 0
            and len(exit_asks) > 0
        ):
            yes_ask = min(float(level[0]) for level in entry_asks)
            yes_bid = max(float(level[0]) for level in entry_bids)
            yes_gap = float(cme_values[i]) - yes_ask
            no_gap = (1.0 - float(cme_values[i])) - (1.0 - yes_bid)
            direction = "YES"
            gap = yes_gap
            if no_gap > yes_gap:
                direction = "NO"
                gap = no_gap
            if direction == "YES":
                entry_cost, entry_fee, entry_fill = buy(entry_asks, 100.0, True)
                exit_value, exit_fee, exit_fill = sell(exit_bids, 100.0, False)
                fade_entry_levels = [
                    [1.0 - float(level[0]), float(level[1])] for level in entry_bids
                ]
                fade_exit_levels = [[1.0 - float(level[0]), float(level[1])] for level in exit_asks]
                fade_entry_cost, fade_entry_fee, fade_entry_fill = buy(
                    fade_entry_levels, 100.0, True
                )
                fade_exit_value, fade_exit_fee, fade_exit_fill = sell(
                    fade_exit_levels, 100.0, False
                )
            else:
                no_entry_asks = [[1.0 - float(level[0]), float(level[1])] for level in entry_bids]
                no_exit_bids = [[1.0 - float(level[0]), float(level[1])] for level in exit_asks]
                entry_cost, entry_fee, entry_fill = buy(no_entry_asks, 100.0, True)
                exit_value, exit_fee, exit_fill = sell(no_exit_bids, 100.0, False)
                fade_entry_cost, fade_entry_fee, fade_entry_fill = buy(entry_asks, 100.0, True)
                fade_exit_value, fade_exit_fee, fade_exit_fill = sell(exit_bids, 100.0, False)
            pnl = exit_value - entry_cost - entry_fee - exit_fee
            fade_pnl = fade_exit_value - fade_entry_cost - fade_entry_fee - fade_exit_fee
            trades = trades + [
                {
                    "decision_epoch": entry_target,
                    "quote_age_seconds": entry_target - int(entry_time),
                    "exit_quote_age_seconds": exit_target - int(exit_time),
                    "cme_probability": round(float(cme_values[i]), 6),
                    "direction": direction,
                    "gross_gap": round(gap, 6),
                    "entry_cost": round(entry_cost, 4),
                    "fees": round(entry_fee + exit_fee, 4),
                    "pnl_100_shares": round(pnl, 4),
                    "fade_pnl_100_shares": round(fade_pnl, 4),
                    "filled": min(entry_fill, exit_fill),
                    "fade_filled": min(fade_entry_fill, fade_exit_fill),
                }
            ]
    thresholds = []
    for threshold in [0.0, 0.02, 0.04, 0.06, 0.08, 0.10]:
        selected = [item for item in trades if item["gross_gap"] >= threshold]
        pnl = sum(item["pnl_100_shares"] for item in selected)
        wins = sum(1 for item in selected if item["pnl_100_shares"] > 0.0)
        fade_pnl = sum(item["fade_pnl_100_shares"] for item in selected)
        fade_wins = sum(1 for item in selected if item["fade_pnl_100_shares"] > 0.0)
        thresholds = thresholds + [
            {
                "threshold": threshold,
                "trades": len(selected),
                "wins": wins,
                "net_pnl_100_shares": round(pnl, 4),
                "fade_wins": fade_wins,
                "fade_net_pnl_100_shares": round(fade_pnl, 4),
            }
        ]
    horizon_results = horizon_results + [
        {
            "horizon_hours": horizon_hours,
            "completed_decisions": len(trades),
            "trades": trades,
            "thresholds": thresholds,
        }
    ]

result = structured_return(
    "CME-versus-Polymarket FOMC development evaluation completed.",
    {
        "horizons": horizon_results,
        "trade_ready": False,
    },
    warnings=[
        "One active contract and at most seven completed 24-hour decisions cannot establish generalization.",
        "CME date-only rows use conservative next-calendar-day noon availability.",
        "Historical order books are executable L2 snapshots, but fills are simulated and exclude latency.",
    ],
)
