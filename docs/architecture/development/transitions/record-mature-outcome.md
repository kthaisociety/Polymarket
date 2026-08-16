# outcome.record-mature-label — mature realized target → immutable OutcomeRecord

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Record realized outcome separately and only when TargetDefinition says it is legally complete/available.

## Relevant locked invariants

I1, I11, I13, I23, I26.

## Source A

Exact prediction/target definition, registered target observations/vintage, decision/horizon/alignment, current simulated time and environment.

## Destination B

Immutable OutcomeRecord with realized label, completion/availability/reference times, target/prediction correlation, vintage/provenance/status.

## Mapping f

Resolve exact target; verify maturity/availability and alignment; publish once; revisions create explicit new linked record/version where policy allows.

## Must preserve

Target/prediction IDs, value/unit, time semantics, vintage/revision, environment, provenance.

## May transform

Equivalent representation may change where semantic identity and behavior survive.

## Must exclude

Premature outcome, reference-time-only maturity, predictor conflation, overwrite, latest revision retroactivity, evaluation/training.

## Authority boundary

Outcome recorder verifies; cannot evaluate or train.

## Allowed state mutation

Create immutable record/lineage/audit.

## Forbidden state mutation

No prediction/target/data rewrite or evidence promotion.

## Failure semantics

Immature/missing/ambiguous target yields not-yet-available/explicit failure; no placeholder/default.

## Observable consequences

Outcome absent before maturity and appears after; later revision cannot rewrite original.

## False-success implementations considered

Attach label at prediction time; overwrite with revised value.

## Falsifying tests

Maturity boundary and revision-lineage tests. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Use reference timestamp as maturity.

**Expected failure:** Pre-maturity record appears, test red.

## Composite dependencies

target.define-outcome/data.build-training-sample; backtest.execute-scenario/backtest.seal-run; evaluation.measure-run evaluates.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added separate not-yet-available status and revision history.

## Remaining user decisions

None.
