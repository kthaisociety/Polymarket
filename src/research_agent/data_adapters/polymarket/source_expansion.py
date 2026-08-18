"""Exact official CLOB price-history expansion into the temporal data kernel."""

# ruff: noqa: EM101, PLR0913, TRY003, TRY004

from __future__ import annotations

import hashlib
import json
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, cast

from research_agent.data_foundation import (
    ApprovedTemporalDataset,
    AuthoritativeDataCatalog,
    FieldDefinition,
    RegisteredTemporalDataset,
    TemporalDatasetProfile,
    TemporalRegistrationAuthority,
)
from research_agent.data_foundation._identity import require_aware, stable_identity
from research_agent.data_workspace import (
    DataWorkspace,
    DerivedDatasetRef,
    DeriveStatus,
    ScoutedFetchReceipt,
    ScoutedFetchStatus,
    SourceScoutingReportRef,
    SourceScoutingService,
    SourceSearchRequest,
    SourceSnapshotRef,
)

if TYPE_CHECKING:
    from research_agent.data_workspace.workspace import JsonValue

_PRICE_HISTORY_HOST = "clob.polymarket.com"
_PRICE_HISTORY_PATH = "/prices-history"
_DOCUMENTATION_URL = "https://docs.polymarket.com/api-reference/markets/get-prices-history"
_AVAILABILITY_RULE = "polymarket-clob-price-history-observation/v1"
_MAX_FIDELITY_MINUTES = 1_440
_PUBLIC_USER_AGENT = "ChronosResearch/0.1 (+https://github.com/)"
_MANDATORY_CAVEATS = (
    (
        "CLOB price-history samples are historical probability observations, not trades or "
        "executable quotes."
    ),
    (
        "The documented sample timestamp is treated as both reference_time and available_at; "
        "the endpoint does not establish historical revision or deletion behavior."
    ),
    "Sampling fidelity may omit intraperiod path and microstructure information.",
)

_PRICE_HISTORY_TRANSFORM = """\
payload = json_input("source")
if set(payload) != set(["history"]):
    invalid = 1 / 0
history = payload["history"]
if len(history) == 0:
    invalid = 1 / 0
observations = []
last_timestamp = int(param("start_ts")) - 1
for ordinal in range(len(history)):
    item = history[ordinal]
    if set(item) != set(["t", "p"]):
        invalid = 1 / 0
    timestamp = int(item["t"])
    price = float(item["p"])
    if (
        float(timestamp) != float(item["t"])
        or timestamp <= last_timestamp
        or timestamp < int(param("start_ts"))
        or timestamp > int(param("end_ts"))
        or price < 0.0
        or price > 1.0
    ):
        invalid = 1 / 0
    last_timestamp = timestamp
    observations = observations + [
        {
            "field_id": "market_probability",
            "value": price,
            "reference_time": unix_utc_iso(timestamp),
            "available_at": unix_utc_iso(timestamp),
            "vintage_id": str(param("vintage_id")),
            "revision_number": 0,
            "dimensions": {
                "market_id": str(param("market_id")),
                "event_id": str(param("event_id")),
                "outcome_index": str(param("outcome_index")),
                "outcome_token": str(param("outcome_token")),
                "fidelity_minutes": str(param("fidelity_minutes")),
            },
            "caveats": [],
        }
    ]
result = emit(
    {
        "schema_version": "temporal-observations/v1",
        "profile_id": str(param("profile_id")),
        "observations": observations,
    }
)
"""


class PolymarketSourceExpansionError(ValueError):
    """Raised when an exact source cannot cross the expansion boundary."""


