# The Noise Machine

## Statistical structure without a validated trading strategy in Polymarket probability histories

Chronos Research Project | 24 August 2026

### Abstract

Polymarket contract histories contain repeatable statistical patterns. Recorded probabilities often stay unchanged for many samples, large moves arrive in bursts, and a nonzero move is more likely than chance to be followed by a move in the opposite direction. Models that use these facts predict the next recorded value better than simpler models on later events. None of this produced a validated trading strategy.

The main dataset contains 803,862 recorded hourly probabilities from 562 contracts grouped into 157 events. An hourly record is one probability stored for one contract at one scheduled observation time. It is not 803,862 trades, nor does it provide the bid, ask, order-book depth, or a price at which an order could have been filled. We therefore study the recorded probability process first and keep trading claims separate.

We compare four descriptions of the next one-hour change. A bounded Gaussian diffusion assumes a continuous change with no special probability of an exact zero. A memoryless jump model allows exact zeros and nonzero moves but ignores the current contract state. A state model uses the current probability and time to resolution. The full model also uses the length of the current quiet run, the sign of the previous nonzero move, and the size of that move. On 17,671 predictions from a later cohort, the full model obtained an event-average negative log score of 2.870, compared with 3.116 for the state model and 4.582 for the diffusion. Lower is better. The full model beat the state model in all 27 eligible events.

The result is useful but narrow. It describes when the stored probability changes and how those changes are distributed. It does not show that the same pattern survives spreads, latency, queue position, partial fills, or market impact. The practical conclusion is selective: broad searches over Polymarket's own price history should stop. Future work should start with contracts that can be matched to a faster outside data source and should test that information against historical quotes or prospective paper fills.

### 1. The question

A prediction contract pays either 0 or 1 after resolution. This gives the price a clear endpoint, but it does not make every recorded price an objective probability or an executable quote [3,4]. A market price can reflect information, risk preferences, inventory, stale orders, and the way the platform records its public history. Our question is therefore concrete: what can be predicted from the recorded probability series, and how much of that prediction remains useful when the test is made on later events?

The answer has two parts. First, the series has structure. Exact zero changes, reversal, quiet periods, and slow variance growth recur across events and chronological cohorts. Second, the structure mostly predicts the observation process itself. A good forecast that the next stored probability will remain unchanged does not say which side to buy. A good forecast of reversal in sampled values is still not a trade if the bid and ask are missing. We call this gap between statistical predictability and demonstrated trading value the noise machine.

<!-- PAGE BREAK -->

## 2. What the data contain

### 2.1 A probability record is not a trade

For one contract, write p(t) for the recorded YES probability at observation time t. A regular one-hour change is

Delta p(t+1) = p(t+1) - p(t).

The main corpus contains 803,862 values of p(t), drawn from 562 contract histories in 157 events. The term observation means one stored probability value. It does not mean that a trade occurred during that hour. The original source does not identify whether the value was a last trade, a midpoint, or another public history mark. This distinction controls every claim in the paper.

Related contracts can belong to the same event. Their errors are correlated because they respond to the same news and may share an outcome structure. Counting each row or contract as an independent experiment would make uncertainty look smaller than it is. We therefore use the event as the main unit for train-test separation and uncertainty.

| Evidence set | Contents | Use in the paper |
|---|---|---|
| Main development cohort | 803,862 hourly probability records, 562 contracts, 157 events | Feature construction, model fitting, and chronological tests |
| Later cohort | 29 later events; 27 eligible for the frozen one-hour models | No-refit test of the selected model family |
| Five-minute panel | 19,258 official central limit order book (CLOB) history records from 10 contracts chosen before values were inspected | Check whether hourly sampling alone creates the patterns |
| Fresh reversal cohort | 6,174 non-overlapping shock cases, 410 contracts, 128 test events | Test a directional path label on different events |
| Protected arrival run | 100 declared decisions, of which 65 could be scored | Final test of one frozen arrival system; rejected for low coverage |

### 2.2 Chronological evaluation

