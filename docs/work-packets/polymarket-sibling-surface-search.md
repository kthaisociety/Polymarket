# Work packet: Polymarket sibling probability-surface search

## Identity

- Packet: `polymarket.test-sibling-probability-surface`
- Owning architecture block: development-only exploration, with conditional formalization.
- Semantic transition: retained development event panel → time-legal sibling-surface features →
  chronological candidate or retained rejection.
- Input repository state: `historical checkpoint 52fb551e` on
  `codex/polymarket-time-series-research`.

## Objective

Test whether other contracts sharing the authoritative Polymarket `event_id` contain stable
six-hour predictive information beyond a target contract's own state and path. This is a generic
co-movement hypothesis and does not assume event contracts are exhaustive or mutually exclusive.

## Context boundary

- Inputs are the exact retained 200-contract corpus and its existing whole-event partition: 24
  development events/155 markets, with the final 7 events/45 markets physically protected.
- The authored study runs through the public constrained Polymarket development analysis path.
- No external source, current database read, protected value, execution quote, or resolution payout
  is needed.
- Server `event_id` is authoritative grouping. Question text is available for interpretation but is
  not parsed into a taxonomy or feature.

## Frozen research design

- Population: development events with at least two contracts and legal target/sibling histories.
- Decisions: every six retained target observations after a 24-observation history. Target trailing
  span must be 18–30 hours and target future span 4.5–7.5 hours.
- Sibling alignment: for each target decision, use only the latest sibling observation at or before
  the decision and at or before six elapsed hours earlier. Exclude a row if any sibling is more than
  two hours stale or lacks the required trailing point. Never interpolate.
- Target-only features: probability, boundary distance, six-hour change, six-hour realized
  variance, 24-hour zero-change fraction, and 24-hour mean absolute change.
- Added sibling features: sibling count; mean, maximum, minimum, dispersion, and raw sum of current
  sibling probabilities; target-minus-sibling mean; target rank; mean and maximum absolute sibling
  six-hour change; and mean signed sibling six-hour change.
- Labels: signed six-hour probability change, absolute six-hour change, and fixed two-cent
  large-move incidence.
- Models: fold-standardized ridge with penalty `0.1`. For each test event, fit only earlier complete
  events with equal total weight per event. Compare the exact target-only and augmented recipes to
  label-appropriate naive controls (zero signed change; historical event-equal mean/rate).
- Gate per label: at least 12 chronological test events; augmented MSE below both controls under
  observation and event-macro weighting; improvement over target-only in both early and late test
  halves; wins on at least 60% of test events; and no one event contributes more than half of all
  positive event-level improvement. Signed change additionally requires directional accuracy above
  50% and above target-only on nonzero moves.

## Correctness

- Governing invariants: I1-I6, I9, I12-I14, I17-I18, and I21-I26.
- Failure modes: using future sibling observations; equating `event_id` with exclusivity; leaking
  protected event membership; letting large events dominate fitting; ordinal rather than elapsed
  time alignment; overlapping events crossing fold order; or selecting a subset after results.
- Counterexample: changing all protected values must leave the source, capabilities, and result
  unchanged. Moving a sibling observation one second after the decision must exclude it from that
  decision.
- Expected evidence: exact source/receipt, coverage and exclusion counts, both aggregate weightings,
  per-event deltas, early/late metrics, win counts, concentration, and actual access records.

## Completion evidence

- The fixed comparison ran through the governed development path. Signed movement and the
  two-cent large-move classifier failed their gates. Absolute six-hour movement passed.
- The one allowed compression trial selected the 14-feature `sibling_state` recipe: six target-path
  features plus sibling count, mean, maximum, minimum, dispersion, sum, target-minus-mean, and
  target rank. Sibling motion was rejected and is not carried forward.
- The selected recipe proceeded to exact authored formal replay and failed. Across 413 OOF
  predictions/20 event groups it worsened observation MSE (`0.00605519` versus `0.00601997`) and
  event-macro MSE (`0.00892503` versus `0.00883438`), worsened both chronological halves, and won
  only 8/20 events. The branch is retained as a formal development rejection and is not retuned.
