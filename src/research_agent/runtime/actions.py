"""Typed decoding of untrusted model action requests."""

# ruff: noqa: EM101, EM102, PLR2004, TRY003

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, cast

from research_agent.data_foundation import (
    CalendarUnit,
    FieldRef,
    MonthEndPolicy,
    OffsetAnchor,
    TemporalOffset,
    TimezonePolicy,
)
from research_agent.investigation import AuthoredCandidateManifest, AuthoredProgramProposal
from research_agent.runtime.models import EpisodeStatus

if TYPE_CHECKING:
    from research_agent.runtime.provider import ModelResponse


class ActionDecodeError(ValueError):
    """Provider response could not be decoded safely."""


@dataclass(frozen=True, slots=True)
class InspectDatasetAction:
    """Bounded read-only request for dataset metadata and preview."""

    action_id: str
    session_id: str
    episode_id: str
    dataset_ref: str
    selected_field_ids: tuple[str, ...]
    preview_limit: int


@dataclass(frozen=True, slots=True)
class AnalysisDataAccessRequest:
    """Exact exploratory view and fields requested by the model."""

    view_id: str
    field_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RunAnalysisAction:
    """Open-ended authored analysis carrying no execution authority."""

    action_id: str
    session_id: str
    episode_id: str
    source: str
    data_access: tuple[AnalysisDataAccessRequest, ...]
    random_seed: int | None = None


@dataclass(frozen=True, slots=True)
class RunScientificWorkflowAction:
    """Request one exact pre-registered scientific workflow without authored payload."""

    action_id: str
    session_id: str
    episode_id: str
    workflow_id: str
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class RunAuthoredDevelopmentTrialAction:
    """Submit one arbitrary scientific program to an exact registered investigation."""

    action_id: str
    session_id: str
    episode_id: str
    investigation_id: str
    proposal: AuthoredProgramProposal
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class EpisodeTransitionProposal:
    """Untrusted requested lifecycle change with explicit synthesis."""

    target_status: EpisodeStatus
    synthesis: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StateUpdateProposal:
    """Independent proposed durable-state delta."""

    starting_state_version: int
    durable_understanding: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProposeEpisodeTransitionAction:
    """Request semantic commit; carries no direct mutation authority."""

    action_id: str
    session_id: str
    episode_id: str
    transition: EpisodeTransitionProposal
    state_update: StateUpdateProposal | None
    idempotency_key: str


type AgentAction = (
    InspectDatasetAction
    | RunAnalysisAction
    | RunScientificWorkflowAction
    | RunAuthoredDevelopmentTrialAction
    | ProposeEpisodeTransitionAction
)


def decode_action(response: ModelResponse) -> AgentAction:
    """Decode only the four approved action families with strict identities."""
    raw = response.action
    _require_exact_keys(
        raw,
        required={"kind", "action_id", "session_id", "episode_id", "arguments"},
    )
    kind = _required_str(raw, "kind")
    action_id = _required_str(raw, "action_id")
    session_id = _required_str(raw, "session_id")
    episode_id = _required_str(raw, "episode_id")
    arguments = raw.get("arguments")
    if not isinstance(arguments, Mapping):
        raise ActionDecodeError("Action arguments must be a mapping.")
    arguments = cast("Mapping[str, object]", arguments)
    if kind == "inspect_dataset":
        _require_exact_keys(
            arguments,
            required={"dataset_ref"},
            optional={"selected_field_ids", "preview_limit"},
        )
        fields = _string_tuple(arguments.get("selected_field_ids", ()), "selected_field_ids")
        preview = arguments.get("preview_limit", 5)
        if not isinstance(preview, int) or isinstance(preview, bool):
            raise ActionDecodeError("preview_limit must be an integer.")
        return InspectDatasetAction(
            action_id,
            session_id,
            episode_id,
            _required_str(arguments, "dataset_ref"),
            fields,
            preview,
        )
    if kind == "run_analysis":
        return _decode_analysis_action(
            arguments,
            action_id=action_id,
            session_id=session_id,
            episode_id=episode_id,
        )
    if kind == "run_scientific_workflow":
        _require_exact_keys(
            arguments,
            required={"workflow_id", "idempotency_key"},
        )
        return RunScientificWorkflowAction(
            action_id=action_id,
            session_id=session_id,
            episode_id=episode_id,
            workflow_id=_required_str(arguments, "workflow_id"),
            idempotency_key=_required_str(arguments, "idempotency_key"),
        )
    if kind == "run_authored_development_trial":
        return _decode_authored_trial_action(
            arguments,
            action_id=action_id,
            session_id=session_id,
            episode_id=episode_id,
        )
    if kind == "propose_episode_transition":
        return _decode_transition_action(
            arguments,
            action_id=action_id,
            session_id=session_id,
            episode_id=episode_id,
        )
    raise ActionDecodeError(f"Unknown action kind {kind!r}.")


