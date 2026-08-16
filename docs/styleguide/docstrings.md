# Docstrings

> Python docstrings follow the Google style unless repository tooling defines a stricter rule.

## One line for simple behavior

Use a single-line docstring when the complete contract fits naturally on one line.

```python
def open_read_only_store() -> ArtifactStore:
    """Open the artifact store in read-only mode."""
```

## Full sections for non-trivial contracts

Use a summary followed by `Args:`, `Returns:`, and `Raises:` when the function has meaningful
inputs, outcomes, side effects, or failure behavior.

```python
def normalize_weights(weights: Sequence[float]) -> list[float]:
    """Return weights scaled to sum to one.

    Args:
        weights: Non-negative values with a positive total.

    Returns:
        A new list whose values sum to one.

    Raises:
        ValueError: If a value is negative or the total is zero.
    """
```

## Types live in signatures

Do not repeat type annotations in prose. Use the docstring for meaning, units, constraints, side
effects, and behavior that the signature cannot communicate.

## Document public contracts

Public modules, classes, and non-trivial public functions need docstrings. Private helpers need one
when their purpose or constraints are not obvious from their name and implementation.

The configured linter and docstring checker determine which cases are mechanically enforced.
