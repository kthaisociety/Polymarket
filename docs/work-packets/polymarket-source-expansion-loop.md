# Work packet: Polymarket source expansion loop

## Identity

- Packet: `polymarket.expand-research-source`
- Owning architecture block: data foundation.
- Semantic transition or responsibility: exact scouted source candidate → retained, derived, and
  temporally registered Polymarket research dataset.
- Input repository state: `bdl-polymarket@747c1345` on
  `codex/polymarket-time-series-research`.

## Objective

Give the existing research loop one public, reproducible path for an external search agent to
propose additional public Polymarket data and for Chronos to acquire and register exactly one
selected official CLOB price-history source into its local research workspace without writing to
the production database.

## Context boundary

- Global authority loaded: `AGENTS.md`, `CONTEXT.md`, locked decisions, invariants, architecture
  map, AI/sandbox authority, and scientific kernel.
- Owning block and transition contracts: data-foundation `README.md`, transition index,
  `IMPLEMENTATION.md`, `data.propose-source-candidates`, `data.retain-source-snapshot`,
  `data.derive-dataset`, and `data.register-observations`.
- Relevant adjacent interfaces: `SourceScoutingService`, `DataWorkspace`,
  `TemporalRegistrationAuthority`, the Polymarket corpus identities, and constrained analysis.
- Explicitly excluded work: production database writes, engine/Kthais changes, authenticated
  trading endpoints, general web-crawler implementation inside Chronos, automatic scientific
  usefulness claims, feature/model fitting, protected exposure, and durable memory mutation.
- Assumptions: Polymarket's documented public `GET https://clob.polymarket.com/prices-history`
  endpoint returns timestamped historical outcome-token probability observations. Its `t` is used
  as both reference and public-observation availability only under an explicit versioned adapter
  rule and caveat; the samples are not executable quotes and retrieval does not prove historical
  revision/deletion behavior.

## Change boundary

- Permitted files or components: one Polymarket source-expansion adapter and CLI, the generic
  offline-transform time helper required by the documented Unix timestamp response, exports,
  focused causal/command tests, active data-foundation/README documentation, and this packet.
- Allowed state effects: append unverified scouting metadata, fetch one exact selected public URL,
  retain immutable response/parser/output bytes and manifests below an operator-selected local
  workspace, and create in-memory registered observations/catalog attestations.
- Forbidden state effects: any production/engine/database mutation; arbitrary or unselected URL
  fetch; credential retention; redirect to an unapproved host/path; response values in sanitized
  receipts; inferred event/token identity; registration from an unverified source; or direct
  research-state/promotion mutation.

## Correctness

- Governing invariants and decisions: I1, I9, I13, I17-I18, I20, and I24; exact
  `(value, reference_time, available_at)` identity; provider-neutral source proposal containment;
  observation is not durable belief.
- Concrete failure modes: a scout-proposed URL changes token/window/fidelity; an unselected source
  is fetched; redirect leaves official CLOB price history; timestamps are unordered/out of bounds;
  prices are outside `[0, 1]`; malformed JSON partially registers; source bytes mutate after
  retention; candidate text grants itself availability/scientific authority; or the command calls
  acquisition/registration success after a failed intermediate stage.
- Expected inputs and outputs: an exact retained scouting report/candidate and exact market/event/
  outcome/window need yield verified source and derived refs plus an authority-issued registered
  dataset/catalog and a value-free receipt.
- Violating mutation or counterexample: change only the selected candidate's outcome-token query;
  acquisition must be denied before any HTTP request.
- Required local tests/evals: strict need/URL validation, only-selected fetch, redirect rejection,
  canonical derivation/registration, temporal availability, malformed/range/order failure, source
  corruption failure, sanitized public command, and deterministic retry identities.
- Required integration evidence: exercise the public path against the documented official endpoint
  for one exact non-protected development token and verify the locally retained registration can
  produce a legal `InformationSet` without touching production.

## Completion evidence

- Focused tests, lint, strict type checking, and the complete Chronos gate pass.
- A sanitized live receipt binds the scouting report/candidate, source/derived refs, temporal
  profile, registration/catalog identities, observation count/time coverage, and caveats without
  emitting prices, credentials, or protected values.
