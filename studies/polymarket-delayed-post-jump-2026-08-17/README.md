# Delayed Polymarket post-jump continuation

Epistemic status: **DEVELOPMENT REJECTION WITH PROVISIONAL REVERSAL LESSON — PROTECTED DATA
UNEXPOSED**.

This study tests whether a retained probability shock of at least two cents continues over the
following 24 hours after delaying entry by one retained observation. It also asks whether legal
pre-shock staleness features improve an expanding event-walk-forward ridge beyond probability state
or shock size alone.

The exact sample, label, 11 features, four models, one-cent cost falsifier, and advancement gates
are fixed in the
[work packet](../../docs/work-packets/polymarket-delayed-post-jump.md) before source 01 reads any
development outcome.

The final seven protected events/45 markets are not requested. Sampled probabilities are not
historical bid/ask quotes, so even a passing cost diagnostic would be a candidate for execution
validation rather than a trading claim.

## Result

The source produced 715 eligible post-shock samples across 23 development events. Expanding
walk-forward evaluation retained 589 OOF rows across 77 markets and 15 later event groups, with 468
labels moving by at least one cent.

| Model | Observation MSE | Event-macro MSE | Meaningful direction accuracy |
|---|---:|---:|---:|
| Zero change | `0.00942` | `0.01636` | — |
| Probability state | `0.01073` | `0.01808` | `0.4765` |
| Shock size/slippage | **`0.00868`** | **`0.01532`** | `0.5150` |
| Shock plus state/staleness | `0.01088` | `0.01683` | `0.5342` |

The candidate lost aggregate MSE to zero and shock-only, won only 4/15 events against shock-only,
and failed the fixed diversity condition because event 14 supplied 46.3% of OOF rows. The largest
single market supplied 15.6%, so contract breadth was real but event-family breadth was not.

The fixed process diagnostic found delayed reversal rather than continuation: mean shock-signed
future change was `-0.01207`, and only 42.3% of meaningful labels continued in the shock direction.
That is a useful statistical lead, but it was not a predeclared candidate and is heterogeneous
across events.

The one-cent cost falsifier selected 486 trades. Observation/event-macro net sampled change was
`+0.00167/+0.01710`, but only 7/15 event means were positive. NO-side mean was `+0.01463`; YES-side
mean was `-0.00717`. The fixed gate failed, and sampled probabilities remain non-executable.

No model is formalized or frozen. The continuation branch is closed; the aggregate reversal may
motivate a separately predeclared incidence question but cannot be called validated or promoted to
Hermes-style memory.

## Exact evidence

- Source SHA-256: `a923a7f044d771fec5ed03cf904102b038b1d64ae068af55e9377974273f9d01`.
- Receipt SHA-256: `311fc5cbfdeb0925e60146fbc565249db9ec3aa6cfbd3d01880ee85a396939a0`.
- Actual accesses: market identity, chronological event ordinal, observation ordinal/time, and
  sampled probability only.
- Protected exposure: false; formal references and durable state effects: empty.
