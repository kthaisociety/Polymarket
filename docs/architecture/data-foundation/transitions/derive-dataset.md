# data.derive-dataset — verified refs + authored code → verified `DerivedDatasetRef`

## Status

`CANDIDATE_CONSENSUS` — bounded local exploratory transformation.

## Architectural purpose

Let a researcher author parsing and transformation logic without granting that code network,
filesystem, process, environment, secret, catalog, state, formalization, or promotion authority.

## Contract

- **Source:** named exact verified source/derived refs, exact authored Python, finite JSON
  parameters, runtime profile, and resource limits.
- **Destination:** canonical JSON bytes plus a `DerivedDatasetRef` binding alias-to-input refs,
  authored-code hash, exact parameter hash, runtime identity, output hash, and byte size.
- **May transform:** arbitrary logic expressible through the bounded language, including generic
  UTF-8, JSON, CSV, and byte access helpers.
- **Must exclude:** unretained/model-authored input values, network/filesystem/process access,
  imports, unrestricted catalog handles, scientific conclusions, formal objects, protected
  evidence, and durable state effects.

Authored code runs in a fresh resource-bounded spawned worker with the same syntax/call-surface approach as
the current `ResearchSandbox`. The parent resolves and verifies inputs before worker creation. The
worker receives bytes only, records actual alias reads, emits finite canonical JSON only, and cannot
publish directly. At least one verified input is required and every declared input must actually be
read. Failed, denied, timed-out, or oversized transformations record a sanitized attempt and return
no ref.

A verified derived JSON object of column arrays can be adapted into the existing
`AuthorizedDataView`; caller-minted or unhealthy refs fail before values are decoded. This adapter
does not register observations, infer schema/availability, or grant protected/scientific authority.

## Falsifying tests

Changing only parser source creates a different ref; code/input/output lineage round-trips after
restart; `open`, imports, dynamic host calls, and network constructors are denied; corrupt output
fails verification; a fabricated ref cannot become a view.

This local worker is not production-grade hostile multi-tenant containment and does not yet expose
NumPy/pandas. A stronger isolated runtime is required before expanding that library surface.
