# observation.assemble-analysis-result — StructuredReturn/AnalysisResult + provenance → StructuredObservation

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Return decision-relevant exploratory facts to the loop while retaining provisional status and full provenance/drill-down.

## Relevant locked invariants

I9, I13–I17, I24; structured-observation and progressive-disclosure rules.

## Source A

Exploratory structured return/result plus sandbox.record-provenance harness provenance, status/warnings, actual access, artifacts, and epistemic classification.

## Destination B

Bounded provisional `StructuredObservation` with substantive numerical/semantic context, warnings, recoverability, provenance, and drill-down.

## Mapping f

Validate structured return; attach harness facts; preserve decision semantics; bound raw volume; externalize detail; explicitly mark exploratory/provisional.

## Must preserve

Values, units, sample/window/time, uncertainty, diagnostics, controls/protocol, caveats, status, actual provenance, refs, provisional role.

## May transform

Equivalent representation, bounded summarization, and implementation-specific types may change where semantic meaning survives.

## Must exclude

Naked scalar/success, forged provenance, unbounded stdout, promoted/formal status, subjective hard-coded conclusion, hidden failure, state mutation.

## Authority boundary

Research code reports; harness validates facts; observation informs episode but cannot become formal evidence/belief by itself.

## Allowed state mutation

Create observation/artifacts/audit coherently.

## Forbidden state mutation

No formal-object creation, validation/promotion, state commit, or permission change.

## Failure semantics

Malformed/inconsistent return becomes explicit failed observation; required omitted detail must remain drillable; no plausible fabricated summary.

## Observable consequences

Correlation 0.31 arrives with n/window/stability/caveats/provenance, not merely 0.31; next packet can distinguish results.

## False-success implementations considered

Return a scalar or “looks good”; label exploratory output validated; store only artifact ID.

## Falsifying tests

Pair equal headline statistic with different stability/sample/caveat; packet-only consumer chooses differently. Assert provisional status and actual provenance. Oversized output yields summary+ref. **Level C.**

## Mutation-sensitivity check

**Mutation:** Keep only headline metric and artifact ID.

**Expected failure:** Paired consumer test becomes red because both observations become indistinguishable.

## Composite dependencies

sandbox.execute-analysis/sandbox.record-provenance/artifact.persist-analysis-output; episode.record-observation/context.build-packet feedback; feature.revise-from-diagnostics/development.revise-candidate interpretation.

## Fundamentals review

`CONSISTENT`: preserves useful meaning without premature scientific commitment.

## Grill findings

Added paired same-headline/different-context causal test.

## Remaining user decisions

None.
