# Work packet: Polymarket stochastic-process paper

## Identity

- Packet: `polymarket.discriminate-stochastic-process-for-paper`.
- Paper mandate: *Financial Mathematics and Machine Learning on Prediction Markets*.
- Research questions from the verified project plan:
  1. How much established equity and option theory transfers to prediction markets, and which
     structural differences require different mathematics?
  2. Which type of stochastic process best describes a Polymarket contract?
- Empirical core: question 2. Question 1 is answered by interpreting the same controlled evidence.
- Starting repository state: `bdl-polymarket@6106701a` on
  `codex/polymarket-time-series-research`.

## Exact research question

For the retained sampled YES-probability process of resolved binary Polymarket contracts, which of
the following descriptions survives chronological whole-event controls?

1. a bounded martingale with approximately continuous diffusion increments;
2. a bounded state-dependent diffusion or jump-diffusion;
3. a sticky, zero-inflated marked jump process with state- and age-dependent arrival intensity;
4. an apparent process created mainly by irregular sampling and stale probability observations.

The question concerns the registered sampled-probability process. It does not silently claim the
same law for latent beliefs, executable quotes, or transaction prices.

## Theory-transfer map

The paper begins from finance concepts that remain relevant but need qualification:

- **No-arbitrage and martingales:** a fairly priced binary payoff is naturally bounded in `[0, 1]`
  and converges to `0` or `1`; unpredictability of signed changes does not imply independent or
  Gaussian increments.
- **Diffusion and stochastic volatility:** conditional variance and time scaling remain testable,
  but an unbounded geometric Brownian motion is structurally incompatible with a binary payoff.
- **Jump models:** event news can arrive discontinuously, so jump intensity and jump sizes may
  matter more than smooth local volatility.
- **Market microstructure:** repeated sampled prices, sparse updates, and bid/ask mechanics can
  create apparent zeros or reversal without describing the latent efficient price.
- **Finite maturity and absorption:** time to close/resolution and the terminal binary payout are
  first-class state variables rather than small corrections.

The empirical work will determine which statements are supported. This map is motivation, not a
conclusion.

## Data authority and population

- Expanded immutable corpus:
  `polymarket-corpus:8c73260377ea5cb3e569bbc3c744ce9b62a95c8f54dafb73d07671845ccec4c6`,
  1,000 contracts, 235 events, and 1,180,437 sampled probabilities.
- Exact ancestor corpus:
  `polymarket-corpus:610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f`.
- The public fresh-replication composition excludes every ancestor event and the expanded final
  47-event protected block before authored code receives a data capability.
- Registered fields permitted for the opening analysis: market identity, authoritative event
  ordinal, observation ordinal/time, sampled YES probability, close time, and terminal payout.
- Historical samples are not bids, asks, depth, fills, or guaranteed executable prices.
- The cohort conditions on resolved binary contracts with at least 24 retained samples and the
  fixed corpus selection in the expanded-corpus receipt.

## Observation clocks

The opening analysis keeps three clocks distinct:

1. observation ordinal;
2. elapsed UTC time between retained samples;
3. elapsed time remaining to the recorded market close.

Primary one-step diagnostics use consecutive observations whose gap is between 0.75 and 1.25
hours. All-consecutive diagnostics remain coverage checks. Multi-step variance ratios use exact
2/4/8/24-observation lags only when elapsed time is within 25% of the named horizon.

## Predeclared opening analysis

Source 01 is descriptive model discrimination. It will retain:

- population, chronology, gap, and missing/order diagnostics;
- exact-zero mass and nonzero-move frequency;
- raw increment mean, variance, lag dependence, tail quantiles, and kurtosis;
- 2/4/8/24-hour variance ratios;
- state-conditional drift and variance across five fixed probability bands;
- move-arrival probability across four fixed quiet-run bands: `0`, `1-5`, `6-23`, and `24+`
  consecutive unchanged observations;
- move activity across fixed time-to-close bands: `<=24h`, `24-72h`, `72-168h`, and `>168h`;
- waiting times between nonzero moves and sign continuation/reversal diagnostics;
- low/high boundary persistence;
- sparse terminal-probability Brier/calibration summaries by time to close;
- event-level distributions so one large event cannot define the conclusion.

