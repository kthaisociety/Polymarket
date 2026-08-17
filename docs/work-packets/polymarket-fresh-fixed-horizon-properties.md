# Work packet: fresh-contract fixed-horizon path properties

## Identity and authority

- Packet: `polymarket.fresh-fixed-horizon-path-properties`.
- Expanded corpus:
  `polymarket-corpus:8c73260377ea5cb3e569bbc3c744ce9b62a95c8f54dafb73d07671845ccec4c6`.
- Ancestor corpus:
  `polymarket-corpus:610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f`.
- Required capability: `whole-event-chronological-fresh-replication/v1`.
- Permitted population: only the 157 pre-protection events absent from the ancestor corpus. The
  31 ancestor events and final 47 expanded events remain unavailable.
- Selection ancestry: fresh reversal receipt
  `e777f93b48c87604d845dfd08160036449b2accdd13277a0acf55d243d658c77`.

This is a selection-exposed candidate-revision and property benchmark. It is not an independent
replication. The 21-hour horizon is chosen before this run because every admitted delayed entry is
at most three hours after its shock, making the label a fixed decision-time horizon contained in
the earlier shock-plus-24-hour question.

## Question

Across previously unseen Polymarket contracts, can information already present in the contract's
sampled probability path predict three fixed-horizon statistical properties during the next 21
elapsed hours after delayed entry?

1. reversal reaches two cents before continuation reaches two cents;
2. either-direction displacement reaches two cents;
3. an interior contract reaches an empirical boundary at or below `.02` or at or above `.98`.

The first property is the formalization target. The other two are bounded mechanism controls, not
additional candidate-selection opportunities.

## Population and time rules

- A shock is a one-step absolute probability change of at least `.02` over 0.5-3 elapsed hours.
- The shock has 24 prior observations spanning 18-30 hours.
- Decision/entry is the next retained observation, 0.5-3 hours after the shock, in `[.05,.95]`.
- The outcome path ends at entry plus 21 elapsed hours. The first retained point at or after that
  boundary must be no more than six hours late, and the last retained point on or before the
  boundary must be at least 15 hours after entry.
- Shocks are greedily non-overlapping by 24 elapsed hours within a market.
- An event ordinal is tested once after at least eight earlier fresh event groups. All rows in a
  test event are predicted from earlier events only; each training event receives equal total fit
  weight.

No resolution label, question text, current close-time metadata, ancestor event, or protected event
is available to the models.

## Features and fixed models

The six-feature state/shock model uses entry probability, boundary distance, `.005/.995`-clipped
logit, shock sign, absolute shock size, and shock-signed entry slippage. The 12-feature path model
adds clipped immediate retracement, reversal and continuation headroom, 24-hour zero-change
fraction, quiet-run duration under a half-cent threshold, and trailing mean absolute step.

For each binary property, compare:

- the earlier-event equal-weight rate;
- six-feature ridge logistic regression;
- 12-feature ridge logistic regression.

Both regressions use fold-local event-equal standardization, L2 penalty `.1`, an unpenalized
intercept, and exactly four Newton updates. There is no hyperparameter search.

## Evidence and gates

For every property retain observation and event-macro Brier, early/late event-macro Brier, pooled
and event-macro average precision, event wins, mean prediction versus incidence, top-quintile
precision/lift, largest market/event row shares, and per-event diagnostics.

The reversal candidate remains formalizable only if the six-feature model:

- has at least 1,000 OOF rows, 300 observations in each class, 100 markets, and 30 test events;
- has largest market/event shares no greater than 10%/20%;
- beats the earlier-event rate on observation, event-macro, early, and late Brier;
- beats it on pooled and event-macro average precision and in at least 60% of events;
- has absolute mean calibration error no greater than `.10`;
- has pooled top-quintile lift at least `.10`, positive event lift in at least 60% of eligible
  events, and no event supplying more than 25% of positive Brier improvement.

The 12-feature model is incremental evidence only. It passes only under the same clauses versus the
six-feature model, with top-quintile lift at least `.15`; it cannot rescue a failed six-feature
candidate. Movement-incidence and boundary-entry results are descriptive transfers and cannot be
selected as substitutes in this packet.

