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

## Opening source

- [`source/01_fresh_process_signatures.py`](source/01_fresh_process_signatures.py): deterministic
  coverage and process-signature diagnostics. It fits no model and cannot access protected data.

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
