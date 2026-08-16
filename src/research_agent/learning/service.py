"""Authority-bearing services for the slow cross-task learning loop."""

# ruff: noqa: C405, C901, D107, EM101, PLR0912, PLR0913, S101, SLF001, TRY003
# pyright: reportPrivateUsage=false

from __future__ import annotations

from dataclasses import replace
from threading import RLock
from typing import TypeVar

from research_agent.learning.models import (
    ApplicabilityScope,
    CandidateLesson,
    EvidenceOmission,
    EvidenceSourceCapability,
    EvidenceSourcePolicy,
    EvidenceStatus,
    HistoryEvidence,
    KnowledgeEntry,
    KnowledgeEntryStatus,
    KnowledgePublisherCapability,
    KnowledgePublisherPolicy,
    KnowledgeQuery,
    KnowledgeRetrieval,
    LearningLedgerEntry,
    LearningReaderCapability,
    LearningReaderPolicy,
    LessonDecisionOutcome,
    LessonKind,
    LessonValidationDecision,
    LessonValidationStandard,
    LessonValidatorCapability,
    Reflection,
    ReflectionEvidenceSelection,
    RejectedLesson,
    ValidatedLearning,
    identified,
)
from research_agent.runtime._canonical import content_digest
from research_agent.runtime.models import (
    ContextObservation,
    ContextPacket,
    ObservationStatus,
    Recoverability,
)


class LearningAuthorityError(PermissionError):
    """A caller attempted to cross an unissued learning boundary."""


class LearningConflictError(RuntimeError):
    """One immutable identity was reused with changed meaning."""


LearningRecord = TypeVar("LearningRecord")


class LearningAuthorityRegistry:
    """Trusted bootstrap issuer for in-memory learning capabilities."""

    def __init__(
        self,
        *,
        source_policies: tuple[EvidenceSourcePolicy, ...],
        validator_authority_ids: tuple[str, ...],
        reader_policies: tuple[LearningReaderPolicy, ...],
        publisher_policies: tuple[KnowledgePublisherPolicy, ...],
    ) -> None:
        if not all((source_policies, validator_authority_ids, reader_policies, publisher_policies)):
            raise ValueError("Learning authority configuration must be complete.")
        self._sources: dict[str, EvidenceSourceCapability] = {}
        for policy in source_policies:
            if policy.source_authority_id in self._sources:
                raise ValueError("Learning authority identifiers must be unique.")
            capability = identified(EvidenceSourceCapability, policy=policy)
            assert isinstance(capability, EvidenceSourceCapability)
            self._sources[policy.source_authority_id] = capability
        self._validators: dict[str, LessonValidatorCapability] = {}
        for authority_id in validator_authority_ids:
            if not authority_id or authority_id in self._validators:
                raise ValueError("Learning authority identifiers must be unique and explicit.")
            capability = identified(LessonValidatorCapability, authority_id=authority_id)
            assert isinstance(capability, LessonValidatorCapability)
            self._validators[authority_id] = capability
        self._readers: dict[str, LearningReaderCapability] = {}
        for policy in reader_policies:
            if policy.actor_id in self._readers:
                raise ValueError("Learning authority identifiers must be unique.")
            capability = identified(LearningReaderCapability, policy=policy)
            assert isinstance(capability, LearningReaderCapability)
            self._readers[policy.actor_id] = capability
        self._publishers: dict[str, KnowledgePublisherCapability] = {}
        for policy in publisher_policies:
            if policy.authority_id in self._publishers:
                raise ValueError("Learning authority identifiers must be unique.")
            capability = identified(KnowledgePublisherCapability, policy=policy)
            assert isinstance(capability, KnowledgePublisherCapability)
            self._publishers[policy.authority_id] = capability
        source_ids = set(self._sources)
        if any(
            not set(capability.policy.readable_source_ids).issubset(source_ids)
            for capability in self._readers.values()
        ):
            raise ValueError("Learning reader policy names an unknown evidence source.")

    def source(self, authority_id: str) -> EvidenceSourceCapability:
        """Return one configured source capability to trusted composition code."""
        capability = self._sources.get(authority_id)
        if not isinstance(capability, EvidenceSourceCapability):
            raise LearningAuthorityError("Evidence source authority is not configured.")
        return capability

    def validator(self, authority_id: str) -> LessonValidatorCapability:
        """Return one configured validation capability to its trusted owner."""
        capability = self._validators.get(authority_id)
        if not isinstance(capability, LessonValidatorCapability):
            raise LearningAuthorityError("Lesson validator authority is not configured.")
        return capability

    def reader(self, actor_id: str) -> LearningReaderCapability:
        """Return one configured bounded reader capability."""
        capability = self._readers.get(actor_id)
        if not isinstance(capability, LearningReaderCapability):
            raise LearningAuthorityError("Learning reader authority is not configured.")
        return capability

    def publisher(self, authority_id: str) -> KnowledgePublisherCapability:
        """Return one configured bounded publication capability."""
        capability = self._publishers.get(authority_id)
        if not isinstance(capability, KnowledgePublisherCapability):
            raise LearningAuthorityError("Knowledge publisher authority is not configured.")
        return capability

    def require_source(self, capability: EvidenceSourceCapability) -> None:
        """Reject a copied or self-rehashed source capability."""
        if self._sources.get(capability.policy.source_authority_id) is not capability:
            raise LearningAuthorityError("Evidence source capability was not issued here.")

    def require_validator(self, capability: LessonValidatorCapability) -> None:
        """Reject a copied or self-rehashed validator capability."""
        if self._validators.get(capability.authority_id) is not capability:
            raise LearningAuthorityError("Validator capability was not issued here.")

    def require_reader(self, capability: LearningReaderCapability) -> None:
        """Reject a copied or self-rehashed reader capability."""
        if self._readers.get(capability.policy.actor_id) is not capability:
            raise LearningAuthorityError("Learning reader capability was not issued here.")

    def require_publisher(self, capability: KnowledgePublisherCapability) -> None:
        """Reject a copied or self-rehashed publisher capability."""
        if self._publishers.get(capability.policy.authority_id) is not capability:
            raise LearningAuthorityError("Knowledge publisher capability was not issued here.")


