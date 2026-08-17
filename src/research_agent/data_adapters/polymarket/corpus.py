"""Immutable retention and temporal registration for resolved Polymarket corpora."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, cast

from research_agent.data_adapters.polymarket.models import (
    PolymarketCorpus,
    PolymarketCorpusContract,
    PolymarketCorpusOutcome,
    PolymarketCorpusRequest,
    PolymarketPricePoint,
    PolymarketResolutionRecord,
)
from research_agent.data_foundation import (
    DataCatalogSnapshot,
    DatasetSchema,
    FieldDefinition,
    ObservationInput,
    ObservationRegistrar,
    RegisteredDataset,
)

if TYPE_CHECKING:
    from pathlib import Path

_SNAPSHOT_SCHEMA = "polymarket-resolution-corpus-snapshot/v1"
_PRICE_DATASET = "polymarket-outcome-price-series"
_PRICE_SCHEMA = "polymarket-outcome-price-series/v1"
_RESOLUTION_DATASET = "polymarket-resolution-outcomes"
_RESOLUTION_SCHEMA = "polymarket-resolution-outcomes/v1"
_PRICE_AVAILABILITY = "polymarket-clob-price-sample/v1"
_RESOLUTION_AVAILABILITY = "polymarket-onchain-resolution/v1"
_PRICE_DIMENSIONS = (
    "market_id",
    "event_id",
    "outcome_index",
    "outcome_token",
    "fidelity",
)
_RESOLUTION_DIMENSIONS = (
    "market_id",
    "event_id",
    "outcome_index",
    "outcome_token",
)
_SHA256_LENGTH = 64


@dataclass(frozen=True, slots=True)
class PolymarketCorpusSnapshotRef:
    """Path-independent identity of one exact retained production corpus."""

    content_sha256: str
    size_bytes: int

    @property
    def uri(self) -> str:
        """Return the stable reference spelling used by provenance records."""
        return f"polymarket-corpus:{self.content_sha256}"

    def as_dict(self) -> dict[str, object]:
        """Return sanitized identity metadata without source values or a local path."""
        return {
            "kind": "PolymarketCorpusSnapshotRef",
            "uri": self.uri,
            "content_sha256": self.content_sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True, slots=True)
class PolymarketCorpusSnapshot:
    """Verified canonical corpus bytes resolved back into immutable records."""

    ref: PolymarketCorpusSnapshotRef
    corpus: PolymarketCorpus


@dataclass(frozen=True, slots=True)
class PolymarketCorpusRetention:
    """Sanitized result of retaining exact corpus bytes."""

    ref: PolymarketCorpusSnapshotRef


@dataclass(frozen=True, slots=True)
class PolymarketCorpusRegistration:
    """Separate predictor and mature-label registrations from one retained snapshot."""

    snapshot_ref: PolymarketCorpusSnapshotRef
    price_dataset: RegisteredDataset
    resolution_dataset: RegisteredDataset
    catalog: DataCatalogSnapshot


class PolymarketCorpusStore:
    """Minimal content-addressed store for exact production corpus bytes."""

    def __init__(self, root: Path) -> None:
        """Bind one operator-selected root without making its path scientific identity."""
        self.root = root.absolute()

    @staticmethod
    def from_corpus(corpus: PolymarketCorpus) -> PolymarketCorpusSnapshot:
        """Canonicalize one corpus and return its path-independent identity."""
        content = _canonical_bytes(corpus)
        ref = PolymarketCorpusSnapshotRef(_sha256(content), len(content))
        return PolymarketCorpusSnapshot(ref, corpus)

    def retain(self, corpus: PolymarketCorpus) -> PolymarketCorpusRetention:
        """Publish exact bytes once, reusing only byte-identical existing content."""
        snapshot = self.from_corpus(corpus)
        content = _canonical_bytes(corpus)
        path = self.object_path(snapshot.ref)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            if path.read_bytes() != content:
                msg = "retained Polymarket corpus identity conflicts with changed bytes"
                raise ValueError(msg) from None
        else:
            with os.fdopen(descriptor, "wb") as output:
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
        if not self.verify(snapshot.ref):
            msg = "retained Polymarket corpus failed content verification"
            raise ValueError(msg)
        return PolymarketCorpusRetention(snapshot.ref)

    def verify(self, ref: PolymarketCorpusSnapshotRef) -> bool:
        """Verify size and digest against the retained regular file."""
        path = self.object_path(ref)
        try:
            content = path.read_bytes()
        except OSError:
            return False
        return len(content) == ref.size_bytes and _sha256(content) == ref.content_sha256

    def load(self, ref: PolymarketCorpusSnapshotRef) -> PolymarketCorpusSnapshot:
        """Resolve verified bytes into strict records and recheck canonical identity."""
        if not self.verify(ref):
            msg = "cannot load an unverified Polymarket corpus snapshot"
            raise ValueError(msg)
        corpus = _decode_corpus(self.object_path(ref).read_bytes())
        snapshot = self.from_corpus(corpus)
        if snapshot.ref != ref:
            msg = "Polymarket corpus snapshot content does not match its reference"
            raise ValueError(msg)
        return snapshot

    def object_path(self, ref: PolymarketCorpusSnapshotRef) -> Path:
        """Return the local storage location without making it part of identity."""
        if len(ref.content_sha256) != _SHA256_LENGTH or any(
            character not in "0123456789abcdef" for character in ref.content_sha256
        ):
            msg = "Polymarket corpus reference must contain a lowercase SHA-256"
            raise ValueError(msg)
        return self.root / "objects" / ref.content_sha256[:2] / f"{ref.content_sha256}.json"


def register_polymarket_resolution_corpus(
    snapshot: PolymarketCorpusSnapshot,
) -> PolymarketCorpusRegistration:
    """Register prices as predictors and settlements as separately maturing labels."""
    corpus = snapshot.corpus
    environment_id = corpus.request.environment_id
    provenance = snapshot.ref.uri
    price_schema = DatasetSchema(
        dataset_id=_PRICE_DATASET,
        version=_PRICE_SCHEMA,
        environment_id=environment_id,
        provenance_ref=provenance,
        fields=(
            FieldDefinition(
                field_id="market_probability",
                semantic_name="sampled outcome-token probability price",
                data_type="float",
                unit="collateral_per_outcome_share",
                dimensions=_PRICE_DIMENSIONS,
                description="Historical CLOB probability sample for one exact outcome token.",
            ),
        ),
    )
    resolution_schema = DatasetSchema(
        dataset_id=_RESOLUTION_DATASET,
        version=_RESOLUTION_SCHEMA,
        environment_id=environment_id,
        provenance_ref=provenance,
        fields=(
            FieldDefinition(
                field_id="resolution_payout",
                semantic_name="on-chain outcome settlement payout",
                data_type="float",
                unit="collateral_per_outcome_share",
                dimensions=_RESOLUTION_DIMENSIONS,
                description="Final payout for one outcome, available at recorded settlement.",
            ),
        ),
    )
    contract_by_market = {item.market_id: item for item in corpus.contracts}
    price_rows = tuple(
        _price_observation(price_schema, snapshot.ref, contract_by_market[point.market_id], point)
        for point in corpus.prices
    )
    resolution_by_market = {item.market_id: item for item in corpus.resolutions}
    resolution_rows = tuple(
        _resolution_observation(
            resolution_schema,
            snapshot.ref,
            contract,
            resolution_by_market[contract.market_id],
            corpus.request.outcome_index,
        )
        for contract in corpus.contracts
    )
    registrar = ObservationRegistrar()
    price_dataset = registrar.register(price_schema, price_rows)
    resolution_dataset = registrar.register(resolution_schema, resolution_rows)
    catalog = DataCatalogSnapshot(environment_id, (price_dataset, resolution_dataset))
    return PolymarketCorpusRegistration(
        snapshot.ref,
        price_dataset,
        resolution_dataset,
        catalog,
    )


def _price_observation(
    schema: DatasetSchema,
    ref: PolymarketCorpusSnapshotRef,
    contract: PolymarketCorpusContract,
    point: PolymarketPricePoint,
) -> ObservationInput:
    dimensions = (
        ("market_id", point.market_id),
        ("event_id", contract.event_id),
        ("outcome_index", str(point.outcome_index)),
        ("outcome_token", point.outcome_token),
        ("fidelity", str(point.fidelity)),
    )
    source_ref = (
        f"polymarket-price:{point.market_id}:{point.outcome_index}:"
        f"{point.observed_at.isoformat()}:{point.fidelity}"
    )
    return ObservationInput(
        field_ref=schema.field_ref("market_probability"),
        value=float(point.price),
        reference_time=point.observed_at,
        available_at=point.observed_at,
        vintage_id=ref.uri,
        revision_number=0,
        source_ref=source_ref,
        provenance_ref=ref.uri,
        availability_rule_version=_PRICE_AVAILABILITY,
        dimensions=dimensions,
        caveats=(
            "sample timestamp is treated as public CLOB observation time",
            "sampling fidelity is explicit and this is not a transaction execution quote",
        ),
    )


def _resolution_observation(
    schema: DatasetSchema,
    ref: PolymarketCorpusSnapshotRef,
    contract: PolymarketCorpusContract,
    resolution: PolymarketResolutionRecord,
    outcome_index: int,
) -> ObservationInput:
    outcome = contract.outcomes[outcome_index]
    dimensions = (
        ("market_id", contract.market_id),
        ("event_id", contract.event_id),
        ("outcome_index", str(outcome_index)),
        ("outcome_token", outcome.outcome_token),
    )
    transaction = resolution.transaction_hash or "unrecorded"
    return ObservationInput(
        field_ref=schema.field_ref("resolution_payout"),
        value=float(resolution.payouts[outcome_index]),
        reference_time=contract.close_time,
        available_at=resolution.resolved_time,
        vintage_id=ref.uri,
        revision_number=0,
        source_ref=f"polymarket-resolution:{contract.market_id}:{transaction}",
        provenance_ref=ref.uri,
        availability_rule_version=_RESOLUTION_AVAILABILITY,
        dimensions=dimensions,
        caveats=("reference_time is contract close; available_at is recorded on-chain settlement",),
    )


def _canonical_bytes(corpus: PolymarketCorpus) -> bytes:
    return json.dumps(
        _corpus_payload(corpus),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _corpus_payload(corpus: PolymarketCorpus) -> dict[str, object]:
    return {
        "schema_version": _SNAPSHOT_SCHEMA,
        "request": {
            "environment_id": corpus.request.environment_id,
            "as_of": corpus.request.as_of.isoformat(),
            "min_points": corpus.request.min_points,
            "max_markets": corpus.request.max_markets,
            "outcome_index": corpus.request.outcome_index,
            "fidelity": corpus.request.fidelity,
        },
        "contracts": [
            {
                "market_id": item.market_id,
                "event_id": item.event_id,
                "market_type": item.market_type,
                "question": item.question,
                "open_time": item.open_time.isoformat(),
                "close_time": item.close_time.isoformat(),
                "outcomes": [
                    {
                        "outcome_index": outcome.outcome_index,
                        "label": outcome.label,
                        "outcome_token": outcome.outcome_token,
                        "payout": str(outcome.payout),
                    }
                    for outcome in item.outcomes
                ],
            }
            for item in corpus.contracts
        ],
        "resolutions": [
            {
                "market_id": item.market_id,
                "resolved_time": item.resolved_time.isoformat(),
                "payouts": [str(value) for value in item.payouts],
                "oracle": item.oracle,
                "question_id": item.question_id,
                "transaction_hash": item.transaction_hash,
            }
            for item in corpus.resolutions
        ],
        "prices": [
            {
                "market_id": item.market_id,
                "outcome_index": item.outcome_index,
                "outcome_token": item.outcome_token,
                "observed_at": item.observed_at.isoformat(),
                "price": str(item.price),
                "fidelity": item.fidelity,
            }
            for item in corpus.prices
        ],
    }


def _decode_corpus(content: bytes) -> PolymarketCorpus:
    raw = cast("dict[str, object]", json.loads(content))
    if raw.get("schema_version") != _SNAPSHOT_SCHEMA:
        msg = "unknown Polymarket corpus snapshot schema"
        raise ValueError(msg)
    request_raw = cast("dict[str, object]", raw["request"])
    request = PolymarketCorpusRequest(
        environment_id=str(request_raw["environment_id"]),
        as_of=datetime.fromisoformat(str(request_raw["as_of"])),
        min_points=int(cast("int", request_raw["min_points"])),
        max_markets=int(cast("int", request_raw["max_markets"])),
        outcome_index=int(cast("int", request_raw["outcome_index"])),
        fidelity=int(cast("int", request_raw["fidelity"])),
    )
    contracts = tuple(_decode_contract(item) for item in cast("list[object]", raw["contracts"]))
    resolutions = tuple(
        _decode_resolution(item) for item in cast("list[object]", raw["resolutions"])
    )
    prices = tuple(_decode_price(item) for item in cast("list[object]", raw["prices"]))
    return PolymarketCorpus(request, contracts, resolutions, prices)


def _decode_contract(value: object) -> PolymarketCorpusContract:
    raw = cast("dict[str, object]", value)
    outcomes = tuple(
        PolymarketCorpusOutcome(
            outcome_index=int(cast("int", item["outcome_index"])),
            label=str(item["label"]),
            outcome_token=str(item["outcome_token"]),
            payout=Decimal(str(item["payout"])),
        )
        for item in cast("list[dict[str, object]]", raw["outcomes"])
    )
    return PolymarketCorpusContract(
        market_id=str(raw["market_id"]),
        event_id=str(raw["event_id"]),
        market_type=str(raw["market_type"]),
        question=str(raw["question"]),
        open_time=datetime.fromisoformat(str(raw["open_time"])),
        close_time=datetime.fromisoformat(str(raw["close_time"])),
        outcomes=outcomes,
    )


def _decode_resolution(value: object) -> PolymarketResolutionRecord:
    raw = cast("dict[str, object]", value)
    return PolymarketResolutionRecord(
        market_id=str(raw["market_id"]),
        resolved_time=datetime.fromisoformat(str(raw["resolved_time"])),
        payouts=tuple(Decimal(str(item)) for item in cast("list[object]", raw["payouts"])),
        oracle=cast("str | None", raw["oracle"]),
        question_id=cast("str | None", raw["question_id"]),
        transaction_hash=cast("str | None", raw["transaction_hash"]),
    )


def _decode_price(value: object) -> PolymarketPricePoint:
    raw = cast("dict[str, object]", value)
    return PolymarketPricePoint(
        market_id=str(raw["market_id"]),
        outcome_index=int(cast("int", raw["outcome_index"])),
        outcome_token=str(raw["outcome_token"]),
        observed_at=datetime.fromisoformat(str(raw["observed_at"])),
        price=Decimal(str(raw["price"])),
        fidelity=int(cast("int", raw["fidelity"])),
    )
