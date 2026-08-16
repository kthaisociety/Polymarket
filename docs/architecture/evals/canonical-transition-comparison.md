# mission.confirm-task–action.decode-intent automated-review calibration comparison

Status: **calibration passed — broad consistency, useful critique, no systemic disagreement**

This is a read-only comparison. It does not regenerate, edit, or supersede the canonical contracts
under the block-local `docs/architecture/*/transitions/` directories.

## mission.confirm-task — UserMandate to confirmed ResearchTask

- **Automated conclusion:** `CONSISTENT`.
- **Agreement:** exact readback/confirmation authority, unresolved-versus-blocking ambiguity, stable environment identity, no research before confirmation, and idempotent publication all follow the locked mission and authority rules.
- **Missed subtlety recovered:** broad discovery is not satisfied by the first positive candidate; bounded exhaustion must disclose searched, rejected, inaccessible, and materially untested paths.
- **New useful concern:** none beyond the canonical false-success analysis.
- **Unnecessary concern rejected:** requiring every target/horizon detail before confirmation would improperly convert researchable uncertainty into blocking rigidity.
- **Test-strength disagreement:** none. mission.confirm-task-T4 proves the confirmation-carrying arrow rather than merely observing proposal then task.

## mission.evolve-direction — direction change to agenda evolution or task version

- **Automated conclusion:** `CONSISTENT`.
- **Agreement:** task identity is governed by semantic preservation of the confirmed main goal and hard constraints, not by mechanically detecting a new target, horizon, or objective field.
- **Missed subtlety recovered:** old sessions and evidence remain attached to their exact parent task even after a confirmed rescope.
- **New useful concern:** none; nuanced goal-preservation quality may later merit a behavioral eval, but deterministic authority outcomes remain testable locally.
- **Unnecessary concern rejected:** demanding human confirmation for every subordinate hypothesis would destroy the autonomous research loop.
- **Test-strength disagreement:** none. T1 and T3/T4 jointly kill both over-versioning and silent goal replacement.

## runtime.initialize-research — runtime initialization

- **Automated conclusion:** `CONSISTENT`.
- **Agreement:** initialization creates a coherent session/state-zero/episode-zero organism atomically, performs no research, preserves exact task/environment versions, and distinguishes retry from an independent attempt.
- **Missed subtlety recovered:** opaque task/environment IDs are insufficient if the starting position cannot reconstruct usable mission meaning.
- **New useful concern:** none.
- **Unnecessary concern rejected:** a model-generated opening plan is not needed for deterministic initialization and would contaminate epistemic zero.
- **Test-strength disagreement:** none. T1 is causal and T5 kills active half-session publication.

## context.build-packet — authoritative runtime records to ContextPacket

- **Automated conclusion:** `CONSISTENT`.
- **Agreement:** context is a bounded permission-safe projection of coherent authoritative truth, not transcript memory or durable belief; mandatory scientific meaning survives compaction.
- **Missed subtlety recovered:** bounded raw volume cannot become scientifically impoverished content. Decision-relevant coefficients, uncertainty, sample size, periods, protocol, caveats, status, and drill-down must remain usable.
- **New useful concern:** none beyond the already named composite dependencies runtime.continue-from-observation, artifact.retrieve-authorized-content, research.continue-from-exploration, and context.rebuild-after-loss.
- **Unnecessary concern rejected:** requiring full datasets or full trajectory in every packet would violate selective working context without improving evidence preservation.
- **Test-strength disagreement:** none. T2 and T4 are Level C/A-C arrow tests with side-channel exclusion.

## model.request-decision — ContextPacket/action schemas to ModelResponse

- **Automated conclusion:** `CONSISTENT`.
- **Agreement:** the model receives decision-sufficient context and a small deep action family while gaining no execution or governance authority; provider transcripts remain optional caches rather than memory.
- **Missed subtlety recovered:** broad actions may accurately report genuine unavailability, but must not be dynamically hidden merely to steer the agent through a preferred scientific path.
- **New useful concern:** none.
- **Unnecessary concern rejected:** Level D real-model evidence is not required to prove deterministic provider-boundary preservation and authority isolation.
- **Test-strength disagreement:** none. T2 proves context sensitivity, T3 protects unusual open-ended analysis, and T9 protects one accepted response per logical call.

## model.normalize-response — provider-native response to neutral ModelResponse

- **Automated conclusion:** `CONSISTENT`.
- **Agreement:** this is a representation adapter only; native types, sessions, credentials, partial streams, multiple actions, and provider failures cannot become valid domain intent or runtime authority.
- **Missed subtlety recovered:** exact authored strings such as code retain their textual representation even though ordinary envelope representation need not survive.
- **New useful concern:** none.
- **Unnecessary concern rejected:** scientific-method understanding inside the adapter would create provider coupling and premature restriction.
- **Test-strength disagreement:** none. T5/T6 kill first-action and partial-stream false success.

## action.decode-intent — neutral ModelResponse to typed AgentAction

- **Automated conclusion:** `TEST_INSUFFICIENT`.
- **Agreement:** typing constrains the request envelope rather than scientific imagination; harness-owned replay identity, exact originating schemas, untrusted target claims, and no dispatch/currentness preserve the action.decode-intent/action.authorize-request boundary.
- **Missed subtlety recovered:** a stale or foreign target must survive as an untrusted claim so action.authorize-request can reject it; replacing it with the current episode would launder identity.
- **New useful concern:** action.decode-intent-T2 permits a contract/test action schema before the production `RunAnalysisAction` exists, but does not explicitly require that schema to enter through the same production registration and generic decoding path as M1 actions.
- **Unnecessary concern rejected:** action.decode-intent must not perform action.authorize-request currentness checks or sandbox execution merely to strengthen local proof.
- **Test-strength disagreement:** a plausible test-only generic decoder plus hard-coded production switch can keep current T2 green. The eventual red test must inject the schema through the real production decoder mechanism. This is a non-semantic test strengthening, not an architectural redesign.

## Calibration gate result

The automated review preserves the manually established creativity gradient, authority boundaries, state distinctions, identity/version rules, provider neutrality, explicit failure semantics, and local-versus-composite test scope. The sole material disagreement reproduces the useful known action.decode-intent test concern. There is no broad or systemic conflict with locked fundamentals, so the experiment may proceed to action.authorize-request.
