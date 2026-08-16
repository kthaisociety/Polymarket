# Milestone 1 Implementation Readiness

Status: **READY for red-test implementation (readiness level 4 of 5)**.

This document is authoritative for the high-risk semantic seams and discriminating test designs of
Milestone 1. It refines `MILESTONE_1_RUNTIME_DESIGN.md`; it does not replace the global
architecture, locked decisions, invariants, or approved contracts. If a conflict is found, use the
precedence and contradiction protocol in `ALIGNMENT_AND_DIAGRAMS.md`.

Level 4 means the critical seams, failure behavior, and falsifying tests are specified closely
enough to implement red tests. Level 5 requires those tests to exist and pass. No tests or production
code are added by this document.

## 1. Scope and source of truth

The Milestone 1 organism is:

```text
UserMandate -> TaskCompiler -> ResearchTaskProposal -> exact human confirmation -> ResearchTask -> ResearchRuntime.initialize
-> ResearchSession + ResearcherState + ResearchEpisode
-> ContextBuilder -> ContextPacket -> ModelProvider -> typed AgentAction -> ActionRouter
-> authorized capability or semantic-transition request
-> StructuredObservation or CommitResult -> ResearchEpisode progression
-> next reconstructed ContextPacket
```

The semantic-commit branch is:

```text
ProposeEpisodeTransitionAction -> CommitRequest
-> independent episode/state validation -> atomic governed commit
-> ResearchEpisode and optional ResearcherState progression
```

The detailed M1 scope remains in `MILESTONE_1_RUNTIME_DESIGN.md`. The approved entry contracts
remain authoritative in `contracts/001-user-mandate-to-research-task.md` and
`contracts/002-runtime-initialization.md`. This document adds the missing arrow-level layer. It
specifies semantics and observable behavior, not package layout, classes, databases, serializers,
or provider-specific wire formats.

## 2. Empirical constraint carried into the rebuild

An identifier crossing a seam does not prove that the required meaning crossed it.

```text
upstream evidence E1 -> downstream decision B1
upstream evidence E2 -> downstream decision B2

E1 != E2
B1 != B2
```

The downstream actor must have no hidden access to the upstream dataset, capability result, store,
fixture branch, or pre-scripted turn queue. The canonical M1 discriminating case is:

```text
observed row_count = 18 -> second action requests RESOLVED
observed row_count = 2  -> second action requests SUSPENDED
```

The second action must be selected from the first observation as reconstructed into the next
`ContextPacket`. `observation_id` and `artifact_refs` support identity and drill-down, but are not
substitutes for bounded substantive evidence needed for the next decision.

## 3. Test-strength classification

| Level | Meaning | Valid claim |
|---|---|---|
| A | Unit or grader logic only | A local rule or grader behaves as specified. |
| B | Scripted sequence whose later outputs ignore context | Wiring, ordering, and fixed orchestration work. |
| C | Deterministic context-sensitive behavioral test | Information crossing the intended seam caused a later action. |
| D | Real-model stochastic eval | A real provider exhibits graded behavior within limits. |

A deque-only provider that returns `queue.popleft()` is Level B even across multiple turns. It may
prove orchestration, not observation-driven autonomy. Level C is required when the claim is that
semantic information caused the next model action. Level D is not required for M1 red-test
implementation readiness.

## 4. Critical seam inventory

| ID | Seam | Primary risk | Minimum evidence |
|---|---|---|---|
| S1 | `UserMandate + environment metadata + human confirmation -> ResearchTask` | identity / information / authority | Level A/B global mission.confirm-task cases |
| S2 | `ResearchTask + ResearchEnvironmentSnapshot -> RuntimeInitialization` | identity / lifecycle / state | Level B coherent-or-nothing initialization |
| S3 | `authoritative runtime records -> ContextPacket` | information / permissions / staleness | Level C downstream choice from reconstructed content |
| S4 | `ContextPacket -> ModelProvider -> normalized ModelResponse` | provider neutrality / information | Level B capture and provider replacement |
| S5 | `untrusted ModelResponse -> typed AgentAction` | authority / identity | Level A/B malformed and mismatched-action cases |
| S6 | `AgentAction -> authorized CapabilityExecutionResult` | authority / side effects | Level B denial and read-only execution |
| S7 | `CapabilityExecutionResult -> StructuredObservation` | provenance / information | Level A/B forged provenance and bounded output |
| S8 | `StructuredObservation -> ResearchEpisode working evidence` | state mutation / lifecycle | Level B episode-updated/state-unchanged |
| S9 | `ResearchEpisode working evidence -> next ContextPacket` | causal feedback / information | Level C row-count branch |
| S10 | `ProposeEpisodeTransitionAction -> CommitRequest` | intent / lifecycle separation | Level A/B explicit presence/absence |
| S11 | `CommitRequest -> independent validation decisions` | authority / evidence / concurrency | Level A/B stale and invalid-evidence cases |
| S12 | `validated proposals -> atomic CommitResult` | state mutation / atomicity | Level B fault injection |
| S13 | `commit retry -> original result or IDEMPOTENCY_CONFLICT` | identity / irreversible effects | Level B replay and changed payload |
| S14 | `consequential runtime transitions -> Trajectory and ArtifactStore` | provenance / auditability | Level B append-only success/rejection trace |

