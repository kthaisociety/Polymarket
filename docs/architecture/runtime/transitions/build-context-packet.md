# context.build-packet — Authoritative runtime records → ContextPacket

Status: **LOCKED — readiness level 4 of 5**

## Purpose

context.build-packet reconstructs the bounded working surface used for one model decision from system-owned truth.
It connects the stable research mission, committed understanding, active investigation, relevant
evidence, and current authority without treating the provider transcript as memory or the packet as
the system of record.

```text
ResearchTask                   stable authorized mission
ResearchSession                exact execution attempt
ResearcherState                durable committed position
active ResearchEpisode         temporary current investigation
Evidence/Artifacts             relevant supporting material
Environment/Permissions        current accessible world and authority
Warnings                       decision-critical constraints
        ↓ ContextBuilder
ContextPacket                  bounded view for one decision
```

If this mapping is wrong, the model may forget the goal, mistake temporary observations for accepted
belief, act on stale interpretations, bypass permissions, or choose its next action without the
meaning produced by prior research.

## Formal state/context model

`S_t` is reserved project-wide for the completed legal `TrainingSample` at simulated time `t`; it
must not also mean researcher state. For this seam:

```text
R_t       = committed ResearcherState at autonomous turn t
E_t       = active ResearchEpisode/checkpoint plus subsequent working evidence
Ω_t       = coherent authoritative session view
C_t       = ContextPacket for one model decision
q_t       = model's untrusted requested action/intent
```

Conceptually:

```text
Ω_t = (
  exact Task,
  exact Session,
  R_t,
  E_t,
  relevant permitted evidence/artifacts,
  exact Environment,
  current permissions/exposure,
  warnings
)

C_t = ContextBuilder(Ω_t, configured_bound, semantic_priority_policy)
q_t = ModelProvider(C_t, available_action_schemas, model_configuration)
```

After an authorized action returns an observation `o_t`:

```text
o_t → E_(t+1)
R_t remains unchanged unless a separate validated semantic commit occurs
C_(t+1) = ContextBuilder(Ω_(t+1), ...)
```

Thus context compression is a projection of the current authoritative view, not a mutation of that
view and not an alternative memory system. `C_t` must be decision-sufficient: if an authorized fact,
number, uncertainty, caveat, status, or contradiction can materially change the rational next
action, it must be substantively present or the packet must make the necessary authorized drill-down
the evident next action.

## Relevant locked invariants

- **I9 — Observation is not durable belief.** Episode observations must remain distinguishable from
  committed `ResearcherState`.
- **I10 — Mission cannot silently drift.** Context carries the exact authorized task/version and
  cannot rewrite its main goal or constraints.
- **I13 — Provenance follows scientific claims.** Decision-relevant claims retain evidence/provenance
  references and status.
- **I14 — Context cannot bypass permissions.** Relevance never overrides current visibility rules.
- **I15 — Compaction does not destroy evidence.** Compression may change immediate accessibility,
  not information existence or authorized drill-down.
- **I16 — Current state beats stale interpretation.** Superseded meaning cannot appear as current.
- **I20 — Model provider is replaceable.** Reconstruction cannot require a provider transcript,
  session, authentication object, or native response type.
- **I24 — Environment identity is explicit.** Context preserves the environment/schema versions
  governing the current and historical material it surfaces.

Authoritative sources: `INVARIANTS.md`, `STATE_CONTEXT_AND_MEMORY.md`, M1 runtime design/readiness,
and mission.confirm-task–runtime.initialize-research.

## Source A

context.build-packet reads an exact coherent current view for one session from authoritative runtime records:

- the exact confirmed `ResearchTask` version and usable mission semantics;
- the exact `ResearchSession` and runtime identity;
- the current committed `ResearcherState` version;
- the one active `ResearchEpisode`, or its authoritative structured checkpoint plus subsequent
  working material;
- permitted, relevant evidence summaries and provenance;
- artifact/evidence references and current authorized drill-down availability;
- the exact current `ResearchEnvironmentSnapshot`/schema references and capability metadata;
- current permissions, protected-resource state, warnings, and contradictions;
- current/superseded/temporary/rejected status and lineage required to interpret surfaced material.

The source is a coherent snapshot/view, not an arbitrary mixture of records loaded at different
versions. Complete trajectory and broad knowledge remain possible retrieval sources but are not
automatically packet contents.

