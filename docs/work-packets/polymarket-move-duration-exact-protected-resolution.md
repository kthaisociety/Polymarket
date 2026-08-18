# Work packet: exact move-duration protected resolution

## Identity

- Packet: `polymarket.move-duration-exact-protected-resolution`.
- Owning architecture block: autonomous investigation, adjacent protected evaluation.
- Semantic responsibility: an exact credible authored candidate and authority-issued plan resolve
  through independently configured freeze, governance, resource, evaluation, and validation
  capabilities without researcher-supplied authority or protected-plan substitution.
- Input repository state: `bdl-polymarket@7b844dc9` on
  `codex/polymarket-time-series-research`.

## Objective

Execute the already predeclared duration runner exactly once and retain either an independently
issued protected finding or protected rejection, with one irreversible exposure and a sealed report,
or retain a safe pre-content denial/failure without pretending that protected evidence was seen.

## Context boundary

- Global authority loaded: `CONTEXT.md`, locked decisions, invariants I1-I8, I11-I13, I17,
  I21-I26, and the end-to-end architecture.
- Owning contract: `investigation.resolve-protected-candidate`.
- Adjacent contracts: `backtest.request-evaluation`, `backtest.authorize-request`,
  `backtest.bind-protected-view`, and `exposure.record-disclosure`.
- Exact gate memo:
  [`polymarket-move-duration-protected-gate.md`](polymarket-move-duration-protected-gate.md).
- Frozen runner:
  [`source/05_exact_plan_protected_resolution.py`](../../studies/polymarket-move-duration-2026-08-17/source/05_exact_plan_protected_resolution.py),
  SHA-256 `be6215c4fe5f3ae0d4d8e46e5a490499995bf7cc7febe13c7bcfcfa5abf885d5`,
  committed at `08f06e70` before protected disclosure.
- Explicitly excluded: changing target, sample, features, model, penalty, training protocol,
  thresholds, metrics, claim, protected partition, or any Chronos/engine implementation.
- Assumption: this trusted repository runner is host composition, not researcher-authored sandbox
  code. Its program strings receive only phase-scoped scientific interfaces and cannot import or
  receive issuer capabilities, authority registries, grants, protected catalogs, or decisions.

## Change boundary

- Permitted state effects: replay the unchanged three-trial development ancestry; issue a new exact
  frozen identity bound to the issued plan; create one protected request; issue a permit or safe
  denial; if permitted, record one exposure before loading the exact protected catalog; seal one
  run/report/validation decision/finding-or-negative; write one immutable JSON receipt.
- Permitted files: the new protected receipt, this packet, the study README/ledger, and a transition
  receipt. The frozen source is read-only.
- Forbidden state effects: protected read before permit/exposure; caller-appointed authority through
  `resolve()`; exposure rollback; duplicate run on retry; development revision; result-dependent
  threshold/claim change; production database mutation; production engine or sibling-repository
  change.

## Correctness

- Inputs: exact candidate
  `authored-candidate:bb76fb6846cd5bb935934e16d53c520865f5649d230c53b0cc1ca5c3e1be770d`,
  exact evidence
  `authored-development-evidence:7729af09c56fed64323cc805df708ab2643ec547aa90877dda30e53a6e9c5372`,
  retained corpus
  `polymarket-corpus:610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f`,
  and the final seven whole-event holdout.
- Expected output: exact development identity match, authority-issued plan/resource/freeze,
  exactly one exposure if content is requested, complete declared-decision coverage or typed
  failures, immutable report, independent validation, and a reconstructible receipt.
- Concrete failure modes: alias or plan substitution; forged freeze; scope/catalog mismatch;
  self-authorization; future predictor or immature-label access; omitted failed decisions;
  duplicate exposure/execution; evaluator training; post-result threshold or claim change.
- Violating mutation: allowing the resolution request to carry a governance grant or plan object
  must make caller-authority/substitution tests fail before loader invocation.
- Local evidence already green at packet open: canonical composed suite, 469 passed; source hash and
  Git ancestry verified; no protected receipt exists.
- Required run evidence: source emits a receipt whose driver hash matches the frozen hash; receipt
  identities resolve; ledger ordering places exposure before execution; counts and metrics agree
  with the sealed report; exact rerun is idempotent or byte-identical without a second exposure.

## Completion evidence

- retain and hash the exact protected receipt;
- audit every gate, identity, decision count, failure, metric, exposure, validation status, and
  warning without modifying the frozen system;
- update the study and exploratory ledger with finding or protected rejection status;
- run targeted authored-protected integration tests plus the canonical composed suite;
- publish a transition receipt and commit the coherent boundary locally.

## Boundary revisions

The initial audit suspected source 05 granted researcher authority because trusted host composition
and model-authored program strings share one study file. The boundary did not require implementation
repair: `AuthoredProtectedResolutionService.resolve()` accepts no plan, catalog, grant, authority,
metric, threshold, or outcome from the requester. It resolves opaque capabilities from registries
configured outside the candidate program, and the program sandbox cannot import or access the host
composition. Existing substitution, forgery, retry, and full-runtime tests exercise that distinction.
The packet therefore contracts from implementation repair to exact governed execution and audit.

The first execution attempt was externally interrupted before it emitted a protected receipt. Its
in-memory privileged-operation state did not survive, and no protected value or metric was returned.
Because there is no durable checkpoint proving whether loader invocation occurred, the attempt is
conservatively classified `POSSIBLE_EXPOSURE_IN_DOUBT` in
[`05_attempt_01_interrupted.json`](../../studies/polymarket-move-duration-2026-08-17/protected-incidents/05_attempt_01_interrupted.json).
The boundary now permits only one exact recovery retry with unchanged source bytes and the same
idempotency key. This is not a fresh experiment; the possible first exposure remains history.
