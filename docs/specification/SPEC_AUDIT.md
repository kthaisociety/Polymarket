# Specification Audit

Audit date: **2026-08-12**

Purpose: verify that this Codex handoff is a faithful durable representation of the accumulated Time-Series Research Agent design before implementation begins, and distinguish genuine omissions from choices intentionally deferred to implementation.

This audit is **not** a claim that every low-level API/class has been designed. The architecture deliberately stops short of exhaustive micro-specification. The goal is to ensure that the scientific meaning, autonomous runtime, authority model, state/context semantics, evidence governance, testing philosophy, and known high-risk contracts are not trapped only in prior conversation.

## 1. Audit basis

The package was checked against the accumulated project design record, including the decisions that were repeatedly marked locked during architecture work:

- generic time-series research kernel rather than domain-specific kernels;
- autonomous harness-owned research loop;
- provider-neutral replaceable model boundary;
- temporal/availability semantics and six scientific axioms;
- dataset/target/feature/model/predictive-system ontology;
- research/development/protected-evidence promotion funnel;
- default decision-time refit semantics;
- backtest/evaluator/validator/report separation;
- protected exposure/trial ancestry;
- AI authority map, ResearchSandbox, tool/action philosophy, and structured observations;
- `Trajectory` vs active research episode vs `ResearcherState`;
- semantic state commits rather than tool-result-to-belief mutation;
- broad machine-accessible knowledge with selective reconstructible context;
- slow validated Memory/Skill learning;
- explicit failure/recovery/versioning rules;
- top-down architecture + bottom-up implementation;
- tests as executable scientific/architectural specifications;
- deliberate avoidance of exhaustive pre-code micro-specification.

## 2. Files reviewed individually

Every Markdown file present in the original handoff was read and cross-checked for responsibility, duplication, contradiction, and missing locked decisions.

| File | Audit role | Status |
|---|---|---|
| `README.md` | Reading order / source-of-truth hierarchy | reviewed, updated |
| `AGENTS.md` | Codex durable repo instructions | reviewed, updated |
| `ARCHITECTURE.md` | End-to-end topology and loops | reviewed, updated |
| `DECISIONS.md` | Locked vs deferred design record | reviewed, updated |
| `INVARIANTS.md` | Non-negotiable executable semantics | reviewed, updated |
| `TEST_STRATEGY.md` | Test/eval architecture | reviewed, updated |
| `SCIENTIFIC_KERNEL.md` | Time-series scientific machinery | reviewed, updated |
| `BACKTEST_AND_EVALUATION.md` | Protected evidence / evaluation / validation / reporting | reviewed, updated |
| `STATE_CONTEXT_AND_MEMORY.md` | State, episode, context, retrieval, compaction, slow learning | reviewed, updated |
| `AUTHORITY_SANDBOX_AND_TOOLS.md` | AI authority, sandbox, actions, observations, failures | reviewed, updated |
| `MODEL_PROVIDER.md` | Autonomous runtime/provider boundary | reviewed; no semantic correction required |
| `META_TESTS.md` | First-principles architecture heuristics | reviewed; no semantic correction required |
| `OPEN_QUESTIONS.md` | Intentionally deferred choices | reviewed, updated |
| `IMPLEMENTATION_PLAN.md` | Bottom-up build sequence | reviewed, updated |
| `PLANS.md` | Execution-plan template / first vertical slice | reviewed; no semantic correction required |
| `CODEX_WORKFLOW.md` | Day-to-day Codex working protocol | reviewed, updated |
| `HANDOFF_CHECKLIST.md` | Coverage checklist | reviewed, updated |
| `docs/specification/contracts/README.md` | Contract-writing threshold | reviewed; no semantic correction required |
| `docs/specification/contracts/001-user-mandate-to-research-task.md` | Initial task contract | reviewed; consistent |
| `docs/specification/contracts/002-runtime-initialization.md` | Initial runtime/session contract | reviewed; consistent with medium-fidelity/no-overdesign stance |

