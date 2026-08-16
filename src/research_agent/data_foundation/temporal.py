"""Identity-bearing elapsed and calendar temporal offsets."""

# ruff: noqa: EM101, PLR0913, TRY003

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from research_agent.data_foundation._identity import require_aware, stable_identity

_MICROSECONDS_PER_SECOND = 1_000_000
_SECONDS_PER_DAY = 86_400


class TemporalOffsetKind(Enum):
    """Whether an offset advances an absolute timeline or a civil calendar."""

    ELAPSED = "elapsed"
    CALENDAR = "calendar"


class CalendarUnit(Enum):
    """Identity-bearing civil-calendar units supported by the kernel."""

    MONTH = "month"
    QUARTER = "quarter"


class OffsetAnchor(Enum):
    """The datetime from which an offset is evaluated."""

    EXACT_INPUT = "exact_input"


class MonthEndPolicy(Enum):
    """Declared handling when a calendar month lacks the anchor day."""

    NOT_APPLICABLE = "not_applicable"
    CLAMP = "clamp"
    PRESERVE = "preserve"
    REJECT = "reject"


class TimezonePolicy(Enum):
    """Declared absolute-time or local-wall-clock behavior."""

    ABSOLUTE_ELAPSED = "absolute_elapsed"
    WALL_CLOCK_REJECT_TRANSITION = "wall_clock_reject_transition"
    WALL_CLOCK_PRESERVE_FOLD = "wall_clock_preserve_fold"


