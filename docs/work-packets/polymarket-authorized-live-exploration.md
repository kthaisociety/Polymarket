# Work packet

## Identity

- Packet: `polymarket.compose-authorized-live-exploration`
- Owning architecture block: Data foundation, composed with open-ended exploration.
- Semantic transition or responsibility: Turn one live, read-only, temporally registered
  Polymarket contract tape into an exact non-protected `AuthorizedDataView` and execute unchanged
  researcher-authored analysis through the existing `AnalysisHarness`.
- Input repository state: `historical checkpoint fdac9ca9` on
  `codex/polymarket-time-series-research`.

## Objective

Given explicit contract IDs, an explicit aware research decision time, and bounded authored Python,
the public Chronos application path returns one provisional `StructuredObservation` whose actual
access provenance resolves to the exact live registration and whose values contain no observation
with `available_at` after the decision time.

## Context boundary

- Global authority loaded: `AGENTS.md`, `CONTEXT.md`, locked decisions, invariants, architecture,
  data lifecycle, test strategy, alignment policy, and sandbox authority specification.
- Owning block and transition contract: data-foundation and exploration block maps;
  `data.register-observations`, `sandbox.authorize-execution`, `sandbox.execute-analysis`,
  `sandbox.record-provenance`, and `observation.assemble-analysis-result`.
- Relevant adjacent interfaces: `InformationSetBuilder`, `AuthorizedDataView`, `CapabilityPolicy`,
  `AnalysisHarness`, the existing Polymarket ingestion result, and the fail-closed `human_ro` smoke.
- Explicitly excluded work: scientific feature/label/model defaults, outcome labels, formal
  candidates, development evaluation, freeze, protected exposure, promotion, durable memory,
  external-system changes, and production writes.
- Assumptions: live fills are exploratory development data only; the existing
  `polymarket-onchain-block-inclusion/v1` rule and snapshot caveats remain unchanged.

## Change boundary

- Permitted files or components: Chronos Polymarket adapter composition, focused tests, public CLI
  navigation, data-foundation/exploration implementation maps, and this packet.
- Allowed state effects: production reads through proved `human_ro`, in-memory registration,
  in-memory artifacts, bounded stdout containing no credentials, test-local temporary files, and
  committed research-only documentation/artifacts.
- Forbidden state effects: database writes, credential output or persistence, implicit current
  time, protected access, scientific promotion, or external-system mutation.

## Correctness

- Governing invariants and decisions: I1, I9, I13, I14, I17, I18, and I24; open-ended authored
  method, pre-read authorization, harness-observed provenance, explicit time identity, and
  provisional epistemic status.
- Concrete failure modes: run the live smoke but never expose values to the sandbox; construct a
  view from raw fills instead of the exact registration; admit a post-decision observation; expose
  protected or undeclared fields; record requested rather than actual access; rewrite authored
  code; treat exploratory output as a finding; print a DSN or credential; or convert a failed live
  read into fixture success.
- Expected inputs and outputs: exact contract IDs, environment identity, aware decision time, and
  authored source produce a sanitized live-ingestion receipt plus one provisional structured
  observation and actual access lineage.
- Violating mutation or counterexample: bypass `InformationSetBuilder` and put every registered
  observation in the view; the temporal-cutoff regression must become red.
- Required local tests/evals: missing-DSN fail-closed CLI, temporal-cutoff view, actual field-access
  provenance, exact registration identity, unchanged authored computation, and protected/formal
  status absence.
- Required integration evidence: execute the public command against one real production contract
  under proved `human_ro`, retain the exact source/registration/code/result identities, and report
  only exploratory claims.

## Completion evidence

- Focused adapter/exploration tests pass.
- The public live command runs real authored analysis through `AnalysisHarness`.
- A reproducible exploratory memo records question, exact evidence refs, coverage, observations,
  rival explanations, limitations, and falsifiers.
- Proportionate static checks and the complete Chronos quality gate pass.
- Documentation matches the executable path and remaining red gates.
- A transition receipt closes this packet and the coherent Chronos delta is committed locally.

## Boundary revisions

- The first live authored run returned a 6,147-byte structured result. The sandbox correctly
  externalized it past the inline threshold, but the CLI process owned only an in-memory
  `ArtifactStore`, so exit made the result undrillable. The packet expands within the same
  `artifact.persist-analysis-output` dependency to let an operator select an explicit artifact
  directory and persist exact digest-verified sandbox artifacts. Authored code receives no path or
  filesystem capability.
