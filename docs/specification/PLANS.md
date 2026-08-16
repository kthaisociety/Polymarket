# Execution Plans

Use this file/template for multi-step Codex work that spans several components or carries
architectural risk.

Do not require a full execution plan for trivial local edits.

## Plan template

### Goal

What concrete behavior or capability will exist when this work is complete?

### Context to read

List the authoritative repository files and contracts relevant to this task.

### Architectural boundaries

Which responsibilities are in scope and explicitly out of scope?

### Invariants at risk

Reference specific items from `INVARIANTS.md`.

### Failure modes

What plausible implementation mistakes could produce incorrect scientific or runtime behavior?

### Tests and evals first

List:

- deterministic contract tests;
- adversarial invariant tests;
- integration tests;
- behavioral evals if a model is involved.

### Implementation steps

Use small ordered steps. Avoid designing unrelated future abstractions.

### Verification commands

Fill these in after repository bootstrap establishes the canonical commands.

### Done when

State observable completion criteria, not "code written."

### Spec changes discovered

If implementation reveals a genuine architectural inconsistency, record the proposed change and why
it is architectural rather than local.

---

# Initial Execution Plan - Milestone 1 Runtime Slice

The implementation-ready contract is `MILESTONE_1_RUNTIME_DESIGN.md`.

## Goal

Create the minimal autonomous research loop with state and episode separation, scripted model
actions, and one real read-only `inspect_dataset` capability without implementing the temporal
scientific kernel.

## Context to read

- `CONTEXT.md`;
- `ARCHITECTURE.md`;
- `DECISIONS.md`;
- `STATE_CONTEXT_AND_MEMORY.md`;
- `AUTHORITY_SANDBOX_AND_TOOLS.md`;
- `MODEL_PROVIDER.md`;
- `MILESTONE_1_RUNTIME_DESIGN.md`;
- `INVARIANTS.md` I9, I10, I14-I16, I20, I25;
- `TEST_STRATEGY.md`;
- contracts 001 and 002.

## Boundaries

In scope:

- task and session initialization;
- `ResearcherState` and `ResearchEpisode`;
- context reconstruction;
- provider interface and scripted provider;
- typed action routing;
- read-only `inspect_dataset` against the shared toy dataset;
- harness-owned provenance assembly;
- structured observation;
- trajectory;
- independently validated episode and state proposals;
- atomic and idempotent semantic commit.

Out of scope:

- temporal admissibility and `InformationSet I_t`;
- target maturity and `TrainingSample S_t`;
- feature, model, and backtest machinery;
- real protected data;
- real provider authentication;
- slow memory learning;
- production storage.

## Failure modes

- raw observation mutates durable state;
- active research episode disappears from the next context;
- context uses trajectory transcript as state;
- state commit occurs on every tool result;
- capability self-reports false authoritative provenance;
- combined validation leaves a half-committed semantic boundary;
- retry duplicates a scientific commit;
- reused idempotency key hides a changed semantic request;
- unresolved task semantics are silently invented.

## Tests and evals first

1. Arrow 1 contract tests.
2. Arrow 2 initialization coherence tests.
3. Multi-turn inspection scenario: observation enters `ResearchEpisode`, not `ResearcherState`.
4. Context reconstruction after synthetic provider-context loss.
5. Harness provenance reflects actual authorized access.
6. Exact successful idempotency replay does not duplicate a scientific commit.
7. Reused idempotency key with changed semantic payload returns `IDEMPOTENCY_CONFLICT`.
8. Failed combined validation commits neither episode nor state change.
9. Independent sessions for the same task remain independent.
10. The full acceptance scenario in `MILESTONE_1_RUNTIME_DESIGN.md`.

## Implementation steps

### Execution discipline for every increment

For each numbered increment:

