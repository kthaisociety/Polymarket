# Reporting implementation map

Status: **canonical deterministic boundary implemented**.

- Code: `src/research_agent/reporting/builder.py`
- Public interface: `src/research_agent/reporting/__init__.py`
- Tests: `tests/reporting/test_report_builder.py`
- Transition contracts: [`transitions/`](transitions/)
- Implemented transition: `report.render-finding`

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

## Verification

```bash
uv run pytest -q tests/reporting
uv run ruff check src/research_agent/reporting tests/reporting
uv run ruff format --check src/research_agent/reporting tests/reporting
uv run basedpyright src/research_agent/reporting tests/reporting
./scripts/check.sh
```

The adversarial suite covers exact machine round trips, multiple presentations sharing one
scientific fingerprint, attempted claim/metric/caveat replacement, omitted and reordered caveats,
forged rehashed findings without publication authority, mismatched canonical evidence, rejected
validation decisions, and a domain-neutral finding without insurance or trading fields.

## Remaining reds and deliberate limits

- No AI prose generator, chart renderer, HTML/PDF renderer, or persisted registry adapter is
  implemented. Such adapters must preserve and reverify the same machine payload.
- The current protected `ValidatedFinding` carries target identity but no separately rendered
  horizon value; reporting cannot invent one. Horizon remains recoverable through the target
  definition identified by `target_id` until a canonical target resolver is added.
- The registered scientific-workflow runtime action renders and returns exact promoted reports as
  provisional observation/artifact evidence. General report distribution and arbitrary runtime
  report requests remain unimplemented.
