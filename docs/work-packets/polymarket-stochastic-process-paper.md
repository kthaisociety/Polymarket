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

Source 02 completed and both fixed falsifiers passed. The one-hour event-equal mean was negative in
both chronological halves, non-overlapping event-equal daily change was `-0.00957`, and market- and
event-weighted probabilities exceeded outcome frequencies by more than two percentage points at
all four horizons. This opens a separate calibration/financial-theory branch, but does not consume
one of the three declared process-model branches. Its next allowed analyses are fixed event-cluster
uncertainty, predeclared semantic/regime stability, and chronological calibration models that must
compare against the raw market probability.

### Fixed source 03 arrival-model comparison

Source 03 consumes the first declared process-model branch. Its prediction question is whether the
next retained sample changes, conditional on the next sample arriving 0.75–1.25 elapsed hours
later. The label matures at that next sample. Decisions require 24 consecutive regular prior
increments; an irregular gap resets the warm-up.

The fixed models are:

1. earlier-event equal-weight move rate;
2. ridge-logistic state model using probability, boundary distance, and winsorized `.005` logit;
3. the same model plus `log(1 + prior quiet-run observations)` and the fraction of the previous 24
   regular increments that were exactly zero.

Every mean, scale, class prior, and coefficient is fitted on earlier whole events with equal total
weight per represented event. Expanding folds train through event 39 and test events in fixed
15-event blocks beginning at event 40; the final block ends at event 156. Ridge penalty `0.1`, four
Newton updates, feature definitions, and block boundaries are fixed.

The state-plus-staleness model passes only if it improves both observation and event-macro Brier
and event-macro log loss versus state alone, reduces event-macro Brier by at least 5%, wins at least
60% of represented events, and improves event-macro Brier in both chronological halves. This is a
process-arrival result, not a price-direction or trading claim.

Source 03 completed and passed every fixed gate. Across 566,501 out-of-time predictions in 113
later events, adding staleness to price state reduced event-macro Brier from `0.22950` to `0.16610`,
a `27.63%` relative improvement, and reduced event-macro log loss from `0.65030` to `0.50256`.
The full model beat the state-only model in 112/113 events and in both chronological halves. Its
two standardized staleness coefficients remained negative in all eight expanding folds, ending at
`-0.541` for log quiet run and `-0.520` for the prior-24 zero fraction.

This is evidence that the observed update clock is not memoryless: conditional update hazard falls
with recent inactivity even after controlling for the probability state. The two correlated
staleness variables are not separately causal, and the result may partly describe the public
sampling mechanism. The next declared process branch must model the mark conditional on a nonzero
update; it cannot reinterpret arrival prediction as direction or profit.

### Fixed source 04 nonzero-sign comparison

Source 04 consumes the second process-model branch. Conditional on a nonzero registered change
after 24 consecutive regular increments, it predicts whether that change is positive. The decision
time is the preceding sample and the label matures at the next sample. Current price, boundary
distance, winsorized logit, and log time-to-close form the state model. The path model adds the
previous nonzero sign, previous regular change, prior-24 net change, prior-24 absolute variation,
and prior-24 zero fraction.

The expanding whole-event folds, event-equal training weights, ridge penalty `0.1`, and four Newton
updates match source 03. The path model passes only if it improves observation and event-macro
Brier and event-macro log loss, improves event-macro Brier by at least 2%, wins at least 60% of
represented events, and improves both chronological halves. A pass would show path dependence in
the registered nonzero mark sign; it would not by itself distinguish belief dynamics from sampled
price microstructure or establish an executable strategy.

Source 04 completed and passed every fixed gate. Across 174,956 out-of-time nonzero updates in 113
later events, adding path history reduced event-macro Brier from `0.24796` to `0.23815`, a `3.96%`
relative improvement, and event-macro log loss from `0.68907` to `0.66912`. It beat state alone in
96/113 events and in both chronological halves. The prior-nonzero-sign coefficient dominated the
other path terms and was negative in all eight folds (`-0.221` to `-0.286` on the standardized
scale), consistent with short-horizon sign reversal.

This rejects a conditionally independent mark-sign description for the registered samples. The
effect is modest beside the arrival result, and price state alone did not improve event-macro error
over the earlier-event constant. Sampling, bid/ask bounce, contract rounding, and aggregation
remain rivals to belief mean reversion. The third process-model branch must test the nonzero mark
magnitude/distribution before any combined hurdle process is frozen.

### Fixed source 05 nonzero-magnitude comparison

Source 05 consumes the third process-model branch. Conditional on a nonzero regular-hour change
after 24 legal prior increments, its target is `log(max(1e-6, abs(change)))`. It compares an
earlier-event constant, a ridge state model (price, boundary distance, logit, and time-to-close),
and the same model plus prior nonzero size, last absolute change, prior-24 absolute variation,
prior-24 maximum absolute change, and prior-24 zero fraction. Folds and event-equal weighting match
sources 03–04.

The path model passes only with lower observation/event-macro MSE and event-macro MAE, at least 2%
event-macro MSE improvement, wins in 60% of events, and improvement in both chronological halves.
Using its earlier-event residual scales, Gaussian, Laplace, and Student-t with three degrees of
freedom are compared by out-of-time negative log likelihood on the common log-magnitude scale. A
heavy-tail law passes only if Laplace or Student-t improves both observation and event-macro mean
NLL by at least 2% relative to Gaussian.
