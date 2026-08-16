# runtime.continue-from-observation — prior StructuredObservation → next model-visible ContextPacket

## Status

`CANDIDATE_CONSENSUS` — experimental composite contract, not canonical.

## Architectural purpose

Prove the fast autonomous loop is genuinely observation-driven: meaning learned by an authorized action becomes the only cause of a different next decision after persistence and context reconstruction.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I9, I13–I16, I20.
- Canonical context.build-packet, model.request-decision, observation.assemble-authoritative-result, and episode.record-observation semantics.
- `docs/specification/MILESTONE_1_IMPLEMENTATION_READINESS.md`, C1 and C2.

## Source A

Two fresh equivalent sessions whose first authorized actions produce observations differing only in a decision-relevant semantic, persisted into their exact active episodes.

## Destination B

Reconstructed next `ContextPacket`s, and a deterministic context-sensitive consumer's next typed actions, differ because that observation semantic crossed observation.assemble-authoritative-result → episode.record-observation → context.build-packet → model.request-decision/action.decode-intent.

## Mapping f

Execute first action; assemble observation; durably append working evidence; discard transient/provider context; rebuild the exact current packet; invoke one deterministic provider that can inspect only the packet; decode its next request. Compare paired outcomes.

## Must preserve

Observation payload/status/warnings/provenance, episode order/currentness, permission filtering, provider neutrality, and pre-commit state separation.

## May transform

The observation may become bounded episode evidence and then packet sections/summaries, provided the discriminating meaning remains usable.

## Must exclude

Provider transcript, direct dataset/capability/store/fixture access, session-specific hard-coded responses, hidden test globals, whole trajectory replay, unauthorized evidence, and implicit state mutation.

## Authority boundary

Local seams keep their existing owners. The composite test grants the downstream consumer no authority beyond reading `ContextPacket`; it observes decisions but does not itself commit them.

## Allowed state mutation

Only authorized execution records, observation/artifact/trajectory records, and episode working evidence. `ResearcherState` remains unchanged before a separately validated commit.

## Forbidden state mutation

No hidden state update, episode transition, or cross-session sharing used to create the differing next action.

## Failure semantics

If observation persistence, reconstruction, authorization filtering, or required semantics fail, the second provider call must not proceed as if it received evidence. Failure is explicit and repairable where defined.

## Observable consequences

With observation value 18, the packet-only consumer requests resolution; with value 2 it requests further investigation; missing/unparseable meaning produces a third sentinel outcome. Deleting only the observation payload collapses both to the sentinel and fails the test.

## False-success implementations considered

- Script the second action by call count.
- Let provider read the fixture or dataset directly.
- Preserve only observation ID while test reads original observation.
- Reuse transcript memory rather than rebuild context.
- Mutate durable state on first observation and read that instead.

## Falsifying tests

Run C1 and C2 with fresh isolated sessions, identical provider code, transcript deletion, fail-on-access stores/data/capabilities, and paired observations 18 versus 2. Assert different packet facts and actions, sentinel for absent payload, unchanged pre-commit `ResearcherState`, and no side channel. **Level C.**

## Mutation-sensitivity check

**Mutation:** drop observation payload during episode.record-observation/context.build-packet while retaining IDs and then choose the second action by scripted turn number.

**Expected failure:** the Level C test becomes red because both sessions take the sentinel branch; call order cannot select 18-versus-2 outcomes.

## Composite dependencies

Participating local seams: action.authorize-request–episode.record-observation plus canonical context.build-packet–action.decode-intent. This composite proves causal continuation that no local projection/persistence/provider test establishes alone.

## Fundamentals review

`CONSISTENT`. The paired intervention and side-channel exclusion prove the arrow, not endpoint sequence, while respecting observation/state separation.

## Grill findings

Resolved non-semantically: required fresh sessions, transcript destruction, a third missing-evidence branch, and fail-on-access source systems to exclude scripted/hidden causality.

## Remaining user decisions

None. The specific discriminating values and action names are fixtures, not architecture.
