# Work packet

## Identity

- Packet: LL-04a activity-conditioned taker participation gate
- Owning architecture block: Data foundation and authored low-latency investigation
- Semantic transition or responsibility: exact H3/H5 attempt screen plus LL-00 activity series to
  a paired gated-versus-ungated economic diagnostic
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the uncommitted
  low-latency corpus, H1/H3/H5, capture-command, and LL-00 packets recorded in this worktree

## Objective

Apply one explicit activity gate at each existing H3/H5 signal time and report an immutable paired
comparison that preserves every parent attempt, terminal missing value, touch-economics field, and
source identity.

## Context boundary

- Global authority loaded: repository and Chronos `AGENTS.md`, `CONTEXT.md`, locked decisions,
  invariants, semantic architecture map, and the time-series feature-design principles.
- Owning block and transition contract: data-foundation `README.md`, transition index,
  `IMPLEMENTATION.md`, `data.build-information-set`, plus the H3/H5 and LL-00 packet contracts.
- Relevant adjacent interfaces: `PostJumpReversalScreen`, `DepthImbalanceScreen`, their exact
  attempts/terminal statuses, `BookActivitySeries`, and prior arrival evidence E16/R17/P19.
- Explicitly excluded work: signal regeneration, threshold fitting, maker orders, open-position
  cancellation, widening, queue/fill simulation, fees beyond the parent definition, cross-corpus
  event aggregation, protected evaluation, and live trading.
- Assumptions: every parent attempt decision is triggered by its definition's reference leg and
  must have one exact LL-00 point at `(reference_leg, decision_at)`; absence is an identity failure,
  while a present point with incomplete history is an explicit abstention.

## Feature candidate memo

### Exact question and ancestry

For an unchanged LL-03 or LL-05 taker screen, does participating only when the reference leg's
collector-time quiet duration is at most a fixed threshold and its fixed-window prior source-event
count is at least a fixed threshold improve net displayed-touch PnL and displayed collateral-time
efficiency relative to all original attempts?

The parent is LL-00, which descends only the sampled-process arrival mechanism. The later no-refit
arrival result was strong, but its protected implementation was rejected and neither result was
directional or executable. LL-04a is therefore a new quote-based participation hypothesis, not a
continuation or revival of the protected candidate.

### Decision, target, maturity, and missingness

- Decision: the exact parent attempt `decision_at`; no nearest/as-of activity join is permitted.
- Population: every raw attempt emitted by one exact H3 or H5 screen, including unentered,
  cancelled, missing-exit, and truncated attempts.
- Action: `PASS` only when both fixed activity clauses pass. Missing quiet duration or an incomplete
  recent window always abstains; no imputation is allowed.
- Target: the parent attempt's unchanged `net_touch_pnl_per_share`, terminal status, displayed
  diagnostic quantity, and elapsed holding/collateral time. The label matures only at the parent's
  `terminal_at`. `None` remains unresolved and never becomes zero.
- Horizon: inherited elapsed parent holding/action policy; LL-04a cannot change it.

### Semantic feature and rule table

| Input/rule | Mapping | Fitted state | Failure behavior | Falsifier |
|---|---|---|---|---|
| `quiet_duration <= maximum_quiet_duration` | Exact LL-00 point at parent signal time; elapsed collector duration. | None; threshold is required identity. | Missing history abstains; absent exact point fails composition. | No paired improvement or effect concentrated in capture anomalies. |
| `recent_source_event_count >= minimum_recent_source_event_count` | Exact fixed LL-00 `[t-window,t)` count, excluding current burst. | None; threshold is required identity. | Incomplete window abstains; no zero fill. | No incremental value over quiet duration or one market supplies the result. |
| Parent attempt outcome | Reuse the same frozen attempt object and its terminal record. | None. | Unentered and unresolved remain counted but unscored. | Improvement disappears when coverage/missingness and capital time are preserved. |

The rule reports separate quiet-only, recent-only, joint inactivity, and missing-history abstentions.
It reports attempt/entry/scorable/unresolved counts; positive/zero/negative scorable counts; mean and
sum net touch PnL; holding duration; one-share displayed collateral-seconds; and displayed-quantity
weighted diagnostic PnL/collateral efficiency. These are displayed-book diagnostics, not fills.

### Development protocol and stopping rule

The mandatory baseline is the same ordered parent attempt tuple with no activity filter. One
gate evaluation creates no new trades: the gated set is a subset by parent index. Gate thresholds
must be fixed before quote values are inspected or selected inside chronological development folds
with explicit parent-trial ancestry; this implementation supplies no defaults. Later evidence must
be reported by event family and chronological block, with missing-label coverage, sign counts,
concentration, and the identical cost definition.

