"""Receipt-backed publication audit without scientific promotion authority."""

# ruff: noqa: D105, D107, EM101, EM102, PLR0913, TRY003

from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Final, cast

from research_agent.data_foundation._identity import stable_identity
from research_agent.exploration.campaign import EvidenceTier

if TYPE_CHECKING:
    from collections.abc import Iterable

_SHA256_HEX_LENGTH: Final[int] = 64
_MINIMUM_BOOTSTRAP_UNITS: Final[int] = 2
_MINIMUM_BOOTSTRAP_REPETITIONS: Final[int] = 1000
_MINIMUM_CONFIDENCE_LEVEL: Final[float] = 0.95
_PAIR_LENGTH: Final[int] = 2
_RESERVED_TRADING_TERMS: Final[tuple[str, ...]] = (
    "executable",
    "profit",
    "profitable",
    "tradable",
    "trading strategy",
)
_RESERVED_CAUSAL_TERMS: Final[tuple[str, ...]] = ("causal", "causes", "caused")


class PaperAuditError(ValueError):
    """Paper inputs or retained evidence failed exact verification."""


class PaperDecision(Enum):
    """Publication decision; it is not scientific promotion."""

    ACCEPT = "accept"
    REJECT = "reject"


class ClaimKind(Enum):
    """Fixed claim classes with non-configurable evidentiary requirements."""

    AUDIT_FACT = "audit_fact"
    EVIDENCE_BOUNDARY = "evidence_boundary"
    DEVELOPMENT_RESULT = "development_result"
    PROCESS_GENERALIZATION = "process_generalization"
    PREDICTIVE_REPLICATION = "predictive_replication"
    CAUSAL_MECHANISM = "causal_mechanism"
    TRADING_STRATEGY = "trading_strategy"


class EvidenceUnit(Enum):
    """Independent unit used by uncertainty and hypothesis tests."""

    ROW = "row"
    MARKET = "market"
    EVENT = "event"
    WALLET_EVENT = "wallet_event"


_DEPENDENCE_AWARE_UNITS: Final[frozenset[EvidenceUnit]] = frozenset(
    (EvidenceUnit.EVENT, EvidenceUnit.WALLET_EVENT)
)


class EffectDirection(Enum):
    """Predeclared direction of an effect relative to its null value."""

    ABOVE = "above"
    BELOW = "below"
    DIFFERENT = "different"


class AlternativeHypothesis(Enum):
    """Alternative for an exact binomial event-level test."""

    GREATER = "greater"
    LESS = "less"
    TWO_SIDED = "two_sided"


class ExecutionDataKind(Enum):
    """Strongest market observation used by an asserted strategy result."""

    SAMPLED_MARKS = "sampled_marks"
    HISTORICAL_QUOTES = "historical_quotes"
    ORDER_BOOK = "order_book"
    RECORDED_FILLS = "recorded_fills"


class ValueFormat(Enum):
    """Fixed rendering used to bind a manuscript value to receipt data."""

    RAW = "raw"
    INTEGER = "integer"
    PERCENT_2 = "percent_2"
    DECIMAL_4 = "decimal_4"


@dataclass(frozen=True, slots=True)
class CampaignReference:
    """Exact on-disk campaign bundle admitted to a paper protocol."""

    reference_id: str
    directory_ref: str
    manifest_sha256: str
    completion_sha256: str

    def __post_init__(self) -> None:
        if not self.reference_id.strip() or not self.directory_ref.strip():
            raise PaperAuditError("campaign reference identity and directory must be non-empty")
        if (
            len(self.manifest_sha256) != _SHA256_HEX_LENGTH
            or len(self.completion_sha256) != _SHA256_HEX_LENGTH
        ):
            raise PaperAuditError("campaign references require exact SHA-256 identities")


@dataclass(frozen=True, slots=True)
class EvidenceLocator:
    """Unambiguous reference to one analysis in one retained campaign."""

    campaign_reference_id: str
    analysis_id: str

    def __post_init__(self) -> None:
        if not self.campaign_reference_id.strip() or not self.analysis_id.strip():
            raise PaperAuditError("evidence locator fields must be non-empty")


@dataclass(frozen=True, slots=True)
class EffectInterval:
    """Dependence-aware uncertainty interval bound to exact evidence."""

    interval_id: str
    evidence: EvidenceLocator
    unit: EvidenceUnit
    method: str
    confidence_level: float
    estimate: float
    lower: float
    upper: float
    null_value: float
    direction: EffectDirection
    repetitions: int

    def __post_init__(self) -> None:
        if not self.interval_id.strip() or not self.method.strip():
            raise PaperAuditError("interval identity and method must be non-empty")
        if not 0.0 < self.confidence_level < 1.0:
            raise PaperAuditError("interval confidence level must be between zero and one")
        if self.lower > self.estimate or self.estimate > self.upper:
            raise PaperAuditError("interval bounds must contain the estimate")
        if self.repetitions < 0:
            raise PaperAuditError("interval repetitions cannot be negative")


@dataclass(frozen=True, slots=True)
class HypothesisTest:
    """Exact event-level binomial test registered in a search family."""

    test_id: str
    evidence: EvidenceLocator
    family_id: str
    unit: EvidenceUnit
    successes: int
    trials: int
    null_probability: float
    alternative: AlternativeHypothesis

    def __post_init__(self) -> None:
        if not self.test_id.strip() or not self.family_id.strip():
            raise PaperAuditError("test and family identities must be non-empty")
        if self.trials < 1 or not 0 <= self.successes <= self.trials:
            raise PaperAuditError("binomial counts are invalid")
        if not 0.0 < self.null_probability < 1.0:
            raise PaperAuditError("binomial null probability must be between zero and one")


