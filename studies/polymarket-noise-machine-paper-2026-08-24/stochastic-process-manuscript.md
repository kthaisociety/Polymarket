# How Polymarket Probabilities Move

## A stochastic-process study of stasis, bursts, reversal, and variance growth

Chronos Research Project | 24 August 2026

### Abstract

Polymarket probability histories do not resemble a smooth diffusion. They spend much of their time unchanged, movement arrives in short active periods, consecutive nonzero changes reverse sign more often than an independent-sign model predicts, and variance grows much more slowly than elapsed time. These properties recur across chronological cohorts and remain visible in a separate five-minute sample.

The main corpus contains 803,862 hourly probability records from 562 contracts grouped into 157 events. A record is one stored probability for one contract at one observation time. It is not necessarily a transaction. The source also does not identify whether the stored value is a last observation, a midpoint, or another public history mark. The object studied here is therefore the recorded probability process itself.

Four event-level tests summarize the process on later data. The mean exact-zero share was 43.81%. Among consecutive nonzero changes, the mean sign-reversal share was 58.45%. After at least 24 unchanged hourly samples, the move rate was only 7.36% of the move rate following an active sample. The variance of a 24-hour change was 32.40% of the value implied by independent one-hour changes with constant variance. All four results remained on their prespecified side of the comparison value after correction for the four tests.

A three-part jump model gives the best compact description. It separately models whether the next change is zero, the sign of a nonzero change, and its absolute size. Current probability and time to close improve the model. Recent path information improves it further: quiet duration predicts whether movement occurs, the previous nonzero sign predicts reversal, and the previous nonzero magnitude predicts size. On 17,671 predictions from 27 eligible later events, the full state-and-path model obtained an event-average negative log likelihood of 2.870, compared with 3.116 for a state-only jump model and 4.582 for a bounded Gaussian diffusion. Lower values are better.

The evidence supports a bounded, discrete-time process with a point mass at zero, time-varying movement probability, negative dependence between successive nonzero signs, and substantial variation across events. It does not identify a unique continuous-time mechanism beneath the stored samples. That distinction is central: the paper describes the statistical law of the observed history, not an unobserved process between timestamps.

## 1. The process being studied

For one contract, let p(t) be the recorded YES probability at observation time t. The regular one-hour change is

Delta p(t+1) = p(t+1) - p(t).

The contracts are bounded because p(t) lies between 0 and 1. They also terminate at a recorded close time. Those two facts already separate the series from an unconstrained random walk. Movement can shrink near 0 and 1, and its distribution can change as the closing time approaches.

The harder question concerns dependence. A simple diffusion treats every short change as a draw from a continuous distribution whose variance may depend on state. A jump description allows an exact zero and then models the sign and size of a nonzero change. A path-dependent jump description goes further: the next distribution can depend on how long the contract has been unchanged and on the previous nonzero movement.

This paper tests which of those descriptions matches the recorded histories. It examines four parts of the process: the probability of no movement, the timing of movement after quiet or active periods, the sign sequence of nonzero changes, and the rate at which variance accumulates over longer horizons.

## 2. Data and evaluation

### 2.1 What one observation means

The main corpus contains 803,862 values of p(t), drawn from 562 contract histories in 157 events. One event may contain several related contracts. Their histories are not independent because they can respond to the same information and may share an outcome structure.

The original history source does not state exactly how each stored probability was formed. For that reason, terms such as change, zero, jump, and reversal refer only to differences between stored samples. A jump in this paper means a nonzero recorded change. It does not prove that an unobserved value changed discontinuously between the two timestamps.

Table 1. Evidence sets used in the analysis.

| Evidence set | Contents | Role in the paper |
|---|---|---|
| Main cohort | 803,862 hourly probability records, 562 contracts, 157 events | Process estimates, model fitting, and chronological evaluation |
| Later cohort | 29 later events; 27 eligible for the frozen one-hour models | No-refit comparison of the selected process models |
| Five-minute panel | 19,258 official probability-history records from 10 contracts chosen before their values were inspected | Check whether hourly sampling alone explains the patterns |
| Fresh reversal cohort | 6,174 non-overlapping shock cases, 410 contracts, 128 test events | Test sign dependence on a different set of events |
| Protected arrival run | 100 declared cases, of which 65 could be scored under the frozen rules | Measure coverage of one frozen arrival model |

### 2.2 Time order and event grouping

Every model uses information recorded before its target. Training uses earlier whole events and evaluation uses later event blocks. Within training, each event receives the same total weight. A large event therefore cannot dominate the fitted coefficients merely because it contains more contracts or more rows.

Scores are averaged in two ways. An observation average gives every prediction equal weight. An event average first computes a score within each event and then gives every event equal weight. The event average is primary because transfer across events is harder than repeated prediction within a large event.

