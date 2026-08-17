# Work packet: Persistent scientific-program trial worker

## Identity

- Packet: `investigation.scientific-program-session-throughput`.
- Owning architecture block: autonomous authored investigation.
- Semantic responsibility: execute a bounded sequence of phase-separated authored-program
  invocations without changing scientific inputs, outputs, capability access, or identity.
- Input repository state: `bdl-polymarket@00c39203` on
  `codex/polymarket-time-series-research`, plus the active move-duration protected-evaluation
  artifacts not yet committed.

## Objective

Replace repeated process startup inside one authored development/protected trial with an optional
persistent constrained worker, while returning exactly the same value, actual-access records,
errors, and scientific identities as the existing one-invocation worker. Demonstrate a material
wall-time reduction on a deterministic multi-invocation benchmark.

## Context boundary

- Global authority loaded: `AGENTS.md`, `CONTEXT.md`, locked decisions, invariants, autonomous
  investigation contract, and authority/sandbox specification.
- Owning block: `docs/architecture/autonomous-investigation/README.md`, `IMPLEMENTATION.md`, and
  transition index. No narrower transition contract currently owns worker execution; the locked
  autonomous investigation contract governs this internal mechanism.
- Relevant adjacent interfaces: `AuthoredDevelopmentEvaluator` and `AuthoredBacktestEngine`, which
  construct legal phase inputs and consume `ProgramResult` values/accesses.
- Explicitly excluded: changes to sampling, folds, label maturity, fitting windows, model recipes,
  protected authority, exposure, evaluation thresholds, identities, domain-specific caching,
  broader scientific libraries, or OS-level hostile-code claims.
- Assumption: the parent evaluator remains the sole constructor of information, outcome, training,
  state, and feature grants; persistence is only a worker-lifecycle optimization.

## Change boundary

- Permitted components: `investigation/program.py`, development/protected evaluator composition,
  focused investigation/integration tests, this packet/receipt, and the owning implementation map.
- Allowed state effects: one child process may serve a bounded authored-program session; each call
  may return one existing `ProgramResult` or existing `ScientificProgramError`.
- Forbidden state effects: authored global/module state surviving calls; widened capabilities;
  cross-call data visibility; different values/access ordering; silent retry/fallback; altered
  candidate/evidence/run/report identity; or weaker timeout/memory/output enforcement.

## Correctness

- Governing invariants: no future/availability leakage; prediction without learning; exact actual
  access provenance; bounded resources; phase-separated capabilities; no silent fallback; frozen
  scientific identity cannot mutate.
- Failure modes:
  1. persistent namespace leaks state or data across invocations;
  2. source validation or compilation occurs under a weaker policy;
  3. one timed-out/crashed invocation leaves a reusable ambiguous worker;
  4. per-call JSON/result/access behavior diverges from the reference path;
  5. session cleanup leaks workers;
  6. evaluator integration changes formal evidence identity; or
  7. optimization produces no meaningful speedup.
- Expected input/output: exact source plus ordered `ProgramInvocation` values → ordered existing
  `ProgramResult`/typed failure semantics, with a fresh execution namespace and access recorder per
  invocation.
- Violating mutation: retain the executed namespace between two calls to a source that mutates a
  module-level dictionary. The second result would change and the state-isolation test must fail.
- Required local tests: reference/session equivalence for all four phases and access records;
  mutable-global reset; phase denial; per-call result limit; timeout closes session; invocation
  bound; exact development evidence identity.
- Required integration evidence: unchanged authored development acceptance and authored protected
  execution tests; deterministic benchmark showing the persistent path faster than one-shot forks.

## Completion evidence

- Focused tests pass under the documented engine import path.
- Ruff format/check and basedpyright pass for the changed scope.
- Full 448-test suite and complete local quality gate pass.
- Benchmark method/count and observed timings are retained in the transition receipt.
- `docs/architecture/autonomous-investigation/IMPLEMENTATION.md` states the new path, invariants,
  verification, and honest remaining boundary.
- Coherent changes are committed locally without push, merge, or changes outside Chronos.

## Boundary revisions

None.

## Transition receipt

### Result

- Status: **COMPLETE**.
- Resulting state: one bounded scientific-program worker session per development or protected
  evaluation, with the process-per-invocation API retained as the reference path.

### Delivered state delta

- Added `ScientificProgramHarness.session()` and `ScientificProgramSession` with a two-million-call
  explicit default ceiling, deterministic context-manager cleanup, and fail-closed teardown on
  timeout or worker loss.
- The session worker validates before startup, compiles the exact source once, and re-executes that
  code in a fresh namespace with a copied safe-builtins dictionary and fresh access recorder for
  every invocation. Authored module state cannot cross calls.
- Development and protected authored evaluators now reuse one session without changing sample
  keys, chronological folds, label maturity, fitting windows, prediction inputs, metrics,
  protected exposure, or any scientific identity payload.
- The original `invoke()` process-per-call implementation remains available for exact reference
  comparisons and callers that need a single invocation.

### Evidence

- All four phases produce exactly equal `ProgramResult` values and ordered access records through
  persistent and one-shot paths.
- A mutable module-global adversary returns the same first-call value twice, phase-denied access
  still fails, a timeout closes the worker, oversized results fail, and the invocation ceiling is
  enforced.
- A complete authored development evaluation run through the persistent path equals the original
  one-shot reference evidence object, including its candidate, trial, prediction, metric, access,
  and evidence identities.
- A deterministic 500-feature-call benchmark returned exactly equal results: one-shot forks took
  `3.1111240840s`; one persistent session took `0.0635283720s`, a `48.972199x` wall-time speedup.
- Focused authored investigation/protected tests, the complete Chronos suite, Ruff format/check,
  basedpyright, and `git diff --check` pass at this transition.

### Honest boundary

This change removes worker startup overhead only. It neither reduces statistically required
walk-forward fits nor caches repeated protected training-example construction. The worker remains
the documented local syntax-gated process boundary, not production hostile-code containment.
