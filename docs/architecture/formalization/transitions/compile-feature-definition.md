# feature.compile-definition — FeatureDefinition → exact FeatureExpression / computation graph

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Compile stable feature meaning into executable representation without semantic substitution.

## Relevant locked invariants

I1–I2, I5–I6, I17, I24; FeatureDefinition versus AST distinction.

## Source A

Exact immutable FeatureDefinition and versioned operator/compiler/field registry environment.

## Destination B

FeatureExpression/graph semantically equivalent to the definition, with node/dependency/time/fitted-state provenance.

## Mapping f

Resolve exact refs/operators; encode transformations, temporal windows and fitted nodes; verify semantic equivalence; fail if unsupported.

## Must preserve

Definition identity, operator parameters/order, fields, time semantics, missingness, fitted boundaries, compiler version.

## May transform

Equivalent representation may change where semantic identity and behavior survive.

## Must exclude

Nearest operator/field fallback, eager fitting, algebraic “simplification” changing missing/time meaning, latest definition, silent unsupported behavior.

## Authority boundary

Compiler translates only; cannot fit, materialize, or rewrite science.

## Allowed state mutation

Create immutable compiled representation/provenance/cache.

## Forbidden state mutation

No definition/data/state mutation or learned state.

## Failure semantics

Unsupported/ambiguous operation fails explicitly; no approximate compiler fallback.

## Observable consequences

Distinct definitions produce correspondingly distinct graphs; evaluator can trace every node to definition semantics.

## False-success implementations considered

Replace unsupported operator with close one; drop lag; reorder non-equivalent missingness operations.

## Falsifying tests

Adversarial definitions where lag/drop/log order changes outputs; compile and compare semantic interpreter, fail unsupported. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Drop Lag node while retaining feature ID.

**Expected failure:** Graph/semantic-output test turns red.

## Composite dependencies

feature.define-identity; feature.materialize-definition executes; training.fit-system fits nodes.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added non-commutative transformation fixture and no-approximation rule.

## Remaining user decisions

None.
