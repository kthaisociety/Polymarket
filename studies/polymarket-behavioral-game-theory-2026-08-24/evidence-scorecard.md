# Behavioral/game-theoretic strategy evidence scorecard

Status: **PROGRAM AUDIT COMPLETE — NO EXECUTION-VALIDATED STRATEGY**.

This scorecard compares evidence maturity, not effect sizes from unlike questions. It is generated
from the exact sources and receipts verified by
[`audit_program_evidence.py`](audit_program_evidence.py) and
[`program-evidence-audit.json`](program-evidence-audit.json). Development chronology, fresh-event
replication, protected exposure, and executable validation are separate claims.

## Evidence vocabulary

| Tier | Meaning |
|---|---|
| 1 — Blocked/not tested | A data, semantic, clock, or authority gate failed before strategy values |
| 2 — Exploratory development | Selection-exposed development evidence; chronological splits are diagnostics, not fresh OOS |
| 3 — Fresh development replication | Fixed question executed on events absent from the selection corpus, with the final block still protected |
| 4 — Protected result | Governed holdout exposure; may still lack executable prices or coverage |
| 5 — Execution-validated | Legal historical quotes or prospective fills with spread, depth, latency, fees and failures |

No behavioral, time-series, or low-latency strategy in this comparison reaches tier 5.

## Behavioral and game-theoretic program

| Branch | Mechanism and fixed action | Evidence/OOS tier | Leakage and dependence controls | Cost evidence | Result |
|---|---|---|---|---|---|
| B1 skilled-wallet response | Follow fold-local high-skill takers | Tier 2; skill trains on earlier resolved events and evaluates later development events, but the overall branch is selection-exposed | Labels mature before training cutoff; event macro; delayed entry; price, side, horizon, momentum and activity matching; chronological halves | Recorded fills initially; later 1¢ delayed sampled-price hurdle, not executable quotes | Rejected after combined controls: matched increment `+0.00383`, below 1¢; high-skill edge `+0.07127` early and `−0.02697` late |
| B2 expert consensus | Follow agreement among distinct high-skill wallets | Tier 2 development | One vote per wallet/market/hour; delayed entry; single-high and non-high-crowd rivals; event macro and chronology | 1¢ sampled-price hurdle | Rejected: trails single-high rival by `−0.01468`; crowd comparison reverses strongly across time |
| B3 longshot fade | Buy complement when selected-outcome probability is 2–10% | Tier 2 development only; exact frozen fresh source has not run | Immutable corpus; whole-event 80/20 boundary; fixed horizons/bands; adjacent 10–20% rival; event macro; chronology | 2¢ sampled-price hurdle | Only surviving behavioral lead: net `+0.00160/+0.01842` at 72h/168h and paired adjacent-band advantage `+0.05259/+0.11654`; all 70 novel events remain protected, so fresh OOS evidence is absent |
| B3 favorite follow | Buy selected outcome at 90–98% | Tier 2 development | Same fixed corpus, rival and event controls as longshot branch | 2¢ sampled-price hurdle | Rejected: negative event-macro edge at both horizons and inadequate 168h breadth |
| B4 focal anchoring | Trade barrier/breakout at salient probability levels | Tier 2 development | First crossing per market/level; nearby non-focal controls; event macro; chronological halves | No executable cost model; sampled path only | Rejected: focal-minus-control `−0.00113` at 24h, below gate, with early/late sign reversal |
| B5 disposition effect | Fade cost-basis-conditioned winner selling/loser holding | Tier 1; not tested | Predeclared historical inventory replay requires complete fills plus split/merge/redemption history | None | Blocked correctly: global cursor reached genesis, but 7,162/9,905 market repair spans remained pending, so gain/loss states could be false |
| B6 NegRisk complete set | Buy every venue-authorized YES leg when total executable cost is below guaranteed payout | Tier 1; no basket value inspected | Exact event/NegRisk/YES mapping and full-leg coverage audited; causal history requires dual clocks and retained event bytes | None; fees/depth/fills deliberately deferred | 1,013 semantic candidates and six complete current-top scopes exist, but production snapshot/delta tables lack `reference_time`; no historical causal replay |
| B7 crowded extrapolation | Fade a broad wallet crowd chasing an existing 6h move | Tier 2 development | One wallet vote per hour; pending-repair markets excluded; delayed entry; thin-trend and crowded-flat component rivals; event macro and chronology | 1¢ sampled-price hurdle | Rejected: only 25 signals/14 events; fades lose `−0.04259` at 6h, `−0.06854` at 24h and `−0.06405` to settlement |
| B8 ambiguity aversion | Buy moderate-probability selected outcomes with fixed complex-question proxy | Tier 2 development | Immutable corpus; frozen text categories; one 168h sample; simple wording rival inside event/5-point band | 2¢ sampled-price hurdle | Rejected: only two eligible complex markets in one event, `−0.445` net edge, no paired cells; title text is an inadequate ambiguity proxy |

