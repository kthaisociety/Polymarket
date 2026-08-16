# learning.influence-future-research — permitted validated learning → future ContextPacket and changed behavior

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Prove validated learning—not merely its ID—can influence a later task while respecting scope, currentness, permissions and no hidden side channel.

## Relevant locked invariants

I13–I16, I20, I24; cross-task learning flow and causal-test standard.

## Source A

Two future-task sessions differing only in relevant permitted current validated Memory/Skill content, with same provider/harness and no transcript/store access.

## Destination B

Different reconstructed ContextPackets and next research behavior causally attributable to substantive validated learning; out-of-scope/denied/superseded learning excluded.

## Mapping f

Publish via learning.publish-to-knowledge; retrieve under an issued reader capability; immediately
before projection recompute the exact retrieval against current entries/permissions and hold the
publication lock through observation assembly; assemble episode/context; fresh deterministic
provider reads only packet and chooses action.

## Must preserve

Lesson content/type/scope/caveats/provenance/status, future task relation, permissions and exact identity.

## May transform

Equivalent representation may change where semantic meaning, identity, status and observable behavior survive.

## Must exclude

ID-only context, global injection, stale/denied lesson, provider direct knowledge store, unvalidated lesson, model-weight claim, scripted action.

## Authority boundary

Validated status permits publication; retrieval/context enforce current applicability; model may use but cannot treat as universal authority.

## Allowed state mutation

Retrieval/observation/episode/trajectory only; no automatic state commit.

## Forbidden state mutation

No source/permission/task mutation or hidden model training.

## Failure semantics

Missing/denied/out-of-scope learning yields explicit absence/sentinel. A retrieval invalidated by
supersession, new current results, or permission change hard-fails instead of stale/global fallback.

## Observable consequences

Relevant procedural Skill causes diagnostic-first action while absence causes baseline plan; out-of-scope same Skill does not.

## False-success implementations considered

Expose `lesson_id` only while provider is preprogrammed; inject every memory into system prompt.

## Falsifying tests

Paired fresh sessions, transcript deletion, fail-on-KnowledgeEnvironment access, third sentinel/out-of-scope branch. **Level C.**

## Mutation-sensitivity check

**Mutation:** Drop lesson payload and choose action by presence of ID.

**Expected failure:** Payload-intervention with same ID/status yields wrong/same behavior, test red.

## Composite dependencies

learning.reflect-history–learning.publish-to-knowledge, knowledge.retrieve-evidence/knowledge.return-retrieved-evidence/context.build-packet/model.request-decision.

## Fundamentals review

`CONSISTENT`: implied composite uniquely follows validated-learning architecture.

## Grill findings

Added same-ID/different-content causality, out-of-scope and superseded controls.

## Remaining user decisions

None.
