"""Issue a harness-owned inventory for prior studies that must not be replayed as analyses."""

# ruff: noqa: E501, INP001, T201

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from research_agent.exploration import (
    AnalysisDisposition,
    AnalysisHarness,
    ArtifactStore,
    AuthorizedDataView,
    CampaignAnalysis,
    CampaignManifest,
    CampaignStore,
    CapabilityPolicy,
    DataAccessRequest,
    EvidenceTier,
    ResearchCampaignAuthority,
    ResourceLimits,
)


@dataclass(frozen=True, slots=True)
class CoverageItem:
    """One exact prior source or receipt and its non-replay disposition."""

    item_id: str
    source: str | None
    receipt: str
    status: str
    reason: str
    replacement: str


_ITEMS = (
    CoverageItem(
        "stochastic.process-diagnostics.failed-v1",
        "polymarket-process-tradability-2026-08-17/sources/01_process_diagnostics.py",
        "polymarket-process-tradability-2026-08-17/development-receipts/01_process_diagnostics.json",
        "FAILED_VARIANT_REPLACED",
        "The original worker timed out; the linear policy-safe revision is the final runnable source.",
        "stochastic.process-tradability.linear-diagnostics.v1",
    ),
    CoverageItem(
        "stochastic.reversal-falsifier.denied-v1",
        "polymarket-process-tradability-2026-08-17/sources/04_reversal_execution_falsifiers.py",
        "polymarket-process-tradability-2026-08-17/development-receipts/04_reversal_execution_falsifiers.json",
        "DENIED_VARIANT_REPLACED",
        "The source requested an ungranted interface; the permitted revision is the final runnable source.",
        "stochastic.process-tradability.execution-falsifiers.v1",
    ),
    CoverageItem(
        "stochastic.first-move.denied-v1",
        "polymarket-first-move-direction-2026-08-17/source/01_direction_benchmark.py",
        "polymarket-first-move-direction-2026-08-17/development-receipts/01_direction_benchmark.json",
        "DENIED_VARIANT_REPLACED",
        "The source requested an ungranted interface; the policy-safe revision is the final runnable source.",
        "stochastic.first-move-direction.policy-safe.v1",
    ),
    CoverageItem(
        "stochastic.sibling-benchmark.failed-v1",
        "polymarket-sibling-surface-2026-08-17/source/01_sibling_surface_benchmark.py",
        "polymarket-sibling-surface-2026-08-17/development-receipts/01_sibling_surface_benchmark.json",
        "FAILED_VARIANT_REPLACED",
        "The source failed before evidence; the alignment-safe revision is the final runnable source.",
        "stochastic.sibling-surface.alignment-safe.v1",
    ),
    CoverageItem(
        "stochastic.fixed-horizon.formal-failed-v1",
        "polymarket-fresh-fixed-horizon-properties-2026-08-17/source/02_formal_time_legal_reversal.py",
        "polymarket-fresh-fixed-horizon-properties-2026-08-17/formal-receipts/02_formal_time_legal_reversal_failed.json",
        "FORMAL_OPERATIONAL_FAILURE_REPLACED",
        "This formal-transition attempt failed operationally and was superseded by an ordered formal revision.",
        "stochastic.fresh-fixed-horizon.properties.v1",
    ),
    CoverageItem(
        "stochastic.fixed-horizon.formal-ordered-v1",
        "polymarket-fresh-fixed-horizon-properties-2026-08-17/source/03_formal_time_legal_reversal_ordered.py",
        "polymarket-fresh-fixed-horizon-properties-2026-08-17/formal-receipts/03_formal_time_legal_reversal_ordered.json",
        "FORMAL_WORKFLOW_NOT_REPLAYED",
        "Formal-state transitions are not exploratory analyses and cannot be reissued by AnalysisHarness.",
        "stochastic.fresh-fixed-horizon.properties.v1",
    ),
    CoverageItem(
        "stochastic.fixed-horizon.formal-revision-v1",
        "polymarket-fresh-fixed-horizon-properties-2026-08-17/source/04_formal_full_path_revision.py",
        "polymarket-fresh-fixed-horizon-properties-2026-08-17/formal-receipts/04_formal_full_path_revision.json",
        "FORMAL_WORKFLOW_NOT_REPLAYED",
        "Formal-state transitions are not exploratory analyses and cannot be reissued by AnalysisHarness.",
        "stochastic.fresh-fixed-horizon.properties.v1",
    ),
    CoverageItem(
        "stochastic.duration.formal-panel-v1",
        "polymarket-move-duration-2026-08-17/source/03_formal_duration_panel.py",
        "polymarket-move-duration-2026-08-17/development-receipts/03_formal_duration_panel.json",
        "FORMAL_WORKFLOW_NOT_REPLAYED",
        "The formal panel is governed state, not a standalone exploratory source.",
        "stochastic.move-duration.mechanism-compression.v1",
    ),
    CoverageItem(
        "stochastic.duration.freeze-replay-v1",
        "polymarket-move-duration-2026-08-17/source/04_coordinator_freeze_replay.py",
        "polymarket-move-duration-2026-08-17/development-receipts/04_coordinator_freeze_replay.json",
        "FORMAL_WORKFLOW_NOT_REPLAYED",
        "The freeze transition is governed state; its underlying analytical source was rerun instead.",
        "stochastic.move-duration.mechanism-compression.v1",
    ),
    CoverageItem(
        "stochastic.duration.protected-attempt-v1",
        "polymarket-move-duration-2026-08-17/source/05_exact_plan_protected_resolution.py",
        "polymarket-move-duration-2026-08-17/protected-incidents/05_attempt_01_interrupted.json",
        "PROTECTED_NOT_REOPENED",
        "The protected attempt is in doubt and reopening protected values would violate one-shot governance.",
        "",
    ),
    CoverageItem(
        "stochastic.sibling.formal-panel-v1",
        "polymarket-sibling-surface-2026-08-17/source/04_formal_sibling_state_panel.py",
        "polymarket-sibling-surface-2026-08-17/development-receipts/04_formal_sibling_state_panel.json",
        "FORMAL_FAILED_VARIANT_REPLACED",
        "This formal reporting attempt failed and was superseded without changing the analytical candidate.",
        "stochastic.sibling-surface.compression.v1",
    ),
    CoverageItem(
        "stochastic.sibling.formal-coverage-safe-v1",
        "polymarket-sibling-surface-2026-08-17/source/05_formal_sibling_state_panel_coverage_safe.py",
        "polymarket-sibling-surface-2026-08-17/development-receipts/05_formal_sibling_state_panel_coverage_safe.json",
        "FORMAL_FAILED_VARIANT_REPLACED",
        "This formal reporting attempt failed and was superseded without changing the analytical candidate.",
        "stochastic.sibling-surface.compression.v1",
    ),
    CoverageItem(
        "stochastic.sibling.formal-reporting-safe-v1",
        "polymarket-sibling-surface-2026-08-17/source/06_formal_sibling_state_panel_reporting_safe.py",
        "polymarket-sibling-surface-2026-08-17/development-receipts/06_formal_sibling_state_panel_reporting_safe.json",
        "FORMAL_WORKFLOW_NOT_REPLAYED",
        "Formal-state transitions are not exploratory analyses; the underlying analytical source was rerun.",
        "stochastic.sibling-surface.compression.v1",
    ),
    CoverageItem(
        "stochastic.paper.successor-identity-v1",
        "polymarket-stochastic-process-paper-2026-08-18/source/07_successor_partition_identity.py",
        "polymarket-stochastic-process-paper-2026-08-18/successor-corpus/partition-receipts/07_successor_partition_identity.json",
        "IDENTITY_ONLY_NOT_SCIENTIFIC",
        "The source intentionally reads zero value fields; the v2 manifest now binds the successor partition directly.",
        "stochastic.paper.frozen-process-replay.successor.v1",
    ),
    CoverageItem(
        "stochastic.paper.formal-hurdle-freeze-v1",
        "polymarket-stochastic-process-paper-2026-08-18/source/14_formal_hurdle_arrival_freeze.py",
        "polymarket-stochastic-process-paper-2026-08-18/development-receipts/14_formal_hurdle_arrival_freeze.json",
        "FORMAL_WORKFLOW_NOT_REPLAYED",
        "The formal rejection is governed state; source 12 and its successor replay carry the analytical evidence.",
        "stochastic.paper.composed-family.initial.v1",
    ),
    CoverageItem(
        "stochastic.paper.formal-continuous-hazard-v1",
        "polymarket-stochastic-process-paper-2026-08-18/source/18_formal_continuous_arrival_hazard.py",
        "polymarket-stochastic-process-paper-2026-08-18/development-receipts/18_formal_continuous_arrival_hazard.json",
        "FORMAL_WORKFLOW_NOT_REPLAYED",
        "The formal freeze is governed state; its development and successor analytical sources were rerun.",
        "stochastic.paper.frozen-arrival-replay.successor.v1",
    ),
    CoverageItem(
        "stochastic.paper.protected-continuous-hazard-v1",
        "polymarket-stochastic-process-paper-2026-08-18/source/19_continuous_arrival_hazard_protected_resolution.py",
        "polymarket-stochastic-process-paper-2026-08-18/protected-receipts/19_continuous_arrival_hazard_protected_resolution.json",
        "PROTECTED_NOT_REOPENED",
        "The one-shot protected result already rejected the model and must not be rerun on exposed protected values.",
        "",
    ),
    CoverageItem(
        "behavioral.skilled-wallet.fold-local-sql-v1",
        "polymarket-behavioral-game-theory-2026-08-24/source/02_fold_local_skilled_wallet.sql",
        "polymarket-behavioral-game-theory-2026-08-24/development-receipts/02_fold_local_skilled_wallet.json",
        "DIRECT_SQL_REPLACED_BY_REGISTERED_VIEW",
        "The direct SQL mechanism was replaced by a parent-bound taker-fill view and exact harness execution.",
        "behavioral.skilled-wallet-matched-state.v2",
    ),
    CoverageItem(
        "behavioral.skilled-wallet.matched-state-sql-v1",
        "polymarket-behavioral-game-theory-2026-08-24/source/03_skilled_wallet_matched_state.sql",
        "polymarket-behavioral-game-theory-2026-08-24/development-receipts/03_skilled_wallet_matched_state.json",
        "DIRECT_SQL_REPLACED_BY_REGISTERED_VIEW",
        "The direct SQL mechanism was replaced by a parent-bound taker-fill view and exact harness execution.",
        "behavioral.skilled-wallet-matched-state.v2",
    ),
    CoverageItem(
        "behavioral.expert-consensus.sql-v1",
        "polymarket-behavioral-game-theory-2026-08-24/source/04_delayed_wallet_and_expert_consensus.sql",
        "polymarket-behavioral-game-theory-2026-08-24/development-receipts/04_delayed_wallet_and_expert_consensus.json",
        "DIRECT_SQL_REPLACED_BY_REGISTERED_VIEW",
        "The direct SQL mechanism was replaced by a parent-bound taker-fill view and exact harness execution.",
        "behavioral.delayed-expert-consensus.v2",
    ),
    CoverageItem(
        "behavioral.skilled-wallet.activity-match-sql-v1",
        "polymarket-behavioral-game-theory-2026-08-24/source/05_delayed_wallet_state_activity_match.sql",
        "polymarket-behavioral-game-theory-2026-08-24/development-receipts/05_delayed_wallet_state_activity_match.json",
        "DIRECT_SQL_REPLACED_BY_REGISTERED_VIEW",
        "The direct SQL falsifier was rewritten against the registered parent-bound taker panel.",
        "behavioral.delayed-wallet-state-activity-match.v2",
    ),
    CoverageItem(
        "behavioral.disposition-readiness.sql-v1",
        "polymarket-behavioral-game-theory-2026-08-24/source/07_disposition_history_sufficiency.sql",
        "polymarket-behavioral-game-theory-2026-08-24/development-receipts/07_disposition_history_sufficiency.json",
        "DATA_BLOCKED",
        "Incomplete repair history can manufacture historical inventory and cost basis, so no strategy analysis is admissible.",
        "",
    ),
    CoverageItem(
        "behavioral.crowded-extrapolation.sql-v1",
        "polymarket-behavioral-game-theory-2026-08-24/source/08_crowded_extrapolation_exhaustion.sql",
        "polymarket-behavioral-game-theory-2026-08-24/development-receipts/08_crowded_extrapolation_exhaustion.json",
        "DIRECT_SQL_REPLACED_BY_REGISTERED_VIEW",
        "The direct SQL falsifier was rewritten against the registered parent-bound taker panel.",
        "behavioral.crowded-extrapolation-exhaustion.v2",
    ),
    CoverageItem(
        "game-theory.negrisk-readiness.sql-v1",
        "polymarket-behavioral-game-theory-2026-08-24/source/09_negrisk_coordination_data_sufficiency.sql",
        "polymarket-behavioral-game-theory-2026-08-24/development-receipts/09_negrisk_coordination_data_sufficiency.json",
        "DATA_BLOCKED",
        "Historical dual-clock executable depth and exact exhaustive event membership are absent, so no basket backtest is admissible.",
        "",
    ),
    CoverageItem(
        "behavioral.probability-weighting.fresh-boundary-v1",
        None,
        "polymarket-behavioral-game-theory-2026-08-24/fresh-replication/boundary-receipt.json",
        "PROTECTED_NOT_OPENED",
        "The latest whole-event block remains protected; rerunning the exposed screen cannot create fresh evidence.",
        "behavioral.probability-weighting.v1",
    ),
)

