# Low-latency Polymarket hypothesis program

Epistemic status: **EXPLORATORY PROGRAM DESIGN — NO TRADE, FORMAL CANDIDATE, OR PROTECTED
CLAIM**.

Research decision time: `2026-08-23T10:36:21+00:00`.

This memo turns the existing Chronos evidence into a falsifiable low-latency research program. It
does not reinterpret sampled probabilities or transaction prints as executable quotes. The
collector and Chronos now implement the dual-clock capture, exact bounded read, immutable retention,
replay, and registration boundary. The first empirical branch still needs that collector change deployed and
a post-change production corpus captured; no historical quote values were manufactured.

## Mandate and definition

The mandate is to find time-series strategies whose decision is triggered by a new market event and
whose order can be submitted within a measured sub-minute latency budget. Holding period and
reaction latency remain separate: a position may last longer than a minute, but a strategy is not
called low latency merely because it polls an hourly signal quickly.

Every study must keep these clocks distinct:

1. `reference_time`: when the venue says the market event occurred;
2. `available_at`: when the exact event became observable to the collector;
3. `decision_time`: when the normalized legal state was available to the strategy;
4. `order_sent_at`, `order_acknowledged_at`, and `fill_time`: the execution path;
5. label maturity: when the declared response or completed execution became knowable.

The first campaign will use event-triggered sampling. Clock-time, trade-count, size, and notional
views may be diagnostics, but none replaces the event clock without a stated mechanism.

## What the previous work establishes

| Evidence family | Directly supported conclusion | Consequence for low-latency research |
|---|---|---|
| Raw fills, flow, runs, size, and transforms | Large apparent reversal effects collapsed under same-aggressor or two-sided controls. | Do not reuse transaction-price bounce as alpha. Quote midpoint or exact executable-side labels are required. |
| General internal feature search | State, inactivity, and path persistence predict movement magnitude and arrival better than direction. | Use these as participation, cancellation, or risk gates rather than inventing a directional claim. |
| Fresh post-jump studies | Reversal-before-continuation replicated across 128 fresh events, but strict formal stability remained unresolved and no historical book was tested. | Retain as the strongest internal directional prior; re-test on executable book state with a fixed action delay. |
| Sibling surfaces, bracket overround, and first-move direction | Exploratory gains failed formal replay, cost, breadth, or stability gates. | Do not reopen these exact branches through threshold search. |
| FedWatch, PortWatch, Brazil polls, and XTracker | Direct follow rules failed; post-hoc or discovery effects were sparse or reversed on confirmation. | Slow public-series following is not the opening low-latency branch. |
| Marked-jump and quiet-duration studies | Sticky, zero-inflated marked-jump structure and update-arrival predictability were broad and reproducible. | Use process state to decide when a fast strategy should participate, not as standalone directional P&L. |
| Retained strategy lab | Order-book imbalance, parity, maker capture, and cross-venue matching were implemented or scoped, but the lab records no real scoring or live fills for them. | Treat code and thresholds as hypothesis ancestry, not evidence. Chronos must estimate them from retained event-time data. |

The current evidence therefore rejects a generic `fast momentum` or `fast mean reversion` mandate.
The research program begins from mechanisms that survived some prior control or have a payoff
identity independent of price prediction.

## New cross-venue evidence boundary

The active-data campaign retained an exact semantic audit for two Brazil election contracts and a
cross-venue taker-fill file:

- semantic audit SHA-256:
  `75ec8496452816964f4db6749c1ba90db0c3bd1c27a5e0b510ef2a9e66d67d89`;
- compressed fill file SHA-256:
  `7a08c71c2e88563a247dd10d9a5480a435dc6b834fbed168907a041bf0ffb32c`;
- fill-file bounds: `2026-01-01T00:00:00+00:00` through
  `2026-08-18T20:38:11+00:00`;
- 59,000 retained rows: 4,713 Kalshi and 54,287 Polymarket fills across the matched Lula and
  Flavio contracts.

The audit establishes only one conservative settlement direction: buy Kalshi YES plus buy
Polymarket NO. Under the documented outcomes its minimum combined payout is one dollar per paired
share. The reverse pair is not granted the same authority because the unresolved-result cutoffs
differ.

