# Work packet

## Identity

- Packet: `polymarket.register-contract-tape`
- Owning architecture block: Data foundation
- Semantic transition or responsibility: Read an exact Polymarket contract tape from the
  production read interface and register it as time-legal, domain-neutral observations.
- Input repository state: `historical checkpoint f27716db`.

## Objective

Given explicit Polymarket contract IDs and a production read executor, return one immutable
registration whose observations preserve contract, outcome, print, time, block-vintage, and source
identity. No observation outside the pinned block window may enter the registration.

## Context boundary

- Global authority loaded: `AGENTS.md`, `CONTEXT.md`, locked decisions, invariants, architecture,
  data lifecycle, test strategy, and alignment rules.
- Owning block and transition contract: data-foundation README, implementation map, and
  `data.register-observations`.
- Relevant adjacent interfaces: `data.build-information-set`, `data.build-training-sample`, the
  parameterized Polymarket query surface, and the local async PostgreSQL pool.
- Explicitly excluded work: external application imports, database mutation, autonomous question selection,
  feature or target selection, fitting, protected access, validation, memory, and reporting changes.
- Assumptions: A Polymarket on-chain fill becomes publicly observable at its recorded block time.
  This rule is versioned and carries the caveat that confirmation and collector latency are not
  modeled.

## Change boundary

- Permitted files or components: the Chronos package, root `README.md`, and research documentation.
- Allowed state effects: Construct immutable in-memory registrations and print non-secret smoke
  receipts. Tests may create temporary files.
- Forbidden state effects: Database writes, DSN or password persistence/output, protected evidence
  exposure, changes to external application, and changes to the external collection service.

## Correctness

- Governing invariants and decisions: I1, I11, I13, I17, I24, and I26. Registration must not invent
  availability or silently substitute missing block, contract, outcome, or vintage identity.
- Concrete failure modes: future block admitted, fill without block accepted, duplicate print
  identity, cross-contract fill substitution, incomplete contract metadata, read failure treated as
  empty data, or connection assumed read-only without proof.
- Expected inputs and outputs: Exact contract IDs plus a reader implementing the production read
  protocol produce contract metadata, a closed block vintage, and one `RegisteredDataset`.
- Violating mutation or counterexample: Replace block-time availability with import time or remove
  the block-window filter. The causal information-set and vintage adversaries must fail.
- Required local tests/evals: protocol-backed registration, time admissibility, vintage filtering,
  missing block rejection, changed contract identity, read failure, and read-only smoke preflight.
- Required integration evidence: Execute the real smoke against `human_ro` when the approved tunnel
  is available. If unavailable, record the exact access blocker and do not claim live evidence.

## Completion evidence

- Focused Polymarket adapter tests pass.
- Chronos quality gate passes.
- A live read-only smoke receipt exists, or its exact environmental blocker remains explicit.
- Data-foundation implementation documentation and Chronos navigation describe the new boundary.
- A transition receipt closes this packet without claiming a protected backtest or research result.

## Boundary revisions

The first live database gate was blocked by missing workstation access. That blocker was later
cleared through approved SSH and age-recipient setup. The first isolated live attempt then exposed
an undeclared `asyncpg` dependency; `polymarket.compose-live-read-environment` records its repair.

## Transition receipt

### Result

- Packet: `polymarket.register-contract-tape`
- Status: **COMPLETE** for the research-only adapter and live production read-only acceptance gate.
- Input repository state: `historical checkpoint f27716db`.
- Resulting repository state: the commit containing this receipt on
  `codex/polymarket-time-series-research`.

### Delivered state delta

- Files and interfaces changed: a self-contained Chronos kernel, a parameterized Polymarket reader,
  a fail-closed ingestion boundary, a read-only smoke CLI, causal tests, and root navigation.
- Behavior added, removed, or preserved: exact contract/outcome/print identities and inclusive
  block vintages enter the unchanged domain-neutral registration boundary. Resolution payouts are
  metadata only. No label is inferred, no event group is invented, and no protected evidence is
  accessed.
- Allowed state effects observed: immutable in-memory objects, test-local temporary files, and
  non-secret terminal receipts only. The adapter and smoke issue no database writes.
- Documentation status updated: provenance, architecture Mermaid, data-foundation map, explicit
  research reds, and independent-vendor policy now match the implementation.

### Evidence

- Tests and evals run:
  `PYTHONPATH=src .venv/bin/pytest -q`;
  `.venv/bin/ruff format --check .`; `.venv/bin/ruff check .`; `.venv/bin/basedpyright`.
- Results: `400 passed`; `141 files already formatted`; Ruff clean; basedpyright
  `0 errors, 0 warnings, 0 notes`.
- Boundary/debug observations: the executor tests exercise the same parameterized query protocol
  against a protocol-compatible test executor. Those tests are not described as live data.
- Violating mutation or counterfactual demonstrated: inserting a backfilled fill inside an
  unchanged cursor window preserves the block-vintage identifier but changes the source digest.
  Missing blocks, foreign outcomes, duplicate print identities, and unavailable connection
  configuration fail closed.
- Integration evidence: after approved workstation access was configured, the independently
  packaged smoke proved the `human_ro` role, both read-only settings, and false insert/update
  privileges for `market.markets` and `market.fills`. It read one explicit contract, 10,140 fills,
  and registered 40,560 observations with an exact cursor vintage and source digest. No secret or
  DSN was emitted or persisted.

### Knowledge carried forward

- Decisions and assumptions relied upon: on-chain block inclusion time is a versioned public-chain
  observability rule, not evidence of when this collector or database learned a fill.
- New facts discovered: the public read surface exposes outcome identity, close time, resolution
  status, payout, fills, and cursors, but not authoritative event/group identity or exact resolution
  availability.
- Unresolved uncertainty: the cursor-bounded database read is not an immutable database snapshot.
- Remaining reds or follow-up dependencies: add authoritative resolution availability before creating outcome labels; expose
  event/group identity before grouped validation; retain immutable source bytes or a database
  snapshot identity before treating a cursor window as reproducible protected evidence.

This receipt proves bounded live read-only database access, but does not prove historical collector knowledge, an immutable
database snapshot, label validity, grouped validation, a protected backtest, a research finding, or
model usefulness. It proves the research-only adapter's fail-closed behavior, standalone packaging,
and compatibility with the production read protocol.
