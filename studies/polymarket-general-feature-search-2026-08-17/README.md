# General internal Polymarket feature and label search

Epistemic status: **ACTIVE DEVELOPMENT RESEARCH — PROTECTED DATA UNEXPOSED**.

This cycle tests whether reusable internal path structure predicts several six-hour outcomes across
the 24 development events/155 markets. The final 7 events/45 markets remain unavailable.

## Frozen first benchmark

Decisions are spaced by six retained samples. A row is legal only when its trailing 24 samples span
18–30 hours and its future six samples span 4.5–7.5 hours. Event ordinals 8–23 are tested once after
fitting only earlier events, with equal total training weight per event.

Feature groups are nested: state; state plus expiry; state plus diffusion/jump path; and full state,
expiry, path, and fixed interactions. Labels are six-hour signed change, absolute change, a fixed
two-cent large-move indicator, and future membership in `[0,.02] ∪ [.98,1]`. Fixed-penalty ridge is
compared with label-appropriate naive baselines. The benchmark is rejected for a label unless it
improves both event-macro and observation-weighted MSE and wins at least 10/16 test events. A
boundary-state result must also beat current-boundary persistence.

This benchmark predicts sampled probability paths. It does not establish execution, directionally
tradable alpha, or protected validity.

See the [work packet](../../docs/work-packets/polymarket-general-feature-label-search.md).

## Benchmark 01 result

The harness admitted 8,945 development samples and excluded 424 irregular windows. Each of the 16
test events produced out-of-fold evidence; 8,049 test predictions were scored per label/model.

| Label | Naive baseline MSE (event / observation) | Best group | Best MSE (event / observation) | Event wins |
|---|---:|---|---:|---:|
| signed six-hour change | 0.003242 / 0.001539 | none | all groups worse | at most 6/16 |
| absolute six-hour change | 0.003304 / 0.002202 | full interactions | 0.002578 / 0.001192 | 13/16 |
| two-cent large move | 0.193291 / 0.174323 | full interactions | 0.132994 / 0.117383 | 14/16 |
| future boundary state | 0.025000 / 0.021369 | current-boundary persistence | all groups worse | 4/16 |

The direction and future-boundary hypotheses are rejected at this stage. Internal state, expiry,
diffusion/jump, and interaction features contain repeatable information about **movement magnitude
and large-move incidence**, not the sign of the move. State plus expiry was especially effective
for magnitude (`0.001249` observation-weighted MSE), while dynamics and interactions contributed
more to the large-move label.

This result survives the opening gate but is not yet formalized. The next frozen diagnostic compares
stand-alone and leave-group-out features for magnitude and large-move labels, reports per-event
label rates and error deltas, and checks whether improvement is dominated by expiry, one jump proxy,
boundary persistence, or a small number of events. No threshold or penalty will be retuned.

## Frozen attribution diagnostic 02

The sample, six-hour horizon, two-cent threshold, event folds, and equal-event fitting remain
unchanged. Thirteen scalar OLS candidates are tested independently: boundary distance, current
boundary state, expiry, 6/24-hour variance, bipower jump variation, jump concentration, zero-change
fraction, six-hour change, mean absolute change, boundary×expiry, jump×expiry, and boundary
closeness×variance. Predictions are clipped only where label support requires it.

For each magnitude and large-move candidate, the receipt retains all 16 event MSE deltas, early
(events 8–15) and late (16–23) macro MSE, event win count, and the largest event's share of total
positive improvement. A mechanism is attribution-credible only if it beats the baseline under both
aggregate weightings, wins at least 10/16 events, improves both halves, and no single event supplies
more than half of all positive event-level improvement. Nested group comparisons from benchmark 01
remain the leave-group evidence; this diagnostic supplies the complementary stand-alone view.

## Attribution diagnostic 02 result

The common sample reproduced exactly: 8,945 development rows, 424 irregular exclusions, and the
same 16 test events. Stand-alone results show that the full model is not driven by one mysterious
jump statistic.

