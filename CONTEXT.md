# Time-Series Research Agent Context

This glossary defines the canonical project language. It is a vocabulary map, not an architecture
specification. The linked specification remains authoritative for each term's full semantics.


## UserMandate

**Meaning:** The human's original natural-language research intent and explicit constraints.

**Not the same as:** A compiled `ResearchTask` or a finding.

**Key invariant:** Its original meaning remains recoverable and cannot be silently completed or
changed by the compiler.

**See:** `docs/specification/contracts/001-user-mandate-to-research-task.md`

## ResearchTaskProposal

**Meaning:** A versioned, human-readable formalization of a `UserMandate` awaiting confirmation by
the instruction giver.

**Not the same as:** An authoritative `ResearchTask` or permission to begin research.

**Key invariant:** Confirmation applies only to the exact proposal semantics/version reviewed;
editing the proposal requires a new readback and confirmation.

**See:** `docs/architecture/mission/transitions/confirm-task.md`

## ResearchTask

**Meaning:** The human-confirmed, structured, versioned mission for the scientific problem to
investigate.

**Not the same as:** A `ResearchSession`, hypothesis, or execution attempt.

**Key invariant:** It can be created only from the exact confirmed `ResearchTaskProposal`. The
agent may evolve subordinate research questions autonomously; only a semantic change to the
task-level main goal, hard constraints, or completion meaning creates a new task version.

**See:** `docs/specification/contracts/001-user-mandate-to-research-task.md`

## ResearchSession

**Meaning:** One concrete autonomous execution attempt for a `ResearchTask` under a particular
environment, harness, and model configuration.

**Not the same as:** The scientific problem itself.

**Key invariant:** Independent sessions can investigate the same task without changing task identity.

**See:** `docs/specification/contracts/002-runtime-initialization.md`

## ResearchQuestion

**Meaning:** One exact subordinate scientific question investigated autonomously inside a confirmed
`ResearchTask`.

**Not the same as:** The task-level mandate, an authored candidate, or a finding.

**Key invariant:** Its exact environment, data identity, evidence ancestry, and terminal status
remain reconstructible; changing a subordinate question does not silently change the confirmed
task.

**See:** `docs/specification/AUTONOMOUS_INVESTIGATION_CONTRACT.md`

## QuestionMemoryRecord

**Meaning:** The terminal, authority-issued record that an exact research question reached either a
protected validated finding or a protected rejection.

**Not the same as:** Development evidence, a governance denial, generated Markdown, or a
cross-task `CandidateLesson`.

**Key invariant:** Only independently issued protected terminal evidence may create it; exact replay
converges, prior rejection remains visible, and presentation files cannot alter its status.

**See:** `docs/architecture/autonomous-investigation/transitions/record-question-resolution.md`

## QuestionReopenDeclaration

**Meaning:** An explicit link from a new-catalog or materially changed-hypothesis investigation to
one prior `QuestionMemoryRecord`.

**Not the same as:** Deleting, superseding, or retrying the prior terminal question.

**Key invariant:** The prior memory remains terminal and enters the new context; fabricated,
cross-environment, or unchanged reopen claims fail closed.

**See:** `docs/architecture/autonomous-investigation/transitions/reconstruct-question-memory.md`

## ResearchEnvironment

**Meaning:** A versioned snapshot or reference describing available data, capabilities, permissions,
compute, and protected-resource metadata for a session.

**Not the same as:** `ResearcherState` or the data itself.

**Key invariant:** Historical state refers to the environment it used rather than adopting later
environment changes retroactively.

**See:** `docs/specification/contracts/002-runtime-initialization.md`

## Autonomous Research Runtime

**Meaning:** The harness-owned outer loop that reconstructs context, calls a model, routes authorized
actions, records observations, and advances research state.

**Not the same as:** A `ModelProvider` or provider-specific agent shell.

**Key invariant:** Replacing the model provider must not change the scientific architecture.

**See:** `docs/specification/MODEL_PROVIDER.md`

## ModelProvider

**Meaning:** A replaceable interface that turns a `ContextPacket` and available action schemas into
a normalized model response.

**Not the same as:** The autonomous runtime or scientific authority.

**Key invariant:** Provider-specific authentication and response formats do not leak into scientific
modules.

**See:** `docs/specification/MODEL_PROVIDER.md`


## ResearcherState

**Meaning:** The committed, resumable snapshot of the researcher's current intellectual,
operational, and epistemic position.

**Not the same as:** A transcript, active research episode, trajectory, ledger, or artifact collection.

**Key invariant:** Raw tool output cannot mutate it directly. Changes occur at semantic commit
boundaries through a validated proposal.