This audit file is new and therefore was not part of the original handoff count.

## 3. Corrections made during this audit

The first handoff was broadly coherent, but several previously discussed details were only implicit or absent. They are now explicit.

### 3.1 Domain layer

Added explicit prohibition on introducing either `DomainAdapter` **or `DomainResearchSpec`** by default. Insurance, Polymarket, macro, etc. remain different `ResearchTask`s over the same kernel unless genuinely domain-exclusive machinery earns a separate extension.

### 3.2 Decision-time refit semantics

Added the distinction between:

- newly released predictor information, which changes `I_t`; and
- newly matured labels/outcomes, which changes `S_t`.

They are independent temporal changes and must not be represented as one generic "new data" event.

### 3.3 Simulation clock stance

Added the earlier decision that decision times must be explicit, while a heavyweight `SimulationClock` class is not required. A scenario-provided ordered sequence is sufficient until richer clock semantics prevent a real failure.

### 3.4 AFML / trial-aware evidence

Added explicit PSR/DSR wording alongside the existing DSR-like/multiple-testing discussion. Trial ancestry/count is always important; PSR/DSR or related corrections remain optional and task-justified rather than universal kernel requirements.

Also made explicit that protected backtesting is evidence generation, not a feature-selection/research tool.

### 3.5 ResearchLedger / EvidenceStore terminology

Clarified that `ResearchLedger` is the canonical append-only evidence/history responsibility in this handoff. An implementation may call or split part of this role into an `EvidenceStore` for a concrete reason, but the architecture does not require two near-duplicate abstractions.

### 3.6 ResearchSandbox conceptual roles

Made the previously discussed conceptual responsibilities explicit:

- `AuthorizedDataView`;
- `CapabilityPolicy`;
- `ProvenanceRecorder`;
- `ResourceLimits`;
- `ArtifactStore`;
- `StructuredReturn` / `AnalysisResult` role.

These are responsibilities, not mandatory one-class-per-name requirements.

### 3.7 Structured failure drill-down

Added the rule that model-facing failures should be typed/concise, while raw traceback/stdout/stderr remain available through drill-down/artifact references. Added an adversarial test fixture for this behavior.

### 3.8 Episode decision status

Made explicit that an active research episode may surface a `NOT_YET_RESOLVED`-style decision status while required checks remain, preventing premature semantic commits without restricting exploratory reasoning.

### 3.9 Context budgeting

Made explicit that context budgeting should use semantic priority classes rather than rigid percentage allocations. Exact token thresholds remain empirical/deferred.

### 3.10 Report shape nuance

Restored the product intent that a concise one-page research view is a useful default, while preserving the later locked decision that report presentation/style remains AI-driven and is not part of scientific validation.

### 3.11 Tests added to the specification

Added explicit fixtures for:

- predictor-release vs label-maturity independence;
- structured-error/raw-traceback drill-down.

Added invariant `I26` for independent predictor-availability and target-maturity boundaries.

## 4. Cross-document consistency checks

The package was checked for the following contradictions. None remain in the audited version.

- No document makes insurance/finance a separate kernel by default.
- No document requires a `DomainAdapter`/`DomainResearchSpec` layer.
- No document makes Codex/Claude Code the irreplaceable outer runtime.
- No document requires human confirmation for ordinary autonomous research actions.
- No document allows `reference_time` alone to establish data admissibility.
- No document allows fitting during default `predict()`.
- No document allows protected evidence to be reused as fresh after exposure.
- No document allows in-place frozen-system mutation.
- No document allows raw tool observations to mutate durable state directly.
- No document makes the protected backtest an ordinary iterative tuning fold.
- No document makes one scalar metric the canonical evaluation representation.
- No document permits formal silent fallback unless predeclared.
- No document treats rejected evidence as deletable history.
- No document makes report wording authoritative over `ValidatedFinding`.
- No document makes conversation/provider transcript the scientific source of truth.

