# Work packet

## Identity

- Packet: `polymarket.disposition-data-sufficiency`
- Owning architecture block: Polymarket data foundation composed with open-ended exploration.
- Semantic transition or responsibility: Prove or reject whether the production on-chain history
  can causally reconstruct wallet inventory and average cost immediately before each fill, before
  any disposition-effect strategy is authored or tested.
- Input repository state: `bdl-polymarket@712fc693bd17` on
  `codex/polymarket-time-series-research`, after the frozen probability-weighting candidate.

## Objective

Audit the live read-only substrate for complete fill and Conditional Tokens Framework lifecycle
history. Continue to a predeclared disposition-effect screen only if the backward cursor has
reached the configured CTF Exchange genesis, every scope-growth repair is done, all required tables
are readable, and market identity coverage is adequate. Otherwise preserve the rejection of the
data substrate and do not manufacture historical positions from the current position projection.

## Context boundary

- Authority loaded: Chronos global authority; data-foundation and exploration architecture;
  time-series analysis and feature-design principles; engine position replay semantics.
- Production authority: `human_ro`, repeatable-read, transaction read-only, SELECT only.
- Configured Polymarket genesis block: `33605403` from `engine/config/apps/ingest.toml`.
- Explicit exclusions: writes to production; protected-corpus access; current `market.positions` as
  historical truth; outcome-based account selection; executable-price or public-mempool claims.

## Change boundary

- Permitted: this packet; one SELECT-only audit source; one sanitized audit receipt; study README
  and index updates; and, only after a passing audit, a separate predeclared development packet.
- Allowed effects: production SELECTs inside the proved read-only transaction and local research
  artifacts.
- Forbidden: production mutation, core runtime edits, strategy testing before the audit gate,
  protected evaluation, and edits to unrelated low-latency work.

## Correctness

- Failure modes: using a forward cursor as proof of history; ignoring pending scope repairs;
  replaying fills without splits, merges, or redemptions; conflating the current position projection
  with a historical snapshot; missing unmapped token or condition identities; double-counting raw
  exchange logs as wallet actions; or using settlement information at a prior decision time.
- Inputs/outputs: operational cursors and repair ledger plus bounded existence/range coverage of raw
  fills, normalized attributed fills, CTF lifecycle events, market identities, and the current
  diagnostic position projection produce a sanitized readiness decision.
- Counterexample: millions of recent fills do not make the substrate complete when the history
  cursor remains above genesis or even one tracked market retains a pending repair.
- Verification: query identity is retained; the runner proves `human_ro`, default and active
  read-only settings; the source contains one SELECT statement; no account, question, token, DSN,
  secret, price path, or payout value is emitted.

## Predeclared decision rules

The audit is sequential. The inexpensive operational gate evaluates clauses 1--4 first. Clauses
5--6 are exhaustively evaluated only if that gate passes, because their full-history joins cannot
change a failure caused by incomplete collection. The inventory replay substrate passes only if
all clauses eventually hold at the audit transaction:

1. `pm-onchain-history.cursor.block <= 33605403`.
2. Polymarket pending scope-repair count is zero and no done repair is partially covered.
3. `human_ro` has SELECT privilege on all four required internal lifecycle tables, normalized
   fills, market identity/outcomes, and the operational cursor/repair tables.
4. Raw order fills, normalized fills, splits, merges, and redemptions are non-empty.
5. Every normalized Polymarket fill maps to a known market and outcome.
6. Every split, merge, and redemption condition maps to a known Polymarket market.

Failure of any clause blocks the disposition strategy screen. Passing permits a new, independently
predeclared development packet; it is not itself evidence for the behavioral mechanism or profit.

## Completion evidence

- Sanitized JSON receipt with exact SQL SHA-256, repository input state, audit time, cursor gate,
  repair gate, table ranges/existence, mapping diagnostics, privilege diagnostics, and decision.
- Study note explaining whether causal pre-fill inventory replay is available and what remains
  distinct from sampled-price execution evidence.

## Transition receipt

Status: **COMPLETE — DATA SUBSTRATE REJECTED FOR THIS STRATEGY**. Two aggregate-only exhaustive
queries were cancelled after 245 and 92 seconds without returning values; neither exposed strategy
data. The sequential operational gate then completed under `human_ro`.

- The backward cursor equals the configured genesis block (`33605403`).
- All required lifecycle/fill tables are non-empty and readable.
- `7,162` of `9,905` Polymarket scope-repair spans remain pending; repair completeness fails.
- The disposition mechanism and strategy were not run. Exact identity joins and wallet replay were
  correctly deferred because they could not reverse the failed repair gate.
- Exact source SHA-256:
  `c4cdcfb489ef5de55a33e78c77bcdfb8b3d774a5130c60be3702ef0472daf964`.

This closes only the readiness audit. The broader behavioral-strategy goal remains active.
