# Work packet: Polymarket stochastic process and tradability

## Identity

- Packet: `polymarket.identify-process-and-tradability`
- Owning architecture block: open-ended exploration, composed with development validation.
- Semantic transition or responsibility: retained development-only probability paths → provisional
  stochastic-process diagnosis → controlled chronological pseudo-trading evidence.
- Input repository state: `historical checkpoint 6fe5949a` on
  `codex/polymarket-time-series-research`.

## Objective

Determine whether the exact retained Polymarket development paths are better described, at the
available hourly observation scale, by a martingale diffusion, state-dependent bounded diffusion,
mean-reverting/momentum drift, or jump-dominated observation process; then test whether any
surviving conditional drift could support a trading candidate after a declared hypothetical cost
grid without exposing the final protected event block.

## Context boundary

- Global authority loaded: `AGENTS.md`, `CONTEXT.md`, invariants, plan discipline, Polymarket
  boundary, and the research-guidance skills.
- Owning blocks and contracts: exploration and development READMEs/implementation maps;
  `sandbox.execute-analysis` and `development.evaluate-candidate`.
- Relevant adjacent interfaces: exact retained resolution corpus, whole-event chronological
  development partition, `AnalysisHarness`, study receipt persistence, CLOB source expansion, and
  the final seven-event protected block.
- Explicitly excluded work: protected exposure without an independent freeze/governance decision,
  production writes, external-system changes, invented quote history, trading execution, result-based
  deletion, and declaring sampled probabilities executable.
- Assumptions: the retained hourly `price_series` is a sampled outcome-token probability process.
  It is not a fill series, quote midpoint, bid/ask, or guaranteed executable price. Contract/event
  inclusion conditions on eventual resolution and declared minimum coverage.

## Change boundary

- Permitted files or components: authored study sources and immutable receipts under one new study
  directory; this packet; study index; research memo. A narrowly tested pure numeric sandbox helper
  may be added only if an authored diagnostic exposes its absence as a concrete interface failure.
- Allowed state effects: load exact retained corpus bytes; execute bounded authored analysis over
  the existing 24-event/155-market development capability; persist new source/receipt evidence;
  append documentation; make a coherent local Chronos commit.
- Forbidden state effects: expose any of the final seven protected events or their 45 markets;
  tune on protected evidence; mutate source corpus; access network/filesystem from authored code;
  claim validation/promotion/memory; or print/store credentials.

## Correctness

- Governing invariants: I1-I3, I9, I12-I13, I17-I18, I21-I24, and I26.
- Concrete failure modes: pool dependent contracts as IID; confuse sampled probability with trade;
  infer a process only from marginal fit; fit transforms or drift on test events; use overlapping
  horizons as independent; choose only the best rule after seeing results; omit the no-change
  martingale forecast; ignore boundary-dependent variance; treat volatility predictability as
  directional edge; or subtract hypothetical costs and call the result executable PnL.
- Expected inputs and outputs: exact snapshot/partition and authored source identities produce
  development-only diagnostics for increments, variance scaling, dependence, jumps, walk-forward
  conditional-mean forecasts, and non-overlapping pseudo-PnL under every declared rule/cost.
- Violating mutation or counterexample: mutate every protected price/payout; all authored sources,
  actual accesses, and results must remain unchanged under the existing partition causal test.
- Required local tests/evals: existing protected-isolation regression; authored study success with
  actual accesses; all candidate rules retained; fold-local fitting; event-level stability;
  cost-grid reporting; value interpretation caveats; any new helper receives policy/causal tests.
- Required integration evidence: execute every source through `run_corpus_studies` against
  `polymarket-corpus:610b8b9d...` and retain exact receipts with zero protected exposure.

## Predeclared interpretation and trading gate

- A martingale-like conditional mean requires the current-price forecast to be unbeaten in
  event-macro next-price MSE by a practically meaningful margin, with negligible stable drift.
- Diffusion adequacy requires low zero mass, non-extreme tails, variance ratios near one, and a
  state-variance shape that generalizes across later event groups. Failure implies a more suitable
  jump/mixture or observation-process description even if the conditional mean is martingale-like.
- A pseudo-trading rule is development-credible only if it is evaluated one event ahead after at
  least eight earlier events, uses non-overlapping decisions within each horizon, has positive
  equal-event and market-weighted net change after a 0.01 probability-unit round-trip cost, wins in
  at least 60% of test events, and does not depend on one event for the sign of aggregate evidence.
