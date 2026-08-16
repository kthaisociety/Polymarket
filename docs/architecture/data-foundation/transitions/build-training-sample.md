# data.build-training-sample — InformationSet I_t + TargetDefinition + formal features → completed legal TrainingSample S_t

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Construct supervised examples whose predictors were legal at their decision times and whose labels are complete and legally available by current simulated time, without hidden fitting or conflating predictor release with target maturity.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I1–I3, I17, I23, I26.
- `docs/specification/SCIENTIFIC_KERNEL.md`, Training sample construction.
- `docs/specification/DATA_FLOW_AND_LIFECYCLE.md` 5.3.

## Source A

Exact `I_t`; immutable `TargetDefinition`; formal feature definitions/materialization rules; unique
candidate `SampleKey` values binding historical decision time to an exact named population slice;
missingness/alignment protocol; exact environment/data/schema versions and provenance. A
decision-time-only shorthand is equivalent to a `SampleKey` with no dimensions and is legal only
when every scoped field is dimensionless.

## Destination B

Immutable provenance-bearing `TrainingSample S_t` containing only aligned examples whose predictor values were legal at their own decision time and whose target outcome is complete/available by `t`, with explicit exclusions/insufficiency.

## Mapping f

For each unique candidate sample key, reconstruct/verify legal predictor information within its
exact population slice; apply formal feature definitions causally; construct endpoint/path/event/
censored outcome in the same slice using the exact target semantics and only causally legal
time-local derivations; admit only complete, mature, legally available labels; apply declared
non-learned missingness rules; emit sample and provenance. No learned preprocessing or selection.

## Must preserve

Current `t`; each example's decision/predictor times; label reference/completion/availability times; target/feature identities; alignment; missingness policy; environment/data vintages; exclusions; row lineage; and legal insufficiency.

## May transform

Legal observations/features into aligned predictor-label rows; deterministic non-learned filtering/representation declared by protocol.

## Must exclude

Immature/future/partially developed labels, predictors unavailable at their decision time,
current-vintage backfill into past rows, cross-population predictor/target joins, duplicate sample
keys, global fitting/imputation/scaling/PCA/selection/target-threshold estimation, target leakage,
endpoint-for-path substitution, alignment defaults, one generic “new data” boundary, silent
rare-class removal, and silent row dropping beyond policy.

## Authority boundary

Builder enforces frozen target/feature/protocol semantics; it cannot invent or fit them. Learned operations belong to training.fit-system within `W_t`.

## Allowed state mutation

Create immutable sample/provenance and exclusion/insufficiency records.

## Forbidden state mutation

No source/definition mutation, model fitting, feature selection, prediction, outcome rewrite, or evidence promotion.

## Failure semantics

Unresolved target/alignment, illegal feature dependency, missing provenance, or insufficient mature examples yields typed explicit failure/insufficiency. No global fitting, future label, imputation, nearby field, or relaxed maturity fallback.

## Observable consequences

New predictor release may change current `I_t` without adding completed training rows; later label maturity may add historical rows to `S_t` even with unchanged current predictor set.

## False-success implementations considered

- Use all labels with `reference_time <= t` regardless of maturity.
- Fit scaler/imputer globally during sample build.
- Build past predictors from current/latest vintage.
- Drop missing rows silently.
- Treat `I_t` rows as automatically supervised.

## Falsifying tests

1. Target-maturity fixture: label reference time passed but completion/availability has not; exclude until mature. **Level A/B.**
2. Predictor-release versus label-maturity paired events change `I_t` and `S_t` independently.
3. Fail-on-fit transforms prove no learned operation; global-scaler leakage fixture remains red under mutation.
4. Historical revision and missingness/alignment fixtures preserve exact provenance or fail explicitly.
5. Two entities observed at one decision time produce two exact rows with no cross-entity pairing;
   omitting the required population slice fails.
6. Repeating one sample key fails before window selection, so it cannot satisfy a minimum-sample
   threshold.

## Mutation-sensitivity check

**Mutation:** admit labels whenever their reference timestamp is at or before `t`.

**Expected failure:** test 1 becomes red because an outcome enters before the `TargetDefinition` says it is complete/available.

## Composite dependencies

data.build-information-set supplies legal predictors; target.define-outcome target semantics; data.select-training-window selects fitting subset; data.advance-independent-clocks proves dual boundaries; training.fit-system owns fitting.

## Fundamentals review

`CONSISTENT`. The mapping sharply separates temporal predictor legality, label maturity, and learning authority.

## Grill findings

Resolved non-semantically: required predictor legality at each historical decision time and fail-on-fit proof, not merely final-row timestamp checks.

## Remaining user decisions

None. Concrete missingness protocol is part of the supplied formal specification.
