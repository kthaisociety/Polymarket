"""Harness-owned execution and completion boundary for research campaigns."""

# ruff: noqa: EM101, EM102, TRY003

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass, replace
from enum import Enum, IntEnum
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, cast

from research_agent.data_foundation._identity import stable_identity
from research_agent.exploration.sandbox import AnalysisRequest, AnalysisStatus

_ACTUAL_ACCESS_COMPONENT_COUNT = 4
_DISPOSITION_COMPONENT_COUNT = 2

if TYPE_CHECKING:
    from collections.abc import Mapping

    from research_agent.exploration.sandbox import AnalysisHarness, DataAccessRequest, JsonValue


class EvidenceTier(IntEnum):
    """Maximum scientific meaning an exact campaign execution may carry."""

    BLOCKED_OR_NOT_TESTED = 0
    EXPOSED_REPRODUCTION = 1
    EXPLORATORY_DEVELOPMENT = 2
    FRESH_DEVELOPMENT_REPLICATION = 3
    PROTECTED_RESULT = 4
    EXECUTION_VALIDATED = 5


class AnalysisDisposition(Enum):
    """Campaign-level interpretation retained separately from execution success."""

    BLOCKED = "blocked"
    REJECTED = "rejected"
    RETAINED = "retained"
    EXECUTION_VALIDATED = "execution_validated"


@dataclass(frozen=True, slots=True)
class CampaignAnalysis:
    """One exact authored analysis and the capability facts it must actually consume."""

    analysis_id: str
    family: str
    source: str
    data_access: tuple[DataAccessRequest, ...]
    required_actual_accesses: tuple[tuple[str, str], ...]
    expected_dataset_refs: tuple[str, ...]
    expected_environment_refs: tuple[str, ...]
    expected_harness_binding_identity: str
    evidence_tier: EvidenceTier

    def __post_init__(self) -> None:
        """Reject ambiguous or vacuous campaign declarations."""
        if not self.analysis_id.strip() or not self.family.strip() or not self.source.strip():
            raise ValueError("campaign analysis identity, family, and source must be non-empty")
        if not self.data_access:
            raise ValueError("campaign analysis requires an exact data-access declaration")
        if not self.required_actual_accesses:
            raise ValueError("campaign analysis requires at least one observed field access")
        requested = {
            (access.view_id, field_id)
            for access in self.data_access
            for field_id in access.field_ids
        }
        if not set(self.required_actual_accesses) <= requested:
            raise ValueError("required actual accesses exceed the declared capability request")
        if len(set(self.required_actual_accesses)) != len(self.required_actual_accesses):
            raise ValueError("required actual accesses must be unique")
        if (
            not self.expected_dataset_refs
            or not self.expected_environment_refs
            or not self.expected_harness_binding_identity
        ):
            raise ValueError("campaign analysis requires exact input and environment identities")

    @property
    def source_sha256(self) -> str:
        """Return the exact authored-source identity."""
        return hashlib.sha256(self.source.encode()).hexdigest()

    @property
    def identity(self) -> str:
        """Return a stable identity over scientific meaning and execution requirements."""
        return stable_identity(
            "campaign-analysis",
            {
                "analysis_id": self.analysis_id,
                "family": self.family,
                "source_sha256": self.source_sha256,
                "data_access": tuple(
                    (access.view_id, access.field_ids) for access in self.data_access
                ),
                "required_actual_accesses": self.required_actual_accesses,
                "expected_dataset_refs": self.expected_dataset_refs,
                "expected_environment_refs": self.expected_environment_refs,
                "expected_harness_binding_identity": self.expected_harness_binding_identity,
                "evidence_tier": self.evidence_tier.name,
            },
        )


