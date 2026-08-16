# action.decode-intent — Untrusted ModelResponse → typed AgentAction or structured failure

Status: **LOCKED — readiness level 4 of 5**

## Purpose

action.decode-intent converts one untrusted provider-neutral model intent into a faithfully typed runtime request
before any currentness check, authorization, execution, observation, or scientific mutation.

```text
untrusted ModelResponse M_t
+ exact action schemas supplied for logical call L
        ↓ action.decode-intent action decoding
typed AgentAction Q_t
or structured decoding failure
```

Typing constrains the request envelope, not the model's scientific imagination. Open-ended authored
analysis remains open-ended; downstream runtime code receives a bounded, inspectable request rather
than arbitrary provider output.

The local invariant is:

> Preserve creative scientific content exactly, validate only the declared request envelope, create
> harness-owned transport identity, and leave authority/currentness to action.authorize-request.

## Relevant locked invariants

- **I18 — Exploratory freedom does not grant side-effect freedom.** Model-authored code may be
  expressive, while typed requests still grant no execution authority.
- **I20 — Model provider is replaceable.** Decoding consumes only neutral `ModelResponse`, never
  provider-native objects.
- **I25 — Runtime retries do not duplicate irreversible effects.** Harness-owned action/idempotency
  identity remains stable for exact replay and cannot be forged by model output.
- **model.request-decision.** The provider boundary preserves open-ended model intent and emits zero or one untrusted
  action intent per M1 turn.
- **model.normalize-response.** Provider-native representation has already been normalized without changing intent.

Authoritative sources: M1 runtime design/readiness, `MODEL_PROVIDER.md`,
`AUTHORITY_SANDBOX_AND_TOOLS.md`, model.request-decision, and model.normalize-response.

## Source A

action.decode-intent receives:

1. **One untrusted neutral `ModelResponse`** correlated to an exact logical model call. It may carry
   one requested action intent, finish/no-action intent, model-authored explanation, and neutral
   provenance/operational metadata.
2. **The exact action-schema set supplied for that logical call** — not a newer global registry or
   whichever actions happen to be installed when decoding later.
3. **Trusted decoding correlation** — logical call, task/session/episode context references, schema
   set/version, and retry identity established by the harness rather than accepted from model text.

Model-supplied action names, arguments, code, target identities, idempotency values, and assertions
are untrusted content until their respective downstream boundaries validate them.

## Destination B

action.decode-intent returns exactly one of:

1. **Typed `AgentAction`** — a structurally valid request whose action family existed in the exact
   supplied schema set. Its common envelope conceptually carries:
   - harness-created `action_id`;
   - stable harness-created idempotency/request identity where required;
   - originating logical model-call and schema-set identity;
   - typed action kind;
   - model-claimed target session/episode/version references as untrusted claims;
   - faithfully preserved typed arguments, authored code/text, and structured-return request;
   - bounded model-response provenance needed for later audit.
2. **Structured decoding failure** — safe code/message/recoverability and correlation, with no
   `AgentAction` and no downstream effect.
3. **Explicit no-action/finish result** — not an `AgentAction` and not an episode transition.

M1 initially implements only the action types in its declared schema set (currently
`InspectDatasetAction` and `ProposeEpisodeTransitionAction`). The contract also governs later small,
deep action families such as open-ended `RunAnalysisAction` when their schemas become enabled. action.decode-intent
must not invent unsupported domain actions early.

## Mapping f

```text
M_t + exact schemas/correlation for L
    → classify action versus no-action/failure
    → require zero or one requested action
    → match action kind against the exact schema supplied for L
    → validate the common envelope and action-specific structural schema
    → preserve model-authored scientific content
    → attach harness-owned action/replay identity and trusted call provenance
    → emit typed AgentAction or explicit structured failure/no-action
```

Structural validation may check required fields, types, bounds encoded in the advertised schema,
unknown envelope fields, representability, and exact action cardinality. It may not judge whether
the proposed science is wise, whether data access is permitted, or whether the target episode is
still current.

## Must preserve

- exact model-authored action kind when supported by the supplied schema;
- authored code, text, values, nested structures, lists, parameters, transformations, and
  structured-return requests;
- unfamiliar but schema-valid content in explicitly extensible argument locations;
- distinction between requested action, rationale, and finish/no-action intent;
- model-claimed target/session/episode/version values as untrusted claims without substitution;
- originating logical call, schema-set, model-response, and provider-neutral provenance;
- semantic difference between exact replay and a changed request;
- untrusted/request status: a typed action is not authorization or execution.

Representation may become domain-typed. Scientific meaning may not be narrowed, repaired, or
rewritten.

## May transform

- neutral mappings/lists/scalars into typed action/envelope representations;
- valid encoded argument values into equivalent typed values;
- model-call/request position into stable harness-owned action/idempotency identity;
- decoding problems into safe structured failure vocabulary;
- supported action aliases only when the exact advertised schema declares them equivalent.

