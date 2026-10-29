# Work packet

## Identity

- Packet: `polymarket.probability-weighting-development`
- Owning architecture block: Open-ended exploration over the retained Polymarket data foundation.
- Semantic transition or responsibility: Convert the existing broad calibration lead into fixed
  longshot-fade and favorite-follow strategy screens, with adjacent probability-state rivals,
  event dependence, chronology, and an adverse-execution hurdle.
- Input repository state: `bdl-polymarket@712fc693bd17` on
  `codex/polymarket-time-series-research`, after the rejected B1/B2 wallet packet.

## Objective

Test whether probability weighting supplies strategy-specific information beyond generic
probability state. Preserve the negative result if low-probability overpricing does not exceed a
neighboring low-probability control or if any apparent edge is chronologically unstable.

## Context boundary

- Authority loaded: Chronos global authority, exploration transition, retained-corpus adapter,
  time-series analysis and feature-design principles, and the completed behavioral packets.
- Input snapshot: exact immutable corpus
  `polymarket-corpus:184b83f7f8012da4ca9116c8b6bad2076570ad5f0bada95b22615ee2f5cceae8`.
- Development/protection boundary: earlier 80% of whole event groups visible; latest 20% hidden by
  the existing partition composition.
- Explicit exclusions: production access, protected-value access, executable-quote claims,
  threshold tuning, semantic subgroup selection, formal promotion, and trading.

## Change boundary

- Permitted: this packet, one authored sandbox source, one development receipt, study README and
  index updates, and a local read-only runner for the exact retained corpus.
- Allowed effects: verified snapshot load, development-only sandbox execution, and local research
  artifacts.
- Forbidden: production or core runtime mutation, protected evaluation, prior-receipt mutation,
  and edits to unrelated low-latency work.

## Correctness

- Failure modes: treating every hourly sample as independent; using a favorable horizon selected
  after inspection; calling sampled prices executable; conflating broad YES overprediction with
  longshot-specific weighting; ignoring event composition; double-counting multiple samples per
  market/horizon; or inspecting protected outcomes.
- Inputs/outputs: one closest legal sample per market at fixed 72h and 168h horizons, exact mature
  payout, whole-event identity, and fixed bands produce event-macro net edges and paired adjacent
  band differences.
- Counterexample: if longshot and adjacent-low bands have equal edge, the probability-weighting
  mechanism is rejected even when both have positive raw calibration edge.
- Verification: exact source digest and actual accesses; `protected_values_exposed=false`; one
  decision per market/horizon; order checks; explicit market/event coverage; focused sandbox and
  corpus tests remain green.

## Predeclared decision rules

- Horizons: closest sample to 72 hours before close within 12 hours, and 168 hours within 24 hours.
- Longshot fade: BUY NO when YES probability is `[0.02, 0.10)`; adjacent rival is BUY NO in
  `[0.10, 0.20)`. Net edge is `price - payout - 0.02`.
- Favorite follow: BUY YES when YES probability is `(0.90, 0.98]`; adjacent rival is BUY YES in
  `(0.80, 0.90]`. Net edge is `payout - price - 0.02`.
- Longshot survival requires at least 100 markets and 30 events at both horizons, positive
  event-macro net edge at both, paired longshot-minus-adjacent event-macro edge of at least `+0.01`
  at both, and positive longshot net edge in both chronological halves at 168h.
- Favorite survival uses the same rule with lower breadth floors of 30 markets and 20 events at
  both horizons because the fixed high-probability cells are rarer.
- Failure of any clause rejects that fixed strategy. A pass permits only a fresh immutable
  evaluation request; sampled marks remain non-executable.

## Completion evidence

- Sandbox receipt, exact source identity, coverage, chronology, paired rivals, and decision status.
- Updated comparison against the time-series program: probability band is a state feature; only
  the incremental adjacent-band contrast can be attributed to the weighting hypothesis.
- Focused tests and a transition receipt distinguish calibration, sampled-price strategy evidence,
  and executable alpha.

## Boundary revisions

- The retained outcome label inventory contains 1,149 `Yes` paths and three `Up` paths. Exact
  selected-outcome payout identity remains valid. Reporting therefore uses “selected outcome”
  rather than incorrectly claiming a YES-only cohort; no probability, payout, band, or gate changed.

## Transition receipt

### Result

- Status: **COMPLETE**.
- The fixed longshot fade passed the development rule and is frozen for genuinely later
  whole-event replication. Favorite follow failed and is rejected.

### Evidence

- Longshot: 181 markets/109 events at 72h and 169/93 at 168h; two-cent-hurdled event-macro edge
  `+0.00160` and `+0.01842`; paired adjacent-band differences `+0.05259` and `+0.11654`.
- Chronology: 168h longshot edges `+0.01232`/`+0.02345`; 72h early edge `-0.00844` remains a red.
- Favorite: event-macro net edges `-0.00478`/`-0.01291`; fixed candidate rejected.
- The sandbox exposed 256 development events/1,152 markets while 65 events/357 markets remained
  protected. Exact source SHA-256 is
  `0d5f047b06dc3885c4b3ef596adc03a82d3e5a3453cbc1b8ccfaa1073a2a7d46`.

### Knowledge carried forward

The low-probability effect is more specific than broad calibration because the adjacent 10–20%
fade loses after the same hurdle. Its short-horizon magnitude and paired-event breadth are fragile.
Only an exact no-refit replay on events that were absent from this development execution can advance
it; sampled prices still cannot establish executable alpha.
