# Milestone 1 study cards — action.authorize-request–runtime.run-bounded-episode

## action.authorize-request — AgentAction → authorization/routing decision

**Why does it exist?** Typing is not permission; current identity and policy must be checked before any effect.
**Which fundamental does it protect?** Current authority and least privilege without narrowing authored science.
**What must cross?** Exact unchanged request, target claims, current versions, policy reason, and bound route/context.
**Most dangerous false success?** Replace a stale target with the active episode and authorize it.
**Which test catches it?** Current-versus-foreign target pair with fail-on-call capability.
**Any unresolved human decision?** No.

## data.inspect-authorized-view — authorized inspection → CapabilityExecutionResult

**Why does it exist?** Compute useful bounded facts only from the view actually authorized.
**Which fundamental does it protect?** Exploratory freedom under constrained information and side effects.
**What must cross?** Exact authorized dataset/fields/version and descriptive facts.
**Most dangerous false success?** Resolve through an unrestricted catalog.
**Which test catches it?** Scoped view plus inaccessible same-name decoy and fail-on-catalog access.
**Any unresolved human decision?** No.

## observation.assemble-authoritative-result — execution result → StructuredObservation

**Why does it exist?** Create bounded working evidence with harness-observed provenance.
**Which fundamental does it protect?** Provenance follows claims; observations are not beliefs.
**What must cross?** Decision-relevant facts, status, warnings, actual access/execution identity, and drill-down.
**Most dangerous false success?** Trust capability-authored provenance.
**Which test catches it?** Capability claims X while harness records Y.
**Any unresolved human decision?** No.

## episode.record-observation — StructuredObservation → episode working evidence

**Why does it exist?** Make the current investigation resumable without committing belief.
**Which fundamental does it protect?** Tool result is not durable `ResearcherState`.
**What must cross?** Substantive observation meaning, order, provenance, warnings, and refs.
**Most dangerous false success?** Persist only an observation ID.
**Which test catches it?** Reload episode after transient loss and require row-count/provenance meaning.
**Any unresolved human decision?** No.

## runtime.continue-from-observation — prior observation → next ContextPacket/action

**Why does it exist?** Prove the loop is causally observation-driven.
**Which fundamental does it protect?** Research is a feedback loop, not a scripted pipeline.
**What must cross?** Discriminating observation semantics through persistence and reconstruction.
**Most dangerous false success?** Choose the second response by turn count or hidden fixture access.
**Which test catches it?** Fresh paired sessions, 18 versus 2, packet-only deterministic provider, sentinel branch.
**Any unresolved human decision?** No.

## commit.compose-request — transition action → CommitRequest

**Why does it exist?** Package semantic-boundary intent without applying or inventing it.
**Which fundamental does it protect?** Durable state changes only through validated semantic commits.
**What must cross?** Exact lifecycle proposal, explicit state-proposal presence/absence, refs, versions, identity.
**Most dangerous false success?** Generate a default state delta on resolution.
**Which test catches it?** Lifecycle-only versus combined request pair.
**Any unresolved human decision?** No.

## commit.validate-proposals — CommitRequest → independent validation decisions

**Why does it exist?** Prevent valid lifecycle intent from smuggling invalid durable understanding.
**Which fundamental does it protect?** Beneficiaries cannot self-authorize; evidence and currentness are independently checked.
**What must cross?** Exact proposal semantics, versions, evidence authority, and separate reasons.
**Most dangerous false success?** Episode acceptance authorizes the entire request.
**Which test catches it?** Valid resolution paired with stale/unsupported state delta and unchanged stores.
**Any unresolved human decision?** No.

## commit.publish-boundary — validated proposals → atomic CommitResult

**Why does it exist?** Avoid scientifically impossible half-state.
**Which fundamental does it protect?** Formal failure blocks false success; immutable lineage.
**What must cross?** Exactly validated proposals and one all-or-nothing result.
**Most dangerous false success?** Persist episode before state then fail.
**Which test catches it?** Fault injection after every underlying write.
**Any unresolved human decision?** No.

## commit.retry-idempotently — commit retry → original result/conflict

**Why does it exist?** Survive uncertain acknowledgement without duplicate epistemic effects.
**Which fundamental does it protect?** Runtime retries do not duplicate irreversible effects.
**What must cross?** Full semantic payload identity and original result.
**Most dangerous false success?** Compare only the idempotency key.
**Which test catches it?** Change each semantic dimension under one key and require conflict.
**Any unresolved human decision?** No.

## runtime.return-repairable-failure — repairable failure → failure observation

**Why does it exist?** Let the agent correct failures without false success or lost history.
**Which fundamental does it protect?** Explicit failure and observation/state separation.
**What must cross?** Exact failure meaning, recoverability, safe reason, diagnostics, and identity.
**Most dangerous false success?** Log rejection only, so the next model cannot repair it.
**Which test catches it?** Packet-only provider emits evidence-specific correction from the failed observation.
**Any unresolved human decision?** No.

## trajectory.append-event — operations/rejections → Trajectory

**Why does it exist?** Preserve ordered replay/audit history without making it belief.
**Which fundamental does it protect?** Rejections remain history; operational history is not state.
**What must cross?** Exact attempt, action, authorization, result, failure, and correlation order.
**Most dangerous false success?** Record only successful operations.
**Which test catches it?** Mixed success/rejection/retry trace reload.
**Any unresolved human decision?** No.

## artifact.persist-output — large output → artifact/ref

**Why does it exist?** Bound context without destroying accessible detail.
**Which fundamental does it protect?** Compression changes accessibility, not information existence.
**What must cross?** Complete immutable content, integrity, provenance, classification, and useful ref metadata.
**Most dangerous false success?** Store only the preview while claiming a full artifact.
**Which test catches it?** Exact authorized round-trip and integrity check.
**Any unresolved human decision?** No.

## artifact.retrieve-authorized-content — permitted ref → authorized drill-down content

**Why does it exist?** Make references usable without turning possession into permission.
**Which fundamental does it protect?** Context/retrieval cannot bypass current permissions.
**What must cross?** Exact substantive content, provenance, status, bounds, and authorization.
**Most dangerous false success?** Read because the caller knows an opaque ID.
**Which test catches it?** Permission revocation before retrieval with zero content reads.
**Any unresolved human decision?** No.

## runtime.run-bounded-episode — initialized session → bounded terminal run result

**Why does it exist?** Prove the complete M1 organism and its limits.
**Which fundamental does it protect?** Causal feedback, separated authority/state, explicit failure, bounded autonomy.
**What must cross?** Exact current state across every local seam and truthful terminal/limit reason.
**Most dangerous false success?** Script model responses by turn count and call it autonomous feedback.
**Which test catches it?** Paired Level C whole-episode scenario plus repair/idempotency/limit companions.
**Any unresolved human decision?** No.
