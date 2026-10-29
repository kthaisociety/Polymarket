"""Run an exact multi-study Polymarket corpus catalog through campaign authority."""

# ruff: noqa: EM101, EM102, T201, TRY003, TRY301

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

from research_agent.data_adapters.polymarket.behavioral_fills import (
    BehavioralFillSnapshotRef,
    BehavioralFillStore,
    build_behavioral_fill_analysis,
)
from research_agent.data_adapters.polymarket.campaign_analysis import (
    CampaignInputView,
    build_polymarket_campaign_analysis_for_views,
)
from research_agent.data_adapters.polymarket.corpus import (
    PolymarketCorpusSnapshotRef,
    PolymarketCorpusStore,
)
from research_agent.data_adapters.polymarket.corpus_analysis import (
    build_polymarket_development_analysis,
    build_polymarket_replication_analysis,
)
from research_agent.exploration import (
    AnalysisDisposition,
    CampaignManifest,
    CampaignStore,
    EvidenceTier,
    ResearchCampaignAuthority,
    ResourceLimits,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from research_agent.data_adapters.polymarket.corpus_analysis import (
        PolymarketDevelopmentAnalysis,
    )

_SCHEMA_VERSION = "chronos-polymarket-corpus-campaign/v1"
_ACCESS_COMPONENT_COUNT = 2


@dataclass(frozen=True, slots=True)
class CorpusInput:
    """One exact retained corpus partition available to catalog studies."""

    input_id: str
    snapshot: PolymarketCorpusSnapshotRef
    ancestor: PolymarketCorpusSnapshotRef | None
    partition_id: str
    wall_time_seconds: float
    max_memory_bytes: int
    max_inline_bytes: int
    max_result_bytes: int
    behavioral_fill_snapshot: BehavioralFillSnapshotRef | None

    @property
    def resource_limits(self) -> ResourceLimits:
        """Return the catalog-owned limits enforced on every source in this input."""
        return ResourceLimits(
            wall_time_seconds=self.wall_time_seconds,
            max_memory_bytes=self.max_memory_bytes,
            max_inline_bytes=self.max_inline_bytes,
            max_result_bytes=self.max_result_bytes,
        )


@dataclass(frozen=True, slots=True)
class CorpusStudy:
    """One exact source, input partition, evidence ceiling, and interpretation."""

    analysis_id: str
    family: str
    source_path: Path
    input_id: str
    evidence_tier: EvidenceTier
    disposition: AnalysisDisposition
    required_accesses: tuple[tuple[str, str], ...] | None


@dataclass(frozen=True, slots=True)
class CorpusCampaignCatalog:
    """Validated complete catalog used to construct an immutable campaign manifest."""

    campaign_id: str
    mandate: str
    session_id: str
    execution_evidence_tier: EvidenceTier
    inputs: tuple[CorpusInput, ...]
    studies: tuple[CorpusStudy, ...]


def build_parser() -> argparse.ArgumentParser:
    """Build the retained-corpus campaign command surface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--corpus-workspace", required=True, type=Path)
    parser.add_argument("--campaign-directory", required=True, type=Path)
    parser.add_argument("--behavioral-fill-workspace", type=Path)
    parser.add_argument("--defer-completion", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Execute a complete catalog, retaining authority-owned receipts as it progresses."""
    arguments = build_parser().parse_args(argv)
    try:
        catalog = load_catalog(arguments.catalog)
        corpus_store = PolymarketCorpusStore(arguments.corpus_workspace)
        preflight = _preflight_harnesses(
            corpus_store,
            catalog,
            behavioral_fill_workspace=arguments.behavioral_fill_workspace,
        )
        sources = {study.analysis_id: study.source_path.read_text() for study in catalog.studies}
        campaign_analyses = tuple(
            build_polymarket_campaign_analysis_for_views(
                analysis_id=study.analysis_id,
                family=study.family,
                source=sources[study.analysis_id],
                views=preflight[study.input_id][1],
                expected_harness_binding_identity=preflight[study.input_id][0],
                evidence_tier=catalog.execution_evidence_tier,
                required_accesses=study.required_accesses,
            )
            for study in catalog.studies
        )
        authority = ResearchCampaignAuthority(
            CampaignManifest(catalog.campaign_id, catalog.mandate, campaign_analyses),
            store=CampaignStore(arguments.campaign_directory),
        )
        receipts: list[dict[str, object]] = []
        for corpus_input in catalog.inputs:
            analysis = _load_analysis(
                corpus_store,
                corpus_input,
                session_id=catalog.session_id,
                behavioral_fill_workspace=arguments.behavioral_fill_workspace,
            )
            if analysis.partition.partition_id != corpus_input.partition_id:
                raise ValueError("catalog partition identity differs from retained input bytes")
            for study in catalog.studies:
                if study.input_id != corpus_input.input_id:
                    continue
                receipt = authority.execute(
                    study.analysis_id,
                    harness=analysis.harness,
                    session_id=catalog.session_id,
                )
                receipts.append(
                    {
                        "analysis_id": receipt.analysis_id,
                        "receipt_id": receipt.receipt_id,
                        "status": receipt.harness_execution_status,
                        "admissible": receipt.admissible,
                    }
                )
        completion = None
        if not arguments.defer_completion:
            completion = authority.complete(
                {study.analysis_id: study.disposition for study in catalog.studies}
            )
    except (KeyError, OSError, TypeError, ValueError) as error:
        print(
            json.dumps(
                {
                    "status": "FAILED",
                    "error_code": "POLYMARKET_CAMPAIGN_FAILED",
                    "error_type": type(error).__name__,
                },
                sort_keys=True,
            )
        )
        return 2
    print(
        json.dumps(
            {
                "status": ("EXECUTED_PENDING_DISPOSITIONS" if completion is None else "SUCCEEDED"),
                "campaign_identity": authority.manifest.identity,
                "completion_receipt_id": (None if completion is None else completion.receipt_id),
                "analysis_count": len(receipts),
                "receipts": receipts,
            },
            sort_keys=True,
        )
    )
    return 0


def load_catalog(path: Path) -> CorpusCampaignCatalog:
    """Load and strictly validate one explicit JSON campaign inventory."""
    raw = cast("object", json.loads(path.read_bytes()))
    if not isinstance(raw, dict):
        raise TypeError("Polymarket campaign catalog must be a JSON object")
    catalog = cast("Mapping[str, object]", raw)
    if catalog.get("schema_version") != _SCHEMA_VERSION:
        raise ValueError("unsupported Polymarket campaign catalog schema")
    base = path.parent
    input_values = _list_of_mappings(catalog, "inputs")
    study_values = _list_of_mappings(catalog, "analyses")
    inputs = tuple(_parse_input(item) for item in input_values)
    input_ids = {item.input_id for item in inputs}
    if len(input_ids) != len(inputs):
        raise ValueError("campaign catalog input identities must be unique")
    studies = tuple(_parse_study(item, base=base) for item in study_values)
    analysis_ids = {item.analysis_id for item in studies}
    if len(analysis_ids) != len(studies):
        raise ValueError("campaign catalog analysis identities must be unique")
    if not studies or any(study.input_id not in input_ids for study in studies):
        raise ValueError("every campaign study must reference one declared input")
    campaign_id = _required_string(catalog, "campaign_id")
    mandate = _required_string(catalog, "mandate")
    session_id = _required_string(catalog, "session_id")
    execution_evidence_tier = EvidenceTier[_required_string(catalog, "execution_evidence_tier")]
    if any(execution_evidence_tier > study.evidence_tier for study in studies):
        raise ValueError("campaign execution tier exceeds a study's prior evidence ceiling")
    return CorpusCampaignCatalog(
        campaign_id,
        mandate,
        session_id,
        execution_evidence_tier,
        inputs,
        studies,
    )


def _parse_input(raw: Mapping[str, object]) -> CorpusInput:
    ancestor_sha = raw.get("ancestor_snapshot_sha256")
    ancestor_size = raw.get("ancestor_snapshot_size")
    if (ancestor_sha is None) != (ancestor_size is None):
        raise ValueError("ancestor snapshot digest and size must be supplied together")
    ancestor = (
        None
        if ancestor_sha is None
        else PolymarketCorpusSnapshotRef(str(ancestor_sha), int(cast("int", ancestor_size)))
    )
    behavioral_fill_snapshot = _optional_behavioral_fill_ref(raw)
    if ancestor is not None and behavioral_fill_snapshot is not None:
        raise ValueError("behavioral fill inputs cannot also declare a replication ancestor")
    return CorpusInput(
        input_id=_required_string(raw, "input_id"),
        snapshot=PolymarketCorpusSnapshotRef(
            _required_string(raw, "snapshot_sha256"),
            _required_int(raw, "snapshot_size"),
        ),
        ancestor=ancestor,
        partition_id=_required_string(raw, "partition_id"),
        wall_time_seconds=_optional_float(raw, "wall_time_seconds", 180.0),
        max_memory_bytes=_optional_int(raw, "max_memory_bytes", 4_000_000_000),
        max_inline_bytes=_optional_int(raw, "max_inline_bytes", 500_000),
        max_result_bytes=_optional_int(raw, "max_result_bytes", 4_000_000),
        behavioral_fill_snapshot=behavioral_fill_snapshot,
    )


def _parse_study(raw: Mapping[str, object], *, base: Path) -> CorpusStudy:
    accesses_raw = raw.get("required_accesses")
    required_accesses = None
    if accesses_raw is not None:
        if not isinstance(accesses_raw, list):
            raise TypeError("required_accesses must be a list")
        pairs: list[tuple[str, str]] = []
        for raw_item in cast("list[object]", accesses_raw):
            if not isinstance(raw_item, list):
                raise TypeError("required access must be a two-item list")
            item = cast("list[object]", raw_item)
            if len(item) != _ACCESS_COMPONENT_COUNT or not all(
                isinstance(value, str) and value for value in item
            ):
                raise TypeError("required access must contain exact view and field strings")
            pairs.append((cast("str", item[0]), cast("str", item[1])))
        required_accesses = tuple(pairs)
    source_path = (base / _required_string(raw, "source")).resolve()
    return CorpusStudy(
        analysis_id=_required_string(raw, "analysis_id"),
        family=_required_string(raw, "family"),
        source_path=source_path,
        input_id=_required_string(raw, "input_id"),
        evidence_tier=EvidenceTier[_required_string(raw, "evidence_tier")],
        disposition=AnalysisDisposition(_required_string(raw, "disposition")),
        required_accesses=required_accesses,
    )


def _load_analysis(
    store: PolymarketCorpusStore,
    corpus_input: CorpusInput,
    *,
    session_id: str,
    behavioral_fill_workspace: Path | None = None,
) -> PolymarketDevelopmentAnalysis:
    snapshot = store.load(corpus_input.snapshot)
    if corpus_input.behavioral_fill_snapshot is not None:
        if behavioral_fill_workspace is None:
            raise ValueError("behavioral fill workspace is required by the catalog")
        fill_snapshot = BehavioralFillStore(behavioral_fill_workspace).load(
            corpus_input.behavioral_fill_snapshot
        )
        return build_behavioral_fill_analysis(
            snapshot,
            fill_snapshot,
            session_id=session_id,
            resource_limits=corpus_input.resource_limits,
        )
    if corpus_input.ancestor is None:
        return build_polymarket_development_analysis(
            snapshot,
            session_id=session_id,
            resource_limits=corpus_input.resource_limits,
        )
    ancestor = store.load(corpus_input.ancestor)
    return build_polymarket_replication_analysis(
        snapshot,
        ancestor,
        session_id=session_id,
        resource_limits=corpus_input.resource_limits,
    )


def _preflight_harnesses(
    store: PolymarketCorpusStore,
    catalog: CorpusCampaignCatalog,
    *,
    behavioral_fill_workspace: Path | None,
) -> dict[str, tuple[str, tuple[CampaignInputView, ...]]]:
    """Derive exact data-bearing harness identities before manifest publication."""
    bindings: dict[str, tuple[str, tuple[CampaignInputView, ...]]] = {}
    for corpus_input in catalog.inputs:
        analysis = _load_analysis(
            store,
            corpus_input,
            session_id=catalog.session_id,
            behavioral_fill_workspace=behavioral_fill_workspace,
        )
        if analysis.partition.partition_id != corpus_input.partition_id:
            raise ValueError("catalog partition identity differs from retained input bytes")
        views = (
            analysis.price_view,
            analysis.outcome_view,
            *analysis.registered_event_views,
        )
        bindings[corpus_input.input_id] = (
            analysis.harness.binding_identity,
            tuple(
                CampaignInputView(
                    view.view_id,
                    view.dataset_ref,
                    view.environment_ref,
                    frozenset(view.fields),
                )
                for view in views
            ),
        )
    return bindings


def _optional_behavioral_fill_ref(
    raw: Mapping[str, object],
) -> BehavioralFillSnapshotRef | None:
    digest = raw.get("behavioral_fill_snapshot_sha256")
    size = raw.get("behavioral_fill_snapshot_size")
    if (digest is None) != (size is None):
        raise ValueError("behavioral fill digest and size must be supplied together")
    if digest is None:
        return None
    if not isinstance(digest, str) or not isinstance(size, int):
        raise TypeError("behavioral fill digest and size have invalid types")
    return BehavioralFillSnapshotRef(digest, size)


def _list_of_mappings(raw: Mapping[str, object], key: str) -> tuple[Mapping[str, object], ...]:
    value = raw.get(key)
    if not isinstance(value, list) or not value:
        raise TypeError(f"{key} must be a non-empty list")
    items: list[Mapping[str, object]] = []
    for item in cast("list[object]", value):
        if not isinstance(item, dict):
            raise TypeError(f"{key} entries must be objects")
        items.append(cast("Mapping[str, object]", item))
    return tuple(items)


def _required_string(raw: Mapping[str, object], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise TypeError(f"{key} must be a non-empty string")
    return value


def _required_int(raw: Mapping[str, object], key: str) -> int:
    value = raw.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise TypeError(f"{key} must be a positive integer")
    return value


def _optional_int(raw: Mapping[str, object], key: str, default: int) -> int:
    value = raw.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise TypeError(f"{key} must be a positive integer")
    return value


def _optional_float(raw: Mapping[str, object], key: str, default: float) -> float:
    value = raw.get(key, default)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise TypeError(f"{key} must be a positive number")
    return float(value)


if __name__ == "__main__":
    raise SystemExit(main())
