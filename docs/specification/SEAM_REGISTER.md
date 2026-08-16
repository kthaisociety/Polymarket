# Global Architectural Seam Register

Status: **architecture inventory and coverage audit; not a seam-contract specification**.

This register inventories semantically meaningful mappings across the planned system. It was
derived from the authoritative architecture and subsystem specifications before comparison with
the Milestone 1 seam list. It does not prescribe package layout, classes, storage technology, or
tests, and it does not authorize implementation.

## Reading the register

- **Basis A**: the arrow is explicit in authoritative prose or a subordinate architecture diagram.
- **Basis B**: the mapping is strongly required by the architecture but is not explicitly drawn or
  assigned to a clear producer/consumer path.
- **LOCAL**: the contract is observable at one adjacent architectural boundary.
- **COMPOSITE**: the semantic proposition spans multiple components and may need an end-to-end
  contract/test without needing a new production object.
- **Depth HIGH**: a subtly wrong mapping can produce plausible scientific, epistemic, authority, or
  operational false success.
- **Depth MEDIUM**: important identity, lifecycle, or information can be damaged, but the failure is
  more directly visible or locally contained.
- **Depth LOW**: primarily plumbing/representation with limited semantic consequence.
- **Status LOCKED**: a locked decision, invariant, or approved contract defines the mapping.
- **Status DEFINED**: authoritative subsystem prose defines the responsibility, but no approved
  seam contract exists.
- **Status IMPLIED-GAP**: the architecture requires the mapping, but creator, consumer, or semantic
  transition is not explicit enough to implement without further seam work.
- **Status DEFERRED**: the architecture deliberately places the mapping outside the current kernel
  implementation plan.

Risk labels are: `INFORMATION`, `AUTHORITY`, `IDENTITY`, `STATE_MUTATION`, `PROVENANCE`,
`SCIENTIFIC_EVIDENCE`, `TEMPORAL_LEGALITY`, `LEARNING`, and `LOW_RISK`.

## Seam register

### Milestone 1 — task identity and autonomous runtime

