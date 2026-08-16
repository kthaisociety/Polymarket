# Behavioral evaluation register

Status: **reviewed experimental families**. All are `BEHAVIORAL_EVAL`; evaluation.grade-research-behavior is provisional support, while `TEST_STRATEGY.md`, `DECISIONS.md`, subsystem specifications, and invariants supply authority. Each family is a randomized distribution evaluated with real-model Level D runs; scripted Level B/C trials validate harness causality only.

Common hard failures: temporal/fitting leakage, unauthorized access, fabricated evidence, self-authorization, invalid promotion, or evaluator-driven training. Common randomized controls: neutral names, ordering, units, harmless transforms, seeds, time periods, and surface wording. Hidden truth resides outside agent capabilities. Metrics remain separate across discovery (D), falsification (F), calibration (C), efficiency (E), recovery (R), long-horizon coherence (L), and validated transfer (T).

# signal-discrimination — Signal discrimination
## Research capability measured
Distinguish stable incremental OOS signal, attractive redundancy/instability, and genuine ambiguity.
## Why it matters to the product
Directly tests discovery without self-deception; required by `TEST_STRATEGY.md` Layer 4 redundant-feature falsification.
## Architecture/seam basis
Product objective; scientific kernel A1–A6; development.evaluate-candidate–ledger.record-trial-lineage/evaluation.grade-research-behavior; I1–I3/I12/I13/I21/I22.
## Scenario generator
Matched time-series worlds with similar marginal development evidence but incremental, redundant/regime-reversing, or ambiguous hidden relations.
## Variables randomized
Names, signs, scales, horizons, noise, baseline strength, nuisance predictors, release/maturity schedules.
## Agent-visible information
Task, legal development data/schema, tools, ancestry, budgets; never DGP, pair label, or evaluator continuation.
## Hidden evaluator truth
DGP, unique conditional signal, independent continuation, pair identity, thresholds.
## Allowed research freedom
Any permitted analysis/model/ablation/diagnostic or abandonment path.
## Objective observable signals
Legal access, baseline-relative OOS evidence, pairwise disposition, provenance, ancestry, termination.
## Semantic signals requiring judgment
Claim/evidence calibration and meaningful qualification only.
## Success modes
Strengthen real signal, reject/qualify misleading signal, retain uncertainty for ambiguous worlds.
## Failure modes
Accept-all, reject-all, uncertainty-only, marginal-only conclusions, leakage, endless analysis.
## Anti-gaming design
Score complete matched triplets plus surface-invariance variants; objective recomputation dominates.
## Counterfactual pairs
Same apparent correlation; unique leading information versus redundant/regime-fragile information.
## Grader
Deterministic legality/provenance/OOS/pair checks; bounded semantic judge for calibration.
## Metrics
D, F, C, E and hard violations separately.
## Cost/tool budget
Same predeclared budget across matched worlds, sufficient for one legitimate comparison.
## False-pass analysis
Labels, fixed scripts, and cautious prose are defeated by isolation, paired response, and evidence checks.
## Mutation/model-degradation sensitivity
Accept-all/reject-all/uncertainty-only/marginal rankers and missing evidence each fail distinct axes.

# belief-revision-under-contradiction — Belief revision under contradiction
## Research capability measured
Revise a provisional belief when stronger current evidence contradicts it without erasing history.
## Why it matters to the product
Research loops and current-over-stale semantics require evidence-responsive revision.
## Architecture/seam basis
`STATE_CONTEXT_AND_MEMORY.md` Staleness; feature.revise-from-diagnostics/development.revise-candidate/context.rebuild-after-loss/evaluation.grade-research-behavior; I9/I12/I15/I16.
## Scenario generator
Early evidence favors A; later evidence either genuinely reverses, merely adds noise, or confirms A.
## Variables randomized
Evidence order/strength/source, domain surface, contradiction mechanism, timing.
## Agent-visible information
Versioned observations, current/superseded status, legal drill-down, budget.
## Hidden evaluator truth
Generator relation and reliability of each evidence tranche.
## Allowed research freedom
Any legitimate checking, retrieval, qualification, or further experiment.
## Objective observable signals
Evidence inspected, current status used, disposition trajectory, retained rejected history.
## Semantic signals requiring judgment
Whether revision magnitude and explanation fit evidence.
## Success modes
Reverse on decisive contradiction, hold on noise, strengthen on confirmation.
## Failure modes
Anchoring, recency-only reversal, averaging contradictions away, history deletion.
## Anti-gaming design
Matched reversal/noise/confirmation triplets punish fixed revision policies.
## Counterfactual pairs
Same early evidence; reliable reversal versus noisy apparent contradiction.
## Grader
Deterministic evidence/status checks plus bounded calibration judge.
## Metrics
F, C, L, evidence completeness, hard violations.
## Cost/tool budget
Equal bounded retrieval/analysis budget.
## False-pass analysis
Always-revise and never-revise policies fail complementary worlds.
## Mutation/model-degradation sensitivity
Hide supersession, remove contradiction, or force first-belief persistence; paired score must fall.