1. Write the smallest test that exposes the next required behavior.
2. Run it and confirm it fails for the intended reason.
3. Implement only enough behavior to satisfy that test.
4. Run the focused test.
5. Run all previously completed Milestone 1 tests.
6. Refactor only while the completed set remains green.
7. Record any genuine specification contradiction before proceeding.

Do not write all tests first and all implementation later. Each increment is a narrow
red-green-refactor slice that leaves the repository coherent.

### Increment 0 - Bootstrap one executable quality path

**Purpose:** Establish a minimal Python environment in which every later contract can be driven by a
test.

**Write first:**

- one smoke test that imports the single source package;
- one trivial typed surface only if needed to prove runner and checker wiring.

**Implement only:**

- Python 3.12-or-newer project metadata;
- `uv` dependency and lock configuration;
- one source package;
- `tests/contract`, `tests/unit`, `tests/integration`, and `tests/behavioral`;
- `pytest`;
- Ruff formatting and linting;
- strict basedpyright configuration once the first public type exists;
- canonical commands in `AGENTS.md`.

Do not create future scientific packages, a plugin framework, database configuration, application
server, or deployment scaffold.

**Pass before continuing:** the environment resolves from a clean checkout, the smoke test passes,
and formatting, linting, and strict typing pass for the bootstrap surface.

### Increment 1 - Compile UserMandate into ResearchTask

**Purpose:** Implement Contract 001 as the first real arrow.

**Write failing contract tests first:**

- explicit objective, target, horizon, dataset reference, and constraints are preserved;
- original mandate remains recoverable;
- missing horizon produces `PARTIALLY_RESOLVED` with an unresolved field;
- explicit target is not replaced by another available field;
- material rescope creates a new task version;
- hypothesis change does not create a new task;
- compilation performs no model call, mutation, research, or protected access.

Use the acceptance scenario's explicit mandate as the happy-path fixture.

**Implement only:**

- the minimum typed mandate, task, compilation result, status, and compiler behavior;
- stable identities and lineage required by these tests;
- explicit failures from the approved Milestone 1 vocabulary.

Do not implement autonomous clarification.

**Invariants:** I10 and I24.

### Increment 2 - Initialize session, state, and episode

**Purpose:** Implement Contract 002 and establish their canonical separation.

**Write failing contract tests first:**

- one task and environment snapshot produce one session, state version 0, and `ACTIVE`
  `ResearchEpisode`;
- initialization makes no model call;
- state begins with mission orientation and no invented finding or exposure;
- episode contains the initial objective, question, plan position, and starting state version;
- two sessions for the same task receive independent state and episode identities;
- mismatched task, session, state, episode, or environment references are rejected.

**Implement only:**

- minimum typed records for session, state, episode, lifecycle status, and initialization result;
- narrow read interfaces and in-memory persistence for current state and episodes;
- no production transaction abstraction yet.

**Invariants:** I9, I10, and I24.

### Increment 3 - Reconstruct ContextPacket from stores

**Purpose:** Prove that provider context is a derived working surface rather than the system of
record.

**Write failing tests first:**

- current task, state, active research episode, environment, permissions, warnings, and references
  appear in the packet;
- full trajectory does not appear as durable state;
- inaccessible evidence is not surfaced;
- provider transcript can be deleted and an equivalent packet rebuilt;
- current versions beat superseded interpretations;
- a missing active research episode causes an explicit failure.

**Implement only:**

- minimum `ContextPacket`, context input view, and `ContextBuilder`;
- deterministic ordering and bounded fields required for stable tests;
- no semantic search, token-ranking algorithm, or general compaction system.

**Invariants:** I14-I16 and I20.

### Increment 4 - Normalize scripted model responses into typed actions

**Purpose:** Establish a provider-neutral action-request boundary.

**Write failing provider and action tests first:**

- a scripted response becomes either `InspectDatasetAction` or
  `ProposeEpisodeTransitionAction`;