| ID | From | To | Architectural purpose | Risk labels | Depth | Scope | Basis | Milestone / subsystem | Existing contract? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| mission.confirm-task | `UserMandate` + environment metadata + human confirmation | human-confirmed `ResearchTask` | Formalize and read back a faithful actionable mission; publish it only after exact human confirmation | INFORMATION, AUTHORITY, IDENTITY, PROVENANCE | HIGH | COMPOSITE | A | M1 / task creation | Contract 001; M1 S1; `../architecture/mission/transitions/confirm-task.md` | LOCKED |
| mission.evolve-direction | proposed research-direction change + exact current task/agenda versions | same-task agenda evolution, potential rescope, or human-confirmed new `ResearchTask` version | Let subordinate questions evolve autonomously while preserving the confirmed main goal, hard constraints, prior task, and explicit lineage | IDENTITY, STATE_MUTATION, PROVENANCE, AUTHORITY | HIGH | LOCAL | A/B | M1 / task versioning | Contract 001; `../architecture/mission/transitions/evolve-direction.md` | LOCKED |
| runtime.initialize-research | confirmed `ResearchTask` + exact `ResearchEnvironmentSnapshot` + authorized initialization request | coherent `ResearchSession` + `ResearcherState_0` + active `ResearchEpisode_0` | Create one independent epistemic-zero execution attempt atomically, idempotently, and without research | IDENTITY, STATE_MUTATION, AUTHORITY, PROVENANCE | HIGH | LOCAL | A/B | M1 / initialization | Contract 002; M1 S2; `../architecture/runtime/transitions/initialize-research.md` | LOCKED |
| context.build-packet | coherent authoritative task/session/state/episode/environment/permissions/evidence view | bounded provider-neutral `ContextPacket` | Reconstruct a permission-safe, status-preserving current decision surface from system-owned truth | INFORMATION, AUTHORITY, IDENTITY, PROVENANCE | HIGH | LOCAL | A/C | M1 / context | M1 S3; `../architecture/runtime/transitions/build-context-packet.md` | LOCKED |
| model.request-decision | decision-sufficient `ContextPacket` + small expressive action schemas + model/call configuration | untrusted provider-neutral `ModelResponse` | Obtain replaceable intelligence while preserving scientific context and open-ended authored intent without runtime authority | INFORMATION, AUTHORITY, IDENTITY | HIGH | LOCAL | A/C | M1 / provider boundary | M1 S4; `../architecture/runtime/transitions/request-model-decision.md` | LOCKED |
| model.normalize-response | complete provider-native response or failure + exact call correlation | normalized untrusted `ModelResponse` or explicit normalization failure | Preserve authored intent while preventing provider wire/auth/session types from defining runtime behavior | INFORMATION, IDENTITY | MEDIUM | LOCAL | A | M1 / provider adapter | M1 S4 (combined); `../architecture/runtime/transitions/normalize-model-response.md` | LOCKED |
| action.decode-intent | untrusted normalized `ModelResponse` + exact advertised schema/call correlation | typed `AgentAction`, explicit no-action, or structured failure | Faithfully type model intent and attach harness-owned request identity without narrowing science or granting authority | AUTHORITY, IDENTITY, INFORMATION | HIGH | LOCAL | A/B | M1 / action decoding | M1 S5; `../architecture/runtime/transitions/decode-action-intent.md` | LOCKED |
| action.authorize-request | typed `AgentAction` + current session/episode/policy | authorization/routing decision | Ensure only a current, permitted action reaches a capability or governed transition | AUTHORITY, IDENTITY | HIGH | LOCAL | A | M1 / routing | M1 S5–S6 (split) | LOCKED |
| data.inspect-authorized-view | authorized `InspectDatasetAction` + `AuthorizedDataView` | `CapabilityExecutionResult` | Execute bounded read-only inspection against the actual authorized view | AUTHORITY, INFORMATION, PROVENANCE | HIGH | LOCAL | A | M1 / inspect capability | M1 S6 | LOCKED |
| observation.assemble-authoritative-result | `CapabilityExecutionResult` + harness-observed authorization/access/execution facts | authoritative `StructuredObservation` | Produce bounded model-facing evidence with non-forgeable provenance and drill-down refs | PROVENANCE, INFORMATION, AUTHORITY | HIGH | LOCAL | A | M1 / observation assembly | M1 S7 | LOCKED |
| episode.record-observation | `StructuredObservation` | current `ResearchEpisode` working evidence | Persist substantive working evidence without directly changing durable belief | STATE_MUTATION, INFORMATION, PROVENANCE | HIGH | LOCAL | A | M1 / progression | M1 S8 | LOCKED |
| runtime.continue-from-observation | prior `StructuredObservation` | next model-visible `ContextPacket` | Close the causal feedback loop so observed meaning can change the next decision | INFORMATION, PROVENANCE | HIGH | COMPOSITE | A | M1 / feedback loop | M1 S8–S9; C1–C2 | LOCKED |
| commit.compose-request | `ProposeEpisodeTransitionAction` | `CommitRequest` with explicit episode proposal and optional state proposal | Represent semantic-boundary intent without granting mutation authority or inventing a state delta | AUTHORITY, IDENTITY, STATE_MUTATION | HIGH | LOCAL | A | M1 / semantic commit | M1 S10 | LOCKED |
| commit.validate-proposals | `CommitRequest` + authoritative evidence/current versions | independent episode/state validation decisions | Authorize lifecycle and durable understanding separately | AUTHORITY, SCIENTIFIC_EVIDENCE, IDENTITY | HIGH | LOCAL | A | M1 / validation | M1 S11 | LOCKED |
| commit.publish-boundary | validated proposals + current stores | atomic `CommitResult` + episode transition + optional new state version | Publish one all-or-nothing semantic boundary without half-state | STATE_MUTATION, AUTHORITY, IDENTITY, PROVENANCE | HIGH | LOCAL | A | M1 / commit | M1 S12 | LOCKED |
| commit.retry-idempotently | repeated idempotent `CommitRequest` | original result or `IDEMPOTENCY_CONFLICT` | Make uncertain retries safe while rejecting changed semantic payloads | IDENTITY, STATE_MUTATION, PROVENANCE | HIGH | LOCAL | A | M1 / idempotency | M1 S13 | LOCKED |
| runtime.return-repairable-failure | repairable action/provider/validation/commit failure | safe `StructuredObservation` in active episode | Return actionable failure to the intelligence loop without false success or corruption | INFORMATION, STATE_MUTATION, AUTHORITY | HIGH | COMPOSITE | A | M1 / recovery | M1 failure summary; repair companion | DEFINED |
| trajectory.append-event | consequential runtime operations and rejections | append-only `Trajectory` events | Preserve ordered audit/replay history without treating events as belief | PROVENANCE, IDENTITY, STATE_MUTATION | HIGH | LOCAL | A | M1 / trajectory | M1 S14 (trajectory half) | LOCKED |
| artifact.persist-output | large/raw/debug output | immutable artifact + `ArtifactRef` | Keep context bounded while preserving full drill-down evidence | INFORMATION, PROVENANCE | MEDIUM | LOCAL | A | M1 / artifacts | M1 S7/S14 | DEFINED |
| artifact.retrieve-authorized-content | permitted `ArtifactRef` / evidence ref | authorized drill-down content | Recover referenced semantics without bypassing permissions or confusing refs with evidence | AUTHORITY, INFORMATION, PROVENANCE | HIGH | LOCAL | B | M1 / retrieval-drill-down | No separate contract | IMPLIED-GAP |
| runtime.run-bounded-episode | initialized session | terminal `EpisodeRunResult` under limits | Compose the autonomous organism while enforcing causal feedback, authority, state separation, and bounded execution | INFORMATION, AUTHORITY, STATE_MUTATION, PROVENANCE | HIGH | COMPOSITE | A | M1 / whole episode | M1 whole-episode seam and acceptance | DEFINED |

### Milestone 2 — temporal scientific data boundary