class LearningLedger:
    """Append-only audit history for positive and negative learning."""

    def __init__(self) -> None:
        self._entries: tuple[LearningLedgerEntry, ...] = ()
        self._by_id: dict[str, LearningLedgerEntry] = {}
        self._by_effect: dict[tuple[str, str, tuple[str, ...]], LearningLedgerEntry] = {}
        self._lock = RLock()

    def append(
        self,
        *,
        event_type: str,
        subject_id: str,
        detail_refs: tuple[str, ...],
    ) -> LearningLedgerEntry:
        """Append or return an exact idempotent audit event."""
        with self._lock:
            effect = (event_type, subject_id, detail_refs)
            prior = self._by_effect.get(effect)
            if prior is not None:
                return prior
            ordinal = len(self._entries) + 1
            entry = identified(
                LearningLedgerEntry,
                event_type=event_type,
                subject_id=subject_id,
                detail_refs=detail_refs,
                ordinal=ordinal,
            )
            assert isinstance(entry, LearningLedgerEntry)
            existing = self._by_id.get(entry.entry_id)
            if existing is not None:
                if existing != entry:
                    raise LearningConflictError("Learning ledger identity conflict.")
                return existing
            self._entries += (entry,)
            self._by_id[entry.entry_id] = entry
            self._by_effect[effect] = entry
            return entry

    def entries(self) -> tuple[LearningLedgerEntry, ...]:
        """Return complete positive and negative history."""
        with self._lock:
            return self._entries


class LearningRepository:
    """Canonical issued objects; self-hashes alone never grant authority."""

    def __init__(self, *, authorities: LearningAuthorityRegistry) -> None:
        self._authorities = authorities
        self._reflections: dict[str, Reflection] = {}
        self._evidence: dict[str, HistoryEvidence] = {}
        self._selections: dict[str, ReflectionEvidenceSelection] = {}
        self._candidates: dict[str, CandidateLesson] = {}
        self._standards: dict[str, LessonValidationStandard] = {}
        self._decisions: dict[str, LessonValidationDecision] = {}
        self._validated: dict[str, ValidatedLearning] = {}
        self._rejected: dict[str, RejectedLesson] = {}
        self._effect_by_decision: dict[str, ValidatedLearning | RejectedLesson] = {}
        self._successor_by_learning: dict[str, str] = {}
        self._lock = RLock()

    def require_authorities(self, authorities: LearningAuthorityRegistry) -> None:
        """Prevent a caller from mounting a newly configured issuer over this repository."""
        if self._authorities is not authorities:
            raise LearningAuthorityError("Learning repository is bound to another authority root.")

    def _admit(
        self,
        store: dict[str, LearningRecord],
        key: str,
        item: LearningRecord,
    ) -> LearningRecord:
        """Publish one exact object to its canonical typed store."""
        with self._lock:
            existing = store.get(key)
            if existing is not None and existing != item:
                raise LearningConflictError("Learning identity was reused with changed semantics.")
            store[key] = item
            return item

    def evidence(self, evidence_id: str) -> HistoryEvidence | None:
        """Resolve canonical evidence without exposing registry mutation."""
        with self._lock:
            return self._evidence.get(evidence_id)

    def all_evidence(self) -> tuple[HistoryEvidence, ...]:
        """Return an immutable snapshot for authority-scoped selection."""
        with self._lock:
            return tuple(self._evidence.values())

    def selection(self, selection_id: str) -> ReflectionEvidenceSelection | None:
        """Resolve one authority-issued bounded reflection input."""
        with self._lock:
            return self._selections.get(selection_id)

    def reflection(self, reflection_id: str) -> Reflection | None:
        """Resolve one issued provisional reflection."""
        with self._lock:
            return self._reflections.get(reflection_id)

    def candidate(self, candidate_id: str) -> CandidateLesson | None:
        """Resolve one issued candidate."""
        with self._lock:
            return self._candidates.get(candidate_id)

    def standard(self, standard_id: str) -> LessonValidationStandard | None:
        """Resolve one predeclared validation standard."""
        with self._lock:
            return self._standards.get(standard_id)

    def decision(self, decision_id: str) -> LessonValidationDecision | None:
        """Resolve one authority-issued decision."""
        with self._lock:
            return self._decisions.get(decision_id)

    def learning(self, learning_id: str) -> ValidatedLearning | None:
        """Resolve one promoted learning object."""
        with self._lock:
            return self._validated.get(learning_id)

    def rejections(self) -> tuple[RejectedLesson, ...]:
        """Return append-only negative learning history."""
        with self._lock:
            return tuple(self._rejected.values())


