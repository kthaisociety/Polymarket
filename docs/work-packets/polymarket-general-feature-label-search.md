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
3. Compression receipt 03, SHA-256
   `829ff86c0bca350e2b4a004b7aa1286c8b8c6fd5d4725bd1ebb526c98cbeb2e9`, selected the seven-feature
   activity core. It beat the retained full model for magnitude (`0.002489/0.001125` versus
   `0.002578/0.001192`) and large moves (`0.131986/0.114559` versus `0.132994/0.117383`). Removing
   expiry materially weakened observation-weighted evidence. The subset-search budget is closed.
4. Attempting to preserve the selected cross-contract claim exposes adjacent formal-harness gaps:
   `AuthoredCandidateManifest` binds one exact dimension-value slice; authored programs receive no
   decision-time interface; and the registered formal catalog has no lifecycle close-time field.
   The research packet therefore adds a separate implementation dependency before formal replay.
   Protected data remains outside both packets.
5. Commit `8187784d` resolves the generic panel-population seam without broadening catalog or field
   authority. Historical time-to-expiry remains blocked: the current production close time is
   mutable and the retained source has no revision/availability clock. Formal replay therefore
   uses the already-tested six-feature no-expiry rival.
6. Formal authored panel receipt 04, source SHA-256
   `0c4fcbdb0b33fc55dd32a889b1d740337ebf516eef28de80aac436aa74221da5`, evaluated 459 declared
   development keys and produced 419 legal OOF predictions across 22 event groups. The fixed ridge
   improved observation MSE from `0.006012` to `0.005546`, event-macro MSE from `0.008803` to
   `0.008159`, and won 15/22 events. Its absolute MSE still failed the predeclared `0.003`
   credibility threshold, so it is retained as formal revise/negative evidence and is not
   freeze-eligible. Protected values remain unexposed.
7. Loss diagnostic attempt 05 was denied before any data access because the source called one
   unavailable runtime interface. Its denied receipt and zero-access provenance are retained.
   Corrected diagnostic 06, SHA-256
   `20445367ff299f2e8d7ce187b90de0e66bf8774d052dedd4be6b60a1936650f7`, exactly reproduced both
   formal MSE values. The largest 1%/5% of rows contribute 49.1%/79.8% of ridge loss; one market
   contributes 18.5% and the top five 54.6%. Moves of at least five cents have MSE `0.0350`, while
   near-absorbed contracts have MSE `0.000145` and central contracts have MSE `0.01667`.
8. The next trial budget is fixed at two materially distinct model recipes on the same exact legal
   features, label, sample, expanding maturity boundary, event weights, and penalty: (a) a
   five-cent large-move ridge gate mixed with fold-local conditional means; (b) the same gate mixed
   with fold-local conditional ridges, with an explicitly declared intercept-only warm-up until
   each regime has eight legal rows. Either candidate must beat the existing ridge under both
   observation and event-macro MSE, win a majority of event groups, and still satisfy absolute MSE
   `<= 0.003` to become credible. No threshold search or third mixture recipe is permitted in this
   family.
9. Hurdle receipt 07, SHA-256
   `8447428937ec57bc98b1db4941905287b0222fd0f46e9e0370c52e7590585fce`, exhausted that budget.
   Conditional means improved observation MSE only from `0.0055461` to `0.0055129`, won 8/22
   events, and remained above the absolute gate. Conditional ridges worsened MSE to `0.0058144`.
   Both are rejected before formalization; the threshold and recipes will not be searched further.
10. The next distinct label is the pre-existing fixed two-cent large-move indicator, not another
    magnitude-model revision. Its six-feature no-expiry linear-probability ridge retains penalty
    `0.1`, exact sample/maturity/event weights, and event-rate baseline. A pre-formal replay must
    achieve Brier/MSE `<= 0.15`, beat the baseline under observation and event-macro weighting, and
    win at least 12/22 event groups. This is one fixed classifier trial; the two-cent threshold was
    declared in benchmark 01 and is not retuned from formal loss diagnostics.
11. Classifier receipt 08, SHA-256
    `6f8f900131330ae0e315e879d143258cb39cebd76da4db6b91c19561c3c97273`, improved Brier from
    `0.20821` to `0.16278`, improved event-macro Brier from `0.21607` to `0.19697`, and won 16/22
    events. It nevertheless failed the fixed absolute `0.15` gate and is rejected before formal
    replay.
12. One ancestry-supported revision is permitted: benchmark 01's exact 11-feature no-expiry
    `state_plus_dynamics` set replaces the compact six-feature set while retaining the two-cent
    label, sample, folds, event weights, penalty `0.1`, and the same `0.15`/12-event gate. It adds
    raw probability, fixed-.005 logit state, 24-hour variance, bipower jump variation, and raw
    six-hour change; no expiry or newly selected interaction enters. Failure closes this classifier
    family before formalization.
13. State-plus-dynamics receipt 09, SHA-256
    `dc8d3348eb593e9c23f37684bd163d37a55e592b67fd09bab43785752e615948`, improved event-macro
    Brier to `0.18313` and won 16/22 events, but observation-weighted Brier was `0.17432`, worse
    than compact receipt 08's `0.16278` and above the fixed `0.15` gate. The bounded classifier
    family is closed as negative development evidence. Neither candidate proceeds to formal or
    protected evaluation.
