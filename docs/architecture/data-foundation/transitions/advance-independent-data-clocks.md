# data.advance-independent-clocks — predictor releases/revisions and label-maturity events → independently rebuilt I_t and S_t

## Status

`CANDIDATE_CONSENSUS` — experimental composite contract, not canonical.

## Architectural purpose

Prove the runtime keeps current predictor information and completed supervised labels as two distinct temporal boundaries rather than processing both through one generic “new data” event.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I1–I3, I23, I26.
- `docs/specification/DECISIONS.md`, Backtest semantics.
- data.build-information-set and data.build-training-sample contracts.

## Source A

A sequence of explicit simulated decision times with independently scheduled predictor release/revision events and target completion/availability events under exact data/target definitions.

## Destination B

At every `t`, independently reconstructed exact `I_t` and `S_t` whose membership/provenance changes according to their own semantics.

## Mapping f

For each decision time, rebuild `I_t` from registered availability/vintage/permission; separately rebuild `S_t` from historically legal predictors and target maturity; record both identities. Never incrementally copy one boundary into the other.

## Must preserve

Event kind/time, decision time, predictor availability/revision provenance, target maturity rule, exact membership changes, and independence of identities.

## May transform

Events into newly materialized immutable views; caching is allowed only if semantically equivalent to rebuild.

## Must exclude

One shared “new data” flag, labels admitted on predictor release, predictors delayed until label maturity, stale cached membership, current revision backfill, and hidden fitting.

## Authority boundary

data.build-information-set and data.build-training-sample retain their respective legality rules. Composite orchestration schedules/rebuilds; it cannot merge or relax them.

## Allowed state mutation

Create immutable per-time `I_t`/`S_t` identities and provenance/audit records.

## Forbidden state mutation

No data/definition mutation, learning, evaluation, or cross-boundary promotion.

## Failure semantics

Failure to rebuild either boundary is explicit and prevents downstream fitting/prediction for that time according to protocol; the other boundary's success cannot stand in for it. No stale-cache fallback.

## Observable consequences

A predictor-only release changes `I_t` but not `S_t`; a label-only maturity event changes `S_t` while current predictor membership may remain unchanged; a revision affects only legal vintages from its availability onward.

## False-success implementations considered

- One `has_new_data` branch rebuilds both from row timestamps.
- Copy `I_t` rows directly into `S_t`.
- Update neither boundary unless both predictor and label change.
- Reuse previous view after rebuild failure.

## Falsifying tests

Use a four-time sequence with predictor-only release, no event, label-only maturity, and later revision. Assert exact independent membership/identity changes and provenance at each time; fail-on-fit doubles. **Level B.**

## Mutation-sensitivity check

**Mutation:** rebuild `S_t` whenever `I_t` gains a predictor row and treat it as a completed example.

**Expected failure:** the predictor-only step becomes red because `S_t` changes before label maturity.

## Composite dependencies

Participating seams: data.register-observations–data.build-training-sample; data.prove-temporal-substrate and backtest.execute-scenario consume the per-time boundaries.

## Fundamentals review

`CONSISTENT`. It directly encodes I26 and proves independent temporal causality rather than co-occurrence.

## Grill findings

Resolved non-semantically: added label-only and revision events plus stale-cache failure to prevent a coincident-event test from passing a conflated implementation.

## Remaining user decisions

None. Scenario decision times are explicit inputs; no heavyweight clock object is required.
