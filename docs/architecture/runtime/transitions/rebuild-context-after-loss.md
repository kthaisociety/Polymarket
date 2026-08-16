# context.rebuild-after-loss — state + checkpoint/episode + evidence + permissions → rebuilt equivalent ContextPacket

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Prove scientific behavior survives provider transcript/context loss through durable reconstruction.

## Relevant locked invariants

I9, I13–I16, I20, I24.

## Source A

Exact task/session/current state, active checkpoint/episode, permitted evidence/artifacts, current permissions/environment, fresh provider with no transcript.

## Destination B

Semantically equivalent bounded current ContextPacket and next evidence-dependent behavior.

## Mapping f

Load coherent authoritative versions; apply current permission/status; expand checkpoint plus later evidence; rebuild via context.build-packet; invoke fresh packet-only provider.

## Must preserve

Mission, state/episode distinction, plan/evidence/unresolved work, current/superseded, warnings/permissions, refs/provenance.

## May transform

Equivalent representation may change where semantic meaning, identity, status and observable behavior survive.

## Must exclude

Transcript dependency, stale checkpoint overriding later evidence, unauthorized cached content, whole trajectory, IDs-only context, state mutation.

## Authority boundary

Context builder reads current truth; checkpoint carries no extra authority; provider has packet only.

## Allowed state mutation

Context-build observability only.

## Forbidden state mutation

No state/episode/evidence/permission mutation.

## Failure semantics

Incoherent/missing/unsafe reconstruction fails before provider; no stale packet/transcript fallback.

## Observable consequences

Original and rebuilt packets produce equivalent deterministic action; changed current permission/status changes rebuilt behavior appropriately.

## False-success implementations considered

Use provider history to fill omitted evidence; cache pre-revocation packet.

## Falsifying tests

Destroy all provider/transient context; fresh provider, fail-on-store access, permission revocation and post-checkpoint observation fixtures. **Level C.**

## Mutation-sensitivity check

**Mutation:** Rebuild from checkpoint ID plus hidden provider transcript.

**Expected failure:** Fresh-provider equivalence test red.

## Composite dependencies

context.build-packet/context.checkpoint-episode/artifact.retrieve-authorized-content; later learning.influence-future-research learning context.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added post-checkpoint delta and revoked-permission tests.

## Remaining user decisions

None.
