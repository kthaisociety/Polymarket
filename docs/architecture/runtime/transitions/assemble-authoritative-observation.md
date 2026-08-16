# observation.assemble-authoritative-result — CapabilityExecutionResult + harness facts → authoritative StructuredObservation

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Convert capability content into bounded decision-relevant working evidence whose provenance comes from what the harness authorized and observed, not what the capability claims about itself.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I9, I13–I15, I17, I24.
- `docs/specification/DECISIONS.md`, Structured observations and Failure semantics.
- `docs/specification/MILESTONE_1_RUNTIME_DESIGN.md`, authorized execution and observation envelope.

## Source A

The capability result plus harness-owned action/authorization identities, actual data-view access/version, execution environment, timing/resource facts, status, warnings, raw diagnostics, and persisted artifact identities.

## Destination B

An authoritative `StructuredObservation` correlated to action and execution, with bounded substantive payload, status/type, safe summary, warnings, recoverability, harness provenance, and authorized artifact/drill-down references. “Authoritative” describes execution facts, not scientific truth or durable belief.

## Mapping f

Correlate trusted execution records; validate capability content against actual access; override or reject inconsistent self-reports; retain decision-relevant semantics; bound primary model-facing content; externalize large/raw/debug detail immutably; emit success or safe structured failure.

## Must preserve

- action, authorization, execution, dataset/environment, and observation identities;
- schema/field meaning, counts, coverage, missingness, preview, warnings, failure/recoverability;
- actual accessed resource/version and artifact lineage;
- provisional working-evidence status.

## May transform

- capability output into typed bounded payload/summary;
- raw diagnostics and large detail into immutable artifacts plus usable refs;
- native exceptions into safe failure vocabulary.

## Must exclude

Forged capability provenance, unbounded rows, raw traceback as primary content, fabricated scientific conclusion, unauthorized values, mutation instructions, implicit belief update, hidden success fallback, and opaque refs when the next decision requires substantive meaning.

## Authority boundary

The capability reports computation content. Harness instrumentation owns authorization/access/execution provenance and observation identity. episode.record-observation may persist the observation as episode evidence; only later validated commits can alter durable state.

## Allowed state mutation

Create the immutable observation, required artifacts, and append-only provenance/trajectory records coherently.

## Forbidden state mutation

No episode/state mutation, task change, permission grant, protected exposure, validation, promotion, or scientific claim acceptance.

## Failure semantics

Inconsistent result/provenance is rejected or corrected from harness facts with the discrepancy visible. Artifact persistence required to preserve omitted meaning must succeed before a healthy observation is published. Exceptions become safe structured failures with diagnostic refs; no raw traceback or fabricated empty success.

## Observable consequences

A lying capability cannot change recorded dataset/version. The next model can use bounded facts without loading the whole artifact, while authorized drill-down retains full detail. Failed execution remains explicitly failed.

## False-success implementations considered

- Copy capability-supplied provenance verbatim.
- Emit only `artifact_id` and “success.”
- Place the full dataset/traceback in primary context.
- Convert exception into empty successful result.
- Publish observation before required artifact/provenance records exist.

## Falsifying tests

1. Capability claims dataset/version X while harness access records Y; assert Y or explicit rejection, never X. **Level A/B.**
2. Supply result exceeding bounds; assert decision-relevant summary/payload plus authorized artifact ref, with full raw content absent from primary observation.
3. Throw a recognizable exception; assert safe failure/recoverability and diagnostic ref, not traceback or success.
4. Inject required artifact/provenance persistence failure and assert no healthy orphan observation.

## Mutation-sensitivity check

**Mutation:** trust capability provenance verbatim.

**Expected failure:** test 1 becomes red because forged X appears instead of harness-observed Y or rejection.

## Composite dependencies

data.inspect-authorized-view/sandbox.execute-analysis supply execution results; artifact.persist-output persists artifacts; episode.record-observation records working evidence; runtime.continue-from-observation/research.continue-from-exploration prove feedback; sandbox.record-provenance generalizes provenance.

## Fundamentals review

`CONSISTENT`. It preserves useful semantics and authoritative provenance without prematurely promoting an observation into belief.

## Grill findings

Resolved non-semantically: required coherent artifact/observation publication and made the “opaque ref instead of meaning” attack explicit.

## Remaining user decisions

None. Payload schemas, summarization implementation, and artifact technology remain free.
