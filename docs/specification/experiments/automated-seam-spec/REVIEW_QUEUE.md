# Automated seam-spec human review queue

Generated candidate contracts are experimental and not canonical. Ranking considers scientific risk, authority risk, downstream dependency count, and false-success plausibility.

## 1. USER_DECISION_REQUIRED

None.

The implied-gap seams artifact.retrieve-authorized-content, target.define-outcome, knowledge.return-retrieved-evidence, formalization.create-candidate, feature.revise-from-diagnostics, freeze.assess-eligibility, backtest.bind-protected-view, and learning.influence-future-research were derivable from already locked principles without choosing new scientific meaning. A concrete target/lesson/request instance may still require human input when its supplied semantics are genuinely unresolved; the seam contracts preserve that outcome rather than defaulting it.

## 2. ARCHITECTURE_CONFLICT

None.

## 3. INSUFFICIENT_SPECIFICATION

None.

## 4. TEST_INSUFFICIENT

None among action.authorize-request–learning.influence-future-research.

Calibration note outside this generated range: canonical `action.decode-intent` retains the previously
identified T2 weakness. A test-only generic decoder could pass while production decoding remains
hard-coded. See `docs/architecture/evals/canonical-transition-comparison.md`.

## 5. CANDIDATE_CONSENSUS — HIGH risk

Ranked review bands:

1. **Protected evidence and irreversible authority:** freeze.assess-eligibility–governance.retry-privileged-operation. Freeze, permits, exact protected views, exposure, backtest execution, immutable evidence, validation, findings, ledger, and privileged idempotency carry the highest scientific and authority consequence.
2. **Temporal legality and learning:** data.register-observations–data.prove-temporal-substrate and training.fit-system–ledger.record-trial-lineage. These prevent availability leakage, target-maturity leakage, global preprocessing fit, prediction-time learning, silent recipe fallback, and erased selection history.
3. **Runtime authority and semantic mutation:** action.authorize-request–trajectory.append-event and runtime.run-bounded-episode. These protect current-target authorization, provenance, observation/state separation, causal feedback, independent validation, atomic commit, repair, and bounded orchestration.
4. **Exploratory sandbox and feedback:** sandbox.authorize-execution–observation.assemble-analysis-result, knowledge.retrieve-evidence–knowledge.return-retrieved-evidence, and research.continue-from-exploration. These preserve open-ended computation while constraining information/side effects and proving returned semantics—not hidden access—change behavior.
5. **Formal scientific identity:** formalization.create-candidate–formalization.version-material-change. These distinguish candidate, formal definition, compiled representation, materialization, set/system identity, diagnostics, and immutable version lineage.
6. **Context, reporting, behavior, and learning:** report.render-finding, context.checkpoint-episode–learning.promote-lesson, and learning.publish-to-knowledge–learning.influence-future-research. These preserve finding substance, reconstructibility, honest behavioral evidence, independent lesson promotion, scoped knowledge publication, and causal future use.

## 6. CANDIDATE_CONSENSUS — MEDIUM/LOW risk

Ranked MEDIUM seams:

1. **artifact.persist-output** — immutable artifact/ref integrity is foundational to progressive disclosure.
2. **observation.translate-analysis-failure** — safe diagnostic translation must not leak secrets or fabricate success.
3. **artifact.persist-analysis-output** — exploratory artifacts must not become formal scientific objects implicitly.
4. **research.repair-exploratory-action** — repair must retain failure ancestry and reacquire authority.
5. **ledger.record-rejected-lesson** — rejected lessons remain durable history without becoming universal prohibition.
6. **provider.authenticate-adapter** — provider authentication remains operational, secret-contained, and replaceable.

There are no LOW-risk seams in action.authorize-request–learning.influence-future-research.
