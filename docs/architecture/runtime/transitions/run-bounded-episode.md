# runtime.run-bounded-episode — initialized session → terminal EpisodeRunResult under limits

## Status

`CANDIDATE_CONSENSUS` — experimental composite contract, not canonical.

## Architectural purpose

Compose the Milestone 1 organism so autonomous turns, causal feedback, repair, authority, state separation, commit atomicity, audit, and configured bounds hold end to end.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I8–I18, I20, I24–I25 as exercised by M1.
- `docs/specification/MILESTONE_1_RUNTIME_DESIGN.md`, whole-episode seam and acceptance scenario.
- Canonical mission.confirm-task–action.decode-intent and candidate action.authorize-request–artifact.retrieve-authorized-content responsibilities.

## Source A

A coherent initialized active session, replaceable scripted/model provider, registered actions/capabilities, current policies/stores, and explicit action/turn/time/resource limits.

## Destination B

An `EpisodeRunResult` that truthfully reports terminal lifecycle or explicit bounded stop/failure, final exact episode/state identities, turn/action/resource counts, last observation/result, and trajectory/artifact/commit correlations.

## Mapping f

Repeatedly reconstruct current context, request one intent, decode, authorize, execute or validate/commit, assemble/persist observation, and continue from authoritative state until a valid terminal transition, unrecoverable failure, or configured limit. Never use provider transcript as state or bypass a seam for convenience.

## Must preserve

Exact session/task/environment identity; current episode/state versions; action/observation/commit order; observation-driven behavior; provider neutrality; permissions; failure/recovery class; audit/artifact refs; and limits/outcome reason.

## May transform

Local seam results into turn/run summaries. Loop scheduling and internal orchestration are free within serial M1 consequence semantics.

## Must exclude

Scripted next actions independent of context when claiming feedback, hidden store/data access by provider, direct tool-to-state mutation, unauthorized execution, auto-repair changing meaning, half commits, unbounded looping, swallowed failures, and claims of M2 temporal legality.

## Authority boundary

The harness orchestrates but inherits each seam's authority; orchestration grants no extra authority. The model proposes, capabilities compute, validators authorize, coordinator commits.

## Allowed state mutation

Only mutations authorized by participating seams: episode evidence, trajectory/artifacts, and validated atomic lifecycle/state commits.

## Forbidden state mutation

No bypass mutation, cross-session effect, unrecorded protected access, or update after terminal state. Limits cannot be disabled by model requests.

## Failure semantics

Repairable failures re-enter the active loop through runtime.return-repairable-failure; governance denial remains denial; unrecoverable failure or configured bound yields explicit non-success run result with coherent stores. Terminal episode cannot transition again. Uncertain commit acknowledgement resolves through commit.retry-idempotently.

## Observable consequences

The three-turn M1 scenario inspects, uses observation meaning in the next packet, proposes an evidence-backed transition, commits atomically, and returns terminal result. Idempotency and repair companions pass; state remains version 0 until valid commit.

## False-success implementations considered

- Queue scripted responses by turn count.
- Pass dataset/episode store to provider.
- Update state immediately from inspection.
- Mark terminal after persuasive finish text.
- Ignore action/time/resource limits.
- Return success after partial audit/artifact/commit failure.

## Falsifying tests

1. Full M1 acceptance scenario with a deterministic context-sensitive provider and fail-on-side-channel dependencies. **Level C.**
2. Paired 18-versus-2 sessions produce different second actions solely from rebuilt context; transcript is destroyed.
3. Invalid evidence repair companion remains active/unchanged, returns failure observation, then succeeds with corrected new request.
4. Lost commit acknowledgement/replay yields one effect; changed payload conflicts.
5. Independently exhaust turn/action/time/resource limits and assert explicit bounded result/no extra effect. **Level B.**

## Mutation-sensitivity check

**Mutation:** choose the provider's second response from a preloaded queue rather than reconstructed observation content.

**Expected failure:** paired Level C test becomes red because identical scripted second responses cannot produce 18-versus-2 outcomes and the sentinel branch exposes missing causality.

## Composite dependencies

Participating seams are runtime.initialize-research–artifact.retrieve-authorized-content. No new production object is required beyond the existing run result/orchestrator contract; the seam tests composition.

## Fundamentals review

`CONSISTENT`. It proves the organism without collapsing local authority or claiming autonomous reasoning from a context-ignoring script.

## Grill findings

Resolved non-semantically: required independent limit attacks, transcript destruction, fail-on-side-channel provider, repair, and uncertain-acknowledgement companions.

## Remaining user decisions

None. Production limit values and orchestration class structure remain deferred implementation/configuration choices.
