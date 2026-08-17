# Financial machine-learning idea catalog

Status: **optional research guidance**. This document preserves a broad set of ideas distilled from
the user-supplied chapters 2–9 of *Advances in Financial Machine Learning*. It is not architecture,
evidence, a required workflow, or a claim that a method transfers to Polymarket.

## Contents

1. [How to use this catalog](#how-to-use-this-catalog)
2. [Polymarket translation boundary](#polymarket-translation-boundary)
3. [Data structure and sampling ideas](#data-structure-and-sampling-ideas)
4. [Label ideas](#label-ideas)
5. [Overlap, uniqueness, and weighting ideas](#overlap-uniqueness-and-weighting-ideas)
6. [Memory-preserving transformation ideas](#memory-preserving-transformation-ideas)
7. [Ensemble ideas](#ensemble-ideas)
8. [Temporal cross-validation ideas](#temporal-cross-validation-ideas)
9. [Feature-diagnostic ideas](#feature-diagnostic-ideas)
10. [Hyperparameter-search ideas](#hyperparameter-search-ideas)
11. [Polymarket research menus](#polymarket-research-menus)
12. [Method-selection record](#method-selection-record)

## How to use this catalog

Start with the scientific question and the data-generating process. Open one section only when a
specific failure mode or rival explanation makes it useful. Trying a method creates a trial; it does
not create evidence in favor of that method.

For any idea selected from this catalog:

1. Name the mechanism it probes and the rival it distinguishes.
2. State the exact legal inputs, observation and availability clocks, population, and exclusions.
3. Declare every threshold, window, transformation, learned choice, and initialization rule.
4. Put learned choices inside the legal fold. A full-history diagnostic cannot silently become a
   fixed preprocessing decision.
5. Compare against a simpler view and predeclare a falsifier and trial-budget cost.
6. Preserve nulls, failures, unstable signs, and variants through exact ancestry.

Do not assemble every section into a canonical pipeline. The useful method depends on the question;
some ideas conflict, some solve the same problem differently, and some are inapplicable to the
currently registered Polymarket fill tape.

## Polymarket translation boundary

The source material largely discusses securities, returns, positions, and strategy PnL. A
Polymarket outcome token is a bounded claim whose transaction price is often interpreted as a
market-implied probability, but the adapter currently proves only executed fill facts. Translation
therefore requires explicit choices:

- **Unit of analysis:** contract, outcome token, fill, activity bucket, decision time, or event.
- **Price representation:** raw token price, declared complement mapping, logit, change, path
  excursion, or another authored transform. Near-zero and near-one values make log and logit
  transforms numerically delicate.
- **Clock:** elapsed time, trade count, cumulative size, cumulative notional, imbalance, block, or
  event trigger. They answer different questions.
- **Outcome:** a later print, a path statistic, or eventual resolution. The first is exposed to
  spread mechanics; the last is not yet a legal label because exact resolution availability is
  absent.
- **Population dependence:** contracts may share an event or mutually constrain one another.
  Authoritative event/group identity is currently missing.
- **Historical identity:** cursor windows are not immutable snapshots. Development and especially
  protected use require exact retained bytes or an external snapshot identity.

These are not reasons to avoid research. They determine which exploratory claims are honest today.

## Data structure and sampling ideas

### Work from source facts and point-in-time meaning

Processed datasets embed somebody else's choices about alignment, corrections, aggregation, and
missingness. For any registered field, distinguish what happened, when it happened, when it became
legally observable, which revision/vintage is present, and how it was transformed. A convenient
timestamp is not evidence of availability.

Possible Polymarket probes include comparing raw-fill results with alternative legal aggregations,
checking whether a finding depends on one outcome-token mapping, and verifying that repeated reads
retain the same digest at a fixed decision cutoff.

### Choose a sampling clock that matches the mechanism

Irregular activity can be represented in several ways:

- **Clock-time buckets** compare equal elapsed durations but may oversample quiet periods and
  compress active bursts.
- **Transaction-count buckets** compare equal numbers of prints but can be sensitive to matching
  fragmentation.
- **Size buckets** compare equal traded outcome-token quantity.
- **Notional buckets** compare an authored value measure such as price times size; its interpretation
  near probability boundaries must be explicit.
- **Imbalance buckets** close when accumulated signed ticks, size, or notional diverges from a
  trailing expectation.
- **Run buckets** focus on persistent one-sided activity rather than netting opposite directions.

These are examples of alternative observation clocks. None is a default. Expected bucket size or
imbalance is learned state when estimated from data and must obey the fold boundary in formal work.

Useful falsifiers include changing only the clock while holding the underlying fills fixed,
checking stability across activity regimes, and comparing against unaggregated or simple time-bucket
baselines.

### Sample around information-bearing events

Dense adjacent samples often repeat nearly the same state. A researcher may instead seed analyses
when an observable process moves enough to justify a new question. Examples include a cumulative
sum threshold, volatility jump, unusually long no-trade interval, flow burst, price-boundary entry,
or abrupt change in activity.

The event rule must be computable from legal history. Thresholds chosen after seeing outcomes are
selection, and sampling only dramatic successful moves creates conditioning bias. Always report the
unsampled population and compare against a simple schedule.

### Treat multi-outcome structure as authored semantics

Combining outcome tokens resembles constructing a multi-leg series: weights, complement mappings,
execution times, and costs may create apparent changes unrelated to the underlying belief. A
synthetic YES-equivalent series may be useful, but retain raw outcome indices and test whether the
result survives each leg separately. Do not infer an event basket or a mutually exclusive set from
price arithmetic alone.

## Label ideas

### Fixed-horizon changes

A later-price label can be defined after an exact elapsed-time or activity horizon. Declare how the
future observation is selected, what happens when none exists, whether the horizon is calendar or
elapsed time, and whether the label uses transaction price or another legal state.

Possible targets include signed change, absolute change, threshold crossing, direction, or a
continuous future value. Fixed thresholds can mean very different things in quiet and active
regimes or near the 0/1 boundaries; a trailing scale is one possible comparison, not an automatic
improvement.

### Path-aware labels

A label may depend on which of several declared conditions occurs first: an upper excursion, lower
excursion, or time/activity expiry. This family can express asymmetric paths and distinguish an
endpoint move from an interim adverse excursion.

For Polymarket, barrier distance could be absolute price, logit distance, trailing variability, or
another legal scale. Each is a different hypothesis. Sparse prints can miss the actual crossing,
and transaction-price bounce can create false touches. A historical quote-state label is unavailable
until quotes are registered with exact availability.

### Side versus selectivity

One model may propose direction while a second model estimates whether to act, how confident to be,
or whether the primary situation is trustworthy. This separation can be useful when an economic
hypothesis supplies a side but the data may help distinguish strong from weak instances.

It is only an example architecture. The secondary label must be generated from legally matured
outcomes, and the primary signal used to create it must be reproduced out of fold. Filtering after
seeing the same outcomes is not meta-learning; it is selection leakage.

### Class balance and rare outcomes

Rare labels may reflect a genuinely rare event, a bad threshold, sparse observation, or an invalid
population. Before dropping or reweighting them, report their meaning and coverage. Removing rare
cases changes the question and may delete precisely the risk of interest. Classification metrics
must reveal the resulting precision, recall, calibration, and abstention coverage rather than only
headline accuracy.

### Resolution labels remain blocked

Eventual payout is economically attractive but not currently legal for historical Chronos labels.
Contract close time and current resolution metadata do not prove when the outcome became publicly
available. Do not adapt path-label or classification ideas into resolution prediction until an exact
resolution-availability rule and immutable source identity are registered.

## Overlap, uniqueness, and weighting ideas

### Make outcome intervals explicit

Two training examples are dependent when their labels consume overlapping future information.
Record each label's decision/start time and maturity/end time. A long horizon sampled frequently can
produce many nominal rows but little distinct outcome information.

Possible diagnostics include concurrency through time, per-example average uniqueness, effective
sample size, and metric sensitivity after removing or downweighting the most redundant examples.
These diagnostics use future label intervals and therefore belong with matured training/evaluation
data, never predictor construction.

### Weighting is part of the hypothesis

Possible weights include inverse concurrency/uniqueness, outcome magnitude, recency, contract
balance, regime balance, or class balance. Each changes the estimand. A uniqueness weight may reduce
the influence of duplicated paths; a magnitude weight may prioritize large moves; recency weighting
may favor an adaptive-market story. None is automatically more truthful.

Report results with unweighted baselines, weight distributions, concentration, and effective sample
size. Estimate adaptive or normalization parameters inside each training fold.

### Resampling can preserve or destroy diversity

Ordinary bootstrap samples may repeatedly select highly overlapping examples. Sequentially favoring
draws that add distinct label intervals is one possible way to increase diversity. Another is to use
smaller non-overlapping or block-aware samples. Validate the claimed benefit directly; a complex
sampler that does not change effective uniqueness only adds degrees of freedom.

## Memory-preserving transformation ideas

### Stationarity is diagnostic, not an admission rule

Levels preserve long history but can drift; integer differences often reduce drift while discarding
level information. Fractional differencing spans intermediate memory lengths by weighting a long
history with decaying coefficients. A fixed-width approximation avoids changing the effective
weight vector merely because the series grows.

Possible comparisons include raw bounded price, simple changes, returns where defined, logit
changes away from boundaries, rolling normalization, and several predeclared fractional orders.
For each, measure warm-up loss, missingness, retained relationship to the level, stability across
time, and incremental out-of-fold value.

Choosing the minimum order that passes a full-history stationarity test would leak a learned
preprocessing decision. Estimate or select the order and truncation threshold inside the legal
training fold, or predeclare them as scientific alternatives counted against the trial budget.

Polymarket prices are bounded and tend toward terminal extremes, so equity-price unit-root intuition
may not transfer. Fractional transforms are probes for memory versus drift, not a default feature.

## Ensemble ideas

### Diagnose bias, variance, and irreducible noise separately

A complex model can fail because its assumptions are too rigid, its fitted result changes wildly
with small sample changes, or the outcome is mostly noise. Compare simple baselines, perturb training
windows, inspect prediction stability, and avoid treating added model complexity as evidence of a
solvable signal.

### Bagging and random feature subsets

Aggregating diverse fitted models can reduce variance when their errors are not too correlated.
Possible diversity sources include resampled rows, distinct legal windows, random feature subsets,
or different seeds. Overlapping outcomes can make nominally different bootstrap samples nearly the
same and inflate out-of-bag estimates.

If bagging or forests are tried, inspect base-model correlation, uniqueness of in-bag examples,
stability across seeds, and temporal out-of-fold performance. Tree count, depth, row fraction,
feature fraction, class weights, and early stopping are learned or predeclared choices—not harmless
implementation details.

### Boosting and sequential correction

Sequentially emphasizing prior errors may reduce bias but can chase noisy or mislabeled financial
observations. It is a plausible comparison when simple models consistently underfit a stable
mechanism; it is risky when labels are sparse, overlapping, mechanically noisy, or repeatedly tuned.
Preserve failures and compare with a regularized simple learner and a variance-reducing ensemble.

### Ensemble weighting

Equal, performance-based, regime-dependent, or diversity-aware ensemble weights express different
hypotheses. Any weight learned from data belongs inside the fold and inside the frozen system.
Combining many tried models after seeing development scores adds selection exposure even if each
component was individually legal.

## Temporal cross-validation ideas

### Reproduce historical decisions

At every validation decision, reconstruct predictor information using `available_at`, admit only
training labels matured by that decision, fit all learned state on the legal training rows, and
predict without the validation outcome. Random shuffling is incompatible with this proposition.

Expanding windows, rolling windows, blocked folds, and event-group folds answer different stability
questions. Choose them from the deployment/research claim, not from the best score.

### Purging and embargo

Purging removes training examples whose label-information intervals overlap a validation interval.
An embargo removes a declared neighboring region when an additional serial-dependence path remains.
Purging follows from exact label spans; embargo requires a named threat and size policy. Neither is
ceremony or a substitute for point-in-time data.

For Polymarket, group separation may also be needed across related contracts, but cannot be claimed
until authoritative event/group identity exists.

### Selection exposure remains after legal folds

Repeatedly trying features, labels, horizons, models, metrics, windows, and thresholds on the same
development folds can find an attractive false positive. Count all trials through ancestry, fix a
budget and stopping rule, and reserve protected evidence for one frozen falsification. A third split
does not remain fresh if researchers use it repeatedly or indirectly.

## Feature-diagnostic ideas

Feature diagnostics can suggest mechanisms, redundancy, instability, and failure. They do not
promote features automatically.

### Impurity-based importance

Tree split importance is fast and in-sample. It can assign importance to noise, favor variables with
many split points, and divide credit among substitutes. Treat it as a model-behavior description,
not predictive proof.

### Out-of-fold permutation or ablation

Measure how legal out-of-fold performance changes when a feature or group is perturbed. Preserve the
temporal structure of the perturbation when ordinary row shuffling would create impossible data.
Correlated substitutes can hide one another, so grouped or conditional perturbations may answer a
better question.

### Single-feature and grouped evidence

Single-feature models show stand-alone signal and avoid substitution effects, but miss interactions.
Grouped models can test mechanisms such as activity, price state, or flow without pretending every
column has an independent interpretation. Compare both with the full system.

### Orthogonal views

PCA or another fold-fitted orthogonal representation can expose redundant directions or reduce
dimension. Components are transformations rather than economic mechanisms, and unsupervised does
not mean leakage-free if fitted on future data. Compare component stability and the agreement
between unsupervised structure and predictive diagnostics without treating agreement as validation.

### Cross-contract and regime stability

Importance may be computed within contracts or on a stacked population. Within-contract results can
reveal heterogeneity; stacking can test shared structure but requires compatible semantics and group
controls. Current missing event identity prevents authoritative independence claims. Always inspect
time, price regime, activity, contract, seed, and missingness stability.

## Hyperparameter-search ideas

### Search is part of model fitting and selection

Grid search is transparent but scales poorly. Random search can allocate a fixed trial budget across
many dimensions and can sample scale parameters on a logarithmic scale. More adaptive search methods
are possible, but each observation of development performance changes selection exposure.

All preprocessing, sampling, weighting, feature selection, model parameters, and ensemble choices
influenced by search must be nested inside the legal training boundary. Record the sampled space,
seed, failed configurations, score, resource budget, and winning ancestry.

### Match the score to the decision

Accuracy ignores probability confidence and can be misleading under imbalance. Log loss examines
probability quality; Brier-style error examines probability calibration; precision/recall/F-scores
examine selective classification; continuous error metrics answer regression questions. Economic
utility or PnL requires additional execution and decision assumptions not supplied by the current
research kernel.

Choose the score before search and report complementary diagnostics. A metric selected because it
makes the candidate look best is another trial.

### Prefer bounded, interpretable searches

Start from a simple baseline and a small space justified by the mechanism. Widen only when evidence
shows underfitting or boundary effects. Randomized or log-scale examples are ways to spend a budget,
not instructions to maximize it. Stop when additional search no longer tests a distinct scientific
idea.

## Polymarket research menus

These menus illustrate combinations that could answer concrete questions. They are not roadmaps to
run wholesale.

### Transaction microstructure

- Compare next-print changes with same-aggressor, opposite-aggressor, and longer-horizon changes.
- Contrast clock-time, trade-count, size, notional, imbalance, and run sampling.
- Condition on price boundary, activity, size, interarrival time, and outcome leg.
- Falsify apparent flow effects with spread-direction mechanics and subperiod stability.

### Activity and information arrival

- Ask whether bursts, droughts, or imbalance changes precede a change in later transaction state.
- Compare fixed schedules with event-triggered samples and report the unsampled population.
- Test whether an effect survives raw levels, within-contract normalization, and multiple activity
  regimes.

### Cross-contract structure

- Study whether transformations behave similarly across exact contract identities and price
  regimes.
- Keep contract-level results separate from pooled results.
- Treat common event membership and mutual exclusivity as unresolved until authoritative grouping
  is registered.

### Probability dynamics and calibration

- Explore bounded-price changes, logit-space changes away from boundaries, path excursions, or
  persistence baselines.
- Do not claim calibration to outcomes without legal resolution labels and exact availability.
- Do not call a transaction price a frictionless probability without confronting execution and
  microstructure alternatives.

### Model comparisons after a mechanism survives

- Compare a persistence/mean baseline, a regularized linear or simple nonlinear learner, and a
  variance-controlled ensemble.
- Add transforms or interactions one mechanism at a time.
- Diagnose feature contribution with fold-legal ablation, grouped permutation, and stability rather
  than a single importance ranking.
- Bound tuning and retain every attempt.

## Method-selection record

When a catalog idea is used, preserve this compact record with the study or candidate memo:

```text
Question and mechanism:
Rival explanation:
Exact data/view and decision clock:
Idea family and why it is relevant:
Required fields and legal prerequisites:
Fixed choices:
Fold-learned choices:
Simpler baseline:
Falsifier:
Trial-budget and parent-trial effect:
Outcome: retain | revise | reject | blocked
Evidence/artifact references:
```

This catalog preserves possibilities. The harness determines whether an authored implementation was
legal and reproducible; evidence determines whether the idea survives.
