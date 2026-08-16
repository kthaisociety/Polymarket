# Automated evaluation-specification experiment

Status: experimental, downstream of architecture and seam contracts.

This experiment derives L3 deterministic composite tests and L4 behavioral eval families, then
builds production-facing verification infrastructure. It does not modify canonical architecture or
canonical seams. Proof adapters may call production application code, but evaluator fixtures do not
replace the mechanisms under test.

## Authority

Every verification assertion must cite a locked invariant/decision and/or a seam contract. Candidate action.authorize-request–learning.influence-future-research contracts remain provisional supporting detail. An untraceable expectation is `ARCHITECTURE_GAP`, never an implicit architecture change.

## Layers

- L1: unit/invariant test.
- L2: local seam test.
- L3: deterministic composition proving propagation across seams.
- L4: real-model behavioral eval for open-ended scientific judgment.

Exact correctness uses deterministic tests. Model judgment uses scenario families with hidden truth, objective graders where possible, and narrowly bounded semantic judgment only when needed.

## Batch review record

Each major batch refreshes the current instructions from disk and records:

- system-eval-design: applied
- fundamentals-review: applied
- grill-with-docs: applied

Experimental outputs are candidates, not `LOCKED` specifications.
