# Polymarket behavioral and game-theoretic strategy discovery

Epistemic status: **PROGRAM AUDIT COMPLETE — NO EXECUTION-VALIDATED STRATEGY**.

## Mandate

Discover plural Polymarket strategies whose mechanism comes from game theory or behavioral
economics, test them against actual contract-level production facts, and compare them under the same
scientific standards as the prior time-series and low-latency program.

The server is the primary data source. Production access is constrained to the proved `human_ro`
role. Exact source bytes or sanitized receipts are retained locally; production is never mutated.

## Live data suitability audit

The audit was run on 2026-08-24 through a localhost-only SSH tunnel. The connection proved role
`human_ro`, session and transaction read-only state, and denied insert/update privileges. The
sanitized result is retained in [`server-data-audit.json`](server-data-audit.json).

Usable development surfaces:

| Surface | Live coverage observed | Scientific use | Binding caveat |
|---|---:|---|---|
| Contract metadata | 15,647 Polymarket markets, 2,677 event groups | Exact questions, lifecycle, event dependence | One missing event ID; text does not by itself prove exhaustive partitions |
| On-chain resolutions | 3,109 binary payout vectors | Mature outcome labels at recorded settlement | Use on-chain payouts, not Gamma `is_winner` |
| Sampled prices | 3,933,307 points across 13,144 markets in 7 days | Calibration, anchoring, path and state screens | Samples are not executable quotes |
| Taker prints | 446,155 prints, 35,345 wallets, 8,675 markets in 7 days | Wallet skill, costly-signal and cascade screens | Availability is block inclusion; filter the per-party ledger to the taker aggregate leg |
| Resolved taker history | 710,731 prints across 3,011 resolved markets and 47,617 wallets in 30 days | Fold-local wallet reputation and agreement tests | Historical skill must mature only after each market resolves |
| L2 deltas | 2,125,154 rows across 30 markets in 24 hours | Collector-time persistence and book-state exploration | Deployed tables lack `reference_time`; no sub-second causal latency claim |

Two adversarial checks matter immediately:

1. `market.fills` is a per-party ledger. Reading all 1,146,454 recent rows would double count match
   volume and mechanically offset signed flow. The database adapter's taker-leg predicate yields 446,155
   one-row-per-match aggregate prints.
2. Gamma resolved prices are near terminal (`0.9995`/`0.0005`) and its exact-equality-derived
   `is_winner` field is therefore unusable in the observed cohort. Against 105 contracts with both
   sources, the direction of Gamma's terminal price agrees with the direct on-chain payout ordering
   in 210/210 outcome cells and with the reversed order in 0/210. Chronos uses the on-chain vector.

## Candidate strategy program

### B1 — Fold-local skilled-wallet response

- Mechanism: privately informed or analytically skilled traders pay a cost to acquire information;
  their aggressive trades are more credible than anonymous price movement.
- Signal: net taker-side flow from wallets whose performance was estimated only from markets
  resolved before decision time, shrunk toward the population mean.
- Action/target: follow skilled-wallet consensus after block inclusion; measure 1-hour, 6-hour, and
  24-hour executable midpoint movement and eventual payout calibration.
- Rivals: wallet size, liquidity provision, topic specialization, common news, and survivorship.
- Falsifier: no incremental chronological value over raw flow, price state, volume, and the existing
  arrival/staleness model.
- Status: **DEVELOPMENT MECHANISM LEAD; ADVERSARIAL FOLLOW-UP ACTIVE**. The first fold-local test
  passed its informativeness gate at recorded fill prices. Fixed state matching, delayed public
  entry, costs, and chronology are preregistered below.

### B2 — Expert agreement versus crowd cascade

- Mechanism: information cascades can make many agents repeat public behavior without independent
  information; agreement among independently skilled wallets should be more credible than raw
  wallet count.
- Signal: distinct aggressive-wallet count, concentration, skill-weighted agreement, and the share
  of flow explained by the first mover in a fixed block-time window.
- Action/target: continuation for dispersed skilled agreement; reversal/exhaustion for concentrated
  unskilled herding, tested as explicit rivals.
