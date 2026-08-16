# Milestone 6 study cards — freeze.assess-eligibility–governance.retry-privileged-operation

## freeze.assess-eligibility — development candidate/evidence → freeze decision/request

**Why does it exist?** Establish that a candidate meets pre-freeze research criteria without letting its creator self-certify.

**Which fundamental does it protect?** `CONSISTENT`: implied gate follows locked funnel/authority.

**What must cross?** Candidate/standard/evidence/protocol/trials/environment/requester and decision reasons.

**Most dangerous false success?** Accept requester-authored `validated=true`.

**Which test catches it?** Adversarial ancestry/evidence-status cases and beneficiary-controlled requester; require independent outcome. **Level A/B.**

**Any unresolved human decision?** None; concrete standard is supplied policy.

## freeze.seal-system — accepted freeze request/candidate → FrozenPredictiveSystemDefinition

**Why does it exist?** Seal complete scientific identity immutably so protected evaluation cannot drift.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** All target/features/models/ensemble/training/evaluation/fallback/environment identities, lineage, decision/provenance.

**Most dangerous false success?** Resolve frozen component refs dynamically to latest.

**Which test catches it?** Publish newer components, reload old frozen semantics; mutate each material dimension and require new candidate. **Level A/B.**

**Any unresolved human decision?** None.

## backtest.request-evaluation — frozen system + evaluation world/spec + caller → BacktestRequest

**Why does it exist?** Bind a protected-evidence request to exact frozen identity, predeclared scenario, evaluation intent, data scope and requester before exposure.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Frozen identity, scenario/decision times, data slice, evaluation/promotion refs, caller, ancestry/exposure context, key.

**Most dangerous false success?** Accept unfrozen candidate and resolve it at execution time.

**Which test catches it?** Vary every semantic dimension; fail-on-protected-read; unfrozen input rejected. **Level A.**

**Any unresolved human decision?** None.

## backtest.authorize-request — BacktestRequest + governance state → BacktestPermit or safe denial

**Why does it exist?** Independently authorize protected evaluation only when freeze, gates, ancestry, exposure, permission and predeclaration are valid, without leaking contents.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Request/system/scenario/scope/authority/policy versions, exposure/ancestry facts, decision reason.

**Most dangerous false success?** Ignore exposure of parent lineage after candidate modification.

**Which test catches it?** Fail-on-content protected store, modified descendant after exposure, scope variants, self-authorizer. **Level A/B.**

**Any unresolved human decision?** None.

## backtest.bind-protected-view — BacktestPermit + protected resource identity → exact AuthorizedDataView

**Why does it exist?** Bind governance permission to the actual protected bytes/view exposed to execution; prevent permit swapping or broader access.

**Which fundamental does it protect?** `CONSISTENT`: implied mapping uniquely follows permit/data authority and exposure rules.

**What must cross?** Permit/request/system/scenario, resource/slice/version, environment, access identity/limits.

**Most dangerous false success?** Ignore permit resource binding and open requested holdout.

**Which test catches it?** Swap resource/version/date/caller; fail-on-read; exact scope succeeds only. **Level A/B.**

**Any unresolved human decision?** None.

## exposure.record-disclosure — protected access/result disclosure → irreversible Exposure + ledger state

**Why does it exist?** Record the earliest epistemically meaningful disclosure so the period can never be claimed unseen for affected lineage, including failed/negative results.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Exact content scope/period/version, permit/request/candidate lineage, disclosure time/recipient/status/failure, provenance.

**Most dangerous false success?** Create exposure only when BacktestRun completes successfully.

**Which test catches it?** Inject failure after first protected read and before run result; assert exposure persists and descendant denied. **Level B.**

**Any unresolved human decision?** None.

## backtest.execute-scenario — permit + frozen system + scenario → historical fit/prediction/outcome/failure sequence

**Why does it exist?** Execute exact protected simulation across explicit decision times, rebuilding legal predictor and label boundaries and refitting frozen recipe as declared.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Permit/system/scenario, every time boundary, vintages, fit/prediction/outcome IDs, failures, seeds/environment, exposure.

