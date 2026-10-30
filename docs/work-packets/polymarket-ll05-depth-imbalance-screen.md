# Work packet: LL-05 multi-level depth-imbalance impulse screen

## Identity

- Packet: `polymarket-ll05-depth-imbalance-screen`
- Owning architecture block: Polymarket dual-clock L2 corpus and open-ended exploration
- Semantic transition: exact retained full-depth binary-outcome book events into a deterministic,
  delayed and marketable-touch order-book imbalance continuation screen
- Input repository state: active low-latency working tree after LL-03 implementation; all existing
  research artifacts remain user-owned

## Evidence ancestry and correction

The retained strategy lab's A11 idea computes
`(bid_depth - ask_depth) / (bid_depth + ask_depth)` over every returned level. Its reasoned,
unscored starting gates are imbalance at least `.50`, spread no more than `.03`, total displayed
depth at least `100`, and a two-minute maximum hold. The lab explicitly records that these values
were not fitted to real Polymarket tapes and that it produced no live score or fill evidence.

The cited primary Polymarket paper, *The Anatomy of a Decentralized Prediction Market:
Microstructure Evidence from the Polymarket Order Book* (arXiv `2604.24366`), supports one data
choice: depth is distributed more like a uniform geometric grid than a touch-concentrated book, so
top-of-book size is not a faithful substitute for the retained ladder. Its abstract also reports
sub-50 ms median archive ingestion with a multi-second tail, supporting measured tail-delay replay.
It does **not** report a directional order-book-imbalance strategy result. General-market evidence
on order flow imbalance is mechanism context, not Polymarket validation.

The implementation must therefore preserve the lab thresholds as falsifiable ancestry while
correcting the evidence claim: H5 begins with no empirical directional support in this repository.

## Objective

Determine whether a large, persistent multi-level YES-book depth imbalance under a tight spread
predicts enough same-direction executable movement over a fixed sub-minute horizon to survive
action delay, spread, displayed size, explicit cost budget, signal decay, and chronological
non-overlap.

## Required depth registration

Every replayed source state retains the complete best-first bid and ask ladders that existed after
that source event. Registration publishes price and size for each `(side, level)` with the same
venue `reference_time`, collector `available_at`, event ordinal, and sequence as the state. The
existing top fields remain unchanged. A consumer may derive all-level, top-N, price-band, or
concentration diagnostics, but the LL-05 definition fixes one depth horizon before values are
inspected.

The first screen mirrors A11 and uses all retained levels. Top-touch imbalance and depth
concentration are mandatory rival diagnostics, not alternative signals selected after seeing PnL.

## Fixed strategy semantics

Each definition binds exactly two semantically authorized outcomes of one binary Polymarket market:

- `reference_leg`: YES book whose midpoint, spread, and multi-level imbalance define the signal;
- `complement_leg`: NO book used to express an ask-heavy YES signal without naked shorting.

A raw signal begins only when the reference book crosses from no eligible direction into:

- signed all-level imbalance magnitude at least the configured threshold (`.50` in A11 ancestry);
- spread no more than the configured limit (`.03` in A11 ancestry);
- combined displayed bid/ask depth at least the configured floor (`100` in A11 ancestry);
- reference midpoint inside a fixed tradable band (A11 ancestry: `[.05, .95]`).

Bid-heavy YES selects YES; ask-heavy YES selects NO. At `decision_at + action_delay`, entry is
cancelled unless the reference quote is fresh and still passes the same direction, imbalance,
spread, depth, and price-band gates. The selected outcome must also have a fresh ask and the fixed
minimum displayed quantity. Entry uses that ask.

After entry, exit the selected outcome at its displayed bid on the first of:

1. configured same-direction YES-midpoint take-profit distance;
2. configured opposite-direction stop distance;
3. signed imbalance decaying to or through the configured exit threshold;
4. fixed maximum holding deadline.

The first empirical protocol must freeze action delay from paper-order tail latency and choose
take-profit, stop, exit-imbalance, hold, freshness, quantity, and cost values before quote values are
inspected. A 30-second fixed hold is the primary horizon because the inherited mechanism is alleged
to decay in seconds; the old two-minute hold is retained only as an ancestry sensitivity. No
threshold search is authorized by this packet.

## Time, sampling, and missingness

- Observation clock: coalesced collector `available_at` union clock.
- Signal order: reference-book states in collector order; `reference_time` cannot reorder them.
- Entry fields: latest legal state as of the fixed delayed arrival.
- Exit fields: contemporaneous/latest-as-of selected bid at the first terminal condition.
- Coverage: the half-open retained corpus must extend strictly beyond a timeout deadline; otherwise
  the position is `TRUNCATED`.
