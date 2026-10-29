# Reporting implementation map

Status: **canonical finding rendering and deterministic paper audit implemented**.

- Code: `src/research_agent/reporting/builder.py`
- Paper audit: `src/research_agent/reporting/paper.py`
- Public interface: `src/research_agent/reporting/__init__.py`
- Tests: `tests/reporting/test_report_builder.py`
- Paper tests: `tests/reporting/test_paper_auditor.py`
- Transition contracts: [`transitions/`](transitions/)
- Implemented transitions: `report.render-finding`, `report.audit-paper`

The compatible model-provider adapter in `src/research_agent/runtime/provider.py` supplies runtime
decision intelligence only. It does not grant provider-authored wording authority over report
evidence, caveats, status, provenance, or conclusion; those remain owned by this boundary.

## Delivered behavior

- immutable, content-addressed `ReportSpecification` and `RenderedFindingReport`;
- an exact JSON-safe `FindingMachinePayload` that reconstructs the protected-evaluation
  `ValidatedFinding` and reruns its own content-identity validation;
- a `CanonicalReportRegistry` that admits only exact finding/report/decision bundles backed by the
  expected evaluation, independent promotion, and finding-publication ledger events;
- independent builder verification against that registry, not merely against caller-supplied hashes;
- Markdown rendering of the exact claim, target/system/scenario identities, promotion status,
  metrics and warnings, stability/concentration evidence, all ordered scope limitations and
  caveats, evidence/provenance refs, trial/exposure context, authority, and publication identity;
- predefined presentation choices with no scientific override or downstream-decision channel.

The paper-audit transition additionally delivers:

- independent verification of exact campaign manifest, source, execution, completion, receipt, and
  on-disk SHA-256 identities;
- a complete execution inventory that retains duplicate reruns and legacy unbound manifests rather
  than silently deduplicating history;
- a value-bound bridge requiring each cited legacy fresh source to have a source-identical rerun
  whose manifest fixes the exact harness binding;
- fixed evidence requirements for audit facts, evidence boundaries, development results, process
  generalizations, predictive replications, causal mechanisms, and trading strategies;
- deterministic whole-unit bootstrap support, exact binomial event tests, Holm correction for
  complete hypothesis families, and conservative Bonferroni correction over incompletely scored
  recorded searches;
- claim-value assertions that bind each displayed number or status to an exact nested receipt field;
- explicit falsification, stability, freeze, causal-design, and execution-evidence checks;
- content-addressed protocol and audit JSON plus a concise renderer that prints only audited claims
  and their limitations.

The retained Polymarket integration is under
`studies/polymarket-paper-acceptance-audit-2026-08-24/`. It verifies 90 governed executions across
five campaigns, representing 48 unique analysis identifiers and 42 retained reruns. The accepted
paper contains no execution-validated or protected finding claim.

## Verification

```bash
uv run pytest -q tests/reporting
uv run ruff check src/research_agent/reporting tests/reporting
uv run ruff format --check src/research_agent/reporting tests/reporting
uv run basedpyright
./scripts/check.sh
```

The adversarial suite covers exact machine round trips, multiple presentations sharing one
scientific fingerprint, attempted claim/metric/caveat replacement, omitted and reordered caveats,
forged rehashed findings without publication authority, mismatched canonical evidence, rejected
validation decisions, and a domain-neutral finding without downstream business or trading fields.

The paper suite also mutates receipt bytes, displayed values, dependence units, hypothesis-family
membership, search completeness, evidence tiers, and sampled-mark execution assertions. The real
Polymarket receipt is checked for exact identity, acceptance, 90-execution coverage, 48 unique
analyses, 42 reruns, and zero failed claims.

## Remaining reds and deliberate limits

- No AI prose generator, chart renderer, HTML/PDF renderer, or persisted registry adapter is
  implemented. Such adapters must preserve and reverify the same machine payload.
- The current protected `ValidatedFinding` carries target identity but no separately rendered
  horizon value; reporting cannot invent one. Horizon remains recoverable through the target
  definition identified by `target_id` until a canonical target resolver is added.
- The registered scientific-workflow runtime action renders and returns exact promoted reports as
  provisional observation/artifact evidence. General report distribution and arbitrary runtime
  report requests remain unimplemented.
- Paper auditing currently provides exact binomial event tests and deterministic percentile
  bootstrap intervals. Other dependence structures require a declared externally computed interval
  whose values are still bound to retained evidence; the auditor does not invent an inference
  method.
- Semantic entailment outside structured claim declarations is deliberately excluded. The concise
  paper renderer eliminates free-form scientific prose; a future external prose renderer must retain
  the same claim IDs and pass an additional entailment verifier.
