# Polymarket stochastic-process paper study

Epistemic status: **EXPLORATORY PROCESS REPLICATION — PROTECTED DATA UNEXPOSED**.

This study operationalizes the two research questions in the KTH AI Society project plan
*Financial Mathematics and Machine Learning on Prediction Markets*. The empirical core asks which
stochastic-process family best describes registered Polymarket YES-probability samples. The
financial-theory question is answered by identifying which restrictions from martingale,
diffusion, jump, finite-maturity, and microstructure theory survive the evidence.

The exact scope, process families, observation clocks, opening diagnostics, interpretation rules,
later trial budget, and paper deliverables are fixed in the
[work packet](../../docs/work-packets/polymarket-stochastic-process-paper.md).

The first source uses the expanded corpus only through its ancestor-bound fresh-development
capability. All 31 ancestor events and the final 47 protected events are absent from its views.
Historical sampled probabilities are not represented as quotes or executable prices.

This snapshot is an experiment anchor, not Chronos's permanent research universe. The study may
discover additional Polymarket contracts and public data, retain successor content-addressed
corpora, and open new predeclared replications. Each experiment remains bound to its exact bytes,
selection, temporal registration, and protected split; later expansion never mutates earlier
evidence or inherits authority across different field types.

## Opening source

- [`source/01_fresh_process_signatures.py`](source/01_fresh_process_signatures.py): deterministic
  coverage and process-signature diagnostics. It fits no model and cannot access protected data.
- [`source/02_drift_composition_falsifier.py`](source/02_drift_composition_falsifier.py): fixed
  weighting, terminal-convergence, payout-conditional, and fixed-horizon calibration diagnostic.
  Realized payout is diagnostic-only and cannot enter a predictor.
- [`source/03_arrival_model_comparison.py`](source/03_arrival_model_comparison.py): predeclared
  chronological comparison of constant, price-state, and price-state-plus-staleness next-hour
  update probabilities.
- [`source/04_nonzero_sign_model_comparison.py`](source/04_nonzero_sign_model_comparison.py):
  predeclared chronological comparison of constant, state, and state-plus-path models for the sign
  of a nonzero next-hour registered change.
- [`source/05_nonzero_magnitude_model_comparison.py`](source/05_nonzero_magnitude_model_comparison.py):
  predeclared chronological prediction of nonzero log magnitude plus Gaussian, Laplace, and
  Student-t residual-law comparison.
- [`source/06_development_semantic_inventory.py`](source/06_development_semantic_inventory.py):
  development-only question/lifecycle inventory plus fixed time-spread selection for an official
  five-minute measurement expansion; it reads no payouts or probability values.
- [`source/07_successor_partition_identity.py`](source/07_successor_partition_identity.py):
  zero-field audit of the broader successor corpus against the exact 1,000-contract ancestor before
  any newly acquired value is exposed.
- [`source/10_five_minute_measurement_falsifier.py`](source/10_five_minute_measurement_falsifier.py):
  fixed comparison of ten preselected official five-minute paths with the same-market retained
  hourly paths. It tests sampling alignment, zero mass, elapsed-duration dependence, variance
  scaling, sign reversal, and probability-grid concentration without fitting a trade model.
- [`source/11_event_cluster_process_uncertainty.py`](source/11_event_cluster_process_uncertainty.py):
  fixed whole-event prevalence, chronological-half, and deterministic event-resampling uncertainty
  for zero mass, 24-hour variance scaling, elapsed-duration dependence, and nonzero reversal.

The paper-working literature and claim map is retained in
[`literature/theory-transfer-map.md`](literature/theory-transfer-map.md). It distinguishes direct,
conditional, and failed transfers from conventional finance and ties each provisional process
claim to a primary source and a Chronos receipt.

## Opening result

