# Chronos documentation map

Use this page to select context. Do not bulk-load `docs/`: current authority, implementation maps,
completed work packets, and experimental design records serve different purposes.

## Research path

For a live Polymarket study, read only:

1. the [project landing page](../README.md) and
   [`$start-polymarket-research`](../.agents/skills/start-polymarket-research/SKILL.md);
2. its [Polymarket boundary](../.agents/skills/start-polymarket-research/references/polymarket-boundary.md);
3. the smallest applicable analysis, candidate-design, or backtest-gate skill;
4. a relevant section of the
   [financial-ML idea catalog](research-guidance/financial-machine-learning-ideas.md) only when a
   concrete question needs alternatives.

The executable harness and retained receipts—not guidance prose—decide data authority, temporal
legality, scientific identity, protected exposure, and memory.

## Implementation path

For a material code or architecture change:

1. read [`AGENTS.md`](../AGENTS.md), [locked decisions](specification/DECISIONS.md),
   [invariants](specification/INVARIANTS.md), and the relevant terms in [`CONTEXT.md`](../CONTEXT.md);
2. open the owning block in the [semantic architecture map](architecture/README.md);
3. read that block's `README.md`, `transitions/README.md`, `IMPLEMENTATION.md`, and exact transition
   contract;
4. load only the cross-cutting specification or adjacent contract that governs an input, output,
   authority, time boundary, identity, state effect, or failure under change;
5. use `$execute-work-packet` for material work.

If authoritative sources conflict, follow
[the contradiction protocol](specification/ALIGNMENT_AND_DIAGRAMS.md) instead of choosing silently.

## Document classes

| Location | Status and use |
|---|---|
| `docs/specification/DECISIONS.md`, `INVARIANTS.md`, approved contracts | Canonical authority. |
| `docs/specification/` subsystem documents | Cross-cutting semantic authority when relevant to the selected transition. |
| `docs/architecture/<block>/README.md` | Current visual responsibility map. |
| `docs/architecture/<block>/transitions/` | Exact semantic mapping contracts. |
| `docs/architecture/<block>/IMPLEMENTATION.md` | Current code paths, tests, completed transitions, and remaining reds. |
| `docs/work-packets/` | Completed or active scoped work records and receipts; evidence of change, not replacement authority. |
| `docs/specification/experiments/` | Historical/provisional eval and seam-design evidence; load only for related evaluation work. |
| `docs/specification/MILESTONE_*`, `IMPLEMENTATION_PLAN.md`, `SPEC_AUDIT.md` | Historical design/readiness records; not current implementation status. |
| `docs/research-guidance/` | Optional method catalogs; not evidence or mandatory workflow. |
| `docs/styleguide/` | Code and test conventions for implementation work. |
| `studies/` | Exploratory research ledger with exact receipts/artifacts; not terminal runtime memory. |

## Current Polymarket truth

- Live production reads are proved read-only under `human_ro` and enter Chronos through the
  Polymarket adapter.
- Registered fill tapes can reach the constrained exploratory analysis harness with exact actual
  access and persisted receipt identities.
- The server now exposes append-only resolution timestamps, payouts, event identity, and historical
  sampled prices. The bounded corpus command retains exact bytes and registers separate predictor
  and label clocks, closing those former red gates for that retained corpus only.
- The first retained-corpus study executed seven exact authored trials over 24 chronological
  development events while keeping the final 7 events unavailable. The raw sampled probability
  beat an unconditional baseline, but momentum and calibration adjustments failed grouped
  walk-forward controls, so no protected request or validated-memory mutation occurred.
- Historical executable quotes remain distinct from sampled probabilities. Live fill/cursor reads
  are still mutable unless separately retained, and development/protected composition must operate
  from the retained corpus rather than claiming the live database itself is immutable.
- Standalone `ModelProvider` context does not automatically load repository skill files. Repository-
  aware agents use them explicitly until a separate version-bound routing transition is implemented.
