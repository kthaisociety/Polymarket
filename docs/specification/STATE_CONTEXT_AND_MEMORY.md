# Research State, Context, Knowledge, and Memory

## 1. Fundamental distinction

\[
\boxed{R_t \neq C_t}
\]

`R_t` denotes the researcher's durable/system state at autonomous turn `t`; `C_t` denotes the
bounded context shown to the model. (`S_t` is reserved for the completed legal `TrainingSample` in
the scientific kernel.) The durable state is much larger than the current model context.

Context is a reconstructed working surface, not the system of record.

---

## 2. Researcher framing

Primary state question:

> If the researcher were frozen right now, what would be needed to resume their work intelligently?

`ResearcherState` is the resumable snapshot of the current intellectual and operational position. It is **not** a transcript and not a store for every intermediate number.

A fact belongs in durable research state only if knowing it would materially change what a competent researcher should do next.

---

## 3. Three-layer model

### 3.1 Trajectory

Complete action/observation history for:

- audit;
- replay/debugging;
- later learning/reflection;
- behavioral analysis.

Trajectory is not automatically placed in model context.

### 3.2 ResearchEpisode

`ResearchEpisode` is the canonical public and domain type for one investigation. The phrase **active research episode** describes the `ResearchEpisode` whose lifecycle status is currently `ACTIVE`; it is not a separate type.

Conceptually, a `ResearchEpisode` contains:

```text
episode_id
session_id
starting_state_version
objective / active question
current_plan
intermediate_observations
temporary_interpretations
active_artifact_refs
unresolved_questions
status
```

It may also carry completed and pending steps, branch changes, warnings, and an explicit `NOT_YET_RESOLVED`-style decision marker while required checks remain.

Lifecycle states are conceptually:

```text
ACTIVE
RESOLVED
ABANDONED
SUSPENDED
```

Exact field and enum mechanics are implementation-level. If persistence or performance later requires a buffer, that buffer remains implementation-private and must not become a second scientific concept.

### 3.3 ResearcherState

Committed durable understanding and current research position.

Conceptual categories:

1. **Mission/Goal** — research question, target, horizon, objective.
2. **Working Understanding** — active hypotheses, interpretations, important committed findings, uncertainties.
3. **Exploration Map** — important paths tried, outcomes, rejection/promotion reasons, evidence refs.
4. **Current Focus** — current subproblem, active entities, open questions, intended next investigation.
5. **Resource/Access Snapshot Ref** — reference to current environment/capabilities.
6. **Epistemic Position** — gates/stage, protected periods exposed, trial ancestry/status.

Do not store full tool history here.

---

## 4. Tool result is not belief update

Critical invariant:

\[
\boxed{\text{tool result}\rightarrow\text{ResearchEpisode}\not\Rightarrow\text{ResearcherState}}
\]

Example:

The agent plans `A → B → C`. A produces an interesting correlation. That result belongs in the active research episode while the investigation is unresolved. It must not automatically become a durable conclusion before B/C or a semantic resolution step.

This prevents premature conclusions and stale intermediate evidence from contaminating future research state.

---

## 5. Semantic commit boundaries

Durable `ResearcherState` changes when a meaningful research boundary occurs, such as:

- subproblem resolved;
- hypothesis rejected;
- hypothesis materially strengthened/promoted;
- investigation abandoned/suspended;
- material re-scope;
- gate crossing;
- checkpoint/termination where durable resume information is required.

At commit:

```text
ResearchEpisode
→ AI synthesis
→ StateUpdateProposal
→ structural validation
→ ResearcherState delta commit
```

The AI owns scientific interpretation. The harness validates:

- evidence refs exist;
- referenced evidence was legitimately available;
- protected/gate state cannot be forged;
- schema/integrity is valid;
- mission cannot silently change;
- history is appended/superseded rather than rewritten.

Prefer deltas/versioning/supersession over full state replacement.

---

## 6. ContextBuilder

Conceptually:

\[
C_t = CoreInstructions + ResearcherState + ResearchEpisode + RelevantEvidence + Permissions/Warnings
\]

The builder should provide the model what it needs for the next decision while preserving access to broader knowledge outside the immediate prompt.

Context budgeting should use semantic **priority classes** (mission/current state/active research episode/warnings before lower-priority background), not rigid fixed percentages. Exact token budgets/ranking thresholds are empirical implementation choices.

Key principle:

