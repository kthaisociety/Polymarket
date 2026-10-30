# Active-contract external-data campaign

Epistemic status: **EXPLORATORY — ACTIVE; NO TRADE OR PROTECTED CLAIM**.

## Mandate

Find a tradable idea for specific active Polymarket contracts using public information outside
Polymarket. Chronos must keep predictor availability distinct from market time, test direction and
net executable P&L rather than sampled-price fit alone, retain negative results, and use a fresh
protected cohort only after fixed development gates are earned.

The earlier internal-data campaign is summarized from least to most promising in the paper's
[`signal ranking`](../polymarket-stochastic-process-paper-2026-08-18/paper/signal-ranking.md). It
contains **zero trade-ready signals**. The best internal components predict update arrival, move
timing, and the complete registered-sample law; none establishes directional net return.

## Startup memo

- Research decision time: `2026-08-18T19:09:23+00:00` for the storage boundary; each acquired
  source and market snapshot receives its own aware acquisition time.
- Market authority: bounded parameterized `SELECT` statements under proved production role
  `human_ro`; production remains read-only.
- Initial population: active, non-expired contracts with at least one fill in the prior 72 hours,
  ranked by recent observed notional only to scout economically measurable families. Ranking is
  not scientific selection evidence.
- Opening question: does a time-legal public external series produce a directional probability
  estimate sufficiently different from executable Polymarket quotes to earn positive forward P&L
  after spread, fees, latency, depth, and abstention?
- Rival explanations: the market incorporates the source before Chronos can act; source timestamps
  are later than claimed; publication surprises are confounded with common news; apparent returns
  are sampled-price bounce; spreads and finite depth consume the discrepancy; one event family
  cannot generalize.
- First candidate families: Brazil presidential polling versus the active candidate surface;
  CME FedWatch/Fed Funds information versus the September FOMC outcome surface; public maritime
  traffic versus Hormuz-normalization deadlines. These are a source-feasibility queue, not three
  hypotheses already selected for testing.
- First falsifier: reject a family before modeling if exact source publication availability,
  contract/outcome mapping, a historical development window, or legal executable-price measurement
  cannot be established.
- Protected boundary: the earlier arrival-hazard holdout is exposed and cannot be reused. No new
  protected request exists.

## Server storage boundary

Raw external bytes belong under the isolated server root
`/home/tage/chronos-external-data/active-external-2026-08-18`. The baseline and ownership ledger
are [`storage-baseline.json`](storage-baseline.json) and
[`server-ownership-manifest.json`](server-ownership-manifest.json).

Deletion policy is deliberately narrow:

1. Use available capacity before considering deletion.
2. Never delete a pre-existing object or anything absent from this campaign's manifest.
3. A removable object must have `owner=chronos-active-external-2026-08-18`, an exact path beneath
   the isolated root, source identity, hash, size, and creation receipt.
4. Deletion, if ever necessary, is recorded rather than erasing provenance.

At baseline the main 300 GiB filesystem was 48% used with `161,473,957,888` bytes available.
Nothing was removed.

## Research stages

1. Retain the exact active-universe inventory and source-feasibility audit.
2. Select the smallest contract family with legal external history and executable quotes.
3. Retain raw source bytes, derive time-legal observations, and register both clocks.
4. Run simple benchmarks before richer features; group uncertainty at the event or publication
   shock level.
5. Evaluate directional quote-crossing and passive alternatives with costs, latency, depth,
   abstention, and concentration.
6. Preserve rejection or, only after fixed gates, author an exact formal system and independent
   protected plan on a fresh cohort.

No current quote or exploratory discrepancy is a recommendation to trade.

## First completed candidate

The CME FedWatch versus September `+25 bp` contract study is complete in development. The direct
idea failed strongly: following the dated CME probability lost after fees at every completed 6-,
12-, 24-, and 48-hour decision. A post-hoc 48-hour fade was positive (+$19.165 over seven
overlapping 100-share trades, four winners), but it is a fragile hypothesis that requires a new,
predeclared event cohort. See [`fomc-fedwatch-result.md`](fomc-fedwatch-result.md).

## Second completed candidate

