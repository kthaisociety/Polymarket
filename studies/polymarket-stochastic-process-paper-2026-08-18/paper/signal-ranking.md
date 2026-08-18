# Signal ranking: what Chronos tried and how close it came to a trade

Status: **paper-facing research summary; zero trade-ready signals**.

This ranking runs from least to most promising. It is not a leaderboard of comparable model
scores. A rejected trading rule, a useful movement-timing forecast, and a strong stochastic-process
law answer different questions. The ranking rewards survival of temporal and mechanism controls,
breadth across event groups, fresh or protected replication, proximity to directional return, and
the presence of executable quote/cost evidence. The machine-readable source is
[`signal-ranking.json`](signal-ranking.json).

| Rank | Tested idea | What survived | Why it is not tradable | Disposition |
|---:|---|---|---|---|
| 1 | Raw flow, size, runs, rolling and fractional transforms | Nothing after direction-neutral controls | Headline effects were transaction-side switching and sampled-price bounce | Rejected mechanical artifact |
| 2 | Bucket underround and bracket-overround compression | Some raw cross-leg discrepancies | Costs, stale legs, signal count, and event breadth failed | Rejected |
| 3 | Momentum and probability recalibration | Raw market probability remained a useful benchmark | Adjustments lost out of fold; no executable prices | Rejected |
| 4 | XTracker post-count forecasts | A discovery discrepancy only | It reversed on three untouched event families | Rejected on confirmation |
| 5 | PortWatch traffic changes and low-state Hormuz NO rules | Exact publication vintages and canonical taker fills across three deadlines | Every general rule lost; one geopolitical episode cannot identify recovery hazard | Rejected regime mismatch |
| 6 | Brazil runoff-poll changes versus Lula/Flávio relative prices | 31 exact TSE-matched vintages; some three-day gross fade response | Every five-trade rule lost after costs; one election and sparse paired execution | Rejected as direct trade; retain weak mechanism hint |
| 7 | Same-event sibling surface | Exploratory sibling-state gain | Gain vanished in expanding label-matured replay | Rejected formal branch |
| 8 | Boundary/volatility/magnitude models | State and inactivity helped relative magnitude prediction | Absolute gates failed; magnitude has no direction | Rejected formal branch |
| 9 | First-move direction and delayed continuation | No stable cross-event directional edge | Delay and cost screens were negative or concentrated | Rejected |
| 10 | Post-jump reversal-first hazard | Fresh development replication across 128 events | Sampled prices, mixed sign/stability controls, no protected quote test | Promising directional mechanism only |
| 11 | 48-hour meaningful-move incidence | Strong within-event ranking, positive in 13/13 eligible events | Failed calibration and has no direction | Promising eligibility component |
| 12 | Time to next meaningful move | Large OOF timing-error reduction | Predicts timing, not direction; protocol not protected-ready | Frozen development component |
| 13 | Zero-inflated marked-jump law | Won 112/113 development and 27/27 later event comparisons | Process density is not an executable trading rule | Strongest paper-level process result |
| 14 | Continuous quiet-duration arrival hazard | 33.38% later event-Brier improvement; formal gate passed; protected completed rows scored 0.189 | Protected coverage/failure/concentration failed; no direction or P&L | Most promising component; exact system rejected |
| 15 | Fade stale CME/FOMC probability gaps | Post-hoc 48-hour inverse made +$19.165 over seven fee-adjusted 100-share trades | One contract, overlapping sample, and rule/horizon selected after inspection | Most promising trade hypothesis; not validated |

## Standouts in plain English

1. **Best scientific result:** Polymarket probability samples behave like a sticky marked-jump
   process, not a smooth diffusion. This result is broad and reproduced, but it is a description
   and forecast of the sampled process rather than a trade.
2. **Best predictive component:** How long a contract has been quiet strongly predicts whether its
   next registered sample will change. The protected implementation still failed because 35% of
   declared decisions could not be executed.
3. **Closest internal directional lead:** Post-jump reversal replicated in fresh development data,
   but it has not survived a historical executable-book test with latency, depth, fees, and
   protected validation.
4. **Most useful negative lesson:** Large raw flow and transform correlations can be almost entirely
   manufactured by transaction direction. They should not be reported as alpha without a midpoint
   or same-direction control.
5. **Closest external-data trade hypothesis:** Following a dated CME probability lost at every
   tested FOMC decision. A post-hoc 48-hour fade was positive, but it is only a rule to replicate on
   fresh meetings; the current stale gap is an abstain, not a trade.
6. **Cleanest alternative-data rejection:** Exact PortWatch publication vintages and real Hormuz
   fills showed that neither weekly ship-count direction nor an extremely low traffic state made
   money. The missing quantity is the probability of a geopolitical reopening before each
   deadline, not a more elaborate transform of the current ship count.
7. **Best official-poll lesson:** Exact Brazil runoff-poll releases sometimes preceded a gross
   relative-price response, but no follow/fade rule paid for four crossed legs. Poll percentages
   are voting-intention measurements, not candidate win probabilities.

## Paper-safe conclusion

Chronos found reproducible statistical structure and several useful model components. It did not
find a validated trading strategy. Any future trading claim needs a directional label, legal
historical quotes or prospective paper fills, spread/depth/latency/cost accounting, event-grouped
temporal evaluation, and a fresh protected cohort. The previously exposed arrival-hazard holdout
cannot become fresh again.
