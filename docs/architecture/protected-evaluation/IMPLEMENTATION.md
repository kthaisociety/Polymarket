# Protected-evaluation implementation map

Status: **protected historical vertical slice and adversarial authority repair implemented;
production persistence, alternative-world executors, and metric plugins remain open**.

- Code: `src/research_agent/protected_evaluation/`
- Tests: `tests/protected_evaluation/`; broader autonomous behavioral verification remains planned
  under `tests/verification/`
- Transition contracts: [`transitions/`](transitions/)
- Required evidence: exact freeze binding, independent authority, exposure-on-disclosure,
  immutable runs, pure measurement, independent validation, negative-history retention, and
  idempotent privileged retries.

## Delivered authority substrate

The current implementation provides:

- an append-only `ResearchLedger` with exact replay and changed-identity conflict behavior;
- structurally complete `FreezeEligibilityRequest`, independently issued exact
  `FreezeEligibilityRegistration`, independent `FreezeDecision`, and immutable
  `FrozenPredictiveSystemIdentity` records;
- evaluator-owned `DevelopmentEvidenceRegistry` bindings that resolve the exact evaluated system
  identity/version/ancestry, environment, data/training/development protocols, and protected
  `EvaluationSpec`/`PromotionStandard` identities predeclared before development execution; the
  independent `FreezeEligibilityIssuer` also requires the exact development trial to terminate
  `SELECTED` before publishing a decision into an authority-owned `FreezeEligibilityRegistry`;
- a `FreezeGate.assess(request)` API with no caller-supplied authority, approval, or reason. It
  resolves only the exact request already published into its configured eligibility registry;
  invented systems, evidence, protocols, ancestry, unissued registrations, and mismatched decision
  authorities fail closed before sealing;
- a public-path regression from `DevelopmentEvaluator` through `FreezeEligibilityIssuer`,
  `FreezeGate`, and `BacktestGovernance`. The exact protected spec/standard survives into the
  frozen identity and authorizes the matching backtest request; changing either identity after
  development fails at issuance and governance rather than being appended post hoc;
- an authority-owned scientific-workflow composition in which the workflow definition carries no
  governance/validation labels or protected catalog/binding. Independent configured grants and an
  external `ProtectedResourceRegistry` are resolved into an immutable workflow issuance before
  execution; correct-label/fake-capability and changed binding/catalog probes fail before any
  ledger or exposure effect;
- exact `BacktestRequest`, `BacktestPermit`, and safe `BacktestDenial` identities;
- governance checks for exact frozen identity, configured independent authority, current
  environment/policy, caller permission, protected scope, and lineage exposure before any
  protected resolution;
- authority-owned `FrozenSystemRegistry` and `PermitRegistry` publication paths with no public
  caller `add`; each issued object is bound to the exact freeze/governance ledger event that
  created its authority, so a correctly rehashed caller fabrication remains unauthorized;
- idempotent, lock-protected, one-permit `ProtectedViewBinder` behavior that resolves an exact
  resource identity once, even under concurrent binding, and only after all
  issued-permit/request/caller/scope checks pass;
- authority-issued `ProtectedContentManifest` binding and alias-independent epistemic-period
  identity. Protected scope carries only an opaque manifest ID; the loader returns the verified
  manifest plus exact parsed catalog after exposure, and any manifest/catalog substitution seals
  typed failed evidence rather than executing;
- explicit `UNSEEN`/`PREEXPOSED` protected-resource status. Governance rejects content already
  accessible to the research process before resource resolution, and the protected-resource
  registry refuses to assign identical content or a corrected resource version a fresh epistemic
  period under another label;
- irreversible `ExposureRecord` history for successful or failed work after disclosure, including
  descendant-lineage contamination;
- a reusable `PrivilegedOperationCoordinator` with explicit `CLAIMED`, `EFFECT_SEALED`, and
  `ACKNOWLEDGED` phases. An acknowledgement lost after sealing returns the original result on exact
  retry; changed payloads conflict, and an unsealed claimed operation fails in-doubt rather than
  guessing that no effect occurred.

