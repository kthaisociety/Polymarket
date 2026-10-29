# Work packet

## Identity

- Packet: `polymarket.longshot-fade-fresh-replication`
- Owning architecture block: Polymarket data foundation composed with open-ended exploration.
- Semantic transition: retain a later immutable production corpus and replay the exact frozen
  probability-weighting source only on legal whole-event successors absent from the selection
  corpus.
- Frozen source identity:
  `06_probability_weighting_strategy.py@0d5f047b06dc3885c4b3ef596adc03a82d3e5a3453cbc1b8ccfaa1073a2a7d46`.

## Objective

Determine whether enough genuinely later resolved events exist to replicate the selected-outcome
2–10% fade without refitting bands, horizons, costs, weighting, or gates. Never inspect either the
ancestor's or successor's final protected event block.

## Context boundary

- Ancestor snapshot:
  `polymarket-corpus:184b83f7f8012da4ca9116c8b6bad2076570ad5f0bada95b22615ee2f5cceae8`,
  retained at 2026-08-18 11:40 UTC and already used for development selection.
- Later production ceiling: `2026-08-24T09:13:44.071211+00:00`.
- Fixed corpus selection: outcome index 0, fidelity 60, minimum 24 price points, maximum 2,000
  contracts, same environment identity.
- Explicit exclusions: production writes, threshold changes, protected values, existing 29-event
  successor reuse as “fresh” after it was included in the development selection, executable-price
  claims, promotion, and trading.

## Change boundary

- Permitted: one later content-addressed corpus beneath ignored `data/`, sanitized corpus and
  replication receipts, local runners, this packet, and study documentation.
- Allowed state effects: one bounded repeatable-read `human_ro` corpus SELECT, immutable local
  retention, registration, and offline sandbox replay.
- Forbidden: any database mutation, credential output/persistence, source-byte change, overwrite of
  retained objects, protected evaluation, or unrelated runtime changes.

## Correctness

- Failure modes: late backfills break strict ancestor-prefix identity; successor events overlap the
  selection cohort; a final protected block leaks; values are read before source freezing; corpus
  selection changes; missing fresh coverage is reported as rejection; or sampled marks are called
  executable.
- Required evidence: read-only role proof, exact as-of and corpus request, verified immutable
  snapshot digest, strict compatible ancestor validation, fresh whole-event count, protected and
  ancestor embargo counts, exact source digest, actual accesses, and no protected exposure.
- Outcome interpretation: `REPLICATION_SUPPORT` only if the unchanged source passes on fresh
  events; `REPLICATION_CONTRADICTION` only if its original breadth floors are met but a substantive
  rule fails; otherwise `INSUFFICIENT_FRESH_COVERAGE`.

## Completion evidence

- Sanitized later-corpus receipt and exact immutable identity.
- No-refit sandbox receipt over only fresh legal events.
- Study ledger and comparison table state whether the candidate advances, contradicts, or waits for
  more events, plus the continuing executable-quote boundary.

## Boundary revisions

None at opening.

## Transition receipt

### Result

- Status: **COMPLETE — INSUFFICIENT FRESH COVERAGE**.
- A bounded repeatable-read `human_ro` acquisition retained 1,930 contracts, 391 events, and
  1,943,938 hourly samples at the fixed ceiling.
- Current snapshot:
  `polymarket-corpus:0c27543ac944a6d946b52bbf5749b419fc6a0f3d15a8632d30205376a865e40a`
  (525,139,813 bytes). The strict ancestor prefix passed.
- The current 79-event protected tail contains all 70 novel events. The 312 legal development
  events are all ancestor events and therefore embargoed; fresh development count is zero.
- The frozen strategy source did not execute and no novel probability or payout value was exposed.
  The total event count must reach at least 403 before the first successor can enter development,
  and 404 before the minimum two-event replication partition can execute.

### Knowledge carried forward

The longshot fade remains a selection-exposed development candidate. The correct next action is to
wait for legal successor coverage, then replay the unchanged source; using the currently protected
70 events would invalidate the scientific boundary. No executable or protected claim advances.
