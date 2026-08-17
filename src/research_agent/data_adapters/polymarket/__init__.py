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
from research_agent.data_adapters.polymarket.corpus_analysis import (
    PolymarketDevelopmentAnalysis,
    PolymarketEventPartition,
    PolymarketRegisteredEventField,
    build_polymarket_development_analysis,
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
from research_agent.data_adapters.polymarket.source_expansion import (
    PolymarketPriceHistoryNeed,
    PolymarketSourceExpansion,
    PolymarketSourceExpansionError,
    expand_scouted_price_history,
    expansion_receipt_json,
    price_history_search_request,
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
    "PolymarketDevelopmentAnalysis",
    "PolymarketEventPartition",
    "PolymarketExploratoryAnalysis",
    "PolymarketFillRecord",
    "PolymarketImportRequest",
    "PolymarketIngestionResult",
    "PolymarketOutcomeRecord",
    "PolymarketPriceHistoryNeed",
    "PolymarketPricePoint",
    "PolymarketRegisteredEventField",
    "PolymarketResearchReader",
    "PolymarketResolutionRecord",
    "PolymarketSourceExpansion",
    "PolymarketSourceExpansionError",
    "analyze_registered_polymarket_tape",
    "build_polymarket_development_analysis",
    "expand_scouted_price_history",
    "expansion_receipt_json",
    "ingest_polymarket_contract_tape",
    "price_history_search_request",
    "register_polymarket_resolution_corpus",
]
