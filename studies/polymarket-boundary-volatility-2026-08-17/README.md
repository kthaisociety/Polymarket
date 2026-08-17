# Polymarket boundary, volatility, and alternative-data study

Epistemic status: **ACTIVE DEVELOPMENT RESEARCH — PROTECTED DATA UNEXPOSED**.

This study uses the exact retained corpus
`polymarket-corpus:610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f`
and its whole-event partition
`49d5e9a97985a44e3277f43ee55ce1281c430a1d0a1823754a9a759ac56d3bd1`.
Only the first 24 event groups/155 markets are available; the final seven event groups/45 markets
remain protected.

## Frozen opening hypotheses

1. A logit representation may make interior probability dynamics more homogeneous than raw-price
   changes. Logit diagnostics use only observations strictly between 0.005 and 0.995. Boundary
   observations are counted separately; they are never silently clipped into the logit sample.
2. Near-boundary values may behave as empirically absorbing states, or may instead be stale samples
   that frequently escape. Five fixed state bands are used: `[0, .02]`, `(.02, .10)`, `[.10, .90]`,
   `(.90, .98)`, and `[.98, 1]`.
3. Six- and 24-hour trailing realized variance may predict future absolute or squared movement.
   This is a volatility hypothesis, not directional evidence.
4. Any directional follow-up must beat the no-change probability baseline in one-event-ahead
   development folds, survive a one-observation execution delay, and satisfy the existing 0.01
   sampled-price cost/stability gate before formalization.
5. Alternative data is acquired only after a named development mechanism identifies one exact
   contract/question, source field, publication clock, join, and falsifier. Searching for many
   series and retaining only the best correlation is forbidden.

## Frozen model trial after diagnostic 01

Diagnostic 01 showed that logit dynamics remain negatively dependent and that trailing realized
variance has modest, heterogeneous association with future absolute movement. Before fitting, the
follow-up trial is fixed as follows:

- common population: hourly-regular decisions with 24 trailing observations, two future
  observations, and every logit input strictly inside `(0.005, 0.995)`;
- features: one-hour raw change, one-hour logit change, logit state, boundary distance, 6- and
  24-hour raw realized variance, 6-hour logit realized variance, raw-change × 6-hour-variance
  interaction, and `log(1 + hours-to-close)`;
- labels: next-hour raw change for direction, next-hour absolute raw change for magnitude, and the
  following one-hour raw change as the execution-delay falsifier;
- models: no-change martingale, fold-fitted one-feature raw OLS, fixed logit reversal, and one
  fold-standardized ridge linear model with fixed penalty 0.1; magnitude compares the earlier-event
  mean with the same fixed ridge recipe;
- folds: one event ahead after eight earlier development events, with equal total weight per
  training event;
- candidate gate: direction must improve both equal-event and observation-weighted MSE versus the
  martingale, win at least 60% of events, and pass the existing delayed two-sided plus delayed
  long-only 0.01-cost stability conditions. Magnitude improvement alone cannot pass a trading gate.

## Frozen magnitude ablation after model trial 02

The full ridge improved next-hour absolute-change forecasts but mixed volatility with state and
time-to-close. Trial 03 therefore compares the earlier-event mean with separate fold-fitted scalar
OLS models using `log(1 + hours-to-close)`, boundary distance, 6-hour raw realized variance,
24-hour raw realized variance, or 6-hour logit realized variance on the identical common sample.
A volatility feature is considered incrementally useful only if it beats both the mean baseline and
the time-to-close model under equal-event and observation weighting and wins at least 60% of test
events. This ablation is explanatory development evidence, not a trading gate.

## Frozen formal-harness trial after ablation 03

Trial 04 exercises the authored-candidate path on the development-set July 2026 Fed no-change
contract, selected for its direct economic link to the separately scouted CME FedWatch source—not
for its historical performance. The protected event block is physically omitted from the formal
catalog. Decisions are sampled every 24 retained observations only when the trailing 24 samples
span 18–30 hours. The label is the absolute probability move over the next elapsed 24 hours.

