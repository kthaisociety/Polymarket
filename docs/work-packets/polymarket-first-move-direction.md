# Work packet: Polymarket first-move direction

## Identity

- Packet: `polymarket.test-first-move-direction`.
- Input repository state: `bdl-polymarket@692fd71b` on
  `codex/polymarket-time-series-research`.
- Responsibility: retained development probability paths → non-overlapping signed first-passage
  labels → chronological directional evidence → retained rejection or one formalization candidate.

## Objective

Test whether direction in the legally observed path predicts the sign of the first sampled
two-cent move within 48 elapsed hours, beyond probability state and earlier-event drift. This is a
separate question from the retained movement-risk and duration mechanisms. A passing result is a
time-legal directional mechanism; sampled prices still cannot establish executable alpha.

## Startup boundary and rivals

- Exact corpus:
  `polymarket-corpus:610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f`.
- Exact whole-event partition:
  `49d5e9a97985a44e3277f43ee55ce1281c430a1d0a1823754a9a759ac56d3bd1`.
- Permitted fields: development market identity, authoritative chronological event ordinal,
  observation ordinal/time, and sampled market probability.
- Population: the 24 development events/155 development markets only. The final seven events/45
  markets remain omitted. The active duration holdout process must not be inspected, restarted,
  duplicated, or used to select this branch.
- Observation clock: retained sampled-price timestamps with legal decision histories. These are
  sampled probabilities, not fills, quotes, midpoints, or guaranteed executable prices.
- Main mechanism: recent directional path state persists when the next meaningful sampled move
  occurs, especially after a quiet/stale interval.
- Rivals: the conditional mean is martingale-like; any apparent sign comes only from probability
  boundaries or global resolution drift; last-step reversal is sampling bounce; a result is
  concentrated in a few events.

## Fixed exploratory design

- Reuse the duration study's sampling without reading its labels or results during execution:
  require 24 retained observations spanning 18–30 hours, a six-step span of 4.5–7.5 hours, a
  retained endpoint 42–54 hours later, then advance the next decision by at least 48 elapsed hours.
  Outcome windows therefore do not overlap within a market.
- Label the first retained probability at least `0.02` from the decision probability within 48
  hours as `+1` for an upward crossing and `-1` for a downward crossing. Label no sampled crossing
  by 48 hours as `0`. The label matures only when the complete 48-hour path is available.
- Test event ordinals 8–23 one event ahead. Fit only lower event ordinals, giving each training
  event equal total weight.
- Models use fold-standardized ridge penalty `0.1`; predictions are clipped to `[-1, 1]`.
- Baselines:
  1. constant zero expected signed move;
  2. earlier-event-equal mean signed label; and
  3. state ridge using probability, nearest-boundary distance, and `.005`-winsorized logit.
- Direction comparator: state plus signed 6-hour change, signed 24-hour change, and the sign of the
  latest nonzero sampled step in the trailing 24 observations.
- Candidate: the direction comparator plus trailing 24-step zero-change fraction, log one plus
  quiet-run hours under the fixed `.005` step definition, signed-6-hour-change times zero fraction,
  and latest-nonzero-sign times log quiet-run hours. These last two interactions test the specific
  direction-after-staleness mechanism rather than adding generic volatility features.

## Metrics and predictive gate

Retain observation and event-macro MSE/MAE; early/late event-macro MSE; event wins; overall label
mean and prediction mean; up/down/no-crossing counts; crossing-only directional accuracy; and the
largest positive event-MSE improvement share.

The candidate may advance to one authored formal replay only if all conditions hold:

1. at least 500 OOF rows, 100 upward labels, 100 downward labels, and 10 test events containing
   both upward and downward labels;
2. lower observation and event-macro MSE than zero, event-mean, state, and direction-comparator
   models;
3. lower event-macro MSE than state in both chronological halves and at least 60% of test events;
4. crossing-only directional accuracy at least `0.55` and at least `0.03` above state;
5. mean prediction within `0.10` of the mean signed label; and
6. no event supplies more than half of total positive state-relative MSE improvement.

