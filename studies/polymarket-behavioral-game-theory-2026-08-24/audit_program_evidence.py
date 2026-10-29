"""Deterministically verify the behavioral program's retained evidence identities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


_STUDY = Path(__file__).resolve().parent
_RECEIPTS = _STUDY / "development-receipts"
_SOURCES = _STUDY / "source"

_EXPECTED = {
    "01_focal_price_anchoring.json": {
        "source": "01_focal_price_anchoring.py",
        "status": "succeeded",
        "decision_path": ("details", "screen_outcome"),
        "decision": "NO_STABLE_FOCAL_EFFECT",
        "protected": True,
    },
    "02_fold_local_skilled_wallet.json": {
        "source": "02_fold_local_skilled_wallet.sql",
        "status": "SUCCEEDED",
        "decision_path": ("development_gate", "status"),
        "decision": "MECHANISM_SUPPORTED_FOR_EXECUTABLE_FOLLOW_UP",
        "protected": False,
    },
    "03_skilled_wallet_matched_state.json": {
        "source": "03_skilled_wallet_matched_state.sql",
        "status": "SUCCEEDED",
        "decision_path": ("decision", "status"),
        "decision": "REJECT_FIXED_B1_MATCHED_STATE_CANDIDATE",
        "protected": False,
    },
    "04_delayed_wallet_and_expert_consensus.json": {
        "source": "04_delayed_wallet_and_expert_consensus.sql",
        "status": "SUCCEEDED",
        "decision_path": ("b2_expert_consensus", "decision", "status"),
        "decision": "REJECT_FIXED_B2_EXPERT_CONSENSUS_CANDIDATE",
        "protected": False,
    },
    "05_delayed_wallet_state_activity_match.json": {
        "source": "05_delayed_wallet_state_activity_match.sql",
        "status": "SUCCEEDED",
        "decision_path": ("decision", "status"),
        "decision": "REJECT_FIXED_B1_DELAYED_STATE_ACTIVITY_CANDIDATE",
        "protected": False,
    },
    "06_probability_weighting_strategy.json": {
        "source": "06_probability_weighting_strategy.py",
        "status": "succeeded",
        "decision_path": ("details", "decisions", "LONGSHOT_FADE", "status"),
        "decision": "RETAIN_FOR_FRESH_EVALUATION",
        "protected": True,
    },
    "07_disposition_history_sufficiency.json": {
        "source": "07_disposition_history_sufficiency.sql",
        "status": "BLOCKED_DATA_SUBSTRATE",
        "decision_path": ("audit", "decision"),
        "decision": "BLOCK_DISPOSITION_SCREEN",
        "protected": False,
    },
    "08_crowded_extrapolation_exhaustion.json": {
        "source": "08_crowded_extrapolation_exhaustion.sql",
        "status": "SUCCEEDED",
        "decision_path": ("decision",),
        "decision": "REJECT_FIXED_CROWDED_EXTRAPOLATION_CANDIDATE",
        "protected": False,
    },
    "09_negrisk_coordination_data_sufficiency.json": {
        "source": "09_negrisk_coordination_data_sufficiency.sql",
        "status": "BLOCKED_DATA_SUBSTRATE",
        "decision_path": ("decision",),
        "decision": "BLOCK_COMPLETE_SET_STRATEGY",
        "protected": False,
    },
    "10_ambiguity_aversion_strategy.json": {
        "source": "10_ambiguity_aversion_strategy.py",
        "status": "succeeded",
        "decision_path": ("details", "decision"),
        "decision": "REJECT_FIXED_AMBIGUITY_PROXY_CANDIDATE",
        "protected": True,
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def _at(value: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = value
    for key in path:
        if not isinstance(current, dict) or key not in current:
            raise KeyError(".".join(path))
        current = current[key]
    return current


def _check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> None:
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    actual_names = {path.name for path in _RECEIPTS.glob("*.json")}
    _check(
        actual_names == set(_EXPECTED),
        f"receipt inventory mismatch: {sorted(actual_names ^ set(_EXPECTED))}",
        errors,
    )
    for receipt_name, expected in _EXPECTED.items():
        receipt_path = _RECEIPTS / receipt_name
        source_path = _SOURCES / str(expected["source"])
        _check(receipt_path.is_file(), f"missing receipt: {receipt_name}", errors)
        _check(source_path.is_file(), f"missing source: {source_path.name}", errors)
        if not receipt_path.is_file() or not source_path.is_file():
            continue
        receipt = _load(receipt_path)
        actual_source_hash = _sha256(source_path)
        _check(
            receipt.get("source_name") == source_path.name,
            f"source name mismatch: {receipt_name}",
            errors,
        )
        _check(
            receipt.get("source_sha256") == actual_source_hash,
            f"source hash mismatch: {receipt_name}",
            errors,
        )
        _check(
            receipt.get("status") == expected["status"],
            f"status mismatch: {receipt_name}",
            errors,
        )
        decision = _at(receipt, expected["decision_path"])
        _check(
            decision == expected["decision"],
            f"decision mismatch: {receipt_name}",
            errors,
        )
        _check(
            receipt.get("durable_state_effects") == [],
            f"unexpected durable state effect: {receipt_name}",
            errors,
        )
        if expected["protected"]:
            _check(
                receipt.get("protected_values_exposed") is False,
                f"protected exposure mismatch: {receipt_name}",
                errors,
            )
        rows.append(
            {
                "receipt": receipt_name,
                "source": source_path.name,
                "source_sha256": actual_source_hash,
                "status": receipt.get("status"),
                "decision": decision,
                "protected_values_exposed": receipt.get(
                    "protected_values_exposed", False
                ),
                "durable_state_effect_count": len(
                    receipt.get("durable_state_effects", [])
                ),
            }
        )

    server_audit_path = _STUDY / "server-data-audit.json"
    server_audit = _load(server_audit_path)
    server_source = _STUDY / str(server_audit["source_name"])
    role = server_audit["role_proof"]
    _check(
        server_audit["source_sha256"] == _sha256(server_source),
        "server audit source hash mismatch",
        errors,
    )
    _check(role["role"] == "human_ro", "server role is not human_ro", errors)
    _check(role["default_read_only"] == "on", "default read-only is off", errors)
    _check(
        role["transaction_read_only"] == "on", "transaction read-only is off", errors
    )
    mutation_privileges = [
        value
        for key, value in role.items()
        if key.startswith("can_insert_") or key.startswith("can_update_")
    ]
    _check(not any(mutation_privileges), "server mutation privilege detected", errors)
    _check(
        server_audit.get("durable_state_effects") == [],
        "server audit durable state effect detected",
        errors,
    )

    boundary_path = _STUDY / "fresh-replication" / "boundary-receipt.json"
    boundary = _load(boundary_path)
    boundary_source = _STUDY / str(boundary["audit_source_name"])
    _check(
        boundary["audit_source_sha256"] == _sha256(boundary_source),
        "fresh boundary source hash mismatch",
        errors,
    )
    _check(
        boundary["strict_ancestor_prefix_verified"] is True,
        "ancestor prefix not verified",
        errors,
    )
    _check(
        boundary["protected_values_exposed"] is False,
        "fresh boundary exposed protected values",
        errors,
    )
    _check(boundary["source_executed"] is False, "B3 source executed early", errors)
    _check(
        boundary["fresh_development_event_count"] == 0,
        "unexpected legal B3 fresh events in retained boundary",
        errors,
    )

    corpus_path = _STUDY / "fresh-replication" / "corpus-receipt.json"
    corpus = _load(corpus_path)
    _check(corpus["database_role"] == "human_ro", "fresh corpus role mismatch", errors)
    _check(corpus["transaction_read_only"] is True, "fresh corpus not read-only", errors)
    _check(
        corpus.get("durable_state_effects") == [],
        "fresh corpus durable state effect detected",
        errors,
    )

    result = {
        "schema_version": "polymarket-behavioral-program-evidence-audit/v1",
        "status": "PASSED" if not errors else "FAILED",
        "error_count": len(errors),
        "errors": errors,
        "receipt_count": len(rows),
        "source_hashes_verified": len(rows) if not errors else None,
        "receipts": rows,
        "server_authority": {
            "role": role["role"],
            "default_read_only": role["default_read_only"],
            "transaction_read_only": role["transaction_read_only"],
            "mutation_privilege_count": sum(bool(value) for value in mutation_privileges),
            "server_audit_source_sha256": _sha256(server_source),
        },
        "b3_fresh_boundary": {
            "status": boundary["status"],
            "current_event_count": boundary["current_event_count"],
            "fresh_development_event_count": boundary[
                "fresh_development_event_count"
            ],
            "source_executed": boundary["source_executed"],
            "protected_values_exposed": boundary["protected_values_exposed"],
            "first_legal_successor_total": boundary[
                "required_total_event_count_for_first_legal_successor"
            ],
            "minimum_runnable_total": 404,
        },
        "invariants": {
            "all_retained_source_hashes_match": not any(
                "source hash mismatch" in item for item in errors
            ),
            "no_protected_values_exposed": not any(
                "protected" in item and "mismatch" in item for item in errors
            ),
            "no_durable_state_effects": not any(
                "durable state effect" in item for item in errors
            ),
            "production_reads_proved_read_only": not any(
                "read-only" in item or "role" in item or "privilege" in item
                for item in errors
            ),
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