**See:** `docs/specification/STATE_CONTEXT_AND_MEMORY.md`

## ResearchEpisode

**Meaning:** One investigation containing its objective, plan, intermediate observations, temporary interpretations, active artifact references, unresolved questions, and lifecycle status.

**Not the same as:** Durable `ResearcherState` or complete `Trajectory`. "Active research episode" means the `ResearchEpisode` whose status is `ACTIVE`, not another type.

**Key invariant:** A tool result may update the `ResearchEpisode`, but cannot automatically update `ResearcherState`.

_Avoid:_ `ActiveEpisode`, `WorkingEpisode`, and `EpisodeBuffer` as public or domain type names.

**See:** `docs/specification/STATE_CONTEXT_AND_MEMORY.md`

## EpisodeCheckpoint

**Meaning:** A structured, reconstructible snapshot of unresolved episode work created under context
pressure or at a checkpoint.

**Not the same as:** A generic transcript summary or durable belief update.

**Key invariant:** Compaction changes retrieval latency, not whether underlying information exists.

**See:** `docs/specification/STATE_CONTEXT_AND_MEMORY.md`

## Trajectory

**Meaning:** The complete action, observation, model, tool, and runtime-event history used for audit,
replay, debugging, reflection, and behavioral analysis.

**Not the same as:** Current model context or the `ResearchLedger`.

**Key invariant:** Trajectory entries are not automatically inserted into context or promoted to
belief.

**See:** `docs/specification/STATE_CONTEXT_AND_MEMORY.md`

## ResearchLedger

**Meaning:** The canonical append-only history of consequential scientific identity, evidence,
governance, evaluation, validation, exposure, and promotion events.

**Not the same as:** The complete runtime trajectory or cross-task memory.

**Key invariant:** Rejected evidence and prior exposure remain recorded and cannot be rewritten away.

**See:** `docs/specification/BACKTEST_AND_EVALUATION.md`

## ArtifactStore

**Meaning:** Durable storage for large outputs such as tables, plots, code, fitted artifacts,
tracebacks, and detailed diagnostics referenced by other records.

**Not the same as:** Model context, committed state, or the scientific ledger.

**Key invariant:** Summarization may change accessibility, but referenced raw evidence remains
drillable.

**See:** `docs/specification/STATE_CONTEXT_AND_MEMORY.md`

## KnowledgeEnvironment

**Meaning:** The broad machine-accessible surface spanning structured state, ledger evidence,
trajectory, artifacts, data metadata, reference documents, and validated memory or skills.

**Not the same as:** The small working context sent to the model.

**Key invariant:** Broad access is preserved while each `ContextPacket` remains selective.

**See:** `docs/specification/STATE_CONTEXT_AND_MEMORY.md`

## ContextBuilder

**Meaning:** The harness component that reconstructs the next working context from committed state,
the active research episode, relevant evidence, environment, permissions, and warnings.

**Not the same as:** A transcript appender or retrieval store.

**Key invariant:** It prefers current, structurally relevant knowledge and preserves supersession and
authority metadata.

**See:** `docs/specification/STATE_CONTEXT_AND_MEMORY.md`

## ContextPacket

**Meaning:** The bounded, reconstructible working surface presented to the model for one decision.

**Not the same as:** Durable system state or all machine-accessible knowledge.

**Key invariant:** Losing provider context must not lose scientific state.

**See:** `docs/specification/STATE_CONTEXT_AND_MEMORY.md`

## StateUpdateProposal

**Meaning:** A model-authored proposal to convert resolved episode understanding into a durable state
delta.

**Not the same as:** A direct state mutation or raw observation.

**Key invariant:** The harness validates references, provenance, authority, mission identity, and
idempotency before commit.

**See:** `docs/specification/STATE_CONTEXT_AND_MEMORY.md`

## EpisodeTransitionProposal

**Meaning:** A request to move one `ResearchEpisode` from `ACTIVE` to a terminal lifecycle status.

**Not the same as:** A `StateUpdateProposal` or a persisted transition.

**Key invariant:** Changing episode status never implies a durable state mutation.

**See:** `docs/specification/MILESTONE_1_RUNTIME_DESIGN.md`

## CommitRequest

**Meaning:** One semantic-boundary request containing an episode-transition proposal, an optional state-update proposal, and idempotency identity.

**Not the same as:** Either proposal alone or an already committed result.

**Key invariant:** Required proposals validate separately and persist atomically.

**See:** `docs/specification/MILESTONE_1_RUNTIME_DESIGN.md`

## CandidateLesson