| ID | From | To | Architectural purpose | Risk labels | Depth | Scope | Basis | Milestone / subsystem | Existing contract? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| data.register-observations | source bytes / cleaned rows + schema/release/vintage policy | registered observations in `DataCatalog` / `DataStore` | Bind physical values to stable dataset/field identity, `reference_time`, `available_at`, provenance, and caveats | IDENTITY, PROVENANCE, TEMPORAL_LEGALITY | HIGH | LOCAL | A | M2 / registration | No | DEFINED |
| data.resolve-field-reference | stable `FieldRef` | exact `DatasetSchema` field and physical values | Resolve scientific references without path/column substitution or semantic drift | IDENTITY, INFORMATION, PROVENANCE | HIGH | LOCAL | A | M2 / schema registry | No | DEFINED |
| data.build-information-set | registered observations + environment snapshot + capability policy + decision time | legal `InformationSet I_t` | Admit only information legally knowable and authorized at simulated time `t` | TEMPORAL_LEGALITY, AUTHORITY, INFORMATION, PROVENANCE | HIGH | LOCAL | A | M2 / information boundary | No | LOCKED |
| target.define-outcome | resolved task target/horizon semantics | `TargetDefinition` | Create an unambiguous target, alignment, horizon, prediction type, and maturity rule | IDENTITY, TEMPORAL_LEGALITY, SCIENTIFIC_EVIDENCE | HIGH | LOCAL | B | M2 / target semantics | No | IMPLIED-GAP |
| data.build-training-sample | `InformationSet I_t` + `TargetDefinition` + formal feature definitions | completed legal `TrainingSample S_t` | Align predictors and only mature, legally available labels without hidden fitting | TEMPORAL_LEGALITY, SCIENTIFIC_EVIDENCE, PROVENANCE | HIGH | LOCAL | A | M2 / sample construction | No | LOCKED |
| data.select-training-window | `TrainingSample S_t` + frozen `TrainingWindowPolicy` | selected `TrainingWindow W_t` | Select the declared legal fitting subset without learning or silent policy change | TEMPORAL_LEGALITY, IDENTITY, INFORMATION | HIGH | LOCAL | A | M2 / window policy | No | DEFINED |
| data.advance-independent-clocks | predictor releases/revisions and label-maturity events | independently rebuilt `I_t` and `S_t` | Prevent one generic “new data” event from conflating current predictors with completed labels | TEMPORAL_LEGALITY, SCIENTIFIC_EVIDENCE | HIGH | COMPOSITE | A | M2 / dual time boundaries | No | LOCKED |
| data.prove-temporal-substrate | registered data + target/window policies across decision times | legal temporal substrate for fitting/backtest | Prove end-to-end availability, label maturity, version provenance, and insufficiency behavior | TEMPORAL_LEGALITY, PROVENANCE, SCIENTIFIC_EVIDENCE | HIGH | COMPOSITE | A | M2 / temporal vertical slice | No | DEFINED |

### Milestone 3 — sandbox, tools, retrieval, and exploratory evidence

| ID | From | To | Architectural purpose | Risk labels | Depth | Scope | Basis | Milestone / subsystem | Existing contract? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| sandbox.authorize-execution | requested exploratory action + capability policy | sandbox execution authority / `AuthorizedDataView` | Convert requested computation into least-authority data and side-effect capabilities | AUTHORITY, INFORMATION, TEMPORAL_LEGALITY | HIGH | LOCAL | A | M3 / sandbox authorization | No | DEFINED |
| sandbox.execute-analysis | AI-authored code + authorized capabilities + resource/side-effect limits | sandbox execution result | Permit open-ended analysis without unrestricted host, secret, network, store, or protected-data authority | AUTHORITY, INFORMATION | HIGH | LOCAL | A | M3 / sandbox execution | No | LOCKED |
| sandbox.record-provenance | actual sandbox access/execution/artifacts | execution provenance record | Establish authoritative dataset, code, environment, random-state, resource, and artifact lineage | PROVENANCE, AUTHORITY, SCIENTIFIC_EVIDENCE | HIGH | LOCAL | A | M3 / provenance | No | LOCKED |
| observation.assemble-analysis-result | exploratory `StructuredReturn` / `AnalysisResult` + harness provenance | `StructuredObservation` | Preserve decision-relevant facts and warnings while retaining provisional epistemic status | INFORMATION, PROVENANCE, SCIENTIFIC_EVIDENCE | HIGH | LOCAL | A | M3 / exploratory observation | No | DEFINED |
| observation.translate-analysis-failure | exploratory exception/stdout/stderr | concise failure observation + raw diagnostic artifact | Enable repair without flooding context or hiding the real failure | INFORMATION, PROVENANCE | MEDIUM | LOCAL | A | M3 / error translation | No | DEFINED |
| artifact.persist-analysis-output | exploratory output | `ArtifactStore` identity and ref | Retain large tables, plots, code, and temporary models without promoting them | PROVENANCE, IDENTITY, SCIENTIFIC_EVIDENCE | MEDIUM | LOCAL | A | M3 / artifacts | No | DEFINED |
| knowledge.retrieve-evidence | knowledge-retrieval action + current permissions/epistemic position | authorized relevant evidence | Retrieve broad knowledge without surfacing protected, stale, or unrelated material | AUTHORITY, INFORMATION, PROVENANCE | HIGH | LOCAL | A | M3 / knowledge retrieval | No | DEFINED |
| knowledge.return-retrieved-evidence | authorized retrieved evidence | `StructuredObservation` / active episode | Return retrieved meaning, current/superseded status, and drill-down refs to the research loop | INFORMATION, PROVENANCE, STATE_MUTATION | HIGH | LOCAL | B | M3 / retrieval feedback | No | IMPLIED-GAP |
| research.repair-exploratory-action | ordinary exploratory operational failure | repaired action within same episode | Continue only when repair preserves scientific meaning and state remains uncorrupted | STATE_MUTATION, SCIENTIFIC_EVIDENCE | MEDIUM | COMPOSITE | A | M3 / recovery loop | No | DEFINED |
| research.continue-from-exploration | agent action through sandbox/tool/retrieval execution | next evidence-dependent agent action | Prove the authorized exploratory loop changes behavior through returned semantics, not hidden access | INFORMATION, AUTHORITY, PROVENANCE | HIGH | COMPOSITE | A | M3 / behavioral loop | No | DEFINED |

