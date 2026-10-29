"""Exact dual-clock L2 retention, replay, and temporal registration."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from itertools import groupby
from typing import TYPE_CHECKING, Literal, Protocol, cast

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

type BookVenue = Literal["kalshi", "polymarket"]
type BookSide = Literal["ASK", "BID"]
type BookEventRecord = BookSnapshotRecord | BookDeltaRecord

_SNAPSHOT_SCHEMA = "cross-venue-book-corpus-snapshot/v1"
_DATASET_ID = "cross-venue-decoded-book-top"
_DATASET_SCHEMA = "cross-venue-decoded-book-top/v1"
_AVAILABILITY_RULE = "decoded-book-collector-absorb/v1"
_TOP_FIELDS = (
    ("best_bid_price", "best executable bid price", "collateral_per_outcome_share"),
    ("best_ask_price", "best executable ask price", "collateral_per_outcome_share"),
    ("best_bid_size", "displayed size at best bid", "outcome_shares"),
    ("best_ask_size", "displayed size at best ask", "outcome_shares"),
)
_DEPTH_FIELDS = (
    (
        "depth_price",
        "displayed limit price at one retained depth level",
        "collateral_per_outcome_share",
    ),
    ("depth_size", "displayed size at one retained depth level", "outcome_shares"),
)
_TOP_DIMENSIONS = ("venue", "market_id", "outcome_index", "event_ordinal", "seq")
_DEPTH_DIMENSIONS = (*_TOP_DIMENSIONS, "side", "level")
_SHA256_LENGTH = 64
_LEVEL_WIDTH = 2


class _FetchExecutor(Protocol):
    """Small parameterized SELECT surface implemented by asyncpg and test fakes."""

    async def fetch(self, query: str, *args: object) -> Sequence[Mapping[str, object]]:
        """Return rows for one read-only query."""
        ...


def _require_aware(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        msg = f"{field} must be timezone-aware"
        raise ValueError(msg)


@dataclass(frozen=True, slots=True, order=True)
class BookLeg:
    """One exact venue/market/outcome quoted leg."""

    venue: BookVenue
    market_id: str
    outcome_index: int

    def __post_init__(self) -> None:
        """Reject incomplete or unsupported leg identity."""
        if (
            self.venue not in ("kalshi", "polymarket")
            or not self.market_id
            or self.outcome_index < 0
        ):
            msg = "book leg requires an exact supported venue, market, and outcome"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class BookCorpusRequest:
    """Canonical exact legs and half-open collector-time scope."""

    environment_id: str
    scope_authority_ref: str
    legs: tuple[BookLeg, ...]
    start_at: datetime
    end_at: datetime

    def __post_init__(self) -> None:
        """Reject unbounded, repeated, or order-ambiguous requests."""
        _require_aware(self.start_at, "start_at")
        _require_aware(self.end_at, "end_at")
        if not self.environment_id or not self.scope_authority_ref:
            msg = "book corpus requires environment and exact scope-authority identity"
            raise ValueError(msg)
        if self.start_at >= self.end_at:
            msg = "book corpus requires an environment and a non-empty half-open time window"
            raise ValueError(msg)
        if (
            not self.legs
            or self.legs != tuple(sorted(self.legs))
            or len(set(self.legs)) != len(self.legs)
        ):
            msg = "book corpus legs must be unique and in canonical order"
            raise ValueError(msg)


def _validate_level(level: tuple[str, str]) -> tuple[Decimal, Decimal]:
    try:
        price = Decimal(level[0])
        size = Decimal(level[1])
    except (IndexError, ArithmeticError) as error:
        msg = "book level must contain exact decimal price and size text"
        raise ValueError(msg) from error
    if price < 0 or price > 1 or size <= 0:
        msg = "book snapshot level has invalid price or non-positive size"
        raise ValueError(msg)
    return price, size


def _validate_levels(levels: tuple[tuple[str, str], ...], *, bids: bool) -> None:
    parsed = tuple(_validate_level(level) for level in levels)
    prices = tuple(price for price, _ in parsed)
    expected = tuple(sorted(prices, reverse=bids))
    if prices != expected or len(set(prices)) != len(prices):
        msg = "book snapshot levels must be unique and best-first"
        raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class BookSnapshotRecord:
    """One exact full-depth replay anchor with two explicit clocks."""

    leg: BookLeg
    ts: datetime
    reference_time: datetime
    seq: int
    bids: tuple[tuple[str, str], ...]
    asks: tuple[tuple[str, str], ...]
    raw: Mapping[str, object]

    def __post_init__(self) -> None:
        """Validate clocks, sequence, and exact best-first depth."""
        _require_aware(self.ts, "ts")
        _require_aware(self.reference_time, "reference_time")
        if self.seq < 0:
            msg = "book sequence cannot be negative"
            raise ValueError(msg)
        _validate_levels(self.bids, bids=True)
        _validate_levels(self.asks, bids=False)

    @property
    def sort_key(self) -> tuple[object, ...]:
        """Return deterministic cross-leg source ordering."""
        return (self.ts, self.leg, self.reference_time, self.seq, 0)


@dataclass(frozen=True, slots=True)
class BookDeltaRecord:
    """One exact level replacement after a replay anchor."""

    leg: BookLeg
    ts: datetime
    reference_time: datetime
    seq: int
    side: BookSide
    price: Decimal
    size: Decimal
    raw: Mapping[str, object]

    def __post_init__(self) -> None:
        """Validate both clocks and level-replacement semantics."""
        _require_aware(self.ts, "ts")
        _require_aware(self.reference_time, "reference_time")
        if (
            self.seq < 0
            or self.side not in ("ASK", "BID")
            or self.price < 0
            or self.price > 1
            or self.size < 0
        ):
            msg = "book delta has invalid sequence, side, price, or size"
            raise ValueError(msg)

    @property
    def sort_key(self) -> tuple[object, ...]:
        """Return deterministic ordering, including rows sharing one event sequence."""
        return (
            self.ts,
            self.leg,
            self.reference_time,
            self.seq,
            1,
            self.side,
            self.price,
        )


@dataclass(frozen=True, slots=True)
class BookCorpus:
    """Exact bounded source rows for explicitly approved cross-venue legs."""

    request: BookCorpusRequest
    events: tuple[BookEventRecord, ...]

    def __post_init__(self) -> None:
        """Fail closed on scope, ordering, duplicates, or missing anchors."""
        ordered = tuple(sorted(self.events, key=lambda item: item.sort_key))
        if not self.events or self.events != ordered:
            msg = "book corpus events must be non-empty and canonically ordered"
            raise ValueError(msg)
        if len({item.sort_key for item in self.events}) != len(self.events):
            msg = "book corpus contains duplicate source rows"
            raise ValueError(msg)
        requested = frozenset(self.request.legs)
        anchored: set[BookLeg] = set()
        for event in self.events:
            if event.leg not in requested:
                msg = "book corpus event does not belong to a requested leg"
                raise ValueError(msg)
            if not self.request.start_at <= event.ts < self.request.end_at:
                msg = "book corpus event falls outside the collector-time window"
                raise ValueError(msg)
            if isinstance(event, BookSnapshotRecord):
                anchored.add(event.leg)
        if frozenset(anchored) != requested:
            msg = "book corpus requires at least one snapshot anchor for every requested leg"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class BookCorpusSnapshotRef:
    """Path-independent identity of one exact retained L2 corpus."""

    content_sha256: str
    size_bytes: int

    @property
    def uri(self) -> str:
        """Return the stable provenance reference."""
        return f"polymarket-book-corpus:{self.content_sha256}"


@dataclass(frozen=True, slots=True)
class BookCorpusSnapshot:
    """Verified canonical bytes decoded into strict source records."""

    ref: BookCorpusSnapshotRef
    corpus: BookCorpus


@dataclass(frozen=True, slots=True)
class BookCorpusRetention:
    """Sanitized identity of a retained L2 object."""

    ref: BookCorpusSnapshotRef


@dataclass(frozen=True, slots=True)
class BookTopState:
    """One full-depth replay state after a complete source event."""

    leg: BookLeg
    event_ordinal: int
    seq: int
    reference_time: datetime
    available_at: datetime
    bid_price: Decimal
    ask_price: Decimal
    bid_size: Decimal
    ask_size: Decimal
    bid_levels: tuple[tuple[Decimal, Decimal], ...]
    ask_levels: tuple[tuple[Decimal, Decimal], ...]

    def __post_init__(self) -> None:
        """Keep top fields and complete best-first ladders inseparable."""
        if not self.bid_levels or not self.ask_levels:
            msg = "book state requires non-empty bid and ask ladders"
            raise ValueError(msg)
        expected_bids = tuple(sorted(self.bid_levels, key=lambda level: level[0], reverse=True))
        expected_asks = tuple(sorted(self.ask_levels, key=lambda level: level[0]))
        if self.bid_levels != expected_bids or self.ask_levels != expected_asks:
            msg = "book state depth ladders must be best-first"
            raise ValueError(msg)
        if (
            len({price for price, _ in self.bid_levels}) != len(self.bid_levels)
            or len({price for price, _ in self.ask_levels}) != len(self.ask_levels)
            or any(price < 0 or price > 1 or size <= 0 for price, size in self.bid_levels)
            or any(price < 0 or price > 1 or size <= 0 for price, size in self.ask_levels)
        ):
            msg = "book state depth ladder contains invalid or repeated levels"
            raise ValueError(msg)
        if (
            self.bid_levels[0] != (self.bid_price, self.bid_size)
            or self.ask_levels[0] != (self.ask_price, self.ask_size)
            or self.bid_price >= self.ask_price
        ):
            msg = "book state top fields disagree with a non-crossed depth ladder"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class BookCorpusRegistration:
    """Replay states and their domain-neutral temporal registration."""

    snapshot_ref: BookCorpusSnapshotRef
    scope_authority_ref: str
    start_at: datetime
    end_at: datetime
    states: tuple[BookTopState, ...]
    dataset: RegisteredDataset
    catalog: DataCatalogSnapshot

    def __post_init__(self) -> None:
        """Reject detached replay state or registration content."""
        _require_aware(self.start_at, "start_at")
        _require_aware(self.end_at, "end_at")
        if (
            not self.scope_authority_ref
            or self.start_at >= self.end_at
            or self.catalog.datasets != (self.dataset,)
        ):
            msg = "book registration requires exact scope authority and one catalog dataset"
            raise ValueError(msg)
        if any(
            state.available_at < self.start_at or state.available_at >= self.end_at
            for state in self.states
        ):
            msg = "book registration state is outside retained collector-time coverage"
            raise ValueError(msg)
        expected = {
            (
                field_id,
                state.reference_time,
                state.available_at,
                dimensions,
                float(value),
            )
            for state in self.states
            for field_id, value, dimensions in _registered_state_values(state)
        }
        observed = {
            (
                item.field_ref.field_id,
                item.reference_time,
                item.available_at,
                item.dimensions,
                item.value,
            )
            for item in self.dataset.observations
        }
        if expected != observed:
            msg = "book replay states do not match their immutable registered observations"
            raise ValueError(msg)


class DatabaseBookCorpusReader:
    """Read exact post-clock-change book rows through a supplied read-only executor."""

    def __init__(self, executor: _FetchExecutor) -> None:
        """Bind a connection already proved read-only by the composition boundary."""
        self._executor: _FetchExecutor = executor

    async def read_corpus(self, request: BookCorpusRequest) -> BookCorpus:
        """Read snapshots and deltas using identical parameterized scope."""
        args = (
            tuple(leg.venue for leg in request.legs),
            tuple(leg.market_id for leg in request.legs),
            tuple(leg.outcome_index for leg in request.legs),
            request.start_at,
            request.end_at,
        )
        snapshot_rows = await self._executor.fetch(_SNAPSHOTS_SQL, *args)
        delta_rows = await self._executor.fetch(_DELTAS_SQL, *args)
        events: tuple[BookEventRecord, ...] = (
            *tuple(_snapshot_record(row) for row in snapshot_rows),
            *tuple(_delta_record(row) for row in delta_rows),
        )
        return BookCorpus(request, tuple(sorted(events, key=lambda item: item.sort_key)))


class BookCorpusStore:
    """Content-addressed local store for canonical L2 corpus bytes."""

    def __init__(self, root: Path) -> None:
        """Bind an operator-selected root without adding its path to corpus identity."""
        self.root: Path = root.absolute()

    @staticmethod
    def from_corpus(corpus: BookCorpus) -> BookCorpusSnapshot:
        """Canonicalize one corpus and derive its path-independent identity."""
        content = _canonical_bytes(corpus)
        ref = BookCorpusSnapshotRef(hashlib.sha256(content).hexdigest(), len(content))
        return BookCorpusSnapshot(ref, corpus)

    def retain(self, corpus: BookCorpus) -> BookCorpusRetention:
        """Publish exact canonical bytes once and verify them after persistence."""
        snapshot = self.from_corpus(corpus)
        content = _canonical_bytes(corpus)
        path = self.object_path(snapshot.ref)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            if path.read_bytes() != content:
                msg = "retained book corpus identity conflicts with changed bytes"
                raise ValueError(msg) from None
        else:
            with os.fdopen(descriptor, "wb") as output:
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
        if not self.verify(snapshot.ref):
            msg = "retained book corpus failed content verification"
            raise ValueError(msg)
        return BookCorpusRetention(snapshot.ref)

    def verify(self, ref: BookCorpusSnapshotRef) -> bool:
        """Check both retained byte size and SHA-256 identity."""
        try:
            content = self.object_path(ref).read_bytes()
        except OSError:
            return False
        return (
            len(content) == ref.size_bytes
            and hashlib.sha256(content).hexdigest() == ref.content_sha256
        )

    def load(self, ref: BookCorpusSnapshotRef) -> BookCorpusSnapshot:
        """Decode verified bytes and prove their canonical identity again."""
        if not self.verify(ref):
            msg = "cannot load an unverified book corpus snapshot"
            raise ValueError(msg)
        corpus = _decode_corpus(self.object_path(ref).read_bytes())
        snapshot = self.from_corpus(corpus)
        if snapshot.ref != ref:
            msg = "book corpus content does not match its reference"
            raise ValueError(msg)
        return snapshot

    def object_path(self, ref: BookCorpusSnapshotRef) -> Path:
        """Return the local object path without making it scientific identity."""
        digest = ref.content_sha256
        invalid_character = any(character not in "0123456789abcdef" for character in digest)
        if len(digest) != _SHA256_LENGTH or invalid_character:
            msg = "book corpus reference must contain a lowercase SHA-256"
            raise ValueError(msg)
        return self.root / "objects" / digest[:2] / f"{digest}.json"


def register_book_corpus(snapshot: BookCorpusSnapshot) -> BookCorpusRegistration:
    """Replay exact source rows and register two-sided top state with both clocks."""
    states = _replay(snapshot.corpus)
    schema = DatasetSchema(
        dataset_id=_DATASET_ID,
        version=_DATASET_SCHEMA,
        environment_id=snapshot.corpus.request.environment_id,
        provenance_ref=snapshot.ref.uri,
        fields=tuple(
            FieldDefinition(
                field_id=field_id,
                semantic_name=semantic_name,
                data_type="float",
                unit=unit,
                dimensions=dimensions,
                description=description,
            )
            for fields, dimensions, description in (
                (
                    _TOP_FIELDS,
                    _TOP_DIMENSIONS,
                    "Replayed two-sided L2 top after one decoded source event.",
                ),
                (
                    _DEPTH_FIELDS,
                    _DEPTH_DIMENSIONS,
                    "One best-first level from the complete replayed L2 depth ladder.",
                ),
            )
            for field_id, semantic_name, unit in fields
        ),
    )
    rows = tuple(
        row for state in states for row in _state_observations(schema, snapshot.ref, state)
    )
    dataset = ObservationRegistrar().register(schema, rows)
    catalog = DataCatalogSnapshot(schema.environment_id, (dataset,))
    return BookCorpusRegistration(
        snapshot.ref,
        snapshot.corpus.request.scope_authority_ref,
        snapshot.corpus.request.start_at,
        snapshot.corpus.request.end_at,
        states,
        dataset,
        catalog,
    )


def _replay(corpus: BookCorpus) -> tuple[BookTopState, ...]:
    states = [state for leg in corpus.request.legs for state in _replay_leg(corpus, leg)]
    if {state.leg for state in states} != set(corpus.request.legs):
        msg = "book replay produced no two-sided state for at least one requested leg"
        raise ValueError(msg)
    return tuple(
        sorted(
            states,
            key=lambda state: (state.available_at, state.leg, state.event_ordinal),
        )
    )


def _source_event_key(event: BookEventRecord) -> tuple[object, ...]:
    return (
        event.ts,
        event.reference_time,
        event.seq,
        isinstance(event, BookDeltaRecord),
    )


def _replay_leg(corpus: BookCorpus, leg: BookLeg) -> tuple[BookTopState, ...]:
    """Replay one leg independently so venue sequences never share state."""
    bids: dict[Decimal, Decimal] = {}
    asks: dict[Decimal, Decimal] = {}
    anchored = False
    states: list[BookTopState] = []
    events = (event for event in corpus.events if event.leg == leg)
    for ordinal, (_, source_group) in enumerate(groupby(events, key=_source_event_key)):
        group = tuple(source_group)
        first = group[0]
        if isinstance(first, BookSnapshotRecord):
            if len(group) != 1:
                msg = "book replay encountered more than one snapshot for one source event"
                raise ValueError(msg)
            bids = {Decimal(price): Decimal(size) for price, size in first.bids}
            asks = {Decimal(price): Decimal(size) for price, size in first.asks}
            anchored = True
        elif not anchored:
            continue
        else:
            _apply_deltas(bids, asks, group)
        if not bids or not asks:
            continue
        bid_price = max(bids)
        ask_price = min(asks)
        if bid_price >= ask_price:
            msg = f"book replay produced a crossed or locked state for {leg.market_id}"
            raise ValueError(msg)
        bid_levels = tuple(sorted(bids.items(), key=lambda level: level[0], reverse=True))
        ask_levels = tuple(sorted(asks.items(), key=lambda level: level[0]))
        states.append(
            BookTopState(
                leg=leg,
                event_ordinal=ordinal,
                seq=first.seq,
                reference_time=first.reference_time,
                available_at=first.ts,
                bid_price=bid_price,
                ask_price=ask_price,
                bid_size=bids[bid_price],
                ask_size=asks[ask_price],
                bid_levels=bid_levels,
                ask_levels=ask_levels,
            )
        )
    return tuple(states)


def _apply_deltas(
    bids: dict[Decimal, Decimal],
    asks: dict[Decimal, Decimal],
    group: tuple[BookEventRecord, ...],
) -> None:
    for event in group:
        delta = cast("BookDeltaRecord", event)
        levels = bids if delta.side == "BID" else asks
        if delta.size == 0:
            levels.pop(delta.price, None)
        else:
            levels[delta.price] = delta.size


def _state_observations(
    schema: DatasetSchema,
    ref: BookCorpusSnapshotRef,
    state: BookTopState,
) -> tuple[ObservationInput, ...]:
    source = (
        f"{ref.uri}:{state.leg.venue}:{state.leg.market_id}:"
        f"{state.leg.outcome_index}:{state.event_ordinal}:{state.seq}"
    )
    caveats = (
        "available_at is collector absorb after event decode, not kernel or wire receipt",
        "reference_time is venue supplied or the collector fallback recorded at capture",
        "the complete retained displayed ladder does not prove hidden depth or quote ownership",
        "displayed depth does not prove fill, queue position, latency, or fee-adjusted execution",
    )
    return tuple(
        ObservationInput(
            field_ref=schema.field_ref(field_id),
            value=float(value),
            reference_time=state.reference_time,
            available_at=state.available_at,
            vintage_id=ref.uri,
            revision_number=0,
            source_ref=(
                f"{source}:{field_id}:"
                + ":".join(
                    f"{key}={value}" for key, value in dimensions if key in ("side", "level")
                )
            ),
            provenance_ref=ref.uri,
            availability_rule_version=_AVAILABILITY_RULE,
            dimensions=dimensions,
            caveats=caveats,
        )
        for field_id, value, dimensions in _registered_state_values(state)
    )


def _state_dimensions(state: BookTopState) -> tuple[tuple[str, str], ...]:
    return (
        ("venue", state.leg.venue),
        ("market_id", state.leg.market_id),
        ("outcome_index", str(state.leg.outcome_index)),
        ("event_ordinal", str(state.event_ordinal)),
        ("seq", str(state.seq)),
    )


def _state_values(state: BookTopState) -> tuple[tuple[str, Decimal], ...]:
    return (
        ("best_bid_price", state.bid_price),
        ("best_ask_price", state.ask_price),
        ("best_bid_size", state.bid_size),
        ("best_ask_size", state.ask_size),
    )


def _registered_state_values(
    state: BookTopState,
) -> tuple[tuple[str, Decimal, tuple[tuple[str, str], ...]], ...]:
    top_dimensions = _state_dimensions(state)
    top = tuple((field_id, value, top_dimensions) for field_id, value in _state_values(state))
    depth = tuple(
        (field_id, value, (*top_dimensions, ("side", side), ("level", str(level))))
        for side, levels in (("BID", state.bid_levels), ("ASK", state.ask_levels))
        for level, (price, size) in enumerate(levels)
        for field_id, value in (("depth_price", price), ("depth_size", size))
    )
    return (*top, *depth)


def _leg_from_row(row: Mapping[str, object]) -> BookLeg:
    venue = row.get("venue")
    if venue not in ("kalshi", "polymarket"):
        msg = "book row has an unsupported venue"
        raise ValueError(msg)
    return BookLeg(
        venue,
        str(row["market_id"]),
        int(cast("int", row["outcome_index"])),
    )


def _time_from_row(row: Mapping[str, object], field: str) -> datetime:
    value = row.get(field)
    if not isinstance(value, datetime):
        msg = f"book row requires non-null {field}"
        raise TypeError(msg)
    _require_aware(value, field)
    return value


def _raw_from_row(row: Mapping[str, object]) -> Mapping[str, object]:
    value = row.get("raw")
    if not isinstance(value, Mapping):
        msg = "book row requires its exact raw JSON object"
        raise TypeError(msg)
    return cast("Mapping[str, object]", value)


def _levels_from_row(row: Mapping[str, object], field: str) -> tuple[tuple[str, str], ...]:
    value = row.get(field)
    if not isinstance(value, list | tuple):
        msg = f"book snapshot requires {field} levels"
        raise TypeError(msg)
    levels: list[tuple[str, str]] = []
    for raw_level in cast("Sequence[object]", value):
        if not isinstance(raw_level, list | tuple):
            msg = f"book snapshot {field} must preserve decimal text"
            raise TypeError(msg)
        level = cast("Sequence[object]", raw_level)
        if (
            len(level) != _LEVEL_WIDTH
            or not isinstance(level[0], str)
            or not isinstance(level[1], str)
        ):
            msg = f"book snapshot {field} must preserve decimal text"
            raise ValueError(msg)
        levels.append((level[0], level[1]))
    return tuple(levels)


def _snapshot_record(row: Mapping[str, object]) -> BookSnapshotRecord:
    return BookSnapshotRecord(
        leg=_leg_from_row(row),
        ts=_time_from_row(row, "ts"),
        reference_time=_time_from_row(row, "reference_time"),
        seq=int(cast("int", row["seq"])),
        bids=_levels_from_row(row, "bids"),
        asks=_levels_from_row(row, "asks"),
        raw=_raw_from_row(row),
    )


def _delta_record(row: Mapping[str, object]) -> BookDeltaRecord:
    side = row.get("side")
    if side not in ("ASK", "BID"):
        msg = "book delta has an unsupported side"
        raise ValueError(msg)
    return BookDeltaRecord(
        leg=_leg_from_row(row),
        ts=_time_from_row(row, "ts"),
        reference_time=_time_from_row(row, "reference_time"),
        seq=int(cast("int", row["seq"])),
        side=side,
        price=Decimal(str(row["price"])),
        size=Decimal(str(row["size"])),
        raw=_raw_from_row(row),
    )


def _canonical_bytes(corpus: BookCorpus) -> bytes:
    return json.dumps(
        _corpus_payload(corpus),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


def _corpus_payload(corpus: BookCorpus) -> dict[str, object]:
    return {
        "schema_version": _SNAPSHOT_SCHEMA,
        "request": {
            "environment_id": corpus.request.environment_id,
            "scope_authority_ref": corpus.request.scope_authority_ref,
            "start_at": corpus.request.start_at.isoformat(),
            "end_at": corpus.request.end_at.isoformat(),
            "legs": [
                {
                    "venue": leg.venue,
                    "market_id": leg.market_id,
                    "outcome_index": leg.outcome_index,
                }
                for leg in corpus.request.legs
            ],
        },
        "events": [_event_payload(event) for event in corpus.events],
    }


def _event_payload(event: BookEventRecord) -> dict[str, object]:
    common: dict[str, object] = {
        "kind": "snapshot" if isinstance(event, BookSnapshotRecord) else "delta",
        "venue": event.leg.venue,
        "market_id": event.leg.market_id,
        "outcome_index": event.leg.outcome_index,
        "ts": event.ts.isoformat(),
        "reference_time": event.reference_time.isoformat(),
        "seq": event.seq,
        "raw": _canonical_json(event.raw),
    }
    if isinstance(event, BookSnapshotRecord):
        common.update({"bids": event.bids, "asks": event.asks})
    else:
        common.update({"side": event.side, "price": str(event.price), "size": str(event.size)})
    return common


def _canonical_json(value: object) -> object:
    if isinstance(value, Mapping):
        mapping = cast("Mapping[object, object]", value)
        items = sorted(((str(key), item) for key, item in mapping.items()))
        return {key: _canonical_json(item) for key, item in items}
    if isinstance(value, list | tuple):
        return [_canonical_json(item) for item in cast("Sequence[object]", value)]
    if isinstance(value, Decimal | datetime):
        return str(value) if isinstance(value, Decimal) else value.isoformat()
    if value is None or isinstance(value, str | int | float | bool):
        return value
    msg = f"unsupported raw JSON value: {type(value).__name__}"
    raise TypeError(msg)


def _decode_corpus(content: bytes) -> BookCorpus:
    raw = cast("dict[str, object]", json.loads(content))
    if raw.get("schema_version") != _SNAPSHOT_SCHEMA:
        msg = "unknown book corpus snapshot schema"
        raise ValueError(msg)
    request_raw = cast("dict[str, object]", raw["request"])
    legs = tuple(
        BookLeg(
            cast("BookVenue", leg["venue"]),
            str(leg["market_id"]),
            int(cast("int", leg["outcome_index"])),
        )
        for leg in cast("list[dict[str, object]]", request_raw["legs"])
    )
    request = BookCorpusRequest(
        str(request_raw["environment_id"]),
        str(request_raw["scope_authority_ref"]),
        legs,
        datetime.fromisoformat(str(request_raw["start_at"])),
        datetime.fromisoformat(str(request_raw["end_at"])),
    )
    events = tuple(
        _decode_event(cast("dict[str, object]", event))
        for event in cast("list[object]", raw["events"])
    )
    return BookCorpus(request, events)


def _decode_event(raw: dict[str, object]) -> BookEventRecord:
    leg = BookLeg(
        cast("BookVenue", raw["venue"]),
        str(raw["market_id"]),
        int(cast("int", raw["outcome_index"])),
    )
    ts = datetime.fromisoformat(str(raw["ts"]))
    reference_time = datetime.fromisoformat(str(raw["reference_time"]))
    seq = int(cast("int", raw["seq"]))
    source_raw = cast("Mapping[str, object]", raw["raw"])
    if raw.get("kind") == "snapshot":
        row = cast("Mapping[str, object]", raw)
        return BookSnapshotRecord(
            leg=leg,
            ts=ts,
            reference_time=reference_time,
            seq=seq,
            bids=_levels_from_row(row, "bids"),
            asks=_levels_from_row(row, "asks"),
            raw=source_raw,
        )
    if raw.get("kind") == "delta":
        side = raw.get("side")
        if side not in ("ASK", "BID"):
            msg = "decoded book delta has invalid side"
            raise ValueError(msg)
        return BookDeltaRecord(
            leg=leg,
            ts=ts,
            reference_time=reference_time,
            seq=seq,
            side=side,
            price=Decimal(str(raw["price"])),
            size=Decimal(str(raw["size"])),
            raw=source_raw,
        )
    msg = "decoded book event has unknown kind"
    raise ValueError(msg)


_SNAPSHOTS_SQL = """
WITH requested AS (
    SELECT *
    FROM unnest($1::text[], $2::text[], $3::smallint[])
        AS leg(venue, market_id, outcome_index)
)
SELECT s.venue, s.market_id, s.outcome_index, s.ts, s.reference_time, s.seq,
       s.bids, s.asks, s.raw
FROM market.book_snapshots AS s
JOIN requested USING (venue, market_id, outcome_index)
WHERE s.ts >= $4 AND s.ts < $5
  AND s.reference_time IS NOT NULL
ORDER BY s.ts, s.venue, s.market_id, s.outcome_index, s.reference_time, s.seq
"""

_DELTAS_SQL = """
WITH requested AS (
    SELECT *
    FROM unnest($1::text[], $2::text[], $3::smallint[])
        AS leg(venue, market_id, outcome_index)
)
SELECT d.venue, d.market_id, d.outcome_index, d.ts, d.reference_time, d.seq,
       d.side, d.price, d.size, d.raw
FROM market.book_deltas AS d
JOIN requested USING (venue, market_id, outcome_index)
WHERE d.ts >= $4 AND d.ts < $5
  AND d.reference_time IS NOT NULL
ORDER BY d.ts, d.venue, d.market_id, d.outcome_index, d.reference_time, d.seq, d.side, d.price
"""
