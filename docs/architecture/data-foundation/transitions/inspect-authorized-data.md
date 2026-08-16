# data.inspect-authorized-view — authorized InspectDatasetAction + AuthorizedDataView → CapabilityExecutionResult

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Perform bounded read-only inspection against exactly the data view action.authorize-request authorized, without giving the capability a wider catalog, scientific authority, or mutation power.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I14, I18, I24.
- `docs/specification/DECISIONS.md`, ResearchSandbox, Action/tool space, Structured observations.
- `docs/specification/MILESTONE_1_RUNTIME_DESIGN.md`, inspect_dataset contract.

## Source A

An authorized `InspectDatasetAction`, exact authorization/execution identity, bounded requested semantic field IDs and preview size, and an `AuthorizedDataView` already scoped to the permitted dataset/version/fields.

## Destination B

A `CapabilityExecutionResult` containing computation facts from that exact view: schema/field semantics, row count, temporal coverage, missingness, bounded preview, status/warnings, and correlation. It is not yet authoritative provenance or a `StructuredObservation`.

## Mapping f

Validate request bounds against the supplied view; read only that view; compute deterministic descriptive facts; return bounded content and raw-detail candidates for observation.assemble-authoritative-result/artifact.persist-output. Never resolve the request through an unrestricted catalog.

## Must preserve

- action/authorization/execution identity;
- exact authorized dataset, version, schema, field identities, and requested bounds;
- values and descriptive facts as present in the authorized view;
- missingness and temporal semantics without reinterpretation.

## May transform

- rows into summaries, counts, coverage, missingness, and bounded previews;
- large permitted detail into content designated for artifact persistence.

## Must exclude

Unauthorized rows/fields/versions, protected values, secrets, writable stores, unrestricted catalog handles, unbounded dataset output, fitting, scientific conclusions, field substitution, network/filesystem side effects, episode/state mutation, and self-authored authoritative provenance.

## Authority boundary

action.authorize-request owns permission and constructs the least-authority view. data.inspect-authorized-view may compute only inside it. observation.assemble-authoritative-result combines result content with harness-observed access facts; the capability cannot certify its own provenance.

## Allowed state mutation

Resource consumption and bounded execution telemetry only. Source data and scientific/runtime state remain unchanged.

## Forbidden state mutation

No dataset, task, episode, state, evidence, artifact-store, exposure, permission, or promotion mutation. Artifact persistence belongs downstream.

## Failure semantics

Missing permitted data is `NOT_FOUND`; invalid fields/bounds are `INVALID_REQUEST`; inability to operate solely through the supplied view fails explicitly. Failure returns no forbidden data and cannot fall back to an unrestricted catalog or a neighboring dataset.

## Observable consequences

Inspection facts match only the authorized view, remain bounded, and leave the source byte/value identity unchanged. A denied or absent field is not silently replaced.

## False-success implementations considered

- Resolve `dataset_ref` from a global catalog despite receiving a scoped view.
- Read the whole dataset and truncate only the returned payload.
- Substitute a similarly named physical column.
- Fit a transform or infer scientific usefulness during inspection.
- Mutate cached/source rows while profiling.

## Falsifying tests

1. Supply an authorized view containing one dataset while an inaccessible decoy with the same friendly name exists globally. Prevent catalog access and assert all facts come from the view. **Level B.**
2. Compare source content identity before/after inspection and assert exact equality plus bounded preview.
3. Request missing/unauthorized semantic fields and assert explicit failure, zero decoy/protected reads, and no substitution.
4. Verify result contains facts but no scientific conclusion, fitted state, or authoritative provenance claim.

## Mutation-sensitivity check

**Mutation:** resolve the action's dataset reference through the unrestricted catalog rather than the supplied view.

**Expected failure:** test 1 becomes red because the fail-on-access catalog is touched or decoy facts appear.

## Composite dependencies

action.authorize-request supplies authority; observation.assemble-authoritative-result assembles authoritative observation/provenance; artifact.persist-output stores large output; runtime.run-bounded-episode exercises the composed turn.

## Fundamentals review

`CONSISTENT`. Least-authority execution preserves exploratory usefulness without granting general data or side-effect access.

## Grill findings

Resolved non-semantically: distinguished reading a bounded view from reading all data then truncating, and required semantic field identity rather than path/column coincidence.

## Remaining user decisions

None. Inspection algorithms, preview formatting, and in-memory representation remain free.
