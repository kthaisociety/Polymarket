# Work packet: Polymarket time to next meaningful move

## Identity

- Packet: `polymarket.search-time-to-next-move`.
- Owning architecture block: constrained exploration with conditional formalization/development.
- Responsibility: retained development probability paths → legal non-overlapping duration labels →
  chronological evidence → retained rejection or one exact candidate.
- Input state: `historical checkpoint bd41fefc` on `codex/polymarket-time-series-research`.

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
  data, current lifecycle close times, executable-price claims, external application, and the production data service.
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
4. Formal source 03 must replay the exact greedy 48-hour key algorithm and label through authored
   `history()` and `outcome_path()` interfaces. It evaluates a three-trial ancestry: event-equal
   duration mean, the exact three-feature state ridge, then the selected five-feature state-staleness
   ridge; all use penalty `0.1` and event-equal fitting. The compact candidate is freeze-eligible
   only if it produces at least 500 OOF predictions across 12 events, with at least 100 capped and
   100 uncapped outcomes and 10 mixed events; has observation and event-macro MAE and MSE no worse
   than `0.30`/`0.15`; beats both comparators under all four aggregate losses; lowers event-macro
   MAE by at least 5% versus state-only; improves both chronological halves; wins at least 60% of
   events versus state-only; has largest positive event-MAE improvement share at most `0.50`; and
   keeps mean prediction within `0.10` normalized duration of the observed mean. Failure rejects
   the exact candidate. Passing establishes only freeze eligibility; a separate freeze transition
   and independently authorized protected plan would still be required.
5. Authoring source 03 exposed a generic formal-program interface gap before candidate execution:
   authorized timestamps were strings only, so elapsed duration could not be computed without an
   unavailable parser. The narrow repair exposes the same reference and availability clocks as
   epoch seconds in both development and protected observation payloads. It grants no new rows or
   fields and is covered by unchanged-source development/protected integration execution.
6. Formal source 03, driver SHA-256
   `98ebb1311edd5b65fb33ee83d393f7ad6a976248dcf411bc8958fa1c1e334206`, passed the exact gate.
   Receipt SHA-256 `bccc524a0600b04a29fffa6ea82bdafdfe6a57856f7793eb57b0907661376690`
   contains 1,013 OOF predictions over 22 events. State-staleness improved observation/event-macro
   MAE from `0.25945/0.25928` to `0.21633/0.21683`, improved MSE from `0.10689/0.10471` to
   `0.08621/0.08177`, improved both halves, and won 18/22 events. Its mean prediction `0.60123`
   closely matched mean outcome `0.59824`. The candidate is scientifically freeze-eligible under
   the declared gate, but it is not authority-frozen.
7. Freeze audit found the direct formal request lacked `ProtectedEvaluationPredeclaration`.
   Chronos therefore cannot freeze source 03 evidence. Source 04 must declare, before replay, the
   exact retained-corpus final-seven-event data protocol; greedy non-overlapping 48-hour decision
   protocol; event-equal expanding training protocol; duration MAE/MSE evaluation protocol;
   validation, claim-template, protected-scope, and freeze-standard identities. It must then replay
   the exact three sources, manifests, keys, budget, and ancestry through
   `RuntimeInvestigationCoordinator`, require candidate/evidence identity equality with receipt 03,
   and submit only the matching credible pair to an independently identified freeze authority.
   Source 04 may seal the candidate but must not load or evaluate protected values.
8. Source 04 is fixed at SHA-256
   `58ae71b26d7736f53843e514019a06cfbfe3b154e0bb3575994670ab6b5cc3be`. Its predeclaration binds
   the retained snapshot's final-seven-event data scope, the exact greedy 48-hour decision rule,
   event-equal expanding training, duration MAE/MSE evaluation, protected-improvement validation,
   first-passage claim template, and formal-duration freeze standard. The replay must match formal
   candidate `authored-candidate:bb76fb6846cd5bb935934e16d53c520865f5649d230c53b0cc1ca5c3e1be770d`
   and evidence
   `authored-development-evidence:7729af09c56fed64323cc805df708ab2643ec547aa90877dda30e53a6e9c5372`
   exactly before the independent authority can seal it.
9. Source 04 succeeded with receipt SHA-256
   `00a7d84ab97be39f83e36206137cf88a40a1e372e14ecfa750e0ccd599a5ccd4`. The coordinator replay
   reproduced both exact identities and all declared formal metrics. Independent authority
   `authority:independent-polymarket-duration-freeze` accepted the predeclared development rule and
   sealed
   `frozen-system:65af99a116e6ddabc965b7317ac18162665d05501f0fb77aec6b6b2a6ac19c42`.
   The receipt records `protected_values_exposed=false` and `protected_backtest_run=false`; freezing
   the development identity does not itself authorize or execute protected evaluation.
10. The required backtest-gate audit found source 04's readable protocol aliases cannot resolve to
    the content identities required by an authority-issued `AuthoredProtectedPlan`. Frozen system
    `65af99a1…` remains immutable but is not protected-ready. Source 05 is fixed at SHA-256
    `be6215c4fe5f3ae0d4d8e46e5a490499995bf7cc7febe13c7bcfcfa5abf885d5`. Before replay it
    constructs and authority-issues the exact historical scenario, decision sequence, expanding
    training candidates, full retained-corpus manifest/scope, MAE/MSE/coverage/failure evaluation,
    numerical promotion standard, and bounded claim. It must reproduce the exact candidate and
    development evidence, obtain a new independent freeze over those actual identities, and pass
    independent governance before the loader is invoked. Loader invocation is irreversible
    disclosure; every declared protected decision and failure must remain in the sealed report.