## Delivered protected execution and evidence slice

The implementation now also provides:

- exact immutable `EvaluationScenario`, `EvaluationSpec`, `PromotionStandard`, and
  `ClaimDefinition` identities; changing decision sample keys including population dimensions,
  metrics, thresholds, authority policy, or bounded claim substance changes identity;
- authored panel candidates whose frozen dimension-name schema may apply to authority-declared
  protected entity values not present in development; every protected invocation remains filtered
  to the decision key's exact values, and a schema mismatch is retained as dimension-scope failure;
- `BacktestEngine` validation against the authoritative issued frozen-system, permit, and view
  registries, with system, scenario, scope, environment, protocol, and exact frozen ancestry
  correspondence checked before exposure or protected-content resolution;
- a conservative disclosure contract: invoking the protected loader is itself the disclosure
  boundary. Exposure is durably recorded immediately before invocation, so loader failure remains
  exposed and produces a sealed typed failure run without claiming that bytes were successfully
  parsed;
- historical walk-forward execution that independently rebuilds legal `InformationSet I_t`, mature
  `TrainingSample S_t`, and declared `TrainingWindow W_t` at every exact `SampleKey`, then fits the
  exact frozen recipe, predicts without learning, and records the later outcome;
- immutable protected fit, prediction, outcome, failure, decision, and sealed `BacktestRun` records;
  every declared sample key remains represented even when information, sample construction, window
  selection, fitting, prediction, outcome recording, or another formal step fails;
- distinctly typed alternative-temporal-path and synthetic-counterfactual scenarios. Their
  executors are intentionally unsupported in this slice and return sealed `UNSUPPORTED` evidence
  without reading protected contents or relabeling the world as historical;
- authority-owned `BacktestRunRegistry`, `EvaluationReportRegistry`,
  `ValidationDecisionRegistry`, `ValidatedFindingRegistry`, and negative-result publication. Each
  registry accepts records only from its owning engine/evaluator/validator/publisher together with
  the exact ledger publication event; downstream consumers reject fully rehashed caller forgeries;
- a pure `Evaluator` whose API accepts only an engine-issued sealed run and exact spec. The initial standard-library
  metric family covers MSE, MAE, coverage, and failure rate plus per-time, dimension, temporal
  stability, typed failure structure, and error-concentration views; it has no trainer, fitting,
  recalibration, or selection callback;
- an independently configured binary `Validator` that accepts only evaluator-issued reports,
  carries exact run status/execution validity, hard-rejects unsupported or incomplete execution,
  and applies the exact predeclared standard and
  authority policy, denies self-validation, records `PROMOTE` or `REJECT` immutably, and preserves
  rejection in an append-only `NegativeResultRegistry` and `ResearchLedger`;
- `FindingPublisher`, which creates and registers an immutable `ValidatedFinding` only from an
  exact validator-issued `PROMOTE` decision, evaluator-issued report, and predeclared
  `ClaimDefinition`, carrying metrics, stability, concentration, caveats, trial ancestry, exposure,
  standard, and validation-authority identity;
- finite-number validation at promotion thresholds, protected prediction/outcome records, metrics,
  multidimensional report values, and an independent validator recheck. Non-finite source evidence
  becomes typed insufficiency/negative evidence and cannot exploit disabled optional report views;
- exposure eligibility keyed by a holdout-period identity separate from resource version. Publishing
  `v2` of an exposed `v1` resource does not restore freshness for descendants unless an explicit
  policy boundary changes;
- idempotent run, report, decision, exposure, and finding effects. Fault-injected acknowledgement
  loss after each sealed effect returns the original object without another catalog read, exposure,
  execution, report, decision, negative result, or finding.

The freeze boundary does not perform a "latest system" lookup. Its eligibility authority resolves
the exact evaluator-issued development binding, rather than trusting an opaque caller-supplied
`system_id` or accepting a caller-provided definition as proof. The trusted composition root owns
the development evidence, trial ledger, eligibility issuer/registry, and configured gate authority;
runtime callers receive assessment, not those issuance capabilities.

