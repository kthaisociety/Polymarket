"""Polymarket production-tape registration for the domain-neutral kernel."""

from research_agent.data_adapters.polymarket.analysis import (
    PolymarketAnalysisRequest,
    PolymarketExploratoryAnalysis,
    analyze_registered_polymarket_tape,
)
from research_agent.data_adapters.polymarket.ingestion import (
    PolymarketIngestionResult,
    ingest_polymarket_contract_tape,
)
from research_agent.data_adapters.polymarket.models import (
    PolymarketBlockVintage,
    PolymarketContractRecord,
    PolymarketFillRecord,
    PolymarketImportRequest,
    PolymarketOutcomeRecord,
)
from research_agent.data_adapters.polymarket.reader import (
    EnginePolymarketResearchReader,
    PolymarketResearchReader,
)

__all__ = [
    "EnginePolymarketResearchReader",
    "PolymarketAnalysisRequest",
    "PolymarketBlockVintage",
    "PolymarketContractRecord",
    "PolymarketExploratoryAnalysis",
    "PolymarketFillRecord",
    "PolymarketImportRequest",
    "PolymarketIngestionResult",
    "PolymarketOutcomeRecord",
    "PolymarketResearchReader",
    "analyze_registered_polymarket_tape",
    "ingest_polymarket_contract_tape",
]
