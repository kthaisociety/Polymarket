# Work packet

## Identity

- Packet: `standalone-polymarket-boundary-cleanup`
- Owning architecture block: repository composition and data foundation
- Semantic transition or responsibility: present and execute Chronos as a self-contained Polymarket research system without external runtime dependencies or source-extraction language
- Input repository state: `Polymarket@7600d2994ff5f9d778823e64f2966c0915d51cf2` on `main`

## Objective

Make the current repository self-contained in code, configuration, naming, and public documentation: direct database composition must use only local modules, operator configuration must use standalone Polymarket names, and a reader should not need external repository context to use the project.

## Context boundary

- Global authority loaded: `AGENTS.md`, `CONTEXT.md`, locked decisions, invariants, documentation map, and architecture map
- Owning block and transition contract: data-foundation README, transition index, and implementation map; this packet changes composition and presentation, not data semantics
- Relevant adjacent interfaces: package exports, live database commands, retained study scripts, tests, README, provenance documentation, and CI
- Explicitly excluded work: changing scientific results, rewriting immutable receipt identities, rewriting Git history, changing database schemas, protected-evidence access, or changing research conclusions
- Assumptions: historical receipts may retain exact environment identifiers because changing them would falsify evidence identity; current executable and public-facing surfaces must use standalone terminology

## Change boundary

- Permitted files or components: repository documentation and metadata, Polymarket adapter exports and database composition, live command configuration, reproducible study acquisition scripts, related tests, work packets, and transition receipt
- Allowed state effects: rename local source/test files and public symbols, update standalone configuration names, commit and push the verified cleanup
- Forbidden state effects: production database mutation, evidence-result mutation, protected execution, removal of rejected research, or force-pushing rewritten history

## Correctness

- Governing invariants and decisions: I1, I5, I12, I13, I17, I18, and I24; no silent fallback; immutable evidence identifiers remain intact
- Concrete failure modes: leaving an import of a missing external package; requiring a non-project environment variable; breaking downstream imports during the reader rename; rewriting historical evidence; replacing legitimate internal backtest terminology; leaving source-extraction wording that implies an external runtime dependency
- Expected inputs and outputs: current standalone repository in; standalone code/config/docs with preserved scientific semantics out
- Violating mutation or counterexample: clone only this repository in a clean path and run imports, checks, and tests without any sibling source checkout or external-project runtime configuration
- Required local tests/evals: focused Polymarket adapter and command tests, Ruff, basedpyright, full pytest, `research-agent verify`, and a targeted dependency/reference scan
- Required integration evidence: `./scripts/check.sh` from repository root plus remote CI after push

## Completion evidence

- No current executable import depends on an undeclared sibling source path
- Every current live command uses `POLYMARKET_DATABASE_URL` rather than an external-project configuration name
- Public API and test names describe the standalone database reader
- Root and architecture documentation describe only the standalone system
- Historical scientific receipts remain byte-for-byte unchanged
- Full local gate and scientific verifier pass
- Cleanup commit is pushed and remote CI passes

## Boundary revisions

None at packet opening.