- provider-native response objects do not escape normalization;
- unknown action, invalid arguments, missing identity, and mismatched session or episode fail safely;
- `PROVIDER_UNAVAILABLE` is structured and recoverable according to policy;
- retrying a provider call does not itself execute an action.

**Implement only:**

- neutral `ModelProvider` and `ModelResponse` contracts;
- deterministic `ScriptedModelProvider`;
- the two approved typed actions and common action envelope;
- no real provider, authentication, generic plugin registry, or broad event enum.

**Invariant:** I20.

### Increment 5 - Execute inspect_dataset through authority and provenance

**Purpose:** Add the first real read-only capability as an authorized vertical path.

**Write fixture and failing tests first:**

- deterministic 12-to-24-row monthly dataset with stable semantic field IDs;
- one publication delay and one missing predictor;
- authorized dataset inspection succeeds;
- unknown reference returns `NOT_FOUND`;
- unauthorized reference returns non-retryable `AUTHORITY_DENIED` without leaking values;
- selected fields and preview bounds are enforced;
- source data is unchanged;
- entire data is not inserted into the observation;
- capability self-reported provenance cannot override actual access metadata;
- controlled failure returns a safe structured error and diagnostic artifact reference.

**Implement only:**

- toy dataset and minimal descriptive schema;
- `AuthorizedDataView` and minimum capability policy;
- `ActionRouter` support for `InspectDatasetAction`;
- `inspect_dataset`;
- `CapabilityExecutionResult`;
- harness provenance assembly;
- `StructuredObservation`;
- in-memory `ArtifactStore` and append-only `TrajectoryStore` behavior required by this path.

Do not filter by `available_at`, build `InformationSet I_t`, or claim temporal legality.

**Invariants:** I9, I14, I18, and I24.

### Increment 6 - Advance one autonomous inspection turn

**Purpose:** Join context, provider, routing, capability execution, observation, episode progression,
and trajectory behind the primary runtime seam.

**Write failing integration tests first:**

- `advance_one_turn` builds current context and sends it to the scripted provider;
- inspection executes once through the authorized path;
- the observation appends to `ResearchEpisode`;
- `ResearcherState` remains unchanged at version 0;
- action, authorization, execution, provenance, and observation events append in causal order;
- the next packet contains relevant working evidence;
- failed or rejected actions remain in trajectory and produce a repairable observation when allowed.

**Implement only:**

- orchestration required for one turn;
- centralized progression authority in the runtime;
- narrow store writes owned by the runtime path;
- explicit per-turn limits required to keep execution bounded.

Providers, router, capability, and provenance machinery receive no independent writable state-store
handles.

**Invariants:** I9, I15, I20, and I25.

### Increment 7 - Validate episode and state proposals independently

**Purpose:** Preserve
`EpisodeTransitionProposal != StateUpdateProposal`.

**Write failing deterministic and adversarial tests first:**

- `ACTIVE` may transition to `RESOLVED`, `ABANDONED`, or `SUSPENDED`;
- a terminal episode cannot transition again;
- lifecycle-only transition is accepted only when state-proposal absence is explicit;
- transition proposal never synthesizes a state delta;
- state proposal checks starting version, mission identity, evidence existence and authority,
  supersession, and forbidden harness-owned fields;
- stale version returns `STALE_STATE_VERSION`;
- missing or unauthorized evidence returns `INVALID_EVIDENCE_REFERENCE`;
- validators perform no persistence.

**Implement only:**

- both proposal types, validation results, and both validators;
- no commit behavior yet.

**Invariants:** I9, I10, I13, I14, I16, and I24.

### Increment 8 - Commit atomically and idempotently

**Purpose:** Make one semantic boundary safe against partial persistence and retries.

**Write failing tests first:**

- valid lifecycle-only request commits only the episode transition;
- valid combined request commits episode and state exactly once;
- either required validation failure commits neither effect;
- persistence failure exposes no half-committed state;
- exact successful replay returns the original `CommitResult`;
- exact replay creates no new state version, transition, or scientific commit event;
- key reuse with changed status, synthesis, state delta, or evidence returns
  `IDEMPOTENCY_CONFLICT`;