### Milestone 4 — formal feature, model, and predictive-system identity

| ID | From | To | Architectural purpose | Risk labels | Depth | Scope | Basis | Milestone / subsystem | Existing contract? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| formalization.create-candidate | hypothesis / exploratory idea + evidence | candidate feature/model | Turn provisional interpretation into an explicit candidate with ancestry rather than an implicit scientific object | SCIENTIFIC_EVIDENCE, IDENTITY, PROVENANCE | HIGH | LOCAL | B | M4 / candidate creation | No | IMPLIED-GAP |
| feature.define-identity | candidate feature + dependencies/temporal/missingness/fitted-state semantics | formal `FeatureDefinition` | Promote exploratory computation into a reproducible, time-legal scientific identity | IDENTITY, TEMPORAL_LEGALITY, PROVENANCE, SCIENTIFIC_EVIDENCE | HIGH | LOCAL | A | M4 / feature formalization | No | DEFINED |
| feature.compile-definition | `FeatureDefinition` | exact `FeatureExpression` / computation graph | Compile stable feature meaning without substituting fields/operators or losing temporal semantics | IDENTITY, INFORMATION, TEMPORAL_LEGALITY | HIGH | LOCAL | A | M4 / feature compilation | No | DEFINED |
| feature.materialize-definition | `FeatureDefinition` + legal data/information environment | provenance-bearing `FeatureSeries` | Materialize exact formal feature values in the named environment | TEMPORAL_LEGALITY, PROVENANCE, IDENTITY | HIGH | LOCAL | A | M4 / feature materialization | No | DEFINED |
| feature.assemble-set | selected formal `FeatureDefinition`s | versioned `FeatureSet` | Preserve the exact set of feature identities used by a candidate system | IDENTITY, SCIENTIFIC_EVIDENCE, PROVENANCE | HIGH | LOCAL | A | M4 / feature sets | No | DEFINED |
| feature.revise-from-diagnostics | feature diagnostics / `FeatureAnalysis` + agent interpretation | candidate revision, rejection, or formalization decision | Keep diagnostic evidence distinct while allowing it to influence research choices | INFORMATION, SCIENTIFIC_EVIDENCE | HIGH | COMPOSITE | B | M4 / feature loop | No | IMPLIED-GAP |
| model.define-recipe | candidate model/recipe | formal `ModelDefinition` | Separate reproducible model recipe and selection procedure from learned fitted state | IDENTITY, LEARNING, PROVENANCE | HIGH | LOCAL | A | M4 / model formalization | No | DEFINED |
| model.define-ensemble | selected model definitions / method | `EnsembleDefinition` | Freeze ensemble membership and method separately from learned weights | IDENTITY, LEARNING, SCIENTIFIC_EVIDENCE | HIGH | LOCAL | A | M4 / ensembles | No | DEFINED |
| system.assemble-definition | `TargetDefinition` + `FeatureSet` + model(s) + ensemble + training/evaluation protocol | candidate `PredictiveSystemDefinition` | Assemble every scientific choice that changes experimental meaning into one versioned identity | IDENTITY, PROVENANCE, SCIENTIFIC_EVIDENCE, LEARNING | HIGH | LOCAL | A | M4 / system definition | No | LOCKED |
| formalization.version-material-change | material change to a formal feature/model/system | new version/candidate with lineage | Prevent in-place mutation or disguised experiment changes | IDENTITY, STATE_MUTATION, PROVENANCE | HIGH | LOCAL | A | M4 / versioning | No | LOCKED |

### Milestone 5 — controlled fitting and development research

