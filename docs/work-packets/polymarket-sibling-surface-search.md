# Work packet: Polymarket sibling probability-surface search

## Identity

- Packet: `polymarket.test-sibling-probability-surface`
- Owning architecture block: development-only exploration, with conditional formalization.
- Semantic transition: retained development event panel → time-legal sibling-surface features →
  chronological candidate or retained rejection.
- Input repository state: `bdl-polymarket@52fb551e` on
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
- The selected recipe may proceed to an exact authored formal candidate; failed labels and feature
  groups are retained and are not retuned inside this packet.
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
