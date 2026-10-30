# Work packet

## Identity

- Packet: LL-00 dual-clock book activity and quiet-duration features
- Owning architecture block: Data foundation and dataset setup
- Semantic transition or responsibility: verified retained L2 source events to causal timing
  diagnostics and per-leg activity features
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the uncommitted
  low-latency capture, corpus, and H1/H3/H5 packets already recorded in this worktree

## Objective

Derive a provenance-bound, value-blind activity series from one verified dual-clock L2 snapshot so
Chronos can measure collector timing and later test H4 against identical ungated H3/H5 attempts
without using future events, row multiplicity, or venue timestamps as availability.

## Context boundary

- Global authority loaded: repository and Chronos `AGENTS.md`, `CONTEXT.md`, locked decisions,
  invariants, semantic architecture map, and relevant style guidance.
- Owning block and transition contract: data-foundation `README.md`, transition index,
  `IMPLEMENTATION.md`, and `data.register-observations`; the feature-design principles govern the
  authored feature meaning but grant no registration, fitting, or protected authority.
- Relevant adjacent interfaces: `BookCorpusSnapshot`, `BookEventRecord`, exact snapshot/delta
  sequence semantics, H3/H5 attempt labels, and prior arrival evidence E16/R17/P19.
- Explicitly excluded work: threshold selection, model fitting, H4 gate scoring, order/action latency
  inference, queue or fill simulation, protected evaluation, database access, and live trading.
- Assumptions: `(venue, available_at, reference_time, seq)` identifies one captured venue message
  within a row kind; multiple delta rows and legs may descend from that message; equal venue and
  collector times remain ambiguous because the retained schema does not distinguish a venue stamp
  from the collector fallback.

## Feature candidate memo

### Question and evidence ancestry

Later H4 asks whether activity available at an H3/H5 signal time improves the underlying attempt's
net touch outcome or capital-time efficiency relative to the exact ungated attempt population.
The prior sampled-probability arrival hazard used `log(1 + quiet run)` and the prior-24-increment
unchanged fraction. It improved later-cohort event-macro Brier from `0.26106` to `0.17392` and won
27/27 eligible events, but the exact protected system was rejected because only 65/100 decisions
were executable and concentration/failure gates failed. That ancestry supports an arrival feature,
not a book-direction or PnL claim.

### Decision, target, and maturity

- Decision: each distinct collector absorb time at which at least one exact source event affects a
  requested book leg. All source events at that time are coalesced before one point is published.
- Population: requested retained legs, beginning with their first in-window source event. No event
  before the half-open corpus start is inferred.
- Future H4 target: the already declared H3 or H5 attempt's terminal status, net displayed-touch
  PnL, and elapsed capital time under the identical strategy definition. It matures only at that
  attempt's recorded exit/cancel/truncation boundary.
- This packet creates no label or candidate result; it only makes the legal predictor history
  reproducible.

### Semantic feature table

| Name | Hypothesis and inputs | Temporal mapping and units | Fitted state | Failure behavior and falsifier |
|---|---|---|---|---|
| `quiet_duration` | Time since the previous distinct collector update affecting the exact leg may proxy update intensity. | `decision_time - previous_leg_event_time`, elapsed `timedelta`; current event is legal, future event is excluded. | None. | Missing on the first retained point. H4 is falsified if it does not improve an identical ungated strategy chronologically. |
| `recent_source_event_count` | Prior message intensity may distinguish equal quiet durations with different recent paths. | Count of coalesced source messages in `[t - recent_window, t)` for the same leg; current-time messages excluded. | None; `recent_window` is fixed identity. | Missing until the full elapsed window lies inside retained coverage. A threshold selected after values is not authorized. |
| `concurrent_source_event_count` | Same-time burst size is a capture diagnostic and possible rival, not a primary economic feature. | Number of source-message identities affecting the leg at exactly `t`. | None. | Must not create multiple decisions or row-order dependence. |
| `reference_delay_min/max` | Venue/collector clock differences diagnose skew and fallback contamination. | Signed `available_at - reference_time` across current source messages. | None. | Negative and exactly zero values remain visible. They cannot be relabeled as end-to-end action latency. |

Clock profiles use fixed nearest-rank `p50/p90/p95/p99` quantiles over nonnegative signed delays and
report negative, zero, and positive counts separately. Exact-zero delay is not assumed to be genuine
zero ingestion latency. Interarrival features use collector time exclusively.

### Later development protocol

The mandatory baselines are the identical ungated H3/H5 attempts, a clock-health-only exclusion,
and simple fixed activity gates. Event-family chronological partitions, attempt overlap, terminal
missingness, costs, and capital time remain unchanged. Thresholds must be fixed before quote values
are inspected or fitted inside development folds with trial ancestry. Stop H4 if no gate improves
net touch PnL, adverse-selection proxy, or capital-time efficiency across event groups, or if gains
come from capture anomalies, one venue, one market, or missing-attempt selection.

Recommendation after this packet: `EVALUATE` only after a real corpus exists; do not formalize or
request protected evidence.

## Change boundary

- Permitted files or components: one Polymarket activity-feature module, its one-to-one adversarial
  test, public exports, data-foundation implementation map, low-latency program/status, and this
  packet receipt.
- Allowed state effects: none; the transform returns immutable in-memory diagnostics derived from
  a verified retained snapshot.
- Forbidden state effects: raw-byte mutation, data registration changes, inferred pre-window
  events, learned thresholds, scientific promotion, protected exposure, or trading authority.

