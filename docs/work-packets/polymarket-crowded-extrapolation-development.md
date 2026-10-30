# Work packet

## Identity

- Packet: `polymarket.crowded-extrapolation-development`
- Owning architecture block: Open-ended exploration over the live read-only Polymarket data
  foundation.
- Semantic transition or responsibility: Test whether distinct-wallet crowding adds reversal
  information specifically when aggressive traders extrapolate an already-salient price move,
  beyond either trend state or crowd breadth alone.
- Input repository state: `historical checkpoint 712fc693bd17` on
  `codex/polymarket-time-series-research`, after B1/B2 rejection, B3 freezing, and B5 data-readiness
  rejection.

## Objective

Execute one fixed, delayed-entry development screen for crowded extrapolation exhaustion. Preserve
a negative result unless a fade of broad same-direction wallet chasing reverses over sampled
6-hour and 24-hour paths, survives a settlement/cost stress, remains chronological, and improves
on both component rivals.

## Context boundary

- Authority loaded: Chronos global authority; data-foundation and exploration transitions;
  time-series analysis and feature-design principles; prior behavioral wallet packets.
- Database ceiling: `2026-08-24T09:13:44.071211+00:00`, matching the prior wallet development
  program. Whole resolved events are partitioned 60% train, 20% development, 20% embargo by latest
  resolution; only development labels enter this screen.
- Availability: taker actions are public at block inclusion; sampled fidelity-60 prices use their
  recorded timestamps. Entry is delayed beyond the signal hour.
- Explicit exclusions: pending-repair markets; wallet skill or cost-basis history; protected event
  labels; L2 execution claims; production writes; formal promotion; and trading.

## Change boundary

- Permitted: this packet; one SELECT-only authored source; one sanitized development receipt;
  behavioral study/index updates.
- Allowed effects: one repeatable-read `human_ro` query and local research artifacts.
- Forbidden: production-system mutation, edits to unrelated low-latency work, refitting after
  inspection, protected evaluation, or fallbacks from missing delayed marks to originating fills.

## Correctness

- Failure modes: counting both party legs; counting one wallet repeatedly inside an hour; treating
  a one-wallet split order as crowd breadth; conditioning signal construction on settlement;
  entering at the triggering fill; overlapping every hourly signal; ignoring known scope holes;
  treating sampled paths as executable; or relabeling ordinary momentum reversal as behavioral.
- Inputs/outputs: one final canonical vote per wallet/market/hour, prior and delayed public marks,
  mature development payouts, exact event identity, and repair state produce crowd/trend component
  cohorts, sampled reversal paths, settlement stress, event-macro chronology, and paired rivals.
- Counterexample: if the same prior trend reverses equally with one or two wallets, crowd breadth
  adds no behavioral information even if the crowded fade is profitable in isolation.
- Verification: aggregate-only receipt; embargo labels absent; one signal per market/cohort/UTC
  day; distinct-wallet and agreement diagnostics; exact source hash; fixed no-fallback behavior.

## Predeclared definitions

- Canonical direction: outcome-0 BUY or outcome-1 SELL is `+1`; the complementary actions are
  `-1`. Only the database adapter's one-row-per-match taker aggregate leg is admitted.
- Crowd: at least five distinct wallet votes in one market/hour, at least 75% agreeing, no tie.
- Thin: one or two distinct wallets, unanimous when two.
- Chase: the consensus direction agrees with a sampled outcome-0 move of at least five percentage
  points from a mark 6--8 hours before the hour-end decision mark.
- Flat: absolute prior move below two percentage points.
- Cohorts: `CROWDED_CHASE` is the candidate; `THIN_CHASE` removes crowd breadth;
  `CROWDED_FLAT` removes extrapolation. At most the first qualifying signal per cohort, market, and
  UTC day is retained.
- Entry: first fidelity-60 outcome-0 sample from one to two hours after hour end. Fade direction is
  opposite the crowd. Missing entry means no signal.
- Path targets: first sample 6--8 hours and 24--28 hours after entry, before resolution. Settlement
  edge is fade direction times payout-minus-entry, minus a fixed `0.010` adverse-execution hurdle.
- Dependence: signals average within market, then event; event groups receive equal primary weight.
  Chronological halves follow authoritative event ordinals.
- Paired rivals: within event, canonical crowd direction, five-point entry band, and resolution
  horizon, each cohort must contribute at least two signals. Cell differences average within event,
  then across events.

## Predeclared decision rule

`CROWDED_CHASE` survives development only if every clause holds:

1. At least 300 covered signals across at least 30 event groups.
2. Positive event-macro fade return at both 6 hours and 24 hours.
3. Positive one-cent-hurdled settlement edge in both chronological halves.
4. At least 20 paired events and 40 matched cells against each component rival.
5. Event-macro matched settlement advantage of at least `+0.010` over both `THIN_CHASE` and
   `CROWDED_FLAT`.

Failure of any clause rejects the fixed behavioral interaction. A pass permits only immutable
fresh-event replication and executable-quote follow-up; it is not a trading finding.

## Completion evidence

- Exact source/receipt identity, live read-only authority, coverage, component rivals, path and
  settlement results, chronology, exclusions, decision, and warnings.
- Comparison note distinguishes the behavioral interaction from the prior pure time-series
  post-jump reversal hypothesis.

## Transition receipt

Status: **COMPLETE — FIXED CANDIDATE REJECTED**.

- Candidate coverage was 25 signals across 14 events, below the 300/30 gate.
- Event-macro fade returns were `-0.04259` at 6 hours and `-0.06854` at 24 hours.
- One-cent-hurdled settlement edge was `-0.06405`, changing from `-0.11984` early to
  `+0.01035` late.
- No component-rival cell met the fixed two-signals-per-cohort common-support requirement.
- All four decision checks failed. No threshold or cohort was changed after inspection.
- Exact source SHA-256:
  `605dd6e40a8200ab1950e02f1fc5dca1838af6289c2b9ae4c683b21eea8abba7`.

The candidate was under-breadth and contradicted on direction: sampled prices continued with the
crowd rather than reversing. The broader goal remains active; B3 still awaits legal fresh events.
