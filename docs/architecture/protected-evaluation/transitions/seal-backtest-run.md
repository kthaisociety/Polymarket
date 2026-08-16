# backtest.seal-run — completed execution records + frozen/scenario provenance → immutable BacktestRun

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Seal exactly what happened, including failures and exposure, as an immutable simulation record rather than a performance report.

## Relevant locked invariants

I11–I13, I17, I24.

## Source A

Complete ordered backtest.execute-scenario records, frozen/system/scenario/permit/data/environment identities, failures, exposure/audit/artifacts, completion status.

## Destination B

Immutable BacktestRun referencing exact sequence and provenance, complete or explicitly failed/incomplete; no metrics judgment.

## Mapping f

Validate completeness/order/correlation; bind all records; publish coherently and immutably.

## Must preserve

All identities/times/records/failures/omissions/status/provenance/exposure.

## May transform

Equivalent representation may change where exact scientific meaning, identity and behavior survive.

## Must exclude

Failure filtering, record rewrite, metric/evaluation, latest-system/data substitution, partial healthy run, mutable append after seal.

## Authority boundary

Assembler seals facts; evaluator reads but cannot rewrite.

## Allowed state mutation

Create run/ledger record atomically.

## Forbidden state mutation

No record/system mutation, evaluation/validation/promotion.

## Failure semantics

Missing/torn/inconsistent records prevent completed status; correction creates linked new record/run, never rewrite.

## Observable consequences

Reload yields failures and exact records; later evaluation cannot edit run.

## False-success implementations considered

Drop failed fits; seal partial list as completed; add outcomes later in place.

## Falsifying tests

Inject missing/out-of-order/corrupt record and require non-complete; attempt mutation; failure count preserved. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Filter failed decision times before sealing.

**Expected failure:** Failure-count/sequence test red.

## Composite dependencies

backtest.execute-scenario; evaluation.measure-run; ledger.preserve-scientific-history.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added complete-versus-failed status and correction lineage.

## Remaining user decisions

None.
