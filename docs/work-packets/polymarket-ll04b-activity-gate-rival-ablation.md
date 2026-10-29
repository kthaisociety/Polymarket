# Work packet

## Identity

- Packet: LL-04b activity-gate component rival ablation
- Owning architecture block: Data foundation and authored low-latency investigation
- Semantic transition or responsibility: one immutable LL-04a comparison to common-support,
  quiet-only, recent-activity-only, and joint-gate paired economic populations and contrasts
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the uncommitted
  low-latency corpus, H1/H3/H5, LL-00, LL-04a, and acquisition packets recorded in this worktree

## Objective

Make the H4 taker hypothesis falsifiable against its two component rivals without changing the
parent attempts, gate thresholds, feature history, outcome path, or terminal economics.

## Context boundary

- Global authority loaded: repository and Chronos `AGENTS.md`, `CONTEXT.md`, locked decisions,
  invariants, semantic architecture map, and time-series feature-design principles.
- Owning block and transition contract: data-foundation `README.md`, transition index,
  `IMPLEMENTATION.md`, `data.build-information-set`, and the LL-00/LL-04a packet contracts.
- Relevant adjacent interfaces: `ActivityGateComparison`, its exact decisions and economic
  summaries, the H3/H5 parent attempt types, and sampled-process evidence E03/E10/E11/E16/R17/P19.
- Explicitly excluded work: selecting or fitting thresholds; reading quote values; changing H3/H5
  signals, actions, costs, or exits; event aggregation; maker cancellation; fill/queue simulation;
  protected evaluation; and live trading.
- Assumptions: component rivals are evaluated on the same complete-history support. A point with
  either feature missing enters only the ungated population, never a component or joint rival.

## Feature candidate revision memo

### Exact question and ancestry

If the fixed joint LL-04a gate appears better than its unchanged H3/H5 parent, is the result
incremental to (a) merely removing feature-warm-up attempts, (b) a maximum-quiet-duration rule
alone, and (c) a minimum-recent-source-event-count rule alone?

The sampled-process ancestry supports only a duration-dependent arrival mechanism. State plus
staleness improved event-macro Brier by 27.63% and won 112/113 chronological event comparisons;
the later no-refit law also improved materially. Five-minute and event-stratified robustness
preserved long-quiet hazard collapse. Those sources observe sampled probabilities, not L2 source
messages, and their numerical hour-scale parameters do not transfer to seconds-level collector
activity. The protected continuous-arrival candidate was also rejected on coverage, failure rate,
and concentration. LL-04b therefore adds rivals but no threshold value or positive prior.

### Decision, target, maturity, populations, and missingness

- Decision, parent population, target, maturity, costs, and horizon are exactly LL-04a.
- `UNGATED`: all ordered parent attempts, including missing feature history.
- `COMPLETE_HISTORY`: attempts whose quiet and recent-count components are both known.
- `QUIET_ONLY`: complete-history attempts satisfying only the fixed quiet threshold.
- `RECENT_ACTIVITY_ONLY`: complete-history attempts satisfying only the fixed count threshold.
- `JOINT`: attempts satisfying both clauses; this must equal LL-04a `gated` exactly.
- `None` feature history never becomes a component failure or zero; it is isolated through the
  `COMPLETE_HISTORY - UNGATED` contrast.
- Every population is an ordered subset by parent index. No population regenerates an attempt.

### Required contrasts and falsifiers

Each named contrast is left minus right and reports attempt/scorable coverage, net touch PnL sum
and mean, one-share collateral-time efficiency, displayed-quantity PnL, and displayed collateral-
time efficiency:

1. `COMPLETE_HISTORY - UNGATED`: warm-up/missing-history selection diagnostic, not alpha.
2. `QUIET_ONLY - COMPLETE_HISTORY`: marginal quiet rule.
3. `RECENT_ACTIVITY_ONLY - COMPLETE_HISTORY`: marginal count rule.
4. `JOINT - COMPLETE_HISTORY`: full gate on common support.
5. `JOINT - QUIET_ONLY`: incremental count clause.
6. `JOINT - RECENT_ACTIVITY_ONLY`: incremental quiet clause.

Reject the joint mechanism if its apparent improvement is only warm-up removal, if neither
component has a stable marginal effect, or if the joint rule adds no stable collateral-time value
over both component rivals. A lower PnL sum caused by fewer trades is not alone a failure; coverage,
mean, efficiency, sign balance, and later chronological concentration remain jointly required.

## Change boundary

- Permitted files or components: LL-04a gate module and tests, public Polymarket exports,
  data-foundation implementation map, low-latency hypothesis/status documentation, and this packet.
- Allowed state effects: none; the ablation returns immutable derived summaries and contrasts.
- Forbidden state effects: threshold selection, attempt mutation/regeneration, feature imputation,
  source-data changes, fitting, finding/promotion state, protected exposure, or trading authority.

