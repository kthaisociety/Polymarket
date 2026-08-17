# Polymarket bracket-overround compression

Epistemic status: **EXPLORATORY DEVELOPMENT REJECTION — PROTECTED DATA UNEXPOSED**.

This study tests a fixed cross-contract mechanism on exact retained Polymarket development data:
whether the sampled sum of mutually exclusive post-count bracket probabilities rises far enough
above one to predict cost-screened portfolio compression over the next day.

The discovery/confirmation split, synchronization rule, threshold, label, cost screen, and gate are
frozen in the
[work packet](../../docs/work-packets/polymarket-bracket-overround-compression.md).

The first execution was denied before data access because pure scalar `sqrt` was absent from the
sandbox namespace. That denied receipt is retained. After a separately tested two-name sandbox
repair, the byte-identical source ran successfully:

- all eight event question sets parsed into pairwise non-overlapping brackets;
- 40 of 40 day/event portfolios had complete snapshots synchronized within five minutes;
- per-leg overround correlated `0.5573` with next-day per-leg decline;
- only eight portfolios met the fixed `0.015` per-leg overround threshold;
- mean one-cent-screened decline was `+0.00289`, but only 50% were positive and only three of eight
  event means were positive.

The predeclared gate required at least 10 signals, 60% positive screened changes, and four positive
event means. It failed, so later-event confirmation, formalization, freeze, and protected evaluation
were not authorized. The positive continuous association is retained as descriptive evidence, not
rescued through a lower post-hoc threshold.
