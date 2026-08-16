# learning.propose-lesson — reflection output → CandidateLesson

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Turn a provisional reflection into an explicit scoped knowledge/procedure proposal with evidence, rather than silently writing memory.

## Relevant locked invariants

I8–I9, I13, I22, I24; slow learning flow.

## Source A

Reflection, exact supporting/contrary evidence periods/tasks, proposed lesson content/type/scope/applicability/caveats, requester/provenance.

## Destination B

Immutable provenance-bearing CandidateLesson classified as knowledge (`Memory`) or procedure (`Skill`) candidate, with scope, evidence and unresolved risks; non-validated.

## Mapping f

Validate traceability/completeness; classify every selected evidence item; separate knowledge from
procedure; require proposed applicability to be a subset of reflection evidence scope; publish candidate.

## Must preserve

Lesson meaning/type/scope, supporting/contrary evidence, periods/tasks/environments, caveats, reflection/provenance.

## May transform

Equivalent representation may change where semantic meaning, identity, status and observable behavior survive.

## Must exclude

Automatic memory, universal scope, source-less advice, protected contamination, self-validation, knowledge/procedure conflation.

## Authority boundary

Agent proposes; harness records; learning.validate-lesson independently validates.

## Allowed state mutation

Candidate lesson/lineage/ledger record.

## Forbidden state mutation

No Memory/Skill/KnowledgeEnvironment publication or behavior change.

## Failure semantics

Missing evidence/scope/type or conflicting unresolved claim blocks complete candidate; no broad default scope.

## Observable consequences

Two lessons with same text but different evidence/scope remain distinct and unvalidated.

## False-success implementations considered

Write reflection directly to prompt memory; label procedure as fact.

## Falsifying tests

Omit source/scope/type in turn; require no valid candidate. Same text/different evidence identity. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Persist reflection text directly as validated memory.

**Expected failure:** Status/store test red.

## Composite dependencies

learning.reflect-history; learning.validate-lesson.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added knowledge-versus-procedure and contrary-evidence requirements.

## Remaining user decisions

None.
