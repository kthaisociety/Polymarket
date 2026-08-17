# Design Decisions

This file distinguishes **locked architectural decisions** from **deliberately deferred implementation choices**.

## Product identity — LOCKED

The product is a reusable **Time-Series Research Kernel / Product**.

Core scientific objective:

\[
\boxed{\text{Given information available at }t,\text{ discover whether anything predicts }y_{t+h}.}
\]

Chronos's first live adapter is Polymarket; its originating Insurance application is recorded in
`VENDORED_FROM.md`. They use the same scientific kernel rather than separate domain kernels.

Do not introduce a separate `DomainAdapter` **or `DomainResearchSpec`** layer merely because the target/data semantics differ. The same research kernel receives a different `ResearchTask`, datasets, hypotheses, evaluation criteria, and report framing.

Meta-rule:

> Is this fundamentally different scientific machinery, or is the same research kernel simply being asked a different question over different data?

Only introduce domain-exclusive machinery when it prevents a concrete failure or supports genuinely different downstream action (for example execution/portfolio allocation after prediction).

## Human / AI ownership — LOCKED

The human owns architecture, abstraction, scientific reasoning standards, test intent, debugging understanding, and verification.

The agent may handle repetitive/mechanical execution and may autonomously perform research inside the architecture.

The intended product runtime is autonomous:

```text
human research mandate
  → autonomous harness + model
  → validated finding / rejected evidence trail
```

The human should not be on the critical path for every hypothesis, tool call, or code execution.

## Core scientific principle — LOCKED

```text
The agent generates hypotheses;
deterministic research infrastructure decides whether they survive.
```

The AI can reason freely and write its own exploratory code. Scientific identity, temporal legality, provenance, protected evidence, and promotion authority are controlled by the harness.

## Architecture / implementation strategy — LOCKED

- Full architecture: top-down.
- Implementation: bottom-up.
- Tests are a first-class design activity, not post-hoc QA.
- For critical boundaries: contract + tests before implementation.
- For low-risk plumbing: medium-fidelity responsibility first; implementation can discover exact interfaces.
- First implementation target: a complete narrow vertical slice.
- Complexity must be earned by a concrete failure mode.
- Steal useful abstractions from other agent systems, not their entire implementations.

## Test philosophy — LOCKED

Use at least four layers:

1. deterministic unit/contract tests;
2. scientific/governance invariant and adversarial tests;
3. integration/vertical-slice tests;
4. behavioral agent evals using scripted or real model runs.

Real-run failure loop:

```text
observe failure
→ identify general failure mode
→ add failing regression test/eval
→ fix
```

## Time semantics — LOCKED

Observation identity includes:

```text
(value, reference_time, available_at)
```

The admissibility condition at simulated time `t` is `available_at <= t`.

`reference_time` is not enough to determine whether information was knowable.

Every scientific horizon, target interval, feature lag/window, or other relative-time value must
declare whether it is an **elapsed duration** on the absolute timeline or a **civil-calendar
offset**. Calendar months and quarters preserve their own identities and require explicit anchor,
month-end, timezone, and DST/fold behavior. They are never normalized to 30-day months or 90-day
quarters. If a required policy is unresolved, the boundary blocks rather than choosing one.

## Dataset / feature ontology — LOCKED

- Raw time series/tables live in `Dataset` with a stable semantic schema/field registry.
- Target is a semantic view/transformation of a dataset field.
- `FeatureDefinition` is the public scientific abstraction `φ_j: D_{≤t} → z_t^(j)`.
- Internally, features may compile to a `FeatureExpression` / AST / computation graph.
- Operators are implementation representation, not the public domain abstraction.
- `FeatureSeries` is a materialization.
- `FeatureSet` is a set of definitions.
- Feature analysis is distinct from feature definition.
- Fitted transforms such as scaling/PCA must obey fold/time legality.

## Model ontology — LOCKED

```text
ModelDefinition != FittedModel != ModelSelection
```

`PredictiveSystemDefinition` is the frozen recipe containing target, feature set, model(s), ensemble, training protocol, and evaluation protocol/specification.

## Backtest semantics — LOCKED

Default deployment/backtest behavior is refit at every decision time `t`:

