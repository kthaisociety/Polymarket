# feature.materialize-definition — FeatureDefinition + legal environment → provenance-bearing FeatureSeries

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Materialize exact formal feature values under a named legal data environment without future access or global fitting.

## Relevant locked invariants

I1–I3, I13, I17, I24; feature materialization.

## Source A

Definition/expression, exact legal InformationSet/data view, materialization times, environment/schema, and where applicable already-fitted state tied to legal window.

## Destination B

Immutable FeatureSeries values indexed by time/entity with definition/environment/data/fitted-state provenance and explicit missing/failure status.

## Mapping f

Evaluate exact expression only on legal inputs; require fitted state from authorized trainer when needed; record per-value lineage.

## Must preserve

Definition/version, times, values/units, dependencies/vintages, environment, fitted-state/window ID, missingness/caveats.

## May transform

Equivalent representation may change where semantic identity and behavior survive.

## Must exclude

Future data, current vintage backfill, on-demand fitting, alternate operator/field, silent missing fallback, definition mutation.

## Authority boundary

Materializer computes; cannot learn or choose features. Fitted operations require supplied legal state.

## Allowed state mutation

Create immutable series/provenance/artifacts.

## Forbidden state mutation

No definition/source/fitted state mutation or state/evidence promotion.

## Failure semantics

Unavailable dependency/fit state or computation failure is explicit; no dropping feature or fitting globally.

## Observable consequences

Changing only data vintage/environment changes series identity/values; identical definition+environment is reproducible.

## False-success implementations considered

Fit scaler during materialization; use latest data; return all-NA success.

## Falsifying tests

Publication-delay/revision fixture, fail-on-fit, missing dependency explicit failure, exact lineage. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Fit missing scaler on all available data.

**Expected failure:** Fail-on-fit and leakage assertions turn red.

## Composite dependencies

data.build-information-set/feature.compile-definition; feature.assemble-set set; training.fit-system fitted state.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added already-fitted-state identity and all-NA false-success.

## Remaining user decisions

None.
