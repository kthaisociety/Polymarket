# development.revise-candidate — development diagnostics → interpretation + revised candidate

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Close development feedback causally while recording every trial and creating new identity when scientific meaning changes.

## Relevant locked invariants

I5, I9, I12–I13, I22, I24.

## Source A

development.evaluate-candidate evidence plus candidate/episode/task/ledger context and current permissions.

## Destination B

Evidence-dependent episode interpretation and explicit continue/reject/revise/new-version/freeze-request intent with ancestry.

## Mapping f

Return diagnostics via context; model decides; persist interpretation and candidate action; version material changes and retain all trials.

## Must preserve

Diagnostic substance/status, candidate identity, rationale, trial/exposure ancestry, failed paths.

## May transform

Equivalent representation may change where semantic identity and behavior survive.

## Must exclude

Scripted decision, hidden direct evidence, winner-only history, in-place mutation, protected tuning, state belief auto-commit.

## Authority boundary

Agent interprets; harness versions/records; freeze.assess-eligibility/freeze.seal-system independently gate freeze.

## Allowed state mutation

Episode evidence, new candidate/version, ledger entries.

## Forbidden state mutation

No protected exposure reuse, direct freeze/promotion, old trial deletion.

## Failure semantics

Missing/failed diagnostics cannot justify success; changed meaning gets new identity.

## Observable consequences

Same headline with stable vs regime-fragile evidence causes different next candidate action through context alone.

## False-success implementations considered

Always select best metric; overwrite candidate; provider reads metrics store.

## Falsifying tests

Paired Level C diagnostic feedback, no store access, transcript deletion, ancestry assertions.

## Mutation-sensitivity check

**Mutation:** Choose revision by scripted turn count.

**Expected failure:** Paired actions do not differ correctly, test red.

## Composite dependencies

development.evaluate-candidate/formalization.version-material-change/ledger.record-trial-lineage/freeze.assess-eligibility.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added same-headline robustness causality and no winner-only history.

## Remaining user decisions

None.
