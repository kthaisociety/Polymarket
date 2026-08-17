# Work packet: Polymarket time to next meaningful move

## Identity

- Packet: `polymarket.search-time-to-next-move`.
- Owning architecture block: constrained exploration with conditional formalization/development.
- Responsibility: retained development probability paths → legal non-overlapping duration labels →
  chronological evidence → retained rejection or one exact candidate.
- Input state: `bdl-polymarket@bd41fefc` on `codex/polymarket-time-series-research`.

## Objective

Test whether decision-time path persistence predicts how long a Polymarket probability remains
within two cents of its current level. This changes the scientific question from signed or
fixed-horizon magnitude prediction to a capped first-passage duration.

## Context boundary

- Data: exact retained corpus
  `polymarket-corpus:610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f`;
  whole-event partition `49d5e9a97985a44e3277f43ee55ce1281c430a1d0a1823754a9a759ac56d3bd1`.
- Permitted fields: development market identity, chronological event ordinal, retained observation
  ordinal/time, and sampled market probability.
- Excluded: the final 7 events/45 markets, resolution values, production reads or writes, external
  data, current lifecycle close times, executable-price claims, Kthais, and the production engine.
- Sampled probabilities are retained observations. A two-cent sampled displacement does not prove
  that an executable trade crossed that distance between samples.

## Fixed scientific design

- History: at least 24 retained observations spanning 18–30 elapsed hours.
- Decisions: start at ordinal 24 and select the next legal decision only after at least 48 elapsed
  hours. This makes successive 48-hour outcome windows non-overlapping within a market.
- Outcome window: require a retained endpoint 42–54 hours after the decision. The label is elapsed
  hours to the first retained probability at least `0.02` away from the decision probability,
  capped at 48 hours and normalized by 48. If no crossing is sampled, the label is 1.
- Test folds: chronological event ordinals 8–23. Every fit uses only lower event ordinals and gives
  each training event equal total weight.
- Baseline: fold-local event-equal mean normalized duration.
- State comparator: fixed-penalty `0.1` ridge on probability, distance to the nearest boundary, and
  a `.005`-winsorized logit.
- Persistence candidate: the state comparator plus 6/24-hour realized variance, 24-hour zero-step
  fraction, mean absolute step, maximum step, signed six-hour change, and log one plus the elapsed
  trailing quiet-run hours. A quiet step is fixed as an absolute sampled change below `.005`.
- Predictions are clipped to `[0,1]`. Primary losses are MAE and MSE, reported under observation
  and event-macro weighting. Event wins and early/late event-macro MAE are retained.

## Advancement gate

The persistence candidate advances to one robustness/compression trial only if all conditions hold:

1. at least 500 OOF rows, 100 uncapped crossings, and 10 represented test events containing both
   capped and uncapped labels;
2. lower observation and event-macro MAE and MSE than both the event-rate baseline and state-only
   comparator;
3. at least 5% lower event-macro MAE than state-only;
4. lower event-macro MAE than state-only in both chronological halves;
5. MAE wins against state-only in at least 60% of represented events; and
6. no single event supplies more than half of total positive MAE improvement.

Failure closes this exact feature/label/model branch. Passing authorizes one declared dependence
control or feature compression; it does not authorize formalization, freezing, or protected access.

## Evidence requirements

- Run unchanged authored source through the public retained-corpus analysis command.
- Retain exact source SHA-256, sanitized receipt, actual accesses, exclusions, coverage, all
  comparator metrics, gate result, warnings, and zero protected exposure.
- Record the disposition in the study README and exploratory ledger.
- Run repository quality checks and commit the coherent branch locally without pushing.

## Boundary revisions

1. Benchmark 01 passed the exact advancement gate on 975 OOF rows across 15 test events, including
   507 uncapped crossings and 13 events with both capped and uncapped labels. Path persistence
   reduced event-macro MAE from `0.28272` for state-only to `0.24085`, improved both chronological
   halves, won 12/15 events, and had largest positive-improvement share `0.19479`. This authorizes
   the one bounded compression trial, not formalization or protected access.
2. Compression source 02 replays the exact sample, label, folds, weighting, ridge penalty, and gate.
   It compares four predeclared mechanism groups: state plus volatility/activity
   (`rv6`, `rv24`, mean/max absolute step); state plus staleness (zero-step fraction and quiet-run
   duration); state plus signed six-hour path; and state plus volatility/activity and staleness.
   The existing ten-feature full model is the reference. The selected representation is the
   fewest-feature group that passes the original gate and remains within 5% of full-model
   observation and event-macro MAE. Ties follow the written group order. No individual feature,
   penalty, threshold, horizon, or additional subset may be searched after this declaration.
3. Compression receipt 02, source SHA-256
   `1128d26eb4c51e11b61a77f2b6d1db80b58e71b02abf638f99b4e1ae3cac21d1`, selected the five-feature
   `state_staleness` group. It achieved observation/event-macro MAE `0.27627/0.24071`, improved both
   chronological halves, and won 12/15 events against state-only. Volatility/activity alone was
   outside the fixed full-model tolerance and signed path failed the original gate. The full model
   did not materially improve the compact result. This exact compact representation is eligible
   for one authored formal development replay; it is not frozen and protected data remain
   unexposed.