- Ruff, strict typing, relevant tests, and coherent local commit remain green. No push or protected
  evaluation occurs.

## Boundary revisions

1. The fixed benchmark passed only for absolute six-hour movement. Before formalization, one
   bounded attribution/compression trial compares the unchanged 17-feature recipe with three exact
   rivals: sibling state only (target six plus indices 6–13), sibling motion only (target six plus
   indices 14–16), and compact joint (target six plus target-minus-mean, rank, and all three motion
   terms). The same folds, penalty, label, controls, and gates remain fixed. Select the fewest-feature
   passing recipe whose observation and event-macro MSE are each within 5% of the full recipe;
   ties resolve by feature count and then motion, compact joint, state, full. No further subset is
   allowed inside this packet.
2. Formalization exposed a generic harness seam: an authored candidate can declare exact
   sample-dimension history, but cannot declare contextual history matched on a strict subset such
   as `event_id`. The only permitted implementation change is an explicit, manifest-bound context
   dependency with declared matching dimensions, a separately tracked program interface, and
   causality/authority tests. It must not encode sibling selection, event semantics, or feature
   formulas in the harness. After that repair, the exact selected recipe is replayed against its
   six-feature baseline on the same sparse development panel. No protected evaluation is allowed.
3. The generic seam is implemented as a manifest-bound `ContextHistoryDependency` plus the
   separately audited `context_history(field_id)` worker interface. Application tests prove exact
   group matching, exclusion of an unreleased same-group poison observation, rejection of a match
   dimension absent from the field schema, public action decoding, and unchanged protected replay.
   The complete Chronos suite passes with 448 tests; Ruff and strict basedpyright are clean. This
   changes access mechanics only and does not make the sibling-state recipe credible by itself.
4. The formal replay is fixed before execution. It uses at most the first and last legal decision
   per development market to keep worker cost bounded while preserving at least 200 chronological
   OOF predictions. A decision requires the same 24-point/18–30-hour target history and original
   sibling-alignment cohort, plus a target observation 4.5–6 elapsed hours ahead so the authored
   six-hour horizon and exploratory label agree. The exact rivals are event-equal ridge `0.1` over
   the six target features and the selected 14-feature sibling-state recipe. The selected recipe
   must have MSE at most `0.003`, beat target-only under observation and event-macro weighting,
   improve both chronological event halves, win at least 60% of evaluated events, and have no one
   event supply more than half its positive event-level improvement. Failure is retained; there is
   no additional model or subset trial in this packet.
5. Formal attempt 04 failed before any candidate metric because 305 declared keys yielded fewer
   than the required 200 label-matured chronological OOF predictions. The source and failure
   receipt are retained; the sibling-state candidate never executed. One coverage-only revision is
   allowed: use first, middle, and last legal decisions per market, as in the earlier formal panel.
   The 200-prediction floor, data, features, label, model, penalty, gates, and protected boundary do
   not change. Lowering the evidence floor or changing the recipe is not allowed.
6. Coverage-safe attempt 05 completed both formal model evaluations, then its receipt diagnostic
   failed because it expected `event_chronological_ordinal` in `SampleKey.dimensions`; the formal
   price schema carries `event_id` and `market_id`. No metric was persisted or reconstructed from
   transient state. Source and failure receipt are retained. One reporting-only revision may order
   event groups by their earliest OOF decision time. Candidate source, exact 457 keys, evidence
   floor, scientific recipe, and gates remain unchanged.
7. Reporting-safe attempt 06 succeeded with 413 OOF predictions and exact context-history access
   provenance. The sibling-state recipe failed its predeclared gate: overall and event-macro MSE
   were worse than target-only, both early and late event halves worsened, only 8/20 events
   improved, and absolute MSE exceeded `0.003`. Positive improvements were not over-concentrated
   (`0.37736` maximum share), but that lone passing condition does not rescue the candidate. The
   packet is closed as a formal development rejection. Protected values remain unexposed.
