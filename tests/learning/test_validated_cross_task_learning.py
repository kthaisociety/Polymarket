"""Causal and adversarial evidence for validated cross-task learning."""

# ruff: noqa: D103, PLR0913

from __future__ import annotations

from dataclasses import replace

import pytest

from research_agent.data_foundation import (
    CalendarUnit,
    MonthEndPolicy,
    OffsetAnchor,
    TemporalOffset,
    TimezonePolicy,
)
from research_agent.learning import (
    ApplicabilityScope,
    CandidateLesson,
    EvidenceProtection,
    EvidenceSourceCapability,
    EvidenceSourcePolicy,
    EvidenceStatus,
    HistoricalEvidenceRegistrar,
    HistoricalEvidenceSelector,
    HistoryEvidence,
    HistoryReflector,
    KnowledgeEnvironment,
    KnowledgePublisherPolicy,
    KnowledgeQuery,
    KnowledgeRetrieval,
    LearningAuthorityError,
    LearningAuthorityRegistry,
    LearningConflictError,
    LearningContextProjector,
    LearningLedger,
    LearningReaderPolicy,
    LearningRepository,
    LessonDecisionOutcome,
    LessonKind,
    LessonPromoter,
    LessonProposer,
    LessonValidationDecision,
    LessonValidationStandard,
    LessonValidator,
    LessonValidatorCapability,
    ReflectionEvidenceSelection,
    RejectedLesson,
    ValidatedLearning,
    identified,
)
from research_agent.runtime.models import ContextPacket, EpisodeStatus

TASK_IDS = (
    "origin-task",
    "origin",
    "independent-1",
    "independent-2",
    "independent-3",
    "independent-4",
    "future-task",
    "different-task",
)


def _standard() -> LessonValidationStandard:
    item = identified(
        LessonValidationStandard,
        version=1,
        minimum_independent_evidence=2,
        minimum_independent_tasks=2,
        require_no_unresolved_contrary_evidence=True,
    )
    assert isinstance(item, LessonValidationStandard)
    return item


def _scope() -> ApplicabilityScope:
    return ApplicabilityScope(
        task_kinds=("time-series-research",),
        environment_refs=("env@1",),
        subject_tags=("claims",),
    )


def _packet(*, task_id: str = "future-task", target_field_id: str = "claims") -> ContextPacket:
    return ContextPacket(
        packet_id="base-packet",
        session_id="future-session",
        task_id=task_id,
        task_version=1,
        state_id="state-0",
        state_version=0,
        episode_id="episode-0",
        environment_ref="env@1",
        mission="Discover a lawful predictive relationship.",
        constraints=(),
        target_field_id=target_field_id,
        forecast_horizon=TemporalOffset.calendar(
            count=3,
            unit=CalendarUnit.MONTH,
            anchor=OffsetAnchor.EXACT_INPUT,
            month_end_policy=MonthEndPolicy.CLAMP,
            timezone_name="UTC",
            timezone_policy=TimezonePolicy.WALL_CLOCK_REJECT_TRANSITION,
        ),
        unresolved_semantics=(),
        committed_understanding=(),
        episode_objective="Find the next discriminating analysis.",
        episode_status=EpisodeStatus.ACTIVE,
        active_question="Which diagnostic should run first?",
        current_plan=(),
        unresolved_questions=(),
        temporary_interpretations=(),
        working_observations=(),
        total_observation_count=0,
        omitted_observation_count=0,
        checkpoint_ref=None,
        omitted_observations_ref=None,
        permitted_dataset_refs=("dataset:v1",),
        available_actions=("run_analysis",),
        protected_exposure_refs=(),
        protected_resource_refs=(),
        warnings=(),
    )


