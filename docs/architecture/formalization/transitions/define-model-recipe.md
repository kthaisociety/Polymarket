# model.define-recipe — candidate model/recipe → ModelDefinition

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Formalize a reproducible model and selection recipe distinct from learned fitted state.

## Relevant locked invariants

I2–I6, I13, I17, I24; model ontology.

## Source A

Candidate model idea plus algorithm, hyperparameters or frozen selection procedure/search space, preprocessing dependencies, randomness, training requirements, provenance/ancestry.

## Destination B

Immutable versioned ModelDefinition with complete recipe/selection semantics and no learned parameters.

## Mapping f

Validate completeness/reproducibility and learned-state ownership; publish definition/lineage.

## Must preserve

Algorithm, parameters/search procedure, preprocessing, randomness, compatibility, training protocol refs, provenance.

## May transform

Equivalent representation may change where semantic identity and behavior survive.

## Must exclude

Fitted coefficients, hidden data-derived choices, defaults changing meaning, artifact-as-definition, latest dependency, in-place edit.

## Authority boundary

Agent proposes; formal validator publishes recipe; training.fit-system learns within W_t.

## Allowed state mutation

Create model definition/version/lineage.

## Forbidden state mutation

No fit/selection execution, feature/system mutation, freeze/promotion.

## Failure semantics

Missing material recipe/selection semantics blocks; repair changing meaning creates new version.

## Observable consequences

Definitions differing only in selection procedure/random policy have distinct identities; no fitted state exists.

## False-success implementations considered

Serialize fitted estimator as definition; omit hyperparameter-search procedure.

## Falsifying tests

Fail-on-fit, inspect absence of learned state, vary each semantic dimension and assert identity. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Embed fitted coefficients in ModelDefinition.

**Expected failure:** No-learned-state test turns red.

## Composite dependencies

formalization.create-candidate; system.assemble-definition system; training.fit-system trainer; formalization.version-material-change.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added selection-procedure identity and artifact distinction.

## Remaining user decisions

None.
