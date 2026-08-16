# Git

> General conventions for commits and pull requests.

## Commits

- Use terse, imperative subjects in the repository's established style.
- Do not add AI watermarks or generated-by notices.
- Keep each commit coherent and reviewable.
- Order commits so each one leaves the tree internally consistent where practical.
- Explain important rationale and tradeoffs in the commit body.

Examples:

```text
Add dataset boundary validation
Record autonomous episode transitions
```

## Pull requests

- Keep the description aligned with what is actually on the branch.
- State the problem, important decisions, verification performed, and known limitations.
- Link the governing specification or issue when one exists.
- Do not add AI watermarks.

## Validation

Run the repository's documented full validation gate before publishing changes. Do not copy commands
from another project into this guide.
