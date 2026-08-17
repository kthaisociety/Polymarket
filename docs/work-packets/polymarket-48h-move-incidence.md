# Work packet: Polymarket 48-hour meaningful-move incidence

## Identity

- Packet: `polymarket.test-48h-move-incidence`.
- Input repository state: `bdl-polymarket@d3551fbb` plus the pure-`sqrt` sandbox packet.
- Responsibility: exact duration-study sampling → binary 48-hour crossing label → chronological
  development evidence.

## Objective

Test whether the compact state/staleness mechanism that predicts sampled first-passage duration also
predicts whether a two-cent sampled move occurs at all within 48 elapsed hours. A passing result is
a movement-risk mechanism, not direction or executable trading alpha.

## Fixed design

- Exact retained development corpus/partition used by the duration study; protected values remain
  unavailable.
- Reuse the exact greedy decisions: 24-point history spanning 18–30 hours, six-step span 4.5–7.5
  hours, 42–54 hours of future coverage, then advance at least 48 elapsed hours.
- Label `1` iff a retained probability at least `0.02` from the decision value appears within 48
  elapsed hours; otherwise `0`.
- Chronological one-event-ahead test folds 8–23; fit only lower event ordinals with equal total
  weight per training event.
- Baseline: earlier-event-equal crossing rate.
- State model: probability, boundary distance, and `.005`-winsorized logit.
- Candidate: state plus 24-hour zero-step fraction and log-one-plus quiet-run hours under the fixed
  `.005` quiet-step definition.
- Both models use fold-standardized ridge penalty `0.1` with predictions clipped to `[0,1]`.
- Metrics: observation and event-macro Brier score, pooled and event-macro average precision,
  event wins, early/late event Brier, prediction mean, and incidence.

## Gate

The candidate advances only with at least 500 OOF rows, 100 positives, 100 negatives, and 10 mixed
events; lower observation/event Brier than baseline and state; higher pooled/event-macro AP than
both; state-relative Brier improvement in both chronological halves and at least 60% of events;
observation and event-macro Brier at most `0.20`; and mean prediction within `0.10` of incidence.

No label, feature, penalty, fold, threshold, or gate may change after source 01 reads data. Failure
closes the branch. Passing permits one authored formal replay, not freeze or protected access.

## Caveats

- Retained probability samples do not establish continuous-time passage or executable quotes.
- Non-overlapping outcome windows reduce within-market label dependence but do not make contracts or
  event groups independent.
- The features were selected using the continuous-duration question, so this is selection-exposed
  transfer evidence rather than a pristine feature discovery.
- No production writes, external data, Kthais, engine changes, sibling-repository changes, protected
  access, or terminal-memory mutation are permitted.

## Boundary revisions

1. Source 01's average-precision helper sorted `[prediction, outcome]` pairs in reverse order, so
   outcomes accidentally broke prediction ties. This inflated constant-score event AP to `1.0`.
   Brier scores, calibration, predictions, labels, folds, and coverage were unaffected. Source 02
   changes only average precision to threshold-grouped tie handling; all scientific choices and the
   predeclared gate remain fixed. The flawed receipt remains retained and cannot support a ranking
   claim.
2. Tie-safe source 02 reproduced all non-ranking values exactly. The state/staleness model improved
   observation/event-macro Brier from state-only `0.22698/0.16319` to `0.18563/0.14359`, improved
   pooled/event-macro AP from `0.74174/0.84611` to `0.87174/0.89321`, improved both chronological
   halves, and won 10/15 events. Coverage was 975 OOF rows with 507 positives, 468 negatives, and 13
   mixed events. It nevertheless failed the calibration gate: mean prediction `0.71007` exceeded
   incidence `0.52000` by `0.19007`. The exact calibrated-probability branch is rejected. The score
   remains selection-exposed ranking evidence and may motivate a separately declared
   nonstationary-prior question; it cannot be relabeled as a passing result here.
