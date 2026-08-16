# sandbox.record-provenance — actual sandbox access/execution/artifacts → execution provenance record

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Record what code actually ran and what it actually accessed so exploratory outputs remain auditable despite untrusted code self-report.

## Relevant locked invariants

I11, I13, I18, I24; `AUTHORITY_SANDBOX_AND_TOOLS.md` provenance for code execution.

## Source A

Harness-observed code/source hash, authorization grant, actual data/field/time accesses, environment/libraries, seeds, resources, status/errors, and generated artifact identities.

## Destination B

Immutable provenance record correlated to action/execution/result with actual access lineage and reproducibility metadata.

## Mapping f

Assemble from harness instrumentation; reconcile requested versus actual; reject/flag inconsistency; publish coherently with result/artifacts.

## Must preserve

Action/code/environment/data/vintage/view IDs, actual ranges/fields, seeds, libraries where practical, status/errors, artifact refs, times/resources.

## May transform

Equivalent representation, bounded summarization, and implementation-specific types may change where semantic meaning survives.

## Must exclude

Code-authored provenance as authority, requested access presented as actual, secrets, mutable overwrite, fabricated success, scientific validity claim.

## Authority boundary

Harness instrumentation owns facts; code/capability may supply hints only. Recorder cannot authorize or promote.

## Allowed state mutation

Append immutable provenance/audit record.

## Forbidden state mutation

No state/evidence/gate/permission/exposure mutation or result rewriting.

## Failure semantics

Missing required instrumentation or inconsistent identity blocks consequential observation as provenance-complete; no guessed provenance.

## Observable consequences

Code claiming dataset X while instrumented access is Y yields Y/discrepancy, never X; record survives reconstruction.

## False-success implementations considered

Log request metadata rather than actual access; trust code return; omit environment/seeds.

## Falsifying tests

Code requests X but accesses authorized Y through alias and self-reports X; assert actual Y. Vary seed/environment/data version and assert distinct lineage. Inject recorder/artifact failure and assert no provenance-complete success. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Copy requested dataset list as actual-access provenance.

**Expected failure:** Alias/access test becomes red because X is recorded instead of Y.

## Composite dependencies

sandbox.authorize-execution/sandbox.execute-analysis; observation.assemble-analysis-result observation; artifact.persist-analysis-output artifacts; ledger.record-trial-lineage/ledger.preserve-scientific-history later lineage.

## Fundamentals review

`CONSISTENT`: authoritative provenance follows actual execution without upgrading epistemic status.

## Grill findings

Added request-versus-actual deception and coherent publication.

## Remaining user decisions

None.