@dataclass(frozen=True, slots=True)
class HypothesisFamily:
    """Multiplicity family including the evidence searched to select a result."""

    family_id: str
    test_ids: tuple[str, ...]
    search_evidence: tuple[EvidenceLocator, ...]
    complete_test_inventory: bool

    def __post_init__(self) -> None:
        if not self.family_id.strip() or not self.test_ids or not self.search_evidence:
            raise PaperAuditError("hypothesis family must name tests and searched evidence")
        if len(set(self.test_ids)) != len(self.test_ids):
            raise PaperAuditError("hypothesis family test identities must be unique")
        if len(set(self.search_evidence)) != len(self.search_evidence):
            raise PaperAuditError("hypothesis family search evidence must be unique")


@dataclass(frozen=True, slots=True)
class ExecutionEvidence:
    """Observed execution inputs required before a paper may assert tradability."""

    data_kind: ExecutionDataKind
    observed_spreads: bool
    observed_fees: bool
    modeled_latency: bool
    modeled_queue_position: bool
    modeled_partial_fills: bool


@dataclass(frozen=True, slots=True)
class EvidenceAssertion:
    """Exact receipt value that must also appear in the declared claim wording."""

    evidence: EvidenceLocator
    details_path: tuple[str | int, ...]
    expected_value: str | int | float | bool
    value_format: ValueFormat

    def __post_init__(self) -> None:
        if not self.details_path or any(
            (isinstance(item, str) and not item.strip()) or (isinstance(item, int) and item < 0)
            for item in self.details_path
        ):
            raise PaperAuditError("evidence assertion requires a non-empty details path")


@dataclass(frozen=True, slots=True)
class ClaimDeclaration:
    """Exact paper claim and all evidence used to support it."""

    claim_id: str
    statement: str
    kind: ClaimKind
    evidence: tuple[EvidenceLocator, ...]
    assertions: tuple[EvidenceAssertion, ...]
    interval_id: str | None
    test_id: str | None
    falsification_refs: tuple[EvidenceLocator, ...]
    stability_refs: tuple[EvidenceLocator, ...]
    frozen_before_evaluation: bool
    causal_design_ref: str | None
    execution_evidence: ExecutionEvidence | None
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.claim_id.strip() or not self.statement.strip() or not self.evidence:
            raise PaperAuditError("claim identity, statement, and evidence must be non-empty")
        if len(set(self.evidence)) != len(self.evidence):
            raise PaperAuditError("claim evidence references must be unique")
        if any(assertion.evidence not in self.evidence for assertion in self.assertions):
            raise PaperAuditError("claim assertion must reference the claim's evidence")
        if any(
            reference not in self.evidence
            for reference in (*self.falsification_refs, *self.stability_refs)
        ):
            raise PaperAuditError("robustness references must be part of claim evidence")


@dataclass(frozen=True, slots=True)
class PaperProtocol:
    """Content-addressed paper claims and predeclared statistical audit."""

    protocol_id: str
    title: str
    campaigns: tuple[CampaignReference, ...]
    claims: tuple[ClaimDeclaration, ...]
    intervals: tuple[EffectInterval, ...]
    tests: tuple[HypothesisTest, ...]
    families: tuple[HypothesisFamily, ...]
    alpha: float

    def __post_init__(self) -> None:
        if self.protocol_id != stable_identity("paper-protocol", _protocol_body(self)):
            raise PaperAuditError("paper protocol identity does not match content")
        if not self.title.strip() or not self.campaigns or not self.claims:
            raise PaperAuditError("paper protocol title, campaigns, and claims are required")
        if not 0.0 < self.alpha < 1.0:
            raise PaperAuditError("paper alpha must be between zero and one")
        _require_unique((item.reference_id for item in self.campaigns), "campaign reference")
        _require_unique((item.claim_id for item in self.claims), "claim")
        _require_unique((item.interval_id for item in self.intervals), "interval")
        _require_unique((item.test_id for item in self.tests), "test")
        _require_unique((item.family_id for item in self.families), "family")

    @classmethod
    def create(
        cls,
        *,
        title: str,
        campaigns: tuple[CampaignReference, ...],
        claims: tuple[ClaimDeclaration, ...],
        intervals: tuple[EffectInterval, ...],
        tests: tuple[HypothesisTest, ...],
        families: tuple[HypothesisFamily, ...],
        alpha: float,
    ) -> PaperProtocol:
        """Create an exact protocol identity from every consequential declaration."""
        fields = {
            "title": title,
            "campaigns": campaigns,
            "claims": claims,
            "intervals": intervals,
            "tests": tests,
            "families": families,
            "alpha": alpha,
        }
        return cls(
            protocol_id=stable_identity("paper-protocol", fields),
            title=title,
            campaigns=campaigns,
            claims=claims,
            intervals=intervals,
            tests=tests,
            families=families,
            alpha=alpha,
        )

    def as_dict(self) -> dict[str, object]:
        """Return a fresh JSON-safe representation of the exact protocol."""
        return cast("dict[str, object]", _json_safe(asdict(self)))

    def to_json(self) -> str:
        """Serialize the protocol deterministically for immutable storage."""
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class CampaignAudit:
    """Verified identities and counts for one complete retained campaign."""

    reference_id: str
    campaign_identity: str
    campaign_id: str
    manifest_sha256: str
    completion_sha256: str
    execution_count: int
    legacy_unbound_execution_count: int
    execution_validated_strategy_count: int


@dataclass(frozen=True, slots=True)
class TrialRecord:
    """One exact campaign execution retained in the publication inventory."""

    campaign_reference_id: str
    campaign_identity: str
    analysis_id: str
    analysis_identity: str
    family: str
    source_sha256: str
    harness_binding_identity: str | None
    manifest_harness_binding_identity: str | None
    evidence_tier: EvidenceTier
    disposition: str
    execution_receipt_id: str
    execution_receipt_ref: str
    execution_receipt_sha256: str
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AdjustedTestResult:
    """Exact raw and search-adjusted result for one registered test."""

    test_id: str
    family_id: str
    unit: EvidenceUnit
    raw_p_value: float
    adjusted_p_value: float
    adjustment_method: str
    search_count: int
    passed: bool


