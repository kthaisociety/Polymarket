# Runtime implementation map

Status: **Milestone 1 core, runtime/exploration continuation, checkpoint reconstruction, a
production-shaped provider adapter, model-authored development trials, and an exact registered
scientific-workflow action implemented**.

The Milestone 1 slice proves one provider-neutral autonomous inspection episode and an explicit
semantic commit. A separately registered workflow composition now invokes the repository's
temporal-sample, formal-system, development-evaluation, freeze, protected-execution, evaluation,
and validation modules under exact authority bindings. The free-form inspection action itself
makes none of those scientific claims, and neither path claims production persistence or live
provider/credential verification.

## Public modules

- Task proposal and exact human confirmation:
  `src/research_agent/task_compilation.py`
- Canonical runtime records and failures:
  `src/research_agent/runtime/models.py`
- Coherent in-memory logical stores and trajectory:
  `src/research_agent/runtime/store.py`
- Session/state-zero/episode-zero initialization:
  `src/research_agent/runtime/initialization.py`
- Reconstructible `ContextPacket` projection:
  `src/research_agent/runtime/context.py`
- Provider-neutral response, deterministic scripted provider, and compatible JSON adapter:
  `src/research_agent/runtime/provider.py`
- Typed action decoding:
  `src/research_agent/runtime/actions.py`
- Authorized toy-dataset inspection and harness provenance:
  `src/research_agent/runtime/capabilities.py`
- Independent proposal validation and atomic/idempotent commit. The in-memory store stages
  replacement episode/state/commit/trajectory tables behind one lock and restores every prior
  table reference if publication faults after any individual staged assignment. Exact retry then
  publishes once; this proves in-process atomicity, not crash-durable database transactions:
  `src/research_agent/runtime/commit.py`
- `advance_one_turn` and bounded runtime orchestration:
  `src/research_agent/runtime/engine.py`
- Session-bound `run_analysis` routing and adaptation:
  `src/research_agent/runtime/actions.py`, `src/research_agent/runtime/capabilities.py`
- Structured `EpisodeCheckpoint` publication and reconstruction:
  `src/research_agent/runtime/models.py`, `src/research_agent/runtime/context.py`,
  `src/research_agent/runtime/store.py`
- Exact registered scientific-workflow composition:
  `src/research_agent/scientific_workflow/`, with the runtime transport and authority seam in
  `src/research_agent/runtime/actions.py`, `src/research_agent/runtime/capabilities.py`, and
  `src/research_agent/runtime/engine.py`
- Creativity-first authored investigation and one-trial-per-turn runtime bridge:
  `src/research_agent/investigation/`, with strict decoding/routing in
  `src/research_agent/runtime/actions.py`, `src/research_agent/runtime/capabilities.py`, and
  `src/research_agent/runtime/engine.py`

## Completed Milestone 1 transitions

The implementation provides the first executable path through:

```text
mission.confirm-task
→ runtime.initialize-research
→ context.build-packet
→ model.request-decision / model.normalize-response
→ action.decode-intent / action.authorize-request
→ observation.assemble-authoritative-result
→ episode.record-observation
→ runtime.continue-from-observation
→ commit.compose-request / commit.validate-proposals
→ commit.publish-boundary / commit.retry-idempotently
```

The composite proof is
`tests/integration/test_milestone_1_acceptance.py`. It discards provider-side call history after an
inspection, reconstructs context from stores, verifies that the observation remains episode working
evidence while state stays at version zero, and then commits a separately proposed evidence-backed
state delta and terminal episode transition.

`OpenAICompatibleProvider` is an optional provider-boundary implementation over injected
`HttpTransport` and `SecretResolver` protocols. It serializes the complete bounded
`ContextPacket` and exact five-action JSON schema, uses explicit endpoint/model/timeout/request
bounds, independently validates the returned action against that recursive schema, and normalizes
exactly one compatible function call into the existing `ModelResponse`.
`UrllibHttpTransport` provides an SDK-free standard-library transport; `ScriptedModelProvider`
remains the deterministic runtime/eval provider. Credentials exist only in the private transport
header path; request/header representations are redacted, unsafe header values fail before
transport, and echoed credential material is rejected before it can enter normalized response
content, metadata, exceptions, or scientific records. Request and response bytes plus JSON nesting
are bounded. Each independent invocation receives a fresh logical-call identity; internal transient
retries reuse one exact request/idempotency identity, and an identity collision cannot accept a
second decision. Authentication, permanent request, malformed output, tool-free output,
response-cardinality, recursive-schema, and response-bound failures fail closed without retry.