**Most dangerous false success?** Precompute features/scaler on full protected history.

**Which test catches it?** Multi-time leakage fixture, fail-on-evaluator/update, failure retention, exact decision sequence. **Level B.**

**Any unresolved human decision?** None.

## backtest.seal-run — completed execution records + frozen/scenario provenance → immutable BacktestRun

**Why does it exist?** Seal exactly what happened, including failures and exposure, as an immutable simulation record rather than a performance report.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** All identities/times/records/failures/omissions/status/provenance/exposure.

**Most dangerous false success?** Filter failed decision times before sealing.

**Which test catches it?** Inject missing/out-of-order/corrupt record and require non-complete; attempt mutation; failure count preserved. **Level A/B.**

**Any unresolved human decision?** None.

## evaluation.measure-run — BacktestRun + EvaluationSpec → multidimensional EvaluationReport

**Why does it exist?** Measure immutable evidence under exact predeclared metrics/slices without training, reselection or collapsing task meaning into one scalar.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Run/spec IDs, metrics/benchmarks/slices, uncertainty, failures/coverage, trials/exposure, caveats/provenance.

**Most dangerous false success?** Drop failed records from denominator/coverage.

**Which test catches it?** Fail-on-fit, predeclared-spec identity, failure/coverage and multidimensional assertions. **Level A/B.**

**Any unresolved human decision?** None.

## finding.validate-report — EvaluationReport + promotion standard + independent authority → ValidationDecision

**Why does it exist?** Make binary scientific promotion decision against predeclared standards without self-authorization or changing evidence.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Report/standard/candidate IDs, thresholds/rules, failures/caveats/trials/exposure, validator identity, reasons.

**Most dangerous false success?** Accept a model-authored `meets_standard=true`.

**Which test catches it?** Self-authorizer and post-hoc-standard tests; fail-on-write evidence. **Level A/B.**

**Any unresolved human decision?** None.

## finding.publish-validated-claim — promoting decision + canonical evidence → immutable ValidatedFinding

**Why does it exist?** Preserve exact scientific substance of a promoted claim so later presentation cannot alter status, caveats, evidence or meaning.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Claim scope, target/horizon, system, metrics, robustness, caveats, evidence/trials/exposure, decision/authority.

**Most dangerous false success?** Generate claim from headline metric while dropping caveats.

**Which test catches it?** Adversarial report with strong headline but critical caveat; require caveat and bounded claim. Rejected decision cannot create. **Level A/B.**

**Any unresolved human decision?** None.

## ledger.record-negative-result — denied/rejected/failed protected operation → ledger + safe model result

**Why does it exist?** Retain negative scientific/governance history and exposure without leaking protected values or pretending success.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Request/candidate/evidence/decision/failure identity, reasons, exposure, trials, provenance and status.

**Most dangerous false success?** Record exposure/rejection only for successful promotions.

**Which test catches it?** Denial secret/value sentinels, failed-after-disclosure, rejection-history traversal. **Level A/B.**

**Any unresolved human decision?** None.

## ledger.preserve-scientific-history — formal objects/governance/evidence → append-only ResearchLedger history

**Why does it exist?** Compose reconstructible scientific identity, ancestry, exposure, evidence and decisions across the protected pipeline.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Every formal identity/version, data periods/environment, protocols, trial ancestry, governance authority, exposure, evidence/status, correction links.

**Most dangerous false success?** Persist only final successful chain and omit losing trials/exposures.

**Which test catches it?** Build complex graph with failure/revision/exposure and assert complete traversal after reload; mutation/delete impossible. **Level B.**

**Any unresolved human decision?** None.

## governance.retry-privileged-operation — retried privileged request after uncertain ack → one irreversible result

**Why does it exist?** Prevent retries from duplicating protected execution, exposure or promotion while detecting semantic key reuse.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Full request/system/scenario/data/decision payload, original outcome and every irreversible effect/provenance.

**Most dangerous false success?** On missing response, issue a fresh permit and rerun.

**Which test catches it?** Inject lost ack after each irreversible boundary, reconstruct, replay/concurrent/change payload, assert one effect. **Level B.**

**Any unresolved human decision?** None.
