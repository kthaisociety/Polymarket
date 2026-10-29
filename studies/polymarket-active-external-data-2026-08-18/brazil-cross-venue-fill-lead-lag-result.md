# Brazil cross-venue fill lead-lag scout

Epistemic status: **EXPLORATORY SOURCE-TIME PRINT DIAGNOSTIC — DO NOT ADVANCE**.

Research decision time: `2026-08-23T11:04:12Z`.

## Decision

The retained fill tape does **not** support advancing H2 into a strategy candidate. It cannot test
the symmetric hypothesis as acquired, and the observable one-sided Kalshi-to-Polymarket path is
sparse, conditional on a new print, unstable across candidates and months, and no better than its
matched reverse window. Polymarket-to-Kalshi response coverage is effectively absent at the
predeclared low-latency horizons.

This is not a claim that cross-venue price discovery does not exist. It is a decision that these
transaction bytes do not establish it. A successor test needs collector-time ordered, symmetric,
executable book state.

## Exact evidence

- semantic audit SHA-256:
  `75ec8496452816964f4db6749c1ba90db0c3bd1c27a5e0b510ef2a9e66d67d89`;
- compressed 59,000-fill tape SHA-256:
  `7a08c71c2e88563a247dd10d9a5480a435dc6b834fbed168907a041bf0ffb32c`;
- authored analysis SHA-256:
  `8d61a4351d202b89e37dd3e23cd699f93b2f1f57326baee3dedad2204f3ec9b8`;
- canonical result SHA-256:
  `c082c7fcfa0e2cc25e15b5d4df3c363d55df0e0bd127fc2a17ced7dac73aea90`;
- source-time bounds: `2026-01-01T00:00:00+00:00` through
  `2026-08-18T20:38:11+00:00`;
- accessed fields: `venue`, `fill_time`, `fill_uid`, `market_id`, `outcome_index`, `side`,
  `price`, and `size`.

The rerun over the exact bytes reproduced the canonical result byte for byte. No database or
network read was made by the analysis.

## Predeclared measurement

A trigger is a same-side source-time innovation of at least one cent after no more than a two-hour
source gap. Triggers have a ten-minute cooldown. The matched-venue baseline is strictly before the
trigger and at most 30 minutes old in the primary analysis; two hours is a sensitivity. The
response is the latest same-side print in `(trigger, trigger + horizon]` at fixed horizons of 30,
120, and 600 seconds. No response remains missing and is never imputed as zero.

The analysis also reports an any-side contamination diagnostic, an equal-length pre-trigger
reverse window, candidate and calendar-month slices, matched-baseline age, and response delay. All
results are unweighted trigger observations. They use source timestamps, not collector
`available_at` timestamps, so they cannot prove causal decision-time ordering.

## Coverage defect discovered before interpretation

All 4,713 retained Kalshi fills are BUY: 2,294 for Flavio and 2,419 for Lula. The acquisition kept
only `outcome_index = 0`, while Kalshi normalization records the taker's selected outcome leg.
NO-taking trades needed to reconstruct the opposite YES-price direction are therefore absent. The
analysis excludes rather than zero-fills every trigger direction that the matched venue cannot
observe.

Of 1,029 raw one-cent triggers, 571 are response-eligible and 458 are explicitly excluded for the
missing matched side. Eligible triggers comprise 264 Kalshi sources and 307 Polymarket sources.
The contracts are two candidates in one dependent election family, not independent event
replications.

Kalshi prints are intrinsically too slow for a print-response test in the reverse direction. Median
collapsed-observation interarrival is about 95 minutes for Flavio and 77 minutes for Lula, versus
about 2.8 and 4.1 minutes on Polymarket. Kalshi coverage also ends on August 9 while Polymarket
continues through August 18.

## Primary observations

With the 30-minute matched-baseline freshness limit:

| Source to response | Horizon | Matched / triggers | Conditional aligned mean | Median | Positive | Matched reverse delta |
|---|---:|---:|---:|---:|---:|---:|
| Kalshi to Polymarket | 30 s | 39 / 264 (14.8%) | +0.220 cents | approximately 0 | 53.8% | -0.019 cents, 10 pairs |
| Kalshi to Polymarket | 120 s | 56 / 264 (21.2%) | +0.099 cents | approximately 0 | 51.8% | -0.165 cents, 27 pairs |
| Kalshi to Polymarket | 600 s | 89 / 264 (33.7%) | +0.036 cents | 0 | 48.3% | -0.353 cents, 53 pairs |
| Polymarket to Kalshi | 30 s | 1 / 307 (0.3%) | 0 | 0 | 0% | unavailable |
| Polymarket to Kalshi | 120 s | 3 / 307 (1.0%) | -1.332 cents | 0 | 33.3% | unavailable |
| Polymarket to Kalshi | 600 s | 13 / 307 (4.2%) | -0.238 cents | 0 | 38.5% | +2.900 cents, 4 pairs |

The 30-second Kalshi-source mean is small relative to both the mean 1.447-cent trigger innovation
and the 0.295-cent mean absolute matched response. Its 10th-to-90th percentile range is roughly
-0.10 to +0.75 cents. The typical matched baseline is already 106 seconds old, even though the
final response arrives a median 6.5 seconds after the trigger. This describes sparse transaction
printing, not a stable executable-price adjustment.

Candidate slices disagree. At 120 seconds Flavio is -0.018 cents while Lula is +0.245 cents; at
600 seconds Flavio is -0.079 cents while Lula is +0.149 cents. Calendar-month means also change
sign, and the 600-second response is negative in January, June, and July. Expanding the allowable
baseline age to two hours raises coverage but leaves the Kalshi-source 30-second median at zero and
reduces its conditional mean to +0.170 cents.

## Rivals and failed checks

- **Sparse-print selection:** every mean conditions on a matched print. Coverage is reported
  separately and never silently promoted to the full trigger population.
- **Transaction-side mechanics:** same-side paths avoid the most direct BUY/SELL bounce, but they
  still contain spread, taker-selection, and venue-mechanics effects. The any-side diagnostic does
  not establish a cleaner mechanism.
- **Pre-existing movement:** the paired post-minus-reverse statistic is negative at all three
  Kalshi-source horizons. The apparent post-trigger mean therefore does not beat its local
  pre-trigger comparison.
- **Concentration:** candidate and month slices are inconsistent, and both candidates share the
  same election event.
- **Clock ordering:** source timestamps cannot determine when either observation reached the
  collector or when a strategy could act.
- **Executability:** fills provide no midpoint, touch, depth, fee, queue, acknowledgement,
  partial-fill, or hedge evidence.

## Disposition and next falsifier

Do not formalize, freeze, expose a protected cohort, or describe a trade. H2 remains only a
mechanism hypothesis to be revisited on the same dual-clock L2 corpus required for H1. A legitimate
successor must:

1. retain both Kalshi outcome legs and canonicalize both directions to one YES-price convention;
2. use collector `available_at` ordering and exact executable midpoint or touch state;
3. fix action delay, quote freshness, spread, depth, and fee rules before inspecting responses;
4. require chronological breadth across independent event families; and
5. beat the matched reverse-window and no-change baselines after execution costs.

The first falsifier is still decisive: if the aligned response disappears under those quote,
clock, cost, and breadth controls, close H2. The present scout supplies no reason to divert the
capture program away from H1.