@dataclass(frozen=True, slots=True)
class ClaimCheck:
    """One deterministic pass/fail proposition about a declared claim."""

    code: str
    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class ClaimAudit:
    """Complete requirement audit for one exact declared claim."""

    claim_id: str
    statement: str
    kind: ClaimKind
    passed: bool
    checks: tuple[ClaimCheck, ...]
    evidence_receipt_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PaperAuditReport:
    """Immutable machine-readable publication decision and evidence inventory."""

    report_id: str
    schema_version: int
    protocol_id: str
    title: str
    decision: PaperDecision
    campaigns: tuple[CampaignAudit, ...]
    trials: tuple[TrialRecord, ...]
    unique_analysis_count: int
    duplicate_execution_count: int
    tests: tuple[AdjustedTestResult, ...]
    claims: tuple[ClaimAudit, ...]
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise PaperAuditError("unsupported paper audit schema")
        if self.report_id != stable_identity("paper-audit-report", _report_body(self)):
            raise PaperAuditError("paper audit report identity does not match content")

    def as_dict(self) -> dict[str, object]:
        """Return a fresh JSON-safe representation of the exact report."""
        return cast("dict[str, object]", _json_safe(asdict(self)))

    def to_json(self) -> str:
        """Serialize the report deterministically for immutable storage."""
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"))


class PaperAuditor:
    """Verify retained evidence and enforce fixed requirements by claim kind."""

    _root: Final[Path]

    def __init__(self, *, root: Path) -> None:
        self._root = root.resolve()

    def audit(self, protocol: PaperProtocol) -> PaperAuditReport:
        """Return a deterministic publication decision without changing evidence status."""
        campaign_audits: list[CampaignAudit] = []
        trial_records: list[TrialRecord] = []
        details_by_locator: dict[EvidenceLocator, object] = {}
        for reference in protocol.campaigns:
            campaign, trials, details_by_analysis = self._audit_campaign(reference)
            campaign_audits.append(campaign)
            trial_records.extend(trials)
            details_by_locator.update(
                {
                    EvidenceLocator(reference.reference_id, analysis_id): details
                    for analysis_id, details in details_by_analysis.items()
                }
            )
        trial_by_locator = {
            EvidenceLocator(trial.campaign_reference_id, trial.analysis_id): trial
            for trial in trial_records
        }
        if len(trial_by_locator) != len(trial_records):
            raise PaperAuditError("campaign references created ambiguous evidence locators")
        self._verify_protocol_references(protocol, trial_by_locator)
        adjusted_tests = _adjust_tests(protocol)
        test_by_id = {item.test_id: item for item in adjusted_tests}
        interval_by_id = {item.interval_id: item for item in protocol.intervals}
        claim_audits = tuple(
            _audit_claim(
                claim,
                trial_by_locator=trial_by_locator,
                details_by_locator=details_by_locator,
                interval_by_id=interval_by_id,
                test_by_id=test_by_id,
            )
            for claim in protocol.claims
        )
        unique_analysis_count = len({trial.analysis_id for trial in trial_records})
        fields = {
            "schema_version": 1,
            "protocol_id": protocol.protocol_id,
            "title": protocol.title,
            "decision": (
                PaperDecision.ACCEPT
                if all(claim.passed for claim in claim_audits)
                else PaperDecision.REJECT
            ),
            "campaigns": tuple(campaign_audits),
            "trials": tuple(trial_records),
            "unique_analysis_count": unique_analysis_count,
            "duplicate_execution_count": len(trial_records) - unique_analysis_count,
            "tests": adjusted_tests,
            "claims": claim_audits,
            "warnings": (
                "publication acceptance is not scientific promotion",
                "exposed evidence remains exposed after exact reproduction",
                "a passing non-trading paper does not establish executable profitability",
            ),
        }
        return PaperAuditReport(
            report_id=stable_identity("paper-audit-report", fields),
            schema_version=1,
            protocol_id=protocol.protocol_id,
            title=protocol.title,
            decision=cast("PaperDecision", fields["decision"]),
            campaigns=tuple(campaign_audits),
            trials=tuple(trial_records),
            unique_analysis_count=unique_analysis_count,
            duplicate_execution_count=len(trial_records) - unique_analysis_count,
            tests=adjusted_tests,
            claims=claim_audits,
            warnings=cast("tuple[str, ...]", fields["warnings"]),
        )

    def _audit_campaign(
        self, reference: CampaignReference
    ) -> tuple[CampaignAudit, tuple[TrialRecord, ...], dict[str, object]]:
        directory = self._resolve_relative(reference.directory_ref)
        manifest_bytes = (directory / "manifest.json").read_bytes()
        completion_bytes = (directory / "completion.json").read_bytes()
        _require_sha256(manifest_bytes, reference.manifest_sha256, "campaign manifest")
        _require_sha256(completion_bytes, reference.completion_sha256, "campaign completion")
        manifest = _json_object(manifest_bytes, "campaign manifest")
        completion = _json_object(completion_bytes, "campaign completion")
        analyses = _verify_manifest(manifest)
        campaign_identity = _string(manifest, "campaign_identity")
        _verify_completion(completion, campaign_identity, analyses)
        dispositions = {
            _list_string_pair(item, "campaign disposition")[0]: _list_string_pair(
                item, "campaign disposition"
            )[1]
            for item in _list(completion, "dispositions")
        }
        completion_receipt_ids = tuple(_strings(completion, "receipt_ids"))
        trials: list[TrialRecord] = []
        details_by_analysis: dict[str, object] = {}
        for index, analysis in enumerate(analyses):
            analysis_id = _string(analysis, "analysis_id")
            execution_name = hashlib.sha256(analysis_id.encode()).hexdigest()
            execution_path = directory / "executions" / f"{execution_name}.json"
            execution_bytes = execution_path.read_bytes()
            execution = _json_object(execution_bytes, "campaign execution")
            _verify_execution(execution, analysis, campaign_identity)
            receipt_id = _string(execution, "receipt_id")
            if completion_receipt_ids[index] != receipt_id:
                raise PaperAuditError("campaign completion execution order is inconsistent")
            trials.append(
                TrialRecord(
                    campaign_reference_id=reference.reference_id,
                    campaign_identity=campaign_identity,
                    analysis_id=analysis_id,
                    analysis_identity=_string(analysis, "analysis_identity"),
                    family=_string(analysis, "family"),
                    source_sha256=_string(analysis, "source_sha256"),
                    harness_binding_identity=_optional_string(
                        execution, "harness_binding_identity"
                    ),
                    manifest_harness_binding_identity=_optional_string(
                        analysis, "expected_harness_binding_identity"
                    ),
                    evidence_tier=EvidenceTier[_string(analysis, "evidence_tier")],
                    disposition=dispositions[analysis_id],
                    execution_receipt_id=receipt_id,
                    execution_receipt_ref=execution_path.relative_to(self._root).as_posix(),
                    execution_receipt_sha256=hashlib.sha256(execution_bytes).hexdigest(),
                    warnings=tuple(_strings(execution, "warnings")),
                )
            )
            details_by_analysis[analysis_id] = execution.get("details")
        campaign = CampaignAudit(
            reference_id=reference.reference_id,
            campaign_identity=campaign_identity,
            campaign_id=_string(manifest, "campaign_id"),
            manifest_sha256=reference.manifest_sha256,
            completion_sha256=reference.completion_sha256,
            execution_count=len(trials),
            legacy_unbound_execution_count=sum(
                trial.manifest_harness_binding_identity is None for trial in trials
            ),
            execution_validated_strategy_count=_integer(
                completion, "execution_validated_strategy_count"
            ),
        )
        return campaign, tuple(trials), details_by_analysis

    def _resolve_relative(self, reference: str) -> Path:
        relative = Path(reference)
        if relative.is_absolute():
            raise PaperAuditError("paper evidence references must be relative to the audit root")
        resolved = (self._root / relative).resolve()
        if resolved != self._root and self._root not in resolved.parents:
            raise PaperAuditError("paper evidence reference escaped the audit root")
        return resolved

    @staticmethod
    def _verify_protocol_references(
        protocol: PaperProtocol,
        trial_by_locator: dict[EvidenceLocator, TrialRecord],
    ) -> None:
        for claim in protocol.claims:
            _require_locators(claim.evidence, trial_by_locator)
        for interval in protocol.intervals:
            _require_locators((interval.evidence,), trial_by_locator)
        for test in protocol.tests:
            _require_locators((test.evidence,), trial_by_locator)
        _verify_families(protocol, trial_by_locator)


