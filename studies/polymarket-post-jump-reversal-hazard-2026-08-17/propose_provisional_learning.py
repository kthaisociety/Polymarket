"""Create the exact unvalidated learning proposal from two post-shock studies."""

# ruff: noqa: EM101, INP001, T201, TRY003

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TYPE_CHECKING

from research_agent.learning import (
    ApplicabilityScope,
    EvidenceSourcePolicy,
    EvidenceStatus,
    HistoricalEvidenceRegistrar,
    HistoricalEvidenceSelector,
    HistoryReflector,
    KnowledgePublisherPolicy,
    LearningAuthorityRegistry,
    LearningLedger,
    LearningReaderPolicy,
    LearningRepository,
    LessonKind,
    LessonProposer,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

_ENVIRONMENT = "polymarket-corpus:610b8b9d423d94332923f1e2033410007a890b9da0f9dc67936f17e92263fb2f"
_TASK_KIND = "polymarket-time-series-research"
_TASKS = (
    "polymarket-delayed-post-jump-2026-08-17",
    "polymarket-post-jump-reversal-hazard-2026-08-17",
)
_TAGS = ("post-shock-model-selection", "execution-screening")


def build_parser() -> argparse.ArgumentParser:
    """Build the study-local immutable receipt command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Issue a candidate lesson without validation or publication authority."""
    arguments = build_parser().parse_args(argv)
    ledger = LearningLedger()
    authorities = LearningAuthorityRegistry(
        source_policies=(
            EvidenceSourcePolicy(
                "chronos-study-ledger",
                (_ENVIRONMENT,),
                (_TASK_KIND,),
                _TAGS,
            ),
        ),
        validator_authority_ids=("independent-lesson-board",),
        reader_policies=(
            LearningReaderPolicy(
                "chronos-researcher",
                ("chronos-study-ledger",),
                _TASKS,
                (_TASK_KIND,),
                (_ENVIRONMENT,),
                _TAGS,
            ),
        ),
        publisher_policies=(
            KnowledgePublisherPolicy(
                "knowledge-curator",
                ("chronos-researcher",),
                (_TASK_KIND,),
                (_ENVIRONMENT,),
                _TAGS,
            ),
        ),
    )
    repository = LearningRepository(authorities=authorities)
    registrar = HistoricalEvidenceRegistrar(
        repository,
        ledger,
        authorities=authorities,
    )
    source = authorities.source("chronos-study-ledger")
    delayed = registrar.register(
        source=source,
        task_id=_TASKS[0],
        task_kind=_TASK_KIND,
        environment_ref=_ENVIRONMENT,
        subject_tags=_TAGS,
        status=EvidenceStatus.SUCCEEDED,
        summary=(
            "Delayed-continuation study found aggregate reversal while its learned model and "
            "event/side cost stability failed."
        ),
        source_refs=(
            "sha256:a923a7f044d771fec5ed03cf904102b038b1d64ae068af55e9377974273f9d01",
            "sha256:311fc5cbfdeb0925e60146fbc565249db9ec3aa6cfbd3d01880ee85a396939a0",
        ),
    )
    hazard = registrar.register(
        source=source,
        task_id=_TASKS[1],
        task_kind=_TASK_KIND,
        environment_ref=_ENVIRONMENT,
        subject_tags=_TAGS,
        status=EvidenceStatus.SUCCEEDED,
        summary=(
            "Reversal-hazard study improved aggregate Brier and passed its sampled-price cost "
            "screen while failing pooled-AP, early-half, and ranking clauses."
        ),
        source_refs=(
            "sha256:25baa10e9273e19b8ff969e4e9f6659b2ccaf4110f6deb7e485feb34a68fcc3a",
            "sha256:65e9a70ce16551f560b38d4e90155fa00fb25b00ddb3c95558fc8bcc7b73b442",
        ),
    )
    scope = ApplicabilityScope(
        task_kinds=(_TASK_KIND,),
        environment_refs=(_ENVIRONMENT,),
        subject_tags=_TAGS,
    )
    selector = HistoricalEvidenceSelector(
        repository,
        ledger,
        authorities=authorities,
    )
    selection = selector.select(
        reader=authorities.reader("chronos-researcher"),
        scope=scope,
        task_ids=_TASKS,
    )
    reflection = HistoryReflector(
        repository,
        ledger,
        selector=selector,
    ).reflect(
        selection=selection,
        protocol_id="chronos-post-shock-reflection/v1",
        claims=(
            "Predictive stability and cost-aware execution screens must remain conjunctive.",
            "A sampled-price execution pass cannot override a failed predeclared predictive gate.",
        ),
        uncertainties=(
            "The proposed procedure has not been independently validated outside this corpus.",
            "Neither study contains executable quote evidence or protected confirmation.",
        ),
    )
    candidate = LessonProposer(repository, ledger).propose(
        reflection=reflection,
        proposer_id="chronos-researcher",
        kind=LessonKind.SKILL,
        content=(
            "Keep predictive stability and cost-aware execution screens conjunctive for internal "
            "Polymarket post-shock rules; retain an execution-only pass as a development lead when "
            "the predeclared predictive gate fails."
        ),
        scope=scope,
        supporting_evidence_ids=(delayed.evidence_id, hazard.evidence_id),
        contrary_evidence_ids=(),
        caveats=(
            "Applies only to the exact retained Polymarket corpus and post-shock research scope.",
            "Candidate is unvalidated and grants no publication, protected, or trading authority.",
        ),
    )
    payload = {
        "schema_version": "chronos-candidate-lesson-receipt/v1",
        "epistemic_status": "CANDIDATE_UNVALIDATED",
        "candidate_id": candidate.candidate_id,
        "reflection_id": reflection.reflection_id,
        "selection_id": selection.selection_id,
        "proposer_id": candidate.proposer_id,
        "kind": candidate.kind.value,
        "content": candidate.content,
        "scope": {
            "task_kinds": list(candidate.scope.task_kinds),
            "environment_refs": list(candidate.scope.environment_refs),
            "subject_tags": list(candidate.scope.subject_tags),
        },
        "supporting_evidence": [
            {
                "evidence_id": item.evidence_id,
                "task_id": item.task_id,
                "status": item.status.value,
                "summary": item.summary,
                "source_refs": list(item.source_refs),
            }
            for item in (delayed, hazard)
        ],
        "contrary_evidence_ids": list(candidate.contrary_evidence_ids),
        "caveats": list(candidate.caveats),
        "originating_task_ids": list(candidate.originating_task_ids),
        "validation_decision": None,
        "published_learning": None,
        "ledger": [
            {
                "ordinal": item.ordinal,
                "event_type": item.event_type,
                "subject_id": item.subject_id,
                "detail_refs": list(item.detail_refs),
            }
            for item in ledger.entries()
        ],
    }
    content = (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode()
    arguments.receipt.parent.mkdir(parents=True, exist_ok=True)
    try:
        with arguments.receipt.open("xb") as receipt_file:
            receipt_file.write(content)
    except FileExistsError:
        if arguments.receipt.read_bytes() != content:
            raise ValueError("learning receipt path contains different bytes") from None
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
