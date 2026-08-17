# Backtest, Evaluation, Validation, and Reporting

## 1. Core contract

Conceptually:

\[
B(\text{System},\text{EvaluationWorld})\rightarrow\text{BacktestRun}
\]

The backtest subsystem answers **what happened under the frozen simulated procedure**. It does not decide whether the result is good enough.

Keep three boundaries separate:

\[
\boxed{B:\text{ What happened?}\quad E:\text{ How measure it?}\quad V:\text{ Good enough?}}
\]

---

## 2. Backtest execution flow

At each simulated decision time `t`:

```text
Dataset(s)
→ InformationSet I_t
→ TrainingSample S_t
→ TrainingWindow W_t
→ SystemTrainer
→ fitted predictive system F_t
→ prediction from current legal information
→ immutable PredictionRecord
```

When outcome becomes available, record it separately as an `OutcomeRecord`.

Default refit policy is **every decision time**.

Two kinds of change must remain distinct while advancing through historical time:

- newly released/current predictor information updates the legal `InformationSet I_t`;
- newly matured outcomes/labels update the completed supervised `TrainingSample S_t`.

A predictor release can occur without a new label becoming mature, and a label can mature without a new predictor release. The backtest must rebuild both boundaries from their own temporal semantics rather than treating "new data" as one undifferentiated event.

Decision times are explicit properties of the evaluation scenario. A heavyweight `SimulationClock` abstraction is optional; a scenario-provided ordered sequence of decision times is sufficient unless richer clock semantics are later earned by a failure mode.

This means every prediction is generated as if the researcher/deployer were standing at that historical time with only legally available information.

### Evaluation worlds are not interchangeable

A protected evaluation may contain more than one predeclared view of system behavior, but every
view must retain its own interpretation:

- a historical walk-forward simulation asks what the frozen procedure would have produced along
  one realized sequence of decision times;
- a temporally legal resampling/scenario protocol asks how behavior varies across alternative
  partitions or paths and is not automatically a literal historical simulation;
- a synthetic scenario protocol asks how behavior changes in generated counterfactual worlds and
  is evidence conditional on the generator, calibration data, and assumptions.

The historical path is important evidence, not universal truth. Alternative scenarios may reveal
concentration, regime dependence, or fragility, but they cannot erase an adverse historical result
or acquire a stronger interpretation than their construction supports. The scenario suite and its
interpretation are fixed before protected contents are exposed.

---

## 3. FitRecord

Each fit should have enough provenance to reconstruct what was trained:

- simulated decision time;
- frozen system definition ID/version;
- training sample/window reference;
- dataset/schema versions;
- fit-state/artifact refs;
- random seeds where applicable;
- environment/code version/hash where practical;
- explicit fit failure if fitting did not succeed.

Do not silently omit failed fits from the simulation.

---

## 4. PredictionRecord

A prediction record is immutable and should include at least conceptually:

- decision time;
- target/horizon identity;
- frozen system ID/version;
- fitted-system/fit record reference;
- prediction value/distribution/probability as appropriate;
- information/provenance references needed for audit;
- execution status/failure.

Prediction and outcome are separate records because the outcome is generally not knowable at prediction time.

---

## 5. BacktestRun

`BacktestRun` is an immutable simulation record, not a performance report.

Conceptually it contains/references:

- run ID;
- frozen system definition;
- evaluation scenario/world;
- dataset/schema versions;
- decision-time sequence;
- fit records;
- prediction records;
- outcome records;
- execution failures;
- audit/provenance metadata.

A completed run cannot be rewritten because later evaluation is inconvenient.

---

## 6. Backtest governance

Protected backtest is a privileged operation.

```text
FrozenPredictiveSystemDefinition
→ BacktestRequest
→ BacktestGovernance
→ DENY or PERMIT
```

Governance checks should include, as applicable:

- system truly frozen;
- required research/development gates passed;
- protected evidence has not already been exposed in a way that invalidates the requested claim;
- evaluation criteria/specification are sufficiently predeclared;
- provenance/trial ancestry is available;
- caller has permission;
- requested protected data slice is authorized.

Protected scope is not established by a path or caller-chosen resource label. The protected-data
authority binds an opaque verified content-manifest identity, an epistemic-period identity, and an
explicit unseen/`PREEXPOSED` status. Identical bytes under another resource ID, a corrected version
of an exposed period, or content already accessible to the research process cannot become fresh
holdout evidence. Governance uses only safe metadata; byte/content verification occurs after
authorization and exposure recording, before scientific execution consumes the parsed catalog.

The agent may request this operation. It cannot grant itself permission.

A denial must not expose the protected contents it is protecting.

---

## 7. Exposure semantics

Protected evidence exposure is part of epistemic state.

Once a protected period/result is exposed to the research process, it cannot later be represented as unseen validation evidence for a modified candidate.

