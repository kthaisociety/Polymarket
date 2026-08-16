# runtime.return-repairable-failure — repairable runtime failure → safe StructuredObservation in active episode

## Status

`CANDIDATE_CONSENSUS` — experimental composite contract, not canonical.

## Architectural purpose

Return repairable provider, action, authorization, validation, or commit failure to the intelligence loop as truthful working evidence, without false success, corruption, terminalization, or governance bypass.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I6, I9, I12, I17, I25.
- `docs/specification/DECISIONS.md`, Failure semantics and Research loops.
- M1 repair companion and failure vocabulary.

## Source A

A classified repairable failure with exact operation/action/request/session/episode identity, safe explanation, recoverability, harness facts, and raw diagnostic detail designated for artifact storage.

## Destination B

A safe failed `StructuredObservation`, append-only rejection/attempt trace, and one ordered working-evidence entry in the still-active exact episode, available to the next reconstructed context.

## Mapping f

Classify failure without changing meaning; externalize unsafe/large diagnostics; assemble authoritative failed observation; append it idempotently to the exact active episode; reconstruct next context. Governance denial remains denial, not an automatically retryable technical fault.

## Must preserve

Exact failure class, affected intent and identity, recoverability, safe reason, diagnostic refs/provenance, unsuccessful status, attempt history, and current episode/state versions.

## May transform

Native exceptions/rejections into safe vocabulary and raw diagnostic artifacts; suggested repair may be explanatory but cannot silently alter the request.

## Must exclude

Fabricated success/default action, raw secrets/tracebacks in primary context, automatic scientific repair, state/lifecycle mutation, erased rejection history, duplicate effects, and authority denial relabeled as ordinary transient error.

## Authority boundary

Harness classifies and records observed failure. The model may propose a corrected new action; it cannot override denial or reuse old authority. Validators/coordinators retain their boundaries.

## Allowed state mutation

Append failure observation to active episode, diagnostics to artifact store, and attempts/rejections to trajectory. No durable belief.

## Forbidden state mutation

No requested effect, state commit, terminal transition, permission/exposure change, evidence promotion, or original-history rewrite.

## Failure semantics

If safe observation persistence fails, the turn cannot claim repair feedback was delivered. Terminal/foreign episode rejects append. Exact retry does not duplicate the observation. Non-repairable or governance failures retain their class and may block further action according to existing policy.

## Observable consequences

An invalid evidence reference leaves episode active and state unchanged; the next packet contains a bounded rejection explaining what can be corrected. A corrected request uses new semantic identity and can proceed without erasing the failed attempt.

## False-success implementations considered

- End the session on every malformed request.
- Convert failure to empty successful observation.
- Auto-fix the evidence ref and commit.
- Put raw traceback/secrets in model context.
- Record only the corrected attempt.

## Falsifying tests

1. Submit invalid evidence reference; assert no commit, active episode, unchanged state, failed observation in next packet, and retained rejection. **Level C** for next-action dependence.
2. Deterministic provider reads only failure observation and emits a corrected request; missing failure meaning takes a sentinel branch.
3. Governance denial stays `AUTHORITY_DENIED`, leaks no values, and is not auto-retried.
4. Diagnostic persistence/episode append failure cannot produce acknowledged repair feedback.

## Mutation-sensitivity check

**Mutation:** record rejection only in trajectory and omit it from episode/context.

**Expected failure:** tests 1–2 become red because the packet-only provider cannot produce the evidence-specific correction.

## Composite dependencies

model.normalize-response–action.authorize-request, commit.validate-proposals–commit.retry-idempotently produce failures; observation.assemble-authoritative-result/episode.record-observation assemble and persist them; context.build-packet/model.request-decision close feedback; trajectory.append-event/artifact.persist-output retain trace/detail; runtime.run-bounded-episode composes recovery.

## Fundamentals review

`CONSISTENT`. Repair preserves meaning and history without converting failure into authority or belief.

## Grill findings

Resolved non-semantically: distinguished governance denial from recoverable operations and required causal repair feedback rather than mere rejection logging.

## Remaining user decisions

None. Concrete retry limits remain runtime policy.
