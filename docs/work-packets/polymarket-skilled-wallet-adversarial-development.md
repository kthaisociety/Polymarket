# Work packet

## Identity

- Packet: `polymarket.skilled-wallet-adversarial-development`
- Owning architecture block: Open-ended exploration, composed with the Polymarket data foundation.
- Semantic transition or responsibility: Challenge the development-only skilled-wallet lead with
  fixed price-state, time-to-resolution, execution-delay, cost, chronology, and independent-wallet
  agreement adversaries before any protected evaluation or promotion decision.
- Input repository state: `historical checkpoint 712fc693bd17` on
  `codex/polymarket-time-series-research`, with the completed behavioral-discovery packet and
  pre-existing uncommitted low-latency work preserved.

## Objective

Determine whether the observed fold-local skilled-wallet advantage contains incremental,
actionable information after fixed causal controls, and whether agreement among distinct skilled
wallets improves on individual skilled flow. Return a retain/reject decision for later untouched
evaluation, not a trading finding.

## Context boundary

- Global authority loaded: repository and Chronos instructions, `CONTEXT.md`, locked decisions,
  invariants, architecture map, authority/sandbox specification, test strategy, and style guide.
- Owning block and transition contract: exploration README and transitions,
  `sandbox.execute-analysis`, `sandbox.record-provenance`, and
  `observation.assemble-analysis-result`; Polymarket source boundary and public-source expansion.
- Relevant adjacent interfaces: proved `human_ro` production role, taker aggregate-leg predicate,
  on-chain payout ordering, hourly sampled prices, event-group chronology, and prior H3/H4
  time-series rivals.
- Explicitly excluded work: production mutation, final-embargo payout/value queries, protected
  evaluation, threshold tuning after results, strategy promotion, live execution, causal
  microsecond claims, and treating sampled prices as executable quotes.
- Assumptions: a fill becomes public no earlier than block inclusion; hourly price samples are
  delayed public-state proxies; event identity is the dependence unit; a fixed one-cent hurdle is
  a stress test rather than a fee model.

## Change boundary

- Permitted files or components: this packet; the existing behavioral study README; new authored
  SQL sources and sanitized development receipts inside that study; and the studies index if its
  status changes.
- Allowed state effects: bounded repeatable-read production SELECTs through `human_ro`, exact local
  source and receipt creation, local validation, and read-only inspection of existing research.
- Forbidden state effects: any server write, credential persistence/output, final-embargo value
  access, edits to core Chronos authority or runtime, mutation of prior receipts, and modification
  of unrelated low-latency work.

## Correctness

- Governing invariants and decisions: availability, label maturity, event-group dependence,
  development/protected separation, no silent fallback, actual-access provenance, and exploratory
  outputs remaining provisional.
- Concrete failure modes: double-counting the per-party fill ledger; learning wallet skill from
  unresolved/future markets; using the same fill price as a followable entry; allowing repeated
  orders from one wallet to masquerade as independent agreement; comparing different event, side,
  price, or resolution-horizon mixtures; using a mutable database without a fixed as-of ceiling;
  silently losing delayed-price coverage; or selecting a favorable subgroup after inspection.
- Expected inputs and outputs: frozen SQL at server ceiling
  `2026-08-24T09:13:44.071211+00:00`, resolved binary contracts, aggregate taker fills, hourly
  sampled probabilities, and on-chain payouts produce exact matched-state, delayed-entry, and
  expert-consensus development receipts with the final event block excluded.
- Violating mutation or counterexample: replace the one-row taker predicate with all fill rows, or
  admit price samples before one elapsed hour. Source inspection and receipt diagnostics must make
  either violation visible.
- Required local tests/evals: SQL parses and completes in a repeatable-read read-only transaction;
  JSON receipts parse; source digests match exact bytes; thresholds, coverage, chronology, and
  missing delayed-mark coverage are explicit; focused retained-corpus/exploration tests stay green.
- Required integration evidence: actual production rows traverse only `human_ro`; all result
  aggregation is limited to the training and development event partitions and respects the fixed
  server ceiling.

## Predeclared decision rules

1. **Matched-state B1.** Compare `HIGH_SKILL` with `NON_HIGH` inside fixed cells of event, aggressor
   side, five-point fill-price band, and time-to-resolution band (`<=24h`, `24-72h`, `72-168h`,
   `>168h`). Retain only if at least 30 events and 100 cells contain both cohorts with at least five
   fills each, the equal-event high-minus-non-high edge is at least `+0.010`, and it is non-negative
   in both chronological halves.
2. **Delayed-entry B1.** Collapse binary outcome-token fills to one canonical outcome-0 vote per
   wallet, market, and UTC hour, using that wallet's final aggressive fill in the hour. Use the
   first fidelity-60 outcome-0 price sample from one to two elapsed hours after that signal as the public
   entry proxy. Deduct a fixed `0.010` adverse-execution hurdle. Retain only if at least 30 events
   and 1,000 high-skill signals are covered, high-skill net event-macro settlement edge is positive
   in both halves, and high-minus-non-high event-macro net edge is at least `+0.010`.
