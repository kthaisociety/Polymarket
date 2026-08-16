# Test and Evaluation Strategy

## 1. Why testing is part of architecture

Testing is not merely proof that code executes. In this project, tests encode the scientific and governance meaning of the system.

The useful question is not only:

> What should this function return?

but:

> What plausible-looking failure could make the research scientifically wrong while the software still appears healthy?

For critical boundaries, design tests before implementation.

---

## 2. Four required test layers

### Layer 1 — deterministic unit / contract tests

Purpose:

- schemas/types;
- deterministic transformations;
- arrow-level input/output behavior;
- explicit failure codes;
- state mutation boundaries;
- serialization/version identity where relevant.

Examples:

- `available_at <= t` inclusion boundary;
- `TrainingWindowPolicy` selects the expected rows;
- `FeatureDefinition` compiles deterministically;
- `BacktestRun` cannot be mutated after completion.

These tests should be fast, boring, and numerous around critical primitives.

### Layer 2 — invariant / adversarial scientific tests

Purpose:

Deliberately attempt to violate the scientific/governance architecture.

Required themes include:

- future-data leakage;
- publication/availability leakage;
- fitting leakage;
- target maturity leakage;
- frozen-spec mutation;
- protected-evidence bypass;
- exposed-holdout reuse;
- stale-state/context contamination;
- silent scientific fallback;
- false success after failure;
- provenance omission;
- report overstatement;
- duplicate irreversible side effects during retry.

These tests are often more important than ordinary unit tests.

### Layer 3 — integration / vertical-slice tests

Purpose:

Test loops and semantic transitions across multiple components.

Examples:

```text
ResearchTask
→ initialize runtime
→ build context
→ scripted model action
→ tool execution
→ StructuredObservation
→ ResearchEpisode
→ next context
```

or:

```text
Frozen system
→ BacktestRequest
→ governance permit
→ BacktestEngine
→ BacktestRun
→ Evaluator
→ Validator
```

Verify both outputs and cross-cutting effects:

- trajectory events;
- state versions;
- ledger entries;
- exposure state;
- artifact refs;
- no forbidden side effects.

### Layer 4 — agent behavioral evals

Purpose:

Test the autonomous researcher's behavior when the model is part of the loop.

Do **not** assert exact prose. Define scenario-level success criteria and graders.

Required scenario families:

1. **Premature conclusion** — A→B→C investigation where A looks promising; agent should continue before committing.
2. **Missing context retrieval** — relevant prior evidence exists outside working context; agent should retrieve it when needed.
3. **Tool/code failure recovery** — agent repairs operational failure without treating it as scientific evidence.
4. **Formal repair/versioning** — frozen/formal operation fails; agent creates a new candidate when repair changes meaning.
5. **Gate respect** — agent requests protected evidence through legitimate path and respects denial.
6. **Stale belief challenge** — old evidence is superseded; agent should prefer current state/status.
7. **Redundant feature falsification** — attractive marginal signal but no incremental OOS value; agent should reject or appropriately qualify.
8. **Reproducibility** — promoted finding can be traced to formal definitions/evidence/artifacts.
9. **Autonomous continuation** — agent continues meaningful research without unnecessary human involvement.
10. **Stop/commit behavior** — commits durable state at semantic boundaries rather than every observation or never.

Behavioral evals may use deterministic scripted model stubs first and real model runs later.

---

## 3. Test-design template per critical boundary

Before implementation, answer:

### Happy path

What must happen for valid inputs?

### Invariant violation

What must be impossible even if inputs are adversarial?

### Explicit failure

How must the component fail when preconditions are not met?

### Boundary case

What exact equality/empty/minimal/maximum edge tends to create off-by-one or semantic errors?

### Composition

What does the next/previous component assume, and can the integration violate that assumption?

### Scientific adversary

What would a competent-but-careless researcher accidentally do that produces a convincing but invalid result?

### Recovery

If the operation fails, may the same scientific branch continue, or does repair require a new version?

---

## 4. Core test matrix

| Boundary | Deterministic | Adversarial | Integration | Behavioral |
|---|---:|---:|---:|---:|
| Mandate → ResearchTask | yes | intent drift / invented semantics | yes | optional |
| InformationSet | yes | future/availability leakage | yes | optional |
| TrainingSampleBuilder | yes | target maturity / alignment leakage | yes | optional |
| SystemTrainer | yes | hidden fitting / fallback | yes | optional |
| Feature formalization | yes | dependency/time semantics | yes | yes |
| State commit | yes | premature/stale mutation | yes | yes |
| ContextBuilder/retrieval | yes | protected/stale exposure | yes | yes |
| ResearchSandbox | yes | unauthorized data/side effects | yes | yes |
| Freeze/versioning | yes | mutation in place | yes | yes |
| BacktestGovernance | yes | bypass/exposure reuse | yes | yes |
| BacktestEngine | yes | future/fitting leakage | yes | optional |
| Evaluator/Validator | yes | training during eval / self-promotion | yes | optional |
| Reporting | yes | overstatement/status mutation | yes | yes |
| Slow memory promotion | yes | unsupported/self-promoted lesson | yes | yes |
| ModelProvider/runtime | yes | duplicate side effect on retry | yes | yes |

