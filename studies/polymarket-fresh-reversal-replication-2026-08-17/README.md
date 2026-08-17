# Fresh-event post-jump reversal-hazard replication

Epistemic status: **PREDECLARED — NO FRESH RESULT YET**.

This study applies the fixed post-jump competing-risk question to the expanded production corpus
through the ancestor-bound fresh-replication capability. It may see only events absent from the
original 31-event corpus and before the expanded corpus's final protected event block.

The exact population, label, features, models, temporal folds, prediction gates, and sampled-price
cost falsifiers are fixed in the
[work packet](../../docs/work-packets/polymarket-fresh-reversal-replication.md) before authored code
reads any fresh price path.

Frozen authored source:
[`source/01_fresh_reversal_replication.py`](source/01_fresh_reversal_replication.py), SHA-256
`e97d91b7d698888674ddfab20ec47ffbcc1014774b2693d6780bf25b47b21d5a`. The Chronos sandbox
source validator accepted the exact bytes before execution.

## First execution

The public runner established 157 fresh development events/562 markets while excluding all 31
ancestor events and the expanded final 47 events. The authored worker then returned `MemoryError`
under its fixed 512 MB address-space limit before any statistical details existed. The exact failed
receipt is retained at
[`development-receipts/01_fresh_reversal_replication.json`](development-receipts/01_fresh_reversal_replication.json),
SHA-256 `5f216aa4d2df03eecfb9c6eb4b68822b158db5eb7642d16fe2aef9f3f540e20d`.

This is an operational harness result, not evidence for or against the hypothesis. The frozen
source and scientific gates remain unchanged.
