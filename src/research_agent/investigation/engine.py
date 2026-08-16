"""Question-to-evidence orchestration for authored scientific programs."""

# ruff: noqa: D102, D105, D107, EM101, SLF001, TRY003

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from math import fsum, isfinite
from threading import RLock
from typing import TYPE_CHECKING, cast

from research_agent.data_foundation._identity import stable_identity
from research_agent.data_foundation.information import InformationSetBuilder
from research_agent.development.records import TrialLedger, TrialStatus
from research_agent.investigation.program import (
    ProgramInvocation,
    ScientificProgramError,
    ScientificProgramHarness,
)
from research_agent.investigation.records import (
    AuthoredCandidate,
    AuthoredDevelopmentEvidence,
    AuthoredProgramProposal,
    DevelopmentDisposition,
    InvestigationRequest,
    InvestigationResult,
    QuestionStatus,
    RegisteredInvestigation,
    Researcher,
    ResearcherContext,
    RuntimeTrialReceipt,
)

if TYPE_CHECKING:
    from datetime import datetime

    from research_agent.data_foundation.observations import (
        RegisteredObservation,
    )
    from research_agent.data_foundation.samples import SampleKey
    from research_agent.investigation.memory import QuestionMemoryRecord, ValidatedQuestionMemory
    from research_agent.investigation.program import JsonValue
    from research_agent.investigation.records import DevelopmentBudget, ProgramAccess


class CandidateRegistry:
    """Authority-owned publication registry; self-hashed candidates are insufficient."""

    def __init__(self) -> None:
        self._issued: dict[str, AuthoredCandidate] = {}
        self._lock = RLock()

    def __copy__(self) -> CandidateRegistry:
        raise TypeError("candidate publication authority cannot be copied")

    def __deepcopy__(self, memo: dict[int, object]) -> CandidateRegistry:
        del memo
        raise TypeError("candidate publication authority cannot be copied")

    def _issue(self, candidate: AuthoredCandidate) -> AuthoredCandidate:
        with self._lock:
            existing = self._issued.get(candidate.candidate_id)
            if existing is not None and existing != candidate:
                raise ValueError("candidate publication identity conflict")
            self._issued[candidate.candidate_id] = candidate
        return candidate

    def require_issued(self, candidate: AuthoredCandidate) -> None:
        with self._lock:
            if self._issued.get(candidate.candidate_id) != candidate:
                raise ValueError("candidate was not issued by this publication authority")


class CandidatePublisher:
    """Validate one proposal against the active question before publication."""

    def __init__(self, registry: CandidateRegistry | None = None) -> None:
        self.registry = registry or CandidateRegistry()

    def publish(
        self,
        request: InvestigationRequest,
        proposal: AuthoredProgramProposal,
        *,
        expected_parent_trial_id: str | None,
    ) -> AuthoredCandidate:
        manifest = proposal.manifest
        if manifest.question_id != request.question.question_id:
            raise ValueError("candidate proposal belongs to a different research question")
        if manifest.environment_id != request.catalog.environment_id:
            raise ValueError("candidate proposal belongs to a different environment")
        if expected_parent_trial_id is None:
            if proposal.parent_trial_ids:
                raise ValueError("first candidate cannot claim unissued trial ancestry")
        elif expected_parent_trial_id not in proposal.parent_trial_ids:
            raise ValueError("candidate revision must include the immediately prior trial")
        for field in (*manifest.predictor_fields, manifest.outcome_field):
            request.catalog.resolve_schema(field)
        digest = hashlib.sha256(proposal.source.encode()).hexdigest()
        payload = {
            "source_sha256": digest,
            "manifest_id": manifest.identity,
            "rationale": proposal.rationale,
            "parent_trial_ids": proposal.parent_trial_ids,
        }
        candidate = AuthoredCandidate(
            candidate_id=stable_identity("authored-candidate", payload),
            source=proposal.source,
            source_sha256=digest,
            manifest=manifest,
            rationale=proposal.rationale,
            parent_trial_ids=proposal.parent_trial_ids,
        )
        return self.registry._issue(candidate)  # pyright: ignore[reportPrivateUsage]


@dataclass(frozen=True, slots=True)
class _Example:
    key: SampleKey
    features: dict[str, float]
    label: float
    label_matured_at: datetime


