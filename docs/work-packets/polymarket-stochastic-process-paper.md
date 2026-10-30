# Work packet: Polymarket stochastic-process paper

## Identity

- Packet: `polymarket.discriminate-stochastic-process-for-paper`.
- Paper mandate: *Financial Mathematics and Machine Learning on Prediction Markets*.
- Research questions from the verified project plan:
  1. How much established equity and option theory transfers to prediction markets, and which
     structural differences require different mathematics?
  2. Which type of stochastic process best describes a Polymarket contract?
- Empirical core: question 2. Question 1 is answered by interpreting the same controlled evidence.
- Starting repository state: `historical checkpoint 6106701a` on
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

### Corpus evolution and exploration rule

Chronos is not confined to one permanent corpus. It may continue to inspect the read-only
production database and approved public sources, choose additional contracts or data surfaces for
a named hypothesis, and retain a successor content-addressed corpus. Immutability applies to the
exact snapshot consumed by an experiment: source bytes, selection, identity, and partitions cannot
move after that experiment begins. It does not freeze the future research universe.

Every expansion must therefore follow `discover -> declare need -> acquire read-only -> retain
exact bytes -> register temporal semantics -> partition -> analyze`. Successor corpora preserve
their ancestry and do not overwrite or silently enlarge earlier evidence. New trades, quote/order
book data, alternative sampling frequencies, related-event surfaces, or external signals receive
their own field meanings and availability rules; authority from the hourly sampled-probability
corpus does not transfer automatically.

The 1,000-contract corpus below is the controlled starting snapshot for sources 01–05, not a
permanent data ceiling. Measurement rivals that the snapshot cannot identify should trigger a
bounded expansion when an available source can actually distinguish them. Otherwise they remain
explicit limitations rather than being approximated from the wrong field.

The first successor acquisition is fixed at as-of `2026-08-18T11:40:00+00:00`, `min_points=24`,
`max_markets=2000`, YES `outcome_index=0`, and hourly `fidelity=60`. It uses the existing
chronological production selection, so any additional capacity extends later resolutions after the
first 1,000 rather than re-ranking them by a researched result. Acquisition is registered data,
not evidence; values remain unread until exact ancestry and partitions are established.

The acquisition succeeded with 1,509 contracts, 321 events, and 1,585,740 hourly probability
observations. Its content identity is
`polymarket-corpus:184b83f7f8012da4ca9116c8b6bad2076570ad5f0bada95b22615ee2f5cceae8`.
Relative to the 1,000-contract ancestor it adds 509 contracts and 86 event groups. The sanitized
receipt proves `human_ro`, both read-only settings, repeatable-read isolation, and no durable state
effect. These counts establish material expansion only; they authorize no scientific conclusion.

Source 07 established the successor replication partition by composing the 1,509-contract snapshot
against the exact 1,000-contract ancestor through the existing whole-event boundary. Its authored
body read zero data fields and recorded zero actual accesses. Partition
`f7b47ea95c3630f083552bce84126711fb1a23b20ec7caa33e7527ba977586d7` contains 29 wholly fresh
development events (147 markets), 227 embargoed ancestor events (1,005 markets), and 65 protected
events (357 markets). Eight additional ancestor events lie within the successor's final protected
chronological block; their values remain unavailable. The receipt reports
`protected_values_exposed=false`.

The first successor experiment replayed source 01 unchanged on only those 29 fresh development
events. Across 147 markets and 42,549 observations, regular interior zero mass was `44.85%`,
regular increment kurtosis was `55.01`, and the 24-hour variance ratio was `0.23029`. Move
probability fell from `73.68%` immediately after a move to `2.08%` after at least 24 unchanged
observations; low/high boundary persistence was `98.16%`/`99.12%`. Both frozen signature checks
passed again, while the lower zero mass versus the earlier cohort (`62.40%`) demonstrates material
cross-cohort heterogeneity. Protected values remained unavailable.

The second successor experiment is fixed as an unchanged replay of source 02 on the same 29 fresh
events. Its source bytes and all observation/market/event weighting, chronological-half,
non-overlapping daily, fixed-horizon, and calibration gates predate acquisition. It will test the
negative-drift and broad-overpricing diagnostics without semantic filtering or threshold changes.
Failure will be retained as a non-replication and cannot be repaired after seeing this cohort.