def _decode_analysis_action(
    arguments: Mapping[str, object],
    *,
    action_id: str,
    session_id: str,
    episode_id: str,
) -> RunAnalysisAction:
    _require_exact_keys(
        arguments,
        required={"source", "data_access"},
        optional={"random_seed"},
    )
    source = _required_str(arguments, "source")
    access_value = arguments.get("data_access", ())
    if not isinstance(access_value, (list, tuple)):
        raise ActionDecodeError("data_access must be a sequence of objects.")
    access_items = cast("list[object] | tuple[object, ...]", access_value)
    data_access: list[AnalysisDataAccessRequest] = []
    for access_value_item in access_items:
        if not isinstance(access_value_item, Mapping):
            raise ActionDecodeError("Each data_access item must be an object.")
        access_item = cast("Mapping[str, object]", access_value_item)
        _require_exact_keys(access_item, required={"view_id", "field_ids"})
        data_access.append(
            AnalysisDataAccessRequest(
                view_id=_required_str(access_item, "view_id"),
                field_ids=_string_tuple(access_item.get("field_ids", ()), "field_ids"),
            )
        )
    random_seed = arguments.get("random_seed")
    if random_seed is not None and (
        not isinstance(random_seed, int) or isinstance(random_seed, bool)
    ):
        raise ActionDecodeError("random_seed must be an integer or null.")
    return RunAnalysisAction(
        action_id=action_id,
        session_id=session_id,
        episode_id=episode_id,
        source=source,
        data_access=tuple(data_access),
        random_seed=random_seed,
    )


def _decode_transition_action(
    arguments: Mapping[str, object],
    *,
    action_id: str,
    session_id: str,
    episode_id: str,
) -> ProposeEpisodeTransitionAction:
    _require_exact_keys(
        arguments,
        required={"target_status", "synthesis", "evidence_refs", "idempotency_key"},
        optional={"state_update"},
    )
    status_text = _required_str(arguments, "target_status")
    try:
        target_status = EpisodeStatus(status_text.lower())
    except ValueError as error:
        raise ActionDecodeError("Unknown episode target status.") from error
    evidence_refs = _string_tuple(arguments.get("evidence_refs", ()), "evidence_refs")
    state_update = _decode_state_update(arguments.get("state_update"))
    return ProposeEpisodeTransitionAction(
        action_id=action_id,
        session_id=session_id,
        episode_id=episode_id,
        transition=EpisodeTransitionProposal(
            target_status,
            _required_str(arguments, "synthesis"),
            evidence_refs,
        ),
        state_update=state_update,
        idempotency_key=_required_str(arguments, "idempotency_key"),
    )