def bootstrap_mean_interval(
    values: tuple[float, ...], *, repetitions: int, seed: int
) -> tuple[float, float]:
    """Return a deterministic percentile interval by resampling whole supplied units."""
    if len(values) < _MINIMUM_BOOTSTRAP_UNITS:
        raise PaperAuditError("bootstrap requires at least two independent units")
    if repetitions < _MINIMUM_BOOTSTRAP_REPETITIONS:
        raise PaperAuditError("paper bootstrap requires at least 1000 repetitions")
    generator = random.Random(seed)  # noqa: S311 - deterministic scientific resampling
    sample_count = len(values)
    means = [
        (sum(values[generator.randrange(sample_count)] for _ in range(sample_count)) / sample_count)
        for _ in range(repetitions)
    ]
    means.sort()
    lower_index = int((repetitions - 1) * 0.025)
    upper_index = int((repetitions - 1) * 0.975)
    return means[lower_index], means[upper_index]


def render_concise_paper(report: PaperAuditReport) -> str:
    """Render only accepted, machine-audited claims and their explicit limitations."""
    lines = [
        f"# {report.title}",
        "",
        f"Publication gate: **{report.decision.value.upper()}**.",
        "",
        "## Evidence design",
        "",
        (
            f"The audit verified {len(report.trials)} governed executions representing "
            f"{report.unique_analysis_count} unique analysis identifiers. "
            f"{report.duplicate_execution_count} executions were exact or revised reruns retained "
            "as trial history."
        ),
        "",
        "## Statistical controls",
        "",
        "| Test | Unit | Raw p | Adjusted p | Search correction | Result |",
        "|---|---|---:|---:|---|---|",
        *(
            (
                f"| {test.test_id} | {test.unit.value} | {test.raw_p_value:.6g} | "
                f"{test.adjusted_p_value:.6g} | {test.adjustment_method} "
                f"(n={test.search_count}) | {'PASS' if test.passed else 'FAIL'} |"
            )
            for test in report.tests
        ),
        "",
        "## Audited claims",
        "",
    ]
    for claim in report.claims:
        label = "SUPPORTED" if claim.passed else "WITHHELD"
        lines.extend((f"### {claim.claim_id} — {label}", "", claim.statement, ""))
        if claim.limitations:
            lines.extend(("Scope:", "", *(f"- {item}" for item in claim.limitations), ""))
        failed = tuple(check.detail for check in claim.checks if not check.passed)
        if failed:
            lines.extend(("Why withheld:", "", *(f"- {item}" for item in failed), ""))
    lines.extend(
        (
            "## Status boundary",
            "",
            (
                "Publication acceptance checks wording against retained evidence. It is not "
                "scientific promotion, protected confirmation, or authorization to trade."
            ),
            "",
            f"Machine audit: `{report.report_id}`.",
            "",
        )
    )
    return "\n".join(lines)