These are the high-risk seams only. Local helpers and collection shapes are not additional public
contracts unless implementation exposes a new failure mode.

## 5. Seam contracts

## Seam: UserMandate + environment metadata + human confirmation -> ResearchTask

The global mission.confirm-task contract supersedes this document's former compilation-only grouping:
`docs/architecture/mission/transitions/confirm-task.md`.

It requires a faithful `ResearchTaskProposal` and readable formalization, exact human confirmation
before an authoritative task exists, new confirmation after edits, explicit unresolved/clarification
semantics, preservation of broad-discovery and bounded-exhaustion meaning, metadata-only compilation,
and coherent/idempotent publication. Its eight falsifying tests and mutation-sensitivity check are
the authoritative red-test designs for M1 task creation.

## Seam: ResearchTask + ResearchEnvironmentSnapshot -> RuntimeInitialization

Canonical global contract: `docs/architecture/runtime/transitions/initialize-research.md`.

### Purpose

Create one coherent autonomous attempt without performing research.

### Source

A versioned task and identified environment snapshot.

### Destination

One linked `ResearchSession`, `ResearcherState` version 0, and `ResearchEpisode` in `ACTIVE`.

### Must preserve

Task/version, environment identity, unresolved semantics, independent identities, epistemic zero.

### Must exclude

Invented findings, protected values/exposures, provider output, cross-session mutable state.

### Allowed side effects

Persist session, initial state, initial episode, and initialization event coherently.

### Forbidden side effects

No model call, data mutation, research, task mutation, protected access, or memory write.

### Failure semantics

Coherent-or-failed: persistence failure cannot leave a resumable healthy-looking half-session.

### Observable consequence

Loading yields one matching state v0 and active episode tied to the same task/environment, with no
findings.

### Falsifying test

Inject failure between persistence steps; assert no valid active half-session. Initialize twice;
assert independent identities/contents. Level B.

### Mutation sensitivity

Reuse one mutable state instance between sessions. The independence test goes red.

## Seam: authoritative runtime records -> ContextPacket

Canonical global contract:
`docs/architecture/runtime/transitions/build-context-packet.md`.

### Purpose

Reconstruct working context from system-owned truth rather than provider transcript.

### Source

Current task, session, state, episode, permitted evidence, environment, permissions, warnings.

### Destination

`ContextBuilder` produces a provider-neutral packet for the next decision.

### Must preserve

Mission/task, state version, episode identity/status/plan, bounded substantive observations,
unresolved questions, current/superseded meaning, refs, environment, permissions, warnings.

### Must exclude

Required transcript dependence, whole trajectory, unauthorized content, stale belief as current,
raw large artifacts, unrelated store content.

### Allowed side effects

Authorized reads and context-build observability.

### Forbidden side effects

No state/episode mutation, authorization, tool execution, protected exposure, hidden provider call.

### Failure semantics

Missing/incoherent records or unsafe projection fail explicitly before provider invocation.

### Observable consequence

After transient context is discarded, reconstruction permits the same evidence-dependent decision.

### Falsifying test

Two otherwise identical episodes contain different bounded facts; a provider reads only each packet
and chooses different actions. Level C.

### Mutation sensitivity

Project only observation/artifact IDs. The causal test goes red.

## Seam: ContextPacket -> ModelProvider -> normalized ModelResponse

Canonical model.request-decision public provider contract:
`docs/architecture/runtime/transitions/request-model-decision.md`.