## Fair comparison with prior time-series research

| Prior program | Evidence tier | What is genuinely stronger | What remains weaker than a trading claim |
|---|---|---|---|
| Fresh post-jump reversal-first hazard | Tier 3 fresh development replication | Fixed question passed on 6,174 OOF shocks, 410 markets and 128 fresh events; one-cent sampled-price screen returned `+0.04103` event-macro over 70 events | Sampled probabilities, not historical asks/bids/depth; no protected execution validation |
| Zero-inflated marked-jump law | Tier 3 fresh replication | Broadest reproducibility: beat rivals on 112/113 development and 27/27 later events | Describes process/arrival/magnitude, not a directional trade; no P&L claim |
| Continuous arrival hazard | Tier 4 protected negative | Reached a governed protected run, a higher evidence tier than any behavioral candidate | Failed protected coverage, failure-rate and concentration requirements; non-directional and not tradable |
| B3 longshot fade | Tier 2 development | Strongest behavioral result and beats an adjacent probability-state rival after a fixed 2¢ hurdle | Weaker evidence than fresh reversal because it has zero legal successor events and no quote execution |

The correct scientific ranking is therefore not “B3 wins because its development edge is large.”
Fresh post-jump reversal has stronger out-of-sample support. The marked-jump law has stronger
reproducibility but is not a strategy. B3 is the best behavioral candidate only within tier 2.

## Fair comparison with the low-latency program

| Low-latency branch | Mechanism | Empirical tier | Current evidence |
|---|---|---|---|
| H1 cross-venue payout dominance | Mechanical guaranteed-payout lower bound | Tier 1 | Exact semantic direction exists; no simultaneous symmetric executable book corpus |
| H2 print lead-lag | Cross-venue information transmission | Tier 2 exploratory scout, rejected | One-sided sparse prints, unstable slices, zero median response and negative reverse-window comparison |
| H3 quote-confirmed reversal | Microstructure reversal after book shock | Tier 1 for quote strategy | Implementation and synthetic mechanics exist; no deployed dual-clock corpus |
| H4 activity gate | Participate when quiet-duration/activity state improves parent strategy | Tier 1 for strategy | Strong prior arrival mechanism, but thresholds/campaign have no production L2 values or execution |
| H5 depth imbalance | Multi-level order pressure | Tier 1 | Replay code exists; no retained causal production corpus or empirical result |
| B6 NegRisk complete set | Same-venue coordination failure | Tier 1 | Stronger venue grouping than semantic inference, abundant current candidates, but same simultaneous-depth/fill gate as H1 |

Code, tests and fixed policies are readiness evidence, not alpha. Production currently runs without
the two clock columns; the existing local implementation cannot be treated as deployed data.

## Program conclusion

Chronos successfully discovered and falsified multiple behavioral/game-theoretic strategies under
explicit information, event, chronology, rival and cost boundaries. The result is scientifically
useful but commercially negative:

- no execution-validated strategy exists;
- B1, B2, B4, B7 and B8 are rejected;
- favorite-follow is rejected;
- B5 and B6 were withheld rather than tested on invalid data;
- B3 longshot fade is the sole behavioral development lead, below the evidence tier of fresh
  post-jump reversal and awaiting untouched successor events;
- mechanical H1/B6 remain the cleanest payoff identities but have no causal book/fill evidence.

The next evidence-changing observations are externally defined: at least 404 retained events for a
minimum B3 fresh replay, or reviewed deployment plus a fresh full-event dual-clock capture for B6.
Neither missing observation weakens the completed negative results or upgrades the current lead.
