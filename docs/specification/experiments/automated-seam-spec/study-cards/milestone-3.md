# Milestone 3 study cards — sandbox.authorize-execution–research.continue-from-exploration

## sandbox.authorize-execution — requested exploratory action + policy → sandbox authority / AuthorizedDataView

**Why does it exist?** Translate open-ended requested computation into least-authority data and side-effect capabilities without judging or narrowing its scientific method.

**Which fundamental does it protect?** `CONSISTENT`: it restricts authority, not scientific imagination.

**What must cross?** Authored code/arguments and requested outputs; exact identities; allowed dataset/field/time scope; limits; policy/version; denial reasons.

**Most dangerous false success?** Build a broad context then ask sandbox code to behave

**Which test catches it?** Pair permitted/denied actions with fail-on-read resources; assert exact grant/no read. Supply unusual code and assert byte/semantic preservation. Change only requested field/time/network capability and assert least-authority delta. **Level A/B.**

**Any unresolved human decision?** None; capability representation and sandbox technology remain free.

## sandbox.execute-analysis — AI-authored code + authorized capabilities/limits → sandbox execution result

**Why does it exist?** Execute genuinely open-ended exploratory computation while preventing access outside the granted information and side-effect domain.

**Which fundamental does it protect?** `CONSISTENT`: maximum computational creativity inside enforced information/side-effect boundaries.

**What must cross?** Code and input identity, authorized views, environment, seeds, result values/structures, status, warnings, resource usage.

**Most dangerous false success?** Run code in host process with convention-based restrictions

**Which test catches it?** Adversarial code probes every denied channel while performing a novel permitted calculation; assert only granted data influences result, probes fail, limits terminate, and source/store hashes remain unchanged. **Level B.**

**Any unresolved human decision?** None; isolation runtime/library catalog remain implementation/configuration choices.

## sandbox.record-provenance — actual sandbox access/execution/artifacts → execution provenance record

**Why does it exist?** Record what code actually ran and what it actually accessed so exploratory outputs remain auditable despite untrusted code self-report.

**Which fundamental does it protect?** `CONSISTENT`: authoritative provenance follows actual execution without upgrading epistemic status.

**What must cross?** Action/code/environment/data/vintage/view IDs, actual ranges/fields, seeds, libraries where practical, status/errors, artifact refs, times/resources.

**Most dangerous false success?** Log request metadata rather than actual access

**Which test catches it?** Code requests X but accesses authorized Y through alias and self-reports X; assert actual Y. Vary seed/environment/data version and assert distinct lineage. Inject recorder/artifact failure and assert no provenance-complete success. **Level A/B.**

**Any unresolved human decision?** None.

## observation.assemble-analysis-result — StructuredReturn/AnalysisResult + provenance → StructuredObservation

**Why does it exist?** Return decision-relevant exploratory facts to the loop while retaining provisional status and full provenance/drill-down.

**Which fundamental does it protect?** `CONSISTENT`: preserves useful meaning without premature scientific commitment.

**What must cross?** Values, units, sample/window/time, uncertainty, diagnostics, controls/protocol, caveats, status, actual provenance, refs, provisional role.

**Most dangerous false success?** Return a scalar or “looks good”

**Which test catches it?** Pair equal headline statistic with different stability/sample/caveat; packet-only consumer chooses differently. Assert provisional status and actual provenance. Oversized output yields summary+ref. **Level C.**

**Any unresolved human decision?** None.

## observation.translate-analysis-failure — exploratory exception/stdout/stderr → concise failure observation + diagnostic artifact

**Why does it exist?** Make exploratory failure diagnosable and repairable without context flooding, secret leakage, or false success.

**Which fundamental does it protect?** `CONSISTENT`: repair feedback remains truthful and bounded.

**What must cross?** Failure class, operation/code/execution identity, safe message/context, recoverability, provenance, artifact integrity.

**Most dangerous false success?** Dump traceback into prompt

