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
