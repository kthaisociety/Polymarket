# Module READMEs

> General conventions for package and subsystem README files.

## Purpose

A module README should quickly answer:

- Why the module exists.
- What responsibilities it owns.
- What it explicitly does not own.
- Which deeper design documents define its contracts.

Add a module README when a directory represents a meaningful subsystem and the code alone does not
make its boundary obvious. Do not create one merely to repeat filenames.

## Suggested structure

```text
# <module> - <short role>

<Why this module exists>

## Map

## <named flow or lifecycle section>

## Boundaries

## Deep dives
```

Use only the sections that add information.

- **Title:** Name the module and its role.
- **Why:** State the need before describing the mechanism.
- **Map:** Give each important file or submodule a one-line responsibility.
- **Flow:** Use a small Mermaid diagram when relationships are clearer visually.
- **Boundaries:** State what the module owns, what it may depend on, and who consumes it.
- **Deep dives:** Link to authoritative design documents instead of restating them.

## Diagram rules

Diagrams must render on GitHub:

- Use `flowchart`, `sequenceDiagram`, or `stateDiagram-v2`.
- Choose the diagram type that matches the relationship.
- Quote labels containing punctuation.
- Use `<br/>` for line breaks inside labels.
- Do not use `end` as a node identifier.
- Do not use click directives, hard-coded themes, or color styling.
- Draw only implemented relationships as solid facts. Mark planned paths clearly.

## Prose rules

- Prefer short declarative sentences.
- Prefer a table, list, or diagram when it communicates the structure better.
- Use plain language and avoid filler.
- Do not use emoji in technical documentation.
- Link to authoritative detail instead of copying it.

## Keep documentation honest

Verify wiring claims against the working tree. Distinguish current behavior from planned behavior.
Qualify names that could refer to several domain concepts. When a table mirrors code or configuration,
name its source of truth beside it.

Use the repository's documented validation command after editing generated or indexed documentation.
Do not claim a documentation generator exists until it is configured.