The runtime now also decodes `RunAnalysisAction`, verifies current session/episode and the
environment's `run_analysis` capability before execution, and delegates only to the exact
session-bound `AnalysisHarness`. Runtime authorization additionally requires every requested view
to name the exact versioned environment snapshot, a dataset in that snapshot's readable scope, and
no protected resource. An unversioned environment-name match, view-local `protected` flag, or field
allow-list is insufficient authority. The adapter preserves harness-observed code/data-access provenance,
warnings, recoverability, provisional epistemic status, and drill-down artifact identities in the
runtime `StructuredObservation`. Analysis results enter only the active `ResearchEpisode`; they do
not change `ResearcherState` without a later independently validated semantic commit.

Runtime observations now carry exact delivery, session, episode, action, environment-snapshot, and
content identities. JSON-like payloads are recursively detached and immutable. Exact delivery
replay converges without a second append; changed payload under a delivery/observation identity and
foreign authority bindings conflict before episode mutation. Semantic commit rechecks that every
episode evidence record still has the exact session/episode/environment binding before allowing its
identity or artifacts to support durable state.

The runtime now also decodes `RunScientificWorkflowAction`. Its model-authored payload contains
only `workflow_id` and an idempotency key in addition to current action/session/episode identity;
it cannot submit a caller-authored catalog, system, scenario, metric, threshold, claim, protected
scope, authority label, or authority object. `ActionRouter` verifies the capability and asks the
coordinator to authorize the exact current task, task semantic digest, session, episode,
environment snapshot and content, confirmed dataset/target scope, and protected-resource scope
before recording an authorization event. The coordinator then rechecks currentness and resolves
only the exact authority-issued graph.

Workflow admission is an authority-owned composition boundary. `RegisteredScientificWorkflow`
contains the scientific graph and exact task/session/environment scope, but carries no governance
or validation identity, protected catalog, or protected binding. An immutable
`WorkflowAuthorityRegistry` resolves governance permission and validation authority from
independently configured grants. A separate `ProtectedResourceRegistry` resolves the exact
protected scope to an authority-issued binding and catalog. `WorkflowRegistry` exposes resolution,
not public registration; its paired issuer holds a non-reconstructible capability and seals those
inputs into `ScientificWorkflowIssuance`. Reusing the correct authority label with a different
capability, or changing the protected binding/catalog for an issued scope, conflicts before ledger
or exposure effects.

API crosswalk for the hardened composition root:

| Removed caller-owned input/path | Authority-owned replacement |
|---|---|
| `WorkflowRegistry.register(workflow)` | `configure_scientific_workflow_authority(...)` plus `ScientificWorkflowIssuer.issue(workflow)` |
| workflow governance/validation labels | `WorkflowAuthorityRegistry` exact grants resolved during issuance |
| workflow protected binding/catalog | `ProtectedResourceIssuer.issue(...)` into `ProtectedResourceRegistry` |
| workflow record as execution authority | immutable `ScientificWorkflowIssuance` resolved by the coordinator |

One registered graph composes legal development-sample construction and `DevelopmentEvaluator`
evidence through an authority-issued exact freeze-eligibility registration, independent freeze,
protected governance and view binding, historical execution, pure evaluation, independent
validation, and either `ValidatedFinding` or retained negative
evidence. Exact retry returns the original `WorkflowReceipt`; a changed workflow under the same key
conflicts before another protected effect, while a new attempt after disclosure is denied as prior
exposure. A promoted finding alone is admitted to the canonical report registry and rendered under
one fixed presentation specification; a rejected result cannot produce a report reference. The
runtime cannot choose the freeze outcome: a pre-issued denial returns the exact development and
freeze-decision evidence without protected disclosure. The resulting `StructuredObservation`
carries bounded receipt/evidence/report references and is
explicitly provisional. It updates the active episode only; a later independently validated
semantic commit is still required to change `ResearcherState`.

