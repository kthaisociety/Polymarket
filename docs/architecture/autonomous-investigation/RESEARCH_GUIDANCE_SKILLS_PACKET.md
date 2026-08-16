# Work packet: malleable research guidance skills

## Identity

- Packet: `research.route-first-principles-guidance`
- Owning architecture block: autonomous investigation
- Semantic responsibility: give an authored researcher concise, stage-specific first-principles
  guidance without granting scientific or governance authority
- Input repository state: `73bea00` (`Connect retained data to the time-series kernel`)

## Objective

Add three project-local skills—analysis, feature-set design, and backtest-gate review—that improve
research judgment while preserving open-ended authored code and every deterministic harness gate.

## Context boundary

- Global authority loaded: `AGENTS.md`, locked decisions, scientific kernel, invariants, and the
  autonomous-investigation contract.
- Owning block and transition contract: autonomous investigation plus its exploration,
  formalization, development, and protected-evaluation boundaries.
- Relevant adjacent interfaces: `Researcher`, `ResearcherContext`, authored program manifest,
  development evidence, freeze request, and protected validation.
- Explicitly excluded work: runtime prompt injection, model-provider changes, new analysis tools,
  new feature operators, evaluation implementation, protected authority, and memory promotion.
- Assumption: Codex and other repository-aware agents load project-local skills through repository
  instructions; standalone providers require a later explicit context-routing integration.

## Change boundary

- Permitted files: three folders under `.agents/skills/`, their generated `agents/openai.yaml`,
  `AGENTS.md` routing, this packet, and the owning implementation map.
- Allowed state effects: versioned Markdown guidance and discoverable skill metadata only.
- Forbidden state effects: data access, trial execution, evidence mutation, fitting, freeze,
  protected disclosure, validation, promotion, or durable research-memory mutation.

## Correctness

- Governing invariants and decisions: research freedom; I1–I8, I12–I13, I17–I18, and I21–I26;
  increasing epistemic burden; development/protected separation.
- Concrete failure modes: one giant context-heavy manual; finance-specific doctrine; fixed feature
  recipes; advice presented as evidence; model self-approval; post-hoc backtest criteria; hiding
  failed trials; and updating guidance from an anecdote without preserving the observed failure.
- Expected inputs and outputs: each skill consumes task-local evidence and produces a proposal,
  checklist, or decision memo containing exact evidence references, uncertainties, alternatives,
  and an explicit next action.
- Violating mutation: remove the independent-authority warning from the backtest skill, prescribe a
  mandatory transform/model in the feature skill, or let analysis wording claim formal status.
- Required local tests/evals: skill folder validation, metadata/schema checks, semantic content
  assertions, and one realistic forward test per skill when explicitly authorized.
- Required integration evidence: `AGENTS.md` routes repository research work to the three skills
  while stating that their outputs remain proposals consumed by existing harness boundaries.

## Completion evidence

- All three skill folders pass `quick_validate.py`.
- Deterministic tests make the three violating mutations red.
- The complete repository quality gate passes.
- Owning Mermaid diagram and implementation map show where guidance enters and where authority stays.
- A transition receipt records exact limits and the standalone-provider follow-up.

## Boundary revisions

None.

## Transition receipt

- Status: **COMPLETE**.
- Resulting repository state: the commit containing this receipt on
  `codex/research-guidance-skills`.
- Delivered: three project-local skills with short stable workflows, editable first-principles
  references, Codex discovery metadata, explicit `AGENTS.md` routing, and architecture Mermaid.
- Authority preserved: skill outputs remain analysis memos, candidate proposals, and gate
  recommendations. Existing code alone controls data access, formal identity, fitting, freeze,
  protected exposure, validation, promotion, and durable memory.
- Skill validation: the official `quick_validate.py` reports `Skill is valid!` for all three
  folders.
- Focused evidence: `tests/skills/test_research_guidance_skills.py` reports `5 passed`; removing
  exploratory status/two-clock guidance, legal fitting, non-mandatory recipes, independent
  backtest authority, or traceable feedback requirements makes these tests red.
- Complete gate: Ruff formatting clean, Ruff lint clean, BasedPyright `0 errors, 0 warnings,
  0 notes`, and pytest `389 passed`.
- Not proven: the standalone `ModelProvider` does not yet load these repository files or bind skill
  versions into runtime context. No real-model forward test was run because independent subagent
  testing was not authorized for this packet. The skills improve repository-aware Codex research;
  they do not by themselves prove researcher quality.
