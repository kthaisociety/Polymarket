# finding.validate-report — EvaluationReport + promotion standard + independent authority → ValidationDecision

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Make binary scientific promotion decision against predeclared standards without self-authorization or changing evidence.

## Relevant locked invariants

I8, I11, I13, I21–I22.

## Source A

Exact report, predeclared standard/version, frozen candidate/trial/exposure context, independent validator identity/authority.

## Destination B

Immutable PROMOTE/REJECT ValidationDecision with reasons, exact report/standard/evidence/authority provenance.

## Mapping f

Verify exact inputs/authority; apply standard deterministically; record decision/reasons; do not modify report or train.

## Must preserve

Report/standard/candidate IDs, thresholds/rules, failures/caveats/trials/exposure, validator identity, reasons.

## May transform

Equivalent representation may change where exact scientific meaning, identity and behavior survive.

## Must exclude

Beneficiary self-approval, post-hoc thresholds, evidence rewrite, retraining, economic usefulness claim, missing caveats.

## Authority boundary

Independent validator alone decides scientific promotion; downstream business authority separate.

## Allowed state mutation

Create decision/ledger record.

## Forbidden state mutation

No report/run/system/exposure mutation or finding content yet.

## Failure semantics

Missing/ambiguous standard or authority rejects/blocks; no favorable default or threshold adjustment.

Unsupported/incomplete run status and any non-finite metric or multidimensional report value reject
independently of configured metric thresholds and optional-view settings.

## Observable consequences

Same report under standards differing predeclared threshold yields expected decisions; candidate actor cannot decide.

## False-success implementations considered

Let candidate owner call promote; tune threshold after results.

## Falsifying tests

Self-authorizer and post-hoc-standard tests; fail-on-write evidence. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Accept a model-authored `meets_standard=true`.

**Expected failure:** Independent recomputation disagrees, test red.

## Composite dependencies

evaluation.measure-run; finding.publish-validated-claim/ledger.record-negative-result; ledger.preserve-scientific-history.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added standard-version/timing attack and business-decision exclusion.

## Remaining user decisions

None.
