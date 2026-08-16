# Scientific Kernel

## 1. Objective

The scientific kernel answers:

\[
\boxed{\text{Given information available at }t,\text{ discover whether anything predicts }y_{t+h}.}
\]

The kernel is generic across insurance, macro forecasting, market research, Polymarket, and other time-series domains. What changes between tasks is the concrete target, horizon, datasets, evaluation criteria, hypotheses, and downstream use—not the scientific machinery by default.

A new scientific question enters as a new or versioned `ResearchTask` plus an exact
`ResearchEnvironment`. A new autonomous attempt creates an independent `ResearchSession`. Neither
case requires a new domain kernel or a default adapter layer: the same runtime and scientific
contracts operate on different formal definitions and permitted resources.

---

## 2. Six axioms

### A1 — Temporal admissibility

Predictions at time `t` use only information legally knowable at `t`.

Every observation carries at least:

```text
value
reference_time
available_at
```

Admissibility:

\[
available\_at \le t
\]

`reference_time` and `available_at` are distinct. A value about January published in March is not available in February merely because its reference period is January.

### A2 — Learning is information

All fitted/learned state obeys the same temporal restriction:

- imputation;
- scaling;
- PCA;
- feature selection;
- hyperparameter tuning;
- model fitting;
- ensemble weights;
- auxiliary learned transforms.

Anything learned from data is information and must be time-legal.

### A3 — Frozen specification for true backtest

A protected/true backtest evaluates a fully frozen `PredictiveSystemDefinition`.

The frozen identity includes at least:

- target definition;
- feature set;
- model definition(s);
- ensemble definition;
- training protocol;
- evaluation protocol/specification where relevant to predeclaration.

A protected result cannot be used to silently alter the object that supposedly produced it.

### A4 — Evidence provenance

Scientific claims and lessons carry provenance, including the data periods/evidence sources from which they were learned.

### A5 — Selection changes evidence meaning

Repeated search, feature selection, model trials, and prior exposure alter the interpretation of later evidence. Trial ancestry/history must be recorded rather than pretending each surviving candidate was the first idea tested.

### A6 — Historical performance is conditional evidence

Backtest performance is evidence conditional on the historical world and specification, not a statement of timeless truth.

---

## 3. Dataset semantics

A `Dataset` represents raw time series/tables together with a stable semantic schema.

Use stable semantic identities:

```text
FeatureDefinition
→ FieldRef
→ DatasetSchema / field registry
→ physical storage
```

Do not let scientific definitions depend on fragile physical column positions/file paths when stable semantic IDs can be used.

The target is a semantic view/transformation of dataset fields, not a special physical dataset type.

---

## 4. Information sets

At simulated time `t`, construct:

\[
\mathcal I_t = \{\text{information legally knowable at }t\}
\]

`InformationSet` is the boundary that makes time legality explicit.

It must account for:

- publication/release delays;
- revisions/vintages when relevant;
- feature maturity;
- unavailable future observations;
- target/outcome maturity where appropriate downstream.

Do not infer legality from row timestamp alone.

---

## 5. Target semantics

A `TargetDefinition` defines how observations after a decision time become the outcome associated
with that decision. Conceptually:

\[
\psi : (D_{(t,m(t)]}, t, h, protocol) \rightarrow y_t
\]

where `t` is the decision time, `h` is the scientific horizon, and `m(t)` is the time at which the
outcome is complete and legally available. The target mapping may inspect future observations to
construct a label; those observations are never predictor information at `t`, and the completed
label cannot enter `TrainingSample S_t` before `m(t)`.

Important dimensions include:

- semantic target field/transformation;
- decision-time population/cadence and forecast horizon `h`, represented as exact elapsed time or
  an exact civil-calendar offset with declared anchor, month-end, timezone, and DST/fold policy;
- outcome observation interval, timestamp alignment, and label completion/availability rule;
- endpoint, cumulative, path-dependent, duration, first-event, or other declared outcome meaning;
- units, scale, direction, class/value encoding, and prediction type;
- censoring, partial development, competing events, missingness, and insufficiency behavior;
- fixed versus state-conditioned thresholds/baselines, their causal derivation rule, and any
  research-selection procedure;
