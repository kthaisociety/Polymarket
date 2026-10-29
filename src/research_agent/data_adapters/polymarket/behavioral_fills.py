"""Immutable taker-fill panel for behavioral Polymarket research."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Protocol, cast

from research_agent.data_adapters.polymarket.corpus_analysis import (
    PolymarketDevelopmentAnalysis,
    build_polymarket_development_analysis,
)
from research_agent.data_foundation._identity import require_aware
from research_agent.exploration import (
    AnalysisHarness,
    ArtifactStore,
    AuthorizedDataView,
    CapabilityPolicy,
    ResourceLimits,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from research_agent.data_adapters.polymarket.corpus import PolymarketCorpusSnapshot
    from research_agent.exploration.sandbox import JsonValue

_SCHEMA = "polymarket-behavioral-taker-fill-corpus/v1"
_SHA256_LENGTH = 64
_TWO_OUTCOMES = 2


class _FetchConnection(Protocol):
    async def fetch(self, query: str, *args: object) -> Sequence[Mapping[str, object]]:
        """Return rows from one bounded parameterized SELECT."""
        ...


@dataclass(frozen=True, slots=True)
class BehavioralFillRequest:
    """Exact fixed ceiling and parent corpus for one taker-fill acquisition."""

    environment_id: str
    as_of: datetime
    parent_snapshot_ref: str

    def __post_init__(self) -> None:
        """Require an aware ceiling and explicit parent authority."""
        require_aware(self.as_of, "as_of")
        if not self.environment_id or not self.parent_snapshot_ref:
            msg = "behavioral fill request requires environment and parent snapshot identities"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class BehavioralTakerFill:
    """One aggregate taker leg with its public block-time identity."""

    account: str
    market_id: str
    fill_time: datetime
    fill_uid: str
    outcome_index: int
    side: str
    price: Decimal
    size: Decimal
    block_number: int
    transaction_hash: str

    def __post_init__(self) -> None:
        """Reject ambiguous legs and invalid probability-price records."""
        require_aware(self.fill_time, "fill_time")
        if not all((self.account, self.market_id, self.fill_uid, self.transaction_hash)):
            msg = "behavioral fill identity fields must be non-empty"
            raise ValueError(msg)
        if (
            self.outcome_index not in range(_TWO_OUTCOMES)
            or self.side not in {"BUY", "SELL"}
            or not Decimal(0) <= self.price <= Decimal(1)
            or self.size <= 0
            or self.block_number < 0
        ):
            msg = "behavioral fill has invalid side, outcome, price, size, or block"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class BehavioralFillCorpus:
    """Ordered exact taker rows joined only later to a protected event partition."""

    request: BehavioralFillRequest
    fills: tuple[BehavioralTakerFill, ...]

    def __post_init__(self) -> None:
        """Require nonempty, unique, deterministic rows below the fixed ceiling."""
        if not self.fills:
            msg = "behavioral fill corpus must contain at least one taker leg"
            raise ValueError(msg)
        identities = tuple(item.fill_uid for item in self.fills)
        if len(set(identities)) != len(identities):
            msg = "behavioral fill corpus contains duplicate fill identities"
            raise ValueError(msg)
        if any(item.fill_time > self.request.as_of for item in self.fills):
            msg = "behavioral fill corpus exceeds its fixed as-of ceiling"
            raise ValueError(msg)
        ordered = tuple(sorted(self.fills, key=lambda item: (item.fill_time, item.fill_uid)))
        if self.fills != ordered:
            msg = "behavioral fill corpus must use deterministic chronological ordering"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class BehavioralFillSnapshotRef:
    """Path-independent identity of one retained taker-fill panel."""

    content_sha256: str
    size_bytes: int

    @property
    def uri(self) -> str:
        """Return the stable provenance spelling."""
        return f"polymarket-behavioral-fills:{self.content_sha256}"

    def as_dict(self) -> dict[str, object]:
        """Return identity metadata without account or trade values."""
        return {
            "kind": type(self).__name__,
            "uri": self.uri,
            "content_sha256": self.content_sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True, slots=True)
class BehavioralFillSnapshot:
    """Verified canonical fill bytes decoded into strict records."""

    ref: BehavioralFillSnapshotRef
    corpus: BehavioralFillCorpus


class BehavioralFillStore:
    """Content-addressed storage for exact behavioral taker-fill inputs."""

    def __init__(self, root: Path) -> None:
        """Bind one local root without incorporating its path into identity."""
        self.root = root.absolute()

    @staticmethod
    def from_corpus(corpus: BehavioralFillCorpus) -> BehavioralFillSnapshot:
        """Canonicalize one in-memory corpus."""
        content = _canonical_bytes(corpus)
        return BehavioralFillSnapshot(
            BehavioralFillSnapshotRef(hashlib.sha256(content).hexdigest(), len(content)),
            corpus,
        )

    def retain(self, corpus: BehavioralFillCorpus) -> BehavioralFillSnapshotRef:
        """Publish canonical bytes once and verify the retained object."""
        snapshot = self.from_corpus(corpus)
        content = _canonical_bytes(corpus)
        path = self.object_path(snapshot.ref)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            if path.read_bytes() != content:
                msg = "behavioral fill snapshot identity conflicts with changed bytes"
                raise ValueError(msg) from None
        else:
            with os.fdopen(descriptor, "wb") as output:
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
        if not self.verify(snapshot.ref):
            msg = "retained behavioral fill snapshot failed verification"
            raise ValueError(msg)
        return snapshot.ref

    def verify(self, ref: BehavioralFillSnapshotRef) -> bool:
        """Verify exact size and digest of one retained object."""
        try:
            content = self.object_path(ref).read_bytes()
        except OSError:
            return False
        return len(content) == ref.size_bytes and hashlib.sha256(content).hexdigest() == (
            ref.content_sha256
        )

    def load(self, ref: BehavioralFillSnapshotRef) -> BehavioralFillSnapshot:
        """Decode verified bytes and recheck canonical identity."""
        if not self.verify(ref):
            msg = "cannot load an unverified behavioral fill snapshot"
            raise ValueError(msg)
        corpus = _decode_corpus(self.object_path(ref).read_bytes())
        snapshot = self.from_corpus(corpus)
        if snapshot.ref != ref:
            msg = "behavioral fill content does not match its reference"
            raise ValueError(msg)
        return snapshot

    def object_path(self, ref: BehavioralFillSnapshotRef) -> Path:
        """Return the validated local content-addressed path."""
        if len(ref.content_sha256) != _SHA256_LENGTH or any(
            character not in "0123456789abcdef" for character in ref.content_sha256
        ):
            msg = "behavioral fill reference must contain a lowercase SHA-256"
            raise ValueError(msg)
        return self.root / "objects" / ref.content_sha256[:2] / f"{ref.content_sha256}.json"


class DatabaseBehavioralFillReader:
    """Bounded SELECT-only reader for aggregate Polymarket taker legs."""

    def __init__(self, connection: _FetchConnection) -> None:
        """Bind an already proved read-only transaction connection."""
        self._connection = connection

    async def read_corpus(
        self,
        request: BehavioralFillRequest,
        *,
        market_ids: tuple[str, ...],
    ) -> BehavioralFillCorpus:
        """Read only exact parent-corpus markets below the fixed ceiling."""
        if not market_ids or len(set(market_ids)) != len(market_ids):
            msg = "behavioral fill acquisition requires unique parent market identities"
            raise ValueError(msg)
        rows = await self._connection.fetch(_FILL_QUERY, market_ids, request.as_of)
        fills = tuple(
            sorted(
                (_decode_database_fill(row) for row in rows),
                key=lambda item: (item.fill_time, item.fill_uid),
            )
        )
        return BehavioralFillCorpus(request, fills)


def build_behavioral_fill_analysis(
    parent: PolymarketCorpusSnapshot,
    fill_snapshot: BehavioralFillSnapshot,
    *,
    session_id: str,
    resource_limits: ResourceLimits | None = None,
) -> PolymarketDevelopmentAnalysis:
    """Join retained taker legs to only the parent corpus's development events."""
    if fill_snapshot.corpus.request.parent_snapshot_ref != parent.ref.uri:
        msg = "behavioral fill panel belongs to a different parent corpus"
        raise ValueError(msg)
    if fill_snapshot.corpus.request.environment_id != parent.corpus.request.environment_id:
        msg = "behavioral fill panel belongs to a different environment"
        raise ValueError(msg)
    base = build_polymarket_development_analysis(
        parent,
        session_id=session_id,
        resource_limits=resource_limits,
    )
    fill_view = _behavioral_fill_view(base, fill_snapshot)
    artifacts = ArtifactStore()
    views = (base.price_view, base.outcome_view, fill_view)
    limits = resource_limits or base.resource_limits
    harness = AnalysisHarness(
        views={view.view_id: view for view in views},
        policy=CapabilityPolicy(
            session_id=session_id,
            environment_ref=base.price_view.environment_ref,
            allowed_fields_by_view={view.view_id: frozenset(view.fields) for view in views},
        ),
        artifacts=artifacts,
        resource_limits=limits,
    )
    return PolymarketDevelopmentAnalysis(
        partition=base.partition,
        price_view=base.price_view,
        outcome_view=base.outcome_view,
        registered_event_views=(fill_view,),
        harness=harness,
        artifacts=artifacts,
        resource_limits=limits,
    )


