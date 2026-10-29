# Transition receipt

## Result

- Packet: `standalone-polymarket-repository-extraction`
- Status: `COMPLETE`
- Input repository state: `bdl-polymarket@712fc693bd1728794ba76f9cb6627e957b1ec7b4` plus the then-current modified and untracked `research/chronos/` working state
- Resulting repository state: standalone implementation commit `4aa1208` on local `Polymarket/main`; this receipt is the only subsequent state delta

## Delivered state delta

- Files and interfaces changed: filtered Chronos history became repository-root history; the current Chronos code, tests, documentation, skills, studies, and retained evidence were overlaid; local asyncpg pool composition replaced the parent engine pool dependency; standalone README, CI, license, check script, and repository metadata were added
- Behavior added, removed, or preserved: Chronos research behavior and retained evidence were preserved; direct read-only, parameterized Polymarket database access is now locally composed; no parent engine or deployment tree is present
- Allowed state effects observed: a local repository and local commits were created; the source repository was read but not modified; dependencies were installed only into the ignored local virtual environment
- Documentation status updated: standalone usage, provenance, implementation mapping, work packet, and this receipt are current

## Evidence

- Tests and evals run: `./scripts/check.sh`; `.venv/bin/research-agent verify`; focused standalone adapter tests; source/config engine-reference scan; ignored-file, secret-pattern, large-file, history, and remote audits
- Results: Ruff formatting and lint passed; basedpyright passed with 0 errors and 0 warnings; all 629 pytest tests passed; scientific-kernel verification reported 10 `HARNESS_GREEN`, 5 documented `EXPECTED_RED`, 0 `UNEXPECTED_GREEN`, and 0 `HARNESS_BUG`
- Boundary/debug observations: 21 HTTP-boundary tests initially failed only because the restricted sandbox denied loopback socket creation; the identical suite passed with loopback access. Two study scripts construct local read-only PostgreSQL URLs from runtime password input; no credential value is stored in the repository
- Violating mutation or counterfactual demonstrated: the repository passes without the parent checkout on `PYTHONPATH`, without `../../engine/src`, and without imports from parent `core` or `market` packages
- Integration evidence: standalone `scripts/check.sh` passed from the repository root; the local repository has no configured remote and no AIS operation occurred

## Knowledge carried forward

- Decisions and assumptions relied upon: the current Chronos working tree was authoritative; all retained studies and evidence had to remain; AIS creation or push requires explicit user verification after local completion
- New facts discovered: the extracted working state contained 158 strict typing errors that were corrected without weakening the project-wide gate; the parent-dependent reader and pool seam required a standalone implementation
- Unresolved uncertainty: the exact AIS Git owner/organization, remote URL, repository visibility, and authorization remain intentionally unresolved pending user verification
- Remaining reds or follow-up dependencies: AIS repository creation, remote configuration, and push remain pending; the five scientific-kernel `EXPECTED_RED` items are documented product limitations, not extraction regressions

This receipt proves the local standalone extraction and its verification evidence. It does not prove live production database access, scientific promotion of any retained study, deployment readiness, or successful publication to AIS.