| ID | From | To | Architectural purpose | Risk labels | Depth | Scope | Basis | Milestone / subsystem | Existing contract? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| training.fit-system | predictive-system recipe + legal `TrainingWindow W_t` | `FitRecord` + immutable fitted system `F_t` | Fit all learned preprocessing, selection, models, and ensemble state only inside the legal window | LEARNING, TEMPORAL_LEGALITY, PROVENANCE | HIGH | LOCAL | A | M5 / `SystemTrainer` | No | LOCKED |
| prediction.generate-record | fitted system `F_t` + legal current feature values from `I_t` | immutable `PredictionRecord` | Produce prediction without learning and preserve system/time/information identity | LEARNING, TEMPORAL_LEGALITY, PROVENANCE, SCIENTIFIC_EVIDENCE | HIGH | LOCAL | A | M5 / prediction | No | LOCKED |
| outcome.record-mature-label | matured realized target under target semantics | immutable `OutcomeRecord` | Record outcome separately and only when legally complete/available | TEMPORAL_LEGALITY, SCIENTIFIC_EVIDENCE, PROVENANCE | HIGH | LOCAL | A | M5 / outcomes | No | DEFINED |
| development.evaluate-candidate | candidate feature/model/system + development data/protocol | development-validation evidence/diagnostics | Generate iterative evidence without confusing it with protected evidence | SCIENTIFIC_EVIDENCE, TEMPORAL_LEGALITY, PROVENANCE | HIGH | LOCAL | A | M5 / development validation | No | DEFINED |
| development.revise-candidate | development diagnostics | agent interpretation and revised candidate | Close the model/system development loop while recording trial ancestry and changes | INFORMATION, SCIENTIFIC_EVIDENCE, IDENTITY | HIGH | COMPOSITE | A | M5 / development loop | No | DEFINED |
| training.block-invalid-fallback | frozen fitting procedure failure | typed blocking failure or predeclared fallback | Prevent silent substitution of preprocessing/model/feature behavior | LEARNING, IDENTITY, SCIENTIFIC_EVIDENCE | HIGH | LOCAL | A | M5 / formal failure | No | LOCKED |
| ledger.record-trial-lineage | development trials and candidate lineage | `ResearchLedger` trial ancestry | Preserve selection history so surviving evidence is not presented as a first untouched trial | PROVENANCE, SCIENTIFIC_EVIDENCE, STATE_MUTATION | HIGH | LOCAL | A | M5 / trial history | No | LOCKED |

### Milestone 6 — freeze, protected backtest, evaluation, and promotion

| ID | From | To | Architectural purpose | Risk labels | Depth | Scope | Basis | Milestone / subsystem | Existing contract? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| freeze.assess-eligibility | development-eligible candidate + research-validation evidence | freeze decision/request | Establish that the candidate has met required pre-freeze research criteria | AUTHORITY, SCIENTIFIC_EVIDENCE, IDENTITY | HIGH | LOCAL | B | M6 / research-validation gate | No | IMPLIED-GAP |
| freeze.seal-system | accepted freeze request / candidate definition | immutable `FrozenPredictiveSystemDefinition` | Seal complete scientific identity; later material change creates a new candidate | AUTHORITY, IDENTITY, STATE_MUTATION, PROVENANCE | HIGH | LOCAL | A | M6 / freeze | No | LOCKED |
| backtest.request-evaluation | frozen system + evaluation world/specification + caller identity | `BacktestRequest` | Request protected evidence for an exact frozen identity and predeclared scenario | IDENTITY, AUTHORITY, SCIENTIFIC_EVIDENCE, PROVENANCE | HIGH | LOCAL | A | M6 / request | No | LOCKED |
| backtest.authorize-request | `BacktestRequest` + freeze/gate/exposure/trial/provenance/permission state | `BacktestPermit` or safe denial | Independently authorize or deny protected evaluation without content leakage | AUTHORITY, SCIENTIFIC_EVIDENCE, PROVENANCE | HIGH | LOCAL | A | M6 / governance | No | LOCKED |
| backtest.bind-protected-view | `BacktestPermit` + protected resource identity | exact authorized protected data view | Bind permit scope to the data actually exposed to execution | AUTHORITY, IDENTITY, PROVENANCE | HIGH | LOCAL | B | M6 / protected access | No | IMPLIED-GAP |
| exposure.record-disclosure | protected-data access/result disclosure | irreversible `Exposure` / epistemic-state and ledger update | Record that evidence can never again be claimed unseen for the affected lineage | STATE_MUTATION, SCIENTIFIC_EVIDENCE, PROVENANCE, AUTHORITY | HIGH | LOCAL | A | M6 / exposure | No | LOCKED |
| backtest.execute-scenario | permit + frozen system + protected evaluation scenario | historical sequence of fit/prediction/outcome/failure records | Execute the exact simulated procedure across explicit decision times | TEMPORAL_LEGALITY, LEARNING, SCIENTIFIC_EVIDENCE, PROVENANCE | HIGH | COMPOSITE | A | M6 / backtest engine | No | LOCKED |
| backtest.seal-run | completed execution records + frozen identity/scenario provenance | immutable `BacktestRun` | Seal what happened without omitting failures or permitting later rewrite | SCIENTIFIC_EVIDENCE, IDENTITY, PROVENANCE, STATE_MUTATION | HIGH | LOCAL | A | M6 / run assembly | No | LOCKED |
| evaluation.measure-run | immutable `BacktestRun` + `EvaluationSpec` | multidimensional `EvaluationReport` | Measure evidence without retraining, reselection, or collapsing task meaning into one scalar | SCIENTIFIC_EVIDENCE, PROVENANCE, LEARNING | HIGH | LOCAL | A | M6 / evaluation | No | LOCKED |
| finding.validate-report | `EvaluationReport` + predeclared promotion standard + independent authority | immutable `ValidationDecision` | Decide promote/reject without self-authorization or changing evidence | AUTHORITY, SCIENTIFIC_EVIDENCE, PROVENANCE | HIGH | LOCAL | A | M6 / validation | No | LOCKED |
| finding.publish-validated-claim | promoting `ValidationDecision` + canonical evidence/identity/caveats | immutable `ValidatedFinding` | Preserve the exact scientific substance of the promoted claim | SCIENTIFIC_EVIDENCE, IDENTITY, PROVENANCE, STATE_MUTATION | HIGH | LOCAL | A | M6 / finding | No | LOCKED |
| ledger.record-negative-result | denied/rejected/failed protected operation or validation | append-only `ResearchLedger` record + safe model-facing result where applicable | Retain negative history and exposure without leaking protected values or pretending success | PROVENANCE, SCIENTIFIC_EVIDENCE, AUTHORITY | HIGH | LOCAL | A | M6 / negative evidence | No | LOCKED |
| ledger.preserve-scientific-history | formal candidates, permits, runs, reports, decisions, exposure, promotion | append-only `ResearchLedger` history | Preserve reconstructible scientific identity, evidence, governance, and ancestry | PROVENANCE, SCIENTIFIC_EVIDENCE, STATE_MUTATION | HIGH | COMPOSITE | A | M6 / ledger | No | LOCKED |
| governance.retry-privileged-operation | retried privileged request after uncertain acknowledgement | one protected execution/exposure/promotion result | Prevent retries from duplicating irreversible epistemic effects | IDENTITY, AUTHORITY, STATE_MUTATION, PROVENANCE | HIGH | COMPOSITE | A | M6 / privileged idempotency | No | LOCKED |