Every prediction uses information that was available before its target. Models train on earlier whole events and predict later event blocks. Within each training fold, every event receives the same total weight. A large event with many contracts therefore cannot dominate the fitted model merely because it supplies more rows.

We report two kinds of averages. An observation average gives every prediction equal weight. An event average first computes the score within each event and then averages the event scores, giving a small event the same weight as a large event. The event average is the main result because the research question concerns transfer across events.

For binary targets we use the Brier score [1], the mean squared difference between a predicted probability q and the observed outcome y:

Brier = mean[(q - y)^2].

A perfect forecast scores 0. Lower values are better. For a full probability law we use negative log likelihood. The model assigns probability to the interval containing the observed change, and the loss is minus the logarithm of that probability. Lower values are better. If one model assigns twice as much probability to what occurred, its loss for that observation is lower by log(2).

### 2.3 Uncertainty and repeated testing

Confidence intervals resample whole events, not individual rows. The paper uses 10,000 deterministic event bootstrap draws for the retained predictive comparisons. Four fixed process signatures form one test family and use Holm's correction. Two selected predictive tests are penalized across all 37 recorded stochastic analyses with a Bonferroni correction. Failed trials and reruns remain in the inventory. The audit covers 90 governed executions representing 48 distinct analysis identities.

This procedure does not turn development data into an untouched holdout. It does make the reported uncertainty and test count match the way the research was conducted.

<!-- PAGE BREAK -->

## 3. How the recorded probabilities move

### 3.1 Four features of the process

Zero mass is the fraction of regular one-hour changes that equal exactly zero. A continuous Gaussian model assigns zero probability to an exact zero, so a large zero mass is direct evidence against that description of the stored series.

In this paper, a jump means a nonzero change between two stored samples. It does not prove that an unobserved market value changed discontinuously between those samples.

The sign-reversal rate is computed only when two nonzero changes occur in sequence. It is the fraction for which the signs differ. A value above 50% means an up move is followed by a down move, or a down move by an up move, more often than under independent balanced signs.

The quiet ratio compares two move rates. The numerator is the chance that the next sample changes after at least 24 consecutive unchanged samples. The denominator is the chance of a change when the immediately preceding sample changed. A ratio below 1 means that a quiet contract tends to remain quiet. A value of 0.074 means that the long-quiet move rate is 7.4% of the active move rate.

The 24-hour variance ratio compares the variance of a 24-hour change with 24 times the variance of a one-hour change:

VR(24) = Var[p(t+24) - p(t)] / {24 Var[p(t+1) - p(t)]}.

Independent one-hour changes with constant variance give a ratio near 1. A ratio below 1 means that variance grows more slowly than clock time. Reversal is one mechanism that can produce this result because adjacent moves cancel.

[[FIGURE:process_signatures.png]]

Figure 1. Event-average estimates on the later cohort. Horizontal lines show 95% whole-event bootstrap intervals. The vertical marker is the fixed comparison value for each test.

| Measure | Later event mean | 95% interval | Fixed comparison | Events on predicted side | Holm-adjusted p |
|---|---:|---:|---:|---:|---:|
| Exact-zero share | 43.81% | 38.71% to 49.52% | Above 20% | 25 of 26 | 0.00000161 |
| Sign-reversal share | 58.45% | 55.53% to 61.41% | Above 50% | 21 of 26 | 0.00249 |
| Long-quiet / active move-rate ratio | 7.36% | 5.23% to 9.65% | Below 50% | 7 of 7 | 0.00781 |
| 24-hour variance ratio | 32.40% | 24.97% to 40.43% | Below 75% | 24 of 26 | 0.0000157 |

### 3.2 What these numbers mean

The stored series alternates between long periods with no recorded change and short periods with movement. Once movement occurs, the next nonzero move often points in the opposite direction. Over a day, these reversals make total variance grow much less than it would under independent one-hour changes.

The exact levels are not universal. The zero rate differed between the main and later cohorts, and only seven later events had enough long-quiet and active observations for the quiet-ratio test. The repeated result is the direction of the effects, not a single parameter that applies to every contract.

