# mission.evolve-direction — Research-direction change → agenda evolution or new ResearchTask version

Status: **LOCKED — readiness level 4 of 5**

## Purpose

mission.evolve-direction lets the autonomous researcher evolve questions, hypotheses, and methods beneath a confirmed
main goal without turning the task into a frozen experiment. At the same time, it prevents that
freedom from becoming silent replacement of the human-authorized mission.

The local invariant is not “a changed field creates a task version.” It is:

> The research agenda may evolve autonomously while the confirmed main goal and hard constraints
> remain intact; changing that task-level semantic core requires explicit respecification and a new
> `ResearchTask` version.

## Relevant locked invariants

- **I10 — Mission cannot silently drift.** Task-level target, horizon, objective, or other research
  identity changes require explicit respecification/versioning. Hypotheses and questions within the
  same problem do not.
- **I24 — Environment identity is explicit.** Historical work remains interpretable under the task,
  environment, and schema versions that governed it.
- **I25 — Runtime retries do not duplicate irreversible effects.** Retried agenda/rescope requests
  cannot duplicate publication or rebind history.
- **mission.confirm-task — Human-confirmed task authority.** A genuine replacement of the confirmed main goal or
  hard constraints returns to proposal/readback/exact-confirmation authority before a new task
  version becomes authoritative.

Authoritative sources: `INVARIANTS.md` I10/I24/I25, Contract 001, `CONTEXT.md`, and mission.confirm-task.

## Source A

The source is a proposed research-direction change evaluated against an exact current
`ResearchTask` version. It contains or references:

- the exact base task identity/version and its confirmed semantic core;
- the proposed question, subquestion, objective, target, horizon, hypothesis, method, source, or
  constraint change;
- the requesting actor and request/idempotency identity;
- an explicit account of how the proposed direction serves the main goal;
- any declared effect on hard constraints or task-level completion meaning;
- the current agenda version when the proposal changes durable agenda state.

The confirmed semantic core includes the main goal, human-declared hard constraints, and
task-level completion obligation. A target, horizon, or objective is part of that core only when its
meaning is task-level; the same kind of field may legitimately belong to a subordinate question.

## Destination B

mission.evolve-direction has three explicit outcomes:

1. **Goal-preserving agenda evolution** — the same `ResearchTask` identity/version remains
   authoritative and a provenance-bearing research question or related agenda change is recorded.
2. **Potential rescope** — the relationship to the main goal is ambiguous, unsupported, or appears
   to alter the semantic core. Nothing is adopted; the agent may explain/reformulate or a rescope
   proposal may be prepared.
3. **Confirmed genuine rescope** — after proposal/readback/exact human confirmation, a new immutable
   `ResearchTask` version is published with explicit parent lineage and semantic difference.

Exact result names and storage types are implementation choices.

## Mapping f

```text
ProposedResearchDirectionChange + exact current ResearchTask/agenda versions
    → evaluate against confirmed main goal and hard constraints
        → goal demonstrably preserved
            → evolve agenda under the same ResearchTask version
        → ambiguous or task core would change
            → adopt nothing; surface potential rescope
        → genuine rescope proposed and exactly human-confirmed
            → publish new ResearchTask version with parent lineage
```

The agent may autonomously add, refine, prioritize, abandon, or replace subordinate research
questions. It may explore prediction beneath a broad relationship-discovery goal, add a forecast
horizon to that subquestion, investigate regional variation, change candidate sources, or test new
hypotheses without versioning the task when the main goal and constraints remain intact.

The agent may request and explain a genuine rescope, but cannot authorize a replacement main goal
or weakened hard constraint merely by calling it a subquestion.

## Must preserve

- the confirmed main goal and its intended breadth;
- human-declared hard constraints;
- task-level completion and bounded-exhaustion obligations;
- distinction between the durable task and its evolving research agenda;
- exact base task and agenda versions;
- the rationale connecting each adopted direction to the main goal;
- requesting actor, decision, and publication provenance;
- the old task, agenda history, sessions, state, findings, evidence, and environment/schema identity;
- for a genuine rescope, exact parent lineage and an explicit semantic difference from the parent.

Preservation is semantic; no particular classes, hashes, database, or serialization are required.

## May transform