### Milestone 7 — reporting, provider integration, and context pressure

| ID | From | To | Architectural purpose | Risk labels | Depth | Scope | Basis | Milestone / subsystem | Existing contract? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| report.render-finding | `ValidatedFinding` | human-facing report | Change wording/layout/framing without altering evidence, caveats, provenance, status, or conclusion | INFORMATION, SCIENTIFIC_EVIDENCE | HIGH | LOCAL | A | M7 / reporting | No | LOCKED |
| provider.authenticate-adapter | supported provider credentials/configuration | authenticated provider adapter/session | Establish operational access without leaking auth/session objects into scientific modules | AUTHORITY, IDENTITY | MEDIUM | LOCAL | A | M7 / real provider | No | DEFINED |
| context.checkpoint-episode | active `ResearchEpisode` under context pressure | `EpisodeCheckpoint` | Preserve plan, evidence, unresolved work, refs, warnings, and permissions in reconstructible form | INFORMATION, PROVENANCE, STATE_MUTATION | HIGH | LOCAL | A | M7 / compaction | No | LOCKED |
| context.rebuild-after-loss | durable state + checkpoint/episode + relevant evidence + permissions | equivalent rebuilt `ContextPacket` after transcript loss | Preserve scientific behavior despite provider-session/context loss | INFORMATION, AUTHORITY, PROVENANCE | HIGH | COMPOSITE | A | M7 / reconstruction | M1 C2 partially | LOCKED |

### Milestone 8 — behavioral evidence for the autonomous researcher

| ID | From | To | Architectural purpose | Risk labels | Depth | Scope | Basis | Milestone / subsystem | Existing contract? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| evaluation.grade-research-behavior | scenario state/actions/evidence/traps + scripted or real provider | graded behavioral outcome | Establish whether the composed agent respects research, authority, retrieval, recovery, and commit semantics | INFORMATION, AUTHORITY, SCIENTIFIC_EVIDENCE | HIGH | COMPOSITE | A | M8 / behavioral evals | Test strategy only | DEFINED |

### Milestone 9 — reflection, validated memory, and future behavior

| ID | From | To | Architectural purpose | Risk labels | Depth | Scope | Basis | Milestone / subsystem | Existing contract? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| learning.reflect-history | `Trajectory` + `ResearchLedger` outcomes | reflection output | Synthesize cross-task operational/scientific history without treating history itself as durable learning | INFORMATION, SCIENTIFIC_EVIDENCE, PROVENANCE | HIGH | LOCAL | A | M9 / reflection | No | DEFINED |
| learning.propose-lesson | reflection output | provenance-bearing `CandidateLesson` | Propose explicit durable knowledge/procedure with supporting periods and evidence | LEARNING, PROVENANCE, SCIENTIFIC_EVIDENCE | HIGH | LOCAL | A | M9 / lesson creation | No | DEFINED |
| learning.validate-lesson | `CandidateLesson` + independent evidence/authority | promote/reject lesson validation decision | Prevent a lesson or benefiting agent from self-promoting unsupported learning | AUTHORITY, LEARNING, SCIENTIFIC_EVIDENCE | HIGH | LOCAL | A | M9 / lesson validation | No | LOCKED |
| learning.promote-lesson | promoting lesson decision | validated `Memory` or `Skill` | Change epistemic status while preserving scope, provenance, and knowledge/procedure distinction | LEARNING, STATE_MUTATION, PROVENANCE | HIGH | LOCAL | A | M9 / learning promotion | No | LOCKED |
| ledger.record-rejected-lesson | rejected lesson decision | append-only `ResearchLedger` record | Preserve rejected learning and its evidence instead of erasing failed lessons | PROVENANCE, SCIENTIFIC_EVIDENCE | MEDIUM | LOCAL | A | M9 / learning history | No | DEFINED |
| learning.publish-to-knowledge | validated `Memory` / `Skill` | `KnowledgeEnvironment` | Make approved cross-task learning retrievable without granting it universal authority | LEARNING, INFORMATION, PROVENANCE | HIGH | LOCAL | A | M9 / knowledge publication | No | DEFINED |
| learning.influence-future-research | relevant permitted validated learning in `KnowledgeEnvironment` | future `ContextPacket` and changed research behavior | Prove validated learning—not merely its ID—can influence a later task while respecting scope/currentness | LEARNING, INFORMATION, AUTHORITY, PROVENANCE | HIGH | COMPOSITE | B | M9 / future-context learning | No | IMPLIED-GAP |