```text
Push structurally obvious context;
pull uncertain context on demand.
```

---

## 7. Broad access, selective working context

Do not impose human memory limits on a machine merely because the researcher analogy is useful.

Two questions:

1. Would a researcher need this in working memory for the next decision?
2. Are we omitting this because it is irrelevant, or only because a human could not process it?

If the second is true, preserve machine access through retrieval/synthesis rather than deleting knowledge.

Core principle:

```text
Keep reasoning surface narrow
while accessible knowledge surface extremely broad.
```

---

## 8. Retrieval hierarchy

Use multiple access modes:

### 8.1 Pinned working context

Always/usually available:

- mission;
- current committed understanding;
- active research episode;
- current warnings/permissions;
- active entities/refs;
- unresolved decision status.

### 8.2 Structural retrieval

Prefer explicit relationships when available:

- IDs;
- feature/model lineage;
- evidence refs;
- hypothesis links;
- current/superseded status;
- trial ancestry.

### 8.3 Machine-scale search/synthesis

Use semantic/search retrieval across broader knowledge when relevant:

- prior trajectories;
- ledger evidence;
- papers/books/docs;
- broad experiment archives;
- validated memory/skills.

### 8.4 Drill-down

The agent can request raw values, artifact contents, full diagnostics, code, or larger evidence slices when needed.

---

## 9. KnowledgeEnvironment

Logical sources include:

- structured research graph/state/evidence links;
- ResearchLedger;
- TrajectoryStore;
- ArtifactStore;
- DataCatalog/schema/environment metadata;
- papers/books/domain docs;
- validated cross-task Memory/Skills.

A retrieval `ContextPacket` should emphasize:

- current question;
- key facts/findings;
- contradictions/warnings;
- current/superseded status;
- source/evidence refs;
- drill-down refs.

---

## 10. Staleness and supersession

Context must not present old interpretations as current merely because they are semantically similar.

Use:

- version/current status;
- `superseded_by` or equivalent lineage;
- preference for current committed state;
- explicit contradiction/warning metadata.

A retrieval system that returns a stale belief without current-status context can silently corrupt reasoning.

---

## 11. Compaction

Do **not** use generic "summarize the conversation" as the primary compaction model.

When context pressure occurs:

```text
active research episode
→ structured EpisodeCheckpoint
→ discard transient prompt clutter
→ rebuild context from durable state + checkpoint + relevant evidence
```

Checkpoint contents should preserve:

- objective;
- current plan;
- completed checks;
- key observations;
- temporary interpretation;
- unresolved questions;
- artifact/evidence refs;
- warnings/permissions.

The full trajectory remains external.

Principle:

```text
compression changes accessibility latency,
not information existence
```

Completion test:

> If the entire LLM context disappeared, could the system reconstruct a scientifically equivalent working context from durable state, active research episode/checkpoint, permissions, and referenced evidence?

---

## 12. Research environment reference

The environment changes independently of scientific task/state.

`ResearcherState` should refer to environment/capability snapshots rather than duplicating entire catalogs/tool lists.

Historical state should remain reproducible even if a later environment adds datasets/tools.

---

## 13. Slow cross-task learning

Outer learning does not initially modify model weights.

Conceptually:

\[
L(\tau,R(\tau))\rightarrow(\Delta M,\Delta K,\Delta R)
\]

Where trajectories/outcomes are reflected on to produce candidate lessons.

Flow:

```text
Trajectory / Ledger
→ Reflection
→ CandidateLesson
→ LessonValidator
→ validated Memory / Skill
```

A candidate lesson should include provenance/evidence periods and cannot self-promote.

Memory = durable knowledge that should change future research behavior.

Skills = durable procedural knowledge about how to operate/research.

Raw experiment results are evidence, not automatically memory.

---

## 14. Logical storage boundaries

Preserve logical separation even if the first implementation uses simple files or one database:

- `ResearcherStateStore` — committed resumable state;
- `ResearchEpisodeStore` — unresolved active work/checkpoints;
- `TrajectoryStore` — complete actions/observations/events;
- `ArtifactStore` — large tables/plots/code/models;
- `ResearchLedger` — immutable experiment/backtest/evaluation/validation/provenance record;
- `DataCatalog/DataStore` — datasets/schema/vintage metadata;
- `KnowledgeEnvironment` — external/reference knowledge;
- validated `Memory/Skill` store.

Physical storage technology is intentionally deferred.