1. rebuild legal `InformationSet I_t`;
2. rebuild completed legal `TrainingSample S_t`;
3. select training window `W_t`;
4. fit the frozen predictive-system recipe to obtain immutable `F_t`;
5. predict using current legal information;
6. record the prediction immutably.

Keep two information changes conceptually distinct:

- **new predictor information** changes what is present in `I_t`;
- **newly matured labeled information** changes which historical rows are legally eligible for `S_t`.

They may change at different times and must not be conflated.

Decision times must be explicit in the evaluation scenario, but a heavyweight `SimulationClock` class is **not** required by the architecture. A sequence/iterator of scenario decision times is sufficient until a richer clock prevents a concrete failure.

Periodic/conditional refit is optional policy, not the default architectural center.

The outer backtest is not the same as inner model-selection validation.

`predict()` never learns.

## Evaluation / validation — LOCKED

```text
BacktestEngine: What happened?
Evaluator: How is it measured?
Validator: Does it meet the predeclared scientific promotion standard?
```

`BacktestRun` is an immutable simulation record, not a performance report.

`Validator` is a binary scientific promotion gate (`accept/reject`), not an economic trading decision.

A downstream human/PM/domain decision maker may decide whether a scientifically promoted result is economically useful.

## Reporting — LOCKED

`ValidatedFinding` is the immutable scientific substance. `ReportBuilder` may use AI freely for presentation/layout/wording.

A concise one-page human-facing research view is a useful default product target, but it is **not** a scientific invariant or fixed style guide.

Presentation must not change or overstate:

- evidence;
- caveats;
- provenance;
- validation status;
- scientific conclusion.

## AI authority — LOCKED

Four zones:

1. **Free reasoning** — understand, hypothesize, diagnose, plan, propose.
2. **Constrained execution** — AI requests or writes computation; harness restricts data/side effects and checks invariants.
3. **Privileged operations** — AI may request but cannot self-authorize protected backtest, scientific promotion, or memory/skill promotion.
4. **Forbidden direct authority** — no direct protected-holdout access, ledger rewrite, completed-run mutation, direct lesson promotion, or in-place mutation of a frozen scientific spec.

Key formulation:

```text
AI owns research intent and may author local computation.
Harness owns what information that computation can see,
its execution boundary, and whether its output is admissible.
```

## ResearchSandbox — LOCKED

The sandbox should feel like a powerful Python scientific research environment, conceptually:

```text
powerful computation
× restricted information domain
× restricted side effects
```

AI-written exploratory code is encouraged. The sandbox controls authorized data views, side effects, resources, provenance, and artifact storage.

## Action/tool space — LOCKED

Prefer a small deep action space:

- research/hypothesis state actions;
- open-ended `run_analysis` / code sandbox;
- formal feature/model/system construction;
- common deterministic scientific analyses with typed outputs;
- privileged `request_*` operations for protected/final transitions.

Tools assist exploration; gates enforce standards.

## Structured observations — LOCKED

Tool results should return typed decision-relevant scientific observations, not only "success" or massive stdout.

Numbers must include semantic context (sample size, temporal window, stability, warnings, etc.) and artifact references for drill-down.

Summaries are progressive disclosure, not lossy prisons.

## Escalating epistemic gates — LOCKED

```text
Exploration
→ Candidate
→ Research-Validated
→ Frozen
→ Protected Backtest
→ Promoted Finding
```

Freedom decreases and evidentiary burden increases as a candidate moves through the funnel.

The actor benefiting from approval cannot grant the privileged approval.

## Research loops — LOCKED

Do not model research as a false linear pipeline.

Fast loop:

```text
plan → act → observe → revise plan → act again
```

Important loops:

- data-understanding loop;
- hypothesis/feature falsification loop;
- model/system development loop;
- protected-evidence boundary that intentionally breaks ordinary iterative reuse;
- slow cross-task learning loop through reflection and validated memory/skills.

Every scientific observation may update the current `ResearchEpisode`, but not every observation may be reused as fresh validation evidence.

## State/context architecture — LOCKED

`R_t != C_t`: durable `ResearcherState` is not model context. `S_t` remains reserved for the
completed legal `TrainingSample`.