This is not yet arbitrage evidence. The retained file contains only `outcome_index = 0` taker fills,
not the required simultaneous Kalshi-YES and Polymarket-NO marketable asks. It has no historical
depth, quote sequence, collector receipt time, order acknowledgement, queue state, or partial-fill
path. Kalshi coverage ends on August 9 while Polymarket coverage continues to August 18. The two
candidate contracts are also one election family, not independent replications. The file has not
yet been registered as an authorized Chronos quote view.

## Ranked hypothesis backlog

### H1 — Cross-venue conservative payout dominance

**Question.** When exact marketable depth is observed on the semantically authorized pair, does
buying Kalshi YES and Polymarket NO lock positive value after venue fees, depth consumption,
latency, capital costs, and failed-leg hedging?

**Mechanism.** The edge comes from a documented lower bound on combined payout, not a forecast of
the election winner.

**First falsifier.** At the measured production action delay, either no positive combined-cost
window remains, available paired size is immaterial, or conservative failed-leg closeout makes the
net lower bound non-positive.

**Priority.** 1. This is the cleanest initial study because its economic mechanism and permitted
direction are explicit. It still needs a historical or prospective executable-book record.

### H2 — Cross-venue price-discovery lead and lag

**Question.** After a direction-neutral price innovation on one venue, does the other venue's
executable midpoint or touch move in the same direction after the strategy's measured action delay?

**Rivals.** Timestamp mismatch, common-news response, venue-specific spread bounce, stale quotes,
and selection on active periods can all manufacture lead-lag.

**First falsifier.** The response disappears with collector-time ordering, same-side or midpoint
controls, spread and depth costs, and chronological event-family evaluation.

**Exploratory scout result.** The exact 59,000-fill source-time diagnostic does not advance H2.
The retained Kalshi leg is one-sided because the acquisition omitted the opposite outcome leg. On
the remaining eligible Kalshi-to-Polymarket path, the 30-second conditional aligned mean is only
+0.220 cents, the median is effectively zero, same-side response coverage is 39/264, candidate and
month slices are unstable, and the matched post-minus-reverse comparison is negative. Only 1/307
eligible Polymarket triggers receives a Kalshi same-side print within 30 seconds. See
[`brazil-cross-venue-fill-lead-lag-result.md`](brazil-cross-venue-fill-lead-lag-result.md).

**Priority.** 2 only as a shared-data secondary analysis. Do not acquire another print-only corpus
or formalize this result. Reuse H1's symmetric dual-clock book and clock dataset before H2 expands.

### H3 — Book-confirmed post-jump reversal

**Question.** After an executable midpoint shock and one fixed update/action delay, does the
predeclared path-regime state predict that a marketable reversal threshold is reached before a
continuation threshold?

**Prior.** The reversal-first property replicated on 6,174 fresh development shocks across 128
events and survived a one-cent sampled-price screen. The strict formal candidate later failed
conjunctive stability clauses, so the prior is real but not freeze-eligible.

**First falsifier.** The signal fails on quote midpoints, disappears after a real action delay, or
cannot earn positive net execution value on both shock signs across chronological event groups.

**Priority.** 3. This is the strongest internal directional mechanism, but it must be treated as a
new quote-based question rather than a continuation of sampled-price selection.

**Implementation status.** LL-03 is now encoded as a fixed dual-clock book replay rather than a
reused fitted model. Consecutive YES midpoints define a two-cent shock in collector order. After a
configured action delay, an upward YES shock buys the authorized NO outcome at its ask and a
downward shock buys YES, avoiding a naked-short assumption. The selected outcome exits at its bid
on the first two-cent reversal or continuation crossing, otherwise at the 24-hour deadline. Exact
coverage, quote freshness, displayed size, cost budget, overlap suppression, and missing execution
states are explicit. Synthetic tests establish causal mechanics only; no captured quote result or
candidate exists. See
[`polymarket-ll03-book-reversal-screen.md`](../../docs/work-packets/polymarket-ll03-book-reversal-screen.md).

### H4 — Staleness-conditioned execution and cancellation gate

**Question.** Does the legal quiet-duration and activity state improve the net result of another
fast strategy by deciding when to enter, cancel, widen, or abstain?

