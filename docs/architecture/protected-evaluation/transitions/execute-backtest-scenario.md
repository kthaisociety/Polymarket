# backtest.execute-scenario — permit + frozen system + scenario → fit/prediction/outcome/failure sequence

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Execute one exact protected scenario across explicit decision times, rebuilding legal predictor and label boundaries and refitting the frozen recipe as declared, without overstating the scenario's interpretation.

## Relevant locked invariants

I1–I7, I17, I21–I26; backtest flow.

## Source A

Exact permit/view, frozen system, evaluation scenario decision times/world, registered data and runtime environment.

## Destination B

Ordered immutable fit/prediction/outcome/failure records with exact temporal/system/scenario/provenance and scenario interpretation, plus execution status for backtest.seal-run.

## Mapping f

For each t rebuild I_t/S_t/W_t independently; fit exact recipe; predict without learning; record outcome only when mature; retain failures; respect permit/limits; label historical, alternative-path and synthetic evidence according to the declared protocol.

## Must preserve

Permit/system/scenario and its interpretation, every time boundary, vintages, fit/prediction/outcome IDs, failures, seeds/environment, exposure.

## May transform

Equivalent representation may change where exact scientific meaning, identity and behavior survive.

## Must exclude

Future data outside the declared scenario semantics, generic new-data event, skipped failures, recipe fallback, evaluation/reselection, stale fits unless policy declares, hidden protected tuning, synthetic evidence relabeled as observed history.

## Authority boundary

Engine executes permit only; trainer/predictor local authorities; evaluator/validator later.

## Allowed state mutation

Execution records/artifacts/exposure/trajectory/ledger as governed.

## Forbidden state mutation

No frozen mutation, evaluation/promotion, failure omission.

## Failure semantics

Per-time failure recorded and behavior follows frozen scenario; undeclared repair/fallback forbidden; permit breach hard stops.

## Observable consequences

Adversarial release/maturity sequence yields exact different I_t/S_t changes and immutable records, including failed fits.

## False-success implementations considered

Build once using full history; omit failed dates; adapt model after outcomes.

## Falsifying tests

Multi-time leakage fixture, fail-on-evaluator/update, failure retention, exact decision sequence, and scenario-interpretation preservation. **Level B.**

## Mutation-sensitivity check

**Mutation:** Precompute features/scaler on full protected history.

**Expected failure:** Future-poison predictions/fits change and test red.

## Composite dependencies

data.register-observations–data.prove-temporal-substrate/training.fit-system–outcome.record-mature-label/training.block-invalid-fallback/backtest.bind-protected-view/exposure.record-disclosure; backtest.seal-run.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added full-history preprocessing poison and failure retention.

## Remaining user decisions

None.