- Rivals: one large order split across transactions, event-wide public news, and price-induced
  selection.
- Falsifier: wallet dispersion and skill do not improve on total flow and current price movement.
- Status: **ADVERSARIAL DEVELOPMENT TEST PREREGISTERED**. Distinct-wallet, skill-weighted agreement
  is tested separately from raw crowd flow under the delayed-entry protocol below.

### B3 — Probability weighting / favorite-longshot bias

- Mechanism: traders overweight small probabilities and may underweight large probabilities.
- Signal: fixed pre-close probability bands, event-equal calibration residuals, and semantic/time
  controls.
- Action/target: buy NO against overpriced longshot YES or buy YES on underpriced favorites only
  when delayed executable quotes cover fees and spread.
- Rivals: selection, topic mix, time-to-close, stale sampling, and non-executable marks.
- Falsifier: calibration gaps vanish under event weighting, chronological splits, or executable
  prices.
- Status: **SAMPLED-PRICE LEAD ONLY**. Prior development evidence showed broad overprediction but
  already established strong cohort/topic heterogeneity.

### B4 — Focal-price anchoring barrier or breakout

- Mechanism: salient probabilities can anchor beliefs and limit-order placement. A focal level may
  behave as a reflection barrier or, after coordinated escape, as a breakout threshold.
- Signal: first local directional crossing per market and level at focal probabilities
  `0.10/0.25/0.50/0.75/0.90`, compared with fixed nearby controls
  `0.15/0.30/0.55/0.70/0.85`.
- Action/target: signed continuation at elapsed 6 and 24 hours.
- Rivals: bounded state dynamics, generic round ticks, large news jumps, and event composition.
- Falsifier: focal-minus-control continuation is economically trivial, chronologically unstable,
  or lacks event breadth.
- Status: **FIRST PREDECLARED DEVELOPMENT SCREEN**; protocol below.

### B5 — Disposition-driven liquidity response

- Mechanism: loss aversion and the disposition effect can make holders sell winners too early and
  retain losers, changing supply after price moves.
- Signal: fold-reconstructed wallet cost basis, unrealized gain/loss, and subsequent maker/taker
  behavior.
- Action/target: fade predictable inventory release or demand withholding after controlling for
  public price movement.
- Rivals: tax/portfolio constraints, market resolution proximity, and mechanically forced exits.
- Falsifier: gain/loss state adds no chronological information after wallet and market fixed
  effects.
- Status: **REJECTED ON CURRENT DATA READINESS**. The local replay can process fills plus splits, merges,
  and redemptions, and the global history cursor has reached genesis. However, 7,162 of 9,905
  market-scope repair spans were pending at the 2026-08-24 audit. Current-position rows cannot be
  used as past information, and incomplete prehistory can manufacture gain/loss states, so no B5
  mechanism or strategy test was run.

### B6 — Complete-set coordination failure

- Mechanism: mutually exclusive, exhaustive event outcomes should obey an executable add-up
  constraint; fragmented attention and capital can delay coordination.
- Signal: sum of executable asks below one or bids above one across semantically proved complete
  sets, net of fees and partial-fill constraints.
- Action/target: atomic or conservatively sequenced complete-set trade.
- Rivals: non-exhaustive wording, resolution-rule asymmetry, stale legs, and incomplete fills.
- Falsifier: no net edge using simultaneous executable depth and authoritative event semantics.
- Status: **LIVE OPPORTUNITY SET EXISTS; HISTORICAL STRATEGY TEST DATA-BLOCKED**. Production has
  1,013 open multi-leg NegRisk semantic candidates and six events with every YES leg represented in
  current collector top state. One current ten-leg event has all legs on the same sweep. However,
  the deployed snapshot and delta tables still lack `reference_time`, and exact Gamma event bytes
  proving exhaustive membership are not retained. No basket value was inspected. B6 requires the
  existing dual-clock migration to deploy, a fresh full-event capture, exact event retention, and
  depth/fee/fill-aware replay.

### B7 — Crowded extrapolation exhaustion

- Mechanism: an information cascade may cause many distinct aggressive wallets to extrapolate an
  already-salient move; delayed reversal would indicate attention-driven overreaction.