## Destination B

`ContextPacket` is a provider-neutral, bounded, reconstructible working surface for one decision.
It is transient/derived, not durable scientific authority.

Its mandatory semantic core contains:

- main goal, breadth, hard constraints, and task-level completion obligation;
- exact task, session, state, episode, environment/schema, and packet-build identities/versions;
- current committed understanding and epistemic position;
- active episode objective/question, current plan/status, temporary interpretation, and unresolved
  questions/decision status;
- critical permissions, access limits, warnings, contradictions, and protected-exposure status;
- enough provenance/status information to distinguish committed, temporary, rejected, and
  superseded material.

Its bounded working-evidence layer may contain:

- recent and structurally relevant substantive observations;
- current evidence summaries and failed/rejected paths relevant to the decision;
- bounded previews with evidence/artifact references;
- explicit drill-down options currently available to the agent.

Exact serialization, prompt wording, tokenization, section names, and internal packet classes are
implementation choices.

## Mapping f

```text
exact session identity
    → load one coherent authoritative runtime view
    → validate task/state/episode/environment relationships and currentness
    → filter by current permission and epistemic authority
    → distinguish committed state from temporary episode material
    → select and deterministically order by semantic priority/relevance
    → compress lower-priority material into structured summaries/checkpoints + references
    → emit bounded provider-neutral ContextPacket
```

Priority is semantic rather than a rigid percentage allocation:

1. mandatory mission, identity, current state, active episode, critical authority/warnings;
2. decision-relevant current observations, contradictions, and working evidence;
3. background, older relevant history, and optional detail;
4. large/raw material represented through authorized references and drill-down.

The packet must stand alone as a reconstructible current decision surface. Delta information may be
emphasized, but a delta-only packet that requires provider memory is invalid.

## Authorized observation and evidence ingress channels

context.build-packet is intentionally not limited to dataset row counts or one fixed tool catalog. It reconstructs
decision-sufficient meaning from two epistemically different ingress routes.

### Exploratory working-evidence route

Agent-authored and standard exploratory tools return through the observation loop:

```text
AgentAction
    → authorized capability / ResearchSandbox
    → computation result + harness-observed execution/access provenance
    → StructuredObservation
    → active ResearchEpisode working evidence
    → context.build-packet ContextBuilder
    → next ContextPacket
```

This route includes:

- data discovery, schema inspection, profiling, scoping, missingness, descriptive statistics, and
  relationship analysis;
- AI-authored `run_analysis` code for novel diagnostics, transformations, regressions, plots,
  outlier checks, simulations, and temporary models;
- feature diagnostics and exploratory feature analysis;
- development diagnostics, model comparison, residual analysis, calibration, redundancy, stability,
  and robustness work;
- recoverable operational failures and authorized drill-down results.

The supporting seams include action.authorize-request–runtime.continue-from-observation for the initial loop; sandbox.authorize-execution–artifact.persist-analysis-output for sandboxed open-ended
analysis, provenance, observations, and artifacts; and artifact.retrieve-authorized-content/knowledge.return-retrieved-evidence/research.continue-from-exploration for drill-down, retrieval, and
the broader exploratory feedback loop. Some of those later seams remain to be individually locked.

### Formal scientific-evidence route

Not every formal result should be converted into an ordinary exploratory observation. Immutable
scientific records may remain in their authoritative evidence/ledger form:

```text
FeatureAnalysis / development-validation evidence / BacktestRun
/ EvaluationReport / ValidationDecision / ValidatedFinding
    → authoritative evidence or ResearchLedger record
    → permission- and status-aware relevance selection by context.build-packet
    → bounded substantive evidence + provenance + drill-down in ContextPacket
```

This route preserves the difference between development evidence, protected exposure, evaluation,
rejection, validation, and promoted findings. The model may interpret permitted formal evidence and
record that interpretation in its active episode, but context.build-packet cannot change the formal record's status
or present it as a different kind of evidence.

Feature/development decision feedback is elaborated by feature.revise-from-diagnostics and development.revise-candidate. Protected backtest/evaluation
records and their authority/status are produced by exposure.record-disclosure–ledger.preserve-scientific-history. context.build-packet consumes their permitted current
meaning; it does not replace those producer/governance seams.