**Mechanism.** Quiet duration predicts update and meaningful-move arrival. A market maker may use
that intensity forecast to reduce adverse selection; a taker may use it to avoid paying spread when
the expected response window is too slow.

**First falsifier.** The gate does not improve net PnL, adverse-selection loss, or capital-time
efficiency against the identical ungated strategy under chronological replay.

**Priority.** 4. The predictive component is strong, but honest testing requires queue position,
asynchronous fills, cancels, and maker rebates. It is not a shortcut around execution modeling.

**Feature-substrate status.** LL-00 now transfers only the defensible timing mechanism into the L2
corpus. Exact source messages are coalesced across rows/legs, then each leg receives causal
collector-time quiet duration and a fixed-window prior message count with explicit first-point and
warm-up missingness. Same-time bursts, signed venue/reference delay, negative skew, and exact-zero
delay are retained as diagnostics. The transform does not reuse the rejected protected system,
select a gate threshold, infer order latency, or claim H4 improvement. See
[`polymarket-ll00-book-activity-features.md`](../../docs/work-packets/polymarket-ll00-book-activity-features.md).

**Taker-ablation status.** LL-04a now composes those exact features with either LL-03 or LL-05
without changing the parent signal, arrival, exit, holding period, cost, or attempt ordering. The
mandatory ungated baseline retains every parent attempt; the gate only selects an ordered subset at
the original signal time. Missing feature history abstains, unresolved parent outcomes remain
unscored, and paired outputs include PnL sign/coverage plus one-share and displayed-quantity
collateral-time efficiency. Thresholds are required identity with no implementation defaults. This
is not the maker cancellation branch and does not establish H4 improvement. See
[`polymarket-ll04a-activity-participation-gate.md`](../../docs/work-packets/polymarket-ll04a-activity-participation-gate.md).

**Component-rival status.** LL-04b prevents a favorable joint result from receiving credit merely
for removing feature warm-up or reproducing one component. It reports all attempts, complete
history, quiet-only, recent-activity-only, and joint populations from the same ordered parent
attempts, plus fixed-direction contrasts between them. Prior sampled-process evidence supplies the
duration-dependent mechanism but not a numerical seconds-level L2 threshold; no historical
hour-scale coefficient or cutoff is copied. The joint hypothesis must add stable collateral-time
value over both component rivals on chronological event blocks or be rejected. See
[`polymarket-ll04b-activity-gate-rival-ablation.md`](../../docs/work-packets/polymarket-ll04b-activity-gate-rival-ablation.md).

**Chronological-campaign status.** LL-04c now aggregates one exact parent recipe and activity policy
across explicit non-overlapping collector blocks and multiple markets. Every block and the pooled
campaign retain all five populations and six contrasts. The predeclared primary contrast/metric
reports missing-aware sign counts, block macro, early/late means, and positive-improvement
concentration; the primary must compare the joint gate with complete history or a component rival,
so warm-up removal cannot become the headline. The early/late split occurs before missing values
are removed. Duplicate attempts,
policy drift, recipe drift, scope drift, and out-of-block coverage fail. This measures temporal
stability but does not supply semantic event-family breadth or a promotion rule. See
[`polymarket-ll04c-chronological-activity-campaign.md`](../../docs/work-packets/polymarket-ll04c-chronological-activity-campaign.md).

**Fixed-candidate status.** LL-04d now removes the remaining threshold ambiguity with one
pre-inspection, no-fit candidate. Maximum quiet duration equals one declared parent action-delay
interval; the recent window equals five action-delay intervals; and at least two prior source
messages must lie in that window. The triggering message is excluded. A zero-delay parent fails,
microseconds are preserved exactly, and the derived gate ID hashes the complete H3/H5 parent
definition. This is a one-trial hypothesis: alternate multipliers or counts require a new candidate
and ancestry after rejection. The declared delay is not measured latency. See
[`polymarket-ll04d-latency-scaled-activity-policy.md`](../../docs/work-packets/polymarket-ll04d-latency-scaled-activity-policy.md).

