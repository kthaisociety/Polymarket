# Sampling, size, and transform probes on Polymarket fills

Epistemic status: **EXPLORATORY — NEGATIVE RESULT**. No formal candidate, development trial,
protected evidence, finding, or terminal question-memory record was created.

## Startup scope

The study forward-tested `$start-polymarket-research` and `$analyze-time-series-data` against two
exact production contract tapes under the proved `human_ro` read-only role. It retained the same
fixed decision cutoffs as the earlier flow study:

| Contract | Decision cutoff | Fills | Price regime |
|---|---|---:|---|
| `0x822e...a46e` | 2026-08-17 09:12:24 UTC | 60,518 | all canonical prices below 0.05 |
| `0xdce8...f264` | 2026-08-17 09:12:42 UTC | 59,937 | all canonical prices below 0.05 |

The contract questions and authoritative event grouping remain unavailable. Both contracts may
belong to one event and are not treated as independent replication. `fill_time` is available only
under `polymarket-onchain-block-inclusion/v1`; current cursor bounds are not immutable historical
database snapshots.

## Authored probes and exact evidence

Each program accessed only `trade_price`, `signed_trade_size`, `outcome_index`,
`reference_time_epoch_seconds`, and `fill_uid`. Every receipt records exact registration,
information-set, source, code, actual-access, and result identities.

| Program | Code SHA-256 | Contract 1 | Contract 2 |
|---|---|---|---|
| [Activity clocks and events](activity_clocks.py) | `f3e97e51e47cc55e76527362dd0a3b6828d100132221208ac03dea646e2cdd72` | [receipt](contract-1-activity-receipt.json), [result](artifacts/67e5d42f35f5fd86f2589948472aebd1271a6c187e02b2266a5b76b0593b3695.result) | [receipt](contract-2-activity-receipt.json), [result](artifacts/dff9b31645b440bf0c676f1d733d1a760174a73679f4e71092f03c0f7370a9f4.result) |
| [Size and transforms](size_and_transforms.py) | `8528815ffc6aefece1e87390817be0dcbfc8fe1f4d4a9dfd92390978e9697ad4` | [receipt](contract-1-size-transform-receipt.json), [result](artifacts/323c9f7e35f0e38e6ed1e4933861cdb90cf71d6b906f7c3cccce1475fce3cb8b.result) | [receipt](contract-2-size-transform-receipt.json), [result](artifacts/ce9c73149ef4e2e234ee0b1304e55f6fbea7c8fcb21a5abbb971167031597a3d.result) |
| [Microstructure controls](microstructure_controls.py) | `50f3a13cd93be14fea48fffbe2150efa0a1050eb96c9af1a84c69d2f27256bde` | [inline receipt](contract-1-controls-receipt.json) | [inline receipt](contract-2-controls-receipt.json) |

During the runs the backward cursor moved from block `45056009` to `45026009`. The fixed-cutoff fill
counts stayed unchanged, but contract-1 registration/source identity changed as designed. The
receipts preserve the exact vintage used by each result; they do not claim to reconstruct older
database bytes.

## Questions and alternatives

The method menu was used selectively to ask:

1. Does signed flow behave differently on trade-count, elapsed-time, or early-calibrated size
   clocks?
2. Do extreme rolling imbalance and aggressor runs anticipate later canonical transaction-price
   changes?
3. Does fill size predict the next same-aggressor price after controlling immediate side switching?
4. Do rolling deviations or fixed-width fractional transforms expose price memory beyond a simple
   level baseline?
5. Are strong effects actually explained by aggressor switching and transaction-price bounce?

The declared rival was microstructure mechanics. The decisive falsifiers were separate buy/sell
paths and a two-sided bucket price formed as the average of within-bucket buy and sell means. That
two-sided value is only a diagnostic, not a historical quote midpoint.

## Observations

### Activity clocks changed the apparent result

| Probe | Contract 1 correlation | Contract 2 correlation |
|---|---:|---:|
| 50-fill bucket imbalance → next bucket return | -0.0290 | +0.0087 |
| 15-minute nonempty bucket imbalance → next bucket return | -0.4783 | -0.4594 |
| Early-calibrated size-bucket imbalance → next bucket return | -0.0919 | -0.0685 |
| Rolling-20 imbalance crossing → 20-fill return | -0.3362 | -0.3394 |
| Five-fill aggressor run → 20-fill return | -0.6153 | -0.5956 |

The 50-fill result was approximately null and changed sign. The strong elapsed-time, imbalance, and
run results were plausible only before controlling transaction direction.

### Size evidence was outlier- and side-dependent

For the next same-aggressor price within 100 fills, raw-size correlation was `+0.0649` and `+0.0963`.
After capping size at the first-fifth 95th percentile, it fell to `+0.0092` and `+0.0076`. Buy-only
raw correlations were larger (`+0.1815`, `+0.4167`) but contract 1's second-half value was only
`+0.0028`; sell-only correlations were negative (`-0.0544`, `-0.1094`). Top-minus-bottom mean
changes were only a few millionths in canonical price.

This does not support a stable size feature. It shows sensitivity to outliers, aggressor side,
contract, and chronology.

### Raw transform results inherited reversal mechanics

One-fill price-change autocorrelation was `-0.5597` and `-0.5678`. Rolling-50 deviation correlation
with a 20-fill future change was `-0.6510` and `-0.5685`; the strongest tested fixed-width fractional
example (`d=0.5`, width 50) was `-0.5912` and `-0.5706`.

These large values were not treated as signal because the same price series alternates between
aggressor sides. After splitting the paths:

| Control | Contract 1 | Contract 2 |
|---|---:|---:|
| Buy-path one-step autocorrelation | -0.0620 | -0.1118 |
| Sell-path one-step autocorrelation | -0.0396 | -0.1938 |
| Buy-path rolling deviation → future same-side return | -0.2628 | +0.1501 |
| Sell-path rolling deviation → future same-side return | -0.1564 | +0.0338 |

The rolling-deviation signs also changed across contracts or chronological halves. Fractional
orders and window width were illustrative trials, not fold-selected stationarity solutions.

### Direction-neutral buckets falsified the headline effect

| Control | Contract 1 correlation | Contract 2 correlation |
|---|---:|---:|
| 15-minute imbalance → next two-sided bucket-price change | +0.0499 | +0.0376 |
| 60-minute imbalance → next two-sided bucket-price change | +0.0708 | +0.0619 |

The raw 15-minute relationship changed from about `-0.47` to a small positive value. Its sign and
magnitude were therefore governed primarily by which aggressor side set transaction prices, not by
a demonstrated belief response to flow.

## Disposition

Reject all inspected flow, run, raw-size, rolling-deviation, and fractional-transform variants
before formalization. The apparent strength is mechanically explained, outlier-sensitive, unstable,
or approximately null under the relevant control. No method from the financial-ML catalog becomes a
default or a surviving candidate merely because it was tried.

This negative result updates the exploratory ledger only. Chronos terminal question memory remains
unchanged because no independently permitted protected run issued a finding or rejection.

## Remaining questions

1. **Historical quote state:** do any activity or size effects survive a registered top-of-book
   midpoint label? Blocked until quote history with exact availability exists.
2. **Broader price regimes:** do direction-neutral diagnostics differ away from prices below 0.05?
   Requires an explicitly selected broader contract population and authoritative group controls.
3. **Event independence:** does a result reproduce across unrelated events? Blocked on event/group
   identity.
4. **Real predictive development:** can one exploratory mechanism survive enough controls to justify
   a formal later-transaction target? No current probe passed that threshold.
