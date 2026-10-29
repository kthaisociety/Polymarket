# Chronos-enforced Polymarket research rerun

Status: **COMPLETE — REPRODUCIBLE MECHANISM EVIDENCE, NO EXECUTION-VALIDATED STRATEGY**.

## Bottom line

The enforcement gap is closed for this research path. A campaign can complete only after Chronos
binds exact source bytes, exact registered view values, capabilities, dataset and environment
identities, resource limits, actual field accesses, artifacts, and one disposition per declared
analysis. Legacy or externally assembled receipts cannot enter the campaign.

The rerun does **not** support the claim that behavioral economics or game theory is the only useful
way to model Polymarket. Of the tested behavioral/game-theoretic mechanisms, focal anchoring,
skilled-wallet following, expert consensus, crowded extrapolation, ambiguity aversion, sampled
underround, and bracket-overround compression were rejected or data-blocked. The sole surviving
behavioral lead is a fixed longshot fade, but it is selection-exposed and has no executable-quote
evidence.

The stochastic program has materially stronger predictive evidence. Path-dependent post-jump
reversal replicated on fresh events, and duration/path features improved update-arrival, sign,
magnitude, and complete-process predictions out of time. Those are still models of sampled
probability marks, not executable trading results. No campaign row is execution validated.

## Enforcement and coverage

| Evidence object | Result |
|---|---:|
| Core value-bound campaign | 44/44 successful and admissible |
| Exact prior-result comparisons in the core campaign | 42 identical, 0 changed, 2 new registered-view analyses |
| Behavioral add-on campaign | 2/2 successful and admissible |
| Fixed five-minute campaign | 1/1 successful, admissible, and identical to the prior result |
| Substantive enforced executions | 47 |
| Non-replay inventory | 25 exact prior source/receipt pairs |
| Execution-validated strategies | 0 |

The four completion receipts are:

- core: `campaign-completion-receipt:184dbd75271bc528d95c963af78b857824f4c4615c42c1d1884cb6e793613a82`;
- behavioral add-on: `campaign-completion-receipt:0c10260cd3870e015e26080d2741b0d5e6247f3a4ddec81805536f1acfe1d494`;
- five-minute measurement: `campaign-completion-receipt:20f78f838d818d4d3447b7de4e30445f4dee21d4c33ccdd6c0dcb76ed9bca820`;
- non-replay audit: `campaign-completion-receipt:ee79c63edea5e44cca1c39b5c632021b839ac5af08a1968341dc9beb2790f8b0`.

All substantive reruns have maximum tier `EXPOSED_REPRODUCTION`. Re-execution proves
reproducibility; it does not restore the earlier fresh status or reopen protected values.

### Registered behavioral input

The production acquisition used the proved `human_ro`, repeatable-read, read-only boundary and made
no production writes. The retained parent-bound corpus contains 1,032,031 aggregate taker legs,
1,509 markets, and 124,666 wallets from 2025-05-02 through 2026-08-17. Its content identity is
`polymarket-behavioral-fills:81253fd1f305683e44428ece03036cecfec50b399e6471f6c31de699dbaba3d3`.
The parent's protected whole-event block is excluded before the fill values enter the harness.

## Behavioral and game-theoretic strategies

| Mechanism | Enforced result | Scientific disposition |
|---|---|---|
| Fold-local skilled wallets, matched state | 75,230 evaluation fills; 43 matched events and 607 cells. High-skill event-macro edge was `-0.02197` versus `-0.01086` for controls; increment `-0.01112`. | Rejected |
| Delayed skilled wallets, matched state and activity | 43 events and 841 cells. High-skill edge was `-0.02808` versus `-0.01317`; increment `-0.01492`. Early/late high edges were `-0.06987`/`+0.01181`, while both incremental halves were negative. | Rejected |
| Delayed expert consensus versus raw crowd | At 6h, expert net was `-0.00631` and incremental value `+0.00331`; at 24h, expert net was `-0.00690` and incremental value `+0.01031`. The rule required positive net value and stable improvement at both horizons. | Rejected |
| Crowded extrapolation fade | 72 chase signals across 34 events. Fade return was `+0.00191` at 6h but `-0.00774` at 24h; settlement edge was `-0.01348`, below both fixed rivals. | Rejected |
| Focal-price anchoring | Focal-minus-control continuation was `+0.00080` at 6h and `-0.00113` at 24h, below the `0.0025` gate and chronologically sign-unstable. | Rejected |
| Probability weighting: 2–10% longshot fade | After a fixed two-cent hurdle, event-macro edge was `+0.00160` at 72h and `+0.01842` at 168h. Paired improvement over 10–20% contracts was `+0.05259`/`+0.11654`. | Retain only for sealed fresh/executable evaluation |
| Probability weighting: favorite follow | Negative event-macro edge at both 72h and 168h. | Rejected |
| Ambiguity-aversion text proxy | Only two eligible complex markets in one event; net edge `-0.445`, with no paired control cell. | Rejected as strategy and inadequate proxy |
| Exhaustive-bucket underround | The declared live-quote candidate gate failed across the four semantic event groups. Sampled probabilities were not simultaneous asks. | Rejected for advancement |
| Bracket-overround compression | Only eight signals; mean one-cent-screened decline per leg `+0.00289`; the fixed discovery gate failed. | Rejected |
| Disposition-driven liquidity response | Historical inventory/cost basis remains invalid while repair history is incomplete. | Data-blocked; not tested |
| NegRisk complete-set coordination | Exact exhaustive membership plus historical dual-clock executable depth, fees, and partial-fill replay are absent. | Data-blocked; not tested |

