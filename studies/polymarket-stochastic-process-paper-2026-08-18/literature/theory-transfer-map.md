# Theory transfer map

## Purpose and status

This is a paper-working bibliography and claim map, not a final literature review. It records which
parts of established financial mathematics are candidates for transfer to binary prediction
contracts, what additional assumptions each transfer requires, and how the Chronos development
evidence bears on them. Recent 2026 working papers are treated as contemporaneous evidence, not as
settled authority.

## Contract and identification layer

A YES share has a terminal payoff `X` in `{0, 1}`. The familiar contingent-claim identity
`P_t = E^Q[X | F_t]` transfers only as a pricing-measure statement under no-arbitrage and an
appropriate numeraire. It does not automatically make `P_t` the physical probability, the mean
trader belief, or an executable midprice. Prediction markets lack the continuously traded
underlying and replication argument that anchors an ordinary equity option.

- [Wolfers and Zitzewitz (2004), “Prediction Markets”](https://www.aeaweb.org/articles?id=10.1257%2F0895330041371321)
  describe binary contracts as information-aggregation and forecasting mechanisms, while making
  market design and contract interpretation part of the problem.
- [Manski (2006), “Interpreting the predictions of prediction markets”](https://doi.org/10.1016/j.econlet.2006.01.004)
  shows that heterogeneous risk-neutral beliefs do not generally identify their mean from price;
  the equilibrium price only partially identifies central tendency.
- [Wolfers and Zitzewitz (2006), “Interpreting Prediction Market Prices as Probabilities”](https://www.nber.org/papers/w12200)
  give sufficient conditions under which price corresponds to mean belief and argue that the gap
  is often small for broader parameter classes. The disagreement with Manski is assumption-driven,
  so the paper must state rather than hide its identifying assumptions.

**Chronos consequence:** call the recorded field a sampled YES probability because that is its
source representation, but treat calibration to realized payout as an empirical property. Do not
equate it with latent belief, a quote, or an executable probability by definition.

## Dynamic-price layer

The martingale idea transfers as a falsifiable benchmark: if price is the correctly measured
conditional expectation under a stable relevant measure, innovations should have zero conditional
mean. Brownian diffusion does not transfer automatically. The state space is bounded, terminal
payoff is absorbed at zero or one, information arrives discontinuously, and trading/sampling may be
irregular.

- [Archak and Ipeirotis, “Modeling Volatility in Prediction Markets”](https://pages.stern.nyu.edu/~narchak/acm_ec_paper.pdf)
  derive a binary-market volatility model from a latent competitive-state process. It motivates
  probit/logit-style coordinates and time-to-resolution effects rather than constant volatility in
  raw price space.
- [Majumder, Diermeier, Rietz, and Amaral (2009), “Price dynamics in political prediction markets”](https://doi.org/10.1073/pnas.0805037106)
  report uncorrelated returns, persistent volatility, heavy return tails, and volatility that can
  rise toward settlement in Iowa election contracts. Their binary-option model explicitly differs
  from ordinary options because there is no traded underlying and settlement is discontinuous.
- [Hawkes (1971), “Spectra of some self-exciting and mutually exciting point processes”](https://doi.org/10.1093/biomet/58.1.83)
  supplies the canonical event-time framework for clustered arrivals. It is a candidate language
  for update timing, not evidence that Polymarket changes are literally Hawkes-distributed.
- [Bacry et al., “Modeling microstructure noise with mutually exciting point processes”](https://arxiv.org/abs/1101.3422)
  show how positive and negative price jumps can be represented by mutually exciting counting
  processes. This is relevant to separating an update clock from signed marks and to interpreting
  short-run reversal as possible microstructure.

**Chronos evidence:** source 01 rejects smooth Gaussian diffusion for the registered samples;
69.62% of increments are zero and nonzero tails are extreme. Source 03 shows a non-memoryless
update clock: state plus staleness improves event-macro Brier 27.63% and wins 112/113 events. Source
04 shows modest path dependence in nonzero signs, dominated by a stable reversal term. Source 05
shows strong conditional size clustering, while Gaussian residuals win after modeling log absolute
nonzero size. The current leading empirical decomposition is a bounded hurdle/marked process:

1. a state- and duration-dependent update indicator;
2. a signed mark with short-run reversal;
3. a path-dependent log-size component with approximately Gaussian residuals in the fixed
   comparison;
4. terminal absorption at zero or one.

This description applies to registered hourly samples. A continuous latent efficient price may
still exist underneath them.

## Calibration and financial-theory layer

Proper scoring rules, reliability diagrams, chronological validation, and cluster-aware inference
transfer cleanly. Treating every sampled row or related contract as independent does not.

- [Brier (1950), “Verification of forecasts expressed in terms of probability”](https://doi.org/10.1175/1520-0493%281950%29078%3C0001%3AVOFEIT%3E2.0.CO%3B2)
  provides the quadratic probability score used for forecast evaluation.
- [Bürgi, Deng, and Whelan (2025), “Makers and Takers: The Economics of the Kalshi Prediction Market”](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5502658)
  report informative prices alongside favorite–longshot bias in a modern regulated venue and
  connect it to quote-driven microstructure.
- [Dubach (2026), “The Anatomy of a Decentralized Prediction Market”](https://arxiv.org/abs/2604.24366)
  reports Polymarket order-book structure and shows that public-feed trade-direction inference can
  be unreliable against on-chain ground truth. This supports Chronos's refusal to call sampled
  probability changes trades or signed order flow.
- [Gruener (2026), “Calibrated but Not Sharp”](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6863546)
  demonstrates on a narrow Polymarket crypto cohort how dependence-naive trade samples can create a
  calibration finding that disappears under cluster-aware inference. It is a recent working-paper
  warning, not a general Polymarket conclusion.

**Chronos evidence:** source 02 finds sampled probabilities above realized YES rates by roughly
4.1–9.2 percentage points at fixed horizons, under both market and event weighting. This is a
development lead consistent with favorite–longshot-style miscalibration, not yet mispricing. It
still needs event-cluster uncertainty, semantic/regime stability, related-contract controls, and
an executable-quote boundary.

## What transfers, what changes, what currently fails

| Established idea | Transfer status | Required prediction-market modification | Current evidence |
|---|---|---|---|
| Contingent claim payoff | Direct | Binary terminal payout and resolution rules are part of identity | Supported by corpus outcomes |
| No-arbitrage/martingale pricing | Conditional benchmark | Incomplete market, no replicating underlying, physical versus pricing measure | Raw negative drift and sign reversal challenge the observed-sample martingale |
| Constant Brownian diffusion | Fails descriptively | Bounded state, zero inflation, jumps, irregular information time | Rejected by source 01 |
| Local/state-dependent volatility | Transfers | Must degenerate/absorb at boundaries and change with time-to-close | State strongly predicts log magnitude in source 05 |
| Event-time point process | Transfers | Duration, price state, semantics, and sampling mechanism enter intensity | Strongly supported by source 03 |
| Volatility clustering | Transfers | Separate arrival clustering from conditional mark-size clustering | Both components supported by sources 03 and 05 |
| Return-sign independence | Fails for registered marks | Allow bid/ask bounce, rounding, aggregation, or belief reversal | Source 04 passes modestly |
| Heavy-tailed raw returns | Transfers descriptively | Decompose zero mass and conditional size before selecting a residual law | Raw tails supported; heavy-tailed log-size residuals rejected in source 05 |
| Probability calibration | Transfers empirically | Prices are forecasts only under explicit interpretation; cluster by event | Source 02 opens but does not settle the claim |
| Black–Scholes replication | Does not transfer directly | No traded underlying or dynamic completeness; resolution is semantic/discontinuous | Structural non-transfer |
| Cross-contract arbitrage | Potentially transfers | Requires complete mutually exclusive/exhaustive outcome surfaces and executable quotes | Not identified by current corpus |

## Paper claims not yet authorized

- A specific continuous-time SDE for latent beliefs.
- A Hawkes parameterization or branching ratio.
- Objective-probability equality.
- General Polymarket favorite–longshot bias.
- Executable alpha, Sharpe ratio, or profit after spread, fees, slippage, and latency.
- Causal interpretation of staleness, reversal, or magnitude features.

Those claims require the remaining semantic/regime controls, exact formalization, and—where
applicable—quote/order-book data that the current immutable corpus does not contain.
