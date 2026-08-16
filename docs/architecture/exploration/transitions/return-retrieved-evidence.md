# knowledge.return-retrieved-evidence — authorized retrieved evidence → StructuredObservation / active episode

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Return retrieved meaning and its current/superseded/provenance status to the research loop so retrieval can change decisions without becoming durable belief.

## Relevant locked invariants

I9, I13–I16; retrieval and observation rules.

## Source A

knowledge.retrieve-evidence authorized evidence set, retrieval/action identity, query, ranking/omission metadata, source status/provenance, drill-down refs.

## Destination B

Bounded retrieval `StructuredObservation` durably appended as provisional episode working evidence.

## Mapping f

Assemble substantive results/status/caveats/refs; correlate query and sources; append through episode.record-observation; expose in next context.build-packet context.

## Must preserve

Query, substantive snippets/facts, source identity, current/superseded/rejected status, provenance, contradictions, omissions/rank, refs.

## May transform

Equivalent representation, bounded summarization, and implementation-specific types may change where semantic meaning survives.

## Must exclude

IDs without meaning, source-less synthesis, status flattening, durable belief/state delta, unauthorized content, transcript-only result.

## Authority boundary

Retrieval supplies permitted evidence; episode stores provisional working evidence; later commits decide durable interpretation.

## Allowed state mutation

Observation/artifact/trajectory and episode append.

## Forbidden state mutation

No source/state/promotion/permission mutation.

## Failure semantics

Missing/unsafe result is explicit; episode append/reconstruction failure cannot acknowledge feedback; no “no evidence” from inaccessible evidence.

## Observable consequences

Two retrieved evidence sets differing only in substantive conclusion/status cause a packet-only consumer to choose different next actions.

## False-success implementations considered

Append only document IDs; summarize stale/current together; keep result only in transcript.

## Falsifying tests

Paired current-supporting versus superseded-contradicting evidence, fresh sessions, transcript deletion, no source access by provider; assert different next actions and unchanged state. **Level C.**

## Mutation-sensitivity check

**Mutation:** Persist only retrieval IDs and generic success.

**Expected failure:** Paired feedback test becomes red; consumer takes missing-evidence sentinel.

## Composite dependencies

knowledge.retrieve-evidence/episode.record-observation/context.build-packet; research.continue-from-exploration composite.

## Fundamentals review

`CONSISTENT`: the implied feedback mapping follows locked retrieval/episode semantics.

## Grill findings

Added current-versus-superseded causal discrimination and transcript destruction.

## Remaining user decisions

None.