Failure closes this exact label/feature/model branch. Passing authorizes one exact authored replay,
not freeze or protected access. No penalty, feature, interaction, threshold, fold, or gate may be
changed after source 01 reads data.

## Cost and execution falsifier

For every OOF model prediction, also retain a non-authoritative sampled-price diagnostic:

- delay entry to the first retained observation after the decision;
- take only a directly buyable long position when prediction is greater than `0.10`;
- exit at the first declared crossing or the last retained point within 48 hours;
- subtract `0.01` probability units per completed long trade; and
- report observation/equal-event mean, positive-event share, and leave-one-event-out minimum.

This diagnostic passes only if there are at least 100 trades, both aggregate means are positive,
at least 60% of represented events are positive, and the leave-one-event-out minimum is positive.
It cannot establish tradability because the corpus has no historical bid/ask or depth. Predictive
advancement does not require this execution falsifier to pass; a failure explicitly bounds the
result to mechanism evidence.

## Evidence and change boundary

- Execute unchanged source through the public retained-corpus analysis command.
- Retain source and receipt hashes, actual accesses, exact coverage/exclusions, every comparator,
  all event views, gate results, warnings, and `protected_values_exposed=false`.
- Permitted changes are this packet and one study's source, receipts, README, and study index. A
  concrete harness defect may be repaired only after a general failing regression is added.
- Forbidden: production reads/writes, Kthais, engine or sibling-repository changes, external data,
  protected values, threshold rescue, result deletion, executable-price claims, freeze, promotion,
  or terminal-memory mutation.

## Status

Design fixed before source 01 reads development values. Epistemic status: `EXPLORATORY`.

## Boundary revisions

1. Source 01 was denied by the analysis policy before any data access because result cleanup used
   Python's `del` statement, which is outside the authored language. Its exact source SHA-256 is
   `6bffa141739a454b0290b46ac605831e30f1be23b463f015dbe80895fb5f95ea`; the receipt records no
   actual accesses and `protected_values_exposed=false`. One policy-safe revision may remove only
   that cleanup statement. The question, data request, sample, label, features, models, penalty,
   metrics, gates, and output content remain fixed.

## Transition receipt

### Result

- Status: **COMPLETE — DEVELOPMENT REJECTION**.
- Exact policy-safe source SHA-256:
  `0083bba4b070b4bf439e8a044b2c9a7ad842762a361c48e77b662579b57cbfe7`.
- Exact successful receipt SHA-256:
  `22cc473b7c2397744c9729cd59afbd9a1a1c2b03e69d4ef51c4d170a2156e33d`.

### Evidence

- The unchanged sample produced 1,053 development decisions and 975 OOF rows. OOF labels included
  278 upward crossings, 229 downward crossings, and both directions in all 15 evaluated events.
- Observation/event-macro MSE was `0.52000/0.63189` for zero, `0.57565/0.64954` for the
  earlier-event mean, `0.57299/0.64101` for state, `0.58787/0.66259` for state plus direction, and
  `0.60322/0.67101` for direction after staleness.
- The candidate won only 4/15 events against state. Crossing-direction accuracy was `0.54635`,
  below state and the earlier-event mean at `0.54832`. Candidate mean prediction `0.32271` also
  missed mean signed label `0.05026` materially.
- The delayed one-cent-cost long-only diagnostic generated 948 sampled trades. Equal-event mean
  net change was positive `0.00827`, but observation-weighted mean was negative `-0.00280`; large
  events 14 and 15 dominated the row-weighted loss. The fixed execution falsifier failed.
- Actual accesses were exactly market ID, chronological event ordinal, observation ordinal/time,
  and sampled probability. The receipt records no formal objects, no durable effects, and
  `protected_values_exposed=false`.

### Disposition

The path-direction and direction-after-staleness hypotheses fail this label/model design. No
feature, threshold, penalty, or weighting revision is permitted under this packet. No candidate is
formalized or frozen, and no protected request or terminal-memory update is authorized. The result
also reinforces the earlier finding that event-equal apparent profitability can disagree with
observation-weighted evidence when a few large events dominate; neither weighting may be hidden.
