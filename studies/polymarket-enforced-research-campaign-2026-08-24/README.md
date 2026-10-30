# Enforced behavioral and stochastic Polymarket rerun

Epistemic status: **COMPLETE — REPRODUCIBLE MECHANISM EVIDENCE, NO EXECUTION-VALIDATED STRATEGY**.

The scientific results, evidence ranking, exact campaign counts, and limitations are in
[`FINAL_REPORT.md`](FINAL_REPORT.md).

This study is the recovery campaign for the Chronos enforcement gap. Its first catalog contains
the final runnable, registered-corpus sources from the behavioral/game-theory program and the
earlier stochastic/time-series programs. Exact failed or superseded authoring attempts are retained
in their original studies but are not silently counted as final analyses here.

The campaign ran only through `ResearchCampaignAuthority`. That authority owns the exact source
and input manifest, invokes `AnalysisHarness`, verifies actual field access and identities, retains
externalized result bytes by hash, and refuses completion until every catalog item has an
authority-issued admissible receipt and disposition. Direct SQL receipts have no admission path.

The exposed corpora make this a reproducibility run. It does not restore fresh-development,
protected, or execution-validation status. The protected stochastic resolution was not re-opened.
The direct behavioral SQL mechanisms were rewritten against a registered parent-bound taker view;
formal, superseded, protected, and data-blocked sources are covered by an exact non-replay audit.

Run the registered-corpus catalog from the repository root:

```bash
PYTHONPATH=src .venv/bin/python -m \
  research_agent.data_adapters.polymarket.run_campaign_studies \
  --catalog studies/polymarket-enforced-research-campaign-2026-08-24/corpus-campaign.json \
  --corpus-workspace data/chronos/polymarket-corpora \
  --behavioral-fill-workspace data/chronos/polymarket-behavioral-fills \
  --campaign-directory studies/polymarket-enforced-research-campaign-2026-08-24/corpus-campaign-v2
```

The add-on, five-minute, and non-replay commands are retained as
[`behavioral-addon-campaign.json`](behavioral-addon-campaign.json),
[`run_fixed_clob_campaign.py`](run_fixed_clob_campaign.py), and
[`run_nonreplay_coverage_audit.py`](run_nonreplay_coverage_audit.py).
