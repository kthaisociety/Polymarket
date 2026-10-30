# Work packet: LL-01 gross payout-dominance feasibility

## Identity

- Packet: `polymarket-ll01-gross-feasibility`
- Owning architecture block: exploration over the data-foundation boundary
- Semantic transition or responsibility: retained registered two-leg top states plus an exact gross
  strategy definition into a causal, fixed-delay feasibility screen
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the completed
  dual-clock data model and `polymarket-low-latency-book-corpus` working-tree deltas

## Objective

For one explicitly authorized conservative payout pair, identify collector-time decisions where
the latest legal displayed asks sum below the payout floor, size the pair at the smaller displayed
top size, and measure whether the displayed gross edge remains at a fixed action delay without
using future quotes at decision time.

## Context boundary

- Global authority loaded: prior packet context plus the LL-01 program memo
- Owning boundary: exact retained `BookCorpusRegistration.states`; observation availability remains
  collector absorb time
- Relevant adjacent interfaces: `BookLeg`, `BookTopState`, immutable registration identity, and
  the fixed conservative direction in the Brazil semantic audit
- Explicitly excluded work: fees, deeper-level consumption, fills, atomicity, order routing,
  partial-fill hedging, capital costs, parameter search, protected evaluation, and trading
- Assumptions: the payout floor and leg direction come from the bound scope authority; displayed
  top state is only an optimistic execution-feasibility diagnostic

## Change boundary

- Permitted files or components: one Chronos low-latency analysis module, adapter exports/tests,
  LL-01 documentation, and this packet/receipt
- Allowed state effects: immutable in-memory definitions and screen results
- Forbidden state effects: database access, retained-byte mutation, production writes, fee
  inference, quote interpolation, future/nearest joins, or performance claims

## Correctness

- Governing invariants and decisions: I1, I11, I13, I17, I24; information is available only at
  `available_at`; observation is not belief
- Concrete failure modes: use the future other-leg quote; count two updates at one collector time
  twice; admit stale state beyond the predeclared age; reverse the authorized legs; call display a
  fill; let a delayed quote alter the original signal; treat equality to payout as positive edge
- Expected inputs and outputs: exact two legs, payout floor, strict minimum gross edge, max quote
  age, and fixed action delay produce immutable decision records with decision and delayed displayed
  costs, edges, sizes, and source ordinals
- Violating mutation or counterexample: replace the as-of join with nearest-time selection; a future
  adverse quote must incorrectly erase an earlier legal candidate and make the test red
- Required local tests/evals: definition validation, causal as-of join, same-time coalescing, strict
  edge, staleness, delay survival, and registration-scope mismatch
- Required integration evidence: run against a synthetic retained/replayed registration; production
  quote values remain unavailable until deployment and capture

## Completion evidence

- Focused LL-01 tests pass
- Existing Polymarket adapter suite remains green
- Ruff, formatter, basedpyright, and `git diff --check` pass
- Receipt preserves the distinction between gross displayed feasibility and executable net value

## Boundary revisions

None at packet open.

## Transition receipt

### Result

- Packet: `polymarket-ll01-gross-feasibility`
- Status: **COMPLETE** for the predeclared gross displayed-state screen.
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the completed
  dual-clock capture and Chronos book-corpus working-tree deltas.
- Resulting repository state: the working tree containing this receipt; no commit, live read,
  deployment, or order was created.

### Delivered state delta

- Added an immutable definition carrying exact directed legs, scope authority, payout floor,
  strict minimum gross edge, maximum quote age, and fixed action delay.
- Added union-clock evaluation that coalesces every state sharing one collector absorb time before
  taking one decision and uses only latest-as-of state for the other leg.
- Added strict positive dominance: equality to the payout floor is not an opportunity even when
  the configured minimum edge is zero.
- Added displayed top sizing as the smaller of the two ask sizes and a separate arrival-time
  displayed cost/edge/size record. Arrival values never rewrite the decision signal.
- Added scope checks requiring exact agreement between the retained authority/legs and the strategy
  definition. Book registration now also rejects detached or mutated replay states whose clocks,
  dimensions, or values no longer match the immutable registered observations.

### Evidence

- LL-01 screen adversaries: `7 passed`; book-corpus plus screen adversaries: `16 passed`.
- Full Polymarket adapter suite: `86 passed`.
- Broader Chronos suite excluding the two sandbox-incompatible localhost-server modules:
  `455 passed`.
- Full formatter: `161 files already formatted`; full Ruff passed; full basedpyright reported `0
  errors, 0 warnings, 0 notes`; `git diff --check` passed.
- Causal counterexample: a favorable state at collector second two remains the legal signal even
  when an adverse other-leg quote arrives at second three. With a two-second action delay, the
  original +0.05 displayed edge remains recorded while the arrival diagnostic becomes -0.05.

### Knowledge carried forward

- LL-01 now has an exact first-stage falsifier: if no strict gross best-touch gap exists under
  causal as-of joins, freshness, and fixed action delay, fees and deeper asks cannot rescue H1.
- A positive screen is only a reason to retain fee schedules and build full-depth/failed-leg paper
  execution. It is not arbitrage evidence because displayed size may cancel or fail to fill and
  cross-venue atomicity is absent.
- The screen intentionally does not search thresholds, latencies, or staleness. Those values are
  part of definition identity and must be fixed before production quote values are inspected.
- No empirical result exists: `POLYMARKET_DATABASE_URL` is not configured in this workspace,
  and the dual-clock collector change has not been deployed to generate admissible rows.
