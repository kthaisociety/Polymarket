"""Application-level acceptance for the creativity-first investigation loop."""

# ruff: noqa: D103, PLR0915, PLR2004

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import cast

import pytest

from research_agent.data_foundation import (
    DataCatalogSnapshot,
    DatasetSchema,
    FieldDefinition,
    FieldRef,
    ObservationInput,
    ObservationRegistrar,
    SampleKey,
    TemporalOffset,
)
from research_agent.exploration import (
    AnalysisHarness,
    ArtifactStore,
    AuthorizedDataView,
    CapabilityPolicy,
)
from research_agent.investigation import (
    AuthoredCandidateManifest,
    AuthoredFreezeService,
    AuthoredProgramProposal,
    AutonomousInvestigation,
    DevelopmentBudget,
    DevelopmentDisposition,
    InvestigationConflictError,
    InvestigationRequest,
    ProtectedEvaluationPredeclaration,
    QuestionStatus,
    ResearcherContext,
    ResearchQuestion,
    RuntimeInvestigationCoordinator,
)
from research_agent.protected_evaluation import (
    FreezeEligibilityRegistry,
    FreezeGate,
    FrozenSystemRegistry,
    ResearchLedger,
)
from research_agent.runtime.actions import RunAuthoredDevelopmentTrialAction
from research_agent.runtime.capabilities import ActionRouter, DatasetRepository
from research_agent.runtime.commit import CommitCoordinator
from research_agent.runtime.context import ContextBuilder
from research_agent.runtime.engine import AutonomousResearchRuntime
from research_agent.runtime.initialization import ResearchRuntimeInitializer
from research_agent.runtime.models import (
    ContextObservation,
    ContextPacket,
    FailureCode,
    ObservationStatus,
    ResearchEnvironmentSnapshot,
)
from research_agent.runtime.provider import ModelResponse
from research_agent.runtime.store import InMemoryRuntimeStore
from research_agent.task_compilation import (
    ResearchEnvironmentSummary,
    TaskCompiler,
    TaskConfirmation,
    TaskPublisher,
    UserMandate,
)

DAY = timedelta(days=1)
ORIGIN = datetime(2025, 1, 1, tzinfo=UTC)


class _OneProposalResearcher:
    """A provider-shaped test double; this proves plumbing, not model quality."""

    def __init__(self, proposal: AuthoredProgramProposal) -> None:
        self._proposal = proposal
        self.contexts: list[ResearcherContext] = []

    def propose(self, context: ResearcherContext) -> AuthoredProgramProposal:
        self.contexts.append(context)
        return self._proposal


class _RevisionResearcher:
    """Revise a failed recipe using the exact prior evidence ancestry."""

    def __init__(self, proposal: AuthoredProgramProposal) -> None:
        self._proposal = proposal
        self.contexts: list[ResearcherContext] = []

    def propose(self, context: ResearcherContext) -> AuthoredProgramProposal:
        self.contexts.append(context)
        if not context.prior_evidence:
            source = self._proposal.source.replace(
                'return {"slope": numerator / denominator}',
                'return {"slope": 0.0}',
            )
            return replace(self._proposal, source=source)
        return replace(
            self._proposal,
            parent_trial_ids=(context.prior_evidence[-1].trial_id,),
            rationale="Revise the failed zero-slope recipe using its exact trial evidence.",
        )


