# mission.confirm-task — UserMandate + environment metadata + human confirmation → ResearchTask

Status: **LOCKED — readiness level 4 of 5**

mission.confirm-task formalizes the human's research idea, reads the proposed mission back to that human, and
creates an authoritative `ResearchTask` only after confirmation of the exact proposal reviewed.
This contract refines Contract 001 and the Milestone 1 task-compilation seam.

## Purpose

Create a durable, faithful, actionable research mission without prematurely freezing the later
scientific experiment or allowing the compiler to authorize its own interpretation of human intent.

If mission.confirm-task changes a discovery question into a one-result search, substitutes a target, hides
uncertainty, or starts a different proposal than the human reviewed, every downstream component can
work correctly while researching the wrong problem.

## Relevant locked invariants

- **I10 — Mission cannot silently drift.** Material target, horizon, objective, or research-identity
  changes require explicit task respecification/versioning.
- **I24 — Environment identity is explicit.** Later environment/schema changes cannot retroactively
  alter the task meaning confirmed by the human.
- **Human/AI ownership.** The human owns the initial mandate; the autonomous agent owns ordinary
  research after the mission is confirmed.

## Source A

mission.confirm-task receives:

1. **`UserMandate`** — the exact human request and any explicit objective, target concept, horizon,
   research mode, geography, time scope, seed sources, constraints, preferences, and stopping
   expectations.
2. **Versioned environment/schema metadata** — metadata sufficient to resolve named resources and
   stable semantic identities when resolution is unambiguous. It may reveal that protected
   resources exist but does not expose protected values.
3. **Human review decisions** — confirm the exact proposal, request changes, reject it, or provide
   clarification.

Dataset values, protected evidence, research findings, provider transcripts, and mutable research
state are not mission.confirm-task inputs.

## Destination B

The authoritative destination is a human-confirmed `ResearchTask`: the versioned mission that may
be passed to runtime initialization.

Before confirmation, compilation produces a `ResearchTaskProposal`, not a `ResearchTask`. Its
human-readable readback and structured semantics include:

- original mandate and formalized mission;
- objective mode: discovery, confirmation, comparison, falsification, evaluation, or another
  explicit mode;
- target concept and any resolved target reference;
- intended relationship, such as association versus predictive power;
- geography/time scope;
- seed hypotheses/resources, separated from hard constraints;
- assumptions and metadata-backed resolutions;
- actionable unresolved semantics and blocking clarification questions;
- completion expectations and required stopping account;
- environment/schema and compilation provenance;
- proposal identity/version sufficient to bind confirmation to the exact reviewed semantics.

The proposal may be complete, actionable with unresolved formal details, blocked on mission
clarification, or unresolvable. Exact enum names are implementation choices.

## Mapping f

```text
UserMandate + EnvironmentMetadata
    → faithful ResearchTaskProposal
    → human-readable readback
    → human confirms exact proposal identity/version/semantics
    → authoritative ResearchTask
```

If the human edits, rejects, or clarifies:

```text
ResearchTaskProposal
    → human feedback
    → revised proposal with new identity/version
    → new readback
    → new confirmation decision
```

mission.confirm-task may preserve, structure, unambiguously resolve from authoritative metadata, classify
unresolved meaning, request clarification, reject invalid input, and publish a confirmed task. It
may not research, speculate, silently complete meaning, or treat compiler output as human authority.

## Must preserve

- the exact original mandate in recoverable form;
- all explicit objective, target, horizon/unit, relationship type, geography/time scope,
  development/evaluation objective, and other scientific meaning;
- for any resolved horizon, elapsed-versus-calendar kind and the exact anchor, month-end, timezone,
  and DST/fold policy; calendar months/quarters never become 30/90 elapsed days;
- association/correlation versus predictive power;
- seed suggestions/preferences versus hard constraints;
- blocking mission ambiguity versus researchable uncertainty;
- unresolved scientific semantics without arbitrary defaults;
- objective mode and breadth;
- for broad discovery, that one positive candidate does not satisfy the task;
- bounded exhaustion: terminal resolution requires an account of what was searched, tested,
  rejected, surviving, inaccessible, and materially untested, and why no remaining high-priority
  path within the maintained research map, authorized resources, scientific checks, and configured
  limits is expected to change the bounded conclusion;
- stable metadata-backed identities and the environment/schema version used;
- assumptions, resolutions, proposal lineage, confirmation provenance, and task lineage;
- exact semantic identity between the reviewed proposal and confirmed task.

Preservation is semantic. No specific class library, UI, digest algorithm, serialization, or
storage system is required.

## May transform

- natural language into concise structured fields and readable prose;
- unambiguous names into stable metadata-backed references;
- human corrections into a new proposal version;
- actionable partially specified missions into confirmable proposals whose unresolved formal
  semantics remain explicit.