class AuthoredDevelopmentEvaluator:
    """Build legal examples and OOF evidence around arbitrary authored methods."""

    def __init__(
        self,
        *,
        candidates: CandidateRegistry,
        programs: ScientificProgramHarness | None = None,
        ledger: TrialLedger | None = None,
    ) -> None:
        self._candidates = candidates
        self._programs = programs or ScientificProgramHarness()
        self.ledger = ledger or TrialLedger()

    def evaluate(
        self,
        request: InvestigationRequest,
        candidate: AuthoredCandidate,
    ) -> AuthoredDevelopmentEvidence:
        self._candidates.require_issued(candidate)
        trial_id = stable_identity(
            "authored-development-trial",
            {
                "candidate_id": candidate.candidate_id,
                "catalog_id": request.catalog.identity,
                "budget_id": request.budget.identity,
                "ordinal": len(self.ledger.records),
            },
        )
        self.ledger.append(
            trial_id=trial_id,
            candidate_id=candidate.candidate_id,
            protocol_id=request.budget.identity,
            parent_trial_ids=candidate.parent_trial_ids,
            status=TrialStatus.ATTEMPTED,
            rationale="execute authored program under temporal development controls",
        )
        try:
            evidence = self._evaluate(request, candidate, trial_id)
        except (ScientificProgramError, TypeError, ValueError) as error:
            failure_id = stable_identity(
                "authored-development-failure",
                {"trial_id": trial_id, "detail": str(error)},
            )
            self.ledger.append(
                trial_id=trial_id,
                candidate_id=candidate.candidate_id,
                protocol_id=request.budget.identity,
                parent_trial_ids=candidate.parent_trial_ids,
                status=TrialStatus.FAILED,
                rationale="authored development trial failed without fallback",
                failure_id=failure_id,
            )
            raise
        self.ledger.append(
            trial_id=trial_id,
            candidate_id=candidate.candidate_id,
            protocol_id=request.budget.identity,
            parent_trial_ids=candidate.parent_trial_ids,
            status=TrialStatus.SUCCEEDED,
            rationale="selection-exposed authored development evidence generated",
            evidence_refs=(evidence.evidence_id,),
        )
        return evidence

    def _evaluate(
        self,
        request: InvestigationRequest,
        candidate: AuthoredCandidate,
        trial_id: str,
    ) -> AuthoredDevelopmentEvidence:
        examples, feature_accesses, label_accesses = self._examples(request, candidate)
        if len(examples) <= request.budget.minimum_training_rows:
            raise ValueError("insufficient legal examples for one out-of-fold prediction")
        predictions: list[float] = []
        outcomes: list[float] = []
        row_keys: list[SampleKey] = []
        fit_accesses: list[ProgramAccess] = []
        prediction_accesses: list[ProgramAccess] = []
        for ordinal, validation in enumerate(examples):
            if ordinal < request.budget.minimum_training_rows:
                continue
            training = tuple(
                item
                for item in examples[:ordinal]
                if item.label_matured_at <= validation.key.decision_time
            )
            if len(training) < request.budget.minimum_training_rows:
                continue
            fit = self._programs.invoke(
                candidate.source,
                ProgramInvocation(
                    "fit",
                    training=[
                        {
                            "decision_time": item.key.decision_time.isoformat(),
                            "dimensions": [list(value) for value in item.key.dimensions],
                            "features": cast("dict[str, JsonValue]", item.features),
                            "label": item.label,
                        }
                        for item in training
                    ],
                ),
            )
            prediction = self._programs.invoke(
                candidate.source,
                ProgramInvocation(
                    "predict",
                    state=fit.value,
                    features=cast("dict[str, JsonValue]", validation.features),
                ),
            )
            value = _finite_number(prediction.value, "prediction")
            predictions.append(value)
            outcomes.append(validation.label)
            row_keys.append(validation.key)
            fit_accesses.extend(fit.accesses)
            prediction_accesses.extend(prediction.accesses)
        if len(predictions) < request.budget.minimum_oof_predictions:
            raise ValueError("insufficient out-of-fold predictions for declared evidence budget")
        metrics = ((request.budget.primary_metric, _metric(request.budget, predictions, outcomes)),)
        payload = {
            "trial_id": trial_id,
            "candidate_id": candidate.candidate_id,
            "catalog_id": request.catalog.identity,
            "budget_id": request.budget.identity,
            "row_keys": tuple(row_keys),
            "predictions": tuple(predictions),
            "outcomes": tuple(outcomes),
            "metrics": metrics,
            "feature_accesses": tuple(feature_accesses),
            "label_accesses": tuple(label_accesses),
            "fit_accesses": tuple(fit_accesses),
            "prediction_accesses": tuple(prediction_accesses),
            "warnings": (
                "authored development evidence is selection-exposed and not protected validation",
            ),
        }
        return AuthoredDevelopmentEvidence(
            evidence_id=stable_identity("authored-development-evidence", payload),
            trial_id=trial_id,
            candidate_id=candidate.candidate_id,
            catalog_id=request.catalog.identity,
            budget_id=request.budget.identity,
            row_keys=tuple(row_keys),
            predictions=tuple(predictions),
            outcomes=tuple(outcomes),
            metrics=metrics,
            feature_accesses=tuple(feature_accesses),
            label_accesses=tuple(label_accesses),
            fit_accesses=tuple(fit_accesses),
            prediction_accesses=tuple(prediction_accesses),
            warnings=(
                "authored development evidence is selection-exposed and not protected validation",
            ),
        )

    def _examples(
        self,
        request: InvestigationRequest,
        candidate: AuthoredCandidate,
    ) -> tuple[list[_Example], list[ProgramAccess], list[ProgramAccess]]:
        manifest = candidate.manifest
        dimensions = tuple(sorted(manifest.population_dimensions))
        if any(key.dimensions != dimensions for key in request.sample_keys):
            raise ValueError("sample population differs from the exact candidate population")
        examples: list[_Example] = []
        feature_accesses: list[ProgramAccess] = []
        label_accesses: list[ProgramAccess] = []
        for key in sorted(request.sample_keys, key=lambda item: item.decision_time):
            information = InformationSetBuilder().build(
                request.catalog,
                decision_time=key.decision_time,
                requested_fields=manifest.predictor_fields,
            )
            histories = {
                field.field_id: [
                    _observation_json(item)
                    for item in information.for_field(field)
                    if item.reference_time <= key.decision_time and item.dimensions == dimensions
                ]
                for field in manifest.predictor_fields
            }
            if any(not values for values in histories.values()):
                if manifest.missing_value_policy == "fail_trial":
                    raise ValueError("candidate history is insufficient at a decision boundary")
                continue
            outcome_end = manifest.horizon.apply(key.decision_time)
            if outcome_end > request.current_time:
                continue
            outcome = [
                item
                for item in request.catalog.observations
                if item.field_ref == manifest.outcome_field
                and item.dimensions == dimensions
                and key.decision_time < item.reference_time <= outcome_end
                and item.available_at <= request.current_time
            ]
            outcome.sort(key=lambda item: (item.reference_time, item.revision_number))
            if len(outcome) < manifest.minimum_outcome_points:
                if manifest.missing_value_policy == "fail_trial":
                    raise ValueError("candidate outcome path is incomplete")
                continue
            feature_result = self._programs.invoke(
                candidate.source,
                ProgramInvocation("make_features", histories=histories),
            )
            label_result = self._programs.invoke(
                candidate.source,
                ProgramInvocation(
                    "make_label",
                    outcome=[_observation_json(item) for item in outcome],
                ),
            )
            features = _feature_values(feature_result.value, manifest.feature_names)
            label = _finite_number(label_result.value, "label")
            matured_at = max(outcome_end, *(item.available_at for item in outcome))
            examples.append(_Example(key, features, label, matured_at))
            feature_accesses.extend(feature_result.accesses)
            label_accesses.extend(label_result.accesses)
        return examples, feature_accesses, label_accesses


