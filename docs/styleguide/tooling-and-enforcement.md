# Tooling and enforcement

> General conventions for automated quality gates and suppressions.

## Repository configuration is authoritative

A rule is `[enforced]` only when a committed tool or local check verifies it. A rule that depends on
review is `[convention]`.

Do not claim that a formatter, linter, type checker, test runner, package manager, CI job, or
documentation generator exists until it is configured in this repository.

## Provide one full validation command

Once the toolchain is chosen, document one command that runs the complete local gate. CI should run
the same checks or their exact equivalents.

Keep formatting, linting, typing, tests, and project-specific invariant checks reproducible from a
clean checkout.

## Fix findings at the source

Prefer correcting the code over suppressing a diagnostic. A necessary suppression must:

- Name the exact diagnostic.
- Be limited to the smallest useful scope.
- Include a brief reason.
- Fail or become visible when it is no longer needed, where tooling supports that.

Never add blanket ignore rules to make a failing gate pass.

## Track deferred work

A TODO must point to the repository's configured issue tracker or durable planning artifact. Do not
hard-code GitHub issue syntax until GitHub is selected as the tracker.

## Generated files name their owner

Do not hand-edit generated artifacts. Document the generating command and source beside the artifact
or in the relevant README. The generation check becomes part of the full gate once it exists.

## Use the selected environment consistently

Run project commands through the environment and package manager selected by the repository. Avoid
mixing host and project runtimes. For this workspace, command execution follows the root
`AGENTS.md` and uses Ubuntu under WSL.
