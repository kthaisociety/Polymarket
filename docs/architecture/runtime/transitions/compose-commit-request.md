# commit.compose-request — ProposeEpisodeTransitionAction → CommitRequest

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Represent the agent's intent to cross a semantic boundary without letting the request itself mutate lifecycle or durable understanding, and without inventing a state delta when the model proposed none.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I8–I10, I13, I17, I25.
- `docs/specification/STATE_CONTEXT_AND_MEMORY.md`, semantic commit boundaries.
- `docs/specification/MILESTONE_1_RUNTIME_DESIGN.md`, semantic commit seam.

## Source A

A current authorized typed transition action naming exact session/episode, expected state/episode versions, target lifecycle status, synthesis, evidence/artifact refs, required episode proposal, optional explicitly present or absent `StateUpdateProposal`, and harness-owned idempotency correlation.

## Destination B

A stable `CommitRequest` containing the exact `EpisodeTransitionProposal`, explicit state-proposal presence/absence, evidence references, base versions, provenance, and canonical semantic payload identity. It carries intent, not validation or authority.

## Mapping f

Validate structural/current routing prerequisites already granted by action.authorize-request; faithfully construct proposals; make absence explicit; bind exact base identities and semantic idempotency payload; emit request and audit event without applying anything.

## Must preserve

Target status, synthesis, exact identities/versions, evidence/artifact refs, proposal presence, authored delta when present, action/call provenance, and idempotency semantics.

## May transform

Typed action fields into proposal/request representation and canonical semantic identity.

## Must exclude

Implicit/default state delta, store handles, validation decisions, forged gate status, hidden task rescope, latest-version substitution, evidence fabrication, lifecycle/state mutation, and normalized-away semantic differences.

## Authority boundary

The model proposes; commit.compose-request packages exact intent. commit.validate-proposals validates episode and state proposals independently; commit.publish-boundary alone commits.

## Allowed state mutation

Append a request-construction trajectory event. No scientific or lifecycle mutation.

## Forbidden state mutation

No episode transition, state version, evidence promotion, task rescope, permission/gate change, or commit result.

## Failure semantics

Malformed/mismatched request construction fails as `INVALID_REQUEST`; structurally illegal lifecycle intent is `INVALID_EPISODE_TRANSITION`; no partial request may be treated as authorized. Exact reconstruction/retry yields the same semantic request identity; changed meaning conflicts downstream.

## Observable consequences

Two actions differing only in explicit state-proposal presence yield different request payloads; the absent case cannot alter state, and neither action changes stores before validation/commit.

## False-success implementations considered

- Generate a default durable summary when resolving an episode.
- Treat rationale/synthesis as a state delta.
- Drop evidence refs or base versions.
- Mutate lifecycle while constructing the request.
- Bind idempotency only to a caller key, not semantic payload.

## Falsifying tests

1. Pair lifecycle-only and combined transition actions. Assert explicit absence versus exact delta and unchanged stores. **Level A/B.**
2. Provide stale/foreign targets, malformed refs, and hidden rescope content; assert structured failure/no effect rather than substitution.
3. Canonicalize exact replay and independently vary status, synthesis, evidence, and proposal presence; assert semantic request identity changes.

## Mutation-sensitivity check

**Mutation:** synthesize a default `StateUpdateProposal` whenever target status is `RESOLVED`.

**Expected failure:** test 1 becomes red because explicit absence is replaced with an unauthorized durable delta.

## Composite dependencies

action.authorize-request authorizes routing; commit.validate-proposals validates; commit.publish-boundary commits atomically; commit.retry-idempotently governs retries; runtime.return-repairable-failure returns repairable rejection.

## Fundamentals review

`CONSISTENT`. It maintains a sharp proposal-versus-authority boundary and protects state/lifecycle separation.

## Grill findings

Resolved non-semantically: required proposal-presence discrimination and semantic payload identity rather than key-only identity.

## Remaining user decisions

None. Canonical serialization and request types remain implementation choices.
