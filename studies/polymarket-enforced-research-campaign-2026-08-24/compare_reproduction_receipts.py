"""Compare enforced campaign details with matching prior Chronos receipts."""

# ruff: noqa: INP001, T201

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast


def main() -> int:
    """Match by source and partition identity, then compare exact structured details."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-directory", required=True, type=Path)
    parser.add_argument("--studies-directory", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()

    prior = _prior_receipts(arguments.studies_directory, arguments.campaign_directory)
    rows = []
    for receipt_path in sorted((arguments.campaign_directory / "executions").glob("*.json")):
        receipt = cast("dict[str, object]", json.loads(receipt_path.read_bytes()))
        source_sha256 = cast("str", receipt["source_sha256"])
        dataset_refs = {
            str(item[1])
            for item in cast("list[list[object]]", receipt["actual_accesses"])
        }
        matches = [
            item
            for item in prior
            if item[1].get("source_sha256") == source_sha256
            and _partition_matches(item[1], dataset_refs)
        ]
        current_details = _campaign_details(receipt, arguments.campaign_directory)
        if len(matches) == 1:
            prior_path, prior_receipt = matches[0]
            prior_details = prior_receipt.get("details")
            status = "IDENTICAL" if current_details == prior_details else "CHANGED"
            prior_relative = str(prior_path.relative_to(arguments.studies_directory))
        else:
            status = "NO_UNIQUE_PRIOR_RECEIPT"
            prior_relative = None
        rows.append(
            {
                "analysis_id": receipt["analysis_id"],
                "source_sha256": source_sha256,
                "comparison": status,
                "prior_receipt": prior_relative,
                "matching_prior_count": len(matches),
            }
        )
    payload = {
        "schema_version": "chronos-campaign-reproduction-comparison/v1",
        "campaign_identity": json.loads(
            (arguments.campaign_directory / "manifest.json").read_bytes()
        )["campaign_identity"],
        "analysis_count": len(rows),
        "identical_count": sum(item["comparison"] == "IDENTICAL" for item in rows),
        "changed_count": sum(item["comparison"] == "CHANGED" for item in rows),
        "unmatched_count": sum(
            item["comparison"] == "NO_UNIQUE_PRIOR_RECEIPT" for item in rows
        ),
        "rows": rows,
    }
    _persist(payload, arguments.output)
    print(json.dumps(payload, sort_keys=True))
    return 0


def _prior_receipts(
    studies_directory: Path,
    campaign_directory: Path,
) -> list[tuple[Path, dict[str, object]]]:
    rows = []
    campaign_root = campaign_directory.resolve()
    for path in studies_directory.rglob("*.json"):
        if campaign_root in path.resolve().parents:
            continue
        try:
            payload = json.loads(path.read_bytes())
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if (
            isinstance(payload, dict)
            and isinstance(payload.get("source_sha256"), str)
            and payload.get("status") == "succeeded"
            and "details" in payload
        ):
            rows.append((path, cast("dict[str, object]", payload)))
    return rows


def _partition_matches(receipt: dict[str, object], dataset_refs: set[str]) -> bool:
    partition = receipt.get("partition_id")
    if not isinstance(partition, str):
        return False
    return any(partition in dataset_ref for dataset_ref in dataset_refs)


def _campaign_details(receipt: dict[str, object], campaign_directory: Path) -> object:
    details = receipt.get("details")
    if details is not None:
        return details
    artifacts = cast("list[dict[str, object]]", receipt.get("artifacts"))
    result_artifacts = [item for item in artifacts if item.get("kind") == "result"]
    if len(result_artifacts) != 1:
        message = "externalized campaign result does not resolve uniquely"
        raise ValueError(message)
    result = json.loads(
        (campaign_directory / str(result_artifacts[0]["object_ref"])).read_bytes()
    )
    return result["details"]


def _persist(payload: dict[str, object], path: Path) -> None:
    content = (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as output:
            output.write(content)
    except FileExistsError:
        if path.read_bytes() != content:
            message = "reproduction comparison conflicts with existing bytes"
            raise ValueError(message) from None


if __name__ == "__main__":
    raise SystemExit(main())
