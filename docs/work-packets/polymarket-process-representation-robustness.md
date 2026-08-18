# Work packet: Polymarket process representation robustness

## Identity

- Packet: `polymarket.test-process-representation-robustness`.
- Parent evidence: sources 01, 08, 10, 11, 12, and 13 in the stochastic-process paper study.
- Epistemic status at opening: `EXPLORATORY`; development and later no-refit evidence only.
- Data capability: the existing expanded-corpus fresh-development view. Ancestor and protected
  events remain unavailable.

## Question and rivals

The leading description is a bounded, sticky, state- and duration-dependent marked jump process.
This packet asks whether its decisive descriptive signatures survive reasonable representations
that were not selected from their results.

The fixed rivals are:

1. boundary absorption creates the apparent zero mass and sub-diffusive scaling;
2. probability coordinates create the apparent tails and scaling, which disappear in log-odds;
3. terminal convergence creates the process signatures only near market close;
4. the one-hour observation clock creates stickiness that disappears on a coarser six-hour clock.

This is a robustness analysis, not a new model-selection branch or protected candidate.

## Fixed views

The source will compute the same metrics in five one-hour views:

1. all legal regular probability increments;
2. strict interior probability increments with both endpoints in `(0.02, 0.98)`;
3. the same strict interior rows transformed to log-odds before differencing;
4. probability increments whose starting observation is more than 168 hours before close;
5. probability increments whose starting observation is between zero and 168 hours before close.

It will separately construct approximately six-hour increments from observations six ordinals
apart and compare them with approximately 24-hour increments from observations 24 ordinals apart.
The all-row, strict-interior probability, and strict-interior log-odds views are fixed for this
coarser clock.

No row is treated as a quote, trade, latent belief, or executable return. Log-odds is evaluated only
strictly inside the boundaries; no post-result clipping constant is permitted.

## Fixed metrics and event unit

For every eligible view, retain:

- pooled row count, exact-zero rate, raw increment kurtosis, and mean change;
- event-equal exact-zero rate;
- event-equal 24-hour variance ratio relative to one-hour variance;
- event-equal ratio of next-sample move rates after at least 24 quiet regular samples versus
  immediately after a move;
- event-equal nonzero-sign reversal rate;
- early- and late-event means and deterministic event-bootstrap intervals;
- prevalence of the original paper thresholds across eligible events.

The coarser-clock views retain six-hour zero mass and a 24-hour variance ratio relative to four
six-hour periods. An event needs at least 100 observations for a row-rate metric and at least 100
increments at both horizons for a variance ratio. Missing event metrics remain missing.

## Fixed falsifiers

The robustness conclusion passes only if all of the following hold:

- strict-interior probability and log-odds views each have at least 30 eligible events, an
  event-equal exact-zero rate above 20%, and an event-equal 24-hour variance ratio below 0.75;
- far-from-close and near-close views each have at least 20 eligible events, event-equal exact-zero
  rate above 20%, and event-equal 24-hour variance ratio below 0.75;
- the strict-interior log-odds raw increment kurtosis exceeds 20;
- the all-row six-hour clock has exact-zero rate above 20% and its event-equal 24-hour variance
  ratio relative to six hours is below 0.75;
- the strict-interior quiet-duration contrast has at least 20 eligible events and its event-equal
  mean remains below 0.50.

Failure is retained and narrows or overturns the corresponding paper statement. Passing supports
representation robustness but does not identify the latent process or authorize a formal finding.

## Trial budget and stopping rule

This packet authorizes one authored source and one correction only for an execution defect that is
visible without changing a scientific definition or threshold. A scientific failure ends the
packet. No protected request is allowed from this experiment.

## Deliverables

- exact authored source and immutable development receipt;
- concise result section in the study README;
- manuscript robustness table, evidence-index entry, and replay command;
- retained negative evidence and warnings if any fixed view is sparse or fails.

## Completion

**COMPLETE — FIXED ROBUSTNESS GATE PASSED; PROTECTED VALUES UNEXPOSED.** Source 15 completed with
zero ordering defects. Strict-interior probability and log-odds, both fixed maturity regimes, and
the six-hour clock preserved the predeclared sticky, heavy-tailed, and sub-diffusive signatures.
The exact source and receipt hashes, full results, warnings, and paper projection are retained in
the stochastic-process study. No protected request was authorized.
