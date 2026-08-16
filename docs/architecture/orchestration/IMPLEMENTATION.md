# One-shot orchestration implementation map

Status: **executable verification framework; ten production compositions narrowly proved**.

- Production framework: `src/research_agent/verification/`
- Compatibility import: `tests/verification/eval_spec_harness.py`
- Harness self-tests: `tests/verification/test_eval_spec_harness.py`
- Transition contracts: [`transitions/`](transitions/)
- Planned orchestration definitions: work-package schema, dependency waves, ownership rules, evidence gates, repair protocol, and completion report.

`HARNESS_GREEN` now means a repository-registered adapter returned raw externally observed
production traces, and the catalog-owned proposition oracle independently validated the exact
component IDs and every required assertion. Adapter-supplied booleans or component names carry no
proof authority. Untrusted/registration-only mechanisms are `UNEXPECTED_GREEN`; adapter or catalog
defects are `HARNESS_BUG`; production execution regressions and falsified/absent compositions are
`EXPECTED_RED`.

Current deterministic composition status:

- `HARNESS_GREEN`: observation-to-next-action. It uses 18-row, 2-row, and deliberately
  missing-payload worlds with fresh stateless providers;
- `HARNESS_GREEN`: evidence-to-atomic-commit. An authority-produced inspection observation crosses
  `record_observation` and independent episode/state validation into one copy-on-write publication
  of terminal episode, state successor, stored idempotency result, and correlated trajectory event.
  Foreign and internally consistent forged authority bindings publish neither scientific effect;
  faults after episode, state, result, and event staging expose none and remain exactly retryable;
  exact replay returns one original effect; and a changed synthesis under the same key conflicts.
  Omitting any fault world, denial, correlated event, retry, or changed-payload conflict turns the
  catalog oracle red. The proof is one-process atomicity, not crash-durable persistence;
- `HARNESS_GREEN`: registered-data-to-legal-fit. Eight catalog-owned raw production worlds execute
  `ObservationRegistrar.register` -> `InformationSetBuilder.build` ->
  `TrainingSampleBuilder.build` -> `TrainingWindowSelector.select` -> `SystemTrainer.fit`. Paired
  interventions prove that a registered but unreleased poison changes neither legal rows nor the
  causal learned payload, while releasing that same scientific value changes both; predictor-only
  release changes `I_t` without `S_t`, label-only maturity changes `S_t` without `I_t`; a future
  revision stays absent from an earlier view; and an insufficient window records zero trainer
  calls. The oracle compares row contents and learned parameters rather than full fitted identity,
  because catalog/sample/window identity is expected to differ across intervention catalogs.
  Removing a required registered observation, learned-state payload, clock world, revision world,
  or insufficiency world turns the composition red;
- `HARNESS_GREEN`: development-to-protected-authority, frozen-system-to-immutable-run, and
  run-to-finding-or-rejection. Their paired domain-neutral workflow worlds execute the production
  `ScientificWorkflowCoordinator` under exact registered task/session/environment bindings. The
  catalog oracle independently checks evaluator-issued development evidence against a pre-issued
  freeze-eligibility registration; independently configured governance and validation grants;
  an authority-issued protected scope/binding/catalog; authorization before protected disclosure;
  exact frozen/system/scenario/scope propagation; complete immutable run sealing; fail-on-fit pure
  measurement; and distinct retained finding/rejection outcomes. Each execution first proves that
  the original substituted-authority-label path, the same-label/different-capability path, and
  changed protected binding/catalog paths fail with zero ledger or exposure effects. Removing one
  of those causal observations turns the authority composition red;
- `HARNESS_GREEN`: finding-to-report-invariance. The promoted workflow world resolves its exact
  authoritative finding/report/decision bundle through `CanonicalReportRegistry` and renders a
  machine-reconstructible report, while the rejection counterpart publishes no report;
- `HARNESS_GREEN`: authorized-exploration-to-next-action. The catalog compares low, high, and
  missing-meaning worlds that run identical authored code through the session-authorized
  `AnalysisHarness`. It verifies harness-observed field access, exact code/environment/view
  provenance, session-readable content-addressed stdout drill-down, packet projection, and distinct
  typed next actions selected by a fresh stateless packet-only fixture policy. Removing actual
  access or artifact evidence turns the proposition red. This proves runtime mechanics, not model
  or researcher quality;
- `HARNESS_GREEN`: context-loss-reconstruction. Paired open-question/closed-question worlds publish
  a production `EpisodeCheckpoint`, record transcript destruction, rebuild from the current
  checkpoint, and feed uninterrupted and rebuilt packets to fresh stateless fixture policies. The
  oracle compares exact task/state/episode/environment authority, plan, unresolved questions,
  provisional observation provenance, artifact refs, packets, and decoded actions. Dropping the
  open question from the rebuilt packet turns the proposition red;
- `HARNESS_GREEN`: failure-to-repaired-continuation. Controlled-failure and no-failure worlds run
  two turns through `AutonomousResearchRuntime.run_until_terminal`. The failure world retains a
  repairable structured failure, failed execution provenance, session-readable traceback, and the
  first observation in the second packet before the same episode executes corrected code. The
  no-failure world selects no repair. Both leave durable researcher state at version zero; removing
  traceback evidence turns the proposition red;
- `EXPECTED_RED`: the remaining 5 composites. The former learning trace is intentionally red: its
  own fixture registered the historical source and decision-authority labels, so it demonstrated
  scoped causality but not independent learning authority/currentness/lineage. In addition,
  privileged-retry-idempotency lacks uncertain-acknowledgement proof over irreversible effects;
- `UNEXPECTED_GREEN`: 0;
- `HARNESS_BUG`: 0.

The behavioral runner executes opaque harness-causality fixture envelopes for all 12 designed
families. Agent views contain no generator seed, order, or truth; case order is reproducibly shuffled
in evaluator-owned state, and public family metadata contains only family IDs. Fixture execution
reports `BehavioralExecutionStatus` separately from `HarnessValidity`. Even a perfect explicitly
evaluator-owned oracle remains `HARNESS_CAUSALITY_ONLY` with `ResearcherQuality.NOT_ASSESSED`.
These fixtures test grader mechanics, not the designed Level-D scientific scenarios or researcher
quality.

The registered workflow proof is intentionally narrower than an autonomous scientist. It proves
composition after an exact workflow has been registered; it does not prove that a model can yet
author, revise, select, or register formal systems and protocols through runtime actions. It also
does not claim durable crash recovery, report distribution/publication beyond the canonical
rendered finding artifact, or validated cross-task learning.

Verification:

```bash
PYTHONPATH=src:. .venv/bin/python -m pytest tests/verification -q
PYTHONPATH=src:. .venv/bin/python -m pytest -q
# See the final one-shot completion receipt for the current full-gate count.
```