- Passing that gate does **not** establish tradability. It becomes only a candidate for separately
  retained historical bid/ask validation or prospective quote-based paper execution. With sampled
  prices alone, the strongest permissible conclusion is “gross predictive candidate; execution
  unproved.”
- Any apparent reversal that passes the first sampled-price gate must also survive a predeclared
  execution falsifier on the same walk-forward folds: delay entry by one available observation,
  charge the same 0.01 round-trip cost, and separately retain two-sided, long-only, and short-only
  results. The candidate remains usable only if both delayed two-sided and delayed long-only results
  have positive equal-event and observation-weighted net change, at least 60% positive test events,
  and positive leave-one-event-out minimum. The long-only condition avoids silently assuming that
  an outcome token can be shorted; short-only evidence remains diagnostic rather than executable.
- Active-move (absolute trailing change at least 0.01) and entry-probability regimes are retained as
  mechanism diagnostics, not alternative gates from which to select a winner.
- Semantic discovery, performed before examining any event-level sum, identifies development event
  ordinals 0, 8, 11, and 15 as explicit exhaustive and mutually exclusive outcome buckets from
  their question wording. Other multi-contract events are excluded because their retained contract
  sets omit ranges, describe non-exclusive phrases, or do not prove that every candidate is present.
- For those four event groups, an independent structural hypothesis tests whether synchronized YES
  probabilities sum below one. A synchronized observation requires every retained leg in the same
  UTC hour and a maximum five-minute timestamp span. Underround net is `1 - sum(YES) - n * cost`,
  with costs of 0, 0.005, and 0.01 per leg. It becomes only a live-quote scan candidate if the 0.01
  per-leg median is positive in every event, its 10th percentile is positive in at least three of
  four events, and at least 60% of qualifying current opportunities remain positive one hour later.
  This is deliberately stricter than observing isolated asynchronous sum deviations.

## Completion evidence

- Process diagnostics and follow-up hypotheses run through the real development harness.
- Every attempted rule and negative result remains retained with exact source/receipt identity.
- The process conclusion distinguishes conditional mean, conditional variance, jumps/zeros,
  sampling, and execution.
- Any credible candidate receives the declared pseudo-trading checks; otherwise the result records
  why no trade candidate survived.
- Focused checks and the complete Chronos gate pass; a transition receipt closes the packet and the
  coherent Chronos delta is committed locally without push.

## Boundary revisions

1. The first authored process diagnostic exceeded the bounded execution time before reading data
   because repeated list concatenation made construction quadratic. Its failed source and receipt
   remain retained; the linear rewrite answers the same predeclared question.
2. A walk-forward run exposed that the authorized development view carried event identity but not
   the partition's authoritative chronological event ordinal. Physical corpus order is not temporal
   authority. The view now issues the partition-derived ordinal, with a regression that reverses
   physical input order.
3. Semantic hypothesis formation exposed that authored development research could see opaque IDs
   but not contract meaning. The development outcome capability now includes exact contract
   questions while the entire protected event block remains absent; arbitrary ungranted metadata
   is still denied before disclosure.
4. The exhaustive-bucket diagnostic then required an out-of-band assumption that outcome index zero
   meant YES. The authorized outcome view now supplies the exact retained outcome label, so authored
   analysis can bind probability meaning rather than infer it from position.

## Transition receipt

- Status: **COMPLETE — DEVELOPMENT REJECTION**.
- Exact partition: `49d5e9a97985a44e3277f43ee55ce1281c430a1d0a1823754a9a759ac56d3bd1`.
- Scope: 24 development event groups/155 markets; final 7 event groups/45 markets remained
  unrequested and unexposed.
- Evidence: eight immutable authored source/receipt pairs, including one resource failure and one
  capability denial, are retained under
  `studies/polymarket-process-tradability-2026-08-17/`.
- Process conclusion: hourly samples are best described as bounded sticky zero-inflated,
  heavy-tailed jump/mixture observations with a roughly martingale-like conditional mean and small
  transient negative dependence, not a smooth Gaussian diffusion.
- Candidate disposition: fitted reversal failed the frozen delay/long-only gate; exhaustive-bucket
  underround failed the frozen per-leg-cost/persistence gate. No candidate earned formalization,
  protected exposure, reporting promotion, or a trading claim.
- Memory: repository study history and ledger are updated. Validated terminal question memory is
  unchanged because only an independently governed protected finding or rejection can write it.
- Verification: Ruff clean; basedpyright 0 errors; complete Chronos suite 436 passed with the
  required source path and loopback-only test servers enabled.
