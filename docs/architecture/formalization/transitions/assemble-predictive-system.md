# system.assemble-definition — target + FeatureSet + models/ensemble + protocols → PredictiveSystemDefinition

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Assemble every choice changing experimental meaning into one versioned candidate identity.

## Relevant locked invariants

I2–I6, I13, I21–I24; central predictive-system ontology.

## Source A

Exact TargetDefinition, FeatureSet, model definitions, optional ensemble, training/window/selection/missingness and evaluation protocol/spec refs, environment/provenance/ancestry.

## Destination B

Immutable candidate PredictiveSystemDefinition with complete component identities and semantic digest/lineage, not yet frozen or fitted.

## Mapping f

Validate completeness/compatibility; bind exact versions; include every material protocol; publish candidate identity.

## Must preserve

All component versions, target/feature/model/ensemble/training/evaluation semantics, environment, ancestry, status.

## May transform

Equivalent representation may change where semantic identity and behavior survive.

## Must exclude

Latest substitution, omitted preprocessing/selection/evaluation, fitted state, frozen status, in-place change, hidden fallback.

## Authority boundary

Agent assembles; harness validates identity; freeze.seal-system freezes; training.fit-system fits only frozen recipe as required.

## Allowed state mutation

Create candidate system/version/ledger record.

## Forbidden state mutation

No fitting/freeze/backtest/evaluation/promotion or component mutation.

## Failure semantics

Incomplete/incompatible identity fails; any material repair/new choice is new version.

## Observable consequences

Changing one material component/protocol changes identity; historical system resolves exact components.

## False-success implementations considered

Hash only component names; omit evaluation protocol; include fitted objects.

## Falsifying tests

Vary each material dimension and assert identity; reload after newer components; fail-on-fit/freeze. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Omit preprocessing/selection procedure from system identity.

**Expected failure:** Identity-completeness test turns red.

## Composite dependencies

target.define-outcome/feature.assemble-set/model.define-recipe/model.define-ensemble; formalization.version-material-change/freeze.seal-system/training.fit-system.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added semantic-dimension matrix and historical exact resolution.

## Remaining user decisions

None.
