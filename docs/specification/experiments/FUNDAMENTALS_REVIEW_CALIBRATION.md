# Fundamentals-review calibration — model.request-decision and action.decode-intent

Date: 2026-08-13
Branch: `experiment/automated-seam-spec`
Mode: read-only review of locked contracts; no canonical seam or register edits

## Calibration purpose

Evaluate whether `fundamentals-review` detects project-level consistency and weak proof without becoming a second seam designer. The calibration applies the skill to two HIGH-risk locked seams and compares its results with the contracts' own challenge and mutation analysis.

## model.request-decision calibration

### Overall verdict

`CONSISTENT`

model.request-decision preserves exploration freedom while keeping information selection, execution, mutation, and governance authority in the harness; its tests distinguish local provider-boundary proof from later composite-loop proof.

### Reviewed proposition

`model.request-decision: decision-sufficient ContextPacket + expressive action schemas + model/call configuration -> untrusted provider-neutral ModelResponse`, with model-authored intent preserved and no runtime authority granted.

### Strong agreement

- Open-ended `run_analysis` and the prohibition on method rewriting preserve “constrain information and side effects, not creativity” (`docs/specification/DECISIONS.md`, Core scientific principle, Action/tool space, and Escalating epistemic gates).
- The provider receives only the permission-safe `ContextPacket`, not stores, capabilities, data, or governance handles (`docs/specification/INVARIANTS.md` I14, I18, and I20).
- Transcript independence preserves the state/context distinction and provider replaceability (`docs/specification/DECISIONS.md`, State/context architecture and Model provider/runtime).
- Explicit operational failure and logical-call retry identity address fabricated intent and duplicated downstream action (`docs/specification/INVARIANTS.md` I17 and I25).

### Test adequacy

- model.request-decision-T2 is causal: two otherwise identical decision surfaces produce different intent through a deterministic provider that can read only `C_t`. A context-ignoring provider becomes red.
- model.request-decision-T3 kills creativity narrowing that rewrites novel analysis or drops extensible fields.
- model.request-decision-T5 kills authority bypass with fail-on-access handles and zero-effect assertions.
- model.request-decision-T9 kills duplicate retry acceptance.
- The contract does not claim model.request-decision alone proves execution or the complete feedback loop.

### Subtlety the ordinary summary could miss

The broad action family is stable but not fictional: genuinely unavailable capabilities may be shown as unavailable, while schemas may not be dynamically shrunk merely to steer research.

### Scope discipline

- Correctly deferred: native normalization to model.normalize-response, typing to action.decode-intent, authorization to action.authorize-request, sandbox execution to sandbox.authorize-execution/sandbox.execute-analysis, and end-to-end feedback to research.continue-from-exploration.
- Unnecessary criticism rejected: a real-model Level D eval would test stochastic research quality, not model.request-decision's deterministic preservation/authority proposition.
- No new architecture concern was found.

### Limits

This review does not prove provider SDK integration, real-model behavior, downstream decoding, execution, or causal observation feedback. It did not modify model.request-decision or the seam register.

## action.decode-intent calibration

### Overall verdict

`TEST_INSUFFICIENT`

The contract is architecturally consistent, but action.decode-intent-T2 can remain green under a plausible decoder that supports generic open-ended content only through a special contract/test path while hard-coding production action kinds.

### Reviewed proposition

`action.decode-intent: untrusted neutral ModelResponse + exact advertised schema/call correlation -> typed AgentAction, no-action, or structured failure`, preserving scientific content while attaching harness-owned identity and granting no authority.

### Strong agreement

- Exact originating-schema validation prevents stale/latest-registry substitution and preserves call identity (`docs/specification/INVARIANTS.md` I16, I20, and I25).
- Harness-owned replay identity and untrusted target claims correctly leave currentness and authorization to action.authorize-request.
- Envelope validation leaves exploratory code and parameters open, matching the creativity gradient (`docs/specification/DECISIONS.md`, Action/tool space and Escalating epistemic gates).
- Structured rejection without repair, dispatch, or state mutation preserves explicit failure and `tool result != belief update` (`docs/specification/INVARIANTS.md` I9 and I17).

### [TEST_INSUFFICIENT] Test-only generic schema path can mask a hard-coded production decoder

- Source: `docs/specification/SEAM_REGISTER.md`, action.decode-intent row; `AGENTS.md`, Design style and Definition of done; `docs/specification/ALIGNMENT_AND_DIAGRAMS.md`, Stable project principles; `docs/architecture/runtime/transitions/decode-action-intent.md`, action.decode-intent-T2.
- Contract claim: typing constrains envelopes rather than scientific imagination, and a contract/test action schema may prove open-ended preservation before the sandbox action exists.
- Attack: implement a permissive decoder branch used only by the injected test schema, while the actual production registration/decoding mechanism remains a hard-coded switch over the two M1 actions.
- Consequence: T2 passes, yet the deep-action boundary cannot admit a later schema without decoder redesign. The test proves a fixture path rather than the production arrow's extensibility.
- Resolution owner: `non-semantic reconciliation`. Require the contract/test schema to enter through the same production schema-registration and generic decoding path used by M1 actions; no sandbox action or neighboring seam need be implemented.

### Test adequacy

- Violating mutation: add a test-only generic schema decoder while retaining a closed production action switch.
- Expected red test: revised action.decode-intent-T2 injects the contract schema through the real production schema mechanism and requires no action-kind-specific decoder branch. Current wording does not definitely make this mutation red.
- action.decode-intent-T3, T5, T6, T7, and T9 otherwise strongly cover exact schemas, no translation, preserved target claims, harness identity, and state-pure decoding.
- No Level C/D test is needed locally because action.decode-intent proves deterministic typing, not model reasoning.

### Subtlety the ordinary summary could miss

action.decode-intent must preserve a stale or foreign target as an untrusted claim rather than replacing it with the current episode. Otherwise action.authorize-request receives a laundered identity and cannot prove currentness.

### Scope discipline

- Correctly deferred: currentness/authorization to action.authorize-request, execution to sandbox.authorize-execution/sandbox.execute-analysis, and observation-driven behavior to research.continue-from-exploration.
- Unnecessary criticism rejected: rejecting stale targets here would collapse the action.decode-intent/action.authorize-request boundary; demanding sandbox execution in T2 would implement a neighboring seam.

### Limits

This review does not prove decoder implementation, action.authorize-request authorization, sandbox execution, or end-to-end research creativity. It did not modify action.decode-intent or the seam register.

## Comparative calibration result

- Agreement: both reviews matched the contracts on creativity, authority separation, provider neutrality, explicit failure, and local-versus-composite scope.
- Missed subtlety recovered: model.request-decision's broad-but-not-fictional actions and action.decode-intent's preservation of untrusted stale targets are project-specific requirements a generic checklist could flatten.
- New useful concern: action.decode-intent-T2 needs same-production-path wording to exclude a convincing test-only generic decoder.
- Unnecessary criticism avoided: no real-model eval demand at deterministic boundaries, no model.request-decision execution demand, and no action.decode-intent currentness/sandbox demand.
- Calibration verdict: the skill can return `CONSISTENT` when warranted and `TEST_INSUFFICIENT` for a surviving mutation without inventing new project semantics.
