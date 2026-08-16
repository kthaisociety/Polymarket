# context.checkpoint-episode — active ResearchEpisode under pressure → EpisodeCheckpoint

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Preserve the investigation in structured reconstructible form without treating generic conversation summary as state or deleting evidence.

## Relevant locked invariants

I9, I13–I16, I24; compaction section.

## Source A

Exact active episode, plan/checks/observations/temporary interpretations/unresolved questions/refs/warnings/permissions and pressure/bound.

## Destination B

Immutable/versioned EpisodeCheckpoint tied to episode/base state/environment, preserving required semantics/status and references.

## Mapping f

Validate coherent view; structurally encode objective, plan, completed checks, key evidence, temporary beliefs, unresolved work, refs, warnings/permissions; publish before dropping transient clutter.

## Must preserve

All decision-relevant semantics, epistemic roles, order/status, identities, refs/provenance and authority.

## May transform

Equivalent representation may change where semantic meaning, identity, status and observable behavior survive.

## Must exclude

Generic prose summary, state promotion, evidence deletion, stale/current flattening, unauthorized content, checkpoint as transcript.

## Authority boundary

Harness checkpoint boundary preserves; cannot commit belief or alter permissions.

## Allowed state mutation

Append checkpoint/version/audit; later episode may point to current checkpoint.

## Forbidden state mutation

No underlying trajectory/evidence/artifact deletion or state/lifecycle mutation.

## Failure semantics

If required meaning cannot fit/persist, fail compaction and retain prior context; no destructive partial checkpoint.

## Observable consequences

After transcript deletion, unresolved plan/evidence/status reconstructs; raw stores remain accessible.

## False-success implementations considered

Summarize chat and discard artifacts; retain IDs only; merge temporary into committed.

## Falsifying tests

Paired checkpoints differing in one unresolved/evidence status lead to different rebuilt action; integrity and no-delete assertions. **Level C.**

## Mutation-sensitivity check

**Mutation:** Drop substantive observation payload while retaining ref ID.

**Expected failure:** Rebuilt consumer takes missing-evidence branch, test red.

## Composite dependencies

context.build-packet/artifact.persist-output/artifact.retrieve-authorized-content; context.rebuild-after-loss composite.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added publish-before-discard and epistemic-role paired test.

## Remaining user decisions

None.