- concurrent or in-progress exact requests converge on one result;
- in-progress key reuse with changed payload conflicts;
- commit and rejection attempts remain observable in trajectory.

**Implement only:**

- `CommitRequest`, semantic payload identity, `CommitResult`, and `CommitCoordinator`;
- one narrow Milestone 1 persistence transaction that atomically publishes:
  - episode transition;
  - optional state version;
  - successful idempotency result;
  - scientific commit event;
- an in-memory implementation with the smallest lock or copy-on-write mechanism proving the
  contract.

The transaction is a persistence port beneath the coordinator, not a domain type or production
database decision. Reads may remain through the named logical stores.

**Invariants:** I9, I10, I13, I24, and I25.

### Increment 9 - Return repairable commit failures to the loop

**Purpose:** Let invalid proposals be corrected without corrupting state or ending the session.

**Write the repair companion first:**

- invalid evidence leaves episode `ACTIVE` and state at version 0;
- structured rejection observation appends to the episode;
- rejection event appends to trajectory;
- next context explains the repairable error without raw diagnostics;
- corrected proposal with a new idempotency key can succeed;
- authority-forging proposal receives hard `AUTHORITY_DENIED` and does not mutate or silently
  terminate the session.

**Implement only:**

- conversion from validation and commit failures to structured model-facing observations;
- minimum runtime branching needed to continue repairable work.

Do not create a universal retry policy.

**Invariants:** I9, I14, I17, and I25.

### Increment 10 - Run the complete deterministic episode

**Purpose:** Make the acceptance scenario the first whole-organism integration test.

**Write or complete the acceptance test first:**

1. Compile the explicit mandate.
2. Initialize session, state, and episode.
3. Scripted provider requests inspection.
4. Authorized capability returns bounded evidence with harness provenance.
5. Observation updates episode but not state.
6. Context is rebuilt and provider proposes the semantic boundary.
7. Validators approve independent proposals.
8. Coordinator commits atomically.
9. Episode becomes `RESOLVED`.
10. State becomes version 1 with only evidence-backed understanding.
11. Trajectory contains the complete causal history.

Run exact-replay, changed-payload conflict, repair, independent-session, and context-loss companions
beside the happy path.

**Implement only:**

- `run_until_terminal` with action, turn, time, and resource limits;
- composition of already-tested seams;
- a human-readable deterministic trace using the same public path.

Do not add a UI, real model, or temporal scientific operations.

**Invariants:** I9, I10, I14-I16, I20, I24, and I25.

### Increment 11 - Close the Milestone 1 gate

**Required evidence:**

- every contract, adversarial, integration, and deterministic behavioral test passes;
- formatting, linting, and strict typing pass;
- acceptance trace runs from a clean environment;
- every failure-matrix row has a test or permitted deferral;
- no Milestone 2 legality claim appears in code, test names, or docs;
- canonical commands and documentation match what exists;
- discovered failures become regression tests before fixes.

No real provider integration begins until this gate passes.

## Verification commands

Phase 0 establishes:

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
```

Focused development runs the narrowest relevant test first, then all completed Milestone 1 tests.
The final acceptance command is:

```bash
uv run pytest tests/integration/test_milestone_1_acceptance.py -q
```

Phase 0 may adjust exact spelling for selected tool versions, but must update `AGENTS.md`, this
plan, and CI together. Commands must work from a clean checkout.

## Done when

A deterministic scripted model can run the complete Milestone 1 acceptance scenario, use the real
read-only dataset capability, preserve the state and episode boundary, commit atomically and
idempotently at a semantic boundary, and pass all specified contract, adversarial, integration, and
behavioral tests.

## Spec changes discovered

Record any genuine contradiction before changing tests or implementation. Cheap local representation
choices do not belong here.