- Signal: at least five distinct wallet votes with 75% agreement in one market/hour, aligned with
  a six-to-eight-hour probability move of at least five points. One or two unanimous wallets on the
  same trend and a broad crowd after a flat path are fixed component rivals.
- Action/target: fade after a one-to-two-hour sampled-price delay; measure 6-hour and 24-hour paths
  and one-cent-hurdled settlement edge.
- Status: **REJECTED IN DEVELOPMENT**. Only 25 candidate signals across 14 events survived the
  fixed filters. Fade returns were `-0.04259` at 6 hours and `-0.06854` at 24 hours; settlement
  edge was `-0.06405`, with an early/late sign reversal. Sampled prices continued with the crowd,
  and no fixed rival cell reached common support.

### B8 — Ambiguity aversion from question complexity

- Mechanism: traders may discount propositions with conditional, alternative, or boundary-heavy
  resolution language beyond what current probability warrants.
- Signal: a frozen four-category title-level complexity score; buy the selected outcome seven days
  before close only at probability `[0.20,0.80]`, with simple wording in the same event/five-point
  band as the rival.
- Status: **REJECTED AS AN INADEQUATE PROXY AND LOSING FIXED STRATEGY**. Only 13 of 1,152 questions
  scored complex, and just two moderate-probability markets in one event were trade-eligible. Their
  two-cent-hurdled net edge was `-0.445`; no paired control cell existed. The threshold remains
  frozen rather than being weakened after inspection. This does not reject ambiguity aversion in
  general because descriptions and complete resolution rules are absent from the retained corpus.

## Predeclared focal-price screen

The first empirical screen uses retained production snapshot
`polymarket-corpus:184b83f7f8012da4ca9116c8b6bad2076570ad5f0bada95b22615ee2f5cceae8`.
Chronos exposes only the earlier 80% whole-event development block; the latest event block remains
hidden.

- Each market contributes at most its first local crossing of each focal/control level.
- A crossing requires consecutive samples 45-75 elapsed minutes apart and both prices within five
  probability points of the level. Large jumps that merely skip over a level are excluded.
- Targets are the nearest legal later samples to 6 hours (tolerance 1 hour) and 24 hours (tolerance
  2 hours).
- The signed target is crossing direction times subsequent probability change.
- The primary comparison is paired event-macro focal-minus-control signed continuation at 24 hours;
  6 hours, per-level rows, positive-continuation rates, and chronological halves are diagnostics.
- Barrier support requires focal-minus-control continuation at or below `-0.0025` at both horizons,
  the same negative sign in both 24-hour chronological halves, at least 100 focal signals, and at
  least 30 paired events at 24 hours. Breakout support is the symmetric positive rule. Anything
  else is `NO_STABLE_FOCAL_EFFECT`.

This rule was fixed before executing [`01_focal_price_anchoring.py`](source/01_focal_price_anchoring.py).
It is a behavioral mechanism screen over sampled probabilities, not an executable return test.

### Focal-price screen result

Status: **NO_STABLE_FOCAL_EFFECT**.

- Coverage passed: 1,537 focal signals at 6 hours, 1,480 at 24 hours, and 221 paired
  event groups at 24 hours.
- Paired event-macro focal-minus-control continuation was `+0.00080` at 6 hours and
  `-0.00113` at 24 hours, both below the absolute `0.0025` gate.
- The 24-hour difference changed from `+0.01538` in the early chronological half to
  `-0.01529` in the late half.
- Individual levels were heterogeneous; that does not permit selecting the best level after this
  screen. The universal anchoring strategy is rejected and retained.
- Exact receipt: [`01_focal_price_anchoring.json`](development-receipts/01_focal_price_anchoring.json).

## Predeclared skilled-wallet informativeness screen

The second screen uses the production taker tape and on-chain payout vectors at server transaction
time. Whole event groups are ordered by their latest market-resolution time: the first 60% form the
training block, the next 20% form the development evaluation block, and the final 20% are embargoed
from value queries by this source.

- The database adapter's taker aggregate-leg predicate reduces each Polymarket match bundle to one aggressive
  wallet row. The per-party ledger is never summed directly.
