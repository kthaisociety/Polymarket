# Work packet: declared offline-study resource policy

## Identity

- Packet: `sandbox.declare-offline-study-resources`.
- Owning architecture block: open-ended exploration.
- Semantic responsibility: operator-declared bounded resources for exact offline authored studies.
- Input repository state: the local commit following `bdl-polymarket@60cc1bcd`, including the
  retained fresh-replication `MemoryError` receipt.

## Objective

Allow the public offline study runner to bind explicit wall-time, address-space, inline-result, and
result-size limits to the existing `AnalysisHarness`, so a large authorized corpus can execute
without weakening data scope, sandbox syntax, provenance, or protected boundaries.

## Context boundary

- Global and block authority: previously loaded `AGENTS.md`, canonical vocabulary, locked
  decisions/invariants, exploration block, `sandbox.authorize-execution`, authority/sandbox spec,
  data lifecycle, and test strategy.
- Concrete failure: exact frozen source `e97d91b…` over 157 fresh events/562 markets failed with
  `MemoryError` at the hard-coded 512 MB worker limit; no scientific result exists.
- Relevant interfaces: `ResourceLimits`, retained-corpus builder, public offline study parser, and
  conflict-detecting receipts.
- Explicitly excluded: scientific source/gates, data selection, authorization fields, sandbox safe
  syntax/calls, protected execution, production engine/database, and other repositories.

## Change boundary

- Permitted components: offline runner resource arguments, focused parser/integration tests,
  exploration implementation map, and this receipt.
- Allowed effects: a caller may request larger but still finite positive limits; the receipt keeps
  normal execution provenance and the worker continues enforcing `RLIMIT_AS`, timeout, and result
  bounds.
- Forbidden effects: unlimited resources, environment-derived silent overrides, data/protected
  authority changes, scientific fallback, or mutation/deletion of the failed run.

## Correctness

- Governing invariants: I14, I17, I18, I24, and I25.
- Expected mapping: exact positive CLI values become the exact `ResourceLimits` passed into the
  existing analysis composition. Defaults preserve prior behavior and receipt identity.
- Failure modes: partial/invalid values, unbounded sentinel values, parsed-but-ignored limits,
  changes to ordinary receipt bytes, or a resource retry overwriting prior evidence.
- Violating mutation: ignore one declared value or replace it with a hidden environment default;
  the integration test must observe the wrong bound/failure.
- Required evidence: parser/default tests, public-runner composition with explicit limits, focused
  Polymarket tests, strict static checks, and the full Chronos gate.

## Completion evidence

Status: **ACTIVE**. Close only after the declared limits are enforced by the existing worker,
defaults remain compatible, all tests pass, and the failed receipt remains retained.

## Boundary revisions

None.
