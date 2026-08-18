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
