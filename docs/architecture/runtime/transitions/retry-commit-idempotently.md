# commit.retry-idempotently — repeated idempotent CommitRequest → original result or IDEMPOTENCY_CONFLICT

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Make uncertain commit acknowledgement safe without letting a reused key overwrite or duplicate a scientifically meaningful transition.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I11, I25.
- `docs/specification/MILESTONE_1_RUNTIME_DESIGN.md`, idempotency companion.

## Source A

A `CommitRequest` carrying stable harness-recognized idempotency identity and canonical semantic payload, evaluated against a logical durable idempotency/result store.

## Destination B

First-use commit result, the exact original result for exact semantic replay, or `IDEMPOTENCY_CONFLICT` for key reuse with changed meaning.

## Mapping f

Atomically claim key with canonical semantic identity; on first use perform commit.validate-proposals/commit.publish-boundary and store outcome; on exact replay return stored outcome without reapplication; on semantic difference reject and preserve original.

## Must preserve

Key, full semantic payload identity, original result/versions/evidence/provenance, first outcome including failures where policy defines, and exactly-once irreversible effects.

## May transform

Semantic request into canonical comparison/digest representation; representation-only differences may normalize only when meaning is unchanged.

## Must exclude

Key-only comparison, partial field comparison, overwrite, duplicate state/episode/commit events, changed payload accepted as replay, process-memory-only correctness, and model-authored authoritative key substitution.

## Authority boundary

Harness/store owns idempotency identity and comparison. Replay cannot grant new validation or execution authority.

## Allowed state mutation

First use may perform one commit.publish-boundary commit and persist idempotency/result record. Conflict may append rejection observability.

## Forbidden state mutation

Exact replay and conflict cannot reapply, alter, or delete the original result or scientific effects.

## Failure semantics

Exact replay after coordinator reconstruction returns original. Independently changing target status, synthesis, state-proposal presence/delta, evidence set, base versions, or identities conflicts. Concurrent first uses converge. Uncertain internal failure cannot be guessed as success; recovery consults durable outcome.

## Observable consequences

Lost acknowledgement followed by retry returns the same result and counts. Changed requests under the same key conflict, with original stores unchanged.

## False-success implementations considered

- Deduplicate only in process memory.
- Compare only key or target episode.
- Recompute and recommit on replay.
- Treat reordered/differently serialized same semantics as conflict.
- Overwrite the stored payload/result on conflict.

## Falsifying tests

1. Commit, lose acknowledgement, reconstruct coordinator over same stores, replay, and assert exact original result/one effect. **Level B.**
2. Change each semantic dimension separately under same key; assert conflict and original preservation.
3. Concurrent exact first uses converge on one result/effect.
4. Equivalent representation with identical semantics replays, while meaning-changing representation conflicts.

## Mutation-sensitivity check

**Mutation:** compare only the idempotency key.

**Expected failure:** test 2 becomes red because changed status/delta/evidence is incorrectly returned as exact replay.

## Composite dependencies

commit.compose-request defines semantic payload; commit.validate-proposals/commit.publish-boundary validate/commit; trajectory.append-event records retry/conflict; runtime.run-bounded-episode exercises uncertain acknowledgement.

## Fundamentals review

`CONSISTENT`. Semantic idempotency protects irreversible state while leaving canonicalization mechanics free.

## Grill findings

Resolved non-semantically: added concurrent first-use and representation-versus-meaning cases to avoid key-only or byte-only false success.

## Remaining user decisions

None. Which non-success outcomes are durably replayed may follow the existing failure contract; no new semantic choice is needed for successful-commit idempotency.