class _RuntimeRevisionProvider:
    """Packet-only provider double that revises from the prior runtime observation."""

    def __init__(self, investigation_id: str, proposal: AuthoredProgramProposal) -> None:
        self._investigation_id = investigation_id
        self._proposal = proposal
        self.proposals: list[AuthoredProgramProposal] = []
        self.calls: list[ContextPacket] = []

    def complete(self, packet: ContextPacket) -> ModelResponse:
        self.calls.append(packet)
        if len(self.calls) == 1:
            proposal = replace(
                self._proposal,
                source=self._proposal.source.replace(
                    'return {"slope": numerator / denominator}',
                    'return {"slope": 0.0}',
                ),
            )
        else:
            trial_id = packet.working_observations[-1].payload["trial_id"]
            assert isinstance(trial_id, str)
            proposal = replace(
                self._proposal,
                parent_trial_ids=(trial_id,),
                rationale="Revise the zero-slope recipe from exact runtime evidence.",
            )
        self.proposals.append(proposal)
        action: dict[str, object] = {
            "kind": "run_authored_development_trial",
            "action_id": f"action-authored-trial-{len(self.calls)}",
            "session_id": packet.session_id,
            "episode_id": packet.episode_id,
            "arguments": {
                "investigation_id": self._investigation_id,
                "source": proposal.source,
                "manifest": _manifest_json(proposal.manifest),
                "rationale": proposal.rationale,
                "parent_trial_ids": list(proposal.parent_trial_ids),
                "idempotency_key": f"authored-trial-key-{len(self.calls)}",
            },
        }
        return ModelResponse(
            message="Revise from development evidence.",
            action=action,
            provider_metadata={"fixture": "packet-only"},
        )


class _StatelessSurfaceResearcher:
    """Derive every exact action and manifest identity from the current packet alone."""

    __slots__ = ()

    def complete(self, packet: ContextPacket) -> ModelResponse:
        registration = next(
            item
            for item in packet.working_observations
            if item.observation_type == "authored_investigation_registered"
        )
        trials = tuple(
            item
            for item in packet.working_observations
            if item.observation_type == "authored_development_trial"
        )
        analyses = tuple(
            item
            for item in packet.working_observations
            if item.observation_type == "analysis_result"
        )
        if not trials:
            return self._trial_response(packet, registration, feature_kind="level")
        if not analyses:
            surfaces = cast(
                "tuple[Mapping[str, object], ...]",
                registration.payload["analysis_surfaces"],
            )
            assert surfaces
            surface = surfaces[0]
            field_ids = cast("tuple[str, ...]", surface["field_ids"])
            return ModelResponse(
                message=(
                    "Compare generic level and interaction candidates after the baseline failed."
                ),
                action={
                    "kind": "run_analysis",
                    "action_id": "action:surface-diagnostic",
                    "session_id": packet.session_id,
                    "episode_id": packet.episode_id,
                    "arguments": {
                        "source": _generic_relationship_diagnostic_source(),
                        "data_access": [
                            {
                                "view_id": surface["view_id"],
                                "field_ids": list(field_ids),
                            }
                        ],
                        "random_seed": 17,
                    },
                },
                provider_metadata={"fixture": "stateless-packet-only"},
            )
        details = analyses[-1].payload["details"]
        assert isinstance(details, Mapping)
        assert details["best_feature"] == "interaction"
        return self._trial_response(
            packet,
            registration,
            feature_kind="interaction",
            parent_trial_id=trials[-1].payload["trial_id"],
            analysis_observation_id=analyses[-1].observation_id,
        )

    @staticmethod
    def _trial_response(
        packet: ContextPacket,
        registration: ContextObservation,
        *,
        feature_kind: str,
        parent_trial_id: object | None = None,
        analysis_observation_id: str | None = None,
    ) -> ModelResponse:
        payload = registration.payload
        field_definitions = cast("tuple[Mapping[str, object], ...]", payload["field_definitions"])
        refs: dict[str, Mapping[str, object]] = {}
        for item in field_definitions:
            field_ref = cast("Mapping[str, object]", item["field_ref"])
            field_id = cast("str", field_ref["field_id"])
            refs[field_id] = field_ref
        target_id = packet.target_field_id
        assert target_id is not None
        horizon = packet.forecast_horizon
        assert horizon is not None
        assert horizon.elapsed_microseconds is not None
        predictors = [refs["x1"]] if feature_kind == "level" else [refs["x1"], refs["x2"]]
        feature_name = "x1_level" if feature_kind == "level" else "interaction"
        evidence_refs = [registration.observation_id]
        if analysis_observation_id is not None:
            evidence_refs.append(analysis_observation_id)
        action_number = 1 if parent_trial_id is None else 2
        assert parent_trial_id is None or isinstance(parent_trial_id, str)
        return ModelResponse(
            message=f"Author the {feature_kind} candidate from exact context identities.",
            action={
                "kind": "run_authored_development_trial",
                "action_id": f"action:packet-authored-trial:{action_number}",
                "session_id": packet.session_id,
                "episode_id": packet.episode_id,
                "arguments": {
                    "investigation_id": payload["investigation_id"],
                    "source": _authored_linear_source(feature_kind),
                    "manifest": {
                        "question_id": payload["question_id"],
                        "environment_id": refs[target_id]["environment_id"],
                        "predictor_fields": predictors,
                        "outcome_field": refs[target_id],
                        "horizon": {
                            "kind": "elapsed",
                            "elapsed_microseconds": horizon.elapsed_microseconds,
                        },
                        "minimum_outcome_points": 1,
                        "population_dimensions": [],
                        "feature_names": [feature_name],
                        "missing_value_policy": "exclude_example",
                        "evidence_refs": evidence_refs,
                        "provenance_refs": ["researcher:stateless-packet-only"],
                    },
                    "rationale": f"The packet evidence supports the {feature_kind} candidate.",
                    "parent_trial_ids": [] if parent_trial_id is None else [parent_trial_id],
                    "idempotency_key": f"packet-authored-trial:{action_number}",
                },
            },
            provider_metadata={"fixture": "stateless-packet-only"},
        )


