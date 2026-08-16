# Automated seam-specification experiment summary

Status: **complete for all non-deferred seams action.authorize-request–learning.influence-future-research; candidates only**

## Aggregate classification

| Classification | Count |
|---|---:|
| `CANDIDATE_CONSENSUS` | 75 |
| `USER_DECISION_REQUIRED` | 0 |
| `ARCHITECTURE_CONFLICT` | 0 |
| `INSUFFICIENT_SPECIFICATION` | 0 |
| `TEST_INSUFFICIENT` | 0 |
| **Total processed** | **75** |

decision.apply-validated-finding is explicitly `DEFERRED` in the canonical register and was not processed. mission.confirm-task–action.decode-intent were calibrated read-only and not regenerated.

## Breakdown by milestone

| Milestone | Seam range | Processed | Candidate consensus | High | Medium | Local | Composite |
|---|---|---:|---:|---:|---:|---:|---:|
| M1 — task identity/autonomous runtime | action.authorize-request–runtime.run-bounded-episode | 14 | 14 | 13 | 1 | 11 | 3 |
| M2 — temporal scientific data | data.register-observations–data.prove-temporal-substrate | 8 | 8 | 8 | 0 | 6 | 2 |
| M3 — sandbox/tools/retrieval | sandbox.authorize-execution–research.continue-from-exploration | 10 | 10 | 7 | 3 | 8 | 2 |
| M4 — formal feature/model/system identity | formalization.create-candidate–formalization.version-material-change | 10 | 10 | 10 | 0 | 9 | 1 |
| M5 — fitting/development research | training.fit-system–ledger.record-trial-lineage | 7 | 7 | 7 | 0 | 6 | 1 |
| M6 — freeze/protected evaluation | freeze.assess-eligibility–governance.retry-privileged-operation | 14 | 14 | 14 | 0 | 11 | 3 |
| M7 — reporting/provider/context pressure | report.render-finding–context.rebuild-after-loss | 4 | 4 | 3 | 1 | 3 | 1 |
| M8 — behavioral evidence | evaluation.grade-research-behavior | 1 | 1 | 1 | 0 | 0 | 1 |
| M9 — reflection/validated learning | learning.reflect-history–learning.influence-future-research | 7 | 7 | 6 | 1 | 6 | 1 |
| **Total** | action.authorize-request–learning.influence-future-research | **75** | **75** | **69** | **6** | **60** | **15** |

There are no LOW-risk seams in the processed range.

## Strongest architectural concerns exposed

1. **Authority laundering through identity repair.** action.authorize-request must preserve stale/foreign targets for rejection rather than substituting current state; backtest.authorize-request/backtest.bind-protected-view bind independent permits to exact protected resources.
2. **Exposure timing.** Protected evidence becomes irreversible at actual content/result disclosure, even if execution later fails; completion-only exposure tracking is invalid.
3. **Temporal boundaries are plural.** `available_at`, historical vintages, legal predictor information, and label maturity cannot collapse into row date or one “new data” event.
4. **Every learned quantity has one controlled home.** Imputation, scaling, PCA, selection, hyperparameters, models, and ensemble weights fit only inside legal `W_t`; materialization, prediction, evaluation, and reporting cannot learn.
5. **Progressive disclosure requires both meaning and retrieval.** IDs/refs alone are insufficient when the next decision depends on content; possession of a ref is never permission.
6. **Promotion status is not contagious.** Exploratory artifacts, diagnostics, reflections, and candidate lessons do not become formal objects, findings, Memory, or Skills without their explicit independent gates.

## Strongest test-design concerns

- Paired interventions and sentinel outcomes are required for runtime.continue-from-observation, observation.assemble-analysis-result, knowledge.return-retrieved-evidence, research.continue-from-exploration, feature.revise-from-diagnostics, development.revise-candidate, context.checkpoint-episode–learning.reflect-history, and learning.influence-future-research; endpoint sequence cannot prove feedback.
- Providers/consumers must be denied direct fixture, dataset, episode, artifact, ledger, and KnowledgeEnvironment access in causal tests.
- Full-history poison fixtures are required to catch hidden preprocessing fit and current-vintage historical backfill.
- Fault injection must cover every partial publication and irreversible-effect acknowledgement boundary.
- Graph/history tests must require losing trials, failures, denials, rejections, and exposures—not only the successful chain.
- Behavioral evaluations must state Level A–D honestly; authority/scientific violations cannot be averaged away by fluent output or efficiency.

## Creativity-restriction audit

No candidate imposes a predefined scientific-method catalog on exploration. sandbox.authorize-execution restricts only information and side-effect authority; sandbox.execute-analysis runs unusual permitted code unchanged; observation.assemble-analysis-result preserves unfamiliar structured returns; research.continue-from-exploration proves novel analysis can affect the next action. Rigor increases only at explicit formalization, freeze, protected evaluation, finding, and learning-promotion boundaries.

## Most important composite seams

- **runtime.continue-from-observation:** observation meaning changes next model-visible context/action.
- **runtime.run-bounded-episode:** complete bounded M1 organism including repair and idempotency.
- **data.advance-independent-clocks/data.prove-temporal-substrate:** independent predictor/label boundaries and full temporal substrate.
- **research.continue-from-exploration:** authorized open-ended exploration/retrieval causally changes behavior.
- **feature.revise-from-diagnostics/development.revise-candidate:** feature and model diagnostics causally drive versioned research decisions.
- **backtest.execute-scenario/ledger.preserve-scientific-history/governance.retry-privileged-operation:** exact protected simulation, reconstructible evidence graph, and once-only irreversible effects.
- **context.rebuild-after-loss/evaluation.grade-research-behavior:** reconstruction after transcript loss and honest behavioral evaluation.
- **learning.influence-future-research:** scoped validated learning causally changes future behavior.

## Calibration quality

Read-only calibration against mission.confirm-task–action.decode-intent was broadly consistent with manual reasoning and recovered project-specific subtleties: bounded exhaustion, semantic task versioning, usable context rather than opaque refs, and open-ended model intent. It reproduced the known useful action.decode-intent `TEST_INSUFFICIENT` concern: a test-only generic decoder can mask hard-coded production decoding. Because this was a local test-strength issue rather than systemic architectural disagreement, processing continued.

## Output paths

- Experiment root: `docs/specification/experiments/automated-seam-spec/`
- Human review queue: `docs/specification/experiments/automated-seam-spec/REVIEW_QUEUE.md`
- Study cards: `docs/specification/experiments/automated-seam-spec/study-cards/`
- Calibration: `docs/architecture/evals/canonical-transition-comparison.md`
- Candidate contracts: block-local `transitions/` directories under `docs/architecture/`

## Scope confirmation

- No candidate was canonicalized or marked `LOCKED`.
- No canonical mission.confirm-task–action.decode-intent contract or `SEAM_REGISTER.md` entry was edited.
- No production application code was changed.
- No executable application test or final system-level eval harness was implemented.
- The deferred downstream decision.apply-validated-finding seam was not processed.
