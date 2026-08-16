# data.select-training-window — TrainingSample S_t + frozen TrainingWindowPolicy → TrainingWindow W_t

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Select exactly the declared legal fitting subset from completed examples without learning, optimizing the policy from results, or silently changing window semantics.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I2, I5–I6, I17, I24.
- `docs/specification/SCIENTIFIC_KERNEL.md`, Training-window policy.

## Source A

Immutable `TrainingSample S_t`, exact frozen/versioned `TrainingWindowPolicy`, decision time, candidate system/environment identity, and required minimum-sample semantics.

## Destination B

Immutable `TrainingWindow W_t`: exact selected sample identities/order/bounds, policy/version, decision time, exclusions, provenance, or typed insufficiency/failure.

## Mapping f

Apply the declared expanding/rolling/other deterministic selection rule to eligible `S_t`; validate bounds/minimums; preserve row identities/order and policy provenance; emit selected view. Do not fit, rank by outcome quality, or choose another policy.

## Must preserve

Sample identity, legal eligibility, row/time identity, order, policy kind/parameters/version, current `t`, environment/system provenance, and insufficiency meaning.

## May transform

Eligible sample into a selected subset/view; physical slicing/index representation is free.

## Must exclude

Rows outside `S_t`, future/immature rows, outcome-driven window tuning, hidden fit/selection, fallback from rolling to expanding, latest policy substitution, silent minimum relaxation, and source mutation.

## Authority boundary

Frozen policy determines selection. Window selector cannot learn or repair policy; meaning-changing repair creates a new policy/candidate upstream.

## Allowed state mutation

Create immutable window/provenance and explicit insufficiency record.

## Forbidden state mutation

No sample/policy/definition mutation, fitting, prediction, evaluation, or evidence status change.

## Failure semantics

Insufficient rows, invalid bounds, unavailable required history, or policy execution failure blocks fitting explicitly. No undeclared fallback or partial “best effort” window.

## Observable consequences

Given the same `S_t` and policy/version, selection is equivalent; rolling and expanding policies select visibly different exact identities. Insufficiency prevents training.fit-system.

## False-success implementations considered

- Select latest N regardless of declared policy.
- Tune window using target performance.
- Fall back to all history on insufficiency.
- Resolve latest policy version.
- Reorder/drop rows during selection.

## Falsifying tests

1. Apply contrasting frozen rolling/expanding policies to one sample and assert exact selected identities/order. **Level A.**
2. Fail-on-fit/evaluator doubles prove selection performs no learning/performance query.
3. Insufficient-history fixture yields typed failure and zero trainer invocation.
4. Publish newer policy and assert historical explicit policy/version remains unchanged.

## Mutation-sensitivity check

**Mutation:** silently use all available history when the declared rolling window is insufficient.

**Expected failure:** tests 1/3 become red because selected identities or failure outcome differ.

## Composite dependencies

data.build-training-sample supplies legal sample; system.assemble-definition freezes policy in system identity; training.fit-system fits exact window; data.prove-temporal-substrate composes insufficiency behavior.

## Fundamentals review

`CONSISTENT`. Deterministic selection preserves identity and blocks undeclared scientific fallback.

## Grill findings

Resolved non-semantically: added no-performance-query and explicit-policy-version attacks.

## Remaining user decisions

None. Concrete window policies are scientific-spec inputs, not chosen by this seam.
