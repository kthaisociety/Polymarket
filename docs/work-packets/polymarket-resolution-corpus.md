# Work packet

## Identity

- Packet: `polymarket.retain-and-register-resolution-corpus`
- Owning architecture block: data foundation.
- Semantic transition or responsibility: convert an exact read-only production selection of
  Polymarket contract identity, sampled price paths, and on-chain settlement facts into immutable
  retained source bytes and temporally registered predictor/label observations.
- Input repository state: `bdl-polymarket@ecfeb31d` on
  `codex/polymarket-time-series-research`; current production inspection proved the new server
  tables and fields under `human_ro`.

## Objective

One public Chronos command can select an explicit bounded resolved-contract cohort, prove the
production connection is read-only, read the exact event identity, price-series points, and
resolution facts now present on the server, retain canonical source bytes by digest, and register
predictors and mature labels with separate availability rules for later development/protected use.

## Context boundary

- Global authority loaded: `AGENTS.md`, `CONTEXT.md`, locked decisions, invariants, architecture
  map, and alignment policy.
- Owning block and transition contract: data-foundation `README.md`, `IMPLEMENTATION.md`, transition
  index, `data.register-observations`, `target.define-outcome`, and
  `data.build-training-sample`.
- Relevant adjacent interfaces: existing Polymarket records/reader/database/ingestion commands,
  generic temporal registration, the production `human_ro` connection proof, and the ignored local
  `data/` artifact root.
- Explicitly excluded work: engine/Kthais changes, database writes, model fitting, candidate
  selection, freeze, protected disclosure, validation, reporting, and durable memory mutation.
- Assumptions: `market.resolutions.resolved_time` is the recorded on-chain settlement availability
  time; `market.price_series.ts` is the public sampled-price observation time under an explicit
  versioned rule; retained canonical bytes, not a mutable cursor, provide the immutable source
  identity used by downstream research. Contracts whose recorded settlement precedes their
  declared close time are explicitly excluded from this close-anchored corpus rather than having
  their lifecycle silently rewritten. The append-only `market.resolutions.payouts` vector is the
  label source; mutable `market_outcomes.payout` is not treated as a competing settlement fact.

## Change boundary

- Permitted files or components: Chronos Polymarket adapter models/reader/registration/database and
  one public CLI; focused adapter tests; data-foundation implementation documentation; this packet.
- Allowed state effects: production SELECTs in a read-only repeatable-read transaction; immutable
  content-addressed files beneath an operator-selected ignored `data/` root; registered in-memory
  observations; sanitized receipts.
- Forbidden state effects: any production mutation; secrets or DSNs in outputs/artifacts; inferred
  event identity or settlement time; mutable overwrite of retained bytes; fitting or access to a
  protected partition.

## Correctness

- Governing invariants and decisions: I1, I11-I13, I17-I18, and I23-I26; exact
  `(value, reference_time, available_at)` identity; observation is not belief; separate predictor
  and label clocks.
- Concrete failure modes: reuse the old fill-only record and silently omit new facts; use contract
  close time as settlement availability; read related markets without event identity; query values
  outside a repeatable-read transaction; call a digest an immutable snapshot without retaining the
  bytes; expose a DSN; overwrite changed content at an existing identity; register outcome payouts
  as predictors; or accept a writable/unknown role.
- Expected inputs and outputs: an explicit as-of time, minimum price-point coverage, maximum market
  count, environment identity, and artifact root produce a sanitized receipt plus verified snapshot
  and registration identities. The retained payload contains exact selected rows and no credential.
- Violating mutation or counterexample: replace resolution `available_at` with `close_time`; the
  maturity adversary must become red because a label enters before its recorded settlement.
- Required local tests/evals: exact SQL/protocol mapping, read-only proof, deterministic selection,
  canonical-byte/digest identity, conflict detection, event grouping, distinct price/resolution
  availability, and missing/inconsistent row failures.
- Required integration evidence: execute the public command against production through
  `human_ro`, verify the retained object offline, and build legal pre-resolution and
  post-resolution information boundaries from the exact snapshot.

## Completion evidence

- Focused adapter tests, type checking, lint, and the complete Chronos gate pass.
- A live sanitized receipt records role proof, cohort/event/point counts, exact query/as-of identity,
  retained content digest, registration identities, and caveats without values or credentials.
- The data-foundation implementation map and public README match the new executable path and remove
  only red gates that the live evidence actually closes.
- Packet closes with an explicit transition receipt; downstream research remains a separate packet.

## Boundary revisions

None.

## Transition receipt

### Result

- Packet: `polymarket.retain-and-register-resolution-corpus`
- Status: **COMPLETE**.
- Input repository state: `bdl-polymarket@ecfeb31d` on
  `codex/polymarket-time-series-research`.
- Resulting repository state: the local commit containing this receipt on the same branch.

### Delivered state delta

- Added strict bounded corpus records, a parameterized SELECT-only production reader, canonical
  content-addressed retention, distinct price and resolution registrations, a read-only repeatable-
  read composition, and a sanitized public snapshot command.
- Preserved the original fill-tape adapter. No engine, Kthais, trading, or database-write code
  changed.
- Updated active navigation and research guidance to distinguish fill-only limitations from the
  exact semantics now available through a verified retained corpus.

### Evidence

- Focused causal tests prove event identity, exact settlement time/payout, price identity, maturity
  separation, immutable-byte reuse/conflict behavior, missing-access failure, and expanded read-only
  privilege denial.
- The complete Chronos gate passed: 150 files formatted, Ruff clean, basedpyright
  `0 errors, 0 warnings, 0 notes`, and `419 passed`.
- The public production command proved `human_ro`, session and transaction read-only status, and a
  repeatable-read transaction. It retained 19,434,443 canonical bytes containing 200 resolved
  contracts across 31 server event groups and 71,467 60-second price samples.
- Exact retained identity:
  `polymarket-corpus:610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f`.
  The sanitized receipt contains no questions, prices, payouts, DSN, or credential.

### Knowledge carried forward

- The prior blockers were stale adapter limitations, not missing production facts. The server now
  provides append-only resolution availability, payouts, event identity, and historical sampled
  prices.
- Real data exposed two distinctions now enforced permanently: early-settled contracts cannot enter
  a close-anchored design, and append-only `resolutions.payouts` is authoritative over the mutable
  outcome projection.
- This receipt proves a reproducible registered corpus. It does not prove a predictive candidate,
  protected evaluation, validated finding/rejection, report, or terminal memory update.