The runtime also decodes `RunAuthoredDevelopmentTrialAction`. Trusted composition first registers
only a question, exact readable development catalog, sample population/current clock, and fixed
search/evidence budget. Registration creates a bounded model-visible observation containing the
exact investigation ID, stopping rule, exact `FieldRef` descriptions, and only the value-free
exploratory views/fields already granted by the current session harness. It contains no values or
preassembled target, feature, model, or workflow ID. The provider then supplies arbitrary
four-entrypoint scientific source plus a manifest and parent-trial ancestry. `ActionRouter`
rechecks current task,
session/episode, environment, dataset readability, non-protected scope, capability, and exact
registration before candidate publication or worker execution.

Each successful turn returns selection-exposed out-of-fold evidence, actual phase/field accesses,
candidate/evidence/ledger identities, and a harness-owned `revise`, `reject`, or `credible`
disposition. The observation is recorded as `DEVELOPMENT` and is reconstructed into the next packet
so the model can author a revision. Exact idempotent replay returns one receipt; changed source,
manifest, rationale, or ancestry under the same key conflicts. A malformed program creates a
failure receipt and append-only failed trial rather than a silent fallback. `credible` means only
that the predeclared development rule was met; this action cannot freeze, disclose protected data,
validate, promote, or report by model authority. When trusted composition configures the independent
`AuthoredFreezeService`, the router submits only the coordinator-issued credible candidate/evidence
pair. The service requires protected protocol identities fixed in the registration before trial one,
issues no caller-selected decision field, and seals the exact source digest and trial ancestry through
the existing `FreezeGate`. A successful development trial that did not meet the credibility rule
cannot cross this boundary. Protected disclosure, execution, validation, promotion, and reporting
remain separate.

`ContextBuilder.checkpoint_current_episode` publishes a content-addressed immutable in-memory
`EpisodeCheckpoint` containing unresolved plan/interpretation semantics, current permissions,
warnings, version lineage, and a bounded suffix of substantive evidence. Count and serialized-byte
bounds apply to both checkpoints and model packets. Older evidence remains in the observation store
and is named by an immutable drill-down artifact reference plus explicit omission count and ordered
evidence-chain digest. Publication and retrieval independently recompute checkpoint identity and
compare task, session, state, episode, environment, permissions, warnings, protected metadata, and
retained evidence with authoritative stores. Reconstruction adds bounded later evidence without
walking or embedding the complete episode history.

`ContextPacket` now carries the mandatory confirmed target/horizon/constraints, unresolved task
semantics, episode objective/status/temporary interpretations, exact permissions and warnings, and
available protected-resource/exposure references. Paired deterministic providers prove constraint
and provisional-interpretation differences change the next packet-only action.

The horizon is transported as the task's exact `TemporalOffset`; context construction never
normalizes calendar months/quarters into elapsed days. Its complete policy identity therefore
survives initialization, checkpoint canonicalization, and model readback.

## Contract and adversarial coverage

- `tests/contract/test_task_compilation*.py` covers unresolved and invalid semantics, exact
  target/environment preservation, proposal lineage, human confirmation, and stale confirmation.
- `tests/runtime/test_initialization_and_context.py` covers epistemic zero, retry versus independent
  session, coherent-or-nothing initialization, reconstructibility, dangling evidence, and identity
  mismatch.
- `tests/runtime/test_capability_and_actions.py` covers provider normalization, typed decoding,
  bounded read-only inspection, authority denial without value leakage, and harness provenance.
- `tests/runtime/test_semantic_commit.py` covers independent validation, atomicity, exact replay,
  semantic key conflict, invalid evidence, and injected publication failure.
- `tests/integration/test_milestone_1_acceptance.py` covers the complete deterministic organism and
  repair after a rejected commit.
- `tests/integration/test_runtime_exploration_loop.py` covers packet-driven analysis continuation,
  operational repair, forged/capability/protected denial before execution, exact access provenance,
  provisional state separation, large artifact references, and absent/stale/protected view denial
  before sandbox execution.
