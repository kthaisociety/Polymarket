# Work packet: protected authored-example materialization cache

## Identity

- Packet: `chronos.optimize-protected-example-materialization`.
- Trigger: the exact Polymarket move-duration holdout started from `bdl-polymarket@08f06e70`
  demonstrated repeated legal-example reconstruction after the worker-reuse repair.
- Status: **COMPLETE**. The original protected process remains in flight against the modules it
  loaded before this change and was neither restarted nor duplicated.

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

## Boundary revisions

On 2026-08-17 the user explicitly authorized implementing the queued speed repair while the
original protected process remained active. Python had already loaded that process's old modules,
so editing the working tree could not change its frozen execution. The no-restart, no-duplicate,
and no-holdout-benchmark boundaries remained unchanged.

## Transition receipt

### Result

- Status: **COMPLETE**.
- Resulting state: protected authored execution retains pure feature and label materializations for
  one `_execute_once` call, while preserving the exact walk-forward fit/predict schedule.

### Delivered state delta

- Feature results are keyed by exact candidate ID, catalog ID, and `SampleKey`, retaining the value,
  information identity, observation identities, and observed program accesses.
- Label inputs are resolved at every legal label clock. Successful label results are keyed by exact
  candidate, catalog, sample key, and the ordered historical, contextual, and outcome observation
  identities. A newly available revision therefore invokes the authored label again.
- Immature, missing, and failed materializations are not retained as negative cache entries.
- The cache is allocated inside one protected execution and cannot cross executions, requests,
  candidates, catalogs, plans, processes, or authority boundaries.
- `fit` and `predict` remain one invocation per declared decision. No fitted state, window, or
  prediction is cached.
- `scripts/check.sh` now uses the populated project `.venv` when `uv` is installed but absent from
  the invoking shell's `PATH`; it still prefers `uv run` when available.

### Evidence

- Cached and uncached reference paths produced exactly equal protected decision records over the
  nine-decision expanding-window fixture.
- Authored calls fell from 144 to 20 for `make_features` and from 144 to 20 for `make_label`.
  `fit` and `predict` remained 9 calls each on both paths.
- A deterministic ten-run timing comparison took `2.0301471280s` cached versus `3.8796409760s`
  uncached, a `1.911015x` wall-time speedup on the small integration fixture. Invocation counts,
  rather than scheduler-sensitive elapsed time, are the semantic performance evidence.
- Revision poison changed only the later legal label materialization and row identity; maturity
  poison became eligible later; candidate/catalog/execution changes missed the cache; repeated
  authored failures remained failures and were re-executed without fallback.
- The focused authored protected integration suite passed `8` tests.
- The complete gate passed Ruff format, Ruff lint, basedpyright, and all `460` tests. The first
  sandboxed attempt passed `440` and was blocked only for `20` localhost-fixture tests; the exact
  gate then passed outside that socket restriction.

### Honest boundary

The evaluator still resolves exact legal label inputs at each decision clock and still performs
every statistically required walk-forward refit. This removes redundant authored-program work; it
does not turn protected evaluation into a vectorized batch estimator or weaken revision semantics.
The already-running Polymarket holdout uses the old loaded evaluator and receives no speedup from
this transition.
