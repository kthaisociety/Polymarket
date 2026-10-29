# Work packet

## Identity

- Packet: `polymarket.negrisk-coordination-data-sufficiency`
- Owning architecture block: Polymarket data foundation composed with open-ended exploration.
- Semantic transition or responsibility: Prove or reject whether venue-authorized NegRisk event
  semantics and causal, simultaneous, full-depth book capture can support the B6 complete-set
  coordination strategy before any basket edge is inspected.
- Input repository state: `bdl-polymarket@712fc693bd1728794ba76f9cb6627e957b1ec7b4` on
  `codex/polymarket-time-series-research`, with unrelated dirty low-latency work preserved.

## Objective

Audit production for exact open NegRisk event groups with at least three binary markets and for
post-dual-clock order-book coverage of every YES leg in at least one such group. Return a sanitized
readiness decision. Do not infer exhaustiveness from question text or calculate a basket return
unless the semantic and causal-data gates pass.

## Context boundary

- Global authority loaded: Chronos `AGENTS.md`, context, locked decisions and invariants; work-packet,
  Polymarket-startup, time-series analysis, and feature-design skills and their required references.
- Owning block and transition: data-foundation README/transitions/implementation and the existing
  bounded dual-clock book-corpus composition; open-ended exploration remains provisional.
- Relevant adjacent interfaces: Gamma-derived `market.markets.raw`, exact `event_id`,
  `market.market_outcomes`, `market.book_snapshots`, `market.book_deltas`, the existing
  `strategy.lab.signals.neg_risk_arb.basket_return`, and `human_ro` repeatable-read execution.
- Explicitly excluded: production writes; semantic inference from titles; legacy null-clock rows;
  current top-only claims; incomplete-event pricing; fees or fills guessed from theory; protected
  evaluation; order placement; and live trading.
- Assumptions to test rather than grant: Gamma `state.neg_risk=true` plus exact venue `event_id`
  supplies the grouping authority; outcome index zero is the YES leg only when its retained label
  says `Yes`; displayed book levels are quotes, not fills.

## Change boundary

- Permitted: this packet; one SELECT-only audit source; one sanitized receipt; B6 study/index
  documentation; and, only after a passing audit, a separate predeclared development packet.
- Allowed state effects: bounded production SELECTs inside a proved read-only transaction and local
  research artifacts.
- Forbidden: engine or production mutation, retroactive scope expansion, strategy-value inspection
  before readiness, protected-value access, or edits to unrelated low-latency implementation.

## Correctness

- Governing invariants: explicit availability and label maturity; exact source identity; event-level
  dependence; no silent fallback; observation is not belief; actual-access provenance; development
  is selection-exposed.
- Concrete failure modes: mixing ordinary and NegRisk markets in one event; treating a subset of
  candidates as exhaustive; pricing NO instead of YES; accepting an event with a closed leg;
  admitting `reference_time IS NULL`; confusing collector sweep time with venue time; combining
  non-overlapping leg histories; ignoring missing snapshot anchors, depth, fees, partial fills, or
  failed-leg unwind risk.
- Expected inputs/outputs: aggregate Gamma semantic inventory, exact outcome mapping, schema
  clock presence, recent snapshot/delta ranges, and per-event/per-leg coverage produce a sanitized
  readiness decision and exact candidate scopes, without price or size values.
- Violating counterexample: an event with ten NegRisk legs but book capture on only two must fail;
  two visible legs cannot be priced as a ten-leg guaranteed basket.
- Required local verification: source hash, JSON parsing, `git diff --check`, and focused book-corpus
  plus exploration tests.
- Required integration evidence: `human_ro`, session/transaction read-only proof, populated
  venue-semantic rows, post-change clock rows, and at least one complete captured event before a
  strategy packet may open.

## Predeclared readiness gates

The audit passes to strategy predeclaration only if at least one exact event satisfies every clause:

1. At least three currently open markets share one non-null server `event_id`; every market has
   `raw.state.neg_risk=true`, accepts orders, and supplies exactly one outcome-0 token labeled `Yes`.
2. Every market in that exact event has at least one post-change snapshot with non-null
   `reference_time` in the audited seven-day window and at least one subsequent delta or snapshot.
3. Snapshot and delta tables both expose the dual-clock column and contain non-null-clock
   Polymarket rows.
4. The event has no partial leg coverage. Audit output must report total legs and captured YES legs
   separately; equality is required.
5. Fee schedule and minimum-order metadata are present on every leg so a later screen can price a
   conservative hurdle rather than assume zero cost.

Passing grants only a new development work packet. It does not prove simultaneous state replay,
positive locked value, fills, atomicity, profitability, or permission to trade.

## Completion evidence

- Exact SELECT source and SHA-256; sanitized live audit receipt; explicit readiness decision and
  candidate event/market identities; updated B6 status and comparison notes.

## Boundary revisions

1. The initial query deliberately referenced the required clock column and failed at parse time
   because production has not deployed it. The audit source was revised before any value read to
   retain the schema failure plus legacy collector-time coverage and semantic inventory. Legacy
   rows remain inadmissible; the decision rule did not change.
2. A full seven-day legacy delta count was cancelled after 63 seconds because the failed schema
   gate already fixes the decision. The final audit uses only the small current-top state as a
   descriptive coverage diagnostic and explicitly defers every historical replay/value query.

## Transition receipt

Status: **COMPLETE — DATA SUBSTRATE REJECTED FOR B6 PRICING**.

- Production contains 1,243 observed multi-leg NegRisk events and 1,013 open semantic candidates
  satisfying the database membership, YES mapping, accepting-order, and cost-metadata rules.
- Six candidates have all YES legs in current collector top state; event `166435` has ten of ten
  legs on the same current sweep.
- Production `market.book_snapshots` and `market.book_deltas` both lack `reference_time`. Therefore
  none of the legacy history can enter the dual-clock corpus, regardless of current-top coverage.
- No basket price, size, fee amount, payout, question, or return was read. Historical overlap,
  exact event-byte retention, and strategy scoring were deferred.
- Exact source SHA-256:
  `8163a608fd8c12703d3e3e6b3b74f7a5550dd84f00fbd1fb89b19149a907f255`.

This packet closes the readiness audit, not B6 or the broader goal. The next causal dependency is
deployment of the already-implemented dual-clock schema/collector followed by a fresh capture.

Deployment inspection found production on `f27716db25bf579f1e38c39cff8aa46cef3e7b7b` with
`pm_books` healthy. Neither production nor `origin/main` contains the clock columns; the complete
dual-clock delta is uncommitted in the shared dirty worktree. The documented activation path
requires reviewed merge to `main` and an interactive sudo operator. No hot patch or promote was
attempted.
