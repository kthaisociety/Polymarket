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

## Replay the representation robustness experiment

```bash
.venv/bin/python -m research_agent.data_adapters.polymarket.run_corpus_studies \
  --snapshot-sha256 8c73260377ea5cb3e569bbc3c744ce9b62a95c8f54dafb73d07671845ccec4c6 \
  --snapshot-size 318684407 \
  --ancestor-snapshot-sha256 610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f \
  --ancestor-snapshot-size 19434443 \
  --workspace ../../data/chronos/polymarket-corpora \
  --source studies/polymarket-stochastic-process-paper-2026-08-18/source/15_representation_robustness.py \
  --receipt-directory /tmp/chronos-process-representation-replay \
  --session-id paper-process-representation-replay \
  --wall-time-seconds 600 \
  --max-memory-bytes 4294967296
```

The source SHA-256 must be
`30b19d7c611cb5217b465cffa758f6460c84bf1822de0435804b16fc8e1b7147`; the retained receipt
SHA-256 is `757ee06535d3e7e06b8ccc5401aa027266122adaf18b253729ac021cc72bcfc9`.

## Replay the arrival-hazard freeze

```bash
.venv/bin/python -m research_agent.data_adapters.polymarket.run_corpus_studies \
  --snapshot-sha256 8c73260377ea5cb3e569bbc3c744ce9b62a95c8f54dafb73d07671845ccec4c6 \
  --snapshot-size 318684407 \
  --ancestor-snapshot-sha256 610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f \
  --ancestor-snapshot-size 19434443 \
  --workspace ../../data/chronos/polymarket-corpora \
  --source studies/polymarket-stochastic-process-paper-2026-08-18/source/16_freeze_arrival_hazard.py \
  --receipt-directory /tmp/chronos-arrival-hazard-freeze-replay \
  --session-id paper-arrival-hazard-freeze-replay \
  --wall-time-seconds 600 \
  --max-memory-bytes 4294967296
```

Source 16 must reproduce source 03's constant, state, full, fold, and gate objects exactly. Its
source SHA-256 is `dabe18ab627c9a95c4d066e90a03dfd2a4350d3c465464bad785381e0d627e5c`;
the retained receipt SHA-256 is
`21c3d08cc236953d1ad7e2b6ddc3986db0528d90e9b7813bd31614d97f0f9314`.

## Replay the frozen later arrival hazard

```bash
.venv/bin/python -m research_agent.data_adapters.polymarket.run_corpus_studies \
  --snapshot-sha256 184b83f7f8012da4ca9116c8b6bad2076570ad5f0bada95b22615ee2f5cceae8 \
  --snapshot-size 428280682 \
  --ancestor-snapshot-sha256 8c73260377ea5cb3e569bbc3c744ce9b62a95c8f54dafb73d07671845ccec4c6 \
  --ancestor-snapshot-size 318684407 \
  --workspace ../../data/chronos/polymarket-corpora \
  --source studies/polymarket-stochastic-process-paper-2026-08-18/source/17_frozen_arrival_hazard_successor_replay.py \
  --receipt-directory /tmp/chronos-arrival-hazard-successor-replay \
  --session-id paper-arrival-hazard-successor-replay \
  --wall-time-seconds 600 \
  --max-memory-bytes 4294967296
```

Source 17 performs no fitting. Its source SHA-256 is
`aaf439a67f61d42f50e5b4f711a8f6255a2fefce9733f9b3b43f6a91d7dc2f95`; the retained receipt
SHA-256 is `0ffda46feea1e16ea9398ac9054ad70bc5b7cc1992874926b6b4e6abdbb8843f`.

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