_SOURCE = """
item_ids = read("chronos-nonreplay-coverage", "item_id")
source_paths = read("chronos-nonreplay-coverage", "source_path")
source_hashes = read("chronos-nonreplay-coverage", "source_sha256")
receipt_paths = read("chronos-nonreplay-coverage", "receipt_path")
receipt_hashes = read("chronos-nonreplay-coverage", "receipt_sha256")
statuses = read("chronos-nonreplay-coverage", "status")
reasons = read("chronos-nonreplay-coverage", "reason")
replacements = read("chronos-nonreplay-coverage", "replacement_analysis_id")
rows = []
for row in range(len(item_ids)):
    rows = rows + [{
        "item_id": item_ids[row],
        "source_path": source_paths[row],
        "source_sha256": source_hashes[row],
        "receipt_path": receipt_paths[row],
        "receipt_sha256": receipt_hashes[row],
        "status": statuses[row],
        "reason": reasons[row],
        "replacement_analysis_id": replacements[row],
    }]
result = structured_return(
    "Exact inventory of prior sources that were replaced, blocked, formal, or protected.",
    {
        "schema_version": "chronos-nonreplay-coverage-audit/v1",
        "item_count": len(rows),
        "rows": rows,
    },
    warnings=[
        "This receipt proves coverage accounting, not execution of the inventoried source.",
        "Protected and formal artifacts are intentionally not reopened by AnalysisHarness.",
    ],
)
"""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    """Bind the exact inventory into a harness, execute it, and close the audit campaign."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--studies-directory", required=True, type=Path)
    parser.add_argument("--campaign-directory", required=True, type=Path)
    arguments = parser.parse_args()
    root = arguments.studies_directory
    source_paths = tuple("" if item.source is None else item.source for item in _ITEMS)
    receipt_paths = tuple(item.receipt for item in _ITEMS)
    source_hashes = tuple(
        "" if item.source is None else _sha256(root / item.source) for item in _ITEMS
    )
    receipt_hashes = tuple(_sha256(root / item.receipt) for item in _ITEMS)
    fields = {
        "item_id": tuple(item.item_id for item in _ITEMS),
        "source_path": source_paths,
        "source_sha256": source_hashes,
        "receipt_path": receipt_paths,
        "receipt_sha256": receipt_hashes,
        "status": tuple(item.status for item in _ITEMS),
        "reason": tuple(item.reason for item in _ITEMS),
        "replacement_analysis_id": tuple(item.replacement for item in _ITEMS),
    }
    session_id = "chronos-polymarket-nonreplay-audit-2026-08-24"
    view_id = "chronos-nonreplay-coverage"
    dataset_ref = "chronos-nonreplay-coverage:" + hashlib.sha256(
        json.dumps(fields, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    environment_ref = "chronos:local-retained-audit"
    view = AuthorizedDataView(view_id, dataset_ref, environment_ref, fields)
    harness = AnalysisHarness(
        views={view_id: view},
        policy=CapabilityPolicy(
            session_id,
            environment_ref,
            {view_id: frozenset(fields)},
        ),
        artifacts=ArtifactStore(),
        resource_limits=ResourceLimits(wall_time_seconds=30.0, max_inline_bytes=500_000),
    )
    access = DataAccessRequest(view_id, tuple(fields))
    analysis = CampaignAnalysis(
        analysis_id="audit.nonreplay-coverage.v1",
        family="research-governance",
        source=_SOURCE,
        data_access=(access,),
        required_actual_accesses=tuple((view_id, field) for field in fields),
        expected_dataset_refs=(dataset_ref,),
        expected_environment_refs=(environment_ref,),
        expected_harness_binding_identity=harness.binding_identity,
        evidence_tier=EvidenceTier.BLOCKED_OR_NOT_TESTED,
    )
    authority = ResearchCampaignAuthority(
        CampaignManifest(
            "polymarket-nonreplay-coverage-audit-v1-2026-08-24",
            "Account exactly for prior sources that cannot or should not be replayed as ordinary analyses.",
            (analysis,),
        ),
        store=CampaignStore(arguments.campaign_directory),
    )
    execution = authority.execute(analysis.analysis_id, harness=harness, session_id=session_id)
    completion = authority.complete({analysis.analysis_id: AnalysisDisposition.RETAINED})
    print(
        json.dumps(
            {
                "status": "SUCCEEDED",
                "item_count": len(_ITEMS),
                "execution_receipt_id": execution.receipt_id,
                "completion_receipt_id": completion.receipt_id,
                "admissible": execution.admissible,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
