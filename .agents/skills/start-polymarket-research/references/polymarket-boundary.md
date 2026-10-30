# Polymarket research boundary

## Exact source and field meaning

- Production reads use the standalone adapter's bounded parameterized SELECTs under the proved
  `human_ro` role. The session and transaction must be read-only, and insert/update privileges must
  remain denied.
- The fill view identifies a contract by exact market/condition identity but has no event grouping.
  The retained resolution corpus additionally preserves server `event_id`, question, lifecycle,
  sampled price path, and append-only settlement identity.
- The adapter registers taker-side fills. `trade_price` is the executed outcome-token price;
  `signed_trade_size` follows the adapter's declared aggressor convention; `outcome_index` selects
  the outcome token. Any YES-equivalent or complement mapping is an authored transformation whose
  assumptions and dimensions must be stated.
- `reference_time` and `available_at` currently both use `fill_time` only under the explicit
  `polymarket-onchain-block-inclusion/v1` public-chain observability rule. This does not establish
  collector receipt time, confirmation latency, or off-chain quote availability.

## Path-specific gates

- On the fill-only path, close time is not resolution availability, cursor bounds are not immutable
  bytes, and event grouping remains unavailable. Do not use that path for resolution labels or
  independent cross-contract folds.
- The resolved-corpus path closes those gates only for its exact content-addressed object: labels
  become available at recorded `resolved_time`, and folds may group by retained server `event_id`.
  A different live read does not inherit that identity.
- The registered source is a fill tape, not historical top-of-book state. Transaction-price
  effects may be bid/ask bounce or aggressor-direction mechanics; a midpoint claim requires a
  separately registered legal quote source.
- Historical `price_series` values are sampled probabilities, not guaranteed executable quotes.
  Costs, spread, and order-book execution claims require a separately retained legal source.

## Authority separation

- The researcher may choose questions, mappings, sampling, transforms, labels, features, models,
  and falsifiers.
- The adapter and harness own source authority, availability, exact identity, allowed fields,
  temporal views, actual access, execution bounds, and reproducibility.
- Development evidence is selection-exposed. Independent services alone may freeze, expose
  protected data, validate, promote, or write terminal question memory.

If a question depends on a red-gated fact, record the blocked prerequisite and choose a different
exploratory question rather than silently approximating it.
