"""Causal clock diagnostics and quiet-duration features for retained L2 events."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import groupby
from typing import Literal, cast

from research_agent.data_adapters.polymarket.book_corpus import (
    BookCorpus,
    BookCorpusSnapshot,
    BookCorpusSnapshotRef,
    BookCorpusStore,
    BookDeltaRecord,
    BookLeg,
    BookVenue,
)

type BookSourceEventKind = Literal["DELTA", "SNAPSHOT"]

_CLOCK_PROFILE_QUANTILES = ((1, 2), (9, 10), (19, 20), (99, 100))


def _require_aware(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        message = f"{field} must be timezone-aware"
        raise ValueError(message)


@dataclass(frozen=True, slots=True)
class BookActivityDefinition:
    """Fixed elapsed lookback for a causal per-leg activity feature."""

    recent_window: timedelta

    def __post_init__(self) -> None:
        """Reject windows without positive elapsed-duration meaning."""
        if self.recent_window <= timedelta(0):
            message = "book activity recent window must be positive"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class BookSourceEvent:
    """One captured venue message coalesced across retained rows and legs."""

    venue: BookVenue
    available_at: datetime
    reference_time: datetime
    seq: int
    kind: BookSourceEventKind
    legs: tuple[BookLeg, ...]
    row_count: int

    def __post_init__(self) -> None:
        """Reject an incomplete or cross-venue source identity."""
        _require_aware(self.available_at, "available_at")
        _require_aware(self.reference_time, "reference_time")
        if (
            self.venue not in ("kalshi", "polymarket")
            or self.seq < 0
            or self.kind not in ("DELTA", "SNAPSHOT")
            or not self.legs
            or self.legs != tuple(sorted(set(self.legs)))
            or any(leg.venue != self.venue for leg in self.legs)
            or self.row_count < len(self.legs)
        ):
            message = "book source event has invalid identity or row ancestry"
            raise ValueError(message)

    @property
    def reference_delay(self) -> timedelta:
        """Return signed collector absorb time minus venue/fallback event time."""
        return self.available_at - self.reference_time


@dataclass(frozen=True, slots=True)
class BookVenueClockProfile:
    """Value-blind signed clock-delay diagnostics for one venue."""

    venue: BookVenue
    source_event_count: int
    negative_delay_count: int
    zero_delay_count: int
    positive_delay_count: int
    signed_delay_min: timedelta
    signed_delay_max: timedelta
    nonnegative_p50: timedelta | None
    nonnegative_p90: timedelta | None
    nonnegative_p95: timedelta | None
    nonnegative_p99: timedelta | None

    def __post_init__(self) -> None:
        """Keep signed clock classes and quantiles internally coherent."""
        classified = self.negative_delay_count + self.zero_delay_count + self.positive_delay_count
        quantiles = (
            self.nonnegative_p50,
            self.nonnegative_p90,
            self.nonnegative_p95,
            self.nonnegative_p99,
        )
        if (
            self.venue not in ("kalshi", "polymarket")
            or self.source_event_count <= 0
            or classified != self.source_event_count
            or min(
                self.negative_delay_count,
                self.zero_delay_count,
                self.positive_delay_count,
            )
            < 0
            or self.signed_delay_min > self.signed_delay_max
            or (
                (self.zero_delay_count + self.positive_delay_count == 0)
                != all(quantile is None for quantile in quantiles)
            )
        ):
            message = "book venue clock profile is internally inconsistent"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class BookActivityPoint:
    """Causal activity state at one distinct collector time for one exact leg."""

    leg: BookLeg
    decision_time: datetime
    previous_event_time: datetime | None
    quiet_duration: timedelta | None
    recent_source_event_count: int | None
    concurrent_source_event_count: int
    source_event_sequences: tuple[int, ...]
    reference_delay_min: timedelta
    reference_delay_max: timedelta

    def __post_init__(self) -> None:
        """Reject fabricated history or a split same-time decision."""
        _require_aware(self.decision_time, "decision_time")
        if self.previous_event_time is not None:
            _require_aware(self.previous_event_time, "previous_event_time")
        expected_quiet = (
            None
            if self.previous_event_time is None
            else self.decision_time - self.previous_event_time
        )
        if (
            self.quiet_duration != expected_quiet
            or (self.quiet_duration is not None and self.quiet_duration <= timedelta(0))
            or (self.recent_source_event_count is not None and self.recent_source_event_count < 0)
            or self.concurrent_source_event_count <= 0
            or len(self.source_event_sequences) != self.concurrent_source_event_count
            or self.source_event_sequences != tuple(sorted(self.source_event_sequences))
            or self.reference_delay_min > self.reference_delay_max
        ):
            message = "book activity point is temporally inconsistent"
            raise ValueError(message)


@dataclass(frozen=True, slots=True)
class BookActivitySeries:
    """Provenance-bound clock profile and per-leg activity feature series."""

    snapshot_ref: BookCorpusSnapshotRef
    environment_id: str
    scope_authority_ref: str
    start_at: datetime
    end_at: datetime
    definition: BookActivityDefinition
    source_event_count: int
    clock_profiles: tuple[BookVenueClockProfile, ...]
    points: tuple[BookActivityPoint, ...]
    caveats: tuple[str, ...]

    def __post_init__(self) -> None:
        """Keep feature output attached to exact source coverage and identity."""
        _require_aware(self.start_at, "start_at")
        _require_aware(self.end_at, "end_at")
        if (
            not self.environment_id
            or not self.scope_authority_ref
            or self.start_at >= self.end_at
            or self.source_event_count <= 0
            or not self.clock_profiles
            or not self.points
            or sum(profile.source_event_count for profile in self.clock_profiles)
            != self.source_event_count
            or tuple(profile.venue for profile in self.clock_profiles)
            != tuple(sorted(profile.venue for profile in self.clock_profiles))
            or self.points
            != tuple(sorted(self.points, key=lambda point: (point.decision_time, point.leg)))
            or any(
                point.decision_time < self.start_at or point.decision_time >= self.end_at
                for point in self.points
            )
            or any(
                (point.decision_time - self.definition.recent_window < self.start_at)
                != (point.recent_source_event_count is None)
                for point in self.points
            )
            or not self.caveats
        ):
            message = "book activity series is detached from canonical source coverage"
            raise ValueError(message)


def coalesce_book_source_events(corpus: BookCorpus) -> tuple[BookSourceEvent, ...]:
    """Coalesce exact source rows without merging venues or distinct messages."""
    buckets: dict[
        tuple[BookVenue, datetime, datetime, int, BookSourceEventKind],
        list[BookLeg],
    ] = {}
    kinds: dict[tuple[BookVenue, datetime, datetime, int], BookSourceEventKind] = {}
    row_counts: dict[
        tuple[BookVenue, datetime, datetime, int, BookSourceEventKind],
        int,
    ] = {}
    for event in corpus.events:
        kind: BookSourceEventKind = "DELTA" if isinstance(event, BookDeltaRecord) else "SNAPSHOT"
        base_key = (event.leg.venue, event.ts, event.reference_time, event.seq)
        previous_kind = kinds.setdefault(base_key, kind)
        if previous_kind != kind:
            message = "book source identity spans incompatible row kinds"
            raise ValueError(message)
        key = (*base_key, kind)
        buckets.setdefault(key, []).append(event.leg)
        row_counts[key] = row_counts.get(key, 0) + 1

    source_events = (
        BookSourceEvent(
            venue=key[0],
            available_at=key[1],
            reference_time=key[2],
            seq=key[3],
            kind=key[4],
            legs=tuple(sorted(set(legs))),
            row_count=row_counts[key],
        )
        for key, legs in buckets.items()
    )
    return tuple(
        sorted(
            source_events,
            key=lambda event: (
                event.available_at,
                event.venue,
                event.reference_time,
                event.seq,
                event.kind,
            ),
        )
    )


def build_book_activity_series(
    snapshot: BookCorpusSnapshot,
    definition: BookActivityDefinition,
) -> BookActivitySeries:
    """Derive value-blind clock and activity state from one verified snapshot."""
    canonical = BookCorpusStore.from_corpus(snapshot.corpus)
    if canonical.ref != snapshot.ref:
        message = "book activity snapshot identity does not own the supplied corpus"
        raise ValueError(message)
    source_events = coalesce_book_source_events(snapshot.corpus)
    clock_profiles = _clock_profiles(source_events)
    points = _activity_points(snapshot.corpus, source_events, definition)
    request = snapshot.corpus.request
    return BookActivitySeries(
        snapshot_ref=snapshot.ref,
        environment_id=request.environment_id,
        scope_authority_ref=request.scope_authority_ref,
        start_at=request.start_at,
        end_at=request.end_at,
        definition=definition,
        source_event_count=len(source_events),
        clock_profiles=clock_profiles,
        points=points,
        caveats=(
            "quiet duration and recent activity use collector absorb time, not venue event time",
            "the first quiet duration and each partial recent window remain missing",
            "exact zero reference delay may be venue timing or the collector fallback",
            "archival reference delay is not order-send, acknowledgement, or fill latency",
            "activity may describe the observation mechanism and grants no directional alpha",
        ),
    )


def _clock_profiles(
    source_events: tuple[BookSourceEvent, ...],
) -> tuple[BookVenueClockProfile, ...]:
    profiles: list[BookVenueClockProfile] = []
    ordered = sorted(source_events, key=lambda event: event.venue)
    for venue, venue_group in groupby(ordered, key=lambda event: event.venue):
        events = tuple(venue_group)
        delays = tuple(event.reference_delay for event in events)
        nonnegative = tuple(sorted(delay for delay in delays if delay >= timedelta(0)))
        quantiles = tuple(
            _nearest_rank(nonnegative, numerator, denominator)
            for numerator, denominator in _CLOCK_PROFILE_QUANTILES
        )
        profiles.append(
            BookVenueClockProfile(
                venue=cast("BookVenue", venue),
                source_event_count=len(events),
                negative_delay_count=sum(delay < timedelta(0) for delay in delays),
                zero_delay_count=sum(delay == timedelta(0) for delay in delays),
                positive_delay_count=sum(delay > timedelta(0) for delay in delays),
                signed_delay_min=min(delays),
                signed_delay_max=max(delays),
                nonnegative_p50=quantiles[0],
                nonnegative_p90=quantiles[1],
                nonnegative_p95=quantiles[2],
                nonnegative_p99=quantiles[3],
            )
        )
    return tuple(profiles)


def _nearest_rank(
    values: tuple[timedelta, ...],
    numerator: int,
    denominator: int,
) -> timedelta | None:
    if not values:
        return None
    rank = (len(values) * numerator + denominator - 1) // denominator
    return values[rank - 1]


def _activity_points(
    corpus: BookCorpus,
    source_events: tuple[BookSourceEvent, ...],
    definition: BookActivityDefinition,
) -> tuple[BookActivityPoint, ...]:
    points: list[BookActivityPoint] = []
    for leg in corpus.request.legs:
        leg_events = tuple(event for event in source_events if leg in event.legs)
        history: deque[datetime] = deque()
        previous_event_time: datetime | None = None
        for decision_time, time_group in groupby(
            leg_events,
            key=lambda event: event.available_at,
        ):
            current_events = tuple(time_group)
            window_start = decision_time - definition.recent_window
            while history and history[0] < window_start:
                history.popleft()
            recent_count = len(history) if window_start >= corpus.request.start_at else None
            delays = tuple(event.reference_delay for event in current_events)
            points.append(
                BookActivityPoint(
                    leg=leg,
                    decision_time=decision_time,
                    previous_event_time=previous_event_time,
                    quiet_duration=(
                        None if previous_event_time is None else decision_time - previous_event_time
                    ),
                    recent_source_event_count=recent_count,
                    concurrent_source_event_count=len(current_events),
                    source_event_sequences=tuple(sorted(event.seq for event in current_events)),
                    reference_delay_min=min(delays),
                    reference_delay_max=max(delays),
                )
            )
            history.extend(event.available_at for event in current_events)
            previous_event_time = decision_time
    return tuple(sorted(points, key=lambda point: (point.decision_time, point.leg)))
