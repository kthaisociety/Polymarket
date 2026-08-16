# commit.publish-boundary — validated proposals + current stores → atomic CommitResult

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Publish one semantic boundary coherently so lifecycle and durable understanding cannot enter a scientifically impossible half-state.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I9–I13, I17, I25.
- `docs/specification/STATE_CONTEXT_AND_MEMORY.md`, semantic commit boundaries.
- `docs/specification/MILESTONE_1_RUNTIME_DESIGN.md`, atomic semantic commit.

## Source A

The original exact `CommitRequest`, every applicable accepting validation decision, and exact current episode/state/store versions at commit time.

## Destination B

An authoritative `CommitResult` correlated to the request, with atomically published episode transition and, only when explicitly proposed/validated, one new state version with lineage/evidence; plus coherent commit/trajectory records.

## Mapping f

Recheck decision/request/current-version correspondence; stage replacement episode, state, commit,
and trajectory tables; publish them behind one store lock with exact rollback to every prior table
reference on a mid-publication exception; return success only after all records are coherently
reloadable. This is the in-process adapter; crash-durable storage must supply an equivalent
transaction.

## Must preserve

Request/key/payload identity, proposal presence, target lifecycle, exact state delta, evidence/provenance, prior-state lineage, result identity, and all-or-nothing relation.

## May transform

Accepted proposals into durable episode/state representations and one result envelope; transaction technology is free.

## Must exclude

Unvalidated/implicit mutation, partial success, history rewrite, second state version, payload alteration, stale acceptance, duplicate effect, task rescope, or success before required audit/provenance exists.

## Authority boundary

Validators authorize propositions; the coordinator may only apply exactly those decisions. Stores persist but cannot expand semantics. The agent/provider cannot write directly.

## Allowed state mutation

Atomically transition exact episode, optionally create one state version, and append coherent commit/trajectory records.

## Forbidden state mutation

No task/environment/evidence rewrite, extra state delta, unrelated episode mutation, or any write when an applicable validation/currentness check fails.

## Failure semantics

Validation mismatch, concurrency/version conflict, or persistence failure commits none of the required proposal effects and publishes no healthy success. Lifecycle-only success leaves state exactly unchanged. Retry delegates to commit.retry-idempotently semantics.

## Observable consequences

Reload after success shows a coherent terminal episode and exactly one optional state successor sharing the commit identity. Fault injection after each underlying write leaves the pre-request records authoritative.

## False-success implementations considered

- Write episode first, then fail state.
- Publish success before audit/provenance.
- Apply a default state change on lifecycle-only commit.
- Revalidate loosely against latest versions.
- Compensate a partial write by rewriting immutable history.

## Falsifying tests

1. Inject failure after every potential underlying write of a combined request; assert active episode, old state, no success, and coherent retry. **Level B.**
2. Commit lifecycle-only and assert exact state identity/content/version unchanged.
3. Swap validation decision/request/current versions and assert rejection/no writes.
4. Successful combined commit reloads exact episode/state/evidence/result correlation and one new version only.

## Mutation-sensitivity check

**Mutation:** persist episode transition before state creation without atomic staging.

**Expected failure:** test 1 becomes red when fault injection exposes a terminal episode with old state.

## Composite dependencies

commit.compose-request/commit.validate-proposals supply proposals/decisions; commit.retry-idempotently governs uncertain replay; runtime.return-repairable-failure reports repairable failure; trajectory.append-event records trace; runtime.run-bounded-episode composes acceptance.

## Fundamentals review

`CONSISTENT`. Atomic publication and explicit absence protect state/lifecycle meaning without prescribing transaction internals.

## Grill findings

Resolved non-semantically: success now requires coherent audit/provenance visibility, while rollback mechanism remains free.

## Remaining user decisions

None. Physical transaction/storage mechanism remains deferred.
