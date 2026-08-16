# Composite deterministic-test register

Status: **reviewed experimental candidates**. All assertions flow from architecture/invariants and the cited seams. Candidate seam contracts provide provisional detail and do not become canonical through this register.

## Register summary

| ID | Proposition | Seams | Invariants | Risk | Classification |
|---|---|---|---|---|---|
| observation-to-next-action | observation meaning causally changes the next typed action | observation.assemble-authoritative-result–runtime.continue-from-observation, context.build-packet–action.decode-intent | I9, I14–I16, I20 | HIGH | `DETERMINISTIC_COMPOSITE_TEST` |
| evidence-to-atomic-commit | authoritative evidence alone can produce one validated atomic semantic commit | commit.compose-request–trajectory.append-event | I9–I13, I25 | HIGH | `DETERMINISTIC_COMPOSITE_TEST` |
| registered-data-to-legal-fit | registered data becomes a fit using only legal independent predictor/label boundaries | data.register-observations–data.prove-temporal-substrate, training.fit-system | I1–I3, I23, I24, I26 | HIGH | `DETERMINISTIC_COMPOSITE_TEST` |
| feature-identity-to-prediction | exact feature/system identity governs fitting and prediction without learning | feature.define-identity–prediction.generate-record | I2–I6, I24 | HIGH | `DETERMINISTIC_COMPOSITE_TEST` |
| exploration-to-development-evidence | exploratory results influence formal objects and development evidence without implicit promotion | sandbox.authorize-execution–feature.revise-from-diagnostics, development.evaluate-candidate–ledger.record-trial-lineage | I1–I3, I6, I12, I13, I18 | HIGH | `DETERMINISTIC_COMPOSITE_TEST` |
| development-to-protected-authority | development evidence reaches protected values only through exact independent governance | freeze.assess-eligibility–backtest.bind-protected-view | I4, I5, I8, I13, I14, I22 | HIGH | `DETERMINISTIC_COMPOSITE_TEST` |
| frozen-system-to-immutable-run | an exact permit/frozen system/scenario yields a reconstructible immutable protected run | backtest.bind-protected-view–backtest.seal-run, training.fit-system–outcome.record-mature-label | I1–I7, I11, I21–I26 | HIGH | `DETERMINISTIC_COMPOSITE_TEST` |
| run-to-finding-or-rejection | immutable run evidence becomes an independent finding or retained rejection | evaluation.measure-run–ledger.preserve-scientific-history | I8, I11–I13, I19, I21 | HIGH | `DETERMINISTIC_COMPOSITE_TEST` |
| exposure-to-descendant-governance | protected exposure prevents descendants from claiming the same evidence fresh | formalization.version-material-change, ledger.record-trial-lineage, backtest.authorize-request, exposure.record-disclosure, ledger.record-negative-result–ledger.preserve-scientific-history | I7, I11, I12, I22 | HIGH | `DETERMINISTIC_COMPOSITE_TEST` |
| authorized-exploration-to-next-action | permitted open-ended computation/retrieval causally changes the next action | sandbox.authorize-execution–research.continue-from-exploration, observation.assemble-authoritative-result–runtime.continue-from-observation | I9, I14–I18 | HIGH | `DETERMINISTIC_COMPOSITE_TEST` |
| context-loss-reconstruction | context loss followed by reconstruction permits scientifically equivalent continuation | context.checkpoint-episode–evaluation.grade-research-behavior, context.build-packet–action.decode-intent | I14–I16, I20, I24 | HIGH | `DETERMINISTIC_COMPOSITE_TEST` |
| failure-to-repaired-continuation | recoverable failure is diagnosed and repaired without corrupting episode meaning | runtime.return-repairable-failure, observation.translate-analysis-failure, research.repair-exploratory-action, episode.record-observation–runtime.continue-from-observation, runtime.run-bounded-episode | I9, I12, I15, I17, I25 | HIGH | `DETERMINISTIC_COMPOSITE_TEST` |
| privileged-retry-idempotency | retry after uncertain privileged acknowledgement produces one irreversible effect | backtest.authorize-request–governance.retry-privileged-operation | I7, I8, I11, I25 | HIGH | `DETERMINISTIC_COMPOSITE_TEST` |
| finding-to-report-invariance | report variation cannot alter validated scientific substance | finding.publish-validated-claim, report.render-finding | I13, I19 | HIGH | `DETERMINISTIC_COMPOSITE_TEST` |
| validated-learning-to-future-behavior | validated learning changes appropriate future behavior without bypassing promotion | learning.reflect-history–learning.influence-future-research | I8, I11–I16, I24 | HIGH | `DETERMINISTIC_COMPOSITE_TEST` |

