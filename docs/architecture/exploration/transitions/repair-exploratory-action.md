# research.repair-exploratory-action — ordinary exploratory failure → repaired action in same episode

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Continue exploration after operational failure only when repair preserves scientific meaning and state remains uncorrupted.

## Relevant locked invariants

I9, I12, I17–I18, I25; exploratory failure rules.

## Source A

Failed structured observation in active episode, original action/code, diagnostics/provenance, exact current identities, and model-proposed repaired action.

## Destination B

Authorized new action in same episode or explicit branch/block decision, with ancestry to failure and no erased history.

## Mapping f

Feed failure through context; agent proposes repair; action.authorize-request/sandbox.authorize-execution reauthorize new request; compare intent/meaning where relevant; execute as new action identity while retaining ancestry.

## Must preserve

Original failure/action/code, repair rationale/difference, episode/task goal, evidence status, provenance, attempt identities.

## May transform

Equivalent representation, bounded summarization, and implementation-specific types may change where semantic meaning survives.

## Must exclude

Silent auto-repair, reuse old authority/idempotency, state rollback corruption, erased failure, governance denial treated as operational, meaning-changing formal repair on same candidate.

## Authority boundary

Agent proposes; harness reauthorizes. In exploration, changed code is a new action; formal meaning changes later require new version.

## Allowed state mutation

New action/observation/artifact/trajectory entries in same active episode.

## Forbidden state mutation

No state commit, history deletion, permission widening, false success.

## Failure semantics

Unrepairable/governance or limit failure remains explicit. Failed repair loops remain bounded and recorded.

## Observable consequences

Missing-column failure leads through context to corrected-column action; state unchanged and both attempts retained.

## False-success implementations considered

Capability retries internally with guessed column; overwrite failed event; reuse grant after request change.

## Falsifying tests

Deterministic provider repairs only from failure observation; assert new action identity/authorization, both attempts, same episode, unchanged state. Governance denial does not auto-repair. **Level C.**

## Mutation-sensitivity check

**Mutation:** Capability silently substitutes nearest column and returns success.

**Expected failure:** Expected failure observation/repair ancestry is absent, making test red.

## Composite dependencies

runtime.return-repairable-failure/observation.translate-analysis-failure/action.authorize-request/sandbox.authorize-execution/sandbox.execute-analysis; research.continue-from-exploration.

## Fundamentals review

`CONSISTENT`: exploration can recover without scientific falsification or authority bypass.

## Grill findings

Added new authorization/identity and governance distinction.

## Remaining user decisions

None.
