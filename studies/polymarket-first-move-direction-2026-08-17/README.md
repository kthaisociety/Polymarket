# Polymarket first-move direction

Epistemic status: **EXPLORATORY — PROTECTED DATA UNEXPOSED**.

This study asks whether legal path direction predicts the sign of the first retained two-cent move
within 48 elapsed hours, beyond probability state and earlier-event drift. It deliberately starts
from the retained development corpus and does not inspect the active duration holdout.

The exact sampling, signed label, feature groups, chronological folds, predictive gate, and delayed
long-only sampled-price falsifier were fixed before reading development values in the
[work packet](../../docs/work-packets/polymarket-first-move-direction.md).

## Startup memo

- Scope: exact retained corpus `610b8b9d…`, whole-event development partition `49d5e9a9…`, 24
  development events/155 markets, with all seven protected events/45 markets omitted.
- Authorized fields: market identity, chronological event ordinal, observation ordinal/time, and
  sampled market probability.
- Label: `-1`, `0`, or `+1` for the first downward crossing, no crossing, or first upward crossing
  of two cents within a complete 48-hour sampled path.
- Mechanism: recent path direction may persist into a meaningful move after a quiet/stale interval.
- Rivals: martingale-like direction, probability-boundary asymmetry, resolution drift, transient
  sampling reversal, and event concentration.
- Explicit exclusions: fills, quotes, midpoint, spread/depth, protected values, external data,
  payout, causal claims, and executable PnL.
- First falsifier: one-event-ahead event-equal ridge comparisons with early/late and per-event views;
  a one-observation-delayed, one-cent-cost long-only diagnostic is reported separately.

No formal candidate, freeze, protected request, validation, finding, or terminal memory is created
by this memo or the exploratory run.

## Attempt 01

Source 01 was denied before data access because its final result projection used the unavailable
Python `del` statement. The denial is retained with source SHA-256 `6bffa141…`; actual accesses are
empty and protected values remain unexposed. A meaning-identical revision may remove only that
cleanup statement before retrying.