def verify_paper_audit_json(serialized: str) -> str:
    """Verify the content identity of a serialized paper-audit receipt."""
    try:
        decoded: object = json.loads(serialized)
    except json.JSONDecodeError as error:
        raise PaperAuditError("paper audit receipt is not valid JSON") from error
    raw = _as_object(decoded, "paper audit receipt")
    if set(raw) != {
        "report_id",
        "schema_version",
        "protocol_id",
        "title",
        "decision",
        "campaigns",
        "trials",
        "unique_analysis_count",
        "duplicate_execution_count",
        "tests",
        "claims",
        "warnings",
    }:
        raise PaperAuditError("paper audit receipt has unexpected fields")
    report_id = _string(raw, "report_id")
    body = dict(raw)
    del body["report_id"]
    if stable_identity("paper-audit-report", body) != report_id:
        raise PaperAuditError("paper audit receipt identity is invalid")
    return report_id


def _audit_claim(
    claim: ClaimDeclaration,
    *,
    trial_by_locator: dict[EvidenceLocator, TrialRecord],
    details_by_locator: dict[EvidenceLocator, object],
    interval_by_id: dict[str, EffectInterval],
    test_by_id: dict[str, AdjustedTestResult],
) -> ClaimAudit:
    trials = tuple(trial_by_locator[item] for item in claim.evidence)
    checks: list[ClaimCheck] = [
        ClaimCheck(code="EVIDENCE_PRESENT", passed=True, detail="all evidence resolved")
    ]
    highest_tier = max(trial.evidence_tier for trial in trials)
    required_tier = _required_tier(claim.kind)
    checks.append(
        ClaimCheck(
            "EVIDENCE_TIER",
            highest_tier >= required_tier,
            f"highest tier {highest_tier.name}; required {required_tier.name}",
        )
    )
    legacy_trials = tuple(
        trial for trial in trials if trial.manifest_harness_binding_identity is None
    )
    binding_bridged = all(
        any(
            candidate.manifest_harness_binding_identity is not None
            and candidate.analysis_id == legacy.analysis_id
            and candidate.source_sha256 == legacy.source_sha256
            for candidate in trials
        )
        for legacy in legacy_trials
    )
    checks.append(
        ClaimCheck(
            "HARNESS_BINDING",
            binding_bridged,
            "each legacy unbound source has a value-bound exact rerun"
            if binding_bridged
            else "legacy fresh evidence lacks a cited source-identical value-bound rerun",
        )
    )
    assertions_required = claim.kind in {
        ClaimKind.DEVELOPMENT_RESULT,
        ClaimKind.PROCESS_GENERALIZATION,
        ClaimKind.PREDICTIVE_REPLICATION,
        ClaimKind.CAUSAL_MECHANISM,
        ClaimKind.TRADING_STRATEGY,
    }
    assertions_passed = bool(claim.assertions) and all(
        _assertion_matches(assertion, claim.statement, details_by_locator)
        for assertion in claim.assertions
    )
    if assertions_required or claim.assertions:
        checks.append(
            ClaimCheck(
                "EVIDENCE_VALUE_ASSERTIONS",
                assertions_passed,
                "claim values match exact receipt fields"
                if assertions_passed
                else "claim values are missing from or differ from exact receipt fields",
            )
        )
    interval_required = claim.kind in {
        ClaimKind.PROCESS_GENERALIZATION,
        ClaimKind.PREDICTIVE_REPLICATION,
        ClaimKind.CAUSAL_MECHANISM,
        ClaimKind.TRADING_STRATEGY,
    }
    if interval_required or claim.interval_id is not None:
        interval = interval_by_id.get(claim.interval_id or "")
        interval_passed = (
            interval is not None
            and interval.evidence in claim.evidence
            and interval.unit in _DEPENDENCE_AWARE_UNITS
            and interval.confidence_level >= _MINIMUM_CONFIDENCE_LEVEL
            and interval.repetitions >= _MINIMUM_BOOTSTRAP_REPETITIONS
            and _interval_excludes_null(interval)
        )
        checks.append(
            ClaimCheck(
                "DEPENDENCE_AWARE_INTERVAL",
                interval_passed,
                "required event-level interval is complete and excludes its declared null"
                if interval_passed
                else "missing or insufficient dependence-aware interval",
            )
        )
    test_required = interval_required
    if test_required or claim.test_id is not None:
        test = test_by_id.get(claim.test_id or "")
        test_passed = test is not None and test.unit in _DEPENDENCE_AWARE_UNITS and test.passed
        checks.append(
            ClaimCheck(
                "MULTIPLICITY_ADJUSTED_TEST",
                test_passed,
                "registered dependence-aware test passed its search adjustment"
                if test_passed
                else "missing or failed multiplicity-adjusted dependence-aware test",
            )
        )
    robustness_required = claim.kind in {
        ClaimKind.PROCESS_GENERALIZATION,
        ClaimKind.PREDICTIVE_REPLICATION,
        ClaimKind.CAUSAL_MECHANISM,
        ClaimKind.TRADING_STRATEGY,
    }
    if robustness_required:
        checks.extend(
            (
                ClaimCheck(
                    "FALSIFICATION_EVIDENCE",
                    bool(claim.falsification_refs),
                    "falsification evidence declared"
                    if claim.falsification_refs
                    else "required falsification evidence is missing",
                ),
                ClaimCheck(
                    "STABILITY_EVIDENCE",
                    bool(claim.stability_refs),
                    "stability evidence declared"
                    if claim.stability_refs
                    else "required stability evidence is missing",
                ),
            )
        )
    if claim.kind in {ClaimKind.PREDICTIVE_REPLICATION, ClaimKind.TRADING_STRATEGY}:
        checks.append(
            ClaimCheck(
                "FROZEN_BEFORE_EVALUATION",
                claim.frozen_before_evaluation,
                "system was frozen before evaluation"
                if claim.frozen_before_evaluation
                else "predictive recipe was not proved frozen before evaluation",
            )
        )
    if claim.kind is ClaimKind.CAUSAL_MECHANISM:
        checks.append(
            ClaimCheck(
                "CAUSAL_DESIGN",
                claim.causal_design_ref is not None,
                "causal identification design declared"
                if claim.causal_design_ref is not None
                else "observational association has no causal identification design",
            )
        )
    if claim.kind is ClaimKind.TRADING_STRATEGY:
        execution_validated = any(
            trial.evidence_tier >= EvidenceTier.EXECUTION_VALIDATED
            and trial.disposition == "execution_validated"
            for trial in trials
        )
        checks.append(
            ClaimCheck(
                "EXECUTION_TIER_INSUFFICIENT",
                execution_validated,
                "campaign contains execution-validated evidence"
                if execution_validated
                else "no cited campaign evidence is execution-validated",
            )
        )
        execution = claim.execution_evidence
        complete_execution = (
            execution is not None
            and execution.data_kind
            in {
                ExecutionDataKind.HISTORICAL_QUOTES,
                ExecutionDataKind.ORDER_BOOK,
                ExecutionDataKind.RECORDED_FILLS,
            }
            and execution.observed_spreads
            and execution.observed_fees
            and execution.modeled_latency
            and execution.modeled_queue_position
            and execution.modeled_partial_fills
        )
        checks.append(
            ClaimCheck(
                "EXECUTION_DATA_INSUFFICIENT",
                complete_execution,
                "quote/fill, spread, fee, latency, queue, and partial-fill evidence is complete"
                if complete_execution
                else "sampled marks or incomplete execution assumptions cannot support trading",
            )
        )
    language_passed = _language_is_compatible(claim)
    checks.append(
        ClaimCheck(
            "CLAIM_LANGUAGE",
            language_passed,
            "claim language matches its declared evidence class"
            if language_passed
            else "claim wording exceeds its declared evidence class",
        )
    )
    passed = all(check.passed for check in checks)
    return ClaimAudit(
        claim_id=claim.claim_id,
        statement=claim.statement,
        kind=claim.kind,
        passed=passed,
        checks=tuple(checks),
        evidence_receipt_ids=tuple(trial.execution_receipt_id for trial in trials),
        limitations=claim.limitations,
    )