- The complete gate then exposed that `scripts/check.sh` did not compose the adapter source path,
  although focused verification supplied it manually. The packet expands the gate script so
  complete verification uses the same declared `src` composition as the public live commands.
  No external-system or sibling-research code changes.

## Transition receipt

### Result

- Packet: `polymarket.compose-authorized-live-exploration`
- Status: **COMPLETE**
- Input repository state: `historical checkpoint fdac9ca9` on
  `codex/polymarket-time-series-research`.
- Resulting repository state: the local commit containing this receipt on the same branch.

### Delivered state delta

- Files and interfaces changed: shared proved read-only database composition; registered
  Polymarket `InformationSet` to requested wide `AuthorizedDataView`; public live authored-analysis
  command; exact artifact and sanitized receipt persistence; focused regressions; aligned README,
  implementation maps, and quality-gate composition.
- Behavior added, removed, or preserved: explicit contract IDs, an aware decision time, requested
  fields, and unchanged authored code now produce one provisional observation with actual access
  lineage. The existing smoke remains fail-closed and reuses the same `human_ro` proof. No
  scientific method, feature, label, or model default was added.
- Allowed state effects observed: production SELECT reads, immutable in-memory registrations,
  operator-selected study artifacts/receipts, test-local files, and non-secret stdout.
- Documentation status updated: public operation, code paths, live acceptance, remaining red gates,
  and the negative study now match the executable boundary.

### Evidence

- Tests and evals run: `PATH=/home/tage/.local/bin:$PATH ./scripts/check.sh` outside the
  socket-restricted sandbox; `.venv/bin/research-agent verify --json`; focused Polymarket tests and
  repeated public live commands recorded in the study receipts.
- Results: Ruff format and lint clean; basedpyright `0 errors, 0 warnings, 0 notes`; `406 passed`;
  verification `10 HARNESS_GREEN`, `5 EXPECTED_RED`, `0 UNEXPECTED_GREEN`, `0 HARNESS_BUG`.
- Boundary/debug observations: an all-catalog coverage read was unusable without bounded scope; the
  packaged one-contract smoke succeeded with 60,518 fills and 242,072 observations; the first
  authored result correctly externalized beyond the inline limit but exposed the in-memory artifact
  lifetime defect; exact persistent artifacts repaired that defect. Repeated cutoff-scoped results
  kept identical result bytes while a moving backward cursor changed registration/information-set
  identity, confirming the documented snapshot limitation.
- Violating mutation or counterfactual demonstrated: the temporal-cutoff regression admits only the
  first of two fills at an intermediate decision time and would fail if the view bypassed
  `InformationSetBuilder`; incomplete wide rows, unknown fields, missing DSN, artifact conflicts,
  and receipt conflicts fail explicitly.
- Integration evidence: two real production contracts produced exact registered legal views and
  sandbox observations. The same-direction-trade falsifier reduced the apparent buy-minus-sell
  reversal from `-0.0008446` to approximately zero (`+0.00000036`), while opposite-direction
  comparison enlarged it to `-0.0019848`; the raw-flow idea was rejected and retained as negative
  exploratory evidence.

### Knowledge carried forward

- Decisions and assumptions relied upon: predictor availability uses
  `polymarket-onchain-block-inclusion/v1`; decision time is explicit; only requested fields enter
  the grant; exploratory evidence cannot self-formalize or promote.
- New facts discovered: live registered values can now traverse the real sandbox path; the studied
  raw flow reversal is largely transaction-direction mechanics; exact study bytes can remain stable
  while cursor-vintage identity legitimately changes.
- Unresolved uncertainty: contract question/event identity, historical midpoint data,
  resolution-availability time, event groups, immutable database snapshots, and cross-event
  independence remain unavailable.
- Remaining reds or follow-up dependencies: quote-based labels require registered historical book
  state; grouped research requires authoritative event identity; any protected study requires
  retained immutable input bytes or an external snapshot identity; the production proof catalog
  still marks `exploration-to-development-evidence` expected red.

This receipt does not prove a predictive feature, formal candidate, development improvement,
causal effect, protected backtest, validated finding, trading value, or generalization beyond the
two exact low-price contract tapes. It proves the live registration-to-exploration application path
and preserves one reproducible exploratory negative result.