- prose into structured research questions, objectives, or relationship/rationale records;
- a broad question into multiple subordinate questions;
- agenda ordering, grouping, or status while retaining history and provenance;
- a potential rescope into a human-readable task proposal;
- a confirmed rescope proposal into a new task representation/version.

## Must exclude

- mechanical versioning merely because a subordinate question introduces a target, horizon, or
  analytical objective;
- silent editing of the authoritative task core;
- weakening a hard constraint by relabeling the change as exploration;
- treating an unsubstantiated “this helps the goal” assertion as sufficient authority;
- rebinding old sessions, state, findings, evidence, or exposures to a new task version;
- latest-version substitution for the exact base task/agenda version;
- treating a rescope proposal as an authoritative task;
- research findings or evidence fabricated to justify the classification;
- partial publication of agenda entries, task versions, lineage, or provenance.

## Authority boundary

- The instruction giver owns the confirmed main goal and hard constraints.
- The autonomous researcher may request and execute goal-preserving agenda evolution.
- The researcher may recommend a genuine rescope but may not authorize it.
- The harness validates exact base identities, hard-constraint preservation, confirmation binding,
  idempotency, and coherent publication.
- Exact human confirmation authorizes a genuine new task version through the mission.confirm-task authority rule.
- Existing sessions and evidence stores do not gain authority to rewrite their task association.

## Allowed state changes

For goal-preserving evolution, mission.evolve-direction may atomically append/update provenance-bearing agenda state
under the same task version.

For a potential rescope, it may record the request and explicit non-adoption outcome without
changing the authoritative task or active agenda.

For an exactly confirmed rescope, it may atomically publish a new task version, parent lineage,
semantic difference, and confirmation provenance. Subsequent research may initialize a new session
for that version through runtime.initialize-research.

## Forbidden state changes

- no mutation or deletion of the parent task/version;
- no silent change to the current task core;
- no task version solely for ordinary hypothesis/question/method evolution;
- no agenda adoption when goal preservation is not established;
- no automatic rebinding of a running session to the new task;
- no retroactive relabeling of historical state/evidence;
- no partial commit after validation/publication failure;
- no duplicate durable effect on exact retry.

## Failure semantics

- Unknown, stale, or mismatched base task/agenda identity is rejected explicitly; the system cannot
  substitute the latest version.
- A proposed direction that contradicts a hard constraint or replaces the main goal is not adopted
  as agenda evolution. It becomes a potential-rescope outcome.
- Ambiguous or insufficiently explained goal relationship preserves both task and agenda unchanged.
  The agent may supply a stronger rationale or reformulate without changing the task.
- A stale/mismatched human confirmation cannot publish a new task version.
- Exact duplicate requests/confirmations are idempotent; reuse with changed semantics conflicts.
- Publication failure rolls back the complete agenda or task-version transition. Retry uses the same
  request identity and cannot duplicate effects.

## Observable consequences

- Adding a next-quarter prediction question beneath a broad external-relationship discovery goal
  leaves the task identity/version unchanged while making the new question and its rationale
  recoverable in agenda history.
- Replacing that goal with an unrelated optimization objective cannot appear in the active agenda
  merely because the agent calls it a subquestion.
- After genuine rescope confirmation, both old and new tasks are readable; their semantic difference
  and lineage are explicit, and old sessions/evidence still reference the parent version.
- Removing transient model context does not erase why an agenda change was accepted or rejected.

## False-success implementations considered

1. Version the task whenever any nested target/horizon/objective differs.
2. Never version tasks; accept every model-authored direction as a subquestion.
3. Ask the model whether its own change is goal-preserving and accept an unsupported `yes`.
4. Create a new version correctly but rewrite old sessions/evidence to point at it.
5. Validate against whichever task version is latest rather than the submitted base version.
6. Publish the task before lineage or confirmation provenance is durably available.
7. Retry an accepted request by appending a duplicate agenda item/version.

## Falsifying tests

All deterministic tests below are Level A/B. They prove the boundary and runtime policy, not
autonomous model judgment. A later Level D eval may grade whether a real model recognizes nuanced
goal preservation, but it is not required to implement the deterministic authority boundary.

### mission.evolve-direction-T1 — subordinate prediction question preserves task identity

Start from the confirmed broad goal “find useful external-data relationships for Swedish healthcare
waiting times.” Propose a next-quarter prediction subquestion with a forecast horizon and an
explicit link to testing leading indicators. Assert that it is adopted into the agenda, the exact
task identity/version is unchanged, and rationale/provenance are recoverable.