def _generic_relationship_diagnostic_source() -> str:
    return """
left = read("development-view", "x1")
right = read("development-view", "x2")
outcome = read("development-view", "y")
interaction = [a * b for a, b in zip(left, right)]
left_error = sum((a - y) ** 2 for a, y in zip(left, outcome))
interaction_error = sum((a - y) ** 2 for a, y in zip(interaction, outcome))
best_feature = "interaction" if interaction_error < left_error else "x1"
result = structured_return(
    "Compared lawful generic candidate relationships.",
    {"best_feature": best_feature, "scores": {"x1": left_error, "interaction": interaction_error}},
)
"""


def _authored_linear_source(feature_kind: str) -> str:
    expression = (
        'history("x1")[-1]["value"]'
        if feature_kind == "level"
        else 'history("x1")[-1]["value"] * history("x2")[-1]["value"]'
    )
    feature_name = "x1_level" if feature_kind == "level" else "interaction"
    return f"""\
def make_features():
    return {{"{feature_name}": {expression}}}

def make_label():
    return outcome_path()[-1]["value"]

def fit():
    rows = training_rows()
    numerator = sum(row["features"]["{feature_name}"] * row["label"] for row in rows)
    denominator = sum(row["features"]["{feature_name}"] ** 2 for row in rows)
    return {{"slope": numerator / denominator}}

def predict():
    return model_state()["slope"] * feature_values()["{feature_name}"]
"""


def _world(*, poison_multiplier: float = 1.0, signal: bool = True) -> DataCatalogSnapshot:
    schema = DatasetSchema(
        dataset_id="hidden-world",
        version="v1",
        environment_id="development-world",
        provenance_ref="fixture:hidden-world",
        fields=(
            FieldDefinition("x1", "Signal one", "float", "index", (), "First input."),
            FieldDefinition("x2", "Signal two", "float", "index", (), "Second input."),
            FieldDefinition(
                "future_poison",
                "Tempting future value",
                "float",
                "index",
                (),
                "Published only after every simulated decision.",
            ),
            FieldDefinition("y", "Future outcome", "float", "units", (), "One-day outcome."),
        ),
    )
    rows: list[ObservationInput] = []
    for day in range(1, 25):
        left = -1.0 if day % 2 else 1.0
        right = -1.0 if day % 4 < 2 else 1.0
        label = 3.0 * left * right if signal else (1.0 if day % 3 else -1.0)
        values = {"x1": left, "x2": right}
        for field_id, value in values.items():
            rows.append(_row(schema, field_id, value, day, day))
        rows.append(
            _row(
                schema,
                "future_poison",
                poison_multiplier * label,
                day,
                100,
            )
        )
        rows.append(_row(schema, "y", label, day + 1, day + 1))
    return DataCatalogSnapshot(
        schema.environment_id,
        (ObservationRegistrar().register(schema, tuple(rows)),),
    )