The source 02 replay passed both gates. Regular-hour event-equal drift was `-0.0012374`, negative
in both chronological halves, and non-overlapping daily event-equal drift was `-0.029996`.
Market/event-macro probability-minus-outcome gaps exceeded two points at 72, 168, and 336 hours,
but not at 24 hours. The 336-hour result has only 27 markets in 7 events. Thus the sign-level drift
and broad calibration lead replicated, but magnitudes are heterogeneous and long-horizon coverage
is thin. No inefficiency or tradable-return claim is authorized without semantic/regime stability,
event-cluster uncertainty, and executable quote/spread/fee evidence.

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
- No external application, production-data-service, or sibling-repository changes.
- No claim that current market price equals objective probability without assumptions.
- No treating dependent contracts or overlapping rows as IID.
- No synthetic paths before the observed process and fitted parameters are legally specified.
- No strategy/PnL claim from sampled probabilities.
- No post-result replacement of the declared process families or gates.
- No treating snapshot immutability as a ban on later, separately registered Polymarket discovery.

## Completion status

**OPEN — SOURCE 05 COMPLETE; SUCCESSOR SOURCES 01–02 REPLICATED.** The verified project plan has
been translated into an exact Chronos
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

The first source 05 execution failed with `NameError` because the constrained runtime does not
inject `pi`; it exposed no protected values and produced no analytical details. The failed receipt
is retained. Declaring the identical numerical constant locally repairs execution without changing
the predeclared target, models, distributions, folds, or gates.

The repaired source 05 completed. Across 174,956 out-of-time nonzero marks in 113 later events,
path history reduced event-macro log-magnitude MSE from `1.36764` to `1.08572`, a `20.61%`
improvement, won 101/113 events, and improved both chronological halves. The prior nonzero
log-magnitude coefficient was positive and stable (`0.449` to `0.515`), showing magnitude
clustering beyond bounded price state and time-to-close.

The fixed heavy-tail residual gate failed: on the common conditional log-magnitude scale, Gaussian
residual NLL (`1.46518` event macro) beat Laplace (`1.48312`) and Student-t df3 (`1.54454`). Raw
increments remain extremely heavy-tailed because of the zero mass, changing intensity, and
multiplicative size variation; conditional nonzero log size is instead provisionally compatible
with a Gaussian-residual/lognormal-style component. This is not an exact distributional claim
because price-grid rounding and bounded support remain unmodeled.

### Fixed source 06 discovery and measurement-expansion inventory

Before semantic categories or a higher-frequency measurement comparison are chosen, source 06
will expose only development contract identity, server event identity/ordinal, question, lifecycle,
and registered point count. It reads no payout or probability value. For a five-minute official
CLOB measurement falsifier, it deterministically selects the first registered market from event
ordinals `10, 25, 40, 55, 70, 85, 100, 115, 130, 145`. Missing target ordinals remain missing; no
replacement event may be chosen after inspecting questions.

Each selected market may open one exact public expansion for its YES outcome token over at most the
last seven days before close at five-minute fidelity. Tokens come from retained source identity,
not question inference. The resulting source bytes and registered observations must remain separate
from the hourly corpus and retain the official-endpoint caveats. The planned falsifier asks whether
zero inflation, update-duration dependence, sign reversal, and magnitude clustering survive on a
finer official sampling clock; it does not turn either clock into a quote or trade tape.

The first source 06 execution reached its 120-second worker limit with zero recorded field
accesses and no analytical details. The authored inventory was valid but its result exceeded the
operating-system process-pipe buffer: the parent waited for worker exit before draining the pipe,
while the worker waited for the parent to receive its bounded structured result. The failed receipt
is retained. Chronos may repair this transport deadlock by receiving the already-bounded message
before joining the worker; the source, data grant, selection, and scientific design remain
unchanged. A regression test must cover a result materially larger than a typical pipe buffer
before source 06 is retried.

The transport repair passed its dedicated large-result regression, strict quality checks, and the
complete 470-test Chronos suite. The identical source 06 then completed in 14 seconds. Its exact
receipt catalogues 562 development contracts and selects the first market from all 10 fixed event
ordinals. Seven identity, question, lifecycle, and point-count fields were accessed; no probability,
payout, ancestor, or protected value was read. The receipt SHA-256 is
`e04036b2c07821de014b8ce2e59f5aa9ebe4fe7be9449083c7dbd668959a566e`.

