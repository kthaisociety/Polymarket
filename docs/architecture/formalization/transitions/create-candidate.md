# formalization.create-candidate — hypothesis/exploratory idea + evidence → candidate feature/model

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Make scientific candidacy explicit, versioned, and ancestry-bearing rather than promoting an interpretation or artifact implicitly.

## Relevant locked invariants

I5, I9, I12–I13, I24; exploration/formalization gradient.

## Source A

Hypothesis/idea, supporting and contrary exploratory evidence, exact task/episode/environment, proposed candidate kind/scope/rationale.

## Destination B

A provisional candidate record with identity, kind, hypothesis, ancestry, evidence refs/status, assumptions, unresolved formalization work; not yet FeatureDefinition/ModelDefinition.

## Mapping f

Validate provenance and goal relation; create candidate with trial ancestry; preserve contradictory/rejected evidence and provisional status.

## Must preserve

Hypothesis meaning, evidence status/provenance, task/environment, assumptions, ancestry.

## May transform

Equivalent representation may change where semantic identity and behavior survive.

## Must exclude

Implicit formal object, artifact-as-model, evidence deletion, validation/freeze status, task drift, protected-evidence reuse.

## Authority boundary

Agent proposes; harness records candidate identity/ancestry; formalization gates later validate definitions.

## Allowed state mutation

Create candidate/lineage/ledger trial record.

## Forbidden state mutation

No formal definition, fitted state, gate, promotion, state rewrite.

## Failure semantics

Missing provenance or ambiguous candidate kind/scope yields explicit incomplete candidate or no publication; never infer a formal recipe.

## Observable consequences

Two identical hypotheses with different evidence ancestry remain distinguishable; exploratory artifact alone cannot become formal.

## False-success implementations considered

Create formal feature from a correlation scalar; omit failed trials.

## Falsifying tests

Pair same hypothesis with different evidence ancestry; assert distinct provenance and provisional status. Try artifact-only promotion; reject. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Treat any temporary model artifact as a formal model candidate with no ancestry.

**Expected failure:** Candidate/formal-status assertions turn red.

## Composite dependencies

observation.assemble-analysis-result/artifact.persist-analysis-output inputs; feature.define-identity/model.define-recipe formalize; ledger.record-trial-lineage ledger.

## Fundamentals review

`CONSISTENT`: implied candidate mapping uniquely follows the promotion funnel.

## Grill findings

Added contrary-evidence retention and artifact-versus-candidate attack.

## Remaining user decisions

None.
