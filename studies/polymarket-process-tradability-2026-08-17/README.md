# Polymarket probability process and tradability study

Epistemic status: **DEVELOPMENT REJECTION — PROTECTED DATA UNEXPOSED**.

This study asks which mathematical/statistical process, if any, best describes the retained hourly
probability paths and whether a stable conditional drift could support a trading candidate. Every
analysis runs against the exact development capability for
`polymarket-corpus:610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f`.
The final seven event groups and their 45 markets remain protected and unavailable.

The working process families are a driftless martingale/random walk, bounded state-dependent
diffusion, mean-reverting or momentum drift, and a zero-inflated jump/mixture observation process.
Sampled probabilities are not executable bid/ask quotes, so any return calculation is explicitly a
pseudo-trading diagnostic until separately validated on legal historical book state or prospective
paper execution.

See the controlling
[work packet](../../docs/work-packets/polymarket-stochastic-process-tradability.md) for the
predeclared interpretation and trading gates.

Before execution, the follow-up reversal falsifier was frozen to require both a one-observation
delay and a directly buyable long-only result at the same 0.01 cost. Two-sided, short-only,
active-move, and probability-regime results are all retained; only the delayed two-sided plus
delayed long-only pair governs whether the sampled-price candidate remains usable.

## What process do these samples follow?

At the retained hourly scale, a simple Gaussian random walk or smooth bounded diffusion is a poor
description of the observations:

- 62.54% of one-hour changes are exactly zero;
- increment kurtosis is 99.29;
- lag-one change correlation is -0.212;
- 2-, 4-, 8-, and 24-hour variance ratios are 0.762, 0.584, 0.429, and 0.247 rather than near one;
- drift and variance vary materially across probability regions.

The most defensible description is therefore a **bounded, sticky, zero-inflated heavy-tailed
jump/mixture observation process whose conditional mean is approximately martingale-like, with a
small transient negative-dependence component**. That describes the sampled token history. It does
not prove the latent belief process or executable quote process has exactly the same law.

## Executed research loop

Every row below is an exact authored source and immutable receipt. Failed and denied attempts were
kept rather than rewritten out of the record.

| Trial | Question | Result | Disposition |
|---|---|---|---|
| 01 | Broad process diagnostics | Timed out before data access because authored list construction was quadratic. | Retain failure; rewrite without changing the question. |
| 02 | Linear process diagnostics | 60,511 observations/60,356 increments; zero mass, extreme tails, negative lag dependence, and sublinear variance growth. | Reject smooth Gaussian diffusion; retain sticky jump/mixture description. |
| 03 | Walk-forward martingale, momentum, reversal, and state-drift models at 1/6/24 hours | Fitted reversal improved event-macro MSE only by 0.000062, 0.000109, and 0.000055. Immediate sampled-price pseudo-PnL looked positive at 1 cent for 1 and 24 hours. | Falsify execution sensitivity before formalization. |
| 04 | First execution falsifier | Denied before data access because method calls are outside the sandbox language. | Retain denial; express the identical frozen test in the allowed subset. |
| 05 | One-sample delay and position-side falsifiers | At one hour, delayed two-sided net was -0.000559 per decision with 2/16 positive events; delayed long-only was -0.000233 with 3/16. At 24 hours, delayed two-sided weighting signs disagreed and delayed long-only was negative. | Reject reversal as transient sampled-price bounce, not a usable trade. |
| 06 | Can the researcher see contract meaning? | Development-only catalog retained questions for 155 markets; protected questions stayed hidden. | Use exact wording to form a separate structural hypothesis. |
| 07 | Do explicit exhaustive outcome buckets show persistent underround? | At 1 cent per leg, zero of four events had positive median net underround; the predeclared gate failed. Some raw sums were implausibly far above one. | Reject underround; treat extremes as stale/non-executable sample evidence. |
| 08 | Does outcome index zero actually mean YES? | All 155 development paths carry the exact retained label `Yes`. | Rule out label reversal; retain outcome meaning as explicit authority. |

## Tradability conclusion

No tradable idea survived development controls.

The fitted reversal was the only directional candidate to clear the first sampled-price/cost screen,
but it vanished after a one-observation delay on both the two-sided and directly buyable long-only
variants. The exhaustive-bucket idea also failed its frozen per-leg-cost and persistence gate.
Neither result reached formal feature/label/system definition, freeze, protected evaluation, or
validated memory.

This is not a claim that Polymarket has no edge. It is a narrower result: this resolved-contract,
hourly sampled-price corpus does not establish an executable edge under the tested mechanisms.
Historical bid/ask depth or prospective quote-based paper execution is required for a trading
claim; sampled probabilities cannot substitute for that evidence.

## Harness improvements exposed by the research

The real runs required two narrow authority repairs:

- development views now issue the partition's authoritative chronological event ordinal, so
  walk-forward fitting cannot infer time from physical file order;
- development outcome views now issue exact question text and the selected outcome label, enabling
  semantic hypotheses and outcome-identity audits without exposing protected events.

The failed quadratic trial and denied sandbox-language trial remain retained. The final seven event
groups/45 markets were never requested or exposed. Repository Markdown records this development
history; validated terminal question memory correctly remains unchanged because no protected
resolution occurred.
