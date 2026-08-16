# Handoff Completeness Checklist

This checklist exists to make it easy to verify that the architectural work is represented in durable repository documents before implementation begins.

## Product and development philosophy

- [x] Generic time-series research kernel, not insurance-specific architecture.
- [x] Human owns architecture/test intent/verification; agent owns autonomous research execution.
- [x] Full architecture top-down; implementation bottom-up.
- [x] Complexity must be earned by concrete failure modes.
- [x] Avoid exhaustive pre-code micro-specification.
- [x] First target is a complete narrow autonomous vertical slice.

## Scientific kernel

- [x] Core objective `I_t -> y_(t+h)`.
- [x] `reference_time` vs `available_at`.
- [x] Six axioms A1-A6.
- [x] `Dataset` / schema / stable `FieldRef` semantics.
- [x] `TargetDefinition` and outcome maturity.
- [x] `FeatureDefinition` public abstraction vs internal expression/AST.
- [x] `FeatureSeries` vs `FeatureSet`.
- [x] Feature analysis separated from feature definition.
- [x] Fitted transforms obey temporal windows.
- [x] `ModelDefinition != FittedModel != ModelSelection`.
- [x] Ensemble semantics.
- [x] `PredictiveSystemDefinition` as frozen recipe.
- [x] Controlled `SystemTrainer` fitting boundary.
- [x] Development vs protected evidence distinction.
- [x] AFML used as failure-mode source, not doctrine.
- [x] Purging/CPCV optional only when problem structure warrants it.
- [x] PSR/DSR/trial-aware corrections treated as optional task-justified methods; trial ancestry always recorded.

## Backtest / evaluation / governance

- [x] `D -> I_t -> S_t -> W_t -> F_t -> prediction -> record`.
- [x] Default refit at every decision time.
- [x] New predictor information (`I_t`) distinguished from newly matured labels (`S_t`).
- [x] Decision times explicit; heavyweight `SimulationClock` not required by default.
- [x] `predict()` does not learn.
- [x] Invariant explicitly requires independent predictor-availability and label-maturity boundaries.
- [x] `BacktestRun` immutable simulation record.
- [x] `Evaluator` generic, `EvaluationSpec` task-specific.
- [x] `Validator` binary scientific promotion gate.
- [x] Protected backtest governance and exposure tracking.
- [x] Frozen identity/versioning.
- [x] No silent fallback.
- [x] Append-only ResearchLedger/trial ancestry; `EvidenceStore` may be an implementation naming/split, not a mandatory second abstraction.
- [x] `ValidatedFinding` as canonical scientific substance.
- [x] Flexible AI-driven report presentation cannot alter substance.
- [x] Prediction kept separate from downstream trading/allocation/business action.

## Agent runtime and authority

- [x] Autonomous research loop is the product runtime.
- [x] Model provider is replaceable intelligence, not outer architecture.
- [x] Free reasoning vs constrained execution vs privileged request vs forbidden authority.
- [x] AI may write arbitrary exploratory scientific code.
- [x] ResearchSandbox constrains information domain and side effects, not creativity.
- [x] Small deep action space with open-ended `run_analysis` escape hatch.
- [x] Typed scientific tools for repeated standardized operations.
- [x] Explicit privileged `request_*` paths.
- [x] Structured observations with progressive disclosure and artifact refs.
- [x] Structured failures keep concise typed errors in context while raw tracebacks/stdout/stderr remain drillable.
- [x] Sandbox roles explicitly cover capability policy, provenance recorder, resource limits, and structured return/result.
- [x] Runtime events distinguished from intelligence observations.
- [x] Exploratory/formal/governance failure classes.

## State, context, knowledge, learning

- [x] `R_t != C_t` for researcher state versus context; `S_t` remains the completed legal training sample.
- [x] Three layers: Trajectory, ResearchEpisode, ResearcherState.
- [x] `tool result != belief update`.
- [x] Semantic commit boundaries and StateUpdateProposal path.
- [x] State deltas/supersession rather than history rewrite.
- [x] Context built from state + episode + relevant evidence + permissions.
- [x] Broad machine knowledge access with selective working context.
- [x] Structural retrieval before fuzzy retrieval when explicit lineage exists.
- [x] Stale/superseded evidence handling.
- [x] Structured checkpoint compaction; full evidence remains external.
- [x] Context reconstruction completion test.
- [x] Context budgets use semantic priority classes, not fixed percentages.
- [x] Logical storage boundaries preserved; physical storage deferred.
- [x] Slow reflection -> CandidateLesson -> LessonValidator -> Memory/Skill loop.

## Testing

- [x] Tests treated as first-class design activity.
- [x] Contract/unit tests.
- [x] Scientific/governance adversarial tests.
- [x] Integration/vertical-slice tests.
- [x] Behavioral autonomous-agent evals.
- [x] Real failure -> regression test/eval -> fix discipline.
- [x] Publication-delay, target-maturity, global-fitting, frozen-fallback, protected-exposure, premature-state, stale-belief, retry-idempotency, predictor-vs-label-maturity, and structured-error drill-down fixtures.
- [x] Architecture owner retains test-intent/verification ownership.

## Integration contracts already specified

- [x] Contract 001 / mission.confirm-task: `UserMandate -> ResearchTaskProposal -> exact human confirmation -> ResearchTask`.
- [x] Contract 002: `ResearchTask + ResearchEnvironment -> ResearchRuntime.initialize -> ResearchSession + ResearcherState_0 + ResearchEpisode_0`.
- [x] Explicit decision not to micro-specify every later arrow before implementation.

## Codex handoff structure

- [x] Concise root `AGENTS.md`.
- [x] Deeper architecture documents referenced rather than copied into `AGENTS.md`.
- [x] `PLANS.md` execution-plan template for difficult multi-step work.
- [x] Goal/context/constraints/done-when prompt protocol.
- [x] Testing and review built into definition of done.
- [x] Open/deferred choices explicitly separated from locked decisions.
