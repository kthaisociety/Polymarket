# Work packet: Polymarket process contract heterogeneity

## Identity

- Packet: `polymarket.test-process-contract-heterogeneity`.
- Parent evidence: sources 11, 12, 13, and 15 in the stochastic-process paper study.
- Epistemic status at opening: `EXPLORATORY`; one fixed development-only robustness trial.
- Data capability: expanded-corpus fresh-development prices and contract lifecycle metadata.
  Ancestor and final protected events remain unavailable.

## Question and rivals

The retained process description is a bounded, sticky, state- and duration-dependent marked jump
process. This packet asks whether its principal descriptive signatures are broad across measurable
contract structures, or whether one kind of contract/event silently determines the result.

The fixed rivals are:

1. large multi-contract events create the apparent stickiness and reversal;
2. long-lived contracts create the apparent sub-diffusive scaling;
3. deeply sampled contracts create all four signatures while sparse contracts differ.

This is a heterogeneity diagnostic. It does not select another predictive model, use settlement
payout, inspect protected values, or authorize protected access.

## Fixed structural strata

Each event receives exactly one label under each predeclared structural partition:

1. event breadth: one market, two to four markets, or at least five markets;
2. median contract lifecycle: at most 30 days, more than 30 through 180 days, or more than 180 days;
3. median retained sampling depth per contract: fewer than 500 points, 500 through 1,999 points, or
   at least 2,000 points.

The bins are fixed before the metric run and cover every development event. They use only contract
identity, open/close time, and retained point count. Question text and eventual payout are excluded
to avoid an unstable semantic classifier or future-outcome composition.

## Fixed metrics, eligibility, and event unit

Source 20 reconstructs the unchanged source-11 event rows:

- strict-interior regular exact-zero rate, eligible at 100 increments;
- 24-hour variance ratio relative to 24 one-hour increments, eligible at 100 increments at both
  horizons;
- next-move rate after at least 24 quiet hours divided by the rate immediately after a move,
  eligible at 50 observations on each side;
- adjacent nonzero-sign reversal rate, eligible at 50 pairs.

For every stratum and metric it retains event count, eligible-event count, event-equal mean, median,
threshold prevalence, and a deterministic 95% event-bootstrap interval. Markets and rows never
become independent uncertainty units.

## Fixed falsifier

For each of the three structural partitions:

- at least two strata must contain ten eligible events for zero mass, variance scaling, and sign
  reversal;
- every such eligible stratum must have event-equal zero mass above `0.20`, 24-hour variance ratio
  below `0.75`, and reversal rate above `0.50`;
- at least two strata must contain five eligible events for the sparse long-quiet contrast, and every
  such stratum must have an event-equal quiet/active move-rate ratio below `0.50`.

Any breadth failure or directional contradiction is retained and narrows the paper claim. Passing
supports structural breadth only; it does not identify latent beliefs, trades, quotes, or an
executable strategy.

## Trial budget and stopping rule

One authored source is authorized. One correction is allowed only for a visible execution defect
that does not change a stratum, metric, eligibility rule, threshold, or conclusion. No protected
request is allowed.

## Deliverables

- exact source and immutable development receipt;
- all stratum rows, including sparse or contradictory groups;
- update to the study README, manuscript, evidence index, and reproducibility instructions;
- retained negative result if the fixed structural-breadth gate fails.

## Completion

**COMPLETE — FIXED STRUCTURAL-HETEROGENEITY GATE PASSED; PROTECTED VALUES UNAVAILABLE.** All
three structural partitions passed every predeclared breadth and directional gate with zero order
breaks. Every headline-eligible stratum had event-equal zero mass above `0.20`, variance ratio below
`0.75`, reversal above `0.50`, and quiet/active move-rate ratio below `0.50`.

The two-to-four-market breadth stratum contained only nine eligible events for zero mass, variance,
and reversal, so it remains below the fixed ten-event headline threshold; its observed directions
nevertheless agree with the other strata and its six-event quiet contrast passes. No bin,
eligibility rule, or threshold was changed. Source SHA-256 is
`50a42d5282aef22550a76da0128fa2eb0fb67bbbd67a1312956aef302ca0dd28`; receipt SHA-256 is
`ef28bbb4cd5a263a8b594721ba275651c51c59e02318fe46ba753100577df680`.