Provider-native normalization remains the separate model.normalize-response seam, canonically specified at
`docs/architecture/runtime/transitions/normalize-model-response.md`.

### Purpose

Obtain intelligence through a replaceable provider without granting runtime authority.

### Source

Harness supplies packet, action schemas, model configuration.

### Destination

`ModelProvider` returns provider-neutral `ModelResponse`.

### Must preserve

Context semantics, schema identities, turn correlation, structured arguments, termination signal,
relevant usage/failure metadata.

### Must exclude

Writable stores, data/capability handles, governance authority, provider-native objects downstream,
hidden-transcript dependence for correctness.

### Allowed side effects

Provider operation and append-only model-call events; retry cannot repeat downstream effects.

### Forbidden side effects

Provider cannot persist state/episode, execute, authorize, or mutate scientific objects.

### Failure semantics

Operational failure becomes `PROVIDER_UNAVAILABLE`; malformed output is not coerced to valid action.

### Observable consequence

Provider replacement requires no runtime/scientific architecture change.

### Falsifying test

Capture exact packet/schema and substitute a second provider returning the same normalized response;
assert identical typed action. Level B only.

### Mutation sensitivity

Route on provider-native tool-call type. Replacement-provider test goes red.

## Seam: untrusted ModelResponse -> typed AgentAction

Canonical global contract:
`docs/architecture/runtime/transitions/decode-action-intent.md`.

action.decode-intent preserves structurally valid target claims as untrusted request content. action.authorize-request owns comparison
with authoritative current session/episode/policy and rejection of mismatch or staleness.

### Purpose

Turn model intent into a bounded typed request before execution or mutation.

### Source

Untrusted normalized response.

### Destination

Action decoding yields one M1 action or structured failure.

### Must preserve

Kind, action/session/episode identity, arguments, bounds, effectful idempotency key.

### Must exclude

Unknown kinds, malformed fields, cross-session/episode identity, extra executable paths,
provider-native objects.

### Allowed side effects

Append request/rejection events; decoding is state-pure.

### Forbidden side effects

No capability, state/episode/artifact write, or commit before validation.

### Failure semantics

Malformed is `MALFORMED_MODEL_RESPONSE`; unsupported/mismatched is `INVALID_REQUEST`; neither runs.

### Observable consequence

Only current typed `InspectDatasetAction` or `ProposeEpisodeTransitionAction` reaches its next seam.

### Falsifying test

Unknown action and valid action naming another episode both produce failure, zero downstream calls,
unchanged stores, recorded rejection. Level A/B.

### Mutation sensitivity

Omit episode comparison. Zero-call assertion goes red.

## Seam: AgentAction -> authorized CapabilityExecutionResult

### Purpose

Execute permitted read-only inspection inside current capability/data authority.

### Source

Router supplies validated inspection action and harness-built `AuthorizedExecutionContext`.

### Destination

Capability receives `AuthorizedDataView` and returns result content.

### Must preserve

Action/session/episode correlation, requested dataset/fields/bounds, actual view/version, status,
facts from that view.

### Must exclude

Unauthorized values, secrets, writable stores, unrestricted raw access, unbounded content,
scientific claims, fitting, persistence/provenance authority.

### Allowed side effects

Read authorized view, consume configured resources, produce result/events.

### Forbidden side effects

No source/state/episode mutation, protected exposure, unapproved filesystem/network, promotion.

### Failure semantics

`AUTHORITY_DENIED`, `NOT_FOUND`, or `INVALID_REQUEST` as applicable; failures leak no forbidden data.

### Observable consequence

Permitted request reads only its view without mutation; denial reads no data.

### Falsifying test

Use read counters and before/after source hashes for permitted and denied inspection. Level B.

### Mutation sensitivity

Resolve from unrestricted catalog. Denied-read assertion goes red.

## Seam: CapabilityExecutionResult -> StructuredObservation

### Purpose

Create bounded model-facing evidence with harness-authoritative provenance.

### Source

Capability content plus harness authorization, access, timing, environment, artifact instrumentation.

### Destination

Harness produces `StructuredObservation` for progression.

### Must preserve

Observation/action correlation, status/type, summary/payload, schema semantics, row count, coverage,
missingness, bounded preview, warnings, recoverability, actual resource/version, execution identity,
drill-down refs.

### Must exclude

