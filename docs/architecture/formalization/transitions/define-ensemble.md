# model.define-ensemble — selected model definitions/method → EnsembleDefinition

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Freeze ensemble membership and combination method separately from learned weights.

## Relevant locked invariants

I2, I5–I6, I13; ensemble semantics.

## Source A

Exact model definitions, ensemble method/parameters, weight-learning or fixed-weight procedure, ordering/compatibility, provenance.

## Destination B

Immutable versioned EnsembleDefinition with exact members/method and explicit learned-state procedure, no fitted weights unless fixed constants are definition.

## Mapping f

Validate members/method; distinguish fixed constants from weights learned within W_t; publish identity/lineage.

## Must preserve

Members/versions/order, method, fixed vs learned weights, training procedure, provenance.

## May transform

Equivalent representation may change where semantic identity and behavior survive.

## Must exclude

Latest model substitution, prefit weights, implicit equal-weight fallback, in-place edit, fitted models.

## Authority boundary

Definition records recipe; training.fit-system fits learned weights.

## Allowed state mutation

Create definition/version.

## Forbidden state mutation

No fitting/model mutation/system freeze.

## Failure semantics

Unsupported/incompatible method or missing weight semantics fails; no equal-weight fallback.

## Observable consequences

Changing member/version/method/weight procedure changes identity; learned weights absent before fit.

## False-success implementations considered

Compute weights on all data during definition; default equal weights.

## Falsifying tests

Fail-on-fit; inspect identity variants; insufficient weight semantics fails. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Store learned weights in definition from exploratory full data.

**Expected failure:** Fail-on-fit/no-learned-state test turns red.

## Composite dependencies

model.define-recipe; system.assemble-definition; training.fit-system.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added fixed-versus-learned distinction and no equal-weight fallback.

## Remaining user decisions

None.