The IMF/OCHA PortWatch versus active Hormuz deadline study is complete in development. Exact Git
publication vintages were joined to 24,921 canonical taker fills across three
deadline contracts. Following weekly traffic changes lost after fees at both 24 hours and seven
days. Buying NO merely because traffic remained far below the resolution threshold also lost at
every tested state threshold and horizon. The result rejects a mechanical traffic rule and shows
that these contracts chiefly price a future geopolitical regime switch, not the current ship
count. See [`hormuz-portwatch-result.md`](hormuz-portwatch-result.md).

## Third completed candidate

The Brazil runoff-poll study is complete in development. Thirty-one exact, national,
TSE-matched releases formed 25 immutable decision events and were joined to 17,570 canonical
production taker fills in the Lula and Flávio winner contracts. Four poll-change features were
followed and faded over 24 hours, 72 hours, and seven days. Every rule with at least five
executable relative pairs lost after conservative fees. A weak three-day gross fade response was
too small to cover four crossed legs and came from one dependent election. See
[`brazil-poll-result.md`](brazil-poll-result.md).

## Low-latency successor program

Chronos has now synthesized the internal study ledger, the retained strategy-lab ancestry, the exact
Brazil cross-venue semantic audit, and the retained 59,000-row two-venue taker tape into a ranked
low-latency hypothesis program. The first branch is conservative Kalshi-YES plus Polymarket-NO
payout dominance, followed by cross-venue lead-lag, book-confirmed post-jump reversal,
staleness-conditioned execution, and order-book imbalance.

The existing fill tape cannot test those execution claims: it contains only outcome-index-zero
prints and no simultaneous book depth, collector receipt time, order acknowledgement, or
partial-fill path. The collector now preserves separate venue-event and collector-absorb clocks for
new book rows, and Chronos has a bounded legacy-excluding reader, immutable retention, anchored L2
replay, causal top-of-book registration, and a predeclared H1 gross payout-dominance screen with
as-of joins, staleness, top-size, and fixed-delay controls. No post-change production corpus has yet
been captured. A bounded public snapshot command now accepts only an explicit semantic-authority
reference, canonical legs, and aware half-open collector interval; it uses the proved `human_ro`
repeatable-read path and emits a sanitized immutable receipt. This removes ad hoc acquisition code
from the next run but does not replace deployment or create data by itself.

The predeclared fill-only H2 scout has also completed. Its one-sided Kalshi-to-Polymarket path has
a small +0.220-cent conditional 30-second mean, an effectively zero median, only 39/264 matched
responses, inconsistent candidate/month slices, and a negative matched reverse-window comparison.
Polymarket-to-Kalshi response coverage is only 1/307 at 30 seconds. The retained Kalshi leg omitted
NO-taking trades, and the tape has no collector clock or executable book state, so the result does
not advance. See
[`brazil-cross-venue-fill-lead-lag-result.md`](brazil-cross-venue-fill-lead-lag-result.md).

The exact LL-01 data requirements, event clock, label, rivals, falsifier, and explicit exclusions are in
[`low-latency-hypothesis-program.md`](low-latency-hypothesis-program.md). The branch remains
exploratory and blocked on deployment plus executable-book and execution evidence; no current gap
is a trade.

The strongest replicated internal directional mechanism is also prepared as LL-03. Its fixed book
replay detects two-cent YES-midpoint shocks in collector order, waits the configured action delay,
buys the opposite economic outcome at a marketable ask, and exits at the selected outcome's bid on
the first two-cent reversal/continuation crossing or fixed deadline. It records displayed size,
spread, explicit cost budget, non-overlap, stale quotes, missing exits, and truncated coverage. The
eight focused tests are synthetic causal evidence, not empirical strategy evidence; LL-03 awaits
the same post-deployment L2 corpus as H1.

LL-05 now carries the order-book-imbalance branch without reducing it to touch size. Chronos
retains and registers every best-first depth level, detects new all-level imbalance crossings,
re-confirms them after action delay, trades YES or NO symmetrically at marketable touches, and exits
on price target, stop, imbalance decay, or timeout. Top-touch imbalance remains a fixed rival.
Eleven focused tests cover far-depth-only signals, same-time coalescing, left truncation, delayed
decay cancellation, both directions, touch PnL, missing exits, and incomplete coverage. The old
historical thresholds remain unscored ancestry, and no H5 empirical result exists.

