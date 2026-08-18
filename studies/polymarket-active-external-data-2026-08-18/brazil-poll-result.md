# Brazil polls versus Polymarket: development result

Status: **direct poll-change rules rejected; weak gross response; no trade**.

## Question

Can a newly published Lula-versus-Flávio runoff poll predict the relative movement of their active
Polymarket election-winner contracts? The poll measures intended runoff vote share. Each contract
instead pays one dollar only if that candidate ultimately wins the presidency. Those quantities
are related, but they are not interchangeable probabilities.

## Time-legal data and execution

- Official TSE open data supplied registration, publication date, scope, sample, and methodology;
  it does not publish candidate results.
- Versioned AFOS poll releases supplied results. Thirty-one releases passed exact TSE protocol,
  national-scope, publication-date, unique Lula/Flávio runoff, and no-later-correction gates.
- Earliest Git commit time—not a claimed article timestamp—was the decision clock. Simultaneous
  releases were collapsed into one median event, leaving 25 decision events.
- The production corpus contains 17,570 canonical one-row-per-match taker fills: 11,111 Lula and
  6,459 Flávio. The original 45,553-row extraction was rejected before reporting because it
  contained both maker and taker ledger legs.
- A trade bought one candidate's YES and the other's NO, then unwound both 100-share legs after
  24, 72, or 168 hours. Every leg required observed same-direction taker execution inside fixed
  six-hour windows. Each entry and exit charged `shares × 0.05 × price × (1-price)`.
- Chronos enforced authorized fields, immutable input hashes, isolated code execution, actual
  access provenance, and an unexposed protected boundary.

## Features tested

1. Change from the previous release event.
2. Change in the median of the latest three release events.
3. Surprise versus the median of the previous five events.
4. Change versus the same pollster's prior release, reducing pollster house effects.

Each feature was followed and faded at fixed 0, 2, and 4 percentage-point gates.

## Result

Every rule with at least five executable paired trades lost after modeled costs.

| Rule | Horizon | Trades | Wins | Gross P&L | Fees | Net P&L |
|---|---:|---:|---:|---:|---:|---:|
| Fade release changes larger than 2 points | 72 hours | 5 | 1 | +$6.3868 | $21.0912 | -$14.7044 |
| Fade any rolling-three median change | 72 hours | 6 | 2 | +$9.4868 | $25.4746 | -$15.9878 |
| Fade any release change | 72 hours | 7 | 2 | +$10.6868 | $29.6577 | -$18.9709 |
| Follow same-pollster change | 72 hours | 7 | 1 | +$1.9127 | $29.6445 | -$27.7318 |

The interesting fragment is a three-day **gross fade response**: abrupt poll moves were partly
reversed in relative contract prices. It is not tradeable evidence because four crossed legs
consumed more than the response, only one election generated the observations, and the rule grid
was exploratory.

## Disposition

Reject direct mechanical trading of poll changes. A stronger future model would convert a
timestamped poll-of-polls into a distribution of election outcomes using sampling error, pollster
effects, undecided voters, first-round qualification, and time remaining. It would need several
independent elections or prospective releases and executable passive-order evidence before a
protected test.

Exact harness evidence: [`brazil-poll-development.json`](brazil-poll-development.json).
