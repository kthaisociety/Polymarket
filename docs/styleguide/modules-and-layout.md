# Modules and layout

> General conventions for package boundaries, imports, constants, and file layout.

## Organize by responsibility

A module should have one coherent reason to change. Group code by domain responsibility rather than
by incidental framework mechanism when that makes ownership clearer.

The architecture documents define the actual package map. Do not copy a package layout from another
project into this guide.

## Dependencies point toward stable contracts

Higher-level orchestration may depend on lower-level domain contracts. Domain code must not depend on
UI, provider, deployment, or composition details.

Keep dependency direction explicit and acyclic. If the repository adds an automated layering check,
its configuration becomes the executable source of truth.

## Keep composition at the edge

Construction and dependency wiring belong in a small composition boundary. Domain modules should
receive collaborators through explicit interfaces instead of importing concrete providers globally.

Provider-specific adapters implement project-owned contracts. They do not define the research
architecture.

## Put values with their owner

A type, constant, or rule belongs to the narrowest stable module that owns its meaning. Move it to a
shared location only when several modules genuinely share the same concept.

Do not duplicate shared values across modules. Repeated copies drift.

## Imports

- Prefer absolute imports from the configured application package root.
- Keep type-only imports out of runtime when the language and checker support it.
- Avoid import side effects.
- Do not add dependency exceptions merely to make a convenient import pass.

The project configuration will decide whether Python packages use regular or namespace packages.

## Constants

Place module constants near the imports and annotate them as immutable when the type system supports
that. Explain only non-obvious constraints.

## File headers

Add a legal or copyright header only when the repository has an actual license policy requiring it.
Never copy an organization name, proprietary notice, or year from another project.

## Dependencies

Declare dependencies in the repository's chosen package configuration. Keep development tooling
separate from runtime dependencies where the package manager supports that distinction. Do not
document an unchosen package manager as mandatory.
