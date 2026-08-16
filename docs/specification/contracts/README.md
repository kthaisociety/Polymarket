# Critical Integration Contracts

Do not create exhaustive contracts for every internal function before implementation.

Create/maintain a contract here when the boundary is high-risk because a mistake could cause:

- scientifically invalid but plausible results;
- authority/protected-evidence bypass;
- corrupted durable state;
- lost provenance/identity;
- difficult cross-module inconsistency.

Each contract should cover:

```text
caller / callee
input/output conceptual types
responsibility
preconditions
permissions/authority
invariants
state effects
provenance
failure semantics
acceptance tests
```

Low-risk plumbing can be specified through ordinary code/tests unless it later proves architectural.