class AutonomousInvestigation:
    """Bounded provider-neutral loop from research question to development disposition."""

    def run(
        self,
        request: InvestigationRequest,
        researcher: Researcher,
    ) -> InvestigationResult:
        publisher = CandidatePublisher()
        evaluator = AuthoredDevelopmentEvaluator(candidates=publisher.registry)
        evidence: list[AuthoredDevelopmentEvidence] = []
        candidate: AuthoredCandidate | None = None
        prior_trial_id: str | None = None
        for ordinal in range(request.budget.max_trials):
            context = _researcher_context(request, ordinal, tuple(evidence))
            proposal = researcher.propose(context)
            candidate = publisher.publish(
                request,
                proposal,
                expected_parent_trial_id=prior_trial_id,
            )
            trial_evidence = evaluator.evaluate(request, candidate)
            evidence.append(trial_evidence)
            prior_trial_id = trial_evidence.trial_id
            primary_value = dict(trial_evidence.metrics)[request.budget.primary_metric]
            if primary_value <= request.budget.credible_at_or_below:
                return InvestigationResult(
                    request.question,
                    DevelopmentDisposition.CREDIBLE,
                    QuestionStatus.CREDIBLE_CANDIDATE,
                    ordinal + 1,
                    candidate,
                    tuple(evidence),
                    evaluator.ledger.records,
                )
        return InvestigationResult(
            request.question,
            DevelopmentDisposition.REJECT,
            QuestionStatus.NEGATIVE,
            request.budget.max_trials,
            candidate,
            tuple(evidence),
            evaluator.ledger.records,
        )


