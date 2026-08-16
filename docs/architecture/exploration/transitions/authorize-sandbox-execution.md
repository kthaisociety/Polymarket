# sandbox.authorize-execution — requested exploratory action + policy → sandbox authority / AuthorizedDataView

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Translate open-ended requested computation into least-authority data and side-effect capabilities without judging or narrowing its scientific method.

## Relevant locked invariants

I1, I8, I14, I18, I24; `AUTHORITY_SANDBOX_AND_TOOLS.md` ResearchSandbox and authority zones.

## Source A

Exact typed exploratory action, current session/episode/environment, capability policy, permissions, requested resources/code, and temporal/protected scope.

## Destination B

Explicit authorization/denial plus execution context containing only exact authorized data views, filesystem/process/network/resource capabilities, limits, and policy provenance.

## Mapping f

Validate current identities and request; compute least-authority capability grant before content access; bind grant to action/code/environment/time and exact views; deny explicitly. Never rewrite the computation into a preferred method.

## Must preserve

Authored code/arguments and requested outputs; exact identities; allowed dataset/field/time scope; limits; policy/version; denial reasons.

## May transform

Equivalent representation, bounded summarization, and implementation-specific types may change where semantic meaning survives.

## Must exclude

Raw unrestricted catalog/host/secrets/network, protected values, latest-target substitution, scientific-method whitelist, permission inferred from schema visibility, execution or state mutation.

## Authority boundary

Model requests; harness policy grants/denies; sandbox may consume only the bound grant. The requester cannot self-authorize.

## Allowed state mutation

Persist bounded authorization/audit records and short-lived capability context.

## Forbidden state mutation

No computation, content read before authorization, episode/state/evidence/exposure/policy mutation.

## Failure semantics

Unknown/stale target, denied resource, indeterminate policy, or unrepresentable least-authority context fails closed without data read or helpful substitution.

## Observable consequences

Two identical analyses under different permissions receive different grants; denial reads nothing; novel permitted code remains unchanged.

## False-success implementations considered

Build a broad context then ask sandbox code to behave; hide unfamiliar analyses; check policy after opening data.

## Falsifying tests

Pair permitted/denied actions with fail-on-read resources; assert exact grant/no read. Supply unusual code and assert byte/semantic preservation. Change only requested field/time/network capability and assert least-authority delta. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Create an unrestricted data context and rely on runtime code not to misuse it.

**Expected failure:** Permission test becomes red because denied/extra resources are reachable or read.

## Composite dependencies

action.authorize-request routes; sandbox.execute-analysis executes; sandbox.record-provenance records actual access; research.continue-from-exploration proves feedback.

## Fundamentals review

`CONSISTENT`: it restricts authority, not scientific imagination.

## Grill findings

Added pre-read authorization, exact capability-delta, and no-method-whitelist attacks.

## Remaining user decisions

None; capability representation and sandbox technology remain free.
