# AGENTS.md

## Mission

Build an autonomous time-series scientific research agent from the architecture in this repository.
The human should provide a research mandate and inspect promoted findings and evidence. The human
must not be required to supervise each model or tool step.

## Finance research posture

Chronos treats Polymarket as a time-series environment, not as permission to hard-code a trading
method. The researcher may invent analyses, labels, features, models, and execution hypotheses.
The harness must keep five questions separate:

1. What public information was observable at the simulated decision time?
2. When did a target become complete and legally usable as a label?
3. Which transformations and learned quantities were fitted inside each temporal fold?
4. Which choices were made using development evidence?
5. Was the final system frozen before protected evidence was exposed?

*Advances in Financial Machine Learning* is useful research guidance for event labeling, purged
validation, feature importance, backtest overfitting, and deflated performance. It is not a source
of automatic defaults. Every adopted procedure remains an explicit, testable scientific choice.

For Polymarket data, production access is read-only. Source adapters may translate facts from the
engine's public read surface or issue bounded parameterized SELECTs through a proved `human_ro`
transaction; they cannot mutate engine tables or infer missing availability. A block window remains
mutable. The retained resolution corpus may register payouts as labels only because it preserves
exact source bytes and uses the append-only resolution fact's `resolved_time` as availability.

## Instruction hierarchy

Start at `docs/README.md` and load context by task. Do not bulk-read `docs/`.

Before modifying architecture or scientific behavior, always read `CONTEXT.md`, locked decisions,
invariants, the architecture map, and the owning block's `README.md`, `transitions/README.md`,
`IMPLEMENTATION.md`, and exact transition contract. Then load only the approved contract,
cross-cutting specification, test strategy, or adjacent transition that governs an input, output,
authority, time boundary, identity, state effect, or failure under change.

Treat explicit LOCKED decisions, invariants, and approved contracts as authoritative. Follow
`docs/specification/ALIGNMENT_AND_DIAGRAMS.md` when sources conflict. Do not
reinterpret them merely to make implementation easier.

Architectural transitions use semantic names such as `context.build-packet` and
`data.build-information-set`. Numeric seam aliases are historical migration metadata and must not
be introduced into new filenames, diagrams, work packages, tests, or implementation notes.

## Scoped context and work packets

For material implementation, refactoring, debugging, or architecture work, use the repository-local
`$execute-work-packet` skill in `.agents/skills/execute-work-packet/`. Work on one semantic
transition or comparably coherent responsibility at a time: open an explicit packet, solve and
debug within its boundary, then close it with verification evidence and a transition receipt.

Scope context; do not discard it. Every packet retains global authority and canonical vocabulary,
loads its owning architecture block and exact contract, and may deliberately expand to adjacent
context when the boundary proves incomplete. A packet is not complete merely because its endpoint
test passes or its code runs.

## Research guidance skills

For repository-aware authored research, use the smallest applicable project skill:

- `$start-polymarket-research` to establish exact live Polymarket scope, caveats, a falsifiable
  opening question, and the next stage-specific skill;
- `$analyze-time-series-data` for data meaning, coverage, anomalies, and exploratory questions;
- `$design-time-series-feature-set` for target/label, feature-set, and candidate design or revision;
- `$review-backtest-gate` before requesting freeze/protected evaluation and when interpreting its
  immutable result.

These skills guide researcher judgment and produce proposals or memos. They do not grant data
access, formal identity, fitting authority, freeze, protected exposure, validation, promotion, or
durable-memory authority. Financial method catalogs are optional idea menus, not default pipelines.
Update principles only from traceable general failure modes, retain counterexamples, and preserve
prior versions in Git.

## Working agreement

Use the canonical terms in `CONTEXT.md`. Follow each term's linked subsystem specification before
changing its meaning. Do not introduce a near-synonym without first documenting a real semantic
distinction.

When authoritative sources conflict, follow the contradiction protocol in
`docs/specification/ALIGNMENT_AND_DIAGRAMS.md`. Do not silently choose or invent a reconciliation.

For complex, multi-component, or architecturally risky work, use the plan-first workflow in
`docs/specification/PLANS.md` before implementation. Low-risk local plumbing does not require
ceremony.

For every material component or behavior change:

1. State the component responsibility and relevant invariant(s).
2. Identify the concrete failure modes.
3. Add or confirm tests and evals before or alongside implementation.
4. Implement the smallest coherent solution.
5. Run the relevant deterministic tests, integration tests, and behavioral evals.
6. Review the diff against the architecture, not only against test pass or fail.

When a real run exposes a new failure, first create a failing regression test or eval that captures
the general failure mode, then fix the implementation.

## Non-negotiable rules

- No future-data or availability-time leakage.
- Predictor availability (`I_t`) and target-label maturity (`S_t`) are separate temporal
  boundaries.
- All learned or fitted state obeys the same temporal restriction as model fitting.
- A true protected backtest evaluates a frozen `PredictiveSystemDefinition`.
- Frozen scientific identity cannot silently mutate.
- Protected evidence access is privileged, recorded, and cannot be treated as unseen again after
  exposure.
- A tool result or observation does not automatically become a durable belief.
- Durable `ResearcherState` changes only at semantic commit boundaries.
- Formal scientific machinery must not use silent fallback unless the fallback was predeclared in
  the frozen specification.
- The AI may write open-ended exploratory code, but data access and side effects remain
  capability-constrained.
- The actor benefiting from approval cannot grant its own privileged approval.
- Rejected experiments and findings remain in the evidence and trajectory history.
- Do not weaken or delete a test simply because implementation fails it.

## Design style

- Prefer a small number of deep capabilities over many narrow tools.
- Prefer explicit provenance and graph references over fuzzy retrieval when the relationship is
  already known.
- Keep large evidence outside the LLM context but drillable by reference.
- Keep `AGENTS.md` concise. Put architectural detail in linked documents.
- Treat Mermaid as a subordinate communication representation. Keep diagrams beside their
  authoritative prose and preserve loops, state ownership, and privileged gates explicitly.
- Keep each transition contract beneath the architecture block that owns its decisive authority or
  state effect. Cross-block consumers link to that contract rather than duplicating it.
- Keep each block's `IMPLEMENTATION.md` aligned with the real code paths, tests, completed
  transitions, remaining reds, and verification commands as implementation evolves.
- Complexity must be earned by a concrete failure mode. Avoid framework-like abstractions without a
  demonstrated need.
- Low-risk plumbing may be chosen during implementation. High-risk scientific boundaries require
  explicit tests and contracts.

## Definition of done for a component

A component is not done merely because it runs. It is done when:

- its responsibility is clear;
- its critical invariants have executable tests;
- failure is explicit rather than silently converted to success;
- provenance and state effects are correct;
- it composes with adjacent components in at least one integration test;
- the implementation does not create a new unreviewed authority or evidence path.

## Code Review Rules

Flag any change that:

- bypasses temporal admissibility or protected-evidence gates;
- allows fitting during prediction;
- mutates a frozen scientific object in place;
- mutates durable research state directly from raw tool output;
- hides a scientific failure behind fallback or default behavior;
- loses provenance needed to reconstruct an experiment;
- lets report wording alter scientific conclusion or validation status;
- couples the research architecture irreversibly to one model provider;
- adds a new subsystem without identifying the concrete failure mode it prevents.

## Canonical development commands

Run project commands from the repository root inside Ubuntu under WSL.

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
./scripts/check.sh
```

`./scripts/check.sh` is the complete local quality gate. Use `uv sync --locked` in CI or another
verification context where a stale committed lockfile must fail rather than update.
