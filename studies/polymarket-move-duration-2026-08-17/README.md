# Time to next meaningful probability move

Epistemic status: **EXPLORATORY DEVELOPMENT CANDIDATE — FORMAL REPLAY PENDING — PROTECTED DATA
UNEXPOSED**.

This study asks whether legal decision-time path persistence predicts elapsed time until the next
retained Polymarket probability at least two cents away from its current level. It does not predict
direction, resolution, executable returns, or continuous-time first passage.

The exact design, trial budget, and gates are frozen in the
[work packet](../../docs/work-packets/polymarket-move-duration-search.md).

## Design and coverage

Decisions use a 24-observation history and are at least 48 elapsed hours apart, so their future
windows do not overlap within a market. The label is sampled elapsed time to the first two-cent
displacement, capped at 48 hours and divided by 48. Event ordinals 8–23 are evaluated once using
only earlier events, with equal total fit weight per event.

The exact development sample contains 1,053 decisions from 22 events. Chronological evaluation
produced 975 OOF rows across 15 test events, including 507 uncapped crossings and 13 events with
both capped and uncapped labels. The final 7 events/45 markets were not exposed.

## Benchmark result

- Earlier-event mean: observation/event-macro MAE `0.43560`/`0.39391`.
- State-only ridge: observation/event-macro MAE `0.34335`/`0.28272`.
- Ten-feature path-persistence ridge: observation/event-macro MAE `0.27104`/`0.24085`.
- The full model improved both chronological halves, won 12/15 events against state-only, and had
  largest positive-improvement share `0.19479`. It passed every predeclared advancement gate.

## Mechanism compression

The one permitted compression trial selected the five-feature `state_staleness` representation:
probability, boundary distance, fixed-.005 logit, trailing 24-step zero-change fraction, and log one
plus trailing quiet-run hours under the fixed `.005` step threshold.

- Compact state-staleness MAE: observation `0.27627`, event macro `0.24071`.
- It improved both chronological halves and won 12/15 events against state-only.
- Volatility/activity alone passed the original relative gate but fell outside the fixed 5% full
  observation-MAE tolerance.
- Signed six-hour path failed the original gate.
- Adding volatility/activity and signed path did not materially improve the compact model.

The retained hypothesis is therefore narrow: recent sampled-price staleness predicts future sampled
first-passage time. This may be useful for modeling update/movement timing, but it may also reflect
the retained observation process. It is not a trading or directional claim. One exact formal
authored replay is required before any freeze decision.

## Exact evidence

- Benchmark source SHA-256:
  `4ba45fc9c8c47b34cb874ad11c320f34a45787f11484be98a40eb44aef0daf98`.
- Benchmark receipt SHA-256:
  `8fa132aaa799b3d4050e039a395aef18f6821efd0a0221a7005a20b012c9695e`.
- Compression source SHA-256:
  `1128d26eb4c51e11b61a77f2b6d1db80b58e71b02abf638f99b4e1ae3cac21d1`.
- Compression receipt SHA-256:
  `d8694d86d9a788fba41a709f4f06a014446ef8b10797248bc68642ea12e2e25d`.
- Both executions accessed only development price identity, event ordinal, observation ordinal/time,
  and sampled probability; both report `protected_values_exposed=false` and no durable effects.