## Correctness

- Governing invariants and decisions: I1 temporal admissibility, I2 fitted state, I5 scientific
  identity, I6 no fallback, I13 provenance, I17 explicit failure, I23/I26 target maturity
  separation, I24 environment identity, and locked elapsed-duration semantics.
- Concrete failure modes: treating each delta row as an event; merging two venues with the same
  sequence; splitting cross-leg rows from one Polymarket message; letting current-time rows enter
  the prior count; inventing first-point quiet duration from corpus start; reporting a partial
  lookback count as complete; quantiling negative clock skew as latency; accepting a detached
  snapshot ref; or calling archival delay order latency.
- Expected inputs and outputs: exact `BookCorpusSnapshot` plus positive elapsed recent window;
  canonical source-event identities, per-venue clock profiles, and sorted per-leg activity points
  carrying snapshot/scope identity and explicit missingness.
- Violating mutation or counterexample: changing the count from source messages to rows makes one
  multi-level delta spuriously more active; initializing quiet duration from `start_at` turns left
  truncation into fabricated history.
- Required local tests/evals: multi-row/cross-leg coalescing, cross-venue separation, same-time
  decision coalescing, left truncation, warm-up, current-event exclusion, signed clock classes,
  fixed quantiles, invalid definitions, ambiguous row kinds, and detached identity.
- Required integration evidence: existing corpus replay tests, H3/H5 timing tests, full Polymarket
  adapter suite, broader Chronos suite, and strict static checks.

## Completion evidence

- Focused activity/corpus/strategy tests pass.
- Full Polymarket and proportionate Chronos suites pass.
- Ruff, formatter, basedpyright, docs-index generation, hashes, and `git diff --check` pass.
- Owning implementation and research status documents preserve the prior negative and state exactly
  what the feature does not prove.
- A transition receipt records code/test identities and remaining empirical dependency.

## Boundary revisions

None.

# Transition receipt

## Result

- Packet: LL-00 dual-clock book activity and quiet-duration features
- Status: `COMPLETE`
- Input repository state: `712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the recorded
  uncommitted low-latency predecessor packets
- Resulting repository state: feature module SHA-256
  `a34f164f700a1161a38138fcce399eb4aaa0eca87e144238f77daee82b0b26f3`; adversary
  SHA-256 `d50eaa09255cb3746f71062db5a1cee898a2a30e63888f58f3d440cd53419edf`

## Delivered state delta

- Files and interfaces changed: added `book_activity.py`, public Polymarket exports, its one-to-one
  adversarial test, and aligned the data-foundation implementation and low-latency study documents.
- Behavior added, removed, or preserved: added verified source-message coalescing, per-venue signed
  clock profiles, and causal per-leg activity points; preserved raw retained bytes, registration,
  replay, and all strategy definitions unchanged.
- Allowed state effects observed: none; all output is immutable in-memory derived state attached to
  the exact retained snapshot identity.
- Documentation status updated: LL-00 feature meaning, H4 ancestry/target, prior protected negative,
  operational caveats, and remaining empirical dependency are explicit.

## Evidence

- Tests and evals run: twelve focused activity adversaries; combined LL-00/corpus/capture/H1/H3/H5
  group; full Polymarket adapter suite; broader Chronos suite excluding the two sandbox-incompatible
  loopback HTTP modules; Ruff, formatter, basedpyright, docs-index generation, hashes, and diff
  whitespace validation.
- Results: LL-00 `12 passed`; focused low-latency group `54 passed`; adapter `129 passed`; broader
  Chronos `498 passed`; 32 adapter files formatted; Ruff all checks passed; basedpyright 0
  errors/warnings; `git diff --check` clean.
- Boundary/debug observations: one Polymarket source message can emit several price-level rows and
  affect both outcome legs, so row count is not activity count. Collector time is the only legal
  interarrival clock. The current retained schema cannot distinguish a genuine equal venue stamp
  from the collector fallback.
- Violating mutation or counterfactual demonstrated: splitting multi-row/cross-leg messages changes
  event count; merging identical cross-venue clocks changes identity; current bursts cannot enter
  their own prior count; first quiet duration and incomplete windows cannot become zero; mixed row
  kinds and detached snapshot refs fail closed.
- Integration evidence: every existing replayed book state joins an activity point on its exact
  `(leg, available_at)` key without changing the replay or strategy clock.

## Knowledge carried forward

- Decisions and assumptions relied upon: the prior E16/R17 evidence supports sampled-update arrival
  structure only; P19 is an immutable protected rejection; all feature durations are elapsed; no
  fitted state exists in LL-00.
- New facts discovered: H4 can share one causal timing substrate with H3/H5, but ingestion delay and
  action latency are different measurements; exact-zero delay provenance needs a future source flag
  if venue-versus-fallback separation becomes necessary.
- Unresolved uncertainty: no L2 value distribution or H4 outcome has been observed; activity may be
  recorder/subscription behavior; queue, fill, cancel, acknowledgement, fee, and rebate evidence is
  absent.
- Remaining reds or follow-up dependencies: capture real post-change books, audit clock profiles,
  join LL-00 to H3/H5 attempts, predeclare fixed/fold-local gate selection and chronological event
  comparison, and collect execution lifecycle data before any maker/cancel interpretation.

This receipt proves deterministic feature timing, provenance, and replay composition only. It does
not prove a useful gate, update causality, direction, order latency, executable PnL, protected
evidence, or authority to trade.
