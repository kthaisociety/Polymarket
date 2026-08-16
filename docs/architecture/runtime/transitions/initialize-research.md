# runtime.initialize-research — ResearchTask + ResearchEnvironmentSnapshot → coherent runtime initialization

Status: **LOCKED — readiness level 4 of 5**

## Purpose

runtime.initialize-research creates the blank, durable, trustworthy starting point for one autonomous research attempt
before the model performs any reasoning or research.

It maps one exact human-confirmed task version and one exact environment snapshot into one coherent
organism:

```text
ResearchSession
├── ResearcherState_0
└── active ResearchEpisode_0
```

The session identifies the attempt. State version 0 records its committed epistemic zero. Episode 0
is its empty active workspace for subsequent orientation and planning. runtime.initialize-research exists so the first model
response cannot accidentally become the untracked or authoritative starting state.

## Relevant locked invariants

- **I9 — Observation is not durable belief.** Initialization cannot turn available metadata or raw
  values into committed belief.
- **I10 — Mission cannot silently drift.** The exact confirmed task/version remains the mission of
  the new attempt.
- **I24 — Environment identity is explicit.** The attempt remains tied to the exact environment and
  schema versions under which it began.
- **I25 — Runtime retries do not duplicate irreversible effects.** An exact initialization retry
  cannot create another session.
- **Contract 001 / mission.confirm-task.** Only an authoritative human-confirmed `ResearchTask`, never a proposal,
  may initialize research.
- **Contract 002.** Initialization is deterministic infrastructure/orientation, performs no research,
  and creates a coherent session, initial state, and active episode.

## Source A

runtime.initialize-research receives:

1. **Exact `ResearchTask` identity/version and usable task semantics** — confirmed main goal, hard
   constraints, initial seeds/preferences, unresolved researchable semantics, completion obligation,
   and task provenance. An opaque ID alone is insufficient if initialization cannot reconstruct the
   meaning needed by the starting state and episode.
2. **Exact `ResearchEnvironmentSnapshot` identity/version and authorized metadata** — environment
   and schema identity, available catalog/dataset references, capability metadata, permissions,
   compute metadata, and protected-resource metadata without protected values.
3. **Authorized initialization request identity** — distinguishes an exact retry from an intentional
   independent attempt and binds the requested task/environment versions.

A `ResearchTaskProposal`, latest-version alias, mutable live environment without snapshot identity,
or unauthorized request is not a valid source.

## Destination B

The authoritative destination is one coherent `RuntimeInitialization` containing or durably linking:

### ResearchSession

- a distinct attempt identity;
- exact task and environment snapshot identities;
- the required state-0 and episode-0 identities;
- relevant runtime/model/harness configuration identity;
- initialization request/provenance;
- lifecycle status that can be active only when the complete initialization is authoritative.

### ResearcherState_0

- version 0 and the same session/task/environment identities;
- the confirmed goal, hard constraints, seeds/preferences, unresolved semantics, and completion
  obligation required to reconstruct the starting position;
- empty explored-path, accepted-finding, and durable-belief history;
- no passed scientific/governance gates;
- no protected exposures;
- no invented epistemic progress.

### ResearchEpisode_0

- the same session/task/environment and base-state identities;
- active lifecycle status;
- an orientation workspace carrying mission, constraints, seeds, and unresolved questions;
- no model output, observations, executed actions, evidence, findings, or completed research plan.

Exact classes, field layouts, persistence technology, and wording are implementation choices.

## Mapping f

```text
confirmed ResearchTask@T
+ authorized ResearchEnvironmentSnapshot@E
+ InitializationRequest@R
    → validate exact identities, authority, and usable semantics
    → project mission/environment into epistemic-zero state and empty active episode
    → coherently publish Session + State_0 + Episode_0 + initialization provenance
```

Request identity determines retry versus independence:

```text
same exact R + same semantics  → same coherent initialization (idempotent retry)
new R + same T/E              → new independent research attempt
same R + changed T/E/semantics → conflict
```

The mapping may copy or reference task/environment meaning, allocate identities, establish links,
create zero-state orientation, and persist initialization events. It may not reason, research, call
a model, inspect protected values, or infer scientific usefulness.

## Must preserve

- exact task identity and version;
- task-level main goal, constraints, breadth, unresolved semantics, and completion obligation;
- distinction between seed resources/preferences and hard constraints or accepted evidence;
- exact environment and schema snapshot identity;
- permissions and protected-resource metadata without upgrading them into access or exposure;
- exact initialization request identity and provenance;
- semantic and referential coherence among the session, state, and episode;
- epistemic zero: no findings, explored paths, gates, exposures, or model-authored content;
- independence between different session attempts;
- historical interpretability after later task or environment versions exist.