class InvestigationConflictError(ValueError):
    """An idempotency key was reused for changed authored semantics."""


@dataclass(slots=True)
class _RuntimeInvestigationState:
    registration: RegisteredInvestigation
    prior_question_memory: tuple[QuestionMemoryRecord, ...]
    publisher: CandidatePublisher
    evaluator: AuthoredDevelopmentEvaluator
    evidence: list[AuthoredDevelopmentEvidence]
    trials_attempted: int
    last_trial_id: str | None
    receipts: dict[str, tuple[str, RuntimeTrialReceipt]]


class RuntimeInvestigationCoordinator:
    """Composition-owned, one-trial-per-turn bridge for the autonomous runtime."""

    def __init__(self, *, question_memory: ValidatedQuestionMemory | None = None) -> None:
        self._states: dict[str, _RuntimeInvestigationState] = {}
        self._evidence: dict[str, AuthoredDevelopmentEvidence] = {}
        self._candidates: dict[str, AuthoredCandidate] = {}
        self._question_memory = question_memory
        self._lock = RLock()

    def __copy__(self) -> RuntimeInvestigationCoordinator:
        raise TypeError("runtime investigation authority cannot be copied")

    def __deepcopy__(self, memo: dict[int, object]) -> RuntimeInvestigationCoordinator:
        del memo
        raise TypeError("runtime investigation authority cannot be copied")

    def register(
        self,
        request: InvestigationRequest,
        *,
        session_id: str,
        episode_id: str,
    ) -> RegisteredInvestigation:
        """Publish one exact runtime scope from trusted application composition."""
        prior_question_memory: tuple[QuestionMemoryRecord, ...] = ()
        if self._question_memory is not None:
            self._question_memory.require_open(request)
            prior_question_memory = self._question_memory.context_for(request)
        payload = {
            "session_id": session_id,
            "episode_id": episode_id,
            "question": request.question,
            "catalog_id": request.catalog.identity,
            "sample_keys": request.sample_keys,
            "current_time": request.current_time,
            "budget_id": request.budget.identity,
            "random_seed": request.random_seed,
            "protected_predeclaration": request.protected_predeclaration,
            "reopen": request.reopen,
        }
        registration = RegisteredInvestigation(
            stable_identity("registered-investigation", payload),
            session_id,
            episode_id,
            request,
        )
        with self._lock:
            existing = self._states.get(registration.registration_id)
            if existing is not None:
                if existing.registration != registration:
                    raise InvestigationConflictError("investigation registration conflict")
                return existing.registration
            publisher = CandidatePublisher()
            self._states[registration.registration_id] = _RuntimeInvestigationState(
                registration,
                prior_question_memory,
                publisher,
                AuthoredDevelopmentEvaluator(candidates=publisher.registry),
                [],
                0,
                None,
                {},
            )
        return registration

    def memory_context(self, registration_id: str) -> tuple[QuestionMemoryRecord, ...]:
        """Return the bounded exact-lineage memory fixed when an investigation registered."""
        with self._lock:
            state = self._states.get(registration_id)
            if state is None:
                raise KeyError(registration_id)
            return state.prior_question_memory

    def authorize(
        self,
        registration_id: str,
        *,
        session_id: str,
        episode_id: str,
    ) -> RegisteredInvestigation:
        """Resolve only an exact registration bound to the active runtime authority."""
        with self._lock:
            state = self._states.get(registration_id)
            if state is None:
                raise KeyError(registration_id)
            registration = state.registration
            if registration.session_id != session_id or registration.episode_id != episode_id:
                raise PermissionError(registration_id)
            return registration

    def execute(
        self,
        registration_id: str,
        proposal: AuthoredProgramProposal,
        *,
        session_id: str,
        episode_id: str,
        idempotency_key: str,
    ) -> RuntimeTrialReceipt:
        """Publish and evaluate exactly one proposal, preserving replay semantics."""
        with self._lock:
            registration = self.authorize(
                registration_id,
                session_id=session_id,
                episode_id=episode_id,
            )
            state = self._states[registration_id]
            request_digest = stable_identity(
                "runtime-authored-trial-request",
                {
                    "registration_id": registration_id,
                    "proposal": proposal,
                    "idempotency_key": idempotency_key,
                },
            )
            replay = state.receipts.get(idempotency_key)
            if replay is not None:
                if replay[0] != request_digest:
                    raise InvestigationConflictError(
                        "authored trial idempotency key changed semantics"
                    )
                return replay[1]
            request = registration.request
            attempted = state.trials_attempted
            if attempted >= request.budget.max_trials:
                raise ValueError("authored investigation trial budget is exhausted")
            previous_trial = state.last_trial_id
            before_ledger = len(state.evaluator.ledger.records)
            state.trials_attempted += 1
            candidate: AuthoredCandidate | None = None
            try:
                candidate = state.publisher.publish(
                    request,
                    proposal,
                    expected_parent_trial_id=previous_trial,
                )
                evidence = state.evaluator.evaluate(request, candidate)
            except (ScientificProgramError, TypeError, ValueError) as error:
                events = state.evaluator.ledger.records[before_ledger:]
                trial_id = events[0].trial_id if events else None
                if trial_id is not None:
                    state.last_trial_id = trial_id
                disposition = (
                    DevelopmentDisposition.REVISE
                    if attempted + 1 < request.budget.max_trials
                    else DevelopmentDisposition.REJECT
                )
                receipt = _runtime_receipt(
                    registration_id=registration_id,
                    idempotency_key=idempotency_key,
                    trial_ordinal=attempted,
                    trial_id=trial_id,
                    execution_status="failed",
                    disposition=disposition,
                    question_status=(
                        QuestionStatus.ACTIVE
                        if disposition is DevelopmentDisposition.REVISE
                        else QuestionStatus.NEGATIVE
                    ),
                    candidate_id=None if candidate is None else candidate.candidate_id,
                    evidence=None,
                    failure_detail=str(error),
                    ledger_event_ids=tuple(item.event_id for item in events),
                )
                state.receipts[idempotency_key] = (request_digest, receipt)
                return receipt
            state.evidence.append(evidence)
            state.last_trial_id = evidence.trial_id
            self._evidence[evidence.evidence_id] = evidence
            self._candidates[candidate.candidate_id] = candidate
            value = dict(evidence.metrics)[request.budget.primary_metric]
            if value <= request.budget.credible_at_or_below:
                disposition = DevelopmentDisposition.CREDIBLE
                question_status = QuestionStatus.CREDIBLE_CANDIDATE
            elif attempted + 1 >= request.budget.max_trials:
                disposition = DevelopmentDisposition.REJECT
                question_status = QuestionStatus.NEGATIVE
            else:
                disposition = DevelopmentDisposition.REVISE
                question_status = QuestionStatus.ACTIVE
            events = state.evaluator.ledger.records[before_ledger:]
            receipt = _runtime_receipt(
                registration_id=registration_id,
                idempotency_key=idempotency_key,
                trial_ordinal=attempted,
                trial_id=evidence.trial_id,
                execution_status="succeeded",
                disposition=disposition,
                question_status=question_status,
                candidate_id=candidate.candidate_id,
                evidence=evidence,
                failure_detail=None,
                ledger_event_ids=tuple(item.event_id for item in events),
            )
            state.receipts[idempotency_key] = (request_digest, receipt)
            return receipt

    def resolve_evidence(self, evidence_id: str) -> AuthoredDevelopmentEvidence:
        """Resolve exact coordinator-issued evidence for drill-down and later authorities."""
        with self._lock:
            evidence = self._evidence.get(evidence_id)
            if evidence is None:
                raise KeyError(evidence_id)
            return evidence

    def resolve_candidate(self, candidate_id: str) -> AuthoredCandidate:
        """Resolve exact coordinator-issued candidate content."""
        with self._lock:
            candidate = self._candidates.get(candidate_id)
            if candidate is None:
                raise KeyError(candidate_id)
            return candidate

    def require_credible(
        self,
        *,
        candidate_id: str,
        evidence_id: str,
    ) -> tuple[RegisteredInvestigation, AuthoredCandidate, AuthoredDevelopmentEvidence]:
        """Resolve only the exact candidate/evidence pair that earned a credible receipt."""
        with self._lock:
            candidate = self._candidates.get(candidate_id)
            evidence = self._evidence.get(evidence_id)
            if candidate is None or evidence is None:
                raise ValueError("credible candidate or evidence was not coordinator-issued")
            for state in self._states.values():
                if any(
                    receipt.disposition is DevelopmentDisposition.CREDIBLE
                    and receipt.execution_status == "succeeded"
                    and receipt.candidate_id == candidate_id
                    and receipt.evidence_id == evidence_id
                    for _, receipt in state.receipts.values()
                ):
                    return state.registration, candidate, evidence
            raise ValueError("candidate/evidence pair did not earn a credible development receipt")