The five-minute panel addresses a simple rival explanation: perhaps the hourly clock creates zeros and reversals by skipping changes inside the hour. It does not. Across 19,012 regular five-minute increments, 78.00% were zero, the nonzero reversal rate was 67.87%, and the 24-hour variance ratio was 0.067. This panel contains only ten preselected contracts, so it is a measurement check rather than venue-wide evidence.

<!-- PAGE BREAK -->

## 4. Models, features, and benchmarks

### 4.1 The prediction target

The full process model predicts the next regular one-hour change in the stored probability. It has three parts. The arrival part predicts whether the change is zero. If the change is nonzero, the sign part predicts whether it is positive. The magnitude part predicts the logarithm of the absolute change. Combining the three parts gives a probability distribution for the next recorded change.

Separating the time of a move from its sign and size follows the basic division used in point-process models of market activity [2,5]. Here the division is used to make a one-hour forecast; it does not imply that the stored series reveals every market event between samples.

This split matters. The raw one-hour changes have very large tails, but much of that appearance comes from mixing many exact zeros with occasional moves of different sizes. After the model separates zero arrival and predicts the logarithm of nonzero size, a Gaussian residual beat Laplace and Student-t residuals in the fixed comparison. “Heavy tails” describes the raw changes; it was not the best residual law after the split.

### 4.2 Feature definitions

| Feature | Exact meaning | Why it is included |
|---|---|---|
| Probability level | The recorded p(t) before the target change | Movement can differ near 0, near 1, and in the interior |
| Boundary distance | min[p(t), 1 - p(t)] | Measures how close the contract is to either terminal boundary |
| Clipped log odds | log[p/(1-p)] after clipping p to 0.005 through 0.995 | Represents the same state on an unbounded scale without infinite values |
| Time to close | Hours from the current observation to the recorded contract close time | Separates early-life movement from movement near resolution |
| Quiet run | Number of consecutive regular one-hour changes equal to zero | Measures how long the recorded series has been unchanged |
| Prior-24 zero fraction | Share of the preceding 24 regular changes equal to zero | Measures recent inactivity without relying only on the current run |
| Previous nonzero sign | +1 for the last upward nonzero change and -1 for the last downward change | Tests whether the next nonzero sign tends to reverse |
| Previous nonzero magnitude | Absolute size of the last nonzero change | Tests whether large moves tend to be followed by large moves |

No feature uses the future resolution or a later probability. Features reset after an irregular time gap. Each fitted value is standardized using the training events only.

### 4.3 What each benchmark means

The diffusion benchmark assumes a zero mean Gaussian change. Its variance depends on the current probability and time to close, and it is multiplied by p(t)[1-p(t)] so that variation shrinks near 0 and 1. It has no exact-zero component. Beating it shows that the recorded series needs more than bounded, state-dependent Gaussian variance.

The memoryless jump benchmark has a separate probability for no change and a distribution for nonzero sign and size. These probabilities are estimated from earlier events but ignore the current contract state and recent path. Beating it shows that zeros and jumps alone are insufficient.

The state benchmark lets the arrival, sign, and size distributions depend on the current probability and time to close. It still ignores how long the series has been quiet and what happened in the previous nonzero move. Beating it is the hardest relevant comparison because it already knows that boundary and maturity matter.

The full model adds quiet duration to the arrival part, the previous nonzero sign to the sign part, and the previous nonzero magnitude to the size part. The comparison isolates whether recent path information improves prediction beyond current state.

The component benchmarks follow the same rule. For next-hour arrival, the state-only logistic model uses probability level, boundary distance, and clipped log odds. The quiet-history model adds log(1 + quiet run) and the prior-24 zero fraction. For reversal after a shock, the rate benchmark is the reversal frequency in earlier events. The six-feature state-and-shock model adds delayed entry probability, boundary distance, clipped log odds, shock direction, absolute shock size, and the probability movement between the shock sample and the next sample.

<!-- PAGE BREAK -->

## 5. What beat the benchmarks

### 5.1 The complete distribution of the next change

The development test produced 566,501 chronological predictions across 113 later development events. The selected full model then ran without refitting on 17,671 predictions from 27 eligible events in a later cohort.