**Development-standard status.** LL-04e now predeclares the one-trial disposition before any L2
campaign values are inspected. The primary comparison is joint versus complete history on net
touch PnL per one-share collateral-second. At least 10 chronological blocks, 80% scored-block
coverage, 30 joint scorable attempts, 25% joint retention, and no more than 10% unresolved joint
entries are required. With sufficient coverage, at least 60% of scored blocks, the pooled value,
block macro, and both chronological halves must be positive; no one positive block may contribute
more than 50% of positive improvement; and the joint gate must beat quiet-only and recent-activity-
only rivals. Missing coverage returns insufficient, any economic failure rejects development, and
full passage advances only to a separately authored paper-execution study. Every ablation must
retain its exact LL-04d-derived parent identity. See
[`polymarket-ll04e-activity-development-advancement.md`](../../docs/work-packets/polymarket-ll04e-activity-development-advancement.md).

**Retained-snapshot application status.** LL-04f now binds a predeclared environment, scope,
ordered collector blocks, unique retained snapshot hashes, complete market-specific H3 or H5
definitions, shared parent recipe, and the exact LL-04d/e identities. Its read-only runner requires
each snapshot's interval and two legs to equal its binding, then composes replay, the parent screen,
LL-00, all activity rivals, the chronological campaign, and the development disposition. Empty
markets remain visible as insufficient evidence. This removes manual stage-to-stage reconstruction
but does not prove pre-inspection plan timing; a persisted plan receipt remains necessary before a
real campaign. See
[`polymarket-ll04f-retained-snapshot-application.md`](../../docs/work-packets/polymarket-ll04f-retained-snapshot-application.md).

**Application-plan precommit status.** LL-04g now canonicalizes every LL-04f scientific field into
one path-independent SHA-256/size receipt. Exact retries preserve one immutable local object;
missing, corrupted, conflicting, or structurally changed plans fail before any retained quote
corpus is loaded. This closes the exact-input enforcement gap, but local content identity and file
metadata do not independently prove when the plan was retained. A real campaign must still bind
the receipt to durable externally ordered evidence before value inspection. See
[`polymarket-ll04g-application-plan-precommit.md`](../../docs/work-packets/polymarket-ll04g-application-plan-precommit.md).

### H5 — Tight-spread order-book imbalance impulse

**Question.** Conditional on a tight spread and minimum real depth, does multi-level book imbalance
predict an executable price move over 1–30 seconds?

**Prior.** The retained strategy lab contains a reasoned implementation, but its threshold, 30-second cadence,
and hold limit were never calibrated on retained Polymarket book events.

The cited Polymarket paper supports retaining depth beyond the touch; it does not report a
directional imbalance strategy. The lab's `.50` imbalance, `.03` spread, `100`-share depth, and
two-minute hold are unscored starting points rather than empirical priors.

**First falsifier.** Imbalance has no incremental value over spread, recent trades, and state; the
effect reverses under cancellation/spoof controls; or taker costs consume it at the measured action
delay.

**Priority.** 5. Treat every existing threshold as an untested ancestor, not a default.

**Implementation status.** LL-05 now preserves and temporally registers the complete best-first
depth ladder after every replayed source event. Its fixed screen detects a new all-level imbalance
crossing under spread, total-depth, and price-band gates; re-confirms the same direction after a
configured action delay; buys YES for bid-heavy pressure or NO for ask-heavy pressure; and exits at
the selected outcome's bid on take-profit, stop, imbalance decay, or a fixed timeout. It reports
top-touch imbalance as a mandatory rival, displayed size, explicit cost budget, cancelled arrivals,
missing exits, non-overlap, and truncation. Eleven synthetic adversaries establish mechanics only;
the directional hypothesis remains empirically untested. See
[`polymarket-ll05-depth-imbalance-screen.md`](../../docs/work-packets/polymarket-ll05-depth-imbalance-screen.md).

## First empirical study: LL-01

### Exact question and population

For the two semantically audited Brazil pairs only, do simultaneous marketable asks in the
authorized Kalshi-YES plus Polymarket-NO direction create a positive conservative locked-value
opportunity after all deterministic costs and measured action latency?

The two pairs are a feasibility population within one election family. They cannot support a broad
cross-event generalization. Any later general claim requires a new exact semantic audit and a fresh
matched-event cohort.

