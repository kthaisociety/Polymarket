# provider.authenticate-adapter — supported provider credentials/config → authenticated provider adapter/session

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Establish operational model access without leaking credentials or provider sessions into runtime/scientific objects.

## Relevant locked invariants

I14, I20; provider/runtime decision.

## Source A

Supported provider configuration, credential source/refresh authority, model settings, transport policy.

## Destination B

Authenticated adapter/session behind neutral ModelProvider or explicit operational failure, with secrets confined.

## Mapping f

Validate supported auth method; load/refresh credentials inside adapter; establish client/session; expose only neutral interface/metadata.

## Must preserve

Provider/model/config identity, supported settings, auth status/expiry and safe operational provenance.

## May transform

Equivalent representation may change where semantic meaning, identity, status and observable behavior survive.

## Must exclude

Secrets/tokens/client/session in context/state/response, guessed unsupported subscription auth, scientific dependence on session, silent provider switch.

## Authority boundary

Credential manager/adapter own auth; scientific runtime sees neutral interface only.

## Allowed state mutation

Operational session/cache and safe audit.

## Forbidden state mutation

No task/state/evidence/permission/scientific mutation.

## Failure semantics

Expired/unsupported/denied auth explicit; refresh does not duplicate model effects; no fallback provider unless configured.

## Observable consequences

Delete session and reauthenticate without changing scientific objects; secret sentinels never escape adapter.

## False-success implementations considered

Put token/client in ContextPacket; use undocumented auth transport; silently switch provider.

## Falsifying tests

Secret-sentinel serialization scans, adapter replacement, expiry/refresh and unsupported-auth failures. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** Return authenticated client object as neutral provider.

**Expected failure:** Native-object/secret isolation test red.

## Composite dependencies

model.request-decision/model.normalize-response; operational only.

## Fundamentals review

`CONSISTENT` (MEDIUM): provider mechanics stay replaceable.

## Grill findings

Rejected unsupported-auth guessing and session-as-memory.

## Remaining user decisions

None; exact provider/auth remains integration configuration.