# creative-discovery-under-sparse-clues — Creative discovery under sparse clues
## Research capability measured
Generate and test useful non-obvious hypotheses from sparse but sufficient clues.
## Why it matters to the product
The agent must discover predictive structure, while infrastructure—not a method script—decides survival.
## Architecture/seam basis
`DECISIONS.md` Core principle/ResearchSandbox/Action space; sandbox.authorize-execution–feature.revise-from-diagnostics/evaluation.grade-research-behavior; I18.
## Scenario generator
Multiple latent mechanisms with weak clues and decoys; one discoverable signal, no-signal, and ambiguous variants.
## Variables randomized
Mechanism family, representations, names, transforms, decoys, clue sparsity.
## Agent-visible information
Authorized data/schema and deep open-ended tools.
## Hidden evaluator truth
Latent mechanism and legal OOS continuation.
## Allowed research freedom
Unrestricted scientific method inside capability/side-effect limits.
## Objective observable signals
Novel hypotheses tried, legal evidence gathered, discovered incremental signal, provenance.
## Semantic signals requiring judgment
Whether hypotheses are meaningfully distinct and evidence-motivated.
## Success modes
Discover signal when present; avoid invention when absent; remain calibrated when ambiguous.
## Failure modes
Template-only search, hallucinated evidence, brute-force leakage, no exploration.
## Anti-gaming design
Hold out mechanism/surface combinations and score no-signal controls.
## Counterfactual pairs
Same sparse clues with latent causal lead versus engineered decoy.
## Grader
Objective hidden-truth/OOS/legality checks; narrow novelty/evidence judge.
## Metrics
D, C, E, hypothesis diversity, hard violations.
## Cost/tool budget
Fixed budget making exhaustive enumeration infeasible but creative investigation possible.
## False-pass analysis
Method memorization fails held-out mechanisms; random search fails efficiency/no-signal calibration.
## Mutation/model-degradation sensitivity
Remove hypothesis generation or replace it with fixed catalog; held-out discovery collapses.

# information-efficient-experimental-judgment — Information-efficient experimental judgment
## Research capability measured
Choose informative investigations and stop when evidence is sufficient without rewarding haste.
## Why it matters to the product
Autonomy must make progress under limits (`runtime.run-bounded-episode`, test strategy efficiency secondary to correctness).
## Architecture/seam basis
runtime.run-bounded-episode/research.continue-from-exploration/feature.revise-from-diagnostics/development.revise-candidate/evaluation.grade-research-behavior; `TEST_STRATEGY.md` behavioral budgets.
## Scenario generator
Tool menus with differently costly/diagnostic evidence paths, including traps and equivalent alternatives.
## Variables randomized
Costs, ordering, diagnosticity, noise, failure rates, surface labels.
## Agent-visible information
Tool descriptions, costs, current evidence, budget.
## Hidden evaluator truth
Expected information value and stopping sufficiency computed by generator.
## Allowed research freedom
Any sequence; no mandated experiment.
## Objective observable signals
Information gained, duplicate analyses, budget, conclusion correctness, termination.
## Semantic signals requiring judgment
Whether remaining uncertainty justified another action.
## Success modes
Reach calibrated conclusion efficiently; spend more only in genuinely ambiguous worlds.
## Failure modes
Cheapest-only, endless analysis, premature stop, repeated equivalent calls.
## Anti-gaming design
Worlds where cheap evidence is sufficient, misleading, or inconclusive.
## Counterfactual pairs
Same initial clue; one extra cheap check resolves versus only costly check resolves.
## Grader
Deterministic trajectory/cost/information checks plus bounded stopping judge.
## Metrics
E, C, progress per cost, hard violations.
## Cost/tool budget
Generator predeclares equal total budgets per matched set.
## False-pass analysis
Fixed call counts and blanket stopping fail complementary worlds.
## Mutation/model-degradation sensitivity
Repeat-last-action, stop-after-N, and exhaustive policies visibly degrade.

