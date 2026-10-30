# Work packet

## Identity

- Packet: LL-04g content-addressed application-plan precommit
- Owning architecture block: Data foundation with a development-validation consumer
- Semantic transition or responsibility: one exact LL-04f application plan to an immutable,
  path-independent plan receipt, then receipt plus structurally identical plan to the unchanged
  LL-04f application result
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the uncommitted
  low-latency program through LL-04f in this worktree

## Objective

Provide a fail-closed local precommit boundary that content-addresses every scientific field of an
LL-04f plan and refuses a missing, corrupted, or structurally changed plan before any retained quote
corpus is loaded.

## Context boundary

- Global authority loaded: repository and Chronos `AGENTS.md`, style guide, `CONTEXT.md`, locked
  decisions, invariants, semantic architecture map, test strategy, and feature-design principles.
- Owning block and transition contract: data-foundation `README.md`, transition index,
  `IMPLEMENTATION.md`, and `data.retain-source-snapshot`; the store adopts immutable
  content-addressed retention mechanics without claiming network acquisition or formal ledger
  authority.
- Relevant adjacent interfaces: LL-04f `ActivityGateApplicationPlan`, `BookCorpusStore`, complete
  H3/H5 definitions, LL-04d policy, LL-04e standard, and
  `development.evaluate-candidate`'s development/protected distinction.
- Explicitly excluded work: database or network access, corpus capture, quote inspection, block or
  market selection, plan decoding into executable domain objects, threshold search, fitting,
  protected evaluation, ledger authority, external timestamping, orders, and live trading.
- Assumptions: the operator supplies an isolated plan-store root. A verified local receipt proves
  exact retained bytes and exact runner input, but its filesystem metadata alone does not prove
  that retention preceded quote inspection; scientific use still needs independently ordered
  durable evidence.

## Change boundary

- Permitted files or components: one plan-retention/precommit module and adversarial test,
  Polymarket public exports, data-foundation/development implementation maps, study status, and this
  packet/receipt.
- Allowed state effects: create one canonical content object beneath the operator-selected plan
  store with exclusive creation; exact retries are idempotent. The verified runner reads the plan
  object and then delegates to LL-04f.
- Forbidden state effects: overwrite or repair retained objects, load a corpus before plan
  verification, include quote values or secrets in plan bytes, mutate the plan, infer wall-clock
  ordering, access protected evidence, validate/promote, or place orders.

## Correctness

- Governing invariants and decisions: I2 learned-state legality, I5 frozen identity immutability,
  I6 no fallback, I11 immutable evidence, I12 rejected-history retention, I13 provenance, I17 formal
  failure, I18 side-effect control, I21 evaluation is not training, I22 development/protected
  separation, I24 environment identity, and I25 retry idempotency.
- Concrete failure modes: omitting a nested policy or parent parameter from identity; normalizing
  ordered blocks or bindings into an unordered set; accepting an old receipt for a changed plan;
  loading quote bytes before checking the receipt; accepting a missing, size-mismatched, or
  hash-mismatched plan object; overwriting conflicting bytes; or presenting local retention as
  independent time-order proof.
- Expected inputs and outputs: one valid LL-04f plan; a sanitized SHA-256/size reference and exact
  canonical JSON object; later, the same plan and verified ref produce the unchanged LL-04f result.
- Violating mutation or counterexample: change one nested H3 shock threshold while reusing the old
  plan ref. The precommitted runner must fail before `BookCorpusStore.load` can observe quote bytes.
- Required local tests/evals: deterministic canonical identity; sensitivity to every nested plan
  family and sequence order; exact retain/verify/retry; missing/tampered/conflicting objects; public
  import; successful LL-04f composition; and changed-plan rejection before corpus access.
- Required integration evidence: LL-04f and plan-precommit tests, complete Polymarket adapters,
  proportionate Chronos suite, format/lint/type checks, docs generation, and `git diff --check`.

## Completion evidence

- One public plan ref/store and verified runner preserve complete LL-04f scientific identity.
- Deterministic adversaries prove nested mutation sensitivity and pre-corpus failure ordering.
- Store retries are exact and immutable; diagnostics contain no path, secret, or quote values.
- Architecture and study docs distinguish exact local precommit mechanics from independent ordering
  evidence and empirical strategy results.
- A transition receipt records hashes, commands, limitations, and remaining production dependency.

## Boundary revisions

None.

## Transition receipt

### Result

- Packet: LL-04g content-addressed application-plan precommit
- Status: `COMPLETE`
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the recorded
  uncommitted low-latency program through LL-04f
- Resulting repository state: one immutable local plan store and verified runner that reject plan
  drift before LL-04f may load retained quote values

### Delivered state delta

- `ActivityGateApplicationPlanRef` binds lowercase SHA-256 and exact canonical byte size without a
  local path.
- `ActivityGateApplicationPlanStore` canonicalizes every LL-04f dataclass field, ordered block and
  binding, parent type and definition, retained snapshot ref, recipe, policy, and standard.
- Decimal spellings and exact elapsed durations are canonicalized semantically; aware datetimes are
  represented as exact UTC instants. Sequence order remains identity.
- Retention uses exclusive creation, exact-retry idempotency, and post-write hash/size verification;
  an existing conflicting object is never overwritten.
- `run_precommitted_activity_gate_application` verifies retained bytes and exact caller-plan
  identity before delegating to the unchanged LL-04f runner. Plan mismatch therefore precedes any
  `BookCorpusStore.load` call.
- Public exports and data-foundation, development, and study documentation preserve the local-
  receipt versus independent-ordering distinction.
- No database/network access, corpus capture, quote inspection, fitting, protected exposure,
  production plan retention, order, or trading state occurred.

### Evidence

- The focused adversary first failed during collection because the LL-04g module did not exist.
- Six focused LL-04g tests passed for canonical/path-independent identity, nested mutation and
  sequence sensitivity, exact retry, verification, missing/tampered/conflicting objects,
  pre-corpus rejection, public import, and unchanged LL-04f composition.
- The full Polymarket adapter suite passed: 185 tests under
  `PYTHONPATH=src`.
- The broader Chronos suite passed: 554 tests, excluding only the two previously documented
  sandbox-incompatible loopback HTTP modules.
- Ruff formatting passed across 44 Polymarket files; Ruff checking passed; full basedpyright passed
  with zero errors or warnings.
- Root docs-index generation and `git diff --check` passed.
- Plan-store source SHA-256:
  `96e6bd885b0a60eb4607bc86987ecc95971f4907b8b2102685c7767dec3e2806`.
- Plan-store test SHA-256:
  `525ef17e0bce6538d291e07209ed77aecbe298c97b9852bdedbd29666c0d49a9`.

### Knowledge carried forward

- The exact LL-04f question can now be retained and later enforced without reserializing or
  manually comparing its scientific fields.
- Content identity proves exact bytes and runner-plan equality. It does not prove that retention
  occurred before a researcher inspected quotes; filesystem timestamps are neither independent nor
  authoritative scientific ordering evidence.
- A production campaign still needs dual-clock collector deployment, an approved retained L2
  corpus, a pre-value plan receipt bound to independently ordered durable evidence, measured order
  latency and fees, semantic event grouping, and prospective acknowledgement/fill/partial-fill
  evidence.
- This receipt proves deterministic offline precommit mechanics only. It does not prove H3, H4, or
  H5 empirical alpha, fillability, scientific validation, or trading authority.
