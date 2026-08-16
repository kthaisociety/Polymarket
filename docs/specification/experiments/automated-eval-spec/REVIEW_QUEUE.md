# Evaluation-design review queue

## ARCHITECTURE_GAP

None.

## USER_DECISION_REQUIRED

None. Scenario effect bands, ambiguity bands, budgets, and acceptance thresholds are evaluation-owner choices that must be predeclared per run; no universal product threshold was invented.

## ARCHITECTURE_CONFLICT

None.

## TEST_INSUFFICIENT

None after reconciliation.

## Reviewed deterministic composites

observation-to-next-action–validated-learning-to-future-behavior: `CONSISTENT`, HIGH risk. Every item has `P(A)⇒Q(C)`, an objective oracle, intermediate propagation evidence, side-channel exclusions, a discriminating counterfactual, and a violating mutation.

## Reviewed behavioral families

signal-discrimination–avoid-harmful-lesson-overgeneralization: `CONSISTENT`. Each is a randomized family with hidden-truth isolation, complementary worlds defeating blanket policies, objective graders for exact facts, and only narrowly scoped semantic judgment.

## Reconciled grill findings

- Endpoint sequence replaced with causal/intermediate assertions.
- Fixed puzzles replaced with randomized matched distributions.
- Scripted behavior exposed with fresh-session counterfactuals and sentinels.
- Hidden labels placed outside all agent-visible capabilities.
- Grader facts independently computed rather than inferred from claims.
- LLM judges removed from deterministic facts and denied authority over hard failures.
- Scientific procedures remain free; only evidence quality/outcomes are graded.
- Test-only paths cannot stand in for production compositions.
- Retry, partial commit, exposure-on-failure, stale identity, and losing-history cases are explicit.

## Batch skill audit

Composite batch:
- system-eval-design: applied
- fundamentals-review: applied
- grill-with-docs: applied

Behavioral batch:
- system-eval-design: applied
- fundamentals-review: applied
- grill-with-docs: applied
