# backtest.bind-protected-view — BacktestPermit + protected resource identity → exact AuthorizedDataView

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Bind governance permission to the actual protected bytes/view exposed to execution; prevent permit swapping or broader access.

## Relevant locked invariants

I7–I8, I13–I14, I24–I25.

## Source A

Exact unconsumed/current permit, protected resource/slice/version, opaque content-manifest identity,
epistemic-period identity, freshness status, caller/execution identity, and environment/policy.

## Destination B

Least-authority protected AuthorizedDataView bound to permit/request/system/scenario and exact resource identity, or denial.

## Mapping f

Verify signatures/correlation/scope/currentness; resolve the exact authority-issued resource binding
after authorization; construct a non-broadenable metadata view. After exposure is recorded, the
loader must return the exact verified content manifest and parsed catalog identity bound to that
view or execution fails closed.

## Must preserve

Permit/request/system/scenario, resource/slice/version, content manifest, epistemic period,
freshness, environment, access identity/limits.

## May transform

Equivalent representation may change where exact scientific meaning, identity and behavior survive.

## Must exclude

Wildcard/latest resource, neighboring holdout, path/resource alias laundering, relabeling
`PREEXPOSED` content as unseen, permit reuse/transfer, pre-check read, unrestricted store, content
leakage.

## Authority boundary

Governance permit authorizes exact scope; access boundary materializes; execution only consumes view.

## Allowed state mutation

Create view/access audit; actual disclosure triggers exposure.record-disclosure.

## Forbidden state mutation

No scientific state/promotion; no out-of-scope read.

## Failure semantics

Mismatch/stale/consumed/reused permit and `PREEXPOSED` scope deny before content read. No fallback
to an available protected set. A post-disclosure content-manifest or parsed-catalog mismatch seals
typed failed evidence and retains exposure.

## Observable consequences

Permit for H1 cannot open H2 or wider dates; denied attempts read zero bytes.

## False-success implementations considered

Treat any valid permit as access to protected catalog; resolve latest holdout.

## Falsifying tests

Swap resource/version/date/caller; serve changed bytes after binding; publish identical bytes under
another resource ID; mark already open bytes `PREEXPOSED`; fail-on-read; exact scope succeeds only.
**Level A/B.**

## Mutation-sensitivity check

**Mutation:** Ignore permit resource binding and open requested holdout.

**Expected failure:** Swap test red.

## Composite dependencies

backtest.authorize-request; exposure.record-disclosure exposure; backtest.execute-scenario engine.

## Fundamentals review

`CONSISTENT`: implied mapping uniquely follows permit/data authority and exposure rules.

## Grill findings

Added pre-read verification and nontransferability.

## Remaining user decisions

None.
