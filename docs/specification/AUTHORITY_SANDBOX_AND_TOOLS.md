# AI Authority, ResearchSandbox, Tools, Observations, and Failure Semantics

## 1. Design objective

The system must avoid two opposite failures:

1. unconstrained agent freedom that corrupts evidence or side effects;
2. "safety" that makes the researcher too dumb to do real research.

Core rule:

\[
\boxed{\text{Constrain epistemic semantics and side effects, not problem-solving creativity.}}
\]

---

## 2. Authority map

### Zone A — Free reasoning

The AI may freely:

- understand the mandate;
- form/revise hypotheses;
- plan investigations;
- interpret permitted evidence;
- diagnose failures;
- propose features/models/ensembles;
- decide which permitted analysis to run;
- write exploratory code;
- draft presentation.

### Zone B — Constrained execution

The AI may request/author computation, while the harness controls:

- which data is visible;
- temporal/legal data views;
- allowed filesystem/network/process side effects;
- resources/timeouts;
- provenance capture;
- admissibility of formal outputs.

### Zone C — Privileged requests

The AI may request but cannot self-authorize:

- protected backtest;
- final scientific promotion;
- memory/skill promotion;
- any other operation that irreversibly changes epistemic status or protected exposure.

### Zone D — Forbidden direct authority

The AI cannot directly:

- access protected holdout contents outside a permit;
- mutate completed `BacktestRun`;
- rewrite ResearchLedger history;
- mutate a frozen scientific spec in place;
- promote its own lesson/finding without validation;
- access secrets/unapproved data sources;
- convert a formal failure into silent fallback.

---

## 3. ResearchSandbox

Conceptual boundary:

```text
AI-written code
→ ResearchSandbox
→ AuthorizedCapabilities
```

The sandbox should expose enough scientific power that the model can behave like a real researcher/data scientist.

### Expected capabilities

- controlled `AuthorizedDataView`;
- scientific Python environment (exact library list deferred);
- temporary workspace for tables/models/derived variables;
- artifact persistence for large outputs;
- structured return channel (`StructuredReturn` / `AnalysisResult` conceptually);
- deterministic/scientific tool access where useful.

### Boundary controls

Conceptually these roles include:

- `CapabilityPolicy` / capability-data policy;
- `ProvenanceRecorder`;
- `ResourceLimits` / timeouts;
- side-effect policy;
- `ArtifactStore`;
- structured error translation;
- protected-data exclusion.

These names describe responsibilities, not a requirement to create one class per noun.

Core formulation:

```text
powerful computation
× restricted information domain
× restricted side effects
```

---

## 4. Exploratory code vs formal scientific computation

### Exploratory mode

AI may write arbitrary permitted code for:

- data wrangling;
- descriptive statistics;
- unusual diagnostics;
- temporary regressions/models;
- plots;
- outlier analysis;
- novel transformations;
- hypothesis exploration.

Outputs are working evidence/artifacts, not automatically formal/promoted scientific objects.

### Formal mode

To enter the formal scientific pipeline, computations/definitions require explicit identity and reproducibility, such as:

- `FeatureDefinition`;
- `ModelDefinition`;
- `FeatureSet`;
- `EnsembleDefinition`;
- `PredictiveSystemDefinition`.

Formalization should capture:

- dependencies;
- temporal semantics;
- code/expression identity;
- provenance;
- missing-data behavior;
- fitted-state behavior;
- version lineage.

This is promotion from temporary research code to scientific/productized computation.

---

## 5. Action space

Prefer a small number of deep action families.

### 5.1 Research/state actions

Examples conceptually:

- create/update hypothesis;
- mark investigation resolved/abandoned;
- propose state commit;
- inspect research graph/history.

### 5.2 Open-ended analysis

A general `run_analysis`/sandbox action is the escape hatch for novel computation.

Do not force every possible scientific idea into a prebuilt tool.

### 5.3 Formal scientific construction

Actions for defining/compiling:

- features;
- models;
- feature sets;
- ensembles;
- predictive systems.

### 5.4 Common deterministic scientific operations

Standard analyses may deserve first-class typed tools because standardized behavior + structured observations are valuable, e.g.:

- feature diagnostics;
- temporal CV/development validation;
- model comparison;
- residual diagnostics;
- calibration;
- redundancy/stability checks.