class _LearningFixture:
    def __init__(self) -> None:
        self.ledger = LearningLedger()
        self.authorities = LearningAuthorityRegistry(
            source_policies=(
                EvidenceSourcePolicy(
                    "runtime-ledger", ("env@1",), ("time-series-research",), ("claims",)
                ),
                EvidenceSourcePolicy(
                    "independent-evaluator",
                    ("env@1", "env@2"),
                    ("time-series-research",),
                    ("claims",),
                ),
                EvidenceSourcePolicy(
                    "protected-ledger",
                    ("env@1",),
                    ("time-series-research",),
                    ("claims",),
                    EvidenceProtection.PROTECTED,
                ),
            ),
            validator_authority_ids=("lesson-board", "researcher-a"),
            reader_policies=(
                LearningReaderPolicy(
                    "researcher-a",
                    ("runtime-ledger", "protected-ledger"),
                    TASK_IDS,
                    ("time-series-research",),
                    ("env@1",),
                    ("claims",),
                ),
                LearningReaderPolicy(
                    "future-researcher",
                    ("runtime-ledger", "independent-evaluator"),
                    ("future-task", "different-task"),
                    ("time-series-research",),
                    ("env@1",),
                    ("claims", "weather"),
                ),
                LearningReaderPolicy(
                    "other",
                    ("runtime-ledger",),
                    ("future-task",),
                    ("time-series-research",),
                    ("env@1",),
                    ("claims",),
                ),
            ),
            publisher_policies=(
                KnowledgePublisherPolicy(
                    "knowledge-curator",
                    ("future-researcher",),
                    ("time-series-research",),
                    ("env@1",),
                    ("claims",),
                ),
            ),
        )
        self.repository = LearningRepository(authorities=self.authorities)
        self.registrar = HistoricalEvidenceRegistrar(
            self.repository, self.ledger, authorities=self.authorities
        )
        self.selector = HistoricalEvidenceSelector(
            self.repository, self.ledger, authorities=self.authorities
        )
        self.reflector = HistoryReflector(
            self.repository,
            self.ledger,
            selector=self.selector,
        )
        self.proposer = LessonProposer(self.repository, self.ledger)
        self.standard = _standard()
        self.validator = LessonValidator(
            self.repository,
            self.ledger,
            authorities=self.authorities,
            standards=(self.standard,),
        )
        self.promoter = LessonPromoter(self.repository, self.ledger)
        self.knowledge = KnowledgeEnvironment(
            self.repository, self.ledger, authorities=self.authorities
        )
        self.reflector_reader = self.authorities.reader("researcher-a")
        self.future_reader = self.authorities.reader("future-researcher")
        self.publisher = self.authorities.publisher("knowledge-curator")
        self.lesson_board = self.authorities.validator("lesson-board")

    def evidence(
        self,
        name: str,
        task: str,
        *,
        status: EvidenceStatus = EvidenceStatus.SUCCEEDED,
        source: str = "runtime-ledger",
        environment_ref: str = "env@1",
        current: bool = True,
    ) -> HistoryEvidence:
        return self.registrar.register(
            source=self.authorities.source(source),
            task_id=task,
            task_kind="time-series-research",
            environment_ref=environment_ref,
            subject_tags=("claims",),
            status=status,
            summary=name,
            source_refs=(f"record:{name}",),
            current=current,
        )

    def candidate(self, *, max_evidence: int = 64) -> CandidateLesson:
        success = self.evidence("development success", "origin-task")
        failure = self.evidence("failed shortcut", "origin-task", status=EvidenceStatus.FAILED)
        selection = self.selector.select(
            reader=self.reflector_reader,
            scope=_scope(),
            task_ids=("origin-task",),
            max_evidence=max_evidence,
        )
        reflection = self.reflector.reflect(
            selection=selection,
            protocol_id="reflection-v1",
            claims=("Run a diagnostic before selecting a feature.",),
            uncertainties=("The failed shortcut may not generalize.",),
        )
        selected_ids = {item.evidence_id for item in reflection.evidence}
        return self.proposer.propose(
            reflection=reflection,
            proposer_id="researcher-a",
            kind=LessonKind.SKILL,
            content="Run a missingness and availability diagnostic before feature selection.",
            scope=_scope(),
            supporting_evidence_ids=(success.evidence_id,)
            if success.evidence_id in selected_ids
            else (),
            contrary_evidence_ids=(failure.evidence_id,)
            if failure.evidence_id in selected_ids
            else (),
            caveats=("Applies only to claims time-series tasks in env@1.",),
        )

    def independent(
        self,
        *,
        statuses: tuple[EvidenceStatus, EvidenceStatus] = (
            EvidenceStatus.SUCCEEDED,
            EvidenceStatus.SUCCEEDED,
        ),
        environment_ref: str = "env@1",
        suffix: str = "",
    ) -> tuple[HistoryEvidence, HistoryEvidence]:
        tasks = (
            ("independent-1", "independent-2")
            if not suffix
            else (
                "independent-3",
                "independent-4",
            )
        )
        return tuple(
            self.evidence(
                f"replication {index}{suffix}",
                task,
                source="independent-evaluator",
                status=status,
                environment_ref=environment_ref,
            )
            for index, (task, status) in enumerate(zip(tasks, statuses, strict=True), 1)
        )  # type: ignore[return-value]

    def decide(
        self,
        *,
        statuses: tuple[EvidenceStatus, EvidenceStatus] = (
            EvidenceStatus.SUCCEEDED,
            EvidenceStatus.SUCCEEDED,
        ),
    ) -> tuple[CandidateLesson, LessonValidationDecision]:
        candidate = self.candidate()
        decision = self.validator.validate(
            candidate=candidate,
            standard_id=self.standard.standard_id,
            validator=self.lesson_board,
            independent_evidence=self.independent(statuses=statuses),
        )
        return candidate, decision

    def publish(self, learning: ValidatedLearning) -> None:
        self.knowledge.publish(
            learning=learning,
            publisher=self.publisher,
            permitted_actor_ids=("future-researcher",),
        )

    def query(
        self, *, actor_id: str = "future-researcher", subject: str = "claims"
    ) -> KnowledgeRetrieval:
        reader = self.authorities.reader(actor_id)
        return self.knowledge.retrieve(
            KnowledgeQuery(
                actor_id=actor_id,
                task_id="future-task",
                task_kind="time-series-research",
                environment_ref="env@1",
                subject_tags=(subject,),
            ),
            reader=reader,
        )


