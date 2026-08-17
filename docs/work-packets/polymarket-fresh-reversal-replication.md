# Work packet: fresh-event Polymarket reversal-hazard replication

## Identity and ancestry

- Packet: `polymarket.replicate-post-jump-reversal-hazard-on-fresh-events`.
- Predeclaration checkpoint: `bdl-polymarket@1c581999`.
- Expanded corpus:
  `polymarket-corpus:8c73260377ea5cb3e569bbc3c744ce9b62a95c8f54dafb73d07671845ccec4c6`.
- Ancestor corpus:
  `polymarket-corpus:610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f`.
- Required partition method: `whole-event-chronological-fresh-replication/v1`; all ancestor events
  and the expanded final 20% whole-event block remain absent.
- Selection-exposed source/receipt ancestry: original reversal-hazard source
  `25baa10e9273e19b8ff969e4e9f6659b2ccaf4110f6deb7e485feb34a68fcc3a` and receipt
  `65e9a70ce16551f560b38d4e90155fa00fb25b00ddb3c95558fc8bcc7b73b442`.

## Question

On previously uninspected Polymarket events, can internal sampled-price state and shock geometry
predict whether a two-cent reversal occurs before a two-cent continuation during the 24 elapsed
hours following a retained probability shock?

This is a replication of a statistical-property lead, not a claim about executable quotes or
profit. The original corpus selected the hypothesis, feature families, model recipes, thresholds,
and gates; it is not confirmation evidence.

## Fixed population and label

Reuse the original semantic rules without retuning:

- one-step absolute shock at least `.02`, spanning 0.5-3 hours;
- 24-observation history spanning 18-30 hours;
- entry at the next retained observation 0.5-3 hours later and in `[.05,.95]`;
- coverage at or after shock plus 24 hours but no later than 30 hours, with the last legal point
  between 18 and 24 hours after shock;
- greedy 24-elapsed-hour non-overlap inside each market.

From delayed entry, label `1` when an opposite-shock-direction displacement of at least `.02`
occurs before a same-direction displacement of `.02`; label `0` for continuation first or neither.
The diagnostic exit is the first crossing, otherwise the final legal point.

## Fixed features and models

The 12 entry-time features remain:

1. entry probability;
2. boundary distance;
3. `.005/.995`-clipped logit;
4. shock sign;
5. absolute shock size;
6. shock-signed entry slippage;
7. clipped immediate retracement fraction;
8. reversal-direction headroom;
9. continuation-direction headroom;
10. pre-shock zero-change fraction;
11. log one plus pre-shock quiet-run hours under `.005`;
12. pre-shock mean absolute step.

Models are the earlier-event reversal rate, six-feature state/shock ridge-logistic, and 12-feature
full path-regime ridge-logistic. Each fresh event ordinal from 8 onward is predicted using only
earlier fresh event groups. Fits give each event equal mass, standardize inside the fold, use L2
penalty `.1`, leave the intercept unpenalized, and execute exactly four Newton updates without
fallback.

## Fixed evidence and gates

Report total/OOF populations, classes, markets/events, largest market/event shares, observation and
event-macro Brier, pooled and event-macro tie-safe average precision, early/late event Brier, event
wins, calibration, top-quintile lift, event concentration, and per-event diagnostics.

The primary state/shock replication gate requires:

- at least 1,000 OOF rows, 300 positives, 300 negatives, 100 markets, and 30 test events;
- largest market/event shares no more than 10%/20%;
- state/shock Brier below the rate model under observation, event-macro, early-event, and late-event
  views;
- state/shock average precision above rate under pooled and event-macro views;
- state/shock wins at least 60% of events versus rate;
- mean prediction within `.10` of the observed rate;
- pooled top-quintile lift at least `.10`, positive lift in at least 60% of eligible events;
- no event supplies more than 25% of positive Brier improvement over rate.

The secondary full-model incremental gate applies the same comparison clauses against state/shock,
except its pooled top-quintile lift threshold is `.15`. It is diagnostic and cannot rescue a failed
primary state/shock replication.

## Fixed sampled-price execution falsifiers

For both state/shock and full prediction, at probability at least `.65`, buy the token opposite the
shock at delayed sampled entry and exit at the diagnostic crossing/final point. Charge one cent
round trip. Each screen requires at least 100 trades/20 events, positive observation and event-macro
net change, at least 60% positive event means, positive leave-one-event-out minimum, at least 25
trades after each shock sign, and nonnegative mean for each sign.

