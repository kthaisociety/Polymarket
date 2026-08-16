# ledger.record-negative-result — denied/rejected/failed protected operation → ledger + safe model result

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Retain negative scientific/governance history and exposure without leaking protected values or pretending success.

## Relevant locked invariants

I7, I11–I13, I17, I22.

## Source A

Denied request/permit, failed protected run/evaluation, rejected validation/finding with exact identities, exposure and safe reason/provenance.

## Destination B

Append-only negative ledger record and, where repairable/visible, safe structured result/observation retaining class/status/ancestry.

## Mapping f

Record exact negative outcome and exposure before safe feedback; externalize diagnostics; never erase or relabel.

## Must preserve

Request/candidate/evidence/decision/failure identity, reasons, exposure, trials, provenance and status.

## May transform

Equivalent representation may change where exact scientific meaning, identity and behavior survive.

## Must exclude

Protected values in denial, false success, deletion, “unseen” reset, winner-only history, automatic retry/promotion.

## Authority boundary

Governance/evaluator/validator produce; ledger preserves; model may reason but not override.

## Allowed state mutation

Negative ledger/trajectory/artifact and safe episode observation where allowed.

## Forbidden state mutation

No evidence rewrite, exposure reversal, promotion, permission grant.

## Failure semantics

Audit persistence required for truthful acknowledgement; denial safe/fail closed; failed disclosure remains exposed.

## Observable consequences

Rejected/failed attempt remains traversable and descendant cannot claim freshness; model-facing reason leaks no values.

## False-success implementations considered

Log only promoted findings; delete failed backtest; include protected metric in denial.

## Falsifying tests

Denial secret/value sentinels, failed-after-disclosure, rejection-history traversal. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Record exposure/rejection only for successful promotions.

**Expected failure:** Negative history/exposure test red.

## Composite dependencies

backtest.authorize-request/exposure.record-disclosure/backtest.execute-scenario/finding.validate-report; ledger.preserve-scientific-history.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added safe denial leakage and failed-disclosure persistence.

## Remaining user decisions

None.