Both candidates author the same traceable `raw_realized_variance_24h` feature. Candidate A fits an
expanding historical-mean magnitude baseline. Candidate B fits an expanding one-feature OLS model
and clips forecasts to `[0, 1]`. At least 20 matured training examples and 20 out-of-fold predictions
are required. This is a formal chronological development backtest, not a directional strategy,
not a protected backtest, and not a promotion gate.

The first driver invocation failed before candidate publication because it requested the wrong
registered dataset identifier (`polymarket-prices` rather than
`polymarket-outcome-price-series`). It produced no evidence and consumed no scientific or
protected trial; the corrected invocation is retained in source.

The next invocation exposed a generic dimension-order defect before producing evidence: registered
observations preserve schema order while `SampleKey` canonicalizes named dimensions. The authored
evaluator compared the tuples positionally and therefore excluded valid Polymarket rows. The repair
compares canonicalized named dimensions in both development and protected replay; again, no
scientific or protected result was consumed by the failed invocation.

## Results

The logit transform did not cleanly recover a diffusion. Lag-one increment correlation was
`-0.212` in raw probability and `-0.226` in logit space. The 2/4/8/24-hour variance ratios remained
sublinear in both representations. Low-boundary observations were highly persistent (`98.5%`
remained in the low boundary band at the next sample), but the high-boundary sample contained only
seven transitions and cannot support a symmetric absorption claim.

Trailing realized variance predicted some future-move magnitude in pooled development diagnostics,
but not incremental magnitude beyond the simpler time-to-close feature. In the one-event-ahead
ablation, all three volatility variants beat the constant baseline in 15/16 events, while
time-to-close had better aggregate MSE than every volatility-only model.

The fully authored formal trial then tested 24-hour raw realized variance on the predeclared July
2026 Fed no-change contract. Chronos produced 84 out-of-fold predictions after 20 matured training
examples. The expanding mean baseline had MSE `0.00194354`; expanding one-feature OLS had MSE
`0.00357062`, worse by `0.00162708`. OLS won 50/84 individual squared-error comparisons, but larger
misses dominated. The candidate is therefore a **formal development rejection**. It is not frozen,
not promoted, and not eligible for protected evaluation.

The receipt retains both candidate IDs, exact source SHA-256 values, trial ancestry, evidence IDs,
metrics, and harness-observed accesses. Feature construction accessed only historical
`market_probability`; label construction accessed that legal history plus the future outcome path;
fit and prediction accessed only their phase-specific interfaces.

## Alternative-data scout

The exact economically matched external series for the selected Fed contract is CME FedWatch's
historical meeting probability distribution. CME documents a FedWatch REST API, but its official
[`FedWatch EOD via REST API` fee schedule](https://www.cmegroup.com/market-data/files/interface-connection-agreement-apis.pdf?redirect=/ica-api)
is credentialed and begins at $25/month per API ID. No credentials or purchasing authority were
available, so Chronos did not acquire or register it.

Public FRED [effective-rate](https://fred.stlouisfed.org/series/EFFR) and
[target-range](https://fred.stlouisfed.org/series/DFEDTARU) series describe realized policy/rates,
not the point-in-time probability distribution for the upcoming July meeting. They were rejected
as a weak semantic substitute, and current downloads were not treated as proof of
historical-vintage availability. The alternative-data branch is therefore **blocked on an exact
licensed source**, not silently replaced with a convenient proxy.

## Harness findings

The research exposed and repaired three narrow, domain-neutral seams:

- exploratory authored code can now use pure `log` and `exp` without gaining imports, attributes,
  filesystem, network, or side-effect authority;
- a registered series may legally be both predictor history and future outcome, and label code may
  use the instrumented decision-time history needed to define changes or returns;
- named population dimensions are canonicalized for comparison in development and protected
  authored evaluation, matching `SampleKey` semantics without changing schema order.

Repository evidence records the development rejection. Validated `QuestionMemoryRecord` state
correctly remains unchanged because no protected terminal evaluation occurred.

See the controlling
[work packet](../../docs/work-packets/polymarket-boundary-volatility-alternative-data.md).