**Meaning:** A provenance-bearing hypothesis about durable knowledge or procedure learned through
reflection across research history.

**Not the same as:** Validated `Memory`, a `Skill`, or a raw experiment result.

**Key invariant:** A candidate lesson cannot promote itself.

**See:** `docs/specification/STATE_CONTEXT_AND_MEMORY.md`

## Memory

**Meaning:** Validated durable knowledge that should change future research behavior.

**Not the same as:** Raw evidence, trajectory, or an unvalidated lesson.

**Key invariant:** Promotion requires independent validation and provenance.

**See:** `docs/specification/STATE_CONTEXT_AND_MEMORY.md`

## Skill

**Meaning:** Validated durable procedural knowledge about how to conduct research or operate the
system.

**Not the same as:** A one-off action sequence or provider capability.

**Key invariant:** Procedural learning follows the same governed promotion path as memory.

**See:** `docs/specification/STATE_CONTEXT_AND_MEMORY.md`


## ResearchSandbox

**Meaning:** The constrained execution boundary in which model-authored exploratory computation can
use authorized data and controlled resources.

**Not the same as:** The model, unrestricted host execution, or the formal scientific kernel.

**Key invariant:** Computational creativity is broad while information access, side effects,
resources, and provenance remain constrained.

**See:** `docs/specification/AUTHORITY_SANDBOX_AND_TOOLS.md`

## AuthorizedDataView

**Meaning:** A capability-scoped view exposing only data legally and operationally permitted for an
action.

**Not the same as:** The complete data store or a protected-evidence permit.

**Key invariant:** Data legality is enforced by the harness rather than trusted to model behavior.

**See:** `docs/specification/AUTHORITY_SANDBOX_AND_TOOLS.md`

## CapabilityPolicy

**Meaning:** The policy that determines which data, tools, resources, and side effects an action may
use.

**Not the same as:** Scientific interpretation or model instructions.

**Key invariant:** The model may request authority but cannot grant it to itself.

**See:** `docs/specification/AUTHORITY_SANDBOX_AND_TOOLS.md`

## ProvenanceRecorder

**Meaning:** The responsibility that records data, code, environment, random-state, action, and
artifact lineage needed for audit and reproduction.

**Not the same as:** The complete `ResearchLedger` or `Trajectory`.

**Key invariant:** Scientifically consequential outputs retain enough lineage to reconstruct their
origin.

**See:** `docs/specification/AUTHORITY_SANDBOX_AND_TOOLS.md`

## StructuredObservation

**Meaning:** A concise, typed account of an action outcome containing decision-relevant payload,
context, warnings, provenance, recoverability, and drill-down references.

**Not the same as:** A `RuntimeEvent`, raw stdout, or a durable belief.

**Key invariant:** It may update the active research episode but cannot directly update `ResearcherState`.

**See:** `docs/specification/AUTHORITY_SANDBOX_AND_TOOLS.md`

## RuntimeEvent

**Meaning:** An audit and observability record of runtime activity such as model calls, action
requests, retries, or failures.

**Not the same as:** A model-facing scientific observation.

**Key invariant:** Runtime events enter trajectory and do not automatically enter model context.

**See:** `docs/specification/MODEL_PROVIDER.md`

## StructuredReturn / AnalysisResult

**Meaning:** The conceptual result channel by which sandboxed analysis returns a structured payload
and references to larger artifacts.

**Not the same as:** Unstructured console output or automatic formal evidence.

**Key invariant:** Exploratory results remain provisional until explicitly formalized or committed.

**See:** `docs/specification/AUTHORITY_SANDBOX_AND_TOOLS.md`

## CapabilityExecutionResult

**Meaning:** The non-authoritative computation and result facts returned by a capability before harness provenance assembly.

**Not the same as:** An authoritative `StructuredObservation`.

**Key invariant:** The harness verifies actual access and execution provenance before presenting the result as an observation.

**See:** `docs/specification/MILESTONE_1_RUNTIME_DESIGN.md`

## reference_time

**Meaning:** The period or instant that an observed value describes.

**Not the same as:** `available_at`.

**Key invariant:** A past reference period does not make a later-published value usable earlier.

**See:** `docs/specification/SCIENTIFIC_KERNEL.md`

## available_at

**Meaning:** The earliest time at which an observed value may legally enter an information set.

**Not the same as:** The time the value describes.

**Key invariant:** A prediction at time `t` may use the value only when `available_at <= t`.

**See:** `docs/specification/SCIENTIFIC_KERNEL.md`

## InformationSet I_t

**Meaning:** All information legally knowable at simulated decision time `t`.