This kills mechanical field-based versioning.

### mission.evolve-direction-T2 — ordinary research evolution does not rescope

Independently change hypotheses, candidate datasets, features, methods, and agenda priority while
keeping the main goal/constraints fixed. Assert no new task version and no loss of agenda history.

### mission.evolve-direction-T3 — quiet goal replacement is not agenda evolution

Against the same waiting-time task, propose “minimize staffing cost regardless of waiting-time
effects” as a subquestion. Assert it is not adopted, the task/agenda remain unchanged, and the
observable outcome identifies potential rescope rather than silently granting authority.

This kills the mutation that trusts the requester's classification or rationale label.

### mission.evolve-direction-T4 — hard constraint cannot be weakened as exploration

Propose a direction that violates an explicit geography, protected-resource, or other human-declared
hard constraint. Assert non-adoption and unchanged authoritative state even if the proposal says it
serves the goal.

### mission.evolve-direction-T5 — ambiguity preserves state

Submit a direction with no usable relationship to the main goal. Assert an explicit ambiguous/
potential-rescope result, no agenda entry, no new task, and legal reformulation/retry.

### mission.evolve-direction-T6 — confirmed rescope preserves lineage and history

Create/read back a genuine rescope proposal and confirm its exact identity/version/semantics. Assert
one new task version with explicit parent and semantic difference; the parent, its running session,
state, evidence, and environment references remain unchanged. A new session is required to research
under the new version.

### mission.evolve-direction-T7 — stale, conflicting, and duplicate requests

Submit against a stale base task/agenda version and assert rejection without latest-version
substitution. Retry an exact accepted request and assert one durable effect. Reuse its identity with
changed semantics and assert conflict.

### mission.evolve-direction-T8 — coherent publication failure

Inject failure between agenda/task publication and required provenance/lineage publication. Assert
that no partial agenda entry or task version becomes authoritative; retry publishes exactly once.

## Mutation-sensitivity check

**Mutation A:** Classify every newly introduced target, horizon, or objective as task rescope.

**Expected test failure:** mission.evolve-direction-T1 becomes red because the task version changes instead of the
prediction subquestion entering the existing agenda.

**Mutation B:** Trust the requester's `goal_preserving=true` declaration without comparing the
proposed meaning to the confirmed goal/constraints.

**Expected test failure:** mission.evolve-direction-T3 and mission.evolve-direction-T4 become red because goal replacement or constraint
weakening is incorrectly adopted.

## Composite dependencies

- **mission.confirm-task:** exact human confirmation for a genuine rescope proposal.
- **runtime.initialize-research:** a new session initializes under a newly confirmed task version.
- **context.build-packet/runtime.continue-from-observation/runtime.run-bounded-episode:** the active task and evolving agenda must later be visible to context and
  continued behavior.
- **formalization.create-candidate:** hypotheses/ideas may later become candidate features/models with ancestry.

These dependencies are named, not specified or locked here.

## User decisions

The architecture owner approved:

1. `ResearchTask` holds the stable main goal and hard constraints, not a frozen list of research
   questions.
2. The autonomous researcher may add, refine, abandon, or replace subordinate questions while the
   main goal remains intact.
3. Adding prediction, horizons, targets, or other analytical objectives can remain inside the same
   task when they are subordinate avenues serving a broad main goal.
4. Materiality is semantic and task-level, not triggered mechanically by a changed field type.
5. Genuine replacement of the main goal, weakening of hard constraints, or change to task-level
   completion meaning requires explicit rescope/versioning.
6. The agent may proceed autonomously when it can explicitly demonstrate the relationship to the
   goal; otherwise it records a potential rescope rather than silently adopting the change.
7. The parent task and all historical research remain immutable and attached to their exact task
   version.

## Implementation-readiness verdict

**Level 4 / pre-implementation READY.** The source/destination, semantics, authority, state effects,
failure behavior, observable consequences, eight discriminating tests, and two violating mutations
are specified. Level 5 requires executable tests passing through the production path.

The implementation-readiness audit was intentionally limited to mission.evolve-direction. It did not reopen the global
seam inventory or authorize implementation.

## Status

**LOCKED — readiness level 4 of 5.**

This contract and handoff do not authorize production code or executable-test implementation.
