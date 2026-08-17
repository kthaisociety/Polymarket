# Data-foundation implementation map

Status: **generic temporal boundary and Polymarket production-tape adapter implemented; live
production read and capability-constrained authored exploration accepted through independently
packaged read-only commands; immutable DB snapshots, resolution-label availability, and
event/group identity remain red**.

## Generic kernel

- Temporal registration: `src/research_agent/data_foundation/`
- Content-addressed workspace: `src/research_agent/data_workspace/`
- Registration adversaries: `tests/data_foundation/`
- Workspace adversaries: `tests/data_workspace/`
- Data-to-research composition: `tests/integration/test_data_to_research_kernel.py`

The generic kernel keeps `reference_time`, `available_at`, predictor legality, label maturity,
fitting, and protected exposure as separate boundaries. No source adapter may grant itself later
scientific or protected authority.

## Polymarket adapter

- Source records and import request:
  `src/research_agent/data_adapters/polymarket/models.py`
- Public engine read adapter:
  `src/research_agent/data_adapters/polymarket/reader.py`
- Temporal registration:
  `src/research_agent/data_adapters/polymarket/ingestion.py`
- Fail-closed live smoke:
  `src/research_agent/data_adapters/polymarket/smoke.py`
- Shared proved read-only composition:
  `src/research_agent/data_adapters/polymarket/database.py`
- Registered information-set to authorized wide view:
  `src/research_agent/data_adapters/polymarket/analysis.py`
- Public authored live-analysis command:
  `src/research_agent/data_adapters/polymarket/live_analysis.py`
- Standalone live runtime dependencies: `asyncpg>=0.31.0`, `tenacity>=9`, and
  `prometheus-client>=0.26.0` in `pyproject.toml`
- Causal and command adversaries:
  `tests/data_adapters/polymarket/`

```mermaid
flowchart LR
    IDS["Explicit contract IDs"] --> READ["Engine public market reads"]
    CURSORS["History and forward cursors"] --> READ
    READ --> CONTRACTS["Contract, outcome, payout metadata"]
    READ --> FILLS["Taker-side fills"]
    CONTRACTS --> VALIDATE["Exact identity validation"]
    FILLS --> VALIDATE
    VALIDATE --> WINDOW["Inclusive block-window filter"]
    WINDOW --> REGISTER["ObservationRegistrar"]
    REGISTER --> CATALOG["Domain-neutral DataCatalogSnapshot"]
    WINDOW --> DIGEST["Exact read digest"]
    CATALOG --> INFO["InformationSet at explicit decision time"]
    INFO --> VIEW["Requested non-protected AuthorizedDataView fields"]
    VIEW --> SANDBOX["Unchanged authored code in AnalysisHarness"]
    SANDBOX --> OBS["EXPLORATORY StructuredObservation + artifacts"]
```

Each retained print produces price, absolute size, signed size, and block observations. Dimensions
bind `market_id`, `outcome_index`, `outcome_token`, and `fill_uid`. Source and provenance bind the
fill, transaction when present, block, and cursor vintage.

The availability rule is `polymarket-onchain-block-inclusion/v1`: `fill_time` represents public
chain observability. It does not represent collector or database arrival. Confirmation and
collector delay remain caveats on every observation.

Resolved payouts are read as authoritative contract metadata but are not registered as target
observations. The public read interface does not provide exact resolution availability, so doing so
would invent `available_at`. Event/group identity is also absent, so event-grouped validation is a
red gate rather than a silent market-ID fallback.

## Snapshot limitation

The cursor window is not an immutable database snapshot. The scope-repair backfill may insert a row
inside an existing window. The source digest makes a rerun observably different, and the adversary
proves that the registration identity moves, but the live database cannot reconstruct the prior
bytes. Protected evaluation needs retained immutable input bytes or an external database snapshot
identity.

## Verification

```bash
PYTHONPATH=src:../../engine/src uv run pytest tests/data_adapters/polymarket -q
PYTHONPATH=src:../../engine/src uv run ruff check \
  src/research_agent/data_adapters/polymarket tests/data_adapters/polymarket
PYTHONPATH=src:../../engine/src uv run basedpyright \
  src/research_agent/data_adapters/polymarket tests/data_adapters/polymarket
```

The real smoke additionally requires the approved `human_ro` tunnel and `BDL__DB__URL`. A missing
connection exits `BLOCKED`, not green. The driver is a direct Chronos runtime dependency because
the shipped smoke composes the engine's PostgreSQL pool; it must not depend accidentally on the
parent repository's environment.

The live read-only acceptance was rerun through the standalone Chronos environment. It proved
`human_ro`, session and transaction read-only settings, and denied insert/update privileges before
reading one contract, 10,140 fills, and registering 40,560 observations. No DSN or secret is stored
in this repository or emitted in the receipt.

The live authored-analysis path was then exercised on two explicit high-coverage contracts. It
registered 60,518 and 59,937 fills respectively, built exact cutoff-scoped information sets,
recorded actual requested-field accesses, and persisted digest-verified result artifacts and
sanitized receipts under `studies/polymarket-flow-2026-08-17/`. A same-direction-trade falsifier
rejected the initial raw-flow interpretation as likely transaction-price mechanics. The study is a
preserved exploratory negative result, not development evidence or a finding.
