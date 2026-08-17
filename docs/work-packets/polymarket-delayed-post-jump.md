# Work packet: delayed Polymarket post-jump continuation

## Identity

- Packet: `polymarket.test-delayed-post-jump-continuation`.
- Owning responsibility: development-only constrained exploration with conditional formalization.
- Input corpus: `polymarket-corpus:610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f`.
- Partition: `49d5e9a97985a44e3277f43ee55ce1281c430a1d0a1823754a9a759ac56d3bd1`.
- Repository checkpoint at predeclaration: `bdl-polymarket@e70c31b6` on
  `codex/polymarket-time-series-research`.

## Question

After a retained hourly YES-probability update of at least two cents, does the update continue over
the following day after waiting one retained observation, and do pre-jump staleness features
identify the continuation better than state or shock size alone?

This is distinct from the earlier unconditional drift/reversal and first-passage-direction tests.
It conditions on an information-sized observed update, delays entry before measuring the outcome,
and uses non-overlapping post-jump windows. The economic hypothesis is gradual incorporation after
a discrete information shock. Reversal remains a reported falsifier, not an alternative selected
after results.

## Authority boundary

- Permitted fields: development market identity, authoritative chronological event ordinal,
  observation ordinal/time, and sampled market probability.
- Excluded: final seven protected events/45 markets, resolution payouts, question semantics,
  external data, production writes, Kthais, the production engine, sibling repositories, and any
  claim that sampled probabilities are executable quotes.
- The final seven events remain unavailable unless an exact development candidate independently
  passes the fixed gate, is replayed through the formal authored evaluator, frozen, and authorized
  by protected governance.

## Fixed sample

- A shock is a one-observation signed probability change with absolute size at least `0.02`; the
  two observations must be 0.5-3 elapsed hours apart.
- At least 24 earlier observations are required. Their elapsed span must be 18-30 hours.
- The sampled entry is the first retained observation after the shock, 0.5-3 elapsed hours later.
- Entry probability must be in `[0.05, 0.95]`; absorbed or nearly absorbed entries are outside the
  two-sided risk population.
- The outcome is the last retained probability no later than 24 elapsed hours after the shock. It
  must be 18-24 hours after the shock, and a retained observation at or after the 24-hour boundary
  must occur no later than 30 hours after the shock.
- Eligible shocks are selected greedily in market-time order. After selecting one shock, no later
  shock in the same market is eligible until 24 elapsed hours after the selected shock. This makes
  outcome windows non-overlapping within a market.
- Event ordinals 8-23 are tested exactly once using only eligible rows from earlier event ordinals.
  Every fitting fold gives each training event equal total weight.

## Fixed label and features

The continuous label is:

`last sampled probability at or before shock + 24h - delayed entry probability`.

The feature vector is fixed at delayed entry time:

1. delayed-entry probability;
2. distance to the nearest probability boundary;
3. probability logit clipped at `.005/.995`;
4. signed shock size;
5. absolute shock size;
6. entry slippage from the shock observation to delayed entry;
7. pre-shock zero-change fraction over the prior 23 steps;
8. log one plus pre-shock quiet-run hours under the fixed `.005` step threshold;
9. pre-shock mean absolute step over the prior 23 steps;
10. signed shock times pre-shock zero fraction;
11. shock sign times log quiet-run hours.

The fixed ridge penalty is `0.1`. Every fold standardizes with training data only. Models are:

- zero-change baseline;
- state ridge using features 1-3;
- shock ridge using features 4-6;
- shock-plus-staleness ridge using all 11 features (candidate).

No feature subset, penalty, shock threshold, entry delay, horizon, or probability regime may be
searched after observing this result.

## Fixed evidence views and gates

Report observation and event-macro MSE/MAE, early/late event-macro MSE, mean prediction versus mean
label, meaningful-direction accuracy on labels with absolute size at least one cent, per-event
metrics, event wins versus shock-only, represented market count, largest market/event row shares,
and concentration of positive MSE improvements.

The predictive mechanism gate requires all of:

- at least 150 OOF rows across at least 30 markets and 10 test events;
- no single market contributes more than 20% and no single event more than 30% of OOF rows;
- at least 50 meaningful positive and 50 meaningful negative labels;
- candidate observation and event-macro MSE below zero, state, and shock-only;
- candidate early and late event-macro MSE below shock-only;
- candidate wins at least 60% of represented events versus shock-only;
- meaningful-direction accuracy at least `0.55` and at least `0.03` above shock-only;
- absolute mean-prediction/mean-label gap at most `0.01`;
- no one event supplies more than half of total positive MSE improvement versus shock-only.

The separate cost falsifier buys YES when candidate prediction exceeds `+0.01` and buys NO when it
is below `-0.01`. Net sampled change is signed label minus a fixed one-cent round-trip cost. It
requires at least 40 trades in at least eight events, positive observation and event-macro mean
net change, at least 60% positive event means, positive leave-one-event-out minimum event-macro
mean, at least ten YES and ten NO trades, and nonnegative mean net change on each side.

Passing the predictive gate authorizes one exact formal development replay. Passing the cost
falsifier additionally identifies a pseudo-execution candidate, but cannot establish tradability
without historical bid/ask depth or prospective paper execution. Failure closes this exact branch
as development negative evidence.

## Logging and memory

Retain the exact authored source, source SHA-256, immutable receipt, actual field accesses,
snapshot/partition identities, all aggregate and event-level metrics, exclusions, gate values,
caveats, and zero protected exposure. Repository study history is updated for every result.

Hermes-style validated memory is not a Markdown summary. Only an independently governed protected
finding or protected rejection may become terminal question memory. Development lessons remain
explicitly selection-exposed in the research ledger until that authority exists.