- sampling relationship and applicability across entity, geography, frequency, or regime;
- environment/schema/field identity, assumptions, provenance, version, and lineage.

The target is a scientific hypothesis about what is worth predicting, not a convenient existing
column. Fixed-horizon endpoint labels, path-dependent event labels, and a secondary accept/abstain
target are optional task constructions with different meanings. The kernel does not prescribe
triple barriers, return signs, rare-class deletion, or a primary/secondary model arrangement.

A target rule may derive time-local state for one example only from information legal at that
example's decision time—for example, a trailing scale estimate. If the form or hyperparameters of
that rule are selected from data, the choice is development selection: it occurs inside the declared
development folds, retains every tried variant in ancestry, and is frozen before protected
evaluation. Neither time-local derivation nor research-time selection may inspect future information
relative to the boundary it claims or hide a whole-history choice as predetermined.

If task semantics are genuinely unresolved at research start, preserve them as unresolved rather than inventing precision. Formal model development/backtest gates may require resolution later.

Calendar offsets are not duration approximations. A calendar quarter may span different elapsed
day counts depending on its decision-time anchor, and month-end or daylight-saving transitions may
change or invalidate a local wall-clock result under the declared policy. These semantics remain
part of target, feature, fold, and evidence identity wherever that boundary consumes the offset.

---

## 6. Feature ontology

### 6.1 Public abstraction

A feature is a reproducible, time-legal mapping:

\[
\phi_j : D_{\le t} \rightarrow z_t^{(j)}
\]

Represent this as `FeatureDefinition`.

### 6.2 Internal representation

A feature may compile to `FeatureExpression` / AST / computation graph built from operators such as:

- `Field`;
- `Lag`;
- `Diff`;
- `Log`;
- `RollingMean`;
- `Ratio`;
- arithmetic/interaction operators;
- fitted operators such as scaling/PCA/KMeans-or-other clustering/auxiliary models.

Principle:

```text
FeatureDefinition = stable scientific/domain abstraction
operators/AST      = internal representation
```

### 6.3 Materialization

`FeatureSeries` is a materialized output of a `FeatureDefinition` under a concrete dataset/information environment.

`FeatureSet` is a set of formal feature definitions.

### 6.4 Fitted feature operations

Fitted operators store fit state keyed by training window/provenance. They must be fitted inside the time-legal training boundary, never globally as a convenience.

### 6.5 Transformation principle

A feature transformation is a scientific choice about which information to preserve and which
statistical failure to reduce. It may trade retained memory or level information against
comparability, invariance, noise reduction, or easier estimation. Statistical convenience alone is
not evidence that the transformation is useful.

Every consequential transformation should therefore declare:

- the named failure mode or hypothesis it addresses;
- information/history it uses, removes, compresses, or approximates;
- fixed parameters versus data-selected/fitted parameters and their legal fitting boundary;
- lag, window, warm-up, initialization, truncation, and finite-history behavior;
- expected applicability and assumptions, including stability/regime sensitivity;
- missingness, invalid-domain, insufficiency, and failure semantics;
- diagnostics and development evidence used to retain, revise, or reject it.

Stationarity is not a universal feature-admission gate, and rejection of one unit-root test is not
proof of predictive usefulness or stable generalization. Differencing, fractional differencing,
detrending, scaling, smoothing, aggregation, learned representations, and raw levels are candidate
feature families. The researcher may compare them through open-ended analysis; any selected
version becomes an exact `FeatureDefinition`, and all data-selected choices occur fold-locally.

---

## 7. Feature analysis is not feature definition

Feature-analysis methods produce evidence/diagnostics; they are not themselves predictive features by default.

Examples:

- MDI;
- MDA/permutation importance;
- SFI;
- correlation analysis;
- redundancy analysis;
- PCA used exploratorily.

PCA can alternatively be a fitted feature operator when it is part of the predictive pipeline and obeys fold/time legality.

---

## 8. Leakage taxonomy

Tests and design should explicitly consider at least:

