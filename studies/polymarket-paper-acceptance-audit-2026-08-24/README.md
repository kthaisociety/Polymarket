# Polymarket paper acceptance audit — 2026-08-24

This study applies the deterministic Chronos paper gate to the complete retained behavioral,
game-theory, and stochastic-process campaign history. It verifies five campaign manifests,
executions, and completion receipts; resamples whole events for the available predictive
comparisons; corrects fixed successor signatures with Holm and the broader stochastic search with a
conservative recorded-search Bonferroni penalty; binds manuscript numbers to receipt fields; and
blocks causal, confirmatory, or trading language that exceeds the evidence.

Run from the Chronos root:

```bash
.venv/bin/python studies/polymarket-paper-acceptance-audit-2026-08-24/build_audit.py
```

Outputs are conflict-detecting:

- `paper-protocol.json` — exact claims, evidence, tests, and search families;
- `paper-acceptance-receipt.json` — machine-readable inventory and decision;
- `PAPER.md` — concise rendering of the same audited claims.

An accepted paper is not a promoted finding or trading authorization. Existing exposed evidence
remains exposed, and a new untouched cohort plus quote/order-book execution evidence are still
required for the claims identified in the paper.
