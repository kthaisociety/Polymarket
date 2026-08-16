"""Whole path from retained bytes through one reusable authored-research kernel."""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.message import Message
from typing import TYPE_CHECKING, Self

from research_agent.data_foundation import (
    ApprovedTemporalDataset,
    FieldDefinition,
    SampleKey,
    TemporalDatasetProfile,
    TemporalOffset,
    TemporalRegistrationAuthority,
)
from research_agent.data_workspace import DataWorkspace, FetchRequest, FetchStatus
from research_agent.investigation import (
    AuthoredCandidateManifest,
    AuthoredProgramProposal,
    AutonomousInvestigation,
    DevelopmentBudget,
    DevelopmentDisposition,
    InvestigationRequest,
    ResearcherContext,
    ResearchQuestion,
)

if TYPE_CHECKING:
    from pathlib import Path
    from urllib.request import Request

    import pytest

    from research_agent.data_foundation import AuthoritativeDataCatalog
    from research_agent.data_foundation.observations import DimensionValues


ORIGIN = datetime(2020, 1, 1, tzinfo=UTC)


class _Response:
    def __init__(self, content: bytes, url: str) -> None:
        self._stream = io.BytesIO(content)
        self._url = url
        self.status = 200
        self.headers = Message()
        self.headers["Content-Type"] = "application/json"
        self.headers["Content-Length"] = str(len(content))

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        del args

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)


@dataclass
class _OneProposalResearcher:
    proposal: AuthoredProgramProposal

    def propose(self, context: ResearcherContext) -> AuthoredProgramProposal:
        assert context.question.question_id == self.proposal.manifest.question_id
        return self.proposal


def _profile(
    name: str,
    *,
    dimensions: tuple[str, ...],
) -> TemporalDatasetProfile:
    return TemporalDatasetProfile(
        dataset_id=f"dataset:{name}",
        schema_version="v1",
        environment_id=f"environment:{name}",
        semantic_provenance_ref=f"semantics:{name}:v1",
        availability_rule_version=f"availability:{name}:observed-v1",
        fields=(
            FieldDefinition("x", "Signal", "float", "index", dimensions, "Predictor."),
            FieldDefinition("y", "Outcome", "float", "units", dimensions, "Outcome."),
        ),
        mandatory_caveats=("EXACT_RETAINED_RESEARCH_FIXTURE",),
    )


def _envelope(
    profile: TemporalDatasetProfile,
    *,
    step: timedelta,
    dimensions: dict[str, str],
) -> dict[str, object]:
    observations: list[dict[str, object]] = []
    for ordinal in range(9):
        decision = ORIGIN + step * ordinal
        outcome = decision + step
        observations.extend(
            (
                {
                    "field_id": "x",
                    "value": float(ordinal + 1),
                    "reference_time": decision.isoformat(),
                    "available_at": decision.isoformat(),
                    "vintage_id": "initial",
                    "revision_number": 0,
                    "dimensions": dimensions,
                    "caveats": [],
                },
                {
                    "field_id": "y",
                    "value": float(2 * (ordinal + 1)),
                    "reference_time": outcome.isoformat(),
                    "available_at": outcome.isoformat(),
                    "vintage_id": "initial",
                    "revision_number": 0,
                    "dimensions": dimensions,
                    "caveats": [],
                },
            )
        )
    return {
        "schema_version": "temporal-observations/v1",
        "profile_id": profile.identity,
        "observations": observations,
    }


def _approval(
    workspace: DataWorkspace,
    profile: TemporalDatasetProfile,
    *,
    url: str,
) -> ApprovedTemporalDataset:
    fetched = workspace.fetch(FetchRequest(url))
    assert fetched.status is FetchStatus.SUCCEEDED
    assert fetched.snapshot_ref is not None
    derived = workspace.derive(
        inputs={"source": fetched.snapshot_ref},
        source='payload = json_input("source")\nresult = emit(payload)',
        parameters={},
    )
    assert derived.dataset_ref is not None
    return ApprovedTemporalDataset(
        derived_ref=derived.dataset_ref,
        profile=profile,
        approval_ref=f"review:{profile.dataset_id}",
    )