def _policy(packet: ContextPacket) -> str:
    contents = tuple(
        str(item.payload.get("content", ""))
        for item in packet.working_observations
        if item.observation_type == "validated_learning"
    )
    return (
        "run-availability-diagnostic"
        if any("availability diagnostic" in item for item in contents)
        else "baseline-feature-search"
    )


def test_validated_skill_substance_causally_changes_future_packet_only_policy() -> None:
    fixture = _LearningFixture()
    candidate, decision = fixture.decide()
    promoted = fixture.promoter.apply(candidate=candidate, decision=decision)
    assert isinstance(promoted, ValidatedLearning)
    fixture.publish(promoted)
    retrieval = fixture.query()
    projected = LearningContextProjector(fixture.knowledge, reader=fixture.future_reader).project(
        _packet(), retrieval
    )
    assert _policy(_packet()) == "baseline-feature-search"
    assert _policy(projected) == "run-availability-diagnostic"
    assert projected.working_observations[-1].payload["content"] == promoted.content
    assert projected.working_observations[-1].payload["caveats"] == promoted.caveats
    assert projected.working_observations[-1].payload["provenance_refs"]


def test_copied_source_and_validator_capabilities_have_no_authority() -> None:
    fixture = _LearningFixture()
    source = fixture.authorities.source("runtime-ledger")
    copied_source = identified(EvidenceSourceCapability, policy=source.policy)
    assert isinstance(copied_source, EvidenceSourceCapability)
    with pytest.raises(LearningAuthorityError, match="not issued"):
        fixture.registrar.register(
            source=copied_source,
            task_id="origin",
            task_kind="time-series-research",
            environment_ref="env@1",
            subject_tags=("claims",),
            status=EvidenceStatus.SUCCEEDED,
            summary="invented",
            source_refs=("fake:1",),
        )

    candidate = fixture.candidate()
    copied_validator = identified(
        LessonValidatorCapability, authority_id=fixture.lesson_board.authority_id
    )
    assert isinstance(copied_validator, LessonValidatorCapability)
    with pytest.raises(LearningAuthorityError, match="not issued"):
        fixture.validator.validate(
            candidate=candidate,
            standard_id=fixture.standard.standard_id,
            validator=copied_validator,
            independent_evidence=fixture.independent(),
        )

    foreign = LearningAuthorityRegistry(
        source_policies=(
            EvidenceSourcePolicy(
                "runtime-ledger", ("env@1",), ("time-series-research",), ("claims",)
            ),
        ),
        validator_authority_ids=("lesson-board",),
        reader_policies=(
            LearningReaderPolicy(
                "researcher-a",
                ("runtime-ledger",),
                ("origin",),
                ("time-series-research",),
                ("env@1",),
                ("claims",),
            ),
        ),
        publisher_policies=(
            KnowledgePublisherPolicy(
                "knowledge-curator",
                ("future-researcher",),
                ("time-series-research",),
                ("env@1",),
                ("claims",),
            ),
        ),
    )
    with pytest.raises(LearningAuthorityError, match="another authority root"):
        HistoricalEvidenceRegistrar(
            fixture.repository,
            fixture.ledger,
            authorities=foreign,
        )


