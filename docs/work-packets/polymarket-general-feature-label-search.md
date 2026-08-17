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
14. The next branch changes the scientific question from unconditional move magnitude to fixed
    boundary-transition hazards. Diagnostic 10 will use the already-declared absorption region
    `[0,.02] ∪ [.98,1]`, six-observation decisions, a 24-observation history warm-up, and only two
    fixed legal horizons: six observations with elapsed time 4.5–7.5 hours and 24 observations with
    elapsed time 18–30 hours. It will count, but not model, four conditional labels: interior to
    boundary (entry) and boundary to interior (escape) at each horizon. A label is model-eligible
    only when test events 8–23 provide at least 400 rows, 40 positives, 40 negatives, and both
    classes in at least 8 event groups. At most two eligible labels may advance, selected in the
    fixed economic priority `entry_24h`, `escape_24h`, `entry_6h`, `escape_6h`. The diagnostic may
    report side and event heterogeneity, but it cannot tune the `.02` boundary, invent another
    horizon, fit a model, or authorize protected access.
15. Coverage receipt 10, SHA-256
    `2191c8d1c116da54edadfa1e87349efc08cb82e9179946ca3859551d8e260952`, applied the fixed rule.
    All four labels met the numerical coverage gate, so the priority cap selected `entry_24h` and
    `escape_24h`. The OOF at-risk sets contain 5,192/238 entry rows/positives across 15 represented
    events and 2,607/106 escape rows/positives across 12 represented events. Transition direction
    is extremely asymmetric: 237/238 entries and 106/106 escapes involve the lower boundary. The
    labels therefore describe this retained outcome-token corpus, not a symmetric universal 0/1
    process.
16. The bounded model trial uses only those two selected labels and one fixed 11-feature state and
    boundary-kinematics representation: probability, boundary distance, fixed-.005 logit,
    six-/24-hour boundary-distance changes, six-/24-hour realized variance, jump concentration,
    zero-change fraction, mean absolute change, and log current-regime run length. Fold-local
    event-equal ridge-logistic models use penalty `0.1`; the nested state comparator uses only the
    first three features, and the other comparator is the earlier-event hazard rate. A full model
    may advance only if it beats both comparators under observation and event-macro Brier, beats
    state-only average precision under pooled and event-macro views, wins a majority of represented
    events versus state-only, places at least twice the unconditional positive rate in its fixed
    top-decile score set, and keeps its mean probability within a factor of two of the observed
    rate. No feature subset, penalty, boundary, horizon, or third model recipe may be searched in
    this family.
17. Model source 11, SHA-256
    `2b7b61352ea26e7cbfbe70e9e534f3d6deec112ab2326449e49660a9a58db7cf`, exceeded the sandbox
    wall-clock limit before any field access; its failed receipt is retained and contains zero
    accesses. Corrected child 12 changes no label, feature, penalty, fold, weight, comparator, or
    gate. It fixes the convex solver budget at eight Newton updates per fold, with no convergence
    test or data-dependent fallback, so the exact recipe can execute inside the analysis limit.
18. Eight-update child 12, SHA-256
    `1060d86bf23ca5e375b676e095fb49edac306a8191cac12373e45634bab1262b`, also reached the wall-clock
    limit before any field access. Final runtime child 13 retains the exact scientific design and
    fixes four Newton updates. This is the last runtime-only retry: another timeout closes this
    logistic implementation route rather than weakening the analysis limit or changing recipes.
19. Four-update child 13, SHA-256
    `c00d6ae9595c267f0d92d56dcd4a1d1628f538cfe0d741bfdb45035bb9552c83`, completed with exact
    ancestry. For entry, full kinematics improved observation/event Brier to `0.03716/0.07259` and
    pooled average precision to `0.3522`, but event-macro average precision fell from state-only
    `0.5083` to `0.4776`; the fixed gate therefore failed. For escape, state-only was better than
    full kinematics under observation/event Brier (`0.04780/0.05061` versus `0.05275/0.05630`) and
    pooled/event average precision (`0.2279/0.3541` versus `0.1561/0.3484`). Both exact candidates
    are rejected before formalization. The remaining strong state-only ranking is selection-exposed
    hypothesis evidence, not an eligible model, and the kinematics family is closed.
