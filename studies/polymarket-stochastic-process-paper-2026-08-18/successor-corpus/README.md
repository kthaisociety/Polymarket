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

The exact ancestor/fresh/protected composition must be established through the existing replication
boundary before any new value is read.