The in-memory stores prove contracts and retry semantics inside one process. A durable persistence
adapter with atomic publication/reconciliation is still required before crash-safe production use.

## Purpose and hard boundary

The protected backtest is a falsification and robustness stage for an already frozen
`PredictiveSystemDefinition`. It is not the next feature-development loop. The model may request an
evaluation and later interpret a disclosed report, but it cannot authorize access, alter the frozen
recipe, choose a more favorable metric or scenario after seeing results, or promote its own claim.

A failed result can motivate a new candidate in a new research episode. That new candidate retains
the failed result in its ancestry, and the disclosed period remains exposed rather than becoming a
fresh holdout again.

## Predeclared protected protocol

Before protected content is read, the `BacktestRequest` must bind exact references for:

- the complete frozen system, target/horizon, data scope/version, environment, and trial ancestry;
- ordered decision times plus information, label-maturity, training-window, refit, and declared
  failure/fallback behavior;
- the evaluation world and every requested scenario protocol;
- metrics, benchmarks, slices, uncertainty/robustness views, and coverage treatment;
- the independent validation standard and the claim that the evidence is intended to support;
- requester identity, prior exposure state, permission scope, and idempotency identity.

The request describes an experiment, not permission. Governance independently issues an exact,
non-broadenable permit or a safe denial without inspecting or leaking protected values.

## Scenario roles

The implementation may support a suite of evaluation scenarios without pretending they are the
same kind of evidence:

1. **Historical walk-forward.** Reconstruct the frozen procedure at each historical decision time,
   build `InformationSet I_t` and mature-label `TrainingSample S_t` independently, fit inside the
   legal window, predict, and retain every success and failure. This is one realized path.
2. **Alternative temporal paths or partitions.** When justified, a legal resampling protocol may
   estimate variability across alternative folds or paths. Purging is required when training labels
   overlap the tested information interval; embargo is used only for an additional declared
   dependence threat. If training uses observations later than a tested episode, the result is a
   scenario/stress estimate rather than a literal historical trading or deployment narrative.
3. **Synthetic counterfactuals.** A declared generator may produce additional worlds for stress and
   sensitivity analysis. The protocol retains generator identity, calibration data, fitted-state
   boundary, assumptions, seeds, parameter uncertainty, and known misspecification. Synthetic
   success cannot overwrite historical failure or be presented as observed out-of-sample behavior.

Walk-forward variants, combinatorial path construction, probability-of-backtest-overfitting
methods, and synthetic generators are optional implementations selected to address named failure
modes. The kernel requires truthful identity, legality, provenance, and interpretation—not a fixed
finance toolbox.

## Backtest execution evidence

For each permitted scenario, execution creates immutable fit, prediction, outcome, and failure
records at its declared decision times. A separately sealed `BacktestRun` binds that complete
ordered sequence to the exact frozen system, permit, data, scenario, environment, seeds, and
exposure. It is a record of what happened, not a performance conclusion.

No evaluator callback may fit, recalibrate, select, mutate, or request a replacement candidate.
Undeclared repair, silent date removal, full-history preprocessing, or a fallback that changes the
frozen procedure is a failed execution, not a convenient continuation.

## Multidimensional evaluation

`EvaluationSpec` is task-supplied. The generic evaluator must be able to return:

- task-appropriate predictive quality and calibration rather than one universal score;
- benchmark and ablation comparisons;
- per-time, rolling, subgroup, entity, and regime behavior where declared;
- uncertainty and sensitivity to defensible protocol/scenario choices;
- concentration in a few dates, entities, outcomes, or outliers;
- error, missingness, fit/prediction failure, coverage, and insufficiency structure;
- trial count/ancestry, prior exposure, selection context, warnings, and caveats;
- separate scenario-level results plus any cross-scenario comparison whose construction and exact
  input runs were predeclared.

