# artifact.persist-analysis-output — exploratory output → ArtifactStore identity/ref

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Retain large exploratory tables, plots, code, and temporary models without promoting them into formal scientific objects.

## Relevant locked invariants

I11, I13, I15, I18, I24; storage/progressive-disclosure rules.

## Source A

Permitted output bytes/object plus execution/code/data/environment provenance, content type, sensitivity, temporary/provisional status.

## Destination B

Immutable artifact/ref with integrity, lineage, classification, producer identity, and authorized retrieval metadata.

## Mapping f

Persist exact output immutably; bind sandbox.record-provenance provenance/status; publish ref after retrievability; retain provisional type.

## Must preserve

Content/integrity/type/shape, execution/code/data/environment IDs, temporary status, sensitivity, created time.

## May transform

Equivalent representation, bounded summarization, and implementation-specific types may change where semantic meaning survives.

## Must exclude

Formal Feature/Model identity, validation/promotion, overwrite, dangling ref, unauthorized preview, state mutation.

## Authority boundary

Artifact store retains; formalization seams separately create scientific identities; ref possession is not read permission.

## Allowed state mutation

Create immutable artifact/ref/audit.

## Forbidden state mutation

No prior overwrite, formal candidate/gate/state creation.

## Failure semantics

Persistence/provenance failure returns no healthy ref; changed content cannot reuse identity silently.

## Observable consequences

Temporary model artifact remains drillable and explicitly non-formal; exact round-trip works.

## False-success implementations considered

Treat pickled model as ModelDefinition; mutable path ref; store preview only.

## Falsifying tests

Persist table/plot/code/temp-model; exact round-trip/integrity/provenance and provisional status. Attempt overwrite and formal-use without formalization.create-candidate/model.define-recipe; reject. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Infer formal ModelDefinition from artifact type.

**Expected failure:** No-promotion test becomes red because a formal object appears.

## Composite dependencies

artifact.persist-output/artifact.retrieve-authorized-content generic artifact rules; formalization.create-candidate/model.define-recipe formalization.

## Fundamentals review

`CONSISTENT`: retains creativity outputs without epistemic promotion.

## Grill findings

Added artifact-type-versus-formal-identity attack.

## Remaining user decisions

None.