def _row(
    schema: DatasetSchema,
    field_id: str,
    value: float,
    reference_day: int,
    available_day: int,
) -> ObservationInput:
    return ObservationInput(
        field_ref=schema.field_ref(field_id),
        value=value,
        reference_time=ORIGIN + DAY * reference_day,
        available_at=ORIGIN + DAY * available_day,
        vintage_id="initial",
        revision_number=0,
        source_ref="fixture:hidden-world",
        provenance_ref=f"fixture:{field_id}:{reference_day}:{value}",
        availability_rule_version="fixture-release-v1",
        dimensions=(),
    )


def _proposal(catalog: DataCatalogSnapshot) -> AuthoredProgramProposal:
    schema = catalog.datasets[0].schema
    source = """
def make_features():
    left = history("x1")
    right = history("x2")
    return {"interaction": left[-1]["value"] * right[-1]["value"]}

def make_label():
    path = outcome_path()
    return path[-1]["value"]

def fit():
    rows = training_rows()
    numerator = sum(row["features"]["interaction"] * row["label"] for row in rows)
    denominator = sum(row["features"]["interaction"] ** 2 for row in rows)
    return {"slope": numerator / denominator}

def predict():
    return model_state()["slope"] * feature_values()["interaction"]
"""
    manifest = AuthoredCandidateManifest(
        question_id="question:interaction",
        environment_id=catalog.environment_id,
        predictor_fields=(schema.field_ref("x1"), schema.field_ref("x2")),
        outcome_field=schema.field_ref("y"),
        horizon=TemporalOffset.elapsed(DAY),
        minimum_outcome_points=1,
        population_dimensions=(),
        feature_names=("interaction",),
        missing_value_policy="exclude_example",
        evidence_refs=("observation:exploratory-interaction",),
        provenance_refs=("researcher:test-provider",),
    )
    return AuthoredProgramProposal(
        source=source,
        manifest=manifest,
        rationale="The outcome may depend on an interaction absent from marginal effects.",
        parent_trial_ids=(),
    )


def _request(
    catalog: DataCatalogSnapshot,
    *,
    max_trials: int = 1,
    task_ref: str = "task:hidden-interaction",
    predeclare_protected: bool = False,
) -> InvestigationRequest:
    question = ResearchQuestion(
        question_id="question:interaction",
        text="Can an authored interaction predict the next observation?",
        environment_id=catalog.environment_id,
        task_ref=task_ref,
        evidence_refs=("observation:question",),
    )
    return InvestigationRequest(
        question=question,
        catalog=catalog,
        sample_keys=tuple(SampleKey(ORIGIN + DAY * day) for day in range(2, 24)),
        current_time=ORIGIN + DAY * 30,
        budget=DevelopmentBudget(
            max_trials=max_trials,
            minimum_training_rows=6,
            minimum_oof_predictions=8,
            primary_metric="mse",
            credible_at_or_below=1e-12,
        ),
        random_seed=17,
        protected_predeclaration=(
            ProtectedEvaluationPredeclaration(
                data_protocol_ref="protocol:data:authored-v1",
                training_protocol_ref="protocol:training:authored-v1",
                scenario_ref="scenario:protected-authored-v1",
                decision_times_ref="decision-times:protected-authored-v1",
                evaluation_spec_ref="protocol:evaluation:protected-v1",
                validation_standard_ref="protocol:validation:protected-v1",
                protected_scope_id="scope:protected-authored-v1",
                claim_template_ref="claim-template:authored-v1",
                freeze_standard_ref="standard:freeze:authored-v1",
            )
            if predeclare_protected
            else None
        ),
    )