@dataclass(frozen=True, slots=True)
class CampaignManifest:
    """Complete, immutable inventory required before a campaign may execute."""

    campaign_id: str
    mandate: str
    analyses: tuple[CampaignAnalysis, ...]

    def __post_init__(self) -> None:
        """Reject duplicate names even when their authored bytes happen to match."""
        if not self.campaign_id.strip() or not self.mandate.strip() or not self.analyses:
            raise ValueError("campaign identity, mandate, and analyses must be non-empty")
        by_id: dict[str, CampaignAnalysis] = {}
        for analysis in self.analyses:
            existing = by_id.get(analysis.analysis_id)
            if existing is not None:
                raise ValueError("manifest analysis identity conflict")
            by_id[analysis.analysis_id] = analysis

    @property
    def identity(self) -> str:
        """Return a stable identity over the complete declared campaign."""
        return stable_identity(
            "research-campaign",
            {
                "campaign_id": self.campaign_id,
                "mandate": self.mandate,
                "analysis_ids": tuple(item.identity for item in self.analyses),
            },
        )


@dataclass(frozen=True, slots=True)
class CampaignExecutionReceipt:
    """Authority-issued facts from one exact `AnalysisHarness` invocation."""

    receipt_id: str
    campaign_identity: str
    analysis_identity: str
    analysis_id: str
    source_sha256: str
    harness_binding_identity: str
    harness_action_id: str
    harness_execution_status: str
    actual_accesses: tuple[tuple[str, str, str, str], ...]
    dataset_refs: tuple[str, ...]
    environment_refs: tuple[str, ...]
    summary: str
    details: JsonValue
    warnings: tuple[str, ...]
    artifacts: tuple[CampaignArtifact, ...]
    admissible: bool
    admission_errors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CampaignCompletionReceipt:
    """Execution closure without promotion, protection, or trading authority."""

    receipt_id: str
    campaign_identity: str
    execution_complete: bool
    dispositions: tuple[tuple[str, AnalysisDisposition], ...]
    receipt_ids: tuple[str, ...]
    maximum_evidence_tier: EvidenceTier
    execution_validated_strategy_count: int
    warnings: tuple[str, ...]


class CampaignCompletionError(ValueError):
    """A campaign attempted to close without its declared harness evidence."""


@dataclass(frozen=True, slots=True)
class CampaignArtifact:
    """One exact harness artifact durably retained by the campaign authority."""

    artifact_id: str
    kind: str
    size_bytes: int
    sha256: str
    object_ref: str


class CampaignStore:
    """Conflict-detecting durable store for one exact research campaign."""

    def __init__(self, root: Path) -> None:
        """Bind persistence to an explicit campaign-owned directory."""
        self.root = root

    def bind_manifest(self, manifest: CampaignManifest) -> None:
        """Publish the complete manifest exactly once or verify an exact replay."""
        _publish_immutable(self.root / "manifest.json", _manifest_bytes(manifest))

    def persist_artifact(
        self,
        *,
        artifact_id: str,
        kind: str,
        expected_size: int,
        expected_sha256: str,
        content: bytes,
    ) -> CampaignArtifact:
        """Retain and verify one externalized harness result by content identity."""
        digest = hashlib.sha256(content).hexdigest()
        if digest != expected_sha256 or len(content) != expected_size:
            raise ValueError("harness artifact bytes differ from their issued reference")
        relative = Path("artifacts") / digest[:2] / digest
        _publish_immutable(self.root / relative, content)
        return CampaignArtifact(
            artifact_id=artifact_id,
            kind=kind,
            size_bytes=expected_size,
            sha256=digest,
            object_ref=relative.as_posix(),
        )

    def persist_execution(self, receipt: CampaignExecutionReceipt) -> None:
        """Publish an authority-issued execution receipt exactly once."""
        _publish_immutable(self._execution_path(receipt.analysis_id), _execution_bytes(receipt))

    def load_execution(
        self,
        analysis: CampaignAnalysis,
        *,
        campaign_identity: str,
    ) -> CampaignExecutionReceipt | None:
        """Recover and validate an exact prior execution for one manifest item."""
        path = self._execution_path(analysis.analysis_id)
        if not path.exists():
            return None
        receipt = _execution_from_bytes(path.read_bytes())
        if (
            receipt.campaign_identity != campaign_identity
            or receipt.analysis_identity != analysis.identity
            or receipt.analysis_id != analysis.analysis_id
            or receipt.source_sha256 != analysis.source_sha256
            or receipt.harness_binding_identity != analysis.expected_harness_binding_identity
            or receipt.receipt_id != _execution_receipt_id(receipt)
        ):
            raise ValueError("persisted campaign execution conflicts with the manifest")
        for artifact in receipt.artifacts:
            content = (self.root / artifact.object_ref).read_bytes()
            if (
                len(content) != artifact.size_bytes
                or hashlib.sha256(content).hexdigest() != artifact.sha256
            ):
                raise ValueError("persisted campaign artifact failed identity verification")
        return receipt

    def persist_completion(self, receipt: CampaignCompletionReceipt) -> None:
        """Publish the terminal campaign receipt exactly once."""
        _publish_immutable(self.root / "completion.json", _completion_bytes(receipt))

    def load_completion(
        self,
        *,
        campaign_identity: str,
    ) -> CampaignCompletionReceipt | None:
        """Recover and validate the terminal campaign receipt when present."""
        path = self.root / "completion.json"
        if not path.exists():
            return None
        receipt = _completion_from_bytes(path.read_bytes())
        if (
            receipt.campaign_identity != campaign_identity
            or receipt.receipt_id != _completion_receipt_id(receipt)
        ):
            raise ValueError("persisted campaign completion failed identity verification")
        return receipt

    def _execution_path(self, analysis_id: str) -> Path:
        digest = hashlib.sha256(analysis_id.encode()).hexdigest()
        return self.root / "executions" / f"{digest}.json"