## Sampled-price falsifier and decision

For reversal predictions at least `.65`, take the sampled complementary direction after the shock
and exit at the first crossing or final legal point; subtract one cent round trip. Require at least
100 rows/20 events, positive observation and event-macro means, at least 60% positive event means,
positive leave-one-event-out minimum, at least 25 entries after each shock sign, and nonnegative
mean for each sign.

Passing the predictive gate permits exact authored-candidate construction on this fixed horizon.
Passing the cost screen retains a quote-validation lead only. Sampled probabilities are not bids,
asks, fills, depth, queue position, capacity, or executable PnL. A failed gate is retained without
threshold or feature retuning, and no protected data is requested by this packet.

## Transition receipt

Status: **COMPLETE — REVERSAL FORMALIZATION GATE PASSED**.

The frozen source SHA-256 is
`aa1c19e9ad0293b6f6719617aef39cafdf8cb8f474c2f88421f2f6278c8c0b13`; the successful receipt
SHA-256 is `7fab2899d9f29c6b559f1dd1bfe3754c324243a6f38b1453659abd2e387aeeb2`.
An exact rerun converged to identical receipt bytes.

Chronos scored 6,185 OOF shocks from 410 markets/128 test events. Reversal-first incidence was
46.47%. The six-feature model improved observation/event Brier from `.24974/.25172` to
`.23959/.23867`, pooled/event AP from `.47052/.50340` to `.58142/.68837`, and top-quintile lift
from `+.00354` to `+.15861`; it won 87/128 events and passed every predictive clause. The 12-feature
model improved Brier to `.22917/.22937`, AP to `.62234/.70303`, and top-quintile lift to `+.21439`,
also passing every incremental clause.

The full model's one-cent sampled-price falsifier passed on 370 rows/69 events with
observation/event-macro net change `+.06150/+.04328`, 76.8% positive event means, and at least 42
rows after either shock sign. This retains a quote-validation lead only. The six-feature screen
failed the negative-shock breadth rule with six rows.

The movement-incidence control confirmed predictable activity state. The rare boundary-entry
control showed useful state ranking but no incremental support for the full path model. Exactly
five development price fields were accessed; all ancestor and protected events remained absent.
Under the predeclared decision, the fixed-horizon reversal target advances to authored-candidate
construction without protected exposure.

## Formal authored trial predeclaration

Predeclaration checkpoint: `bdl-polymarket@50db42dd`.

The exploratory whole-event fold orders events by authoritative resolution chronology, but its
authored code does not independently prove that every earlier event label matured before every
later event decision. The formal trial therefore tests a narrower, strictly time-legal online
claim rather than treating the exploratory receipt as formal evidence.

- Use the same fresh-only catalog and fixed 21-hour label, with no ancestor/protected rows.
- Select the earliest eligible shock per market under the exact population and coverage rules.
  This removes repeated-market dependence and is fixed without inspecting model performance.
- Let `AuthoredDevelopmentEvaluator` admit a training row only after its exact 21-hour label has
  matured at the validation decision. The evaluator's chronological replay may use matured rows
  from another contract in the same event; the formal claim is online cross-contract prediction,
  not untouched-event generalization.
- Compare an earlier, event-equal reversal-rate program with the fixed six-feature event-equal
  ridge-logistic program. Both author the same feature and label functions; only fit/predict differ.
- Require at least 200 OOF rows, 100 markets, 30 events, and 75 observations in each class. The
  candidate must beat rate under observation and event-macro Brier, early and late event-macro
  Brier, pooled and event-macro average precision, and at least 60% of represented events. Mean
  prediction must be within `.10` of incidence, top-quintile lift at least `.08`, and maximum event
  share no more than 20%. Absolute Brier must be no greater than `.245`.
- Failure is a formal development rejection or revision and downgrades the fixed-horizon lead. A
  pass publishes exact candidate/trial/evidence identities but does not itself freeze, expose, or
  validate protected data.