- Wallet skill is the equal-market mean of signed settlement edge from training fills in the
  probability band `[0.05, 0.95]`: `payout - fill_price` for BUY and `fill_price - payout` for SELL.
- Training labels all mature by the fixed training cutoff. Evaluation admits only fills strictly
  after that cutoff and before the evaluated market's own resolution.
- The skill estimate is shrunk by `n_markets / (n_markets + 10)`. A wallet is eligible after five
  distinct training markets; `HIGH_SKILL` requires shrunk edge at least `+0.02`, and `LOW_SKILL`
  requires at most `-0.02`.
- Primary evidence is event-macro signed settlement edge for `HIGH_SKILL` versus `ALL`, with early
  and late evaluation halves. Fill- and market-weighted views remain diagnostics.
- Mechanism support requires at least 30 evaluation events and 1,000 high-skill fills, positive
  high-skill event-macro edge in both chronological halves, and at least a one-percentage-point
  event-macro improvement over all flow. Otherwise the strategy remains unsupported.

The source is [`02_fold_local_skilled_wallet.sql`](source/02_fold_local_skilled_wallet.sql). Even a
positive result would establish wallet informativeness at recorded fill prices, not an executable
post-block-entry strategy; delayed quotes, fees, and impact remain a separate test.

### Skilled-wallet screen result

Status: **MECHANISM SUPPORTED FOR EXECUTABLE FOLLOW-UP — NOT A TRADING FINDING**.

- The high-skill cohort covered 14,910 evaluation fills, 191 markets, and 61 event groups.
- High-skill event-macro signed settlement edge was `0.04140`, compared with `0.01669` for all
  aggressive flow: an improvement of `0.02471`.
- High-skill event-macro edge was positive in both halves (`0.02037` early, `0.05504` late), and
  70.5% of eligible events were positive.
- The predeclared mechanism gate passed. The improvement is nevertheless concentrated late: the
  early high-skill edge was essentially the same as all flow (`0.02040`).
- Low-skill wallets also retained positive development edge, so the reputation score is not a
  stable symmetric ranking. Price state, activity, event mix, wallet specialization, and execution
  delay are required adversaries before this can advance.
- Exact receipt: [`02_fold_local_skilled_wallet.json`](development-receipts/02_fold_local_skilled_wallet.json).

## Preregistered adversarial wallet tests

The follow-up packet freezes the live database ceiling at
`2026-08-24T09:13:44.071211+00:00`, the same recorded server transaction time as the suitability
audit. Resolutions, fills, and sampled prices after that instant are excluded. The first 60% of
whole event groups ordered by resolution remains training, the next 20% remains development, and
the final 20% remains embargoed from payout/value queries.

### B1 matched-state falsification

- `HIGH_SKILL` retains the exact prior definition: at least five training markets and shrunk
  equal-market settlement edge of at least `+0.02`; every other evaluation taker is `NON_HIGH`.
- Comparisons occur only inside the same event, aggressor side, fixed five-percentage-point fill
  price band, and time-to-resolution band (`<=24h`, `24-72h`, `72-168h`, `>168h`).
- A cell must contain at least five fills from each cohort. Cells are averaged within events, then
  events are averaged equally.
- The candidate survives only with at least 30 matched events and 100 matched cells,
  high-minus-non-high event-macro edge at least `+0.010`, and a non-negative difference in both
  chronological halves.

### B1 delayed public-entry stress test

- Binary-token fills map to one canonical outcome-0 vote per wallet and market in each UTC hour:
  BUY outcome 0 and SELL outcome 1 vote positive; SELL outcome 0 and BUY outcome 1 vote negative.
  The wallet's final aggressive fill in the hour fixes the vote and prevents equivalent outcome
  tokens or intrahour order splitting from inflating coverage.
- Entry is the first fidelity-60 sampled probability from one to two elapsed hours after the final
  fill in that signal bucket. A missing sample means no covered signal; there is no fallback to the
  original fill price.
- BUY settlement edge is `payout - delayed_price`; SELL edge is `delayed_price - payout`. A fixed
  `0.010` adverse-execution hurdle is deducted from every signal.
