# Data-analysis principles

## Meaning before arithmetic

- Resolve what each field measures, its unit, population, denominator, frequency, and observation
  process before computing a statistic.
- Distinguish raw entities from aggregates. Never mix hierarchy levels in a total or comparison
  unless an explicit transformation defines the relationship.
- Treat a convenient column name as a clue, not semantic authority.

## Time has more than one clock

- Ask what period an observation describes and when it became legally knowable.
- Reconstruct views with `available_at <= decision_time`; do not infer availability from the
  reference period, file order, extraction date, or latest retained value.
- Keep predictor availability and label maturity separate.
- Treat revisions and vintages as part of the observation process. A revised historical value is
  not automatically what a historical researcher saw.

## Missingness and coverage are evidence

- Measure coverage by time, entity, field, and regime before modeling.
- Investigate whether missingness reflects reporting rules, entry/exit, changed definitions,
  censoring, or failed acquisition.
- Never silently impute, drop, rebalance, or select a complete panel. Any learned missingness
  treatment belongs inside the legal training boundary.

## Relationships need rival explanations

- Start with descriptive levels, changes, lags, distributions, and stable baselines appropriate to
  the data meaning.
- Separate between-entity differences from within-entity changes when panel structure matters.
- Challenge apparent signal with time trends, common shocks, denominator changes, composition,
  regime shifts, outliers, and measurement breaks.
- Correlation, visual alignment, feature importance, and a low development error are not causal
  evidence by themselves.

## Preserve traceability

- Bind every consequential statement to exact data, code, parameters, filters, and artifacts.
- Report actual accesses and exclusions rather than claimed provenance.
- Keep failed analyses and surprising nulls; they constrain the next hypothesis.
- Stop when semantics or availability are unresolved enough that calculation would manufacture
  precision.

## Optional market-data probes

- Irregular observations may be viewed on clock-time, trade-count, size, notional, imbalance, run,
  or event-triggered clocks. Compare a view only when its clock matches a named mechanism.
- Path excursions, activity bursts, price-boundary regimes, interarrival times, and outcome-leg
  mappings are possible exploratory lenses, not required features.
- Apparent transaction-price predictability needs rival checks for spread bounce, aggressor
  direction, matching fragmentation, sparse prints, and a small number of dominant contracts.
- A transform such as differencing, logit mapping, rolling normalization, or fractional memory is
  a hypothesis about what information to retain. Diagnose warm-up, boundary behavior, and stability
  before formalizing it.

## Learned failure pattern: transaction-direction reversal

- Failure evidence: the traced
  [Polymarket method-probe study](../../../../studies/polymarket-method-probes-2026-08-17/)
  found raw imbalance/reversal correlations around `-0.46` to `-0.48` that became only `+0.04` to
  `+0.05` after a two-sided transaction-price control; raw one-fill reversal also collapsed on
  separate aggressor paths.
- General principle: before treating signed flow, runs, rolling deviations, or memory transforms as
  predictive, compare same-aggressor paths or a legal direction-neutral price state. Record whether
  the transformation merely amplifies bid/ask bounce or side switching.
- Counterexample: a genuine state response may survive a registered quote-midpoint label,
  same-direction paths, multiple activity clocks, chronological splits, and unrelated event groups.
  Do not reject such a result merely because raw prints also exhibit bounce.