| Model | Development event NLL | Later event NLL | Meaning of the comparison |
|---|---:|---:|---|
| Bounded Gaussian diffusion | 3.578 | 4.582 | Smooth state-dependent change, no exact-zero mass |
| Memoryless jump model | 2.214 | 3.240 | Allows zero and nonzero moves, ignores state and path |
| State jump model | 2.104 | 3.116 | Uses current probability and time to close |
| State + path jump model | 1.941 | 2.870 | Adds quiet run, previous sign, and previous magnitude |

The full model lowered later event NLL by 7.88% relative to the state model and won all 27 event comparisons. Absolute NLL was worse in the later cohort for every model, which means the later events were harder to predict. The ordering survived even though the score level changed. This supports the model structure, not one permanent set of parameter values.

[[FIGURE:model_scores.png]]

Figure 2. Later-cohort benchmark scores. Lower is better in both panels. The left panel scores the full distribution of the next change. The right panel scores only whether the next stored probability changes.

### 5.2 Predicting whether the next stored value changes

The frozen arrival model makes a binary forecast: will the next regular hourly probability differ from the current value? The state-only benchmark scored 0.2611 by event-average Brier. Adding quiet run and recent inactivity lowered the score to 0.1739, a 33.38% improvement. The full model won in all 27 events. The whole-event bootstrap interval for the absolute Brier improvement was 0.0716 to 0.1035. After a Bonferroni penalty across 37 recorded stochastic analyses, the event-win test had p = 0.000000276.

The model predicts update timing, not direction. A forecast that the next value will remain unchanged cannot by itself choose YES or NO. This was the strongest and most stable component in the research, but it sits one step before a trading decision.

### 5.3 Predicting reversal after a two-cent shock

A separate fresh-event study selected non-overlapping changes of at least two probability points, waited one recorded sample, and asked which threshold was reached first during the following 24 hours: a two-point move back against the shock or a two-point continuation. The delay prevents the model from entering at the same sampled value that defined the shock.

The test contained 6,174 shock cases from 410 contracts and 128 events. The benchmark predicted the event-equal reversal rate estimated from earlier events. A six-feature model based on the delayed entry state and shock details reduced event-average Brier from 0.2522 to 0.2390 and beat the benchmark in 87 of 128 events. The event-average Brier improvement was 0.0132, with a whole-event bootstrap interval from 0.0051 to 0.0214. Its search-adjusted p-value was 0.00109.

This result is directional, but the state-only sampled-price cost screen failed its fixed breadth rule. A larger 12-feature model passed a one-cent sampled-value screen, but that screen substituted a fixed cost for observed spreads and fills. The evidence supports a reversal label forecast. It does not support an executable return estimate.

<!-- PAGE BREAK -->

## 6. Why prediction did not become a strategy

### 6.1 Missing execution data

A stored probability does not show the bid and ask available when a decision was made. Without those quotes, a backtest cannot know whether the model could buy at the stored value, whether enough size was available, or whether the opportunity disappeared before an order reached the book. A complete trading evaluation needs the quote at decision time, subsequent book changes, fees, measured order latency, queue position, partial fills, and the price used to close or settle the position.

The difference is practical. Suppose a sampled value moves from 0.40 to 0.38 and then returns to 0.40. A sampled-price reversal appears to earn two cents. If the available ask was 0.40 and the later bid was 0.38, crossing the spread loses two cents. The same three recorded values can describe either a profitable opportunity or an untradeable bounce. The current hourly corpus cannot distinguish them.

### 6.2 The protected arrival test failed

The continuous arrival model passed development thresholds and was frozen before its protected run. On the 65 decisions it could score, Brier was 0.189, below the fixed ceiling of 0.200. But only 65 of 100 declared decisions were executable under the frozen data and training rules. Required coverage was 95%; observed coverage was 65%. The failure rate was 35% against a maximum of 5%, and one concentration check also failed. Dropping the missing decisions after seeing the protected data would change the system. The protected result was therefore rejected.

This negative result is part of the model, not an administrative detail. A prediction system that works only when enough history happens to be available may fail on a non-random subset of contracts. Coverage must be tested along with prediction error.

