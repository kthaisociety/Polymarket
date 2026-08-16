# data.prove-temporal-substrate — registered data + target/window policies across decision times → legal temporal substrate

## Status

`CANDIDATE_CONSENSUS` — experimental composite contract, not canonical.

## Architectural purpose

Prove end to end that physical data becomes exact, provenance-bearing legal information, mature samples, and declared fitting windows across simulated time, with explicit insufficiency and no leakage/fallback.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I1–I3, I6, I17, I23–I26.
- `docs/specification/DATA_FLOW_AND_LIFECYCLE.md` 5.1–5.4.
- `docs/specification/TEST_STRATEGY.md`, publication-delay, target-maturity, global-scaler, and dual-boundary fixtures.

## Source A

Immutable source fixture with release delays/revision/missingness, exact schema/registration policy, permissions/environment, target definition, formal non-learned features, training-window policy, and decision-time sequence.

## Destination B

For every time: exact registered observation provenance, `I_t`, completed `S_t`, `W_t` or typed insufficiency, with reconstructible membership/exclusions and no downstream trainer invocation when illegal/insufficient.

## Mapping f

Compose data.register-observations–data.advance-independent-clocks in order for each explicit time; discard no history; verify identities/provenance across boundaries; stop on explicit failure; expose outputs to fail-on-illegal-access/fitting downstream doubles.

## Must preserve

Source integrity; field/schema/version; both time axes; vintage/revisions; permissions; target maturity/alignment; feature/sample/window identity; exclusions/failure; environment provenance.

## May transform

Physical data through the declared semantic/legal views. No new production object is required for this composite proposition.

## Must exclude

Future/revised/unreleased data, immature labels, global fitting, current-vintage historical backfill, silent row/window fallback, field substitution, stale view reuse, and claims that a timestamp column alone proves legality.

## Authority boundary

Each local seam retains authority; the vertical slice only orchestrates and verifies. It grants no model, trainer, or evaluator authority.

## Allowed state mutation

Immutable registered observations and derived view/provenance records permitted by local seams.

## Forbidden state mutation

No source/definition rewrite, learned state, prediction/evaluation, protected exposure, or promotion.

## Failure semantics

Any missing availability/maturity/schema/provenance/policy or insufficiency is explicit at its boundary and blocks later steps. Later steps cannot substitute defaults or reuse a stale prior view as current success.

## Observable consequences

The publication-delay row appears only after release; label appears only after maturity; revision only after revision availability; `W_t` follows exact policy; insufficient early times produce no fit-ready window.

## False-success implementations considered

- Tests each endpoint independently but downstream reads raw fixture directly.
- Use row timestamp as all time semantics.
- Fit preprocessing while constructing sample.
- Replace early insufficiency with expanding full-history window.
- Recompute history using latest revision.

## Falsifying tests

One adversarial multi-time vertical slice uses no raw-data side channel after registration. Assert exact membership/provenance at each boundary, independent predictor/label changes, early insufficiency, later legal window, unchanged raw bytes, and zero fitting. **Level B.**

## Mutation-sensitivity check

**Mutation:** construct `I_t`, `S_t`, and `W_t` directly from rows with `reference_time <= t`, ignoring availability, maturity, and declared window policy.

**Expected test failure:** multiple time-specific membership and insufficiency assertions become red.

## Composite dependencies

Participating local seams data.register-observations–data.advance-independent-clocks. training.fit-system and backtest.execute-scenario later consume the legal substrate but are excluded from this proof.

## Fundamentals review

`CONSISTENT`. It proves the composed temporal arrow without inventing a simulation-clock subsystem or claiming fitting/backtest correctness.

## Grill findings

Resolved non-semantically: removed direct-raw-data side channels and required early insufficiency plus revision provenance, which endpoint-only tests could miss.

## Remaining user decisions

None. Exact fixture values and view representations remain free.
