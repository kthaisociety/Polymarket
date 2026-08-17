# Work packet: general Polymarket feature and label search

## Identity

- Packet: `polymarket.search-general-internal-feature-label-space`
- Owning architecture block: exploration with conditional formalization/development.
- Responsibility: development corpus → mechanism-group feature/label evidence → retained rejection
  or exact authored candidate.
- Input state: `bdl-polymarket@ae83ad9d` on `codex/polymarket-time-series-research`.

## Objective

Test whether general internal Polymarket state, expiry, diffusion/jump, path, or interaction features
improve multiple legal six-hour labels across chronological event groups.

## Context boundary

- Loaded: global authority, Polymarket boundary, exploration/formalization/development maps, and the
  analysis, feature-design, and work-packet skills.
- Data: exact retained corpus `polymarket-corpus:610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f`;
  whole-event partition `49d5e9a97985a44e3277f43ee55ce1281c430a1d0a1823754a9a759ac56d3bd1`.
- Excluded: protected 7 events/45 markets, production writes, executable-price claims, external
  data, Kthais/engine/sibling changes, and post-result threshold search.
- Assumption: retained sampled probabilities, exact lifecycle close times, and server event identity
  carry only the semantics registered by the adapter.

## Change boundary

- Permitted: authored study sources/receipts, study report, narrow run-exposed Chronos repairs with
  regression tests, and coherent local commits.
- Allowed effects: development-only constrained execution and repository evidence.
- Forbidden effects: protected exposure, privileged approval, validated-memory mutation, or silent
  model/feature fallback.

## Correctness

- Invariants: I1-I6, I9, I12-I14, I17-I18, I21-I26.
- Failure modes: overlapping horizons presented as independent rows; terminal boundary persistence
  mistaken for direction; time-to-expiry proxying event composition; jump proxy dominated by stale
  sampling; fitting or scaling across test events; label imbalance hidden by accuracy; searching
  thresholds after results.
- Sampling: decisions every six retained observations, 24-observation warm-up, trailing span 18–30
  hours, future-six span 4.5–7.5 hours.
- Folds: event ordinal 8–23 tested once using only earlier events, equal total training weight per
  event.
- Fixed features: probability level, distance to 0/1, fixed 0.005-winsorized logit level, current
  boundary state, log(1+hours-to-close), 6/24-hour realized variance, 24-hour bipower jump
  variation, jump concentration, zero-change fraction, six-hour change, and three mechanism
  interactions.
- Labels: six-hour signed change, absolute change, large move `abs(change) >= 0.02`, and future
  boundary state at `[0,.02] ∪ [.98,1]`.
- Models: fixed-penalty 0.1 fold-standardized ridge for state, state+expiry, dynamics, and full
  feature groups; zero/earlier-event-mean/current-boundary baselines as appropriate.
- Completion: exact source/receipt, actual accesses, group metrics under event and observation
  weighting, win counts, exclusions, result interpretation, full tests/static checks, local commit.

## Boundary revisions

1. Benchmark 01 passed the opening development gate for absolute-move and fixed two-cent large-move
   labels, while direction and future-boundary labels failed. The packet remains inside the same
   data/authority boundary and adds a fixed feature-group attribution diagnostic before any
   formalization. It will compare stand-alone and leave-group-out contributions without changing
   the horizon, threshold, penalty, folds, or protected scope.

## Evidence to date

- Source/receipt: `01_general_feature_label_benchmark.py/json`, SHA-256
  `16fefb285aa33cc016deae54a18f9ee9542ba533f3c3f3b8c1a2b4abcddd7d91`.
- Actual accesses: development market/event/ordinal/time/probability and development lifecycle close
  time only; protected exposure is false.
- 8,945 legal development samples, 424 irregular exclusions, 8,049 out-of-fold predictions per
  model/label across event ordinals 8–23.
- Full interactions improved absolute-move MSE from `0.003304/0.002202` to
  `0.002578/0.001192` under event/observation weighting and won 13/16 events.
- Full interactions improved large-move Brier/MSE from `0.193291/0.174323` to
  `0.132994/0.117383` and won 14/16 events.
- All signed-change and future-boundary models failed their baselines and are retained rejections.
- Attribution receipt 02, SHA-256
  `08cd78ffac3f553b311bfdb391b81a845d95296e377f496adcdc9d7fbe2448ea`, reproduced the exact sample
  and retained per-event rates/deltas. Boundary distance, 6/24-hour variance, jump concentration,
  zero-change fraction, and trailing mean absolute change passed both-half concentration gates for
  both surviving labels. Expiry passed for magnitude but not late-half binary stability; raw change
  and jump×expiry failed.
- Coverage remains heterogeneous (1–2,292 rows per test event; binary label rates 0%–76.6%). This
  does not negate agreeing event/observation metrics, but it blocks a broad homogeneous-process
  interpretation.

## Trial budget revision

2. Attribution supports a final three-recipe compression trial: a seven-feature activity core,
   the same core without expiry, and the existing full-interaction recipe. Horizon, labels,
   sampling, folds, penalty, and gates remain fixed. No additional subset search is permitted before
   a retain/reject/formalize decision.
