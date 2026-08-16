# Style guide

> General conventions for how code and technical documentation are written in this repository.

The [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) is the baseline for
Python. These pages contain only project-wide additions that are independent of a particular product,
company, provider, package layout, or implementation plan.

Architecture and scientific design decisions belong in `docs/specification/`, not here.

## Rule labels

- `[enforced]`: A committed tool or check currently verifies the rule.
- `[convention]`: Reviewers and agents apply the rule, but no automated check currently verifies it.

Do not label a rule enforced until its check exists in this repository. The repository's configured
tooling is always the executable source of truth.

## Contents

| Page | Topic |
|---|---|
| [naming.md](naming.md) | Names for variables, parameters, functions, and types |
| [docstrings.md](docstrings.md) | Docstring style and useful content |
| [comments.md](comments.md) | Why-focused comments and tracked TODOs |
| [functions.md](functions.md) | Flat functions and orchestration-level callers |
| [modules-and-layout.md](modules-and-layout.md) | General package boundaries and imports |
| [module-readmes.md](module-readmes.md) | Lightweight subsystem documentation |
| [types-and-models.md](types-and-models.md) | Types, value objects, optionals, and units |
| [error-handling.md](error-handling.md) | Failure classification and containment |
| [tests.md](tests.md) | Test ownership, seams, scopes, and reproducibility |
| [config-and-data.md](config-and-data.md) | Configuration, secrets, and data boundaries |
| [tooling-and-enforcement.md](tooling-and-enforcement.md) | Quality gates and suppressions |
| [git.md](git.md) | Commits and pull requests |