def test_question_to_authored_code_to_temporal_evidence_is_one_real_path() -> None:
    catalog = _world()
    researcher = _OneProposalResearcher(_proposal(catalog))

    result = AutonomousInvestigation().run(_request(catalog), researcher)

    assert result.disposition is DevelopmentDisposition.CREDIBLE
    assert result.question_status is QuestionStatus.CREDIBLE_CANDIDATE
    assert result.trials_attempted == 1
    assert result.evidence[-1].metrics == (("mse", 0.0),)
    assert len(result.evidence[-1].predictions) >= 8
    assert result.candidate is not None
    assert result.candidate.source_sha256
    assert result.candidate.manifest.feature_names == ("interaction",)
    assert result.evidence[-1].fit_accesses
    assert result.evidence[-1].prediction_accesses
    assert researcher.contexts[0].prior_evidence == ()


def test_unreleased_future_poison_cannot_change_development_evidence() -> None:
    low = _world(poison_multiplier=1.0)
    high = _world(poison_multiplier=999_999.0)

    low_result = AutonomousInvestigation().run(
        _request(low), _OneProposalResearcher(_proposal(low))
    )
    high_result = AutonomousInvestigation().run(
        _request(high), _OneProposalResearcher(_proposal(high))
    )

    assert low_result.evidence[-1].metrics == high_result.evidence[-1].metrics
    assert low_result.evidence[-1].predictions == high_result.evidence[-1].predictions
    assert all(
        access.field_id != "future_poison" for access in low_result.evidence[-1].feature_accesses
    )


def test_budget_exhaustion_preserves_negative_trial_instead_of_cherry_picking() -> None:
    catalog = _world(signal=False)

    result = AutonomousInvestigation().run(
        _request(catalog), _OneProposalResearcher(_proposal(catalog))
    )

    assert result.disposition is DevelopmentDisposition.REJECT
    assert result.question_status is QuestionStatus.NEGATIVE
    assert result.trials_attempted == 1
    assert len(result.trial_ledger) == 2
    assert tuple(record.status.value for record in result.trial_ledger) == (
        "attempted",
        "succeeded",
    )
    assert result.evidence[-1].metrics[0][1] > 0.0


def test_failed_recipe_is_revised_from_evidence_with_exact_trial_ancestry() -> None:
    """The application returns evidence to intelligence and records both complete trials."""
    catalog = _world()
    researcher = _RevisionResearcher(_proposal(catalog))

    result = AutonomousInvestigation().run(_request(catalog, max_trials=2), researcher)

    assert result.disposition is DevelopmentDisposition.CREDIBLE
    assert result.trials_attempted == 2
    assert result.evidence[0].metrics[0][1] > 0.0
    assert result.evidence[1].metrics == (("mse", 0.0),)
    assert result.candidate is not None
    assert result.candidate.parent_trial_ids == (result.evidence[0].trial_id,)
    assert researcher.contexts[1].prior_evidence == (result.evidence[0],)
    assert tuple(record.status.value for record in result.trial_ledger) == (
        "attempted",
        "succeeded",
        "attempted",
        "succeeded",
    )