- Evidence is equal-market within event and equal-event overall. The candidate survives only with
  at least 30 events and 1,000 covered high-skill signals, positive high-skill net event-macro edge
  in both halves, and high-minus-non-high event-macro net edge at least `+0.010`.

### B2 distinct-expert consensus

- Each high-skill wallet votes at most once per binary market and UTC hour after the canonical
  outcome-0 mapping. A consensus requires
  at least two wallets, at least 75% agreement by wallet count, and no tie.
- Decision time is the end of the hourly bucket; entry uses the first fidelity-60 sampled price
  between one and two elapsed hours later, with the same fixed `0.010` hurdle.
- Fixed rivals are a single-high-skill signal in that hour and the corresponding non-high crowd
  direction. The candidate survives only with at least 30 events and 500 covered consensus
  signals, positive net event-macro edge in both chronological halves, and at least `+0.010`
  advantage over each rival.

All three screens use sampled public prices, not executable quotes. A pass permits only fresh,
untouched evaluation after immutable retention; it does not prove tradability.

### Combined delayed-state gate for B1

The generic delayed B1 result is not sufficient because its paired early-half advantage can remain
negative and the separate fill-price state match can fail. Before executing the combined test, the
following stricter gate is fixed:

- Match high-skill and non-high signals inside the same event, canonical direction, five-point
  delayed-entry price band, time-to-resolution band, momentum state, and activity band.
- Momentum is delayed entry minus the latest fidelity-60 public mark at or before the wallet signal
  and no more than two hours old: `DOWN` at or below `-0.02`, `UP` at or above `+0.02`, otherwise
  `FLAT`.
- Activity is the number of distinct wallet votes in the same market/hour, binned as `1`, `2-4`,
  `5-9`, and `10+`. Each matched cell requires at least three signals from each cohort.
- Survival requires at least 25 matched events and 75 cells, equal-event high-minus-non-high net
  edge of at least `+0.010`, non-negative differences in both chronological halves, and positive
  high-skill net event-macro edge in both halves.

This combined gate is the decision test for the narrow B1 candidate. The earlier generic delay pass
cannot override a failure here.

## Adversarial wallet results

### B1 — rejected after combined controls

The generic delayed screen initially appeared favorable: 9,837 high-skill wallet-hour signals
covered 61 events, net event-macro settlement edge after the one-cent hurdle was `+0.03335`, and
the paired advantage over non-high flow was `+0.01668`. That lead was not chronologically clean:
the paired advantage was `-0.01764` early and `+0.03895` late.

The preregistered decision screens rejected it:

- At recorded fill prices, matching event, side, five-point price band, and resolution horizon
  reduced high-minus-non-high edge to `+0.00867`, below the `+0.010` gate.
- With the one-hour delayed mark and one-cent hurdle, additionally matching entry price, momentum,
  wallet activity, direction, horizon, and event reduced the advantage to `+0.00383` across 773
  cells and 41 events.
- In the combined test, the high-skill net edge flipped from `+0.07127` early to `-0.02697` late;
  the matched incremental difference was `-0.00213` early and `+0.00849` late. Only 36.6% of
  matched events favored high-skill flow.

Status: **REJECT FIXED B1 CANDIDATE**. Wallet identity did not add stable value beyond the price,
momentum, activity, timing, and event states in which those wallets traded. The generic delay pass
is retained as a confounded counterexample, not promoted.

Exact receipts:
[`03_skilled_wallet_matched_state.json`](development-receipts/03_skilled_wallet_matched_state.json),
[`04_delayed_wallet_and_expert_consensus.json`](development-receipts/04_delayed_wallet_and_expert_consensus.json),
and
[`05_delayed_wallet_state_activity_match.json`](development-receipts/05_delayed_wallet_state_activity_match.json).

### B2 — rejected against single-wallet and crowd rivals

Expert consensus covered 748 delayed signals over 49 events and had positive net event-macro edge
of `+0.02869`. Agreement nevertheless added no stable information:

- On paired events it trailed a single high-skill wallet by `-0.01468`.
- Its advantage over non-high consensus was `+0.01121` overall but reversed from `-0.06190` early
  to `+0.06265` late.
