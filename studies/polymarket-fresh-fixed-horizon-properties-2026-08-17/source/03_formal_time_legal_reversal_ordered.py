"""Retry the frozen formal trial with canonically ordered derived price rows."""

# ruff: noqa: ANN001, ANN202, D103, E501, EM101, INP001, SLF001, T201, TRY003

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from research_agent.data_adapters.polymarket import (
    PolymarketCorpus,
    PolymarketCorpusRequest,
    PolymarketCorpusStore,
    register_polymarket_resolution_corpus,
)
from research_agent.data_foundation import SampleKey

PARENT_SOURCE = Path(__file__).with_name("02_formal_time_legal_reversal.py")
RECEIPT = Path(__file__).parents[1] / "formal-receipts/03_formal_time_legal_reversal_ordered.json"


def _load_parent():
    spec = importlib.util.spec_from_file_location("chronos_formal_reversal_parent", PARENT_SOURCE)
    if spec is None or spec.loader is None:
        raise ValueError("could not load frozen formal parent source")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _formal_catalog(snapshot, selected):
    selected_ids = frozenset(selected)
    contracts = tuple(item for item in snapshot.corpus.contracts if item.market_id in selected_ids)
    resolution_by_market = {item.market_id: item for item in snapshot.corpus.resolutions}
    resolutions = tuple(resolution_by_market[item.market_id] for item in contracts)
    prices = tuple(
        sorted(
            (point for contract in contracts for point in selected[contract.market_id]["points"]),
            key=lambda point: (point.market_id, point.observed_at),
        )
    )
    request = snapshot.corpus.request
    sliced_request = PolymarketCorpusRequest(
        environment_id=request.environment_id,
        as_of=request.as_of,
        min_points=request.min_points,
        max_markets=len(contracts),
        outcome_index=request.outcome_index,
        fidelity=request.fidelity,
    )
    sliced = PolymarketCorpus(sliced_request, contracts, resolutions, prices)
    derived_snapshot = PolymarketCorpusStore.from_corpus(sliced)
    registration = register_polymarket_resolution_corpus(derived_snapshot)
    probability_dataset = registration.price_dataset
    observation_by_key = {
        (dict(item.dimensions)["market_id"], item.reference_time): item
        for item in probability_dataset.observations
    }
    keys = tuple(
        SampleKey(
            selected[market_id]["decision_time"],
            observation_by_key[(market_id, selected[market_id]["decision_time"])].dimensions,
        )
        for market_id in sorted(selected)
    )
    return registration.catalog, probability_dataset, derived_snapshot.ref, keys


def main() -> None:
    module = _load_parent()
    module._formal_catalog = _formal_catalog
    with TemporaryDirectory(prefix="chronos-formal-reversal-") as temporary:
        temporary_receipt = Path(temporary) / "parent-receipt.json"
        module.RECEIPT = temporary_receipt
        module.main()
        payload = json.loads(temporary_receipt.read_text())
    source_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    payload.update(
        {
            "driver_source_sha256": source_sha256,
            "corrected_parent_source_sha256": hashlib.sha256(
                PARENT_SOURCE.read_bytes()
            ).hexdigest(),
            "operational_correction": "sort derived price rows by market_id and observed_at before registration",
        }
    )
    content = json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n"
    if RECEIPT.exists() and RECEIPT.read_text() != content:
        raise ValueError("corrected formal receipt path already contains different bytes")
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(content)
    print(
        json.dumps(
            {
                "status": "SUCCEEDED",
                "receipt": str(RECEIPT),
                "receipt_sha256": hashlib.sha256(content.encode()).hexdigest(),
                "formal_gate_passed": payload["formal_gate_passed"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