Source 01 succeeded through the public fresh-replication runner under a recorded 600-second/4 GB
worker envelope. Its source SHA-256 is
`de8b8cdffa1069d4c78cfe4f1de9c6c79ac802e18360fdce0fdcc91c9fd15dae`. The exact receipt is
[`development-receipts/01_fresh_process_signatures.json`](development-receipts/01_fresh_process_signatures.json),
SHA-256 `53cb9e82d71ed5d5b16b2adfd1a99512d9a76c48bc28a9a3a42745aa2c2df6cb`.

Authority and coverage:

- 562 markets, 157 fresh development events, and 803,862 sampled probabilities;
- 31 ancestor events/217 markets embargoed;
- final 47 events/221 markets protected and unavailable;
- zero chronology breaks, unknown close times, or negative time-to-close rows;
- exact actual access limited to market/event/observation identity, sample time/probability, close
  time, and terminal payout.

### Process signatures

- 69.62% of all consecutive probability samples were exactly unchanged.
- Among regular interior one-hour samples, 62.40% were unchanged.
- Regular increment kurtosis was 157.10; absolute-change quantiles were 0¢, 1¢, 9¢, and 32¢ at
  the 50th, 90th, 99th, and 99.9th percentiles.
- Variance ratios fell from 0.723 at two hours to 0.536/0.393/0.235 at 4/8/24 hours instead of
  remaining near one.
- Low- and high-boundary next-sample persistence measured 98.99% and 97.07%.
- Consecutive nonzero moves reversed sign 62.21% of the time; immediately adjacent nonzero moves
  reversed 62.91% of the time.

The predeclared smooth-continuous-diffusion signature is therefore contradicted on every decisive
dimension: point mass, tails, and time scaling.

### The update clock has memory

The next regular-sample move rate depended sharply on how long the sampled price had been quiet:

| Prior unchanged samples | Rows | Next-sample move rate | Mean absolute change |
|---|---:|---:|---:|
| 0 | 236,973 | 68.24% | 1.173¢ |
| 1–5 | 199,150 | 28.90% | 0.340¢ |
| 6–23 | 145,703 | 9.50% | 0.116¢ |
| 24+ | 199,562 | 1.72% | 0.025¢ |

The `24+` move rate is only 2.53% of the `0`-quiet rate. That is incompatible with the packet's
constant-intensity tolerance and makes age/staleness part of the observed state. It remains unclear
how much of this is economic inactivity versus the public price-history sampling process.

### Martingale and terminal-probability questions remain open

The observation-weighted regular mean increment was `-0.0001804`, and only 14 of 157 event means
were positive. State bands showed positive mean change below `.20` and negative mean change in the
interior/high bands. Sparse terminal-calibration samples also had mean probabilities above eventual
YES frequencies in every time-to-close band.

This is a strong falsifying lead, not yet proof of predictable drift or market inefficiency. The
resolved cohort has many low-probability YES contracts, unequal paths per market/event, terminal
convergence, and related contracts. The next controlled source must separate observation,
market-equal, event-equal, payout-conditional, state, and time-to-close composition before a drift
model is permitted.

## Current process conclusion

For the registered hourly samples, the leading description is a **bounded, sticky, zero-inflated,
heavy-tailed jump process with state- and age-dependent update intensity**. A smooth Gaussian
diffusion and memoryless jump clock are rejected as descriptions of the observations. Whether the
conditional mean is martingale-like after correct composition controls remains unresolved. The
latent belief and executable quote processes remain unidentified.

No trade rule, formal candidate, protected request, finding, or durable-memory update has been
created.

## Drift-composition result

Source 02 succeeded with source SHA-256
`f6d2fec0f8bc25c37b863f5c0df79e77de273c16cad6e2ae134b66c5b9b5a8fe`. Its exact receipt is
[`development-receipts/02_drift_composition_falsifier.json`](development-receipts/02_drift_composition_falsifier.json),
SHA-256 `8f8765ad35db116bb30d64f45d3c9325edc5bb46bcd6863972878f3f85c2c699`.

