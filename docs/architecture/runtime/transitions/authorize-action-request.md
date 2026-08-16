# action.authorize-request — typed AgentAction + current runtime authority → authorization/routing decision

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Turn a structurally valid but untrusted request into an explicit current authorization and route without executing it. action.decode-intent proves shape; action.authorize-request proves that the claimed session, episode, action kind, and requested authority are valid now.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I8, I14, I18, I25.
- `docs/specification/DECISIONS.md`, AI authority and Action/tool space.
- Canonical action.decode-intent contract: a typed action is not permission.

## Source A

A typed `AgentAction` with harness-owned action/replay identity, originating call/schema identity, model-authored arguments and target claims, plus the exact current session, active episode, environment, permissions, capability policy, and lifecycle state.

## Destination B

An explicit decision that either binds the unchanged request to one authorized capability/governed-transition route and least-authority execution context, or denies/rejects it with safe reason, correlation, and recoverability.

## Mapping f

Validate harness identity and replay correlation; compare claimed targets to exact current records; require an active/current lifecycle; determine whether the advertised action kind has a route; evaluate current policy and concrete prerequisites; emit `AUTHORIZED(route, context)` or a typed denial. Do not execute, repair, retarget, or reinterpret the request.

## Must preserve

- exact action, logical-call, schema, session, episode, and replay identities;
- model-authored kind, targets, arguments, code/text, and bounds;
- distinction among malformed/unsupported, stale identity, governance denial, and operational unavailability;
- policy/environment version and reasons governing the decision.

## May transform

- trusted current records into a bounded authorization context;
- action kind into a registered route identifier;
- denial facts into safe structured failure vocabulary.

## Must exclude

- latest-session/episode substitution; argument rewriting; unknown-action fallback; capability execution; data reads; state/episode mutation; provider-native objects; permissions inferred from a visible schema; authorization granted by the requesting model or beneficiary.

## Authority boundary

The model requests. action.decode-intent types. The harness-owned action.authorize-request policy boundary alone authorizes and routes against current truth. Capabilities and commit coordinators execute later and cannot broaden the decision.

## Allowed state mutation

Append a bounded authorization/rejection trajectory event and reserve a decision identity. No scientific mutation.

## Forbidden state mutation

No task, episode, `ResearcherState`, evidence, artifact, exposure, permission, capability, or gate mutation; no requested effect.

## Failure semantics

Unknown route or mismatched target is `INVALID_REQUEST`; current policy denial is `AUTHORITY_DENIED`; terminal/stale lifecycle is explicit and non-executing; indeterminate policy fails closed. Exact replay converges on the same decision, while changed semantics under the replay identity conflict. Denials never leak forbidden values.

## Observable consequences

The same typed request is routed only when its exact target and policy are current. A foreign/stale target or denied dataset produces no capability/commit invocation. action.authorize-request never changes authored science to make it permissible.

## False-success implementations considered

- Replace claimed episode with the active episode.
- Treat action.decode-intent typing or schema visibility as permission.
- Route unknown kinds to a generic analysis capability.
- Check policy after capability access.
- Let a privileged requester authorize its own transition.

## Falsifying tests

1. Pair otherwise identical actions targeting the current episode and a foreign/stale episode. Only the current action yields a route; fail-on-call capability/commit doubles remain untouched for the other. **Level A/B.**
2. Pair permitted and denied dataset requests and assert denial performs zero data/capability reads and exposes no values. **Level A/B.**
3. Submit unknown kind, terminal episode, indeterminate policy, replay, and changed-payload replay; assert exact structured outcomes and no effect.
4. Preserve unusual schema-valid `run_analysis` content through authorization; policy may deny execution but may not rewrite it.

## Mutation-sensitivity check

**Mutation:** replace every model-claimed episode with the latest active episode before checking.

**Expected failure:** test 1 becomes red because the foreign/stale request is incorrectly authorized; the capability fail-on-call double is invoked.

## Composite dependencies

action.decode-intent supplies faithful untrusted requests; data.inspect-authorized-view and sandbox.authorize-execution execute only authorized contexts; commit.compose-request handles governed transitions; trajectory.append-event records decisions; runtime.run-bounded-episode composes the runtime.

## Fundamentals review

`CONSISTENT`. The contract preserves open-ended intent while enforcing identity and authority at the first effect-bearing boundary. It neither launders targets nor grants authority through tool visibility.

## Grill findings

Resolved non-semantically: added paired current/foreign identity proof, fail-closed indeterminate policy, no-read denial assertions, and explicit separation of route from execution. No unresolved semantic weakness.

## Remaining user decisions

None. Route registry shape, policy engine representation, identifier format, and failure class layout remain implementation choices.