Compiler interpretations must be exposed in the readback. Human confirmation, not compiler
confidence, makes them authoritative.

## Must exclude

- invented/defaulted target, horizon, prediction type, alignment, maturity, source scope, success
  criteria, or evaluation goal;
- nearby field/dataset substitution;
- correlation silently changed into prediction, or the reverse;
- seed sources silently changed into exclusive scope;
- broad discovery silently changed into “find one positive result”;
- hypotheses, evidence, findings, formal objects, or gate status presented as already researched;
- datasets/values, protected contents, secrets, provider-native objects, transcripts, or writable
  runtime/scientific stores;
- hidden proposal changes between readback and confirmation;
- authority to initialize, research, expose protected evidence, backtest, promote, or learn.

## Authority boundary

- **Human:** authors the mandate and alone confirms the initial mission.
- **Task compiler:** structures meaning, performs unambiguous metadata resolution, surfaces
  assumptions/unresolved questions, and issues versioned proposals; it cannot confirm them.
- **Readback layer:** presents all decision-relevant proposal semantics and carries human feedback;
  it cannot omit meaning required for informed confirmation.
- **Task publication boundary:** verifies confirmation of the exact current proposal and creates the
  authoritative task once.
- **Runtime initializer:** may consume only a confirmed task.

Human confirmation is required for every initial task, even when the proposal appears fully
resolved. It is not required for ordinary research steps after initialization.

## Allowed state changes

- create/version proposal, readback, and provenance;
- record clarification, revision, rejection, and confirmation;
- invalidate a prior proposal when semantics change;
- publish one authoritative task for an exact confirmed proposal;
- converge on the existing task for an exact duplicate confirmation.

## Forbidden state changes

- no authoritative task before exact human confirmation;
- no session, episode, researcher state, hypothesis, evidence, finding, formal object, backtest,
  exposure, evaluation, memory, or skill creation;
- no mutation of inputs, prior proposal versions, confirmed tasks, data, or protected state;
- no provider/model call in the deterministic M1 compiler;
- no dataset/protected-value read;
- no auto-publication after readback, timeout, dismissal, or compiler confidence;
- no reuse of confirmation after proposal semantics/version changes.

On failure, no healthy authoritative task may appear.

## Failure semantics

| Condition | Required behavior | Preserved state |
|---|---|---|
| Actionable mission with open formal details | Reviewable proposal with researchable uncertainty explicit | No defaults |
| Materially different plausible missions | Require clarification; no approvable task that hides ambiguity | No task |
| Conclusively invalid metadata reference | Explicit invalid result; no substitution | Inputs/history unchanged |
| Metadata cannot resolve but does not disprove a reference | Preserve unresolved | No data-value lookup |
| Human rejects | Record rejection; create no task | Proposal/history retained |
| Human edits/clarifies | New proposal identity/version, readback, and confirmation | Prior history retained |
| Confirmation names stale/changed proposal | Explicit rejection | No task from stale authority |
| Duplicate exact confirmation | Same task/result, not a duplicate | One task |
| Confirmation identity reused for different semantics | Explicit conflict | Original unchanged |
| Partial proposal/task publication failure | No healthy task without confirmation/provenance | Coherent-or-failed |
| Protected contents would be needed | Refuse resolution or leave unresolved | No exposure |

No silent fallback may select a default horizon, nearby target, latest environment, changed proposal,
or model-authored guess.

A bare integer such as `3 months` is not executable horizon identity until its civil-calendar
policies are resolved and reviewed. The transition may preserve it as unresolved; it may not
reinterpret it as a `timedelta`.

## Observable consequences

- The instruction giver reads and understands the proposed mission before research starts.
- A proposal alone cannot initialize the runtime.
- The task exactly preserves the reviewed semantics, unresolved questions, breadth,
  seed/constraint distinction, and completion expectations.
- Materially different proposals require distinct confirmations.
- A broad-discovery first hit remains candidate evidence rather than task completion.
- Later environments cannot alter the historical confirmed task.
- rejection, revision, mismatch, and failure create no healthy task or research side effects.

## False-success implementations considered

| Attack | Convincing false success | Protection |
|---|---|---|
| Display P1, publish changed P2 | Readback and runtime each look correct | Exact proposal confirmation |
| Generic approval boolean | Works in simple UI flow | Bind confirmation to identity/version/semantics |
| Auto-publish after compile | Convenient workflow | Proposal remains non-authoritative |
| Default missing horizon | Runnable task | Explicit unresolved semantics |
| First available target wins | Plausible field exists | Exact target preservation |
| Seed becomes hard scope | Efficient narrow search | Seed/constraint distinction |
| Correlation becomes prediction | Useful-looking result | Exact relationship type |
| Discovery becomes first-hit search | Quick positive result | Breadth/exhaustion obligation |
| Latest environment resolves old task | Current run looks healthy | Historical environment identity |
| Protected values aid compilation | More precise proposal | Metadata-only authority |
| Retry creates two tasks | Both look correct | Idempotent confirmation |
| Task published before confirmation/provenance | Task initializes normally | Coherent publication |

