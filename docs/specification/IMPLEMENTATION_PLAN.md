# Implementation Plan

## 1. Build philosophy

The architecture is designed top-down; implementation should proceed bottom-up and test-first at high-risk boundaries.

Do not build every conceptual subsystem before running the product.

Target a narrow autonomous vertical slice early, then expand based on real failures.

---

## 2. Phase 0 — repository bootstrap

Deliverables:

- choose minimal implementation language/toolchain consistent with scientific computing needs;
- package/module scaffold;
- deterministic test runner;
- behavioral-eval test location/runner;
- lint/type-check only if useful;
- canonical commands added to `AGENTS.md`;
- one trivial CI/local verification path if appropriate.

Do not add large frameworks at bootstrap.

---

## 3. Milestone 1 — minimal autonomous runtime slice

Goal: prove the agent loop/state separation works independently of scientific sophistication.

The implementation-ready contract is `MILESTONE_1_RUNTIME_DESIGN.md`.

Implement minimally:

- `ResearchTask`;
- `ResearchSession` concept as needed;
- `ResearcherState`;
- `ResearchEpisode`;
- `ContextBuilder`;
- `ModelProvider` interface;
- scripted/deterministic model provider for tests;
- `AgentAction` / action router;
- one real read-only `inspect_dataset` capability against the shared toy dataset;
- `StructuredObservation`;
- trajectory/runtime events;
- semantic state-commit path.

Vertical test:

```text
ResearchTask
→ runtime initialization
→ ContextPacket
→ scripted action A
→ observation
→ scripted action B
→ semantic resolution
→ StateUpdateProposal
→ committed ResearcherState
```

Critical checks:

- A's observation does not directly mutate durable state;
- the next context includes active unresolved work;
- commit happens once at semantic resolution;
- full trajectory remains available externally.

This milestone uses narrow logical store interfaces with in-memory implementations. Production persistence remains deferred.

---

## 4. Milestone 2 — temporal scientific data boundary

Implement:

- `DatasetSchema` / stable `FieldRef`;
- observation `reference_time` + `available_at`;
- `InformationSet` construction;
- `TargetDefinition` basics;
- `TrainingSampleBuilder`;
- `TrainingWindowPolicy`.

Required adversarial fixtures:

- publication-delay leakage;
- target maturity;
- predictor-release vs label-maturity independence;
- missing/insufficient legal sample;
- environment/schema version provenance.

Do not proceed to trusted backtesting until these invariants are strong.

---

## 5. Milestone 3 — ResearchSandbox and exploratory research

Implement minimal safe open-ended analysis:

- authorized data view;
- code execution/workspace;
- artifact storage;
- structured return/error with raw traceback/stdout/stderr preserved as drill-down artifacts rather than primary model context;
- provenance capture;
- resource/side-effect controls.

Add one or two common typed scientific tools only if they improve repeated workflows.

Behavioral eval:

- model writes analysis code;
- code fails operationally;
- model recovers;
- no durable scientific state is corrupted.

---

## 6. Milestone 4 — feature/model formalization

Implement:

- `FeatureDefinition`;
- internal feature expression representation as needed;
- feature compilation/materialization;
- fitted transform handling;
- `FeatureSet`;
- `ModelDefinition` / fitted model separation;
- `EnsembleDefinition` only if first vertical use case needs it;
- `PredictiveSystemDefinition`;
- version/lineage semantics.

Critical tests:

- formal feature cannot access unauthorized future data;
- fitted transform state is training-window scoped;
- exploratory code is not automatically a formal feature;
- material scientific changes create new versions.

---

## 7. Milestone 5 — SystemTrainer and development validation

Implement the controlled fitting boundary.

Required properties:

- all learned preprocessing/model state is fitted inside legal training data;
- `predict()` does not learn;
- inner model selection remains distinct from outer backtest;
- explicit failure when frozen training procedure cannot be executed;
- no silent fallback.

Development-validation loop can initially be simple but must preserve provenance/trial ancestry.

---

## 8. Milestone 6 — freeze + protected backtest + evaluation

Implement:

- freeze/version semantics;
- `BacktestRequest`;
- governance permit/deny;
- exposure tracking;
- `BacktestEngine`;
- immutable fit/prediction/outcome records;
- `BacktestRun`;
- `Evaluator` + task-provided `EvaluationSpec`;
- binary scientific `Validator`;
- `ValidatedFinding`;
- append-only ledger behavior.

This milestone carries the highest scientific adversarial-test burden.

---

## 9. Milestone 7 — report and real provider integration

Implement:

- flexible report builder over canonical findings;
- real model provider adapter(s);
- provider auth/config appropriate to supported mechanism;
- autonomous execution with ordinary research actions not requiring human supervision;
- provider retry/idempotency behavior;
- context pressure/checkpoint reconstruction.

Keep real provider integration replaceable.

---

## 10. Milestone 8 — behavioral research eval suite

Build repeatable scenarios around:

- premature conclusions;
- missing-context retrieval;
- feature falsification;
- recovery;
- gate respect;
- stale/superseded evidence;
- semantic commits;
- reproducibility;
- autonomous continuation.

Use both deterministic scripted models and real-model runs where useful.

---

## 11. Milestone 9 — slow memory/skill learning

Only after the core researcher works reliably:

```text
trajectory/ledger
→ reflection
→ candidate lesson
→ validation
→ durable memory/skill
```

Do not let this subsystem destabilize the first scientific kernel.

---

## 12. First live task

Use Polymarket contract time series as the primary live integration forcing function:

- exact contract identities and registered fill histories;
- open-ended exploratory questions and falsifiers;
- authored labels/features/models when legal targets exist;
- temporal development validation and retained negative trials;
- independently governed protected evaluation only after immutable inputs, label availability, and
  event/group identity are resolved;
- multidimensional evidence and an issued finding/rejection trail.

The purpose is not to maximize model performance initially. It is to expose failures in the
autonomous research architecture without overstating the current data boundary.

---

## 13. Implementation stopping rule for pre-design

Before a component is coded, ask:

> If Codex chooses the wrong detail here, is this a cheap local refactor or a plausible-looking scientific/governance error?

- Cheap local refactor: implement and learn.
- Scientific/governance risk: specify failure mode + test/contract first.
