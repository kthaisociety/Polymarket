# Work packet: Polymarket bracket-overround compression

## Identity

- Packet: `polymarket.test-bracket-overround-compression`.
- Input repository state: `historical checkpoint 94ea6b1d` on
  `codex/polymarket-time-series-research`.
- Owning responsibility: development-only internal-market mechanism test.

## Objective

Test whether sampled probabilities across mutually exclusive post-count brackets temporarily carry
an overround that compresses over the next day strongly enough to survive a one-cent-per-leg screen.
This is a portfolio-coherence mechanism, not another single-contract transform search.

## Authority and scope

- Exact retained corpus:
  `polymarket-corpus:610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f`.
- Development partition:
  `49d5e9a97985a44e3277f43ee55ce1281c430a1d0a1823754a9a759ac56d3bd1`;
  24 events/155 markets. Seven events/45 markets remain protected and unavailable.
- Discovery events are fixed to same-week post-count families `716150`, `716151`, `716152`,
  `716153`, `716154`, `716156`, `716157`, and `716159`.
- Confirmation, if earned, is limited to later development events `739241`, `748763`, and `727674`.
- Questions must parse into pairwise non-overlapping count brackets inside every event. Completeness
  is not required: mutual exclusion alone makes probability mass above one incoherent.
- Production writes, protected values, external data, external application, the production data service, and sibling
  repositories are excluded.

## Fixed discovery design

- Decisions: days 1-5 at 16:00 UTC inside the July 21-28 event window.
- Execution proxy: first retained probability from zero to two hours after each decision for every
  bracket; reject a portfolio snapshot if its cross-market timestamp span exceeds five minutes.
- Outcome: the analogous complete portfolio snapshot 24 to 26 hours later, also within a five-minute
  span.
- Feature: per-leg sampled overround `(sum(probabilities) - 1) / market_count`.
- Signal: sampled overround per leg at least `0.015`; direction is short one equal unit of every
  mutually exclusive YES bracket.
- Label: equal-weight next-day sampled decline, screened by `0.01` per leg.
- Continuous control: correlation between overround per leg and unscreened equal-weight next-day
  decline across every eligible portfolio.
- Discovery gate: at least 10 signal portfolios, positive mean screened decline, at least 60% positive
  screened declines, positive signal-event means in at least four events, and continuous correlation
  at least `0.20`.

No threshold, decision time, synchronization limit, cost screen, event membership, or gate component
may change after source 01 reads prices. Failure closes this mechanism. Passing discovery permits one
locked later-event confirmation but does not permit protected evaluation.

## Evidence and caveats

- Run through the public retained-corpus analysis command and retain source SHA, exact receipt,
  actual accesses, exclusions, and zero protected exposure.
- Historical probabilities are sampled beliefs, not bid/ask quotes. A one-cent screen is a
  tradability falsifier, not a realized P&L claim.
- Equal-unit shorting feasibility, collateral, fees, spread, fill probability, and legging risk are
  unavailable. Even a passing mechanism would require official historical order-book evidence.
- Editing documentation cannot create a candidate, freeze, finding, negative result, or terminal
  question memory.

## Boundary revisions

1. The exact source was denied before any field access because the sandbox exposed `log` and `exp`
   but not pure scalar `sqrt`. The source and scientific design remained byte-identical while the
   separately governed `sandbox.allow-pure-sqrt` packet added that bounded numerical primitive. The
   denied receipt is retained; the rerun receipt lives under `development-receipts/sqrt-enabled/`.
2. The byte-identical rerun produced 40 synchronized portfolios. Although continuous overround had
   `0.5573` correlation with next-day per-leg decline, only eight portfolios met the predeclared
   signal threshold, their mean one-cent-screened decline was `+0.00289`, only 50% were positive,
   and only three of eight event means were positive. The minimum-count, positive-share, and
   event-breadth gates failed. The mechanism is rejected without later-event confirmation.