The negative mean increment did not disappear when long paths or large events stopped dominating:

| Weighting/view | Mean probability change |
|---|---:|
| Regular one-hour, observation weighted | −0.0180¢ |
| Regular one-hour, market equal | −0.0456¢ |
| Regular one-hour, event equal | −0.0449¢ |
| Early-half event equal | −0.0406¢ |
| Late-half event equal | −0.0492¢ |
| Non-overlapping daily, market equal | −1.054¢ |
| Non-overlapping daily, event equal | −0.957¢ |

Only 14/157 event-equal one-hour means were positive. Event-equal daily drift remained negative
through its 90th percentile (`−0.000748`). The predeclared drift-composition falsifier therefore
passed.

Realized-payout diagnosis explains the direction mechanically but not the cross-sectional
calibration gap. The 509 eventual NO contracts lost 31.69¢ from first to last retained sample on
average, while 53 eventual YES contracts gained 35.39¢. Payout is future information and cannot be
a predictor.

### Fixed-horizon calibration lead

One closest retained sample per market produced the following calibration evidence:

| Hours before close | Markets / events | Mean price | YES rate | Price minus YES rate | Event-macro gap |
|---:|---:|---:|---:|---:|---:|
| 24 | 562 / 157 | 13.53% | 9.43% | +4.10 pp | +4.14 pp |
| 72 | 548 / 156 | 13.53% | 8.58% | +4.95 pp | +4.69 pp |
| 168 | 523 / 149 | 17.44% | 8.22% | +9.22 pp | +7.01 pp |
| 336 | 403 / 125 | 14.89% | 7.94% | +6.95 pp | +7.44 pp |

Both market-weighted and event-macro gaps exceeded the fixed two-percentage-point threshold at all
four horizons. The broad-overpricing falsifier passed. Reliability rows show that the gap is
concentrated in low-to-mid probabilities; high-probability cells are small and do not support a
symmetric claim.

This is selection-exposed development evidence for a favorite–longshot-like calibration pattern,
not proof of mispricing. Remaining rivals include semantic event mix, incomplete related-contract
surfaces, cohort selection, and sampled-price versus executable-quote differences. Clustered
uncertainty and fixed semantic/regime tests must run before the paper states a general effect.

## Update-arrival model result

Source 03 succeeded with source SHA-256
`8b8a36423c351a56d6cfafcee6d633a92b2d7d4c5c51339c1f19dbd90c425d78`. Its exact receipt is
[`development-receipts/03_arrival_model_comparison.json`](development-receipts/03_arrival_model_comparison.json),
SHA-256 `810dc73970961bc69386041973c349847b151208d8488f959aaa8e69321353b8`.

The chronological comparison made 566,501 out-of-time predictions over 113 later events:

| Model | Observation Brier | Event-macro Brier | Event-macro log loss |
|---|---:|---:|---:|
| Earlier-event constant rate | 0.21225 | 0.23596 | 0.66533 |
| Price state | 0.21569 | 0.22950 | 0.65030 |
| Price state + staleness | **0.13475** | **0.16610** | **0.50256** |

The full model improved event-macro Brier by 27.63% relative to state alone, won 112/113 event
comparisons, and improved both chronological halves. Its fitted standardized coefficients for log
quiet run and the prior-24 zero fraction were negative in every expanding fold (approximately
`-0.51` to `-0.54` and `-0.44` to `-0.52`, respectively). The predeclared arrival gate passed.

The registered-sample update clock is therefore empirically non-memoryless: recent quiet makes the
next hourly sample less likely to change, beyond the effect of current price state. This supports a
clustered/state-dependent arrival component. It does not identify latent belief updates, quote
changes, trade arrivals, direction, or profitability, and the two correlated inactivity features
must not be read as separately causal.

## Nonzero-update sign result