Three-layer state model:

1. `Trajectory` — complete action/observation history.
2. `ResearchEpisode` — unresolved investigation, intermediate evidence, plan, temporary interpretations, artifacts.
3. `ResearcherState` — committed resumable intellectual/operational position.

Critical rule:

```text
tool result != belief update
```

Durable state changes only at semantic commit boundaries.

Use deltas and supersession rather than rewriting intellectual history.

## Context / knowledge — LOCKED

Context is managed working memory, not transcript.

```text
Context = CoreInstructions
        + ResearcherState
        + ResearchEpisode
        + RelevantEvidence
        + current permissions/warnings
```

Use broad machine-accessible knowledge with selective working context.

```text
Keep reasoning surface narrow while accessible knowledge surface extremely broad.
```

Prefer structural retrieval when explicit IDs/lineage exist; use semantic/search retrieval when relationships are uncertain.

Compaction should create structured episode checkpoints and rebuild context. It must not delete underlying trajectory/evidence.

## Storage boundaries — LOCKED logically, DEFERRED physically

Logical stores:

- ResearcherState store;
- ResearchEpisodeStore;
- TrajectoryStore;
- ArtifactStore;
- ResearchLedger (the canonical append-only evidence/history role; an implementation may call or split part of this role into an `EvidenceStore`, but do not create both without a concrete need);
- DataCatalog/DataStore;
- KnowledgeEnvironment;
- validated Memory/Skills.

Physical technology (Postgres, files, object store, etc.) is deferred.

## Failure semantics — LOCKED

1. exploratory operational failures: agent-recoverable;
2. formal scientific failures: explicit typed failure; if repair changes scientific meaning, create a new version/candidate;
3. governance failures: hard deny, with reasoning-friendly explanation.

No silent fallbacks in formal scientific machinery unless predeclared/frozen.

## Model provider/runtime — LOCKED architecture, DEFERRED provider implementation

The research harness owns the autonomous loop. The model is a replaceable provider behind a neutral interface.

Do not make Codex itself the irreplaceable outer architecture.

Potential providers include OpenAI subscription-auth mechanisms where legitimately supported, OpenAI API, and local/other providers. Exact auth transport is an implementation/integration concern and must follow supported provider behavior rather than being guessed.

## Initial contract decisions — LOCKED at medium fidelity

Arrow 1:

```text
UserMandate → TaskCompiler → ResearchTaskProposal
→ human readback and exact confirmation → ResearchTask
```

`ResearchTaskProposal` formalizes the mandate for review but carries no authority to begin research.
`ResearchTask` is created only from the exact proposal confirmed by the instruction giver. Material
task-level rescoping creates a new version; subordinate questions, hypotheses, targets, horizons,
and methods may evolve autonomously while the confirmed main goal and hard constraints remain
intact. Missing semantics remain unresolved rather than being invented. Broad discovery is not
completed by the first positive candidate.

Arrow 2:

```text
ResearchTask + ResearchEnvironment
→ ResearchRuntime.initialize
→ ResearchSession + ResearcherState_0 + ResearchEpisode_0
```

Initialization creates a coherent research execution context without doing research or touching protected evidence. Exact class/status mechanics remain implementation-level.

## Explicit non-goals / things not to force

- No `DomainAdapter` architecture by default.
- No AFML machinery merely because the use case is finance-like.
- No heavyweight refit scheduler as a central abstraction without a real need.
- No hundreds of narrow tools when open-ended analysis plus typed common operations suffice.
- No transcript-as-state architecture.
- No context design that permanently discards knowledge merely because a human could not process it.
- No scalar-only evaluation as the canonical representation of system behavior.
- No over-specified class taxonomy before implementation evidence exists.

## Deferred decisions

The following should be decided during implementation unless a concrete failure mode makes them architectural:

- programming package/module layout;
- exact persistence technologies;
- exact class/method names below canonical domain objects;
- internal event enum details;
- exact session-status enum;
- exact serialization framework;
- exact scientific Python library list;
- whether selected helpers are classes, pure functions, or services;
- UI/report visual design;
- deployment/CI infrastructure;
- exact provider-auth implementation.