### Required registered data

Before any value analysis, retain and register:

- full depth updates or sequenced L2 snapshots for the exact Kalshi YES and Polymarket NO legs;
- both venue event timestamps and collector `available_at` timestamps, plus clock-health records;
- exact price, displayed size, venue status, tick size, and outcome identity at every update;
- time-versioned taker fees, gas or transfer costs, and the fixed semantic-audit identity;
- prospective paper order send, acknowledgement, fill, cancel, reject, and partial-fill records.

The union of quote events is the observation clock. At each decision, the other leg is joined only
from the latest state whose `available_at` is no later than that decision. No future quote, nearest
timestamp join, or unlimited forward fill is permitted.

### Decision, label, and latency policy

The signal at decision time is the maximum paired quantity for which the depth-consumed Kalshi YES
cost plus Polymarket NO cost and deterministic fees is below the documented one-dollar payout
floor. Orders are submitted concurrently where possible, but cross-venue atomicity is never
assumed. The predeclared first-leg, cancellation, partial-fill, and failed-leg hedge policies are
part of strategy identity.

The primary label is realized conservative locked value after both fills or after the declared
failed-leg hedge completes. A displayed spread is only a diagnostic. The label matures when the
paired execution or hedge path is complete, not when the first quote appears.

Latency is replayed from `decision_time` to the actual or declared `order_sent_at`, then through
acknowledgement and fills. A zero-latency result is reported only as an upper bound. Advancement is
decided at the measured production tail latency fixed before quote values are exposed.

### Baselines and outputs

Report:

- no-trade and zero-latency displayed-gap baselines;
- opportunity count, duration, paired depth, and net locked value by pair and day;
- fully hedged fill rate, partial-fill frequency, failed-leg closeout loss, and worst realized path;
- edge decay across fixed latency buckets and measured production latency quantiles;
- capital lock duration and return on committed capital;
- concentration by pair, day, venue state, and price regime.

The branch stops if no positive opportunity survives deterministic costs at the measured tail
latency, if paired capacity is operationally immaterial, or if the conservative failed-leg path
removes the edge. A passing feasibility result earns a separately authored prospective paper
execution study. It does not directly earn live authority, freeze, protected exposure, validation,
or a trading claim.

## Explicit exclusions

- No raw signed-flow, trade-run, or transaction-price reversal feature without quote controls.
- No midpoint, spread, depth, queue, or fill-probability claim from the current fill tape.
- No reverse cross-venue pair without a separate settlement proof.
- No title-similarity score as semantic settlement authority.
- No reuse of exposed protected cohorts or reopening of closed feature-search budgets.
- No live capital or production writes from this research memo.

## Next research transition

The next transition is deployment of the new dual-clock schema/collector followed by a
bounded invocation of the exact Chronos `book_corpus_snapshot` command. The command now binds the
reviewed scope-authority reference, canonical legs, and half-open collector interval to the proved
`human_ro` repeatable-read path, immutable retention, replay, registration, and a sanitized receipt.
Only after those bytes are captured and exposed through a constrained development view may
`$analyze-time-series-data` inspect values.
Until then, the honest disposition is **prioritize H1; do not advance the source-time print H2
scout; retain H2–H5 only as quote-data hypotheses; the full-depth data boundary, LL-00 activity
features, predeclared H1/H3/H5 screens, LL-04a/b/c campaign machinery, the single LL-04d activity
candidate, its fixed LL-04e development standard, exact LL-04f retained-snapshot application,
LL-04g immutable local plan receipt, and acquisition command are implemented; blocked on
deployment, post-change executable book
observations, fees, and execution-latency evidence**.
The H1 screen is a zero-fee displayed
upper bound with an explicit
fixed-delay persistence diagnostic. LL-03 and LL-05 include spread and an explicit cost budget but
still observe displayed touches rather than fills. LL-04a/b/c/d/e/f/g can falsify the single
activity candidate through paired component, chronological, touch, collateral-time, and exact-plan
evidence but cannot establish a maker, event-family, or execution claim. A zero H1 opportunity
count or non-positive
H3/H5 net-touch result can falsify a branch early; a positive count cannot establish net executable
value.
