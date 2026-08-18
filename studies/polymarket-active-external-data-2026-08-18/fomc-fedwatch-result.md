# FOMC versus CME FedWatch: development result

Status: **direct signal rejected; 48-hour fade is hypothesis generation only; no trade**.

## Question

Does CME FedWatch give an independent probability for the 16 September 2026 `+25 bp` Fed outcome
that can be traded against the exact active Polymarket contract?

The mapping is exact: with the pre-meeting target range at `350-375`, CME's `375-400` column and
Polymarket's `+25 bp` outcome describe the same terminal range. Because CME's historical CSV gives
only a date, Chronos delayed every row until noon UTC on the next calendar day.

## Executable test

- One exact active Polymarket YES token.
- Eight conservative CME decision times; seven have all tested exits.
- Historical L2 snapshots no more than 15 minutes old; actual ages were 10-507 seconds.
- 100-share marketable orders walked through visible depth.
- Taker fees used `shares × 0.05 × price × (1-price)` on entry and exit.
- Fixed horizons: 6, 12, 24, and 48 hours.
- Gap thresholds: 0, 2, 4, 6, 8, and 10 cents.

## Result

Following CME meant buying Polymarket YES because CME's dated probability was 7.0-12.2 cents above
the executable YES ask. This lost at **every completed decision at every horizon**:

| Horizon | Decisions | Wins | Net P&L per sequence of 100-share trades |
|---:|---:|---:|---:|
| 6 hours | 8 | 0 | -$44.2455 |
| 12 hours | 7 | 0 | -$44.1605 |
| 24 hours | 7 | 0 | -$49.0750 |
| 48 hours | 7 | 0 | -$62.7940 |

The apparent external "mispricing" was stale information, not cheap Polymarket probability.
The live page/market comparison therefore receives an abstain decision as well.

After observing the failure, a diagnostic inverted the trade. Buying NO instead made +$19.165 at
48 hours across seven overlapping decisions, with four winners. This is **not validated alpha**:
it was selected after seeing four horizons, contains one contract and one short regime, overlaps in
time, has no independent event, and CME rows lack historical intraday publication timestamps.

## Paper value

This is a clean negative result about alternative-data alignment: semantically matching two
probabilities is insufficient. Freshness and historical availability dominate the headline gap.
The 48-hour fade is worth a predeclared replication on future FOMC meetings or other rate-decision
contracts, but must not be represented as currently tradable.

Exact evidence: [`fomc-fedwatch-final-development.json`](fomc-fedwatch-final-development.json).
