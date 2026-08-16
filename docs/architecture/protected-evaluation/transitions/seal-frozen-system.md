# freeze.seal-system — accepted freeze request/candidate → FrozenPredictiveSystemDefinition

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Seal complete scientific identity immutably so protected evaluation cannot drift.

## Relevant locked invariants

I4–I5, I8, I11, I13, I24.

## Source A

Accepted exact freeze request/decision, complete PredictiveSystemDefinition, component/protocol versions, lineage/provenance.

## Destination B

Immutable FrozenPredictiveSystemDefinition with exact complete semantic identity, freeze decision/time/authority and ancestry.

## Mapping f

Revalidate request/candidate correspondence and completeness; resolve exact components; seal immutable snapshot/identity atomically.

## Must preserve

All target/features/models/ensemble/training/evaluation/fallback/environment identities, lineage, decision/provenance.

## May transform

Equivalent representation may change where exact scientific meaning, identity and behavior survive.

## Must exclude

Mutable refs/latest lookup, omitted protocol, fitted state substitution, self-freeze, partial seal, in-place edits.

## Authority boundary

Independent accepted decision authorizes; freezer seals only exact candidate.

## Allowed state mutation

Create frozen object/freeze ledger record.

## Forbidden state mutation

No component mutation, fit/backtest/exposure/promotion.

## Failure semantics

Any mismatch/staleness/incompleteness rejects; publication coherent-or-nothing. Material change requires new candidate.

## Observable consequences

Later component version cannot change frozen reconstruction; mutation attempt fails.

## False-success implementations considered

Store pointers resolved to latest; freeze only display ID; edit frozen object.

## Falsifying tests

Publish newer components, reload old frozen semantics; mutate each material dimension and require new candidate. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Resolve frozen component refs dynamically to latest.

**Expected failure:** Historical freeze test red.

## Composite dependencies

system.assemble-definition/formalization.version-material-change/freeze.assess-eligibility; backtest.request-evaluation/backtest.execute-scenario.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added deep snapshot completeness and partial-publication attack.

## Remaining user decisions

None.