def test_real_runtime_turn_executes_authored_trial_and_rebuilds_evidence_context() -> None:
    """The provider-facing action reaches the same evaluator and survives context rebuild."""
    catalog = _world()
    task_proposal = (
        TaskCompiler()
        .compile(
            UserMandate(
                original_text="Research the hidden interaction world.",
                research_objective="Find a lawful next-observation predictive relationship.",
                target_field_id="y",
                forecast_horizon=TemporalOffset.elapsed(DAY),
                dataset_refs=("hidden-world",),
            ),
            ResearchEnvironmentSummary(
                environment_id=catalog.environment_id,
                available_field_ids=("x1", "x2", "future_poison", "y"),
                available_dataset_refs=("hidden-world",),
            ),
        )
        .proposal
    )
    assert task_proposal is not None
    published = TaskPublisher().confirm(
        task_proposal,
        TaskConfirmation(
            confirmation_id=f"confirmation:{task_proposal.proposal_id}",
            proposal_id=task_proposal.proposal_id,
            proposal_version=task_proposal.version,
            semantic_digest=task_proposal.semantic_digest,
            approved=True,
        ),
    )
    assert published.task is not None
    task = published.task
    environment = ResearchEnvironmentSnapshot(
        environment_id=catalog.environment_id,
        version=1,
        dataset_refs=("hidden-world",),
        readable_dataset_refs=("hidden-world",),
        capability_names=("run_authored_development_trial",),
    )
    store = InMemoryRuntimeStore()
    initialized = ResearchRuntimeInitializer(store).initialize(
        task,
        environment,
        request_id="initialize-authored-investigation",
    )
    coordinator = RuntimeInvestigationCoordinator()
    ledger = ResearchLedger()
    eligibility = FreezeEligibilityRegistry()
    frozen_systems = FrozenSystemRegistry()
    freeze_service = AuthoredFreezeService(
        authority_id="authority:independent-freeze",
        investigations=coordinator,
        eligibility=eligibility,
        gate=FreezeGate(
            ledger=ledger,
            registry=frozen_systems,
            eligibility=eligibility,
            decision_authority_id="authority:independent-freeze",
            clock=lambda: ORIGIN + DAY * 200,
        ),
    )
    with pytest.raises(TypeError, match="freeze authority cannot be copied"):
        copy.copy(freeze_service)
    with pytest.raises(TypeError, match="freeze authority cannot be copied"):
        copy.deepcopy(freeze_service)
    router = ActionRouter(
        store,
        DatasetRepository(()),
        investigations=coordinator,
        authored_freeze=freeze_service,
    )
    registration = router.register_investigation(
        _request(
            catalog,
            task_ref=task.task_id,
            max_trials=2,
            predeclare_protected=True,
        ),
        session_id=initialized.session.session_id,
    )
    proposal = _proposal(catalog)
    denied = router.execute_authored_development_trial(
        RunAuthoredDevelopmentTrialAction(
            action_id="action-forged-investigation",
            session_id=initialized.session.session_id,
            episode_id=initialized.episode.episode_id,
            investigation_id="investigation:unissued",
            proposal=replace(
                proposal,
                source=proposal.source.replace(
                    'left = history("x1")',
                    'left = open("/etc/passwd")',
                ),
            ),
            idempotency_key="forged-investigation-key",
        )
    )
    assert denied.failure is not None
    assert denied.failure.code is FailureCode.AUTHORITY_DENIED
    assert denied.artifact_refs == ()
    provider = _RuntimeRevisionProvider(registration.registration_id, proposal)
    context = ContextBuilder(store)
    initial_packet = context.build_current_context(initialized.session.session_id)
    runtime = AutonomousResearchRuntime(
        store,
        provider,
        context,
        router,
        CommitCoordinator(store),
    )

    first_turn = runtime.advance_one_turn(initialized.session.session_id)
    rebuilt_after_first = context.build_current_context(initialized.session.session_id)
    second_turn = runtime.advance_one_turn(initialized.session.session_id)
    rebuilt = context.build_current_context(initialized.session.session_id)

    assert first_turn.action_kind == "run_authored_development_trial"
    assert first_turn.observation is not None
    assert first_turn.observation.payload["disposition"] == "revise"
    assert second_turn.action_kind == "run_authored_development_trial"
    turn = second_turn
    assert initial_packet.working_observations[-1].payload["investigation_id"] == (
        registration.registration_id
    )
    assert provider.calls[1].working_observations == rebuilt_after_first.working_observations
    assert provider.proposals[1].parent_trial_ids == (first_turn.observation.payload["trial_id"],)
    assert turn.observation is not None
    assert turn.observation.status is ObservationStatus.SUCCEEDED
    assert turn.observation.epistemic_status == "DEVELOPMENT"
    assert turn.observation.payload["disposition"] == "credible"
    assert turn.observation.payload["candidate_id"]
    assert turn.observation.payload["evidence_id"]
    assert turn.observation.payload["freeze_status"] == "accept"
    frozen_system_id = turn.observation.payload["frozen_system_id"]
    assert isinstance(frozen_system_id, str)
    frozen = frozen_systems.get(frozen_system_id)
    assert frozen is not None
    assert frozen.system_id == turn.observation.payload["candidate_id"]
    assert frozen.development_evidence_refs == (turn.observation.payload["evidence_id"],)
    assert rebuilt.available_actions == (
        "run_authored_development_trial",
        "propose_episode_transition",
    )
    assert (
        rebuilt.working_observations[-1].payload["evidence_id"]
        == turn.observation.payload["evidence_id"]
    )
    evidence_id = turn.observation.payload["evidence_id"]
    assert isinstance(evidence_id, str)
    assert coordinator.resolve_evidence(evidence_id).metrics == (("mse", 0.0),)
    assert first_turn.observation is not None
    first_candidate_id = first_turn.observation.payload["candidate_id"]
    first_evidence_id = first_turn.observation.payload["evidence_id"]
    assert isinstance(first_candidate_id, str)
    assert isinstance(first_evidence_id, str)
    with pytest.raises(ValueError, match="did not earn a credible"):
        freeze_service.assess_credible(
            candidate_id=first_candidate_id,
            evidence_id=first_evidence_id,
            requester_id=initialized.session.session_id,
            beneficiary_id=task.task_id,
        )
    replay = coordinator.execute(
        registration.registration_id,
        provider.proposals[-1],
        session_id=initialized.session.session_id,
        episode_id=initialized.episode.episode_id,
        idempotency_key="authored-trial-key-2",
    )
    assert replay.receipt_id == turn.observation.payload["receipt_id"]
    with pytest.raises(InvestigationConflictError, match="changed semantics"):
        coordinator.execute(
            registration.registration_id,
            replace(provider.proposals[-1], rationale="changed after the scientific effect"),
            session_id=initialized.session.session_id,
            episode_id=initialized.episode.episode_id,
            idempotency_key="authored-trial-key-2",
        )


