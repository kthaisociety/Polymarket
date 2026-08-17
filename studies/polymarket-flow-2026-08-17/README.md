# Aggressor flow and subsequent contract-price changes

Epistemic status: **EXPLORATORY — NEGATIVE RESULT**. This study does not define a formal feature or
label, run development validation, access protected evidence, or establish a finding.

## Question

Does aggressor-signed transaction flow in a binary Polymarket contract predict a later change in
the YES-equivalent transaction price? A BUY of outcome 0 and a SELL of outcome 1 are treated as
positive YES-equivalent flow; outcome-1 prices are mapped to `1 - price`.

The exact contract questions are not available through the Chronos adapter. This is therefore a
market-microstructure question over two exact contract identities, not an interpretation of their
event subject matter.

## Exact evidence

Both contracts were read through the engine's public market reads under proved `human_ro`, with
session and transaction read-only settings and denied insert/update privileges. The common cursor
vintage in the retained receipts is `polygon-blocks:45176009-92169181`.

| Contract | Decision cutoff | Tape coverage | Fills | Source / legal-view identity |
|---|---|---|---:|---|
| `0x822e...a46e` | 2026-08-17 09:12:24 UTC | 2025-07-23 19:06:55 to cutoff | 60,518 | [`contract-1-receipt.json`](contract-1-receipt.json) |
| `0xdce8...f264` | 2026-08-17 09:12:42 UTC | 2025-07-11 19:56:48 to cutoff | 59,937 | [`contract-2-receipt.json`](contract-2-receipt.json) |

The two receipts bind source digests, registrations, catalogs, legal `InformationSet` identities,
actual field accesses, the exact code hash
`524813335006dadfaed16727f70d8aca8776d6b777601e4d23e724388ba38b67`, and result artifacts:

- [`contract 1 result`](artifacts/c000ab2e38eb518bf32a4e3928c0e63ff8df750cc5a2b4095a73553dcac2c2a7.result),
  SHA-256 `2c83958c21865924885c46ca68bc6c7d7cdcff83b09c40daad91bf89f13ee924`;
- [`contract 2 result`](artifacts/26df19c16113531fb5b3f1af1181a5f010048b9088a5003457dc73b9e206f2f5.result),
  SHA-256 `225eb2c6905e5bf257e1954ba7b76ecb87b07f192c3398abc9180b7954c950ba`.

The authored analysis is [`analysis.py`](analysis.py). It accessed only `trade_price`,
`signed_trade_size`, `outcome_index`, `reference_time_epoch_seconds`, and `fill_uid`. Every one of
the four registered fields was present for every admitted fill; the adapter rejected incomplete
wide rows rather than imputing. Horizon construction excluded pairs whose future print did not
have a strictly later timestamp. Resulting sample counts vary by horizon and are recorded in the
artifacts.

## Observations

Current flow had a small negative association with later transaction-price changes in both tapes.
The relationship was directionally stable across chronological halves but modest in magnitude.

| Horizon | Contract 1 correlation | Contract 2 correlation |
|---|---:|---:|
| next later print | -0.0721 | -0.0489 |
| 5 prints | -0.0719 | -0.0404 |
| 20 prints | -0.0640 | -0.0343 |
| first print 5–15 minutes later | -0.0596 | -0.0429 |

Rolling 20-fill flow was materially weaker: correlations ranged from about -0.022 to -0.0066 in
contract 1 and from -0.016 to +0.0050 in contract 2. Both selected contracts had mean canonical
prices below 0.008, so these results cover a very low-price regime rather than a representative
cross-section.

The apparent reversal failed the key microstructure falsifier. In contract 1, the buy-minus-sell
future return difference was:

- `-0.0008446` for the first later print of either aggressor direction;
- `+0.00000036` for the first later print with the same aggressor direction;
- `-0.0019848` for the first later print with the opposite aggressor direction.

The exact falsifier, code hash, accesses, and inline result are in
[`same-side-falsifier-receipt.json`](same-side-falsifier-receipt.json); its authored code is
[`same_side_falsifier.py`](same_side_falsifier.py).

## Interpretation and disposition

The raw signed-flow reversal is not credible as a predictive candidate. It nearly disappears when
the future transaction is matched to the same aggressor direction and becomes much larger when the
direction switches. Bid/ask bounce, transaction-price discreteness, and trade-direction mechanics
are therefore stronger explanations than a durable price response to flow.

Disposition: **reject this feature/label idea before formalization**. Preserve it as negative
exploratory evidence; do not request freeze or protected evaluation.

## Limitations and failed checks

- The contracts were the two highest-coverage tapes in a bounded 100-contract discovery sample,
  not a proven global ranking or a random sample.
- Both have the same 2028-11-07 close time and may belong to one event. Event/group identity is not
  exposed, so they cannot be treated as independent cross-contract replication.
- The adapter exposes prints, not historical bid/ask midpoint. The same-direction diagnostic is a
  proxy for spread mechanics, not a full quote-based adjustment.
- The 100-print cap in the falsifier was chosen after observing the initial result.
- Multiple horizons and signals were inspected without multiplicity correction.
- Cursor bounds are not an immutable database snapshot. During these runs the backward cursor
  advanced while the fixed-cutoff numerical artifact remained identical; the retained receipts
  intentionally bind the later exact vintage and digest, but prior database bytes cannot be
  reconstructed.
- `fill_time` follows the declared on-chain block-inclusion observability rule. Collector latency
  and confirmation delay are not modeled.

## Next questions and falsifiers

1. **Quote-based response:** Does any flow relationship remain when the label is a future midpoint
   rather than a transaction price? Falsifier: the effect vanishes after historical top-of-book
   state is registered with explicit availability.
2. **Within-direction size effect:** The same-direction correlation may reflect size outliers even
   though the buy/sell mean difference is near zero. Falsifier: chronological development folds,
   within-direction centering, robust size transforms, and a same-side persistence baseline show no
   stable incremental error reduction.
3. **Independent contracts:** Does the diagnostic reproduce across unrelated events and price
   regimes? Falsifier: grouped evaluation with authoritative event identity reverses or
   concentrates the effect. This question remains blocked on event/group identity.

No next question should be promoted to a protected study until its exact inputs are retained as an
immutable snapshot and its feature, label maturity, temporal folds, and trial ancestry are
formalized.