@dataclass(frozen=True, slots=True)
class PolymarketPriceHistoryNeed:
    """Exact outcome-token slice requested from the official CLOB history endpoint."""

    environment_id: str
    market_id: str
    event_id: str
    outcome_index: int
    outcome_token: str
    start_time: datetime
    end_time: datetime
    fidelity_minutes: int

    def __post_init__(self) -> None:
        """Reject inferred, ambiguous, or non-integral request identity."""
        require_aware(self.start_time, "start_time")
        require_aware(self.end_time, "end_time")
        if not all((self.environment_id, self.market_id, self.event_id, self.outcome_token)):
            raise ValueError("price-history need requires exact non-empty identities")
        if self.outcome_index < 0:
            raise ValueError("outcome_index cannot be negative")
        if not self.outcome_token.isdecimal():
            raise ValueError("outcome_token must be the exact decimal CLOB token identity")
        if self.start_time >= self.end_time:
            raise ValueError("price-history start_time must precede end_time")
        if (
            not self.start_time.timestamp().is_integer()
            or not self.end_time.timestamp().is_integer()
        ):
            raise ValueError("price-history bounds must use integral Unix seconds")
        if not 1 <= self.fidelity_minutes <= _MAX_FIDELITY_MINUTES:
            raise ValueError("fidelity_minutes must be between 1 and 1440")

    @property
    def start_ts(self) -> int:
        """Return the exact integral UTC epoch lower bound."""
        return int(self.start_time.timestamp())

    @property
    def end_ts(self) -> int:
        """Return the exact integral UTC epoch upper bound."""
        return int(self.end_time.timestamp())

    @property
    def need_id(self) -> str:
        """Bind all requested market and sampling semantics."""
        return stable_identity("polymarket-price-history-need", self)

    @property
    def resource_url(self) -> str:
        """Return the only CLOB resource URL this need permits Chronos to contact."""
        query = urllib.parse.urlencode(
            (
                ("market", self.outcome_token),
                ("startTs", str(self.start_ts)),
                ("endTs", str(self.end_ts)),
                ("fidelity", str(self.fidelity_minutes)),
            )
        )
        return urllib.parse.urlunsplit(
            ("https", _PRICE_HISTORY_HOST, _PRICE_HISTORY_PATH, query, "")
        )

    def as_dict(self) -> dict[str, JsonValue]:
        """Serialize the exact need for an operator or external scout."""
        return {
            "schema_version": "polymarket-price-history-need/v1",
            "need_id": self.need_id,
            "environment_id": self.environment_id,
            "market_id": self.market_id,
            "event_id": self.event_id,
            "outcome_index": self.outcome_index,
            "outcome_token": self.outcome_token,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "fidelity_minutes": self.fidelity_minutes,
        }

    @classmethod
    def from_dict(cls, value: object) -> PolymarketPriceHistoryNeed:
        """Decode exact need JSON and reject stale identities or unknown keys."""
        if not isinstance(value, dict):
            raise ValueError("price-history need must be a JSON object")
        data = cast("dict[str, object]", value)
        expected = {
            "schema_version",
            "need_id",
            "environment_id",
            "market_id",
            "event_id",
            "outcome_index",
            "outcome_token",
            "start_time",
            "end_time",
            "fidelity_minutes",
        }
        if (
            set(data) != expected
            or data.get("schema_version") != "polymarket-price-history-need/v1"
        ):
            raise ValueError("price-history need schema is not exact")
        outcome_index = data.get("outcome_index")
        fidelity = data.get("fidelity_minutes")
        if (
            isinstance(outcome_index, bool)
            or not isinstance(outcome_index, int)
            or isinstance(fidelity, bool)
            or not isinstance(fidelity, int)
        ):
            raise ValueError("price-history integer fields are invalid")
        try:
            need = cls(
                environment_id=cast("str", data.get("environment_id")),
                market_id=cast("str", data.get("market_id")),
                event_id=cast("str", data.get("event_id")),
                outcome_index=outcome_index,
                outcome_token=cast("str", data.get("outcome_token")),
                start_time=datetime.fromisoformat(cast("str", data.get("start_time"))),
                end_time=datetime.fromisoformat(cast("str", data.get("end_time"))),
                fidelity_minutes=fidelity,
            )
        except (TypeError, ValueError) as error:
            raise ValueError("price-history need values are invalid") from error
        if data.get("need_id") != need.need_id:
            raise ValueError("price-history need identity does not match content")
        return need