## Falsifying tests

All mission.confirm-task tests are deterministic Level A/B tests; they do not claim autonomous model reasoning.

### mission.confirm-task-T1 — faithful formalization/readback

Given a broad mandate to find external data associated with Swedish healthcare waiting times and
seed suggestions for labour-market and sickness-absence data, assert the proposal/readback preserves
broad discovery, association rather than prediction, target concept, non-exclusive seeds,
unresolved formal details, first-hit insufficiency, bounded exhaustion, original mandate, and
provenance.

**Mutation:** treat seeds as the complete allowed scope. **Expected failure:** seed/constraint
assertions become red.

### mission.confirm-task-T2 — blocking ambiguity versus researchable uncertainty

Pair an actionable broad discovery question with open formal details against “investigate Swedish
healthcare,” which admits materially different missions. The first yields a reviewable proposal;
the second requires clarification and cannot authorize a task.

**Mutation:** classify all missing fields as blocking, or all ambiguity as researchable. **Expected
failure:** one paired outcome is wrong.

### mission.confirm-task-T3 — no task/research before confirmation

Display a valid proposal with fail-on-call runtime, provider, dataset-value, protected-data,
backtest/evaluation, and learning boundaries. Assert no task or research effect before confirmation.

**Mutation:** auto-publish after compilation. **Expected failure:** a task exists prematurely.

### mission.confirm-task-T4 — exact proposal confirmation

Display P1, produce materially changed P2, then submit confirmation for P1. Publication must reject
the mismatch. Exact confirmation of P1 in a fresh case creates a task semantically identical to P1.
The publisher has no side channel to the original mandate.

**Mutation:** check only approval boolean/title/proposal ID, ignoring version/semantic identity.
**Expected failure:** P2 is incorrectly published from P1 authority.

### mission.confirm-task-T5 — revision requires new confirmation

Edit/reject P1 to produce P2. P1 confirmation cannot authorize P2; P2 requires new readback and
confirmation. Prior proposal/feedback remains auditable.

**Mutation:** carry confirmation across edits. **Expected failure:** P2 becomes authoritative early.

### mission.confirm-task-T6 — idempotent exact confirmation

Submit exact confirmation twice, including after reconstruction over the same logical store. Both
converge on one task. Reuse confirmation identity with different semantics and require conflict.

**Mutation:** allocate a new task per confirmation call. **Expected failure:** identity/count differs.

### mission.confirm-task-T7 — historical environment identity

Confirm under E1, introduce E2, reload without recompiling, and assert task/provenance still name E1.

**Mutation:** resolve against latest environment. **Expected failure:** historical task adopts E2.

### mission.confirm-task-T8 — coherent publication failure

Inject failure between confirmation verification and task/provenance publication. No loadable
healthy task may lack confirmation/provenance; exact retry may converge after recovery.

**Mutation:** publish task first without atomic staging/rollback. **Expected failure:** half-task loads.

## Mutation-sensitivity check

**Mutation:** display P1, accept generic approval, then publish latest P2 after material change.

**Expected test failure:** mission.confirm-task-T4 becomes red because P1 confirmation cannot authorize P2. This
proves the authority-carrying arrow, not merely that proposal and task endpoints both exist.

## Composite dependencies

- **mission.evolve-direction:** later material rescope/versioning.
- **runtime.initialize-research:** initialization from confirmed task only.
- **context.build-packet/runtime.continue-from-observation/runtime.run-bounded-episode:** usable mission breadth and continued-search semantics in context/behavior.
- **target.define-outcome:** later exact `TargetDefinition` without silently filling mission.confirm-task uncertainties.

These dependencies are named, not specified or locked here.

## User decisions

The architecture owner approved:

1. Broad natural-language research questions may be actionable.
2. Structure makes the mission durable without narrowing agent freedom or freezing the experiment.
3. Seed sources are starting points unless explicitly declared constraints.
4. Researchable uncertainty may remain; blocking mission ambiguity requires clarification.
5. One positive correlation/candidate does not complete a discovery task.
6. Exhaustion is bounded by the maintained research map, authorized resources/evidence, scientific
   checks, and configured limits; terminal synthesis discloses coverage and gaps.
7. Every initial proposal is read back and explicitly confirmed by the instruction giver.
8. Confirmation binds exact reviewed semantics; every edit requires new readback/confirmation.
9. Ordinary autonomous research begins after confirmation without continuing human supervision.

## Status

**LOCKED — readiness level 4 of 5.**

Level 5 requires future executable tests and passing evidence through the real production path.
This contract and its handoff do not authorize implementation.
