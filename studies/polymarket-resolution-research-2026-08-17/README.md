# Resolution-probability research on retained Polymarket contracts

Epistemic status: **DEVELOPMENT REJECTION — PROTECTED DATA UNEXPOSED**. This study used a retained
production corpus and a chronological whole-event development partition. It did not freeze a
system, consume protected outcomes, publish a `NegativeResult`, or update validated question
memory.

## Question and population

Do sampled outcome-token probabilities in recently resolved Polymarket markets benefit from a
small path-based or calibration adjustment when predicting the final payout?

The exact source is the 19,434,443-byte corpus
`polymarket-corpus:610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f`,
retained from a repeatable-read production transaction under `human_ro`. It contains 200 binary
markets, 31 server event groups, 71,467 one-hour sampled prices, and 200 recorded on-chain
resolutions. The [corpus receipt](corpus-receipt.json) binds the selection and registrations.

Whole events were ordered by their latest recorded resolution time. The earliest 24 events (155
markets) formed development; the final 7 events (45 markets) remained protected. The exact
partition identity is
`49d5e9a97985a44e3277f43ee55ce1281c430a1d0a1823754a9a759ac56d3bd1`.
Changing every retained value in a protected event leaves the development capability and authored
result invariant in the causal test.

The primary exploratory decision is the 24th retained hourly sample for each market. This is a
reproducible observation ordinal that uses only the path seen so far; it is not a fixed economic
horizon. Corpus inclusion nevertheless conditions on later resolution and minimum coverage, which
limits causal and deployment claims.

## Executed research

Each source under [`sources/`](sources/) ran unchanged through `AnalysisHarness`. Each receipt under
[`development-receipts/`](development-receipts/) records the exact code hash, actual field
accesses, snapshot/partition identity, result, warnings, and zero protected exposure.

| Trial | Question | Development result | Disposition |
|---|---|---|---|
| 01 | Is the 24th sampled probability useful and calibrated? | Raw probability Brier 0.1037 versus descriptive same-sample prevalence Brier 0.1171; observed outcome rates were below mean probabilities in four populated bins. | Retain the raw probability baseline; test calibration out of fold. |
| 02 | Does 12-sample momentum add information beyond current price? | Every fixed momentum strength worsened Brier; the best tested change was +0.00188. | Reject momentum adjustment. |
| 03 | Do recent variability or sampling gaps diagnose forecast error? | Descriptive slopes existed, but were unstandardized, uncontrolled, and not directional predictions. | Do not formalize. |
| 04 | Is the baseline stable across observation ordinals? | Brier was 0.1260, 0.1037, 0.1112, and 0.1106 at ordinals 12, 24, 48, and 96; later populations lost events/markets. | Retain ordinal 24 only as this study's declared question; no horizon claim. |
| 05 | Does fold-local scalar/affine down-calibration improve expanding event blocks? | Both calibrators worsened market-weighted aggregate Brier: about 0.1109 versus 0.1054, and lost in all three folds. | Reject for the market-weighted estimand. |
| 06 | Does rolling event-macro calibration hold? | Execution succeeded, but detail exceeded the old preview and remained only in an ephemeral artifact. | Interface failure retained; no scientific conclusion. |
| 07 | Does compact retained one-event-ahead evidence support event-macro calibration? | Equal-event Brier improved only 0.1224 to 0.1181, with 6 wins in 16 events; market-weighted Brier worsened 0.0824 to 0.0893. Event deltas ranged from -0.3106 to +0.1164. | Reject as concentrated and estimand-dependent. |

## Interpretation

The useful result is narrower than “nothing works.” The sampled probability itself contains real
development predictive information relative to an unconditional prevalence comparator. The
specific attempts to improve it did not survive the declared controls:

- short path momentum is baseline-inferior;
- pooled overprediction does not translate into stable market-weighted walk-forward improvement;
- the small equal-event calibration gain wins in fewer than half of tested events and is dominated
  by one unusually favorable event;
- variability and sampling-gap associations are diagnostics, not yet stable predictive features.

No candidate satisfies the predeclared stability and baseline criteria. The correct transition is
therefore a development rejection with the raw market probability retained as the benchmark for a
new question—not a protected backtest.

## Concrete harness repair

Trial 06 exposed that a successful sandbox result larger than the inline preview could disappear
with its in-memory artifact when the offline command exited. The composition now grants a bounded
200 KB structured-result preview and refuses to write a successful study receipt with missing
details. Trial 07 is a new source and receipt; the failed trial was not overwritten or deleted.

## Limitations and next questions

- Sampled prices are not executable bid/ask quotes, so these are probability-quality results, not
  trading-PnL results.
- Market metadata is a retained current projection, not a historical revision stream. The ordinal
  decision avoids choosing on close/resolution time but does not remove resolved-corpus selection.
- Twenty-four development events are too few for broad domain generalization, and event sizes are
  highly unequal.
- The selected outcome leg and latest resolved cohort may not represent all Polymarket categories,
  price regimes, or horizons.
- A new question could use a larger retained event corpus, quote/midpoint history, and a declared
  fixed economic horizon. It must receive a new partition and trial budget rather than reopening
  these protected events after seeing their outcomes.

Validated terminal memory is intentionally unchanged. Chronos permits that memory only after an
independently issued protected finding or protected rejection; this development ledger is the
truthful memory layer for the present result.