@dataclass(frozen=True, slots=True)
class TemporalOffset:
    """Exact scientific identity for elapsed or calendar-relative time."""

    kind: TemporalOffsetKind
    elapsed_microseconds: int | None
    calendar_count: int | None
    calendar_unit: CalendarUnit | None
    anchor: OffsetAnchor
    month_end_policy: MonthEndPolicy
    timezone_name: str | None
    timezone_policy: TimezonePolicy

    def __post_init__(self) -> None:
        """Reject incomplete or mixed elapsed/calendar semantics."""
        enum_values = (
            (self.kind, TemporalOffsetKind),
            (self.anchor, OffsetAnchor),
            (self.month_end_policy, MonthEndPolicy),
            (self.timezone_policy, TimezonePolicy),
        )
        if any(
            not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
                value, enum_type
            )
            for value, enum_type in enum_values
        ):
            raise TypeError("temporal offset policies must use exact enum identities")
        if self.calendar_unit is not None and not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
            self.calendar_unit, CalendarUnit
        ):
            raise TypeError("calendar offset unit must use an exact CalendarUnit")
        if self.anchor is not OffsetAnchor.EXACT_INPUT:
            raise ValueError("only exact-input temporal anchoring is currently supported")
        if self.kind is TemporalOffsetKind.ELAPSED:
            if (
                self.elapsed_microseconds is None
                or isinstance(self.elapsed_microseconds, bool)
                or not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
                    self.elapsed_microseconds, int
                )
                or self.calendar_count is not None
                or self.calendar_unit is not None
                or self.month_end_policy is not MonthEndPolicy.NOT_APPLICABLE
                or self.timezone_name is not None
                or self.timezone_policy is not TimezonePolicy.ABSOLUTE_ELAPSED
            ):
                raise ValueError("elapsed offsets require only exact elapsed duration semantics")
            return
        if (
            self.elapsed_microseconds is not None
            or self.calendar_count is None
            or isinstance(self.calendar_count, bool)
            or not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
                self.calendar_count, int
            )
            or self.calendar_count == 0
            or self.calendar_unit is None
            or self.month_end_policy is MonthEndPolicy.NOT_APPLICABLE
            or not self.timezone_name
            or self.timezone_policy is TimezonePolicy.ABSOLUTE_ELAPSED
        ):
            raise ValueError(
                "calendar offsets require explicit unit, anchor, month-end, and timezone"
            )
        try:
            ZoneInfo(self.timezone_name)
        except ZoneInfoNotFoundError as error:
            raise ValueError("calendar offset timezone is not available") from error

    @classmethod
    def elapsed(cls, duration: timedelta) -> TemporalOffset:
        """Create an absolute elapsed-time offset without calendar conversion."""
        if not isinstance(duration, timedelta):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("elapsed offset duration must be a timedelta")
        microseconds = (
            duration.days * _SECONDS_PER_DAY + duration.seconds
        ) * _MICROSECONDS_PER_SECOND + duration.microseconds
        return cls(
            kind=TemporalOffsetKind.ELAPSED,
            elapsed_microseconds=microseconds,
            calendar_count=None,
            calendar_unit=None,
            anchor=OffsetAnchor.EXACT_INPUT,
            month_end_policy=MonthEndPolicy.NOT_APPLICABLE,
            timezone_name=None,
            timezone_policy=TimezonePolicy.ABSOLUTE_ELAPSED,
        )

    @classmethod
    def zero(cls) -> TemporalOffset:
        """Return an explicit zero elapsed offset."""
        return cls.elapsed(timedelta(0))

    @classmethod
    def calendar(
        cls,
        *,
        count: int,
        unit: CalendarUnit,
        anchor: OffsetAnchor,
        month_end_policy: MonthEndPolicy,
        timezone_name: str,
        timezone_policy: TimezonePolicy,
    ) -> TemporalOffset:
        """Create a civil-calendar offset with no implicit policy defaults."""
        if isinstance(count, bool) or not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
            count, int
        ):
            raise TypeError("calendar offset count must be an integer")
        return cls(
            kind=TemporalOffsetKind.CALENDAR,
            elapsed_microseconds=None,
            calendar_count=count,
            calendar_unit=unit,
            anchor=anchor,
            month_end_policy=month_end_policy,
            timezone_name=timezone_name,
            timezone_policy=timezone_policy,
        )

    @property
    def identity(self) -> str:
        """Return exact offset identity, including every calendar policy."""
        return stable_identity("temporal-offset", self)

    @property
    def is_zero(self) -> bool:
        """Return whether this exact offset advances no time."""
        return self.kind is TemporalOffsetKind.ELAPSED and self.elapsed_microseconds == 0

    @property
    def is_positive(self) -> bool:
        """Return whether the declared amount is positive."""
        if self.kind is TemporalOffsetKind.ELAPSED:
            return bool(self.elapsed_microseconds is not None and self.elapsed_microseconds > 0)
        return bool(self.calendar_count is not None and self.calendar_count > 0)

    @property
    def is_negative(self) -> bool:
        """Return whether the declared amount is negative."""
        if self.kind is TemporalOffsetKind.ELAPSED:
            return bool(self.elapsed_microseconds is not None and self.elapsed_microseconds < 0)
        return bool(self.calendar_count is not None and self.calendar_count < 0)

    def describe(self) -> str:
        """Return a deterministic human readback of the complete temporal meaning."""
        if self.kind is TemporalOffsetKind.ELAPSED:
            return f"elapsed {self.elapsed_microseconds} microseconds (absolute timeline)"
        if self.calendar_unit is None:
            raise AssertionError("calendar offset lost its unit")
        return (
            f"calendar {self.calendar_count} {self.calendar_unit.value}; "
            f"anchor={self.anchor.value}; month_end={self.month_end_policy.value}; "
            f"timezone={self.timezone_name}; timezone_policy={self.timezone_policy.value}"
        )

    def negated(self) -> TemporalOffset:
        """Return the exact opposite offset without losing policy identity."""
        if self.kind is TemporalOffsetKind.ELAPSED:
            if self.elapsed_microseconds is None:
                raise AssertionError("elapsed offset lost its duration")
            return TemporalOffset.elapsed(timedelta(microseconds=-self.elapsed_microseconds))
        if self.calendar_count is None or self.calendar_unit is None or self.timezone_name is None:
            raise AssertionError("calendar offset lost required semantics")
        return TemporalOffset.calendar(
            count=-self.calendar_count,
            unit=self.calendar_unit,
            anchor=self.anchor,
            month_end_policy=self.month_end_policy,
            timezone_name=self.timezone_name,
            timezone_policy=self.timezone_policy,
        )

    def compare_magnitude(self, other: TemporalOffset) -> int:
        """Compare only offsets whose magnitude is anchor-independently comparable."""
        if self.is_zero or other.is_zero:
            if self.is_zero and other.is_zero:
                return 0
            return -1 if self.is_zero else 1
        if self.kind is TemporalOffsetKind.ELAPSED and other.kind is TemporalOffsetKind.ELAPSED:
            left = self.elapsed_microseconds
            right = other.elapsed_microseconds
        elif self.kind is TemporalOffsetKind.CALENDAR and other.kind is TemporalOffsetKind.CALENDAR:
            policies = (
                self.anchor,
                self.month_end_policy,
                self.timezone_name,
                self.timezone_policy,
            )
            other_policies = (
                other.anchor,
                other.month_end_policy,
                other.timezone_name,
                other.timezone_policy,
            )
            if policies != other_policies:
                raise ValueError(
                    "temporal offsets with different calendar policies are incomparable"
                )
            if self.calendar_count is None or other.calendar_count is None:
                raise AssertionError("calendar offset lost its count")
            left = self.calendar_count * (3 if self.calendar_unit is CalendarUnit.QUARTER else 1)
            right = other.calendar_count * (3 if other.calendar_unit is CalendarUnit.QUARTER else 1)
        else:
            raise ValueError("elapsed and calendar offset magnitudes are anchor-dependent")
        if left is None or right is None:
            raise AssertionError("temporal offset lost its magnitude")
        return (left > right) - (left < right)

    def apply(self, moment: datetime) -> datetime:
        """Apply the exact offset to one timezone-aware anchor datetime."""
        require_aware(moment, "temporal offset anchor")
        if self.kind is TemporalOffsetKind.ELAPSED:
            if self.elapsed_microseconds is None:
                raise AssertionError("elapsed offset lost its duration")
            return (
                moment.astimezone(UTC) + timedelta(microseconds=self.elapsed_microseconds)
            ).astimezone(moment.tzinfo)
        return self._apply_calendar(moment)

    def _apply_calendar(self, moment: datetime) -> datetime:
        if self.calendar_count is None or self.calendar_unit is None or self.timezone_name is None:
            raise AssertionError("calendar offset lost required semantics")
        if _timezone_name(moment) != self.timezone_name:
            raise ValueError("calendar offset anchor timezone does not match its exact identity")
        month_count = self.calendar_count * (3 if self.calendar_unit is CalendarUnit.QUARTER else 1)
        month_index = moment.year * 12 + moment.month - 1 + month_count
        year, zero_based_month = divmod(month_index, 12)
        month = zero_based_month + 1
        target_last_day = monthrange(year, month)[1]
        source_is_month_end = moment.day == monthrange(moment.year, moment.month)[1]
        if self.month_end_policy is MonthEndPolicy.PRESERVE and source_is_month_end:
            day = target_last_day
        elif moment.day <= target_last_day:
            day = moment.day
        elif self.month_end_policy in {MonthEndPolicy.CLAMP, MonthEndPolicy.PRESERVE}:
            day = target_last_day
        else:
            raise ValueError("calendar offset month-end policy rejects the target month")
        naive = moment.replace(tzinfo=None, year=year, month=month, day=day)
        timezone = ZoneInfo(self.timezone_name)
        candidates = _valid_wall_clock_candidates(naive, timezone)
        if not candidates:
            raise ValueError("calendar offset produced a nonexistent or ambiguous local time")
        if self.timezone_policy is TimezonePolicy.WALL_CLOCK_REJECT_TRANSITION:
            if len(candidates) != 1:
                raise ValueError("calendar offset produced a nonexistent or ambiguous local time")
            return candidates[0]
        return next((item for item in candidates if item.fold == moment.fold), candidates[0])


def _timezone_name(moment: datetime) -> str:
    timezone = moment.tzinfo
    key = getattr(timezone, "key", None)
    if isinstance(key, str):
        return key
    if moment.utcoffset() == timedelta(0) and moment.tzname() == "UTC":
        return "UTC"
    return str(timezone)


def _valid_wall_clock_candidates(naive: datetime, timezone: ZoneInfo) -> tuple[datetime, ...]:
    candidates: list[datetime] = []
    instants: set[datetime] = set()
    for fold in (0, 1):
        candidate = naive.replace(tzinfo=timezone, fold=fold)
        instant = candidate.astimezone(UTC)
        round_trip = instant.astimezone(timezone)
        if round_trip.replace(tzinfo=None) != naive or round_trip.fold != fold:
            continue
        if instant in instants:
            continue
        instants.add(instant)
        candidates.append(candidate)
    return tuple(candidates)


__all__ = [
    "CalendarUnit",
    "MonthEndPolicy",
    "OffsetAnchor",
    "TemporalOffset",
    "TemporalOffsetKind",
    "TimezonePolicy",
]
