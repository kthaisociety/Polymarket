# `operator.render-research-library`

## Signature

```text
f : ExactExploratoryReceipt[] × CanonicalFinalizedReport[]
    -> ReadOnlyResearchLibrary
```

## Preconditions

- every exploratory source is bounded JSON under the configured research root;
- exploratory status, scientific authority, and validated-memory effect are explicit;
- finalized reports, when supported, resolve through canonical reporting authority rather than a
  caller-authored status field.

## Postconditions

- ongoing records retain their exact exploratory status, evidence, caveats, and provenance;
- only independently resolved canonical reports may enter the finalized collection;
- absence of a canonical resolver yields an honest empty finalized view;
- the projection produces no formal object, semantic commit, promotion, or memory effect;
- HTTP presentation exposes no state-changing method or arbitrary filesystem path.

## Failure semantics

- malformed or oversized receipts fail projection construction;
- an exploratory receipt that asserts validation, scientific authority, or a memory effect is
  rejected rather than displayed;
- unsupported paths return not found and mutation methods return method not allowed.

## Causal checks

- change `EXPLORATORY` to `VALIDATED` in a receipt: projection fails;
- claim a non-none validated memory effect: projection fails;
- submit a write request to the local server: no state changes and the request returns `405`;
- request a repository path outside the asset allow-list: the server returns `404`;
- remove the canonical finalized-report resolver: finalized research remains visibly empty.