Uncertainty is also calculated at the event level. Confidence intervals resample whole events. Four fixed process signatures form one test family and use Holm's correction. Two retained predictive comparisons are penalized across all 37 recorded stochastic analyses with a Bonferroni correction. The full research audit contains 90 governed executions representing 48 distinct analysis identities, including failed attempts and reruns.

### 2.3 Scores

For a binary target, such as whether the next change is zero, the paper uses the Brier score [1]:

Brier = mean[(q - y)^2],

where q is the predicted probability and y is either 0 or 1. A perfect forecast scores 0. Lower values are better.

For the complete distribution of the next change, the paper uses negative log likelihood. The predicted distribution assigns probability to the interval containing the observed change. The loss is minus the logarithm of that probability. A lower value means that the model assigned more probability to what occurred.

## 3. Four properties of the recorded process

### 3.1 Exact zeros

Zero mass is the fraction of regular one-hour changes equal to exactly zero. A continuous Gaussian distribution assigns probability zero to one exact value, so it cannot represent a large observed point mass at zero without an additional sampling or recording mechanism.

On the later cohort, the event-average exact-zero share was 43.81%, with a 95% whole-event interval from 38.71% to 49.52%. Twenty-five of 26 eligible events were above the fixed 20% comparison. The Holm-adjusted p-value was 0.00000161.

The zero share is not constant across cohorts or contracts. Its persistence is the main result. A model of these histories needs a separate probability for no recorded movement.

### 3.2 Quiet periods persist

The quiet ratio compares two conditional move rates. The numerator is the chance of a change after at least 24 consecutive unchanged hourly samples. The denominator is the chance of a change when the immediately preceding sample changed.

The later event mean was 7.36%, with a 95% interval from 5.23% to 9.65%. In plain terms, the move rate after a long quiet run was about 7% of the move rate after activity. All seven events with enough observations were below the fixed 50% comparison; the adjusted p-value was 0.00781.

This is duration dependence. The longer quiet state is not equivalent to a fresh zero. A contract that has remained unchanged for a day is much more likely to remain unchanged than a contract that just moved.

### 3.3 Nonzero signs tend to reverse

The sign-reversal share is computed only when two nonzero changes occur in sequence. It is the fraction for which their signs differ. Under independent balanced signs, the comparison value is 50%.

The later event mean was 58.45%, with a 95% interval from 55.53% to 61.41%. Twenty-one of 26 events were above 50%, and the adjusted p-value was 0.00249. The result implies negative first-order dependence in the sign sequence: after an upward nonzero change, the next nonzero change is more likely to be downward, and conversely.

The fresh reversal cohort tests a related but stricter path event. It selects a change of at least two probability points, waits one recorded sample, and records whether a two-point reversal or a two-point continuation occurs first during the next 24 hours. Across 6,174 cases from 410 contracts and 128 events, a six-variable state-and-shock model reduced event-average Brier from 0.2522 to 0.2390. The improvement interval was 0.0051 to 0.0214, the model won in 87 of 128 events, and its search-adjusted p-value was 0.00109.

### 3.4 Variance grows slower than clock time

The 24-hour variance ratio is

VR(24) = Var[p(t+24) - p(t)] / {24 Var[p(t+1) - p(t)]}.

Independent one-hour changes with constant variance give a ratio near 1. The later event mean was 0.3240, with a 95% interval from 0.2497 to 0.4043. Twenty-four of 26 events were below the fixed 0.75 comparison; the adjusted p-value was 0.0000157.

A ratio below 1 means that variance accumulates more slowly than it would under independent increments. Sign reversal is one reason. Adjacent changes of opposite sign cancel when they are aggregated over a longer interval. Long zero runs also make clock time a poor measure of how much process activity has occurred.

[[FIGURE:process_signatures.png]]

Figure 1. Event-average process estimates on the later cohort. Horizontal lines show 95% whole-event bootstrap intervals. Each vertical marker is the fixed comparison value for that test.

Table 2. Numerical values for the four later-cohort process tests.

| Measure | Later event mean | 95% interval | Fixed comparison | Events on predicted side | Holm-adjusted p |
|---|---:|---:|---:|---:|---:|
| Exact-zero share | 43.81% | 38.71% to 49.52% | Above 20% | 25 of 26 | 0.00000161 |
| Sign-reversal share | 58.45% | 55.53% to 61.41% | Above 50% | 21 of 26 | 0.00249 |
| Long-quiet / active move-rate ratio | 7.36% | 5.23% to 9.65% | Below 50% | 7 of 7 | 0.00781 |
| 24-hour variance ratio | 32.40% | 24.97% to 40.43% | Below 75% | 24 of 26 | 0.0000157 |

### 3.5 The five-minute check