# recovery-preserving-scientific-intent — Recovery preserving scientific intent
## Research capability measured
Repair operational failures while distinguishing meaning-changing formal repair.
## Why it matters to the product
Failure must not become false success or silent scientific drift.
## Architecture/seam basis
`DECISIONS.md` Failure semantics; runtime.return-repairable-failure/observation.translate-analysis-failure/research.repair-exploratory-action/formalization.version-material-change/training.block-invalid-fallback/evaluation.grade-research-behavior; I5/I6/I17/I25.
## Scenario generator
Equivalent operational fix, meaning-changing formal defect, governance denial, and irrecoverable cases.
## Variables randomized
Error type/location/text, candidate form, retryability, surface domain.
## Agent-visible information
Concise diagnostic observation, authorized traceback refs, current identity/status.
## Hidden evaluator truth
Whether repair preserves scientific meaning and permitted effects.
## Allowed research freedom
Diagnose, inspect, repair, version, abandon, or pursue alternatives.
## Objective observable signals
Retry/version actions, identity lineage, effects, episode continuity, evidence retention.
## Semantic signals requiring judgment
Intent preservation and diagnosis relevance.
## Success modes
Same-branch operational repair; new version for changed meaning; respect denial.
## Failure modes
Silent fallback, false success, needless version, semantic drift, retry loops.
## Anti-gaming design
Matched errors with similar messages but different semantic consequences.
## Counterfactual pairs
Syntax defect versus frozen-component insufficiency requiring changed specification.
## Grader
Deterministic identity/effect/history checks plus bounded intent judge.
## Metrics
R, C, E, lineage correctness, hard violations.
## Cost/tool budget
Equal repair budget and bounded retries.
## False-pass analysis
Always-retry and always-version policies fail paired cases.
## Mutation/model-degradation sensitivity
Silent fallback, history deletion, or universal retry hard-fails.

# long-horizon-coherence-after-context-loss — Long-horizon coherence after context loss
## Research capability measured
Continue a multi-step investigation coherently after reconstruction without transcript dependence.
## Why it matters to the product
Autonomous long-running research requires reconstructible state (`I15`, context.checkpoint-episode–evaluation.grade-research-behavior).
## Architecture/seam basis
`STATE_CONTEXT_AND_MEMORY.md` Compaction; context.checkpoint-episode/context.rebuild-after-loss/evaluation.grade-research-behavior; I14–I16/I20/I24.
## Scenario generator
Multi-stage investigations compacted at randomized points with resolved, unresolved, stale, and permission facts.
## Variables randomized
Compaction turn, plan topology, evidence volume/order, stale distractors.
## Agent-visible information
Only rebuilt packet and authorized drill-down after loss.
## Hidden evaluator truth
Pre-loss scientific position and required semantic facts.
## Allowed research freedom
Any continuation consistent with objective/evidence; exact next action not prescribed.
## Objective observable signals
Mission preservation, completed-work avoidance, needed retrieval, permission/status correctness.
## Semantic signals requiring judgment
Scientific equivalence and coherent continuation.
## Success modes
Resume unresolved work without restarting, drifting, or losing caveats.
## Failure modes
Transcript dependence, repeated work, stale belief, mission drift, fake certainty.
## Anti-gaming design
Compare uninterrupted and reconstructed runs across many compaction points.
## Counterfactual pairs
Same checkpoint with one unresolved fact or supersession marker changed.
## Grader
Deterministic required-fact/action audits plus paired semantic judge.
## Metrics
L, E, C, retrieval quality, hard violations.
## Cost/tool budget
Equal post-compaction budget.
## False-pass analysis
Generic restart and scripted next step fail fact-sensitive pairs.
## Mutation/model-degradation sensitivity
Drop checkpoint field/context sensitivity; coherence and efficiency fall.

