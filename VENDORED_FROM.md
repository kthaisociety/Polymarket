# Chronos provenance

Chronos was imported as a clean Git archive from:

- repository: `https://github.com/tagesk-tech/insurance-market-data`
- source commit: `fb0e8cb49c94a0cbdabb817226e9dcf6279f1083`
- imported on: `2026-08-16`

No nested `.git` directory or source-repository working-tree artifact is present. Insurance
datasets, insurance research reports, EIOPA/Kolada adapters, and their source-specific tests were
excluded from Chronos. The generic kernel, governance architecture, deterministic tests, research
skills, and operator surfaces were retained. Chronos subsequently developed inside
`bdl-polymarket/research/chronos/`. Its filtered history and complete current research state were
extracted into this standalone `Polymarket` repository on 2026-10-29. The parent engine,
deployment system, and Kthais project are not part of this repository.
