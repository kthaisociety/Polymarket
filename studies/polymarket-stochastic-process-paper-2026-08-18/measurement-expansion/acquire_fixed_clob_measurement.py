"""Acquire the ten fixed official CLOB slices through Chronos's exact public boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from research_agent.data_adapters.polymarket.source_expansion import (
    PolymarketPriceHistoryNeed,
    PolymarketSourceExpansionError,
    expand_scouted_price_history,
    price_history_search_request,
)
from research_agent.data_workspace import (
    DataWorkspace,
    RecordedSourceScoutProvider,
    ScoutingStatus,
    SourceScoutingService,
)

_DOCUMENTATION_URL = "https://docs.polymarket.com/api-reference/markets/get-prices-history"
_EXPECTED_NEEDS = (
    "event-010.json",
    "event-025.json",
    "event-040.json",
    "event-055.json",
    "event-070.json",
    "event-085.json",
    "event-100.json",
    "event-115.json",
    "event-130.json",
    "event-145.json",
)
_QUESTION = "Do hourly Polymarket process signatures survive at five-minute sampling fidelity?"


def _candidate(need: PolymarketPriceHistoryNeed) -> dict[str, object]:
    return {
        "title": "Official Polymarket CLOB price history for one fixed development outcome",
        "resource_url": need.resource_url,
        "landing_page_url": _DOCUMENTATION_URL,
        "publisher": "Polymarket",
        "description": "Documented historical probability samples for one exact outcome asset.",
        "why_relevant": "Tests whether hourly process signatures survive five-minute sampling.",
        "temporal_coverage": "Exact requested bounds; retained response determines actual coverage.",
        "frequency": "Five-minute requested fidelity; endpoint sampling remains caveated.",
        "license": "Polymarket public API terms; retained for reproducible research audit.",
        "access_notes": "Public HTTPS GET without credentials; redirects are refused.",
        "risks": [
            "Samples are not trades or executable quotes.",
            "Historical revisions or deletions are not established by the endpoint.",
        ],
        "evidence_urls": [_DOCUMENTATION_URL],
    }


def _persist(payload: dict[str, object], path: Path) -> None:
    content = (json.dumps(payload, allow_nan=False, separators=(",", ":"), sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as receipt_file:
            receipt_file.write(content)
    except FileExistsError:
        if path.read_bytes() != content:
            raise ValueError("measurement acquisition receipt already contains different bytes") from None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--need-directory", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--timeout-seconds", default=30.0, type=float)
    parser.add_argument("--max-bytes", default=16 * 1024 * 1024, type=int)
    arguments = parser.parse_args()

    observed_names = tuple(sorted(path.name for path in arguments.need_directory.glob("*.json")))
    if observed_names != _EXPECTED_NEEDS:
        raise ValueError("measurement acquisition requires exactly the ten fixed need documents")

    workspace = DataWorkspace(arguments.workspace)
    slices: list[dict[str, object]] = []
    for name in _EXPECTED_NEEDS:
        need_path = arguments.need_directory / name
        need = PolymarketPriceHistoryNeed.from_dict(json.loads(need_path.read_text()))
        request = price_history_search_request(need, research_question=_QUESTION)
        provider = RecordedSourceScoutProvider(
            provider_id="codex-official-polymarket-docs-scout-2026-08-18@1",
            response={
                "schema_version": "source-scout-response/v1",
                "candidates": [_candidate(need)],
            },
        )
        scouting = SourceScoutingService(workspace, provider).scout(
            request,
            idempotency_key=f"paper-five-minute:{need.need_id}",
        )
        if scouting.status is not ScoutingStatus.SUCCEEDED or scouting.report_ref is None:
            slices.append(
                {
                    "need_id": need.need_id,
                    "need_file": name,
                    "request_id": request.request_id,
                    "status": "scouting_failed",
                }
            )
            continue
        candidate_id = scouting.report_ref.candidate_ids[0]
        try:
            expansion = expand_scouted_price_history(
                workspace,
                report_ref=scouting.report_ref,
                candidate_id=candidate_id,
                need=need,
                timeout_seconds=arguments.timeout_seconds,
                max_response_bytes=arguments.max_bytes,
            )
        except PolymarketSourceExpansionError:
            slices.append(
                {
                    "candidate_id": candidate_id,
                    "need_id": need.need_id,
                    "need_file": name,
                    "report_ref": scouting.report_ref.uri,
                    "request_id": request.request_id,
                    "status": "acquisition_or_registration_failed",
                }
            )
            continue
        slices.append(
            {
                "candidate_id": candidate_id,
                "need_file": name,
                "report_ref": scouting.report_ref.uri,
                "request_id": request.request_id,
                **expansion.as_dict(),
            }
        )

    succeeded = sum(item["status"] == "succeeded" for item in slices)
    payload: dict[str, object] = {
        "schema_version": "polymarket-fixed-clob-acquisition-receipt/v1",
        "status": "succeeded" if succeeded == len(_EXPECTED_NEEDS) else "partial_or_failed",
        "requested_slice_count": len(_EXPECTED_NEEDS),
        "succeeded_slice_count": succeeded,
        "sample_values_emitted": False,
        "production_database_writes": False,
        "slices": slices,
    }
    _persist(payload, arguments.receipt)
    print(json.dumps(payload, allow_nan=False, sort_keys=True))
    return 0 if succeeded == len(_EXPECTED_NEEDS) else 3


if __name__ == "__main__":
    raise SystemExit(main())
