# sandbox.execute-analysis — AI-authored code + authorized capabilities/limits → sandbox execution result

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Execute genuinely open-ended exploratory computation while preventing access outside the granted information and side-effect domain.

## Relevant locked invariants

I1, I14, I17–I18, I24; `AUTHORITY_SANDBOX_AND_TOOLS.md` exploratory mode.

## Source A

Exact authored code/request, sandbox.authorize-execution capability context and data views, environment/library identity, random/resource limits, structured-return contract.

## Destination B

Execution result or explicit failure with structured return, stdout/stderr/artifact candidates, resource facts, and no authority claims.

## Mapping f

Run exact code in isolated environment exposing only granted capabilities; enforce time/memory/process/filesystem/network/secrets limits; capture outputs/errors; terminate safely; never reinterpret method.

## Must preserve

Code and input identity, authorized views, environment, seeds, result values/structures, status, warnings, resource usage.

## May transform

Equivalent representation, bounded summarization, and implementation-specific types may change where semantic meaning survives.

## Must exclude

Host/global stores, secrets, ungranted network/process/filesystem/data, protected content, silent code rewriting, unbounded output, scientific promotion, state writes.

## Authority boundary

Sandbox executes only grant; code cannot expand it. Harness controls isolation/termination; downstream seams establish provenance/observation.

## Allowed state mutation

Temporary workspace/resource use and declared artifacts; bounded execution telemetry.

## Forbidden state mutation

No authoritative store/permission/exposure/state/evidence mutation or undeclared persistent side effect.

## Failure semantics

Exception, timeout, resource exhaustion, malformed return, or policy violation yields explicit failure; partial output cannot masquerade as success. Same-meaning repair may retry; meaning changes are new action.

## Observable consequences

Novel permitted transformations/models run; forbidden file/network/secret/data probes fail; source data and stores remain unchanged.

## False-success implementations considered

Run code in host process with convention-based restrictions; rewrite unfamiliar code; return timeout partials as success.

## Falsifying tests

Adversarial code probes every denied channel while performing a novel permitted calculation; assert only granted data influences result, probes fail, limits terminate, and source/store hashes remain unchanged. **Level B.**

## Mutation-sensitivity check

**Mutation:** Expose host environment/filesystem and rely on prompt instructions.

**Expected failure:** Probe test becomes red through secret/file/process/network access.

## Composite dependencies

sandbox.authorize-execution grants; sandbox.record-provenance provenance; observation.assemble-analysis-result/observation.translate-analysis-failure observations; artifact.persist-analysis-output artifacts; research.continue-from-exploration loop.

## Fundamentals review

`CONSISTENT`: maximum computational creativity inside enforced information/side-effect boundaries.

## Grill findings

Added malicious probes, partial-result failure, and source immutability.

## Remaining user decisions

None; isolation runtime/library catalog remain implementation/configuration choices.
