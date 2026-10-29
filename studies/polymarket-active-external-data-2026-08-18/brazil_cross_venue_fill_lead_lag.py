# ruff: noqa: C901, D103, INP001, PLR0913, T201

"""Explore source-time lead-lag in the retained Brazil cross-venue taker tape."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import statistics
from bisect import bisect_left, bisect_right
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Literal

_TAPE_SHA256 = "7a08c71c2e88563a247dd10d9a5480a435dc6b834fbed168907a041bf0ffb32c"
_AUDIT_SHA256 = "75ec8496452816964f4db6749c1ba90db0c3bd1c27a5e0b510ef2a9e66d67d89"
_TAPE_SCHEMA = "chronos-brazil-cross-venue-taker-fills/v1"
_AUDIT_SCHEMA = "chronos-brazil-cross-venue-semantic-audit/v1"
_RESEARCH_DECISION_TIME = "2026-08-23T11:04:12Z"
_MINIMUM_MOVE = Decimal("0.01")
_SOURCE_MAX_GAP_SECONDS = 7_200
_TRIGGER_COOLDOWN_SECONDS = 600
_HORIZONS_SECONDS = (30, 120, 600)
_FRESHNESS_SECONDS = (1_800, 7_200)
_PRIMARY_FRESHNESS_SECONDS = 1_800
_EXPECTED_ROWS = 59_000
_PAIR_IDS = {
    "lula": {
        "kalshi": "KXBRPRES-26-LULA",
        "polymarket": "0xdf8e2dc5860027decbe6164555c3c1c9645c3bd33e16b9dc57ca87125047d4a8",
    },
    "flavio": {
        "kalshi": "KXBRPRES-26-FBOL",
        "polymarket": "0x1a01bf78f56a507fcb666d564d8c8b91b0750679163ed6e96746102c9b7d285d",
    },
}
_MARKET_TO_CANDIDATE = {
    market_id: candidate
    for candidate, venues in _PAIR_IDS.items()
    for market_id in venues.values()
}
type Venue = Literal["kalshi", "polymarket"]
type Side = Literal["BUY", "SELL"]


@dataclass(frozen=True, slots=True)
class Fill:
    candidate: str
    venue: Venue
    market_id: str
    time: datetime
    fill_uid: str
    side: Side
    price: Decimal
    size: Decimal


@dataclass(frozen=True, slots=True)
class Observation:
    candidate: str
    venue: Venue
    side: Side | None
    time: datetime
    price: Decimal
    size: Decimal
    row_count: int


@dataclass(frozen=True, slots=True)
class Stream:
    observations: tuple[Observation, ...]
    times: tuple[datetime, ...]


@dataclass(frozen=True, slots=True)
class Trigger:
    candidate: str
    source_venue: Venue
    side: Side
    time: datetime
    innovation: Decimal
    source_gap_seconds: float


@dataclass(frozen=True, slots=True)
class WindowChange:
    change: Decimal
    baseline_age_seconds: float
    final_delay_seconds: float


@dataclass(frozen=True, slots=True)
class Outcome:
    candidate: str
    source_venue: Venue
    side: Side
    month: str
    horizon_seconds: int
    freshness_seconds: int
    innovation: Decimal
    post_same_side: WindowChange | None
    post_any_side: WindowChange | None
    reverse_same_side: WindowChange | None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_hash(path: Path, expected: str, label: str) -> None:
    observed = _sha256(path)
    if observed != expected:
        raise ValueError(f"{label} SHA-256 mismatch: {observed}")


def validate_audit(raw: object) -> None:
    if not isinstance(raw, dict) or raw.get("schema") != _AUDIT_SCHEMA:
        raise ValueError("unexpected semantic-audit schema")
    pairs = raw.get("pairs")
    if not isinstance(pairs, list) or len(pairs) != len(_PAIR_IDS):
        raise ValueError("semantic audit does not contain the exact pair population")
    observed: dict[str, dict[str, str]] = {}
    for item in pairs:
        if not isinstance(item, dict):
            raise TypeError("semantic-audit pair must be an object")
        candidate = item.get("candidate")
        if not isinstance(candidate, str):
            raise TypeError("semantic-audit candidate is missing")
        if (
            item.get("conservative_dominance_pair")
            != "buy Kalshi YES plus buy Polymarket NO"
            or item.get("minimum_combined_payout_under_documented_outcomes") != 1.0
        ):
            raise ValueError("semantic audit changed the authorized payout direction")
        observed[candidate] = {
            "kalshi": str(item.get("kalshi_market_id")),
            "polymarket": str(item.get("polymarket_market_id")),
        }
    if observed != _PAIR_IDS:
        raise ValueError("semantic audit market mapping does not match the authored study")


def validate_header(raw: object) -> dict[str, object]:
    if not isinstance(raw, dict) or raw.get("kind") != "header":
        raise ValueError("tape must start with one header")
    if raw.get("schema") != _TAPE_SCHEMA or raw.get("outcome_index") != 0:
        raise ValueError("unexpected fill-tape schema or outcome leg")
    if set(raw.get("kalshi_market_ids", ())) != {
        venues["kalshi"] for venues in _PAIR_IDS.values()
    } or set(raw.get("polymarket_market_ids", ())) != {
        venues["polymarket"] for venues in _PAIR_IDS.values()
    }:
        raise ValueError("fill-tape population does not match the exact semantic pairs")
    semantics = raw.get("row_semantics")
    if not isinstance(semantics, dict) or semantics.get("side") != "aggressor's YES-outcome side":
        raise ValueError("fill-tape aggressor-side semantics changed")
    return raw


def _parse_fill(raw: object) -> Fill:
    if not isinstance(raw, dict) or raw.get("kind") != "fill":
        raise ValueError("non-fill row found after the tape header")
    venue = raw.get("venue")
    side = raw.get("side")
    market_id = raw.get("market_id")
    if venue not in ("kalshi", "polymarket") or side not in ("BUY", "SELL"):
        raise ValueError("fill has unsupported venue or aggressor side")
    if not isinstance(market_id, str) or market_id not in _MARKET_TO_CANDIDATE:
        raise ValueError("fill belongs to an unauthorized market")
    price = Decimal(str(raw.get("price")))
    size = Decimal(str(raw.get("size")))
    if not 0 <= price <= 1 or size <= 0 or raw.get("outcome_index") != 0:
        raise ValueError("fill has invalid price, size, or outcome leg")
    fill_uid = raw.get("fill_uid")
    if not isinstance(fill_uid, str) or not fill_uid:
        raise ValueError("fill is missing exact source identity")
    return Fill(
        candidate=_MARKET_TO_CANDIDATE[market_id],
        venue=venue,
        market_id=market_id,
        time=datetime.fromisoformat(str(raw.get("fill_time"))).astimezone(UTC),
        fill_uid=fill_uid,
        side=side,
        price=price,
        size=size,
    )


def load_inputs(tape_path: Path, audit_path: Path) -> tuple[dict[str, object], tuple[Fill, ...]]:
    _require_hash(tape_path, _TAPE_SHA256, "fill tape")
    _require_hash(audit_path, _AUDIT_SHA256, "semantic audit")
    validate_audit(json.loads(audit_path.read_text()))
    fills: list[Fill] = []
    seen: set[tuple[Venue, str]] = set()
    with gzip.open(tape_path, "rt") as source:
        header = validate_header(json.loads(next(source)))
        previous_time: datetime | None = None
        for line in source:
            fill = _parse_fill(json.loads(line))
            identity = (fill.venue, fill.fill_uid)
            if identity in seen:
                raise ValueError("fill tape contains duplicate source identity")
            if previous_time is not None and fill.time < previous_time:
                raise ValueError("fill tape is not ordered by source reference time")
            seen.add(identity)
            fills.append(fill)
            previous_time = fill.time
    if len(fills) != _EXPECTED_ROWS:
        raise ValueError(f"expected {_EXPECTED_ROWS} exact fills, found {len(fills)}")
    return header, tuple(fills)


def collapse_observations(fills: tuple[Fill, ...]) -> tuple[Observation, ...]:
    grouped: dict[tuple[str, Venue, Side, datetime], list[Fill]] = defaultdict(list)
    for fill in fills:
        grouped[(fill.candidate, fill.venue, fill.side, fill.time)].append(fill)
    observations = []
    for (candidate, venue, side, time), rows in grouped.items():
        size = sum((row.size for row in rows), start=Decimal(0))
        price = sum((row.price * row.size for row in rows), start=Decimal(0)) / size
        observations.append(
            Observation(candidate, venue, side, time, price, size, len(rows))
        )
    return tuple(sorted(observations, key=lambda item: (item.time, item.candidate, item.venue, item.side)))


def build_streams(
    observations: tuple[Observation, ...],
) -> tuple[dict[tuple[str, Venue, Side], Stream], dict[tuple[str, Venue], Stream]]:
    same_side: dict[tuple[str, Venue, Side], list[Observation]] = defaultdict(list)
    any_side: dict[tuple[str, Venue], list[Observation]] = defaultdict(list)
    for observation in observations:
        assert observation.side is not None
        same_side[(observation.candidate, observation.venue, observation.side)].append(observation)
        any_side[(observation.candidate, observation.venue)].append(
            Observation(
                observation.candidate,
                observation.venue,
                None,
                observation.time,
                observation.price,
                observation.size,
                observation.row_count,
            )
        )
    return (
        {key: _stream(rows) for key, rows in same_side.items()},
        {key: _stream(rows) for key, rows in any_side.items()},
    )


def _stream(rows: list[Observation]) -> Stream:
    ordered = tuple(sorted(rows, key=lambda item: (item.time, item.side or "")))
    return Stream(ordered, tuple(item.time for item in ordered))


def build_triggers(same_side: dict[tuple[str, Venue, Side], Stream]) -> tuple[Trigger, ...]:
    candidates: list[Trigger] = []
    for (candidate, venue, side), stream in same_side.items():
        for previous, current in zip(stream.observations, stream.observations[1:], strict=False):
            gap = (current.time - previous.time).total_seconds()
            innovation = current.price - previous.price
            if gap <= _SOURCE_MAX_GAP_SECONDS and abs(innovation) >= _MINIMUM_MOVE:
                candidates.append(Trigger(candidate, venue, side, current.time, innovation, gap))
    selected: list[Trigger] = []
    last_by_source: dict[tuple[str, Venue], datetime] = {}
    for trigger in sorted(candidates, key=lambda item: (item.time, item.candidate, item.source_venue, item.side)):
        key = (trigger.candidate, trigger.source_venue)
        previous = last_by_source.get(key)
        if previous is not None and (trigger.time - previous).total_seconds() < _TRIGGER_COOLDOWN_SECONDS:
            continue
        selected.append(trigger)
        last_by_source[key] = trigger.time
    return tuple(selected)


def _window_change(
    stream: Stream | None,
    *,
    start: datetime,
    end: datetime,
    freshness_seconds: int,
    end_inclusive: bool,
) -> WindowChange | None:
    if stream is None:
        return None
    baseline_index = bisect_left(stream.times, start) - 1
    if baseline_index < 0:
        return None
    baseline = stream.observations[baseline_index]
    baseline_age = (start - baseline.time).total_seconds()
    if baseline_age > freshness_seconds:
        return None
    final_index = (
        bisect_right(stream.times, end) - 1
        if end_inclusive
        else bisect_left(stream.times, end) - 1
    )
    if final_index <= baseline_index or stream.observations[final_index].time <= start:
        return None
    final = stream.observations[final_index]
    return WindowChange(
        change=final.price - baseline.price,
        baseline_age_seconds=baseline_age,
        final_delay_seconds=(final.time - start).total_seconds(),
    )


def build_outcomes(
    triggers: tuple[Trigger, ...],
    same_side: dict[tuple[str, Venue, Side], Stream],
    any_side: dict[tuple[str, Venue], Stream],
) -> tuple[Outcome, ...]:
    outcomes = []
    for trigger in triggers:
        target_venue: Venue = "kalshi" if trigger.source_venue == "polymarket" else "polymarket"
        same_stream = same_side.get((trigger.candidate, target_venue, trigger.side))
        any_stream = any_side.get((trigger.candidate, target_venue))
        for horizon in _HORIZONS_SECONDS:
            for freshness in _FRESHNESS_SECONDS:
                outcomes.append(
                    Outcome(
                        candidate=trigger.candidate,
                        source_venue=trigger.source_venue,
                        side=trigger.side,
                        month=trigger.time.strftime("%Y-%m"),
                        horizon_seconds=horizon,
                        freshness_seconds=freshness,
                        innovation=trigger.innovation,
                        post_same_side=_window_change(
                            same_stream,
                            start=trigger.time,
                            end=trigger.time + timedelta(seconds=horizon),
                            freshness_seconds=freshness,
                            end_inclusive=True,
                        ),
                        post_any_side=_window_change(
                            any_stream,
                            start=trigger.time,
                            end=trigger.time + timedelta(seconds=horizon),
                            freshness_seconds=freshness,
                            end_inclusive=True,
                        ),
                        reverse_same_side=_window_change(
                            same_stream,
                            start=trigger.time - timedelta(seconds=horizon),
                            end=trigger.time,
                            freshness_seconds=freshness,
                            end_inclusive=False,
                        ),
                    )
                )
    return tuple(outcomes)


def response_eligible_triggers(
    triggers: tuple[Trigger, ...],
    same_side: dict[tuple[str, Venue, Side], Stream],
) -> tuple[Trigger, ...]:
    """Keep only triggers whose matched venue actually retained the same outcome-side path."""
    eligible = []
    for trigger in triggers:
        target_venue: Venue = "kalshi" if trigger.source_venue == "polymarket" else "polymarket"
        if (trigger.candidate, target_venue, trigger.side) in same_side:
            eligible.append(trigger)
    return tuple(eligible)


def _aligned(change: WindowChange, innovation: Decimal) -> float:
    sign = Decimal(1) if innovation > 0 else Decimal(-1)
    return float(sign * change.change)


def _mean(values: list[float]) -> float | None:
    return None if not values else statistics.fmean(values)


def _median(values: list[float]) -> float | None:
    return None if not values else statistics.median(values)


def summarize(group: list[Outcome], dimensions: dict[str, object]) -> dict[str, object]:
    post_rows = [item for item in group if item.post_same_side]
    post = [_aligned(item.post_same_side, item.innovation) for item in post_rows]
    raw = [_aligned(item.post_any_side, item.innovation) for item in group if item.post_any_side]
    reverse = [
        _aligned(item.reverse_same_side, item.innovation)
        for item in group
        if item.reverse_same_side
    ]
    paired = [
        (
            _aligned(item.post_same_side, item.innovation),
            _aligned(item.reverse_same_side, item.innovation),
        )
        for item in group
        if item.post_same_side and item.reverse_same_side
    ]
    return {
        **dimensions,
        "trigger_count": len(group),
        "trigger_mean_absolute_innovation": _mean(
            [float(abs(item.innovation)) for item in group]
        ),
        "post_same_side_count": len(post),
        "post_same_side_coverage": len(post) / len(group) if group else 0.0,
        "post_same_side_mean_aligned_change": _mean(post),
        "post_same_side_median_aligned_change": _median(post),
        "post_same_side_p10_aligned_change": _quantile(post, 0.1),
        "post_same_side_p90_aligned_change": _quantile(post, 0.9),
        "post_same_side_mean_absolute_change": _mean([abs(value) for value in post]),
        "post_same_side_median_baseline_age_seconds": _median(
            [item.post_same_side.baseline_age_seconds for item in post_rows]
        ),
        "post_same_side_median_final_delay_seconds": _median(
            [item.post_same_side.final_delay_seconds for item in post_rows]
        ),
        "post_same_side_positive_share": (
            sum(value > 0 for value in post) / len(post) if post else None
        ),
        "post_same_side_zero_share": sum(value == 0 for value in post) / len(post) if post else None,
        "post_any_side_count": len(raw),
        "post_any_side_mean_aligned_change": _mean(raw),
        "reverse_same_side_count": len(reverse),
        "reverse_same_side_mean_aligned_change": _mean(reverse),
        "paired_post_reverse_count": len(paired),
        "paired_mean_post_minus_reverse": (
            statistics.fmean(after - before for after, before in paired) if paired else None
        ),
    }


def _group_summaries(outcomes: tuple[Outcome, ...], fields: tuple[str, ...]) -> list[dict[str, object]]:
    groups: dict[tuple[object, ...], list[Outcome]] = defaultdict(list)
    for outcome in outcomes:
        key = tuple(getattr(outcome, field) for field in fields)
        groups[key].append(outcome)
    return [
        summarize(group, dict(zip(fields, key, strict=True)))
        for key, group in sorted(groups.items())
    ]


def _quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def coverage(fills: tuple[Fill, ...], observations: tuple[Observation, ...]) -> dict[str, object]:
    rows = []
    for candidate in sorted(_PAIR_IDS):
        for venue in ("kalshi", "polymarket"):
            subset = [item for item in fills if item.candidate == candidate and item.venue == venue]
            points = [
                item.time
                for item in observations
                if item.candidate == candidate and item.venue == venue
            ]
            gaps = [
                (current - previous).total_seconds()
                for previous, current in zip(points, points[1:], strict=False)
            ]
            start = min((item.time for item in subset), default=None)
            end = max((item.time for item in subset), default=None)
            rows.append(
                {
                    "candidate": candidate,
                    "venue": venue,
                    "fill_count": len(subset),
                    "collapsed_observation_count": len(points),
                    "start": None if start is None else start.isoformat(),
                    "end": None if end is None else end.isoformat(),
                    "buy_fill_count": sum(item.side == "BUY" for item in subset),
                    "sell_fill_count": sum(item.side == "SELL" for item in subset),
                    "interarrival_seconds_p50": _quantile(gaps, 0.5),
                    "interarrival_seconds_p90": _quantile(gaps, 0.9),
                    "interarrival_seconds_p99": _quantile(gaps, 0.99),
                }
            )
    return {"by_candidate_venue": rows}


def analyze(header: dict[str, object], fills: tuple[Fill, ...]) -> dict[str, object]:
    observations = collapse_observations(fills)
    same_side, any_side = build_streams(observations)
    raw_triggers = build_triggers(same_side)
    triggers = response_eligible_triggers(raw_triggers, same_side)
    outcomes = build_outcomes(triggers, same_side, any_side)
    code_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    primary = tuple(
        item for item in outcomes if item.freshness_seconds == _PRIMARY_FRESHNESS_SECONDS
    )
    return {
        "schema": "chronos-brazil-cross-venue-fill-lead-lag/v1",
        "epistemic_status": "EXPLORATORY_SOURCE_TIME_PRINT_DIAGNOSTIC",
        "research_decision_time": _RESEARCH_DECISION_TIME,
        "code_sha256": code_sha256,
        "input": {
            "tape_sha256": _TAPE_SHA256,
            "audit_sha256": _AUDIT_SHA256,
            "environment_id": header["environment_id"],
            "source_start": header["start"],
            "source_end": header["end"],
            "fill_count": len(fills),
            "accessed_fields": [
                "venue",
                "fill_time",
                "fill_uid",
                "market_id",
                "outcome_index",
                "side",
                "price",
                "size",
            ],
        },
        "time_semantics": {
            "reference_time": "fill_time from each retained venue tape",
            "available_at": None,
            "label_maturity": None,
            "warning": (
                "The corpus has no collector receipt clock. Source-time ordering is descriptive "
                "and cannot establish a historically executable information set."
            ),
            "kalshi_side_warning": (
                "The outcome_index=0 acquisition retained only Kalshi YES-taking rows; all are "
                "BUY. Opposite YES direction is missing, so the scout is one-sided."
            ),
        },
        "parameters": {
            "minimum_same_side_move": str(_MINIMUM_MOVE),
            "source_max_gap_seconds": _SOURCE_MAX_GAP_SECONDS,
            "trigger_cooldown_seconds": _TRIGGER_COOLDOWN_SECONDS,
            "horizons_seconds": _HORIZONS_SECONDS,
            "matched_baseline_freshness_seconds": _FRESHNESS_SECONDS,
            "primary_freshness_seconds": _PRIMARY_FRESHNESS_SECONDS,
            "same_timestamp_policy": "size-weighted price within candidate/venue/side/fill_time",
            "baseline_policy": "strictly before trigger source time",
            "response_policy": "latest same-side print in (trigger, trigger+horizon]",
            "missing_response_policy": "missing, never zero",
            "weighting": "unweighted trigger observations",
            "eligible_trigger_policy": (
                "retain only a trigger side present on the matched venue; report excluded raw "
                "triggers rather than treating the missing path as no response"
            ),
        },
        "coverage": coverage(fills, observations),
        "raw_trigger_count": len(raw_triggers),
        "trigger_count": len(triggers),
        "excluded_missing_matched_side_trigger_count": len(raw_triggers) - len(triggers),
        "raw_trigger_counts_by_side": {
            f"{candidate}:{venue}:{side}": sum(
                item.candidate == candidate
                and item.source_venue == venue
                and item.side == side
                for item in raw_triggers
            )
            for candidate in sorted(_PAIR_IDS)
            for venue in ("kalshi", "polymarket")
            for side in ("BUY", "SELL")
        },
        "trigger_counts": {
            f"{candidate}:{venue}": sum(
                item.candidate == candidate and item.source_venue == venue for item in triggers
            )
            for candidate in sorted(_PAIR_IDS)
            for venue in ("kalshi", "polymarket")
        },
        "primary_overall": _group_summaries(
            primary, ("source_venue", "horizon_seconds", "freshness_seconds")
        ),
        "primary_by_candidate": _group_summaries(
            primary,
            ("candidate", "source_venue", "horizon_seconds", "freshness_seconds"),
        ),
        "primary_by_month": _group_summaries(
            primary,
            ("month", "source_venue", "horizon_seconds", "freshness_seconds"),
        ),
        "freshness_sensitivity": _group_summaries(
            outcomes, ("source_venue", "horizon_seconds", "freshness_seconds")
        ),
        "limitations": [
            "transaction prices are not executable quotes or midpoint observations",
            "same-aggressor paths reduce but do not eliminate spread, selection, or venue mechanics",
            "matched response statistics condition on a new print and report coverage separately",
            "the two candidates belong to one dependent election family",
            "the retained Kalshi tape omits NO-taking trades and cannot test a symmetric YES path",
            "source timestamps are not collector available_at timestamps",
            "no fee, depth, queue, acknowledgement, partial-fill, or PnL claim is made",
        ],
    }


def analyze_rows(header: object, rows: tuple[object, ...]) -> dict[str, object]:
    """Exercise the authored analysis over strict in-memory rows for regression tests."""
    validated = validate_header(header)
    fills = tuple(_parse_fill(row) for row in rows)
    return analyze(validated, fills)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tape", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    header, fills = load_inputs(args.tape, args.audit)
    result = analyze(header, fills)
    content = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
    with args.output.open("xb") as output:
        output.write(content)
    print(
        json.dumps(
            {
                "status": "EXPLORATORY",
                "fill_count": len(fills),
                "trigger_count": result["trigger_count"],
                "output_sha256": hashlib.sha256(content).hexdigest(),
                "code_sha256": result["code_sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