class HistoricalEvidenceRegistrar:
    """Admit history only from configured source authorities."""

    def __init__(
        self,
        repository: LearningRepository,
        ledger: LearningLedger,
        *,
        authorities: LearningAuthorityRegistry,
    ) -> None:
        self._repository = repository
        self._ledger = ledger
        self._authorities = authorities
        repository.require_authorities(authorities)

    def register(
        self,
        *,
        source: EvidenceSourceCapability,
        task_id: str,
        task_kind: str,
        environment_ref: str,
        subject_tags: tuple[str, ...],
        status: EvidenceStatus,
        summary: str,
        source_refs: tuple[str, ...],
        current: bool = True,
    ) -> HistoryEvidence:
        """Issue a canonical evidence record from one configured source."""
        self._authorities.require_source(source)
        policy = source.policy
        if (
            environment_ref not in policy.allowed_environment_refs
            or task_kind not in policy.allowed_task_kinds
            or not set(subject_tags).issubset(policy.allowed_subject_tags)
        ):
            raise LearningAuthorityError("Historical evidence exceeds source capability scope.")
        evidence = identified(
            HistoryEvidence,
            source_authority_id=policy.source_authority_id,
            task_id=task_id,
            task_kind=task_kind,
            environment_ref=environment_ref,
            subject_tags=subject_tags,
            status=status,
            summary=summary,
            source_refs=source_refs,
            protection=policy.protection,
            current=current,
        )
        assert isinstance(evidence, HistoryEvidence)
        admitted = self._repository._admit(
            self._repository._evidence,
            evidence.evidence_id,
            evidence,
        )
        self._ledger.append(
            event_type="learning.history-evidence-registered",
            subject_id=evidence.evidence_id,
            detail_refs=evidence.source_refs,
        )
        return admitted


class HistoricalEvidenceSelector:
    """Issue complete bounded reflection inputs under reader capability."""

    def __init__(
        self,
        repository: LearningRepository,
        ledger: LearningLedger,
        *,
        authorities: LearningAuthorityRegistry,
    ) -> None:
        self._repository = repository
        self._ledger = ledger
        self._authorities = authorities
        repository.require_authorities(authorities)

    def select(
        self,
        *,
        reader: LearningReaderCapability,
        scope: ApplicabilityScope,
        task_ids: tuple[str, ...],
        max_evidence: int = 64,
    ) -> ReflectionEvidenceSelection:
        """Select all readable evidence in the declared boundary, with bounded omissions."""
        self._authorities.require_reader(reader)
        if max_evidence < 1:
            raise ValueError("Reflection evidence bound must be positive.")
        policy = reader.policy
        if (
            not set(task_ids).issubset(policy.allowed_task_ids)
            or not set(scope.task_kinds).issubset(policy.allowed_task_kinds)
            or not set(scope.environment_refs).issubset(policy.allowed_environment_refs)
            or not set(scope.subject_tags).issubset(policy.allowed_subject_tags)
        ):
            raise LearningAuthorityError("Reflection selection exceeds reader capability scope.")
        selection = self._build_selection(
            reader=reader,
            scope=scope,
            task_ids=task_ids,
            max_evidence=max_evidence,
        )
        admitted = self._repository._admit(
            self._repository._selections,
            selection.selection_id,
            selection,
        )
        self._ledger.append(
            event_type="learning.reflection-evidence-selected",
            subject_id=selection.selection_id,
            detail_refs=tuple(
                item.evidence_id for item in (*selection.evidence, *selection.omissions)
            ),
        )
        assert isinstance(admitted, ReflectionEvidenceSelection)
        return admitted

    def require_current(self, selection: ReflectionEvidenceSelection) -> None:
        """Reject a selection whose declared boundary now contains different evidence."""
        if self._repository.selection(selection.selection_id) != selection:
            raise LearningAuthorityError("Reflection requires an issued evidence selection.")
        reader = self._authorities.reader(selection.reader_actor_id)
        if reader.capability_id != selection.reader_capability_id:
            raise LearningAuthorityError("Reflection selection reader authority changed.")
        current = self._build_selection(
            reader=reader,
            scope=selection.scope,
            task_ids=selection.task_ids,
            max_evidence=selection.max_evidence,
        )
        if current != selection:
            raise LearningAuthorityError("Reflection evidence selection is stale or incomplete.")

    def _build_selection(
        self,
        *,
        reader: LearningReaderCapability,
        scope: ApplicabilityScope,
        task_ids: tuple[str, ...],
        max_evidence: int,
    ) -> ReflectionEvidenceSelection:
        policy = reader.policy
        eligible = tuple(
            sorted(
                (
                    item
                    for item in self._repository.all_evidence()
                    if item.source_authority_id in policy.readable_source_ids
                    and item.task_id in task_ids
                    and item.task_kind in scope.task_kinds
                    and item.environment_ref in scope.environment_refs
                    and bool(set(item.subject_tags).intersection(scope.subject_tags))
                ),
                key=lambda item: (
                    item.status is not EvidenceStatus.SUCCEEDED,
                    item.evidence_id,
                ),
            )
        )
        if any(item.protected for item in eligible):
            raise LearningAuthorityError("Protected evidence cannot enter reflection selection.")
        if not eligible:
            raise ValueError("Reflection selection found no evidence in its declared boundary.")
        if (
            not set(scope.environment_refs).issubset(item.environment_ref for item in eligible)
            or not set(scope.task_kinds).issubset(item.task_kind for item in eligible)
            or not set(scope.subject_tags).issubset(
                subject for item in eligible for subject in item.subject_tags
            )
        ):
            raise LearningAuthorityError(
                "Reflection scope contains applicability not represented by its evidence."
            )
        evidence = eligible[:max_evidence]
        omissions = tuple(
            EvidenceOmission(
                evidence_id=item.evidence_id,
                task_id=item.task_id,
                task_kind=item.task_kind,
                environment_ref=item.environment_ref,
                subject_tags=item.subject_tags,
                status=item.status,
                reason="bounded-context-omission",
            )
            for item in eligible[max_evidence:]
        )
        selection = identified(
            ReflectionEvidenceSelection,
            reader_capability_id=reader.capability_id,
            reader_actor_id=policy.actor_id,
            scope=scope,
            task_ids=task_ids,
            max_evidence=max_evidence,
            evidence=evidence,
            omissions=omissions,
        )
        assert isinstance(selection, ReflectionEvidenceSelection)
        return selection


