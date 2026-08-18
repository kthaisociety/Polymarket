# Hormuz traffic versus Polymarket: development result

Status: **direct traffic rules rejected; useful mechanism lesson; no trade**.

## Question and exact contract meaning

The active contracts ask whether Strait of Hormuz traffic will return to normal by a stated
deadline. `YES` requires IMF PortWatch to publish a seven-day moving average of at least 60 for
`n_total` (arriving ships) on any date through that deadline. The study therefore used the same
observable that resolves the market, rather than a proxy such as oil price or news sentiment.

This does **not** mean today's traffic level equals the contract probability. A contract trading
at 9 cents means the market prices roughly a 9% chance that the threshold will be reached before
the deadline. It is a forecast of a future regime change, not a measurement of today's ships.

## Time-legal and executable test

- Thirteen exact public-data vintages were reconstructed from committed OCHA PortWatch Git blobs.
- Ten fresh vintages had source lag of seven days or less and were eligible before inspection of
  later market fills.
- Three active deadline contracts had usable history: 31 August, 30 September, and 31 December.
- The production slice contains 24,921 canonical one-row-per-match taker fills from 12 May through
  18 August. A prior 71,271-row per-party ledger extraction was superseded before paper use because
  it contained both maker and taker legs.
- Entries and exits required 100 shares of direction-specific observed transaction opportunity
  inside fixed six-hour windows after the publication and after 24 or 168 hours.
- Entry and exit fees used `shares × 0.05 × price × (1-price)`.
- The run used Chronos `AuthorizedDataView`, field policy, isolated execution, source-code hash,
  actual-access provenance, and an immutable result receipt. Protected data was not exposed.

## Result

The obvious rules failed after fees:

| Rule | Horizon | Trades | Wins | Markets | Net P&L per sequence of 100-share trades |
|---|---:|---:|---:|---:|---:|
| Follow the sign of the weekly traffic change | 24 hours | 12 | 4 | 3 | -$22.8502 |
| Follow the sign of the weekly traffic change | 7 days | 12 | 4 | 2 | -$34.2559 |
| Buy NO when seven-day traffic was below 10 | 24 hours | 5 | 2 | 2 | -$6.1975 |
| Buy NO when seven-day traffic was below 10 | 7 days | 5 | 2 | 1 | -$20.6180 |
| Buy NO when seven-day traffic was below 40 | 24 hours | 10 | 3 | 2 | -$18.3997 |
| Buy NO when seven-day traffic was below 40 | 7 days | 11 | 5 | 2 | -$23.9571 |

No threshold cell was positive after the canonical taker-side replay. The least-negative
greater-than-10-ship seven-day cell lost **$1.0136 across two trades with one win**.

## What the negative result teaches

Current traffic is a state variable, but the contract is largely a **regime-switch probability**.
During the retained period, traffic remained far below the 60-ship resolution threshold. Small
week-to-week changes did not tell us whether a political or military reopening would occur before
August, September, or December. Three deadline markets also do not create three independent wars;
their errors are strongly dependent.

The useful next model is therefore not “ships rose, buy YES.” It would estimate a recovery hazard
from genuinely time-stamped geopolitical, shipping, insurance, naval, or diplomatic information,
then map that hazard into deadline-specific probabilities. That hypothesis requires multiple
independent disruption/recovery episodes or prospective releases before it can earn a protected
test.

## Limitations and disposition

The observed fills establish historical transaction opportunities, not guaranteed fills for a
new participant. Rules and thresholds were development-selected. All observations belong to one
geopolitical episode, current PortWatch history may revise older dates, and no independent event
family exists in the test. The direct traffic-level and traffic-change rules are rejected; no
current Hormuz position is recommended.

Exact harness evidence: [`hormuz-weekly-development.json`](hormuz-weekly-development.json).
