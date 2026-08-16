# Work packet: diagram-first repository navigation

## Identity

- Packet: `documentation.render-repository-map`
- Owning architecture block: global architecture navigation
- Semantic responsibility: make the GitHub landing page a truthful visual map into current
  architecture while removing the superseded pre-rebuild archive
- Input repository state: `391749a` (`Add malleable time-series research skills`)

## Objective

A new contributor can open the root GitHub page, understand the product and research loop through
rendered Mermaid diagrams, choose the relevant architecture block through direct links, run the
implemented application, and avoid mistaking archived pre-rebuild code for the current system.

## Context boundary

- Global authority loaded: `AGENTS.md`, architecture map, locked source hierarchy, and Mermaid
  policy.
- Owning block and transition contract: `docs/architecture/README.md`; this is a presentation and
  navigation transition rather than a scientific-state transition.
- Relevant adjacent interfaces: root `README.md`, block `README.md` files, implementation maps,
  tests, CLI entrypoints, and GitHub Markdown rendering.
- Explicitly excluded work: scientific meaning, application code, data files, current contracts,
  implementation status changes, generated research reports, and user-owned untracked research.
- Assumptions: GitHub renders standard fenced `mermaid` blocks; Git history is the recovery path for
  the explicitly superseded archive.

## Change boundary

- Permitted components: root README, global architecture README, documentation-navigation checks,
  this packet, and the tracked `archive/legacy-before-rebuild-2026-08-12` tree.
- Allowed state effects: rewrite presentation/navigation documents and remove the exact legacy
  archive from the current tree.
- Forbidden state effects: delete current specifications/data/research, alter contracts, change
  runtime behavior, or claim unproven capability.

## Correctness

- Governing rules: diagrams remain subordinate to authoritative prose; loops, temporal boundaries,
  privileged gates, and memory authority stay visible; links resolve inside the repository.
- Concrete failure modes: no root Mermaid; unreadable wall of links; broken relative links;
  outdated milestone claims; hidden research loop; protected backtest shown as ordinary tuning;
  archived code mistaken for current code; or deletion of current authority.
- Expected input/output: current architecture and implementation truth become a concise root visual
  map plus direct block navigation; the exact superseded archive disappears from the current tree.
- Violating mutation: remove the root Mermaid, break a block link, reintroduce the archive, omit the
  independent protected gate, or describe development evidence as a validated finding.
- Required local tests/evals: Markdown fence/link checks, required diagram/authority labels,
  archive-absence assertion, focused CLI smoke, and the complete quality gate.
- Required integration evidence: GitHub-visible README uses only standard Mermaid syntax and every
  block link reaches its current local README.

## Completion evidence

- Root README contains a whole-product diagram, a research-life-cycle diagram, and a repository map.
- Architecture README presents current status without completed migration framing.
- All local Markdown links in the landing page resolve.
- The exact legacy archive is absent and recoverable from Git history.
- Documentation checks and complete repository gate pass.
- After integration, GitHub `main` is inspected for rendered diagrams and exact commit identity.

## Boundary revisions

None.

## Transition receipt

- Status: **COMPLETE**.
- Resulting repository state: the commit containing this receipt on
  `codex/documentation-navigation`; integration is permitted only after the destination branch
  points at the same tree.
- Delivered: a root GitHub landing page with three standard Mermaid diagrams, a compact capability
  summary, current run commands, direct links into all twelve visual architecture blocks, and a
  diagram showing the documentation source hierarchy.
- Tidying: removed the exact 102-file `archive/legacy-before-rebuild-2026-08-12` tree and the two
  completed architecture-migration notes. They remain recoverable from Git history. Current
  specifications, architecture blocks, application code, retained data, and research outputs were
  not removed or changed.
- Navigation evidence: `tests/documentation/test_repository_navigation.py` checks the three root
  diagrams, all local landing-page links, Mermaid coverage in every architecture block, protected
  backtest authority labels, and absence of the superseded material.
- Complete gate: Ruff formatting clean, Ruff lint clean, BasedPyright `0 errors, 0 warnings,
  0 notes`, and pytest `394 passed`.
- Honest limit: these checks prove repository structure and standard Mermaid source, not GitHub's
  rendered pixels. The integrated `main` page must still be inspected after push.
