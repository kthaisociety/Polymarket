# feature.define-identity — candidate feature + semantics → FeatureDefinition

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Promote exploratory computation into a reproducible, time-legal feature identity.

## Relevant locked invariants

I1–I2, I5–I6, I13, I17, I24; feature ontology.

## Source A

Candidate plus exact dependencies/FieldRefs, temporal mapping, information-preservation/removal intent, warm-up/initialization/truncation/boundary behavior, missingness, fixed versus data-selected parameters, fitted-state procedure, code/expression identity, environment and evidence ancestry.

## Destination B

Immutable versioned FeatureDefinition describing phi(D<=t)->z_t, with provenance/lineage and explicit fitted operations.

## Mapping f

Validate completeness, exact refs, causal/availability semantics, missingness and fitted-state ownership; publish definition, not values.

## Must preserve

Scientific mapping, dependencies, lags/windows, availability, units/output, retained/removed history semantics, warm-up/truncation/boundaries, missingness, parameter-selection/fitted procedure, provenance.

## May transform

Equivalent representation may change where semantic identity and behavior survive.

## Must exclude

Exploratory diagnostics as feature, stationarity-test success as automatic admission, hidden global fit or parameter selection, latest field, implicit fallback, values/materialization, in-place change.

## Authority boundary

Agent proposes; formal validator checks identity/legality; feature.materialize-definition materializes and training.fit-system fits learned operators.

## Allowed state mutation

Create definition/version/lineage/ledger record.

## Forbidden state mutation

No fitting/materialization/promotion/freeze or prior mutation.

## Failure semantics

Unresolved dependency/time/missingness/fitted semantics blocks formalization; meaning change creates new version.

## Observable consequences

Equivalent representation yields same meaning; changing lag/field/missingness/warm-up/truncation/parameter-selection/fitted procedure yields new identity.

## False-success implementations considered

Wrap notebook output as definition; hide scaler/PCA fit; substitute field.

## Falsifying tests

Omit each semantic and require failure; mutate each meaning dimension and require new identity;
fail-on-fit; distinguish expanding-history from fixed-width boundary behavior; catch globally selected
transformation parameters with a future-regime fixture. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Exclude fitted-state and finite-history boundary semantics from identity.

**Expected failure:** Identity tests turn red when fitted/non-fitted or expanding/fixed-width meanings collide.

## Composite dependencies

formalization.create-candidate candidate; feature.compile-definition compile; feature.materialize-definition materialize; formalization.version-material-change version.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added fail-on-fit and meaning-dimension identity attacks.

## Remaining user decisions

None.
