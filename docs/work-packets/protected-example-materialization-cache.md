# Work packet: protected authored-example materialization cache

## Identity

- Packet: `chronos.optimize-protected-example-materialization`.
- Trigger: the exact Polymarket move-duration holdout started from `bdl-polymarket@08f06e70`
  demonstrated repeated legal-example reconstruction after the worker-reuse repair.
- Status: design fixed while that protected process remains in flight; executable changes are
  forbidden until it returns.

## Problem and target outcome

`AuthoredBacktestEngine` currently rebuilds every eligible training key for every protected
decision. Each rebuild reconstructs its decision-time information, invokes `make_features`, rebuilds
the label information at the current training clock, and invokes `make_label`. With a long expanding
window, work grows approximately as protected decisions times training candidates even when the
exact feature and label inputs have not changed.

Retain the exact walk-forward decisions, maturity boundary, revisions, missingness, fitted state,
predictions, outcomes, accesses, row identities, failures, sealed run, and validation result while
executing pure feature/label materializations at most once per distinct legal input identity within
one protected execution.

## Authority and change boundary

- Permitted implementation: Chronos authored protected evaluator, focused tests, implementation
  documentation, and benchmarks under `research/chronos` only.
- Forbidden: Kthais, production engine, sibling repository, Polymarket data semantics, candidate
  source, protected plan, thresholds, sample keys, fit/predict frequency, sandbox language, resource
  limits, exposure timing, validation, promotion, or terminal-memory authority.
- Cache lifetime: one `_execute_once` call. No cache may cross candidate, catalog, plan, protected
  request, engine invocation, process, or authority boundary.
- The in-flight Polymarket run must complete against its already loaded code. Do not edit the
  executable path until that process returns.

## Exact cache semantics

1. **Decision-time feature materialization.** Cache `_features` only by the exact candidate,
   catalog, and `SampleKey`. The information clock is the key's decision time, so the legal input is
   invariant within one immutable catalog. Retain the original value, information identity,
   observation identities, and `ProgramAccess` tuple.
2. **Label materialization.** Do not cache merely by sample key. First resolve the exact historical
   and outcome inputs legal at the current label clock. Cache the authored label result only by the
   candidate, sample key, and exact ordered input-observation identities. A newly available revision
   or outcome observation must change the key and invoke `make_label` again.
3. **Maturity.** A not-yet-mature, missing, or failed label is not a permanent negative cache entry.
   A later decision clock must be able to admit it normally.
4. **Fitting and prediction.** Invoke `fit` and `predict` once per declared protected decision exactly
   as today. No fitted-state cache, rolling approximation, refit skipping, batch fallback, or
   changed training window.
5. **Failure accounting.** Cached execution must produce the same declared decision denominator,
   failures, coverage, evidence references, and sealed status as uncached semantics.
6. **Identity.** For deterministic authored programs, cached and uncached reference execution must
   produce byte-identical decision records, run identity, report identity, and validation outcome.

## Required evidence

- Focused equivalence test over multiple decisions with an expanding window: every decision, fit,
  prediction, outcome, run, report, and validation identity equals an uncached reference.
- Counting-harness test: repeated feature inputs invoke `make_features` once; repeated unchanged
  label inputs invoke `make_label` once; `fit` and `predict` counts remain one per evaluated decision.
- Revision poison test: a label revision becoming available between decisions changes the label
  input identity, causes a cache miss, and changes only later legal training rows.
- Maturity poison test: an unavailable label at one decision becomes eligible later and is not
  suppressed by a cached exclusion.
- Isolation test: candidate, catalog, or execution changes cannot reuse entries.
- Failure test: authored errors and missingness retain the current fail/skip behavior without a
  silent fallback.
- Focused integration suite for authored protected evaluation plus full Chronos test, lint, format,
  and type checks.
- A deterministic benchmark must demonstrate fewer feature/label invocations on an expanding
  scenario; elapsed time is supporting evidence, not the semantic acceptance gate.

## Stopping rule and handoff

If exact run/report/validation identities differ, a revision is admitted only when the difference
is proven to be non-scientific execution metadata already excluded from canonical identities.
Otherwise reject the optimization. Do not weaken identity assertions or revise the protected
protocol to make the benchmark pass.

After acceptance, rerun only development or synthetic protected fixtures. Never rerun the consumed
Polymarket holdout to benchmark the optimization.