Source 04 succeeded with source SHA-256
`30c4204795356e940577931da34402b797453c75e40ab1af46ca5cdc1b7f314d`. Its exact receipt is
[`development-receipts/04_nonzero_sign_model_comparison.json`](development-receipts/04_nonzero_sign_model_comparison.json),
SHA-256 `793650747f5d415a2a61ddde30d6b1d1ff5e4782b4c5fb51b7d15ae3cf86fd29`.

The chronological comparison made 174,956 predictions conditional on a nonzero registered hourly
change across 113 later events:

| Model | Observation Brier | Event-macro Brier | Event-macro log loss |
|---|---:|---:|---:|
| Earlier-event constant positive rate | 0.25023 | 0.24795 | 0.68905 |
| Price state + time to close | 0.24983 | 0.24796 | 0.68907 |
| State + prior path | **0.23576** | **0.23815** | **0.66912** |

The full model improved event-macro Brier by 3.96% relative to state alone, won 96/113 event
comparisons, and improved both chronological halves. Its previous-nonzero-sign coefficient was
negative in all eight folds and was much larger than the other path coefficients (`-0.221` to
`-0.286` on the standardized feature scale). The predeclared sign gate passed.

This is out-of-time evidence of short-horizon sign reversal in the registered nonzero marks. It is
not yet evidence that latent beliefs mean-revert or that the reversal survives executable quotes,
fees, spread, and latency. The state-only model did not improve event-macro scores over the constant
baseline, so the main result is path dependence rather than directional information in price level.

Its first execution failed before producing analytical details because the constrained runtime does
not inject a `pi` name. The failed receipt is retained as
[`development-receipts/05_nonzero_magnitude_model_comparison.failed-nameerror.json`](development-receipts/05_nonzero_magnitude_model_comparison.failed-nameerror.json),
SHA-256 `1aaf83367ba4aa70ee7e091b77a3d61400c9c7726d08ab890ecf138729817820`.
No protected values were exposed. The implementation now declares the same fixed numerical
constant locally; the target, features, folds, models, distributions, and gates are unchanged.

The repaired source 05 succeeded with source SHA-256
`38ce508aceb10c066b5f51ce62dac48f1a90dc2e699eedf253d1012829ef516f`. Its exact receipt is
[`development-receipts/05_nonzero_magnitude_model_comparison.json`](development-receipts/05_nonzero_magnitude_model_comparison.json),
SHA-256 `f5a0aff4ba388852752aaadfa8f3b98badee0a6d55e5c1bc0d78f58ba5f80fe7`.

| Model for log absolute nonzero change | Observation MSE | Event-macro MSE | Event-macro MAE |
|---|---:|---:|---:|
| Earlier-event constant | 2.33120 | 2.40022 | 1.27650 |
| Price state + time to close | 1.55492 | 1.36764 | 0.91782 |
| State + prior path | **1.11168** | **1.08572** | **0.80846** |

The path model improved event-macro MSE by 20.61%, won 101/113 events, and improved both halves.
The previous nonzero log-magnitude coefficient was the dominant path term and remained positive in
all folds (`0.449` to `0.515` standardized), establishing conditional magnitude clustering. The
predeclared magnitude gate passed.

| Full-model residual law on log magnitude | Observation mean NLL | Event-macro mean NLL |
|---|---:|---:|
| Gaussian | **1.47738** | **1.46518** |
| Laplace | 1.50360 | 1.48312 |
| Student-t, 3 df | 1.56381 | 1.54454 |

The heavy-tail residual gate failed. The raw increment distribution is heavy-tailed, but after
separating zero arrivals and modeling conditional log size, Gaussian residuals won this fixed
comparison. A conditional lognormal-style size component is therefore the leading simple account,
subject to unmodeled grid rounding and bounded support.

## Five-minute measurement falsifier