class ResearchCampaignAuthority:
    """Own campaign execution; external study receipts have no admission route."""

    def __init__(self, manifest: CampaignManifest, *, store: CampaignStore) -> None:
        """Bind one immutable manifest to an initially empty issued-receipt registry."""
        self.manifest = manifest
        self.store = store
        store.bind_manifest(manifest)
        self._analyses = MappingProxyType(
            {analysis.analysis_id: analysis for analysis in manifest.analyses}
        )
        self._receipts: dict[str, CampaignExecutionReceipt] = {
            analysis.analysis_id: receipt
            for analysis in manifest.analyses
            if (
                receipt := store.load_execution(
                    analysis,
                    campaign_identity=manifest.identity,
                )
            )
            is not None
        }
        self._completion = store.load_completion(campaign_identity=manifest.identity)

    def admit_external_receipt(self, receipt: object) -> None:
        """Reject legacy, manually assembled, or foreign evidence unconditionally."""
        del receipt
        raise TypeError("campaign accepts no external execution receipts")

    def execute(
        self,
        analysis_id: str,
        *,
        harness: AnalysisHarness,
        session_id: str,
    ) -> CampaignExecutionReceipt:
        """Execute one manifest-owned source through the supplied constrained harness."""
        if self._completion is not None:
            raise CampaignCompletionError("completed campaign cannot execute another analysis")
        analysis = self._analyses.get(analysis_id)
        if analysis is None:
            raise KeyError(analysis_id)
        existing = self._receipts.get(analysis_id)
        if existing is not None:
            return existing
        if harness.binding_identity != analysis.expected_harness_binding_identity:
            raise ValueError("analysis harness binding differs from the campaign manifest")
        action_id = stable_identity(
            "campaign-analysis-action",
            {
                "campaign_identity": self.manifest.identity,
                "analysis_identity": analysis.identity,
            },
        )
        observation = harness.run(
            AnalysisRequest(
                session_id=session_id,
                action_id=action_id,
                source=analysis.source,
                data_access=analysis.data_access,
            )
        )
        actual_accesses = tuple(
            (
                access.view_id,
                access.dataset_ref,
                access.environment_ref,
                access.field_id,
            )
            for access in observation.provenance.accesses
        )
        observed_pairs = {(item[0], item[3]) for item in actual_accesses}
        artifacts = tuple(
            self.store.persist_artifact(
                artifact_id=ref.artifact_id,
                kind=ref.kind.value,
                expected_size=ref.size_bytes,
                expected_sha256=ref.sha256,
                content=harness.artifacts.read(ref, session_id=session_id),
            )
            for ref in observation.artifact_refs
        )
        errors: list[str] = []
        if observation.status is not AnalysisStatus.SUCCEEDED:
            errors.append("harness execution did not succeed")
        if not set(analysis.required_actual_accesses) <= observed_pairs:
            errors.append("required actual accesses were not observed")
        if observation.provenance.dataset_refs != analysis.expected_dataset_refs:
            errors.append("observed dataset identities differ from the manifest")
        if observation.provenance.environment_refs != analysis.expected_environment_refs:
            errors.append("observed environment identities differ from the manifest")
        if observation.provenance.code_sha256 != analysis.source_sha256:
            errors.append("harness source identity differs from the manifest")
        receipt = CampaignExecutionReceipt(
            receipt_id="",
            campaign_identity=self.manifest.identity,
            analysis_identity=analysis.identity,
            analysis_id=analysis.analysis_id,
            source_sha256=analysis.source_sha256,
            harness_binding_identity=harness.binding_identity,
            harness_action_id=action_id,
            harness_execution_status=observation.status.value,
            actual_accesses=actual_accesses,
            dataset_refs=observation.provenance.dataset_refs,
            environment_refs=observation.provenance.environment_refs,
            summary=observation.summary,
            details=observation.details,
            warnings=observation.warnings,
            artifacts=artifacts,
            admissible=not errors,
            admission_errors=tuple(errors),
        )
        receipt = replace(receipt, receipt_id=_execution_receipt_id(receipt))
        self.store.persist_execution(receipt)
        self._receipts[analysis_id] = receipt
        return receipt

    def complete(
        self,
        dispositions: Mapping[str, AnalysisDisposition],
    ) -> CampaignCompletionReceipt:
        """Close only an exact, fully executed inventory within its evidence ceilings."""
        if self._completion is not None:
            return self._completion
        expected_ids = tuple(self._analyses)
        for analysis_id in expected_ids:
            receipt = self._receipts.get(analysis_id)
            if receipt is None:
                raise CampaignCompletionError(f"missing harness execution for {analysis_id}")
            if receipt.harness_execution_status != AnalysisStatus.SUCCEEDED.value:
                raise CampaignCompletionError(
                    f"harness execution did not succeed for {analysis_id}"
                )
            if not receipt.admissible:
                detail = "; ".join(receipt.admission_errors)
                raise CampaignCompletionError(f"{analysis_id}: {detail}")
            if analysis_id not in dispositions:
                raise CampaignCompletionError(f"missing disposition for {analysis_id}")
        extra = set(dispositions) - set(expected_ids)
        if extra:
            raise CampaignCompletionError("disposition supplied for undeclared analysis")
        ordered_dispositions = tuple((item, dispositions[item]) for item in expected_ids)
        for analysis_id, disposition in ordered_dispositions:
            analysis = self._analyses[analysis_id]
            if (
                disposition is AnalysisDisposition.EXECUTION_VALIDATED
                and analysis.evidence_tier < EvidenceTier.EXECUTION_VALIDATED
            ):
                raise CampaignCompletionError(
                    f"{analysis_id} disposition exceeds the manifest evidence tier"
                )
        maximum_tier = max(item.evidence_tier for item in self.manifest.analyses)
        receipt_ids = tuple(self._receipts[item].receipt_id for item in expected_ids)
        execution_validated = sum(
            disposition is AnalysisDisposition.EXECUTION_VALIDATED
            for _, disposition in ordered_dispositions
        )
        warnings = (
            "campaign completion proves exact harness execution, not protected validation",
            "rerunning an exposed corpus does not restore fresh evidence",
        )
        self._completion = CampaignCompletionReceipt(
            receipt_id="",
            campaign_identity=self.manifest.identity,
            execution_complete=True,
            dispositions=ordered_dispositions,
            receipt_ids=receipt_ids,
            maximum_evidence_tier=maximum_tier,
            execution_validated_strategy_count=execution_validated,
            warnings=warnings,
        )
        self._completion = replace(
            self._completion,
            receipt_id=_completion_receipt_id(self._completion),
        )
        self.store.persist_completion(self._completion)
        return self._completion


