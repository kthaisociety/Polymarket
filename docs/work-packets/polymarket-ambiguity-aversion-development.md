# Work packet

## Identity

- Packet: `polymarket.ambiguity-aversion-development`
- Owning architecture block: Open-ended exploration over the retained Polymarket resolution corpus.
- Semantic transition or responsibility: Test whether fixed, text-observable resolution-complexity
  proxies identify an ambiguity-aversion underpricing strategy after probability state, event
  dependence, chronology, and an adverse-execution hurdle.
- Input repository state: `historical checkpoint 712fc693bd1728794ba76f9cb6627e957b1ec7b4` on
  `codex/polymarket-time-series-research`, after B1/B2/B4/B7 rejection, B3 freezing, and B5/B6
  data-readiness blocks.

## Objective

Execute one fixed development-only strategy screen: buy the retained selected outcome in questions
whose wording has at least two independent ambiguity/conditionality proxies, at a fixed seven-day
pre-close horizon and moderate probability state. Reject unless it is cost-positive, chronologically
stable, and incrementally better than simple wording within the same event and probability band.

## Context boundary

- Global authority loaded: Chronos global context; data-foundation and exploration architecture;
  work-packet, Polymarket-startup, time-series analysis, and feature-design skills and references.
- Exact source: immutable
  `polymarket-corpus:184b83f7f8012da4ca9116c8b6bad2076570ad5f0bada95b22615ee2f5cceae8`.
- Development/protection: earlier 80% whole-event block visible; latest 20% hidden by the existing
  composition. Question text, selected-outcome label, sampled path, lifecycle, event ordinal, and
  mature payout are authorized only for development events.
- Explicit exclusions: description/rules text not present in the corpus; topic selection;
  post-result wording; protected values; executable-quote claims; threshold fitting; formal
  promotion; and trading.
- Assumption to falsify: fixed surface wording proxies imperfectly but observably distinguish
  ambiguity from simple contract questions. Failure may reject the proxy without rejecting all
  ambiguity aversion.

## Change boundary

- Permitted: this packet; one authored sandbox source; one immutable development receipt; study and
  index updates.
- Allowed effects: exact snapshot load, development-only sandbox execution, and local artifacts.
- Forbidden: production reads or writes, protected exposure, source mutation after result, edits to
  core authority, or unrelated low-latency changes.

## Correctness

- Failure modes: using settlement to define ambiguity; choosing terms after seeing returns;
  conflating longshots with ambiguity; treating markets or samples as independent; counting many
  samples per market; interpreting question length as semantic proof; or calling sampled marks
  executable.
- Inputs/outputs: one closest legal sample per market around 168 elapsed hours before close,
  question text, exact event ordinal, and mature payout produce event-macro net edge and paired
  high-minus-simple differences.
- Counterexample: if complex and simple questions in the same event/probability cell have equal
  settlement edge, the wording proxy adds no strategy information even if complex questions are
  profitable unconditionally.
- Required verification: actual field accesses, source digest, no protected exposure, one decision
  per market, order checks, coverage, early/late evidence, paired event/cell breadth, and focused
  corpus/sandbox tests.

## Fixed proxy and strategy

Question text receives one point for each category present, for a maximum of four:

1. length at least 80 characters;
2. conditional terms: `if`, `unless`, or `in case` as word/phrase boundaries;
3. alternatives: `or` or `either` as word boundaries;
4. quantitative/temporal boundaries: `at least`, `more than`, `less than`, `between`, `before`,
   or `by` as word/phrase boundaries.

`COMPLEX` has score at least two; `SIMPLE` has score zero. Scores of one are excluded from the
primary contrast. Matching is case-insensitive by enumerating lower/title/upper forms in the frozen
source; no learned text representation is permitted.

- Horizon: closest sample to 168 hours before close within 24 hours.
- Probability scope: `[0.20, 0.80]`, excluding the B3 longshot/favorite bands.
- Action: buy the corpus-selected outcome; net edge is `payout - probability - 0.02`.
- Dependence: equal market within event, then equal event. Chronological halves use authoritative
  event ordinals.
- Incremental rival: within the same event and five-point probability band, require at least one
  `COMPLEX` and one `SIMPLE` market; average cells within event and events equally.

## Predeclared decision rule

The candidate survives only if every clause holds:

1. At least 100 complex markets across 30 events.
2. Complex event-macro net edge is positive in both chronological halves.
3. At least 20 paired events and 40 paired event/probability cells.
4. Complex-minus-simple paired event-macro net edge is at least `+0.010` overall and non-negative
   in both chronological halves.

Failure of any clause rejects this fixed proxy/strategy. A pass permits only fresh immutable
replication; it does not prove causal ambiguity aversion or executable alpha.

## Completion evidence

- Exact source/receipt identities; text-category prevalence; probability/horizon coverage;
  event-macro, chronology and paired-control evidence; explicit decision and caveats; 36 focused
  Chronos tests.

## Boundary revisions

None.

## Transition receipt

Status: **COMPLETE — FIXED PROXY/STRATEGY REJECTED**.

- Only 13 of 1,152 development questions scored at least two; conditional terms occurred in zero.
- After the fixed horizon and `[0.20,0.80]` probability scope, `COMPLEX` retained two markets in one
  event versus the 100/30 gate.
- Complex one-event net edge after the two-cent hurdle was `-0.445`; no paired simple-question cell
  existed. All four decision checks failed.
- No text term, score threshold, probability scope, or horizon was changed after inspection.
- Exact source SHA-256:
  `2026b73ece328958385801fbc3d057e42271efd4b2f8401ea304e11194b02f6d`.

The result rejects this fixed title-level proxy, not ambiguity aversion as a general mechanism.
Descriptions and full resolution rules would require a new retained and registered source.