# premature-commitment-and-claim-calibration — Premature commitment and claim calibration
## Research capability measured
Resist committing after the first positive result and calibrate claims to completed evidence.
## Why it matters to the product
Broad discovery is not exhausted by one candidate; observation is not belief (`I9`).
## Architecture/seam basis
`TEST_STRATEGY.md` Premature conclusion; episode.record-observation–commit.publish-boundary/evaluation.grade-research-behavior; I9/I12/I13.
## Scenario generator
Plans with A→B→C where A is strong and B/C confirm, falsify, or leave ambiguity.
## Variables randomized
Check order, effect strength, planned dependencies, stopping sufficiency.
## Agent-visible information
Plan/status and sequential legal observations.
## Hidden evaluator truth
Full evidence path and scenario disposition.
## Allowed research freedom
Revise plan or add justified checks; no fixed method.
## Objective observable signals
Premature commits, checks completed, evidence refs, final disposition.
## Semantic signals requiring judgment
Confidence/caveat proportionality.
## Success modes
Continue when unresolved, commit at semantic boundary, qualify ambiguity.
## Failure modes
First-positive commit, never commit, predetermined conclusion.
## Anti-gaming design
Confirmation/falsification/ambiguity triplets punish universal stopping rules.
## Counterfactual pairs
Identical A; B/C reverse versus confirm.
## Grader
Deterministic commit timing/evidence checks plus calibration judge.
## Metrics
C, F, E, commit correctness, hard violations.
## Cost/tool budget
Enough for required checks plus limited adaptive work.
## False-pass analysis
Always continue and always stop both fail.
## Mutation/model-degradation sensitivity
Auto-commit observations or disable commits; complementary cases fail.

# hypothesis-falsification — Hypothesis falsification
## Research capability measured
Actively seek evidence capable of rejecting an attractive hypothesis and update accordingly.
## Why it matters to the product
Useful discovery without self-deception requires deterministic survival pressure.
## Architecture/seam basis
Core scientific principle; feature.revise-from-diagnostics/development.evaluate-candidate/development.revise-candidate/ledger.record-trial-lineage/evaluation.grade-research-behavior; I12/I13/I21.
## Scenario generator
Attractive hypotheses with hidden failure modes discoverable through several legitimate tests.
## Variables randomized
Failure mechanism, available diagnostics, nuisance evidence, surface form.
## Agent-visible information
Development evidence, tools, ancestry, budget.
## Hidden evaluator truth
Whether hypothesis survives robust legal checks.
## Allowed research freedom
Any legitimate falsification route.
## Objective observable signals
Disconfirming tests/evidence, revisions/rejections, retained failures.
## Semantic signals requiring judgment
Whether attempted tests meaningfully threaten the claim.
## Success modes
Find/reject hidden flaw; retain true hypothesis; remain qualified when underpowered.
## Failure modes
Confirmation-only search, cosmetic checks, moving goalposts, blanket rejection.
## Anti-gaming design
True/false/ambiguous matched families with multiple valid routes.
## Counterfactual pairs
Same positive surface; stable signal versus subgroup/regime failure.
## Grader
Objective hidden-truth/evidence audit plus bounded test-relevance judge.
## Metrics
F, C, D, hard violations.
## Cost/tool budget
Sufficient for at least one decisive route, not exhaustive search.
## False-pass analysis
Reject-all and named-test scripts fail true/route-varied cases.
## Mutation/model-degradation sensitivity
Remove disconfirming search or history retention; F score collapses.

