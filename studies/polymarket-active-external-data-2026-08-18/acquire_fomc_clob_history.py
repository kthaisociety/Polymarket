# ruff: noqa: D103, E501, EM101, INP001, S105, T201, TRY003

"""Acquire and register one exact official CLOB history slice for the FOMC candidate."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from research_agent.data_adapters.polymarket import (
    PolymarketPriceHistoryNeed,
    expand_scouted_price_history,
    price_history_search_request,
)
from research_agent.data_workspace import (
    DataWorkspace,
    RecordedSourceScoutProvider,
    ScoutingStatus,
    SourceScoutingService,
)

_MARKET_ID = "0x876506d8b2bd7a0d3fa4fe18c024eee6e1dd81ee24c26795dadd6cfe4a7b5d0d"
_EVENT_ID = "481717"
_YES_TOKEN = "63842529068710005716169325380315470359047749786610778647370693404952498013178"
_DOCUMENTATION_URL = "https://docs.polymarket.com/api-reference/markets/get-prices-history"


def _candidate(need: PolymarketPriceHistoryNeed) -> dict[str, object]:
    return {
        "title": "Official Polymarket CLOB price history for the September +25 bp outcome",
        "resource_url": need.resource_url,
        "landing_page_url": _DOCUMENTATION_URL,
        "publisher": "Polymarket",
        "description": "Documented sampled historical probability series for the exact YES token.",
        "why_relevant": "Aligns an independent CME probability with later Polymarket movement.",
        "temporal_coverage": "Exact requested bounds; retained response determines actual coverage.",
        "frequency": "One-minute requested fidelity; actual endpoint samples remain caveated.",
        "license": "Polymarket public API terms; retained for reproducible research audit.",
        "access_notes": "Public HTTPS GET without credentials; redirects refused.",
        "risks": [
            "Samples are probabilities, not executable quotes.",
            "Historical revision behavior is not established.",
        ],
        "evidence_urls": [_DOCUMENTATION_URL],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    need = PolymarketPriceHistoryNeed(
        environment_id="bdl-polymarket-production-readonly",
        market_id=_MARKET_ID,
        event_id=_EVENT_ID,
        outcome_index=0,
        outcome_token=_YES_TOKEN,
        start_time=datetime.fromisoformat("2026-08-06T23:20:00+00:00"),
        end_time=datetime.fromisoformat("2026-08-18T19:32:00+00:00"),
        fidelity_minutes=1,
    )
    workspace = DataWorkspace(args.workspace)
    request = price_history_search_request(
        need,
        research_question=(
            "Do conservative dated CME FedWatch changes lead the exact September +25 bp "
            "Polymarket outcome after costs?"
        ),
    )
    provider = RecordedSourceScoutProvider(
        provider_id="codex-official-polymarket-docs-scout-2026-08-18@1",
        response={
            "schema_version": "source-scout-response/v1",
            "candidates": [_candidate(need)],
        },
    )
    scouting = SourceScoutingService(workspace, provider).scout(
        request,
        idempotency_key=f"fomc-fedwatch:{need.need_id}",
    )
    if scouting.status is not ScoutingStatus.SUCCEEDED or scouting.report_ref is None:
        raise SystemExit("source scouting failed")
    expansion = expand_scouted_price_history(
        workspace,
        report_ref=scouting.report_ref,
        candidate_id=scouting.report_ref.candidate_ids[0],
        need=need,
        timeout_seconds=30,
    )
    payload = {
        "schema": "chronos-fomc-clob-expansion/v1",
        "need": need.as_dict(),
        **expansion.as_dict(),
    }
    content = (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode()
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.receipt.open("xb") as output:
            output.write(content)
    except FileExistsError:
        if args.receipt.read_bytes() != content:
            raise ValueError("receipt already contains different bytes") from None
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