Task-specific measures remain plugins to this contract. Classification metrics, distributional
scores, or continuous-forecast loss/calibration measures may be appropriate for one target. PnL,
turnover, Sharpe-family measures, probabilistic/deflated Sharpe, or probability-of-overfitting
estimates are appropriate only when the downstream task and their assumptions justify them. Even
when no numerical multiple-testing correction is applicable, the number and ancestry of tried
candidates remain mandatory evidence.

The `EvaluationReport` measures this evidence. An independent Validator applies the predeclared
standard and produces `PROMOTE` or `REJECT`; it does not infer economic usefulness, tune a
threshold, or rewrite the report.

## Tests before protected data exists

1. An unfrozen, incomplete, self-approved, stale, previously exposed, or scope-mismatched request is
   denied before any protected byte is read, and denial text leaks no protected value.
2. A release/maturity fixture proves `I_t` and `S_t` advance independently; future-poison data catches
   full-history features, scaling, selection, or fitting.
3. Every declared decision time yields an immutable success/failure record; failed dates cannot be
   filtered before sealing or scoring.
4. A fail-on-fit evaluator proves measurement cannot train, recalibrate, reselect, or mutate the run.
5. Equal headline scores with different temporal stability, concentration, failure coverage, or
   regime behavior remain distinguishable and may produce different predeclared validation results.
6. A non-overlapping temporal task does not acquire purging/embargo ceremony, while an overlapping
   label fixture fails until the declared contamination is removed.
7. Historical, alternative-path, and synthetic reports retain their different identities and
   interpretations; no aggregate can disguise an adverse scenario or convert synthetic evidence
   into observed history.
8. Changing generator assumptions, scenario construction, metric definitions, trial count, or
   validation thresholds changes protocol/report identity and cannot occur after disclosure in
   place.
9. A failed or interrupted run after first disclosure records irreversible exposure, survives
   retry/reload, and prevents descendants from claiming the same protected period as unseen.
10. A trading-only metric is not required for a non-trading forecast; when a task explicitly selects
    a specialized correction, violated assumptions produce a warning/failure rather than a false
    authoritative number.

No protected data should be introduced before the complete gate, exposure, execution, sealing,
measurement, validation, negative-result, ledger, and idempotent-retry paths pass these tests.

## Current verification and remaining reds

Verified from the lane worktree using the root integration environment:

```text
PYTHONPATH=src:. .venv/bin/python -m pytest -q tests/protected_evaluation
PYTHONPATH=src:. .venv/bin/python -m pytest -q
ruff check .
ruff format --check .
basedpyright
```

The integration checkpoint records the observed counts. Remaining reds and deliberate limits are:

- all stores and idempotency outcomes are in-memory contract implementations, not crash-safe
  durable adapters with atomic recovery;
- a durable production protected-catalog service/loader is not supplied. The workflow composition
  uses an exact authority-issued in-memory scope/binding/catalog registration, while tests inject
  its resource-bound loader after authorization. The in-memory fixture hashes canonical catalog-ID
  bytes; it does not prove hashing or isolation of a production protected byte store. Loader
  invocation is deliberately modeled as disclosure; a future byte-stream adapter must recompute
  SHA-256 and the parsed catalog identity while preserving the same fail-safe exposure guarantee;
- alternative temporal paths and synthetic counterfactuals retain exact identity but their
  executors are explicitly unsupported;
- the metric library does not yet include benchmarks, uncertainty intervals, regime/sensitivity
  plugins, classification/distributional scores, or task-specific measures;
- the current formal feature API fixes dimension values in each `FeatureDefinition`; a scenario may
  carry multiple same-time population slices without identity collapse, but a slice that does not
  match the frozen feature dimensions is retained as `DIMENSION_SCOPE_UNSUPPORTED` rather than
  silently evaluating another entity;
- the current downstream `OutcomeRecorder` supports full-interval target maturity only; other
  declared maturity policies become typed per-decision failure until their exact recorder exists;
- `ValidatedFinding` is implemented, but human-facing `ReportBuilder` rendering remains in the
  reporting block.