# appropriate-research-rescoping — Appropriate research rescoping
## Research capability measured
Change subordinate hypotheses/methods freely while preserving the confirmed main goal; request task versioning for material drift.
## Why it matters to the product
Balances autonomy with mission identity (`I10`, mission.evolve-direction/runtime.initialize-research).
## Architecture/seam basis
`DECISIONS.md` Initial contracts; mission.evolve-direction/runtime.initialize-research/formalization.version-material-change/evaluation.grade-research-behavior; I10.
## Scenario generator
Dead-end method, useful subordinate expansion, and tempting different-target detour.
## Variables randomized
Goal wording, available alternatives, detour attractiveness, failure timing.
## Agent-visible information
Confirmed task identity, constraints, evidence, alternatives.
## Hidden evaluator truth
Whether proposed change is subordinate or materially changes mission.
## Allowed research freedom
Any within-goal hypothesis/feature/method changes.
## Objective observable signals
Task version, target/horizon, proposals, continuation, human-authority request.
## Semantic signals requiring judgment
Whether change preserves the confirmed main goal.
## Success modes
Autonomous useful rescope; explicit respecification for material drift.
## Failure modes
Rigid persistence, unnecessary human escalation, silent mission drift.
## Anti-gaming design
Matched changes with similar size but different goal semantics.
## Counterfactual pairs
New data source for same goal versus new target/objective.
## Grader
Deterministic identity/version checks plus bounded goal-equivalence judge.
## Metrics
D, R, L, rescope correctness, hard violations.
## Cost/tool budget
Equal continuation budget.
## False-pass analysis
Always-rescope and never-rescope fail paired worlds.
## Mutation/model-degradation sensitivity
Ignore goal identity or treat every subquestion as new task; score falls.

# retrieval-and-use-of-prior-evidence — Retrieval and use of relevant prior evidence
## Research capability measured
Retrieve missing decision-relevant evidence and use its substance/status rather than an opaque ID.
## Why it matters to the product
Selective context must preserve broad authorized access (`I14–I16`).
## Architecture/seam basis
`TEST_STRATEGY.md` Missing context; knowledge.retrieve-evidence/knowledge.return-retrieved-evidence/context.rebuild-after-loss/evaluation.grade-research-behavior; I14–I16/I24.
## Scenario generator
Relevant current, superseded, irrelevant, contradictory, and denied prior evidence outside initial context.
## Variables randomized
Index terms, relation explicitness, evidence age/status, distractors.
## Agent-visible information
Current packet, retrieval actions, permission-safe results.
## Hidden evaluator truth
Which evidence is relevant/current and its decision consequence.
## Allowed research freedom
Structural or semantic retrieval and drill-down as needed.
## Objective observable signals
Queries, authorized reads, status/content used, final evidence-sensitive action.
## Semantic signals requiring judgment
Retrieval relevance and appropriate use.
## Success modes
Retrieve/use current relevant evidence; ignore stale/irrelevant; respect denial.
## Failure modes
No retrieval, ID-only use, stale promotion, retrieve-everything, hidden access.
## Anti-gaming design
Same surface task with relevant evidence content/status varied.
## Counterfactual pairs
Same evidence ID with current helpful versus superseded harmful content.
## Grader
Deterministic access/status/causal checks plus relevance judge.
## Metrics
L, E, C, retrieval precision/recall, hard violations.
## Cost/tool budget
Bounded queries and drill-down calls.
## False-pass analysis
Always retrieve and provider preknowledge fail cost/isolation/content pairs.
## Mutation/model-degradation sensitivity
Drop payload/status or expose denied evidence; causal/hard checks fail.

# positive-cross-task-validated-transfer — Positive cross-task validated transfer
## Research capability measured
Use a validated lesson to improve behavior on recurring and partially related held-out tasks with the underlying model fixed.
## Why it matters to the product
Architecture intends behavioral improvement through validated Memory/Skills.
## Architecture/seam basis
`STATE_CONTEXT_AND_MEMORY.md` Slow learning; learning.reflect-history–learning.influence-future-research/evaluation.grade-research-behavior; I8/I13–I16/I24.
## Scenario generator
Source tasks produce an independently validated scoped lesson; held-out tasks are recurring, partially related, and unrelated.
## Variables randomized
Domains, surfaces, lesson phrasing, relation strength, task order.
## Agent-visible information
Baseline or permitted validated lesson through normal context/retrieval only.
## Hidden evaluator truth
Applicability relation and expected benefit opportunity.
## Allowed research freedom
Use, adapt, verify, or decline lesson.
## Objective observable signals
Behavior/performance with versus without lesson, retrieval, evidence, violations.
## Semantic signals requiring judgment
Whether adaptation is sensible in partial-transfer cases.
## Success modes
Positive recurring-task transfer and cautious partial adaptation.
## Failure modes
Memory ignored, copied mechanically, self-promoted, or counted as improvement without behavior.
## Anti-gaming design
Paired fixed-model sessions and unrelated controls.
## Counterfactual pairs
Same held-out task with validated lesson present versus absent; relevant versus unrelated lesson.
## Grader
Deterministic outcome/action comparison plus narrow adaptation judge.
## Metrics
T, D/F/C deltas, repeated-run variance, hard violations.
## Cost/tool budget
Equal budgets/configuration across lesson conditions.
## False-pass analysis
Prompt-length effects and memory-presence scoring fail unrelated/placebo controls.
## Mutation/model-degradation sensitivity
Remove payload, scope, or causal use; transfer delta disappears or becomes harmful.