## observation-to-next-action — Observation-to-next-action causality

**System proposition `P(A) ⇒ Q(C)`.** If authoritative observation meaning differs while all other state is fixed, rebuilt context and the same packet-only deterministic provider produce the fixture-corresponding distinct typed actions.

**Path and traceability.** observation.assemble-authoritative-result→episode.record-observation→context.build-packet/runtime.continue-from-observation→model.request-decision→model.normalize-response→action.decode-intent; `DECISIONS.md` Structured observations, Research loops, State/context; I9 and I14–I16/I20.

**Oracle/world/outcome.** Two isolated episodes contain row-count 18 versus 2. Destroy transcripts, reload stores, rebuild packets, and let an identical provider map visible 18/2 to two declared actions. Assert substantive value at each intermediate, distinct final actions, and unchanged `ResearcherState`.

**Forbidden/false success/mutation.** No source-store, fixture, transcript, session-ID, or call-order side channel. Dropping payload but keeping its ID must take a third sentinel branch and fail intermediate and action assertions.

## evidence-to-atomic-commit — Evidence-to-atomic-semantic-commit

**Proposition.** Valid current evidence plus an exact proposal yields one independently validated atomic commit; invalid/foreign evidence yields no mutation.

**Path/basis.** commit.compose-request→commit.validate-proposals→commit.publish-boundary→commit.retry-idempotently/trajectory.append-event; I9–I13/I25; `STATE_CONTEXT_AND_MEMORY.md` Semantic commit boundaries.

**Oracle/world/outcome.** Pair equal proposals referencing current versus foreign evidence. Observe validator inputs, versioned state/episode/trajectory publication, and exact replay. Current commits all required records once; foreign commits none.

**Forbidden/false success/mutation.** No proposer self-validation, partial stores, latest-evidence substitution, or duplicate retry. Mutate coordinator to publish state before evidence validation; fault injection after each write must reveal and fail partial visibility.

## registered-data-to-legal-fit — Registered-data-to-legal-fit

**Proposition.** At each `t`, fitted state depends only on observations with `available_at≤t` and labels mature under `TargetDefinition`, through independently rebuilt `I_t`, `S_t`, and `W_t`.

**Path/basis.** data.register-observations→data.build-information-set/target.define-outcome→data.build-training-sample→data.select-training-window/data.advance-independent-clocks/data.prove-temporal-substrate→training.fit-system; I1–I3/I23/I24/I26; `DECISIONS.md` Backtest semantics.

**Oracle/world/outcome.** Two worlds are identical through `t` but radically differ afterward; fitted-state digest at `t` is identical. Independent release-only and maturity-only events change only `I_t` and `S_t` respectively.

**Forbidden/false success/mutation.** No row-date proxy, current vintage backfill, global preprocessing, or generic new-data flag. Admit future poison values or merge event flags; exact row/digest assertions fail.

## feature-identity-to-prediction — Feature-identity-to-prediction

**Proposition.** Exact frozen definitions compile/materialize/fit/predict according to their versioned meaning, and prediction cannot learn or silently substitute.

