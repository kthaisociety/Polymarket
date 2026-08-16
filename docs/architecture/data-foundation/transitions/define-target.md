# target.define-outcome — resolved task target/outcome semantics → TargetDefinition

## Status

`CANDIDATE_CONSENSUS` — experimental implied-gap contract, not canonical.

## Architectural purpose

Formalize resolved target meaning into a reproducible identity sufficient to construct labels and determine maturity, while refusing to invent precision from an intentionally broad or unresolved research task.

## Relevant locked invariants

- `docs/specification/INVARIANTS.md` I5, I10, I23–I24, I26.
- `docs/specification/SCIENTIFIC_KERNEL.md`, Target semantics.
- Canonical mission.confirm-task/mission.evolve-direction mission and rescope rules.

## Source A

Exact confirmed task/version and an explicit resolution record for target field/transformation,
decision-time population/cadence, exact elapsed-or-calendar horizon identity, outcome interval,
endpoint/path/event semantics, timestamp alignment, prediction type/encoding,
censoring/partial-outcome behavior, fixed or state-conditioned causal derivation rule and any
development-selection procedure, label completion/availability rule, geography/entity/dimensions,
environment/schema/field refs, rationale/provenance, and resolving authority. Calendar horizons
include anchor, month-end, timezone, and DST/fold behavior. Any remaining alternatives are explicit.

## Destination B

An immutable versioned `TargetDefinition` with stable semantic identity, exact field/transformation refs, decision population, horizon/outcome-path/alignment/prediction/maturity/censoring semantics, causal target-derivation and development-selection procedures, environment/schema provenance, parent lineage where revised, and applicability constraints.

## Mapping f

Verify resolution against the task's main goal/hard constraints and exact schema; take the target
horizon from the exact confirmed task rather than a second caller-supplied value; require every
dimension necessary for unambiguous label construction; preserve task identity,
assumptions/provenance; publish a new definition/version. If multiple legitimate meanings remain,
emit unresolved/user-decision outcome rather than a default definition.

## Must preserve

Task meaning/breadth, exact target/decision population/horizon/outcome interval/path/alignment/type/maturity/censoring/derivation/selection procedures, units/dimensions, field semantics, environment/schema version, assumptions, resolution authority, provenance, and lineage.

## May transform

Resolved prose/agenda conclusions into formal fields and a stable identity; equivalent representation is free.

## Must exclude

Default horizon/alignment/maturity/path/censoring, nearby field substitution, task rescope disguised as target resolution, current/latest schema rebinding, mutable in-place edits, learned values, full-history threshold/baseline choice hidden as predetermined, silent rare-label removal, and label construction itself.

## Authority boundary

The agent may investigate/propose target semantics within the confirmed task. The formalization boundary verifies exact resolved meaning and constraints; it cannot authorize task-level rescope. Genuine task-core change returns to mission.evolve-direction/human confirmation.

## Allowed state mutation

Create immutable target definition/version and provenance/lineage records; record unresolved outcome.

## Forbidden state mutation

No task rewrite, data/sample creation, model fitting, protected evidence access, or mutation of prior target definitions.

## Failure semantics

Missing/ambiguous material semantics, conflicting field/schema, or task-core divergence blocks definition. Alternatives and consequences remain visible as `USER_DECISION_REQUIRED` for that proposal. Meaning-changing repair creates a new candidate/version, never silent fallback.

## Observable consequences

Two resolved path/maturity/alignment/parameter rules produce distinct definition identities and later sample eligibility. An unresolved horizon cannot yield a seemingly complete target definition.

## False-success implementations considered

- Default to next-period horizon.
- Resolve target by friendly column name.
- Omit maturity rule and infer it in sample builder.
- Treat endpoint and path-dependent outcomes as the same target.
- Estimate a state-conditioned target threshold on the complete history.
- Drop a rare outcome class as infrastructure cleanup.
- Mutate definition after examining results.
- Treat subordinate formalization as permission to replace task goal.
- Replace a confirmed calendar quarter with 90 elapsed days because one anchor happens to agree.

## Falsifying tests

1. Pair definitions differing only in path, maturity, alignment, censoring, or target-parameter procedure; assert distinct identities and downstream eligibility semantics. **Level A/B.**
2. Omit each necessary semantic in turn; assert explicit unresolved/blocking outcome and no definition.
3. Introduce same-name nearby field/latest schema and assert exact ref preservation.
4. Attempt meaning-changing edit and assert new version/lineage, old definition unchanged.
5. Use a future-scale-shift fixture and assert that time-local target state cannot see beyond its
   example decision time and any data-selected rule/hyperparameters remain inside declared
   development folds with complete trial ancestry. **Level B.**
6. Run two structurally different task targets through the same transition implementation; assert
   no domain-specific branch or implicit label convention. **Level B.**
7. Bind a January 31 calendar-quarter task to a target, vary month-end/timezone identity, and try a
   90-day substitution; assert only the exact confirmed horizon publishes and downstream intervals
   retain calendar behavior. **Level A/B.**

## Mutation-sensitivity check

**Mutation:** omit path/maturity/derivation/selection procedure from identity and let sample construction infer defaults.

**Expected failure:** tests 1–2 and 5 become red because distinct legal label semantics collapse,
incomplete input publishes, or a data-derived target rule escapes its temporal/development boundary.

## Composite dependencies

mission.confirm-task/mission.evolve-direction govern task meaning; data.resolve-field-reference resolves fields; data.build-training-sample uses maturity/alignment; system.assemble-definition incorporates target identity; formalization.version-material-change versions material change.

## Fundamentals review

`CONSISTENT`. The implied mapping follows the locked target ontology and mission-drift rule. The contract does not choose target semantics; it blocks and queues any instance with legitimate alternatives.

## Grill findings

Resolved non-semantically: separated target formalization from task rescope and made maturity/alignment part of scientific identity.

## Remaining user decisions

None at the seam level. Individual unresolved research tasks may yield `USER_DECISION_REQUIRED` before a concrete target can be formalized.
