# ruff: noqa: D103, EM101, INP001, T201, TRY003

"""Build an exact semantic-pair audit for Brazil contracts on two venues."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

_KALSHI_INVENTORY_SHA256 = "1b3995cf29f6f1788c443d4ecf16482b10bf34fa41c1c6586ae01f5837daa750"
_POLYMARKET_AUDIT_SHA256 = "614d9bcbaa3d2d0d280f323ad20f1b6232af8c91c1440214bc45dadfcf8786a3"
_PAIRS = (
    (
        "lula",
        "KXBRPRES-26-LULA",
        "0xdf8e2dc5860027decbe6164555c3c1c9645c3bd33e16b9dc57ca87125047d4a8",
    ),
    (
        "flavio",
        "KXBRPRES-26-FBOL",
        "0x1a01bf78f56a507fcb666d564d8c8b91b0750679163ed6e96746102c9b7d285d",
    ),
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kalshi-inventory", type=Path, required=True)
    parser.add_argument("--polymarket-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if _sha256(args.kalshi_inventory) != _KALSHI_INVENTORY_SHA256:
        raise SystemExit("Kalshi inventory hash mismatch")
    if _sha256(args.polymarket_audit) != _POLYMARKET_AUDIT_SHA256:
        raise SystemExit("Polymarket audit hash mismatch")
    kalshi = {
        item["market_id"]: item
        for item in json.loads(args.kalshi_inventory.read_text())["contracts"]
    }
    polymarket = {
        item["market_id"]: item for item in json.loads(args.polymarket_audit.read_text())["markets"]
    }
    pairs = []
    for candidate, kalshi_id, polymarket_id in _PAIRS:
        kalshi_item = kalshi[kalshi_id]
        polymarket_item = polymarket[polymarket_id]
        if kalshi_item["question"] != polymarket_item["question"]:
            raise SystemExit("cross-venue question mismatch")
        pairs.append(
            {
                "candidate": candidate,
                "question": kalshi_item["question"],
                "kalshi_market_id": kalshi_id,
                "kalshi_rules_primary": kalshi_item["raw"]["market"]["rules_primary"],
                "kalshi_expiration_time": kalshi_item["raw"]["market"]["expiration_time"],
                "polymarket_market_id": polymarket_id,
                "polymarket_description": polymarket_item["raw"]["description"],
                "polymarket_fees": polymarket_item["raw"]["trading"]["fee_schedule"],
                "same_ordinary_winner_event": True,
                "cutoff_mismatch": (
                    "Polymarket routes an election result unknown by 2027-06-30 23:59 ET "
                    "to Other; Kalshi can remain open until 2027-10-25."
                ),
                "conservative_dominance_pair": "buy Kalshi YES plus buy Polymarket NO",
                "minimum_combined_payout_under_documented_outcomes": 1.0,
                "reverse_pair_is_risk_free": False,
            }
        )
    payload = {
        "schema": "chronos-brazil-cross-venue-semantic-audit/v1",
        "inputs": {
            "kalshi_inventory_sha256": _KALSHI_INVENTORY_SHA256,
            "polymarket_audit_sha256": _POLYMARKET_AUDIT_SHA256,
        },
        "pairs": pairs,
        "authority": (
            "The exact ordinary winner event matches. Only the stated Kalshi-YES plus "
            "Polymarket-NO direction receives conservative minimum-payout authority because "
            "of the differing unresolved-result cutoffs."
        ),
        "protected_values_exposed": False,
    }
    content = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    with args.output.open("xb") as output:
        output.write(content)
    print(
        json.dumps(
            {
                "status": "retained",
                "pair_count": len(pairs),
                "sha256": hashlib.sha256(content).hexdigest(),
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