The visible catalog predeclares a semantic-composition falsifier before any category-conditioned
price or outcome statistic is computed. Market questions receive exactly one category under this
fixed precedence: (1) speech/social-post language; (2) election, nomination, or candidate-selection
language; (3) armed-conflict or geopolitical-action language; (4) office-exit, legal, or
institutional-action language; or (5) other. Exact keyword rules must be committed in authored
source before execution. Results will report market and whole-event counts, regular interior zero
mass, quiet-run move rates, 24-hour variance ratios, event-equal drift, and fixed-horizon
probability-minus-outcome gaps by category when coverage exists. No category may be redefined or
merged after its values are observed; sparse rows remain sparse.

Source 08 completed under those fixed rules. The process conclusion was category-stable: interior
zero mass ranged from `57.27%` to `77.36%`, 24-hour variance ratios ranged from `0.1679` to
`0.4935`, and every category's move rate collapsed after 24 unchanged samples. Event-equal regular
drift was negative in all five categories. The calibration conclusion was not homogeneous.
Election/candidate event-macro probability-minus-outcome gaps were only `2.15%`, `0.99%`, `0.77%`,
and `1.58%` at 24/72/168/336 hours, while speech/social-post gaps were `7.06%`, `11.43%`, `20.30%`,
and `29.89%`. Conflict, institutional, and other categories were intermediate or horizon-dependent.

Thus sticky, duration-dependent, sub-diffusive sampled dynamics survive semantic composition, while
aggregate overpricing is partly a semantic-mix result. The question-text taxonomy is deliberately
coarse and cannot establish causal topic effects. Source 08 is now fixed for an unchanged replay on
the 29-event successor development cohort; no successor question has been used to alter its
keywords, precedence, calculations, or sparse-cell policy.

The unchanged successor replay refined that interpretation. The two adequately covered later
categories—speech/social (12 events) and election/candidate (11)—again showed substantial zero
mass, 24-hour variance ratios of `0.3000` and `0.1360`, and sharply duration-dependent update
hazards. Negative event-equal drift appeared in every category row, although the remaining three
categories contain only 1–3 events. Calibration was chronologically unstable within topic: later
election event-macro gaps rose to `6.89%`–`14.11%`, while later speech/social was approximately
calibrated at 24 hours but reached `14.47%` at 168 hours. The paper should therefore describe
calibration as a semantic-by-regime phenomenon, not a universal overpricing constant or a stable
topic premium.

The fixed source-06 measurement sample cannot enter the official CLOB expansion path from question
or market text alone: the public adapter requires the exact server-provided outcome index and token.
Chronos therefore adds those two identity fields to the existing development-only outcome view.
They are copied from the retained contract outcome selected by the corpus request, remain absent
for ancestor/protected contracts, and are recorded only when authored code actually reads them.
This is an identity/authority seam for the already-declared measurement falsifier, not a new price,
label, feature, or protected capability. A causal test must prove the protected token cannot appear.

Source 09 is fixed before reading either new identity field. It selects the first registered market
from the same source-06 event ordinals in ordinal order and emits exact environment, market, event,
outcome-index, outcome-token, and five-minute window identities. Each window ends at recorded close,
starts at the later of market open or seven days before close, and uses integral Unix seconds.
Missing targets remain missing. It reads no probability or payout. Only this manifest may be turned
into strict `polymarket-price-history-need/v1` documents and passive scout requests; public fetching
remains a later exact, content-addressed transition.

Source 09 completed with all 10 fixed targets. The receipt SHA-256 is
`e4270a572f3dd9df26d42e4fb23ce3f4ec66d5e3618dd9e03b1a56b9d882ec18`. Every selected row is the
retained YES outcome at index zero, carries an exact decimal CLOB token, uses five-minute fidelity,
and spans no more than the final seven days before close. Seven identity/lifecycle fields were read;
probability, payout, ancestor, and protected fields were not accessed. The manifest is authority
for generating exact need/scout documents only, not evidence about the five-minute process.

The first exact acquisition retained all ten official JSON responses but registered none: every
offline strict transform reached the generic workspace's 10-second limit. Value-free attempt
receipts identify `TRANSFORMATION_TIMEOUT`. Inspection exposed the same receive-order defect fixed
earlier in exploratory analysis: `DataWorkspace.derive` joined its child before draining a bounded
result larger than the process-pipe buffer. The failed aggregate receipt is retained. A narrow
receive-before-join repair and large-derived-result regression are allowed without changing any
need, source, transform, or scientific rule; the retry must use the identical retained source
requests and exact candidate identities.