def _runtime_receipt(  # noqa: PLR0913
    *,
    registration_id: str,
    idempotency_key: str,
    trial_ordinal: int,
    trial_id: str | None,
    execution_status: str,
    disposition: DevelopmentDisposition,
    question_status: QuestionStatus,
    candidate_id: str | None,
    evidence: AuthoredDevelopmentEvidence | None,
    failure_detail: str | None,
    ledger_event_ids: tuple[str, ...],
) -> RuntimeTrialReceipt:
    primary_metric = None if evidence is None else evidence.metrics[0]
    payload = {
        "registration_id": registration_id,
        "idempotency_key": idempotency_key,
        "trial_ordinal": trial_ordinal,
        "trial_id": trial_id,
        "execution_status": execution_status,
        "disposition": disposition,
        "question_status": question_status,
        "candidate_id": candidate_id,
        "evidence_id": None if evidence is None else evidence.evidence_id,
        "primary_metric": primary_metric,
        "failure_detail": failure_detail,
        "ledger_event_ids": ledger_event_ids,
    }
    return RuntimeTrialReceipt(
        receipt_id=stable_identity("runtime-trial-receipt", payload),
        registration_id=registration_id,
        idempotency_key=idempotency_key,
        trial_ordinal=trial_ordinal,
        trial_id=trial_id,
        execution_status=execution_status,
        disposition=disposition,
        question_status=question_status,
        candidate_id=candidate_id,
        evidence_id=None if evidence is None else evidence.evidence_id,
        primary_metric=primary_metric,
        failure_detail=failure_detail,
        ledger_event_ids=ledger_event_ids,
    )


