# Codex Working Protocol

This document explains how to use Codex on this repository without losing the architecture in conversational context.

## 1. Repository instructions are durable context

The root `AGENTS.md` is intentionally concise. It tells Codex how to work and points to the deeper architecture/specification files.

Do not paste the entire architecture into every prompt. Instead, point Codex at the relevant files and contract.

When specialized implementation areas emerge, a nested `AGENTS.md` or `AGENTS.override.md` may be added close to that code if local rules genuinely differ. Do not create nested instruction files preemptively.

## 2. Prompt shape for implementation tasks

Use four elements:

```text
Goal
Context
Constraints
Done when
```

Example:

```text
Goal:
Implement the first InformationSet boundary.

Context:
Read SCIENTIFIC_KERNEL.md, INVARIANTS.md I1/I14/I24,
TEST_STRATEGY.md, and the relevant contract.

Constraints:
Do not infer admissibility from reference_time.
No future observation may be exposed.
Keep the implementation minimal.

Done when:
The contract/adversarial tests pass, including the publication-delay fixture,
and the diff has been reviewed against the invariants.
```

## 3. Plan before difficult changes

For multi-module, ambiguous, or architectural work, ask Codex to plan before coding.

The plan should identify:

- relevant architecture documents;
- touched components;
- invariants at risk;
- tests/evals to add;
- implementation steps;
- any architectural ambiguity that should be surfaced rather than guessed.

For routine low-risk plumbing, do not force a large planning ritual.

## 4. Test before/with implementation

For critical scientific/governance boundaries, the expected workflow is:

```text
contract / failure mode
→ test or eval
→ implementation
→ run verification
→ review
```

Codex may generate test code, but should not invent a weaker success criterion to make the task easy.

## 5. Review behavior

After a meaningful implementation unit:

1. run the relevant tests;
2. inspect failures rather than masking them;
3. review the diff against `INVARIANTS.md`;
4. check for new authority/data/evidence paths;
5. check that low-level design has not accidentally changed scientific meaning;
6. update the spec only when the implementation revealed a real architectural fact.

## 6. Keep AGENTS.md practical

Do not continuously add every discovered fact to `AGENTS.md`.

Add a rule when:

- it is repository-wide;
- Codex repeatedly makes the same class of mistake;
- it is important enough to be loaded automatically in most tasks.

Detailed scientific rules belong in the subsystem docs/invariants/tests.

## 7. Context is not the source of truth

Codex session continuity is useful but not authoritative.

Architectural decisions should be committed to repository docs/tests because:

- sessions can end;
- context can compact;
- different model/providers may work on the repo;
- Git should show when a scientific rule changed.

## 8. When to update these docs

Update the architecture docs when implementation demonstrates that:

- two conceptual objects are actually the same responsibility;
- a missing boundary creates a real failure mode;
- an invariant is underspecified;
- a new state/evidence transition is required;
- an existing abstraction cannot preserve the intended scientific semantics.

Do **not** update architecture merely because a local helper function/class name changed.

## 9. Verify Codex loaded repository instructions

Before the first implementation session, verify that Codex is actually reading the root instructions. Current Codex supports checking the active repository guidance, for example by asking it to summarize its current instructions from the repository root. If the summary does not include the critical rules from `AGENTS.md`, fix instruction discovery before coding.

`PLANS.md` is an explicit repository workflow/template referenced by these docs; `AGENTS.md` is the automatically discovered durable instruction layer.

## 10. Commands

The repository has no locked implementation toolchain at handoff time. After bootstrap selects the language/package/test stack, update root `AGENTS.md` with the canonical:

- setup/install command;
- deterministic test command;
- behavioral-eval command;
- lint/type-check command if used;
- minimal end-to-end demo command.

These commands should become the routine definition-of-done checks Codex can run itself.