## Must exclude

- provider-native response, SDK, session, authentication, or wire objects;
- unsupported/unknown action kinds converted into a known kind;
- scientific-method whitelists inside open-ended analysis content;
- generated replacement code or arguments not authored by the model;
- silently dropped unfamiliar content in schema-declared extensible fields;
- model-controlled authoritative action or idempotency identity;
- latest/current session or episode substitution for a model-claimed target;
- currentness, permission, policy, protected-access, or governance decisions;
- execution handles, stores, datasets, sandbox/capability access, or validator authority;
- implicit episode transition or state delta from finish/no-action text.

## Authority boundary

- The model proposes action kind, target claims, and scientific arguments.
- The harness owns logical call/schema correlation and creates authoritative transport/replay
  identity.
- action.decode-intent may validate structure against the exact advertised schema and reject malformed/unsupported
  intent.
- action.authorize-request owns comparison of target claims with authoritative current session/episode/policy and owns
  authorization/routing.
- Capability/sandbox/commit seams own execution and scientific/state effects.
- A typed `AgentAction` means “well-formed request,” never “permitted” or “scientifically valid.”

## Allowed state changes

action.decode-intent may append bounded trajectory/audit events recording decoded request identity/kind or structured
rejection/no-action result. It may allocate/reserve harness-owned action/idempotency identity without
performing the requested effect.

## Forbidden state changes

- no task/session lifecycle, `ResearcherState`, `ResearchEpisode`, evidence, artifact, ledger,
  environment, permission, exposure, gate, candidate, or finding mutation;
- no action authorization, routing, capability/sandbox/tool execution, data read, or semantic commit;
- no creation of observation/evidence from model assertions;
- no provider call or native-response reinterpretation;
- no durable effect keyed by a model-authored idempotency value.

## Failure semantics

- Missing/invalid action envelope, malformed fields/arguments, invalid cardinality, forbidden extra
  envelope fields, or structurally unrepresentable content yields `MALFORMED_MODEL_RESPONSE` (or an
  equivalent locked failure category) and no action.
- An unknown/unsupported action kind, or a kind absent from the exact schema set supplied for the
  logical call, yields `INVALID_REQUEST`; action.decode-intent does not convert it to `run_analysis` or another kind.
- Finish/no-action produces an explicit non-action result, not failure and not a transition.
- Model-supplied target identities that are structurally well formed remain claims in the typed
  request; action.authorize-request rejects mismatch/staleness against authoritative current state.
- Exact replay of the same logical response/schema correlation yields the same harness-owned action
  identity/result. Changed semantics under the same replay identity yields conflict rather than a
  silently changed action.
- Every failure/no-action path is state-pure apart from bounded append-only decoding observability.

## Observable consequences

- A schema-valid novel analysis becomes a typed request with its scientific content intact.
- A structurally identical response under a schema set that did not advertise its action kind is
  rejected rather than routed through a hidden capability.
- The typed request exposes model-claimed targets for action.authorize-request to verify but carries no assertion that
  they are current or authorized.
- Exact replay converges on one request identity; changed intent cannot reuse it.
- Exercising action.decode-intent alone produces no data access, execution, episode/state mutation, or scientific
  evidence.

## False-success implementations considered

1. Convert every unknown action into `RunAnalysisAction` with generated wrapper code.
2. Validate against the latest global action registry rather than the schemas supplied for the call.
3. Trust model-authored `action_id` or idempotency key as authoritative.
4. Replace a stale/foreign target identity with the current episode during decoding.
5. Strip unknown fields everywhere, including schema-declared extensible scientific arguments.
6. Accept arbitrary extra envelope fields that create undocumented execution paths.
7. Treat `finish` text as an episode transition or state commit.
8. Instantiate a typed action and immediately dispatch it from the decoder.
9. Branch on provider-native response/tool-call types.

## Falsifying tests

All action.decode-intent tests are deterministic Level A/B tests. They prove faithful typing and state-pure
rejection, not scientific reasoning, current authorization, or execution.

### action.decode-intent-T1 — supported intent becomes exact typed action

Decode each M1-supported action kind from a neutral response using the exact advertised schema set.
Assert correct typed kind, exact arguments, model-response/call/schema provenance, untrusted target
claims, and harness-owned action/replay identity.

### action.decode-intent-T2 — open-ended analysis content survives typing

When an open-ended analysis schema is enabled, decode custom authored code, nonlinear transforms,
uncommon nested parameters, intermediate structures, and novel structured-return fields. Assert
semantic preservation without method whitelisting, generated replacement code, or field loss.

This test may use a contract/test action schema before the later sandbox production action exists;
it must not prematurely implement sandbox.authorize-execution/sandbox.execute-analysis execution.

### action.decode-intent-T3 — exact supplied schema set governs decoding

Use the same well-formed response with schema set A that advertised its kind and schema set B that
did not. Assert A yields the typed action and B yields `INVALID_REQUEST`. Prevent access to a latest
global registry as a side channel.

