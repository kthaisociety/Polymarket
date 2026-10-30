# Work packet: authored panel population evaluation

## Identity

- Packet: `investigation.evaluate-authored-panel-population`.
- Owning architecture block: autonomous authored investigation, adjacent to development and
  protected evaluation.
- Responsibility: authored candidate plus a declared population-dimension schema → legal
  per-slice histories, labels, fits, predictions, and immutable evidence across multiple entities.
- Input state: `historical checkpoint 302ebfa1` on `codex/polymarket-time-series-research`.

## Objective

Allow one exact authored scientific program to be developed across authorized contract slices and,
after independent freeze and governance, replayed on unseen slices with the same dimension schema.
Each invocation must remain restricted to the current `SampleKey` slice.

## Context boundary

- Loaded: global authority, canonical context, locked decisions and invariants, architecture map,
  authored-investigation contract, owning and adjacent implementation maps, formalization and
  development transition contracts, and the work-packet skill.
- Run-exposed failure: the selected general Polymarket activity model is a cross-contract claim,
  while `AuthoredCandidateManifest.population_dimensions` currently binds one exact value tuple.
  Replaying one contract would change the scientific population instead of formalizing the tested
  claim.
- Explicitly excluded: new data authority, decision-time capability, mutable lifecycle metadata,
  event-group fold invention, model libraries, production writes, and protected-data exposure.
- Availability finding: the retained corpus contains the current contract `close_time`, but the
  production market row is updatable and the retained source has no close-time revision history.
  This packet therefore does not register current close time as historically observable expiry.

## Change boundary

- Permitted: authored manifest population semantics, proposal schema/decoder, development and
  protected authored evaluators, focused tests, implementation documentation, and this packet.
- Allowed state effects: new immutable candidate/evidence identities and local test artifacts.
- Forbidden effects: wildcard field access, cross-slice histories, caller-authored catalog scope,
  automatic protected authorization, altered legacy exact-slice meaning, or silent population
  fallback.

## Correctness

- Governing invariants: I1-I8, I11-I13, I17, I21-I24, and I26.
- Exact-slice mode remains the default and continues to require exact dimension names and values.
- Panel mode declares only the complete canonical dimension-name schema. Every requested
  `SampleKey` must match that schema; every candidate field must resolve to the same schema.
- History and outcome construction filter observations by the current key's complete dimension
  values. A program never receives another slice through the same invocation.
- Development ordering is deterministic by `(decision_time, dimensions)`. Label maturity, not row
  order alone, controls training admission.
- Protected replay accepts new dimension values only under the frozen schema and authority-issued
  protected scenario/catalog; it does not broaden catalog or field authority.
- Exact values and schema-only populations are mutually exclusive candidate meanings and therefore
  have different immutable identities.

## Regression evidence required

1. One development candidate consumes two same-schema populations, produces evidence for both,
   and cannot observe one population while computing the other's feature or label.
2. A missing, extra, or renamed sample dimension and a field with a different schema fail before
   scientific execution.
3. Existing exact-slice and dimensionless candidates retain their behavior.
4. Protected authored replay can evaluate an authority-declared new population value with the same
   frozen schema, while a schema mismatch becomes typed per-decision failure.
5. Focused tests, complete Chronos tests, formatting, lint, and static typing pass.

## Transition receipt

### Result

- Status: **COMPLETE**.
- Resulting state: the local commit containing this receipt on the existing branch.

### Delivered state delta

- Added mutually exclusive exact-slice and complete schema-only panel population identities to
  `AuthoredCandidateManifest`.
- Candidate publication now verifies every panel field against the declared complete schema.
- Development and protected authored evaluators admit schema-compatible entity values while
  filtering histories and outcomes to each current key's exact values.
- Runtime action decoding and provider schema expose the new generic manifest meaning without
  making it mandatory for legacy exact-slice candidates.
- Preserved current contract close time as exploratory-only metadata because no historical
  close-time revision/availability record exists. No false expiry predictor was registered.

### Evidence

- A two-market development adversary uses levels `1` and `100`; both retain perfect predictions,
  proving that one market's history does not replace the other's.
- Candidate publication rejects a field whose dimensions differ from the panel schema and the
  manifest rejects mixed exact-value/schema-only meaning.
- The existing full protected application acceptance now develops on `development-market` and
  executes the same exact frozen source on `protected-market`, while retaining all freeze,
  governance, exposure, evaluation, validation, negative-result, and memory checks.
- Focused Ruff and 16 authored investigation/protected/program tests passed. Repository-wide gate
  evidence is recorded in the commit verification that closes this packet.

No protected Polymarket values were authorized or exposed by this packet.