For both routes, “bounded” means bounded raw volume, not scientifically impoverished content. When
the next decision depends on coefficients, uncertainty, sample size, units, periods/vintages, lags,
missingness, controls, protocol, robustness, caveats, failures, or exposure/status, those semantics
must be present in the packet or immediately available through an authorized drill-down action.

## Must preserve

- exact mission/task meaning and version;
- task/session/state/episode/environment identity and coherence;
- current committed understanding and its epistemic status;
- the active question, plan, unresolved decisions, and temporary interpretations;
- distinction between committed belief, temporary observation/interpretation, rejected evidence,
  and superseded meaning;
- current permissions, warnings, contradictions, gate/exposure position, and capability limits;
- bounded substantive meaning needed for the next decision, not merely opaque observation IDs;
- provenance and usable references for claims/evidence/artifacts;
- authorized drill-down possibility for omitted detail;
- deterministic priority/order for an identical authoritative snapshot and configuration;
- reconstructibility after provider context/transcript loss.

## May transform

- durable records into provider-neutral sections or messages;
- detailed evidence into bounded faithful summaries/previews plus references;
- structured episode checkpoints and subsequent observations into one current working view;
- representations, ordering within equal semantic priority, and bounded formats;
- redundant low-priority content into deduplicated or hierarchically summarized material.

Compression may reduce immediate detail but cannot alter authority, status, identity, provenance,
uncertainty, contradiction, or the availability of authorized underlying evidence.

## Must exclude

- provider transcript/session as required state or an unverified source of truth;
- unauthorized evidence, protected values, or permissions inferred from relevance;
- stale/superseded interpretation presented as current;
- temporary observation presented as committed belief;
- rejected evidence presented as accepted support;
- raw whole datasets, complete large artifacts, or complete trajectory by default;
- unrelated store contents and cross-session material;
- invented summaries, resolved uncertainty, hidden contradiction, or unsupported confidence;
- IDs/references without substantive meaning when the next decision requires that meaning;
- provider-native response/authentication objects;
- authority to mutate state, execute capabilities, authorize access, or call the model.

## Authority boundary

- Authoritative stores own task, state, episode, evidence, environment, and permission truth.
- The harness-owned `ContextBuilder` may read, validate, filter, prioritize, summarize faithfully,
  and expose current authorized drill-down references.
- The builder cannot promote evidence, change episode/state status, grant permission, record protected
  exposure, or decide scientific truth.
- The model consumes the packet and may request actions/retrieval; receiving information grants no
  mutation or execution authority.
- Relevance ranking and summarization never outrank permission, currentness, or epistemic status.

## Allowed state changes

context.build-packet is scientifically read-only. It may emit bounded operational observability such as packet-build
identity, source versions, selection decisions, omissions, sizes, and failure events, provided these
records do not mutate scientific state or become an alternate source of truth.

## Forbidden state changes

- no task, session, state, episode, evidence, environment, permission, gate, or exposure mutation;
- no finding/evidence promotion or supersession;
- no capability/tool execution or data access beyond authorized context reads;
- no protected content read merely to decide whether it should be excluded;
- no provider/model invocation;
- no destructive compaction or deletion of underlying evidence/trajectory/artifacts;
- no persistence of packet summaries as committed belief without a separate governed transition.

## Failure semantics

- Missing active episode, missing mandatory record, incoherent identities/versions, corrupt source,
  or inability to establish a coherent current snapshot fails explicitly before provider invocation.
- Unsafe or indeterminate permission filtering fails closed; it does not expose the questionable
  content or silently grant access.
- Missing optional evidence/detail may be represented explicitly as unavailable while preserving
  its reference/status, but cannot be silently rewritten as absence of evidence.
- If the configured bound cannot hold the mandatory semantic core, construction fails explicitly
  rather than dropping the mission, authority, warning, current-state, or active-episode meaning.
- Compression/summarization failure cannot fall back to stale packets, provider transcript, invented
  summaries, unauthorized content, or latest-version substitution.
- Exact rebuild from unchanged authoritative inputs/configuration is semantically equivalent; no
  persisted packet is required for correctness.

## Observable consequences

- Removing the provider transcript does not prevent reconstruction of a semantically equivalent
  next-decision packet.
- Two authoritative episodes differing only in one decision-relevant observation produce packets
  whose substantive content differs, enabling a packet-only deterministic consumer to choose
  different actions.
