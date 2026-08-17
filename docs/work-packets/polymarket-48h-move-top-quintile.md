# Work packet: 48-hour movement-risk top-quintile stability

## Identity

- Packet: `polymarket.test-48h-move-top-quintile`.
- Parent evidence: tie-safe development source
  `feff143400734a79ef10d0ab14accb29f020c1f7a4307f9eb583541ada52043c`.
- Input repository state: `bdl-polymarket@a0d3c58d`.

## Question and fixed mechanism

The state/staleness model failed as a calibrated probability system but materially improved
tie-safe average precision. Test whether that ranking lead has an interpretable and event-broad
concentration: within each chronological test event, do rows in the fixed highest predicted-risk
quintile experience more sampled two-cent moves within 48 hours than the remaining rows?

The sample, non-overlapping 48-hour decisions, label, five features, expanding event folds,
event-equal standardized ridge, penalty `0.1`, and state-only comparator are unchanged. For each
model/event, select all rows at or above the score of the fixed `ceil(20% * event rows)` order
statistic. Ties at the boundary remain selected; outcomes never break score ties. Compare selected
incidence with incidence below the threshold.

## Gate and stopping rule

The state/staleness ranking is mechanism-credible under this diagnostic only if:

1. at least 10 test events contain selected and unselected rows and both outcome classes;
2. event-macro selected-minus-unselected incidence is at least `0.20` and positive in at least 60%
   of eligible events;
3. early- and late-half event-macro lift are each at least `0.10`;
4. event-macro lift exceeds the exact state-only comparator; and
5. state/staleness has larger lift than state-only in at least 60% of eligible events.

This is one diagnostic with no quintile search, threshold search, feature/model revision, or
post-result fallback. Failure closes this interpretation. Passing retains a development-stage
ranking mechanism only; it does not revive the probability claim or authorize formalization,
freeze, protected access, direction, execution, or profitability.

## Authority and caveats

- Exact retained development corpus and partition only; protected events remain unavailable.
- Sampled price movement is not continuous-time passage or an executable quote.
- Within-event selection avoids pooled event-composition lift but does not create independent rows.
- Features were selected through the related duration study, so this remains selection-exposed
  development evidence with explicit ancestry.
- No production read/write, external acquisition, Kthais/engine/sibling change, protected request,
  or terminal-memory mutation.

## Result and disposition

The fixed diagnostic passed on 13 eligible mixed events:

| Ranking | Event-macro lift | Positive-lift events | Early lift | Late lift |
|---|---:|---:|---:|---:|
| State only | `0.32820` | 12/13 | `0.39677` | `0.26942` |
| State + staleness | **`0.43854`** | **13/13** | **`0.40650`** | **`0.46601`** |

State/staleness produced larger event lift than state-only in 8/13 events, just above the fixed 60%
gate. Its selected-minus-remainder incidence lift exceeded 20 percentage points in 11/13 events;
the two exceptions were still positive (`0.1875` and `0.0800`). Score ties caused selected shares
from 20.0% to 42.9%, exactly under the declared tie policy, so the result is a high-score-group test
rather than an exact-capacity quintile portfolio.

Disposition: retain a mechanism-credible, selection-exposed development ranking lead. The result
does not repair calibration and cannot establish direction, execution, profitability, formal
eligibility, or protected validity. No further cutoff or capacity diagnostic is authorized under
this packet.
