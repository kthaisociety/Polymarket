# data.build-information-set — registered observations + decision authority/time → legal InformationSet I_t

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Construct the exact information legally knowable and authorized at simulated decision time `t`, making temporal and permission legality a first-class boundary rather than an assumption in downstream code.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I1, I14, I16, I24, I26.
- `docs/specification/SCIENTIFIC_KERNEL.md`, A1 and Information sets.
- `docs/specification/DATA_FLOW_AND_LIFECYCLE.md` 5.2.

## Source A

Immutable registered observations with `reference_time`, `available_at`, vintage/revision/status/provenance; exact environment snapshot; current capability/permission/protected policy; explicit decision time `t` and requested dataset/field scope.

## Destination B

An immutable provenance-bearing `InformationSet I_t` containing only observations whose exact versions are legally available and authorized at `t`, plus explicit environment/policy/time identity and insufficiency/exclusion facts.

## Mapping f

Resolve exact registered scope; filter authorization/protected state before content access; admit only `available_at <= t`; apply declared vintage/revision-as-known-at-t semantics; retain provenance/status; publish legal view or explicit insufficiency/failure.

## Must preserve

Decision time, environment/policy versions, dataset/field identities, value/reference/availability times, vintage/revision lineage as knowable at `t`, dimensions, caveats, permissions, exclusions, and provenance.

## May transform

Registered observations into a bounded/queryable immutable legal view; representation/indexing is free.

## Must exclude

Any `available_at > t`, future revision, unauthorized/protected value, latest-vintage substitution, row-timestamp legality, hidden fitting/imputation, target-maturity conflation, cross-environment data, and silent insufficiency.

## Authority boundary

Harness policy and registered time semantics determine admission. Caller/model cannot assert legality; `I_t` grants only the scoped read authority represented by it.

## Allowed state mutation

Create immutable `I_t`/provenance and bounded access/audit facts. Protected exposure, if any, belongs to separately governed seams.

## Forbidden state mutation

No source data/schema/permission/state change, learning/fitting, label construction, or evidence promotion.

## Failure semantics

Missing/ambiguous availability or policy, incoherent versions, denied scope, or insufficient required data yields explicit safe failure/insufficiency. No future/latest/unauthorized fallback and no reading denied values to decide exclusion.

## Observable consequences

At `t1` a delayed observation is absent; at `t2 >= available_at` it appears. A revision published later is absent from earlier `I_t` even if queried after publication. Revoked permissions remove content.

## False-success implementations considered

- Filter by `reference_time` only.
- Use current latest vintage for historical `t`.
- Apply permission after loading values.
- Impute unavailable rows.
- Build one generic “new data” view for predictors and labels.

## Falsifying tests

1. Publication-delay fixture: `reference_time <= t < available_at`; assert exclusion, then inclusion after release. **Level A/B.**
2. Revision fixture queried retrospectively: earlier `I_t` contains only vintage known then.
3. Permission pair with fail-on-content reads for denied scope.
4. Hidden fitting/imputation spies remain untouched; insufficiency is explicit.

## Mutation-sensitivity check

**Mutation:** admit by `reference_time <= t` and ignore `available_at`.

**Expected failure:** test 1 becomes red because unreleased information enters `I_t`.

## Composite dependencies

data.register-observations/data.resolve-field-reference supply registered exact observations; data.build-training-sample constructs completed samples; data.advance-independent-clocks proves independence from label maturity; data.prove-temporal-substrate composes time legality.

## Fundamentals review

`CONSISTENT`. This is the principal temporal/authority information boundary and does no learning.

## Grill findings

Resolved non-semantically: added retrospective revision, pre-read authorization, and explicit insufficiency attacks.

## Remaining user decisions

None. Query/index representation and insufficiency codes remain implementation choices.