def test_protected_history_and_winner_only_selection_fail_closed() -> None:
    fixture = _LearningFixture()
    fixture.evidence("winner", "origin")
    failure = fixture.evidence("known failure", "origin", status=EvidenceStatus.FAILED)
    complete = fixture.selector.select(
        reader=fixture.reflector_reader, scope=_scope(), task_ids=("origin",)
    )
    assert {item.status for item in complete.evidence} == {
        EvidenceStatus.SUCCEEDED,
        EvidenceStatus.FAILED,
    }
    bounded = fixture.selector.select(
        reader=fixture.reflector_reader,
        scope=_scope(),
        task_ids=("origin",),
        max_evidence=1,
    )
    assert tuple(item.evidence_id for item in bounded.omissions) == (failure.evidence_id,)
    assert bounded.omissions[0].status is EvidenceStatus.FAILED
    fixture.evidence("holdout truth", "origin", source="protected-ledger")
    with pytest.raises(LearningAuthorityError, match="Protected"):
        fixture.selector.select(
            reader=fixture.reflector_reader, scope=_scope(), task_ids=("origin",)
        )


def test_reflection_rejects_a_selection_made_incomplete_by_later_evidence() -> None:
    fixture = _LearningFixture()
    fixture.evidence("winner", "origin")
    stale = fixture.selector.select(
        reader=fixture.reflector_reader,
        scope=_scope(),
        task_ids=("origin",),
    )
    fixture.evidence("later registered failure", "origin", status=EvidenceStatus.FAILED)
    with pytest.raises(LearningAuthorityError, match="stale or incomplete"):
        fixture.reflector.reflect(
            selection=stale,
            protocol_id="reflection-v1",
            claims=("winner-only claim",),
            uncertainties=("none",),
        )


def test_forged_reflection_selection_is_rejected() -> None:
    fixture = _LearningFixture()
    evidence = fixture.evidence("registered", "origin")
    forged = identified(
        ReflectionEvidenceSelection,
        reader_capability_id=fixture.reflector_reader.capability_id,
        reader_actor_id="researcher-a",
        scope=_scope(),
        task_ids=("origin",),
        max_evidence=64,
        evidence=(evidence,),
        omissions=(),
    )
    assert isinstance(forged, ReflectionEvidenceSelection)
    with pytest.raises(LearningAuthorityError, match="issued evidence selection"):
        fixture.reflector.reflect(
            selection=forged,
            protocol_id="reflection-v1",
            claims=("claim",),
            uncertainties=("uncertain",),
        )


def test_candidate_scope_cannot_exceed_reflection_evidence_scope() -> None:
    fixture = _LearningFixture()
    evidence = fixture.evidence("support", "origin")
    selection = fixture.selector.select(
        reader=fixture.reflector_reader, scope=_scope(), task_ids=("origin",)
    )
    reflection = fixture.reflector.reflect(
        selection=selection,
        protocol_id="reflection-v1",
        claims=("claim",),
        uncertainties=("uncertain",),
    )
    wider = ApplicabilityScope(("time-series-research",), ("env@1", "env@2"), ("claims",))
    with pytest.raises(LearningAuthorityError, match="exceeds"):
        fixture.proposer.propose(
            reflection=reflection,
            proposer_id="researcher-a",
            kind=LessonKind.MEMORY,
            content="scope widened",
            scope=wider,
            supporting_evidence_ids=(evidence.evidence_id,),
            contrary_evidence_ids=(),
            caveats=("caveat",),
        )

    fixture.evidence("claims-only future evidence", "future-task")
    unsupported_subject_scope = ApplicabilityScope(
        ("time-series-research",),
        ("env@1",),
        ("claims", "weather"),
    )
    with pytest.raises(LearningAuthorityError, match="not represented"):
        fixture.selector.select(
            reader=fixture.future_reader,
            scope=unsupported_subject_scope,
            task_ids=("future-task",),
        )


