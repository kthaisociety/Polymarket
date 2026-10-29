# Work packet: Chronos paper acceptance gate

## Identity

- Packet: `chronos-paper-acceptance-gate`
- Owning architecture block: Reporting
- Semantic transition or responsibility: `report.audit-paper` — audit a declared manuscript and
  its retained evidence without changing scientific status
- Input repository state: branch `codex/polymarket-time-series-research`, ahead of its upstream with
  existing user work and the retained 2026-08-24 enforced Polymarket campaigns

## Objective

Produce a deterministic, receipt-backed publication gate that inventories every declared trial,
checks every manuscript claim against exact retained evidence and statistical requirements, and
emits a machine-readable decision that cannot promote or strengthen the underlying evidence.

## Context boundary

- Global authority loaded: `AGENTS.md`, Chronos `AGENTS.md`, `CONTEXT.md`, locked decisions,
  invariants, the architecture map, and the execution-plan and alignment specifications
- Owning block and transition contract: reporting `README.md`, `IMPLEMENTATION.md`, transition
  index, and `report.render-finding`
- Relevant adjacent interfaces: campaign manifests/execution/completion receipts,
  `ValidatedFinding`, `EvaluationReport`, `ResearchLedger`, and the backtest/evaluation
  specification
- Explicitly excluded work: protected-data re-exposure, new scientific promotion, live trading,
  production writes, and retrospective conversion of exposed development evidence into fresh
  confirmation
- Assumptions: a paper may accurately publish negative, blocked, or development evidence when its
  language and scope state that status; publication acceptance is not finding promotion

## Change boundary

- Permitted files or components: reporting models/auditor/public interface/tests and documentation;
  one retained Polymarket paper-audit study containing declarations, generated reports, paper, and
  exact receipt references
- Allowed state effects: create deterministic local audit and presentation artifacts
- Forbidden state effects: mutate campaign evidence, validation decisions, exposure history,
  protected artifacts, production data, or canonical finding status

## Correctness

- Governing invariants and decisions: I7, I8, I11-I13, I17, I19, I21-I22, and I24; reporting may
  clarify substance but may not validate, promote, or decide trading usefulness
- Concrete failure modes: omitted losing trials; forged or changed evidence bytes; row-level
  uncertainty represented as event-level uncertainty; unadjusted confirmatory multiplicity;
  exploratory evidence called replicated; sampled marks called executable prices; causal or
  profitable language without the required evidence; a paper passing despite an unresolved
  required check; prose changing a machine decision
- Expected inputs and outputs: exact trial/evidence/claim declarations plus retained files produce
  per-check results, per-claim decisions, complete inventory coverage, a stable audit identity, and
  a machine-readable receipt
- Violating mutation or counterexample: changing one retained receipt byte, dropping one declared
  campaign execution, or changing a bounded claim to a profitability claim must turn the audit red
- Required local tests/evals: identity round trip, Holm correction, inventory completeness,
  statistical requirement checks, claim-language checks, execution-evidence checks, and adversarial
  mutations
- Required integration evidence: the real 2026-08-24 behavioral and stochastic campaigns audit
  against their immutable manifests, executions, and completion receipts

## Completion evidence

- Focused reporting and integration tests pass.
- Ruff, formatting, and strict typing pass on the changed surface.
- The real campaign audit produces a deterministic JSON report and publication receipt.
- A concise paper is generated from or checked against the same claim declarations and reports the
  unsupported execution and fresh-confirmation boundaries explicitly.
- Reporting architecture documentation names the new transition, code paths, guarantees, and
  remaining reds.
- A transition receipt records exact verification and what the result does not prove.

## Boundary revisions

None.

## Transition receipt

Status: **COMPLETE — 2026-08-24**.

- Publication decision:
  `paper-audit-report:e8ed21a7f08e0e35c8277138515f0cad1cf0d84f0fe6fca438aa380f0fa2d910`
  is `ACCEPT` for the exact bounded manuscript wording.
- Inventory: five campaign manifests and completion receipts; 90 governed executions; 48 unique
  analysis identifiers; 42 retained rerun executions; and 25 exact non-replay records that the
  ordinary harness must not reissue.
- Statistical enforcement: four fixed successor process tests use Holm correction; two selected
  stochastic tests use a conservative Bonferroni correction across all 37 recorded search
  analyses; predictive intervals resample whole events with 10,000 deterministic draws; every
  accepted predictive/process claim carries exact falsification and stability locators.
- Artifact hashes: protocol
  `bf978c2277ef8099fce728bb1d8be3f8ee329fd5a995ebf81bee1181e5950856`; machine acceptance
  receipt `94f744ee44caa5d067b23cf7fc8e12ed4051d13cb7568ed2d1695278c224a2b7`; concise paper
  `21fc839a5180d883a5cbcd1df9cc75eb983f82f9941384afaef5864748bd8c3e`; deterministic builder
  `4fc91ea3c2a52086e0d9bc9f8d2b9e0a3d833c14e6391274fa2e5a492dc4cb92`.
- Verification: reporting tests `16 passed`; sandbox-safe Chronos suite `584 passed`; the two
  loopback-server modules `45 passed` with local socket permission, for 629/629 total; Ruff check
  and format clean; full Basedpyright `0 errors, 0 warnings, 0 notes`; canonical docs index
  generated; deterministic rebuild and machine-receipt identity verification passed; and
  `git diff --check` passed.
- Scientific disposition: no execution-validated strategy and no protected finding were issued.
  The longshot fade remains selection-exposed development evidence requiring a newly accrued,
  untouched, frozen one-shot cohort. Any profitability claim still requires historical
  quotes/order books, observed spreads and fees, latency, queue position, partial fills, and
  event-level net-edge uncertainty.
