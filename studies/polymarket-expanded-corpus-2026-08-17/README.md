# Expanded Polymarket replication corpus

Epistemic status: **PREDECLARED DATA ACQUISITION — NOT SCIENTIFIC EVIDENCE**.

This study entry records one fixed read-only production snapshot request for up to 1,000 resolved
binary Polymarket contracts as of `2026-08-17T21:00:00+00:00`, with at least 24 retained YES-price
samples at fidelity 60.

Its purpose is to obtain chronologically later contracts for a clean replication of the internal
post-jump reversal lead. The acquisition receipt exposes aggregate metadata only. No new price path
or outcome is inspected until a separate replication design is fixed.

See the [work packet](../../docs/work-packets/polymarket-expanded-corpus-replication.md).

## Acquisition result

The public snapshot command succeeded through the approved production boundary:

- role `human_ro`, default and transaction read-only, repeatable-read isolation;
- 1,000 resolved contracts across 235 server-recorded event groups;
- 1,180,437 registered probability observations and 1,000 resolution observations;
- immutable snapshot
  `polymarket-corpus:8c73260377ea5cb3e569bbc3c744ce9b62a95c8f54dafb73d07671845ccec4c6`;
- canonical object size 318,684,407 bytes, retained only under the ignored local corpus store;
- sanitized receipt SHA-256
  `1d68857a24188c6767df27352794dd390e81f5cea119cdf4436cdbcbc4876a4f`;
- formal references and durable state effects empty.

The previous corpus had 200 contracts/31 events, so the expanded snapshot has enough aggregate
coverage for a later-event replication. This remains registered data, not scientific evidence.
Only identity/chronology auditing is authorized before the replication design is frozen.