**Which test catches it?** Exceptions containing secret sentinel and long trace: primary observation is bounded/secret-free, artifact permissioned and exact where allowed; deterministic provider repairs based only on failure type. **Level C.**

**Any unresolved human decision?** None.

## artifact.persist-analysis-output — exploratory output → ArtifactStore identity/ref

**Why does it exist?** Retain large exploratory tables, plots, code, and temporary models without promoting them into formal scientific objects.

**Which fundamental does it protect?** `CONSISTENT`: retains creativity outputs without epistemic promotion.

**What must cross?** Content/integrity/type/shape, execution/code/data/environment IDs, temporary status, sensitivity, created time.

**Most dangerous false success?** Treat pickled model as ModelDefinition

**Which test catches it?** Persist table/plot/code/temp-model; exact round-trip/integrity/provenance and provisional status. Attempt overwrite and formal-use without formalization.create-candidate/model.define-recipe; reject. **Level A/B.**

**Any unresolved human decision?** None.

## knowledge.retrieve-evidence — knowledge retrieval action + current authority → authorized relevant evidence

**Why does it exist?** Search broad machine-accessible knowledge while enforcing current scope, status, and permissions before substantive content is surfaced.

**Which fundamental does it protect?** `CONSISTENT`: broad access remains permission/status governed.

**What must cross?** Query intent, source/evidence identity, status, provenance, temporal/environment scope, contradictions/caveats, authorization and rank rationale.

**Most dangerous false success?** Vector search first then filter

**Which test catches it?** Seed highly similar denied/stale decoys and less-similar current permitted evidence; assert only latter content. Revoke permission and assert zero reads. **Level A/C.**

**Any unresolved human decision?** None; search/ranking implementation remains free.

## knowledge.return-retrieved-evidence — authorized retrieved evidence → StructuredObservation / active episode

**Why does it exist?** Return retrieved meaning and its current/superseded/provenance status to the research loop so retrieval can change decisions without becoming durable belief.

**Which fundamental does it protect?** `CONSISTENT`: the implied feedback mapping follows locked retrieval/episode semantics.

**What must cross?** Query, substantive snippets/facts, source identity, current/superseded/rejected status, provenance, contradictions, omissions/rank, refs.

**Most dangerous false success?** Append only document IDs

**Which test catches it?** Paired current-supporting versus superseded-contradicting evidence, fresh sessions, transcript deletion, no source access by provider; assert different next actions and unchanged state. **Level C.**

**Any unresolved human decision?** None.

## research.repair-exploratory-action — ordinary exploratory failure → repaired action in same episode

**Why does it exist?** Continue exploration after operational failure only when repair preserves scientific meaning and state remains uncorrupted.

**Which fundamental does it protect?** `CONSISTENT`: exploration can recover without scientific falsification or authority bypass.

**What must cross?** Original failure/action/code, repair rationale/difference, episode/task goal, evidence status, provenance, attempt identities.

**Most dangerous false success?** Capability retries internally with guessed column

**Which test catches it?** Deterministic provider repairs only from failure observation; assert new action identity/authorization, both attempts, same episode, unchanged state. Governance denial does not auto-repair. **Level C.**

**Any unresolved human decision?** None.

## research.continue-from-exploration — exploratory action through execution/retrieval → next evidence-dependent action

**Why does it exist?** Prove the authorized exploratory organism changes behavior because returned semantics crossed the full loop, not because the model retained hidden access.

**Which fundamental does it protect?** `CONSISTENT`: strongest deterministic proof of creative, authorized, observation-driven exploration.

**What must cross?** Authored creativity, actual authorization/access provenance, observation semantics/status, episode persistence, permission filtering, action ancestry.

**Most dangerous false success?** Queue second response

**Which test catches it?** Paired sessions with unusual custom analysis and retrieval variant; fail-on-access provider; transcript deletion; third sentinel branch; assert B1 != B2 solely from substantive observations. **Level C.**

**Any unresolved human decision?** None.