The repaired exact retry registered all ten fixed slices in 4.4 seconds: 19,258 sampled
probabilities total, with 1,378–2,001 observations per market. The value-free acquisition receipt
has SHA-256 `eced7839e2db660e8ab2d94310df578bc4329124d3b12d2904f0ad4e82ebf54a`.
This is an acquisition checkpoint rather than a scientific finding. No five-minute value may be
read until its authored measurement estimands and comparison rules are committed.

The fixed measurement source uses the ten already selected markets and compares their official
five-minute paths with their retained hourly paths over the five-minute panel's observed coverage.
Regular gaps use an 80–120% tolerance. Fixed outputs are zero mass, raw increment kurtosis,
elapsed-duration move rates (zero, up to two hours, two-to-24 hours, and at least 24 hours),
one/four/24-hour variance ratios, nonzero sign reversal, 0.001-grid concentration, and nearest
cross-source agreement within ten minutes. The descriptive gates are frozen at: interior zero mass
at least 50%; 24-hour-or-longer quiet move rate no more than half the zero-quiet rate; five-minute
24-hour variance ratio below 0.75; nonzero reversal above 55%; and at least 80% cross-source
coverage with at most one-cent mean absolute discrepancy and at least 90% within one cent. These
rules test whether hourly process signatures are robust to measurement clock and source; they are
not a trading claim.

Source 10 passed all five fixed checks with receipt SHA-256
`37bc412943cba22665b26f6b2de6f5b9605376d79d510346536bf85834bcedd9`. Five-minute interior zero
mass was `78.00%`, raw kurtosis `203.64`, nonzero reversal `67.87%`, and four/24-hour variance ratios
`0.119/0.067`. The elapsed-duration move rate declined from `55.95%` with zero quiet time to `0.20%`
after at least 24 hours. All 1,580 eligible hourly observations matched the official five-minute
panel within ten minutes; `99.49%` were exact and mean absolute discrepancy was `0.0000487`.

The measurement rival is therefore materially weakened: the registered hourly corpus agrees
almost exactly with an independently acquired official endpoint, and sticky, heavy-tailed,
duration-dependent, reversing, sub-diffusive signatures become stronger at five-minute fidelity.
The result is limited to ten preselected development markets and identifies the observed sampled
process only. It does not identify trades, executable quotes, latent beliefs, or profit.

The next fixed source moves uncertainty to the whole-event level. For every development event it
computes an interior zero rate only with at least 100 eligible increments, a 24-hour variance ratio
only with at least 100 base and horizon increments, an elapsed 24-hour-quiet/zero-quiet move-rate
ratio only with at least 50 observations in both bands, and a nonzero reversal rate only with at
least 50 sign pairs. Missing event metrics remain missing. It reports event-equal mean, median,
10th/90th percentiles, chronological-half means, fixed threshold prevalence, and a deterministic
2,000-resample event-bootstrap interval for the eligible-event mean. Fixed thresholds are zero
mass above 20%, 24-hour variance ratio below 0.75, quiet-rate ratio below 0.50, and reversal above
50%. This is a cluster-robust prevalence diagnostic, not a trade or significance claim.

Source 11 succeeded unchanged on the 157-event original fresh cohort and 29-event successor
cohort. Original/successor eligible-event prevalence was 136/138 and 25/26 for interior zero mass,
142/151 and 24/26 for sub-0.75 24-hour variance ratios, 83/83 and 7/7 for sub-0.50 long-quiet
move-rate ratios, and 134/152 and 21/26 for above-half nonzero reversal. Fixed event-bootstrap mean
intervals stayed entirely on the predicted side in both cohorts. Exact original/successor receipt
hashes are `7262b65b8456577c097f64525ef83e57c6ffe37066e0a84559c78c858e2aeda1` and
`aebb42800f7a63678993f8608a4bd39f7c6fbeb8fd2f74b0d90c8cc5698e11bb`. The successor long-quiet
estimate has only seven eligible events and must remain labeled sparse.

### Fixed source 12 composed process-family comparison

