# feature.assemble-set — selected FeatureDefinitions → versioned FeatureSet

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Preserve exact feature membership/versions/order semantics used by a candidate system.

## Relevant locked invariants

I5, I11, I13, I24; FeatureSet ontology.

## Source A

Explicit selected immutable feature definitions, selection rationale/evidence ancestry, ordering/naming policy, task/environment context.

## Destination B

Immutable versioned FeatureSet with exact member identities, membership semantics, lineage and provenance.

## Mapping f

Validate members/compatibility; canonicalize set representation without losing meaningful order/names; publish new identity.

## Must preserve

Exact members/versions, selection ancestry, output names/order where meaningful, environment constraints.

## May transform

Equivalent representation may change where semantic identity and behavior survive.

## Must exclude

Latest member substitution, duplicate collision, implicit selection, omitted failed trials, in-place membership edit, materialized values.

## Authority boundary

Agent proposes selection; harness validates identity. No fitting/selection learning here.

## Allowed state mutation

Create set/version/lineage record.

## Forbidden state mutation

No member mutation, fitting, materialization, freeze or promotion.

## Failure semantics

Missing/incompatible/duplicate semantic outputs fail explicitly; any membership/version change creates new set.

## Observable consequences

One member-version change changes set identity; historical set resolves exact originals.

## False-success implementations considered

Store friendly names only; auto-upgrade members; sort away meaningful order.

## Falsifying tests

Same names/different versions and order-sensitive model fixture; assert exact identity. **Level A.**

## Mutation-sensitivity check

**Mutation:** Resolve member refs to latest versions.

**Expected failure:** Historical-set test turns red.

## Composite dependencies

feature.define-identity members; system.assemble-definition system; formalization.version-material-change versioning.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added version collision and order-semantics test.

## Remaining user decisions

None.
