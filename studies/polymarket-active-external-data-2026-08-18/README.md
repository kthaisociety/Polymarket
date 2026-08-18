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