Capability self-attestation as sole authority, forged provenance, unbounded rows, raw traceback as
primary content, scientific conclusions, mutation instructions.

### Allowed side effects

Persist large/raw detail and append provenance/observation events.

### Forbidden side effects

No episode/state mutation, promotion, or fabricated provenance.

### Failure semantics

Inconsistent claims are overridden from harness facts or rejected. Failures become safe structured
observations with diagnostic refs.

### Observable consequence

Observation supports next decision without full artifact while retaining authorized drill-down.

### Falsifying test

Capability claims version X, authorized view records Y; assert Y or rejection. Assert preview bounds
and traceback externalization. Level A/B.

### Mutation sensitivity

Trust capability provenance verbatim. Forgery test goes red.

## Seam: StructuredObservation -> ResearchEpisode working evidence

### Purpose

Persist current-investigation evidence without changing durable understanding.

### Source

Runtime progression receives harness observation and current active episode identity.

### Destination

Current episode gains bounded intermediate content and relevant refs/warnings.

### Must preserve

Observation/action identity, substantive payload, status/type, warnings, provenance/refs, order,
episode identity/status.

### Must exclude

Implicit state delta, durable conclusion, forged gate state, unrelated episode content, raw artifacts,
capability/provider mutation authority.

### Allowed side effects

Harness appends working evidence and progression event.

### Forbidden side effects

No `ResearcherState`, task, lifecycle, or promotion change merely because observation arrived.

### Failure semantics

Identity/version mismatch, terminal episode, or persistence failure rejects progression. Successful
turn cannot leave observation unavailable to reconstruction.

### Observable consequence

Reloaded episode exposes bounded observation meaning; state is unchanged.

### Falsifying test

Advance inspection, discard transient objects, reload episode/state; assert row count/provenance and
unchanged state. Level B.

### Mutation sensitivity

Store only IDs. Row-count assertion goes red.

## Seam: ResearchEpisode working evidence -> next ContextPacket

### Purpose

Close the fast feedback loop so the next action can depend on the prior observation.

### Source

Persisted episode plus current state/session/environment and permitted evidence retrieval.

### Destination

Next packet, the tested provider's only observation source.

### Must preserve

Bounded substantive facts, status/warnings, plan/status, provenance/refs, E1-versus-E2 meaning.

### Must exclude

Transcript dependence, hidden fixture state, provider data/capability/store access, whole trajectory,
unauthorized evidence.

### Allowed side effects

Authorized reads and context-build observability.

### Forbidden side effects

No inspection, mutation, transition, authorization, or artifact change.

### Failure semantics

Unsafe/unavailable working evidence fails context build before second provider call.

### Observable consequence

Changing only row count changes the second typed action from one deterministic provider.

### Falsifying test

Two fresh sessions use identical provider logic with no hidden data access. Row count 18 causes
`RESOLVED`; 2 causes `SUSPENDED`, derived solely from second packet. Level C.

### Mutation sensitivity

Drop payload, retain IDs. Both take “fact missing” branch and test goes red.

## Seam: ProposeEpisodeTransitionAction -> CommitRequest

### Purpose

Represent semantic-boundary intent without granting mutation authority.

### Source

Validated transition action naming current identities/status, optional explicit state proposal,
idempotency metadata.

### Destination

Harness creates request with required episode proposal, explicitly present/absent state proposal,
stable semantic identity.

### Must preserve

Identities, starting version, target status, synthesis, refs, proposal presence, key, payload identity.

### Must exclude

Implicit state delta, store handles, forged validation, disguised task rescope, unsupported gate claim.

### Allowed side effects

Construct request and append request event.

### Forbidden side effects

No episode/state mutation before validation/coordinated commit.

### Failure semantics

Malformed/mismatched is `INVALID_REQUEST`; illegal lifecycle is `INVALID_EPISODE_TRANSITION`.

### Observable consequence

Lifecycle-only request explicitly lacks state proposal; adding one changes payload but applies nothing.

### Falsifying test

Compare identical actions except state-proposal presence; assert first cannot alter state and second
carries exact proposal. Level A/B.

### Mutation sensitivity

Create default state delta for `RESOLVED`. Absence assertion goes red.

## Seam: CommitRequest -> independent validation decisions

### Purpose

Authorize lifecycle and durable understanding independently before mutation.

### Source

Request, current versions, authoritative evidence/provenance, permissions, epistemic position.

### Destination

Episode and state validators return separate decisions to coordinator.

