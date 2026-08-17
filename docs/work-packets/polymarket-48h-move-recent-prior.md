# Work packet: recent-prior calibration for 48-hour move incidence

## Identity

- Packet: `polymarket.test-48h-move-recent-prior`.
- Parent evidence: tie-safe development source
  `feff143400734a79ef10d0ab14accb29f020c1f7a4307f9eb583541ada52043c`.
- Input repository state: `bdl-polymarket@08d919d8`.

## Question and mechanism

The compact state/staleness score ranked 48-hour sampled two-cent moves well but its expanding
all-history intercept overpredicted incidence. Test one fold-local prior-shift recipe: keep the exact
expanding ridge slopes and five features, then replace its expanding event-equal intercept with the
mean incidence of the four most recent eligible training event groups. This asks whether event-level
base-rate drift, rather than the state/staleness ranking mechanism, explains calibration failure.

## Exact candidate memo

- Decision/population/label/horizon/maturity/missingness: unchanged from
  `polymarket.test-48h-move-incidence`.
- Features: probability level, boundary distance, `.005`-winsorized logit, 24-hour zero-step
  fraction, and log-one-plus `.005` quiet-run hours; all computed at decision time without fitted
  state.
- Fit: expanding event-equal standardized ridge, fixed penalty `0.1`.
- Prediction-only adjustment: `clip(raw_score - expanding_training_rate + recent_4_event_rate, 0, 1)`.
  Both rates and ridge state are fitted within each legal fold; prediction performs no fitting.
- Rivals: recent-four-event rate, the same prior-shifted state-only ridge, and the unadjusted
  expanding state/staleness ridge.
- Trial budget: this one four-event prior shift. No window search, calibration-family search, feature
  revision, threshold revision, or post-hoc fallback.

## Gate and stopping rule

Coverage remains at least 500 rows, 100 positives, 100 negatives, and 10 mixed events. The adjusted
candidate must:

1. beat recent-rate, adjusted state-only, and unadjusted state/staleness under observation and
   event-macro Brier;
2. beat adjusted state-only under pooled and event-macro average precision and remain no worse than
   unadjusted state/staleness on both ranking metrics;
3. improve Brier versus unadjusted state/staleness in both chronological halves and at least 60% of
   events;
4. achieve observation/event-macro Brier at most `0.20`; and
5. place mean prediction within `0.10` of realized incidence.

Failure rejects this calibration recipe and ends the local revision budget. Passing permits one
authored formal development replay with explicit parent ancestry, not freeze or protected access.

## Authority and caveats

- Exact retained development corpus/partition only; protected events remain unavailable.
- The same sampled-passage, dependence, selection-exposure, and non-executability caveats apply.
- The four-event window is a fixed scientific choice, not fitted. Its adequacy must be demonstrated,
  not assumed.
- No production writes, external acquisition, Kthais/engine/sibling changes, protected request, or
  terminal-memory mutation.

## Result and boundary revision

The fixed recipe failed its gate over the same 975 chronological OOF rows. It reduced mean
prediction from `0.71007` to `0.57858` against `0.52000` incidence and improved observation-weighted
Brier from `0.18563` to `0.16596`. That improvement did not transfer consistently across the
required controls:

- event-macro Brier worsened from `0.14359` to `0.14741`;
- pooled average precision fell from `0.87174` to `0.82781`;
- event-macro average precision slipped from `0.89321` to `0.89206`;
- only 7 of 15 events improved on Brier versus the unadjusted model; and
- early event-macro Brier improved (`0.15824` to `0.15572`) while late Brier worsened (`0.13077`
  to `0.14015`).

The local calibration-revision budget is therefore exhausted. The evidence supports retaining the
state/staleness score only as a development-stage movement-risk ranking mechanism. It does not
support a calibrated probability claim, formalization, freezing, or protected access for this
binary-label branch.