Source 10 succeeded with source SHA-256
`103fd2a7ee9a9e102d3ec6c18c91130eeb62e620b72bd6d9f241df3b83babe83`. Its exact receipt is
[`development-receipts/10_five_minute_measurement_falsifier.json`](development-receipts/10_five_minute_measurement_falsifier.json),
SHA-256 `37bc412943cba22665b26f6b2de6f5b9605376d79d510346536bf85834bcedd9`.
All five predeclared checks passed, with zero identity/order breaks and no protected exposure.

The official five-minute panel contains 19,258 observations and 19,012 regular increments across
the ten development markets. The same-window hourly comparison contains 1,580 observations.

| Diagnostic | Five-minute | Same-window hourly |
|---|---:|---:|
| Regular zero rate | 84.94% | 66.11% |
| Interior zero rate | 78.00% | 49.70% |
| Raw increment kurtosis | 203.64 | 200.68 |
| Nonzero sign reversal | 67.87% | 60.55% |
| Adjacent nonzero reversal | 68.23% | 62.11% |
| 4-hour variance ratio | 0.119 | 0.328 |
| 24-hour variance ratio | 0.067 | 0.121 |
| Nonzero changes on 0.001 grid | 63.93% | 62.60% |

Elapsed quiet time predicts five-minute sample movement even more sharply than the earlier
observation-count diagnostic: the next-sample move rate falls from 55.95% with no prior quiet time
to 12.56% within two hours, 1.51% after two-to-24 hours, and 0.20% after at least 24 hours. This is
about a 278-fold decline from the first to last band. The small panel prevents a population claim,
but it directly rejects the idea that the hourly duration effect was created only by using an
hourly clock.

The source comparison is unusually tight: all 1,580 eligible hourly samples found a five-minute
match within ten minutes; 99.49% matched exactly, 99.81% were within one cent, and mean absolute
discrepancy was `0.0000487` probability units (0.00487 cents). Thus the earlier hourly corpus and
the independently acquired official endpoint are effectively measuring the same sampled series on
these markets. This supports measurement robustness, not executability: neither series is a trade
or historical bid/ask quote.

The process conclusion is strengthened to a **bounded, sticky, grid-affected, zero-inflated marked
jump process with duration-dependent arrival intensity, short-run sign reversal, clustered mark
size, and strong sub-diffusive calendar-time scaling**. It remains a model of observed Polymarket
probability samples, not an identified latent-belief process or a trading strategy.

## Whole-event uncertainty and chronological replication

Source 11 ran unchanged on both fresh cohorts. The original-cohort receipt SHA-256 is
`7262b65b8456577c097f64525ef83e57c6ffe37066e0a84559c78c858e2aeda1`; the successor receipt
SHA-256 is `aebb42800f7a63678993f8608a4bd39f7c6fbeb8fd2f74b0d90c8cc5698e11bb`. The event, rather than
the market or sample, is the uncertainty unit.

| Fixed event diagnostic | Original eligible/pass | Original event mean (95% event bootstrap) | Successor eligible/pass | Successor event mean (95% event bootstrap) |
|---|---:|---:|---:|---:|
| Interior zero rate >20% | 138 / 136 | 56.05% (53.46–58.63%) | 26 / 25 | 43.81% (38.71–49.52%) |
| 24h variance ratio <0.75 | 151 / 142 | 0.358 (0.325–0.391) | 26 / 24 | 0.324 (0.250–0.404) |
| 24h-quiet/active move-rate ratio <0.50 | 83 / 83 | 0.063 (0.053–0.074) | 7 / 7 | 0.074 (0.052–0.096) |
| Nonzero reversal >50% | 152 / 134 | 59.42% (58.35–60.50%) | 26 / 21 | 58.45% (55.53–61.41%) |

All four effects retain the same direction in the successor cohort. The long-quiet ratio has only
seven eligible successor events and is therefore a breadth limitation, not a precise population
estimate. Early/late means within each cohort also preserve the qualitative conclusions. The
process description is consequently broad across events and chronology, rather than a pooled-row
artifact, while its exact parameter values are regime-dependent.
