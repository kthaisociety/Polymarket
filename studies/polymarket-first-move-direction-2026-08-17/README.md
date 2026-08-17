# Polymarket first-move direction

Epistemic status: **DEVELOPMENT REJECTION — PROTECTED DATA UNEXPOSED**.

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

## Policy-safe result

Source 02 changed only the forbidden result-cleanup expression and passed the fixed harness policy.
The exact design produced 1,053 development decisions and 975 OOF rows, including 278 upward and
229 downward first crossings across 15 mixed-direction test events.

| Model | Observation MSE | Event-macro MSE | Crossing direction accuracy |
|---|---:|---:|---:|
| Zero expected signed move | `0.52000` | `0.63189` | — |
| Earlier-event mean | `0.57565` | `0.64954` | `0.54832` |
| Probability state | `0.57299` | `0.64101` | `0.54832` |
| State plus recent direction | `0.58787` | `0.66259` | `0.54832` |
| Direction after staleness | `0.60322` | `0.67101` | `0.54635` |

The candidate lost to every comparator, won only 4/15 events against state, failed both halves,
and predicted a mean signed label of `0.32271` when the observed OOF mean was `0.05026`. Recent path
direction and its fixed staleness interactions therefore do not supply a stable first-move
direction mechanism under this design.

The separate delayed long-only diagnostic generated 948 sampled trades. Its equal-event mean net
change after a one-cent cost was `+0.00827`, but its observation-weighted mean was `-0.00280`; two
large events supplied most trades and were negative. The fixed execution gate failed. Because
these are sampled probabilities rather than bid/ask quotes, even a pass would have been only an
execution candidate, not tradability evidence.

No model is formalized or frozen. The final seven protected events remain unavailable, and the
active duration holdout was not inspected or used.

## Exact evidence

- Denied source SHA-256: `6bffa141739a454b0290b46ac605831e30f1be23b463f015dbe80895fb5f95ea`.
- Policy-safe source SHA-256: `0083bba4b070b4bf439e8a044b2c9a7ad842762a361c48e77b662579b57cbfe7`.
- Successful receipt SHA-256: `22cc473b7c2397744c9729cd59afbd9a1a1c2b03e69d4ef51c4d170a2156e33d`.
- Actual accesses: market identity, chronological event ordinal, observation ordinal/time, and
  sampled probability only; protected exposure is false.
