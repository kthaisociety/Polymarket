# model.request-decision — ContextPacket + expressive action schemas + model configuration → ModelResponse

Status: **LOCKED — readiness level 4 of 5**

## Purpose

model.request-decision inserts replaceable intelligence into the autonomous loop. It gives the selected model a
decision-sufficient scientific context and a small, expressive request vocabulary, then returns the
model's untrusted proposed intent without granting execution, mutation, or scientific authority.

```text
C_t  = decision-sufficient ContextPacket from context.build-packet
A    = small, deep, broadly available action-schema family
G_t  = model configuration + logical call identity
M_t  = untrusted provider-neutral ModelResponse

f005(C_t, A, G_t) → M_t
```

`R_t` remains reserved for `ResearcherState`; `M_t` denotes the model response. model.request-decision is the actual
model-call boundary. It is not action decoding, routing, sandbox execution, or observation handling.

The local creativity invariant is:

> model.request-decision may transform provider-call representation, but it must neither narrow the authorized
> research surface nor rewrite model-authored scientific intent.

## Relevant locked invariants

- **I14 — Context cannot bypass permissions.** model.request-decision receives the already permission-safe packet and
  cannot add hidden data or alternate retrieval.
- **I18 — Exploratory freedom does not grant side-effect freedom.** The model may author open-ended
  research requests, but model.request-decision grants no execution capability.
- **I20 — Model provider is replaceable.** Scientific behavior cannot depend irreversibly on native
  provider sessions, authentication objects, wire types, or transcripts.
- **I25 — Runtime retries do not duplicate irreversible effects.** A logical model call accepts at
  most one response for downstream consideration; retry does not execute actions.
- **context.build-packet.** `C_t` is the complete bounded, decision-sufficient, provider-neutral research surface for
  this decision.

Authoritative sources: `MODEL_PROVIDER.md`, `AUTHORITY_SANDBOX_AND_TOOLS.md`, M1 runtime
design/readiness, `INVARIANTS.md`, and context.build-packet.

## Source A

model.request-decision receives exactly:

1. **`ContextPacket C_t`** — the context.build-packet output, including usable mission, committed position, active
   investigation, decision-relevant numerical evidence, uncertainty, periods/lags/protocol,
   caveats, epistemic status, permissions, warnings, provenance, and permitted drill-down options.
2. **Expressive action schemas `A`** — a small family of deep request interfaces. The important
   exploratory escape hatch is open-ended `run_analysis`, through which the model may author novel
   permitted code, transformations, diagnostics, temporary models, and structured-return requests.
   Other conceptual families cover retrieval, formalization/versioning, privileged requests, and
   research/episode management. Exact grouping and names are implementation choices.
3. **Model/call configuration `G_t`** — selected provider/model, supported neutral inference
   settings, logical call/turn correlation, limits, and operational configuration needed to invoke
   the provider reproducibly and observe failures.

The provider receives no independent store, dataset, sandbox, capability, secret, permission,
protected permit, validator, or governance handle.

The supported action family should normally remain broad and stable. Schemas may accurately reflect
capabilities that are genuinely unavailable or uninstalled, but they must not be dynamically
shrunk merely to steer the model through a harness-preferred scientific path. Preconditions and
authorization for a concrete request are enforced downstream.

## Destination B

`ModelResponse M_t` is an untrusted provider-neutral representation of what the model proposed. It
contains or explicitly represents:

- logical call/turn correlation;
- optional concise model-authored scientific explanation or rationale when supplied;
- zero or one requested action intent for the M1 turn, including action family and authored
  structured arguments/code/text;
- explicit no-action/finish intent when supplied, without itself resolving an episode;
- neutral finish/status information;
- neutral usage/timing/model metadata needed for operations/provenance;
- explicit operational or malformed-response status when no valid neutral response exists.

Private chain-of-thought is neither required nor an architectural record. A response is proposed
intent, not a typed `AgentAction`, authorization, observation, finding, or state transition.

Provider-native response normalization is the internal adapter seam model.normalize-response. model.request-decision specifies the
public neutral invocation contract and its externally observable semantic result; it does not
duplicate model.normalize-response's wire-format rules.

## Mapping f

```text
C_t + A + G_t
    → invoke selected provider through neutral ModelProvider boundary
    → provider reasons over C_t and A
    → provider implementation normalizes native output through model.normalize-response
    → emit one untrusted provider-neutral M_t correlated to the logical call
```

