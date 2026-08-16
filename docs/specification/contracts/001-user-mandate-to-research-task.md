# Contract 001 — UserMandate → ResearchTaskProposal → human-confirmed ResearchTask

Status: **LOCKED at high-risk semantic fidelity by global seam mission.confirm-task**

Canonical detailed contract:
[`../../architecture/mission/transitions/confirm-task.md`](../../architecture/mission/transitions/confirm-task.md).

## Arrow

```text
UserMandate + versioned environment/schema metadata
→ TaskCompiler
→ ResearchTaskProposal + human-readable readback
→ exact human confirmation
→ ResearchTask
```

Human edits or clarification create a new proposal version and require a new readback and
confirmation. A proposal is not an authoritative task and cannot initialize research.

## Responsibility

Turn open human research intent into a durable, structured, actionable mission without silently
changing, narrowing, completing, or researching it. The human who supplied the mandate authorizes
the initial mission by confirming the exact proposal reviewed.

The task may remain formally incomplete when its mission is clear enough for autonomous
orientation. Blocking mission ambiguity requires clarification before confirmation.

## Required meaning

The proposal/task preserves at least:

```text
original mandate
formalized mission and objective mode
target concept / resolved target ref where legitimate
forecast horizon as an exact elapsed or civil-calendar identity, when supplied
relationship type (for example association vs predictive power)
geographic and temporal scope where supplied
seed hypotheses/resources distinct from hard constraints
unresolved formal scientific semantics
assumptions and metadata-backed resolutions
completion expectations and bounded stopping account
environment/schema identity
proposal/task version and lineage
compilation and confirmation provenance
```

For broad discovery, one positive candidate is not completion. Resolution later requires a bounded
account of searched, tested, rejected, surviving, inaccessible, and materially untested paths.

## Invariants

1. The original mandate remains recoverable.
2. Scientific identity cannot drift during formalization or confirmation.
3. Missing semantics remain explicit rather than fabricated.
4. Association/correlation cannot silently become predictive power, or the reverse.
5. Suggested sources remain seeds unless explicitly declared constraints.
6. Material task-level rescope creates a new task version; subordinate questions, targets, horizons,
   objectives, hypotheses, and methods may evolve inside the same confirmed main goal without
   versioning the task.
7. Historical environment/schema identity remains interpretable.
8. Compilation reads metadata, not protected contents or whole datasets.
9. No authoritative `ResearchTask` exists before exact human confirmation.
10. Confirmation of one proposal cannot authorize a changed/stale proposal.
11. Compilation/confirmation cannot create research findings, sessions, episodes, state, evidence,
    exposure, backtests, promotions, memory, or skills.

## Outcomes and failure

Exact enum names are implementation-level, but the boundary must distinguish:

- reviewable actionable proposal, whether formally complete or carrying researchable uncertainty;
- blocking clarification required;
- invalid/unresolvable input or metadata reference;
- human rejection/revision;
- confirmed exact proposal;
- stale/mismatched confirmation;
- duplicate exact confirmation versus semantic conflict;
- coherent publication failure.

No default horizon, nearby target, latest environment, changed proposal, or model-authored guess is
a valid fallback.

An exact horizon is not a numeric month count. Elapsed durations and civil-calendar months/quarters
are distinct meanings. Calendar horizons must expose anchor, month-end, timezone, and DST/fold
behavior in the readback and confirmation identity; a compiler may not turn them into fixed day
counts.

## Acceptance evidence required

The future executable suite must cover:

1. faithful readable formalization of a broad discovery mandate;
2. blocking ambiguity versus researchable uncertainty;
3. no task or research before confirmation;
4. exact proposal/version/semantic confirmation;
5. edit/rejection requiring new readback and confirmation;
6. idempotent exact confirmation and conflict on changed semantics;
7. historical environment identity;
8. coherent publication under injected failure.

See the canonical mission.confirm-task contract for false-success mutations and discriminating test designs.

## Meta-test

> Did the instruction giver knowingly authorize the exact durable mission the autonomous researcher
> will pursue, including its breadth, uncertainty, constraints, and stopping obligation?
