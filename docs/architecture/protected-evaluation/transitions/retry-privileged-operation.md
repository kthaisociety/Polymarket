# governance.retry-privileged-operation — retried privileged request after uncertain ack → one irreversible result

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Prevent retries from duplicating protected execution, exposure or promotion while detecting semantic key reuse.

## Relevant locked invariants

I7, I11, I25.

## Source A

Stable privileged request key and full canonical semantic payload, durable permit/exposure/run/promotion outcome stores, uncertain acknowledgement/concurrency.

## Destination B

Original outcome/result for exact replay or IDEMPOTENCY_CONFLICT; exactly one protected execution/exposure/promotion effect.

## Mapping f

Atomically claim semantic key; recover durable outcome after lost ack; exact replay returns; changed payload conflicts; concurrent calls converge.

The in-memory contract model records `CLAIMED -> EFFECT_SEALED -> ACKNOWLEDGED`. If acknowledgement
is lost after sealing, replay returns the sealed original without rerunning the effect. A claimed
operation with no sealed result is explicitly in doubt and must be reconciled rather than retried as
if nothing happened.

## Must preserve

Full request/system/scenario/data/decision payload, original outcome and every irreversible effect/provenance.

## May transform

Equivalent representation may change where exact scientific meaning, identity and behavior survive.

## Must exclude

Key-only compare, duplicate view/run/exposure/finding, overwrite, process-memory dedupe, changed semantics accepted.

## Authority boundary

Harness idempotency boundary; retry grants no new authority and permit scope remains exact.

## Allowed state mutation

First use effects; replay reads; conflict audit only.

## Forbidden state mutation

Replay/conflict cannot re-execute/expose/promote or alter original.

## Failure semantics

Unknown outcome reconciles from durable records; never guess no exposure. Exact changed dimensions conflict.

## Observable consequences

Lost acknowledgement after exposure still returns original and creates no second run/exposure.

## False-success implementations considered

Retry starts a second protected run; exposure deduped but execution duplicated; compare key only.

## Falsifying tests

Inject lost ack after each irreversible boundary, reconstruct, replay/concurrent/change payload, assert one effect. **Level B.**

## Mutation-sensitivity check

**Mutation:** On missing response, issue a fresh permit and rerun.

**Expected failure:** Execution/exposure counts become two, test red.

## Composite dependencies

backtest.request-evaluation–ledger.preserve-scientific-history.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added fault points across all irreversible effects and durable reconciliation.

## Remaining user decisions

None.
