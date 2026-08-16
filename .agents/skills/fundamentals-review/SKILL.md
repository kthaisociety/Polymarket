---
name: fundamentals-review
description: Independently critique one provisional Insurance architectural seam contract against the repository's locked fundamentals, authority hierarchy, canonical vocabulary, creativity gradient, failure semantics, and mutation-sensitive test standard. Use after seam-review produces a provisional contract and before grill-with-docs or human arbitration. Do not use to design, lock, reconcile, implement, or edit seams.
---

# Fundamentals Review

Act as an independent critic, not an architect. Ask whether the proposed `f: A -> B` is consistent with the project that already exists. Never improve the contract by silently choosing new semantics.

## Position in the workflow

```text
seam-review
  -> provisional seam contract
  -> fundamentals-review
  -> grill-with-docs
  -> reconcile non-semantic defects
  -> human arbitration for semantic choices or conflicts
```

This review is advisory. It cannot mark a seam `LOCKED`, edit the seam register, modify a canonical contract, or authorize implementation.

## Required input

Require one seam only:

- seam ID and the exact `SEAM_REGISTER.md` row;
- provisional contract path or complete provisional contract;
- risk classification;
- directly cited authoritative sources.

If the provisional contract is missing, do not design it. Return `USER_DECISION_REQUIRED` with the missing input.

## Establish authority

1. Read repository instructions and the authority/precedence rules in `AGENTS.md` and `docs/specification/ALIGNMENT_AND_DIAGRAMS.md`.
2. Read `references/project-fundamentals.md` completely.
3. Read the exact register row and provisional contract completely.
4. Follow only the directly relevant authoritative links. Consult `CONTEXT.md` for canonical terms and their linked authoritative homes.
5. Distinguish locked decisions from deferred implementation choices, examples, diagrams, and explanations.
6. If authoritative sources conflict, cite both and stop semantic reconciliation. The verdict is `ARCHITECTURE_CONFLICT` or `USER_DECISION_REQUIRED`, never a reviewer-invented compromise.

## Review method

### Reconstruct the proposition

State in one sentence what the seam claims to prove: source `A`, destination `B`, transformation `f`, and the observable consequence. Do not restate boxes without the arrow's meaning.

### Check project consistency

Test the provisional contract against:

- canonical identity, terminology, and source-of-truth ownership;
- information, provenance, temporal, and epistemic boundaries;
- authority to request, validate, execute, mutate, persist, expose, or promote;
- allowed and forbidden state changes, including failure paths;
- explicit failure meaning and absence of silent fallback;
- provider neutrality and reconstructability where applicable;
- preservation of loops, current/superseded state, evidence, and drill-down;
- the creativity gradient below;
- complexity justified by a named concrete failure.

Do not demand every project invariant from every seam. Cite only constraints that actually govern this arrow.

### Enforce the creativity gradient

Review restrictions according to where the seam sits:

```text
exploration: broad reasoning and computational creativity
formalization: explicit identity, legality, provenance, and reproducibility
protected evaluation/promotion: frozen meaning and strict privileged gates
```

Flag early narrowing that protects no information, side-effect, identity, or evidence boundary. Also flag late permissiveness that lets exploratory freedom bypass formal or protected gates. The project constrains information and side effects, not scientific imagination.

### Attack false success

Name the weakest plausible competent implementation that could satisfy superficial assertions while violating the contract. Prefer deletion, substitution, stale/latest lookup, forged authority, hidden side channels, partial mutation, silent fallback, or opaque-reference attacks.

For a HIGH-risk seam, require at least one named violating mutation and a test that definitely becomes red. A test that proves only `A happened, then B happened` is insufficient when the claim is that information from `A` influenced or constrained `B`.

For information-carrying seams, prefer a paired intervention:

```text
A1 != A2
A1 -> B1
A2 -> B2
B1 != B2
```

Prevent `B` and its test actor from reading `A` through another path. Classify agent evidence honestly as grader-only, scripted sequence, deterministic context-sensitive behavior, or real-model behavioral evidence. Do not demand a real model when the proposition is deterministic boundary behavior.

### Respect seam scope

Flag a missing composite dependency, but do not force the local seam to implement its neighbor. Distinguish a local contract defect, a required composite test/dependency, an intentionally deferred implementation choice, and a genuine architecture decision.

## Verdicts

Use only these verdict labels:

- `CONSISTENT` — no material conflict or test weakness found.
- `CONCERN` — a concrete non-blocking ambiguity, scope leak, unjustified restriction, or insufficiently supported complexity exists.
- `ARCHITECTURE_CONFLICT` — the proposal contradicts a locked source, or authoritative sources contradict each other.
- `USER_DECISION_REQUIRED` — more than one legitimate semantic meaning remains and the owner must choose.
- `TEST_INSUFFICIENT` — the proposed evidence can remain green under a plausible violating implementation.

One review may contain multiple labeled findings. Select the overall verdict by the most consequential unresolved finding; do not invent other verdict vocabulary.

## Output

Read `references/review-template.md` and use it exactly enough that another reviewer can compare results. Every non-`CONSISTENT` finding must include:

- exact source citation by repository path and section/invariant;
- the challenged contract claim;
- concrete counterexample or mutation;
- practical consequence;
- whether resolution is non-semantic reconciliation or human arbitration.

End by naming what this review did not prove. Do not edit any reviewed source during calibration or review.

## Stop conditions

Stop rather than guess when the authority order is unclear, canonical terms conflict, a material failure behavior is undecided, a beneficiary's approval authority is ambiguous, a HIGH-risk test cannot establish causality, or resolving the finding would change scientific meaning.