### 6.3 Why “noise machine” does not mean pure randomness

The recorded series is not independent noise. Its next change depends on recent quiet, current state, the previous sign, and the previous magnitude. The term noise machine describes the economic problem: much of the predictable structure concerns when the public record changes and how sampled changes bounce. That structure can be statistically stable while remaining too far from an executable price to support a trade.

Behavioral and wallet-based hypotheses did not alter this conclusion. Fixed tests of skilled-wallet matching, expert consensus, crowding, and several related ideas were negative. A 2% to 10% longshot fade remained a development lead, but the rule was selected on exposed data and has not been tested once on a new untouched cohort. We therefore keep it outside the main process result.

The paper does not claim that every Polymarket contract is untradeable or that outside information has no value. It shows that a broad search over the platform's own stored probability histories did not establish profit after the tests required for a trading claim.

<!-- PAGE BREAK -->

## 7. A narrower research program

The next program should begin with contract selection rather than model selection. A contract qualifies only when its resolution rule can be mapped to an outside measurement without judgment. Examples of the required form are a dated official release, a count published by a named authority, or a result feed with a stable timestamp. A vague news indicator or a model score with no direct link to the resolution rule does not qualify.

The outside source must also have a clock that can be compared with the market clock. We need the source's publication time, the time the data reached our collector, the exchange timestamp on each quote or book update, and the local receipt time. These clocks answer the central low-latency question: did the outside fact arrive before the executable market moved, and by enough time to place an order?

Each proposed strategy should then face the same sequence. First, freeze the contract mapping and the signal before inspecting the response window. Second, measure the lead between the outside source and the best bid and ask, not a later sampled probability. Third, replay orders with the observed depth, fees, latency, queue assumptions, and partial fills. Fourth, average performance by event and test it on later events. Fifth, run one untouched evaluation after the entire rule and execution model are fixed.

This approach will reject most contracts before a predictive model is fitted. That is the point. A small set of contracts with an exact outside state and a measurable information lead offers a clearer route to value than another search through thousands of transformations of Polymarket's own past prices.

### 7.1 Limits of the current evidence

The study covers retained historical probability paths, one ten-contract five-minute panel, and one rejected protected arrival system. It does not observe historical book state for the main corpus. The later cohort was unused when the earlier model was fitted, but it supported several later analyses and is not a reusable protected holdout. Event grouping handles the strongest known dependence but cannot remove all dependence among related outcomes. The simple diffusion benchmark is intentionally basic; rejecting it does not reject every possible continuous latent-price model with noisy sampling.

### 7.2 Conclusion

Polymarket probability histories have repeatable structure. Exact zeros, quiet-period persistence, reversal, and slow variance growth all survived event-level tests on later data. A model built around those features predicted the next recorded change better than state-only and Gaussian benchmarks. The strongest result predicted whether the stored value would change, while the most direct directional result predicted reversal after a sampled shock.

Neither result established a trading strategy. The main data lack executable quotes, and the one protected arrival system failed coverage. Research based only on the platform's own stored histories has reached its useful limit. The next test should be smaller and harder: select contracts with a precise outside data source, prove that the source leads the order book, and measure whether the lead survives actual execution costs.

### References

[1] Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. Monthly Weather Review, 78(1), 1-3.

[2] Hawkes, A. G. (1971). Spectra of some self-exciting and mutually exciting point processes. Biometrika, 58(1), 83-90.

[3] Manski, C. F. (2006). Interpreting the predictions of prediction markets. Economics Letters, 91(3), 425-429.

[4] Wolfers, J., and Zitzewitz, E. (2004). Prediction markets. Journal of Economic Perspectives, 18(2), 107-126.

[5] Bacry, E., Delattre, S., Hoffmann, M., and Muzy, J. F. (2013). Modelling microstructure noise with mutually exciting point processes. Quantitative Finance, 13(1), 65-77.

[6] Chronos Research Project (2026). Polymarket paper acceptance audit. Audit identity: paper-audit-report:e8ed21a7f08e0e35c8277138515f0cad1cf0d84f0fe6fca438aa380f0fa2d910.
