# Work packet

## Identity

- Packet: LL-04c chronological activity-gate campaign
- Owning architecture block: Data foundation and authored low-latency investigation
- Semantic transition or responsibility: explicit non-overlapping chronological blocks of exact
  LL-04b ablations to immutable block, pooled, stability, and concentration diagnostics
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the uncommitted
  low-latency corpus, H1/H3/H5, LL-00, LL-04a/b, and acquisition packets in this worktree

## Objective

Make one fixed H4 taker policy evaluable across multiple markets and chronological capture blocks
without pooling away instability, missing outcomes, threshold identity, or concentration.

## Context boundary

- Global authority loaded: repository and Chronos `AGENTS.md`, `CONTEXT.md`, locked decisions,
  invariants, semantic architecture map, and time-series feature-design principles.
- Owning block and transition contract: data-foundation `README.md`, transition index,
  `IMPLEMENTATION.md`, `data.build-information-set`, and LL-00/LL-04a/b packet contracts.
- Relevant adjacent interfaces: `ActivityGateRivalAblation`, its exact population indices and
  economics, prior event-macro/early-late/concentration diagnostics, and H3/H5 parent identities.
- Explicitly excluded work: threshold selection or fitting, PnL-based model selection, overlapping
  capture blocks, event-family authority not present in the book corpus, maker behavior, fill/queue
  simulation, fees beyond parent definitions, formal validation, protected evaluation, and trading.
- Assumptions: one block is an explicit half-open collector interval. Its ablations may cover
  different markets but must lie fully inside the block and use one exact policy identity.

## Campaign candidate memo

### Exact question and ancestry

For one fixed LL-04a policy and one H3 or H5 parent family, does the joint activity gate improve a
predeclared displayed-touch economic metric relative to a predeclared LL-04b rival across
chronological non-overlapping capture blocks, rather than only in pooled observations or one block?

Earlier Polymarket studies repeatedly rejected candidates whose aggregate result hid early/late
instability, weak event breadth, or concentrated improvement. LL-04c transfers those diagnostics to
the quote-based H4 campaign. It does not transfer their thresholds or claim that collector blocks
are independent event families.

### Identity, populations, target, and maturity

- Campaign identity requires parent strategy kind, scope authority, recent window, maximum quiet
  duration, minimum recent source-event count, primary contrast, and primary metric.
- Blocks have explicit IDs and aware half-open collector bounds, are supplied in chronological
  non-overlapping order, and contain at least one LL-04b ablation.
- Every ablation must match campaign parent kind, scope, and fixed activity policy; its coverage
  must be contained by its block.
- Duplicate parent-attempt identities across ablations or blocks fail. No deduplication fallback is
  allowed.
- Each block and the pooled campaign recompute the five LL-04b populations and six contrasts from
  unchanged attempt objects. Empty or unresolved subsets remain explicit.
- Parent target, label maturity, cost, action delay, and horizon remain unchanged. A campaign
  neither rematures nor relabels attempts.

### Primary metric and stability semantics

The caller must predeclare one joint-versus-complete-history or joint-versus-component primary
contrast and one of three primary metrics. Warm-up and component-only contrasts remain diagnostics:

- net touch PnL per share mean change;
- one-share net touch PnL per collateral-second change;
- displayed-quantity net touch PnL per collateral-second change.

For that exact pair, LL-04c reports scored/missing block counts, positive/zero/negative block counts,
block-macro mean, early-half mean, late-half mean, and largest positive block share. The chronological
split occurs before missing block values are removed. No result field decides advancement.

### Falsifier and interpretation

Reject or revise if the primary improvement is non-positive in aggregate or block macro, fails in
either chronological half, wins too few scored blocks, is concentrated in one block, has material
missing/unresolved coverage, or does not survive both component rivals. Exact numerical advancement
ceilings remain a later authored development decision; this packet adds measurement, not selection.

Collector-time blocks establish temporal stability only. They do not establish event-family
breadth, market independence, fills, or executable returns. Those require separate semantic and
execution evidence.

## Change boundary

- Permitted files or components: one Polymarket activity-campaign module and adversarial test,
  minimal LL-04b economic helper exposure, public exports, data-foundation implementation map,
  low-latency hypothesis/status documentation, and this packet.
- Allowed state effects: none; campaign construction returns immutable derived evidence.
- Forbidden state effects: source or attempt mutation, threshold fitting/selection, silent
  deduplication, overlap, missing-value imputation, research-state promotion, or trading authority.

## Correctness

- Governing invariants and decisions: I1 temporal admissibility, I2 fitted state, I5 identity, I6
  no fallback, I11 immutable evidence, I12 ancestry, I13 provenance, I17 explicit failure, I21
  evaluation is not training, I23/I26 target maturity separation, and I24 environment identity.
