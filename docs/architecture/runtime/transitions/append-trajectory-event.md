# trajectory.append-event — consequential runtime operations/rejections → append-only Trajectory events

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Preserve ordered audit/replay history of what the runtime attempted, authorized, executed, observed, rejected, validated, and committed without treating event history as current belief.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I9, I11–I13, I25.
- `docs/specification/STATE_CONTEXT_AND_MEMORY.md`, Trajectory versus episode/state.
- M1 audit requirements.

## Source A

Harness-observed consequential operation boundaries and outcomes with exact session/episode/call/action/authorization/execution/observation/request/commit identities, status, order, provenance refs, and bounded safe metadata.

## Destination B

Immutable ordered `Trajectory` events sufficient to reconstruct the operational sequence and correlate attempts, rejections, retries, observations, and commits.

## Mapping f

At each required runtime boundary, append a correlated event derived from harness facts; preserve causal/order links and failure status; make retry versus new operation explicit; never derive belief or authority from event presence.

## Must preserve

Actor and operation identity, exact session/episode, order, attempt/logical identity, request/result status, authorization decision, provenance/artifact refs, retry/conflict correlation, and rejection/failure history.

## May transform

Runtime facts into stable event vocabulary and safe bounded metadata; event physical format/store is free.

## Must exclude

Success-only history, mutable/deletable failures, events as `ResearcherState`, whole trajectory injected by default into context, secrets/protected values, self-reported provenance replacing harness facts, and duplicate scientific effect inferred from duplicate attempts.

## Authority boundary

Harness emits events. Trajectory store appends; it cannot authorize, execute, promote, mutate scientific state, or become the canonical evidence ledger.

## Allowed state mutation

Append immutable trajectory events and indexes/correlation metadata.

## Forbidden state mutation

No event update/delete, episode/state/task/evidence/exposure mutation, permission grant, or requested operation effect.

## Failure semantics

A consequential operation whose audit event is required is not fully acknowledged as healthy unless operation and event correlation are coherent. Audit failure cannot be hidden as success; recovery must not duplicate the underlying effect. Exact attempt duplicates remain distinguishable from one logical effect.

## Observable consequences

Successful inspection, rejected foreign action, repair attempt, and commit reload as one ordered correlated trace; the rejected action remains visible while current state/episode must be loaded from their own stores.

## False-success implementations considered

- Record only successes.
- Update one “latest event” row.
- Treat trajectory replay as current state.
- Lose logical-call versus attempt identity.
- Let provider/capability author authoritative events.

## Falsifying tests

1. Run success, rejection, retry, observation, and commit; reload ordered trace and assert exact correlation/status including rejection. **Level B.**
2. Attempt update/delete and assert append-only preservation.
3. Build context with fail-on-trajectory-full-read and assert state/episode sources remain authoritative.
4. Lost acknowledgement/retry yields multiple attempts but one correlated logical effect.

## Mutation-sensitivity check

**Mutation:** append events only for successful operations.

**Expected failure:** test 1 becomes red because the foreign-action rejection and failed attempt disappear.

## Composite dependencies

All M1 operational seams emit; artifact.persist-output holds large detail; learning.reflect-history later reflects over trajectory plus ledger. Trajectory is not ResearchLedger.

## Fundamentals review

`CONSISTENT`. It retains failure history and provenance while keeping operational history distinct from belief and scientific evidence authority.

## Grill findings

Resolved non-semantically: added coherent acknowledgement and attempt-versus-effect correlation without prescribing distributed transactions.

## Remaining user decisions

None. Exact event taxonomy and storage are implementation choices.
