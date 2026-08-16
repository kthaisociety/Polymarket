---
name: execute-work-packet
description: Scope, solve, validate, and close one bounded Insurance project problem while preserving global architectural context and recording a durable state handoff. Use for material implementation, refactoring, debugging, or architecture work that can be expressed as one semantic transition or similarly coherent responsibility, especially when an agent must work through a larger plan in successive verifiable boxes. Do not use for simple read-only questions or trivial local edits.
---

# Execute Work Packet

Turn one part of the evolving system into a bounded reasoning problem. Scope context without erasing it: keep global authority visible, load the owning block, and inspect adjacent context whenever the boundary proves incomplete.

## Open the box

1. Read `AGENTS.md` and its required authority sources.
2. Select one semantic transition or one comparably coherent responsibility. Do not bundle unrelated arrows merely because they share a milestone.
3. Read the owning architecture block's `README.md`, `transitions/README.md`, `IMPLEMENTATION.md`, and exact transition contract. Read adjacent contracts only when they govern an input, output, authority, or state effect.
4. Read [work-packet-template.md](references/work-packet-template.md) and state the packet before material edits.
5. Record the input repository state, objective, permitted change surface, invariants, failure modes, expected outputs, verification, and completion evidence.

Treat the boundary as a working hypothesis. If the task cannot be solved without omitted authority, state, or an adjacent contract, expand the packet explicitly and then lock it again. Never guess across a missing semantic boundary.

## Work inside the box

1. Inspect the current implementation and tests before choosing mechanics.
2. Add or confirm a failing test or eval for the named failure mode when the behavior is material.
3. Implement the smallest coherent change that satisfies the packet.
4. Preserve references to evidence outside model context; do not copy large evidence into prompts or convert observations directly into durable belief.
5. Record discovered facts, contradictions, and scope changes as they arise. Do not silently widen the task.

Keep three context layers distinct:

- **global:** mission, authority hierarchy, locked decisions, invariants, and canonical vocabulary;
- **block:** the owning diagram, local contracts, current implementation state, and adjacent interfaces;
- **packet:** the immediate objective, concrete files, tests, assumptions, and required evidence.

## Debug the boundary

Validate more than the happy-path return value. Inspect:

- exact inputs consumed and outputs produced;
- allowed and forbidden state mutations;
- provenance and identity preservation;
- temporal admissibility and protected-evidence exposure;
- retry, denial, and partial-failure behavior;
- compatibility with at least one upstream or downstream consumer when the component composes;
- whether the named violating mutation would turn the evidence red.

Use deterministic tests for deterministic propositions. Use behavioral evals only where correctness materially depends on model judgment. A passing endpoint test is insufficient when the contract claims that an input constrained the result.

## Close the box

1. Run the packet's local verification and the proportionate integration checks.
2. Review the diff against the governing architecture, not only the tests.
3. Read [transition-receipt-template.md](references/transition-receipt-template.md) and publish a concise receipt.
4. Update the owning block's `IMPLEMENTATION.md` when implementation status, verification commands, remaining reds, or code paths changed.
5. Preserve unresolved uncertainty and follow-up dependencies explicitly. Do not report the packet complete while required evidence is missing.

The receipt, committed artifacts, and canonical documentation carry knowledge forward. The model's hidden reasoning and raw transcript do not.

## Stop conditions

Stop and expose the issue when authoritative sources conflict, the transition lacks a contract needed to determine scientific meaning, the packet would grant its actor new authority, a protected boundary cannot be verified, or completing the work requires a material expansion beyond the requested scope.