def _researcher_context(
    request: InvestigationRequest,
    ordinal: int,
    evidence: tuple[AuthoredDevelopmentEvidence, ...],
) -> ResearcherContext:
    schemas = tuple(dataset.schema for dataset in request.catalog.datasets)
    return ResearcherContext(
        question=request.question,
        schema_refs=tuple(schema.identity for schema in schemas),
        field_descriptions=tuple(
            (field.field_id, field.description) for schema in schemas for field in schema.fields
        ),
        budget=request.budget,
        trial_ordinal=ordinal,
        prior_evidence=evidence,
    )


def _observation_json(observation: RegisteredObservation) -> dict[str, JsonValue]:
    return {
        "observation_id": observation.observation_id,
        "field_id": observation.field_ref.field_id,
        "value": cast("JsonValue", observation.value),
        "reference_time": observation.reference_time.isoformat(),
        "available_at": observation.available_at.isoformat(),
        "dimensions": [list(item) for item in observation.dimensions],
    }


def _feature_values(value: JsonValue, expected: tuple[str, ...]) -> dict[str, float]:
    if not isinstance(value, dict) or tuple(value) != expected:
        raise ValueError("make_features must return the exact declared ordered outputs")
    return {name: _finite_number(value[name], f"feature {name}") for name in expected}


def _finite_number(value: JsonValue, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        message = f"{name} must be numeric"
        raise TypeError(message)
    result = float(value)
    if not isfinite(result):
        message = f"{name} must be finite"
        raise ValueError(message)
    return result


def _metric(
    budget: DevelopmentBudget,
    predictions: list[float],
    outcomes: list[float],
) -> float:
    errors = tuple(
        prediction - outcome for prediction, outcome in zip(predictions, outcomes, strict=True)
    )
    if budget.primary_metric == "mae":
        return fsum(abs(error) for error in errors) / len(errors)
    return fsum(error * error for error in errors) / len(errors)


__all__ = [
    "AuthoredDevelopmentEvaluator",
    "AutonomousInvestigation",
    "CandidatePublisher",
    "CandidateRegistry",
    "InvestigationConflictError",
    "RuntimeInvestigationCoordinator",
]
