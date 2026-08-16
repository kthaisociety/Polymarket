# report.render-finding — ValidatedFinding → human-facing report

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Allow flexible AI wording/layout while preserving canonical scientific substance.

## Relevant locked invariants

I13, I19; reporting contract.

## Source A

Exact immutable finding, audience/layout request, permitted artifacts/branding.

## Destination B

Human-readable report traceably rendering claim, evidence, metrics, caveats, provenance and validation status.

## Mapping f

Generate presentation from finding; verify every substantive statement/status/ref against canonical fields; reject overstatement/omission.

## Must preserve

Claim scope, target/horizon, metrics, robustness, caveats, refs/provenance, status.

## May transform

Equivalent representation may change where semantic meaning, identity, status and observable behavior survive.

## Must exclude

New scientific claim, omitted caveat, status upgrade, altered metric, economic recommendation as validation, mutable finding.

## Authority boundary

AI controls presentation only; verifier/finding own substance.

## Allowed state mutation

Create report/artifacts/audit.

## Forbidden state mutation

No finding/evidence/decision/state mutation.

## Failure semantics

Unsupported/contradictory/omitted required substance blocks publication; no “helpful” rewrite.

## Observable consequences

Different styles remain semantically equivalent and all required caveats trace to finding.

## False-success implementations considered

Paraphrase association as causation; drop caveat for concision.

## Falsifying tests

Generate adversarial variants and semantic grader compares structured claims/caveats/status to finding, not exact prose. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Omit a critical instability caveat while retaining positive headline.

**Expected failure:** Required-substance grader red.

## Composite dependencies

finding.publish-validated-claim; no downstream business action decision.apply-validated-finding.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added claim entailment and required-caveat verification.

## Remaining user decisions

None.
