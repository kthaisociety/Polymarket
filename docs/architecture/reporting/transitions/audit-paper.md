# report.audit-paper — declared evidence bundle → publication decision

## Status

`CANDIDATE_CONSENSUS` — implemented for deterministic receipt-backed papers.

## Architectural purpose

Prevent a manuscript from omitting trials, overstating evidence status, ignoring dependence or
multiplicity, or converting sampled-price research into causal or executable trading claims.

## Relevant locked invariants

I7, I8, I11-I13, I17, I19, I21-I22, and I24; reporting has no validation or promotion authority.

## Source A

Exact campaign directories and hashes, complete claim declarations, registered statistical tests,
dependence-aware intervals, robustness references, execution evidence, and a fixed paper protocol.

## Destination B

A content-addressed `PaperAuditReport` with a complete trial inventory, adjusted tests, per-claim
checks, an overall publication decision, and exact evidence references.

## Mapping f

Independently verify campaign manifests, executions, completions, and receipt identities; inventory
every execution; adjust registered confirmatory tests within their declared families; apply
non-configurable evidence requirements by claim kind; and reject publication when any asserted
claim fails.

## Must preserve

Campaign evidence tier, exposure, disposition, rejected trials, exact source and receipt identity,
statistical unit, uncertainty method, multiplicity family, caveats, and execution-data limitations.

## May transform

Equivalent representation may change where the same checks, ordering, identities, and decision
remain reconstructible.

## Must exclude

Scientific promotion, protected-data exposure, fitting or candidate selection, caller-defined
weakening of claim requirements, omitted trials, inferred execution quality, and prose-authored
status changes.

## Authority boundary

The auditor may accept or reject a declared paper for publication under its exact bounded wording.
It cannot accept a scientific finding, restore evidence freshness, or decide economic usefulness.

## Allowed state mutation

Create immutable audit, inventory, and generated-paper artifacts.

## Forbidden state mutation

No mutation of campaigns, evidence, exposure, validation decisions, findings, protected stores, or
research state.

## Failure semantics

Missing, conflicting, unverifiable, incomplete, or underpowered required evidence is a failed check;
it never becomes a warning-only pass.

## Observable consequences

Dropping an execution, changing receipt bytes, removing multiplicity membership, using row-level
uncertainty for an event-dependent claim, or asserting profitability without executable evidence
changes the audit to `REJECT`.

## False-success implementations considered

Trust caller-declared tiers; count rows as independent; adjust only the winning hypothesis; accept a
paper because its caveats are eloquent; treat a fixed cost haircut on sampled marks as execution.

## Falsifying tests

Exact campaign round trip, receipt-byte mutation, omitted execution, duplicate-analysis inventory,
Holm-family mutation, missing event interval, missing robustness, unfrozen replay, causal wording,
and sampled-mark profitability. **Level A/B/C.**

## Mutation-sensitivity check

**Mutation:** Change an accepted replicated-prediction claim to a trading claim without adding
historical quote, latency, fee, depth, and fill evidence.

**Expected failure:** Execution-evidence and evidence-tier checks turn red and publication rejects.

## Composite dependencies

Research campaign execution/completion and retained statistical evidence; no dependency on
`finding.publish-validated-claim` is required for accurate development or negative-result papers.

## Fundamentals review

`CONSISTENT`: this is a reporting-integrity decision, not scientific promotion.

## Remaining user decisions

None.
