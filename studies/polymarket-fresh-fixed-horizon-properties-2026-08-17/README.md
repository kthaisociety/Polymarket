# Fresh-contract fixed-horizon path-property study

Epistemic status: **FIXED-HORIZON DEVELOPMENT GATE PASSED — PROTECTED DATA UNEXPOSED**.

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
