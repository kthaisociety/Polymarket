# Fundamentals review template

## Overall verdict

`CONSISTENT | CONCERN | ARCHITECTURE_CONFLICT | USER_DECISION_REQUIRED | TEST_INSUFFICIENT`

One-sentence reason.

## Reviewed proposition

`Sxxx: A -> B` and the observable consequence the provisional contract claims.

## Strong agreement

- Contract claim.
- Governing source.
- Why the mapping preserves the project principle.

## Findings

For each finding:

### [verdict] Short title

- Source: exact repository path and section/invariant.
- Contract claim: the challenged statement or test.
- Attack: weakest plausible implementation, counterexample, or conflicting interpretation.
- Consequence: what can become scientifically, operationally, or architecturally false.
- Resolution owner: `non-semantic reconciliation` or `human arbitration`.

Omit this section only for a clean `CONSISTENT` result.

## Test adequacy

- Claimed proposition and evidence level.
- Violating mutation.
- Exact test expected to become red.
- Causality/side-channel assessment.
- Local proof versus required composite proof.

## Scope discipline

- Correctly deferred neighboring responsibilities.
- Missing composite dependencies, if any.
- Unnecessary criticism deliberately rejected.

## Limits

State what this review did not prove and confirm that no canonical contract/register was edited.