def _manifest_bytes(manifest: CampaignManifest) -> bytes:
    payload = {
        "campaign_id": manifest.campaign_id,
        "mandate": manifest.mandate,
        "campaign_identity": manifest.identity,
        "analyses": [
            {
                "analysis_id": item.analysis_id,
                "analysis_identity": item.identity,
                "family": item.family,
                "source": item.source,
                "source_sha256": item.source_sha256,
                "data_access": [
                    {"view_id": access.view_id, "field_ids": list(access.field_ids)}
                    for access in item.data_access
                ],
                "required_actual_accesses": [
                    list(access) for access in item.required_actual_accesses
                ],
                "expected_dataset_refs": list(item.expected_dataset_refs),
                "expected_environment_refs": list(item.expected_environment_refs),
                "expected_harness_binding_identity": item.expected_harness_binding_identity,
                "evidence_tier": item.evidence_tier.name,
            }
            for item in manifest.analyses
        ],
    }
    return _json_bytes(payload)


def _artifact_payload(artifact: CampaignArtifact) -> dict[str, object]:
    return {
        "artifact_id": artifact.artifact_id,
        "kind": artifact.kind,
        "size_bytes": artifact.size_bytes,
        "sha256": artifact.sha256,
        "object_ref": artifact.object_ref,
    }


