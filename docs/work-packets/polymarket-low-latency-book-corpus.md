# Work packet: retain and register a low-latency book corpus

## Identity

- Packet: `polymarket-low-latency-book-corpus`
- Owning architecture block: data foundation
- Semantic transition or responsibility: exact bounded dual-clock L2 rows from the proved read-only
  engine database into immutable retained bytes and replay-ready registered top-of-book observations
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the completed
  `polymarket-book-receipt-time` working-tree delta

## Objective

Given a retained scope-authority reference, explicit venue/market/outcome legs, and a half-open
collector-time interval, retain only post-clock-change snapshots and deltas, reconstruct each leg
after its first in-window snapshot, and register executable top-of-book state with venue event time
as `reference_time` and collector absorb time as `available_at`.

## Context boundary

- Global authority loaded: `AGENTS.md`, Chronos `CONTEXT.md`, decisions, invariants, style guide,
  alignment protocol, and data-foundation transition contracts
- Owning block and transition contract: data-foundation `IMPLEMENTATION.md`,
  `data.register-observations`, and `data.build-information-set`
- Relevant adjacent interfaces: content-addressed Polymarket corpus retention, direct read-only
  database reader, `market.book_snapshots`, `market.book_deltas`, and the dual-clock engine models
- Explicitly excluded work: production deployment or mutation, semantic cross-venue contract
  matching, fees, queue position, order simulation, feature selection, hypothesis scoring,
  protected evaluation, and live trading
- Assumptions: explicit leg identity has already been semantically approved; `ts` is conservative
  decoded-event availability only for rows with non-null `reference_time`

## Change boundary

- Permitted files or components: Chronos Polymarket adapter models/reader/new book-corpus module,
  adapter exports/tests, data-foundation implementation documentation, and this packet/receipt
- Allowed state effects: parameterized SELECTs through a supplied read-only executor; immutable
  content-addressed files under an operator-selected root; immutable in-memory registrations
- Forbidden state effects: database writes, inferred venue mapping, legacy-row admission, missing
  timestamp substitution, unanchored book-state publication, or scientific/performance claims

## Correctness

- Governing invariants and decisions: I1, I11, I13, I17, I24, I26; locked dual-time semantics;
  observation is not belief
- Concrete failure modes: admit `reference_time IS NULL`; read outside exact legs or `[start,end)`;
  merge events from different legs; apply deltas before a snapshot anchor; treat venue time as
  availability; reorder same-leg events; mutate retained bytes; silently publish a crossed book
- Expected inputs and outputs: exact legs plus bounded absorb times produce canonical retained rows,
  one replay state per source event after anchoring, and bid/ask price/size observations carrying
  both clocks and exact source provenance
- Violating mutation or counterexample: swap `available_at` to `reference_time`, remove the SQL
  legacy predicate, or delete the initial snapshot; causal/admission tests must fail
- Required local tests/evals: request and row validation; parameterized SQL scope; legacy-null
  rejection; anchor behavior; snapshot/delta replay; dual-clock registration; retention integrity
- Required integration evidence: protocol-compatible executor proves the exact production SQL and
  registration composition; live production capture remains a later deployment gate

## Completion evidence

- Focused low-latency book-corpus tests pass
- Chronos adapter Ruff, formatter, and basedpyright gates pass
- Existing Polymarket adapter tests remain green
- `git diff --check` and transition receipt record remaining execution reds

## Boundary revisions

1. The opening request identity named exact legs but did not bind the authority that permits those
   legs to be interpreted together. `scope_authority_ref` is now mandatory and enters the retained
   canonical bytes. For LL-01 it must identify the exact semantic audit; the reader never infers a
   match from titles or prices.

## Transition receipt

### Result

- Packet: `polymarket-low-latency-book-corpus`
- Status: **COMPLETE** for the bounded Chronos read/retain/replay/register boundary.
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the completed
  dual-clock engine working-tree delta.
- Resulting repository state: the working tree containing this receipt; no commit or deployment
  was created.

### Delivered state delta

- Added strict scope records for an authority reference, canonical exact legs, and a half-open
  collector-time window.
- Added two parameterized SELECTs with identical arrays/bounds and an explicit
  `reference_time IS NOT NULL` predicate for snapshots and deltas.
- Added independent Python validation for leg/time scope, row clocks, levels, sequences, ordering,
  duplicates, and a snapshot anchor on every requested leg.
- Added SHA-256 content-addressed canonical retention with byte reuse, conflict detection, load-time
  identity revalidation, and tamper detection.
- Added independent per-leg L2 replay. Pre-anchor deltas remain retained but cannot publish state;
  multi-level deltas sharing one source event publish one resulting top; empty and crossed/locked
  states cannot masquerade as executable two-sided quotes.
- Added four registered fields—best bid/ask price and displayed best bid/ask size—with venue time
  as `reference_time`, collector absorb time as `available_at`, and exact event ordinal/sequence
  dimensions under `decoded-book-collector-absorb/v1`.
- Added a repeatable-read `human_ro` composition that reads, retains, reloads, and registers before
  returning a live result. It performs no database write.

### Evidence

- Focused adversaries: `9 passed`, covering request identity, SQL scope, legacy-null rejection,
  foreign/out-of-window rows, missing anchors, distinct clocks, pre-anchor deltas, crossed state,
  and retained-byte tampering.
- Full Polymarket adapter suite: `79 passed`.
- Broader Chronos suite without the two localhost-server test modules: `448 passed`. The unfiltered
  run reached `472 passed` and `21 errors`; all 21 errors occurred while the sandbox denied
  `ThreadingHTTPServer` socket creation with `PermissionError`, before those unrelated tests ran.
- Full Ruff: `159 files already formatted`; all checks passed. Full basedpyright: `0 errors, 0
  warnings, 0 notes`. `git diff --check` passed.
- Counterfactual demonstrated: querying or returning a legacy null fails before corpus creation;
  an information set just after venue event time but before collector absorb contains no quote.

### Knowledge carried forward

- Chronos can now represent the exact quote state needed to form H1/H2/H3/H5 predictors without
  treating venue timestamps as availability or transaction prints as quotes.
- `scope_authority_ref` binds the two-venue semantic permission but does not prove it; LL-01 must use
  the retained audit digest already recorded in the program memo.
- Collector absorb is stamped after decoded-event handoff, so replay latency is conservative but
  not wire, kernel, venue-processing, order-send, acknowledgement, or fill latency.
- Registration intentionally publishes displayed state, not fills. Fee schedules, tick/status
  histories, clock-health telemetry, queue position, partial fills, failed-leg hedging, and capital
  costs remain required before conservative locked value can be measured.
- No post-change production rows were read because the engine schema/model change has not been
  deployed. This receipt is data infrastructure, not a retained LL-01 corpus, hypothesis result,
  trade recommendation, formal candidate, protected request, or finding.