| Feature | Magnitude MSE (event / observation) | Wins | Large-move MSE (event / observation) | Wins |
|---|---:|---:|---:|---:|
| baseline | 0.003304 / 0.002202 | — | 0.193291 / 0.174323 | — |
| boundary distance | 0.002833 / 0.001792 | 11/16 | 0.160800 / 0.140096 | 12/16 |
| time to close | 0.003091 / 0.001591 | 12/16 | 0.191545 / 0.159259 | 10/16 |
| variance 6h | 0.003173 / 0.002041 | 14/16 | 0.188895 / 0.169676 | 15/16 |
| variance 24h | 0.003072 / 0.001937 | 14/16 | 0.187110 / 0.166640 | 14/16 |
| bipower jump variation | 0.003131 / 0.001908 | 14/16 | 0.190581 / 0.167638 | 12/16 |
| jump concentration | 0.003239 / 0.002092 | 11/16 | 0.190661 / 0.169091 | 11/16 |
| zero-change fraction | 0.002980 / 0.001972 | 14/16 | 0.152502 / 0.140526 | 15/16 |
| trailing mean absolute change | 0.002740 / 0.001616 | 15/16 | 0.157228 / 0.135116 | 15/16 |

Raw six-hour change and jump×expiry failed. Boundary×expiry improved event-macro magnitude but made
observation-weighted magnitude worse, so it also failed the frozen gate. Time-to-close improved the
binary label in aggregate but failed late-half event stability. Bipower jump variation missed that
late-half binary gate by a small amount. The robust common mechanism is therefore **activity state
and staleness persistence conditioned by boundary/expiry state**, not directional drift and not a
clean continuous-time jump-diffusion claim.

No passing stand-alone result was dominated by one event: the largest positive-improvement shares
were below 0.28. However, event coverage is highly heterogeneous. Legal test rows range from one to
2,292 per event, and large-move rates range from 0% to 76.6%. Equal-event and observation-weighted
metrics agree on the strongest features, but this coverage risk must remain explicit.

## Frozen candidate-compression trial 03

Before formalization, one final bounded model comparison will use the unchanged sample and folds:

1. `activity_core`: boundary distance, current boundary state, expiry, 6-hour variance, jump
   concentration, zero-change fraction, and trailing mean absolute change;
2. `activity_no_expiry`: the same set without expiry;
3. the already declared 15-feature full-interaction recipe.

The fixed ridge penalty remains 0.1. Both magnitude and large-move labels are retained. The compact
candidate must match or improve the full model under event-macro and observation weighting, retain
at least 10 event wins versus baseline, and avoid material early/late degradation. Trying additional
subsets after seeing trial 03 is outside this packet's budget.

## Candidate-compression trial 03 result

The seven-feature `activity_core` improved on the original 15-feature full model for both surviving
labels:

| Label | Full model MSE (event / observation) | Activity core | No-expiry core |
|---|---:|---:|---:|
| absolute six-hour change | 0.002578 / 0.001192 | **0.002489 / 0.001125** | 0.002587 / 0.001642 |
| two-cent large move | 0.132994 / 0.117383 | **0.131986 / 0.114559** | 0.133448 / 0.127088 |

The core won against the baseline in 13/16 magnitude events and 14/16 large-move events. Removing
expiry preserved event-level stability but materially harmed observation-weighted performance,
especially for magnitude. The compact core is selected in development; the full model and
no-expiry rival are retained rejections. The packet's feature-subset budget is exhausted.

## Selected development candidate

The primary formalization target is continuous absolute probability movement over the next elapsed
six hours. The two-cent large-move label remains corroborating development evidence rather than a
second selected target. The candidate uses:

- boundary distance and current `[0,.02] ∪ [.98,1]` state;
- `log(1 + hours-to-close)`;
- trailing six-hour realized variance;
- 24-hour maximum-step concentration relative to realized variance;
- trailing 24-hour zero-change fraction;
- trailing 24-hour mean absolute change;
- fold-standardized ridge with fixed penalty 0.1 and expanding legal training history.

Formalization must preserve the cross-contract population claim. The current authored candidate
manifest accepts one exact dimension-value slice, and its program invocation exposes neither the
decision clock nor registered lifecycle close time. Reducing the candidate to one contract would
change the question. These are now explicit run-exposed harness seams to resolve before formal
development replay; they are not reasons to substitute a weaker candidate or expose protected data.
