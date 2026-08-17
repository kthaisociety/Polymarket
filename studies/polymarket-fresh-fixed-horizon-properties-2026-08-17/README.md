# Fresh-contract fixed-horizon path-property study

Epistemic status: **FORMAL DEVELOPMENT REVISION — PROTECTED DATA UNEXPOSED**.

This study asks whether internal sampled-probability state predicts reversal-first, meaningful-move
incidence, and empirical boundary entry during a fixed 21-hour decision horizon on fresh contracts.
It uses only the ancestor-bound development capability: 31 ancestor events and the expanded final
47 events remain unavailable.

The exact population, labels, feature sets, models, whole-event walk-forward procedure, gates, and
sampled-price caveats were frozen in the
[work packet](../../docs/work-packets/polymarket-fresh-fixed-horizon-properties.md) before authored
code could read the data.

Frozen authored source:
[`source/01_fixed_horizon_properties.py`](source/01_fixed_horizon_properties.py), SHA-256
`aa1c19e9ad0293b6f6719617aef39cafdf8cb8f474c2f88421f2f6278c8c0b13`. The Chronos sandbox
source validator accepted these exact bytes before execution.

## Result

The exact public runner completed twice with byte-identical receipt content. The retained receipt is
[`development-receipts/01_fixed_horizon_properties.json`](development-receipts/01_fixed_horizon_properties.json),
SHA-256 `7fab2899d9f29c6b559f1dd1bfe3754c324243a6f38b1453659abd2e387aeeb2`.
It contains 6,185 OOF rows from 410 markets and 128 whole test events; the largest market and event
contributed 3.04% and 7.79% of rows.

### Reversal-first property

The 21-hour fixed-horizon target is balanced enough to be informative: 2,874 reversal-first rows
and 3,311 other rows. Both predeclared predictive gates passed.

| Model | Observation / event Brier | Pooled / event AP | Top-quintile lift | Event wins |
|---|---:|---:|---:|---:|
| earlier-event rate | `.24974 / .25172` | `.47052 / .50340` | `+.00354` | — |
| six-feature state/shock | `.23959 / .23867` | `.58142 / .68837` | `+.15861` | `87/128` |
| 12-feature path regime | **`.22917 / .22937`** | **`.62234 / .70303`** | **`+.21439`** | `83/128` vs state |

The six-feature model beat the rate in both early and late event halves, had positive within-event
top-quintile lift in 70.6% of eligible events, and no event supplied more than 5.63% of its positive
Brier improvement. The 12-feature extension also improved both halves, had positive event lift in
78.0%, and had 6.86% maximum improvement concentration.

The six-feature one-cent sampled-price screen again failed only its fixed negative-shock breadth
clause: 164 rows/40 events but six negative-shock selections. The full model passed every clause on
370 rows/69 events: observation/event-macro net sampled change `+.06150/+.04328`, 76.8% positive
event means, leave-one-event-out minimum `+.03972`, and positive conditional means after 328
positive and 42 negative shocks.

### Mechanism controls

- Any two-cent move was common (82.1%). State/shock features improved pooled AP from `.81488` to
  `.85458`; the full path model reached `.90466`, with top-quintile precision 93.1%. This supports
  predictable activity regime, although the high base rate limits discrimination value.
- Entry into `[0,.02] ∪ [.98,1]` was rare (3.48%). State/shock features improved pooled AP from
  `.03353` to `.12861` and Brier from `.03409` to `.03280`. The full model did not improve pooled
  AP or observation Brier over state, so extra path complexity is not supported for this target.

Exactly five permitted price fields were accessed. Resolution outcomes, question text, close-time
metadata, all 31 ancestor events, and all 47 protected events were absent; protected exposure is
false. This is a fixed-horizon, selection-exposed development confirmation of a cross-contract
statistical mechanism. It is not quote-validated execution evidence and not protected validation.

## Frozen formal trial

After the exploratory result, a separate formal plan was fixed at checkpoint `50db42dd`. It uses
one earliest eligible shock per market and delegates exact label-maturity filtering to the authored
development evaluator. This addresses overlapping event lifetimes and tests online cross-contract
prediction; it does not claim the exploratory resolution-ordered folds were already formal.

Frozen formal driver:
[`source/02_formal_time_legal_reversal.py`](source/02_formal_time_legal_reversal.py), SHA-256
`f8694e97fc353936e0044321fe0803704f6f67b9bef2278a557ed2d68dccaa25`. The driver publishes both
programs through `CandidatePublisher` and evaluates them through `AuthoredDevelopmentEvaluator`;
the model programs retain no filesystem, network, import, or outcome-at-prediction authority.

The first invocation failed before catalog registration because the derived price rows were not in
the corpus-required market/time order. No candidate or evidence was created. The safe failure is
retained in
[`formal-receipts/02_formal_time_legal_reversal_failed.json`](formal-receipts/02_formal_time_legal_reversal_failed.json).
A corrected driver changes only that ordering and otherwise executes the byte-identical parent
trial: [`source/03_formal_time_legal_reversal_ordered.py`](source/03_formal_time_legal_reversal_ordered.py),
SHA-256 `5e4a71d2337a663b8ff62efd1c58e529599f2074cfbe09b53c26892b3a78efcc`.
Its result is retained separately.

### Strict time-legal result

The corrected driver completed and retained
[`formal-receipts/03_formal_time_legal_reversal_ordered.json`](formal-receipts/03_formal_time_legal_reversal_ordered.json),
SHA-256 `03a77f2c6535a4dab6c4c042365bf175516ea46229d29c78dc7233e7684e6f12`.
Chronos declared 423 earliest-per-market keys and produced 319 OOF predictions after the 100-row
warm-up. These cover 319 unique markets and 117 event groups with 149 reversals/170 other outcomes.

The formal six-feature candidate retained substantial signal: observation Brier improved from
`.25076` to `.24402`, event-macro Brier from `.25228` to `.24153`, pooled AP from `.45255` to
`.60157`, and top-quintile precision/lift reached 65.1%/`+18.37` percentage points. Mean prediction
`.45444` remained close to incidence `.46708`, and the largest event supplied 6.90% of rows.

It nevertheless **failed the conjunctive formal gate** on two stability clauses:

- 65/117 event wins (55.6%) was below the fixed 60% requirement;
- late-half event-macro Brier `.25755` was slightly worse than baseline `.25443`, despite a strong
  early-half improvement (`.22524` versus `.25009`).

Candidate `authored-candidate:1a16b9628578166f38f3ae98bf8a48655342197c8612f277cc326a9db12bb0d2`
and evidence
`authored-development-evidence:ecadaca48c07778578ae9ae7ad6d9c175412b9dce6ce525ddb46621b21e2c6cc`
are retained as formal revise/negative evidence. The program accessed only decision history for
features, legal outcome paths for labels, training rows for fit, and fitted state/features for
prediction. No protected backtest ran.

This result downgrades the six-feature model from formalizable candidate to a real but temporally
unstable lead. The already predeclared 12-feature path model is the only scientifically justified
revision; trying arbitrary new subsets or thresholds would be post-result fishing.

## Final formal revision

At checkpoint `433000d7`, the exact previously declared 12-feature path-regime model was authorized
for one final maturity-controlled formal trial on the identical sample. It must improve baseline
and six-feature evidence, including the late half, or formalization stops without protected data.

Frozen revision driver:
[`source/04_formal_full_path_revision.py`](source/04_formal_full_path_revision.py), SHA-256
`2fa36c181157ae8c1e09540f81b39350b289ca676cd1d5d232c392bcae6a47f3`.
