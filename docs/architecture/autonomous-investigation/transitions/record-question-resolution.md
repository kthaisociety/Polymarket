# `investigation.record-question-resolution`

## Mapping

\[
f_{\text{investigation.record-question-resolution}}:
IssuedProtectedResolution \rightarrow QuestionMemoryRecord
\]

```mermaid
stateDiagram-v2
    [*] --> Open
    Open --> Open: exploratory or development evidence
    Open --> Open: protected access denied
    Open --> ResolvedFinding: issued protected finding
    Open --> ResolvedRejection: issued protected rejection
    ResolvedFinding --> ResolvedFinding: exact replay
    ResolvedRejection --> ResolvedRejection: exact replay
    ResolvedFinding --> Conflict: different terminal evidence
    ResolvedRejection --> Conflict: different terminal evidence
    ResolvedFinding --> NewQuestion: new catalog identity or explicit future reopen
    ResolvedRejection --> NewQuestion: new catalog identity or explicit future reopen
```

## Contract

- Only a resolution issued by the configured protected-resolution authority may be recorded.
- Findings and protected rejections are terminal; governance denials are not scientific answers.
- The record retains question, environment, exact catalog, development candidate/evidence,
  protected resolution, terminal evidence, reasons, and first resolution time.
- Exact replay preserves the original record and timestamp.
- The repeat guard uses normalized question text plus exact environment and catalog identity. It
  performs no fuzzy or nearest-neighbor lookup.
- Markdown/Mermaid views are generated from these records and cannot create or mutate them.

```mermaid
flowchart TD
    ISSUED["Authority-issued terminal record"] --> TX["SQLite FULL-synchronous transaction"]
    TX --> TRUTH["Durable structured truth"]
    TRUTH --> PAGE["Generated question Markdown"]
    TRUTH --> INDEX["Generated research index + Mermaid"]
    PAGE -.->|"edits have no authority"| TRUTH
    INDEX -.->|"edits have no authority"| TRUTH
    FAIL["Projection write fails"] --> TRUTH
    FAIL --> RETRY["Exact retry regenerates projections"]
```

## Remaining boundary

The local SQLite archive and deterministic Markdown projection are implemented. The archive is
single-machine and composition-owned; distributed durability, external identity attestation,
semantic search beyond explicit lineage, and cross-machine atomicity remain outside this transition.
Bounded exact-lineage future-context retrieval and explicit reopen declarations are implemented by
[`context.reconstruct-question-memory`](reconstruct-question-memory.md).