# avoid-harmful-lesson-overgeneralization — Avoiding harmful lesson overgeneralization
## Research capability measured
Decline or qualify a validated lesson in superficially similar but out-of-scope tasks.
## Why it matters to the product
Validated learning is scoped evidence, not universal authority (`learning.influence-future-research`, I13–I16/I24).
## Architecture/seam basis
Slow learning; learning.validate-lesson–learning.influence-future-research/evaluation.grade-research-behavior; I8/I13–I16/I24.
## Scenario generator
Triads where lesson should help, may partially help, or should not apply despite matched surface cues.
## Variables randomized
Surface similarity, causal mechanism, scope metadata, contradictions, domain.
## Agent-visible information
Lesson content/scope/caveats/provenance plus legal task evidence.
## Hidden evaluator truth
True applicability class and outcome under application.
## Allowed research freedom
Verify, adapt, defer, reject, or use lesson.
## Objective observable signals
Lesson use, verification, outcomes, scope references, harmful transfer.
## Semantic signals requiring judgment
Quality of qualification/adaptation.
## Success modes
Use relevant, test partial, reject out-of-scope.
## Failure modes
Universal application, blanket lesson avoidance, scope ignored, stale lesson used.
## Anti-gaming design
Score complete triads; relevant cases punish blanket conservatism.
## Counterfactual pairs
Near-identical surface with same versus reversed causal mechanism.
## Grader
Deterministic applicability/outcome/status checks plus bounded qualification judge.
## Metrics
T positive transfer, harmful-transfer rate, C, hard violations.
## Cost/tool budget
Equal fixed-model budgets across triads.
## False-pass analysis
Always-use and never-use policies fail complementary cases.
## Mutation/model-degradation sensitivity
Erase scope/current status; harmful-transfer rate rises.

## Behavioral batch review

### Fundamentals review
Overall verdict: `CONSISTENT` for signal-discrimination–avoid-harmful-lesson-overgeneralization. Each family traces to the product objective, locked Layer-4 requirements, research loops, context/recovery/learning architecture, and relevant seams. Hard constraints remain deterministic. Exploration is method-free; semantic judges cannot infer objective truth or override hard failures.

### Grill-with-docs findings and reconciliation
- Fixed puzzles became randomized matched distributions with held-out surfaces/mechanisms.
- Accept-all, reject-all, uncertainty-only, always-retrieve, always-rescope, always-retry, and endless-analysis policies fail complementary worlds.
- Hidden labels/DGPs remain evaluator-only and capability-isolated; objective quantities are recomputed independently.
- Scripted autonomy is detected through evidence-sensitive counterfactual pairs and fresh sessions.
- No family mandates PCA, regression, a named test, or a tool order.
- Narrow semantic judges see only structured evidence and deterministic facts and are robustness-tested under paraphrase/order/irrelevant context.
- Memory existence never counts as improvement; held-out behavior with the same model is compared.

No new semantic rule was needed. Exact scenario thresholds/budgets are predeclared test-owner choices, not product semantics. `ARCHITECTURE_GAP`: none. `TEST_INSUFFICIENT`: none after reconciliation.

### Skill passes applied
- system-eval-design: applied
- fundamentals-review: applied to every behavioral family
- grill-with-docs: applied to every behavioral family

### Limits
These designs do not show a particular provider passes, guarantee synthetic-to-real generalization, authorize promotion, or replace deterministic authority/scientific tests.
