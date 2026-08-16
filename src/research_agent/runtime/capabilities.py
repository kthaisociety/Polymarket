"""Authorized read-only dataset inspection with harness-owned provenance."""

# ruff: noqa: C901, EM101, EM102, PLR0911, PLR0912, PLR0913, PLR0915, TRY003

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import TYPE_CHECKING, cast
from uuid import uuid4

from research_agent.exploration import (
    AnalysisHarness,
    AnalysisRequest,
    AnalysisStatus,
    DataAccessRequest,
)
from research_agent.investigation import (
    AuthoredFreezeService,
    AuthoredProtectedResolutionService,
    AuthoredResolutionStatus,
    DevelopmentDisposition,
    InvestigationConflictError,
    QuestionMemoryRecorder,
    RuntimeInvestigationCoordinator,
)
from research_agent.protected_evaluation import IdempotencyConflictError
from research_agent.runtime.models import (
    AnalysisDataAccess,
    AnalysisExecutionProvenance,
    ExecutionProvenance,
    FailureCode,
    ObservationStatus,
    Recoverability,
    ResearchEnvironmentSnapshot,
    StructuredFailure,
    StructuredObservation,
)
from research_agent.scientific_workflow import (
    ScientificWorkflowCoordinator,
    WorkflowRegistryError,
    WorkflowStatus,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from research_agent.investigation import InvestigationRequest, RegisteredInvestigation
    from research_agent.runtime.actions import (
        InspectDatasetAction,
        RunAnalysisAction,
        RunAuthoredDevelopmentTrialAction,
        RunScientificWorkflowAction,
    )
    from research_agent.runtime.store import InMemoryRuntimeStore

MAX_PREVIEW_ROWS = 8
MONTHS_PER_YEAR = 12
MISSING_PREDICTOR_INDEX = 5


@dataclass(frozen=True, slots=True)
class DatasetDefinition:
    """Tiny immutable dataset and stable semantic schema."""

    dataset_ref: str
    version: str
    field_semantics: Mapping[str, str]
    rows: tuple[Mapping[str, object], ...]


@dataclass(frozen=True, slots=True)
class CapabilityExecutionResult:
    """Capability computation facts before harness authority is assembled."""

    payload: Mapping[str, object]
    artifact: Mapping[str, object]
    accessed_field_ids: tuple[str, ...]


class DatasetRepository:
    """Read-only repository used through AuthorizedDataView."""

    def __init__(self, datasets: tuple[DatasetDefinition, ...]) -> None:
        """Index exact immutable dataset definitions by stable reference."""
        self._datasets = {dataset.dataset_ref: dataset for dataset in datasets}

    def exists(self, dataset_ref: str) -> bool:
        """Return whether metadata names a dataset without reading its rows."""
        return dataset_ref in self._datasets

    def load(self, dataset_ref: str) -> DatasetDefinition:
        """Load an exact dataset after the caller has established authority."""
        dataset = self._datasets.get(dataset_ref)
        if dataset is None:
            raise KeyError(dataset_ref)
        return dataset


class AuthorizedDataView:
    """Capability-scoped view that enforces dataset authority before values."""

    def __init__(
        self,
        repository: DatasetRepository,
        environment: ResearchEnvironmentSnapshot,
    ) -> None:
        """Bind repository access to one exact environment authority snapshot."""
        self._repository = repository
        self._environment = environment

    def inspect(
        self,
        dataset_ref: str,
        selected_field_ids: tuple[str, ...],
        preview_limit: int,
    ) -> tuple[DatasetDefinition, tuple[Mapping[str, object], ...], tuple[str, ...]]:
        """Return copied, bounded values only after explicit authorization."""
        if dataset_ref not in self._environment.readable_dataset_refs:
            raise PermissionError(dataset_ref)
        dataset = self._repository.load(dataset_ref)
        fields = selected_field_ids or tuple(dataset.field_semantics)
        if any(field not in dataset.field_semantics for field in fields):
            raise ValueError("Request names an unknown semantic field ID.")
        if preview_limit < 1 or preview_limit > MAX_PREVIEW_ROWS:
            raise ValueError(f"preview_limit must be between 1 and {MAX_PREVIEW_ROWS}.")
        preview = tuple(
            {field: row.get(field) for field in fields} for row in dataset.rows[:preview_limit]
        )
        return dataset, preview, fields


class InspectDatasetCapability:
    """Compute descriptive inspection facts without scientific interpretation."""

    name = "inspect_dataset"

    def execute(
        self,
        view: AuthorizedDataView,
        action: InspectDatasetAction,
    ) -> CapabilityExecutionResult:
        """Return bounded payload, drill-down artifact, and actual fields."""
        dataset, preview, fields = view.inspect(
            action.dataset_ref,
            action.selected_field_ids,
            action.preview_limit,
        )
        missingness = {
            field: sum(row.get(field) is None for row in dataset.rows) for field in fields
        }
        reference_times = [str(row["reference_time"]) for row in dataset.rows]
        payload: dict[str, object] = {
            "dataset_ref": dataset.dataset_ref,
            "dataset_version": dataset.version,
            "row_count": len(dataset.rows),
            "field_semantics": {field: dataset.field_semantics[field] for field in fields},
            "temporal_coverage": (min(reference_times), max(reference_times)),
            "missingness": missingness,
            "preview": preview,
        }
        artifact = {
            "inspection_payload": payload,
            "requested_fields": fields,
            "source_row_count": len(dataset.rows),
        }
        return CapabilityExecutionResult(payload, artifact, fields)


class ActionRouter:
    """Validate identity/authority and assemble authoritative observations."""

    def __init__(
        self,
        store: InMemoryRuntimeStore,
        datasets: DatasetRepository,
        *,
        analysis_harnesses: Mapping[str, AnalysisHarness] | None = None,
        scientific_workflow: ScientificWorkflowCoordinator | None = None,
        investigations: RuntimeInvestigationCoordinator | None = None,
        authored_freeze: AuthoredFreezeService | None = None,
        authored_resolution: AuthoredProtectedResolutionService | None = None,
        authored_memory: QuestionMemoryRecorder | None = None,
    ) -> None:
        """Configure authorized inspection against runtime-owned persistence."""
        self._store = store
        self._datasets = datasets
        self._capability = InspectDatasetCapability()
        self._analysis_harnesses = dict(analysis_harnesses or {})
        self._scientific_workflow = scientific_workflow
        self._investigations = investigations
        self._authored_freeze = authored_freeze
        self._authored_resolution = authored_resolution
        self._authored_memory = authored_memory

    def register_investigation(
        self,
        request: InvestigationRequest,
        *,
        session_id: str,
    ) -> RegisteredInvestigation:
        """Publish one model-visible question/data/budget scope from trusted composition."""
        task, environment, session, _, episode = self._store.coherent_view(session_id)
        coordinator = self._investigations
        if coordinator is None:
            raise ValueError("runtime has no authored investigation authority")
        catalog_refs = frozenset(dataset.schema.dataset_id for dataset in request.catalog.datasets)
        if (
            request.question.task_ref != task.task_id
            or request.catalog.environment_id != environment.environment_id
            or not catalog_refs <= frozenset(environment.dataset_refs)
            or not catalog_refs <= frozenset(environment.readable_dataset_refs)
            or bool(catalog_refs & frozenset(environment.protected_resource_refs))
            or "run_authored_development_trial" not in environment.capability_names
        ):
            raise PermissionError("investigation scope is outside runtime authority")
        registration = coordinator.register(
            request,
            session_id=session.session_id,
            episode_id=episode.episode_id,
        )
        prior_question_memory = coordinator.memory_context(registration.registration_id)
        memory_artifact_refs: list[str] = []
        for record in prior_question_memory:
            artifact_ref = f"question-memory:{record.memory_id}"
            self._store.put_artifact(artifact_ref, record)
            memory_artifact_refs.append(artifact_ref)
        field_descriptions = tuple(
            (field.field_id, field.description)
            for dataset in request.catalog.datasets
            for field in dataset.schema.fields
        )
        field_definitions = tuple(
            {
                "field_ref": {
                    "dataset_id": dataset.schema.dataset_id,
                    "schema_version": dataset.schema.version,
                    "field_id": field.field_id,
                    "environment_id": dataset.schema.environment_id,
                },
                "semantic_name": field.semantic_name,
                "data_type": field.data_type,
                "unit": field.unit,
                "dimensions": field.dimensions,
                "description": field.description,
            }
            for dataset in sorted(
                request.catalog.datasets,
                key=lambda item: (item.schema.dataset_id, item.schema.version),
            )
            for field in sorted(dataset.schema.fields, key=lambda item: item.field_id)
        )
        analysis_surfaces: tuple[dict[str, object], ...] = ()
        if "run_analysis" in environment.capability_names:
            harness = self._analysis_harnesses.get(session.session_id)
            if harness is None:
                raise PermissionError("runtime advertises analysis without a session-bound harness")
            analysis_surfaces = tuple(
                {
                    "view_id": surface.view_id,
                    "dataset_ref": surface.dataset_ref,
                    "environment_ref": surface.environment_ref,
                    "field_ids": surface.field_ids,
                }
                for surface in harness.authorized_runtime_surfaces(
                    session_id=session.session_id,
                    environment_ref=environment.snapshot_ref,
                    readable_dataset_refs=environment.readable_dataset_refs,
                    protected_resource_refs=environment.protected_resource_refs,
                    investigation_dataset_refs=catalog_refs,
                )
            )
        memory_warnings = (
            (
                (
                    "Prior terminal question memory is present; research only the explicit "
                    "new-catalog or material-hypothesis delta."
                ),
            )
            if prior_question_memory
            else ()
        )
        action_id = f"register-investigation:{registration.registration_id}"
        observation = StructuredObservation(
            observation_id=f"observation:{session.session_id}:{action_id}",
            delivery_id=f"delivery:{session.session_id}:{action_id}",
            session_id=session.session_id,
            episode_id=episode.episode_id,
            environment_ref=environment.snapshot_ref,
            action_id=action_id,
            status=ObservationStatus.SUCCEEDED,
            observation_type="authored_investigation_registered",
            summary="An authored investigation question, data scope, and budget are available.",
            payload={
                "investigation_id": registration.registration_id,
                "question_id": request.question.question_id,
                "question": request.question.text,
                "catalog_id": request.catalog.identity,
                "dataset_refs": tuple(sorted(catalog_refs)),
                "field_descriptions": field_descriptions,
                "field_definitions": field_definitions,
                "analysis_surfaces": analysis_surfaces,
                "sample_key_count": len(request.sample_keys),
                "current_time": request.current_time.isoformat(),
                "budget_id": request.budget.identity,
                "max_trials": request.budget.max_trials,
                "minimum_training_rows": request.budget.minimum_training_rows,
                "minimum_oof_predictions": request.budget.minimum_oof_predictions,
                "primary_metric": request.budget.primary_metric,
                "credible_at_or_below": request.budget.credible_at_or_below,
                "protected_protocol_refs": (
                    ()
                    if request.protected_predeclaration is None
                    else request.protected_predeclaration.protocol_refs
                ),
                "freeze_standard_ref": (
                    None
                    if request.protected_predeclaration is None
                    else request.protected_predeclaration.freeze_standard_ref
                ),
                "reopen": (
                    None
                    if request.reopen is None
                    else {
                        "prior_memory_id": request.reopen.prior_memory_id,
                        "reason": request.reopen.reason.value,
                        "rationale": request.reopen.rationale,
                    }
                ),
                "prior_question_memory": tuple(
                    {
                        "memory_id": record.memory_id,
                        "status": record.status.value,
                        "question_id": record.question_id,
                        "question": record.question_text,
                        "catalog_id": record.catalog_id,
                        "terminal_evidence_ref": record.terminal_evidence_ref,
                        "reason_codes": record.reason_codes,
                        "resolved_at": record.resolved_at.isoformat(),
                    }
                    for record in prior_question_memory
                ),
            },
            warnings=(
                "The researcher must author the feature, label, fit, and prediction methods.",
                "Development evidence is selection-exposed and cannot claim validation.",
                *memory_warnings,
            ),
            provenance=ExecutionProvenance(
                session_id=session.session_id,
                environment_ref=environment.snapshot_ref,
                capability_name="register_authored_investigation",
                authorized_dataset_ref=None,
                selected_field_ids=tuple(field_id for field_id, _ in field_descriptions),
                preview_limit=None,
                dataset_refs=tuple(sorted(catalog_refs)),
                environment_refs=(environment.snapshot_ref,),
                random_seed=request.random_seed,
                execution_status="registered",
            ),
            artifact_refs=tuple(memory_artifact_refs),
            recoverability=Recoverability.NON_RETRYABLE,
            epistemic_status="DEVELOPMENT_SETUP",
        )
        self._store.record_observation(session_id, observation)
        self._store.append_event(
            session_id,
            "investigation.registered",
            {
                "investigation_id": registration.registration_id,
                "observation_id": observation.observation_id,
            },
        )
        return registration

    def execute_inspection(self, action: InspectDatasetAction) -> StructuredObservation:
        """Execute one authorized inspection or return a safe denial/failure."""
        _, environment, session, _, episode = self._store.coherent_view(action.session_id)
        self._store.append_event(
            action.session_id,
            "action.requested",
            {"action_id": action.action_id, "kind": "inspect_dataset"},
        )
        if action.episode_id != episode.episode_id or action.session_id != session.session_id:
            return self._failure(
                action,
                FailureCode.INVALID_REQUEST,
                "Action identity does not match the active session and episode.",
                Recoverability.REPAIRABLE,
            )
        if self._capability.name not in environment.capability_names:
            return self._failure(
                action,
                FailureCode.AUTHORITY_DENIED,
                "The session is not authorized to use dataset inspection.",
                Recoverability.NON_RETRYABLE,
            )
        if action.dataset_ref not in environment.dataset_refs or not self._datasets.exists(
            action.dataset_ref
        ):
            return self._failure(
                action,
                FailureCode.NOT_FOUND,
                "The requested dataset reference does not exist in this environment.",
                Recoverability.REPAIRABLE,
            )
        if action.dataset_ref not in environment.readable_dataset_refs:
            return self._failure(
                action,
                FailureCode.AUTHORITY_DENIED,
                "The requested dataset is not readable in this session.",
                Recoverability.NON_RETRYABLE,
            )
        self._store.append_event(
            action.session_id,
            "action.authorized",
            {"action_id": action.action_id, "dataset_ref": action.dataset_ref},
        )
        try:
            execution = self._capability.execute(
                AuthorizedDataView(self._datasets, environment),
                action,
            )
        except (KeyError, PermissionError, ValueError) as error:
            diagnostic_ref = f"artifact:diagnostic:{uuid4()}"
            self._store.put_artifact(diagnostic_ref, {"error_type": type(error).__name__})
            return self._failure(
                action,
                FailureCode.INVALID_REQUEST,
                "Dataset inspection request was invalid.",
                Recoverability.REPAIRABLE,
                diagnostic_ref,
            )
        artifact_ref = f"artifact:inspection:{uuid4()}"
        self._store.put_artifact(artifact_ref, execution.artifact)
        provenance = ExecutionProvenance(
            session_id=session.session_id,
            environment_ref=environment.snapshot_ref,
            capability_name=self._capability.name,
            authorized_dataset_ref=action.dataset_ref,
            selected_field_ids=execution.accessed_field_ids,
            preview_limit=action.preview_limit,
        )
        observation = StructuredObservation(
            observation_id=f"observation:{session.session_id}:{action.action_id}",
            delivery_id=f"delivery:{session.session_id}:{action.action_id}",
            session_id=session.session_id,
            episode_id=episode.episode_id,
            environment_ref=environment.snapshot_ref,
            action_id=action.action_id,
            status=ObservationStatus.SUCCEEDED,
            observation_type="dataset_inspection",
            summary=(f"Inspected {action.dataset_ref!r}: {execution.payload['row_count']} rows."),
            payload=execution.payload,
            warnings=("Temporal legality is not evaluated by this Milestone 1 inspection.",),
            provenance=provenance,
            artifact_refs=(artifact_ref,),
            recoverability=Recoverability.REPAIRABLE,
        )
        self._store.append_event(
            action.session_id,
            "capability.executed",
            {"action_id": action.action_id, "artifact_ref": artifact_ref},
        )
        self._store.append_event(
            action.session_id,
            "observation.assembled",
            {"observation_id": observation.observation_id},
        )
        return observation

    def execute_analysis(self, action: RunAnalysisAction) -> StructuredObservation:
        """Authorize and execute provisional analysis through its session-bound harness."""
        _, environment, session, _, episode = self._store.coherent_view(action.session_id)
        self._store.append_event(
            action.session_id,
            "action.requested",
            {"action_id": action.action_id, "kind": "run_analysis"},
        )
        if action.episode_id != episode.episode_id or action.session_id != session.session_id:
            return self._analysis_failure(
                action,
                FailureCode.INVALID_REQUEST,
                "Action identity does not match the active session and episode.",
                Recoverability.REPAIRABLE,
            )
        if "run_analysis" not in environment.capability_names:
            return self._analysis_failure(
                action,
                FailureCode.AUTHORITY_DENIED,
                "The session is not authorized to run exploratory analysis.",
                Recoverability.NON_RETRYABLE,
            )
        harness = self._analysis_harnesses.get(session.session_id)
        requested_view_ids = tuple(access.view_id for access in action.data_access)
        if harness is None or not harness.accepts_runtime_scope(
            session_id=session.session_id,
            environment_ref=environment.snapshot_ref,
            readable_dataset_refs=environment.readable_dataset_refs,
            protected_resource_refs=environment.protected_resource_refs,
            requested_view_ids=requested_view_ids,
        ):
            return self._analysis_failure(
                action,
                FailureCode.AUTHORITY_DENIED,
                "The requested analysis view is not authorized for this session environment.",
                Recoverability.NON_RETRYABLE,
            )
        self._store.append_event(
            action.session_id,
            "action.authorized",
            {"action_id": action.action_id, "capability": "run_analysis"},
        )
        result = harness.run(
            AnalysisRequest(
                session_id=action.session_id,
                action_id=action.action_id,
                source=action.source,
                data_access=tuple(
                    DataAccessRequest(access.view_id, access.field_ids)
                    for access in action.data_access
                ),
                random_seed=action.random_seed,
            )
        )
        artifact_refs: list[str] = []
        for ref in result.artifact_refs:
            runtime_ref = f"analysis-artifact:{ref.artifact_id}"
            self._store.put_artifact(runtime_ref, ref)
            artifact_refs.append(runtime_ref)
        provenance = AnalysisExecutionProvenance(
            session_id=session.session_id,
            environment_ref=environment.snapshot_ref,
            capability_name="run_analysis",
            authorized_dataset_ref=None,
            selected_field_ids=tuple(access.field_id for access in result.provenance.accesses),
            preview_limit=None,
            code_sha256=result.provenance.code_sha256,
            accesses=tuple(
                AnalysisDataAccess(
                    ordinal=access.ordinal,
                    view_id=access.view_id,
                    dataset_ref=access.dataset_ref,
                    environment_ref=access.environment_ref,
                    field_id=access.field_id,
                )
                for access in result.provenance.accesses
            ),
            dataset_refs=result.provenance.dataset_refs,
            environment_refs=result.provenance.environment_refs,
            random_seed=result.provenance.random_seed,
            execution_status=result.provenance.execution_status.value,
        )
        status = {
            AnalysisStatus.SUCCEEDED: ObservationStatus.SUCCEEDED,
            AnalysisStatus.FAILED: ObservationStatus.FAILED,
            AnalysisStatus.DENIED: ObservationStatus.REJECTED,
        }[result.status]
        recoverability = (
            Recoverability.REPAIRABLE if result.recoverable else Recoverability.NON_RETRYABLE
        )
        failure: StructuredFailure | None = None
        if result.status is not AnalysisStatus.SUCCEEDED:
            failure = StructuredFailure(
                FailureCode.AUTHORITY_DENIED
                if result.status is AnalysisStatus.DENIED
                else FailureCode.INTERNAL_FAILURE,
                result.summary,
                recoverability,
                artifact_refs[-1] if artifact_refs else None,
            )
        payload: dict[str, object] = {
            "details": cast("object", result.details),
            "stdout_preview": result.stdout_preview,
            "stderr_preview": result.stderr_preview,
            "actual_accesses": tuple(
                {
                    "ordinal": access.ordinal,
                    "view_id": access.view_id,
                    "dataset_ref": access.dataset_ref,
                    "environment_ref": access.environment_ref,
                    "field_id": access.field_id,
                }
                for access in result.provenance.accesses
            ),
            "code_sha256": result.provenance.code_sha256,
            "random_seed": result.provenance.random_seed,
            "execution_status": result.status.value,
        }
        observation = StructuredObservation(
            observation_id=f"observation:{session.session_id}:{action.action_id}",
            delivery_id=f"delivery:{session.session_id}:{action.action_id}",
            session_id=session.session_id,
            episode_id=episode.episode_id,
            environment_ref=environment.snapshot_ref,
            action_id=action.action_id,
            status=status,
            observation_type="analysis_result"
            if result.status is AnalysisStatus.SUCCEEDED
            else "analysis_failure",
            summary=result.summary,
            payload=payload,
            warnings=result.warnings,
            provenance=provenance,
            artifact_refs=tuple(artifact_refs),
            recoverability=recoverability,
            failure=failure,
            epistemic_status=result.epistemic_status,
        )
        self._store.append_event(
            action.session_id,
            "capability.executed",
            {
                "action_id": action.action_id,
                "status": result.status.value,
                "artifact_refs": tuple(artifact_refs),
            },
        )
        self._store.append_event(
            action.session_id,
            "observation.assembled",
            {"observation_id": observation.observation_id},
        )
        return observation

    def execute_scientific_workflow(
        self,
        action: RunScientificWorkflowAction,
    ) -> StructuredObservation:
        """Authorize one exact registered scientific graph and return provisional evidence."""
        task, environment, session, _, episode = self._store.coherent_view(action.session_id)
        self._store.append_event(
            action.session_id,
            "action.requested",
            {"action_id": action.action_id, "kind": "run_scientific_workflow"},
        )
        if action.episode_id != episode.episode_id or action.session_id != session.session_id:
            return self._workflow_failure(
                action,
                FailureCode.INVALID_REQUEST,
                "Action identity does not match the active session and episode.",
                Recoverability.REPAIRABLE,
            )
        if "run_scientific_workflow" not in environment.capability_names:
            return self._workflow_failure(
                action,
                FailureCode.AUTHORITY_DENIED,
                "The session is not authorized to run registered scientific workflows.",
                Recoverability.NON_RETRYABLE,
            )
        coordinator = self._scientific_workflow
        if coordinator is None:
            return self._workflow_failure(
                action,
                FailureCode.NOT_FOUND,
                "No scientific workflow coordinator is registered for this runtime.",
                Recoverability.REPAIRABLE,
            )
        try:
            coordinator.authorize(
                workflow_id=action.workflow_id,
                session_id=session.session_id,
                episode_id=episode.episode_id,
            )
        except WorkflowRegistryError:
            return self._workflow_failure(
                action,
                FailureCode.AUTHORITY_DENIED,
                "The workflow is not registered for this exact task and session authority.",
                Recoverability.NON_RETRYABLE,
            )
        self._store.append_event(
            action.session_id,
            "action.authorized",
            {
                "action_id": action.action_id,
                "capability": "run_scientific_workflow",
                "task_id": task.task_id,
                "environment_ref": environment.snapshot_ref,
                "workflow_id": action.workflow_id,
            },
        )
        try:
            receipt = coordinator.execute(
                workflow_id=action.workflow_id,
                idempotency_key=action.idempotency_key,
                session_id=session.session_id,
                episode_id=episode.episode_id,
            )
        except WorkflowRegistryError:
            return self._workflow_failure(
                action,
                FailureCode.AUTHORITY_DENIED,
                "The workflow is not registered for this exact task and session authority.",
                Recoverability.NON_RETRYABLE,
            )
        except IdempotencyConflictError:
            return self._workflow_failure(
                action,
                FailureCode.IDEMPOTENCY_CONFLICT,
                "The workflow idempotency key was reused with changed semantics.",
                Recoverability.NON_RETRYABLE,
            )
        receipt_ref = f"workflow-receipt:{receipt.receipt_id}"
        self._store.put_artifact(receipt_ref, receipt)
        status = {
            WorkflowStatus.FINDING: ObservationStatus.SUCCEEDED,
            WorkflowStatus.REJECTED: ObservationStatus.REJECTED,
            WorkflowStatus.DENIED: ObservationStatus.REJECTED,
            WorkflowStatus.FAILED: ObservationStatus.FAILED,
        }[receipt.status]
        recoverability = (
            Recoverability.REPAIRABLE
            if receipt.status in {WorkflowStatus.REJECTED, WorkflowStatus.FAILED}
            else Recoverability.NON_RETRYABLE
        )
        failure = None
        if receipt.status is not WorkflowStatus.FINDING:
            failure = StructuredFailure(
                FailureCode.AUTHORITY_DENIED
                if receipt.status is WorkflowStatus.DENIED
                else FailureCode.INVALID_REQUEST,
                f"Scientific workflow ended with status {receipt.status.value!r}.",
                recoverability,
                receipt_ref,
            )
        observation = StructuredObservation(
            observation_id=f"observation:{session.session_id}:{action.action_id}",
            delivery_id=f"delivery:{session.session_id}:{action.action_id}",
            session_id=session.session_id,
            episode_id=episode.episode_id,
            environment_ref=environment.snapshot_ref,
            action_id=action.action_id,
            status=status,
            observation_type="scientific_workflow_result",
            summary=f"Registered scientific workflow ended with {receipt.status.value!r}.",
            payload={
                "workflow_id": receipt.workflow_id,
                "receipt_id": receipt.receipt_id,
                "workflow_status": receipt.status.value,
                "evidence_refs": receipt.evidence_refs,
                "finding_ref": receipt.finding_ref,
                "negative_result_ref": receipt.negative_result_ref,
                "report_ref": receipt.rendered_report_ref,
                "reason_codes": receipt.reason_codes,
            },
            warnings=("Workflow evidence remains provisional until a separate semantic commit.",),
            provenance=ExecutionProvenance(
                session_id=session.session_id,
                environment_ref=environment.snapshot_ref,
                capability_name="run_scientific_workflow",
                authorized_dataset_ref=None,
                selected_field_ids=(),
                preview_limit=None,
            ),
            artifact_refs=(receipt_ref,),
            recoverability=recoverability,
            failure=failure,
            epistemic_status="PROVISIONAL",
        )
        self._store.append_event(
            action.session_id,
            "capability.executed",
            {
                "action_id": action.action_id,
                "workflow_id": receipt.workflow_id,
                "receipt_id": receipt.receipt_id,
                "status": receipt.status.value,
            },
        )
        self._store.append_event(
            action.session_id,
            "observation.assembled",
            {"observation_id": observation.observation_id},
        )
        return observation

    def execute_authored_development_trial(
        self,
        action: RunAuthoredDevelopmentTrialAction,
    ) -> StructuredObservation:
        """Run one model-authored candidate revision under a registered legal scope."""
        task, environment, session, _, episode = self._store.coherent_view(action.session_id)
        self._store.append_event(
            action.session_id,
            "action.requested",
            {"action_id": action.action_id, "kind": "run_authored_development_trial"},
        )
        if action.episode_id != episode.episode_id or action.session_id != session.session_id:
            return self._authored_trial_failure(
                action,
                FailureCode.INVALID_REQUEST,
                "Action identity does not match the active session and episode.",
                Recoverability.REPAIRABLE,
            )
        if "run_authored_development_trial" not in environment.capability_names:
            return self._authored_trial_failure(
                action,
                FailureCode.AUTHORITY_DENIED,
                "The session is not authorized to execute authored development trials.",
                Recoverability.NON_RETRYABLE,
            )
        coordinator = self._investigations
        if coordinator is None:
            return self._authored_trial_failure(
                action,
                FailureCode.NOT_FOUND,
                "No authored investigation authority is configured for this runtime.",
                Recoverability.REPAIRABLE,
            )
        try:
            registration = coordinator.authorize(
                action.investigation_id,
                session_id=session.session_id,
                episode_id=episode.episode_id,
            )
        except (KeyError, PermissionError):
            return self._authored_trial_failure(
                action,
                FailureCode.AUTHORITY_DENIED,
                "The authored investigation is not registered for this exact runtime scope.",
                Recoverability.NON_RETRYABLE,
            )
        request = registration.request
        catalog_refs = frozenset(dataset.schema.dataset_id for dataset in request.catalog.datasets)
        if (
            request.question.task_ref != task.task_id
            or request.catalog.environment_id != environment.environment_id
            or not catalog_refs <= frozenset(environment.dataset_refs)
            or not catalog_refs <= frozenset(environment.readable_dataset_refs)
        ):
            return self._authored_trial_failure(
                action,
                FailureCode.AUTHORITY_DENIED,
                "The registered investigation crosses task, environment, or readable data scope.",
                Recoverability.NON_RETRYABLE,
            )
        self._store.append_event(
            action.session_id,
            "action.authorized",
            {
                "action_id": action.action_id,
                "capability": "run_authored_development_trial",
                "investigation_id": action.investigation_id,
            },
        )
        try:
            receipt = coordinator.execute(
                action.investigation_id,
                action.proposal,
                session_id=session.session_id,
                episode_id=episode.episode_id,
                idempotency_key=action.idempotency_key,
            )
        except InvestigationConflictError:
            return self._authored_trial_failure(
                action,
                FailureCode.IDEMPOTENCY_CONFLICT,
                "The authored trial idempotency key was reused with changed semantics.",
                Recoverability.NON_RETRYABLE,
            )
        except (KeyError, PermissionError, TypeError, ValueError):
            return self._authored_trial_failure(
                action,
                FailureCode.INVALID_REQUEST,
                "The authored development trial request was invalid.",
                Recoverability.REPAIRABLE,
            )
        receipt_ref = f"authored-trial-receipt:{receipt.receipt_id}"
        self._store.put_artifact(receipt_ref, receipt)
        artifact_refs = [receipt_ref]
        evidence = None
        if receipt.evidence_id is not None:
            evidence = coordinator.resolve_evidence(receipt.evidence_id)
            evidence_ref = f"authored-development-evidence:{evidence.evidence_id}"
            self._store.put_artifact(evidence_ref, evidence)
            artifact_refs.append(evidence_ref)
        freeze_outcome = None
        freeze_status = "not_requested"
        freeze_warning: tuple[str, ...] = ()
        resolution = None
        resolution_status = "not_requested"
        memory_record = None
        memory_status = "not_requested"
        memory_warning: tuple[str, ...] = ()
        if (
            receipt.disposition is DevelopmentDisposition.CREDIBLE
            and receipt.candidate_id is not None
            and receipt.evidence_id is not None
        ):
            freeze_service = self._authored_freeze
            if freeze_service is None:
                freeze_status = "not_configured"
                message = (
                    "Credible candidate was not frozen because no independent freeze service "
                    "is configured."
                )
                freeze_warning = (message,)
            else:
                try:
                    freeze_outcome = freeze_service.assess_credible(
                        candidate_id=receipt.candidate_id,
                        evidence_id=receipt.evidence_id,
                        requester_id=session.session_id,
                        beneficiary_id=task.task_id,
                    )
                    freeze_status = freeze_outcome.decision.status.value
                    freeze_ref = f"authored-freeze:{freeze_outcome.decision.decision_id}"
                    self._store.put_artifact(freeze_ref, freeze_outcome)
                    artifact_refs.append(freeze_ref)
                except ValueError:
                    freeze_status = "denied"
                    freeze_warning = (
                        "Independent freeze assessment denied or lacked exact predeclaration.",
                    )
                if freeze_outcome is not None and freeze_outcome.frozen is not None:
                    resolution_service = self._authored_resolution
                    if resolution_service is None:
                        resolution_status = "not_configured"
                        message = (
                            "Frozen authored candidate was not run because no independent "
                            "protected resolution service is configured."
                        )
                        freeze_warning = (message,)
                    else:
                        try:
                            resolution = resolution_service.resolve(
                                candidate_id=receipt.candidate_id,
                                evidence_id=receipt.evidence_id,
                                frozen_system_id=freeze_outcome.frozen.frozen_system_id,
                                requester_id=session.session_id,
                                beneficiary_id=task.task_id,
                                recipient_id=f"researcher:{session.session_id}",
                                idempotency_key=f"protected:{action.idempotency_key}",
                            )
                            resolution_status = resolution.status.value
                            resolution_ref = (
                                f"authored-protected-resolution:{resolution.resolution_id}"
                            )
                            self._store.put_artifact(resolution_ref, resolution)
                            artifact_refs.append(resolution_ref)
                        except ValueError:
                            resolution_status = "failed"
                            freeze_warning = (
                                "Independent protected resolution failed closed after freeze.",
                            )
                    if resolution is not None and resolution.status in {
                        AuthoredResolutionStatus.FINDING,
                        AuthoredResolutionStatus.REJECTED,
                    }:
                        memory_recorder = self._authored_memory
                        if memory_recorder is None:
                            memory_status = "not_configured"
                            message = (
                                "Protected resolution was not added to validated question memory "
                                "because no memory authority is configured."
                            )
                            memory_warning = (message,)
                        else:
                            try:
                                memory_record = memory_recorder.record(resolution)
                                memory_status = "recorded"
                                memory_ref = f"question-memory:{memory_record.memory_id}"
                                self._store.put_artifact(memory_ref, memory_record)
                                artifact_refs.append(memory_ref)
                            except ValueError:
                                memory_status = "failed"
                                memory_warning = (
                                    "Validated question-memory publication failed closed.",
                                )
        status = (
            ObservationStatus.FAILED
            if receipt.execution_status == "failed"
            or resolution_status == "failed"
            or memory_status == "failed"
            else ObservationStatus.REJECTED
            if resolution is not None
            and resolution.status
            in {AuthoredResolutionStatus.REJECTED, AuthoredResolutionStatus.DENIED}
            else ObservationStatus.REJECTED
            if receipt.disposition is DevelopmentDisposition.REJECT
            else ObservationStatus.SUCCEEDED
        )
        recoverability = (
            Recoverability.REPAIRABLE
            if receipt.disposition is DevelopmentDisposition.REVISE
            else Recoverability.NON_RETRYABLE
        )
        failure = None
        if receipt.execution_status == "failed":
            failure = StructuredFailure(
                FailureCode.INVALID_REQUEST,
                receipt.failure_detail or "Authored development program failed.",
                recoverability,
                receipt_ref,
            )
        elif resolution_status == "failed":
            failure = StructuredFailure(
                FailureCode.INTERNAL_FAILURE,
                "Independent protected resolution failed closed.",
                Recoverability.NON_RETRYABLE,
                receipt_ref,
            )
        elif memory_status == "failed":
            failure = StructuredFailure(
                FailureCode.INTERNAL_FAILURE,
                "Validated question-memory publication failed closed.",
                Recoverability.REPAIRABLE,
                receipt_ref,
            )
        actual_accesses = ()
        if evidence is not None:
            actual_accesses = tuple(
                {
                    "entrypoint": access.entrypoint,
                    "ordinal": access.ordinal,
                    "interface": access.interface,
                    "field_id": access.field_id,
                }
                for access in (
                    *evidence.feature_accesses,
                    *evidence.label_accesses,
                    *evidence.fit_accesses,
                    *evidence.prediction_accesses,
                )
            )
        observation = StructuredObservation(
            observation_id=f"observation:{session.session_id}:{action.action_id}",
            delivery_id=f"delivery:{session.session_id}:{action.action_id}",
            session_id=session.session_id,
            episode_id=episode.episode_id,
            environment_ref=environment.snapshot_ref,
            action_id=action.action_id,
            status=status,
            observation_type="authored_development_trial",
            summary=(
                "Authored development trial ended with "
                f"{receipt.disposition.value!r} after {receipt.execution_status!r} execution."
            ),
            payload={
                "investigation_id": receipt.registration_id,
                "receipt_id": receipt.receipt_id,
                "trial_ordinal": receipt.trial_ordinal,
                "trial_id": receipt.trial_id,
                "execution_status": receipt.execution_status,
                "disposition": receipt.disposition.value,
                "question_status": receipt.question_status.value,
                "candidate_id": receipt.candidate_id,
                "evidence_id": receipt.evidence_id,
                "primary_metric": receipt.primary_metric,
                "ledger_event_ids": receipt.ledger_event_ids,
                "actual_accesses": actual_accesses,
                "freeze_status": freeze_status,
                "freeze_decision_id": (
                    None if freeze_outcome is None else freeze_outcome.decision.decision_id
                ),
                "frozen_system_id": (
                    None
                    if freeze_outcome is None or freeze_outcome.frozen is None
                    else freeze_outcome.frozen.frozen_system_id
                ),
                "protected_resolution_status": resolution_status,
                "protected_resolution_id": (
                    None if resolution is None else resolution.resolution_id
                ),
                "protected_evidence_refs": (() if resolution is None else resolution.evidence_refs),
                "finding_id": None if resolution is None else resolution.finding_id,
                "negative_result_id": (
                    None if resolution is None else resolution.negative_result_id
                ),
                "protected_reason_codes": (() if resolution is None else resolution.reason_codes),
                "question_memory_status": memory_status,
                "question_memory_id": (None if memory_record is None else memory_record.memory_id),
            },
            warnings=(
                "Authored evidence is selection-exposed DEVELOPMENT evidence, not validation.",
                *freeze_warning,
                *memory_warning,
            ),
            provenance=ExecutionProvenance(
                session_id=session.session_id,
                environment_ref=environment.snapshot_ref,
                capability_name="run_authored_development_trial",
                authorized_dataset_ref=None,
                selected_field_ids=tuple(
                    field.field_id for field in action.proposal.manifest.predictor_fields
                ),
                preview_limit=None,
                code_sha256=sha256(action.proposal.source.encode()).hexdigest(),
                dataset_refs=tuple(sorted(catalog_refs)),
                environment_refs=(environment.snapshot_ref,),
                random_seed=request.random_seed,
                execution_status=receipt.execution_status,
            ),
            artifact_refs=tuple(artifact_refs),
            recoverability=recoverability,
            failure=failure,
            epistemic_status=(
                "PROTECTED_VALIDATED"
                if resolution is not None and resolution.status is AuthoredResolutionStatus.FINDING
                else "PROTECTED_REJECTED"
                if resolution is not None and resolution.status is AuthoredResolutionStatus.REJECTED
                else "DEVELOPMENT"
            ),
        )
        self._store.append_event(
            action.session_id,
            "capability.executed",
            {
                "action_id": action.action_id,
                "investigation_id": action.investigation_id,
                "receipt_id": receipt.receipt_id,
                "disposition": receipt.disposition.value,
            },
        )
        self._store.append_event(
            action.session_id,
            "observation.assembled",
            {"observation_id": observation.observation_id},
        )
        return observation

    def _authored_trial_failure(
        self,
        action: RunAuthoredDevelopmentTrialAction,
        code: FailureCode,
        message: str,
        recoverability: Recoverability,
    ) -> StructuredObservation:
        """Return a safe denial without candidate publication or worker execution."""
        _, environment, session, _, episode = self._store.coherent_view(action.session_id)
        failure = StructuredFailure(code, message, recoverability)
        observation = StructuredObservation(
            observation_id=f"observation:{session.session_id}:{action.action_id}",
            delivery_id=f"delivery:{session.session_id}:{action.action_id}",
            session_id=session.session_id,
            episode_id=episode.episode_id,
            environment_ref=environment.snapshot_ref,
            action_id=action.action_id,
            status=ObservationStatus.REJECTED,
            observation_type="authored_development_trial_failure",
            summary=message,
            payload={"failure_code": code.value},
            warnings=(),
            provenance=None,
            artifact_refs=(),
            recoverability=recoverability,
            failure=failure,
            epistemic_status="DEVELOPMENT",
        )
        self._store.append_event(
            action.session_id,
            "action.rejected",
            {"action_id": action.action_id, "failure_code": code.value},
        )
        return observation

    def _workflow_failure(
        self,
        action: RunScientificWorkflowAction,
        code: FailureCode,
        message: str,
        recoverability: Recoverability,
    ) -> StructuredObservation:
        """Return a safe workflow denial without claiming scientific execution."""
        _, environment, session, _, episode = self._store.coherent_view(action.session_id)
        failure = StructuredFailure(code, message, recoverability)
        observation = StructuredObservation(
            observation_id=f"observation:{session.session_id}:{action.action_id}",
            delivery_id=f"delivery:{session.session_id}:{action.action_id}",
            session_id=session.session_id,
            episode_id=episode.episode_id,
            environment_ref=environment.snapshot_ref,
            action_id=action.action_id,
            status=ObservationStatus.REJECTED,
            observation_type="scientific_workflow_failure",
            summary=message,
            payload={"failure_code": code.value},
            warnings=(),
            provenance=None,
            artifact_refs=(),
            recoverability=recoverability,
            failure=failure,
            epistemic_status="PROVISIONAL",
        )
        self._store.append_event(
            action.session_id,
            "action.rejected",
            {"action_id": action.action_id, "failure_code": code.value},
        )
        return observation

    def _analysis_failure(
        self,
        action: RunAnalysisAction,
        code: FailureCode,
        message: str,
        recoverability: Recoverability,
    ) -> StructuredObservation:
        _, environment, session, _, episode = self._store.coherent_view(action.session_id)
        failure = StructuredFailure(code, message, recoverability)
        observation = StructuredObservation(
            observation_id=f"observation:{session.session_id}:{action.action_id}",
            delivery_id=f"delivery:{session.session_id}:{action.action_id}",
            session_id=session.session_id,
            episode_id=episode.episode_id,
            environment_ref=environment.snapshot_ref,
            action_id=action.action_id,
            status=ObservationStatus.REJECTED,
            observation_type="analysis_failure",
            summary=message,
            payload={"failure_code": code.value},
            warnings=(),
            provenance=None,
            artifact_refs=(),
            recoverability=recoverability,
            failure=failure,
            epistemic_status="EXPLORATORY",
        )
        self._store.append_event(
            action.session_id,
            "action.rejected",
            {"action_id": action.action_id, "failure_code": code.value},
        )
        return observation

    def _failure(
        self,
        action: InspectDatasetAction,
        code: FailureCode,
        message: str,
        recoverability: Recoverability,
        diagnostic_ref: str | None = None,
    ) -> StructuredObservation:
        _, environment, session, _, episode = self._store.coherent_view(action.session_id)
        failure = StructuredFailure(code, message, recoverability, diagnostic_ref)
        observation = StructuredObservation(
            observation_id=f"observation:{session.session_id}:{action.action_id}",
            delivery_id=f"delivery:{session.session_id}:{action.action_id}",
            session_id=session.session_id,
            episode_id=episode.episode_id,
            environment_ref=environment.snapshot_ref,
            action_id=action.action_id,
            status=ObservationStatus.REJECTED,
            observation_type="action_failure",
            summary=message,
            payload={"failure_code": code.value},
            warnings=(),
            provenance=None,
            artifact_refs=(diagnostic_ref,) if diagnostic_ref is not None else (),
            recoverability=recoverability,
            failure=failure,
        )
        self._store.append_event(
            action.session_id,
            "action.rejected",
            {"action_id": action.action_id, "failure_code": code.value},
        )
        return observation


def make_toy_monthly_dataset() -> DatasetDefinition:
    """Create the deterministic 18-row fixture reused by later milestones."""
    rows: list[Mapping[str, object]] = []
    for index in range(18):
        year = 2024 + index // MONTHS_PER_YEAR
        month = index % MONTHS_PER_YEAR + 1
        next_month = month % MONTHS_PER_YEAR + 1
        available_year = year + (1 if month == MONTHS_PER_YEAR else 0)
        rows.append(
            {
                "reference_time": f"{year:04d}-{month:02d}-01",
                "available_at": f"{available_year:04d}-{next_month:02d}-15",
                "predictor_value": (
                    None if index == MISSING_PREDICTOR_INDEX else float(100 + index)
                ),
                "target_value": float(50 + index * 2),
            }
        )
    return DatasetDefinition(
        dataset_ref="toy-monthly",
        version="v1",
        field_semantics={
            "reference_time": "Observation reference month.",
            "available_at": "Recorded publication timestamp; not enforced in Milestone 1.",
            "predictor_value": "Synthetic candidate predictor.",
            "target_value": "Synthetic target value.",
        },
        rows=tuple(rows),
    )


__all__ = [
    "MAX_PREVIEW_ROWS",
    "ActionRouter",
    "AuthorizedDataView",
    "CapabilityExecutionResult",
    "DatasetDefinition",
    "DatasetRepository",
    "InspectDatasetCapability",
    "make_toy_monthly_dataset",
]
