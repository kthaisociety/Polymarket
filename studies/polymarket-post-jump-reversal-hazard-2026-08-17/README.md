# Polymarket post-jump reversal-first hazard

Epistemic status: **DEVELOPMENT REJECTION WITH EXECUTION LEAD — PROTECTED DATA UNEXPOSED**.

This study asks whether internal state across different Polymarket contracts predicts a path
property: after a retained two-cent shock and one-observation entry delay, does a two-cent reversal
occur before a two-cent continuation within 24 hours?

The exact population, competing-risk label, 12 features, three ridge-logistic models, metrics,
predictive gate, and sampled-price cost falsifier are fixed in the
[work packet](../../docs/work-packets/polymarket-post-jump-reversal-hazard.md) before source 01 reads
the label paths.

The prior aggregate reversal is selection-exposed ancestry only. The final seven protected event
groups/45 markets remain unavailable.

## Result

The exact population produced 715 eligible shocks. Chronological OOF evaluation retained 589 rows
across 77 markets and 15 later event groups: 279 reversal-first labels and 310 continuation-first or
no-cross labels.

| Model | Observation Brier | Event-macro Brier | Pooled AP | Event-macro AP |
|---|---:|---:|---:|---:|
| Earlier-event rate | `0.25369` | `0.25255` | `0.46813` | `0.48042` |
| State plus shock | `0.24577` | `0.24071` | **`0.57211`** | `0.58162` |
| Full path regime | **`0.24312`** | **`0.23359`** | `0.56786` | **`0.66697`** |

The full model won 10/15 events versus state/shock and improved aggregate Brier. It did not pass the
conjunctive predictive gate: pooled AP was slightly lower, early-half event-macro Brier was worse
(`0.24971` versus `0.23120`), and its fixed top-quintile lift was `0.10751`, below the declared
`0.15`. One event still supplied 46.3% of OOF rows, although event-macro metrics and 77 represented
markets prevent that event from being the sole view.

The separately fixed contrarian cost falsifier did pass. Full-model reversal probability at least
`.65` selected 96 sampled trades across ten events. After a one-cent round trip:

- observation/event-macro net sampled change was `+0.01420/+0.01262`;
- 60% of event means were positive;
- leave-one-event-out minimum was `+0.00886`;
- positive-shock trades averaged `+0.02069` and negative-shock trades `+0.00385`.

This is the strongest internal-data execution lead in the current ledger, but the packet required
both predictive and cost gates. No candidate is formalized or frozen, no protected request is made,
and sampled probabilities are not quote evidence. The exact result is retained so a fresh corpus
or independently predeclared question can test it without erasing the failed stability clauses.

## Exact evidence

- Source SHA-256: `25baa10e9273e19b8ff969e4e9f6659b2ccaf4110f6deb7e485feb34a68fcc3a`.
- Receipt SHA-256: `65e9a70ce16551f560b38d4e90155fa00fb25b00ddb3c95558fc8bcc7b73b442`.
- Actual accesses: market identity, chronological event ordinal, observation ordinal/time, and
  sampled probability only.
- Protected exposure: false; formal object references and durable state effects: empty.

## Provisional learning

The public learning services registered both post-shock study receipts, selected the complete
bounded evidence, issued a provisional reflection, and proposed candidate skill
`a42a22ca81c862cb5ee5e61ea81e8e86f1135593d4fe61754a3a828153b105ba`:

> Keep predictive stability and cost-aware execution screens conjunctive for internal Polymarket
> post-shock rules; retain an execution-only pass as a development lead when the predeclared
> predictive gate fails.

The exact candidate receipt SHA-256 is
`df00bad859f41bc8f24019f0efc61c6b1ce10fbb8bc3075ee072f4e4d023cac9`. Its epistemic status is
`CANDIDATE_UNVALIDATED`; validation decision and published learning are both null. This feeds the
Hermes-style learning pipeline without granting itself memory or skill authority.