No fitted model, feature selection, threshold search, trading rule, or protected access is allowed
in source 01.

## Fixed interpretation rules

These rules were declared from the older 31-event study before source 01 accesses the expanded
fresh-development values.

- A smooth continuous-diffusion description is contradicted if the regular interior process has
  at least 25% exact zero increments, increment kurtosis at least 20, or a 24-hour variance ratio
  outside `[0.75, 1.25]`.
- A memoryless constant-intensity jump arrival is questioned if one-step move rates differ by more
  than a factor of two between the `quiet=0` and `quiet>=24` bands. This is descriptive until a
  later chronological model comparison tests the same mechanism.
- A martingale-like conditional mean remains the default unless a later predeclared drift model
  improves event-macro signed-change MSE by at least 5%, wins at least 60% of test events, improves
  both chronological halves, and survives a one-observation delay. Source 01 cannot pass or fail
  this predictive gate.
- State-dependent variance or move intensity is evidence about conditional risk, not directional
  trading alpha.
- Repeated sampled values may be an observation-process effect. Without historical quote updates,
  source 01 may characterize the registered process but cannot identify the latent efficient-price
  law.

## Declared later trial budget

If source 01 succeeds, at most three model-comparison branches may be opened before a frozen
protected request:

1. **Arrival model:** constant move probability versus state-only versus state-plus-staleness.
2. **Nonzero mark model:** zero drift with state scale versus state-dependent signed drift and
   heavy-tail magnitude alternatives.
3. **Composed hurdle model:** arrival probability multiplied by the conditional nonzero mark law,
   compared with a bounded diffusion baseline by chronological event-macro predictive score and
   fixed residual diagnostics.

Every fit must use earlier whole events with equal total event weight. The final protected block
may be requested only after exact labels, features, models, metrics, and rejection gates are frozen
through the formal harness.

## Paper-grade outputs

The research package must ultimately retain:

- an exact data and sampling table;
- model equations and mapping from theory to observable restrictions;
- descriptive process-signature tables and figures;
- chronological out-of-sample model comparison;
- event-level and regime stability;
- a protected result or an explicit protected failure/negative result;
- limitations separating sampled probabilities, beliefs, quotes, and executable returns;
- a reproducible paper outline and evidence index.

## Explicit exclusions

- No production writes or credential output.
- No Kthais, production-engine, or sibling-repository changes.
- No claim that current market price equals objective probability without assumptions.
- No treating dependent contracts or overlapping rows as IID.
- No synthetic paths before the observed process and fitted parameters are legally specified.
- No strategy/PnL claim from sampled probabilities.
- No post-result replacement of the declared process families or gates.

## Completion status

**OPEN — SOURCE 01 COMPLETE.** The verified project plan has been translated into an exact Chronos
mandate. Source 01 executed successfully over 562 markets/157 fresh development events while the
31-event ancestor and final 47-event protected block remained unavailable. Its exact receipt is
retained under `studies/polymarket-stochastic-process-paper-2026-08-18/`.

The opening evidence contradicts a smooth continuous diffusion and constant-intensity update
clock. Before the declared arrival-model branch is fitted, one fixed composition diagnostic must
test whether the strong negative mean increment is explained by unequal market/event weighting,
terminal convergence, current state, and realized payout. That diagnostic may close a false drift
interpretation but cannot create a predictive candidate.

### Fixed source 02 composition diagnostic

Source 02 is fixed before execution to report:

- regular one-hour drift under observation, market-equal, and event-equal weighting;
- event-equal drift in the first and second chronological halves;
- non-overlapping approximately 24-hour drift under the same market/event hierarchy;
- drift and endpoint movement conditional on eventual payout, for diagnosis only;
- drift by current probability and time-to-close bands;
- one closest sample per market at 24/72/168/336 hours before close, admitted only within fixed
  tolerances of 12/12/24/24 hours;
- market-weighted and event-macro calibration at each horizon, plus fixed probability-bin
  reliability rows.

The negative-drift lead survives this falsifier only if regular event-equal drift is negative in
both chronological halves and non-overlapping daily event-equal drift is also negative. A broad
overpricing interpretation requires mean probability to exceed outcome frequency by at least two
percentage points at three of four fixed horizons under both market weighting and event-macro
weighting. Payout-conditional results cannot be used as features or trading evidence.
