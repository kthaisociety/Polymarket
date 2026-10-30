# Work packet: preserve book-event receipt time

## Identity

- Packet: `polymarket-book-receipt-time`
- Owning architecture block: data foundation
- Semantic transition or responsibility: preserve the source facts required for a later
  `data.register-observations` mapping without collapsing venue event time into collector receipt
  time
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4`, with pre-existing active
  external-data study changes and untracked acquisition artifacts left in place

## Objective

Every newly captured Polymarket or Kalshi L2 snapshot and delta persists both the venue event time
as `reference_time` and the local collector absorb time as `ts`, while legacy reference times remain
explicitly unknown rather than receiving an invented timestamp.

## Context boundary

- Global authority loaded: `AGENTS.md`, `CONTEXT.md`, locked decisions, invariants, documentation
  map, and code style guide
- Owning block and transition contract: data-foundation `README.md`, `IMPLEMENTATION.md`,
  `transitions/README.md`, `data.register-observations`, and `data.build-information-set`
- Relevant adjacent interfaces: `BookSnapshot`/`BookDelta`, Polymarket and Kalshi book-stream
  adapters, book-table writers, and `market.book_snapshots`/`market.book_deltas`
- Explicitly excluded work: Chronos quote registration, LL-01 value analysis, fee modeling, order
  simulation, production deployment, production data mutation, and protected evaluation
- Assumptions: the authoritative data-model contract governs `ts` as collector absorb time;
  neither stored clock grants Chronos `available_at` authority without a registration policy

## Change boundary

- Permitted files or components: book models, source adapters, SQL schema/inserts, their unit
  and integration tests, directly owned documentation, and this packet/receipt
- Allowed state effects: add a nullable `reference_time` column for migration compatibility, stamp
  `ts` at collector absorb, and write a non-null aware reference time for every new row
- Forbidden state effects: backfill legacy `reference_time` from `ts`, reinterpret venue timestamps
  as collector receipt, change book selection or folding, access live/protected values, or claim
  temporal registration is complete

## Correctness

- Governing invariants and decisions: I1, I11, I13, I24; locked time semantics; registration must
  preserve both time axes and must not invent availability
- Concrete failure modes:
  - payload event time is copied into `ts`, recreating the collapsed clock;
  - one venue or one row kind omits the new timestamp;
  - SQL column order writes a timestamp into the wrong field;
  - a schema migration fabricates receipt time for legacy rows;
  - naive and aware datetimes mix silently;
  - book folding, side complements, or sequence identity changes incidentally
- Expected inputs and outputs: one decoded WS frame plus an aware local receive timestamp produces
  the same snapshot/delta content as before with `reference_time` preserving venue semantics and
  `ts` preserving the supplied collector timestamp
- Violating mutation or counterexample: use a payload timestamp different from the supplied receive
  time and assert that both survive; assigning `ts` from the payload must make the test red
- Required local tests/evals: Polymarket and Kalshi book adapter unit tests for distinct clocks;
  model construction and SQL write integration tests for both row kinds
- Required integration evidence: write/read exact `received_at` through the real book-table SQL
  path and confirm legacy-null schema compatibility by inspection

## Completion evidence

- Targeted unit tests for both venue book adapters
- Book writer integration test through PostgreSQL
- Ruff, formatter, and type checks over touched collector files
- `git diff --check` and an architecture review of the final diff
- A transition receipt recording what the new timestamp proves and what remains red for LL-01

## Boundary revisions

1. `docs/build-core/01-data-model.md` explicitly specifies `ts` as absorb time, while the original
   venue adapters and their tests stored the payload timestamp there. Repository history shows the
   specification postdates the adapter. Following the documented precedence, the packet now
   restores `ts` to absorb time and adds canonical `reference_time` for the venue timestamp instead
   of adding a redundant `received_at` column.

## Transition receipt

### Result

- Packet: `polymarket-book-receipt-time`
- Status: **COMPLETE** for the collector capture and persistence boundary.
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4`, with the pre-existing
  Chronos study work and external-data artifacts preserved.
- Resulting repository state: the working tree containing this receipt; no commit was created.

### Delivered state delta

- `BookSnapshot` and `BookDelta` now carry collector absorb time in `ts` and venue event time in
  `reference_time`.
- The Polymarket and Kalshi stream adapters stamp both clocks from one decoded event. When a venue
  event timestamp is absent, `reference_time` explicitly uses the same observed collector time;
  it is not reconstructed later.
- The book tables and batch writers persist the new clock. Idempotent schema convergence adds a
  nullable column without backfilling legacy rows, so `reference_time IS NULL` remains the
  fail-closed legacy marker.
- Book side normalization, outcome identity, sequence handling, primary keys, and top-of-book
  folding are unchanged.

### Evidence

- Venue clock regressions: `27 passed` across the Polymarket and Kalshi book adapter unit tests.
- Broader unit suite: `868 passed` with only the two socket-opening metrics endpoint tests excluded;
  those tests independently fail under this filesystem/network sandbox with `PermissionError`.
- PostgreSQL integration collection: `17 skipped` because Docker/testcontainers are unavailable in
  this environment. The real writer integration test now asserts snapshot and delta
  `reference_time` round trips through their production SQL statements.
- Static gates: targeted Ruff and formatter checks passed; basedpyright reported `0 errors, 0
  warnings, 0 notes`; `ty check` passed; `git diff --check` passed.
- Counterexample exercised: venue payload time differs by 250 milliseconds from collector time in
  both adapter and writer fixtures. The assertions fail if either clock overwrites the other.

### Knowledge carried forward

- `ts` is the only locally observed absorb-time clock and is therefore the conservative candidate
  for a future Chronos `available_at` policy. `reference_time` is diagnostic source time, not an
  availability grant.
- Polymarket absorb time is stamped after the SDK queue yields a decoded event; Kalshi absorb time
  is stamped after frame decode. This is conservative for replay but does not measure wire arrival,
  kernel receipt, exchange processing, or colocated execution latency.
- A Chronos book reader must require `reference_time IS NOT NULL`, exact venue/market/outcome/time
  bounds, and an immutable retention digest. Otherwise it can silently mix pre-change rows whose
  `ts` had different semantics.
- This receipt does not prove production deployment, live row capture, historical L2 availability,
  cross-venue synchronization, executable fills, fees, queue position, or strategy profitability.