model.request-decision may serialize neutral inputs into a provider request, invoke the provider, receive the neutral
adapter result, correlate it to the logical call, expose structured operational failure, and record
append-only model-call observability.

It may not reinterpret an unfamiliar scientific method into a known method, reject a schema-valid
open-ended analysis merely because no narrow tool recognizes it, repair malformed scientific intent
by guessing, or cause the proposed request to execute.

## Must preserve

- every decision-relevant semantic in the supplied `ContextPacket`;
- epistemic roles, numerical values/precision required for the decision, uncertainty, units,
  periods/vintages, lags, controls, protocol, robustness, caveats, warnings, and permissions;
- the supplied action families, schemas, descriptions, and expressive argument structure;
- arbitrary schema-valid model-authored code, text, transformations, intermediate structures,
  parameters, and structured-return requests;
- distinction between rationale, requested action, and finish/no-action intent;
- logical call/turn identity and model/configuration provenance;
- semantic intent across provider implementations and provider-session loss;
- untrusted status: model output carries no execution or scientific authority.

Preservation is semantic. Whitespace, JSON key ordering, wire envelopes, tokenization, and native
provider representations may differ unless exact text is itself an authored action argument.

## May transform

- neutral context/schema/configuration representation into a provider-supported request envelope;
- authentication and transport mechanics inside the provider adapter;
- provider-native output into neutral response representation through model.normalize-response;
- equivalent serialization, escaping, or message/tool-schema layout;
- native usage/error metadata into neutral operational metadata.

Every permitted transformation must preserve context meaning and model-authored intent. Provider
mechanics may change; scientific semantics may not.

## Must exclude

- writable task/session/state/episode/evidence/artifact/ledger stores;
- direct dataset, filesystem, network, process, sandbox, tool, or capability handles;
- secrets or provider credentials in `ContextPacket`/`ModelResponse` scientific content;
- authorization decisions, protected permits, validation authority, or governance state capable of
  self-approval;
- hidden store/data side channels unavailable through `C_t`;
- provider transcript/session as required scientific memory;
- invented context, observations, evidence, findings, or permissions;
- narrowing novel analysis into a predefined statistical method;
- known-analysis whitelists applied to schema-valid open-ended `run_analysis` intent;
- automatic action execution, typing, routing, authorization, episode/state mutation, or promotion;
- provider-native objects in the public model.request-decision result;
- private chain-of-thought as required state or evidence.

## Authority boundary

- context.build-packet/harness owns which authorized research meaning appears in `C_t`.
- The harness owns the expressive request schemas and selects supported provider configuration.
- The model owns reasoning, hypothesis generation, interpretation, planning, authored exploratory
  code, and its proposed next intent.
- model.request-decision/provider may propose but cannot execute, authorize, validate, persist scientific truth, or
  mutate runtime state.
- model.normalize-response owns native-response normalization; action.decode-intent owns decoding into a typed request; action.authorize-request owns
  authorization/routing; sandbox/capability seams own execution and side effects.
- A visible tool schema means “this request form exists,” not “every concrete request is authorized.”

## Allowed state changes

model.request-decision may append operational/trajectory observability such as:

- logical model-call started/completed/failed events;
- attempt/provider/model/configuration identities;
- bounded neutral usage/timing/error metadata;
- which exact packet/schema identities were supplied;
- which response identity was accepted for the logical call.

These events are audit/operations records, not committed research belief or execution effects.

## Forbidden state changes

- no task, session research status, `ResearcherState`, `ResearchEpisode`, evidence, artifact,
  ledger, environment, permission, exposure, gate, candidate, or finding mutation;
- no dataset/protected-content read through a provider side channel;
- no capability/sandbox/tool execution;
- no action authorization, routing, decoding, or semantic commit;
- no scientific conclusion created merely because the model stated it;
- no second accepted response for the same logical model call;
- no provider transcript promoted into durable scientific memory.

## Failure semantics

- Authentication expiry, rate limiting, timeout, cancellation, transport error, context-capacity
  failure, and provider unavailability surface as explicit operational failures without scientific
  mutation or fabricated intent.
- Malformed or unnormalizable native output surfaces explicitly; model.request-decision does not guess a valid action.
- A provider unable to accept the required decision-sufficient packet fails explicitly rather than
  silently truncating scientific meaning.
