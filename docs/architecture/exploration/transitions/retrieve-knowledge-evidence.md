# knowledge.retrieve-evidence — knowledge retrieval action + current authority → authorized relevant evidence

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Search broad machine-accessible knowledge while enforcing current scope, status, and permissions before substantive content is surfaced.

## Relevant locked invariants

I13–I16, I24; `STATE_CONTEXT_AND_MEMORY.md` retrieval hierarchy.

## Source A

Retrieval question/action, current task/episode/state, exact permissions/exposure/environment, source indexes/graphs, bounds and relevance policy.

## Destination B

Authorized ranked evidence set with substantive snippets/summaries, source identity, current/superseded/status/provenance, omissions and drill-down refs—or denial/unavailability.

## Mapping f

Resolve structural links first; otherwise search/synthesize; filter permission/currentness before content; rank relevant authorized material; return bounded meaning and refs.

## Must preserve

Query intent, source/evidence identity, status, provenance, temporal/environment scope, contradictions/caveats, authorization and rank rationale.

## May transform

Equivalent representation, bounded summarization, and implementation-specific types may change where semantic meaning survives.

## Must exclude

Protected/stale/unrelated content, semantic similarity overriding status, whole stores, opaque IDs only, source-less synthesis, permission after read, universal authority.

## Authority boundary

Model requests; harness retrieval controls access; sources own truth/status. Retrieval cannot promote or mutate belief.

## Allowed state mutation

Access/search audit and bounded result creation.

## Forbidden state mutation

No state/evidence/source/permission/exposure mutation.

## Failure semantics

Indeterminate permission/status fails closed; missing source explicit; no nearby/latest or stale-cache fallback.

## Observable consequences

Same query under allowed/denied or current/superseded sources yields correct differentiated evidence with zero denied reads.

## False-success implementations considered

Vector search first then filter; return top IDs; present superseded memo as current.

## Falsifying tests

Seed highly similar denied/stale decoys and less-similar current permitted evidence; assert only latter content. Revoke permission and assert zero reads. **Level A/C.**

## Mutation-sensitivity check

**Mutation:** Rank all content before authorization/currentness filtering.

**Expected failure:** Decoy test becomes red through denied/stale content.

## Composite dependencies

artifact.retrieve-authorized-content drill-down; knowledge.return-retrieved-evidence feedback; research.continue-from-exploration loop; learning.publish-to-knowledge/learning.influence-future-research validated learning later.

## Fundamentals review

`CONSISTENT`: broad access remains permission/status governed.

## Grill findings

Added adversarial relevance decoys and pre-read filtering.

## Remaining user decisions

None; search/ranking implementation remains free.
