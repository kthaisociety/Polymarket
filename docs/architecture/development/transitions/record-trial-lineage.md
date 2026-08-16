# ledger.record-trial-lineage — development trials/candidate lineage → ResearchLedger ancestry

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Preserve selection history so survivors are not presented as untouched first trials.

## Relevant locked invariants

I7, I11–I13, I22, I24.

## Source A

Every candidate/version, development request/protocol, result/failure/rejection, parent relation, environment/data periods, selection decisions.

## Destination B

Append-only ledger graph reconstructing full trial ancestry, evidence status, failures, exposures and survivor selection.

## Mapping f

Append exact trial and lineage records coherently; link revisions/selection; never delete losers or relabel evidence.

## Must preserve

All trial identities/order, parentage, protocols/data periods, outcomes/failures, selection rationale/status, environment.

## May transform

Equivalent representation may change where semantic identity and behavior survive.

## Must exclude

Winner-only history, mutable score/result, orphan candidate, hidden protected exposure, trajectory conflation.

## Authority boundary

Formal pipeline writes scientific ledger; agent cannot rewrite it. Trajectory remains operational history.

## Allowed state mutation

Append ledger records/links.

## Forbidden state mutation

No deletion/update of evidence, candidate mutation, promotion by presence.

## Failure semantics

Missing required ancestry blocks claims of clean validation/freeze; corrections append linked records.

## Observable consequences

Reload winner and traverse all tried ancestors/failures and data periods.

## False-success implementations considered

Record only promoted/best candidate; overwrite rerun.

## Falsifying tests

Run multiple trials including failures/rejection, select one, assert complete graph and immutable correction. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Delete losing trials after selection.

**Expected failure:** Ancestry traversal count/history test red.

## Composite dependencies

formalization.create-candidate/formalization.version-material-change/development.evaluate-candidate/development.revise-candidate; freeze.assess-eligibility/ledger.preserve-scientific-history.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added correction-as-new-record and trajectory distinction.

## Remaining user decisions

None.
