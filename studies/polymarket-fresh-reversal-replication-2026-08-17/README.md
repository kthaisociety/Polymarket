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

## Successful resource-bounded retry

The byte-identical source succeeded through the same public runner under a recorded 600-second,
4 GB worker envelope. The exact successful receipt is
[`resource-retry-receipts/01_fresh_reversal_replication.json`](resource-retry-receipts/01_fresh_reversal_replication.json),
SHA-256 `e777f93b48c87604d845dfd08160036449b2accdd13277a0acf55d243d658c77`.
An exact replay converged to the same receipt bytes.

Epistemic status: **FRESH DEVELOPMENT REPLICATION PASSED — NOT PROTECTED OR EXECUTION-VALIDATED**.

- 6,174 OOF shocks, 2,929 reversal-first/3,245 other, 410 markets, 128 test events;
- primary six-feature state/shock gate passed: observation/event Brier `0.24084/0.23902` versus
  rate `0.25062/0.25222`, pooled/event AP `0.58844/0.69991` versus `0.47947/0.51144`, and
  top-quintile lift `+0.15039`;
- secondary 12-feature incremental gate passed: observation/event Brier `0.23072/0.23025`,
  pooled/event AP `0.62789/0.71552`, and top-quintile lift `+0.20955`;
- the full-model one-cent sampled-price screen passed on 387 trades/70 events with
  observation/event-macro mean `+0.06024/+0.04103` and positive means after both shock signs;
- the state-only cost screen failed its fixed breadth rule because it selected only six
  negative-shock trades, despite positive aggregate and sign-conditional observed means.

This is credible evidence that internal contract state predicts the reversal-before-continuation
path property on different Polymarket events. It is not yet an executable strategy: the corpus has
sampled probabilities rather than historical bid/ask/depth, and the final 47 events remain sealed.
The predeclared next step is exact formal-candidate preparation without protected exposure.
