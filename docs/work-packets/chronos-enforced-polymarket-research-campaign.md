# Work packet

## Identity

- Packet: `chronos.enforce-polymarket-research-campaign`
- Owning architecture block: Autonomous investigation, composed with exploration and the
  Polymarket data foundation.
- Semantic transition or responsibility: Admit and complete a repository research campaign only
  from authority-issued Chronos executions over exact registered inputs; reject direct-script or
  manually asserted evidence.
- Input repository state: `historical checkpoint 712fc693bd1728794ba76f9cb6627e957b1ec7b4` on
  `codex/polymarket-time-series-research`, preserving all pre-existing behavioral, stochastic,
  low-latency, and dual-clock worktree changes.

## Objective

Provide one deterministic campaign manifest, runner, and receipt verifier for which a study cannot
claim a successful or complete research execution unless every required analysis has an exact
registered input identity, harness-issued code/access provenance, immutable receipt bytes, and the
campaign's declared scientific disposition. Use that boundary to rerun the prior behavioral/game-
theory and stochastic-process programs without direct study SQL or manually assembled receipts.

## Context boundary

- Global authority loaded: repository and Chronos `AGENTS.md`, `CONTEXT.md`, locked decisions,
  invariants, sandbox/authority, lifecycle, backtest/evaluation, and test strategy.
- Owning block and transition contract: autonomous-investigation README/implementation and
  `AUTONOMOUS_INVESTIGATION_CONTRACT.md`, with the exploration registration-to-sandbox path as the
  upstream execution interface.
- Relevant adjacent interfaces: `AnalysisHarness`, retained Polymarket corpus store and whole-event
  partitions, live Polymarket registration, `RuntimeInvestigationCoordinator`, immutable receipt
  persistence, and protected/backtest authority separation.
- Explicitly excluded work: provider authentication, protected-data self-authorization, production
  mutation, deployment/trading, rewriting prior receipts, or treating a rerun as fresh evidence
  when it uses an exposed corpus.
- Assumptions: the current Codex session supplies researcher judgment; Chronos must nevertheless
  own every data capability, execution, identity, and receipt. A rerun may reproduce development
  evidence but cannot restore freshness.

## Change boundary

- Permitted files or components: one campaign module and CLI under `research_agent`, focused tests,
  Polymarket registered-data composition needed by the declared campaign, this work packet,
  owning implementation maps, and new rerun artifacts. Existing study source may be copied into a
  versioned campaign source but prior sources/receipts remain immutable.
- Allowed state effects: local content-addressed data retention, local immutable campaign receipts
  and artifacts, bounded `human_ro` reads through approved adapters, and development-only harness
  execution.
- Forbidden state effects: direct SQL from study code, mutable result overwrites, protected-value
  exposure, production writes, secrets in artifacts, or completion from documentation assertions.

## Correctness

- Governing invariants and decisions: I1, I2, I9, I11--I14, I17--I20, I22--I24; AI owns research
  intent while the harness owns admissible information, side effects, provenance, temporal
  legality, and scientific status.
- Concrete failure modes: accepting a receipt without harness access provenance; using a live query
  result without an exact retained input identity; omitting a failed/blocked declared analysis;
  changing source beneath a receipt; completing a trading campaign with only exploratory pattern
  screens; confusing a rerun with fresh or protected evidence; or allowing the campaign actor to
  issue its own protected promotion.
- Expected inputs and outputs: an exact campaign manifest plus registered datasets and versioned
  authored sources produce harness receipts, a complete coverage/disposition matrix, and a
  campaign receipt whose identity is derived from all required inputs and executions.
- Violating mutation or counterexample: insert one legacy receipt lacking actual-access provenance,
  alter one source byte, omit one required analysis, or mark a sampled-price development rerun
  `EXECUTION_VALIDATED`; campaign verification must fail before completion.
- Required local tests/evals: unit tests for admission, identity, immutability, completeness,
  epistemic ceilings, and all four violating cases; registered Polymarket integration test; focused
  investigation/exploration tests; formatting/type checks; `git diff --check`.
- Required integration evidence: at least one prior behavioral source and one prior stochastic-
  process source execute through the same campaign boundary, with exact registered input and field
  accesses in their receipts. Full campaign closure additionally requires every inventoried prior
  analysis to have a rerun or an explicit harness-issued blocked receipt.

## Completion evidence

- The bypass regression is red before implementation and green afterward.
- The campaign CLI cannot import or execute study-owned database clients.
- All declared behavioral/game-theory and stochastic-process analyses are inventoried.
- Each inventory row has an immutable harness-issued rerun receipt or a harness-issued blocked
  prerequisite receipt; no legacy result silently satisfies the campaign.
- Rerun comparisons preserve nulls, failures, exposure history, and the distinction between
  sampled marks and executable quotes.
- Focused and canonical quality gates pass, implementation maps are aligned, and the transition
  receipt states what remains scientifically unresolved.

## Boundary revisions

- The campaign manifest now binds the hash of exact registered view values, policy, session, and
  resource limits rather than relying only on human-readable dataset/environment references.
- Direct behavioral SQL was replaced by a content-addressed, parent-bound aggregate-taker corpus
  and four versioned harness sources. This was necessary to satisfy the original prohibition on
  direct study database access.
- Formal transitions, superseded failures, protected one-shot artifacts, and invalid-data studies
  cannot truthfully receive ordinary analysis receipts. A separate value-bound 25-row non-replay
  audit records their exact source/receipt hashes, status, reason, and replacement rather than
  pretending they were executed.
- The catalog-wide execution tier is explicitly clamped to every study's prior evidence ceiling;
  the completed reruns are `EXPOSED_REPRODUCTION` even where the historical source once had fresh
  status.

## Transition receipt

Status: **CLOSED — 2026-08-24**.

- Implementation: immutable `CampaignManifest`, `CampaignStore`, and
  `ResearchCampaignAuthority`; exact harness-value binding; Polymarket catalog composition;
  parent-bound behavioral fill retention/registration; and focused adversarial tests.
- Core completion:
  `campaign-completion-receipt:184dbd75271bc528d95c963af78b857824f4c4615c42c1d1884cb6e793613a82`
  for 44/44 admissible analyses.
- Behavioral add-on completion:
  `campaign-completion-receipt:0c10260cd3870e015e26080d2741b0d5e6247f3a4ddec81805536f1acfe1d494`
  for 2/2 admissible falsifiers.
- Five-minute completion:
  `campaign-completion-receipt:20f78f838d818d4d3447b7de4e30445f4dee21d4c33ccdd6c0dcb76ed9bca820`.
- Non-replay audit completion:
  `campaign-completion-receipt:ee79c63edea5e44cca1c39b5c632021b839ac5af08a1968341dc9beb2790f8b0`
  over 25 exact prior source/receipt pairs.
- Reproducibility: 43 prior final sources produced identical structured results; zero changed.
  Four registered-view behavioral rewrites produced new admissible negative results.
- Scientific disposition: zero execution-validated strategies. The longshot fade remains the sole
  behavioral lead; fresh reversal and duration/path stochastic models have stronger out-of-time
  evidence but remain non-executable sampled-mark results.
- Verification: focused enforcement/data suite `36 passed`; broad Chronos suite `600 passed` with
  21 loopback fixtures denied by the restricted sandbox, followed by `45 passed` for both affected
  files with loopback permission; Ruff clean; Basedpyright `0 errors`; `git diff --check` clean;
  receipt/count/comparison audit `FINAL_AUDIT_OK`.
