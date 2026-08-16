# Comments

> General convention: comments explain intent that the code cannot express on its own.

## Comment why, not what

The code already states what it does. Add a comment only for a non-obvious reason, constraint,
workaround, provenance requirement, or safety condition.

Place longer explanations above the relevant code. Keep short constraint notes beside a declaration
only when they remain readable.

```python
_MAX_CONTEXT_ITEMS: Final[int] = 50  # the provider request has a fixed context budget
```

## File headers describe purpose

A brief file header may explain why a file exists or what boundary it owns. Do not enumerate every
function or narrate implementation mechanics that will drift.

## Write for the future

Describe an enduring constraint or intent, not a snapshot of the current implementation. If the
explanation becomes false after a normal refactor, it probably belongs in a commit or design record.

## Keep code comments portable

Use ASCII in code comments and docstrings unless the project explicitly adopts a different rule.
Unicode is fine in Markdown documentation.

## TODOs are tracked work

A TODO must link to the repository's configured issue tracker or durable planning artifact. State
what remains and the condition that makes it actionable.

Do not assume GitHub syntax until GitHub has been chosen as the tracker.

## History belongs in version control

Alternatives, review discussion, and the history of why a change was made belong in the commit,
issue, or decision record. Keep source comments focused on constraints a future maintainer still
needs while reading the code.
