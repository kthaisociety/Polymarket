# backtest.authorize-request — BacktestRequest + governance state → BacktestPermit or safe denial

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Independently authorize protected evaluation only when freeze, gates, ancestry, exposure, permission and predeclaration are valid, without leaking contents.

## Relevant locked invariants

I4, I7–I8, I13–I14, I22, I25.

## Source A

Exact request plus frozen/gate/trial/ledger/exposure/permission/protected-scope state and independent authority.

## Destination B

Scope-bound immutable permit or safe denial with reasons/correlation and no protected values.

## Mapping f

Validate exact current records, unexposed claim eligibility, caller, scenario/data scope, criteria and ancestry; issue one-use/idempotent permit or deny.

## Must preserve

Request/system/scenario/scope/authority/policy versions, exposure/ancestry facts, decision reason.

## May transform

Equivalent representation may change where exact scientific meaning, identity and behavior survive.

## Must exclude

Beneficiary approval, content peek, broad/reusable permit, latest substitution, denial leakage, hidden criterion change.

## Authority boundary

Independent governance decides; requester/candidate cannot grant. backtest.bind-protected-view/backtest.execute-scenario cannot broaden permit.

## Allowed state mutation

Permit/denial/ledger records.

## Forbidden state mutation

No protected content read/exposure/run/promotion.

## Failure semantics

Indeterminate/missing/stale/exposed state fails closed; denial safe; exact replay converges.

## Observable consequences

Exposed lineage or unfrozen system denied with zero protected reads; valid exact request gets only scoped permit.

## False-success implementations considered

Check holdout performance before permit; ignore ancestor exposure; wildcard permit.

## Falsifying tests

Fail-on-content protected store, modified descendant after exposure, scope variants, self-authorizer. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Ignore exposure of parent lineage after candidate modification.

**Expected failure:** Exposure-lineage denial test red.

## Composite dependencies

backtest.request-evaluation/backtest.bind-protected-view/exposure.record-disclosure/governance.retry-privileged-operation.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added descendant exposure and permit-scope attacks.

## Remaining user decisions

None.
