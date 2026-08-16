# Work packet: generic autonomous data workspace

## Identity

- Packet: `data.retain-and-derive-snapshots`
- Owning architecture block: data foundation, composed with the exploration sandbox
- Responsibility: source-agnostic acquisition, immutable retention, catalog reconstruction, and
  constrained researcher-authored derivation
- Input repository state: `b8fd76bfdf79c8536577af52d3e8d964777dc7bc`

## Objective

Provide a predictable JSON operator surface that retains exact HTTP response bytes before use,
returns verified content-addressed references, and derives new datasets through a bounded offline
worker with exact input/code/parameter/runtime/output lineage.

## Context and change boundary

- Global authority: `AGENTS.md`, `CONTEXT.md`, locked decisions, I13/I14/I17/I18/I24/I25,
  architecture, lifecycle, sandbox authority, and test policy.
- Owning contracts: `data.register-observations`, `data.inspect-authorized-view`,
  `sandbox.authorize-execution`, `sandbox.execute-analysis`, and `sandbox.record-provenance`.
- Permitted surface: a generic local DataStore/DataCatalog implementation, typed snapshot refs,
  acquisition/derivation CLI, causal tests, and aligned data/exploration documentation.
- Explicit exclusions: source-specific semantics, observation registration, feature/target/model
  construction, development/protected evaluation, reporting, learning, web-search providers,
  production database/object-store durability, and permission-aware multi-user service behavior.

Acquisition alone may use the network. Derivation receives only exact bytes resolved from verified
refs, runs in a bounded worker, and has no network, filesystem, process, environment, secret, or
scientific-promotion interface.

## Failure modes and required evidence

- returned values precede durable verified bytes;
- path identity substitutes for content identity;
- byte mutation remains healthy;
- requests, manifests, or errors disclose credential/body secrets;
- retry publishes divergent or partial state;
- model-authored/unretained data becomes an authorized view;
- parser changes reuse derived identity;
- derivation escapes through filesystem/network/process interfaces;
- process restart or index loss loses canonical refs;
- source-specific API shape leaks into core acquisition.

Contract and adversarial tests must causally distinguish every mutation above, exercise two
structurally different local HTTP APIs through the same interface, and retain all existing
scientific/runtime tests as integration evidence. The canonical completion gate is:

```bash
UV_CACHE_DIR=/tmp/insurance-uv-cache ./scripts/check.sh
```

## Completion receipt

Status: `COMPLETE` in the `codex/lane-generic-data-workspace` commit containing this receipt.

Delivered state:

- immutable content objects and append-only source/derived/failed-attempt manifests;
- `SourceSnapshotRef` and `DerivedDatasetRef` with path-independent canonical identities;
- generic bounded HTTP acquisition with secret-free public records;
- rebuildable in-memory catalog plus inspect/search/verify operations;
- spawned, resource-bounded, offline authored transformation worker with actual input-read facts;
- verified derived-column adapter into the existing non-protected `AuthorizedDataView`;
- predictable-JSON `data fetch|inspect|verify|search|derive` CLI;
- Mermaid/contracts and implementation status aligned with the shipped paths.

Verification evidence:

```text
UV_CACHE_DIR=/tmp/insurance-uv-cache uv run pytest \
  tests/data_workspace/test_generic_workspace.py tests/cli/test_cli.py -q
20 passed

UV_CACHE_DIR=/tmp/insurance-uv-cache ./scripts/check.sh
122 files formatted; Ruff green; basedpyright 0 errors; 359 tests passed
```

Mutation evidence includes response/output/manifest byte tampering, path move, intermediate/object
symlink substitution, exact concurrent retry, changed response bytes, parser change, caller-minted
and input-free authored data, secret request values, oversize/timeout failure, worker host/network
escape attempts, restart, and catalog rebuild.

This packet does not claim external source discovery, production durability, hostile multi-tenant
containment, or scientific admissibility of retained bytes.