## 5. Locked coverage map

### Product identity and autonomy

Covered in `DECISIONS.md`, `ARCHITECTURE.md`, `MODEL_PROVIDER.md`, `AGENTS.md`.

### Scientific kernel

Covered in `SCIENTIFIC_KERNEL.md`, `INVARIANTS.md`, `BACKTEST_AND_EVALUATION.md`.

### Agent-control architecture

Covered in `ARCHITECTURE.md`, `AUTHORITY_SANDBOX_AND_TOOLS.md`, `STATE_CONTEXT_AND_MEMORY.md`, `MODEL_PROVIDER.md`.

### Evidence/governance

Covered in `BACKTEST_AND_EVALUATION.md`, `INVARIANTS.md`, `TEST_STRATEGY.md`.

### State/context/learning

Covered in `STATE_CONTEXT_AND_MEMORY.md`, `ARCHITECTURE.md`, `TEST_STRATEGY.md`.

### Test philosophy

Covered in `TEST_STRATEGY.md`, `AGENTS.md`, `CODEX_WORKFLOW.md`, `PLANS.md`, `IMPLEMENTATION_PLAN.md`.

### Design heuristics

Covered in `META_TESTS.md` and reinforced in `DECISIONS.md`/`AGENTS.md`.

## 6. Intentionally deferred — not omissions

The following remain deliberately unresolved and must **not** be guessed into architecture merely because implementation begins:

- exact Python/package/module layout;
- physical persistence/storage technology;
- detailed `ResearchSession` lifecycle enum/transaction implementation;
- exact event taxonomy;
- exhaustive tool catalog;
- exact context token budgets/retrieval thresholds;
- precise semantic-commit detection mechanism;
- exact research-graph schema;
- task-specific development-validation procedure;
- exact `EvaluationSpec` fields;
- universal multiple-testing correction formula;
- exact OpenAI subscription/API/local provider-auth implementation;
- sandbox network policy for every future task;
- UI architecture;
- fixed report visual style;
- timing/implementation of slow learning;
- non-default periodic/online refit protocols;
- domain-exclusive downstream execution/allocation modules.

These are listed more fully in `OPEN_QUESTIONS.md`.

## 7. Codex repository-instruction compatibility check

The handoff structure was rechecked against current official Codex guidance on 2026-08-12:

- root `AGENTS.md` is the durable automatically discovered repository instruction layer;
- `AGENTS.md` is intentionally concise and points to deeper architecture files;
- repository-wide `## Code Review Rules` are present in root `AGENTS.md`;
- the task prompt convention uses **Goal / Context / Constraints / Done when**;
- difficult work uses plan-first behavior and may use the repository `PLANS.md` execution-plan template;
- tests, verification, and diff review are part of completion rather than optional follow-up.

`PLANS.md` is a repository workflow document referenced by our instructions; `AGENTS.md` remains the automatically discovered durable instruction file.

## 8. Handoff acceptance criterion

This handoff is ready to give to Codex when all of the following are true:

1. Codex can summarize the architecture and reproduce the core loops without relying on old chat context.
2. Codex can identify the locked invariants and explain which tests protect them.
3. Codex can distinguish scientific/governance decisions from intentionally deferred local implementation choices.
4. A provider/model swap does not require redesigning the scientific kernel.
5. The first vertical slice can be planned from repository files alone.
6. If a future implementation contradicts a locked invariant, the repository tells the agent to surface the conflict rather than silently reinterpret it.

Recommended first Codex action after unpacking:

```text
Read AGENTS.md and README.md, then the authoritative files they reference.
Do not implement yet.
Summarize:
1. the end-to-end architecture and explicit feedback loops;
2. locked scientific/runtime invariants;
3. the four-layer testing strategy;
4. intentionally deferred decisions;
5. the first vertical-slice plan.
Flag any contradiction or ambiguity before modifying code.
```