### Must preserve

Request/key, versions, target status, proposal presence, exact refs/authority, mission, reasons.

### Must exclude

Self-authorization, implicit proposal, stale acceptance, invalid evidence, forged gate, mutation.

### Allowed side effects

Read records, append validation observability, return repairable structured rejection.

### Forbidden side effects

Validators do not write state/episode, grant access, or reinterpret synthesis.

### Failure semantics

`INVALID_EPISODE_TRANSITION`, `STALE_STATE_VERSION`, or `INVALID_EVIDENCE_REFERENCE`; any required
rejection blocks all mutation.

### Observable consequence

Valid lifecycle cannot smuggle invalid state delta.

### Falsifying test

Pair valid resolution with stale state or unauthorized evidence; assert separate decisions and no
commit. Level A/B.

### Mutation sensitivity

Episode validation alone authorizes request. Unchanged-store assertion goes red.

## Seam: validated proposals -> atomic CommitResult

### Purpose

Apply one semantic boundary without scientifically impossible half-state.

### Source

Original request, required successful decisions, current store versions.

### Destination

Coordinator persists episode and optional state delta, then returns authoritative result.

### Must preserve

Request/key, version lineage, target status, state-proposal presence, refs, outcome identity,
all-or-nothing relation.

### Must exclude

Unvalidated/implicit mutation, history rewrite, partial success, payload change, duplicate identity.

### Allowed side effects

Atomically transition episode, optionally create state version, persist outcome, append commit event.

### Forbidden side effects

No task mutation, second version, rewrite, or success with inconsistent required records.

### Failure semantics

Validation/concurrency/persistence failure commits neither required proposal. Lifecycle-only success
leaves state unchanged because absence is explicit.

### Observable consequence

Success reloads coherently; injected failure leaves both pre-request records.

### Falsifying test

Inject failure after first underlying write in combined request; assert active episode, old state, no
success result. Level B.

### Mutation sensitivity

Persist episode before state without atomic staging. Fault-injection test goes red.

## Seam: commit retry -> original result or IDEMPOTENCY_CONFLICT

### Purpose

Make retries safe while distinguishing replay from changed request reusing identity.

### Source

Request with stable key/canonical payload and configured logical store.

### Destination

Commit returns first-use result, original result, or `IDEMPOTENCY_CONFLICT`.

### Must preserve

Key, payload identity, original result/versions/evidence, one-time effects.

### Must exclude

Duplicate effects/events, partial comparison, overwrite, changed payload accepted under same key.

### Allowed side effects

First use commits/stores result; exact replay reads/returns it; conflict may append rejection event.

### Forbidden side effects

Replay/conflict cannot reapply or alter original commit.

### Failure semantics

Exact replay returns original. Different semantic payload returns `IDEMPOTENCY_CONFLICT`. This holds
after runtime/coordinator reconstruction against the same logical store; destroyed in-memory store
is outside M1 durability claims.

### Observable consequence

Exact retries preserve result/counts; semantic changes conflict and preserve original.

### Falsifying test

Commit, reconstruct coordinator over same stores, replay, then separately change status, synthesis,
delta, evidence; assert original result, conflicts, one commit. Level B.

### Mutation sensitivity

Compare key only. Changed-payload cases go red.

## Seam: consequential runtime transitions -> Trajectory and ArtifactStore

### Purpose

Preserve audit/replay and drill-down without treating either as belief or context.

### Source

Harness/runtime events across initialization, context/model, action, authorization, execution,
observation, validation, rejection, commit; large/debug outputs.

### Destination

Append-only trajectory and immutable artifact records/refs.

### Must preserve

Session/episode/action/observation/commit correlation, order, status/failure, provenance refs,
artifact identity, request/execution/observation distinctions.

### Must exclude

Events as state, whole trajectory in context, unauthorized artifacts, history rewrite/deletion, raw
traceback as default observation.

### Allowed side effects

Append events/artifacts; repairable rejection observation may enter active episode.

### Forbidden side effects

No event/artifact grants authority, changes lifecycle/state, authorizes evidence, erases failure.

### Failure semantics

Consequential operation is not fully successful unless required audit/refs are consistent. Exact
event enum and physical transaction mechanics remain deferred.

### Observable consequence

Success and rejection reconstruct as ordered traces; detail is drillable; context/state stay distinct.

### Falsifying test