**Not the same as:** All rows whose reference timestamp is at or before `t`, or the mature training
sample set.

**Key invariant:** Publication delay, vintage, feature maturity, and temporal legality are explicit.

**See:** `docs/specification/SCIENTIFIC_KERNEL.md`

## TrainingSample S_t

**Meaning:** The completed supervised examples whose predictors and matured outcomes are legally
available at time `t`.

**Not the same as:** `InformationSet I_t`.

**Key invariant:** Predictor release and label maturity advance independently.

**See:** `docs/specification/SCIENTIFIC_KERNEL.md`

## TemporalOffset

**Meaning:** The immutable scientific identity of either an absolute elapsed duration or a
civil-calendar month/quarter offset, including the exact anchor, month-end, timezone, and DST/fold
policy needed to apply it.

**Not the same as:** A bare number of months, an approximate number of days, or an observation
timestamp.

**Key invariant:** Calendar and elapsed time never silently convert into one another; changing any
unit or calendar policy changes identity.

**See:** `docs/specification/DECISIONS.md`, Time semantics

## TargetDefinition

**Meaning:** The immutable scientific identity of how a future observation interval becomes the
outcome associated with a prediction made at a decision time, including horizon, path/endpoint
meaning, completion, and legal availability.

**Not the same as:** A task-level research goal, a physical target column, a partially observed
outcome, or an `OutcomeRecord` from one concrete prediction.

**Key invariant:** A target may use future observations to define an outcome, but that label cannot
enter `TrainingSample S_t` until its declared outcome is complete and legally available; any
meaning-changing target revision creates a new definition/version.

**See:** `docs/specification/SCIENTIFIC_KERNEL.md`

## FeatureDefinition

**Meaning:** The stable scientific identity of a reproducible, time-legal mapping from available
data to a feature value.

**Not the same as:** A materialized `FeatureSeries` or diagnostic `FeatureAnalysis`.

**Key invariant:** Fitted feature operations learn only inside the legal training boundary.

**See:** `docs/specification/SCIENTIFIC_KERNEL.md`

## FeatureSeries

**Meaning:** The materialized output of a `FeatureDefinition` in a concrete data and information
environment.

**Not the same as:** The feature's scientific definition.

**Key invariant:** Its provenance identifies the definition and environment that produced it.

**See:** `docs/specification/SCIENTIFIC_KERNEL.md`

## FeatureAnalysis

**Meaning:** Evidence or diagnostics about features, such as importance, stability, correlation, or
redundancy analysis.

**Not the same as:** A predictive feature by default.

**Key invariant:** Exploratory analysis becomes part of a predictive recipe only through explicit
formalization.

**See:** `docs/specification/SCIENTIFIC_KERNEL.md`

## ModelDefinition

**Meaning:** The reproducible recipe and choices that define a model before fitting.

**Not the same as:** A `FittedModel` or `ModelSelection` procedure.

**Key invariant:** A model recipe cannot contain learned state from future or protected data.

**See:** `docs/specification/SCIENTIFIC_KERNEL.md`

## FittedModel

**Meaning:** A trained model instance produced from a model definition and a legal training window.

**Not the same as:** The reusable model recipe.

**Key invariant:** Its learned state carries training-window and provenance identity.

**See:** `docs/specification/SCIENTIFIC_KERNEL.md`

## ModelSelection

**Meaning:** A research or training procedure for choosing among model candidates.

**Not the same as:** One model definition or fitted instance.

**Key invariant:** Selection changes evidence meaning and must remain inside declared temporal and
trial boundaries.

**See:** `docs/specification/SCIENTIFIC_KERNEL.md`

## PredictiveSystemDefinition

**Meaning:** The complete scientific recipe joining target, feature set, model definitions,
ensemble, training protocol, and required evaluation predeclarations.

**Not the same as:** A fitted system or exploratory candidate code.

**Key invariant:** Every choice that changes experimental meaning belongs to its identity.

**See:** `docs/specification/SCIENTIFIC_KERNEL.md`

## FrozenPredictiveSystemDefinition

**Meaning:** An immutable version of a predictive-system recipe admitted to protected evaluation.

**Not the same as:** A mutable development candidate.

**Key invariant:** Any substantive change after freeze creates a new candidate version.

**See:** `docs/specification/SCIENTIFIC_KERNEL.md`


## BacktestRequest

**Meaning:** A request to evaluate a frozen predictive system against a specified protected
historical world.

**Not the same as:** Permission to access or run the protected backtest.

**Key invariant:** The requesting actor cannot self-authorize the request.

**See:** `docs/specification/BACKTEST_AND_EVALUATION.md`