- Exact logical-call retries may issue multiple operational attempts according to policy, but at
  most one response becomes accepted for downstream decoding. A late competing response is recorded
  and ignored/quarantined, not emitted as another action intent.
- Reusing a logical call identity with changed packet, schemas, or material configuration is an
  explicit conflict, not a retry.
- Provider/session loss is recoverable by invoking from `C_t`, `A`, and `G_t`; no hidden transcript
  fallback may change meaning.

## Observable consequences

- A provider receives the full context.build-packet packet and expressive action families needed to reason about
  the current scientific situation.
- Scientifically different packets can produce different model intents through the actual boundary.
- An unusual schema-valid open-ended analysis arrives in `M_t` with its authored semantic content
  intact rather than being rewritten into a familiar diagnostic.
- Exercising model.request-decision alone yields no data access, execution, authorization, or scientific mutation.
- Deleting provider-native history still permits a correct call from the neutral inputs.
- Replacing the provider does not require changing runtime/scientific objects or narrowing the
  supported research intent.

## False-success implementations considered

1. Pass only a short “looks promising” summary instead of the complete `ContextPacket`.
2. Expose many narrow tools and reject any analysis not present in a known-analysis registry.
3. Rewrite custom `run_analysis` code into a standard correlation/regression helper.
4. Drop unfamiliar but schema-valid structured-return fields.
5. Give the provider a dataset/store/sandbox handle for convenience.
6. Execute a requested tool inside `ModelProvider.complete`.
7. Depend on a native conversation transcript to supply missing context.
8. Return provider-native tool-call/auth/session objects as `ModelResponse`.
9. Convert timeout/malformed output into a guessed default action.
10. Accept both a retry response and a late original response as separate intents.
11. Hide broad actions dynamically to make the model follow a preferred research workflow.

## Falsifying tests

### model.request-decision-T1 — decision-sufficient scientific context reaches the provider

Construct `C_t` with distinctive coefficient, uncertainty, sample size, period/vintage, lag,
controls, robustness failure, caveat, epistemic status, permission, and warning semantics. A capture
provider receives inputs only through model.request-decision. Assert all semantics arrive intact with exact packet and
logical-call identity; no alternative store/transcript side channel exists. **Level A/B.**

### model.request-decision-T2 — context causally changes model intent

Send otherwise identical packets where one relationship is stable across exclusions and the other
collapses after one region is removed. A deterministic provider reads only `C_t`: the first requests
temporal investigation and the second requests influence diagnostics. Assert different neutral
responses. **Level C.**

### model.request-decision-T3 — novel open-ended analysis survives

Use a deterministic provider response containing an unusual but schema-valid `run_analysis` intent:
custom authored code, nonlinear transformation, intermediate structures, uncommon parameters, and
novel structured-return fields. Assert `M_t` preserves their semantic content without substituting a
known method, dropping fields, or rejecting novelty alone. **Level A/B.**

This test is local to provider-boundary preservation. action.decode-intent later proves preservation into the typed
`AgentAction`; the sandbox seams later prove execution of the exact permitted computation.

### model.request-decision-T4 — small expressive action vocabulary reaches the model without steering

Supply deep schemas including open-ended analysis, retrieval, formalization, privileged request,
and research management. Assert the provider receives their expressive arguments unchanged. Mark a
formal action as currently missing prerequisites but still requestable; assert model.request-decision does not hide it
or replace it with a preferred next step. A genuinely unavailable capability may be represented as
unavailable without inventing an alternative. **Level A.**

### model.request-decision-T5 — provider receives no authority or execution handles

Exercise model.request-decision with fail-on-access doubles for stores, datasets, sandbox, capabilities, permissions,
protected permits, and validators. Assert none are passed or called. A returned action request causes
zero execution, authorization, data read, exposure, or scientific mutation. **Level A/B.**

### model.request-decision-T6 — provider-session/transcript independence

Invoke from complete `C_t`, `A`, and `G_t`, delete/reset all provider-native history, and invoke the
next logical call. Assert the call remains valid and receives complete current semantics without
hidden transcript reconstruction. **Level B.**

### model.request-decision-T7 — neutral provider replacement at the public boundary

Use two provider implementations with different adapter/native mechanics that expose semantically
equivalent neutral responses for equivalent inputs. Assert the model.request-decision caller observes equivalent
`ModelResponse` meaning and no provider-native type or branch. Detailed native normalization is
tested under model.normalize-response. **Level B.**