## Correctness

- Governing invariants and decisions: I1 temporal admissibility, I2 fitted-state legality, I5
  identity, I6 no fallback, I11 immutable evidence, I12 ancestry, I13 provenance, I17 explicit
  failure, I21 evaluation is not training, I23/I26 target maturity separation, and I24 environment.
- Concrete failure modes: comparing component gates on different history support; treating missing
  history as a failed component; regenerating parent attempts; losing parent order; silently using
  different thresholds; allowing `JOINT` to differ from LL-04a `gated`; reversing contrast signs;
  or converting unresolved terminal PnL to zero.
- Expected inputs and outputs: one validated `ActivityGateComparison`; five exact population
  summaries and six ordered left-minus-right contrasts tied to that comparison.
- Violating mutation or counterexample: include a warm-up loss in `COMPLETE_HISTORY` and the quiet
  rule receives false credit; relabel `JOINT - QUIET_ONLY` as the reverse and incremental count
  evidence changes sign without changing data.
- Required local tests/evals: all five dispositions, exact population indices/order, common support,
  joint identity, unresolved preservation, exact contrast arithmetic/direction, immutable-result
  mutation rejection, and both H3/H5 compatibility through the parent comparison.
- Required integration evidence: LL-00/LL-04a/H3/H5 tests, full Polymarket adapters, proportionate
  Chronos tests, strict static checks, documentation index generation, and `git diff --check`.

## Completion evidence

- The rival-ablation API and public exports exist with no threshold defaults or fitting path.
- Deterministic adversaries prove exact populations, common support, joint identity, and contrast
  signs/arithmetic.
- Focused, Polymarket, and proportionate Chronos suites plus strict static checks pass.
- Architecture and hypothesis status distinguish sampled-process mechanism transfer from numerical
  threshold transfer and preserve the absent production L2/execution evidence.
- A receipt records hashes, verification, and remaining empirical dependencies.

## Boundary revisions

None.

## Transition receipt

### Result

- Packet: LL-04b activity-gate component rival ablation
- Status: `COMPLETE`
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the recorded
  uncommitted low-latency program
- Resulting repository state: five immutable rival populations and six fixed-direction economic
  contrasts exported through the Polymarket adapter

### Delivered state delta

- `book_activity_gate.py` now exposes common-history, quiet-only, recent-activity-only, and joint
  subsets beside the exact LL-04a ungated population.
- The joint and ungated endpoints must reproduce the parent comparison exactly. All populations
  retain ordered parent indices and unchanged attempt objects; all contrasts are left minus right.
- No source data, thresholds, attempts, research state, protected evidence, or trading state changed.
- Architecture, hypothesis-program, active-study, and packet status document the rival boundary and
  the non-transferability of sampled hour-scale parameters to L2 seconds.

### Evidence

- Twelve focused LL-04a/LL-04b adversaries passed.
- Sixty-six adjacent LL-00/corpus/H3/H5 tests passed.
- The full Polymarket adapter suite passed: 141 tests.
- The proportionate Chronos suite passed: 510 tests, excluding only the two documented sandbox
  modules that require local HTTP behavior.
- Ruff formatting/checking across 34 Polymarket adapter files and full basedpyright passed.
- A mutation that changes stored contrast economics is rejected when the ablation recomputes from
  its exact parent comparison. The all-five-disposition fixture also proves common-support indices,
  endpoint identity, unresolved preservation, H3/H5 composition, and contrast signs/arithmetic.
- Source SHA-256:
  `892b83cc1d7eedd6bd675fa94a5f2c0b7a44221a1b32abb84790cb0903bd852c`.
- Test SHA-256:
  `9dfd5d3966f4843b3ba25d470e66f5cd88690d3551754be3450bbc35620d276e`.

### Knowledge carried forward

- The transferable prior is structural: activity/staleness can condition arrival. It is not a
  numerical quiet-duration or source-count threshold at L2 scale.
- A future positive joint result must survive common-history and both component rivals, identical
  parent economics, chronological event blocks, concentration checks, and execution evidence.
- Remaining dependencies are a deployed dual-clock collector, retained production L2 corpus,
  pre-inspection threshold policy, fees, measured order latency, fills, and partial-fill evidence.
- This receipt proves deterministic rival mechanics only. It does not prove activity-gate value,
  fills, maker cancellation, executable profitability, formal eligibility, or trading authority.

Post-close lineage note: LL-04c subsequently retained the complete H3/H5 parent definition in the
same comparison and exposed its pure economic summary/contrast helpers for chronological campaign
composition. The hashes above identify the LL-04b close-time version; current hashes and
verification are recorded in the LL-04c receipt.