class HistoryReflector:
    """Create provisional, source-complete reflection over permitted history."""

    def __init__(
        self,
        repository: LearningRepository,
        ledger: LearningLedger,
        *,
        selector: HistoricalEvidenceSelector,
    ) -> None:
        self._repository = repository
        self._ledger = ledger
        self._selector = selector

    def reflect(
        self,
        *,
        selection: ReflectionEvidenceSelection,
        protocol_id: str,
        claims: tuple[str, ...],
        uncertainties: tuple[str, ...],
    ) -> Reflection:
        """Reflect without protected leakage, winner-only filtering, or promotion."""
        self._selector.require_current(selection)
        if any(item.protected for item in selection.evidence):
            raise LearningAuthorityError("Protected evidence cannot enter cross-task reflection.")
        if any(self._repository.evidence(item.evidence_id) != item for item in selection.evidence):
            raise LearningAuthorityError("Reflection requires canonical registered evidence.")
        reflection_id = content_digest(
            (
                "reflection",
                selection.reader_actor_id,
                protocol_id,
                selection.selection_id,
                selection.scope,
                selection.evidence,
                selection.omissions,
                claims,
                uncertainties,
                "PROVISIONAL",
            )
        )
        reflection = Reflection(
            reflection_id=reflection_id,
            reflector_id=selection.reader_actor_id,
            protocol_id=protocol_id,
            selection_id=selection.selection_id,
            scope=selection.scope,
            evidence=selection.evidence,
            omissions=selection.omissions,
            claims=claims,
            uncertainties=uncertainties,
        )
        admitted = self._repository._admit(
            self._repository._reflections,
            reflection.reflection_id,
            reflection,
        )
        self._ledger.append(
            event_type="learning.reflected",
            subject_id=reflection.reflection_id,
            detail_refs=(
                selection.selection_id,
                *(item.evidence_id for item in selection.evidence),
                *(item.evidence_id for item in selection.omissions),
            ),
        )
        assert isinstance(admitted, Reflection)
        return admitted


class LessonProposer:
    """Turn canonical reflection into an explicitly unvalidated proposal."""

    def __init__(self, repository: LearningRepository, ledger: LearningLedger) -> None:
        self._repository = repository
        self._ledger = ledger

    def propose(
        self,
        *,
        reflection: Reflection,
        proposer_id: str,
        kind: LessonKind,
        content: str,
        scope: ApplicabilityScope,
        supporting_evidence_ids: tuple[str, ...],
        contrary_evidence_ids: tuple[str, ...],
        caveats: tuple[str, ...],
        parent_candidate_ids: tuple[str, ...] = (),
    ) -> CandidateLesson:
        """Preserve exact evidence and scope without publishing learning."""
        canonical = self._repository.reflection(reflection.reflection_id)
        if canonical != reflection:
            raise LearningAuthorityError("Candidate requires an issued canonical reflection.")
        if not scope.is_subset_of(reflection.scope):
            raise LearningAuthorityError("Candidate scope exceeds its reflection evidence scope.")
        reflection_evidence = {item.evidence_id: item for item in reflection.evidence}
        referenced = set((*supporting_evidence_ids, *contrary_evidence_ids))
        if referenced != set(reflection_evidence):
            raise ValueError("Candidate must classify every selected reflection evidence item.")
        if any(
            reflection_evidence[item].status is not EvidenceStatus.SUCCEEDED
            for item in supporting_evidence_ids
        ):
            raise ValueError("Only affirmative evidence may be classified as supporting.")
        if any(
            reflection_evidence[item].status is EvidenceStatus.SUCCEEDED
            for item in contrary_evidence_ids
        ):
            raise ValueError("Affirmative evidence cannot be classified as contrary.")
        if parent_candidate_ids and any(
            self._repository.candidate(parent) is None for parent in parent_candidate_ids
        ):
            raise ValueError("Candidate ancestry contains an unknown parent.")
        candidate = identified(
            CandidateLesson,
            reflection_id=reflection.reflection_id,
            proposer_id=proposer_id,
            kind=kind,
            content=content,
            scope=scope,
            supporting_evidence_ids=supporting_evidence_ids,
            contrary_evidence_ids=contrary_evidence_ids,
            caveats=caveats,
            originating_task_ids=tuple(
                sorted({reflection_evidence[item].task_id for item in referenced})
            ),
            parent_candidate_ids=parent_candidate_ids,
            status="CANDIDATE",
        )
        assert isinstance(candidate, CandidateLesson)
        admitted = self._repository._admit(
            self._repository._candidates,
            candidate.candidate_id,
            candidate,
        )
        self._ledger.append(
            event_type="learning.candidate-proposed",
            subject_id=candidate.candidate_id,
            detail_refs=(reflection.reflection_id, *sorted(referenced)),
        )
        assert isinstance(admitted, CandidateLesson)
        return admitted