def _execution_payload(receipt: CampaignExecutionReceipt) -> dict[str, object]:
    return {
        "receipt_id": receipt.receipt_id,
        "campaign_identity": receipt.campaign_identity,
        "analysis_identity": receipt.analysis_identity,
        "analysis_id": receipt.analysis_id,
        "source_sha256": receipt.source_sha256,
        "harness_binding_identity": receipt.harness_binding_identity,
        "harness_action_id": receipt.harness_action_id,
        "harness_execution_status": receipt.harness_execution_status,
        "actual_accesses": [list(item) for item in receipt.actual_accesses],
        "dataset_refs": list(receipt.dataset_refs),
        "environment_refs": list(receipt.environment_refs),
        "summary": receipt.summary,
        "details": receipt.details,
        "warnings": list(receipt.warnings),
        "artifacts": [_artifact_payload(item) for item in receipt.artifacts],
        "admissible": receipt.admissible,
        "admission_errors": list(receipt.admission_errors),
    }


def _execution_identity_payload(receipt: CampaignExecutionReceipt) -> dict[str, object]:
    payload = _execution_payload(receipt)
    del payload["receipt_id"]
    return payload


def _execution_receipt_id(receipt: CampaignExecutionReceipt) -> str:
    return stable_identity("campaign-execution-receipt", _execution_identity_payload(receipt))


def _execution_bytes(receipt: CampaignExecutionReceipt) -> bytes:
    return _json_bytes(_execution_payload(receipt))


def _json_object(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"{label} must be a JSON object")
    mapping = cast("dict[object, object]", value)
    if not all(isinstance(key, str) for key in mapping):
        raise TypeError(f"{label} must use string keys")
    return cast("Mapping[str, object]", mapping)


def _json_array(value: object, *, label: str) -> tuple[object, ...]:
    if not isinstance(value, list):
        raise TypeError(f"{label} must be a JSON array")
    return tuple(cast("list[object]", value))


def _actual_access_from_json(value: object) -> tuple[str, str, str, str]:
    items = _json_array(value, label="actual access")
    if len(items) != _ACTUAL_ACCESS_COMPONENT_COUNT:
        raise TypeError("actual access must contain exactly four values")
    return (str(items[0]), str(items[1]), str(items[2]), str(items[3]))


def _json_int(value: object, *, label: str) -> int:
    if not isinstance(value, (str, int, float)):
        raise TypeError(f"{label} must be numeric")
    return int(value)


def _artifact_from_json(value: object) -> CampaignArtifact:
    item = _json_object(value, label="campaign artifact")
    return CampaignArtifact(
        artifact_id=str(item["artifact_id"]),
        kind=str(item["kind"]),
        size_bytes=_json_int(item["size_bytes"], label="artifact size"),
        sha256=str(item["sha256"]),
        object_ref=str(item["object_ref"]),
    )


