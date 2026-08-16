# model.normalize-response — Provider-native response → normalized ModelResponse

Status: **LOCKED — readiness level 4 of 5**

## Purpose

model.normalize-response translates each provider's native response representation into the provider-neutral,
untrusted `ModelResponse` required by model.request-decision and consumed by action.decode-intent.

```text
OpenAI/native provider response ─┐
local/native provider response  ─┼→ provider adapter → neutral ModelResponse
future provider response        ─┘
```

It prevents provider wire formats, SDK classes, sessions, authentication objects, finish codes, and
error taxonomies from defining scientific/runtime behavior. It changes representation, never
scientific intent.

## Relevant locked invariants

- **I20 — Model provider is replaceable.** Runtime/scientific modules cannot depend irreversibly on
  native provider response, authentication, session, or transcript types.
- **model.request-decision — Context/action space → ModelResponse.** The public provider boundary preserves open-ended
  model-authored intent, grants no runtime authority, and produces zero or one untrusted action
  intent per M1 turn.

Authoritative sources: `MODEL_PROVIDER.md`, M1 runtime design/readiness, and model.request-decision.

## Source A

The source is one complete provider-native response or provider-native operational failure for an
exact logical model-call/attempt identity. Depending on the adapter it may contain:

- native assistant/text content supplied for the runtime;
- native tool/function/action call structures;
- string-encoded or structured arguments, including authored code;
- native finish/no-action codes;
- provider/model/request identity and usage/timing metadata;
- native error/status information;
- streaming chunks that must first form one complete response.

Provider client, credential, transport, session, and SDK objects may be available inside the adapter
but are not semantic response content and cannot become public output.

## Destination B

The destination is one provider-neutral, untrusted `ModelResponse` correlated to the exact logical
call. It represents:

- optional model-authored explanation/text when supplied and permitted;
- zero or one requested action intent for M1;
- exact action family/name and authored structured arguments/code/text;
- explicit finish/no-action status without transition authority;
- neutral provider/model/call and usage/timing metadata;
- or an explicit neutral operational/malformed-response failure.

It is not a typed `AgentAction`, authorization, execution result, observation, or scientific claim.

## Mapping f

```text
complete native response + exact call correlation
    → recognize provider-native envelope
    → decode native text/action/arguments/status/metadata
    → preserve authored semantic content
    → enforce neutral response cardinality and structural representability
    → map native operational status into neutral status
    → emit neutral ModelResponse or explicit normalization failure
```

For M1 action cardinality:

```text
zero native action intents → neutral no-action/finish representation
one native action intent   → one preserved neutral intent
multiple action intents    → explicit cardinality failure
```

model.normalize-response cannot select the first action, merge actions, or serialize them as multiple downstream turns.

## Must preserve

- logical model-call/attempt correlation;
- distinction between model-authored text, requested action, and finish/no-action intent;
- exact semantic action family/name;
- authored code, text, values, nesting, lists, intermediate structures, parameters, and
  structured-return requests;
- unfamiliar but structurally representable content inside the action arguments;
- provider/model identity and neutralizable operational metadata;
- native failure meaning without fabricating valid intent;
- untrusted status and absence of execution/transition authority.

Whitespace, JSON key ordering, SDK classes, envelope nesting, and provider-native field names need
not survive unless exact representation is itself part of an authored string argument such as code.

## May transform

- native envelope/SDK objects into neutral values;
- provider field names and nesting into neutral fields;
- JSON/string arguments into an equivalent structured representation;
- native finish/error/usage categories into documented neutral categories;
- streaming chunks into one complete response before normalization;
- provider-specific identifiers into neutral provenance metadata while retaining correlation.

## Must exclude

- provider SDK response/client/session/authentication/credential objects;
- native tool-call types used as downstream routing discriminators;
- secrets, tokens, headers, transport handles, or request clients;
- invented action names, arguments, code, finish intent, or scientific meaning;
- narrowing novel analysis into a known method;
- dropping unfamiliar structurally valid action content;
- automatic selection/merging of multiple action intents;
- partial/truncated stream content presented as a complete action;
- action decoding into domain `AgentAction`, authorization, execution, or state mutation.

## Authority boundary

- The provider produces native output but grants no runtime/scientific authority.
- The adapter may decode, map, correlate, and reject native representation.
- model.normalize-response cannot decide whether a neutral requested action is a valid domain action or currently
  authorized; action.decode-intent and action.authorize-request own those decisions.
- model.normalize-response cannot access data/capabilities or mutate task/session/state/episode/evidence.

## Allowed state changes

model.normalize-response may emit bounded operational normalization observability: provider/adapter version, call and
attempt identity, success/failure classification, response identity, and neutral usage metadata.

## Forbidden state changes

- no scientific/runtime state, episode, evidence, artifact, ledger, permission, exposure, or gate
  mutation;
- no capability, sandbox, tool, dataset, or protected-resource access;
- no action execution, authorization, routing, domain decoding, or semantic commit;
- no provider transcript/session promoted into scientific memory.

## Failure semantics

- Missing/malformed action name or arguments, invalid encoding, internally conflicting native
  fields, multiple action intents, unknown/unrepresentable response kind, or truncated stream yields
  explicit normalization failure.
- Native authentication, rate-limit, timeout, cancellation, capacity, transport, or availability
  failures map to neutral operational categories without fabricating an action.