**Path/basis.** feature.define-identity→feature.compile-definition/feature.materialize-definition→feature.assemble-set→system.assemble-definition/formalization.version-material-change→training.fit-system→prediction.generate-record; I2–I6/I24; `DECISIONS.md` Dataset/feature and Model ontology.

**Oracle/world/outcome.** Pair two same-named feature versions with different lag semantics. Assert expression, series, set/system IDs, fit provenance, and predictions follow the exact selected version; repeated prediction leaves fitted digest unchanged.

**Forbidden/false success/mutation.** No latest-version lookup, name-only cache, fit during predict, or undeclared fallback. Mutating exact lookup to latest must swap the sentinel prediction and fail lineage assertions.

## exploration-to-development-evidence — Exploration-to-development-evidence

**Proposition.** An authorized exploratory result may causally inform an explicitly formalized candidate and legal development evaluation, but never becomes a formal object or durable conclusion automatically.

**Path/basis.** sandbox.authorize-execution–artifact.persist-analysis-output→formalization.create-candidate–feature.revise-from-diagnostics→development.evaluate-candidate–ledger.record-trial-lineage; I1–I3/I6/I12/I13/I18; `DECISIONS.md` escalating gates.

**Oracle/world/outcome.** Paired diagnostics favor versus falsify a candidate. Packet-only deterministic intent selects formalize versus reject; only explicit validation creates versioned definitions, while both trials and provenance enter history.

**Forbidden/false success/mutation.** No method catalog, exploratory-artifact promotion, hidden fit, or losing-trial deletion. Auto-promote every artifact mutation must fail formal identity and ledger assertions.

## development-to-protected-authority — Development-to-protected-authority

**Proposition.** Protected values are available only when an independently granted permit binds the exact frozen candidate, scenario, slice, caller, and current governance state.

**Path/basis.** freeze.assess-eligibility→freeze.seal-system→backtest.request-evaluation→backtest.authorize-request→backtest.bind-protected-view; I4/I5/I8/I13/I14/I22; `BACKTEST_AND_EVALUATION.md` Backtest governance.

**Oracle/world/outcome.** Correct permit yields the exact sentinel values; same permit with a different candidate/slice/caller yields zero values and safe denial. Fail-on-read data doubles establish pre-access authorization.

**Forbidden/false success/mutation.** No beneficiary authorization, bearer-token widening, or denial leak. Removing candidate binding must expose sentinel values and hard-fail.

## frozen-system-to-immutable-run — Frozen-system-to-immutable-run

**Proposition.** An exact permit, frozen system, and scenario produce the legal time-stepped record and one immutable `BacktestRun` without evaluation or learning outside legal windows.

**Path/basis.** backtest.bind-protected-view→backtest.execute-scenario using data.build-information-set–data.select-training-window/training.fit-system–outcome.record-mature-label→exposure.record-disclosure/backtest.seal-run; I1–I7/I11/I21–I26; `BACKTEST_AND_EVALUATION.md` execution flow.

**Oracle/world/outcome.** Hand-computable decision times include release-only and maturity-only events, failed fit, predictions, and later outcomes. Assert exact records, provenance, exposure at disclosure, and immutable run digest.

**Forbidden/false success/mutation.** No skipped failures, global fit, outcome-at-prediction, completion-only exposure, evaluation, or mutation. Poison future data and mutate fitter to full-history; fit/prediction sentinels fail.

## run-to-finding-or-rejection — Run-to-finding-or-rejection

**Proposition.** Immutable run evidence is measured by the predeclared spec and independently validated into either an immutable finding or retained rejection, without retraining.

**Path/basis.** backtest.seal-run→evaluation.measure-run→finding.validate-report→finding.publish-validated-claim/ledger.record-negative-result→ledger.preserve-scientific-history; I8/I11–I13/I19/I21; `BACKTEST_AND_EVALUATION.md` sections 8–13.