Exact tool catalog should emerge from real use. Do not begin with hundreds of narrow tools.

### 5.5 Privileged requests

Explicit `request_*` paths for operations such as:

- freeze;
- protected backtest;
- finding promotion;
- memory/skill promotion.

Tools assist exploration; gates enforce standards.

---

## 6. StructuredObservation

Golden rule:

\[
\boxed{\text{good harness}=\text{good actions}+\text{good structured observations}}
\]

A tool should not primarily return only:

```text
"success"
```

or hundreds of lines of unstructured stdout.

A structured observation should conceptually include:

```text
status
observation_type
decision-relevant payload
semantic/temporal context
warnings / factual ATTENTION flags
artifact_refs
provenance
recoverability
available drill-downs
```

For execution failures, the primary model-facing observation should remain structured and concise. Raw traceback/stdout/stderr may be preserved as a drill-down artifact/reference for debugging; it should not be the default observation payload.

Example good feature-analysis result:

```text
correlation = 0.31
n = 624
window = 2005-01..2025-12
rolling_range = [-0.08, 0.46]
sign_stability = 83%
outlier_sensitivity = moderate
redundancy: corr 0.91 with feature F12
artifact_ref = ...
```

rather than a naked `0.31`.

---

## 7. Progressive disclosure

Default observation flow:

```text
summary
→ diagnostics
→ selected slices
→ raw values/artifacts on request
```

This protects context budget while preserving full evidence externally.

Summaries must not permanently delete or hide underlying evidence.

Factual attention flags are useful, for example:

- most improvement concentrated in one period;
- high redundancy with existing feature;
- missingness concentrated in early history;
- sign reversal in one regime.

Avoid hard-coding subjective scientific conclusions into low-level tool output when interpretation belongs to the researcher.

---

## 8. Provenance for code execution

Record enough metadata to reproduce/audit important analyses:

- datasets/fields/time ranges accessed;
- authorized view/snapshot ID;
- code hash/source ref;
- environment/library version where practical;
- random seeds where relevant;
- generated artifact refs;
- formal object IDs created;
- execution status/errors.

Not every exploratory print statement must become a heavyweight ledger entry, but scientifically consequential outputs need traceability.

---

## 9. Failure classes

### 9.1 Exploratory operational failure

Examples:

- Python exception;
- missing temporary column;
- plotting error;
- numerical convergence issue during exploration.

Behavior:

```text
structured failure observation
→ agent diagnoses/replans/rewrites code
→ continue same episode where scientific meaning is preserved
```

A structured failure should carry enough fields to reason safely, such as failure type/reason, operation, concise context/message, recoverability, provenance, and preserved artifact/debug refs. Raw tracebacks remain drillable rather than being the primary interface.

### 9.2 Formal scientific failure

Examples:

- fitted transform cannot satisfy frozen specification;
- required feature unavailable;
- insufficient legal training sample;
- model fit fails under frozen protocol.

Behavior:

- explicit typed failure;
- downstream code cannot pretend success;
- agent may diagnose/repair;
- if repair changes scientific meaning, create a new formal version/candidate.

Meta-test:

> Would this recovery preserve the meaning of the experiment currently being evaluated?

If yes: recovery may stay on same scientific branch.

If no: new version/candidate.

### 9.3 Governance failure

Examples:

- unauthorized protected holdout access;
- protected backtest before freeze;
- self-promotion attempt;
- ledger rewrite attempt.

Behavior:

- hard `DENY`;
- structured explanation that does not leak protected contents;
- agent may reason about legitimate alternative paths.

---

## 10. No silent fallback

Formal machinery must not silently substitute a different scientific procedure.

Example:

```text
Frozen spec: PCA(n_components=10)
Fit cannot produce 10 components
```

Invalid behavior:

```text
silently run PCA(7)
```

Valid options:

- explicit failure; or
- execute a fallback that was explicitly predeclared in the frozen protocol.

If the agent decides PCA(7) is a better new candidate, create a new scientific version.

---

## 11. Blocking semantics

Use this test when deciding whether a failure requires an explicit boundary:

> If this operation failed, could a competent researcher mistakenly continue as if it succeeded?

If yes, downstream success must be blocked until the failure is resolved or a new explicit branch/version is created.