@pytest.mark.parametrize(
    "status", [EvidenceStatus.UNSUPPORTED, EvidenceStatus.INVALID, EvidenceStatus.FAILED]
)
def test_nonaffirmative_or_wrong_environment_replication_cannot_promote(
    status: EvidenceStatus,
) -> None:
    fixture = _LearningFixture()
    candidate = fixture.candidate()
    decision = fixture.validator.validate(
        candidate=candidate,
        standard_id=fixture.standard.standard_id,
        validator=fixture.lesson_board,
        independent_evidence=fixture.independent(statuses=(status, status)),
    )
    assert decision.outcome is LessonDecisionOutcome.REJECT
    wrong_environment = fixture.validator.validate(
        candidate=candidate,
        standard_id=fixture.standard.standard_id,
        validator=fixture.lesson_board,
        independent_evidence=fixture.independent(environment_ref="env@2", suffix=" env2"),
    )
    assert wrong_environment.outcome is LessonDecisionOutcome.REJECT


def test_self_validation_overlap_and_self_rehashed_decision_fail_closed() -> None:
    fixture = _LearningFixture()
    candidate = fixture.candidate()
    original = fixture.repository.evidence(candidate.supporting_evidence_ids[0])
    assert original is not None
    with pytest.raises(LearningAuthorityError, match="cannot independently approve"):
        fixture.validator.validate(
            candidate=candidate,
            standard_id=fixture.standard.standard_id,
            validator=fixture.authorities.validator("researcher-a"),
            independent_evidence=(original,),
        )
    forged = identified(
        LessonValidationDecision,
        candidate_id=candidate.candidate_id,
        standard_id=fixture.standard.standard_id,
        validator_authority_id="lesson-board",
        outcome=LessonDecisionOutcome.PROMOTE,
        independent_evidence_ids=("invented-1", "invented-2"),
        independent_task_ids=("new-1", "new-2"),
        reasons=("self-rehashed",),
        scope=candidate.scope,
    )
    assert isinstance(forged, LessonValidationDecision)
    with pytest.raises(LearningAuthorityError, match="authority-issued"):
        fixture.promoter.apply(candidate=candidate, decision=forged)


def test_rejection_is_preserved_and_cannot_enter_knowledge() -> None:
    fixture = _LearningFixture()
    candidate, decision = fixture.decide(
        statuses=(EvidenceStatus.SUCCEEDED, EvidenceStatus.CONTRARY)
    )
    rejection = fixture.promoter.apply(candidate=candidate, decision=decision)
    assert isinstance(rejection, RejectedLesson)
    assert rejection in fixture.repository.rejections()
    with pytest.raises(LearningAuthorityError, match="validated learning"):
        fixture.knowledge.publish(
            learning=rejection,
            publisher=fixture.publisher,
            permitted_actor_ids=("future-researcher",),
        )


def test_scope_permission_context_binding_and_forged_retrieval_fail_closed() -> None:
    fixture = _LearningFixture()
    candidate, decision = fixture.decide()
    promoted = fixture.promoter.apply(candidate=candidate, decision=decision)
    assert isinstance(promoted, ValidatedLearning)
    fixture.publish(promoted)
    assert fixture.query(actor_id="other").entries == ()
    assert fixture.query(subject="weather").entries == ()
    valid = fixture.query()
    projector = LearningContextProjector(fixture.knowledge, reader=fixture.future_reader)
    with pytest.raises(LearningAuthorityError, match="future context"):
        projector.project(_packet(task_id="different-task"), valid)
    with pytest.raises(LearningAuthorityError, match="subject"):
        projector.project(_packet(target_field_id="weather"), valid)
    forged = identified(
        KnowledgeRetrieval,
        query=replace(valid.query, task_id="different-task"),
        entries=valid.entries,
        omitted_count=0,
    )
    assert isinstance(forged, KnowledgeRetrieval)
    with pytest.raises(LearningAuthorityError, match="issued retrieval"):
        projector.project(_packet(task_id="different-task"), forged)


