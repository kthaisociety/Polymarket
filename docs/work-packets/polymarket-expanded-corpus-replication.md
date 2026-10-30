# Work packet: expanded Polymarket corpus for fresh replication

## Identity

- Packet: `polymarket.acquire-expanded-corpus-for-replication`.
- Predeclaration checkpoint: `historical checkpoint d1f5cabb`.
- Live boundary: existing Chronos repeatable-read `human_ro` corpus snapshot command.
- Fixed as-of time: `2026-08-17T21:00:00+00:00`.

## Objective

Acquire a larger immutable cohort of currently retained resolved Polymarket contracts so the exact
post-jump reversal lead can later be replicated on chronologically later event groups rather than
retuned on the original 31-event corpus.

This transition acquires and registers data only. It does not inspect post-jump labels, fit a model,
evaluate the prior rule, expose a protected partition, or create scientific evidence.

## Fixed selection

- binary resolved contracts with authoritative event identity;
- declared open/close lifecycle and settlement no earlier than declared close;
- YES outcome index `0` at fidelity `60`;
- at least 24 retained probability points by the fixed as-of time;
- deterministic resolution/event/market order;
- maximum 1,000 markets;
- exact canonical bytes retained under the ignored local corpus object store.

The command must prove role `human_ro`, default and transaction read-only settings, denied
insert/update privileges, and repeatable-read isolation before retaining bytes. The sanitized
receipt may contain only identities, counts, time bounds, availability rules, and caveats—never a
DSN or credential.

## Decision rule after acquisition

- If the result contains no contracts beyond the original 200/31-event snapshot, retain the data
  result and do not claim a fresh confirmation set.
- If later events exist, compare only immutable contract/event identities and chronology first.
  Before reading any new post-jump outcomes, predeclare an exact old-corpus training ancestry, a
  later-event development-confirmation block, a final whole-event protected block, and the frozen
  reversal feature/model/trade rule.
- No result from the original development study may set a threshold, feature, or gate after new
  values are read.

## Logging

Retain the sanitized snapshot receipt, exact snapshot content hash/size, command selection,
read-only proof, contract/event/price counts, and acquisition caveats. Repository documentation may
refer to the ignored object by content identity. The object bytes and all credentials stay outside
Git.

## Acquisition receipt

- Status: **SUCCEEDED — REGISTERED DATA, NOT SCIENTIFIC EVIDENCE**.
- Snapshot:
  `polymarket-corpus:8c73260377ea5cb3e569bbc3c744ce9b62a95c8f54dafb73d07671845ccec4c6`,
  318,684,407 canonical bytes.
- Sanitized receipt SHA-256:
  `1d68857a24188c6767df27352794dd390e81f5cea119cdf4436cdbcbc4876a4f`.
- Coverage: 1,000 contracts, 235 events, 1,180,437 price observations, 1,000 resolution
  observations.
- Authority: `human_ro`, default/transaction read-only true, repeatable-read isolation; no
  credentials emitted or stored.
- Formal references/durable effects: empty.

The identity/chronology audit exposed a concrete authority defect: the ordinary expanded 80/20
partition would place events from the original sealed block inside development. The bounded repair
is recorded in
[`polymarket-fresh-replication-boundary.md`](polymarket-fresh-replication-boundary.md). Its
fresh-replication view excludes every original-corpus event as well as the expanded final block
before any authored study can read values.