- Non-high consensus (`+0.04301`) and single-high flow (`+0.04661`) both had larger unpaired
  event-macro edges than expert consensus.

Status: **REJECT FIXED B2 CANDIDATE**. Distinct skilled-wallet agreement behaved like correlated
reaction or common-event selection, not incremental independent information.

## Updated comparison with time-series controls

The wallet branch began with a stronger apparent effect than the prior directional time-series
models, but the advantage did not survive those models' state variables. The combined B1 match
explicitly conditions on current probability, recent hourly momentum, market activity,
time-to-resolution, direction, and event. Its remaining `+0.00383` increment is below the fixed
economic gate and unstable across time. On current evidence, state/activity features dominate
wallet reputation and expert-count features; neither behavioral wallet strategy merits protected
evaluation.

## Preregistered B3 probability-weighting strategy screen

The broad calibration lead is not itself a strategy and does not identify probability weighting.
The fixed screen therefore compares each proposed trade with an adjacent probability-state rival
on the immutable whole-event development corpus:

- At 72 hours before close (12-hour tolerance) and 168 hours (24-hour tolerance), use one closest
  sampled probability per market.
- Longshot fade buys NO for YES prices in `[0.02, 0.10)`; its fixed rival buys NO in
  `[0.10, 0.20)`. Favorite follow buys YES in `(0.90, 0.98]`; its rival buys YES in
  `(0.80, 0.90]`.
- Every trade deducts a fixed two-cent adverse-execution hurdle. Results are equal-market within
  event and equal-event overall; adjacent-band differences use only events containing both bands.
- Longshot fade needs 100 markets/30 events at both horizons, positive net event-macro edge at both,
  at least a one-point paired advantage over the adjacent band at both, and positive 168-hour net
  edge in both chronological halves.
- Favorite follow uses the same tests with fixed breadth floors of 30 markets/20 events.

The adjacent-band requirement distinguishes a probability-weighting mechanism from generic
miscalibration or probability-state effects. No failure may be rescued by changing the bands or
horizon after inspection.

### B3 development result

Status: **LONGSHOT FADE RETAINED FOR FRESH REPLICATION; FAVORITE FOLLOW REJECTED**.

- Longshot fade covered 181 markets/109 events at 72h and 169 markets/93 events at 168h. After the
  two-cent hurdle, event-macro net edge was `+0.00160` and `+0.01842`, respectively.
- Its paired advantage over the adjacent 10–20% fade was `+0.05259` at 72h and `+0.11654` at 168h.
  The 168h comparison had only 23 paired events, so its magnitude is fragile despite passing the
  frozen rule.
- At 168h the longshot net edge was positive in both halves (`+0.01232` early, `+0.02345` late).
  The 72h early half was negative (`-0.00844`), but this was not a predeclared failure clause; it is
  carried forward as an explicit replication risk.
- Favorite follow had negative event-macro net edge at both horizons and inadequate 168h breadth;
  it is rejected without changing the fixed band.
- Retained labels were 1,149 `Yes` and three `Up`. Because each probability and mature payout refer
  to the exact retained selected outcome, the valid mechanism claim is low-probability
  selected-outcome weighting, not a literal YES-only effect.

Exact receipt:
[`06_probability_weighting_strategy.json`](development-receipts/06_probability_weighting_strategy.json).
This is sampled-price development evidence only. The source is now frozen at SHA-256
`0d5f047b06dc3885c4b3ef596adc03a82d3e5a3453cbc1b8ccfaa1073a2a7d46` for a genuinely later
whole-event replication.

### Fresh-replication boundary result

A later `human_ro` snapshot was retained at the fixed 2026-08-24 ceiling:

- 1,930 contracts, 391 event groups, and 1,943,938 hourly samples;
- immutable identity
  `polymarket-corpus:0c27543ac944a6d946b52bbf5749b419fc6a0f3d15a8632d30205376a865e40a`;
- exact selection compatibility and strict ancestor-prefix identity verified.