class LessonValidator:
    """Apply a predeclared standard under independent configured authority."""

    def __init__(
        self,
        repository: LearningRepository,
        ledger: LearningLedger,
        *,
        authorities: LearningAuthorityRegistry,
        standards: tuple[LessonValidationStandard, ...],
    ) -> None:
        if not standards:
            raise ValueError("Lesson validation needs predeclared standards.")
        self._repository = repository
        self._ledger = ledger
        self._authorities = authorities
        repository.require_authorities(authorities)
        for standard in standards:
            repository._admit(repository._standards, standard.standard_id, standard)

    def validate(
        self,
        *,
        candidate: CandidateLesson,
        standard_id: str,
        validator: LessonValidatorCapability,
        independent_evidence: tuple[HistoryEvidence, ...],
    ) -> LessonValidationDecision:
        """Issue PROMOTE only for independent, sufficient, conflict-free evidence."""
        canonical = self._repository.candidate(candidate.candidate_id)
        if canonical != candidate:
            raise LearningAuthorityError("Validation requires an issued canonical candidate.")
        self._authorities.require_validator(validator)
        validator_authority_id = validator.authority_id
        if validator_authority_id in {
            candidate.proposer_id,
            self._required_reflection(candidate.reflection_id).reflector_id,
        }:
            raise LearningAuthorityError("A lesson beneficiary cannot independently approve it.")
        standard = self._repository.standard(standard_id)
        if standard is None:
            raise LearningAuthorityError("Validation standard was not predeclared.")
        evidence_ids = tuple(item.evidence_id for item in independent_evidence)
        if any(
            self._repository.evidence(item.evidence_id) != item for item in independent_evidence
        ):
            raise LearningAuthorityError("Validation requires canonical registered evidence.")
        task_ids = tuple(sorted({item.task_id for item in independent_evidence}))
        overlap = set(evidence_ids).intersection(
            (*candidate.supporting_evidence_ids, *candidate.contrary_evidence_ids)
        )
        task_overlap = set(task_ids).intersection(candidate.originating_task_ids)
        original_source_ids = {
            item.source_authority_id
            for evidence_id in (
                *candidate.supporting_evidence_ids,
                *candidate.contrary_evidence_ids,
            )
            if (item := self._repository.evidence(evidence_id)) is not None
        }
        evidence_source_ids = {item.source_authority_id for item in independent_evidence}
        reflection = self._required_reflection(candidate.reflection_id)
        adverse_omission = any(
            item.status is not EvidenceStatus.SUCCEEDED for item in reflection.omissions
        )
        scope_match = (
            all(
                item.environment_ref in candidate.scope.environment_refs
                and item.task_kind in candidate.scope.task_kinds
                and bool(set(item.subject_tags).intersection(candidate.scope.subject_tags))
                for item in independent_evidence
            )
            and set(candidate.scope.environment_refs).issubset(
                item.environment_ref for item in independent_evidence
            )
            and set(candidate.scope.task_kinds).issubset(
                item.task_kind for item in independent_evidence
            )
            and set(candidate.scope.subject_tags).issubset(
                subject for item in independent_evidence for subject in item.subject_tags
            )
        )
        enough = (
            len(set(evidence_ids)) >= standard.minimum_independent_evidence
            and len(task_ids) >= standard.minimum_independent_tasks
            and not overlap
            and not task_overlap
            and not any(item.protected for item in independent_evidence)
            and all(item.current for item in independent_evidence)
            and all(item.status is EvidenceStatus.SUCCEEDED for item in independent_evidence)
            and evidence_source_ids.isdisjoint(original_source_ids)
            and scope_match
            and not (standard.require_no_unresolved_contrary_evidence and adverse_omission)
        )
        outcome = LessonDecisionOutcome.PROMOTE if enough else LessonDecisionOutcome.REJECT
        reasons = (
            ("Independent evidence satisfied the predeclared standard.",)
            if enough
            else ("Independent evidence did not satisfy the predeclared standard.",)
        )
        decision = identified(
            LessonValidationDecision,
            candidate_id=candidate.candidate_id,
            standard_id=standard.standard_id,
            validator_authority_id=validator_authority_id,
            outcome=outcome,
            independent_evidence_ids=evidence_ids,
            independent_task_ids=task_ids,
            reasons=reasons,
            scope=candidate.scope,
        )
        assert isinstance(decision, LessonValidationDecision)
        admitted = self._repository._admit(
            self._repository._decisions,
            decision.decision_id,
            decision,
        )
        self._ledger.append(
            event_type=f"learning.lesson-{outcome.value}",
            subject_id=candidate.candidate_id,
            detail_refs=(decision.decision_id, *evidence_ids),
        )
        assert isinstance(admitted, LessonValidationDecision)
        return admitted

    def _required_reflection(self, reflection_id: str) -> Reflection:
        reflection = self._repository.reflection(reflection_id)
        if reflection is None:
            raise LearningAuthorityError("Candidate reflection is no longer canonical.")
        return reflection


