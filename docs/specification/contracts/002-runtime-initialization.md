# Contract 002 — Research Runtime Initialization

Status: **LOCKED at high-risk semantic fidelity by global seam runtime.initialize-research**

Canonical detailed contract:
[`../../architecture/runtime/transitions/initialize-research.md`](../../architecture/runtime/transitions/initialize-research.md).

## Arrow

```text
ResearchTask + ResearchEnvironment
→ ResearchRuntime.initialize
→ ResearchSession + ResearcherState_0 + ResearchEpisode_0
```

## Why the session concept exists

`ResearchTask` is the scientific problem.

`ResearchSession` is one concrete autonomous attempt/execution of that problem.

The same task may be researched in independent sessions under different environments/models/harness versions without changing task identity.

## Responsibility

Place an autonomous researcher into a coherent initial state with a mandate, legitimate environment/capability reference, and first active research episode.

Initialization is infrastructure/orientation. It must not perform scientific research yet.

## Inputs

### ResearchTask

The human-confirmed, versioned scientific mission from Contract 001. A `ResearchTaskProposal` cannot initialize the runtime.

### ResearchEnvironment / snapshot

Conceptually includes/references:

- available dataset/catalog refs;
- tool/capability metadata;
- compute capabilities;
- permissions;
- protected-resource metadata without contents unless explicitly authorized;
- environment/version identity.

Exact shape is deferred.

## Outputs

### ResearchSession

Distinct execution identity linking task, initial environment, current state/episode refs, runtime/model configuration as needed.

### ResearcherState_0

Must contain orientation, not invented scientific findings.

Conceptually:

```text
mission/goal from ResearchTask
no committed scientific findings yet
empty explored-path history
initial current focus/orientation
environment ref
epistemic position: no protected exposures/gates falsely passed
```

### ResearchEpisode_0

Active initial investigation, broad enough to let the model orient and formulate the first real research plan.

If task fields are unresolved, the episode should preserve/foreground those unresolved questions.

## Invariants

1. Initialization does not call the model as part of deterministic setup unless later implementation demonstrates a compelling architectural need and tests are updated.
2. Initialization does not generate scientific hypotheses/findings on behalf of the researcher.
3. Unresolved task semantics remain unresolved.
4. Protected evidence contents are not accessed.
5. Initial epistemic state contains no fabricated gate/exposure history.
6. Same task can produce multiple independent sessions.
7. Historical environment identity is referenced, not silently replaced by later environment changes.
8. Session/state/episode must be coherent; no healthy active session may exist with missing required initial state/episode.

## State effects

Allowed:

- create session identity;
- create initial durable state;
- create active research episode;
- emit runtime/trajectory initialization events.

Forbidden:

- mutate task;
- create scientific evidence/finding;
- expose protected data;
- pass backtest/promotion gates;
- write cross-task memory/skills.

## Failure semantics

Initialization failure must be explicit and must not leave a session that later appears healthy while required state/episode objects are missing.

Exact transactional mechanism is implementation-level.

## Acceptance tests

### T002.1 — coherent normal initialization

Resolved task + valid environment.

Expected: independent active session, state version 0, active research episode, no scientific findings/exposures.

### T002.2 — no manufactured beliefs

Environment contains plausible predictors CPI/GDP/etc.

Expected: initial committed understanding does not assert they are predictive before model/research action.

### T002.3 — unresolved stays unresolved

Task horizon unresolved.

Expected: initial state/episode preserves unresolved horizon; no default silently inserted.

### T002.4 — same task, independent sessions

Initialize same task twice.

Expected: distinct session/state/episode identities and no cross-session working-state contamination.

### T002.5 — protected metadata without protected read

Environment exposes fact that holdout H exists but not content permission.

Expected: initialization may preserve metadata/ref as needed, but reads zero protected values and changes no exposure state.

### T002.6 — environment reference provenance

Initialize under E1; later environment E2 exists.

Expected: historical initialization remains tied to E1; later state may explicitly move to E2 through a legitimate update.

### T002.7 — epistemic zero state

Expected: no gates passed, no protected exposures, stage/orientation state appropriate to new research attempt.

### T002.8 — coherent failure

Simulate persistence failure during initialization.

Expected: no valid active half-session that can be resumed as if healthy.

### T002.9 — deterministic setup does not invoke provider

Use mocked provider.

Expected: model/provider call count remains zero during infrastructure initialization.

## Meta-test

> If the LLM had not yet produced a single token, could we completely explain the researcher's starting position?