- Superseding a committed interpretation changes its packet status/current presentation without
  deleting historical evidence.
- Revoking permission removes protected content from subsequent packets while preserving permitted
  metadata/warnings where appropriate.
- Packet construction leaves all scientific and authority state unchanged.
- The active research question remains visibly connected to the larger confirmed task goal.

## False-success implementations considered

1. Append the provider conversation and call it reconstructed context.
2. Project only task/observation/artifact IDs without usable decision-relevant meaning.
3. Concatenate every store record until the token limit is reached.
4. Summarize committed state and temporary episode interpretation into one confident narrative.
5. Retrieve semantically similar stale beliefs without current/superseded status.
6. Rank protected evidence highly and expose it because it is relevant.
7. Drop mission, permissions, or warnings when the packet exceeds its bound.
8. Use only changes since the previous packet and assume provider memory.
9. Read or mutate protected/exposure state during “context preparation.”
10. Build from independently loaded latest records that never formed one coherent session snapshot.

## Falsifying tests

### context.build-packet-T1 — task meaning causally crosses the seam

Build packets from otherwise identical coherent views whose confirmed missions differ between
Swedish healthcare waiting times and Swedish electricity prices. A deterministic consumer receives
only each packet, cannot read stores/task inputs, and selects the corresponding domain action.
Assert exact task versions and mandatory meaning are present and the actions differ. **Level C.**

### context.build-packet-T2 — observation meaning, not only its ID, crosses

Create otherwise identical active episodes with a bounded observation stating 18 rows versus 2
rows. A packet-only deterministic consumer requests resolution for 18 and further inspection for 2.
Assert different packets/actions. Replace substantive payload with opaque IDs and the test must
fail. **Level C.**

This locally proves usable projection; runtime.continue-from-observation later proves the composite execution-feedback loop.

### context.build-packet-T3 — committed, temporary, rejected, and superseded remain distinct

Construct a view containing a current committed interpretation, a conflicting temporary episode
interpretation, rejected evidence, and a superseded prior belief. Assert the packet exposes their
roles/status without merging them or presenting stale/rejected material as current truth. Change the
current version and assert current presentation changes while history remains referencable. **Level A.**

### context.build-packet-T4 — permission filtering dominates relevance

Use identical relevant evidence under allowed and denied permissions. Assert substantive content is
present only when allowed; denied packets expose no protected values while retaining only permitted
metadata/warning/reference semantics. The consumer and builder have no bypass store handle. Assert
zero unauthorized/protected reads. **Level A/C.**

### context.build-packet-T5 — provider-transcript-independent reconstruction

Build a packet, discard all provider-native conversation/session context, and rebuild from durable
authoritative sources. Assert semantic equivalence of the mandatory core, working evidence,
authority/status, and references. Assert no provider-native object is required. **Level B.**

### context.build-packet-T6 — exact coherent versions and explicit structural failure

Assert a packet built for session S references its exact task, current state, active episode, and
environment versions. Introduce a mismatched state/episode, stale version substitution, missing
active episode, or torn source view and assert explicit pre-provider failure rather than mixed/latest
fallback. **Level A/B.**

### context.build-packet-T7 — bounded semantic priority and structured compression

Supply material exceeding the configured bound. Assert the mission/constraints, exact identities,
current committed position, active episode/question, critical permissions/warnings, and unresolved
decision status survive. Assert lower-priority detail becomes faithful structured summaries plus
authorized references, underlying evidence remains accessible, and the full trajectory/raw artifacts
are absent. **Level A.**

### context.build-packet-T8 — mandatory core too large fails explicitly

Configure a bound too small for the mandatory semantic core. Assert explicit failure before provider
invocation, not truncation or omission of mission, permissions, warnings, state, or episode meaning.
**Level A.**

### context.build-packet-T9 — context construction is scientifically read-only

Snapshot all authoritative records and attach spies to state/episode/evidence mutation, authorization,
capability execution, protected access, and provider invocation. Build a packet and assert all
scientific/authority state is unchanged and forbidden call/effect counts are zero. Only bounded
packet-build observability is permitted. **Level A/B.**

### context.build-packet-T10 — deterministic rebuild and session isolation

