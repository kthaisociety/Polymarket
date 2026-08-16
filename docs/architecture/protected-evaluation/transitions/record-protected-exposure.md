# exposure.record-disclosure — protected access/result disclosure → irreversible Exposure + ledger state

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Record the earliest epistemically meaningful disclosure so the period can never be claimed unseen for affected lineage, including failed/negative results.

## Relevant locked invariants

I7, I11–I13, I22, I25.

## Source A

Harness-observed protected content access or result disclosure, permit/request/system/lineage,
content manifest, epistemic period, resource/time, recipient/research process, success/failure
facts.

## Destination B

Immutable Exposure record and append-only epistemic/ledger update covering exact resource/period, candidate lineage and disclosure, idempotently.

## Mapping f

At disclosure boundary atomically claim exposure identity, append record, update eligibility; do not depend on favorable result or completed run.

## Must preserve

Exact content-manifest identity, epistemic period, resource scope/version, permit/request/candidate
lineage, disclosure time/recipient/status/failure, provenance.

## May transform

Equivalent representation may change where exact scientific meaning, identity and behavior survive.

## Must exclude

Success-only exposure, deletion/rollback, descendant reset, result rewrite, duplicate exposure, values in safe denial.

## Authority boundary

Harness observes access/disclosure; agent cannot mark unseen. Governance consumes exposure state.

## Allowed state mutation

Append exposure/ledger/eligibility state once.

## Forbidden state mutation

No data/run/finding mutation; no reversal to unexposed.

## Failure semantics

Even failed/cancelled run after disclosure remains exposed. Uncertain ack/retry converges. If no content/result crossed, denial need not create exposure.

The current injected catalog-loader boundary deliberately treats **loader invocation as
disclosure**. The harness records exposure immediately before invoking it. This is a conservative
fail-safe model: a loader that fails before returning a catalog still leaves the holdout period
exposed. A future instrumented stream may narrow this to first byte read, but ordinary loader return
cannot be used as the exposure trigger because failure after an internal read would erase epistemic
history.

## Observable consequences

After any disclosure and candidate modification, the same epistemic period cannot receive an unseen
permit through another path, resource alias, or corrected version. Content already accessible to
the research process enters as `PREEXPOSED` and never receives an unseen permit.

## False-success implementations considered

Record exposure only on successful completed run; new version resets freshness.

## Falsifying tests

Inject failure after first protected read and before run result; assert exposure persists and descendant denied. **Level B.**

## Mutation-sensitivity check

**Mutation:** Create exposure only when BacktestRun completes successfully.

**Expected failure:** Mid-run failure test red.

## Composite dependencies

backtest.bind-protected-view/backtest.execute-scenario; backtest.authorize-request future governance; ledger.record-negative-result/ledger.preserve-scientific-history; governance.retry-privileged-operation.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Clarified disclosure boundary versus mere denied request.

## Remaining user decisions

None.
