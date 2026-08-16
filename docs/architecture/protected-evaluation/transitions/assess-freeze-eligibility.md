# freeze.assess-eligibility — development candidate/evidence → freeze decision/request

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Establish that a candidate meets pre-freeze research criteria without letting its creator self-certify.

## Relevant locked invariants

I8, I13, I22, I24; promotion funnel.

## Source A

Exact candidate/version, research-validation standard, development evidence/trial ancestry, permissions/exposure and requester identity.

## Destination B

Independent accept/deny freeze eligibility decision and, if accepted, exact freeze request; no frozen object yet.

## Mapping f

Validate completeness, temporal legality, evidence status, ancestry and predeclared criteria; preserve denial reasons safely.

## Must preserve

Candidate/standard/evidence/protocol/trials/environment/requester and decision reasons.

## May transform

Equivalent representation may change where exact scientific meaning, identity and behavior survive.

## Must exclude

Self-approval, protected evidence as development, winner-only ancestry, latest candidate, implicit criteria, freeze mutation.

## Authority boundary

Agent requests; independent gate decides; freeze.seal-system seals.

## Allowed state mutation

Decision/request/ledger records.

## Forbidden state mutation

No candidate mutation, freeze, backtest, promotion.

## Failure semantics

Missing/invalid evidence or ambiguous criteria denies; no weakened/default standard.

## Observable consequences

Same candidate with complete vs missing failed-trial ancestry yields permit vs denial.

## False-success implementations considered

Trust candidate flag research_validated; count only winning metrics.

## Falsifying tests

Adversarial ancestry/evidence-status cases and beneficiary-controlled requester; require independent outcome. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Accept requester-authored `validated=true`.

**Expected failure:** Self-approval test turns red.

## Composite dependencies

development.evaluate-candidate/ledger.record-trial-lineage; freeze.seal-system.

## Fundamentals review

`CONSISTENT`: implied gate follows locked funnel/authority.

## Grill findings

Added ancestry and evidence-status attacks.

## Remaining user decisions

None; concrete standard is supplied policy.