**Oracle/world/outcome.** Hand-computable accepted and rejected reports exercise the same validator. Assert exact metrics/slices/warnings, authority separation, finding substance for promotion, rejection history otherwise, and unchanged system/run digests.

**Forbidden/false success/mutation.** No evaluator fitting, scalar collapse, self-promotion, or rejected-record deletion. Let evaluator call fit; a fail-on-fit double must fail immediately.

## exposure-to-descendant-governance — Exposure-to-descendant-governance

**Proposition.** Once protected content is disclosed, any lineage descendant retains exposure and cannot claim the same period fresh.

**Path/basis.** exposure.record-disclosure→ledger.preserve-scientific-history→ledger.record-trial-lineage/formalization.version-material-change→backtest.authorize-request/ledger.record-negative-result; I7/I11/I12/I22; `BACKTEST_AND_EVALUATION.md` Exposure semantics.

**Oracle/world/outcome.** Pair descendant and unrelated candidate after a failed disclosed run. Descendant request is denied/marked exposed; unrelated lineage follows its independent governance facts. History retains failed run and exposure.

**Forbidden/false success/mutation.** No success-only exposure or candidate-ID-only lookup. Record exposure only on completion; the failure-after-disclosure fixture must wrongly permit descendant and fail.

## authorized-exploration-to-next-action — Authorized-exploration-to-next-action

**Proposition.** Different authorized analysis/retrieval meaning, passed only through structured observations and episode/context, causes different next action intent.

**Path/basis.** sandbox.authorize-execution–research.continue-from-exploration→episode.record-observation/runtime.continue-from-observation→context.build-packet–action.decode-intent; I9/I14–I18; `AUTHORITY_SANDBOX_AND_TOOLS.md`.

**Oracle/world/outcome.** Same unusual code/query returns two structured sentinel meanings. Transcript-free packet-only provider chooses declared follow-ups; provenance and drill-down remain authorized and accessible.

**Forbidden/false success/mutation.** No narrow method whitelist, raw stdout flood, ref-without-meaning, direct source access, or scripted turn sequence. Replace structured meaning with generic success; third sentinel action must expose failure.

## context-loss-reconstruction — Context-loss reconstruction

**Proposition.** After transient context disappears, durable state/checkpoint/evidence/permissions reconstruct the required scientific meaning so an identical deterministic provider continues equivalently.

**Path/basis.** context.checkpoint-episode→context.rebuild-after-loss→model.request-decision–action.decode-intent/evaluation.grade-research-behavior; I14–I16/I20/I24; `STATE_CONTEXT_AND_MEMORY.md` Compaction.

**Oracle/world/outcome.** Compare uninterrupted packet with packet rebuilt after transcript destruction. Required mission, plan, observations, unresolved status, versions, permissions, and refs match semantically; provider selects the same sentinel next action.

**Forbidden/false success/mutation.** No transcript dependency, stale status, permission widening, or opaque references. Drop unresolved question from checkpoint; provider must select a different sentinel and fail equivalence.

## failure-to-repaired-continuation — Failure-to-repaired-continuation

**Proposition.** A recoverable exploratory failure becomes diagnostic working evidence and permits a repaired action in the same episode without becoming scientific success or corrupting intent.

**Path/basis.** observation.translate-analysis-failure/runtime.return-repairable-failure→episode.record-observation/runtime.continue-from-observation→research.repair-exploratory-action→runtime.run-bounded-episode; I9/I12/I15/I17/I25; `DECISIONS.md` Failure semantics.

**Oracle/world/outcome.** Controlled code failure stores concise error plus drillable traceback; deterministic packet-only provider corrects the named defect. Episode identity/objective persist, trajectory keeps failure, state/finding stores remain unchanged.

**Forbidden/false success/mutation.** No swallowed error, fabricated observation, lost ancestry, broad semantic rewrite, or duplicate effects. Mark exception as success; sentinel repair branch disappears and assertions fail.

