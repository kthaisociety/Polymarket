# commit.validate-proposals — CommitRequest + authoritative current evidence → independent validation decisions

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Authorize episode lifecycle and durable understanding as separate propositions so a valid transition cannot smuggle an invalid state change, and validation cannot mutate what it judges.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I8–I10, I13, I16–I17, I25.
- `docs/specification/STATE_CONTEXT_AND_MEMORY.md`, semantic commit boundaries.
- `docs/specification/MILESTONE_1_RUNTIME_DESIGN.md`, independent proposal validation.

## Source A

An exact `CommitRequest`, current session/episode/state/environment versions, authoritative permitted evidence/provenance, permissions, lifecycle rules, and current epistemic position.

## Destination B

Separate immutable validation decisions for the required episode proposal and optional state proposal, each with accepted/rejected status, reasons, validated identities/versions/evidence, and request correlation. State absence is an explicit not-applicable decision.

## Mapping f

Load exact current records; validate episode transition legality independently; if a state proposal exists, validate base version, mission scope, evidence support/permission/provenance, and absence of unsupported claims; emit decisions without mutation. Coordinator requires every applicable acceptance.

## Must preserve

Request/idempotency identity, proposal presence, exact base versions, target status, synthesis/delta, evidence refs, mission constraints, permissions, and decision reasons.

## May transform

Validation facts into typed decisions and safe repair guidance; no proposal meaning may be rewritten.

## Must exclude

Beneficiary self-approval, validator mutation, implicit proposal creation, latest-version substitution, unauthorized/invalid evidence, forged gates, protected-value leakage in denial, and “episode valid therefore all valid.”

## Authority boundary

Independent harness validators judge their respective propositions. The proposing agent/provider cannot grant approval. commit.publish-boundary coordinates only completed applicable decisions and cannot weaken them.

## Allowed state mutation

Append bounded validation observability/rejection records. No target scientific records change.

## Forbidden state mutation

No episode/state write, evidence rewrite, permission/exposure change, gate promotion, proposal repair, or commit.

## Failure semantics

Illegal lifecycle, stale state/version, or invalid/unauthorized evidence yields the corresponding explicit rejection. Any applicable rejection blocks the whole commit. Indeterminate evidence/currentness fails closed. Safe reasons support a new corrected request; they do not expose forbidden contents.

## Observable consequences

A valid episode resolution paired with stale or unsupported state delta produces one accepting and one rejecting decision and changes neither store. Lifecycle-only requests do not invoke a fictitious state validator.

## False-success implementations considered

- One validator approves both proposals.
- Episode acceptance authorizes state implicitly.
- Validator writes while checking.
- Validate against latest state/evidence.
- Trust evidence IDs without checking permitted substantive support.

## Falsifying tests

1. Pair valid lifecycle with stale state and with unauthorized/unsupported evidence; assert separate decisions and no writes. **Level A/B.**
2. Lifecycle-only request yields accepted episode decision plus explicit state-not-applicable, not an invented delta.
3. Fail-on-write stores and a beneficiary-controlled validator prove validators cannot self-authorize/mutate.
4. Revoke evidence permission or supersede a version between request and validation; assert rejection without content leakage/latest substitution.

## Mutation-sensitivity check

**Mutation:** treat episode-validator acceptance as authorization for the entire request.

**Expected failure:** test 1 becomes red because stale/unsupported state is allowed or stores are changed downstream.

## Composite dependencies

commit.compose-request supplies exact proposals; commit.publish-boundary applies only all accepted applicable decisions; commit.retry-idempotently preserves retry identity; runtime.return-repairable-failure turns repairable rejection into loop evidence.

## Fundamentals review

`CONSISTENT`. Independent authority and state-pure validation follow locked semantic-commit rules.

## Grill findings

Resolved non-semantically: clarified not-applicable state decision and evidence semantics beyond opaque reference existence.

## Remaining user decisions

None. Validator decomposition and reason-code representation remain free.
