"""Polymarket production-tape registration for the domain-neutral kernel."""

from research_agent.data_adapters.polymarket.analysis import (
    PolymarketAnalysisRequest,
    PolymarketExploratoryAnalysis,
    analyze_registered_polymarket_tape,
)
from research_agent.data_adapters.polymarket.corpus import (
    PolymarketCorpusRegistration,
    PolymarketCorpusRetention,
    PolymarketCorpusSnapshot,
    PolymarketCorpusSnapshotRef,
    PolymarketCorpusStore,
    register_polymarket_resolution_corpus,
)
from research_agent.data_adapters.polymarket.ingestion import (
    PolymarketIngestionResult,
    ingest_polymarket_contract_tape,
)
from research_agent.data_adapters.polymarket.models import (
    PolymarketBlockVintage,
    PolymarketContractRecord,
    PolymarketCorpus,
    PolymarketCorpusContract,
    PolymarketCorpusOutcome,
    PolymarketCorpusRequest,
    PolymarketFillRecord,
    PolymarketImportRequest,
    PolymarketOutcomeRecord,
    PolymarketPricePoint,
    PolymarketResolutionRecord,
)
from research_agent.data_adapters.polymarket.reader import (
    DatabasePolymarketCorpusReader,
    EnginePolymarketResearchReader,
    PolymarketResearchReader,
)

__all__ = [
    "DatabasePolymarketCorpusReader",
    "EnginePolymarketResearchReader",
    "PolymarketAnalysisRequest",
    "PolymarketBlockVintage",
    "PolymarketContractRecord",
    "PolymarketCorpus",
    "PolymarketCorpusContract",
    "PolymarketCorpusOutcome",
    "PolymarketCorpusRegistration",
    "PolymarketCorpusRequest",
    "PolymarketCorpusRetention",
    "PolymarketCorpusSnapshot",
    "PolymarketCorpusSnapshotRef",
    "PolymarketCorpusStore",
    "PolymarketExploratoryAnalysis",
    "PolymarketFillRecord",
    "PolymarketImportRequest",
    "PolymarketIngestionResult",
    "PolymarketOutcomeRecord",
    "PolymarketPricePoint",
    "PolymarketResearchReader",
    "PolymarketResolutionRecord",
    "analyze_registered_polymarket_tape",
    "ingest_polymarket_contract_tape",
    "register_polymarket_resolution_corpus",
]