- Concrete failure modes: accepting overlapping/out-of-order blocks; mixing H3 and H5 or different
  thresholds/scopes; accepting out-of-block source coverage; double-counting one attempt from two
  snapshots; pooling before block diagnostics; splitting early/late after dropping missing blocks;
  reversing the primary contrast; or treating unresolved economics as zero.
- Expected inputs and outputs: exact campaign definition and chronological blocks of LL-04b
  ablations; immutable block aggregates, pooled aggregate, and primary stability diagnostics.
- Violating mutation or counterexample: duplicate a profitable attempt in two block inputs and a
  naive pooled campaign doubles its edge; drop an unscored early block before splitting and the
  apparent early/late comparison changes chronology.
- Required local tests/evals: definition failures, block ordering/overlap, coverage containment,
  exact policy/scope/parent binding, duplicate-attempt rejection, five-population aggregation,
  pooled recomputation, unresolved preservation, primary metric direction, pre-missingness split,
  sign counts, concentration, empty-score behavior, H3/H5 composition, and mutation rejection.
- Required integration evidence: LL-00/LL-04a/b/H3/H5 tests, full Polymarket adapters,
  proportionate Chronos tests, strict static checks, docs generation, and `git diff --check`.

## Completion evidence

- Campaign definitions, blocks, aggregates, stability diagnostics, and public exports exist without
  defaults, fitting, validation, or state mutation.
- Adversaries prove chronology, identity, aggregation, missingness, contrast direction, and
  concentration mechanics.
- Focused, Polymarket, and proportionate Chronos suites plus strict static checks pass.
- Architecture and hypothesis status preserve absent production L2, semantic event-family, and
  execution evidence.
- A transition receipt records hashes, verification, and remaining empirical dependencies.

## Boundary revisions

None.

## Transition receipt

### Result

- Packet: LL-04c chronological activity-gate campaign
- Status: `COMPLETE`
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the recorded
  uncommitted low-latency program
- Resulting repository state: immutable fixed-policy collector-block, pooled, and primary-stability
  evidence over exact LL-04b ablations

### Delivered state delta

- `ActivityGateComparison` now retains the exact H3/H5 parent definition and rejects attempts whose
  decision lies outside retained source coverage.
- `book_activity_campaign.py` binds the market-independent parent recipe, activity policy, scope,
  primary contrast, and metric; validates non-overlapping half-open blocks and contained ablations;
  and rejects duplicate evidence.
- Every block and the pooled result recompute five rival populations and six contrasts. Stability
  retains missing blocks, sign counts, block macro, pre-missingness early/late halves, and positive-
  improvement concentration.
- No source bytes, attempts, thresholds, fitted state, protected evidence, durable research state,
  or trading state changed.

### Evidence

- Twenty-two focused LL-04a/b/c cases passed, including two parametrized collateral-time metrics.
- Seventy-six adjacent LL-00/corpus/H3/H5 tests passed.
- The full Polymarket adapter suite passed: 151 tests.
- The proportionate Chronos suite passed: 520 tests, excluding only the two documented sandbox
  modules that require local HTTP behavior.
- Ruff formatting/checking across 36 Polymarket adapter files and full basedpyright passed.
- Adversaries prove exact block/pooled populations, unresolved preservation, all three primary
  metric paths, chronological splitting before missing removal, sign/concentration arithmetic,
  complete parent-recipe binding, H3/H5 composition, overlap and coverage denial, duplicate-attempt
  denial, source-coverage identity, and result-mutation denial.
- Gate source SHA-256:
  `4b367973796c4a293a9a61c647a54f9ec9e4ef11912672c240ff1a9a3affed26`.
- Campaign source SHA-256:
  `234bd64ff535537da932bf7579d9f680e634fb4063c5eaecf5aeca1454f714b1`.
- Gate test SHA-256:
  `0ab91d9ca6f5e198e2b2ac05844953c7743ef1cfd1460c718fd0e8b07a95f474`.
- Campaign test SHA-256:
  `cb13103729663e9491ee7ddc9638ddeed5f6125f6ac926ab240ed5a2df4b5da2`.

### Knowledge carried forward

- A pooled H4 touch result is insufficient. It must survive exact component rivals, missing-aware
  chronological blocks, both temporal halves, and concentration diagnostics.
- Collector blocks measure temporal stability but are not a substitute for semantic event-family
  identity or independent market breadth.
- Remaining dependencies are a deployed dual-clock collector, retained production L2 corpus,
  pre-inspection thresholds and advancement standards, semantic event grouping, fees, measured
  order latency, fills, and partial-fill evidence.
- This receipt proves deterministic campaign mechanics only. It does not prove activity value,
  executable profitability, formal eligibility, protected validity, or trading authority.