def _required_tier(kind: ClaimKind) -> EvidenceTier:
    if kind in {ClaimKind.AUDIT_FACT, ClaimKind.EVIDENCE_BOUNDARY}:
        return EvidenceTier.BLOCKED_OR_NOT_TESTED
    if kind is ClaimKind.DEVELOPMENT_RESULT:
        return EvidenceTier.EXPLORATORY_DEVELOPMENT
    if kind in {ClaimKind.PROCESS_GENERALIZATION, ClaimKind.PREDICTIVE_REPLICATION}:
        return EvidenceTier.FRESH_DEVELOPMENT_REPLICATION
    if kind is ClaimKind.CAUSAL_MECHANISM:
        return EvidenceTier.PROTECTED_RESULT
    return EvidenceTier.EXECUTION_VALIDATED


def _assertion_matches(
    assertion: EvidenceAssertion,
    statement: str,
    details_by_locator: dict[EvidenceLocator, object],
) -> bool:
    current = details_by_locator.get(assertion.evidence)
    for key in assertion.details_path:
        if isinstance(key, str) and isinstance(current, dict):
            current = cast("dict[str, object]", current).get(key)
        elif isinstance(key, int) and isinstance(current, list):
            current_list = cast("list[object]", current)
            if key >= len(current_list):
                return False
            current = current_list[key]
        else:
            return False
    if (
        not isinstance(current, (str, int, float, bool))
        or isinstance(current, bool) != isinstance(assertion.expected_value, bool)
        or current != assertion.expected_value
    ):
        return False
    return (
        _format_assertion_value(
            value=assertion.expected_value,
            value_format=assertion.value_format,
        )
        in statement
    )


def _format_assertion_value(
    *,
    value: str | float | bool,
    value_format: ValueFormat,
) -> str:
    if value_format is ValueFormat.RAW:
        return str(value)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PaperAuditError("numeric assertion format requires a numeric receipt value")
    if value_format is ValueFormat.INTEGER:
        return str(int(value))
    if value_format is ValueFormat.PERCENT_2:
        return f"{value:.2%}"
    return f"{value:.4f}"


def _language_is_compatible(claim: ClaimDeclaration) -> bool:
    lowered = claim.statement.lower()
    if claim.kind is ClaimKind.EVIDENCE_BOUNDARY:
        return any(marker in lowered for marker in (" no ", " not ", "does not", "requires"))
    if claim.kind is not ClaimKind.TRADING_STRATEGY and any(
        term in lowered for term in _RESERVED_TRADING_TERMS
    ):
        return False
    if claim.kind is not ClaimKind.CAUSAL_MECHANISM and any(
        term in lowered for term in _RESERVED_CAUSAL_TERMS
    ):
        return False
    return claim.kind is not ClaimKind.DEVELOPMENT_RESULT or not any(
        term in lowered for term in ("replicated", "confirmed", "validated")
    )


def _interval_excludes_null(interval: EffectInterval) -> bool:
    if interval.direction is EffectDirection.ABOVE:
        return interval.lower > interval.null_value
    if interval.direction is EffectDirection.BELOW:
        return interval.upper < interval.null_value
    return interval.upper < interval.null_value or interval.lower > interval.null_value


def _adjust_tests(protocol: PaperProtocol) -> tuple[AdjustedTestResult, ...]:
    test_by_id = {test.test_id: test for test in protocol.tests}
    adjusted_by_id: dict[str, AdjustedTestResult] = {}
    for family in protocol.families:
        tests = tuple(test_by_id[test_id] for test_id in family.test_ids)
        raw = {test.test_id: _binomial_p_value(test) for test in tests}
        if family.complete_test_inventory:
            adjusted = _holm_adjust(raw)
            method = "holm"
            search_count = len(tests)
        else:
            search_count = max(len(family.search_evidence), len(tests))
            adjusted = {
                test_id: min(1.0, p_value * search_count) for test_id, p_value in raw.items()
            }
            method = "bonferroni-recorded-search"
        for test in tests:
            adjusted_by_id[test.test_id] = AdjustedTestResult(
                test_id=test.test_id,
                family_id=family.family_id,
                unit=test.unit,
                raw_p_value=raw[test.test_id],
                adjusted_p_value=adjusted[test.test_id],
                adjustment_method=method,
                search_count=search_count,
                passed=adjusted[test.test_id] <= protocol.alpha,
            )
    return tuple(adjusted_by_id[test.test_id] for test in protocol.tests)


