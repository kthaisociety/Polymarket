# prediction.generate-record — F_t + legal current features from I_t → PredictionRecord

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Produce an immutable prediction without learning while preserving exact system/time/information identity.

## Relevant locked invariants

I1–I3, I11, I13, I24.

## Source A

Immutable F_t, exact legal current feature values/materializations from I_t, decision time/entity, prediction protocol/environment.

## Destination B

Immutable PredictionRecord with prediction/distribution, F_t/system/I_t/feature/time identity, status/warnings/provenance.

## Mapping f

Validate exact compatibility/current legal inputs; call inference-only path; record result immutably.

## Must preserve

Prediction semantics/value, all identities, decision time, inputs/vintages, environment, uncertainty/warnings.

## May transform

Equivalent representation may change where semantic identity and behavior survive.

## Must exclude

Fit/update/adapt/select, future values, latest-system substitution, outcome access, overwrite, silent missing fallback.

## Authority boundary

Predictor infers only; trainer owns learning; outcome/evaluator are downstream.

## Allowed state mutation

Create PredictionRecord/audit artifact.

## Forbidden state mutation

No learned-state/definition/data/outcome/evidence mutation.

## Failure semantics

Missing/illegal/incompatible features or inference failure is explicit; no retraining/imputation fallback unless frozen inference procedure contains it.

## Observable consequences

F_t content hash before/after identical; repeated same input predicts equivalently; future/outcome access zero.

## False-success implementations considered

Call fit_transform at predict; online update silently; choose newest model.

## Falsifying tests

Snapshot every learned state, fail-on-fit/update/outcome, exact-version test. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Update scaler statistics during predict.

**Expected failure:** Learned-state snapshot changes and test red.

## Composite dependencies

feature.materialize-definition/training.fit-system; outcome.record-mature-label outcome; backtest.execute-scenario backtest.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added deep learned-state snapshot, not only model coefficients.

## Remaining user decisions

None.