@dataclass(frozen=True, slots=True)
class PolymarketSourceExpansion:
    """Successful exact acquisition, derivation, and temporal registration."""

    need_id: str
    scouted_fetch: ScoutedFetchReceipt
    registered: RegisteredTemporalDataset
    catalog: AuthoritativeDataCatalog

    def as_dict(self) -> dict[str, JsonValue]:
        """Return identities and coverage without publishing sampled probabilities."""
        fetch = self.scouted_fetch.fetch_receipt
        if fetch is None or fetch.snapshot_ref is None:
            raise ValueError("successful expansion lost its source reference")
        observations = self.registered.dataset.observations
        return {
            "schema_version": "polymarket-source-expansion-receipt/v1",
            "status": "succeeded",
            "need_id": self.need_id,
            "report_ref": self.scouted_fetch.report_ref.uri,
            "candidate_id": self.scouted_fetch.candidate_id,
            "source_ref": fetch.snapshot_ref.uri,
            "derived_ref": self.registered.derived_ref_uri,
            "profile_id": self.registered.profile_id,
            "registration_attestation_id": self.registered.attestation_id,
            "catalog_attestation_id": self.catalog.catalog_attestation_id,
            "observation_count": len(observations),
            "first_reference_time": observations[0].reference_time.isoformat(),
            "last_reference_time": observations[-1].reference_time.isoformat(),
            "availability_rule_version": observations[0].availability_rule_version,
            "caveats": list(_MANDATORY_CAVEATS),
            "sample_values_emitted": False,
            "production_database_writes": False,
        }


def price_history_search_request(
    need: PolymarketPriceHistoryNeed,
    *,
    research_question: str,
) -> SourceSearchRequest:
    """Create the bounded request an external scout can answer passively."""
    return SourceSearchRequest(
        research_question=research_question,
        data_need=(
            "Verify the official public Polymarket CLOB price-history resource for exact "
            f"need {need.need_id}; the selected machine-readable URL must be {need.resource_url}"
        ),
        search_queries=(
            "site:docs.polymarket.com api reference markets get prices history",
            "site:docs.polymarket.com clob prices-history fidelity startTs endTs",
        ),
        requirements=(
            "Publisher must be Polymarket.",
            "Resource must be public HTTPS and require no credentials.",
            "Resource URL must exactly preserve the requested token, bounds, and fidelity.",
            "Evidence must document timestamp and probability response fields.",
            "Proposal grants no data, temporal, or scientific authority.",
        ),
        max_candidates=4,
    )


def expand_scouted_price_history(
    workspace: DataWorkspace,
    *,
    report_ref: SourceScoutingReportRef,
    candidate_id: str,
    need: PolymarketPriceHistoryNeed,
    timeout_seconds: float = 30.0,
    max_response_bytes: int = 16 * 1024 * 1024,
) -> PolymarketSourceExpansion:
    """Cross every exact boundary from one selected proposal to registered observations."""
    scouting = SourceScoutingService(workspace)
    report = scouting.resolve_report(report_ref)
    candidate = next(
        (item for item in report.candidates if item.candidate_id == candidate_id),
        None,
    )
    if candidate is None:
        raise PolymarketSourceExpansionError("candidate was not issued by the selected report")
    if candidate.resource_url != need.resource_url:
        raise PolymarketSourceExpansionError(
            "candidate URL does not exactly match the requested token, window, and fidelity"
        )
    fetched = scouting.acquire_candidate(
        report_ref,
        candidate_id=candidate_id,
        max_response_bytes=max_response_bytes,
        timeout_seconds=timeout_seconds,
        allowed_redirect_hosts=(_PRICE_HISTORY_HOST,),
        permit_redirects=False,
        headers={"Accept": "application/json", "User-Agent": _PUBLIC_USER_AGENT},
    )
    if (
        fetched.status is not ScoutedFetchStatus.SUCCEEDED
        or fetched.fetch_receipt is None
        or fetched.fetch_receipt.snapshot_ref is None
    ):
        raise PolymarketSourceExpansionError("selected price-history source acquisition failed")
    source_ref = fetched.fetch_receipt.snapshot_ref
    profile = _profile(need)
    derived = workspace.derive(
        inputs={"source": source_ref},
        source=_PRICE_HISTORY_TRANSFORM,
        parameters={
            "profile_id": profile.identity,
            "start_ts": need.start_ts,
            "end_ts": need.end_ts,
            "market_id": need.market_id,
            "event_id": need.event_id,
            "outcome_index": need.outcome_index,
            "outcome_token": need.outcome_token,
            "fidelity_minutes": need.fidelity_minutes,
            "vintage_id": source_ref.snapshot_id,
        },
    )
    if derived.status is not DeriveStatus.SUCCEEDED or derived.dataset_ref is None:
        raise PolymarketSourceExpansionError("price-history response failed strict derivation")
    approval = ApprovedTemporalDataset(
        derived_ref=derived.dataset_ref,
        profile=profile,
        approval_ref=f"polymarket-price-history-adapter:{need.need_id}",
    )
    authority = TemporalRegistrationAuthority((approval,))
    registered = authority.register(workspace, approval)
    catalog = authority.catalog((registered,))
    return PolymarketSourceExpansion(need.need_id, fetched, registered, catalog)