Stop or reject if mean/sum net touch PnL or collateral-time efficiency does not improve, if entry or
scorable coverage becomes operationally negligible, if unresolved frequency worsens materially,
or if gains depend on one market/time block, collector skew, fallback-like timestamps, or a
post-inspection threshold. Recommendation now: `EVALUATE` only after real retained books exist.

## Change boundary

- Permitted files or components: one LL-04a gate module, its one-to-one adversarial test, public
  exports, data-foundation implementation map, low-latency program/status, and this receipt.
- Allowed state effects: none; the evaluator returns immutable decisions and summaries.
- Forbidden state effects: parent attempt mutation, raw data changes, threshold selection, missing
  value imputation, new strategy execution, finding/promotion state, or trading authority.

## Correctness

- Governing invariants and decisions: I1 temporal admissibility, I2 fitted state, I5 identity, I6
  no fallback, I11 immutable evidence, I13 provenance, I17 explicit failure, I21 evaluation is not
  training, I23/I26 label maturity separation, and I24 environment identity.
- Concrete failure modes: joining the nearest activity point; evaluating at arrival instead of
  signal; filtering parent attempts before the ungated baseline is recorded; treating unentered or
  unresolved attempts as zero PnL; changing holding periods after gating; mismatching snapshots,
  scope, definitions, or legs; using current burst in the prior count; or reporting per-capital
  efficiency without its coverage/denominator.
- Expected inputs and outputs: exact H3/H5 screen, exact matching LL-00 series, and explicit gate
  identity/parent/leg/thresholds; one decision per parent attempt plus paired summaries and deltas.
- Violating mutation or counterexample: replace exact join with latest-as-of and an attempt between
  activity points incorrectly receives old legal state; coerce `None` PnL to zero and a missing-exit
  gate appears safer than it is.
- Required local tests/evals: definition failures, exact source/scope/parent/leg binding, no as-of
  fallback, every gate disposition, unchanged attempt identity/order, H3 and H5 composition,
  unentered/unresolved preservation, exact PnL/sign/collateral-time math, and empty-scored subset.
- Required integration evidence: LL-00/corpus/H3/H5 tests, full Polymarket suite, broader Chronos
  suite, and strict static checks.

## Completion evidence

- Focused LL-04a and adjacent strategy tests pass.
- Full Polymarket and proportionate Chronos suites pass.
- Ruff, formatter, basedpyright, documentation-index generation, source/test hashes, and
  `git diff --check` pass.
- Owning implementation and hypothesis status state that this is a taker subset diagnostic, not
  maker cancellation or empirical improvement.
- The receipt preserves the missing live-corpus and execution-evidence dependencies.

## Boundary revisions

None.

## Implementation receipt

- Implemented `book_activity_gate.py` with exact H3/H5 parent, snapshot, coverage, scope, leg,
  window, and signal-time feature binding; immutable paired decisions; separate gate dispositions;
  and coverage-first economic summaries.
- The gate keeps the parent attempt objects and ordering unchanged. The ungated population is
  mandatory, the gated population is only its `PASS` subset, and unresolved entered attempts are
  counted but never scored as zero.
- One-share and displayed-quantity touch PnL are reported with their exact holding and
  collateral-second denominators. These are displayed-book diagnostics, not execution evidence.
- Nine focused LL-04a adversaries, 63 adjacent LL-00/corpus/H3/H5 tests, 138 Polymarket adapter
  tests, and 507 proportionate Chronos tests passed. Ruff formatting/checking and full basedpyright
  also passed.
- Source SHA-256:
  `7d5d5e72136413c971d4562db7c0b567894408f509849ec5c6250e0eb70d2312`.
- Test SHA-256:
  `500e19d745d62f9c067ab5ff195b56b207b6df483a279e559cbe02b79cd002f3`.
- Empirical disposition: `EVALUATE AFTER CAPTURE`. No production L2 bytes, fixed empirical gate
  thresholds, measured order latency, fees, fills, partial fills, or maker queue/cancel evidence
  were available in this runtime; no H4 improvement or trading claim was produced.

Post-close lineage note: LL-04b subsequently extended the same module and adversarial file with
component-rival ablations. The hashes and nine-test count above identify the LL-04a close-time
version; successor hashes and verification are recorded in the LL-04b and LL-04c receipts.
