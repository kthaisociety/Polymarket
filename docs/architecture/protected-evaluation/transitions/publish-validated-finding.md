# finding.publish-validated-claim — promoting decision + canonical evidence → immutable ValidatedFinding

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Preserve exact scientific substance of a promoted claim so later presentation cannot alter status, caveats, evidence or meaning.

## Relevant locked invariants

I11, I13, I19, I24.

## Source A

Exact PROMOTE decision, report/run/frozen target/system, claim synthesis constrained by evidence, caveats, provenance/trials/exposure.

## Destination B

Immutable ValidatedFinding with canonical claim, target/horizon, identity, metrics/robustness/caveats, evidence refs, trial context and validation status.

## Mapping f

Verify decision/input correspondence; derive/copy only evidence-supported substance; require caveats/provenance; seal finding.

## Must preserve

Claim scope, target/horizon, system, metrics, robustness, caveats, evidence/trials/exposure, decision/authority.

## May transform

Equivalent representation may change where exact scientific meaning, identity and behavior survive.

## Must exclude

Overclaim, omitted caveat, unsupported causal language, report wording authority, rejected decision, mutable finding, economic action.

## Authority boundary

Validation authorizes finding creation; builder cannot expand conclusion; reporter only presents later.

## Allowed state mutation

Create finding/ledger record.

## Forbidden state mutation

No run/report/decision rewrite, business action, memory promotion.

## Failure semantics

Missing correspondence/caveat/evidence or unsupported claim blocks finding; correction creates superseding record.

## Observable consequences

Finding reconstructed without report prose retains exact conclusion/status/caveats.

## False-success implementations considered

Copy only headline metric; AI invents broader causal claim; omit instability caveat.

## Falsifying tests

Adversarial report with strong headline but critical caveat; require caveat and bounded claim. Rejected decision cannot create. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Generate claim from headline metric while dropping caveats.

**Expected failure:** Substance/caveat test red.

## Composite dependencies

finding.validate-report; report.render-finding reporting; ledger.preserve-scientific-history ledger; learning.reflect-history reflection.

## Fundamentals review

`CONSISTENT`.

## Grill findings

Added evidence-supported claim boundary and supersession.

## Remaining user decisions

None.