def _execution_from_bytes(content: bytes) -> CampaignExecutionReceipt:
    raw = _json_object(
        cast("object", json.loads(content)),
        label="campaign execution receipt",
    )
    return CampaignExecutionReceipt(
        receipt_id=str(raw["receipt_id"]),
        campaign_identity=str(raw["campaign_identity"]),
        analysis_identity=str(raw["analysis_identity"]),
        analysis_id=str(raw["analysis_id"]),
        source_sha256=str(raw["source_sha256"]),
        harness_binding_identity=str(raw["harness_binding_identity"]),
        harness_action_id=str(raw["harness_action_id"]),
        harness_execution_status=str(raw["harness_execution_status"]),
        actual_accesses=tuple(
            _actual_access_from_json(item)
            for item in _json_array(raw["actual_accesses"], label="actual accesses")
        ),
        dataset_refs=tuple(
            str(value) for value in _json_array(raw["dataset_refs"], label="dataset references")
        ),
        environment_refs=tuple(
            str(value)
            for value in _json_array(raw["environment_refs"], label="environment references")
        ),
        summary=str(raw["summary"]),
        details=cast("JsonValue", raw["details"]),
        warnings=tuple(str(value) for value in _json_array(raw["warnings"], label="warnings")),
        artifacts=tuple(
            _artifact_from_json(item) for item in _json_array(raw["artifacts"], label="artifacts")
        ),
        admissible=bool(raw["admissible"]),
        admission_errors=tuple(
            str(value) for value in _json_array(raw["admission_errors"], label="admission errors")
        ),
    )


def _completion_payload(receipt: CampaignCompletionReceipt) -> dict[str, object]:
    return {
        "receipt_id": receipt.receipt_id,
        "campaign_identity": receipt.campaign_identity,
        "execution_complete": receipt.execution_complete,
        "dispositions": [[key, value.value] for key, value in receipt.dispositions],
        "receipt_ids": list(receipt.receipt_ids),
        "maximum_evidence_tier": receipt.maximum_evidence_tier.name,
        "execution_validated_strategy_count": receipt.execution_validated_strategy_count,
        "warnings": list(receipt.warnings),
    }


def _completion_identity_payload(receipt: CampaignCompletionReceipt) -> dict[str, object]:
    payload = _completion_payload(receipt)
    del payload["receipt_id"]
    return payload


def _completion_receipt_id(receipt: CampaignCompletionReceipt) -> str:
    return stable_identity("campaign-completion-receipt", _completion_identity_payload(receipt))


def _completion_bytes(receipt: CampaignCompletionReceipt) -> bytes:
    return _json_bytes(_completion_payload(receipt))


def _disposition_from_json(value: object) -> tuple[str, AnalysisDisposition]:
    items = _json_array(value, label="campaign disposition")
    if len(items) != _DISPOSITION_COMPONENT_COUNT:
        raise TypeError("campaign disposition must contain exactly two values")
    return str(items[0]), AnalysisDisposition(str(items[1]))


def _completion_from_bytes(content: bytes) -> CampaignCompletionReceipt:
    raw = _json_object(
        cast("object", json.loads(content)),
        label="campaign completion receipt",
    )
    return CampaignCompletionReceipt(
        receipt_id=str(raw["receipt_id"]),
        campaign_identity=str(raw["campaign_identity"]),
        execution_complete=bool(raw["execution_complete"]),
        dispositions=tuple(
            _disposition_from_json(item)
            for item in _json_array(raw["dispositions"], label="dispositions")
        ),
        receipt_ids=tuple(
            str(value) for value in _json_array(raw["receipt_ids"], label="receipt identities")
        ),
        maximum_evidence_tier=EvidenceTier[str(raw["maximum_evidence_tier"])],
        execution_validated_strategy_count=_json_int(
            raw["execution_validated_strategy_count"],
            label="execution-validated strategy count",
        ),
        warnings=tuple(str(value) for value in _json_array(raw["warnings"], label="warnings")),
    )


def _json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode()


def _publish_immutable(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != content:
                raise ValueError(
                    "immutable campaign content conflicts with existing bytes"
                ) from None
        directory_descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        temporary.unlink(missing_ok=True)


__all__ = [
    "AnalysisDisposition",
    "CampaignAnalysis",
    "CampaignArtifact",
    "CampaignCompletionError",
    "CampaignCompletionReceipt",
    "CampaignExecutionReceipt",
    "CampaignManifest",
    "CampaignStore",
    "EvidenceTier",
    "ResearchCampaignAuthority",
]
