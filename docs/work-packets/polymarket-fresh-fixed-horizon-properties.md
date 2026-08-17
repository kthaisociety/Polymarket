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

