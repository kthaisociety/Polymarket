# training.fit-system — frozen recipe + legal W_t → FitRecord + immutable fitted system F_t

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Fit every learned quantity only inside the legal window under the exact frozen procedure.

## Relevant locked invariants

I1–I6, I13, I17, I24; SystemTrainer.

## Source A

Exact frozen/candidate recipe permitted for fitting, W_t, identity-bearing
`TrainingInformationBundle` containing ordered legal `I_t` views, environment/data versions,
seeds/resources, nested selection protocol.

## Destination B

Immutable fitted system F_t and FitRecord naming recipe/window/data/environment, every learned component/state, procedure, status/warnings/artifacts.

## Mapping f

Compile exact feature definitions; materialize their historical values from the bundle's legal
views; perform nested legal fitting/selection solely on W_t; record bundle/view/compiler/series and
all learned-state provenance; fail explicitly.

## Must preserve

Recipe, window, catalog, sample, row, information-set, compiled-feature, and feature-series
identities; all preprocessing/selection/model/ensemble learned state, seeds/environment, failures.

## May transform

Equivalent representation may change where semantic identity and behavior survive.

## Must exclude

Data outside W_t, global prefit state, undeclared fallback, fit during predict, recipe mutation, omitted learned preprocessing.

## Authority boundary

Trainer alone learns; evaluator/predictor do not. Frozen recipe determines procedure.

## Allowed state mutation

Create F_t/FitRecord/artifacts/ledger records.

## Forbidden state mutation

No definition/window/source mutation, prediction/evaluation/promotion.

## Failure semantics

Any component failure is typed; only predeclared fallback may run; meaning-changing repair is new candidate.

## Observable consequences

Changing one out-of-window sentinel never changes F_t; changing W_t legal values may. Every learned component traces to W_t.

## False-success implementations considered

Fit scaler/PCA globally; evaluate lag as latest/current value; accept caller-authored feature
series; silently reduce PCA components; omit selection ancestry.

## Falsifying tests

Poison outside W_t and assert identical fit; distinguish lag from latest on an irregular signal;
inspect bundle/view/compiler/series and learned provenance; induce component failure and require no
F_t/fallback. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Fit preprocessing on all S_t before selecting W_t.

**Expected failure:** Out-of-window poison changes fitted state, test red.

## Composite dependencies

data.select-training-window/system.assemble-definition/training.block-invalid-fallback; prediction.generate-record predict; ledger.record-trial-lineage ledger.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added out-of-window poison and nested learned-state inventory.

## Remaining user decisions

None.