The wallet results are especially important. The earlier direct-SQL mechanism lead did not survive
registration, broader parent-bound history, fold-local training, state controls, public-entry delay,
or activity matching. Behavioral labels alone therefore do not currently predict this time series
better than the controlled rivals.

The longshot result is different: it survives its fixed development comparisons and is the one
behavioral candidate worth preserving. It is not yet a trading strategy because its marks are not
bid/ask quotes, the two-cent hurdle is assumed rather than measured, and its later event block has
not been opened through a new governed evaluation.

## Stochastic and time-series comparison

The strongest trading-shaped result remains the fresh post-jump reversal model:

- 6,174 out-of-fold shocks across 410 markets and 128 fresh events;
- both the primary state replication and full incremental gates passed;
- the fixed full-path screen selected 387 sampled-mark attempts across 70 events;
- after a one-cent round-trip hurdle, observation mean was `+0.06024` and event-macro mean was
  `+0.04103`.

This is substantially more mature than the behavioral candidates because the rule and evaluation
were replicated on events absent from the original corpus. It is still not quote, fill, latency, or
protected-validation evidence.

The broader process results also reproduced exactly:

- state plus staleness improved next-hour update-arrival event-macro Brier by `27.63%` over state
  alone and won 112/113 event comparisons;
- state plus prior path improved nonzero-direction event-macro Brier by `3.96%` and won 96/113
  events;
- state plus prior path improved nonzero log-magnitude event-macro MSE by `20.61%` and won 101/113
  events; the fixed heavy-tail residual-law gate failed, with Gaussian log-magnitude residuals best;
- the frozen complete marked-jump family improved later-cohort event-macro NLL by `7.88%` over the
  state hurdle and won 27/27 later event comparisons;
- the five-minute panel reproduced 84.94% zero increments, 67.87% nonzero sign reversal, a 24h
  variance ratio of `0.06746`, and 99.49% exact alignment to same-window hourly samples.

The correct process description remains a bounded, sticky, grid-affected, zero-inflated marked
jump process with duration-dependent arrivals, short-run sign reversal, clustered nonzero size, and
sub-diffusive calendar-time scaling. A smooth Gaussian diffusion and memoryless update clock are
poor descriptions of the observed marks.

The one protected continuous-arrival strategy descendant was not rerun. Its prior one-shot result
is already exposed and was rejected: only 65/100 protected decisions were scored, coverage was
`0.65`, failure rate `0.35`, and the coverage, failure-rate, and concentration standards failed.
Reopening it would violate the protected boundary, not improve completeness.

## What the comparison means

Behavioral economics and game theory remain useful for proposing mechanisms and controls, but they
do not replace measurement or statistical representation. A behavioral story becomes a testable
strategy only after it is translated into time-legal variables, fixed rivals, and an out-of-time
decision rule. In this corpus, most such translations failed. The internal path/duration models
currently predict the registered series more reliably than wallet reputation, expert agreement,
crowd breadth, focal prices, or textual ambiguity.

The research ranking is therefore:

1. **Fresh post-jump reversal** — strongest time-series lead; requires executable L2/latency replay.
2. **Longshot fade** — sole behavioral lead; requires sealed fresh events and executable quotes.
3. **Duration-dependent marked-jump process** — strong process model and useful feature substrate,
   but not by itself a directional trade.
4. **All other tested behavioral/game-theoretic strategies** — rejected or scientifically blocked.

No result authorizes production trading.

## Audit artifacts

- [`corpus-campaign-v2/completion.json`](corpus-campaign-v2/completion.json)
- [`corpus-campaign-v2-comparison.json`](corpus-campaign-v2-comparison.json)
- [`behavioral-addon-campaign/completion.json`](behavioral-addon-campaign/completion.json)
- [`fixed-clob-campaign/completion.json`](fixed-clob-campaign/completion.json)
- [`fixed-clob-campaign-comparison.json`](fixed-clob-campaign-comparison.json)
- [`nonreplay-audit-campaign/completion.json`](nonreplay-audit-campaign/completion.json)
- [`behavioral-fill-corpus-receipt.json`](behavioral-fill-corpus-receipt.json)

