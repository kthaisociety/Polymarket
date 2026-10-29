# Work packet

## Identity

- Packet: `standalone-polymarket-repository-extraction`
- Owning architecture block: data foundation and repository composition
- Semantic transition or responsibility: preserve the complete Chronos research system while making its repository and read-only database composition independent of the parent BDL engine checkout
- Input repository state: `bdl-polymarket@712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the current modified and untracked `research/chronos/` working state

## Objective

Produce a local, history-preserving `Polymarket` Git repository whose root is the current Chronos project, which contains all current Chronos code, tests, documentation, skills, studies, and evidence, contains none of the parent engine/deployment/Kthais tree, and passes its standalone verification gate without `../../engine/src`.

## Context boundary

- Global authority loaded: `AGENTS.md`, `CONTEXT.md`, locked decisions, invariants, architecture, and test strategy
- Owning block and transition contract: data-foundation README, transition index, and implementation map; this packet changes repository composition rather than scientific transition semantics
- Relevant adjacent interfaces: Polymarket read-only database composition, operator commands, test/type-check configuration, README commands
- Explicitly excluded work: scientific result changes, study deletion, protected evidence access, production writes, engine extraction, AIS repository creation, network push, and credential handling
- Assumptions: current working-tree Chronos state is authoritative and must be preserved; AIS operations require user verification after local completion

## Change boundary

- Permitted files or components: standalone repository metadata, database pool composition, Polymarket adapter typing/composition, tests, check script, README, implementation map, and work-packet receipt
- Allowed state effects: create a new local Git repository and commits; read the source repository; create and remove a temporary export ref
- Forbidden state effects: modify or discard source working-tree changes, change research evidence/status, contact AIS, mutate production data, or expose secrets

## Correctness

- Governing invariants and decisions: I1, I12, I13, I17, I18, I24; no silent fallback; evidence and rejected studies remain immutable history
- Concrete failure modes: losing uncommitted studies; copying engine code; leaving parent-relative imports; silently weakening the read-only proof; including caches/secrets; overstating successful live access; producing an unpushable repository
- Expected inputs and outputs: current Chronos tree and filtered history in; standalone `Polymarket` repository and green local gate out
- Violating mutation or counterexample: remove/rename the parent engine checkout and show imports, type checks, tests, and CLI verification still work locally
- Required local tests/evals: focused standalone database composition tests, Ruff format/lint, basedpyright, full pytest, repository boundary audit
- Required integration evidence: `scripts/check.sh` from the standalone root and proof that no tracked path or source/config reference requires `../../engine/src`

## Completion evidence

- Clean standalone Git status after commits
- Verified filtered history and current research artifacts
- No parent repository directories or cache/credential files
- No parent-relative engine path dependency
- Full local quality gate passing
- Transition receipt committed
- User approval requested before any AIS operation

## Boundary revisions

None at packet opening.
