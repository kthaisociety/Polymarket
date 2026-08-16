# Milestone-7 study cards

## report.render-finding — ValidatedFinding → human-facing report

**Why does it exist?** Allow flexible AI wording/layout while preserving canonical scientific substance.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Claim scope, target/horizon, metrics, robustness, caveats, refs/provenance, status.

**Most dangerous false success?** Omit a critical instability caveat while retaining positive headline.

**Which test catches it?** Generate adversarial variants and semantic grader compares structured claims/caveats/status to finding, not exact prose. **Level A/B.**

**Any unresolved human decision?** None.

## provider.authenticate-adapter — supported provider credentials/config → authenticated provider adapter/session

**Why does it exist?** Establish operational model access without leaking credentials or provider sessions into runtime/scientific objects.

**Which fundamental does it protect?** `CONSISTENT` (MEDIUM): provider mechanics stay replaceable.

**What must cross?** Provider/model/config identity, supported settings, auth status/expiry and safe operational provenance.

**Most dangerous false success?** Return authenticated client object as neutral provider.

**Which test catches it?** Secret-sentinel serialization scans, adapter replacement, expiry/refresh and unsupported-auth failures. **Level A/B.**

**Any unresolved human decision?** None; exact provider/auth remains integration configuration.

## context.checkpoint-episode — active ResearchEpisode under pressure → EpisodeCheckpoint

**Why does it exist?** Preserve the investigation in structured reconstructible form without treating generic conversation summary as state or deleting evidence.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** All decision-relevant semantics, epistemic roles, order/status, identities, refs/provenance and authority.

**Most dangerous false success?** Drop substantive observation payload while retaining ref ID.

**Which test catches it?** Paired checkpoints differing in one unresolved/evidence status lead to different rebuilt action; integrity and no-delete assertions. **Level C.**

**Any unresolved human decision?** None.

## context.rebuild-after-loss — state + checkpoint/episode + evidence + permissions → rebuilt equivalent ContextPacket

**Why does it exist?** Prove scientific behavior survives provider transcript/context loss through durable reconstruction.

**Which fundamental does it protect?** `CONSISTENT`.

**What must cross?** Mission, state/episode distinction, plan/evidence/unresolved work, current/superseded, warnings/permissions, refs/provenance.

**Most dangerous false success?** Rebuild from checkpoint ID plus hidden provider transcript.

**Which test catches it?** Destroy all provider/transient context; fresh provider, fail-on-store access, permission revocation and post-checkpoint observation fixtures. **Level C.**

**Any unresolved human decision?** None.