def behavioral_fill_query_sha256() -> str:
    """Return the exact bounded production-query identity used by the reader."""
    return hashlib.sha256(_FILL_QUERY.encode()).hexdigest()


def _behavioral_fill_view(
    analysis: PolymarketDevelopmentAnalysis,
    snapshot: BehavioralFillSnapshot,
) -> AuthorizedDataView:
    outcome_fields = analysis.outcome_view.fields
    market_ids = cast("tuple[str, ...]", outcome_fields["market_id"])
    event_ids = cast("tuple[str, ...]", outcome_fields["event_id"])
    event_ordinals = cast("tuple[int, ...]", outcome_fields["event_chronological_ordinal"])
    event_by_market = dict(zip(market_ids, event_ids, strict=True))
    ordinal_by_event = dict(zip(event_ids, event_ordinals, strict=True))
    visible_event_count = len(analysis.partition.development_event_ids)
    rows = tuple(item for item in snapshot.corpus.fills if item.market_id in event_by_market)
    fields: dict[str, tuple[JsonValue, ...]] = {
        "account": tuple(item.account for item in rows),
        "market_id": tuple(item.market_id for item in rows),
        "event_id": tuple(event_by_market[item.market_id] for item in rows),
        "event_chronological_ordinal": tuple(
            ordinal_by_event[event_by_market[item.market_id]] for item in rows
        ),
        "research_partition": tuple(
            "TRAIN"
            if (ordinal_by_event[event_by_market[item.market_id]] + 1) * 4
            <= visible_event_count * 3
            else "EVALUATION"
            for item in rows
        ),
        "fill_time_epoch_seconds": tuple(item.fill_time.timestamp() for item in rows),
        "fill_uid": tuple(item.fill_uid for item in rows),
        "outcome_index": tuple(item.outcome_index for item in rows),
        "side": tuple(item.side for item in rows),
        "price": tuple(float(item.price) for item in rows),
        "size": tuple(float(item.size) for item in rows),
        "block_number": tuple(item.block_number for item in rows),
        "transaction_hash": tuple(item.transaction_hash for item in rows),
    }
    if not rows:
        msg = "behavioral fill panel has no rows in the development partition"
        raise ValueError(msg)
    return AuthorizedDataView(
        view_id="polymarket-development-taker-fills",
        dataset_ref=(f"{snapshot.ref.uri}:partition:{analysis.partition.partition_id}"),
        environment_ref=analysis.price_view.environment_ref,
        fields=fields,
    )


