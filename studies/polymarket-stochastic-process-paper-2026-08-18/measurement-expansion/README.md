# Fixed five-minute CLOB measurement expansion

Epistemic status: **PREDECLARED ACQUISITION — NOT SCIENTIFIC EVIDENCE**.

Source 09 selected 10 development-only markets using event ordinals fixed before question, price,
or payout inspection. The `needs/` documents bind the exact retained YES outcome token, recorded
market/event identity, a window ending at recorded close and spanning at most seven days, and
five-minute fidelity. Each `need_id` is validated by the existing
`PolymarketPriceHistoryNeed.from_dict` boundary before any source proposal or fetch.

The official [Polymarket price-history documentation](https://docs.polymarket.com/api-reference/markets/get-prices-history)
was verified on 2026-08-18. It documents public `GET /prices-history`, the token asset ID supplied
through `market`, absolute `startTs`/`endTs`, minute fidelity, and timestamp/price response fields.
This documentation supports source identity and parsing only; it does not establish that returned
samples are trades, quotes, executable prices, or revision-complete history.

`acquire_fixed_clob_measurement.py` is frozen before any selected endpoint is contacted. For each
need it creates the bounded external-scout request, records one exact official candidate, and uses
the existing Chronos source-expansion adapter to refuse redirects, retain immutable response bytes,
derive the strict temporal envelope offline, and register observations. The aggregate receipt emits
only identities, count/time coverage, availability rules, and caveats. It continues after a failed
slice and retains the failure without substituting another market or window.

Acquisition success is registered data, not a process finding. A later authored analysis must fix
its five-minute estimands and comparison rules before reading registered sample values. Ancestor
and protected markets remain outside this expansion.

## First acquisition attempt

Status: **FAILED AT OFFLINE DERIVATION — NO SCIENTIFIC RESULT**.

All ten exact public HTTPS fetches succeeded and retained immutable JSON source objects of
approximately 36–56 KB. All ten subsequent transforms reached the generic workspace's 10-second
limit with `TRANSFORMATION_TIMEOUT`, so zero slices registered. The aggregate failed receipt is
retained as `acquisition-receipt.failed-transform-timeout.json` with SHA-256
`fe212f46b977a3332fd7dad8cd5c9131738abae8cbb9833d390951d814cfad2c`.

The failure matches the process-pipe defect already exposed in the analysis harness: the workspace
parent joined the transform worker before receiving its bounded derived envelope, allowing outputs
larger than the OS pipe buffer to deadlock. Chronos may make the same narrow receive-before-join
repair in `DataWorkspace.derive`. The source bytes, strict transform, needs, markets, windows, and
scientific design cannot change. A regression must pass with a derived message materially larger
than a typical pipe buffer before the identical acquisition is retried.

## Exact retry

Status: **ACQUISITION AND REGISTRATION SUCCEEDED — VALUES NOT YET ANALYZED**.

After the receive-before-join repair passed the complete 471-test suite, the identical ten needs
and exact candidates were replayed. All ten slices registered in 4.4 seconds, containing 19,258
five-minute sampled probabilities in total (1,378–2,001 per market). No production database write,
protected-data exposure, source substitution, or sample-value emission occurred. The value-free
receipt is `acquisition-receipt.json`, SHA-256
`eced7839e2db660e8ab2d94310df578bc4329124d3b12d2904f0ad4e82ebf54a`.

Registration success only establishes a governed measurement panel. The process estimands and
comparison rules must be frozen in authored source before the harness may read these values.