### Deliberately downstream of the research kernel

| ID | From | To | Architectural purpose | Risk labels | Depth | Scope | Basis | Milestone / subsystem | Existing contract? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| decision.apply-validated-finding | prediction or `ValidatedFinding` | domain `DecisionPolicy` and allocation/trading/insurance action | Keep predictive scientific evidence separate from downstream economic/business action authority | AUTHORITY, SCIENTIFIC_EVIDENCE, IDENTITY | HIGH | LOCAL | A | Future downstream module | No | DEFERRED |

## Counts

- Total seams: **83**
- Depth: **76 HIGH**, **7 MEDIUM**, **0 LOW**
- Scope: **67 LOCAL**, **16 COMPOSITE**

The absence of `LOW`-depth rows is intentional: low-risk helpers and representational plumbing do
not meet this register's definition of an architectural seam. The architecture does contain cheap
local implementation choices, but they are not semantic mappings and therefore are excluded.

## Architecture completeness and connectivity audit

### Explicit arrows (Basis A)

The end-to-end architecture explicitly connects task compilation, runtime initialization, context,
provider/action routing, authorized execution, observations, episode progression, semantic state
commit, the temporal data-to-evidence pipeline, formal scientific objects, development iteration,
freeze/protected evaluation, reporting, ledger/trajectory, and slow learning. These are represented
by the Basis A rows above.

### Strongly implied mappings not explicitly drawn (Basis B)

The following mappings are necessary for the named objects to participate in the architecture but
are not assigned a sufficiently explicit producer/consumer path:

1. **artifact.retrieve-authorized-content — `ArtifactRef` / evidence ref → authorized drill-down content.** Artifacts are promised
   as drillable and are logical knowledge sources, but the exact authority-preserving retrieval seam
   is not explicit.
2. **target.define-outcome — resolved task semantics → `TargetDefinition`.** The target object is required by sample
   construction and the frozen system, but its legitimate creator/resolution path is not shown.
3. **knowledge.return-retrieved-evidence — authorized retrieved evidence → observation/episode.** Knowledge retrieval is an action
   family and a context source, but the canonical return/progression path is only implied.
4. **formalization.create-candidate — hypothesis/exploratory evidence → candidate feature/model.** The feature funnel names
   both ends but not the mapping that establishes candidate identity and ancestry.
5. **feature.revise-from-diagnostics — `FeatureAnalysis` → candidate decision/revision.** Feature analysis is carefully
   distinguished from a definition, but no explicit consuming decision seam connects its evidence
   back to formalization or rejection.
6. **freeze.assess-eligibility — development eligibility → freeze decision/request.** A research-validation gate is
   named, but its inputs, independent authority, and output identity are not assigned to a canonical
   object or component.
7. **backtest.bind-protected-view — `BacktestPermit` → exact protected data view.** Governance can permit the engine, but
   permit-scoped protected-data resolution/access is not separately drawn.
8. **learning.influence-future-research — validated learning → future context/behavior.** Memory/skills enter the
   `KnowledgeEnvironment`, and that environment feeds context, but no semantic-use seam proves that
   validated lesson content changes a later decision within its authorized scope.

### Disconnected or one-sided concepts

- **`TargetDefinition` has important outgoing paths but no explicit legitimate creator.** This is
  captured by target.define-outcome.
- **`FeatureAnalysis` has an architectural distinction and examples, but no explicit outgoing
  production path.** This is captured by feature.revise-from-diagnostics.
- **`ModelSelection` is a canonical concept with legality constraints, but its producer, outputs,
  and relationship to `ModelDefinition`/development evidence are not drawn as an architectural
  path.** It remains a connectivity gap rather than an invented seam contract.
- **`EvaluationSpec` is required by `PredictiveSystemDefinition`, `BacktestRequest`, and
  `Evaluator`, but its authoritative creator/predeclaration path is not explicit.** No row invents
  that authority.
- **Permissions / epistemic position feed context and governance, but the complete authoritative
  update path across exposure and other gates is distributed rather than represented as one
  canonical mapping.** exposure.record-disclosure covers protected exposure only.
