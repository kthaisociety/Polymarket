# learning.publish-to-knowledge — validated Memory/Skill → KnowledgeEnvironment

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Publish approved learning for scoped retrieval without granting it universal or current authority.

## Relevant locked invariants

I13–I16, I24; KnowledgeEnvironment and slow learning.

## Source A

Exact validated object, applicability/scope/status/version/provenance, publication policy/environment.

## Destination B

Immutable indexed KnowledgeEnvironment entry with type, scope, current/superseded status, provenance, permissions and drill-down.

## Mapping f

Verify validated status and registry-issued publisher capability; publish exact content/metadata;
reject changed retry permissions or permission broadening; reconcile the one predecessor as superseded;
index structurally/semantically while preserving status and access controls.

## Must preserve

Memory/Skill identity/type/content, scope/applicability, caveats, evidence/provenance, version/currentness, permissions.

## May transform

Equivalent representation may change where semantic meaning, identity, status and observable behavior survive.

## Must exclude

Unvalidated/rejected lesson, universal prompt injection, caveat loss, latest overwrite, permission bypass, automatic state belief.

## Authority boundary

Publisher makes retrievable; retrieval/context decide relevance/permission; entry grants no action authority.

## Allowed state mutation

Create immutable knowledge entry/index/audit.

## Forbidden state mutation

No source mutation, direct context/state change, model-weight update.

## Failure semantics

Validation mismatch or unsafe scope/permission blocks publication; supersession explicit, not overwrite.

## Observable consequences

Validated lesson is retrievable only within scope and with caveats/status; out-of-scope query does not surface it as applicable.

## False-success implementations considered

Append all memories to every prompt; index rejected lessons as valid.

## Falsifying tests

Validated/rejected and in/out-of-scope pairs, supersession/currentness retrieval. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Ignore applicability and inject entry globally.

**Expected failure:** Out-of-scope test red.

## Composite dependencies

learning.promote-lesson; knowledge.retrieve-evidence retrieval; learning.influence-future-research feedback.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added publication-not-universal-authority and supersession.

## Remaining user decisions

None.
