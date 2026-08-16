# artifact.retrieve-authorized-content — permitted ArtifactRef/evidence ref → authorized drill-down content

## Status

`CANDIDATE_CONSENSUS` — experimental implied-gap contract, not canonical.

## Architectural purpose

Make progressive disclosure real: recover the useful semantics behind a reference while rechecking current authority and preserving identity/provenance, rather than treating an opaque ID as evidence or as permanent permission.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I13–I16, I24.
- `docs/specification/STATE_CONTEXT_AND_MEMORY.md`, drill-down and broad access/selective context.
- `docs/specification/DECISIONS.md`, Context/knowledge and Structured observations.

## Source A

A model-requested permitted artifact/evidence reference, exact current session/episode/environment/permission/exposure state, requested bounded slice/view, and immutable referenced record metadata.

## Destination B

Authorized substantive drill-down content or safe denial/unavailability, with exact ref/content identity, current/superseded/epistemic status, provenance, bounds, and any deeper permitted references.

## Mapping f

Resolve exact immutable reference without latest/neighbor substitution; re-evaluate current permission and epistemic status; select requested authorized portion; verify integrity/provenance; return substantive bounded content through the observation loop. Reference possession alone grants nothing.

## Must preserve

Exact content/artifact/evidence identity, integrity, producer/environment/data provenance, current/superseded/rejected/protected status, requested slice, omissions/bounds, and authorization decision.

## May transform

Bytes/tables/plots into bounded authorized views or structured summaries while retaining an avenue to permitted underlying detail.

## Must exclude

Permission inferred from ID possession, protected/stale content leakage, latest-version substitution, ref-only “success,” cross-session artifact confusion, status promotion, unrestricted download, secrets, and mutation.

## Authority boundary

The model requests. Harness retrieval rechecks authority against current truth. Artifact/evidence stores provide immutable content but cannot grant access. Returned content is observation, not belief.

## Allowed state mutation

Append access/retrieval events and, where architecture requires, protected exposure only through its dedicated governed seam—not implicitly here. Produce a `StructuredObservation` through observation.assemble-authoritative-result/knowledge.return-retrieved-evidence.

## Forbidden state mutation

No artifact/evidence rewrite, permission grant, state commit, finding promotion, or silent exposure mutation.

## Failure semantics

Unknown ref is `NOT_FOUND`; denied ref is `AUTHORITY_DENIED` without existence/value leakage beyond permitted metadata; integrity/version mismatch is explicit; revoked permission fails even if prior packet showed the ref. No fallback to nearby/latest content.

## Observable consequences

Two refs with different permitted content yield different returned substantive observations to a ref-blind consumer; denial reads zero content. Revocation between packet and retrieval prevents access.

## False-success implementations considered

- Return “artifact exists” plus same ID.
- Treat unguessable IDs as authorization.
- Resolve latest artifact by friendly name.
- Read content before checking permission.
- Strip current/superseded/provenance status.

## Falsifying tests

1. Pair refs containing discriminating values; retrieval consumer has no store access and chooses differently from returned content. **Level C.**
2. Allowed then revoked permission: second retrieval denies with zero content reads.
3. Introduce newer/similarly named artifact; exact old ref still resolves old content and provenance.
4. Corrupt content/integrity and assert explicit failure, not stale cache/nearby fallback.

## Mutation-sensitivity check

**Mutation:** treat possession of `ArtifactRef` as sufficient authorization and read before policy check.

**Expected failure:** test 2 becomes red because revoked content is read or returned.

## Composite dependencies

artifact.persist-output/artifact.persist-analysis-output create artifacts; context.build-packet advertises permitted drill-down; observation.assemble-authoritative-result/knowledge.return-retrieved-evidence return observations; runtime.continue-from-observation/research.continue-from-exploration prove feedback; backtest.bind-protected-view/exposure.record-disclosure govern protected data exposure when applicable.

## Fundamentals review

`CONSISTENT`. The implied mapping follows uniquely from locked progressive-disclosure, permission, provenance, and non-belief principles; no new architecture choice is required.

## Grill findings

Resolved non-semantically: required current authorization before any content read, exact identity rather than latest lookup, and a causal useful-semantics test.

## Remaining user decisions

None. View/slicing APIs and physical retrieval technology remain free.
