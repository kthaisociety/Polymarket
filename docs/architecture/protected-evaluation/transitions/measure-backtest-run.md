# evaluation.measure-run — BacktestRun + EvaluationSpec → multidimensional EvaluationReport

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Measure immutable evidence under exact predeclared metrics/slices without training, reselection or collapsing task meaning into one scalar.

## Relevant locked invariants

I11, I13, I21–I22, I24; evaluator and multidimensional evidence.

## Source A

Exact immutable run, EvaluationSpec/version, benchmark/slice/uncertainty protocol, trial/exposure context, environment.

## Destination B

Immutable report with headline and multidimensional metrics, coverage/failures, temporal/regime/robustness views, caveats, run/spec provenance.

## Mapping f

Verify run/spec; compute only declared measurements; include failures/coverage and trial context; publish report.

## Must preserve

Run/spec IDs, metrics/benchmarks/slices, uncertainty, failures/coverage, trials/exposure, caveats/provenance.

The report also preserves exact sealed run status and whether execution was formally valid.
Unsupported or incomplete execution cannot be hidden by a permissive scalar threshold.

## May transform

Equivalent representation may change where exact scientific meaning, identity and behavior survive.

## Must exclude

Fit/retrain/reselect, hidden metric choice after results, failure omission, universal scalar, run rewrite, promotion decision.

## Authority boundary

Evaluator measures only; validator finding.validate-report decides.

## Allowed state mutation

Create report/artifacts/ledger record.

## Forbidden state mutation

No learned/system/run/exposure/promotion mutation.

## Failure semantics

Metric failure explicit; no alternate metric/default or exclusion of inconvenient records.

## Observable consequences

Fail-on-fit trainer untouched; same run under different explicit specs creates different report IDs; failures affect coverage.

## False-success implementations considered

Choose best metric after seeing run; ignore failed dates; refit calibration.

## Falsifying tests

Fail-on-fit, predeclared-spec identity, failure/coverage and multidimensional assertions. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Drop failed records from denominator/coverage.

**Expected failure:** Coverage test red.

## Composite dependencies

backtest.seal-run; finding.validate-report; ledger.preserve-scientific-history.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added metric-selection timing and failure denominator attack.

## Remaining user decisions

None.
