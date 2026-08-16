# ledger.preserve-scientific-history — formal objects/governance/evidence → append-only ResearchLedger history

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Compose reconstructible scientific identity, ancestry, exposure, evidence and decisions across the protected pipeline.

## Relevant locked invariants

I7, I11–I13, I21–I24.

## Source A

All formal candidates/versions/trials, freeze, requests/permits/denials, exposures, runs, reports, decisions, findings/rejections with exact links.

## Destination B

Append-only scientific history graph that reconstructs why a finding/rejection exists and which evidence was exposed/selected.

## Mapping f

Append locally produced records/edges coherently; enforce immutable identity and required ancestry; preserve negative outcomes.

## Must preserve

Every formal identity/version, data periods/environment, protocols, trial ancestry, governance authority, exposure, evidence/status, correction links.

## May transform

Equivalent representation may change where exact scientific meaning, identity and behavior survive.

## Must exclude

Trajectory-as-ledger, winner-only graph, mutable rewrite/delete, orphan promotion, hidden exposure, evaluation as training/memory.

## Authority boundary

Formal pipeline writes; no actor rewrites. Ledger informs gates but does not grant authority alone.

## Allowed state mutation

Append records/links/indexes.

## Forbidden state mutation

No source object mutation, automatic promotion/learning.

## Failure semantics

Missing required ledger edge blocks claims relying on it; correction appends explicit supersession.

## Observable consequences

From finding traverse exact candidate→freeze→permit→run→report→decision plus all trials/exposures/rejections.

## False-success implementations considered

Store disconnected IDs; delete rejected branches; infer lineage by names.

## Falsifying tests

Build complex graph with failure/revision/exposure and assert complete traversal after reload; mutation/delete impossible. **Level B.**

## Mutation-sensitivity check

**Mutation:** Persist only final successful chain and omit losing trials/exposures.

**Expected failure:** Graph completeness test red.

## Composite dependencies

ledger.record-trial-lineage–ledger.record-negative-result; learning.reflect-history reflection.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added graph connectivity not mere endpoint existence.

## Remaining user decisions

None.