## ClaimDefinition

**Meaning:** The exact bounded scientific statement, scope limitations, and required caveats that a
protected evaluation is intended to test, fixed before protected evidence is disclosed.

**Not the same as:** A `ValidatedFinding`, report wording, or an exploratory interpretation.

**Key invariant:** Changing the claim's substance, scope, or required caveats changes identity and
cannot be done post hoc under the original protected request.

**See:** `docs/architecture/protected-evaluation/IMPLEMENTATION.md`

## PromotionStandard

**Meaning:** The exact predeclared metric, robustness, scenario, threshold, and authority-policy
rules an independent `Validator` applies to an `EvaluationReport`.

**Not the same as:** An `EvaluationSpec`, model-selection objective, or downstream business decision.

**Key invariant:** A threshold or authority-policy change creates a new standard identity and cannot
rewrite the standard bound to already disclosed protected evidence.

**See:** `docs/architecture/protected-evaluation/IMPLEMENTATION.md`

## BacktestGovernance

**Meaning:** The privileged authority that permits or denies protected evaluation after checking
freeze, exposure, predeclaration, provenance, trial ancestry, and caller permissions.

**Not the same as:** The backtest engine or validator.

**Key invariant:** Denial reveals no protected contents.

**See:** `docs/specification/BACKTEST_AND_EVALUATION.md`

## BacktestRun

**Meaning:** The immutable record of what happened while executing the frozen system across the
authorized historical simulation.

**Not the same as:** An `EvaluationReport` or validation decision.

**Key invariant:** Later analysis cannot rewrite completed predictions, outcomes, fits, or failures.

**See:** `docs/specification/BACKTEST_AND_EVALUATION.md`

## EvaluationReport

**Meaning:** Multidimensional measurements, benchmarks, diagnostics, robustness views, caveats, and
trial context computed from a `BacktestRun` under an `EvaluationSpec`.

**Not the same as:** A binary promotion decision.

**Key invariant:** Evaluation measures evidence and cannot retrain the system.

**See:** `docs/specification/BACKTEST_AND_EVALUATION.md`

## Validator

**Meaning:** The independent scientific promotion gate deciding whether evidence satisfies the
predeclared standard.

**Not the same as:** A trader, portfolio manager, business decision-maker, evaluator, or report
writer.

**Key invariant:** The candidate's beneficiary cannot grant its own promotion.

**See:** `docs/specification/BACKTEST_AND_EVALUATION.md`

## ValidatedFinding

**Meaning:** The immutable scientific substance of a promoted claim, including identity, evidence,
caveats, provenance, trial context, and validation status.

**Not the same as:** A human-facing report.

**Key invariant:** Presentation changes cannot change the scientific conclusion.

**See:** `docs/specification/BACKTEST_AND_EVALUATION.md`

## ReportBuilder

**Meaning:** The presentation layer that turns a `ValidatedFinding` into a human-facing report.

**Not the same as:** The evaluator or validator.

**Key invariant:** It may change wording and layout, but not evidence, caveats, or scientific status.

**See:** `docs/specification/BACKTEST_AND_EVALUATION.md`

## Exposure

**Meaning:** The durable epistemic fact that protected evidence has become visible to the research
process.

**Not the same as:** A temporary access log entry.

**Key invariant:** Exposed evidence cannot later be represented as fresh or unseen for a modified
candidate. Freshness follows an authority-bound epistemic content period rather than a path or
resource label; previously accessible identical bytes are `PREEXPOSED`.

**See:** `docs/specification/BACKTEST_AND_EVALUATION.md`

## Exploration

**Meaning:** Open-ended, permitted research activity used to form and test provisional hypotheses.

**Not the same as:** Formal scientific computation or protected validation.

**Key invariant:** Exploratory outputs are working evidence, not automatically promotable objects.

**See:** `docs/specification/AUTHORITY_SANDBOX_AND_TOOLS.md`

## Formal Scientific Object

**Meaning:** A versioned, reproducible scientific definition with explicit dependencies, temporal
semantics, provenance, failure behavior, and lineage.

**Not the same as:** Temporary exploratory code or output.

**Key invariant:** Only explicit formalization may enter governed scientific evaluation.

**See:** `docs/specification/AUTHORITY_SANDBOX_AND_TOOLS.md`

## Promotion Gate

**Meaning:** A controlled boundary that changes the authority or epistemic status of an object,
finding, or lesson.

**Not the same as:** An ordinary tool call or model preference.

**Key invariant:** The actor benefiting from promotion cannot grant it.

**See:** `docs/specification/AUTHORITY_SANDBOX_AND_TOOLS.md`
