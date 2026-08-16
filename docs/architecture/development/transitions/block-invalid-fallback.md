# training.block-invalid-fallback — frozen fitting failure → typed block or predeclared fallback

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Prevent failure from silently changing preprocessing/model/feature procedure.

## Relevant locked invariants

I5–I6, I17, I22.

## Source A

Exact frozen recipe/component, W_t, failure facts/provenance, explicitly predeclared fallback graph if any.

## Destination B

Typed blocking failure or execution of exact declared fallback with identity/provenance; never an invented successful F_t.

## Mapping f

Classify failure; verify fallback is part of frozen identity and trigger; either execute it through training.fit-system or block.

## Must preserve

Original procedure, failure, trigger, fallback identity/order, window/environment, status.

## May transform

Equivalent representation may change where semantic identity and behavior survive.

## Must exclude

Nearest alternative, reduced dimensions, skipped feature, default model, agent repair under same frozen ID, partial F_t success.

## Authority boundary

Frozen spec owns allowed fallback; runtime cannot improvise.

## Allowed state mutation

Failure/artifact/ledger records; valid fallback fit records.

## Forbidden state mutation

No frozen definition mutation, false success, partial fitted system.

## Failure semantics

If no applicable predeclared fallback, hard typed failure blocks prediction/evaluation. Meaning-changing repair is new candidate.

## Observable consequences

PCA(10) failure cannot produce PCA(7) unless exact fallback was frozen.

## False-success implementations considered

Catch exception and reduce components; skip failed feature/model.

## Falsifying tests

Induce failure with/without declared fallback; assert block versus exact fallback identity. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Automatically reduce PCA components to available rank.

**Expected failure:** No-fallback case returns F_t, test red.

## Composite dependencies

training.fit-system/formalization.version-material-change/freeze.seal-system; backtest.execute-scenario records failures.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added trigger/order identity for declared fallback.

## Remaining user decisions

None.