def register_retained_price_history(
    workspace: DataWorkspace,
    *,
    need: PolymarketPriceHistoryNeed,
    source_ref_uri: str,
    derived_ref_uri: str,
) -> RegisteredTemporalDataset:
    """Re-register one exact retained expansion without network or semantic inference."""
    try:
        source_ref = workspace.resolve(source_ref_uri)
        derived_ref = workspace.resolve(derived_ref_uri)
    except (KeyError, OSError, ValueError) as error:
        raise PolymarketSourceExpansionError(
            "retained price-history lineage could not be resolved"
        ) from error
    if not isinstance(source_ref, SourceSnapshotRef) or not isinstance(
        derived_ref, DerivedDatasetRef
    ):
        raise PolymarketSourceExpansionError("retained price-history reference kinds are invalid")

    profile = _profile(need)
    expected_parameters = {
        "profile_id": profile.identity,
        "start_ts": need.start_ts,
        "end_ts": need.end_ts,
        "market_id": need.market_id,
        "event_id": need.event_id,
        "outcome_index": need.outcome_index,
        "outcome_token": need.outcome_token,
        "fidelity_minutes": need.fidelity_minutes,
        "vintage_id": source_ref.snapshot_id,
    }
    expected_code_sha256 = hashlib.sha256(_PRICE_HISTORY_TRANSFORM.encode()).hexdigest()
    expected_parameters_sha256 = hashlib.sha256(
        json.dumps(
            expected_parameters,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    ).hexdigest()
    if (
        derived_ref.code_sha256 != expected_code_sha256
        or derived_ref.input_ref_ids != (source_ref.uri,)
        or derived_ref.parameters_sha256 != expected_parameters_sha256
    ):
        raise PolymarketSourceExpansionError(
            "retained price-history derivation does not match the exact need and source"
        )

    approval = ApprovedTemporalDataset(
        derived_ref=derived_ref,
        profile=profile,
        approval_ref=f"polymarket-price-history-adapter:{need.need_id}",
    )
    authority = TemporalRegistrationAuthority((approval,))
    return authority.register(workspace, approval)


def _profile(need: PolymarketPriceHistoryNeed) -> TemporalDatasetProfile:
    need_digest = need.need_id.rsplit(":", 1)[-1]
    return TemporalDatasetProfile(
        dataset_id=f"polymarket-clob-price-history-{need_digest[:20]}",
        schema_version="v1",
        environment_id=need.environment_id,
        semantic_provenance_ref=_DOCUMENTATION_URL,
        availability_rule_version=_AVAILABILITY_RULE,
        fields=(
            FieldDefinition(
                field_id="market_probability",
                semantic_name="Polymarket CLOB sampled outcome probability",
                data_type="float",
                unit="probability_0_1",
                dimensions=(
                    "market_id",
                    "event_id",
                    "outcome_index",
                    "outcome_token",
                    "fidelity_minutes",
                ),
                description=(
                    "A timestamped historical probability sample returned by the official "
                    "Polymarket CLOB price-history endpoint."
                ),
            ),
        ),
        mandatory_caveats=_MANDATORY_CAVEATS,
    )


def expansion_receipt_json(expansion: PolymarketSourceExpansion) -> str:
    """Encode one sanitized receipt in canonical JSON for durable research evidence."""
    return json.dumps(expansion.as_dict(), allow_nan=False, indent=2, sort_keys=True) + "\n"


__all__ = [
    "PolymarketPriceHistoryNeed",
    "PolymarketSourceExpansion",
    "PolymarketSourceExpansionError",
    "expand_scouted_price_history",
    "expansion_receipt_json",
    "price_history_search_request",
    "register_retained_price_history",
]
