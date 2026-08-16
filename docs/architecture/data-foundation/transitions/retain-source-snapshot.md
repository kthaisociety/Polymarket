# data.retain-source-snapshot — bounded HTTP request → verified `SourceSnapshotRef`

## Status

`CANDIDATE_CONSENSUS` — local source-agnostic implementation, not a production durability claim.

## Architectural purpose

Acquire a caller-selected HTTP resource through the only network-enabled data-workspace operation,
retain the exact response bytes under immutable content identity, publish an append-only manifest,
verify both, and only then return a value-free `SourceSnapshotRef`.

## Contract

- **Source:** explicit bounded HTTP/HTTPS request plus secrets supplied only to acquisition.
- **Destination:** a verified ref binding exact request digest, response content digest, and byte
  size; failures return a sanitized receipt and no ref.
- **Must preserve:** exact response bytes, request/content distinction, response media type,
  path-independent identity, and first successful retention record.
- **Must exclude:** response previews, secret header/body/query values, inferred schema, availability
  rules, scientific registration, protected status, field meaning, and model-authored authority.
- **State effect:** append an immutable content object and source manifest, or a sanitized failed
  attempt receipt. Publication is exact-retry idempotent and concurrent-safe.

The local catalog is a reconstructible projection over manifests. It is never authoritative.
Moving the workspace cannot change a reference; changing the request or bytes cannot reuse one.

## Failure semantics

Unsupported scheme/redirect, timeout, response-size overflow, transport failure, non-regular store
entry, integrity mismatch, or publication conflict fails explicitly and returns no healthy ref.
Exact bytes may exist as an unreachable orphan after an interrupted publish, but no scientific
consumer can resolve them without a verified manifest.

## Falsifying tests

Two structurally different loopback HTTP APIs use the same request path; response mutation turns
verification red; exact concurrent retry yields one ref/manifest; moved paths retain identity;
credentials and request bodies are absent from refs, manifests, and public diagnostics.

This transition performs acquisition, not external source discovery. The separate
[`data.propose-source-candidates`](propose-source-candidates.md) transition may retain unverified
URL proposals before this boundary, but it cannot call acquisition until one exact issued candidate
is explicitly selected.
