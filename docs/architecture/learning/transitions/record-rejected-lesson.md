# ledger.record-rejected-lesson — rejected lesson decision → append-only ResearchLedger record

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Preserve rejected learning and evidence so failed lessons are not erased or repeatedly rediscovered as fresh.

## Relevant locked invariants

I11–I13; rejected evidence remains history.

## Source A

Exact REJECT decision, CandidateLesson, evidence/standard/reasons/authority/provenance.

## Destination B

Immutable rejection ledger record linked to lesson/reflection/evidence and future superseding proposals.

## Mapping f

Append complete rejection/status/reasons and ancestry; retain candidate; expose safe retrieval metadata.

## Must preserve

Lesson/type/scope, evidence, standard, reasons, decision/authority, environment/time.

## May transform

Equivalent representation may change where semantic meaning, identity, status and observable behavior survive.

## Must exclude

Deletion, silent discard, validated status, source rewrite, automatic memory, sensitive leakage.

## Authority boundary

Ledger preserves; rejector cannot erase; later new lesson has explicit lineage.

## Allowed state mutation

Append rejection/links/audit.

## Forbidden state mutation

No Memory/Skill/KnowledgeEnvironment publication or source mutation.

## Failure semantics

Audit failure prevents acknowledged durable rejection; correction/supersession appends.

## Observable consequences

Rejected lesson remains discoverable and future similar proposal references it without becoming blocked automatically.

## False-success implementations considered

Delete rejected candidate; store only reason string.

## Falsifying tests

Reload full rejection ancestry and attempt deletion; future revised candidate retains parent. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Persist only promoted lessons.

**Expected failure:** Rejected-history count/traversal red.

## Composite dependencies

learning.validate-lesson; learning.reflect-history future reflection.

## Fundamentals review

`CONSISTENT` (MEDIUM).

## Grill findings

Added future-lineage without making rejection universal prohibition.

## Remaining user decisions

None.
