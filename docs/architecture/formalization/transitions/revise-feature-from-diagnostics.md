# feature.revise-from-diagnostics — FeatureAnalysis + interpretation → candidate revision/rejection/formalization decision

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Let diagnostics causally influence feature research while keeping analysis evidence distinct from the feature definition and recording trial ancestry.

## Relevant locked invariants

I9, I12–I13, I22, I24; feature analysis is not definition.

## Source A

Feature diagnostics/analysis with protocol, sample/time, uncertainty, caveats/provenance and active candidate/episode context.

## Destination B

Episode interpretation and explicit candidate decision: revise/new version, reject, continue, or request formalization, with ancestry and no automatic promotion.

## Mapping f

Persist analysis as evidence; rebuild context; model/harness records explicit decision and links evidence; formalization remains feature.define-identity.

## Must preserve

Diagnostic substance/status/protocol, candidate identity, rationale, ancestry, rejected paths.

## May transform

Equivalent representation may change where semantic identity and behavior survive.

## Must exclude

Metric-as-feature, automatic promotion, hidden protected evidence, state belief update, erased rejection, same-candidate meaning change.

## Authority boundary

Analysis informs; agent proposes; formalization/gates decide later.

## Allowed state mutation

Episode evidence, candidate status/new candidate, ledger trial entries.

## Forbidden state mutation

No direct definition mutation, freeze, state commit, protected promotion.

## Failure semantics

Insufficient/failed diagnostics block claimed decision; meaning-changing revision creates new candidate.

## Observable consequences

Stable versus fragile diagnostics cause different packet-only decisions.

## False-success implementations considered

Always formalize when correlation positive; overwrite candidate; hide instability.

## Falsifying tests

Paired same headline/different stability diagnostics, transcript loss, provider only packet; assert formalize vs revise/reject and ancestry. **Level C.**

## Mutation-sensitivity check

**Mutation:** Base decision only on headline correlation.

**Expected failure:** Paired Level C test turns red.

## Composite dependencies

observation.assemble-analysis-result/formalization.create-candidate/feature.define-identity/ledger.record-trial-lineage; context.build-packet feedback.

## Fundamentals review

`CONSISTENT`: implied feature loop follows locked evidence distinction.

## Grill findings

Added same-headline causal test and protected-status guard.

## Remaining user decisions

None.
