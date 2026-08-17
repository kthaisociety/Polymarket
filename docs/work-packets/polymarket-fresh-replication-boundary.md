# Work packet: fresh Polymarket replication boundary

## Identity

- Packet: `polymarket.authorize-fresh-replication-view`.
- Owning architecture block: open-ended exploration.
- Semantic responsibility: exact expanded snapshot plus exact ancestor snapshot to a least-authority
  fresh-event `AuthorizedDataView`.
- Input repository state: `bdl-polymarket@3610db31` on
  `codex/polymarket-time-series-research`.

## Objective

Permit authored replication studies over events that are absent from the original retained corpus
and precede the expanded corpus's protected block, without exposing either the original corpus's
events or the expanded protected values.

## Context boundary

- Global authority loaded: `AGENTS.md`, canonical vocabulary, locked decisions, invariants, semantic
  architecture map, authority/sandbox specification, data lifecycle, and test strategy.
- Owning block and transition contract: exploration `README.md`, `IMPLEMENTATION.md`, transition
  index, and `sandbox.authorize-execution`.
- Relevant adjacent interfaces: immutable Polymarket corpus snapshots, public offline study runner,
  actual-access provenance, and conflict-detecting receipts.
- Explicitly excluded: Kthais, the production engine, the sibling Insurance repository, scientific
  model behavior, formalization, protected execution, promotion, database writes, and live reads.
- Assumption: deterministic corpus selection makes the smaller snapshot's contract identity and
  resolution chronology an exact prefix of the larger snapshot; the implementation must verify
  this rather than trust it.

## Change boundary

- Permitted components: Polymarket corpus-to-analysis composition, its public runner/export, focused
  tests, this packet, and the owning exploration implementation map.
- Allowed state effects: immutable local code/docs/test changes and later a sanitized study receipt.
- Forbidden state effects: protected-value disclosure, corpus mutation, credential output, database
  mutation, formal scientific identity, finding/lesson promotion, or external repository changes.

## Correctness

- Governing invariants: I7, I14, I18, I22, and I24; authorization occurs before authored code can
  read data; environment and snapshot ancestry remain explicit.
- Concrete failure mode: the expanded snapshot's ordinary 80/20 split would place seven events from
  the original protected block inside development, falsely making previously sealed content
  available through a new resource identity.
- Expected input/output: two verified compatible snapshots produce a fresh-only development view,
  an independently hidden final expanded block, exact partition/ancestry metadata, and normal
  sandbox provenance.
- Violating mutation: reorder an ancestor contract, change its event identity/resolution chronology,
  or mutate values in an excluded ancestor/protected event.
- Required tests: default partition identity unchanged; only fresh events accessible; hidden-value
  counterfactual stability; malformed ancestry rejected; runner receipt carries ancestry and embargo
  counts.
- Required integration evidence: the public study runner builds the fresh view from two exact local
  snapshot references and produces a conflict-detecting receipt without protected values.

## Completion evidence

- Focused Polymarket corpus and sandbox tests pass.
- Formatting, lint, strict type checking, and full Chronos tests pass.
- The exploration implementation map describes the fresh-replication boundary.
- A transition receipt below records exact commands, results, remaining uncertainty, and what the
  packet does not prove.

## Boundary revisions

None. The repair remains inside Chronos's Polymarket-to-exploration composition.

## Transition receipt

### Result

- Status: **COMPLETE**.
- Input repository state: `bdl-polymarket@3610db31`.
- Resulting repository state: the local commit containing this receipt on
  `codex/polymarket-time-series-research`.

### Delivered state delta

- Added `build_polymarket_replication_analysis`, which verifies compatible snapshot requests,
  exact ancestor contract prefix identity, and unchanged ancestor resolution chronology.
- The replication capability exposes only fresh events before the expanded whole-event protected
  block. Original ordinary development partition and receipt identities remain unchanged.
- The public offline study runner accepts an optional exact ancestor digest/size pair and records
  ancestor/embargo metadata only for replication receipts.
- Allowed state effects were local code, tests, and documentation only. No database, external
  repository, protected-evidence, formalization, promotion, or memory state changed.

### Evidence

- `.venv/bin/pytest -q tests/data_adapters/polymarket/test_resolution_corpus.py`: 20 passed.
- `.venv/bin/ruff check ...`: passed for changed Python files.
- `.venv/bin/basedpyright`: 0 errors, 0 warnings, 0 notes.
- `./scripts/check.sh`: formatting clean, Ruff clean, basedpyright clean, 467 tests passed in
  27.73 seconds. The first sandboxed run could not bind test-only localhost servers; the identical
  gate passed with localhost permission.
- Counterfactual evidence: changing prices, payouts, or questions in an ancestor event and an
  expanded protected event leaves fresh views and authored results unchanged.
- Mutation evidence: reordered ancestor contracts, changed event identity, and changed resolution
  chronology all fail closed.
- Integration evidence: the public runner loaded two content-addressed snapshots, executed authored
  code on only fresh events, and persisted ancestry/embargo receipt metadata.

### Knowledge carried forward

- The 1,000-contract corpus may be used for fresh development replication only through this
  ancestor-bound surface; the ordinary 80/20 surface is unsafe for that lineage.
- Freshness here means event identity absent from the full original corpus, not merely a different
  contract row or file path.
- The exact live 200-to-1,000 snapshot ancestry and the number of accessible fresh events remain to
  be confirmed by the first real runner invocation.
- This receipt proves the boundary and its deterministic adversaries. It does not prove a
  Polymarket signal, economic tradability, or any protected result.