## May transform

- task/environment representations into session-facing orientation structures;
- durable task/environment semantics into bounded state/episode projections or authorized references;
- an initialization request into new session/state/episode identities;
- implementation-specific storage operations into one externally coherent publication.

Semantic accessibility must survive: a reference is acceptable only when the starting position can
be reconstructed through the authorized production path after transient context disappears.

## Must exclude

- unconfirmed task proposals;
- latest-task or latest-environment substitution;
- invented targets, horizons, assumptions, plans, hypotheses, findings, or predictor usefulness;
- protected values, unauthorized data contents, or manufactured exposure records;
- provider/model output or calls;
- capability execution, dataset mutation, evidence creation, gate passage, promotion, memory, or
  skill writes;
- shared mutable state or episode contents between independent sessions;
- healthy/active status for a partial initialization;
- duplicate durable sessions for one exact request;
- rebinding an existing session when newer task/environment versions appear.

## Authority boundary

- The instruction giver authorized the mission through mission.confirm-task.
- An authorized caller may request a research attempt for an exact task/environment pair.
- The runtime/harness validates authority, exact identities, request idempotency, and coherence.
- Stores persist through narrow runtime-owned interfaces; they do not invent scientific state or
  independently activate a session.
- The model/provider has no role in initialization and cannot authorize or enrich it.
- Protected-resource metadata does not authorize protected-resource content access.

## Allowed state changes

runtime.initialize-research may coherently create:

- one session identity and lifecycle record;
- one state version 0;
- one active episode version 0;
- exact links among them and their task/environment versions;
- initialization request/idempotency and provenance records;
- bounded runtime/trajectory initialization events.

A new request for the same task/environment may create another independent set.

## Forbidden state changes

- no task or environment mutation;
- no scientific findings, evidence, observations, actions, or explored-path history;
- no protected read or exposure mutation;
- no gate, backtest, validation, or promotion transition;
- no cross-task/session memory or skill mutation;
- no partial initialization visible as healthy or resumable;
- no mutation of an already completed exact initialization on retry;
- no shared mutable research state across independent attempts.

## Failure semantics

- Unconfirmed, missing, corrupt, unauthorized, or mismatched task/environment input is rejected
  explicitly without creating a healthy session.
- Stale explicit versions are never silently replaced by latest versions. An explicitly selected
  historical version may initialize only when it remains available and the caller is authorized;
  its historical/superseded status remains visible.
- Same request identity with changed task, environment, or semantics is an explicit conflict.
- Exact retry converges on the original coherent result, including under concurrency.
- Failure while publishing any required session/state/episode/provenance component yields no active,
  resumable half-session. Retry may complete or recover the same request exactly once.
- No fallback may call the model, inspect protected data, manufacture defaults, or weaken meaning.

## Observable consequences

- Loading a successful initialization yields exactly one mutually consistent session, state 0, and
  active episode 0 for the supplied task/environment versions.
- Changing only the task meaning changes the projected mission while preserving epistemic zero.
- Changing only the environment snapshot changes the exact environment reference and permitted
  metadata without creating beliefs or exposures.
- Two independent requests for the same task/environment produce isolated attempts.
- Exact retries produce one durable attempt.
- After newer task/environment versions appear, historical initialization still reconstructs its
  original starting position.
- If the LLM has produced zero tokens, the entire starting position remains explainable.

## False-success implementations considered

1. Create three records that carry matching IDs but omit usable mission semantics.
2. Resolve task/environment references to their latest versions during initialization or loading.
3. Convert available predictors or seed suggestions into initial beliefs or plans.
4. Read a protected holdout while claiming the exposure history is empty.
5. Reuse one mutable state/episode object across independent sessions.
6. Treat retries as new attempts or new attempts as retries.
7. Mark a session active before all required components/provenance are authoritative.
8. Call the model to produce the first orientation or plan during deterministic setup.
9. Fill unresolved task semantics with convenient defaults.

## Falsifying tests

All runtime.initialize-research tests are deterministic Level A/B tests. They prove initialization semantics and runtime
policy, not autonomous model reasoning. No Level D model evaluation is required because a correct
runtime.initialize-research makes no model call.

### runtime.initialize-research-T1 — exact task meaning crosses the seam

Initialize otherwise identical attempts from two confirmed tasks whose missions differ only between
Swedish healthcare waiting times and Swedish electricity prices. Load outputs only through the
initialization/session path, with no direct task side channel. Assert the state/episode orientations
differ correspondingly, carry the exact task versions, preserve each mission, and remain epistemic
zero.

This kills generic orientation and opaque-reference-without-usable-semantics implementations.