Rebuild twice from the same coherent view/configuration and assert semantic equivalence and stable
ordering. Add highly relevant records belonging to another session and assert they do not cross.
Change only a legitimate current source and assert the corresponding packet portion changes.
**Level A/C.**

### context.build-packet-T11 — heterogeneous analysis channels remain decision-sufficient

Exercise three permitted sources: an agent-authored data diagnostic returned as a
`StructuredObservation`, feature/development diagnostics with temporary or formal evidence status,
and a protected `EvaluationReport`/`ValidationDecision` with exposure and governance status. Build
the next packet through the production context path. Assert each result contributes its
decision-relevant numerical substance, uncertainty/sample/temporal/protocol semantics, caveats,
epistemic status, provenance, and permitted drill-down without being promoted or flattened into a
generic “looks promising” summary. Denied protected content remains absent. **Level A/C.**

## Mutation-sensitivity check

**Mutation A:** Replace every bounded observation payload with only `observation_id` and
`artifact_refs`.

**Expected test failure:** context.build-packet-T2 becomes red because the packet-only consumer cannot distinguish 18
rows from 2 and therefore cannot choose different actions.

**Mutation B:** Rank by semantic relevance before applying authorization/currentness filters.

**Expected test failure:** context.build-packet-T4 or context.build-packet-T3 becomes red because protected or stale information is
presented as usable current context.

**Mutation C:** When over budget, truncate from the beginning of the packet.

**Expected test failure:** context.build-packet-T7/T8 becomes red when mandatory mission/authority meaning is removed
instead of lower-priority material being compressed or construction failing.

## Composite dependencies

- **mission.confirm-task/mission.evolve-direction:** task mission, breadth, and evolving agenda retain usable meaning.
- **runtime.initialize-research:** coherent initialized records provide the zero-point sources.
- **model.request-decision:** the provider consumes this exact neutral packet without acquiring runtime authority.
- **runtime.continue-from-observation:** prior observation meaning must causally affect the next reconstructed packet/action.
- **artifact.retrieve-authorized-content:** authorized artifact/evidence-reference drill-down supplies omitted detail.
- **context.rebuild-after-loss:** later full reconstruction/compaction proves equivalent behavior after broader context loss.
- **learning.influence-future-research:** later validated cross-task learning may become permitted relevant context.

These dependencies are named, not specified or locked here.

## User decisions

The architecture owner approved:

1. Durable state, temporary active investigation, and model-visible working context are distinct
   because they carry different epistemic authority.
2. Information earns durable-state status only when omission would materially change future
   decisions, cause significant repeated work, or lose authoritative scientific/governance truth.
3. After provider transcript loss, another capable model should be able to resume intelligently
   without scientifically meaningful amnesia.
4. Tentative observations remain in the active episode until a validated semantic commit; they do
   not automatically become durable belief.
5. The packet is a selective decision surface while broader authorized knowledge remains retrievable.
6. context.build-packet uses deterministic semantic priority, structured checkpoint/summary forms, bounded evidence
   previews, and authorized drill-down references.
7. Delta information may be emphasized but never becomes a delta-only dependency on model memory.
8. LLM-authored compression and general semantic-search infrastructure are deferred; they are not
   required for the initial context.build-packet implementation.
9. The mandatory core is never silently dropped; an impossibly small configured bound fails.
10. `C_t` is a decision-sufficient projection of coherent authoritative session view `Ω_t`; `R_t`
    denotes researcher state because `S_t` remains reserved for the scientific `TrainingSample`.

## Implementation/test handoff

Implement context.build-packet-T1 through context.build-packet-T11 as ordered red tests before production code for this seam. The
most important causal proof is T2: substantive episode meaning must change a packet-only consumer's
decision. The most important authority proof is T4; the most important compression proof is T7/T8.

Forbidden shortcuts include transcript dependence, opaque references without usable meaning,
latest-version mixing, unauthorized or stale retrieval, epistemic-status flattening, delta-only
context, destructive compaction, truncating mandatory core, provider calls, and scientific mutation.

Package layout, store technology, concrete packet type, serializer, exact text, token estimator,
ranking algorithm within the locked priority rules, and observability mechanism remain free.

This handoff is specification only and does not authorize production code or executable tests.

## Status

**LOCKED — readiness level 4 of 5.**

Level 5 requires executable discriminating tests passing through the real production path.
