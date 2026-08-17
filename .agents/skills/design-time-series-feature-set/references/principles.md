# Feature-set and label principles

## The label is the research question made executable

- Define what happens after the decision time, which path or endpoint matters, and when the outcome
  is complete and legally available.
- Declare horizon as elapsed or calendar time with exact policies. Never replace months or quarters
  with convenient day counts.
- Treat event, endpoint, cumulative, duration, path-dependent, censored, and state-conditioned
  labels as different hypotheses.
- Never remove difficult outcomes or incomplete examples without a declared policy whose effects
  remain visible.

## A feature preserves and discards information

- Define each feature as a reproducible mapping from legal history to a value at the decision time.
- State the failure or mechanism addressed and what history the transformation retains, removes,
  compresses, or approximates.
- Prefer the least destructive transformation that survives evidence; stationarity is diagnostic,
  not an admission rule.
- Make lag, alignment, window, initialization, truncation, dimension, and missingness behavior part
  of feature meaning and version identity.

## Learned choices belong inside folds

- Fit scaling, imputation, differencing order, window choice, PCA, clustering, feature selection,
  hyperparameters, model parameters, and ensemble weights only on the fold's legal training window.
- Do not select a transformation on the full history and then describe it as fixed.
- Keep prediction free of fitting, selection, or adaptation unless an explicit online-learning
  protocol says otherwise.

## Importance is a collection of questions

- Use out-of-fold permutation or ablation to study predictive dependence when applicable.
- Use single-feature evidence to study stand-alone signal while acknowledging interaction blindness.
- Use grouped or conditional perturbations when correlated substitutes make individual rankings
  misleading.
- Inspect stability across folds, time, entities, regimes, seeds, and missingness patterns.
- Preserve conflicting methods. No score directly mutates the feature set.

## Keep the search falsifiable

- Begin with a small mechanism-driven set and meaningful naive baselines.
- Predeclare the trial budget and stopping rule before iterative development.
- Record every attempt, failure, rejection, selection, and parent relation.
- Reject or revise when signal is concentrated, unstable, baseline-inferior, leakage-sensitive, or
  dependent on an unexplained transformation.
- Never promote the best-looking trial merely because the budget ended.

## Optional candidate structures

- Labels may use fixed horizons, first path conditions, continuous future state, or selective
  primary/secondary decisions. Each expresses a different question and maturity interval.
- Overlapping label intervals can motivate concurrency diagnostics, uniqueness weights, purging,
  or block-aware sampling. Weighting changes the estimand and needs an unweighted comparison.
- Raw levels, changes, bounded-space transforms, rolling normalization, and fractional-memory
  transforms are alternatives. Select or fit transformation parameters inside legal folds.
- Simple regularized learners, bagged learners, random feature ensembles, boosting, and authored
  ensembles trade bias, variance, and selection exposure differently. No family is a default.
- Impurity, out-of-fold permutation/ablation, single-feature, grouped, and orthogonal diagnostics
  ask different importance questions. Preserve substitution, interaction, and instability evidence.
