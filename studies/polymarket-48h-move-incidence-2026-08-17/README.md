# Polymarket 48-hour meaningful-move incidence

Epistemic status: **EXPLORATORY DEVELOPMENT REJECTION WITH RANKING LEAD — PROTECTED UNEXPOSED**.

This study transfers the exact compact state/staleness mechanism from continuous sampled
first-passage duration to the binary question of whether a two-cent sampled move occurs within 48
elapsed hours. The fixed design and gate are in the
[work packet](../../docs/work-packets/polymarket-48h-move-incidence.md).

Source 01's average-precision implementation accidentally used outcomes to break prediction ties.
Its receipt remains retained but cannot support ranking claims. Tie-safe source 02 changed only that
metric implementation and reproduced all predictions, labels, Brier scores, and calibration values.

Over 975 chronological OOF rows (507 moves, 468 non-moves, 13 mixed events), the compact
state/staleness model showed a strong selection-exposed ranking improvement:

| Metric | Event-rate baseline | State only | State + staleness |
|---|---:|---:|---:|
| Observation Brier | 0.32680 | 0.22698 | **0.18563** |
| Event-macro Brier | 0.26890 | 0.16319 | **0.14359** |
| Pooled average precision | 0.59486 | 0.74174 | **0.87174** |
| Event-macro average precision | 0.63189 | 0.84611 | **0.89321** |

The candidate improved both chronological halves and won 10/15 events versus state-only. It did not
pass as a probability model: mean prediction was `0.71007` against `0.52000` incidence, outside the
fixed `0.10` calibration tolerance. No formal candidate, freeze, or protected request is authorized
under this packet. The retained lead is narrower: state/staleness ranks 48-hour sampled movement
risk in development, while an expanding all-history ridge has a materially nonstationary level.

A single predeclared calibration revision replaced the expanding intercept with the last four
eligible training events' incidence while preserving the exact slopes and features. It brought mean
prediction to `0.57858` and observation Brier to `0.16596`, but worsened event-macro Brier to
`0.14741`, pooled average precision to `0.82781`, and late-half event-macro Brier to `0.14015`; only
7/15 events improved against the unadjusted candidate. The fixed gate failed, the calibration
revision budget is closed, and the binary branch remains an uncalibrated development ranking lead.
