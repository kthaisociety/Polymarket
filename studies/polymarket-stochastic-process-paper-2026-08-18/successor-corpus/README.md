# Paper successor-corpus acquisition

Epistemic status: **PREDECLARED DATA ACQUISITION — NOT SCIENTIFIC EVIDENCE**.

This acquisition tests the open-discovery rule by requesting a broader chronological production
cohort through the existing fail-closed `human_ro` path. The fixed request is:

- as-of `2026-08-18T11:40:00+00:00`;
- binary resolved contracts with authoritative event identity and legal lifecycle;
- YES outcome index `0`, price fidelity `60`, at least `24` retained points;
- deterministic resolution/event/market order;
- maximum `2,000` markets;
- local content-addressed workspace `data/chronos/polymarket-corpora`.

The command must prove the database role, default and transaction read-only settings, denied
insert/update privileges, and repeatable-read isolation. It may emit only the sanitized receipt.
No newly acquired probability or payout may be inspected until the receipt establishes whether the
snapshot has material coverage beyond the 1,000-contract ancestor and a separate partition/design
is fixed.

This operation does not mutate production, overwrite the ancestor corpus, establish a scientific
finding, or authorize protected exposure.

## Acquisition result

Status: **SUCCEEDED — REGISTERED DATA, NOT SCIENTIFIC EVIDENCE**.

- Snapshot:
  `polymarket-corpus:184b83f7f8012da4ca9116c8b6bad2076570ad5f0bada95b22615ee2f5cceae8`,
  428,280,682 canonical bytes.
- Sanitized [`corpus-receipt.json`](corpus-receipt.json) SHA-256:
  `c32044578a1980018dc2f30f9350593176ba2c2f96a127bd23fde645d20abde3`.
- Coverage: 1,509 contracts, 321 server event groups, 1,585,740 hourly probability observations,
  and 1,509 resolution observations.
- Latest retained price/resolution times: `2026-08-17T15:00:18+00:00` and
  `2026-08-17T18:35:40+00:00`.
- Increment over the ancestor: 509 contracts and 86 event groups.
- Authority: `human_ro`, default/transaction read-only true, repeatable-read isolation; no
  credentials or values emitted and no production writes.

## Identity-only partition result

Status: **SUCCEEDED — AUTHORITY PROOF, NOT SCIENTIFIC EVIDENCE**.

- Partition: `f7b47ea95c3630f083552bce84126711fb1a23b20ec7caa33e7527ba977586d7`,
  using `whole-event-chronological-fresh-replication/v1`.
- Fresh development: 29 event groups and 147 markets.
- Ancestor embargo: 227 event groups and 1,005 markets. The remaining 8 of the 235 ancestor
  event groups fall inside the successor snapshot's final protected chronological block.
- Protected and unavailable: 65 event groups and 357 markets.
- The authored audit requested no partition values, read zero value fields, and recorded zero
  actual accesses. `protected_values_exposed` is false.
- Sanitized [`07_successor_partition_identity.json`](partition-receipts/07_successor_partition_identity.json)
  SHA-256: `82628a646a9c94ec49e0620d5d07e8b6bdd750b7c11fd08d4e93d04fb664538e`.

The next experiment is an unchanged replay of source 01 on only the 29 fresh development event
groups. Its source and interpretation gates were fixed before this successor corpus was acquired.
It may read the registered development fields already authorized for source 01; ancestor and
protected values remain unavailable. The replay is a fresh replication of descriptive process
signatures, not permission to tune thresholds or expose the protected block.

## Source 01 fresh replication result

Status: **SUCCEEDED — EXPLORATORY CHRONOLOGICAL REPLICATION**.

- Exact [`01_fresh_process_signatures.json`](development-receipts/01_fresh_process_signatures.json)
  SHA-256: `d6d652b20d9458e6472e0d8dddf48aaa6e27946e268bd802580961d9e9972f57`.
- Coverage: 29 fresh events, 147 markets, and 42,549 observations; zero chronology or lifecycle
  violations were recorded.
- Regular interior zero rate was `0.44850`, regular increment kurtosis was `55.01`, and the
  24-hour variance ratio was `0.23029`. Both frozen signature checks again rejected a smooth
  continuous diffusion description.
- Next-sample move probability fell from `0.73680` immediately after a move to `0.02080` after
  at least 24 unchanged observations, again questioning a memoryless constant-intensity clock.
- Next-sample persistence was `0.98159` at the low boundary and `0.99121` at the high boundary.
- The later cohort was less stale than the first development cohort: regular interior zero mass
  was `0.44850` versus `0.62398`. This is retained as cross-cohort heterogeneity, while the
  qualitative process discrimination replicated.
- Protected values remained unexposed.

The next successor experiment is fixed as an unchanged replay of source 02 on the same 29 fresh
events. It will apply the existing weighting, chronological-half, daily-drift, fixed-horizon, and
calibration diagnostics without changing a threshold or source byte. This tests whether the
earlier negative-drift and broad-overpricing diagnostics replicate; failure is retained and does
not permit post-result semantic filtering.

## Source 02 fresh replication result

Status: **SUCCEEDED — EXPLORATORY REPLICATION WITH COVERAGE LIMITS**.

- Exact [`02_drift_composition_falsifier.json`](development-receipts/02_drift_composition_falsifier.json)
  SHA-256: `401a4731e9cf523cf63f8fbf3158e037581e097f2f9cd21ddf298dff436f5a57`.
- Regular-hour event-equal drift was `-0.0012374`, with `-0.0014008` in the first chronological
  half and `-0.0010850` in the second. Non-overlapping daily event-equal drift was `-0.029996`.
  The frozen negative-drift composition check passed.
- Market/event-macro probability-minus-outcome gaps were `1.56%`/`0.56%` at 24 hours,
  `2.82%`/`5.52%` at 72 hours, `15.67%`/`15.04%` at 168 hours, and `4.79%`/`8.86%` at 336 hours.
  The frozen broad-overpricing gate passed at three of four horizons under both weightings.
- The 24-hour horizon did not reach the two-point gate. The 336-hour result contains only 27
  markets across 7 events, so it is weak coverage rather than a stable magnitude estimate.
- The later cohort's negative drift is larger than in the earlier development cohort, while its
  24-hour calibration gap is smaller. This heterogeneity makes semantic, chronological-regime,
  cluster-uncertainty, and executable-price rivals mandatory before any market-inefficiency claim.
- Protected values remained unexposed. These sampled probabilities do not establish executable
  returns after spreads, fees, latency, or market impact.

## Predeclared semantic-composition replication

Source 08 was authored and executed on the earlier development cohort before successor questions
were inspected. It is fixed for an unchanged replay on the 29 fresh successor events. The five
question-text categories, their precedence, all process/calibration calculations, and the rule that
sparse cells remain sparse cannot change. This replay asks whether category-stable sticky dynamics,
broad negative drift, and category-heterogeneous calibration extend to the later cohort. It does
not authorize ancestor or protected access and cannot convert a coarse text category into a causal
topic claim.
