"""Register a pinned Polymarket contract tape as temporal observations."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from research_agent.data_foundation import (
    DataCatalogSnapshot,
    DatasetSchema,
    FieldDefinition,
    ObservationInput,
    ObservationRegistrar,
    RegisteredDataset,
)

if TYPE_CHECKING:
    from research_agent.data_adapters.polymarket.models import (
        PolymarketBlockVintage,
        PolymarketContractRecord,
        PolymarketFillRecord,
        PolymarketImportRequest,
    )
    from research_agent.data_adapters.polymarket.reader import PolymarketResearchReader

_DATASET_ID = "polymarket-contract-taker-tape"
_SCHEMA_VERSION = "polymarket-contract-taker-tape/v1"
_AVAILABILITY_RULE = "polymarket-onchain-block-inclusion/v1"
_DIMENSIONS = ("market_id", "outcome_index", "outcome_token", "fill_uid")
_FIELDS = (
    FieldDefinition(
        field_id="trade_price",
        semantic_name="taker-side transaction price",
        data_type="float",
        unit="collateral_per_outcome_share",
        dimensions=_DIMENSIONS,
        description="Executed outcome-share price from one exact taker-side print.",
    ),
    FieldDefinition(
        field_id="trade_size",
        semantic_name="taker-side transaction size",
        data_type="float",
        unit="outcome_shares",
        dimensions=_DIMENSIONS,
        description="Absolute outcome-share quantity from one exact taker-side print.",
    ),
    FieldDefinition(
        field_id="signed_trade_size",
        semantic_name="aggressor-signed transaction size",
        data_type="float",
        unit="outcome_shares",
        dimensions=_DIMENSIONS,
        description="BUY-positive and SELL-negative taker-side outcome-share quantity.",
    ),
    FieldDefinition(
        field_id="block_number",
        semantic_name="Polygon inclusion block",
        data_type="int",
        unit="polygon_block",
        dimensions=_DIMENSIONS,
        description="Exact Polygon block number retained with the normalized fill.",
    ),
)


@dataclass(frozen=True, slots=True)
class PolymarketIngestionResult:
    """Immutable receipt for one exact contract-tape registration."""

    request: PolymarketImportRequest
    vintage: PolymarketBlockVintage
    contracts: tuple[PolymarketContractRecord, ...]
    source_digest: str
    included_fill_count: int
    excluded_fill_count: int
    snapshot_caveats: tuple[str, ...]
    registered: RegisteredDataset
    catalog: DataCatalogSnapshot


async def ingest_polymarket_contract_tape(
    reader: PolymarketResearchReader,
    request: PolymarketImportRequest,
) -> PolymarketIngestionResult:
    """Read, validate, and register one exact block-windowed contract tape.

    Args:
        reader: Read-only production fact interface or a protocol-compatible test executor.
        request: Exact contract scope and environment identity.

    Returns:
        Registration receipt with exact vintage, source digest, and exclusion counts.

    Raises:
        ValueError: If the source facts are incomplete, ambiguous, or inconsistent.
        RuntimeError: If a production read fails.

    """
    vintage = await reader.read_vintage()
    contracts = await reader.read_contracts(request.market_ids)
    _validate_contracts(contracts, request.market_ids)
    fills: list[PolymarketFillRecord] = []
    excluded = 0
    contract_by_id = {contract.market_id: contract for contract in contracts}
    for market_id in request.market_ids:
        tape = await reader.read_fills(market_id)
        _validate_tape(tape, contract_by_id[market_id])
        for fill in tape:
            if fill.block_number is None:
                msg = f"Polymarket fill {fill.fill_uid} has no exact block number"
                raise ValueError(msg)
            if vintage.lower_block <= fill.block_number <= vintage.upper_block:
                fills.append(fill)
            else:
                excluded += 1
    if not fills:
        msg = "Polymarket import contains no fills inside the declared block vintage"
        raise ValueError(msg)
    _require_unique_fill_ids(fills)
    schema = DatasetSchema(
        dataset_id=_DATASET_ID,
        version=_SCHEMA_VERSION,
        environment_id=request.environment_id,
        provenance_ref=(
            "bdl-engine:market.reads.read_market_taker_fills+"
            "read_identity+read_outcome_counts+read_close_times+read_resolved_market_ids"
        ),
        fields=_FIELDS,
    )
    rows = tuple(row for fill in fills for row in _observation_rows(schema, fill, vintage))
    registered = ObservationRegistrar().register(schema, rows)
    catalog = DataCatalogSnapshot(request.environment_id, (registered,))
    return PolymarketIngestionResult(
        request=request,
        vintage=vintage,
        contracts=contracts,
        source_digest=_source_digest(contracts, fills, vintage),
        included_fill_count=len(fills),
        excluded_fill_count=excluded,
        snapshot_caveats=(
            (
                "block bounds exclude later rows outside the window but do not prevent "
                "scope-repair backfill from inserting rows inside it"
            ),
            "source_digest detects an in-window change on rerun but cannot reconstruct prior bytes",
            "fill_time is public-chain observability, not collector or database arrival time",
            (
                "resolved payouts are descriptive metadata only until resolution availability "
                "is registered under an exact rule"
            ),
            "event/group identity is unavailable through the current public engine read surface",
        ),
        registered=registered,
        catalog=catalog,
    )


def _validate_contracts(
    contracts: tuple[PolymarketContractRecord, ...], requested: tuple[str, ...]
) -> None:
    actual = tuple(contract.market_id for contract in contracts)
    if actual != requested:
        msg = "Polymarket contract metadata does not exactly match the requested scope"
        raise ValueError(msg)


def _validate_tape(
    fills: tuple[PolymarketFillRecord, ...], contract: PolymarketContractRecord
) -> None:
    outcome_tokens = {
        (outcome.outcome_index, outcome.outcome_token) for outcome in contract.outcomes
    }
    for fill in fills:
        if fill.market_id != contract.market_id:
            msg = "Polymarket tape returned a fill for a different contract"
            raise ValueError(msg)
        if (fill.outcome_index, fill.outcome_token) not in outcome_tokens:
            msg = f"Polymarket fill {fill.fill_uid} has unknown outcome identity"
            raise ValueError(msg)
        if fill.side not in {"BUY", "SELL"} or not fill.fill_uid:
            msg = f"Polymarket fill {fill.fill_uid!r} has invalid side or identity"
            raise ValueError(msg)
        if fill.fill_time.tzinfo is None or fill.fill_time.utcoffset() is None:
            msg = f"Polymarket fill {fill.fill_uid} has a naive event time"
            raise ValueError(msg)


def _require_unique_fill_ids(fills: list[PolymarketFillRecord]) -> None:
    identities = tuple(fill.fill_uid for fill in fills)
    if len(set(identities)) != len(identities):
        msg = "Polymarket tape contains duplicate fill identities"
        raise ValueError(msg)


def _observation_rows(
    schema: DatasetSchema,
    fill: PolymarketFillRecord,
    vintage: PolymarketBlockVintage,
) -> tuple[ObservationInput, ...]:
    if fill.block_number is None:
        msg = "an exact block is required before observation construction"
        raise ValueError(msg)
    dimensions = (
        ("market_id", fill.market_id),
        ("outcome_index", str(fill.outcome_index)),
        ("outcome_token", fill.outcome_token),
        ("fill_uid", fill.fill_uid),
    )
    source_ref = f"polymarket-fill:{fill.market_id}:{fill.fill_uid}"
    transaction = fill.transaction_hash or "unrecorded"
    provenance_ref = (
        f"bdl-market-fills:block={fill.block_number}:transaction={transaction}:"
        f"vintage={vintage.identity}"
    )
    caveats = (
        "available_at uses the on-chain block timestamp recorded as fill_time",
        "confirmation and collector latency are not modeled by this availability rule",
    )
    signed_size = fill.size if fill.side == "BUY" else -fill.size
    values: tuple[tuple[str, int | float], ...] = (
        ("trade_price", float(fill.price)),
        ("trade_size", float(fill.size)),
        ("signed_trade_size", float(signed_size)),
        ("block_number", fill.block_number),
    )
    return tuple(
        ObservationInput(
            field_ref=schema.field_ref(field_id),
            value=value,
            reference_time=fill.fill_time,
            available_at=fill.fill_time,
            vintage_id=vintage.identity,
            revision_number=0,
            source_ref=source_ref,
            provenance_ref=provenance_ref,
            availability_rule_version=_AVAILABILITY_RULE,
            dimensions=dimensions,
            caveats=caveats,
        )
        for field_id, value in values
    )


def _source_digest(
    contracts: tuple[PolymarketContractRecord, ...],
    fills: list[PolymarketFillRecord],
    vintage: PolymarketBlockVintage,
) -> str:
    payload = {
        "vintage": vintage.identity,
        "contracts": [
            {
                "market_id": contract.market_id,
                "outcomes": [
                    [
                        outcome.outcome_index,
                        outcome.outcome_token,
                        None if outcome.resolved_payout is None else str(outcome.resolved_payout),
                    ]
                    for outcome in contract.outcomes
                ],
                "close_time": (
                    None if contract.close_time is None else contract.close_time.isoformat()
                ),
                "resolved": contract.resolved,
            }
            for contract in contracts
        ],
        "fills": [
            {
                "fill_uid": fill.fill_uid,
                "fill_time": fill.fill_time.isoformat(),
                "market_id": fill.market_id,
                "outcome_index": fill.outcome_index,
                "outcome_token": fill.outcome_token,
                "side": fill.side,
                "price": str(fill.price),
                "size": str(fill.size),
                "block_number": fill.block_number,
                "transaction_hash": fill.transaction_hash,
            }
            for fill in fills
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()