def _proposal(
    catalog: AuthoritativeDataCatalog,
    *,
    question_id: str,
    horizon: TemporalOffset,
    dimensions: DimensionValues,
) -> AuthoredProgramProposal:
    schema = catalog.snapshot.datasets[0].schema
    source = """
def make_features():
    values = history("x")
    return {"level": values[-1]["value"]}

def make_label():
    path = outcome_path()
    return path[-1]["value"]

def fit():
    rows = training_rows()
    numerator = sum(row["features"]["level"] * row["label"] for row in rows)
    denominator = sum(row["features"]["level"] ** 2 for row in rows)
    return {"slope": numerator / denominator}

def predict():
    return model_state()["slope"] * feature_values()["level"]
"""
    manifest = AuthoredCandidateManifest(
        question_id=question_id,
        environment_id=catalog.snapshot.environment_id,
        predictor_fields=(schema.field_ref("x"),),
        outcome_field=schema.field_ref("y"),
        horizon=horizon,
        minimum_outcome_points=1,
        population_dimensions=dimensions,
        feature_names=("level",),
        missing_value_policy="fail_trial",
        evidence_refs=(catalog.catalog_attestation_id,),
        provenance_refs=("researcher:integration-fixture",),
    )
    return AuthoredProgramProposal(
        source=source,
        manifest=manifest,
        rationale="Test one authored level feature and model against an exact future label.",
        parent_trial_ids=(),
    )


def _request(
    catalog: AuthoritativeDataCatalog,
    *,
    question_id: str,
    step: timedelta,
    dimensions: DimensionValues,
) -> InvestigationRequest:
    return InvestigationRequest(
        question=ResearchQuestion(
            question_id=question_id,
            text=f"Can the retained signal predict the next {step.days}-day outcome?",
            environment_id=catalog.snapshot.environment_id,
            task_ref=f"task:{question_id}",
            evidence_refs=(catalog.catalog_attestation_id,),
        ),
        catalog=catalog.snapshot,
        sample_keys=tuple(SampleKey(ORIGIN + step * ordinal, dimensions) for ordinal in range(8)),
        current_time=ORIGIN + step * 10,
        budget=DevelopmentBudget(
            max_trials=1,
            minimum_training_rows=3,
            minimum_oof_predictions=4,
            primary_metric="mse",
            credible_at_or_below=0.0,
        ),
        random_seed=7,
    )


def test_two_retained_subjects_use_the_same_data_bridge_and_research_kernel(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Data and research definitions vary while registration and kernel code remain unchanged."""
    regional = _profile("regional-weekly", dimensions=("region",))
    market = _profile("market-daily", dimensions=())
    payloads = {
        "https://example.test/regional": json.dumps(
            _envelope(regional, step=timedelta(days=7), dimensions={"region": "SE"}),
            separators=(",", ":"),
            sort_keys=True,
        ).encode(),
        "https://example.test/market": json.dumps(
            _envelope(market, step=timedelta(days=1), dimensions={}),
            separators=(",", ":"),
            sort_keys=True,
        ).encode(),
    }

    def response(request: Request, timeout: object) -> _Response:
        del timeout
        url = request.full_url
        return _Response(payloads[url], url)

    monkeypatch.setattr(
        "research_agent.data_workspace.workspace.urllib.request.urlopen",
        response,
    )
    workspace = DataWorkspace(tmp_path / "data")
    regional_approval = _approval(
        workspace,
        regional,
        url="https://example.test/regional",
    )
    market_approval = _approval(
        workspace,
        market,
        url="https://example.test/market",
    )
    authority = TemporalRegistrationAuthority((regional_approval, market_approval))
    regional_catalog = authority.catalog((authority.register(workspace, regional_approval),))
    market_catalog = authority.catalog((authority.register(workspace, market_approval),))
    authority.require_catalog(regional_catalog)
    authority.require_catalog(market_catalog)

    kernel = AutonomousInvestigation()
    regional_dimensions = (("region", "SE"),)
    regional_horizon = TemporalOffset.elapsed(timedelta(days=7))
    market_horizon = TemporalOffset.elapsed(timedelta(days=1))
    regional_result = kernel.run(
        _request(
            regional_catalog,
            question_id="question:regional-weekly",
            step=timedelta(days=7),
            dimensions=regional_dimensions,
        ),
        _OneProposalResearcher(
            _proposal(
                regional_catalog,
                question_id="question:regional-weekly",
                horizon=regional_horizon,
                dimensions=regional_dimensions,
            )
        ),
    )
    market_result = kernel.run(
        _request(
            market_catalog,
            question_id="question:market-daily",
            step=timedelta(days=1),
            dimensions=(),
        ),
        _OneProposalResearcher(
            _proposal(
                market_catalog,
                question_id="question:market-daily",
                horizon=market_horizon,
                dimensions=(),
            )
        ),
    )

    assert regional_result.disposition is DevelopmentDisposition.CREDIBLE
    assert market_result.disposition is DevelopmentDisposition.CREDIBLE
    assert regional_result.evidence[0].metrics == (("mse", 0.0),)
    assert market_result.evidence[0].metrics == (("mse", 0.0),)
    assert regional_result.candidate is not None
    assert market_result.candidate is not None
    assert regional_result.candidate.candidate_id != market_result.candidate.candidate_id
    assert regional_catalog.snapshot.identity != market_catalog.snapshot.identity