## privileged-retry-idempotency — Privileged retry idempotency

**Proposition.** Retrying an identical privileged request after acknowledgement loss converges on one decision/exposure/result; changed semantics under the same key conflict.

**Path/basis.** backtest.authorize-request–governance.retry-privileged-operation; I7/I8/I11/I25; `TEST_STRATEGY.md` Retry-idempotency fixture.

**Oracle/world/outcome.** Fault after effect commit but before response, then retry. Assert one protected read/exposure/run/ledger event and original result; changed candidate/slice under the key returns conflict with zero new effects.

**Forbidden/false success/mutation.** No response-cache-only idempotency or duplicate irreversible calls. Move key recording after response; injected timeout must yield two effect counters and fail.

## finding-to-report-invariance — Finding-to-report invariance

**Proposition.** Any permitted presentation variation preserves finding claim, status, caveats, metrics, provenance, and evidence meaning.

**Path/basis.** finding.publish-validated-claim→report.render-finding; I13/I19; `DECISIONS.md` Reporting.

**Oracle/world/outcome.** Render the same finding under multiple styles/audiences; parse a required machine-readable substance envelope and compare exact canonical fields/references.

**Forbidden/false success/mutation.** No omitted caveat, upgraded status, changed metric, or unsupported claim. A report fake dropping a sentinel caveat must fail exact substance comparison.

## validated-learning-to-future-behavior — Validated-learning-to-future-behavior

**Proposition.** Only independently validated, scoped lessons enter KnowledgeEnvironment and causally alter appropriate future context/action while rejected lessons remain history.

**Path/basis.** learning.reflect-history→learning.propose-lesson→learning.validate-lesson→learning.promote-lesson/ledger.record-rejected-lesson→learning.publish-to-knowledge→learning.influence-future-research; I8/I11–I16/I24; `STATE_CONTEXT_AND_MEMORY.md` Slow cross-task learning.

**Oracle/world/outcome.** With underlying provider fixed, compare no lesson, validated relevant lesson, rejected lesson, and validated superficially similar but out-of-scope lesson. Only the relevant validated lesson appears and triggers the declared different action; all provenance/status survives.

**Forbidden/false success/mutation.** Memory existence is not improvement; no self-promotion, rejected retrieval, scope erasure, or direct hidden access. Remove applicability scope; harmful-case action changes and fails.

## Composite batch review

### Fundamentals review

Overall verdict: `CONSISTENT` for observation-to-next-action–validated-learning-to-future-behavior. Every proposition is an exact composition of locked architecture plus cited seams; provisional seam detail is labeled. The tests constrain information, authority, identity, time, evidence, and side effects rather than scientific method. Objective deterministic oracles suffice. No new product gate or scientific threshold was introduced.

### Grill-with-docs findings and reconciliation

- Endpoint-only passes are blocked by intermediate propagation assertions, paired worlds, fail-on-access doubles, and mutation-specific red assertions.
- Scripted sequences are blocked by transcript destruction, fresh isolated worlds, third sentinel branches, and context-only consumers.
- Test-only generic paths are blocked by requiring the production-facing composition boundary once implemented; harness fakes supply only actors/worlds, never the mechanism under test.
- Circular facts are blocked by generator-owned truth and independently computed expected values.
- No LLM judge is used for these exact propositions.
- Retry, partial failure, stale/latest substitution, hidden fitting, permission widening, exposure timing, and losing-history deletion each have a named attack.

No issue required new semantics. `ARCHITECTURE_GAP`: none. `TEST_INSUFFICIENT`: none after reconciliation.

### Skill passes applied

- system-eval-design: applied
- fundamentals-review: applied to every HIGH-risk composite
- grill-with-docs: applied to every HIGH-risk composite

### Limits

These designs do not prove production mechanisms exist, real-model scientific quality, or numerical thresholds not fixed by upstream specifications. They do not canonicalize candidate seams.
