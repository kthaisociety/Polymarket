# development.evaluate-candidate — candidate + development protocol/data → development evidence/diagnostics

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Generate iterative evidence while keeping it clearly development-grade and temporally legal, not protected validation.

## Relevant locked invariants

I1–I3, I13, I21–I22, I24.

## Source A

Candidate definition, declared development/temporal CV protocol, development-eligible data, trial identity/ancestry, environment.

## Destination B

Immutable development evidence with metrics/diagnostics/folds/failures, protocol/provenance, DEVELOPMENT status and exposure/trial links.

## Mapping f

Execute the exact protocol with legal folds; rebuild one catalog-bound
`TrainingInformationBundle` for each W_t; fit formal feature materializations inside that boundary;
rebuild validation-time `InformationSet` views and predict them through the inference-only
predictor; measure without protected data; record all trials/failures.

## Must preserve

Candidate/protocol/fold/time/catalog/sample/window/information/compiled-feature/series identities,
metrics uncertainty/caveats, failures, selection ancestry, development status.

## May transform

Equivalent representation may change where semantic identity and behavior survive.

## Must exclude

Protected evidence, future/fitting leakage, “validated” status, hidden failed trials, metric-only result, candidate mutation.

## Authority boundary

Development evaluator measures; agent may iterate; cannot promote/freeze itself.

## Allowed state mutation

Create diagnostics/artifacts/ledger trial records.

## Forbidden state mutation

No protected access, candidate mutation, validation/promotion.

## Failure semantics

Leakage/insufficiency/failure explicit; no relaxed CV or protected fallback.

## Observable consequences

Development evidence can revise candidate but remains distinct from protected evidence.

## False-success implementations considered

Use random CV over time; evaluate lag from a current-row value; fabricate row feature identities;
peek protected holdout; log only winner.

## Falsifying tests

Temporal adversarial folds, irregular-signal lag-vs-latest probe, formal fit-record inventory,
fail-on-protected access, all-trials retention. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Use shuffled CV and report best trial only.

**Expected failure:** Leakage/ancestry tests red.

## Composite dependencies

training.fit-system fitting; development.revise-candidate loop; ledger.record-trial-lineage ledger; freeze.assess-eligibility gate.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added selection-history and protected-data probes.

## Remaining user decisions

None.