### runtime.initialize-research-T2 — unresolved semantics remain unresolved

Initialize a task with unresolved forecast horizon. Assert state 0 and episode 0 preserve and
foreground the unresolved horizon, no default such as next quarter appears, and the task is
unchanged.

### runtime.initialize-research-T3 — tempting environment metadata does not manufacture belief

Provide environment metadata listing inflation, unemployment, and regional staffing datasets.
Assert they may appear only as available resources/seeds and that findings, accepted hypotheses,
explored paths, gates, exposures, observations, and model output are empty.

### runtime.initialize-research-T4 — protected metadata causes zero protected reads

Expose metadata that holdout H1 exists without content-read permission. Assert H1 may be referenced
as protected metadata, protected-value read count is zero, and exposure state remains empty.

### runtime.initialize-research-T5 — coherent-or-nothing publication

Inject failure after each potential session/state/episode/provenance persistence boundary. Assert no
request can load or resume a healthy active session unless all required components and links are
coherent. Retry may produce one complete initialization, never a half-session or duplicate.

### runtime.initialize-research-T6 — retry versus independent attempt

Initialize twice with exact request R1 and assert one session and the same coherent result. Initialize
the same task/environment with new request R2 and assert distinct session/state/episode identities.
Mutate allowed working episode state in one attempt and assert the other is unchanged. Concurrent
R1 calls also converge on one result; reusing R1 with changed semantics conflicts.

### runtime.initialize-research-T7 — exact historical environment identity

Initialize one request under E1, then publish E2 and initialize another under E2. Assert each loaded
state/episode remains tied to its exact environment version and E1 is never retroactively replaced.

### runtime.initialize-research-T8 — initialization performs no research

Attach spies/fakes to the provider, capability execution, dataset-content access, protected access,
evidence/finding creation, gates/promotions, and memory/skill writes. Initialize successfully and
assert every forbidden call/effect count remains zero.

### runtime.initialize-research-T9 — episode 0 is an empty active orientation workspace

Assert episode 0 is active and coherent with the same session/task/environment/state 0; mission,
constraints, seeds, and unresolved questions are usable; observations, actions, findings, model
output, and completed plan are absent. Do not assert exact prompt wording or internal layout.

## Mutation-sensitivity check

**Mutation A:** Resolve the supplied task/environment references to the latest available versions.

**Expected test failure:** runtime.initialize-research-T1 or runtime.initialize-research-T7 becomes red because the initialized/historical starting
position changes rather than retaining the exact supplied identity and meaning.

**Mutation B:** Persist/activate the session before state 0 and episode 0 publication completes.

**Expected test failure:** runtime.initialize-research-T5 becomes red under injected failure because a resumable active
half-session becomes visible.

## Composite dependencies

- **mission.confirm-task:** only exact human-confirmed tasks may initialize.
- **mission.evolve-direction:** explicit historical task version and new-session behavior after genuine rescope.
- **context.build-packet:** subsequent context reconstruction consumes authoritative initialized records.
- **runtime.continue-from-observation/runtime.run-bounded-episode:** later turns evolve episode/state; runtime.initialize-research only establishes their zero point.

These dependencies are named, not specified or locked here.

## User decisions

The architecture owner approved:

1. runtime.initialize-research is a necessary logical transition but should remain a small initialization operation, not a
   large subsystem.
2. It creates the trustworthy blank starting checkpoint before any model output.
3. Session, state 0, and active episode 0 are created together so every active session is complete.
4. State 0 is durable epistemic zero; episode 0 is the empty active orientation workspace.
5. Initialization makes no model call and performs no research.
6. Exact retry and intentional independent attempt are distinguished by request identity.
7. Exact historical task/environment versions are preserved and never silently upgraded.
8. Public behavior is protected by the nine approved discriminating red-test designs above.

## Implementation/test handoff

Required red tests are runtime.initialize-research-T1 through runtime.initialize-research-T9. Forbidden shortcuts include latest-version
substitution, opaque IDs without usable meaning, model-assisted initialization, manufactured belief,
protected reads, shared mutable session state, duplicate retries, and partial active publication.

Package layout, storage technology, transaction mechanism, identifiers, internal types, orientation
wording, and refactoring choices remain free where they preserve the locked public semantics.

This handoff names mission.confirm-task, mission.evolve-direction, context.build-packet, runtime.continue-from-observation, and runtime.run-bounded-episode only as dependencies. It does not authorize
production code or executable-test implementation.

## Status

**LOCKED — readiness level 4 of 5.**

Level 5 requires the red tests to be implemented, fail for their intended reasons, and pass through
the real production path after authorized implementation.