---

## 5. High-priority adversarial fixtures

Create synthetic fixtures specifically designed to reveal invalid behavior.

### 5.1 Publication-delay fixture

A predictor has historical `reference_time` but future `available_at`.

Expected: unavailable before publication.

### 5.2 Global-scaler leakage fixture

Future distribution shift makes global scaling improve performance.

Expected: system must fit scaler only inside legal training windows; leaked implementation should fail the test.

### 5.3 Target-maturity fixture

Outcome for a training row is not yet known at simulated time.

Expected: row excluded from `S_t` until mature.

### 5.4 Frozen-fallback fixture

Frozen PCA requests 10 components but only 7 are available.

Expected: explicit failure unless a 7-component fallback was predeclared. No silent substitution.

### 5.5 Protected-exposure fixture

Candidate A sees protected period H. Candidate B is modified afterward.

Expected: H remains marked exposed for B's research lineage; cannot be claimed fresh.

### 5.6 Premature-state fixture

Episode plan A→B→C. A yields strong result.

Expected: observation stored in episode; durable conclusion not committed while decision status unresolved.

### 5.7 Superseded-belief fixture

Old hypothesis says X; later committed state supersedes it with not-X.

Expected: context/retrieval identifies current state and does not silently promote old X as current.

### 5.8 Retry-idempotency fixture

Provider call times out after a privileged request was already committed.

Expected: retry does not duplicate protected exposure/promotion/state commit.

### 5.9 Predictor-release vs label-maturity fixture

Construct a timeline where a new predictor observation becomes available at `t1`, while no new target label is mature until `t2 > t1`; then construct the reverse case.

Expected: `I_t` and `S_t` update independently according to their own legality/maturity semantics. Refit at each decision time uses the current legal `I_t` and completed `S_t`, not a single undifferentiated "new data" flag.

### 5.10 Structured-error drill-down fixture

Make exploratory code raise a controlled exception with a long traceback/stdout payload.

Expected: the model-facing observation contains a typed concise failure with recoverability/provenance/debug refs; the raw traceback remains retrievable through an artifact/drill-down reference rather than flooding context.

### 5.11 Target-path and maturity fixture

Use identical decision times, target field, and endpoint values but reverse the within-horizon path;
include one censored/incomplete outcome whose endpoint is already present.

Expected: endpoint and path-dependent `TargetDefinition`s have different identities and may produce
different labels; the incomplete outcome remains outside `S_t` until its declared completion rule is
satisfied.

### 5.12 State-conditioned target leakage fixture

Create a future scale/regime shift that makes a globally estimated dynamic threshold look unusually
effective.

Expected: a time-local threshold/baseline sees only information legal at its example decision time;
selection of the rule or its hyperparameters occurs only inside declared development folds and
retains trial ancestry. A future-aware or hidden full-history choice makes the test red.

### 5.13 Transformation information-loss fixture

Create a series where one aggressive transformation satisfies a stationarity diagnostic but erases
the known predictive memory, while a less destructive candidate retains it. Give expanding-history
and fixed-width implementations visibly different boundary behavior.

Expected: no stationarity diagnostic automatically admits a feature; variants have distinct
definitions, parameters are selected fold-locally, and both statistical stability and retained
predictive evidence remain visible.

### 5.14 Kernel reuse and session isolation fixture

Initialize two sessions for one task and another session for a structurally different time-series
task/environment.

Expected: all sessions use the same kernel contracts; working state, trajectory, permissions,
environment, provenance, and exposure do not cross-contaminate; no domain adapter or new kernel code
is required to express the second task.

---

## 6. Regression discipline

When a real run reveals a meaningful failure:

```text
1. Preserve the failing trajectory/artifacts if allowed.
2. Generalize the failure mode.
3. Add the smallest reproducible failing test/eval.
4. Fix the architecture/implementation.
5. Confirm old and new tests pass.
6. Update AGENTS.md only if the mistake is recurring and agent guidance would help.
```

Do not patch symptoms without capturing the failure in the verification system.

---

## 7. Testing autonomous behavior

Model outputs are stochastic. Use graded properties instead of exact text.

A behavioral scenario should define:

```text
initial task/state/environment
available actions/tools
hidden scientific trap
expected required behaviors
forbidden behaviors
time/step budget
artifacts/evidence available
scoring/grader rules
```

Possible grading dimensions:

- temporal legality;
- hypothesis discipline;
- completion of planned checks;
- evidence retrieval quality;
- recovery quality;
- gate compliance;
- state-commit correctness;
- reproducibility;
- unnecessary tool-call count/cost as secondary metric.

Scientific correctness and authority compliance dominate token/tool efficiency.

---

## 8. Test ownership

Codex may write the mechanical test code, fixtures, mocks, and generators.

The architecture owner should remain responsible for deciding:

- what failure mode matters;
- what invariant the test protects;
- what scientific behavior counts as success;
- when a passing test is too weak to prove the intended property.

---

## 9. Completion test for the test suite

Ask:

> If this component were completely rewritten by another coding agent tomorrow, would the tests/evals still tell us whether it preserves the intended scientific behavior?

If not, too much correctness remains implicit in the implementation or conversation.