def test_stateless_researcher_discovers_surface_then_authors_evidence_driven_revision() -> None:
    """The application supplies identities and affordances, while the researcher supplies method."""
    catalog = _world()
    task_proposal = (
        TaskCompiler()
        .compile(
            UserMandate(
                original_text="Research the hidden interaction world without a prepared manifest.",
                research_objective="Find a lawful next-observation predictive relationship.",
                target_field_id="y",
                forecast_horizon=TemporalOffset.elapsed(DAY),
                dataset_refs=("hidden-world",),
            ),
            ResearchEnvironmentSummary(
                environment_id=catalog.environment_id,
                available_field_ids=("x1", "x2", "future_poison", "y"),
                available_dataset_refs=("hidden-world",),
            ),
        )
        .proposal
    )
    assert task_proposal is not None
    published = TaskPublisher().confirm(
        task_proposal,
        TaskConfirmation(
            confirmation_id=f"confirmation:{task_proposal.proposal_id}",
            proposal_id=task_proposal.proposal_id,
            proposal_version=task_proposal.version,
            semantic_digest=task_proposal.semantic_digest,
            approved=True,
        ),
    )
    assert published.task is not None
    environment = ResearchEnvironmentSnapshot(
        environment_id=catalog.environment_id,
        version=1,
        dataset_refs=("hidden-world",),
        readable_dataset_refs=("hidden-world",),
        capability_names=("run_analysis", "run_authored_development_trial"),
    )
    store = InMemoryRuntimeStore()
    initialized = ResearchRuntimeInitializer(store).initialize(
        published.task,
        environment,
        request_id="initialize-stateless-surface-researcher",
    )
    left = tuple(-1.0 if day % 2 else 1.0 for day in range(1, 25))
    right = tuple(-1.0 if day % 4 < 2 else 1.0 for day in range(1, 25))
    outcome = tuple(3.0 * a * b for a, b in zip(left, right, strict=True))
    view = AuthorizedDataView(
        view_id="development-view",
        dataset_ref="hidden-world",
        environment_ref=environment.snapshot_ref,
        fields={"x1": left, "x2": right, "y": outcome, "future_poison": outcome},
    )
    harness = AnalysisHarness(
        views={view.view_id: view},
        policy=CapabilityPolicy(
            session_id=initialized.session.session_id,
            environment_ref=environment.snapshot_ref,
            allowed_fields_by_view={view.view_id: frozenset({"x1", "x2", "y"})},
        ),
        artifacts=ArtifactStore(),
    )
    coordinator = RuntimeInvestigationCoordinator()
    router = ActionRouter(
        store,
        DatasetRepository(()),
        analysis_harnesses={initialized.session.session_id: harness},
        investigations=coordinator,
    )
    registration = router.register_investigation(
        _request(
            catalog,
            task_ref=published.task.task_id,
            max_trials=2,
        ),
        session_id=initialized.session.session_id,
    )
    provider = _StatelessSurfaceResearcher()
    context = ContextBuilder(store)
    runtime = AutonomousResearchRuntime(
        store,
        provider,
        context,
        router,
        CommitCoordinator(store),
    )

    baseline = runtime.advance_one_turn(initialized.session.session_id)
    diagnostic = runtime.advance_one_turn(initialized.session.session_id)
    revised = runtime.advance_one_turn(initialized.session.session_id)

    assert not hasattr(provider, "__dict__")
    assert baseline.observation is not None
    assert baseline.observation.payload["disposition"] == "revise"
    assert diagnostic.observation is not None
    assert diagnostic.observation.status is ObservationStatus.SUCCEEDED
    diagnostic_details = cast("Mapping[str, object]", diagnostic.observation.payload["details"])
    assert diagnostic_details["best_feature"] == "interaction"
    assert diagnostic.observation.provenance is not None
    assert tuple(access.field_id for access in diagnostic.observation.provenance.accesses) == (
        "x1",
        "x2",
        "y",
    )
    assert revised.observation is not None
    assert revised.observation.payload["disposition"] == "credible"
    candidate_id = revised.observation.payload["candidate_id"]
    assert isinstance(candidate_id, str)
    candidate = coordinator.resolve_candidate(candidate_id)
    assert candidate.manifest.feature_names == ("interaction",)
    assert candidate.manifest.predictor_fields == (
        catalog.datasets[0].schema.field_ref("x1"),
        catalog.datasets[0].schema.field_ref("x2"),
    )
    assert candidate.parent_trial_ids == (baseline.observation.payload["trial_id"],)
    assert candidate.manifest.evidence_refs == (
        f"observation:{initialized.session.session_id}:register-investigation:{registration.registration_id}",
        diagnostic.observation.observation_id,
    )
    registration_observation = context.build_current_context(
        initialized.session.session_id
    ).working_observations[0]
    surfaces = cast(
        "tuple[Mapping[str, object], ...]",
        registration_observation.payload["analysis_surfaces"],
    )
    surface = surfaces[0]
    assert surface["field_ids"] == ("x1", "x2", "y")
    assert "future_poison" not in cast("tuple[str, ...]", surface["field_ids"])
    exact_refs: dict[str, Mapping[str, object]] = {}
    field_definitions = cast(
        "tuple[Mapping[str, object], ...]",
        registration_observation.payload["field_definitions"],
    )
    for item in field_definitions:
        field_ref = cast("Mapping[str, object]", item["field_ref"])
        exact_refs[cast("str", field_ref["field_id"])] = field_ref
    assert exact_refs["x1"] == {
        "dataset_id": "hidden-world",
        "schema_version": "v1",
        "field_id": "x1",
        "environment_id": "development-world",
    }


def _manifest_json(manifest: AuthoredCandidateManifest) -> dict[str, object]:
    return {
        "question_id": manifest.question_id,
        "environment_id": manifest.environment_id,
        "predictor_fields": [_field_json(item) for item in manifest.predictor_fields],
        "outcome_field": _field_json(manifest.outcome_field),
        "horizon": {
            "kind": "elapsed",
            "elapsed_microseconds": manifest.horizon.elapsed_microseconds,
        },
        "minimum_outcome_points": manifest.minimum_outcome_points,
        "population_dimensions": [list(item) for item in manifest.population_dimensions],
        "feature_names": list(manifest.feature_names),
        "missing_value_policy": manifest.missing_value_policy,
        "evidence_refs": list(manifest.evidence_refs),
        "provenance_refs": list(manifest.provenance_refs),
    }


def _field_json(field: FieldRef) -> dict[str, object]:
    return {
        "dataset_id": field.dataset_id,
        "schema_version": field.schema_version,
        "field_id": field.field_id,
        "environment_id": field.environment_id,
    }