The frozen B3 source was **not executed**. The selection corpus already contains 321 event groups;
the later corpus's whole-event 20% protected tail contains 79. All 70 novel events are in that
protected tail, while all 312 legally visible development events belong to the ancestor. Fresh
development coverage is therefore zero. At least 403 total chronologically ordered events are
needed before even the first successor can leave protection under this boundary; 404 are needed for
Chronos's minimum two-event runnable replication partition.

Status: **B3 DEVELOPMENT CANDIDATE RETAINED; FRESH REPLICATION WAITING FOR LEGAL COVERAGE**. This is
not replication support or contradiction. Receipts:
[`corpus-receipt.json`](fresh-replication/corpus-receipt.json) and
[`boundary-receipt.json`](fresh-replication/boundary-receipt.json).

## Comparison with the prior time-series/low-latency program

| Program | Main information source | Mechanism | Present evidence | Increment required from behavioral branch |
|---|---|---|---|---|
| H1 cross-venue payout dominance | Simultaneous books and exact semantics | Mechanical arbitrage | Highest-priority design, no production result | B6 asks whether within-event coordination failures create analogous dominance |
| B6 NegRisk complete set | Venue event/NegRisk semantics plus every YES-leg book | Mechanical coordination failure | 1,013 candidate events and six complete current-top scopes, but production history lacks dual clocks; no value inspected | Same mechanical family as H1, with stronger venue grouping but the identical simultaneous-depth/execution gate |
| H2 print lead-lag | Cross-venue prints | Short-lived information transmission | Sparse scout not advanced | B1/B2 ask whose trades carry information, not only which venue printed first |
| H3 post-jump reversal | L2 price path | Microstructure overreaction | Strongest directional prior, empirically incomplete | B2 distinguishes informed continuation from uncorroborated-herding reversal |
| H4 staleness/activity gate | Book-state duration | State-dependent opportunity arrival | Strong arrival evidence; no executable result | Behavioral signals must add value conditional on the existing activity clock |
| H5 depth imbalance | Multi-level L2 | Short-horizon order pressure | Implemented, untested | Skilled-wallet agreement is a costlier signal than cancellable displayed depth |
| Prior sampled time series | Hourly probabilities | Statistical process law | Direction weak; arrival/magnitude/staleness strong | B1-B7 must beat state, activity, and event/topic rivals, not merely forecast movement |
| B7 crowded extrapolation | Taker wallet breadth plus six-hour sampled trend | Behavioral overreaction interaction | Rejected: broad trend-chasing crowds continued, and coverage/common support failed | Wallet crowding did not convert trend state into a reliable fade; pure path/state models remain the cleaner hypothesis |
| B8 ambiguity proxy | Question title plus probability state | Ambiguity aversion | Rejected: only two eligible complex markets, `-44.5¢` net edge, no matched cells | Title text added no usable evidence; a valid successor needs retained rule text rather than another fitted time-series transform |

## Program evidence audit

The deterministic program audit completed with zero errors across all ten retained source/receipt
pairs. It verified exact source hashes, expected statuses and decisions, zero protected-value
exposure, zero durable state effects, and the production `human_ro` read-only authority boundary.
It also verified that the frozen B3 source has not run on the later corpus and that all 70 novel
events remain protected.

The fair evidence comparison is retained in
[`evidence-scorecard.md`](evidence-scorecard.md), with its machine-readable audit in
[`program-evidence-audit.json`](program-evidence-audit.json) and repeatable checker in
[`audit_program_evidence.py`](audit_program_evidence.py). The conclusion is deliberately narrower
than a trading claim:

- B1, B2, B4, B7, B8, and the B3 favorite-follow variant are rejected in development;
- B5 and B6 remain untested because their causal data prerequisites failed;
- B3 longshot fade is the sole retained behavioral development lead, but has no legal fresh event
  yet and ranks below the prior fresh reversal result on evidence maturity;
- none of the behavioral, time-series, or low-latency candidates has execution validation.

The original discovery-and-comparison mandate is complete as a research program. Advancement now
depends on new external evidence: at least 404 retained events for the minimum B3 fresh replay, or
a reviewed dual-clock deployment followed by a fresh complete-event B6 capture. Neither condition
may be replaced by reusing the selection corpus or treating sampled marks/current tops as fills.