### action.decode-intent-T4 — malformed envelope/arguments fail without repair

Exercise missing kind, missing required field, wrong type, invalid bound, forbidden extra envelope
field, malformed argument encoding, and multiple action intents. Assert structured
`MALFORMED_MODEL_RESPONSE`, no guessed/default action, and unchanged scientific stores.

### action.decode-intent-T5 — unsupported action is not rewritten

Submit an unknown action with plausible scientific arguments. Assert `INVALID_REQUEST` and exact
rejection observability; it is not converted to `run_analysis`, inspection, or generated code.

### action.decode-intent-T6 — target claims are preserved but not trusted

Decode structurally valid session/episode/version claims that differ from the authoritative current
runtime state. Assert action.decode-intent preserves the claims and emits no currentness/authorization decision.
Pass the action to a fail-on-use action.authorize-request double to show decoding itself makes no comparison or
substitution. The later action.authorize-request test owns rejection of the mismatch.

### action.decode-intent-T7 — harness owns action and replay identity

Provide model-authored action/idempotency-like fields and assert they cannot control authoritative
identity. Exact replay of the same logical response/schema correlation yields the same harness-owned
identity/result; a distinct call yields a distinct identity; changed semantic payload under the same
replay correlation yields conflict.

### action.decode-intent-T8 — finish/no-action is not a transition

Decode a persuasive finish/no-action response. Assert explicit non-action result, no
`AgentAction`, episode transition, state proposal, finding, or commit.

### action.decode-intent-T9 — decoding is side-effect free

Attach fail-on-call doubles for router, authorization, stores, datasets, sandbox, capabilities,
validators, and provider. Decode success and every failure path. Assert zero forbidden calls and no
scientific/authority mutation; only bounded decoding/rejection events are permitted.

### action.decode-intent-T10 — provider-neutral input only

Place recognizable provider-native sentinels beside an otherwise equivalent neutral response.
Assert action.decode-intent accepts only the neutral representation and no downstream typed field/type/branch
depends on native provider mechanics.

## Mutation-sensitivity check

**Mutation A:** Convert an action kind absent from the supplied schema set into `RunAnalysisAction`
with generated wrapper code.

**Expected test failure:** action.decode-intent-T3 and action.decode-intent-T5 become red because an unsupported request is invented
into a valid action instead of rejected.

**Mutation B:** Use the model-provided idempotency key as the authoritative replay identity.

**Expected test failure:** action.decode-intent-T7 becomes red because model content controls trusted identity and
changed requests can collide or impersonate a replay.

**Mutation C:** Replace model-claimed episode identity with the latest active episode.

**Expected test failure:** action.decode-intent-T6 becomes red because the typed action no longer preserves the
untrusted claim that action.authorize-request must evaluate.

## Composite dependencies

- **model.request-decision:** provides the public provider invocation and preserves open-ended intent.
- **model.normalize-response:** supplies provider-neutral untrusted responses.
- **action.authorize-request:** validates exact current identity/authority and routes permitted requests.
- **sandbox.authorize-execution/sandbox.execute-analysis:** later authorize and execute open-ended analysis under restricted capabilities.
- **research.continue-from-exploration:** later proves end-to-end creative analysis affects subsequent behavior through evidence.

These dependencies are named, not specified or locked here. action.decode-intent does not prove authorization or
execution.

## User decisions

The architecture owner approved:

1. Typing constrains request envelopes, not scientific content or creativity.
2. Schema-valid open-ended analysis code and arguments survive without narrowing or a known-method
   whitelist.
3. action.decode-intent checks against the exact action schemas supplied for the originating model call.
4. The harness, not the model, creates authoritative action and replay/idempotency identity.
5. Model-supplied target/session/episode identities remain untrusted claims; action.authorize-request checks them against
   authoritative current state.
6. action.decode-intent neither authorizes nor executes and performs no scientific mutation.
7. Unsupported actions fail explicitly rather than being helpfully translated into another action.

## Implementation/test handoff

Implement action.decode-intent-T1 through action.decode-intent-T10 as ordered red tests before production code for this seam. T2
protects creative content, T3/T5 prevent invented action translation, T6 preserves the action.decode-intent/action.authorize-request
authority boundary, and T7 protects transport/replay identity.

Forbidden shortcuts include latest-schema lookup, unknown-action conversion, scientific argument
rewriting, model-controlled idempotency, target substitution, permissive extra envelope fields,
finish-to-transition conversion, native-provider branching, and dispatch during decoding.

Action type hierarchy, validation library, schema format, identifier algorithm, failure class names
within the locked vocabulary, serialization, and decoding function/class layout remain free.

This handoff is specification only and does not authorize production code or executable tests.

## Status

**LOCKED — readiness level 4 of 5.**

Level 5 requires executable discriminating tests passing through the real production decoding path.
