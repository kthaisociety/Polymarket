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