- temporal leakage;
- availability/publication leakage;
- fitting leakage;
- target leakage;
- feature-selection/data-snooping leakage;
- multiple-testing/trial-selection effects;
- stale-state contamination from prior evidence;
- protected-holdout exposure/reuse.

A result can be numerically correct and scientifically invalid. The harness exists partly to make invalid-but-plausible results difficult to produce silently.

---

## 9. Training sample construction

At time `t`:

\[
TrainingSampleBuilder(\mathcal I_t, TargetDefinition) \rightarrow S_t
\]

`S_t` contains only completed supervised examples that are legally available at `t`.

Responsibilities include:

- legal target availability/maturity;
- correct feature/target alignment;
- causal feature construction;
- outcome maturity windows;
- missing-data behavior according to the frozen protocol;
- explicit insufficiency failures;
- provenance.

The builder must not perform hidden learning/fitting unless the architecture explicitly assigns that operation to the controlled trainer.

---

## 10. Training-window policy

\[
TrainingWindowPolicy(S_t) \rightarrow W_t
\]

This chooses the subset of completed legal samples used for fitting at simulated time `t`.

Examples may include expanding or rolling windows. Exact policies are task/spec choices, not hard-coded kernel assumptions.

---

## 11. Model ontology

Keep distinct:

```text
ModelDefinition
FittedModel
ModelSelection
```

A model recipe is not a fitted instance, and selecting among models is a research/training procedure rather than a property of one fitted model.

---

## 12. Ensemble semantics

Ensembles are part of the predictive-system recipe when used.

Before protected backtest, choose/freeze:

- ensemble method;
- surviving feature set;
- participating model definitions;
- training/fitting protocol.

Any learned ensemble weights must be fit within time-legal windows.

---

## 13. PredictiveSystemDefinition

The central frozen scientific recipe includes:

```text
TargetDefinition
FeatureSet
ModelDefinition(s)
EnsembleDefinition
TrainingProtocol
EvaluationProtocol / EvaluationSpec reference as required
```

This is the identity evaluated by a true protected backtest.

Implementation may include additional fields needed for reproducibility, but must not omit scientific choices that would change the experiment's meaning.

---

## 14. SystemTrainer — controlled fitting boundary

\[
F_t = Train(\mathcal P, W_t)
\]

`SystemTrainer` is the controlled fitting boundary for the frozen predictive recipe `P`.

All learned components belong here or in explicitly nested time-legal procedures:

- imputation parameters;
- scaling parameters;
- PCA state;
- feature selection if the **procedure** was frozen;
- hyperparameter selection if the **procedure** was frozen;
- model parameters;
- ensemble weights.

Outer backtesting is not inner model-selection CV.

`predict()` never learns.

---

## 15. Development vs protected evidence

Development research may iterate:

```text
features/models
→ development validation
→ diagnostics
→ interpretation
→ revised candidate
```

Protected evidence is not another ordinary development fold. Once observed, it becomes exposure and must be tracked.

---

## 16. AFML stance

Advances in Financial Machine Learning is a source of failure modes and optional methods, not doctrine.

Useful general insights include:

- labels encode the scientific question, including outcome path, scale, and maturity, rather than
  merely naming a convenient future column;
- transformations trade statistical regularity against retained information, so the least
  destructive adequate transformation is an empirical candidate rather than a universal rule;
- dangers of backtest overuse and the rule that a protected backtest is evidence generation, not a research/feature-selection tool;
- multiple testing;
- walk-forward / CV design considerations;
- optional purging/embargo when overlapping-label structure actually creates the failure mode;
- multidimensional evaluation;
- skepticism around trial selection;
- trial-aware/selection-adjusted measures such as PSR/DSR when they are justified by the task and trial process.

Do **not** import finance-specific machinery wholesale into the kernel. Triple barriers,
meta-labeling, fractional differentiation, purging, CPCV, and trading-rule conventions are optional
problem-specific methods, not kernel axioms.

---

## 17. Scientific promotion funnel

```text
Idea
→ Candidate
→ Tested
→ Research-Validated
→ Frozen
→ Protected Backtest
→ Promoted Finding
```

The evidentiary burden must increase with epistemic status.

Most candidates should fail before promotion.