- Missing/stale entry is `CANCELLED_AT_ARRIVAL`, not a trade.
- Missing/stale exit is `MISSING_EXIT_QUOTE`, not zero PnL.
- An entered position suppresses new signals through its terminal or unresolved window. A persistent
  imbalance cannot repeatedly enter until it first leaves and then re-crosses the gate.

## Output and rivals

Retain for every non-overlapping raw crossing:

- decision, arrival, and terminal times/status;
- signal sign, selected outcome, all-level and top-touch imbalance, total depth, spread, midpoint,
  and level counts at decision and arrival;
- exact entry ask, exit bid, displayed quantity, gross touch PnL, cost budget, and net diagnostic;
- exit reason and reference midpoint/imbalance at exit;
- raw crossing, arrival-cancel, entered, overlap, status, timeout, and missingness counts.

Mandatory aggregate/sliced analysis on real data must compare:

- all-level signal versus top-touch imbalance and no-signal unconditional horizons;
- both signal signs, independent event families, calendar subperiods, price bands, spread bands,
  depth concentration, and cancellation intensity;
- zero-delay displayed upper bound versus measured action-delay tails;
- gross midpoint response versus spread-inclusive and cost-budget touch PnL;
- signal persistence/decay and timeout rate.

## Correctness adversaries

- Reject non-binary/different-market legs, wrong scope authority, missing/extra corpus legs,
  thresholds outside valid support, non-positive depth/size/time, negative delay/cost, and an exit
  imbalance not strictly below the entry threshold.
- Preserve and register every valid ladder level in deterministic best-first order.
- Reject a replay state whose top fields and ladder disagree or whose ladder is crossed/unsorted.
- Prove far-level depth changes all-level imbalance while leaving top-touch imbalance unchanged.
- Prove same collector-time deltas coalesce before the signal.
- Prove later/future states cannot rewrite delayed entry.
- Prove signal decay during action delay cancels rather than entering.
- Prove bid-heavy selects YES and ask-heavy selects NO.
- Prove take-profit, stop, imbalance-decay, timeout, stale exit, truncation, and non-reentry paths use
  marketable selected-outcome touches and explicit missingness.

## Completion evidence

- Full replay ladders are retained in state and registered with temporal dimensions.
- LL-05 definition, output, and deterministic screen are publicly exported.
- Focused depth-registration and strategy adversaries pass.
- Existing Polymarket adapter suite, configured Ruff/formatter, strict basedpyright, and
  `git diff --check` pass.
- Hypothesis and architecture ledgers identify LL-05 as implemented but empirically unevaluated.

## Explicit exclusions

- No claim that the cited paper validates directional imbalance alpha.
- No use of fill-flow imbalance as a substitute for resting-book imbalance.
- No top-only strategy substituted for the predeclared multi-level question.
- No fee-schedule, hidden-depth, queue, fill, spoof attribution, or live PnL claim.
- No quote-value inspection, protected exposure, deployment, or production write.

## Execution receipt

- Full-depth replay/registration source SHA-256:
  `f90c198aa72571f755813eda7088d489d8d4e8a2a2f6e316616b263905d44592`.
- LL-05 screen source SHA-256:
  `93d08060f03eacf9c0f02151b3b50121850b4c1ba2d3261b196375100a50fa75`.
- LL-05 adversary source SHA-256:
  `69daac3f1306b89b4d5ef4be9ea04ae1999be7e6d6b732ecf5fca38794d3e689`.
- Eleven focused LL-05 adversaries and the new full-depth registration adversary passed; the full
  H1/H3/H5/L2 focused group passed 36/36.
- All 111 Polymarket adapter tests passed.
- The broader Chronos suite passed 480/480 with only the two sandbox-prohibited local HTTP-server
  modules excluded.
- Scoped Ruff and formatter checks passed; configured strict basedpyright passed with zero errors
  or warnings; `git diff --check` passed.
- Mechanical falsifier coverage includes full-depth versus top-touch divergence, same-time row
  coalescing, capture-start left truncation, delayed signal decay/cancellation, symmetric YES/NO
  expression, spread-inclusive take/stop/imbalance/timeout exits, stale selected-outcome exits,
  exact half-open truncation, and persistent-signal non-reentry.
- Empirical status: **IMPLEMENTED, SYNTHETICALLY VERIFIED, DIRECTIONAL CLAIM UNEVALUATED**. The
  implementation proves that Chronos can test the intended multi-level strategy; it supplies no
  evidence that imbalance predicts Polymarket prices or earns positive PnL.