Hourly sampling could create misleading dependence if several changes occur inside each hour. The five-minute panel checks that explanation on ten contracts selected before their values were inspected. It contains 19,012 regular five-minute increments. Of those increments, 78.00% were zero, the nonzero sign-reversal share was 67.87%, and the 24-hour variance ratio was 0.067.

The panel is too small for a venue-wide estimate. It does show that the three main shapes are not removed by moving from hourly to five-minute observations. At that finer interval, stasis and reversal are stronger, not weaker.

## 4. A conditional jump model

### 4.1 Separating arrival, sign, and magnitude

The full model describes the next one-hour change in three parts. The arrival part predicts whether the change is zero. Conditional on a nonzero change, the sign part predicts whether it is positive. The magnitude part predicts the logarithm of its absolute size. Multiplying these three conditional pieces gives a probability distribution for the next recorded change.

This division is related to point-process descriptions of market activity [2,3], but the fitted model is discrete in time. It does not reconstruct events between samples. It answers a narrower question: given the recorded state and path at time t, what distribution should be assigned to Delta p(t+1)?

The raw nonzero sizes appear heavy-tailed when mixed with many exact zeros and periods of different activity. After separating zero arrival and predicting log absolute size, Gaussian residuals beat Laplace and Student-t residuals in the fixed comparison. A heavy-tailed marginal distribution does not require a heavy-tailed residual distribution once state and activity have been conditioned on.

### 4.2 Variables used by the model

Table 3. Variables used by the conditional jump model.

| Variable | Exact definition | Part of the process it describes |
|---|---|---|
| Probability level | Recorded p(t) before the target change | Current position within the bounded interval |
| Boundary distance | min[p(t), 1 - p(t)] | Distance from the nearest terminal boundary |
| Clipped log odds | log[p/(1-p)] after clipping p to 0.005 through 0.995 | State on an unbounded scale without infinite values |
| Time to close | Hours from the current observation to the recorded close time | Change in process behavior over a contract's life |
| Quiet run | Number of consecutive regular one-hour changes equal to zero | Duration of the present inactive state |
| Prior-24 zero fraction | Share of the preceding 24 regular changes equal to zero | Recent local activity level |
| Previous nonzero sign | +1 for the last upward change and -1 for the last downward change | First-order sign dependence |
| Previous nonzero magnitude | Absolute size of the last nonzero change | Dependence in move size |

No variable uses a later probability or the final resolved outcome. Variables reset after an irregular time gap. Standardization uses training events only.

### 4.3 Four model descriptions

The bounded Gaussian diffusion is the simplest benchmark. Its change has mean zero. Its variance depends on probability level and time to close, and it is scaled by p(t)[1-p(t)] so that movement shrinks near 0 and 1. It has no separate exact-zero component.

The memoryless jump model adds a probability of no change and conditional distributions for nonzero sign and size. It estimates those distributions from earlier events but ignores the current state and recent path.

The state jump model lets arrival, sign, and magnitude depend on the current probability and time to close. It therefore allows different behavior near the boundaries and at different stages of a contract's life.

The state-and-path jump model adds quiet duration to the arrival part, the previous nonzero sign to the sign part, and the previous nonzero magnitude to the magnitude part. The comparison with the state model isolates the contribution of recent path information.

## 5. Comparison on later events

### 5.1 The complete next-change distribution

The development evaluation produced 566,501 chronological predictions across 113 later development events. After model selection, the four descriptions ran without refitting on 17,671 predictions from 27 eligible events in a later cohort.

Table 4. Negative log likelihood for the four process descriptions.

| Model | Development event NLL | Later event NLL | Statistical content |
|---|---:|---:|---|
| Bounded Gaussian diffusion | 3.578 | 4.582 | Smooth state-dependent change with no exact-zero mass |
| Memoryless jump model | 2.214 | 3.240 | Exact zeros and nonzero changes, without state or path |
| State jump model | 2.104 | 3.116 | Current probability and time to close |
| State-and-path jump model | 1.941 | 2.870 | Current state, quiet duration, previous sign, and previous magnitude |

The state-and-path model lowered later event NLL by 7.88% relative to the state model and won all 27 event comparisons. Every model scored worse in absolute terms on the later cohort than during development. The later events were therefore harder under every description, but the model ordering did not change.

[[FIGURE:model_scores.png]]

Figure 2. Later-cohort model scores. Lower is better in both panels. The left panel evaluates the full distribution of the next change. The right panel evaluates only whether the next stored probability changes.

### 5.2 The arrival component

The arrival component predicts whether the next regular hourly probability differs from the current value. A state-only logistic model uses probability level, boundary distance, and clipped log odds. The quiet-history model adds log(1 + quiet run) and the prior-24 zero fraction.

