# Work packet: Polymarket XTracker alternative-data trial

## Identity

- Packet: `polymarket.test-xtracker-post-count-signal`
- Owning architecture block: data foundation, then development-only exploration.
- Semantic transition or responsibility: exact official public post records → retained source →
  conservative temporal registration → development-only event-panel test or retained rejection.
- Input repository state: `historical checkpoint bbb79f2b` on
  `codex/polymarket-time-series-research`.

## Objective

Determine whether exact cumulative post count and posting pace, known no earlier than XTracker's
per-record import timestamp, add predictive information for the nine development contracts in
event `739241` beyond their own probability paths. First prove source and time semantics; do not
run the predictor if those semantics fail.

## Context boundary

- Global authority loaded: repository and Chronos instructions, invariants, locked decisions,
  architecture map, data-foundation contracts, and the Polymarket startup/public-source skills.
- Owning transitions: `data.propose-source-candidates`, `data.retain-source-snapshot`,
  `data.derive-dataset`, `data.register-observations`, and development-only constrained analysis.
- Relevant adjacent interfaces: generic `SourceScoutingService`, `DataWorkspace`,
  `TemporalRegistrationAuthority`, retained development corpus, and authored study execution.
- Explicit exclusions: protected events or outcomes, production database writes, X/Twitter direct
  scraping, post content as a feature, credentials, unregistered web values, external-system changes,
  or treating development evidence as validated learning.
- Assumptions subject to verification: `createdAt` is post reference time; `importedAt` is the
  conservative XTracker availability time; exact market interval is
  `[2026-07-25T16:00:00Z, 2026-07-27T15:59:59Z]`.

## Change boundary

- Permitted components: this packet; one immutable study directory; exact passive scout records;
  local content-addressed acquisition; one bounded offline parser; explicit temporal profile and
  registration composition; development-only analysis source and receipts; focused tests only if
  a real public-path failure exposes a generic seam.
- Allowed state effects: append-only files beneath the local Chronos data workspace and coherent
  Chronos study/docs commits.
- Forbidden state effects: production or sibling-repository mutation, arbitrary source access from
  authored analysis, automatic candidate selection, protected access, freeze/promotion, or source
  timestamp reinterpretation after results are seen.

## Correctness

- Governing invariants: exact provenance and identity; `available_at <= decision_time`; immutable
  scientific transitions; development/protected separation; negative-result retention.
- Failure modes: the documented `timezone=EST` option shifts an already offset-bearing query;
  current API retrieval is mistaken for historical availability; deleted posts/revisions are
  silently ignored; duplicate posts are counted; imported time precedes creation; response bounds
  exceed the exact tracking interval; final count leaks into earlier decisions; or one event is
  reported as a general Polymarket result.
- Fixed source choice: official XTracker endpoint for `@elonmusk`, platform `X`, exact UTC start and
  end parameters, without the ambiguous timezone flag.
- Fixed candidate features if registration passes: cumulative imported post count, elapsed-rate,
  trailing 1h/3h/6h imported-post counts, and pace projected over remaining event time. Post text,
  engagement, and final-period aggregates are excluded.
- Fixed labels: for each bracket contract at legal hourly decisions, six-hour future probability
  change and terminal bracket outcome are separate diagnostics. The primary incremental comparison
  is six-hour probability-change error versus the same target-only state/path recipe; outcome
  analysis is calibration-only and must use chronological event ancestry outside event `739241` or
  remain explicitly single-event descriptive evidence.
- Frozen first model comparison: six-hour non-overlapping decision blocks; an expanding ridge fit
  uses only rows whose six-hour label has matured. The target-only baseline uses probability state,
  trailing path, and static bracket bounds. The augmented recipe adds only time-available count,
  recent pace, projected terminal count, bracket gap, elimination, and required-rate terms. Both
  use fold standardization and penalty `0.1`. The augmented recipe must improve observation and
  decision-block macro MSE by at least 10%, beat zero-change under both weightings, and beat the
  target-only model in at least three of four test blocks. This is a replication gate, not a freeze
  gate, because all rows belong to one event.
- Expected output: value-free source/derived/registration identities, timestamp audit, exact join
  coverage, and either a governed negative or a candidate requiring broader event replication.
- Violating counterexample: replace every protected value; every result and receipt must remain
  unchanged. Set `available_at=createdAt`; the derived/profile identity must change and the original
  registration cannot be reused.

## Completion evidence

- Exact passive scouting report precedes selection and network acquisition.
- Raw bytes are immutable and verified; offline derivation rejects malformed, duplicate,
  out-of-window, or temporally inverted records.
- Registered observations expose no post before `importedAt` and the joined development run records
  exact accesses with zero protected exposure.
- Any scientific claim is limited to the observed development event unless multiple chronological
  events with identical semantics become available.
- Static checks and relevant tests pass; coherent changes are committed locally without push.

## Boundary revisions

1. The first real registered-source run exposed that the Polymarket development composition could
   only grant the corpus price and outcome views. The packet permits one generic registered-event
   field seam. It requires an authority-issued registration, exact corpus-environment equality,
   an `event_id` dimension, and physical exclusion of every unknown or protected event before the
   sandbox capability is built.

## Completed evidence

- The passive scout, exact selection, 18,391-byte source snapshot, offline parser, temporal profile,
  registration, and catalog identities are retained. Fifty-nine posts use `createdAt` as reference
  time and the later `importedAt` as availability; the maximum observed import delay is 274.346
  seconds.
- The registered-event composition exposes exact reference/availability columns and values through
  ordinary tracked sandbox reads. Tests deny protected event `event_id` values and mismatched
  environments before disclosure.
- Two failed assertion runs and one alignment diagnostic are retained. One sparse bracket contract
  violated the fixed 4.5–7.5 hour window, so the final trial excluded six rows without interpolation.
- On 32 legal forward rows, the augmented ridge had MSE `0.040309`, versus `0.017979` for the
  target-path/static-bracket ridge and `0.008214` for zero change. It won zero of four blocks against
  either control and is rejected.
- Ruff formatting/lint and strict basedpyright are clean. The complete test gate passes with 444
  tests when run with the required source import path and permitted loopback fixtures.
- No protected value, production write, freeze, promotion, external-system change, push, merge, or PR
  occurred.