def _holm_adjust(raw: dict[str, float]) -> dict[str, float]:
    ordered = sorted(raw.items(), key=lambda item: (item[1], item[0]))
    adjusted: dict[str, float] = {}
    running = 0.0
    count = len(ordered)
    for rank, (test_id, p_value) in enumerate(ordered):
        running = max(running, min(1.0, p_value * (count - rank)))
        adjusted[test_id] = running
    return adjusted


def _binomial_p_value(test: HypothesisTest) -> float:
    probabilities = tuple(
        math.comb(test.trials, successes)
        * test.null_probability**successes
        * (1.0 - test.null_probability) ** (test.trials - successes)
        for successes in range(test.trials + 1)
    )
    if test.alternative is AlternativeHypothesis.GREATER:
        return min(1.0, sum(probabilities[test.successes :]))
    if test.alternative is AlternativeHypothesis.LESS:
        return min(1.0, sum(probabilities[: test.successes + 1]))
    observed = probabilities[test.successes]
    tolerance = 1e-15
    return min(1.0, sum(value for value in probabilities if value <= observed + tolerance))


def _verify_manifest(manifest: dict[str, object]) -> tuple[dict[str, object], ...]:
    analyses = tuple(_as_object(item, "campaign analysis") for item in _list(manifest, "analyses"))
    if not analyses:
        raise PaperAuditError("campaign manifest has no analyses")
    identities: list[str] = []
    analysis_ids: list[str] = []
    for analysis in analyses:
        source = _string(analysis, "source")
        source_sha256 = hashlib.sha256(source.encode()).hexdigest()
        if source_sha256 != _string(analysis, "source_sha256"):
            raise PaperAuditError("campaign analysis source hash is invalid")
        data_access = tuple(
            (
                _string(_as_object(item, "data access"), "view_id"),
                tuple(_strings(_as_object(item, "data access"), "field_ids")),
            )
            for item in _list(analysis, "data_access")
        )
        required_accesses = tuple(
            _list_string_pair(item, "required actual access")
            for item in _list(analysis, "required_actual_accesses")
        )
        expected_binding = _optional_string(analysis, "expected_harness_binding_identity")
        body = {
            "analysis_id": _string(analysis, "analysis_id"),
            "family": _string(analysis, "family"),
            "source_sha256": source_sha256,
            "data_access": data_access,
            "required_actual_accesses": required_accesses,
            "expected_dataset_refs": tuple(_strings(analysis, "expected_dataset_refs")),
            "expected_environment_refs": tuple(_strings(analysis, "expected_environment_refs")),
            "evidence_tier": _string(analysis, "evidence_tier"),
        }
        if expected_binding is not None:
            body["expected_harness_binding_identity"] = expected_binding
        identity = stable_identity("campaign-analysis", body)
        if identity != _string(analysis, "analysis_identity"):
            raise PaperAuditError("campaign analysis identity is invalid")
        EvidenceTier[_string(analysis, "evidence_tier")]
        identities.append(identity)
        analysis_ids.append(_string(analysis, "analysis_id"))
    _require_unique(iter(analysis_ids), "campaign analysis")
    campaign_identity = stable_identity(
        "research-campaign",
        {
            "campaign_id": _string(manifest, "campaign_id"),
            "mandate": _string(manifest, "mandate"),
            "analysis_ids": tuple(identities),
        },
    )
    if campaign_identity != _string(manifest, "campaign_identity"):
        raise PaperAuditError("campaign manifest identity is invalid")
    return analyses


def _verify_completion(
    completion: dict[str, object],
    campaign_identity: str,
    analyses: tuple[dict[str, object], ...],
) -> None:
    body = dict(completion)
    receipt_id = _string(body, "receipt_id")
    del body["receipt_id"]
    if stable_identity("campaign-completion-receipt", body) != receipt_id:
        raise PaperAuditError("campaign completion identity is invalid")
    if _string(completion, "campaign_identity") != campaign_identity:
        raise PaperAuditError("campaign completion references another campaign")
    if not _boolean(completion, "execution_complete"):
        raise PaperAuditError("campaign completion is not complete")
    expected_ids = tuple(_string(item, "analysis_id") for item in analyses)
    dispositions = tuple(
        _list_string_pair(item, "campaign disposition")
        for item in _list(completion, "dispositions")
    )
    if tuple(item[0] for item in dispositions) != expected_ids:
        raise PaperAuditError("campaign completion does not cover the manifest exactly")
    if len(_strings(completion, "receipt_ids")) != len(expected_ids):
        raise PaperAuditError("campaign completion receipt inventory is incomplete")


def _verify_execution(
    execution: dict[str, object],
    analysis: dict[str, object],
    campaign_identity: str,
) -> None:
    body = dict(execution)
    receipt_id = _string(body, "receipt_id")
    del body["receipt_id"]
    if stable_identity("campaign-execution-receipt", body) != receipt_id:
        raise PaperAuditError("campaign execution receipt identity is invalid")
    expected = (
        (_string(execution, "campaign_identity"), campaign_identity),
        (_string(execution, "analysis_identity"), _string(analysis, "analysis_identity")),
        (_string(execution, "analysis_id"), _string(analysis, "analysis_id")),
        (_string(execution, "source_sha256"), _string(analysis, "source_sha256")),
    )
    if any(observed != declared for observed, declared in expected):
        raise PaperAuditError("campaign execution conflicts with its manifest")
    expected_binding = _optional_string(analysis, "expected_harness_binding_identity")
    actual_binding = _optional_string(execution, "harness_binding_identity")
    if expected_binding is not None and actual_binding != expected_binding:
        raise PaperAuditError("campaign execution harness conflicts with its manifest")
    if _string(execution, "harness_execution_status") != "succeeded":
        raise PaperAuditError("campaign execution did not succeed")
    if not _boolean(execution, "admissible"):
        raise PaperAuditError("campaign execution was not admissible")