Source 12 consumes the third and final declared process-model branch. It compares four complete
one-hour observation laws over the same rows after 24 regular warm-up increments: (1) a bounded
zero-drift Gaussian diffusion with variance proportional to `p(1-p)` and fixed probability/
time-to-close cells; (2) a memoryless zero-inflated jump with Bernoulli sign and lognormal nonzero
magnitude; (3) a state-conditioned hurdle using probability/time-to-close cells; and (4) a full
hurdle whose arrival cells add quiet duration, sign cells add previous nonzero sign, and magnitude
cells add previous nonzero magnitude. Every cell shrinks toward the event-equal global law with
exactly one event of prior weight.

All four models assign probability to the same fixed interval of half-width `0.0005` around the
observed probability change. Exact zero is a point mass only under hurdle families. Expanding folds
train through event 39 and test fixed 15-event blocks through event 156. The full family passes only
if it beats both the state hurdle and diffusion under observation and event-macro negative log
score, improves event-macro score at least 2% over state, wins at least 60% of events against both,
and beats both in each chronological half. Its all-development fitted law may be retained only for
a separately authored, unchanged successor replay; it grants no protected access or trading claim.

Source 13 is frozen from source 12's exact all-development parameter arrays before any successor
value is read. It preserves the four laws, 0.001-wide interval score, 24-increment warm-up, and
two-percent/60%-event/both-half gates, performs no fitting, and may run only on the 29 fresh events
of successor partition `f7b47ea95c3630f083552bce84126711fb1a23b20ec7caa33e7527ba977586d7`.
Its parent source/receipt hashes are
`13ea0c25a8e65da52cad44f4fa70a863790760cb9f2d67774769744cefbb477b` and
`2c107a29710e3dd9d13cbf24be00e655b4b0a5c3a628fd8026670a1ad88cd9c5`.

Source 12 passed its fixed gate. Event-macro NLL was `3.5779` for bounded diffusion, `2.2138` for
the memoryless hurdle, `2.1038` for the state hurdle, and `1.9409` for the full hurdle across
566,501 out-of-time rows/113 events. The full law improved 7.74% over state, won 112/113 events
against state and 113/113 against diffusion, and improved both chronological halves. This
authorizes the already frozen source-13 fresh successor replay, not protected access.

Source 13 passed unchanged on the later successor development cohort. Across 17,671 predictions
and 27 eligible events, event-macro NLL was `4.5819` for bounded diffusion, `3.2401` for the
memoryless hurdle, `3.1161` for the state hurdle, and `2.8704` for the frozen full hurdle. The full
law improved 7.88% over state, won 27/27 events against state and diffusion, and beat both in each
chronological half. Source and receipt SHA-256 are
`0934e2f9283a772a65e9f1080a0b9ad5c53f310acfe29e95df205e291fd303d4` and
`dc48119c03b492217c3ab26ae781aaf1e6a5a87342d772cbcb78057095940e13`. This is a no-refit fresh
replication, not a protected result or permission to change the model, gates, or claim.

### Backtest gate memo: hurdle-arrival component

Recommendation: **REQUEST_INDEPENDENT_ASSESSMENT only if the formal replay below passes exactly**.

The complete source-12/source-13 density law cannot enter the current protected evaluator without
new distribution-valued prediction and task-specific log-score machinery. The canonical backtest
specification permits such metrics, but the implementation map records distributional metric
plugins as an open capability. Encoding negative log likelihood as scalar regression error would
let the prediction depend on its unknown outcome and is forbidden. Protected evaluation is
therefore narrowed to the already selected law's arrival component: the probability that the next
regular registered hourly probability changes. This does not upgrade the complete density result
to protected status.

The exact candidate is an event-equal 20-cell Bernoulli hurdle arrival law over five fixed
probability bands and four fixed quiet-duration bands. Each cell shrinks to the event-equal global
move rate with exactly one event of prior weight. It uses only legal probability history; its label
is one when the first registered next sample arrives 0.75--1.25 elapsed hours after the current
sample and changes, and zero when it is unchanged. Fitting remains inside every expanding temporal
boundary and prediction receives no outcome. The formal development schedule uses at most five
markets at one common metadata-selected decision anchor per whole event, preventing a same-event
label from maturing between rows at that anchor. The exact source, sample keys, evidence, and
predeclaration must be frozen before any protected value is disclosed.

