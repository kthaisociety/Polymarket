---
name: review-backtest-gate
description: Audit whether a development candidate is ready to request independent freeze and protected backtesting, and interpret a protected result without tuning on it. Use when Codex or a repository-aware research agent must challenge temporal cross-validation, trial selection, feature stability, frozen identity, predeclared scenarios, metrics, baselines, failure treatment, promotion standards, exposure, or backtest conclusions. This skill recommends; it never grants permission, promotion, or fresh-holdout status.
---

# Review the Backtest Gate

Treat protected evaluation as scarce falsification evidence, not the next development fold.

## Load the principles

Read [references/principles.md](references/principles.md) completely before recommending freeze or
interpreting protected evidence.

## Review before exposure

1. Resolve the exact candidate, target, feature set, model, training protocol, development evidence,
   environment, trial ancestry, and prior exposure. Reject aliases such as “latest” or “best.”
2. Challenge development legality: availability, label maturity, fold-local learned state,
   prediction without learning, overlap, appropriate purging, declared embargo, failures, and
   baseline construction.
3. Challenge selection: number and ancestry of trials, post-hoc choices, metric shopping, feature
   instability, redundancy, interactions, concentration, regime sensitivity, and plausible
   leakage paths.
4. Predeclare the protected resource scope, scenario and decision times, refit policy, metrics,
   baselines, slices, uncertainty/robustness views, failure and coverage treatment, claim, and exact
   promotion standard before protected content is read.
5. State what result would falsify the candidate. Recommend `REVISE`, `REJECT`, or
   `REQUEST_INDEPENDENT_ASSESSMENT`; never recommend approval by the benefiting actor.

## Interpret after exposure

Verify the immutable run and report identities. Interpret headline quality together with coverage,
failed dates, temporal/entity/regime stability, concentration, trial history, prior exposure, and
caveats. Do not tune, replace, repair, rescore, or relabel the frozen system after seeing protected
results. A new hypothesis becomes a new candidate, and the exposed period remains exposed.

## Return a gate memo

Return:

- exact candidate, evidence, trial, protocol, environment, and exposure references;
- satisfied checks and blocking deficiencies;
- leakage and overfitting challenge results;
- complete predeclared protected plan and falsification condition;
- recommendation with reasons and unresolved uncertainty;
- an explicit statement that independent governance and validation alone may authorize or promote.

## Improve the skill from research feedback

Update `references/principles.md` when a traceable run reveals a general false-success pattern or a
missing robustness question. Preserve the triggering evidence reference, describe when the lesson
applies, and include a counterexample. Never weaken a gate because a favored candidate failed it.
