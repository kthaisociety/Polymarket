# backtest.request-evaluation — frozen system + evaluation world/spec + caller → BacktestRequest

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Bind a protected-evidence request to exact frozen identity, predeclared scenario, evaluation intent, data scope and requester before exposure.

## Relevant locked invariants

I4–I8, I13, I24–I25.

## Source A

Exact frozen system, evaluation world/scenario/decision times, EvaluationSpec/promotion-standard refs, protected resource scope, caller/request/idempotency identity.

## Destination B

Immutable BacktestRequest with exact scientific/scenario/data/authority identity and provenance, not permission.

## Mapping f

Validate structural completeness and frozen refs; bind canonical semantic request identity; emit for governance.

## Must preserve

Frozen identity, scenario/decision times, data slice, evaluation/promotion refs, caller, ancestry/exposure context, key.

## May transform

Equivalent representation may change where exact scientific meaning, identity and behavior survive.

## Must exclude

Unfrozen/latest system, unspecified scenario/criteria, protected data read, permit, mutable request, hidden retry changes.

## Authority boundary

Agent may request; governance backtest.authorize-request alone permits.

## Allowed state mutation

Create request/audit/ledger record.

## Forbidden state mutation

No protected access/exposure/run/evaluation.

## Failure semantics

Incomplete/mismatched request rejected without data read; semantic changes under key conflict.

## Observable consequences

Requests differing only in system/scenario/data/criteria have distinct identities and governance evaluation.

## False-success implementations considered

Request “latest best model”; inspect holdout metadata/values to fill criteria.

## Falsifying tests

Vary every semantic dimension; fail-on-protected-read; unfrozen input rejected. **Level A.**

## Mutation-sensitivity check

**Mutation:** Accept unfrozen candidate and resolve it at execution time.

**Expected failure:** Unfrozen/exact-identity test red.

## Composite dependencies

freeze.seal-system; backtest.authorize-request; governance.retry-privileged-operation.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added criteria-before-content and semantic idempotency.

## Remaining user decisions

None.
