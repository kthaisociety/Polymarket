# formalization.version-material-change — material formal-object change → new version/candidate with lineage

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Prevent in-place mutation or disguised experiment changes while allowing representation-only edits that preserve meaning.

## Relevant locked invariants

I5, I11–I13, I24.

## Source A

Existing immutable feature/model/system definition plus proposed change, exact base version, change rationale/provenance, semantic comparison.

## Destination B

Same identity for provably representation-equivalent change, or immutable new version/candidate with parent lineage and explicit semantic diff; conflict/rejection otherwise.

## Mapping f

Compare scientific semantics; validate exact base; classify materiality using locked identity dimensions; publish new object without rewriting parent.

## Must preserve

Parent content/identity, exact diff, ancestry, prior evidence/trials/exposure, environment/provenance.

## May transform

Equivalent representation may change where semantic identity and behavior survive.

## Must exclude

In-place edit, latest-base substitution, history/evidence rebinding, cosmetic byte differences forced into meaning, material change hidden as metadata.

## Authority boundary

Agent proposes; harness enforces immutable versioning. Prior exposure/evidence status follows lineage rules.

## Allowed state mutation

Create new version/lineage or append rejected-change record.

## Forbidden state mutation

No parent/history rewrite, automatic evidence freshness, fit/backtest/promotion.

## Failure semantics

Stale base or ambiguous materiality blocks publication; genuine semantic alternative requiring architecture is user decision, not heuristic.

## Observable consequences

Material change produces new ID/parent; representation-only reorder preserves meaning; old evidence remains attached to old version.

## False-success implementations considered

Mutate object in place; compare only display name; drop exposure ancestry.

## Falsifying tests

Change lag, field, missingness, model, protocol and assert new versions; reorder serialization and assert semantic equivalence; old refs unchanged. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Mutate frozen/component object in place while retaining ID.

**Expected failure:** Historical reload/diff tests turn red.

## Composite dependencies

All formal definitions; freeze.seal-system frozen; ledger.record-trial-lineage/ledger.preserve-scientific-history history.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added representation-versus-semantics pair and evidence-lineage guard.

## Remaining user decisions

None.