- Failure preserves scientific state and does not choose a fallback provider/action inside model.normalize-response.
- Retrying provider calls is owned by model.request-decision/runtime policy; normalizing the same complete native
  response is deterministic and has no scientific side effect.

## Observable consequences

- Two different native formats carrying the same logical intent yield semantically equivalent
  neutral `ModelResponse`s.
- Custom open-ended analysis content survives adaptation even when the adapter does not understand
  its scientific purpose.
- Downstream code can operate entirely on neutral response types and never branch on provider SDK
  classes or native finish/tool-call shapes.
- Malformed, multiple, partial, or failed native output never appears as a valid action intent.

## False-success implementations considered

1. Return the native SDK response inside a nominal neutral wrapper.
2. Route downstream using native tool-call classes or finish codes.
3. Keep only recognized action arguments and discard unfamiliar fields.
4. Rewrite unknown analysis code into a supported diagnostic.
5. Select the first native action when several are returned.
6. Treat an interrupted stream's partial action JSON/code as complete.
7. Convert malformed output or provider failure into a default action.
8. Leak credentials, session, client, or request objects through metadata.

## Falsifying tests

All model.normalize-response tests are deterministic Level A adapter tests. They prove representation normalization,
not model reasoning, action validity, authorization, or execution.

### model.normalize-response-T1 — equivalent providers normalize to equivalent meaning

Create two substantially different native response shapes carrying the same explanation,
`run_analysis` intent, authored code, nested arguments, finish status, and logical call identity.
Assert semantically equivalent neutral `ModelResponse`s and no native-type dependence downstream.

### model.normalize-response-T2 — novel authored analysis survives losslessly in meaning

Normalize custom nonlinear code, unusual intermediate structures, uncommon parameters, and novel
structured-return fields. Assert every authored semantic survives; no known-analysis whitelist,
rewriting, or field deletion occurs.

### model.normalize-response-T3 — finish/no-action normalization grants no authority

Map representative native finish/no-action codes. Assert correct neutral status and zero episode
transition, state commit, action creation, or execution.

### model.normalize-response-T4 — native mechanics do not escape

Populate native response, client, authentication, session, headers, and provider-specific metadata
objects with recognizable sentinels. Assert none appear in public neutral fields or are required by
the downstream consumer; only explicitly neutralized operational metadata survives.

### model.normalize-response-T5 — malformed, conflicting, and multiple actions fail explicitly

Exercise missing action name, malformed/invalid arguments, conflicting native fields, unknown
unrepresentable kind, and two native action intents. Assert explicit normalization/cardinality
failure rather than selection, merging, repair, or default action.

### model.normalize-response-T6 — incomplete stream cannot become intent

Interrupt native streaming inside action arguments/code and assert no valid `ModelResponse` action
is emitted. Complete the stream and assert deterministic normalization of the complete content.

### model.normalize-response-T7 — provider failures map without fabricated intent

Map authentication, rate limit, timeout, cancellation, context capacity, transport, and unavailable
native failures. Assert the documented neutral operational category, exact call correlation, absent
action intent, and unchanged scientific state.

### model.normalize-response-T8 — normalization is side-effect free

Attach fail-on-call doubles to domain decoding, stores, data, sandbox, capabilities, router, and
validators. Normalize success and failure responses; assert zero forbidden calls/mutations and only
bounded operational normalization observability.

## Mutation-sensitivity check

**Mutation:** When more than one native action intent exists, normalize only the first.

**Expected test failure:** model.normalize-response-T5 becomes red because cardinality failure is replaced by a valid
neutral action.

## Composite dependencies

- **model.request-decision:** invokes replaceable intelligence and exposes the public neutral result.
- **action.decode-intent:** decodes the untrusted neutral result into a typed action or structured failure.
- **action.authorize-request:** authorizes/routes only a current typed request.

These dependencies are named, not specified or locked here. model.normalize-response does not prove end-to-end
creativity preservation or authority isolation by itself.

## User decisions

The architecture owner approved model.normalize-response as a self-explanatory technical adapter seam and delegated its
detailed completion within the already locked model.request-decision/provider-neutral architecture. The resulting
decisions are:

1. Provider mechanics may change representation but not model-authored scientific intent.
2. Native objects, sessions, authentication, credentials, and wire types never enter scientific or
   runtime-domain behavior.
3. M1 accepts zero or one action intent; multiple or partial actions fail explicitly.
4. Novel schema-representable content is preserved even when the adapter does not understand its
   scientific purpose.
5. model.normalize-response performs no domain decoding, authorization, execution, or scientific mutation.

## Implementation/test handoff

Implement model.normalize-response-T1 through model.normalize-response-T8 as ordered red tests before production code for this seam.
T1/T2 protect semantic/provider neutrality; T5/T6 protect failure/cardinality; T4/T8 protect type
and authority isolation.

Forbidden shortcuts include native-object wrappers, downstream native-type branching, recognized-
field-only normalization, helpful scientific rewriting, first-action selection, partial-stream
acceptance, guessed fallback intent, and credential/session leakage.

Provider SDK, adapter class/function layout, native schemas, streaming accumulator, JSON library,
neutral enum names, error hierarchy, and metadata field layout remain free where the locked public
semantics hold.

This handoff is specification only and does not authorize production code or executable tests.

## Status

**LOCKED — readiness level 4 of 5.**

Level 5 requires executable adapter tests passing through the production normalization path.
