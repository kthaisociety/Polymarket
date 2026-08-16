# Autonomous Runtime and Model Provider Boundary

## 1. Runtime ownership

The intended architecture is:

```text
our research harness = outer autonomous system
model provider        = replaceable intelligence inside it
```

Do **not** make Codex, Claude Code, or any one model-specific agent shell the irreplaceable outer architecture.

The harness owns:

- `ResearcherState`;
- `ResearchEpisode`;
- `ContextBuilder`;
- action/tool routing;
- ResearchSandbox;
- scientific tools;
- temporal/data permissions;
- governance gates;
- backtesting/evaluation;
- trajectory/ledger/provenance;
- slow memory/skill promotion.

The model owns:

- reasoning;
- hypothesis generation;
- planning;
- code generation;
- diagnosis;
- interpretation of permitted evidence;
- action/tool requests.

---

## 2. Provider-neutral boundary

The research runtime should depend on a neutral model interface conceptually like:

```text
ModelProvider.complete(
    ContextPacket,
    available_action_schemas,
    model_configuration
) -> ModelResponse
```

Exact API shape is deferred.

Canonical public provider-boundary contract:
`docs/architecture/runtime/transitions/request-model-decision.md`.

The caller must not depend on provider-specific authentication details or wire formats.

Provider implementations may include:

- OpenAI access using a legitimately supported subscription-auth flow where appropriate;
- OpenAI API-key usage;
- local model runtimes;
- future/other providers.

The scientific architecture must remain unchanged when the provider changes.

---

## 3. Pi-style integration intent

The desired user experience is similar in spirit to provider-aware systems such as Pi:

```text
research login / provider setup
→ authenticate provider
→ stored provider credentials/session according to supported mechanism
→ autonomous research runtime uses provider through ModelProvider
```

Important architectural point:

The research harness should call the model provider itself rather than requiring a human to sit in an interactive Codex session and supervise each action.

Exact OpenAI subscription-auth transport is an integration detail and must be implemented only through supported behavior/documentation. Do not invent a generic third-party ChatGPT OAuth API if one is not supported.

---

## 4. ModelResponse and AgentAction

Provider output should be normalized before the rest of the system consumes it. Canonical adapter
contract: `docs/architecture/runtime/transitions/normalize-model-response.md`.

Conceptually normalize:

- assistant/reasoning message needed by runtime;
- requested action/tool calls;
- structured arguments;
- finish/termination indication if any;
- provider usage/runtime metadata;
- provider error information.

Provider-specific response objects should not leak throughout scientific modules.

---

## 5. Autonomy requirement

The runtime should be capable of continuing:

```text
context
→ model
→ action
→ observation
→ context
→ model
→ ...
```

without human confirmation for ordinary permitted research actions.

Human interaction should be reserved for:

- the initial mandate where needed;
- explicitly configured external approval requirements;
- final review/consumption of findings;
- architecture/debugging/development work;
- genuinely unresolved user intent that cannot be resolved through the task/environment.

Scientific privileged gates are harness decisions, not routine human approval prompts.

---

## 6. Provider failures

Provider failures are operational failures and should return structured runtime status rather than corrupting research state.

Examples:

- auth expired;
- rate limit;
- transport timeout;
- malformed tool request;
- context limit;
- provider unavailable.

The runtime may retry/recover according to explicit policy, but must not duplicate irreversible scientific side effects merely because a model call was retried.

---

## 7. Context-window pressure

Provider context limits do not redefine durable system state.

If model context is lost/compacted, rebuild it from:

- `ResearcherState`;
- active research episode/checkpoint;
- relevant evidence;
- permissions/environment;
- core instructions.

Provider session transcript is a convenience, not the scientific source of truth.

---

## 8. Runtime events

Model operations should emit audit/runtime events such as:

```text
ModelCallStarted
ModelCallCompleted
ModelCallFailed
ActionRequested
```

These belong in trajectory/observability and do not automatically enter context.

---

## 9. Current implementation status

`src/research_agent/runtime/provider.py` contains both the retained deterministic
`ScriptedModelProvider` and an optional `OpenAICompatibleProvider`. The compatible adapter has no
mandatory provider SDK: it depends on an injected `HttpTransport`, includes a standard-library
`UrllibHttpTransport`, and resolves credentials through a `SecretResolver`. It sends the
authoritative bounded `ContextPacket` with an exact action schema, assigns a fresh logical identity
to each independent invocation, preserves that identity through bounded internal transient retry,
and rejects identity collisions, malformed or recursively schema-invalid actions, multiple-choice,
multiple-action, tool-free, oversized, or excessively nested responses rather than fabricating
intent. Private request diagnostics redact authorization values; credential echoes and native error
details cannot enter the neutral response or public exception chain.

Deterministic fake-transport tests establish serialization, normalization, secret confinement,
retry classification, typed-action compatibility, logical-call collision handling, bounded native
decoding, and context-reconstruction equivalence. A monkeypatched standard-library transport test
also proves bounded reads and native I/O-exception neutralization. This is production-shaped local
evidence, not live compatibility evidence: it does not establish that any live endpoint supports
the compatible envelope, honors idempotency headers, that a real credential works, or that a
particular model reliably chooses scientifically good actions. No model name is hardcoded by the
implementation; endpoint, model, timeout, retry bound, request/response byte bounds, response
nesting bound, and credential reference are explicit configuration. Provider-call journaling is
in-memory, and durable cross-process retry, backoff/`Retry-After`, streaming, cancellation, and live
cost/usage reconciliation remain deferred production work.