def _protocol_body(protocol: PaperProtocol) -> dict[str, object]:
    return {
        "title": protocol.title,
        "campaigns": protocol.campaigns,
        "claims": protocol.claims,
        "intervals": protocol.intervals,
        "tests": protocol.tests,
        "families": protocol.families,
        "alpha": protocol.alpha,
    }


def _report_body(report: PaperAuditReport) -> dict[str, object]:
    return {
        "schema_version": report.schema_version,
        "protocol_id": report.protocol_id,
        "title": report.title,
        "decision": report.decision,
        "campaigns": report.campaigns,
        "trials": report.trials,
        "unique_analysis_count": report.unique_analysis_count,
        "duplicate_execution_count": report.duplicate_execution_count,
        "tests": report.tests,
        "claims": report.claims,
        "warnings": report.warnings,
    }


def _require_locators(
    locators: tuple[EvidenceLocator, ...],
    trial_by_locator: dict[EvidenceLocator, TrialRecord],
) -> None:
    if any(locator not in trial_by_locator for locator in locators):
        raise PaperAuditError("paper protocol references evidence outside verified campaigns")


def _verify_families(
    protocol: PaperProtocol,
    trial_by_locator: dict[EvidenceLocator, TrialRecord],
) -> None:
    test_ids = {test.test_id for test in protocol.tests}
    for family in protocol.families:
        if not set(family.test_ids) <= test_ids:
            raise PaperAuditError("hypothesis family references an unknown test")
        family_tests = tuple(test for test in protocol.tests if test.family_id == family.family_id)
        if {test.test_id for test in family_tests} != set(family.test_ids):
            raise PaperAuditError("test and hypothesis-family membership disagree")
        _require_locators(family.search_evidence, trial_by_locator)
        if family.complete_test_inventory and not {test.evidence for test in family_tests} <= set(
            family.search_evidence
        ):
            raise PaperAuditError("complete test inventory omits its source evidence")
    represented_families = {family.family_id for family in protocol.families}
    if any(test.family_id not in represented_families for test in protocol.tests):
        raise PaperAuditError("every hypothesis test requires a declared search family")


def _require_unique(values: Iterable[object], name: str) -> None:
    sequence = tuple(values)
    if len(set(sequence)) != len(sequence):
        raise PaperAuditError(f"{name} identities must be unique")


def _require_sha256(content: bytes, expected: str, name: str) -> None:
    if hashlib.sha256(content).hexdigest() != expected:
        raise PaperAuditError(f"{name} bytes differ from the protocol")


def _json_object(content: bytes, name: str) -> dict[str, object]:
    try:
        decoded: object = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PaperAuditError(f"{name} is not valid JSON") from error
    return _as_object(decoded, name)


def _as_object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise PaperAuditError(f"{name} must be an object")
    return cast("dict[str, object]", value)


def _string(value: dict[str, object], key: str) -> str:
    result = value.get(key)
    if not isinstance(result, str):
        raise PaperAuditError(f"{key} must be a string")
    return result


def _integer(value: dict[str, object], key: str) -> int:
    result = value.get(key)
    if not isinstance(result, int) or isinstance(result, bool):
        raise PaperAuditError(f"{key} must be an integer")
    return result


def _optional_string(value: dict[str, object], key: str) -> str | None:
    result = value.get(key)
    if result is None:
        return None
    if not isinstance(result, str):
        raise PaperAuditError(f"{key} must be a string or null")
    return result


def _boolean(value: dict[str, object], key: str) -> bool:
    result = value.get(key)
    if not isinstance(result, bool):
        raise PaperAuditError(f"{key} must be a boolean")
    return result


def _list(value: dict[str, object], key: str) -> list[object]:
    result = value.get(key)
    if not isinstance(result, list):
        raise PaperAuditError(f"{key} must be a list")
    return cast("list[object]", result)


def _strings(value: dict[str, object], key: str) -> tuple[str, ...]:
    result = _list(value, key)
    if any(not isinstance(item, str) for item in result):
        raise PaperAuditError(f"{key} must contain strings")
    return tuple(cast("str", item) for item in result)


def _list_string_pair(value: object, name: str) -> tuple[str, str]:
    if not isinstance(value, list):
        raise PaperAuditError(f"{name} must be a two-item list")
    values = cast("list[object]", value)
    if len(values) != _PAIR_LENGTH:
        raise PaperAuditError(f"{name} must be a two-item list")
    first, second = values
    if not isinstance(first, str) or not isinstance(second, str):
        raise PaperAuditError(f"{name} values must be strings")
    return first, second


def _json_safe(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        mapping = cast("dict[object, object]", value)
        return {str(key): _json_safe(item) for key, item in mapping.items()}
    if isinstance(value, (list, tuple)):
        sequence = cast("list[object] | tuple[object, ...]", value)
        return [_json_safe(item) for item in sequence]
    return value


__all__ = [
    "AdjustedTestResult",
    "AlternativeHypothesis",
    "CampaignAudit",
    "CampaignReference",
    "ClaimAudit",
    "ClaimCheck",
    "ClaimDeclaration",
    "ClaimKind",
    "EffectDirection",
    "EffectInterval",
    "EvidenceAssertion",
    "EvidenceLocator",
    "EvidenceUnit",
    "ExecutionDataKind",
    "ExecutionEvidence",
    "HypothesisFamily",
    "HypothesisTest",
    "PaperAuditError",
    "PaperAuditReport",
    "PaperAuditor",
    "PaperDecision",
    "PaperProtocol",
    "TrialRecord",
    "ValueFormat",
    "bootstrap_mean_interval",
    "render_concise_paper",
    "verify_paper_audit_json",
]
