# evaluation.grade-research-behavior — scenario state/actions/evidence/traps + provider → graded behavioral outcome

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Establish whether the composed agent—not just local plumbing—respects research, retrieval, recovery, authority, commit and scientific-evidence behavior.

## Relevant locked invariants

Test strategy Layer 4; all relevant invariants per scenario.

## Source A

Explicit scenario with initial task/state/environment, actions, hidden trap, evidence/artifacts, budgets, provider type, required/forbidden behaviors and graders.

## Destination B

Reproducible run trace and multidimensional graded outcome with evidence level, seeds/config, failures and no exact-prose dependence.

## Mapping f

Run composed runtime; observe public actions/effects; grade invariant properties and scientific behavior; aggregate repeated Level D trials where stochastic.

## Must preserve

Scenario/version, provider/config/seed, available info/actions, trace/effects, grader rules/results, budgets, artifacts.

## May transform

Equivalent representation may change where semantic meaning, identity, status and observable behavior survive.

## Must exclude

Exact prose assertions, hidden grader access used by agent, Level B called autonomous, score hiding authority violation, training on eval outcomes.

## Authority boundary

Scenario owner defines standards; agent/provider acts; deterministic harness enforces authority; grader measures but cannot mutate/retrain.

## Allowed state mutation

Eval run/results/artifacts/audit.

## Forbidden state mutation

No production state/evidence promotion, provider training, architecture change.

## Failure semantics

Harness/infrastructure failure distinct from behavioral failure; invalid grader blocks conclusion; authority/science failures dominate cost.

## Observable consequences

Scenario families catch premature stopping, missing retrieval, failure repair, formal versioning, gate denial, stale belief, redundancy, reproducibility and commits.

## False-success implementations considered

Scripted queue passes despite ignoring context; grader rewards final answer while authority was bypassed.

## Falsifying tests

For causal scenarios use Level C paired interventions/sentinel; for reasoning quality use repeated Level D property graders; adversarially delete context and inject traps.

## Mutation-sensitivity check

**Mutation:** Call a context-independent scripted sequence “autonomous reasoning.”

**Expected failure:** Evidence-level audit and paired intervention expose no causal response.

## Composite dependencies

runtime.run-bounded-episode/research.continue-from-exploration/development.revise-candidate/context.rebuild-after-loss/learning.influence-future-research plus protected seams.

## Fundamentals review

`CONSISTENT`: the seam honestly separates deterministic causality from stochastic reasoning quality.

## Grill findings

Added grader validity, forbidden-behavior dominance and evaluation-not-training.

## Remaining user decisions

None; per-scenario success thresholds remain human-owned before execution.