class LessonPromoter:
    """Materialize only authority-issued decisions; preserve rejection history."""

    def __init__(self, repository: LearningRepository, ledger: LearningLedger) -> None:
        self._repository = repository
        self._ledger = ledger

    def apply(
        self,
        *,
        candidate: CandidateLesson,
        decision: LessonValidationDecision,
        supersedes_learning_id: str | None = None,
    ) -> ValidatedLearning | RejectedLesson:
        """Create a scoped Memory/Skill or append-only rejection."""
        if self._repository.candidate(candidate.candidate_id) != candidate:
            raise LearningAuthorityError("Promotion requires an issued candidate.")
        if self._repository.decision(decision.decision_id) != decision:
            raise LearningAuthorityError("Promotion requires an authority-issued decision.")
        if decision.candidate_id != candidate.candidate_id or decision.scope != candidate.scope:
            raise LearningAuthorityError("Decision does not bind the exact candidate and scope.")
        if decision.outcome is LessonDecisionOutcome.REJECT:
            if supersedes_learning_id is not None:
                raise LearningConflictError("A rejection cannot supersede validated learning.")
            rejection = identified(
                RejectedLesson,
                candidate_id=candidate.candidate_id,
                decision_id=decision.decision_id,
                reasons=decision.reasons,
                provenance_refs=(candidate.reflection_id, decision.standard_id),
            )
            assert isinstance(rejection, RejectedLesson)
            with self._repository._lock:
                prior_effect = self._repository._effect_by_decision.get(decision.decision_id)
                if prior_effect is not None:
                    if prior_effect != rejection:
                        raise LearningConflictError(
                            "Lesson decision was already consumed by another effect."
                        )
                    return prior_effect
                admitted = self._repository._admit(
                    self._repository._rejected,
                    rejection.rejection_id,
                    rejection,
                )
                assert isinstance(admitted, RejectedLesson)
                self._repository._effect_by_decision[decision.decision_id] = admitted
            self._ledger.append(
                event_type="ledger.rejected-lesson-recorded",
                subject_id=candidate.candidate_id,
                detail_refs=(rejection.rejection_id, decision.decision_id),
            )
            return admitted
        previous = (
            self._repository.learning(supersedes_learning_id)
            if supersedes_learning_id is not None
            else None
        )
        if supersedes_learning_id is not None and previous is None:
            raise ValueError("Superseded learning identity is unknown.")
        if previous is not None and (
            previous.kind is not candidate.kind
            or not candidate.scope.is_subset_of(previous.scope)
            or previous.candidate_id not in candidate.parent_candidate_ids
        ):
            raise LearningConflictError(
                "Supersession requires same-kind, non-broadening explicit candidate lineage."
            )
        learning = identified(
            ValidatedLearning,
            candidate_id=candidate.candidate_id,
            decision_id=decision.decision_id,
            kind=candidate.kind,
            content=candidate.content,
            scope=candidate.scope,
            caveats=candidate.caveats,
            provenance_refs=(
                candidate.reflection_id,
                decision.standard_id,
                *decision.independent_evidence_ids,
            ),
            version=1 if previous is None else previous.version + 1,
            supersedes_learning_id=supersedes_learning_id,
        )
        assert isinstance(learning, ValidatedLearning)
        with self._repository._lock:
            prior_effect = self._repository._effect_by_decision.get(decision.decision_id)
            if prior_effect is not None:
                if prior_effect != learning:
                    raise LearningConflictError(
                        "Lesson decision was already consumed by another promotion lineage."
                    )
                assert isinstance(prior_effect, ValidatedLearning)
                return prior_effect
            if previous is not None:
                prior_successor = self._repository._successor_by_learning.get(previous.learning_id)
                if prior_successor is not None and prior_successor != learning.learning_id:
                    raise LearningConflictError(
                        "Validated learning already has a different successor."
                    )
            admitted = self._repository._admit(
                self._repository._validated,
                learning.learning_id,
                learning,
            )
            assert isinstance(admitted, ValidatedLearning)
            self._repository._effect_by_decision[decision.decision_id] = admitted
            if previous is not None:
                self._repository._successor_by_learning[previous.learning_id] = admitted.learning_id
        self._ledger.append(
            event_type="learning.lesson-promoted",
            subject_id=learning.learning_id,
            detail_refs=(candidate.candidate_id, decision.decision_id),
        )
        return admitted


