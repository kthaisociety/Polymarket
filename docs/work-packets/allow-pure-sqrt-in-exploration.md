# Work packet: allow pure square root in exploratory analysis

## Identity

- Packet: `sandbox.allow-pure-sqrt`.
- Owning architecture block: open-ended exploration.
- Semantic transition or responsibility: `sandbox.execute-analysis` pure numerical call surface.
- Input repository state: `bdl-polymarket@94ea6b1d`.

## Objective

Permit researcher-authored `sqrt(x)` inside the constrained analysis namespace so ordinary bounded
statistics such as a correlation denominator can execute without granting a host interface.

## Context boundary

- Global authority loaded: `AGENTS.md`, `CONTEXT.md`, locked decisions, invariants, architecture map.
- Owning block and transition contract: exploration `README.md`, `transitions/README.md`,
  `IMPLEMENTATION.md`, `sandbox.execute-analysis`, and `sandbox.authorize-execution`.
- Relevant adjacent interfaces: `AUTHORITY_SANDBOX_AND_TOOLS.md`, analysis source validation, safe
  builtins, and adversarial sandbox contract tests.
- Explicitly excluded work: broader scientific-library expansion, imports, filesystem/network/process
  access, data capability changes, formalization, protected access, and scientific method changes.
- Assumptions: `math.sqrt` is a deterministic scalar function with no authority or side effects.

## Change boundary

- Permitted files or components: sandbox pure-call allowlist/builtins, exploration tests, exploration
  implementation map, and this receipt.
- Allowed state effects: one additional pure numerical name in a fresh sandbox namespace.
- Forbidden state effects: any new data, host, import, persistence, protected, or privileged surface.

## Correctness

- Governing invariants and decisions: I14, I17, I18; constrain information/side effects rather than
  scientific creativity; exact authored code is preserved.
- Concrete failure mode: a real retained-corpus study was denied before data access solely because
  `sqrt` was absent while `log` and `exp` were present.
- Expected inputs and outputs: nonnegative numeric input returns the standard square root; ordinary
  provenance and access instrumentation remain unchanged.
- Violating mutation or counterexample: adding `math`, `__import__`, or host attribute access would
  widen authority and must remain denied.
- Required local tests/evals: successful `sqrt` calculation with actual-access provenance; existing
  denial, protected-view, timeout, and side-effect tests remain green.
- Required integration evidence: rerun the exact overround scientific design as a lineage-preserving
  child source and obtain an ordinary development receipt.

## Completion evidence

- Focused exploration tests and full quality checks proportionate to the two-line runtime change.
- Retained denied source-01 receipt plus successful or explicit-failure source-02 receipt.
- Updated exploration implementation map and transition receipt below.

## Boundary revisions

None.

## Transition receipt

### Result

- Packet: `sandbox.allow-pure-sqrt`.
- Status: `COMPLETE`.
- Input repository state: `bdl-polymarket@94ea6b1d`.
- Resulting repository state: local working state pending the packet commit.

### Delivered state delta

- Added `sqrt` to the validated safe-call set and bound it directly to `math.sqrt`.
- Added a contract test proving numerical output and instrumented data-access provenance.
- Preserved all existing policy, protected-view, resource, side-effect, and epistemic boundaries.
- Updated the exploration implementation map and corrected its stale test path.

### Evidence

- Red before implementation:
  `.venv/bin/pytest -q tests/exploration/test_analysis_sandbox.py::test_pure_sqrt_supports_authored_statistical_diagnostics`
  failed with `AnalysisStatus.DENIED`.
- Green after implementation: `.venv/bin/pytest -q tests/exploration/test_analysis_sandbox.py`
  reported `13 passed`.
- Integration: exact source SHA
  `d958ec283fcc0f70b1009768a89098304c7c2c48700dc43843122e160312443e`
  moved from a no-access policy denial to an ordinary succeeded development receipt with seven
  instrumented field accesses and no protected exposure.
- Counterfactual: removing either allowlist entry returns the new test to policy denial before data
  access; adding module/attribute access remains outside the AST call policy.

### Knowledge carried forward

- Pure scalar statistics are part of computational creativity, not new authority.
- The enabled study failed its scientific gate; runtime success did not become scientific success.
- This receipt does not prove general numerical-library completeness, tradability, formal evidence,
  or protected validity.