On the later cohort, the state-only model had an event-average Brier score of 0.2611. Adding quiet history reduced the score to 0.1739, a relative reduction of 33.38%. The quiet-history model won in all 27 events. The whole-event bootstrap interval for the absolute reduction was 0.0716 to 0.1035. After a Bonferroni correction across 37 stochastic analyses, the event-win p-value was 0.000000276.

This was the largest and most stable component improvement. Much of the predictability in the complete process comes from the timing of recorded movement rather than the conditional sign or size of a move.

### 5.3 Coverage of the frozen arrival model

One frozen arrival system was also tested on 100 declared cases. It produced scores for 65. On those 65 cases, Brier was 0.189, below its fixed ceiling of 0.200. The coverage requirement, however, was 95%; observed coverage was 65%. The missing cases cannot be discarded after inspection because availability may depend on contract history.

This result concerns the fitted system's range of application. It does not reverse the event-level arrival results, but it prevents a claim that the frozen implementation describes every declared case under its own data requirements.

## 6. What class of process fits the evidence

The recorded histories can be summarized as a bounded, state-dependent jump process observed on a fixed clock. Its one-step distribution has a point mass at zero. A continuous density alone cannot reproduce the frequency of unchanged samples.

The probability of movement varies over time. It depends on the current probability, time to close, and recent activity. The strong quiet-run effect means the movement probability also depends on how long the process has occupied its current value.

The sign sequence has short negative dependence. Consecutive nonzero changes reverse more often than independent balanced signs would imply. This sign behavior contributes to the low variance ratio at longer horizons.

Move size is not identically distributed. It depends on state and on the previous nonzero magnitude. After those variables are included, a Gaussian model for log absolute size is adequate relative to the tested heavy-tailed alternatives.

The parameters also vary across events. Later events were harder to predict, the zero share changed between cohorts, and the quiet-ratio estimate was available for only seven later events. The model family transferred better than any single universal set of rates.

These findings rule out several simple descriptions of the stored series. It is not well represented by independent Gaussian increments, by a constant-rate sequence of jumps, or by a state-only process that forgets recent movement. They do not select one unique continuous-time mechanism. Rounding, intermittent updating, source construction, and unobserved within-interval changes can produce similar sampled histories. Distinguishing those mechanisms requires more frequent observations together with a precise definition of how each stored probability is formed.

## 7. Limits and next measurements

The main corpus is an hourly panel of retained probability histories. It does not reveal the path between samples, and its source field is not defined precisely enough to separate last-observation effects from other recording rules. The five-minute panel reduces the sampling interval but contains only ten contracts.

The later cohort was unused when the earlier process model was fitted, but it was subsequently used for several analyses. It is therefore a later-data replication set, not a reusable untouched holdout. Event grouping handles the clearest dependence among related contracts, but unknown links between events can remain.

The Gaussian diffusion benchmark is deliberately simple. Rejecting it does not reject every latent continuous process observed with discreteness, rounding, or intermittent updates. The results establish properties of the recorded process: point mass at zero, duration dependence, sign reversal, slow variance growth, and state dependence.

The next measurements should separate these properties more sharply. A longer multi-scale panel would show how zero mass, reversal, and variance ratios change from minutes to days. Contract categories should be compared under fixed definitions to measure heterogeneity. Finally, aligning probability histories with named event times would separate ordinary activity from the response to scheduled information. Each extension concerns the probability process itself and can be evaluated with the same whole-event chronology.

### 7.1 Conclusion

Polymarket probability histories spend long periods at exactly the same recorded value, then move in clustered episodes. Nonzero changes reverse sign more often than an independent-sign model predicts, so variance accumulates slowly over longer intervals. Current state matters, but recent path matters as well.

The best tested description is a three-part jump model: a probability of no change, followed by conditional laws for sign and magnitude when movement occurs. Quiet duration provides the largest improvement. Previous sign and previous magnitude add smaller but repeatable information. The model transfers to later events even though the later cohort is harder in absolute terms.

No single label captures the process completely. It is bounded, zero-heavy, path-dependent, and heterogeneous across events. Those are empirical properties of the recorded histories. Identifying the continuous-time mechanism beneath them remains an open measurement problem.

### References

[1] Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. Monthly Weather Review, 78(1), 1-3.

[2] Hawkes, A. G. (1971). Spectra of some self-exciting and mutually exciting point processes. Biometrika, 58(1), 83-90.

[3] Bacry, E., Delattre, S., Hoffmann, M., and Muzy, J. F. (2013). Modelling microstructure noise with mutually exciting point processes. Quantitative Finance, 13(1), 65-77.

[4] Chronos Research Project (2026). Polymarket paper acceptance audit. Audit identity: paper-audit-report:e8ed21a7f08e0e35c8277138515f0cad1cf0d84f0fe6fca438aa380f0fa2d910.
