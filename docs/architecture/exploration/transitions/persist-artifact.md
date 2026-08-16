# artifact.persist-output — large/raw/debug output → immutable artifact + ArtifactRef

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Keep model context bounded while preserving complete permitted output and diagnostics for later authorized drill-down.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I13–I15, I24.
- `docs/specification/DECISIONS.md`, Structured observations, Context/knowledge, Storage boundaries.

## Source A

Large permitted tables, plots, code, stdout/stderr, tracebacks, previews, or diagnostics plus exact producing action/execution/environment/data identities, content type, sensitivity, permission scope, and retention/provenance facts.

## Destination B

An immutable stored artifact with stable content identity and an `ArtifactRef` carrying enough metadata to identify meaning, provenance, authorization requirements, integrity, and available drill-down.

## Mapping f

Validate content scope; persist exact bytes/semantic object immutably; compute stable integrity identity; bind producer/environment/data/provenance and access classification; return ref only after artifact is retrievable through authorized path.

## Must preserve

Exact content, content type/shape, producer/action/execution, dataset/environment versions, timestamps, sensitivity/access classification, integrity, and relationship to the bounded observation.

## May transform

Encoding/compression/storage representation where round-trip meaning/integrity survives; create bounded preview metadata.

## Must exclude

Artifact as belief/evidence promotion, mutable overwrite, dangling ref, unauthorized values in ref metadata/preview, secrets, cross-session substitution, raw diagnostics as default context, and deletion through compaction.

## Authority boundary

Harness/artifact boundary may persist and classify; it cannot make content scientifically accepted or grant read access. artifact.retrieve-authorized-content authorizes retrieval.

## Allowed state mutation

Create immutable artifact, ref, provenance record, and append-only audit correlation.

## Forbidden state mutation

No episode/state/task/evidence/gate/exposure mutation or existing artifact rewrite.

## Failure semantics

Persistence/integrity/provenance failure yields no healthy ref and prevents any observation that depends on omitted detail from claiming complete drill-down. Exact duplicate content/request may converge; changed content gets new identity/conflict according to correlation.

## Observable consequences

The primary observation stays bounded; authorized retrieval round-trips the complete content and verifies integrity/provenance; later compaction does not destroy it.

## False-success implementations considered

- Store only a truncated preview.
- Return path/ID before durable persistence.
- Overwrite artifact at same ref.
- Put secret/traceback content in ref summary.
- Treat artifact creation as scientific promotion.

## Falsifying tests

1. Persist content larger than context bound; assert bounded observation/ref and exact authorized round-trip with integrity. **Level A/B.**
2. Attempt overwrite/cross-content identity reuse and assert immutable new identity or conflict.
3. Inject persistence/provenance failure and assert no usable dangling ref/healthy dependent observation.
4. Verify artifact presence creates no episode/state/evidence promotion.

## Mutation-sensitivity check

**Mutation:** persist only the bounded preview while returning a ref claiming full detail.

**Expected failure:** test 1 becomes red because round-trip bytes/shape/integrity differ.

## Composite dependencies

observation.assemble-authoritative-result/observation.translate-analysis-failure/artifact.persist-analysis-output produce artifacts; artifact.retrieve-authorized-content retrieves; context.build-packet surfaces bounded meaning/ref; context.checkpoint-episode compacts without deletion.

## Fundamentals review

`CONSISTENT`. Full evidence accessibility survives context bounds without confusing storage with epistemic authority.

## Grill findings

Resolved non-semantically: made ref publication contingent on retrievability and integrity, avoiding opaque/dangling-reference false success.

## Remaining user decisions

None. Storage/compression technology and retention implementation remain deferred.
