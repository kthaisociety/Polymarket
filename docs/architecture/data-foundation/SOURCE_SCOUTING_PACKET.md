# Work packet: autonomous source scouting handoff

## Identity

- Packet: `data.propose-source-candidates`
- Owning architecture block: data foundation
- Semantic transition or responsibility: turn a bounded research data need into an append-only,
  provider-neutral list of source proposals without acquiring or registering data
- Input repository state: `f2bd876` (`Make GitHub documentation diagram-first`)

## Objective

A researcher can submit one exact source-search request to an externally orchestrated scout, retain
the request, unverified provider label, proposed sources, risks, and rejected attempts, and explicitly
hand one exact candidate to the existing `data.retain-source-snapshot` boundary.

## Context boundary

- Global authority loaded: `AGENTS.md`, `CONTEXT.md`, locked decisions, I13/I17/I18/I20/I24/I25,
  architecture, data lifecycle, authority/sandbox rules, provider rules, test strategy, and Mermaid
  policy.
- Owning block and transition contract: data-foundation README/implementation map plus the new
  `data.propose-source-candidates` contract; adjacent acquisition authority remains entirely in
  `data.retain-source-snapshot`.
- Relevant adjacent interfaces: `DataWorkspace`, `FetchRequest`, `SourceSnapshotRef`, CLI JSON
  conventions, and a passive provider-neutral scouting response format.
- Explicitly excluded work: temporal profiling, observation registration, kernel changes, model or
  feature construction, protected data, scientific conclusions, source ranking policy, credentials,
  and provider-specific authentication.
- Assumptions: Codex or another external orchestrator performs web search outside the application;
  its caller-labelled output is untrusted proposal content and never scientific evidence merely
  because it is retained.

## Change boundary

- Permitted files or components: one additive data-workspace scouting module, public exports, data
  CLI handoff, focused tests, this packet, the owning transition/index, implementation map, and
  data-foundation Mermaid.
- Allowed state effects: append exact scouting requests, reports, and sanitized failures below the
  workspace's separate scouting ledger; after explicit selection, call the unchanged acquisition
  boundary and receive its ordinary value-free fetch receipt.
- Forbidden state effects: silently fetch every candidate, create registered observations, infer
  `available_at`, grant field meaning or access, update research state, touch protected evidence,
  or let a model select/configure its own executable provider.

## Correctness

- Governing invariants and decisions: acquisition is the only data-workspace operation that may
  fetch bytes; provider replacement cannot change scientific architecture; observations are not
  beliefs; exploratory freedom grants no store, registration, or promotion authority.
- Concrete failure modes: provider text becomes a dataset; search output smuggles bytes, secrets,
  scientific status, or fabricated provenance; scouting silently fetches; a forged/stale report is
  acquired; retry changes or duplicates a prior ledger result; failed scouting disappears; or
  source discovery becomes coupled to one model vendor.
- Expected inputs and outputs: strict `SourceSearchRequest` plus passive recorded response and
  idempotency identity produce a strict `SourceScoutingReceipt`; explicit exact candidate
  selection may later produce the unchanged `FetchReceipt`.
- Violating mutation or counterexample: remove exact report resolution and accept a caller-authored
  candidate URL directly through the scouting acquisition seam; the forged-report test must turn
  red before any HTTP request.
- Required local tests/evals: strict schemas, no-fetch scouting, exact persistence/restart,
  retry/conflict, provider failure, secret/unknown-authority rejection, forged report/candidate
  denial, and exact candidate-to-existing-fetch composition.
- Required integration evidence: two structurally different search needs use one provider-neutral
  seam; one selected local HTTP candidate is retained by the existing workspace while unselected
  candidates cause zero requests and no registration or kernel effect.

## Completion evidence

- Focused scouting, generic workspace, CLI, and data-kernel bridge tests pass.
- Ruff, formatting, BasedPyright, and the complete repository gate pass.
- Owning Mermaid and implementation map show scouting as an external proposal layer before
  acquisition and retain the explicit registration/temporal-profile gate.
- One transition receipt states both the usable Codex/subagent handoff and what remains provider
  configuration rather than kernel behavior.

## Boundary revisions

None.

## Transition receipt

- Delivered one provider-neutral passive response format, strict request/candidate/report
  identities, append-only workspace scouting ledger, external Codex/subagent response adapter,
  and two additive CLI commands: `data scout` and `data acquire-scouted`.
- The scouting command executes no provider code, cannot fetch response bytes, invent temporal
  availability, create registered observations, or update research state. Acquisition resolves one exact issued
  candidate before delegating to the unchanged `DataWorkspace.fetch`.
- Adversarial coverage includes unknown/authority-bearing response fields, credential-like URLs,
  provider failure, exact restart replay, changed-intent conflict, same-process concurrent retry,
  forged report/candidate denial, path-like report identities, and proof that unselected candidates
  make zero requests.
- Real smoke: a Codex research lane proposed two official Eurostat resources for Nordic voluntary
  health-insurance financing and unmet-care waiting lists. Scouting retained both proposals without
  acquisition. Explicitly selecting the financing resource retained 33,843 bytes as
  `source:f759c60c...f8281b1e`; SHA-256
  `5cf2f9dd98188320e8b73cf4125c2589d7494095b2dc9edb68c3cc06553ecfb1` matched the
  independent research lane, and `data verify` returned healthy. The second candidate was not
  fetched.
- Canonical evidence at completion: `uv 0.12.5`; Ruff format/check green; BasedPyright zero
  diagnostics; 47 focused scouting/workspace/CLI tests green; and the complete repository suite
  green at 421 tests.
- Independent read-only audit initially reproduced executable-callback, report-substitution,
  timestamp-integrity, and directory-replacement failures. The final design accepts passive JSON
  only, anchors every ledger read/write/retry to verified directory descriptors, binds time into
  report identity, and rejects filename/content substitution. The reviewer reran the exact replay
  and directory-replacement cases and returned `ACCEPT` with no remaining scoped finding.
- Honest limits: the project does not launch Codex internally or embed one provider; Codex remains
  the external orchestrator that authors the strict response. The provider label is caller-supplied
  correlation metadata, not authenticated provenance. Candidate usefulness, license,
  temporal legality, and field meaning remain unverified until the ordinary downstream gates.
  External provider retries/costs, destination egress policy, and production distributed durability
  remain outside this packet.