These are sampled complementary probabilities, not historical executable quotes. No bid, ask,
depth, queue, fill, slippage, or capacity fact may be inferred.

## Decision and logging

- If the primary gate passes, retain this as a fresh replicated internal-data statistical property
  and prepare one exact formal state/shock candidate; do not expose the expanded protected block.
- If primary and a cost screen pass, additionally retain a quote-validation/execution research lead.
- If the primary gate fails, preserve the negative result and do not retune this replication.
- Retain exact source/receipt hashes, both snapshot refs, partition/embargo counts, actual accesses,
  exclusions, gates, per-event evidence, warnings, and protected status.
- Development evidence may revise provisional learning but cannot self-promote validated memory.

## Transition receipt

Status: **COMPLETE — FRESH DEVELOPMENT REPLICATION PASSED**.

The real public runner verified the exact snapshot ancestry and constructed partition
`2144b8338515271f342738c3ed7ad62565d98343c3e3284353780b436fbd9a40`: 157 fresh development
events/562 markets, 31 embargoed ancestor events/217 markets, and 47 protected events/221 markets.
It then failed with `MemoryError` under the fixed 512 MB authored-worker limit. Five permitted price
fields were accessed; details are null, protected exposure is false, and formal references/durable
effects are empty.

The immutable operational-failure receipt SHA-256 is
`5f216aa4d2df03eecfb9c6eb4b68822b158db5eb7642d16fe2aef9f3f540e20d`. It is not a negative
scientific result and cannot pass or fail any predeclared gate. The source, population, models, and
gates remain frozen. A retry is permitted only after a resource-policy seam is repaired, under a
new conflict-free receipt path that preserves this failed attempt.

The byte-identical source then succeeded under the separately repaired and recorded finite resource
envelope. Successful receipt SHA-256:
`e777f93b48c87604d845dfd08160036449b2accdd13277a0acf55d243d658c77`; exact replay produced the
same conflict-detecting bytes.

### Fresh evidence

- 6,246 eligible shocks across 136 events; 6,174 OOF rows (2,929 reversal-first/3,245 other),
  410 markets, and 128 test events.
- Largest market/event row shares were 3.05%/7.81%, well inside the fixed 10%/20% limits.
- Rate baseline observation/event-macro Brier: `0.25062/0.25222`; pooled/event AP:
  `0.47947/0.51144`.
- Six-feature state/shock Brier: `0.24084/0.23902`; pooled/event AP: `0.58844/0.69991`;
  early/late event Brier `0.23841/0.23963`; 87/128 event wins; top-quintile precision/lift
  `0.62480/+0.15039`; positive event-lift share 73.4%; improvement concentration 5.43%.
- Twelve-feature full Brier: `0.23072/0.23025`; pooled/event AP: `0.62789/0.71552`;
  early/late event Brier `0.23334/0.22716`; 84/128 wins versus state/shock; top-quintile
  precision/lift `0.68395/+0.20955`; positive event-lift share 77.1%; improvement concentration
  6.86%.
- The primary state/shock replication gate and secondary full incremental gate both passed every
  predeclared clause.

### Sampled-price execution evidence

- State/shock threshold: 165 trades/41 events, observation/event-macro net
  `+0.10726/+0.08828`, 87.8% positive event means, leave-one-event-out minimum `+0.08314`.
  The screen failed because only six negative-shock trades were selected versus the fixed minimum
  of 25; its observed negative-shock mean was positive but cannot rescue the failed breadth clause.
- Full threshold: 387 trades/70 events, observation/event-macro net `+0.06024/+0.04103`, 74.3%
  positive event means, leave-one-event-out minimum `+0.03748`, 345 positive-shock and 42
  negative-shock trades with positive means. This passed every fixed one-cent screen clause.
- These are sampled probability changes under a complementary-token assumption, not executable
  historical quotes, and they do not establish slippage, fill, capacity, or deployable PnL.

Exactly five development price fields were accessed. All 31 ancestor events and the expanded final
47 events remained absent; protected exposure is false and formal references/durable effects are
empty. Under the predeclared decision, the six-feature statistical property advances to exact
formal-candidate preparation, while the full-model cost result is retained as a quote-validation
lead. No protected request is made by this study.