Run successful inspection, rejected mismatched action, successful commit; assert ordered correlated
events, rejection retention, drill-down, no automatic belief. Level B.

### Mutation sensitivity

Record only successes. Rejection assertion goes red.

## 6. Cross-seam discriminating scenarios

### C1 — observation-driven continuation (Level C)

Two equivalent fresh sessions use the same deterministic context-sensitive provider. Its first
action always inspects. It has no dataset, capability, episode/artifact store, or fixture access. On
turn two it parses row count only from `ContextPacket`: 18 requests `RESOLVED`, 2 requests
`SUSPENDED`, and missing/unparseable uses a third sentinel outcome. Assert different packet facts and
actions, unchanged pre-commit state, no alternate access, and failure if projection retains IDs only.

### C2 — reconstruction without transcript (Level C)

After observation persistence, destroy transient/provider conversation state and use a fresh
provider instance with the same rule. The same next action must follow from rebuilt context.

### C3 — lifecycle/state separation (Level B)

Lifecycle-only changes only episode. Combined transition changes episode and creates one state
version only after both validations. State-validation failure changes neither.

### C4 — uncertain acknowledgement (Level B)

First commit succeeds but its acknowledgement is lost. Reconstruct over same stores and resend:
original result returns, no duplicate effect; changed payload conflicts.

## 7. Failure semantics summary

| Condition | Required result | Prohibited false success |
|---|---|---|
| malformed provider action | `MALFORMED_MODEL_RESPONSE` | capability/commit invoked |
| unknown/mismatched identity | `INVALID_REQUEST` | cross-session/episode execution |
| unauthorized data | `AUTHORITY_DENIED` | read or protected leakage |
| missing dataset | `NOT_FOUND` | empty inspection as success |
| provider operational failure | `PROVIDER_UNAVAILABLE` | corruption or duplicate effect |
| invalid lifecycle | `INVALID_EPISODE_TRANSITION` | lifecycle mutation |
| stale state | `STALE_STATE_VERSION` | either proposal committed |
| invalid evidence | `INVALID_EVIDENCE_REFERENCE` | durable delta committed |
| reused key, changed payload | `IDEMPOTENCY_CONFLICT` | overwrite or replayed effect |
| persistence/internal failure | `INTERNAL_FAILURE` | healthy half-state or success |

Repairable rejection becomes a structured observation in the active episode and next context.
`AUTHORITY_DENIED` remains governance denial, not ordinary retryable technical error.

## 8. Dependency order for red tests and implementation

The next authorized work should add red tests in this order. This document authorizes neither tests
nor production implementation.

1. Identity/bootstrap: S1, S2.
2. Reconstructable decision surface: S3, S4, S5.
3. Authorized inspect/feedback: S6, S7, S8, S9; make C1 red before any feedback repair.
4. Semantic boundary: S10, S11, S12, S13.
5. Audit/composed organism: S14, C2-C4, then full M1 acceptance scenario.

Level A establishes pure validation. Level B proves deterministic routing, ordering, side effects,
failure, atomicity, idempotency. Level C is mandatory when observation/context is claimed to cause a
later model decision. Level D begins only after deterministic seams are trustworthy.

## 9. Readiness assessment

| Question | Result |
|---|---|
| Canonical M1 boundary recovered | yes |
| High-risk semantic arrows identified | yes |
| Every seam has contract and failure behavior | yes |
| Every seam has falsifying test and mutation sensitivity | yes |
| Causal information seams require Level C | yes |
| Local storage/provider/layout choices avoided | yes |
| Blocking architectural contradiction | no |
| Actual red tests implemented | no |
| Production implementation begun | no |

**Verdict: READY for red-test implementation, not ready for production implementation.**

The next authorization boundary is translating these contracts into the smallest failing tests in
the order above. A green implementation is not authorized here.

## 10. Unresolved questions and deliberately deferred details

No unresolved semantic ambiguity blocks M1 red-test implementation.

Deliberately deferred: package/class layout; physical persistence/transactions and serialization;
complete event taxonomy; exact context budgets; real provider auth/transports; production resource
limits; a manual terminal-context inspection API; durability after destroying an intentionally
in-memory logical store.

The runtime stops calling the provider after a terminal episode. A separate read-only terminal
context API is a local choice. Idempotency survives runtime/coordinator reconstruction against the
same configured logical store; production crash durability depends on later persistence choice.