The first committed formal driver was stopped operationally after fifteen minutes without a result
or protected exposure. Profiling by construction identified repeated catalog-wide information-set
filtering, not worker startup or model fitting, as the avoidable cost. The v2 data protocol retains
the same decision keys and scientific program but registers only the observations the declared
program can consume: the last 25 samples at each anchor and samples in its next 75 minutes. Quiet
duration saturates at 24, so this projection preserves every feature and label exactly. Thresholds,
gates, model code, event anchors, and protected period are unchanged. The aborted attempt has no
scientific result; Git preserves its exact source history.

The first v2 execution failed before authored development because the projection joined canonical
sorted `SampleKey` dimensions to source-order observation dimensions without canonicalizing the
latter. It registered zero observations and stopped at plan construction; no authored value or
protected capability was reached. Canonicalizing the join key is an identity-only repair. It
changes no selected row or scientific rule and is fixed before the next replay.

The same pre-execution audit also caught that a standalone standard partition would combine the
31-event ancestor with the 157-event fresh development cohort. The formal driver now composes the
same exact ancestor-aware replication partition used by sources 01--12 and derives the protected
47 events from the standard chronological partition. Ancestor events remain embargoed rather than
silently entering development or protected evidence.

Formal development must contain at least 200 out-of-fold predictions over at least 80 events, have
observation and event-macro Brier/MSE no greater than `0.20`, early- and late-event macro Brier no
greater than `0.22`, absolute mean prediction-minus-outcome no greater than `0.05`, no individual
event contributing more than 10% of total squared error, and no chronology, identity, capability,
or protected-access break. The complete-law state and diffusion comparisons remain the fixed
selection ancestry rather than being smuggled into this narrower scalar evaluator. Failure means
`REJECT` or `REVISE`, not threshold repair.

If that replay passes, the predeclared protected plan is the original snapshot's final 47 whole
events under a literal historical walk-forward, using the same metadata-only anchor rule and exact
frozen authored source. It refits the frozen recipe at each declared decision using only mature
earlier rows. The evaluator reports MSE (the Brier score for this binary label), MAE, coverage,
failure rate, temporal absolute-error stability, and squared-error concentration, with no per-time
or per-market value disclosure. Promotion requires MSE at most `0.20`, MAE at most `0.40`, coverage
at least `0.95`, failure rate at most `0.05`, absolute-error standard deviation at most `0.30`, and
maximum squared-error concentration at most `0.05`. Any execution insufficiency or non-finite
evidence rejects. The bounded claim is only that this exact sampled-process arrival recipe met that
absolute standard on this retained holdout; it does not assert superiority to every comparator,
latent-belief dynamics, causality, tradeability, or profit.

Satisfied before exposure: source/receipt ancestry is exact; the later no-refit cohort replicated
the complete law; labels and predictors have distinct clocks; every search branch and failure is
retained; both protected blocks remain recorded as unexposed. Remaining blockers are the exact
formal replay, independent freeze decision, exact plan issuance, protected-resource authority,
governance permit, and independent validation. Only those authorities may expose or promote.

The first coordinator execution then failed closed because the declared 300-prediction minimum was
impossible for the metadata-fixed population: 337 development decisions minus the mandatory first
100 training rows allow at most 237 out-of-fold predictions. This count was established from keys
and event identities only, before any metric or outcome was returned. The feasibility minimum is
therefore corrected to 200 while retaining the 100-row training boundary, 80-event breadth, every
quality/calibration/concentration threshold, the exact model and label, and all protected rules.
The protected schedule contains 169 decisions across 46 of the final 47 events; the remaining event
has no timestamp-eligible anchor under the predeclared rule and is not silently replaced.

The corrected formal replay completed in about 100 seconds and rejected the candidate. It issued
231 out-of-fold predictions across 111 events. Observation Brier was `0.202002`, event-macro Brier
was `0.207234`, early/late event-macro Brier was `0.194038`/`0.220194`, mean prediction/outcome was
`0.473069`/`0.424242`, and the largest-event squared-error share was `0.054132`. Thus breadth,
early-half, calibration, and concentration checks passed, but observation, event-macro, and
late-half ceilings failed. Exact receipt SHA-256 is
`2e59fc3be4a6b9157b184cadfcc06eccf946c2131d3f1b12f8fdf44b97f0f7e8`.

Status: **FORMAL DEVELOPMENT REJECTION**. No independent freeze was issued, the protected plan was
not requested, and `protected_values_exposed=false`. The complete density comparison and unchanged
successor replay remain positive development evidence; this narrower scalar arrival compression
is retained as a negative result and cannot be repaired by moving its thresholds.