- `tests/runtime/test_episode_checkpoint.py` covers checkpoint/rebuild equivalence, later evidence,
  supersession and stale rejection, permissions/warnings/currentness, content forgery/mutation,
  bounded checkpoint growth, history drill-down, and explicit bounded-context omission.
- `tests/runtime/test_openai_compatible_provider.py` covers exact packet/schema serialization,
  credential confinement across request/response/error diagnostics, transient-only retry and
  stable per-call idempotency, logical-call collision denial, strict native cardinality and
  recursive action-schema enforcement, typed-action compatibility, request/response/depth bounds,
  safe URL/config parsing, standard-library read/exception behavior, changed-packet identity, and
  checkpoint-rebuilt packet equivalence through injected transports.
- `tests/runtime/test_initialization_and_context.py` covers immutable authority-bound observation
  delivery, exact replay/change conflict, and packet-semantic causal behavior.
- `tests/runtime/test_semantic_commit.py` covers corrupted evidence-authority rejection before any
  durable state effect.
- The verification-owned `evidence-to-atomic-commit` composition now observes the public
  `ActionRouter`/observation-store/`CommitCoordinator` path across authoritative, foreign, forged,
  four staged-publication-fault, retry, exact-replay, and changed-payload worlds. Its catalog-owned
  oracle requires episode, state, stored result, and correlated `commit.published` event to appear
  together; every injected stage restores the exact pre-attempt state and remains retryable; exact
  replay produces one effect; and semantic key reuse conflicts. This is causal proof of the
  in-process copy-on-write boundary, not crash-durable transaction recovery.
- `tests/integration/test_registered_scientific_workflow.py` covers the exact registered workflow
  from a packet-only scripted decision through protected finding or retained rejection, subsequent
  independent semantic commit, retry/conflict/prior-exposure behavior, future-poison exclusion,
  authorization-before-effect denials, authority-label/capability substitution, protected
  binding/catalog substitution, and reuse by a different time-series subject/session.
- `tests/integration/test_autonomous_investigation_acceptance.py` covers question-only registration,
  provider-authored interaction feature/label/fit/predict source, legal OOF evaluation, evidence
  context reconstruction, revision ancestry, future-poison invariance, negative budget exhaustion,
  authorization-before-source execution, exact retry/change conflict, and a provider with no
  instance state deriving its exact manifest and analysis request solely from reconstructed field
  identities, value-free analysis surfaces, failed development evidence, and a harness-owned
  exploratory observation.

## Verification

Run from the repository root:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
./scripts/check.sh
```

## Remaining reds and deliberate deferrals

- Persistence is in-memory and proves semantics, not crash durability or a production database.
- The context builder implements deterministic count/byte-bounded working observations and structured
  checkpoints, not general semantic search, heterogeneous formal evidence, or token-aware
  compression.
- `InspectDatasetAction`, `RunAnalysisAction`, `RunAuthoredDevelopmentTrialAction`,
  `RunScientificWorkflowAction`, and `ProposeEpisodeTransitionAction` exist. Authored development
  publication/revision, independent freeze, protected authored execution, independent resolution,
  and validated question memory now work. The orchestration proof for autonomous
  exploration-to-development authorship and hidden real-researcher family evaluation remain red.
- The deterministic validator proves evidence existence and authority; autonomous scientific
  interpretation quality remains a later behavioral-eval responsibility.
- The compatible provider adapter, authentication boundary, and retry policy are exercised only
  with fake transports and secret resolvers. No live endpoint, credential, model compatibility,
  network, streaming, cancellation, or production observability verification is claimed.
- Logical-call uniqueness and accepted-decision collision protection are in-memory for one adapter
  instance. Crash-durable provider-call journaling, cross-process retry, backoff/`Retry-After`, and
  cost reconciliation remain production integration work.
- Production sandbox isolation, durable runtime persistence, and richer provider usage/cost and
  streaming support remain outside this runtime slice.
- The workflow/authority/protected-resource registries, scientific ledger, development-trial
  history, exposure store, protected evidence store, and idempotency outcomes are in memory. The
  integration proves one-process semantics, not crash durability, distributed concurrency,
  external identity attestation, or recovery after uncertain acknowledgement.
- `available_at` is fixture metadata only. No code in this slice claims `InformationSet I_t` or
  `TrainingSample S_t` legality.
