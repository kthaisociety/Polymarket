# What survived rigorous behavioral and stochastic testing on Polymarket?

Publication gate: **ACCEPT**.

## Evidence design

The audit verified 90 governed executions representing 48 unique analysis identifiers. 42 executions were exact or revised reruns retained as trial history.

## Statistical controls

| Test | Unit | Raw p | Adjusted p | Search correction | Result |
|---|---|---:|---:|---|---|
| test:process-zero-mass | event | 4.02331e-07 | 1.60933e-06 | holm (n=4) | PASS |
| test:process-sign-reversal | event | 0.00124696 | 0.00249392 | holm (n=4) | PASS |
| test:process-quiet-duration | event | 0.0078125 | 0.0078125 | holm (n=4) | PASS |
| test:process-variance-scaling | event | 5.24521e-06 | 1.57356e-05 | holm (n=4) | PASS |
| test:frozen-arrival-event-wins | event | 7.45058e-09 | 2.75671e-07 | bonferroni-recorded-search (n=37) | PASS |
| test:fresh-reversal-event-wins | event | 2.9387e-05 | 0.00108732 | bonferroni-recorded-search (n=37) | PASS |

## Audited claims

### C01 — SUPPORTED

Every campaign execution is present, and the retained nonreplay audit inventories 25 governed artifacts that must not be reissued as ordinary analysis.

Scope:

- The nonreplay audit records coverage; it does not reopen protected evidence.

### C02 — SUPPORTED

Registered hourly probabilities retained an interior zero-increment event mean of 43.81% across 26 eligible later-cohort events, with a whole-event 95% interval from 38.71% to 49.52%; the fixed null was 20%.

Scope:

- The estimand is the registered sample process, not latent belief or price.
- The later cohort is fresh development replication, not protected evidence.

### C03 — SUPPORTED

Adjacent nonzero changes reversed sign at an event mean of 58.45% across 26 eligible later-cohort events, with a whole-event 95% interval from 55.53% to 61.41%; the fixed null was 50%.

Scope:

- The estimand is the registered sample process, not latent belief or price.
- The later cohort is fresh development replication, not protected evidence.

### C04 — SUPPORTED

The long-quiet to active next-move-rate ratio had an event mean of 7.36% across 7 eligible later-cohort events, with a whole-event 95% interval from 5.23% to 9.65%; the fixed null was 50%.

Scope:

- The estimand is the registered sample process, not latent belief or price.
- The later cohort is fresh development replication, not protected evidence.

### C05 — SUPPORTED

The 24-hour variance ratio had an event mean of 32.40% across 26 eligible later-cohort events, with a whole-event 95% interval from 24.97% to 40.43%; the fixed null was 75%.

Scope:

- The estimand is the registered sample process, not latent belief or price.
- The later cohort is fresh development replication, not protected evidence.

### C06 — SUPPORTED

The frozen state-plus-staleness arrival model improved later-cohort event-macro Brier by 33.38% and won 27 of 27 events; the paired event bootstrap improvement interval was 0.0716 to 0.1035.

Scope:

- This predicts the registered next-sample update, not a tradeable price move.
- The replay is fresh development evidence and is not the rejected protected run.

### C07 — SUPPORTED

The unchanged full hurdle law improved successor event-macro NLL by 7.88% and won 27 of 27 events against the state-only law.

Scope:

- This is a registered-sample density result, not a trading result.

### C08 — SUPPORTED

The fresh post-jump reversal state model improved event-macro Brier by 0.0132, won 87 of 128 represented events, and had a paired event-bootstrap interval of 0.0051 to 0.0214.

Scope:

- The candidate predicts reversal-first labels after sampled jumps.
- Its one-cent sampled-mark cost screen failed and is not execution evidence.

### C09 — SUPPORTED

The selection-exposed development screen recorded `RETAIN_FOR_FRESH_EVALUATION` for the 2–10% longshot-fade candidate.

Scope:

- This is a candidate-selection result, not fresh confirmation.
- The two-cent hurdle is not an observed spread, fee, depth, or impact model.

### C10 — SUPPORTED

The exposed behavioral reruns rejected the fixed skilled-wallet, delayed expert, activity-matched wallet, and crowded-extrapolation candidates. Skilled-wallet incremental event-macro edge was -1.11%; six-hour expert net return was -0.63%; and crowded 24-hour fade return was -0.77%.

Scope:

- These are exact exposed reproductions, not independent confirmation.
- Matching and delays are controls, not randomized causal identification.

### C11 — SUPPORTED

The focal screen recorded `NO_STABLE_FOCAL_EFFECT`; ambiguity recorded `REJECT_FIXED_AMBIGUITY_PROXY_CANDIDATE`; the underround `passes_all` result was False; and the bracket discovery gate was False.

Scope:

- Disposition and NegRisk mechanisms remain blocked by missing historical state.

### C12 — SUPPORTED

The verified campaigns contain no execution-validated strategy; a profitability claim requires historical quotes or order books, observed spreads and fees, latency, queue position, partial fills, and event-level net-edge uncertainty.

Scope:

- Sampled probabilities and fixed cost haircuts are not executable evidence.

### C13 — SUPPORTED

The longshot-fade candidate is not confirmed; confirmation requires a frozen one-shot evaluation on a new untouched chronological cohort.

Scope:

- Reusing the exposed development cohort cannot restore freshness.

## Status boundary

Publication acceptance checks wording against retained evidence. It is not scientific promotion, protected confirmation, or authorization to trade.

Machine audit: `paper-audit-report:e8ed21a7f08e0e35c8277138515f0cad1cf0d84f0fe6fca438aa380f0fa2d910`.
