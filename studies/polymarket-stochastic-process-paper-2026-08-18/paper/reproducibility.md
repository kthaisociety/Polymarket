# Reproducibility guide

Run commands from the Chronos root. The production database is not needed to replay retained
studies; exact content-addressed snapshots must exist in `data/chronos/polymarket-corpora`.

## Verify receipt bytes

```bash
find studies/polymarket-stochastic-process-paper-2026-08-18 -type f -name '*.json' -print0 \
  | sort -z \
  | xargs -0 sha256sum
```

Compare the relevant hashes with [`evidence-index.md`](evidence-index.md).

## Replay the complete development comparison

```bash
.venv/bin/python -m research_agent.data_adapters.polymarket.run_corpus_studies \
  --snapshot-sha256 8c73260377ea5cb3e569bbc3c744ce9b62a95c8f54dafb73d07671845ccec4c6 \
  --snapshot-size 318684407 \
  --ancestor-snapshot-sha256 610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f \
  --ancestor-snapshot-size 19434443 \
  --workspace ../../data/chronos/polymarket-corpora \
  --source studies/polymarket-stochastic-process-paper-2026-08-18/source/12_composed_process_family_comparison.py \
  --receipt-directory /tmp/chronos-process-paper-replay \
  --session-id paper-process-comparison-replay
```

The replay must reproduce the source hash and substantive result. The output directory is separate
so immutable retained receipts are not overwritten.

## Replay the frozen later cohort

```bash
.venv/bin/python -m research_agent.data_adapters.polymarket.run_corpus_studies \
  --snapshot-sha256 184b83f7f8012da4ca9116c8b6bad2076570ad5f0bada95b22615ee2f5cceae8 \
  --snapshot-size 428280682 \
  --ancestor-snapshot-sha256 8c73260377ea5cb3e569bbc3c744ce9b62a95c8f54dafb73d07671845ccec4c6 \
  --ancestor-snapshot-size 318684407 \
  --workspace ../../data/chronos/polymarket-corpora \
  --source studies/polymarket-stochastic-process-paper-2026-08-18/source/13_frozen_process_successor_replay.py \
  --receipt-directory /tmp/chronos-process-paper-successor-replay \
  --session-id paper-frozen-successor-replay
```

Source 13 contains literal source-12 parameter arrays and parent source/receipt hashes. It must not
fit or alter a threshold on the successor cohort.

## Replay the formal negative

```bash
.venv/bin/python \
  studies/polymarket-stochastic-process-paper-2026-08-18/source/14_formal_hurdle_arrival_freeze.py
```

The retained path is conflict-detecting. To perform an independent replay without touching the
existing receipt, copy the exact committed driver to a temporary study directory and change only
its output path before execution; that copy then has a different driver hash and must be labeled a
reproduction, not the original evidence object.

## Generate figures

```bash
.venv/bin/python \
  studies/polymarket-stochastic-process-paper-2026-08-18/paper/build_figures.py
```

The figure builder reads retained receipts only. It performs no fitting and has no production or
protected-data capability.

## Verify Chronos

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/basedpyright
```

The paper's source programs are byte-hashed evidence and are excluded from automatic formatting.