class KnowledgeEnvironment:
    """Append-only scoped publication and bounded retrieval of validated learning."""

    def __init__(
        self,
        repository: LearningRepository,
        ledger: LearningLedger,
        *,
        authorities: LearningAuthorityRegistry,
        max_results: int = 8,
    ) -> None:
        if max_results < 1:
            raise ValueError("Knowledge retrieval bound must be positive.")
        self._repository = repository
        self._ledger = ledger
        self._authorities = authorities
        repository.require_authorities(authorities)
        self._max_results = max_results
        self._entries: dict[str, KnowledgeEntry] = {}
        self._entry_by_learning: dict[str, str] = {}
        self._retrievals: dict[str, KnowledgeRetrieval] = {}
        self._lock = RLock()

    def publish(
        self,
        *,
        learning: object,
        publisher: KnowledgePublisherCapability,
        permitted_actor_ids: tuple[str, ...],
    ) -> KnowledgeEntry:
        """Publish exact validated content without broadening its authority."""
        if not isinstance(learning, ValidatedLearning):
            raise LearningAuthorityError(
                "Knowledge publication requires issued validated learning."
            )
        if self._repository.learning(learning.learning_id) != learning:
            raise LearningAuthorityError(
                "Knowledge publication requires issued validated learning."
            )
        self._authorities.require_publisher(publisher)
        policy = publisher.policy
        if (
            not set(permitted_actor_ids).issubset(policy.permitted_actor_ids)
            or not set(learning.scope.task_kinds).issubset(policy.allowed_task_kinds)
            or not set(learning.scope.environment_refs).issubset(policy.allowed_environment_refs)
            or not set(learning.scope.subject_tags).issubset(policy.allowed_subject_tags)
        ):
            raise LearningAuthorityError("Knowledge publication exceeds publisher capability.")
        with self._lock:
            existing_id = self._entry_by_learning.get(learning.learning_id)
            if existing_id is not None:
                existing = self._entries[existing_id]
                if existing.permitted_actor_ids != permitted_actor_ids:
                    raise LearningConflictError(
                        "Knowledge publication retry changed reader permissions."
                    )
                return existing
            previous_entry: KnowledgeEntry | None = None
            if learning.supersedes_learning_id is not None:
                previous_id = self._entry_by_learning.get(learning.supersedes_learning_id)
                if previous_id is None:
                    raise LearningAuthorityError("Superseded learning was not published here.")
                previous_entry = self._entries[previous_id]
                if previous_entry.status is not KnowledgeEntryStatus.CURRENT:
                    raise LearningConflictError("Superseded learning is no longer current here.")
                if not set(permitted_actor_ids).issubset(previous_entry.permitted_actor_ids):
                    raise LearningAuthorityError(
                        "A successor publication cannot broaden reader permissions."
                    )
            entry = identified(
                KnowledgeEntry,
                learning_id=learning.learning_id,
                kind=learning.kind,
                content=learning.content,
                scope=learning.scope,
                caveats=learning.caveats,
                provenance_refs=learning.provenance_refs,
                permitted_actor_ids=permitted_actor_ids,
                status=KnowledgeEntryStatus.CURRENT,
                superseded_by=None,
            )
            assert isinstance(entry, KnowledgeEntry)
            if previous_entry is not None:
                superseded = identified(
                    KnowledgeEntry,
                    learning_id=previous_entry.learning_id,
                    kind=previous_entry.kind,
                    content=previous_entry.content,
                    scope=previous_entry.scope,
                    caveats=previous_entry.caveats,
                    provenance_refs=previous_entry.provenance_refs,
                    permitted_actor_ids=previous_entry.permitted_actor_ids,
                    status=KnowledgeEntryStatus.SUPERSEDED,
                    superseded_by=entry.entry_id,
                )
                assert isinstance(superseded, KnowledgeEntry)
                self._entries[superseded.entry_id] = superseded
                self._entry_by_learning[previous_entry.learning_id] = superseded.entry_id
            self._entries[entry.entry_id] = entry
            self._entry_by_learning[learning.learning_id] = entry.entry_id
        self._ledger.append(
            event_type="learning.published-to-knowledge",
            subject_id=entry.entry_id,
            detail_refs=(learning.learning_id,),
        )
        return entry

    def retrieve(
        self,
        query: KnowledgeQuery,
        *,
        reader: LearningReaderCapability,
    ) -> KnowledgeRetrieval:
        """Return only current, permitted, in-scope entries under a strict bound."""
        self._require_query_authority(query, reader)
        with self._lock:
            retrieval = self._build_retrieval_unlocked(query)
            existing = self._retrievals.get(retrieval.retrieval_id)
            if existing is not None and existing != retrieval:
                raise LearningConflictError("Knowledge retrieval identity conflict.")
            self._retrievals[retrieval.retrieval_id] = retrieval
        self._ledger.append(
            event_type="knowledge.retrieved",
            subject_id=retrieval.retrieval_id,
            detail_refs=tuple(item.entry_id for item in retrieval.entries),
        )
        return retrieval

    def require_current_retrieval(
        self,
        retrieval: KnowledgeRetrieval,
        *,
        reader: LearningReaderCapability,
    ) -> None:
        """Reject stale, superseded, permission-changed, or self-rehashed retrievals."""
        self._require_query_authority(retrieval.query, reader)
        with self._lock:
            if self._retrievals.get(retrieval.retrieval_id) != retrieval:
                raise LearningAuthorityError(
                    "Context projection requires a knowledge-environment-issued retrieval."
                )
            if self._build_retrieval_unlocked(retrieval.query) != retrieval:
                raise LearningAuthorityError(
                    "Knowledge retrieval is stale relative to current entries or permissions."
                )

    def _build_retrieval_unlocked(self, query: KnowledgeQuery) -> KnowledgeRetrieval:
        candidates = tuple(self._entries[entry_id] for entry_id in self._entry_by_learning.values())
        current = tuple(
            item
            for item in candidates
            if item.status is KnowledgeEntryStatus.CURRENT
            and item.kind in query.allowed_kinds
            and query.actor_id in item.permitted_actor_ids
            and item.scope.permits(query)
        )
        ordered = tuple(sorted(current, key=lambda item: item.entry_id))
        selected = ordered[: self._max_results]
        retrieval = identified(
            KnowledgeRetrieval,
            query=query,
            entries=selected,
            omitted_count=len(ordered) - len(selected),
        )
        assert isinstance(retrieval, KnowledgeRetrieval)
        return retrieval

    def _require_query_authority(
        self,
        query: KnowledgeQuery,
        reader: LearningReaderCapability,
    ) -> None:
        self._authorities.require_reader(reader)
        policy = reader.policy
        if (
            query.actor_id != policy.actor_id
            or query.task_id not in policy.allowed_task_ids
            or query.task_kind not in policy.allowed_task_kinds
            or query.environment_ref not in policy.allowed_environment_refs
            or not set(query.subject_tags).issubset(policy.allowed_subject_tags)
        ):
            raise LearningAuthorityError("Knowledge query exceeds reader capability scope.")

    def resolve_retrieval(self, retrieval_id: str) -> KnowledgeRetrieval | None:
        """Resolve one environment-issued retrieval without exposing mutation."""
        with self._lock:
            return self._retrievals.get(retrieval_id)

    def entries(self) -> tuple[KnowledgeEntry, ...]:
        """Return append-only current and superseded representations."""
        with self._lock:
            return tuple(self._entries.values())


