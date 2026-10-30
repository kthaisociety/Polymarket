# Work packet

## Identity

- Packet: Polymarket dual-clock L2 corpus snapshot command
- Owning architecture block: Data foundation and dataset setup
- Semantic transition or responsibility: exact operator request to retained and registered L2 corpus
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the uncommitted
  low-latency corpus and H1/H3/H5 work recorded in adjacent packets

## Objective

Provide one bounded public command that turns an explicit scope-authority reference, canonical book
legs, and half-open collector-time interval into an immutable, registered dual-clock corpus and a
sanitized receipt through the existing proved `human_ro` database boundary.

## Context boundary

- Global authority loaded: `AGENTS.md`, `CONTEXT.md`, locked
  decisions, invariants, and the semantic architecture map.
- Owning block and transition contract: data-foundation `README.md`, `transitions/README.md`,
  `IMPLEMENTATION.md`, `data.retain-source-snapshot`, and `data.register-observations`.
- Relevant adjacent interfaces: `BookCorpusRequest`, `BookCorpusStore`,
  `read_live_book_corpus`, the resolved-corpus command contract, and the H1/H3/H5 consumers.
- Explicitly excluded work: database deployment, tunnel creation, venue subscriptions, strategy
  evaluation, fee inference, trade execution, protected evidence, and H4 implementation.
- Assumptions: the dual-clock database schema is already deployed by an operator before a useful live run; the
  supplied scope-authority reference and leg identities come from a separately reviewed semantic
  audit; the command never invents either.

## Change boundary

- Permitted files or components: a new Polymarket book-corpus command, its unit adversaries, the
  data-foundation implementation map, the low-latency program/README, and this packet receipt.
- Allowed state effects: append content-addressed corpus bytes beneath the requested workspace and,
  optionally, create an immutable sanitized receipt.
- Forbidden state effects: production writes, credential disclosure, replacement of an existing
  different receipt, hidden scope sorting/substitution, scientific promotion, or durable belief.

## Correctness

- Governing invariants and decisions: I1 temporal admissibility, I11 immutable evidence, I13
  provenance, I17 explicit failure, I18 constrained side effects, I24 environment identity, and
  the locked `(value, reference_time, available_at)` identity.
- Concrete failure modes: missing database authority reported as success; naive datetimes; malformed,
  duplicate, or noncanonical legs; empty or reversed interval; secret-bearing diagnostics; receipt
  overwrite; mutable database rows treated as retained identity; counts or bounds reported from a
  different object than the registered snapshot.
- Expected inputs and outputs: explicit environment, authority ref, repeated canonical
  `venue:market_id:outcome_index` legs, aware start/end, workspace, optional receipt; one sanitized
  JSON result containing request scope, immutable snapshot identity, replay/registration counts,
  observed clock bounds, caveats, and no values or credentials.
- Violating mutation or counterexample: removing the environment-variable guard would let an
  unavailable database path masquerade as an empty successful corpus; accepting a naive timestamp
  would destroy the collector-time meaning of the request.
- Required local tests/evals: blocked missing URL, successful exact composition through an injected
  live reader, malformed/naive/noncanonical request failure, immutable receipt conflict, and
  credential absence.
- Required integration evidence: existing L2 retention/replay tests plus the full Polymarket adapter
  suite; static analysis across the adapter package.

## Completion evidence

- Focused command and book-corpus tests pass.
- Full Polymarket adapter suite passes.
- Ruff, formatter, basedpyright, and `git diff --check` pass on the changed Chronos surface.
- The implementation map and low-latency status name the command and preserve the live-deployment
  dependency.
- This file ends with a transition receipt that states what a synthetic command test cannot prove.

## Boundary revisions

None.

# Transition receipt

## Result

- Packet: Polymarket dual-clock L2 corpus snapshot command
- Status: `COMPLETE`
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the recorded
  uncommitted low-latency predecessor packets
- Resulting repository state: command SHA-256
  `ae67e7f12a0fbf78aa6f0c55cf157ef3b9f5280f1b977f1c489483cef5dcf5e7`; adversary
  SHA-256 `f2c66e31d213c138cd9400c08f13c81e41883b4ca48113fabb2daa2d84f2c94e`

## Delivered state delta

- Files and interfaces changed: added `book_corpus_snapshot.py`, its one-to-one command test, and
  aligned the data-foundation implementation map and active low-latency study status.
- Behavior added, removed, or preserved: added an explicit CLI from reviewed request scope to the
  existing repeatable-read/retain/reload/register composition; preserved the reader, retention,
  registration, and strategy semantics unchanged.
- Allowed state effects observed: test workspaces received content-addressed objects and one exact
  receipt; a different pre-existing receipt remained unchanged.
- Documentation status updated: owning implementation map, study README/index, and hypothesis
  transition now identify the public command and the remaining deployment/data dependency.

## Evidence

- Tests and evals run: six command adversaries; combined command/corpus group; complete Polymarket
  adapter suite; broader Chronos suite excluding the two sandbox-incompatible loopback HTTP server
  modules; Ruff, formatter, basedpyright, documentation-index generation, command smoke, and diff
  whitespace validation.
- Results: command/corpus `16 passed`; adapter `117 passed`; broader Chronos `486 passed`; Ruff all
  checks passed; 30 adapter files formatted; basedpyright 0 errors/warnings; `git diff --check`
  clean. The real no-DSN command returned structured `BLOCKED` with no data read.
- Boundary/debug observations: the first broad adapter invocation omitted a required source path
  and produced one `ModuleNotFoundError` after 116 passes; the exact documented
  `PYTHONPATH=src` rerun passed 117/117.
- Violating mutation or counterfactual demonstrated: naive timestamps, malformed/noncanonical legs,
  and unavailable database authority cannot reach successful acquisition; different receipt bytes
  cannot be replaced; the supplied database URL is absent from output and retained receipt.
- Integration evidence: the command fake drives the real request validation, content-addressed
  store, retained reload, full-depth replay, temporal registration, and sanitized result builder.

## Knowledge carried forward

- Decisions and assumptions relied upon: request scope is separately authorized; `available_at` is
  collector absorb time; `reference_time` remains distinct; only retained bytes anchor identity.
- New facts discovered: the scientific L2 boundary was already capture-capable internally; the
  missing component was an operator-safe public entry point rather than another reader or strategy.
- Unresolved uncertainty: no useful production corpus has been captured, collector deployment is not
  proved here, and the command does not observe clock-health records, fees, acknowledgements, fills,
  cancels, queue position, or partial-fill paths.
- Remaining reds or follow-up dependencies: deploy/verify the dual-clock collector, issue exact
  semantic scope, capture a bounded corpus, inspect it through the authorized development path, and
  only then run H1/H3/H5 and design the execution-rich H4 comparison.

This receipt proves deterministic command mechanics and composition only. It does not prove live
database availability, production capture continuity, empirical alpha, executable PnL, protected
evidence, or authority to trade.