- Active implementation docs distinguish external scouting, local acquisition/registration, and
  production DB ingestion.
- A transition receipt records the exact live evidence and remaining source-family/runtime reds.

## Boundary revisions

- The first live official acquisition returned HTTP 403 to Python's default `urllib` user agent
  while the exact URL returned HTTP 200 to a non-default public client. The packet expands the
  existing selected-candidate handoff to accept explicit request headers. Header names enter the
  manifest; exact values are bound by the request digest but are not printed. The source adapter
  supplies only `Accept` and a descriptive public `User-Agent`; credential-bearing behavior remains
  outside this composition.
- A corruption retry exposed that acquisition-ledger identity included only request identity, so a
  later fail-closed receipt conflicted with the earlier successful receipt. The linkage now binds
  the complete value-free fetch receipt, preserving both append-only attempts without converting
  corruption into stale success.

## Transition receipt

### Result

- Packet: `polymarket.expand-research-source`
- Status: **COMPLETE**
- Input repository state: `bdl-polymarket@747c1345` on
  `codex/polymarket-time-series-research`.
- Resulting repository state: the local commit containing this receipt on the same branch.

### Delivered state delta

- A strict `PolymarketPriceHistoryNeed` binds exact environment, server-provided market/event/
  outcome-token identity, aware time bounds, and fidelity to the one canonical official CLOB URL.
- Public commands now create a passive external-scout request and turn one exact issued candidate
  into immutable source bytes, an offline derived temporal envelope, an authority-issued registered
  dataset, and a value-free receipt.
- The generic fetcher can fail closed on redirects before contacting their target, the offline
  transform sandbox has one pure Unix-UTC conversion helper, and scouting acquisitions retain
  exact attempt outcomes.
- The Polymarket startup skill exposes this as an optional research move. It does not prescribe a
  feature, label, model, or exhaustive method list.

### Evidence

- The live public command selected one non-protected development token from the retained 200-market
  production corpus and acquired the documented official endpoint without reading from or writing
  to PostgreSQL during expansion.
- The retained live slice contains 22 registered observations from
  `2026-07-18T01:00:07+00:00` through `2026-07-18T22:00:10+00:00`. Exact replay reproduced source
  `source:8ae0d45e50c5c6cc7ac92b35d8da2fe0788902b19aa5c787f55ad5a848031c97`, derived
  `derived:a81e4461a23796e3c52e94ff45f84ef4ae2081ffcb2bd596a706ad6bbd5086cd`, and the same profile,
  registration, and catalog attestations. The sanitized study receipt emits no probabilities.
- Causal regressions deny a changed token URL before network contact, refuse redirects before a
  target is contacted, reject empty/malformed/unordered/out-of-range/non-probability responses,
  detect source corruption, keep distinct need schemas distinct, enforce availability through
  `InformationSet`, and prove sanitized public command output.
- Skill validation and repository documentation/skill tests pass. Ruff formatting/lint and strict
  basedpyright are clean. The complete gate and final test count are recorded in the commit handoff.
- Production proof status remains `10 HARNESS_GREEN`, `5 EXPECTED_RED`, `0 UNEXPECTED_GREEN`, and
  `0 HARNESS_BUG`.

### Knowledge carried forward

- Official CLOB price-history samples are probability observations, not trades or executable
  quotes. The documented timestamp is used as availability only under the explicit adapter rule;
  historical revisions/deletions remain unknown.
- The new path expands a local content-addressed Chronos workspace. It does not backfill the
  production database and it does not make external scouting authoritative.
- Source scouting remains an external Codex/orchestrator action with a passive JSON handoff; the
  Chronos scientific runtime itself does not gain arbitrary web or agent-spawn capability.
- Registration proves legal data availability, not usefulness. Joining a new registered slice to
  an exact development view, authoring a hypothesis, spending a trial, and retaining its result are
  subsequent research-loop actions.
- Other source families, persistent cross-process scientific catalog composition, automatic
  source-quality comparison, and `exploration-to-development-evidence` remain explicit reds.
