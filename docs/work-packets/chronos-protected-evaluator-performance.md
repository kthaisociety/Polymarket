# Work packet: protected evaluator performance and observability

- Packet: `chronos.repair-protected-evaluator-materialization-cost`.
- Trigger: the exact frozen continuous-arrival candidate in
  `studies/polymarket-stochastic-process-paper-2026-08-18/source/19_continuous_arrival_hazard_protected_resolution.py`.
- Scope: generic Chronos protected authored evaluation only. No Polymarket science, candidate
  source, protected plan, Kthais, production engine, or sibling repository is changed.
- Status: **COMPLETE**; implementation verified and committed locally as `ae15ae50`; the
  pre-change reference execution reached a sealed protected negative.

## Concrete defect exposed by the real run

The source-19 driver reconstructs the exact 304-decision formal development investigation and then
requests one 100-decision protected walk-forward evaluation. The pre-change process remained alive
without stdout, a stage marker, or a receipt for more than forty minutes. The public interface could
not distinguish development reconstruction, protected-content resolution, decision execution, or a
stalled worker.

Inspection found two repeated-cost defects in `AuthoredBacktestEngine`:

1. `_label()` rebuilt two `InformationSet` objects before consulting its label-materialization cache.
   Expanding walk-forward windows therefore rebuilt and sorted the same immutable legal views tens
   of thousands of times.
2. After a legal view was built, each label scanned the full view again to select one exact field and
   dimension slice. For this study that implies hundreds of millions of avoidable comparisons.

The scientific program already runs in one bounded persistent worker. A C++, Rust, GPU, or process-
startup rewrite would not address these dominant costs.

## Admissible repair

Within one protected execution only:

- cache an exact legal `InformationSet` by catalog identity, decision time, and ordered requested
  fields;
- cache an ordered observation slice by information-set identity, exact field, and exact dimensions;
- retain existing feature and label materialization identities and all authored-program invocations;
- expose only structural progress: content resolution, completed/total decision counts, and sealing;
- never include a sample key, timestamp, dimension, prediction, outcome, metric, or protected value
  in progress events;
- suppress progress-observer failures so observability cannot affect scientific execution.

This preserves vintage semantics because a changed decision time, field scope, catalog identity, or
resolved information-set identity cannot hit the same cache entry.

## Evidence so far

- Existing cached and uncached protected decision records remain exactly equal, including fit,
  prediction, outcome, lineage, and stable identities.
- Revision-aware label tests still distinguish a later available revision.
- Immature labels remain excluded rather than negatively cached.
- Cache entries remain isolated across candidates, catalogs, and executions.
- A failing progress observer cannot interrupt execution.
- `tests/integration/test_authored_protected_evaluation.py`: 10 passed.
- `ruff check`: passed.
- project `basedpyright`: 0 errors, 0 warnings.
- correctly configured full suite after both cache layers and observer isolation: 474 passed in
  31.43 seconds.
- An exact development-only source-18 replay completed in 148.26 seconds at 2,930,660 KiB peak RSS
  and reproduced receipt SHA-256
  `417e7c9de63538f558a1cdd97609d6d6c82a49b7195bebaee830f8aafec0f192` byte-for-byte.

## Terminal reference and acceptance evidence

The uninterrupted pre-change source-19 process sealed protected receipt SHA-256
`4e9fa014c774fda83eaa8f4d7f75ec838b913197d7a14778a3333518e430b60d`. It retained one exposure,
100 decisions, 35 typed failures, an execution-valid report, independent validation rejection, and
one negative result. The receipt proves the reference path terminated; the exact wall time is
unavailable because the missing telemetry was itself the defect. Observed wall time exceeded forty
minutes.

The optimized protected path is not rerun on the exposed holdout. Re-execution would add no
scientific value after rejection and would weaken the one-exposure discipline. Semantic parity is
instead established by exact cached/uncached decision and report equality in the integration suite,
revision and isolation tests, observer-failure isolation, clean lint/type checks, and the complete
474-test suite. The development-only source-18 receipt also reproduced byte-for-byte.