class LearningContextProjector:
    """Project substantive validated learning into one future ContextPacket."""

    def __init__(
        self,
        knowledge: KnowledgeEnvironment,
        *,
        reader: LearningReaderCapability,
        max_entries: int = 8,
    ) -> None:
        if max_entries < 1:
            raise ValueError("Learning context bound must be positive.")
        self._knowledge = knowledge
        self._reader = reader
        self._max_entries = max_entries

    def project(
        self,
        packet: ContextPacket,
        retrieval: KnowledgeRetrieval,
    ) -> ContextPacket:
        """Add bounded content, caveats, scope, and provenance—not IDs alone."""
        with self._knowledge._lock:
            return self._project_while_current(packet, retrieval)

    def _project_while_current(
        self,
        packet: ContextPacket,
        retrieval: KnowledgeRetrieval,
    ) -> ContextPacket:
        """Validate and project while publication/supersession is excluded."""
        self._knowledge.require_current_retrieval(retrieval, reader=self._reader)
        query = retrieval.query
        if query.task_id != packet.task_id or query.environment_ref != packet.environment_ref:
            raise LearningAuthorityError("Knowledge retrieval does not bind this future context.")
        selected = retrieval.entries[: self._max_entries]
        if (
            selected
            and packet.target_field_id is not None
            and packet.target_field_id not in query.subject_tags
        ):
            raise LearningAuthorityError("Knowledge retrieval subject does not bind this context.")
        observations = tuple(self._observation(item, packet) for item in selected)
        by_id = {item.observation_id: item for item in packet.working_observations}
        duplicates = tuple(item for item in observations if item.observation_id in by_id)
        if duplicates:
            if len(duplicates) == len(observations) and all(
                by_id[item.observation_id] == item for item in duplicates
            ):
                return packet
            raise LearningConflictError("Learning context projection conflicts with prior content.")
        working = (*packet.working_observations, *observations)
        warnings = packet.warnings
        omitted = retrieval.omitted_count + max(0, len(retrieval.entries) - len(selected))
        if omitted:
            warnings += (
                f"{omitted} applicable validated-learning entries were omitted by bounds.",
            )
        semantics = {
            "base_packet_id": packet.packet_id,
            "retrieval_id": retrieval.retrieval_id,
            "learning_entry_ids": tuple(item.entry_id for item in selected),
            "working_observation_digests": tuple(item.source_content_digest for item in working),
        }
        return replace(
            packet,
            packet_id=content_digest(semantics),
            working_observations=working,
            total_observation_count=packet.total_observation_count + len(observations),
            warnings=warnings,
        )

    @staticmethod
    def _observation(entry: KnowledgeEntry, packet: ContextPacket) -> ContextObservation:
        payload = {
            "learning_id": entry.learning_id,
            "kind": entry.kind.value,
            "content": entry.content,
            "scope": {
                "task_kinds": entry.scope.task_kinds,
                "environment_refs": entry.scope.environment_refs,
                "subject_tags": entry.scope.subject_tags,
            },
            "caveats": entry.caveats,
            "provenance_refs": entry.provenance_refs,
            "status": entry.status.value,
        }
        return ContextObservation(
            observation_id=f"knowledge:{entry.entry_id}",
            status=ObservationStatus.SUCCEEDED,
            observation_type="validated_learning",
            summary=f"Validated {entry.kind.value} applicable to this task.",
            payload=payload,
            warnings=entry.caveats,
            provenance=None,
            artifact_refs=entry.provenance_refs,
            recoverability=Recoverability.NON_RETRYABLE,
            failure=None,
            epistemic_status="VALIDATED_SCOPED_LEARNING",
            source_content_digest=content_digest((entry, packet.task_id, packet.environment_ref)),
        )


__all__ = [
    "HistoricalEvidenceRegistrar",
    "HistoricalEvidenceSelector",
    "HistoryReflector",
    "KnowledgeEnvironment",
    "LearningAuthorityError",
    "LearningAuthorityRegistry",
    "LearningConflictError",
    "LearningContextProjector",
    "LearningLedger",
    "LearningRepository",
    "LessonPromoter",
    "LessonProposer",
    "LessonValidator",
]