def _revised(
    fixture: _LearningFixture,
    candidate: CandidateLesson,
    label: str,
) -> tuple[CandidateLesson, LessonValidationDecision]:
    reflection = fixture.repository.reflection(candidate.reflection_id)
    assert reflection is not None
    revised = fixture.proposer.propose(
        reflection=reflection,
        proposer_id=candidate.proposer_id,
        kind=candidate.kind,
        content=f"{candidate.content} Revision {label}.",
        scope=candidate.scope,
        supporting_evidence_ids=candidate.supporting_evidence_ids,
        contrary_evidence_ids=candidate.contrary_evidence_ids,
        caveats=(f"Caveat {label}",),
        parent_candidate_ids=(candidate.candidate_id,),
    )
    revised_decision = fixture.validator.validate(
        candidate=revised,
        standard_id=fixture.standard.standard_id,
        validator=fixture.lesson_board,
        independent_evidence=fixture.independent(suffix=f" {label}"),
    )
    return revised, revised_decision


def test_superseded_retrieval_cannot_be_projected_and_retry_is_idempotent() -> None:
    fixture = _LearningFixture()
    candidate, decision = fixture.decide()
    first = fixture.promoter.apply(candidate=candidate, decision=decision)
    assert isinstance(first, ValidatedLearning)
    fixture.publish(first)
    stale = fixture.query()
    revised, revised_decision = _revised(fixture, candidate, "new")
    second = fixture.promoter.apply(
        candidate=revised,
        decision=revised_decision,
        supersedes_learning_id=first.learning_id,
    )
    assert isinstance(second, ValidatedLearning)
    fixture.publish(second)
    projector = LearningContextProjector(fixture.knowledge, reader=fixture.future_reader)
    with pytest.raises(LearningAuthorityError, match="stale"):
        projector.project(_packet(), stale)
    current = fixture.query()
    once = projector.project(_packet(), current)
    assert projector.project(once, current) == once


def test_one_decision_has_one_effect_and_one_learning_has_one_successor() -> None:
    fixture = _LearningFixture()
    candidate, decision = fixture.decide()
    first = fixture.promoter.apply(candidate=candidate, decision=decision)
    assert isinstance(first, ValidatedLearning)
    assert fixture.promoter.apply(candidate=candidate, decision=decision) == first
    with pytest.raises(LearningConflictError, match="lineage"):
        fixture.promoter.apply(
            candidate=candidate,
            decision=decision,
            supersedes_learning_id=first.learning_id,
        )
    first_revision = _revised(fixture, candidate, "A")
    second_revision = _revised(fixture, candidate, "B")
    accepted = fixture.promoter.apply(
        candidate=first_revision[0],
        decision=first_revision[1],
        supersedes_learning_id=first.learning_id,
    )
    assert isinstance(accepted, ValidatedLearning)
    with pytest.raises(LearningConflictError, match="different successor"):
        fixture.promoter.apply(
            candidate=second_revision[0],
            decision=second_revision[1],
            supersedes_learning_id=first.learning_id,
        )


def test_publication_retry_cannot_change_or_broaden_permissions() -> None:
    fixture = _LearningFixture()
    candidate, decision = fixture.decide()
    promoted = fixture.promoter.apply(candidate=candidate, decision=decision)
    assert isinstance(promoted, ValidatedLearning)
    fixture.publish(promoted)
    with pytest.raises(LearningConflictError, match="changed reader permissions"):
        fixture.knowledge.publish(
            learning=promoted,
            publisher=fixture.publisher,
            permitted_actor_ids=(),
        )
    with pytest.raises(LearningAuthorityError, match="exceeds publisher"):
        fixture.knowledge.publish(
            learning=promoted,
            publisher=fixture.publisher,
            permitted_actor_ids=("unauthorized-actor",),
        )


def test_repository_resolution_is_read_only_and_identity_cannot_silently_change() -> None:
    fixture = _LearningFixture()
    assert not hasattr(fixture.repository, "validated")
    assert not hasattr(fixture.repository, "decisions")
    candidate, decision = fixture.decide()
    learning = fixture.promoter.apply(candidate=candidate, decision=decision)
    assert isinstance(learning, ValidatedLearning)
    with pytest.raises(ValueError, match="identity"):
        replace(learning, content="silently changed lesson")
