# observation.translate-analysis-failure — exploratory exception/stdout/stderr → concise failure observation + diagnostic artifact

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Make exploratory failure diagnosable and repairable without context flooding, secret leakage, or false success.

## Relevant locked invariants

I9, I12, I17–I18; exploratory failure and progressive disclosure rules.

## Source A

Exception/status, bounded safe execution context, stdout/stderr/traceback, sandbox.record-provenance provenance, sensitivity classification, action/episode identity.

## Destination B

Failed structured observation with safe type/reason/operation/recoverability plus immutable diagnostic artifact/ref.

## Mapping f

Classify/sanitize; preserve exact raw diagnostic in access-controlled artifact; emit concise truthful failure and repair context; append to active episode through normal path.

## Must preserve

Failure class, operation/code/execution identity, safe message/context, recoverability, provenance, artifact integrity.

## May transform

Equivalent representation, bounded summarization, and implementation-specific types may change where semantic meaning survives.

## Must exclude

Raw trace/secret in primary context, empty success, swallowed exception, auto-rewritten code, state mutation, deleted failed attempt.

## Authority boundary

Harness classifies/sanitizes; agent may propose repair; failure does not grant broader access.

## Allowed state mutation

Artifact/observation/trajectory/episode working evidence.

## Forbidden state mutation

No requested computation success, state/permission/promotion change.

## Failure semantics

If diagnostic persistence is required and fails, do not claim drill-down; sanitization must fail closed without erasing failure existence.

## Observable consequences

Agent can distinguish missing column from timeout via safe observation and retrieve permitted trace; secrets stay absent.

## False-success implementations considered

Dump traceback into prompt; catch all and return None/success; auto-fix code.

## Falsifying tests

Exceptions containing secret sentinel and long trace: primary observation is bounded/secret-free, artifact permissioned and exact where allowed; deterministic provider repairs based only on failure type. **Level C.**

## Mutation-sensitivity check

**Mutation:** Catch exception and emit successful empty result.

**Expected failure:** Status/repair test becomes red; provider takes sentinel path.

## Composite dependencies

sandbox.execute-analysis/sandbox.record-provenance/artifact.persist-analysis-output/runtime.return-repairable-failure/research.repair-exploratory-action.

## Fundamentals review

`CONSISTENT`: repair feedback remains truthful and bounded.

## Grill findings

Added secret sanitization and artifact-failure honesty.

## Remaining user decisions

None.