3. **Expert-agreement B2.** In each binary market/hour, count each high-skill wallet once after
   mapping both outcome tokens to the same canonical outcome-0 direction. A
   consensus requires at least two distinct eligible wallets and at least 75% agreement by wallet
   count; ties are excluded. Compare its delayed, one-cent-hurdled result with single-high-skill and
   non-high crowd signals. Retain only if coverage reaches 30 events and 500 consensus signals,
   consensus net event-macro edge is positive in both halves, and exceeds both rivals by at least
   `+0.010` event-macro edge.
4. **Combined delayed-state B1.** The delayed B1 candidate is not eligible for fresh evaluation
   unless it also beats non-high flow inside the same event, canonical direction, five-point
   delayed-entry price band, time-to-resolution band, entry-time momentum state, and market-hour
   activity band. Momentum is delayed entry minus the last public hourly mark no more than two
   hours before the wallet signal (`DOWN <= -0.02`, `FLAT`, `UP >= +0.02`). Activity is distinct
   wallet votes in the signal market/hour (`1`, `2-4`, `5-9`, `10+`). A cell needs three signals
   per cohort. Retain only with at least 25 events and 75 cells, high-minus-non-high equal-event
   net edge of at least `+0.010`, a non-negative difference in both halves, and positive high-skill
   net edge in both halves.

These are development-selection rules. Passing them authorizes only an immutable corpus and a
separately governed untouched evaluation; failing them rejects the fixed candidate without
post-hoc rescue.

## Completion evidence

- Exact authored sources and sanitized receipts are retained and hash-checked.
- Each result states cohort/event/signal coverage, delayed-mark loss, cost hurdle, chronology, and
  comparison against the fixed rival.
- The study ledger records which candidates are rejected, retained for fresh evaluation, or remain
  blocked on dual-clock executable data.
- Focused validation passes and the transition receipt distinguishes sampled-price evidence from
  executable strategy evidence.

## Boundary revisions

- Before delayed-price execution and without inspecting any new result values, the signal unit was
  tightened from outcome-token/side buckets to one canonical binary-market vote per wallet/hour.
  BUY outcome 0 and SELL outcome 1 are the same positive vote; SELL outcome 0 and BUY outcome 1
  are the same negative vote. The wallet's final aggressive fill in the hour breaks intrahour
  direction changes. This prevents logically equivalent binary-token trades from inflating
  independent-wallet agreement or signal coverage.
- After the generic delayed test passed but the recorded-fill state match failed, the packet added
  the combined delayed-state rule above before executing it. This is not a rescue threshold: it
  requires the surviving delayed signal to clear price, momentum, activity, horizon, and event
  controls simultaneously. Failure rejects the B1 candidate; success only permits untouched
  evaluation.

## Transition receipt

### Result

- Packet: `polymarket.skilled-wallet-adversarial-development`
- Status: **COMPLETE**.
- Input repository state: `historical checkpoint 712fc693bd17` with pre-existing low-latency work.
- Resulting repository state: research-only authored SQL, receipts, and documentation added on the
  same dirty branch; runtime and production state are unchanged.

### Delivered state delta

- Added exact matched-state, delayed-entry/consensus, and combined delayed-state/activity sources
  with sanitized receipts.
- Rejected the fixed B1 skilled-wallet follower and B2 expert-consensus candidates under their
  preregistered development rules.
- Preserved the generic delayed B1 pass as a confounded counterexample rather than promoting it.

### Evidence

- Matched B1: 531 cells/38 events; high-minus-non-high `+0.00867`, below `+0.010`.
- Generic delayed B1: 9,837 high signals/61 events; paired increment `+0.01668`, but early/late
  paired differences `-0.01764`/`+0.03895`.
- Combined delayed-state B1: 773 cells/41 events; increment `+0.00383`; high net edge flips from
  `+0.07127` early to `-0.02697` late.
- B2 expert consensus: 748 signals/49 events; trails single-high rival by `-0.01468` on paired
  events and reverses sharply against non-high consensus across chronology.
- All three sources ran in repeatable-read, read-only `human_ro` transactions at the frozen as-of
  ceiling. Final-embargo payouts were excluded from label joins; delayed-price missingness never
  fell back to fill prices.

### Knowledge carried forward

- The original wallet-skill effect is primarily explained by price state, momentum, activity,
  timing, and event selection. Wallet reputation is not incrementally stable under the fixed test.
- Multiple agreeing skilled wallets do not behave like independent private signals in this sample;
  a single skilled wallet and even non-high consensus are stronger rivals.
- The behavioral program should move to a mechanism independent of wallet identity, beginning with
  the fixed probability-weighting/favorite-longshot screen. Executable claims still require
  dual-clock quotes, fees, depth, and impact.

This packet proves no trading strategy or protected finding. It closes only the wallet branch's
development decision; the broader behavioral-strategy goal remains active.