- **`ResearchLedger`, `TrajectoryStore`, and `ArtifactStore` are declared sources in the
  `KnowledgeEnvironment`, but their ingestion/indexing mappings are logical implications, not
  explicit semantic transitions.** knowledge.retrieve-evidence/learning.publish-to-knowledge/learning.influence-future-research avoid assuming a physical knowledge-index design.
- **`ResearchSession` is absent as an output box in the global integrated topology, although
  Contract 002 and M1 explicitly require it.** The approved initialization contract closes this
  diagram-level omission through runtime.initialize-research.
- **Candidate feature/model formalization is present as a funnel, but candidate creation and
  ancestry are underdefined.** formalization.create-candidate flags this without redesigning it.

No authoritative contradiction was found. These are connectivity/specification gaps to resolve
before their respective milestone is implementation-authorized.

## M1 coverage audit

The global inventory above was derived first; this comparison was performed afterward.

| Current M1 seam | Global seam coverage | Result | Rationale |
|---|---|---|---|
| S1 `UserMandate + environment → TaskCompilationResult` | mission.confirm-task proposal stage; mission.confirm-task also adds exact human confirmation; mission.evolve-direction separates agenda evolution from genuine later rescope | **expanded and split** | Global mission.confirm-task locks proposal-to-confirmed-task authority; mission.evolve-direction preserves autonomous question evolution while governing genuine task-core version transitions. |
| S2 `ResearchTask + environment → RuntimeInitialization` | runtime.initialize-research | **covered exactly** | The approved coherent initialization contract maps directly. |
| S3 authoritative runtime records → `ContextPacket` | context.build-packet | **covered exactly** | Same reconstruction and permission/staleness boundary. |
| S4 `ContextPacket → ModelProvider → ModelResponse` | model.request-decision + model.normalize-response | **needs splitting** | Provider invocation and provider-native normalization are separate replaceability boundaries. |
| S5 untrusted `ModelResponse → AgentAction` | action.decode-intent + action.authorize-request (identity/route validation part) | **needs splitting** | Decoding untrusted intent and authorizing/routing a current action have different authority effects. |
| S6 `AgentAction → CapabilityExecutionResult` | action.authorize-request + data.inspect-authorized-view | **needs splitting** | Authorization/routing must be distinguishable from capability computation. |
| S7 `CapabilityExecutionResult → StructuredObservation` | observation.assemble-authoritative-result; artifact.persist-output/artifact.retrieve-authorized-content for artifacts/drill-down | **needs splitting** | Provenance assembly, artifact persistence, and authorized drill-down are separable semantics. |
| S8 `StructuredObservation → ResearchEpisode` | episode.record-observation | **covered exactly** | Same working-evidence/state-separation arrow. |
| S9 episode evidence → next `ContextPacket` | runtime.continue-from-observation | **covered exactly** as composite | The global register names the stronger observation-to-next-context causal proposition. |
| S10 transition action → `CommitRequest` | commit.compose-request | **covered exactly** | Same explicit proposal-presence/intent boundary. |
| S11 `CommitRequest → validation decisions` | commit.validate-proposals | **covered exactly** | Same independent authority boundary. |
| S12 validated proposals → atomic `CommitResult` | commit.publish-boundary | **covered exactly** | Same all-or-nothing mutation boundary. |
| S13 retry → original result/conflict | commit.retry-idempotently | **covered exactly** | Same semantic idempotency mapping. |
| S14 consequential transitions → trajectory/artifacts | trajectory.append-event + artifact.persist-output + artifact.retrieve-authorized-content | **needs splitting** | Audit events, artifact persistence, and artifact retrieval carry different semantics and authority. |

### M1 arrows not fully represented by the current 14 local seams

- **Repair loop:** failure/rejection → structured repair observation → active episode → next context
  (global runtime.return-repairable-failure). The M1 failure summary and repair companion specify it, but it is not a numbered
  M1 seam.
- **Whole autonomous organism under limits:** initialized session → terminal result (global runtime.run-bounded-episode).
  M1 defines this public seam, but it is not one of S1–S14.
- **Authorized artifact/evidence drill-down:** ref → permitted content (global artifact.retrieve-authorized-content). M1 requires
  drillability, but S14 groups storage and audit and does not isolate retrieval authority.
- **Provider-native normalization:** provider-native output → normalized `ModelResponse` (global
  model.normalize-response) is folded into M1 S4.
- **Observation-to-next-model-visible-context composite:** current S8 + S9 and C1/C2 together cover
  it, but it should remain explicitly visible as the causal composite runtime.continue-from-observation.

### M1 result summary

- Covered exactly: **8** (`S2`, `S3`, `S8`, `S9`, `S10`, `S11`, `S12`, `S13`)
- Needs splitting: **6** (`S1`, `S4`, `S5`, `S6`, `S7`, `S14`)
- Needs merging: **0**
- Redundant: **0**
- Missing numbered composite/local concerns: **5** (repair loop, whole organism, authorized
  drill-down, provider-native normalization, explicit observation-to-next-context composite)

The existing M1 seams remain useful and internally coherent. This audit does not edit or invalidate
`MILESTONE_1_IMPLEMENTATION_READINESS.md`; it identifies how its milestone-local grouping maps onto
globally stable seam identities.
