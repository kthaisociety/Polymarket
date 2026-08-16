# Open Questions and Deferred Choices

These are intentionally **not** fully decided at handoff time. Codex should not interpret them as missing requirements that must be solved before the first vertical slice.

## 1. Implementation language and packaging

Python is a natural candidate because the research environment is scientific/time-series oriented, but the architecture does not depend on a language choice in this handoff.

Choose the minimal stack that supports the scientific Python ecosystem if starting from an empty repository, and document the choice.

## 2. Persistence technology

Logical boundaries are fixed; physical storage is not.

Initial implementation may use simple local files/in-memory stores if they preserve interfaces/invariants. Postgres/object storage/etc. should be earned by actual scale/concurrency needs.

## 3. Exact event taxonomy

Runtime events are required conceptually, but the complete enum/schema should evolve with observability needs.

Do not model every conceivable event up front.

## 4. Exact ResearchSession mechanics

We need a distinct execution/session identity for repeated attempts at the same `ResearchTask`, but exact lifecycle/status enums and transaction mechanics are implementation-level unless a failure mode requires stronger semantics.

## 5. Task clarification policy

`ResearchTask` may begin partially resolved. The exact mechanism by which unresolved target/horizon semantics trigger autonomous clarification vs user interaction should be learned from the first tasks.

Never invent missing semantics silently.

## 6. Standard scientific tool catalog

Keep `run_analysis` as the general escape hatch. Add typed tools only when repeated use shows they improve consistency/structured observations.

Do not prebuild a huge catalog.

## 7. Context budgeting algorithm

Priority classes and reconstruction semantics are architectural. Exact token budgets, retrieval thresholds, and ranking methods should be measured empirically.

## 8. Semantic state-commit detection

The semantic boundary is architectural; the exact mechanism may use model proposals plus harness validation, explicit action types, episode status, or a combination.

Behavioral evals should determine whether the mechanism produces premature or missing commits.

## 9. Research graph schema

Explicit IDs/lineage are preferred where relationships are known, but the exact graph/record schema should evolve with implementation.

## 10. Development-validation procedure

The kernel supports generic development validation. Exact CV/walk-forward policies are task-specific and should not be hard-coded globally.

Purging/embargo/CPCV are optional only when the target/label structure creates the relevant failure mode.

## 11. EvaluationSpec schema

It must support multidimensional, task-specific metrics/benchmarks/robustness checks. Exact field structure should emerge from the first insurance and market tasks.

## 12. Trial-count/multiple-testing formalism

Trial ancestry must be recorded. The exact statistical correction/PSR/DSR-like machinery is optional and should be introduced when justified by the research setting rather than universally.

## 13. Real provider authentication

Provider neutrality is fixed. Exact OpenAI subscription-auth/API/local-model adapters must follow currently supported provider mechanisms at implementation time.

Do not couple scientific modules to auth/session internals.

## 14. Network access in ResearchSandbox

Default should be restrictive. Whether specific research tasks can access external web/data APIs should be capability-based and explicit. Do not grant arbitrary network access merely for convenience.

## 15. UI

No UI architecture is required for the first kernel slice. Runtime events should make later UI/observability possible.

## 16. Reporting visual style

Presentation is intentionally flexible. Scientific substance is fixed upstream.

## 17. Slow learning timing

Hermes-style reflection/memory/skills are part of the architecture but should be implemented after the autonomous scientific kernel is behaving reliably.

## 18. Online learning / non-refit protocols

Default is refit at every decision time. Other protocols can be represented later through `TrainingProtocol` when a concrete use case requires them.

The evaluation scenario must provide explicit decision times. Whether those are represented by a list/iterator or eventually by a richer `SimulationClock` is an implementation detail; do not introduce a heavyweight clock abstraction by default.

## 19. Domain-exclusive downstream modules

Trading execution/allocation or insurance action policies sit after prediction/validated finding. Add them only as separate downstream capabilities when required.
