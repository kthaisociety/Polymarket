# Work packet

## Identity

- Packet: `polymarket.compose-live-read-environment`
- Owning architecture block: Data foundation
- Responsibility: make the documented live Polymarket smoke executable from Chronos' isolated
  package environment.

## Boundary

- Permitted: Chronos package metadata and lockfile, smoke packaging regression, and owning
  data-foundation documentation.
- Forbidden: engine/database mutation, credential persistence or output, scientific-state changes,
  and dependence on the parent repository's virtual environment.
- Governing invariants: I13, I17, I24, and I26.

## Failure and counterexample

The adapter tests passed while the standalone live command failed before connection on the engine
database and metrics runtime (`asyncpg`, `tenacity`, and `prometheus-client`). The parent BDL
environment contained these dependencies, so running there produced a misleading success. A
package is not standalone when a shipped command needs undeclared dependencies.

The causal regression reads Chronos' package declaration and fails if any required engine database
or metrics runtime is no longer a direct dependency.

## Transition receipt

- Status: **COMPLETE**.
- Delta: declare `asyncpg>=0.31.0`, `tenacity>=9`, and `prometheus-client>=0.26.0`, regenerate the
  Chronos lock, and retain the packaging regression.
- Integration evidence: run the smoke from `research/chronos` with its own `uv` environment and the
  approved read-only tunnel. Require `human_ro`, both read-only settings, and denied insert/update
  privileges before accepting any live read.
- Remaining reds: immutable database snapshots, historical collector availability, authoritative
  resolution availability, and event/group identity.

This packet changes package composition only. It grants no data, modeling, evaluation, or protected
authority.
