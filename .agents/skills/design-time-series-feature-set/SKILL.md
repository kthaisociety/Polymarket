---
name: design-time-series-feature-set
description: Design or revise a time-series target, label, feature set, and candidate model recipe from exploratory evidence. Use when Codex or a repository-aware research agent must turn a hypothesis into authored make_features/make_label/fit/predict code or formal FeatureDefinition candidates, interpret feature analysis, or revise a development candidate. Preserve temporal legality, fitted-state boundaries, alternatives, and trial ancestry without prescribing one transformation or model family.
---

# Design a Time-Series Feature Set

Turn a mechanism and an exact prediction question into a small falsifiable candidate.

## Load the principles

Read [references/principles.md](references/principles.md) completely before proposing or revising a
candidate. Treat it as guidance; the harness remains the authority for legality and identity.

## Design the candidate

1. Define the decision, population, target meaning, horizon, outcome path, maturity, units,
   censoring, missingness, and insufficiency behavior. A label is part of the hypothesis.
2. State the mechanism: why should information legally available at the decision time help predict
   that label at that horizon?
3. Propose the smallest feature set that distinguishes the mechanism from useful rivals. For every
   feature, declare dependencies, time mapping, lag/window, units, dimensions, warm-up, failure
   behavior, and which parameters are fixed versus learned.
4. Put every learned transformation, selection rule, hyperparameter procedure, model, and ensemble
   weight inside the legal training window. Keep `predict()` inference-only.
5. Declare simple baselines, temporal development protocol, metric meaning, expected failure modes,
   and evidence that would reject or revise the candidate.
6. Interpret performance and feature-analysis methods jointly. Preserve disagreement caused by
   interactions, redundancy, substitutes, regimes, instability, or missingness rather than
   automatically pruning the lowest-ranked feature.
7. Create a new version with parent-trial ancestry for every meaning-changing revision. Retain
   failed and rejected variants.

When the mechanism calls for additional financial-market alternatives, consult only the relevant
section of the [optional idea catalog](../../../docs/research-guidance/financial-machine-learning-ideas.md).
Choose examples because they sharpen a falsifier, never because they appear in the catalog.

## Return a candidate memo

Return:

- exact question, analysis-evidence, catalog/environment, and parent-trial references;
- target/label contract and why its maturity is legal;
- a semantic feature table: name, hypothesis, inputs, temporal mapping, fitted state, failure
  behavior, and falsifier;
- authored program or formal definitions plus model/training recipe;
- development baselines, folds, metrics, budget, and stopping rule;
- known alternatives, uncertainties, and explicit `retain`, `revise`, `reject`, or `evaluate`
  recommendation.

Do not claim a feature is useful because it is stationary, important in-sample, or convenient. Do
not request a protected backtest until the separate backtest-gate review is complete.

## Improve the skill from research feedback

Update `references/principles.md` only from a traceable research failure or repeated cross-task
pattern. Generalize the lesson, name when it does not apply, and add a counterexample. Do not turn
the latest winning feature family into a mandatory recipe.