def _decode_authored_trial_action(
    arguments: Mapping[str, object],
    *,
    action_id: str,
    session_id: str,
    episode_id: str,
) -> RunAuthoredDevelopmentTrialAction:
    _require_exact_keys(
        arguments,
        required={
            "investigation_id",
            "source",
            "manifest",
            "rationale",
            "parent_trial_ids",
            "idempotency_key",
        },
    )
    manifest_value = arguments.get("manifest")
    if not isinstance(manifest_value, Mapping):
        raise ActionDecodeError("manifest must be an exact object")
    manifest = _decode_candidate_manifest(cast("Mapping[str, object]", manifest_value))
    proposal = AuthoredProgramProposal(
        source=_required_str(arguments, "source"),
        manifest=manifest,
        rationale=_required_str(arguments, "rationale"),
        parent_trial_ids=_string_tuple(arguments.get("parent_trial_ids"), "parent_trial_ids"),
    )
    return RunAuthoredDevelopmentTrialAction(
        action_id=action_id,
        session_id=session_id,
        episode_id=episode_id,
        investigation_id=_required_str(arguments, "investigation_id"),
        proposal=proposal,
        idempotency_key=_required_str(arguments, "idempotency_key"),
    )


def _decode_candidate_manifest(value: Mapping[str, object]) -> AuthoredCandidateManifest:
    _require_exact_keys(
        value,
        required={
            "question_id",
            "environment_id",
            "predictor_fields",
            "outcome_field",
            "horizon",
            "minimum_outcome_points",
            "population_dimensions",
            "feature_names",
            "missing_value_policy",
            "evidence_refs",
            "provenance_refs",
        },
    )
    predictor_values = value.get("predictor_fields")
    if not isinstance(predictor_values, (list, tuple)):
        raise ActionDecodeError("predictor_fields must be a sequence")
    predictor_items = cast("list[object] | tuple[object, ...]", predictor_values)
    predictors = tuple(_decode_field_ref(item) for item in predictor_items)
    outcome = _decode_field_ref(value.get("outcome_field"))
    horizon_value = value.get("horizon")
    if not isinstance(horizon_value, Mapping):
        raise ActionDecodeError("horizon must be an exact object")
    minimum = value.get("minimum_outcome_points")
    if not isinstance(minimum, int) or isinstance(minimum, bool):
        raise ActionDecodeError("minimum_outcome_points must be an integer")
    return AuthoredCandidateManifest(
        question_id=_required_str(value, "question_id"),
        environment_id=_required_str(value, "environment_id"),
        predictor_fields=predictors,
        outcome_field=outcome,
        horizon=_decode_temporal_offset(cast("Mapping[str, object]", horizon_value)),
        minimum_outcome_points=minimum,
        population_dimensions=_pair_tuple(
            value.get("population_dimensions"), "population_dimensions"
        ),
        feature_names=_string_tuple(value.get("feature_names"), "feature_names"),
        missing_value_policy=_required_str(value, "missing_value_policy"),
        evidence_refs=_string_tuple(value.get("evidence_refs"), "evidence_refs"),
        provenance_refs=_string_tuple(value.get("provenance_refs"), "provenance_refs"),
    )


def _decode_field_ref(value: object) -> FieldRef:
    if not isinstance(value, Mapping):
        raise ActionDecodeError("field reference must be an exact object")
    field = cast("Mapping[str, object]", value)
    _require_exact_keys(
        field,
        required={"dataset_id", "schema_version", "field_id", "environment_id"},
    )
    return FieldRef(
        dataset_id=_required_str(field, "dataset_id"),
        schema_version=_required_str(field, "schema_version"),
        field_id=_required_str(field, "field_id"),
        environment_id=_required_str(field, "environment_id"),
    )