The capture entry point is
`python -m research_agent.data_adapters.polymarket.book_corpus_snapshot --help`. A useful run still
requires the approved production tunnel, deployed dual-clock schema/collector, exact reviewed leg
scope, and a bounded interval containing a snapshot anchor for every requested leg.

LL-00 also prepares the activity side of H4 without reviving the rejected protected arrival model.
It derives per-leg collector-time quiet duration and fixed-window prior source-message counts from
verified retained bytes, coalescing multi-row and cross-leg venue messages before decisions. First
quiet duration and incomplete windows remain missing; current-time bursts do not enter their own
prior counts. Signed reference delay is reported only as clock health because exact-zero values may
be collector fallback and archival ingestion is not order latency. No threshold or H4 result has
been selected.

LL-04a now makes the first H4 question executable as a taker-only paired ablation over unchanged
LL-03 or LL-05 attempts. It requires an exact signal-time LL-00 point and identical snapshot,
coverage, scope, parent, leg, and window identity. The ungated result always remains beside the
activity-filtered ordered subset; missing history abstains and unresolved parent PnL stays missing.
The comparison reports coverage, sign counts, touch PnL, and collateral-time efficiency, but
supplies no threshold defaults and cannot claim fills, maker cancellation, or empirical
improvement. The focused and broader Chronos suites establish only the mechanics.

LL-04b adds the missing interpretation controls on the exact same decisions: complete feature
history, quiet-only, recent-activity-only, and joint populations beside the original ungated
attempts. Fixed left-minus-right contrasts distinguish warm-up selection from each component and
from the joint rule. The sampled-process ancestry supports testing a duration-dependent mechanism,
but its hourly/five-minute parameters do not identify a seconds-level L2 cutoff. Twelve focused
adversaries establish the revised mechanics; no activity threshold or empirical H4 result has been
selected.

LL-04c makes that fixed-policy question runnable across multiple markets and chronological capture
blocks. It binds the entire market-independent H3 or H5 recipe alongside scope and activity
thresholds, rejects overlapping blocks and duplicate attempts, and recomputes every component rival
within each block and pooled. Missing blocks remain visible, and early/late stability is split before
missing metrics are removed. Block sign counts and positive-improvement concentration prevent a
pooled gain from hiding obvious instability. Collector blocks are not semantic event families, and
this machinery still contains no threshold selection, advancement rule, fills, or empirical result.

LL-04d now predeclares the first and only activity policy trial: quiet duration no greater than one
declared parent action-delay interval and at least two prior source messages inside five such
intervals. The current trigger remains excluded. The rule binds and hashes the complete H3/H5
parent definition, preserves microsecond timing, and rejects zero-delay parents. It deliberately
does not search alternate thresholds or import hourly/five-minute cutoffs. The parent delay remains
a replay assumption until production order latency is measured; no empirical H4 result exists.

LL-04e now supplies the missing pre-inspection development decision standard for that exact policy.
It separates insufficient coverage from economic rejection, requires at least 10 chronological
blocks and 30 scorable joint attempts, preserves missing outcomes, limits concentration, checks
both early and late halves, and requires incremental collateral-time value over complete history
and both component rivals. It rejects a numerically copied gate whose exact LL-04d parent-derived
identity is absent. Even complete passage can only advance to a separately authored prospective
paper-execution study; no L2 campaign has run and no empirical H4 result exists.

LL-04f now makes that fixed question directly runnable over content-addressed retained captures.
One plan binds environment, scope, ordered half-open blocks, unique snapshot hashes, and complete
market-specific H3 or H5 definitions. The read-only runner requires exact coverage and leg equality
before composing replay, activity features, parent attempts, all rival populations, campaign
stability, and LL-04e. It retains zero-attempt markets instead of dropping them. The API records
exact structural identity but does not prove the plan predated value inspection; a real campaign
still needs a persisted pre-inspection receipt. No production L2 application has run.

LL-04g now provides that exact local receipt. It content-addresses the complete LL-04f plan,
retains canonical bytes with exclusive creation, and rejects a missing, corrupted, conflicting, or
changed plan before LL-04f may load quote values. This is an immutable-input mechanism, not an
independent timestamp or ledger: the production campaign must still establish durable ordering
between receipt publication and value exposure. No empirical H4 result exists.