def _decode_database_fill(row: Mapping[str, object]) -> BehavioralTakerFill:
    return BehavioralTakerFill(
        account=str(row["account"]),
        market_id=str(row["market_id"]),
        fill_time=cast("datetime", row["fill_time"]),
        fill_uid=str(row["fill_uid"]),
        outcome_index=int(cast("int", row["outcome_index"])),
        side=str(row["side"]),
        price=Decimal(str(row["price"])),
        size=Decimal(str(row["size"])),
        block_number=int(cast("int", row["block_number"])),
        transaction_hash=str(row["transaction_hash"]),
    )


def _canonical_bytes(corpus: BehavioralFillCorpus) -> bytes:
    payload = {
        "schema_version": _SCHEMA,
        "request": {
            "environment_id": corpus.request.environment_id,
            "as_of": corpus.request.as_of.isoformat(),
            "parent_snapshot_ref": corpus.request.parent_snapshot_ref,
        },
        "fills": [
            {
                "account": item.account,
                "market_id": item.market_id,
                "fill_time": item.fill_time.isoformat(),
                "fill_uid": item.fill_uid,
                "outcome_index": item.outcome_index,
                "side": item.side,
                "price": str(item.price),
                "size": str(item.size),
                "block_number": item.block_number,
                "transaction_hash": item.transaction_hash,
            }
            for item in corpus.fills
        ],
    }
    return (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode()


def _decode_corpus(content: bytes) -> BehavioralFillCorpus:
    raw = cast("dict[str, object]", json.loads(content))
    if raw.get("schema_version") != _SCHEMA:
        msg = "unsupported behavioral fill snapshot schema"
        raise ValueError(msg)
    request = cast("dict[str, object]", raw["request"])
    fills = cast("list[dict[str, object]]", raw["fills"])
    return BehavioralFillCorpus(
        BehavioralFillRequest(
            environment_id=str(request["environment_id"]),
            as_of=datetime.fromisoformat(str(request["as_of"])),
            parent_snapshot_ref=str(request["parent_snapshot_ref"]),
        ),
        tuple(
            BehavioralTakerFill(
                account=str(item["account"]),
                market_id=str(item["market_id"]),
                fill_time=datetime.fromisoformat(str(item["fill_time"])),
                fill_uid=str(item["fill_uid"]),
                outcome_index=int(cast("int", item["outcome_index"])),
                side=str(item["side"]),
                price=Decimal(str(item["price"])),
                size=Decimal(str(item["size"])),
                block_number=int(cast("int", item["block_number"])),
                transaction_hash=str(item["transaction_hash"]),
            )
            for item in fills
        ),
    )


_FILL_QUERY = """
SELECT f.account,
       f.market_id,
       f.fill_time,
       f.fill_uid,
       f.outcome_index,
       f.side,
       f.price,
       f.size,
       (f.raw->>'block_number')::bigint AS block_number,
       f.tx_hash AS transaction_hash
FROM market.fills AS f
WHERE f.venue = 'polymarket'
  AND f.market_id = ANY($1::text[])
  AND f.fill_time <= $2
  AND f.account IS NOT NULL
  AND f.tx_hash IS NOT NULL
  AND f.price BETWEEN 0 AND 1
  AND f.size > 0
  AND lower('0x' || right(f.raw->'topics'->>3, 40)) = lower(f.raw->>'address')
"""


__all__ = [
    "BehavioralFillCorpus",
    "BehavioralFillRequest",
    "BehavioralFillSnapshot",
    "BehavioralFillSnapshotRef",
    "BehavioralFillStore",
    "BehavioralTakerFill",
    "DatabaseBehavioralFillReader",
    "behavioral_fill_query_sha256",
    "build_behavioral_fill_analysis",
]
