# Polymarket research boundary

## Exact source and field meaning

- Production reads use the engine's public market-read surface under the proved `human_ro` role.
  The session and transaction must be read-only, and insert/update privileges must remain denied.
- A contract is identified by its exact market/condition identity. Human question text and an
  authoritative event/group identity are not currently present in the Chronos research view.
- The adapter registers taker-side fills. `trade_price` is the executed outcome-token price;
  `signed_trade_size` follows the adapter's declared aggressor convention; `outcome_index` selects
  the outcome token. Any YES-equivalent or complement mapping is an authored transformation whose
  assumptions and dimensions must be stated.
- `reference_time` and `available_at` currently both use `fill_time` only under the explicit
  `polymarket-onchain-block-inclusion/v1` public-chain observability rule. This does not establish
  collector receipt time, confirmation latency, or off-chain quote availability.

## Current red gates

- Contract close time is not resolution-availability time. Resolved payout metadata is not yet a
  legal historical label.
- Cursor bounds plus a source digest detect changed reads but do not reconstruct immutable prior
  database bytes. A protected study needs retained source bytes or an external snapshot identity.
- Event/group identity is unavailable. Related contracts cannot be treated as independent folds or
  replications, and grouped cross-validation cannot be claimed authoritative.
- The registered source is a fill tape, not historical top-of-book state. Transaction-price
  effects may be bid/ask bounce or aggressor-direction mechanics; a midpoint claim requires a
  separately registered legal quote source.

## Authority separation

- The researcher may choose questions, mappings, sampling, transforms, labels, features, models,
  and falsifiers.
- The adapter and harness own source authority, availability, exact identity, allowed fields,
  temporal views, actual access, execution bounds, and reproducibility.
- Development evidence is selection-exposed. Independent services alone may freeze, expose
  protected data, validate, promote, or write terminal question memory.

If a question depends on a red-gated fact, record the blocked prerequisite and choose a different
exploratory question rather than silently approximating it.
