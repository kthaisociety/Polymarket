# learning.promote-lesson — promoting lesson decision → validated Memory or Skill

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Change epistemic status while preserving exact scope, provenance and knowledge-versus-procedure distinction.

## Relevant locked invariants

I5, I11, I13, I24; Memory/Skill glossary.

## Source A

Exact PROMOTE decision and CandidateLesson, canonical evidence/caveats/scope/type, environment/version lineage.

## Destination B

Immutable validated Memory or Skill with exact content, applicability, provenance, decision/status and lineage.

## Mapping f

Verify decision/candidate correspondence; consume each decision for exactly one effect; require an
explicit same-kind, non-broadening parent-candidate lineage and a single successor when superseding;
create the type-appropriate object and seal immutably.

## Must preserve

Lesson meaning/type/scope/applicability, evidence periods/tasks, caveats, provenance, decision/authority/version.

## May transform

Equivalent representation may change where semantic meaning, identity, status and observable behavior survive.

## Must exclude

Memory↔Skill conversion, universal authority, omitted caveat, mutable overwrite, behavior injection before learning.publish-to-knowledge, source rewrite.

## Authority boundary

Promotion decision authorizes status only; publisher cannot broaden. KnowledgeEnvironment publication is learning.publish-to-knowledge.

## Allowed state mutation

Create validated object/ledger record.

## Forbidden state mutation

No source/decision mutation, context insertion, model-weight update.

## Failure semantics

Mismatch/unsupported content, reused decision, competing successor, broadened scope, or missing
caveat blocks publication; correction/new meaning creates one explicit new version.

## Observable consequences

Procedure candidate becomes Skill and factual candidate Memory; exact scope/caveats survive.

## False-success implementations considered

Turn any promoted lesson into universal system prompt; drop caveats.

## Falsifying tests

Type-paired candidates, scope/caveat preservation, mutation/version tests. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Publish both types as undifferentiated prompt text.

**Expected failure:** Type/status test red.

## Composite dependencies

learning.validate-lesson; learning.publish-to-knowledge.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added publication-versus-validation separation.

## Remaining user decisions

None.
