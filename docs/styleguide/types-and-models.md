# Types and value objects

> General conventions for making domain meaning explicit in Python.

## Annotate public and internal contracts

Annotate function signatures and meaningful attributes. Avoid `Any` in project-owned interfaces.
Use `object` for a value whose shape is genuinely unknown, then validate it at the boundary.

The configured type checker determines which rules are mechanically enforced.

## Test optional values explicitly

Use `is None` and `is not None` when testing presence. Truthiness conflates absence with valid
falsy values such as zero, an empty string, or an empty collection.

Use truthiness only when emptiness itself is the intended condition.

## Prefer immutable value objects

Use immutable, slotted dataclasses or another explicit immutable representation for domain values
when identity and mutation are unnecessary.

Keep value objects focused on meaning and validation. Put operational behavior and infrastructure
access in services or adapters.

## Defaults must carry meaning

A default is appropriate only when it is part of the domain or configuration contract. Do not use a
default merely to make construction easier because that hides where the value came from.

An optional field may default to `None` when `None` has the explicit meaning of absence.

## Declare state clearly

For stateful classes, make instance attributes and their types easy to find. Mark attributes that
are assigned once as final when supported. Avoid adding state dynamically in unrelated methods.

## Units are semantic

Represent time, money, probabilities, identifiers, and other units with types that preserve their
meaning. Convert raw numbers and strings once at external boundaries.

Do not make readers infer a unit from arithmetic or from inconsistent suffixes.

## Closed sets use closed types

Represent a fixed set of values with a `Literal`, enum, or validated value type rather than a bare
string plus a comment. Define the set once and reuse it across contracts.

## Casts are a boundary tool

Avoid casts when validation or a better interface can express the truth. If an untyped dependency
requires a cast, keep it at the adapter boundary and explain why the checker cannot see the type.

## Errors follow the error contract

Expected failures use the explicit mechanism selected by the architecture. See
[error-handling.md](error-handling.md). This guide deliberately does not prescribe a legacy
`Status` or `StatusOr` implementation.