Freshness follows the epistemic content period, not a filesystem path, storage key, or mutable
resource version. Previously public or inspected content is `PREEXPOSED`, even when a separately
governed alias points to the same bytes.

A failed protected backtest may inspire a new research cycle, but the evidence period remains exposed.

This is a governance invariant, not a recommendation.

---

## 8. Evaluator

\[
E(BacktestRun, EvaluationSpec)\rightarrow EvaluationReport
\]

The evaluator is a generic mechanism. `EvaluationSpec` defines the task-specific metrics, benchmarks, slices, and robustness views.

Possible continuous-forecasting metrics:

- MAE/RMSE;
- benchmark improvement;
- rolling stability;
- calibration/coverage where relevant.

Possible probability/market metrics:

- Brier score;
- log loss;
- calibration;
- benchmark/market comparison.

The kernel should not hard-code one domain's scalar objective as universal truth.

---

## 9. Multidimensional evidence

Do not collapse system behavior prematurely into a single scalar.

An `EvaluationReport` should be able to express:

- headline metrics;
- benchmark comparisons;
- temporal/rolling behavior;
- subgroup/regime behavior where appropriate;
- uncertainty/error bars where appropriate;
- sensitivity/ablation/robustness checks;
- failure counts/coverage;
- trial/exposure context;
- warnings/caveats.

Selection-adjusted or trial-aware metrics may be added when justified. Examples include probabilistic/deflated Sharpe-style measures (PSR/DSR) in settings where their assumptions and trial process actually fit. They should not become universal requirements merely because they exist in finance literature. Trial ancestry/count remains important even when no correction metric is applied.

The same rule applies to walk-forward variants, purging/embargo, combinatorial path construction,
probability-of-overfitting estimates, and synthetic-data tests: each is an optional method selected
for a declared failure mode. None is a universal ritual. A method's assumptions, fitting boundary,
selection timing, and interpretation belong in the protocol and report.

For a generic time-series system, the useful evidence dimensions commonly include predictive
quality, calibration where meaningful, temporal/regime stability, error and missingness structure,
concentration in a few dates/entities/outliers, benchmark and ablation comparisons, uncertainty,
coverage/failure counts, and sensitivity to defensible scenario choices. Trading-only quantities
such as PnL, turnover, drawdown, or Sharpe-family statistics are supplied by a trading downstream
task; they are not kernel requirements for probability or other forecasting tasks.

---

## 10. Validator

The scientific validator is a binary promotion gate:

\[
V(E)\in\{0,1\}
\]

Meaning:

- `1 / PROMOTE`: evidence meets the predeclared scientific standard and may become a validated finding.
- `0 / REJECT`: evidence does not meet that standard.

This is **not** an economic trading decision and not a statement that the model is useful for every downstream purpose.

The actor that created/benefits from the candidate cannot simply self-authorize promotion.

---

## 11. ValidatedFinding

`ValidatedFinding` is the canonical immutable scientific substance of a promoted result.

It should contain/refer to:

- claim;
- target/horizon;
- frozen system/candidate identity;
- metrics/benchmarks;
- robustness/stability evidence;
- caveats;
- evidence references;
- provenance/trial context;
- validation decision/status.

---

## 12. ReportBuilder

```text
ValidatedFinding
→ ReportBuilder
→ human-facing report
```

Presentation is intentionally flexible and AI-driven. A concise one-page research view is a useful default output shape, but not a fixed scientific contract.

The agent may optimize:

- wording;
- layout;
- chart/table selection;
- audience/domain framing.

Hard invariant:

> If wording/layout changes, the scientific conclusion must not change.

If a statement is necessary for the conclusion, evidence, caveat, provenance, or validation status, it belongs in the finding/evidence layer rather than being left to stylistic report generation.

---

## 13. ResearchLedger / evidence history

The `ResearchLedger` is the canonical append-only evidence/history role. An implementation may name or split part of this role as an `EvidenceStore` if a concrete storage/access reason emerges, but the architecture does not require two separate stores by default.

It records:

- experiments;
- candidate definitions/versions;
- development evaluations;
- backtest requests/permits/denials;
- backtest runs;
- evaluation reports;
- validation decisions;
- exposure/trial ancestry;
- promoted and rejected findings.

Evaluation evidence is not automatically training data and does not automatically become cross-task memory.

---

## 14. Critical adversarial cases

The test suite must explicitly cover:

1. backtest request for unfrozen system → deny;
2. system changes after freeze → new version/candidate, not in-place mutation;
3. protected result seen, candidate modified, same period claimed as unseen → deny/mark exposed;
4. fit fails and implementation silently changes PCA/model/feature behavior → fail loudly unless fallback was frozen;
5. later evaluation attempts to rewrite `BacktestRun` records → impossible;
6. evaluation metric code cannot cause retraining/fitting;
7. report generator cannot replace scientific status or omit required caveats from canonical finding;
8. protected-data denial must not leak protected values through error text/metadata.
