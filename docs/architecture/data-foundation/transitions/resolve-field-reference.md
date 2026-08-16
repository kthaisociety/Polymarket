# data.resolve-field-reference — stable FieldRef → exact DatasetSchema field and physical values

## Status

`CANDIDATE_CONSENSUS` — experimental, not canonical.

## Architectural purpose

Resolve a scientific field reference to its exact versioned semantic definition and values without letting physical paths, friendly names, column positions, or newer schemas silently change meaning.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I1, I13, I16, I24.
- `docs/specification/DECISIONS.md`, Dataset/feature ontology.
- `docs/specification/SCIENTIFIC_KERNEL.md`, Dataset semantics.

## Source A

A stable `FieldRef` carrying dataset/field identity and required schema/version constraints, plus an exact environment/catalog snapshot and current permission context.

## Destination B

The exact `DatasetSchema` field semantics and authorized physical value binding, with units/type/dimensions/time semantics/version/provenance/status—or explicit resolution failure.

## Mapping f

Resolve identity through the named snapshot/versioned registry; verify semantic/physical binding and permission; expose exact definition and view. Never search by similarity or substitute latest/nearby fields.

## Must preserve

Dataset, field, schema and environment versions; semantic definition; units/type/dimensions; reference/availability roles; vintage/provenance; current/superseded status; and authorized physical binding.

## May transform

Registry representation into an authorized typed field/view; physical location may change if the stable binding/version and values remain exact.

## Must exclude

Friendly-name or position substitution, latest-schema upgrade, cross-dataset collision, unit coercion, unauthorized values, unresolved ref treated as empty field, and path identity treated as scientific identity.

## Authority boundary

Registry/environment own binding truth; resolver reads and verifies. It cannot alter schema, grant access, or choose a scientifically “close enough” field.

## Allowed state mutation

Bounded resolution/access observability only.

## Forbidden state mutation

No schema/data/ref rewrite, permission/exposure change, registration, feature/target mutation, or scientific conclusion.

## Failure semantics

Missing, ambiguous, version-mismatched, corrupt, superseded-without-explicit-selection, or unauthorized reference fails explicitly. Explicit historical refs may resolve with status visible. No empty/default/latest/nearby fallback.

## Observable consequences

Reordering physical columns or adding same-name fields does not alter an exact ref. Introducing a newer schema does not rebind historical refs.

## False-success implementations considered

- Resolve by column name/position.
- Always select latest schema.
- Return empty values on missing ref.
- Convert units silently.
- Read before permission check.

## Falsifying tests

1. Two datasets/schemas contain the same friendly name but different meanings; exact `FieldRef` selects only its target and no global search. **Level A/B.**
2. Reorder physical storage/add newer schema and assert historical exact binding unchanged.
3. Missing/ambiguous/unauthorized refs fail with zero forbidden reads and no empty-success fallback.
4. Verify units/time/vintage semantics cross with values, not only field ID.

## Mutation-sensitivity check

**Mutation:** resolve by friendly column name against the latest schema.

**Expected failure:** tests 1–2 become red through wrong dataset/version/meaning.

## Composite dependencies

data.register-observations registers bindings; data.build-information-set builds legal views; target.define-outcome targets and feature.define-identity/feature.compile-definition features depend on exact refs.

## Fundamentals review

`CONSISTENT`. Stable semantic identity survives physical change and currentness remains explicit.

## Grill findings

Resolved non-semantically: required substantive field semantics and historical status, not merely matching IDs.

## Remaining user decisions

None. Registry indexing and physical locator representation remain free.
