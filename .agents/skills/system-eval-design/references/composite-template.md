# Composite deterministic-test template

## ID and classification

`Cxxx` — `DETERMINISTIC_COMPOSITE_TEST | ARCHITECTURE_GAP`

## System proposition

State `P(A) => Q(C)`.

## Composed path

Name source, intermediates, destination, and seam IDs.

## Architecture traceability

Cite each assertion to an exact invariant, decision, contract, or seam section.

## Deterministic oracle

State what the harness knows exactly and how it computes correctness.

## World and fixture construction

Define visible inputs, harness-only truth, isolation, identities, and versions.

## Expected outcome

State intermediate propagation and final result.

## Forbidden outcome

State forbidden access, mutation, substitution, leakage, evidence loss, or false success.

## Counterfactual

Vary the governing input while holding alternatives fixed.

## Dangerous false-success implementation

Name the weakest plausible endpoint-passing implementation.

## Violating mutation and expected red

Name the mutation and exact assertion it must fail.

## Risk and evidence level

State risk and why deterministic L3 evidence suffices.

## Review outcome

Record fundamentals/grill verdicts and unresolved gaps.