### model.request-decision-T8 — operational failures preserve scientific state

For timeout, rate limit, expired authentication, cancellation, provider unavailable, context
capacity, and malformed/unnormalizable output, assert explicit failure, no fabricated/default action,
and no task/state/episode/evidence/permission/exposure mutation. **Level A/B.**

### model.request-decision-T9 — logical-call retry accepts at most one response

Simulate timeout followed by retry success and a late original completion, including concurrent
completion ordering. Assert one accepted neutral response identity for the logical call, no second
emitted intent, and only operational attempt events. Reuse the call identity with changed packet,
schemas, or configuration and assert conflict. **Level B.**

### model.request-decision-T10 — finish/no-action carries no transition authority

Return finish/no-action intent with a persuasive scientific explanation. Assert model.request-decision reports that
intent without resolving the episode, committing state, creating a finding, or translating it into
an episode-transition action. **Level A/B.**

## Mutation-sensitivity check

**Mutation A:** Replace schema-valid custom `run_analysis` content with the nearest known analysis
type and discard unfamiliar structured-return fields.

**Expected test failure:** model.request-decision-T3 becomes red because model-authored scientific intent differs from
the neutral response.

**Mutation B:** Pass a writable capability/store bundle to the provider so it can “efficiently” act
during reasoning.

**Expected test failure:** model.request-decision-T5 becomes red because forbidden handles cross and fail-on-access
doubles observe authority/execution behavior.

**Mutation C:** Accept every completed retry attempt independently.

**Expected test failure:** model.request-decision-T9 becomes red because one logical call emits multiple intents.

## Composite dependencies

- **context.build-packet:** produces the exact decision-sufficient `ContextPacket`.
- **model.normalize-response:** normalizes provider-native output without changing intent.
- **action.decode-intent:** decodes untrusted neutral intent into a typed action or structured failure.
- **action.authorize-request:** authorizes/routes the exact current typed request.
- **sandbox.authorize-execution/sandbox.execute-analysis:** constrain capabilities and side effects while executing agent-authored analysis.
- **research.continue-from-exploration:** later proves the complete exploratory feedback loop changes behavior through returned
  evidence.

These dependencies are named, not specified or locked here. End-to-end creativity preservation
requires a later composite test across model.request-decision–action.authorize-request and sandbox execution; it is not falsely claimed by
model.request-decision alone.

## User decisions

The architecture owner approved:

1. The model receives a decision-sufficient scientific context before choosing its next request.
2. The action surface uses a few deep action families rather than a proliferation of narrow tools.
3. Open-ended agent-authored analysis is the exploratory escape hatch for novel wrangling,
   diagnostics, transformations, features, and temporary models.
4. The harness maximizes scientific creativity during exploration and increases rigor at
   formalization and protected-evidence boundaries.
5. model.request-decision preserves open-ended model intent but does not own decoding, authorization, execution,
   sandbox policy, observations, or scientific mutation.
6. Preconditions should normally be enforced on the concrete downstream request rather than hiding
   broad tools merely to steer the model.
7. Provider sessions/transcripts are optional operational caches, never scientific memory.
8. M1 serializes consequential interaction to zero or one requested action per model turn; the model
   may express a broader plan in non-authoritative rationale/context.
9. The harness standardizes interfaces, evidence, identity, and authority—not scientific
   imagination.

## Implementation/test handoff

Implement model.request-decision-T1 through model.request-decision-T10 as ordered red tests before production code for this seam. T2 is
the causal information proof, T3 protects creativity, T5 protects authority, and T9 protects logical
call identity under retry.

Forbidden shortcuts include abbreviated context, narrow-analysis whitelists, helpful scientific
rewriting, dropping unfamiliar valid arguments, hidden transcript dependence, provider-held runtime
authority, implicit execution, guessed fallback actions, and duplicate accepted retry responses.

Provider SDK, authentication transport, request/message layout, serialization, identifier format,
retry timing/backoff, usage accounting, and optional provider caching remain free where supported and
semantically conforming. model.normalize-response retains ownership of provider-native normalization details.

This handoff is specification only and does not authorize production code or executable tests.

## Status

**LOCKED — readiness level 4 of 5.**

Level 5 requires executable discriminating tests passing through the real production path.
