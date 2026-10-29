# Work packet: LL-03 book-confirmed post-jump reversal screen

## Identity

- Packet: `polymarket-ll03-book-reversal-screen`
- Owning architecture block: Polymarket dual-clock L2 corpus and open-ended exploration
- Semantic transition: one exact binary Polymarket YES/NO book registration into a deterministic
  delayed-entry, marketable-touch reversal-versus-continuation screen
- Input repository state: active low-latency program working tree after the H2 source-time print
  scout; all pre-existing study artifacts remain user-owned

## Evidence ancestry

- Fresh reversal replication receipt SHA-256:
  `e777f93b48c87604d845dfd08160036449b2accdd13277a0acf55d243d658c77`
- Fresh evidence: 6,174 OOF shocks, 410 markets, 128 test events; the 12-feature path model passed
  the replicated statistical and sampled-price screens on 387 selected rows/70 events.
- Exact ancestor label: a two-cent opposite-shock move from delayed entry before a two-cent
  same-direction move, within 24 elapsed hours, with greedy non-overlap.
- Contrary evidence: strict time-legal formalization later stopped. The final path revision repaired
  late stability but regressed on the predeclared early-half Brier and event-macro AP clauses.
- Consequence: the mechanism justifies a quote-execution hypothesis and fixed screen. It does not
  justify carrying forward the fitted model, its `.65` score cutoff, or any trading claim.

## Objective

Determine whether the replicated post-jump reversal mechanism can survive executable top-of-book
spread, a fixed action delay, displayed size, explicit per-share cost budget, chronological
non-overlap, and complete label coverage on a newly captured dual-clock L2 corpus.

## Fixed strategy semantics

Each screen binds exactly two authorized outcome legs for one binary Polymarket market:

- `reference_leg`: the semantically authorized YES outcome whose midpoint defines shocks and
  thresholds;
- `complement_leg`: the semantically authorized NO outcome used to express an inventory-free
  reversal after an upward YES shock.

The first empirical definition must be fixed before quote values are inspected:

- minimum absolute midpoint shock: `.02`;
- maximum gap between consecutive reference-book updates: three elapsed hours, matching the
  ancestor's upper shock-gap bound;
- action delay: the measured paper-order tail latency selected before analysis, not zero latency;
- maximum legal quote age at entry and exit: fixed from capture-health evidence before analysis;
- reversal and continuation distances from delayed-entry reference midpoint: `.02` each;
- maximum holding period: 24 elapsed hours;
- minimum displayed entry quantity: a fixed operational capacity floor;
- round-trip per-share cost budget: fixed before analysis and reported separately from spread.

After an upward YES-midpoint shock, buy the NO leg at its delayed marketable ask. After a downward
shock, buy the YES leg at its delayed marketable ask. Exit by selling the selected leg at its
marketable bid at the first collector-time state where the YES midpoint reaches either the
opposite-shock reversal threshold or same-direction continuation threshold. If neither is reached,
exit at the fixed holding deadline. Entry/exit quantity is the smaller displayed touch size.

The strategy is deliberately symmetric in economic direction without assuming naked shorting,
YES/NO complement arithmetic, atomic fills, or hidden depth. It needs an exact semantic authority
for the two outcome legs.

## Time and sampling contract

- Observation clock: coalesced collector `available_at` union clock.
- Shock order: consecutive coalesced reference-leg states in collector order; venue
  `reference_time` remains descriptive and cannot reorder decisions.
- Signal time: collector time of the qualifying reference midpoint update.
- Entry time: signal time plus the fixed action delay; all entry fields are latest-as-of that time.
- Label time: first threshold crossing after entry, otherwise the holding deadline.
- Coverage: the retained half-open corpus bound must extend through entry and, absent an earlier
  crossing, through the holding deadline. Truncation remains explicit.
- Missingness: stale/missing entry or exit state is an explicit status, never zero PnL.
- Overlap: after an entered signal, all reference updates continue updating state but new signals
  are ignored until exit, deadline, or corpus truncation.

## Outputs

For every non-overlapping qualifying shock retain:

- decision, arrival, and terminal collector times;
- previous, decision, entry, and exit YES midpoints;
- shock sign/magnitude and selected outcome leg;
- exact entry ask, exit bid, displayed quantity, gross touch PnL, cost budget, and net diagnostic;
- terminal status: reversal, continuation, timeout, stale/missing entry, missing exit quote, or
  truncated coverage;
- source event ordinals and aggregate evaluated-update, raw-shock, overlap, entry, and status counts.

The screen reports displayed marketable-touch economics, not fills. Positive diagnostic PnL cannot
establish capacity, queue priority, acknowledgement latency, realized slippage, partial-fill
handling, or live profitability.

## Correctness and adversaries

- Reject non-Polymarket legs, different market IDs, identical outcome indices, scope-authority
  mismatch, extra/missing corpus legs, non-positive thresholds/windows/size, negative delay/cost,
  and reversal/continuation distances outside probability support.
- Coalesce all states sharing one collector time before detecting a shock or threshold.
- Prove source `reference_time` cannot reorder collector decisions.
- Prove a post-arrival update cannot rewrite the as-of entry price.
- Prove positive shocks select NO and negative shocks select YES.
- Prove reversal and continuation exits use the selected leg's contemporaneous bid and the smaller
  displayed touch size.
- Prove stale entry and missing exit remain explicit rather than becoming a trade or zero return.
- Prove truncated 24-hour coverage cannot become a timeout observation.
- Prove an active position suppresses overlapping shocks while state continues updating.

## Completion evidence

- Registration exposes and validates exact retained start/end coverage.
- Deterministic screen and public exports are implemented.
- Focused causal and execution adversaries pass.
- Existing Polymarket adapter tests, configured Ruff/formatter, strict basedpyright, and
  `git diff --check` pass.
- Architecture and low-latency hypothesis documents identify LL-03 as implemented but empirically
  unevaluated.

## Explicit exclusions

- No reuse or refit of the selection-exposed sampled-price model.
- No protected exposure, threshold search, quote-value inspection, deployment, database access, or
  production write.
- No midpoint trade, complement-price, fill, fee-schedule, queue, or atomicity assumption.
- No scientific or strategy advancement from synthetic tests.

## Execution receipt

- LL-03 implementation is part of `low_latency.py`, SHA-256:
  `24d4fa656d25091276d8e1319445fe4f89819662830b4d97320dfda4a7201ad7`.
- Focused adversary source SHA-256:
  `dc195a67fc849239a1ae27de01554d01ca56eef4490687fd9f72516ab8be4516`.
- Eight LL-03 focused adversaries passed; the H1, L2 corpus, and LL-03 focused group passed 23/23.
- All 99 Polymarket adapter tests passed.
- The broader Chronos suite passed 468/468 with only the two sandbox-prohibited local HTTP-server
  modules excluded.
- Scoped Ruff and formatter checks passed; configured strict basedpyright passed with zero errors
  or warnings; `git diff --check` passed.
- The registration now preserves its exact half-open collector-time coverage so `TRUNCATED` and
  `TIMEOUT_EXIT` are mechanically distinct.
- Empirical status: **IMPLEMENTED, SYNTHETICALLY VERIFIED, UNEVALUATED ON QUOTE VALUES**. No live
  corpus, trade, protected request, candidate, PnL evidence, or durable finding was created.
