---
name: analyze-time-series-data
description: Investigate authorized time-series data before formal candidate design. Use when Codex or a repository-aware research agent must understand field meaning, time axes, revisions, coverage, missingness, populations, aggregation, anomalies, plausible relationships, or the next exploratory question. Produce provisional analysis with exact evidence references; do not use this skill to formalize a feature, claim validation, or authorize protected access.
---

# Analyze Time-Series Data

Understand the data-generating and observation processes before optimizing a model.

## Load the principles

Read [references/principles.md](references/principles.md) completely before authoring analysis. Treat
it as versioned research guidance, not evidence and not executable authority.

## Run the loop

1. Restate the research question and exact authorized dataset, environment, field, population, and
   time boundaries. Preserve unresolved meaning instead of guessing.
2. Separate `reference_time`, `available_at`, label maturity, and the current research clock.
3. Inspect semantics, units, frequency, dimensions, aggregation levels, revisions, missingness,
   coverage, structural breaks, and measurement changes before interpreting relationships.
4. Author the smallest useful analysis that can distinguish competing explanations. Use the
   constrained analysis surface and retain actual access, code, parameters, random state, and
   artifact references.
5. Compare simple baselines and meaningful subperiod/entity views. Treat instability and
   conflicting results as evidence rather than noise to hide.
6. Separate observed facts from interpretations and hypotheses. Propose the next falsifying
   analysis, candidate-design step, or explicit stop.

## Return an analysis memo

Return:

- question and exact evidence/data references;
- fields and population actually accessed;
- temporal coverage, sample counts, missingness, revisions, and exclusions;
- observations supported directly by artifacts;
- alternative explanations and failed checks;
- limitations and epistemic status `EXPLORATORY`;
- one or more next questions, each with a proposed falsifier.

Do not emit a `FeatureDefinition`, frozen candidate, backtest recommendation, validated finding, or
durable memory update. Those require later skills and harness-owned transitions.

## Improve the skill from research feedback

Update `references/principles.md` only when a traced run exposes a general research failure or a
repeatedly useful distinction. Record the failure pattern, generalized principle, and a
counterexample that prevents overfitting the guidance to one dataset. Preserve the prior version in
Git. Never rewrite a research result merely because the guidance changes.
