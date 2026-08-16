# Milestone 2 study cards — data.register-observations–data.prove-temporal-substrate

## data.register-observations — source values → registered observations

**Why does it exist?** Physical rows are not scientific observations until identity, time, vintage, and provenance are bound.
**Which fundamental does it protect?** Temporal admissibility and environment/provenance identity.
**What must cross?** Value, semantic field, `reference_time`, `available_at`, vintage, dimensions, caveats, source.
**Most dangerous false success?** Set `available_at` equal to row date.
**Which test catches it?** Same reference date with different release-delay rules.
**Any unresolved human decision?** No.

## data.resolve-field-reference — FieldRef → exact field/values

**Why does it exist?** Keep scientific meaning stable when storage and schemas change.
**Which fundamental does it protect?** Exact identity and current/superseded semantics.
**What must cross?** Field definition, units, time roles, version, provenance, authorized physical binding.
**Most dangerous false success?** Resolve a friendly name in the latest schema.
**Which test catches it?** Same-name decoys plus historical-version fixture.
**Any unresolved human decision?** No.

## data.build-information-set — registered observations → InformationSet I_t

**Why does it exist?** Make knowability and permission at decision time explicit.
**Which fundamental does it protect?** `available_at <= t`, not row timestamp.
**What must cross?** Exact legal values, vintages, permissions, environment/policy/time identity, exclusions.
**Most dangerous false success?** Admit by `reference_time` or current latest vintage.
**Which test catches it?** Publication-delay and retrospective-revision fixtures.
**Any unresolved human decision?** No.

## target.define-outcome — resolved target semantics → TargetDefinition

**Why does it exist?** Labels need explicit horizon, alignment, prediction, and maturity meaning.
**Which fundamental does it protect?** Mission identity and legal target maturity.
**What must cross?** Exact target ref/transformation, horizon, alignment, type, maturity, provenance/version.
**Most dangerous false success?** Default missing maturity/horizon later.
**Which test catches it?** Omit each necessary semantic and require no definition.
**Any unresolved human decision?** No seam-level choice; unresolved concrete targets are queued.

## data.build-training-sample — I_t/target/features → TrainingSample S_t

**Why does it exist?** Build only legally aligned examples with mature outcomes.
**Which fundamental does it protect?** Predictor legality and label maturity are separate; no hidden fitting.
**What must cross?** Historical predictor legality, mature labels, alignment, missingness, row provenance.
**Most dangerous false success?** Admit labels by reference time or globally fit an imputer.
**Which test catches it?** Target-maturity and fail-on-fit leakage fixtures.
**Any unresolved human decision?** No.

## data.select-training-window — S_t + window policy → W_t

**Why does it exist?** Select the declared fitting subset without adapting the recipe.
**Which fundamental does it protect?** Frozen identity and no silent fallback.
**What must cross?** Exact row identities/order, policy/version, bounds, provenance, insufficiency.
**Most dangerous false success?** Fall back from rolling to all history.
**Which test catches it?** Contrasting policies plus insufficient-history fixture.
**Any unresolved human decision?** No.

## data.advance-independent-clocks — release/maturity events → independent I_t and S_t

**Why does it exist?** Prevent one generic “new data” event from conflating predictors and labels.
**Which fundamental does it protect?** Invariant I26.
**What must cross?** Independent event semantics, membership changes, identities, provenance.
**Most dangerous false success?** Add a training row whenever a predictor is released.
**Which test catches it?** Predictor-only then label-only event sequence.
**Any unresolved human decision?** No.

## data.prove-temporal-substrate — temporal data pipeline → legal fitting substrate

**Why does it exist?** Prove registration, legality, maturity, and windows compose without leakage.
**Which fundamental does it protect?** The complete pre-fitting temporal boundary.
**What must cross?** Exact identities/provenance and explicit insufficiency across data.register-observations–data.advance-independent-clocks.
**Most dangerous false success?** Build every endpoint directly from rows dated before `t`.
**Which test catches it?** Multi-time vertical slice with no raw-data side channel.
**Any unresolved human decision?** No.
