# Work packet: Polymarket post-jump reversal-first hazard

## Identity and ancestry

- Packet: `polymarket.test-post-jump-reversal-first-hazard`.
- Corpus: `polymarket-corpus:610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f`.
- Whole-event partition:
  `49d5e9a97985a44e3277f43ee55ce1281c430a1d0a1823754a9a759ac56d3bd1`.
- Predeclaration checkpoint: `historical checkpoint b2ea6794`.
- Selection-exposed ancestry: delayed post-jump source/receipt
  `a923a7f0…`/`311fc5cb…` found aggregate delayed reversal but rejected its continuous
  shock-plus-staleness return model.

The ancestry motivates this new statistical property but does not confirm it. This packet changes
the label to a competing-risk event, changes the model to ridge-logistic probability, and fixes a
new gate before reading any reversal-first outcomes. It cannot reopen or tune the rejected
continuous-return branch.

## Question

Following a retained two-cent probability shock and a one-observation entry delay, can internal
contract state predict whether a two-cent reversal is observed before a two-cent continuation over
the next 24 elapsed hours?

This is a statistical-property question about post-shock path regime. A usable result would be a
foundation for a contrarian execution candidate, not proof of executable profit.

## Authority and data boundary

- Authorized fields: development market ID, chronological event ordinal, observation ordinal/time,
  and sampled probability.
- Protected final seven events/45 markets, payouts, external data, production writes, external application,
  external-system code, and sibling repositories remain excluded.
- Sampled probabilities are observations, not historical quotes. No bid, ask, depth, queue, or
  fill assumption may be invented.

## Fixed population and label

Reuse the semantic population rule, not the prior realized rows:

- one-step absolute shock at least `.02`, with the shock step spanning 0.5-3 hours;
- 24-observation history spanning 18-30 hours;
- entry at the next retained observation 0.5-3 hours later and in `[.05,.95]`;
- a retained coverage observation at or after shock plus 24 hours, no later than 30 hours;
- last usable point no later than 24 hours must be at least 18 hours after shock;
- greedily selected shocks with 24 elapsed hours between selected shocks in the same market.

From delayed entry, scan forward until 24 hours after the shock. Relative to shock direction:

- label `1` when an opposite-direction displacement of at least `.02` is observed before a
  same-direction displacement of at least `.02`;
- label `0` when continuation crosses first or neither boundary crosses.

The diagnostic exit is the first competing crossing, otherwise the final legal 24-hour point.

## Fixed features and models

Features known at delayed entry:

1. entry probability;
2. boundary distance;
3. `.005/.995`-clipped logit;
4. shock sign;
5. absolute shock size;
6. shock-signed delayed-entry slippage (positive means further continuation);
7. immediate retracement fraction, clipped to `[-2,2]`;
8. reversal-direction probability headroom;
9. continuation-direction probability headroom;
10. pre-shock zero-change fraction over 23 steps;
11. log one plus pre-shock quiet-run hours under `.005`;
12. pre-shock mean absolute step.

Three probability models are fixed:

- earlier-event reversal rate;
- state/shock ridge-logistic using features 1-6;
- full path-regime ridge-logistic using all 12 features.

Each event ordinal 8-23 is predicted using only earlier event groups. Fit weights give each
training event equal mass. Features are fold-standardized. The L2 penalty is `.1`, the intercept is
unpenalized, and exactly four Newton updates are used with no convergence-based fallback.

## Fixed metrics and gate

Report OOF count, positives/negatives, represented markets/events, largest market/event row shares,
observation and event-macro Brier, pooled and event-macro tie-safe average precision, early/late
event-macro Brier, event wins, mean prediction/rate, and fixed top-quintile precision/lift.

The predictive gate requires:

- at least 300 OOF rows, 100 positives, 100 negatives, 50 markets, and 10 test events;
- no market contributes more than 20% of OOF rows;
- full Brier below both comparators under observation and event-macro weighting;
- full average precision above state/shock under pooled and event-macro weighting;
- full early and late event-macro Brier below state/shock;
- full wins at least 60% of events versus state/shock;
- mean prediction within `.10` of observed rate;
- fixed top-quintile precision at least 15 percentage points above the OOF rate, with positive lift
  in at least 60% of events having both classes;
- no one event supplies more than half of total positive Brier improvement versus state/shock.

## Fixed execution falsifier

When full predicted reversal probability is at least `.65`, buy the token opposite the shock at the
delayed sampled entry and exit at the first competing crossing or final legal 24-hour point. Charge
one cent round trip. Require at least 40 trades/eight events, positive observation and event-macro
mean net change, 60% positive event means, positive leave-one-event-out minimum, at least ten trades
after positive and negative shocks, and nonnegative mean net change for both shock signs.

This remains sampled-price pseudo-execution. Passing prediction authorizes one exact formal replay;
passing both gates identifies a quote-validation candidate. Failure closes the exact branch.

## Logging and learning

Retain exact source/receipt hashes, actual accesses, exclusions, all metrics and gates, per-event
evidence, snapshot/partition identity, and protected-exposure status. Development evidence may
enter a provisional reflection or candidate lesson, but validated Hermes-style memory requires an
independent learning authority and qualifying evidence; this study cannot self-promote.

## Transition receipt

- Status: **COMPLETE — DEVELOPMENT REJECTION WITH EXECUTION LEAD**.
- Source SHA-256:
  `25baa10e9273e19b8ff969e4e9f6659b2ccaf4110f6deb7e485feb34a68fcc3a`.
- Receipt SHA-256:
  `65e9a70ce16551f560b38d4e90155fa00fb25b00ddb3c95558fc8bcc7b73b442`.
- Coverage: 715 eligible shocks; 589 OOF rows, 279 reversal-first/310 other, 77 markets,
  and 15 test events. Largest market/event shares were 15.6%/46.3%.
- Earlier-event rate observation/event-macro Brier was `0.25369/0.25255`. State/shock improved it
  to `0.24577/0.24071`; full path-regime improved it further to `0.24312/0.23359` and won 10/15
  events versus state/shock.
- The full candidate still failed the fixed predictive gate: pooled AP slipped from state/shock
  `0.57211` to `0.56786`, early-half event-macro Brier worsened from `0.23120` to `0.24971`, and
  top-quintile lift `0.10751` missed the fixed `0.15` threshold. Event-macro AP improved to
  `0.66697`, so the lead is mixed rather than empty.
- The independently fixed sampled-price cost falsifier passed all of its clauses: 96 trades/10
  events, observation/event-macro net `+0.01420/+0.01262` after one cent, 60% positive event
  means, leave-one-event-out minimum `+0.00886`, and positive means after both shock signs.
- Exactly five development price fields were accessed; protected exposure is false and formal
  references/durable effects are empty.

Because prediction and execution were conjunctive gates, the exact branch is not formalized,
frozen, or sent to protected evaluation. The honest reusable lesson is provisional: internal
state/shock variables contain cross-contract reversal-regime information and a cost-screened
contrarian subset, but richer path features are unstable in the earlier half and do not yet clear
the declared ranking threshold.

The two post-shock receipts were also admitted through the learning service as a bounded
provisional reflection and candidate skill
`a42a22ca81c862cb5ee5e61ea81e8e86f1135593d4fe61754a3a828153b105ba`. Candidate receipt SHA-256 is
`df00bad859f41bc8f24019f0efc61c6b1ce10fbb8bc3075ee072f4e4d023cac9`; validation and publication
remain null by construction.