def _decode_temporal_offset(value: Mapping[str, object]) -> TemporalOffset:
    kind = _required_str(value, "kind")
    if kind == "elapsed":
        _require_exact_keys(value, required={"kind", "elapsed_microseconds"})
        microseconds = value.get("elapsed_microseconds")
        if not isinstance(microseconds, int) or isinstance(microseconds, bool):
            raise ActionDecodeError("elapsed_microseconds must be an integer")
        return TemporalOffset.elapsed(timedelta(microseconds=microseconds))
    if kind != "calendar":
        raise ActionDecodeError("unknown temporal offset kind")
    _require_exact_keys(
        value,
        required={
            "kind",
            "count",
            "unit",
            "anchor",
            "month_end_policy",
            "timezone_name",
            "timezone_policy",
        },
    )
    count = value.get("count")
    if not isinstance(count, int) or isinstance(count, bool):
        raise ActionDecodeError("calendar count must be an integer")
    try:
        unit = CalendarUnit(_required_str(value, "unit"))
        anchor = OffsetAnchor(_required_str(value, "anchor"))
        month_end = MonthEndPolicy(_required_str(value, "month_end_policy"))
        timezone_policy = TimezonePolicy(_required_str(value, "timezone_policy"))
    except ValueError as error:
        raise ActionDecodeError("unknown calendar temporal policy") from error
    return TemporalOffset.calendar(
        count=count,
        unit=unit,
        anchor=anchor,
        month_end_policy=month_end,
        timezone_name=_required_str(value, "timezone_name"),
        timezone_policy=timezone_policy,
    )


def _pair_tuple(value: object, name: str) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, (list, tuple)):
        raise ActionDecodeError(f"{name} must be a sequence of pairs")
    result: list[tuple[str, str]] = []
    items = cast("list[object] | tuple[object, ...]", value)
    for item in items:
        if not isinstance(item, (list, tuple)):
            raise ActionDecodeError(f"{name} must contain text pairs")
        pair = cast("list[object] | tuple[object, ...]", item)
        if len(pair) != 2 or not all(isinstance(part, str) for part in pair):
            raise ActionDecodeError(f"{name} must contain text pairs")
        result.append((cast("str", pair[0]), cast("str", pair[1])))
    return tuple(result)


def _decode_state_update(state_value: object) -> StateUpdateProposal | None:
    if state_value is None:
        return None
    if not isinstance(state_value, Mapping):
        raise ActionDecodeError("state_update must be an object or null.")
    state_raw = cast("Mapping[str, object]", state_value)
    _require_exact_keys(
        state_raw,
        required={"starting_state_version", "durable_understanding", "evidence_refs"},
    )
    version = state_raw.get("starting_state_version")
    if not isinstance(version, int) or isinstance(version, bool):
        raise ActionDecodeError("starting_state_version must be an integer.")
    return StateUpdateProposal(
        version,
        _string_tuple(
            state_raw.get("durable_understanding", ()),
            "durable_understanding",
        ),
        _string_tuple(state_raw.get("evidence_refs", ()), "state evidence_refs"),
    )


def _required_str(value: Mapping[str, object], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ActionDecodeError(f"{key} must be non-empty text.")
    return item


def _require_exact_keys(
    value: Mapping[str, object],
    *,
    required: set[str],
    optional: set[str] | None = None,
) -> None:
    allowed = required | (optional or set())
    if not required.issubset(value) or not set(value).issubset(allowed):
        raise ActionDecodeError("Action does not match the exact schema.")


def _string_tuple(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ActionDecodeError(f"{name} must be a sequence of strings.")
    items = cast("list[object] | tuple[object, ...]", value)
    if not all(isinstance(item, str) for item in items):
        raise ActionDecodeError(f"{name} must be a sequence of strings.")
    return tuple(cast("list[str] | tuple[str, ...]", items))


__all__ = [
    "ActionDecodeError",
    "AgentAction",
    "AnalysisDataAccessRequest",
    "EpisodeTransitionProposal",
    "InspectDatasetAction",
    "ProposeEpisodeTransitionAction",
    "RunAnalysisAction",
    "RunAuthoredDevelopmentTrialAction",
    "RunScientificWorkflowAction",
    "StateUpdateProposal",
    "decode_action",
]
