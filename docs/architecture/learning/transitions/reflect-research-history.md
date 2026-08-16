# learning.reflect-history — Trajectory + ResearchLedger outcomes → reflection output

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Synthesize cross-task operational and scientific history without treating history or reflection itself as validated learning.

## Relevant locked invariants

I9, I11–I13, I21–I22; slow cross-task learning.

## Source A

Authority-issued complete bounded trajectory/ledger selection, explicit bounded omissions,
task/outcome/evidence statuses, permissions, reflection protocol/model/config.

## Destination B

Provisional reflection identifying patterns, failures, candidate lessons, uncertainty and source refs, clearly non-authoritative.

## Mapping f

Recompute the issued selection against current repository history; reject stale/incomplete input;
distinguish operations from scientific evidence; synthesize claims with refs/status and expose
contradictions/coverage including bounded omissions.

## Must preserve

Source identities/periods/status, failures/rejections, exposure, uncertainty, scope and provenance.

## May transform

Equivalent representation may change where semantic meaning, identity, status and observable behavior survive.

## Must exclude

History-as-belief, protected leakage, caller-selected winner-only synthesis, stale selection,
source-less lesson, promotion, model-weight update.

## Authority boundary

Reflector interprets; cannot validate/promote. Ledger/trajectory remain sources.

## Allowed state mutation

Reflection artifact/observation/audit.

## Forbidden state mutation

No source/state/memory/skill mutation.

## Failure semantics

Insufficient/conflicting history yields qualified output, not fabricated pattern; denied sources absent.

## Observable consequences

Same successes with different failure ancestry yield different reflections; every claim drills to sources.

## False-success implementations considered

Summarize only winning runs; infer universal rule from one task.

## Falsifying tests

Paired histories differing in failures/status, source-blind consumer/ref audit, denied-source sentinel. **Level C.**

## Mutation-sensitivity check

**Mutation:** Ignore rejected/failed history.

**Expected failure:** Paired reflection claims do not differ, test red.

## Composite dependencies

trajectory.append-event/ledger.preserve-scientific-history; learning.propose-lesson.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added same-success/different-failure causal reflection.

## Remaining user decisions

None.
