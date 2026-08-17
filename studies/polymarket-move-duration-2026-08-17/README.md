# Time to next meaningful probability move

Epistemic status: **FROZEN DEVELOPMENT CANDIDATE — EXACT PROTECTED PLAN REPLAY REQUIRED —
PROTECTED DATA UNEXPOSED**.

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
authored replay was therefore required before any freeze decision.

## Formal authored replay

Formal source 03 evaluated the event-equal mean, exact state-only ridge, and selected state-staleness
ridge over the same 1,053 declared keys. The authored evaluator produced 1,013 legal expanding OOF
predictions across 22 event groups:

- event-equal mean observation/event-macro MAE: `0.37797/0.37575`;
- state-only observation/event-macro MAE: `0.25945/0.25928`;
- state-staleness observation/event-macro MAE: `0.21633/0.21683`;
- state-only observation/event-macro MSE: `0.10689/0.10471`;
- state-staleness observation/event-macro MSE: `0.08621/0.08177`;
- state-staleness early/late event-macro MAE: `0.22280/0.21087`, versus
  `0.26760/0.25096` for state-only;
- event wins versus state-only: 18 of 22; largest positive improvement share: `0.12924`;
- 467 capped and 546 uncapped outcomes, with 16 mixed event groups;
- mean prediction `0.60123` versus mean outcome `0.59824`.

Every predeclared formal credibility condition passed. Actual accesses show features used only
`history(market_probability)`, labels used that history plus `outcome_path()`, fitting used only
`training_rows()`, and prediction used only `feature_values()` plus `model_state()`.

The direct-evaluator request did not carry a protected protocol predeclaration, and
`AuthoredFreezeService` correctly refused to freeze that request. Source 04 then predeclared the
exact protected data scope, decision-time rule, training protocol, evaluation protocol, validation
standard, claim template, and freeze standard before replaying the same three authored models
through `RuntimeInvestigationCoordinator`.

The replay reproduced the exact selected candidate
`authored-candidate:bb76fb6846cd5bb935934e16d53c520865f5649d230c53b0cc1ca5c3e1be770d`
and evidence
`authored-development-evidence:7729af09c56fed64323cc805df708ab2643ec547aa90877dda30e53a6e9c5372`.
An independently identified freeze authority accepted the predeclared gate and sealed
`frozen-system:65af99a116e6ddabc965b7317ac18162665d05501f0fb77aec6b6b2a6ac19c42`.
This is a frozen development identity, not protected validation or a trading claim. No protected
values were loaded and no protected backtest was run.

A subsequent [backtest-gate audit](../../docs/work-packets/polymarket-move-duration-protected-gate.md)
found that source 04 froze readable protocol aliases rather than the content identities required by
an authority-issued `AuthoredProtectedPlan`. Chronos correctly cannot resolve those aliases into a
protected request. The scientific candidate remains frozen, but this frozen protocol binding is not
protected-ready. The unchanged development ancestry must be replayed with the exact issued plan
identities and independently frozen again; the existing frozen identity may not be edited.

The exact three-model run took about 38 minutes because every feature, label, fit, and prediction
phase starts a separate constrained worker. That is a demonstrated autonomous-loop throughput seam,
not a reason to weaken the scientific sample or gate.

## Exact evidence

- Benchmark source SHA-256:
  `4ba45fc9c8c47b34cb874ad11c320f34a45787f11484be98a40eb44aef0daf98`.
- Benchmark receipt SHA-256:
  `8fa132aaa799b3d4050e039a395aef18f6821efd0a0221a7005a20b012c9695e`.
- Compression source SHA-256:
  `1128d26eb4c51e11b61a77f2b6d1db80b58e71b02abf638f99b4e1ae3cac21d1`.
- Compression receipt SHA-256:
  `d8694d86d9a788fba41a709f4f06a014446ef8b10797248bc68642ea12e2e25d`.
- Formal driver SHA-256:
  `98ebb1311edd5b65fb33ee83d393f7ad6a976248dcf411bc8958fa1c1e334206`.
- Formal receipt SHA-256:
  `bccc524a0600b04a29fffa6ea82bdafdfe6a57856f7793eb57b0907661376690`.
- Coordinator freeze-replay driver SHA-256:
  `58ae71b26d7736f53843e514019a06cfbfe3b154e0bb3575994670ab6b5cc3be`.
- Coordinator freeze-replay receipt SHA-256:
  `00a7d84ab97be39f83e36206137cf88a40a1e372e14ecfa750e0ccd599a5ccd4`.
- All executions accessed only development price identity, event ordinal, observation ordinal/time,
  and sampled probability; all report `protected_values_exposed=false` and no protected run.
